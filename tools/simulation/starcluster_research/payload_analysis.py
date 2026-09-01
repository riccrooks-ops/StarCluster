from __future__ import annotations

import csv, json, math, statistics, time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, fields
from multiprocessing import get_context
from pathlib import Path
from typing import Any, Iterable

from .ecology import (
    CandidateMatrix, EcologyBuild, SideState, SideTelemetry,
    MAP_RADIUS, MAX_TURNS, DAMAGE_MODEL, build_space, generate_primary_builds,
    _create_side, _range, _begin_turn_recharge, _move_one, _plan_once,
    _maybe_reactor_overload, _record_plan, _weapon, _hit_chance,
    _shield_armor, _apply_damage,
)
from .rng import XorShift64, derive_seed
from .study import load_json


@dataclass(frozen=True, slots=True)
class PayloadProfile:
    id: str
    family: str
    min_tl: int
    role: str
    mode: str = 'fixed'
    damage: int | None = None
    damage_delta: int = 0
    spen: int | None = None
    spen_delta: int = 0
    apen: int | None = None
    apen_delta: int = 0
    accuracy_delta: int = 0
    packets: int = 1
    shield_bonus_damage: int = 0
    shield_armor_reduction: int = 0
    recharge_suppression: int = 0
    adaptive_specialist: str | None = None
    assessment_failures_before_switch: int = 2
    mixed_specialist: str | None = None
    mixed_order: str = 'specialist-first'


@dataclass(frozen=True, slots=True)
class PayloadVariant:
    id: str
    tl: int
    side_a: EcologyBuild
    side_b: EcologyBuild
    movement_order: str
    side_a_payload: str
    side_b_payload: str = 'gp-current'
    scenario_group: str = 'missile_payload_characteristic'
    target_profile: str = 'full-defense'
    start_q_a: int = -MAP_RADIUS
    start_q_b: int = MAP_RADIUS
    max_turns: int = MAX_TURNS
    population: str = 'targeted_same_tl_exact_fill_payload'


@dataclass(slots=True)
class PayloadMissileState:
    owner: str
    eta: int
    guidance: int
    payload_id: str
    damage: int
    spen: int
    apen: int
    packets: int
    shield_bonus_damage: int
    shield_armor_reduction: int
    recharge_suppression: int


@dataclass(frozen=True, slots=True)
class PayloadTrialResult:
    winner: str
    unresolved: bool
    turns: int
    hull_a: int
    hull_b: int
    armor_a: int
    armor_b: int
    shield_a: int
    shield_b: int
    side_a: SideTelemetry
    side_b: SideTelemetry
    error: str = ''


class PayloadCatalog:
    def __init__(self, doc: dict[str, Any]):
        self.profiles: dict[str,PayloadProfile] = {}
        for row in doc['payloadProfiles']:
            p=PayloadProfile(
                id=row['id'], family=row['family'], min_tl=int(row['minTl']), role=row['role'], mode=row.get('mode','fixed'),
                damage=row.get('damage'), damage_delta=int(row.get('damageDelta',0)), spen=row.get('spen'), spen_delta=int(row.get('spenDelta',0)),
                apen=row.get('apen'), apen_delta=int(row.get('apenDelta',0)), accuracy_delta=int(row.get('accuracyDelta',0)),
                packets=int(row.get('packets',1)), shield_bonus_damage=int(row.get('shieldBonusDamage',0)),
                shield_armor_reduction=int(row.get('shieldArmorReduction',0)), recharge_suppression=int(row.get('rechargeSuppression',0)),
                adaptive_specialist=row.get('adaptiveSpecialist'), assessment_failures_before_switch=int(row.get('assessmentFailuresBeforeSwitch',2)),
                mixed_specialist=row.get('mixedSpecialist'), mixed_order=row.get('mixedOrder','specialist-first'),
            )
            self.profiles[p.id]=p
    def get(self, pid:str)->PayloadProfile:
        return self.profiles[pid]


def validate_study(doc:dict[str,Any])->list[str]:
    errors=[]
    if doc.get('schemaVersion')!='star-cluster-payload-characteristic-space-v0.1': errors.append('schemaVersion')
    if doc.get('checkpoint')!=114: errors.append('checkpoint')
    if doc.get('damageModel')!=DAMAGE_MODEL: errors.append('damageModel')
    if doc.get('automaticPromotion') is not False: errors.append('automaticPromotion')
    if int(doc.get('trialsPerVariant',0))<1: errors.append('trialsPerVariant')
    ids=[]
    for p in doc.get('payloadProfiles',[]):
        ids.append(p.get('id'))
        if p.get('family') not in ('Missile','Kinetic'): errors.append(f'payloadFamily:{p.get("id")}')
        if int(p.get('packets',1))<1 or int(p.get('packets',1))>3: errors.append(f'packets:{p.get("id")}')
    if len(ids)!=len(set(ids)): errors.append('duplicatePayloadId')
    by={p['id']:p for p in doc.get('payloadProfiles',[])}
    for p in doc.get('payloadProfiles',[]):
        if p.get('mode')=='adaptive' and p.get('adaptiveSpecialist') not in by: errors.append(f'adaptiveSpecialist:{p.get("id")}')
        if p.get('mode')=='mixed' and p.get('mixedSpecialist') not in by: errors.append(f'mixedSpecialist:{p.get("id")}')
    if not {'gp-current','missile-shaped-a','missile-shield-a3','missile-shield-b','missile-shield-c2','kinetic-dense-a','kinetic-saturation-a'} <= set(ids):
        errors.append('requiredPayloadProfiles')
    return errors


def _clone_build(matrix:CandidateMatrix, base:EcologyBuild, suffix:str, *, shield:bool|None=None, pds_family: str|None|object='KEEP', hardener:bool|None=None)->EcologyBuild:
    shield_v=base.shield if shield is None else shield
    pds_v=base.pds_family if pds_family=='KEEP' else pds_family
    hard_v=base.shield_hardener if hardener is None else hardener
    combat=build_space(matrix,base.tl,base.weapon_family,base.main_count,base.reactor_count,shield_v,base.ecm,base.eccm,pds_v,hard_v)
    cap=matrix.capacity(base.tl)
    if combat>cap: raise ValueError(f'build overflow {base.id} {suffix} {combat}>{cap}')
    return EcologyBuild(f'{base.id}-{suffix}',base.tl,f'{base.archetype}-{suffix}',base.weapon_family,base.main_count,base.reactor_count,shield_v,base.ecm,base.eccm,pds_v,hard_v,cap,combat,cap-combat)


def _target_builds(matrix:CandidateMatrix, tl:int, primary_by_id:dict[str,EcologyBuild], family:str='Energy')->dict[str,EcologyBuild]:
    fid=family.lower()
    spec='defense-specialist' if family=='Energy' else 'missile-defense'
    full=primary_by_id[f'tl{tl}-{fid}-{spec}']
    return {
        'full-defense': full,
        'no-pds': _clone_build(matrix,full,'no-pds',pds_family=None),
        'no-hardener': _clone_build(matrix,full,'no-hardener',hardener=False),
        'no-shield': _clone_build(matrix,full,'no-shield',shield=False,hardener=False),
    }


def build_variants(repo:Path, doc:dict[str,Any])->tuple[list[EcologyBuild],list[PayloadVariant]]:
    matrix=CandidateMatrix(repo); primary=generate_primary_builds(matrix); by={b.id:b for b in primary}; catalog=PayloadCatalog(doc)
    all_builds={b.id:b for b in primary}; variants=[]
    orders=(('SideAFirst','afirst'),('SideBFirst','bfirst'))

    # Missile payload characteristic space: TL4/TL5/TL7/TL9, balanced and dual-main attackers,
    # against the same Energy defense package and clean one-component target ablations.
    for tl in doc['missileStudyTls']:
        target_sets={}
        for tfam in ('Energy','Missile'):
            for tname,target in _target_builds(matrix,int(tl),by,tfam).items():
                key=f'{tfam.lower()}-{tname}'
                target_sets[key]=target; all_builds[target.id]=target
        attackers=[by[f'tl{tl}-missile-balanced'],by[f'tl{tl}-missile-dual-main']]
        payloads=[p for p in catalog.profiles.values() if p.family=='Missile' and p.min_tl<=tl and p.mode in ('fixed','adaptive','mixed')]
        for atk in attackers:
            for tname,target in target_sets.items():
                for p in sorted(payloads,key=lambda x:x.id):
                    if p.mode=='mixed' and atk.main_count<2:
                        continue
                    for order,suffix in orders:
                        vid=f'payload-missile-tl{tl}-{atk.archetype}-{p.id}-vs-{tname}-{suffix}'
                        variants.append(PayloadVariant(vid,tl,atk,target,order,p.id,'gp-current','missile_payload_characteristic',tname))

    # Kinetic ammunition characteristic space. TL4/5 exercises automatic smart-projectile accuracy;
    # TL5+ dense penetrators; TL6/7 saturation while the smart-munition accelerator family supports it.
    for tl in doc['kineticStudyTls']:
        targets=_target_builds(matrix,int(tl),by,'Energy')
        for b in targets.values(): all_builds[b.id]=b
        attackers=[by[f'tl{tl}-kinetic-balanced'],by[f'tl{tl}-kinetic-dual-main']]
        payloads=[]
        for p in catalog.profiles.values():
            if p.family!='Kinetic' or p.min_tl>tl: continue
            if p.id.startswith('kinetic-saturation') and tl not in (6,7): continue
            if p.id=='kinetic-smart-auto-plus5' and tl not in (4,5): continue
            if p.id.startswith('kinetic-dense') and tl<5: continue
            if p.id=='gp-current' or p.id.startswith('kinetic-'): payloads.append(p)
        # gp-current is Missile-family in catalog; synthesize it as a universal baseline ID.
        if not any(p.id=='gp-current' for p in payloads):
            payloads=[PayloadProfile('gp-current','Kinetic',1,'current GP control')]+payloads
        for atk in attackers:
            for tname,target in targets.items():
                for p in sorted(payloads,key=lambda x:x.id):
                    for order,suffix in orders:
                        vid=f'payload-kinetic-tl{tl}-{atk.archetype}-{p.id}-vs-{tname}-{suffix}'
                        variants.append(PayloadVariant(vid,tl,atk,target,order,p.id,'gp-current','kinetic_ammunition_characteristic',tname))

    variants.sort(key=lambda v:v.id)
    return sorted(all_builds.values(),key=lambda b:b.id),variants


def _effective_profile(base:dict[str,Any], p:PayloadProfile)->dict[str,Any]:
    if p.id=='gp-current':
        if base['family']=='Kinetic':
            return {'id':p.id,'damage':int(base['damage']),'spen':int(base['spen']),'apen':int(base['apen']),'accuracy':int(base['accuracy']),'packets':1,'shield_bonus_damage':0,'shield_armor_reduction':0,'recharge_suppression':0}
        return {'id':p.id,'damage':int(base['damage']),'spen':int(base['spen']),'apen':int(base['apen']),'accuracy':0,'packets':1,'shield_bonus_damage':0,'shield_armor_reduction':0,'recharge_suppression':0}
    bd=int(base['damage'])
    return {
        'id':p.id,
        'damage':max(0,int(p.damage if p.damage is not None else bd+p.damage_delta)),
        'spen':max(0,int(p.spen if p.spen is not None else int(base['spen'])+p.spen_delta)),
        'apen':max(0,int(p.apen if p.apen is not None else int(base['apen'])+p.apen_delta)),
        'accuracy':int(base.get('accuracy',0))+p.accuracy_delta,
        'packets':p.packets,'shield_bonus_damage':p.shield_bonus_damage,'shield_armor_reduction':p.shield_armor_reduction,'recharge_suppression':p.recharge_suppression,
    }


def _payload_for_launch(side:SideState, base:dict[str,Any], catalog:PayloadCatalog, doctrine_id:str, weapon_index:int=0)->PayloadProfile:
    p=catalog.get(doctrine_id) if doctrine_id in catalog.profiles else PayloadProfile('gp-current',base['family'],1,'current GP control')
    if p.mode=='mixed':
        specialist=catalog.get(str(p.mixed_specialist))
        specialist_slot=(weapon_index % 2 == 0) if p.mixed_order=='specialist-first' else (weapon_index % 2 == 1)
        return specialist if specialist_slot else PayloadProfile('gp-current',base['family'],1,'current GP control')
    if p.mode!='adaptive': return p
    specialist=catalog.get(str(p.adaptive_specialist))
    use_specialist=(side.observed_shield_absorption and side.observed_no_penetration_streak>=p.assessment_failures_before_switch and not side.observed_no_shield_effect_latest and not side.observed_hull_penetration)
    chosen=specialist if use_specialist else PayloadProfile('gp-current',base['family'],1,'current GP control')
    last=side.last_payload_id
    if last and last!=chosen.id: side.telemetry.payload_switches+=1
    side.last_payload_id=chosen.id
    return chosen


def _observe_resolution(observer:SideState, result:dict[str,int], firm:bool)->None:
    if not firm: return
    shield_effect=(result.get('shield_armor_prevented',0)+result.get('shield_absorbed',0)+result.get('shield_bonus_damage',0))>0
    armor_contact=(result.get('armor_prevented',0)+result.get('armor_integrity',0)+result.get('armor_protection',0))>0
    hull=result.get('hull',0)>0
    if shield_effect:
        if not observer.observed_shield_absorption: observer.telemetry.assessment_shield_absorption_observed+=1
        observer.observed_shield_absorption=True
        observer.observed_no_shield_effect_latest=False
    elif armor_contact or hull:
        if not observer.observed_no_shield_effect_latest: observer.telemetry.assessment_shield_absent_observed+=1
        observer.observed_no_shield_effect_latest=True
    if armor_contact:
        if not observer.observed_armor_contact: observer.telemetry.assessment_armor_contact_observed+=1
        observer.observed_armor_contact=True
    if hull:
        if not observer.observed_hull_penetration: observer.telemetry.assessment_hull_penetration_observed+=1
        observer.observed_hull_penetration=True
    armor_damage=(result.get('armor_integrity',0)+result.get('armor_protection',0))>0
    if shield_effect and not armor_damage and not hull:
        observer.observed_no_penetration_streak+=1
        observer.telemetry.assessment_no_penetration_observed+=1
    elif armor_damage or hull or observer.observed_no_shield_effect_latest:
        observer.observed_no_penetration_streak=0


def _apply_payload_hit(target:SideState, prof:dict[str,Any], shield_armor:int, source:str)->dict[str,int]:
    total={'shield_armor_prevented':0,'shield_absorbed':0,'armor_prevented':0,'armor_integrity':0,'armor_protection':0,'hull':0,'shield_bonus_damage':0}
    bonus=min(target.shield,int(prof.get('shield_bonus_damage',0)))
    if bonus:
        target.shield-=bonus
        target.telemetry.shield_absorbed+=bonus
        target.telemetry.payload_shield_bonus_damage+=bonus
        total['shield_absorbed']+=bonus; total['shield_bonus_damage']+=bonus
    effective_shield_armor=max(0,shield_armor-int(prof.get('shield_armor_reduction',0)))
    for _ in range(max(1,int(prof.get('packets',1)))):
        r=_apply_damage(target,int(prof['damage']),int(prof['spen']),int(prof['apen']),effective_shield_armor,source)
        for k in ('shield_armor_prevented','shield_absorbed','armor_prevented','armor_integrity','armor_protection','hull'): total[k]+=int(r[k])
    if int(prof.get('recharge_suppression',0))>0 and (total['shield_armor_prevented']+total['shield_absorbed']+total['shield_bonus_damage'])>0:
        target.recharge_suppression_pending=max(target.recharge_suppression_pending,int(prof['recharge_suppression']))
    return total


def run_payload_trial(matrix:CandidateMatrix,catalog:PayloadCatalog,variant:PayloadVariant,master_seed:int,trial_index:int)->PayloadTrialResult:
    try:
        a=_create_side(matrix,variant.side_a,variant.start_q_a); b=_create_side(matrix,variant.side_b,variant.start_q_b)
        rng=XorShift64(derive_seed(master_seed,variant.id,trial_index)); missiles:list[PayloadMissileState]=[]
        for turn in range(1,variant.max_turns+1):
            inbound_a=sum(m.owner=='B' for m in missiles); inbound_b=sum(m.owner=='A' for m in missiles)
            power_a,_=_begin_turn_recharge(matrix,a,b,inbound_a); power_b,_=_begin_turn_recharge(matrix,b,a,inbound_b)
            if variant.movement_order=='SideAFirst':
                _move_one(a,b,matrix,a.contact); _move_one(b,a,matrix,b.contact)
            else:
                _move_one(b,a,matrix,b.contact); _move_one(a,b,matrix,a.contact)
            rhex=_range(a,b)
            pre_a=_plan_once(matrix,a,b,rhex,inbound_a,power_a,False); pre_b=_plan_once(matrix,b,a,rhex,inbound_b,power_b,False)
            ecm_a=pre_a['ecm_on']; ecm_b=pre_b['ecm_on']
            pa,_=_maybe_reactor_overload(matrix,a,b,rhex,inbound_a,power_a,ecm_b); pb,_=_maybe_reactor_overload(matrix,b,a,rhex,inbound_b,power_b,ecm_a)
            _record_plan(a,pa,power_a,inbound_a); _record_plan(b,pb,power_b,inbound_b)
            a.last_track=pa['track']; b.last_track=pb['track']; a.contact|=pa['track']!='None'; b.contact|=pb['track']!='None'
            direct=[]
            for label,side,target,plan,doctrine in (('A',a,b,pa,variant.side_a_payload),('B',b,a,pb,variant.side_b_payload)):
                w=_weapon(matrix,side.build)
                if w['family']=='Missile':
                    if plan['track']=='Firm' and rhex<=int(w['range']):
                        for weapon_index,wp in enumerate(plan['weapon_plans']):
                            if wp is None: continue
                            if side.weapon_ammo is not None and side.weapon_ammo<=0: continue
                            if side.weapon_ammo is not None: side.weapon_ammo-=1
                            pp=_payload_for_launch(side,w,catalog,doctrine,weapon_index); eff=_effective_profile(w,pp)
                            if pp.id=='gp-current': side.telemetry.payload_gp_launches+=1
                            else: side.telemetry.payload_specialist_launches+=1
                            eta=max(1,math.ceil(rhex/max(1,int(w['missile_move']))))
                            missiles.append(PayloadMissileState(label,eta,int(w['guidance']),pp.id,eff['damage'],eff['spen'],eff['apen'],eff['packets'],eff['shield_bonus_damage'],eff['shield_armor_reduction'],eff['recharge_suppression']))
                            side.telemetry.missile_launches+=1; side.demonstrated_range=max(side.demonstrated_range,rhex)
                    continue
                if plan['track']!='Firm' or rhex>int(w['range']): continue
                for wp in plan['weapon_plans']:
                    if wp is None: continue
                    if side.weapon_ammo is not None and side.weapon_ammo<=0: continue
                    if side.weapon_ammo is not None: side.weapon_ammo-=1
                    if w['family']=='Energy':
                        _,wp_damage,wp_accuracy=wp
                        pp=PayloadProfile('gp-current','Energy',1,'energy mode control')
                        eff={'id':'gp-current','damage':int(wp_damage),'spen':int(w['spen']),'apen':int(w['apen']),'accuracy':int(wp_accuracy),'packets':1,'shield_bonus_damage':0,'shield_armor_reduction':0,'recharge_suppression':0}
                    else:
                        pp=catalog.get(doctrine) if doctrine in catalog.profiles else PayloadProfile('gp-current','Kinetic',1,'control')
                        eff=_effective_profile(w,pp)
                    chance=_hit_chance(matrix,side.build,rhex,eff['accuracy']); hit=rng.d100()<=chance
                    side.telemetry.direct_shots+=1
                    if w['family']=='Kinetic' and pp.id!='gp-current': side.telemetry.kinetic_specialist_shots+=1
                    if hit: side.telemetry.direct_hits+=1
                    direct.append((side,target,plan,hit,eff))
                    side.demonstrated_range=max(side.demonstrated_range,rhex)
            for shooter,target,plan,hit,eff in direct:
                if hit:
                    res=_apply_payload_hit(target,eff,_shield_armor(matrix,target,bool((pb if shooter is a else pa)['hardener_active'])),'direct')
                    _observe_resolution(shooter,res,shooter.last_track=='Firm'); target.contact=True

            for m in missiles: m.eta-=1
            terminal=[m for m in missiles if m.eta<=0]
            if terminal:
                for target_label,target,plan,shooter in (('A',a,pa,b),('B',b,pb,a)):
                    threats=[m for m in terminal if m.owner!=target_label]; reaction_used=0; intercepted=set(); pds=plan['pds']
                    for m in threats:
                        target.telemetry.missile_terminal_arrivals+=1; attempts=0
                        while reaction_used<int(plan['pds_rc']) and attempts<2:
                            if target.pds_ammo is not None and target.pds_ammo<=0: break
                            target.telemetry.pds_attempts+=1; reaction_used+=1; attempts+=1
                            if target.pds_ammo is not None: target.pds_ammo-=1
                            chance=0 if pds is None else min(95,int(pds['baseChancePp'])+int(matrix.p('computer',target.build.tl)['targetingPp']))
                            if rng.d100()<=chance:
                                target.telemetry.pds_intercepts+=1; intercepted.add(id(m)); break
                        if id(m) in intercepted: continue
                        target.telemetry.missile_guidance_attempts+=1
                        if rng.d100()<=int(m.guidance):
                            target.telemetry.missile_hits+=1
                            eff={'damage':m.damage,'spen':m.spen,'apen':m.apen,'packets':m.packets,'shield_bonus_damage':m.shield_bonus_damage,'shield_armor_reduction':m.shield_armor_reduction,'recharge_suppression':m.recharge_suppression}
                            res=_apply_payload_hit(target,eff,_shield_armor(matrix,target,bool(plan['hardener_active'])),'missile')
                            _observe_resolution(shooter,res,shooter.last_track=='Firm'); target.contact=True
                missiles=[m for m in missiles if m.eta>0]
            if a.hull<=0 or b.hull<=0:
                winner='Draw' if a.hull<=0 and b.hull<=0 else ('B' if a.hull<=0 else 'A')
                return PayloadTrialResult(winner,False,turn,a.hull,b.hull,a.armor_integrity,b.armor_integrity,a.shield,b.shield,a.telemetry,b.telemetry)
        return PayloadTrialResult('Unresolved',True,variant.max_turns,a.hull,b.hull,a.armor_integrity,b.armor_integrity,a.shield,b.shield,a.telemetry,b.telemetry)
    except Exception as exc:
        blank=SideTelemetry(); return PayloadTrialResult('Error',False,0,0,0,0,0,0,0,blank,blank,f'{type(exc).__name__}: {exc}')


_WORKER_MATRIX:CandidateMatrix|None=None
_WORKER_CATALOG:PayloadCatalog|None=None

def _init_worker(repo:str,doc:dict[str,Any]):
    global _WORKER_MATRIX,_WORKER_CATALOG
    _WORKER_MATRIX=CandidateMatrix(Path(repo)); _WORKER_CATALOG=PayloadCatalog(doc)

def _mean(results:list[PayloadTrialResult],side:str,name:str)->float:
    vals=[getattr(r.side_a if side=='a' else r.side_b,name) for r in results if not r.error]
    return statistics.fmean(vals) if vals else 0.0

def _aggregate(v:PayloadVariant,results:list[PayloadTrialResult])->dict[str,Any]:
    n=len(results); wins={k:sum(r.winner==k for r in results) for k in ('A','B','Draw','Unresolved','Error')}
    valid=[r for r in results if not r.error]
    row={'variant_id':v.id,'tl':v.tl,'scenario_group':v.scenario_group,'target_profile':v.target_profile,'movement_order':v.movement_order,
         'side_a_build':v.side_a.id,'side_b_build':v.side_b.id,'side_a_family':v.side_a.weapon_family,'side_b_family':v.side_b.weapon_family,
         'side_a_archetype':v.side_a.archetype,'side_b_archetype':v.side_b.archetype,
         'side_a_payload':v.side_a_payload,'side_b_payload':v.side_b_payload,'trials':n,'wins_a':wins['A'],'wins_b':wins['B'],'draws':wins['Draw'],'unresolved':wins['Unresolved'],'errors':wins['Error'],
         'conditional_win_rate_a':wins['A']/max(1,wins['A']+wins['B']),'unresolved_rate':wins['Unresolved']/n if n else 0.0,
         'mean_turns':statistics.fmean(r.turns for r in valid) if valid else 0.0,'mean_final_hull_a':statistics.fmean(r.hull_a for r in valid) if valid else 0.0,'mean_final_hull_b':statistics.fmean(r.hull_b for r in valid) if valid else 0.0}
    for side in ('a','b'):
        for f in fields(SideTelemetry): row[f'mean_{side}_{f.name}']=_mean(results,side,f.name)
    return row

def _task(args):
    v,seed,trials=args
    assert _WORKER_MATRIX is not None and _WORKER_CATALOG is not None
    return _aggregate(v,[run_payload_trial(_WORKER_MATRIX,_WORKER_CATALOG,v,seed,i) for i in range(trials)])

def _chunk(args):
    vs,seed,trials=args; return [_task((v,seed,trials)) for v in vs]

def execute(repo:Path,doc:dict[str,Any],variants:list[PayloadVariant],trials:int,jobs:int)->tuple[list[dict[str,Any]],float]:
    jobs=max(1,min(jobs,len(variants))); start=time.perf_counter(); rows=[]
    if jobs==1:
        _init_worker(str(repo),doc); rows=[_task((v,int(doc['masterSeed']),trials)) for v in variants]
    else:
        chunks=[[] for _ in range(min(len(variants),max(jobs,jobs*4)))]
        for i,v in enumerate(variants): chunks[i%len(chunks)].append(v)
        ctx=get_context('spawn')
        with ProcessPoolExecutor(max_workers=jobs,mp_context=ctx,initializer=_init_worker,initargs=(str(repo),doc)) as ex:
            fut=[ex.submit(_chunk,(c,int(doc['masterSeed']),trials)) for c in chunks if c]
            for f in as_completed(fut): rows.extend(f.result())
    rows.sort(key=lambda r:r['variant_id']); return rows,time.perf_counter()-start

def _write_csv(path:Path,rows:Iterable[dict[str,Any]]):
    rows=list(rows); path.parent.mkdir(parents=True,exist_ok=True)
    if not rows: path.write_text('',encoding='utf-8'); return
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

def _summary(rows:list[dict[str,Any]],group:str)->list[dict[str,Any]]:
    d=defaultdict(list)
    for r in rows:
        if r['scenario_group']==group: d[(int(r['tl']),r['side_a_payload'],r['target_profile'],r['side_a_archetype'])].append(r)
    out=[]
    for (tl,payload,target,attacker),rs in sorted(d.items()):
        out.append({'tl':tl,'payload':payload,'target_profile':target,'attacker_archetype':attacker,'variants':len(rs),
                    'mean_conditional_win_rate':statistics.fmean(float(x['conditional_win_rate_a']) for x in rs),
                    'mean_unresolved_rate':statistics.fmean(float(x['unresolved_rate']) for x in rs),
                    'mean_hits':statistics.fmean(float(x['mean_b_missile_hits'] if group.startswith('missile') else x['mean_a_direct_hits']) for x in rs),
                    'mean_target_shield_absorbed':statistics.fmean(float(x['mean_b_shield_absorbed']) for x in rs),
                    'mean_target_recharge_suppressed':statistics.fmean(float(x['mean_b_shield_recharge_suppressed']) for x in rs),
                    'mean_target_armor_damage':statistics.fmean(float(x['mean_b_armor_integrity_damage']) for x in rs),
                    'mean_target_hull_damage':statistics.fmean(float(x['mean_b_hull_damage']) for x in rs),
                    'mean_payload_switches':statistics.fmean(float(x['mean_a_payload_switches']) for x in rs)})
    return out

def run_payload_analysis(repo:Path,study_path:Path,outdir:Path,trials_override:int|None=None,jobs:int=1)->dict[str,Any]:
    doc=load_json(study_path); errs=validate_study(doc)
    if errs: raise ValueError('invalid CP114 study: '+','.join(errs))
    builds,variants=build_variants(repo,doc); trials=int(trials_override or doc['trialsPerVariant'])
    rows,elapsed=execute(repo,doc,variants,trials,jobs); outdir.mkdir(parents=True,exist_ok=True)
    _write_csv(outdir/'variants.csv',rows)
    _write_csv(outdir/'builds.csv',[{'build_id':b.id,'tl':b.tl,'family':b.weapon_family,'archetype':b.archetype,'combat_space':b.combat_space,'mission_aux_space':b.mission_aux_space,'capacity':b.capacity,'used_space':b.used_space,'free_space':b.capacity-b.used_space} for b in builds])
    ms=_summary(rows,'missile_payload_characteristic'); ks=_summary(rows,'kinetic_ammunition_characteristic')
    _write_csv(outdir/'missile_payload_summary.csv',ms); _write_csv(outdir/'kinetic_ammunition_summary.csv',ks)
    failures=[]
    if any(int(r['errors']) for r in rows): failures.append('trial-errors')
    if any(b.used_space!=b.capacity for b in builds): failures.append('exact-fill')
    if not any(float(r['mean_b_payload_shield_bonus_damage'])>0 for r in rows): failures.append('shield-bonus-telemetry')
    if not any(float(r['mean_b_shield_recharge_suppressed'])>0 for r in rows): failures.append('recharge-suppression-telemetry')
    if trials>=50 and not any(float(r['mean_a_payload_switches'])>0 for r in rows if str(r['side_a_payload']).startswith('missile-adaptive')): failures.append('adaptive-switch-telemetry')
    if not any(float(r['mean_a_kinetic_specialist_shots'])>0 for r in rows if r['scenario_group']=='kinetic_ammunition_characteristic'): failures.append('kinetic-specialist-telemetry')
    analysis={'schemaVersion':'star-cluster-payload-characteristic-space-results-v0.1','checkpoint':114,'damageModel':DAMAGE_MODEL,'internalDamageCriticalsSimulated':False,
              'trialsPerVariant':trials,'variants':len(variants),'totalTrials':len(variants)*trials,'elapsedSeconds':elapsed,'failedGates':failures,'automaticPromotion':False,
              'missilePayloadSummary':ms,'kineticAmmunitionSummary':ks,
              'interpretation':'Exploratory characteristic-space evidence only. Payload profiles are simulation-only candidates; no CP109/CP110 production/candidate number or C#/Godot runtime value is promoted by CP114.'}
    (outdir/'analysis.json').write_text(json.dumps(analysis,indent=2)+'\n',encoding='utf-8')
    return analysis
