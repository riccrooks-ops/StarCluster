from __future__ import annotations

import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from .ecology import (
    CandidateMatrix, EcologyBuild, EcologyVariant, build_space, execute_variants,
    generate_primary_builds, _write_csv,
)
from .study import load_json

SCHEMA = 'star-cluster-build-neighbor-ablation-v0.1'
CHECKPOINT = '112'


def validate_study(doc: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if doc.get('schemaVersion') != SCHEMA: errors.append('schemaVersion')
    if doc.get('checkpoint') != CHECKPOINT: errors.append('checkpoint')
    if doc.get('damageModel') != 'layered_defense_hull_only': errors.append('damageModel')
    if doc.get('internalDamageCriticalsSimulated') is not False: errors.append('internalDamageCriticalsSimulated')
    trials = doc.get('trialsPerVariant')
    if not isinstance(trials, int) or isinstance(trials, bool) or trials < 1: errors.append('trialsPerVariant')
    if doc.get('automaticPromotion') is not False: errors.append('automaticPromotion')
    if doc.get('mixedTlPopulation', {}).get('executed') is not False: errors.append('mixedTlPopulation.executed')
    return errors


def _branch_space(matrix: CandidateMatrix, branch_id: str) -> int:
    return int(matrix.branches[branch_id]['space'])


def make_build(matrix: CandidateMatrix, *, tl: int, family: str, archetype: str,
               main_count: int = 1, reactor_count: int = 1, shield: bool = False,
               ecm: bool = False, eccm: bool = False, pds_family: str | None = None,
               hardener: bool = False, ident: str | None = None) -> EcologyBuild:
    combat = build_space(matrix, tl, family, main_count, reactor_count, shield, ecm, eccm, pds_family, hardener)
    cap = matrix.capacity(tl)
    if combat > cap:
        raise ValueError(f'illegal build {ident or archetype}: {combat}>{cap}')
    return EcologyBuild(
        ident or f'tl{tl}-{family.lower()}-{archetype}', tl, archetype, family,
        main_count, reactor_count, shield, ecm, eccm, pds_family, hardener,
        cap, combat, cap-combat,
    )


def energy_ablation_builds(matrix: CandidateMatrix, tl: int) -> list[EcologyBuild]:
    base = dict(tl=tl, main_count=1, reactor_count=1, shield=True, ecm=False, eccm=True,
                pds_family='Energy', hardener=(tl >= 3))
    specs = [
        ('full', 'Energy', {}),
        ('no-hardener', 'Energy', {'hardener': False}),
        ('no-pds', 'Energy', {'pds_family': None}),
        ('no-eccm', 'Energy', {'eccm': False}),
        ('no-shield', 'Energy', {'shield': False, 'hardener': False}),
        ('no-hardener-no-pds', 'Energy', {'hardener': False, 'pds_family': None}),
        ('kinetic-main-control', 'Kinetic', {}),
        ('missile-main-control', 'Missile', {}),
    ]
    out=[]
    for name,family,delta in specs:
        kw=base.copy(); kw.update(delta); kw['family']=family
        out.append(make_build(matrix, archetype=f'energy-defense-{name}', ident=f'tl{tl}-ablation-energy-defense-{name}', **kw))
    return out


def missile_defense_ablation_builds(matrix: CandidateMatrix, tl: int) -> list[EcologyBuild]:
    base = dict(tl=tl, family='Missile', main_count=1, reactor_count=1, shield=True, ecm=False, eccm=True,
                pds_family='AMM', hardener=(tl >= 3))
    specs = [
        ('full', {}),
        ('no-hardener', {'hardener': False}),
        ('no-pds', {'pds_family': None}),
        ('no-eccm', {'eccm': False}),
        ('no-shield', {'shield': False, 'hardener': False}),
    ]
    return [make_build(matrix, archetype=f'missile-defense-{name}', ident=f'tl{tl}-ablation-missile-defense-{name}', **({**base, **delta})) for name,delta in specs]


def build_variants(repo: Path, doc: dict[str, Any]) -> tuple[list[EcologyBuild], list[EcologyVariant]]:
    matrix=CandidateMatrix(repo)
    primary=generate_primary_builds(matrix)
    by_id={b.id:b for b in primary}
    all_builds={b.id:b for b in primary}
    variants: list[EcologyVariant]=[]

    # A. Energy defense causal ablation, TL3-TL8, against all 11 standard same-TL opponents.
    for tl in range(3,9):
        abls=energy_ablation_builds(matrix,tl)
        for b in abls: all_builds[b.id]=b
        opponents=[b for b in primary if b.tl==tl and b.id != f'tl{tl}-energy-defense-specialist']
        for ab in abls:
            perturb=ab.archetype.replace('energy-defense-','')
            for opp in opponents:
                for order,suffix in [('SideAFirst','afirst'),('SideBFirst','bfirst')]:
                    vid=f'energy-ablation-tl{tl}-{perturb}__vs__{opp.id}-{suffix}'
                    variants.append(EcologyVariant(vid,tl,ab,opp,order,population='targeted_same_tl_exact_fill',scenario_group='energy_defense_ablation',perturbation=perturb))

    # B. Movement-order cliff geometry/range sweep on the strongest native CP111 signals.
    cliff_pairs=[
        (7,'tl7-kinetic-dual-main','tl7-missile-dual-main'),
        (7,'tl7-kinetic-dual-reactor','tl7-missile-dual-reactor'),
        (9,'tl9-kinetic-dual-main','tl9-missile-dual-main'),
    ]
    for tl,a_id,b_id in cliff_pairs:
        a=by_id[a_id]; b=by_id[b_id]
        for start_range in (4,6,8,10):
            qa=-(start_range//2); qb=start_range//2
            for order,suffix in [('SideAFirst','afirst'),('SideBFirst','bfirst')]:
                vid=f'geometry-cliff-tl{tl}-{a_id}__vs__{b_id}-r{start_range}-{suffix}'
                variants.append(EcologyVariant(vid,tl,a,b,order,geometry=f'radius5_axial_start_range_{start_range}',population='targeted_same_tl_exact_fill',start_q_a=qa,start_q_b=qb,scenario_group='movement_order_geometry',perturbation=f'start-range-{start_range}'))

    # C. Late Missile attrition/stalemate decomposition across defense ablations and 60/120-turn horizons.
    for tl in range(7,10):
        defs=missile_defense_ablation_builds(matrix,tl)
        for b in defs: all_builds[b.id]=b
        attackers=[by_id[f'tl{tl}-missile-balanced'],by_id[f'tl{tl}-missile-dual-main']]
        for atk in attackers:
            for deff in defs:
                perturb=deff.archetype.replace('missile-defense-','')
                for horizon in (60,120):
                    for order,suffix in [('SideAFirst','afirst'),('SideBFirst','bfirst')]:
                        vid=f'missile-attrition-tl{tl}-{atk.archetype}__vs__{perturb}-t{horizon}-{suffix}'
                        variants.append(EcologyVariant(vid,tl,atk,deff,order,population='targeted_same_tl_exact_fill',max_turns=horizon,scenario_group='missile_attrition_ablation',perturbation=f'{perturb}-h{horizon}'))

    variants.sort(key=lambda v:v.id)
    return sorted(all_builds.values(),key=lambda b:b.id), variants


def _energy_summary(rows: list[dict[str,Any]]) -> list[dict[str,Any]]:
    groups=defaultdict(list)
    for r in rows:
        if r['scenario_group']=='energy_defense_ablation':
            groups[(int(r['tl']),r['perturbation'])].append(r)
    out=[]
    for (tl,p),rs in sorted(groups.items()):
        out.append({
            'tl':tl,'perturbation':p,'variants':len(rs),
            'mean_conditional_win_rate':statistics.fmean(float(x['conditional_win_rate_a']) for x in rs),
            'mean_unresolved_rate':statistics.fmean(float(x['unresolved_rate']) for x in rs),
            'mean_power_shortfalls':statistics.fmean(float(x['mean_a_power_shortfall_events']) for x in rs),
            'mean_direct_shots':statistics.fmean(float(x['mean_a_direct_shots']) for x in rs),
            'mean_direct_hits':statistics.fmean(float(x['mean_a_direct_hits']) for x in rs),
            'mean_pds_attempts':statistics.fmean(float(x['mean_a_pds_attempts']) for x in rs),
            'mean_pds_intercepts':statistics.fmean(float(x['mean_a_pds_intercepts']) for x in rs),
            'mean_shield_absorbed':statistics.fmean(float(x['mean_a_shield_absorbed']) for x in rs),
            'mean_hull_damage_received':statistics.fmean(float(x['mean_a_hull_damage']) for x in rs),
        })
    # add delta to full within TL
    full={r['tl']:r['mean_conditional_win_rate'] for r in out if r['perturbation']=='full'}
    for r in out: r['delta_vs_full_pp']=(r['mean_conditional_win_rate']-full[r['tl']])*100.0
    return out


def _movement_summary(rows:list[dict[str,Any]]) -> list[dict[str,Any]]:
    groups=defaultdict(list)
    for r in rows:
        if r['scenario_group']=='movement_order_geometry':
            groups[(int(r['tl']),r['side_a_build'],r['side_b_build'],int(r['start_range']))].append(r)
    out=[]
    for (tl,a,b,sr),rs in sorted(groups.items()):
        if len(rs)!=2: continue
        vals={x['movement_order']:float(x['conditional_win_rate_a']) for x in rs}
        out.append({'tl':tl,'side_a_build':a,'side_b_build':b,'start_range':sr,'variants':2,
                    'side_a_win_afirst':vals.get('SideAFirst',0.0),'side_a_win_bfirst':vals.get('SideBFirst',0.0),
                    'movement_order_swing_pp':abs(vals.get('SideAFirst',0.0)-vals.get('SideBFirst',0.0))*100.0,
                    'mean_min_range':statistics.fmean(float(x['mean_min_range']) for x in rs),
                    'mean_turns':statistics.fmean(float(x['mean_turns']) for x in rs)})
    return out


def _missile_summary(rows:list[dict[str,Any]]) -> list[dict[str,Any]]:
    groups=defaultdict(list)
    for r in rows:
        if r['scenario_group']=='missile_attrition_ablation':
            # perturbation includes -h60/-h120
            groups[(int(r['tl']),r['side_a_archetype'],r['perturbation'],int(r['max_turns']))].append(r)
    out=[]
    for (tl,atk,p,horizon),rs in sorted(groups.items()):
        out.append({'tl':tl,'attacker':atk,'defense_perturbation':p.rsplit('-h',1)[0],'max_turns':horizon,'variants':len(rs),
                    'attacker_conditional_win_rate':statistics.fmean(float(x['conditional_win_rate_a']) for x in rs),
                    'unresolved_rate':statistics.fmean(float(x['unresolved_rate']) for x in rs),
                    'mean_missile_launches':statistics.fmean(float(x['mean_a_missile_launches']) for x in rs),
                    'mean_missile_hits':statistics.fmean(float(x['mean_b_missile_hits']) for x in rs),
                    'mean_defender_pds_attempts':statistics.fmean(float(x['mean_b_pds_attempts']) for x in rs),
                    'mean_defender_pds_intercepts':statistics.fmean(float(x['mean_b_pds_intercepts']) for x in rs),
                    'mean_defender_shield_restored':statistics.fmean(float(x['mean_b_shield_base_restored'])+float(x['mean_b_shield_tactical_restored']) for x in rs),
                    'mean_defender_hull_damage':statistics.fmean(float(x['mean_b_hull_damage']) for x in rs)})
    return out


def run_neighbor_analysis(repo:Path, study_path:Path, outdir:Path, trials_override:int|None=None, jobs:int=1) -> dict[str,Any]:
    doc=load_json(study_path)
    errs=validate_study(doc)
    if errs: raise ValueError('invalid CP112 study: '+','.join(errs))
    builds,variants=build_variants(repo,doc)
    trials=int(trials_override or doc['trialsPerVariant'])
    rows,elapsed=execute_variants(repo,variants,int(doc['masterSeed']),trials,jobs)
    outdir.mkdir(parents=True,exist_ok=True)
    _write_csv(outdir/'variants.csv',rows)
    # only targeted/derived builds are useful to list; all are exact fill by construction.
    _write_csv(outdir/'builds.csv',[{'build_id':b.id,'tl':b.tl,'archetype':b.archetype,'family':b.weapon_family,'main_count':b.main_count,'reactor_count':b.reactor_count,'shield':b.shield,'ecm':b.ecm,'eccm':b.eccm,'pds_family':b.pds_family or '', 'hardener':b.shield_hardener,'combat_space':b.combat_space,'mission_aux_space':b.mission_aux_space,'capacity':b.capacity,'used_space':b.used_space,'free_space':b.capacity-b.used_space} for b in builds])
    energy=_energy_summary(rows); movement=_movement_summary(rows); missile=_missile_summary(rows)
    _write_csv(outdir/'energy_defense_ablation.csv',energy)
    _write_csv(outdir/'movement_order_geometry.csv',movement)
    _write_csv(outdir/'missile_attrition_ablation.csv',missile)
    failures=[]
    if any(int(r['errors']) for r in rows): failures.append('trial-errors')
    if any(b.used_space!=b.capacity for b in builds): failures.append('exact-fill')
    counts=defaultdict(int)
    for v in variants: counts[v.scenario_group]+=1
    expected={'energy_defense_ablation':1056,'movement_order_geometry':24,'missile_attrition_ablation':120}
    if dict(counts)!=expected: failures.append(f'variant-shape:{dict(counts)}')
    # Diagnostics must exercise expected telemetry, not hit balance thresholds.
    if not any(float(r['mean_a_power_shield_hardener'])>0 for r in rows if r['scenario_group']=='energy_defense_ablation'): failures.append('hardener-telemetry')
    if not any(float(r['mean_b_pds_attempts'])>0 for r in rows if r['scenario_group']=='missile_attrition_ablation'): failures.append('pds-telemetry')
    if not any(float(r['mean_a_missile_launches'])>0 for r in rows if r['scenario_group']=='missile_attrition_ablation'): failures.append('missile-telemetry')
    analysis={
        'schemaVersion':'star-cluster-build-neighbor-ablation-results-v0.1','checkpoint':'112',
        'damageModel':'layered_defense_hull_only','internalDamageCriticalsSimulated':False,
        'trialsPerVariant':trials,'variants':len(variants),'totalTrials':len(variants)*trials,'elapsedSeconds':elapsed,
        'scenarioVariantCounts':dict(counts),'buildsListed':len(builds),'failedGates':failures,'automaticPromotion':False,
        'energyDefenseSummary':energy,'movementOrderGeometrySummary':movement,'missileAttritionSummary':missile,
        'interpretation':'Causal diagnostic evidence only. No CP109/CP110 numerical value is automatically changed or promoted. Exact-fill residual mission/AUX Space retains zero tactical effect.'
    }
    (outdir/'analysis.json').write_text(json.dumps(analysis,indent=2)+'\n',encoding='utf-8')
    return analysis
