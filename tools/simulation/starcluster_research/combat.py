from __future__ import annotations
import math
from pathlib import Path
from typing import Any
from .model import Build, SideState, Missile, TrialResult, Variant
from .rng import XorShift64, derive_seed
from .study import load_json
from .canonical_mechanics import resolve_layered_damage

MAX_TURNS=60
MAX_RANGE=10


class CombatData:
    def __init__(self, repo:Path):
        catalog=load_json(repo/'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/tl1-tl3-standard-runtime-profiles-v0_4.json')
        self.profiles={p['id']:p for p in catalog['profiles']}
        self.profile_by_tl={1:self.profiles['tl1-production'],2:self.profiles['tl2-cp102-integration-reference'],3:self.profiles['tl3-cp102-executable-candidate']}
        sensor=load_json(repo/'src/StarCluster.ScenarioRunner/Scenarios/SensorEw/tl2-sew01-sensor-discrimination-isolation.json')
        self.sensor_profiles={p['id']:p for p in sensor['candidates']}

    def profile_for_tl(self,tl:int):
        return self.profile_by_tl[min(3,max(1,tl))]


def _opt(build:Build,axis:str): return build.option_payloads[axis]

def _weapon(build:Build,data:CombatData):
    o=_opt(build,'weapon'); p=data.profile_for_tl(o['technologyLevel'])['weapons'][o['family'].lower()]
    def val(k,default=None): return o[k] if k in o and o[k] is not None else p.get(k,default)
    return {
        'family':o['family'],'count':int(o.get('mainWeaponCount',1) or 1),'damage':int(val('damage',0)),'spen':int(val('shieldPenetration',0)),
        'apen':int(val('armorPenetration',0)),'accuracy':int(val('accuracyBonus',0)),'range':int(val('maximumRange',0)),
        'power':int(val('powerCost',0)),'ammo':val('ammunition'), 'missile_move':int(val('missileMove',data.profile_for_tl(o['technologyLevel'])['movement'].get('missileMove',2))),
        'guidance':int(p.get('guidanceChance',55)),
        'high_damage':o.get('preferredSmokeModeDamage'),'high_power':o.get('preferredSmokeModePowerCost'),'high_accuracy':o.get('preferredSmokeModeAccuracyBonus'),
    }


def _sensor(build:Build,data:CombatData):
    o=_opt(build,'sensor'); base=data.sensor_profiles.get(o.get('sensorEwProfileId',''),{})
    return {
        'passive_firm':int(o.get('passiveFirmRange',base.get('passiveFirmRange',1))),
        'passive_approx':int(o.get('passiveApproximateRange',base.get('passiveApproximateRange',3))),
        'low_firm':int(o.get('activeLowFirmRange',base.get('activeFirmRange',3))),
        'low_approx':int(o.get('activeLowApproximateRange',base.get('activeApproximateRange',4))),
        'low_power':int(o.get('activeLowPowerCost',base.get('activePowerCost',1))),
        'high_firm':o.get('activeHighFirmRange'),'high_approx':o.get('activeHighApproximateRange'),'high_power':o.get('activeHighPowerCost'),
        'dr':int(base.get('discriminationResistance',0)),'burn':int(base.get('pointBlankBurnThroughResistance',0)),
    }


def _ew(build:Build,axis:str):
    o=_opt(build,axis); ratings=o.get('ewRatings') or ([] if o.get('ewRating') is None else [o['ewRating']])
    rating=max(ratings) if ratings else 0
    full=o.get('ewFullStrengthNormalPowerCost')
    cost=int(full if full is not None else rating*int(o.get('ewNormalPowerCost',1))) if rating else 0
    return rating,cost


def _reactor_power(build:Build):
    o=_opt(build,'reactor'); return int(o.get('reactorOutput',5))*int(o.get('reactorCount',1) or 1)


def _pds(build:Build):
    o=_opt(build,'pds')
    if o.get('installed',False) is False or int(o.get('pdsCount',0) or 0)==0: return None
    return {'family':o.get('pdsFamily','Kinetic'),'chance':int(o.get('pdsBaseChance',0)),'power':int(o.get('pdsPowerCost',0) or 0),'rc':int(o.get('pdsReactionCapacity',1) or 1),
            'fallback_power':o.get('pdsFallbackPowerCost'),'fallback_rc':o.get('pdsFallbackReactionCapacity'),'ammo':o.get('pdsAmmunition')}


def _targeting(build:Build,data:CombatData):
    o=_opt(build,'computer'); return int(o.get('targetingBonus',data.profile_for_tl(o['technologyLevel'])['powerAndControl']['targetingBonus']))


def _shield(build:Build,data:CombatData):
    o=_opt(build,'shield'); p=data.profile_for_tl(build.max_tl)['defense']; cap=int(o.get('shieldCapacity',p.get('shieldCapacity',0))) if o.get('installed',True) is not False else 0
    return cap,int(p.get('shieldBaseRecharge',1))


def _armor(build:Build,data:CombatData):
    o=_opt(build,'armor'); p=data.profile_for_tl(o['technologyLevel'])['defense']; return int(o.get('armorIntegrity',p.get('armorIntegrity',0))),int(o.get('armorProtection',p.get('armorProtection',0)))


def _hull(build:Build,data:CombatData): return int(data.profile_for_tl(build.max_tl)['defense'].get('hull',12))

def _move(build:Build,data:CombatData):
    o=_opt(build,'stl'); return int(o.get('normalMove',data.profile_for_tl(o['technologyLevel'])['movement'].get('shipMove',1)))


def _hardener(build:Build):
    o=_opt(build,'shieldHardener'); return (o.get('installed',False) is True,int(o.get('shieldArmorBonus',0) or 0),int(o.get('sustainedPowerCost',0) or 0))


def create_side(build:Build,data:CombatData) -> SideState:
    w=_weapon(build,data); sh,rech=_shield(build,data); ai,ap=_armor(build,data); pds=_pds(build)
    return SideState(build,_hull(build,data),ai,ap,sh,sh,rech,None if w['ammo'] is None else int(w['ammo'])*w['count'],None if pds is None or pds['ammo'] is None else int(pds['ammo']))


def sensor_track(build:Build,target:Build,data:CombatData,range_hex:int,available_power:int,prefer_high=True):
    s=_sensor(build,data); own_eccm,eccm_cost=_ew(build,'eccm'); target_ecm,_=_ew(target,'ecm')
    power=available_power; eccm_on=own_eccm>0 and power>=eccm_cost
    eccm=own_eccm if eccm_on else 0
    if eccm_on: power-=eccm_cost
    modes=[]
    if s['high_firm'] is not None and s['high_power'] is not None: modes.append(('high',int(s['high_firm']),int(s['high_approx']),int(s['high_power'])))
    modes.append(('low',s['low_firm'],s['low_approx'],s['low_power']))
    chosen=None
    # choose cheapest normal mode that reaches firm; if none, strongest affordable mode
    firm_candidates=[m for m in modes if range_hex<=m[1] and power>=m[3]]
    if firm_candidates: chosen=min(firm_candidates,key=lambda m:m[3])
    else:
        affordable=[m for m in modes if power>=m[3]]
        if affordable: chosen=max(affordable,key=lambda m:(m[1],-m[3]))
    if chosen is None:
        firm=s['passive_firm']; approx=s['passive_approx']; mode='passive'; cost=0
    else:
        mode,firm,approx,cost=chosen; power-=cost
    base='Firm' if range_hex<=firm else 'Approximate' if range_hex<=approx else 'None'
    net=max(0,target_ecm-eccm); resistance=s['dr']+(s['burn'] if range_hex==0 else 0)
    if base=='Firm' and net>resistance: base='Approximate'
    return base,mode,cost+(eccm_cost if eccm_on else 0),eccm_on


def max_ready_range(build:Build,target:Build,data:CombatData):
    w=_weapon(build,data); power=_reactor_power(build)
    for r in range(w['range'],-1,-1):
        track,_,_,_=sensor_track(build,target,data,r,power)
        if track=='Firm': return r
    return 0


def direct_hit_chance(build:Build,data:CombatData,range_hex:int,weapon_accuracy:int|None=None):
    w=_weapon(build,data); acc=w['accuracy'] if weapon_accuracy is None else weapon_accuracy
    return max(5,min(95,50+acc+_targeting(build,data)-5*range_hex))


def apply_damage(state:SideState,damage:int,spen:int,apen:int,shield_armor:int=0):
    result=resolve_layered_damage(
        shield=state.shield,armor_integrity=state.armor_integrity,
        armor_protection=state.armor_protection,hull=state.hull,
        damage=damage,spen=spen,apen=apen,shield_armor=shield_armor)
    state.shield=result.final_shield
    state.armor_integrity=result.final_armor_integrity
    state.hull=result.final_hull
    return {
        'shield_absorb':result.shield_absorbed,
        'shield_prevented':result.shield_penetration_resisted,
        'shield_bypass':result.shield_bypass,
        'armor_prevented':result.armor_penetration_resisted,
        'armor_integrity':result.armor_absorbed,
        'armor_protection':0,
        'armor_bypass':result.armor_bypass,
        'hull':result.hull_damage,
    }


def _weapon_plan(build:Build,data:CombatData,remaining:int):
    w=_weapon(build,data); plans=[]
    for _ in range(w['count']):
        if w['family']=='Energy' and w['high_power'] is not None:
            hp=int(w['high_power']); hd=int(w['high_damage']); ha=int(w['high_accuracy'] or w['accuracy'])
            if remaining>=hp: plans.append((hp,hd,ha)); remaining-=hp; continue
            if remaining>=w['power']: plans.append((w['power'],w['damage'],w['accuracy'])); remaining-=w['power']; continue
            if remaining>=1: plans.append((1,max(1,w['damage']-1),w['accuracy'])); remaining-=1; continue
            plans.append(None)
        else:
            if remaining>=w['power']: plans.append((w['power'],w['damage'],w['accuracy'])); remaining-=w['power']
            else: plans.append(None)
    return plans,remaining


def _support_plan(side:SideState,target:SideState,data:CombatData,range_hex:int,inbound:int):
    build=side.build; total=_reactor_power(build); rem=total
    # ECCM first when jamming exists; sensor next; ECM defense next; PDS/hardener then weapons.
    tr,mode,sensor_eccm_cost,eccm_on=sensor_track(build,target.build,data,range_hex,rem)
    if sensor_eccm_cost<=rem: rem-=sensor_eccm_cost
    else: tr,mode,sensor_eccm_cost,eccm_on='None','passive',0,False
    ecm_rating,ecm_cost=_ew(build,'ecm'); ecm_on=ecm_rating>0 and rem>=ecm_cost
    if ecm_on: rem-=ecm_cost
    hard_on,hard_armor,hard_cost=_hardener(build); hard_active=hard_on and side.shield>0 and rem>=hard_cost
    if hard_active: rem-=hard_cost
    pds=_pds(build); pds_rc=0; pds_power=0
    if inbound and pds:
        if rem>=pds['power']:
            pds_power=pds['power']; pds_rc=pds['rc']; rem-=pds_power
        elif pds['fallback_power'] is not None and rem>=int(pds['fallback_power']):
            pds_power=int(pds['fallback_power']); pds_rc=int(pds['fallback_rc']); rem-=pds_power
    weapon_plans,after=_weapon_plan(build,data,rem)
    desired_weapon=sum((x[0] if x else _weapon(build,data)['power']) for x in weapon_plans if x is not None)
    if any(x is None for x in weapon_plans): side.power_shortfall_events+=1
    spent=total-after; side.power_spent_total+=spent
    if mode!='passive': side.active_sensor_turns+=1
    if mode=='high': side.high_sensor_turns+=1
    if tr=='Firm': side.firm_track_turns+=1
    return {'track':tr,'sensor_mode':mode,'ecm_on':ecm_on,'hard_active':hard_active,'hard_armor':hard_armor if hard_active else 0,'pds_rc':pds_rc,'pds':pds,'weapon_plans':weapon_plans,'power_remaining':after,'total_power':total,'power_spent':spent}


def _move_order(build:Build,target:Build,data:CombatData,range_hex:int,own_demonstrated:int,opp_demonstrated:int):
    ready=max_ready_range(build,target,data); w=_weapon(build,data)
    if range_hex>ready: return 'close',ready
    if own_demonstrated>opp_demonstrated and own_demonstrated>range_hex: return 'open',min(own_demonstrated,w['range'])
    return 'hold',range_hex


def _apply_move(range_hex:int,order:str,desired:int,move:int):
    if order=='close': return max(desired,range_hex-move)
    if order=='open': return min(MAX_RANGE,max(desired,range_hex+move))
    return range_hex


def run_trial(variant:Variant,data:CombatData,master_seed:int,trial_index:int) -> TrialResult:
    try:
        a=create_side(variant.side_a,data); b=create_side(variant.side_b,data); rng=XorShift64(derive_seed(master_seed,variant.id,trial_index))
        missiles=[]; range_hex=variant.initial_range; demo_a=demo_b=opp_a=opp_b=0
        for turn in range(1,MAX_TURNS+1):
            if a.shield<a.shield_max: a.shield=min(a.shield_max,a.shield+a.shield_recharge)
            if b.shield<b.shield_max: b.shield=min(b.shield_max,b.shield+b.shield_recharge)
            oa,da=_move_order(a.build,b.build,data,range_hex,demo_a,opp_a); ob,db=_move_order(b.build,a.build,data,range_hex,demo_b,opp_b)
            if variant.movement_order=='SideAFirst':
                range_hex=_apply_move(range_hex,oa,da,_move(a.build,data)); range_hex=_apply_move(range_hex,ob,db,_move(b.build,data))
            else:
                range_hex=_apply_move(range_hex,ob,db,_move(b.build,data)); range_hex=_apply_move(range_hex,oa,da,_move(a.build,data))
            inbound_a=sum(m.owner=='B' for m in missiles); inbound_b=sum(m.owner=='A' for m in missiles)
            pa=_support_plan(a,b,data,range_hex,inbound_a); pb=_support_plan(b,a,data,range_hex,inbound_b)
            # simultaneous direct fire commitments
            commits=[]
            for label,side,target,plan in [('A',a,b,pa),('B',b,a,pb)]:
                w=_weapon(side.build,data)
                if w['family']=='Missile':
                    if plan['track']=='Firm' and range_hex<=w['range']:
                        for wp in plan['weapon_plans']:
                            if wp is None: continue
                            if side.weapon_ammo is not None and side.weapon_ammo<=0: continue
                            if side.weapon_ammo is not None: side.weapon_ammo-=1
                            eta=max(1,math.ceil(range_hex/max(1,w['missile_move'])))
                            missiles.append(Missile(label,eta,w['damage'],w['spen'],w['apen'],w['guidance'])); side.missiles_launched+=1
                            if label=='A': demo_a=max(demo_a,range_hex); opp_b=max(opp_b,range_hex)
                            else: demo_b=max(demo_b,range_hex); opp_a=max(opp_a,range_hex)
                    continue
                if plan['track']!='Firm' or range_hex>w['range']: continue
                for wp in plan['weapon_plans']:
                    if wp is None: continue
                    if side.weapon_ammo is not None and side.weapon_ammo<=0: continue
                    cost,damage,acc=wp
                    if side.weapon_ammo is not None: side.weapon_ammo-=1
                    chance=direct_hit_chance(side.build,data,range_hex,acc); roll=rng.d100(); side.direct_shots+=1
                    hit=roll<=chance
                    if hit: side.direct_hits+=1
                    commits.append((label,target,hit,damage,w['spen'],w['apen'],pa['hard_armor'] if label=='B' else pb['hard_armor']))
                    if label=='A': demo_a=max(demo_a,range_hex); opp_b=max(opp_b,range_hex)
                    else: demo_b=max(demo_b,range_hex); opp_a=max(opp_a,range_hex)
            for label,target,hit,damage,spen,apen,target_hard in commits:
                if hit: apply_damage(target,damage,spen,apen,target_hard)
            # advance missiles after both sides have fired; terminal PDS is per target and capped by allocated RC.
            terminal=[]
            for m in missiles:
                m.eta-=1
                if m.eta<=0: terminal.append(m)
            if terminal:
                remaining=[]
                for target_label,target,plan in [('A',a,pa),('B',b,pb)]:
                    threats=[m for m in terminal if m.owner!=target_label]
                    rc=plan['pds_rc']; pds=plan['pds']; intercepted=set()
                    reaction_used=0
                    for idx,m in enumerate(threats):
                        attempts_on_flight=0
                        while reaction_used < rc and attempts_on_flight < 2:
                            if target.pds_ammo is not None and target.pds_ammo<=0: break
                            target.pds_attempts+=1; reaction_used+=1; attempts_on_flight+=1
                            if target.pds_ammo is not None: target.pds_ammo-=1
                            chance=min(95,(pds['chance'] if pds else 0)+_targeting(target.build,data))
                            if rng.d100()<=chance:
                                target.pds_intercepts+=1; intercepted.add(id(m)); break
                        if id(m) in intercepted: continue
                        if rng.d100()<=m.guidance:
                            apply_damage(target,m.damage,m.spen,m.apen,plan['hard_armor'])
                            if m.owner=='A': a.missile_hits+=1
                            else: b.missile_hits+=1
                    # only nonterminal missiles remain globally
                missiles=[m for m in missiles if m.eta>0]
            if a.hull<=0 or b.hull<=0:
                winner='Draw' if a.hull<=0 and b.hull<=0 else 'B' if a.hull<=0 else 'A'
                return TrialResult(winner,turn,range_hex,a.hull,b.hull,a.direct_shots,b.direct_shots,a.missiles_launched,b.missiles_launched,a.pds_attempts,b.pds_attempts,a.power_shortfall_events,b.power_shortfall_events,a.firm_track_turns,b.firm_track_turns)
        # unresolved: score remaining layered defense only to classify decisive attrition; narrow ties remain Draw.
        score_a=a.hull+a.armor_integrity+a.shield; score_b=b.hull+b.armor_integrity+b.shield
        winner='A' if score_a>score_b+2 else 'B' if score_b>score_a+2 else 'Draw'
        return TrialResult(winner,MAX_TURNS,range_hex,a.hull,b.hull,a.direct_shots,b.direct_shots,a.missiles_launched,b.missiles_launched,a.pds_attempts,b.pds_attempts,a.power_shortfall_events,b.power_shortfall_events,a.firm_track_turns,b.firm_track_turns)
    except Exception as exc:
        return TrialResult('Error',0,variant.initial_range,0,0,0,0,0,0,0,0,0,0,0,0,f'{type(exc).__name__}: {exc}')
