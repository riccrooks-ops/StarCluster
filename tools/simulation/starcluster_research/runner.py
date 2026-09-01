from __future__ import annotations
import csv,json,os,platform,statistics,time
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import get_context
from pathlib import Path
from .combat import CombatData,run_trial
from .model import Variant
from .study import load_json,validate_study,build_study
from .parity import run_parity

_WORKER_DATA=None

def _init_worker(repo:str):
    global _WORKER_DATA; _WORKER_DATA=CombatData(Path(repo))

def _run_variant_task(args):
    variant,master,trials=args; results=[]
    for i in range(trials): results.append(run_trial(variant,_WORKER_DATA,master,i))
    wins={'A':0,'B':0,'Draw':0,'Error':0}
    for r in results: wins[r.winner]=wins.get(r.winner,0)+1
    ok=[r for r in results if not r.trial_error]
    mean=lambda attr: statistics.fmean(getattr(r,attr) for r in ok) if ok else 0.0
    return {
        'variant_id':variant.id,'pairing_id':variant.pairing_id,'bundle_id':variant.bundle_id,'orientation':variant.orientation,'source':variant.source,'movement_order':variant.movement_order,
        'side_a_build':variant.side_a.id,'side_b_build':variant.side_b.id,'side_a_family':variant.side_a.family,'side_b_family':variant.side_b.family,
        'side_a_advanced':variant.side_a.advanced_count,'side_b_advanced':variant.side_b.advanced_count,'side_a_used_space':variant.side_a.used_space,'side_b_used_space':variant.side_b.used_space,
        'population_cell':variant.population_cell,'population_count':variant.population_count,'representative_weight':variant.representative_weight,
        'trials':trials,'wins_a':wins['A'],'wins_b':wins['B'],'draws':wins['Draw'],'errors':wins['Error'],
        'win_rate_a':wins['A']/trials,'win_rate_b':wins['B']/trials,'draw_rate':wins['Draw']/trials,
        'mean_turns':mean('turns'),'mean_final_range':mean('final_range'),'mean_direct_shots_a':mean('direct_shots_a'),'mean_direct_shots_b':mean('direct_shots_b'),
        'mean_missile_launches_a':mean('missile_launches_a'),'mean_missile_launches_b':mean('missile_launches_b'),'mean_pds_attempts_a':mean('pds_attempts_a'),'mean_pds_attempts_b':mean('pds_attempts_b'),
        'mean_power_shortfalls_a':mean('power_shortfalls_a'),'mean_power_shortfalls_b':mean('power_shortfalls_b'),'mean_firm_track_turns_a':mean('firm_track_turns_a'),'mean_firm_track_turns_b':mean('firm_track_turns_b'),
        'first_error':next((r.trial_error for r in results if r.trial_error),'')
    }


def _run_variant_chunk(args):
    variants,master,trials=args
    return [_run_variant_task((v,master,trials)) for v in variants]


def execute_variants(repo:Path,variants:list[Variant],master:int,trials:int,jobs:int):
    jobs=max(1,min(jobs,len(variants))); started=time.perf_counter(); out=[]
    if jobs==1:
        _init_worker(str(repo))
        out=[_run_variant_task((v,master,trials)) for v in variants]
    else:
        # Keep IPC/future cardinality bounded. Thousands of one-variant futures are
        # unnecessary and can become unstable in constrained CI/container runtimes.
        chunk_count=min(len(variants),max(jobs,jobs*4))
        chunks=[[] for _ in range(chunk_count)]
        for index,variant in enumerate(variants): chunks[index % chunk_count].append(variant)
        ctx=get_context('spawn')
        with ProcessPoolExecutor(max_workers=jobs,mp_context=ctx,initializer=_init_worker,initargs=(str(repo),)) as ex:
            futures=[ex.submit(_run_variant_chunk,(chunk,master,trials)) for chunk in chunks if chunk]
            for f in as_completed(futures): out.extend(f.result())
    out.sort(key=lambda r:r['variant_id'])
    return out,time.perf_counter()-started


def write_csv(path:Path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    if not rows: path.write_text(''); return
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


def plan_dict(doc,built):
    return {
        'study_id':doc['id'],'generated_study_id':doc['generatedStudyId'],'checkpoint':doc['checkpoint'],'coverage_mode':doc['coverageMode'],'raw_combinations':built['raw'],'legal_builds':len(built['builds']),
        'space_counts':built['space_counts'],'population_cells':len(built['cells']),'logical_pairings':len(built['pairs']),'variants':len(built['variants']),
        'sample_attempts':built['sample_attempts'],'diversity_attempts':built['diversity_attempts'],'master_seed':doc['masterSeed'],'declared_trials_per_variant':doc['trialsPerVariant']
    }


def run_study(repo:Path,study_path:Path,outdir:Path,trials:int|None,jobs:int,mode:str):
    doc=load_json(study_path); errs=validate_study(doc)
    if errs: raise RuntimeError('study validation failed: '+'; '.join(errs))
    built=build_study(doc); outdir.mkdir(parents=True,exist_ok=True)
    (outdir/'plan.json').write_text(json.dumps(plan_dict(doc,built),indent=2)+'\n')
    if built['cells']:
        write_csv(outdir/'population_cells.csv',[{'key':c.key,'composition':c.composition,'progression':c.progression,'space_pair':c.space_pair,'population':c.population,'weight':c.weight,'quota':built['quotas'].get(c.key,0)} for c in sorted(built['cells'].values(),key=lambda c:c.key)])
    write_csv(outdir/'builds.csv',[{'build_id':b.id,'used_space':b.used_space,'free_space':b.free_space,'capacity':b.capacity,'max_tl':b.max_tl,'advanced_count':b.advanced_count,'information_control_advanced_count':b.info_advanced_count,'main_weapons':b.main_weapons,'reactors':b.reactors,'family':b.family,'composition':b.composition,'space_class':b.space_class,**{f'axis_{k}':v for k,v in b.selections.items()}} for b in built['builds']])
    write_csv(outdir/'pairings.csv',[{'pairing_id':p.id,'bundle_id':p.bundle_id,'orientation':p.orientation,'source':p.source,'side_a':p.side_a.id,'side_b':p.side_b.id,'population_cell':p.population_cell,'population_count':p.population_count,'representative_weight':p.representative_weight} for p in built['pairs']])
    if mode=='plan': return {'plan':plan_dict(doc,built),'elapsed_seconds':0.0,'gate_failures':[]}
    actual_trials=int(trials if trials is not None else doc['trialsPerVariant']); results,elapsed=execute_variants(repo,built['variants'],int(doc['masterSeed']),actual_trials,jobs)
    write_csv(outdir/'variants.csv',results)
    failures=[]
    if any(r['errors'] for r in results): failures.append('no-trial-errors')
    families=set(r['side_a_family'] for r in results)|set(r['side_b_family'] for r in results)
    if not {'Kinetic','Energy','Missile'}.issubset(families): failures.append('three-family-coverage')
    if len(results)!=len(built['variants']): failures.append('variant-count')
    summary={'plan':plan_dict(doc,built),'execution':{'trials_per_variant':actual_trials,'total_trials':actual_trials*len(results),'jobs':jobs,'elapsed_seconds':elapsed,'trials_per_second':(actual_trials*len(results)/elapsed if elapsed else 0.0)},'gates':{'failed':failures,'passed':len(failures)==0},'failedGates':len(failures),'aggregate':{'mean_turns':statistics.fmean(r['mean_turns'] for r in results) if results else 0.0,'trial_errors':sum(r['errors'] for r in results),'families':sorted(families)}}
    (outdir/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    return summary


def analyze(primary_csv:Path,overlay_csv:Path|None,outpath:Path):
    def read(p):
        with p.open(newline='',encoding='utf-8') as f:
            return list(csv.DictReader(f))

    def f(row,key):
        return float(row[key])

    def i(row,key):
        return int(row[key])

    def weighted_breakdown(bundle_rows,key):
        grouped={}
        for row in bundle_rows:
            grouped.setdefault(str(row[key]),[]).append(row)
        result=[]
        for label,rows in sorted(grouped.items()):
            weight=sum(r['weight'] for r in rows)
            result.append({
                key:label,
                'bundles':len(rows),
                'population_weight':weight,
                'population_share':weight/EXPECTED_POPULATION_WEIGHT if EXPECTED_POPULATION_WEIGHT else 0.0,
                'weighted_advanced_side_win_rate':sum(r['weight']*r['advanced_win_rate'] for r in rows)/weight if weight else 0.0,
                'weighted_mean_power_shortfall_events':sum(r['weight']*r['power_shortfall'] for r in rows)/weight if weight else 0.0,
            })
        return result

    EXPECTED_PRIMARY_ROWS=1152
    EXPECTED_SOURCE_COUNTS={'statistical':960,'diversity':128,'named':64}
    EXPECTED_STATISTICAL_BUNDLES=240
    EXPECTED_POPULATION_CELLS=96
    EXPECTED_POPULATION_WEIGHT=13_474_170_720.0
    EXPECTED_OVERLAY_ROWS=100
    EXPECTED_OVERLAY_DIAGNOSTICS=25

    primary=read(primary_csv)
    overlay=read(overlay_csv) if overlay_csv and overlay_csv.exists() else []
    failures=[]
    source_counts={name:sum(1 for r in primary if r['source']==name) for name in EXPECTED_SOURCE_COUNTS}
    if len(primary)!=EXPECTED_PRIMARY_ROWS:
        failures.append('primary-variant-count')
    if source_counts!=EXPECTED_SOURCE_COUNTS:
        failures.append('primary-source-counts')
    if sum(i(r,'errors') for r in primary):
        failures.append('primary-trial-errors')
    if len(overlay)!=EXPECTED_OVERLAY_ROWS:
        failures.append('overlay-variant-count')
    if sum(i(r,'errors') for r in overlay):
        failures.append('overlay-trial-errors')

    stat=[r for r in primary if r['source']=='statistical']
    bundles={}
    for r in stat:
        bundles.setdefault(r['bundle_id'],[]).append(r)
    if len(bundles)!=EXPECTED_STATISTICAL_BUNDLES or any(len(rows)!=4 for rows in bundles.values()):
        failures.append('statistical-bundle-shape')

    bundle_rows=[]
    for bid,rows in sorted(bundles.items()):
        weights={f(r,'representative_weight') for r in rows}
        cells={r['population_cell'] for r in rows}
        if len(weights)!=1 or len(cells)!=1:
            failures.append('statistical-bundle-weight-cell-consistency')
            continue
        cell=next(iter(cells)); parts=cell.split('~')
        if len(parts)!=3:
            failures.append('population-cell-format')
            continue
        composition,progression,space_pair=parts
        weight=next(iter(weights))
        adv_win=[]; power=[]; deltas=[]; family_pairs=[]
        for r in rows:
            aa=i(r,'side_a_advanced'); bb=i(r,'side_b_advanced'); wa=f(r,'win_rate_a'); wb=f(r,'win_rate_b')
            adv_win.append(wa if aa>bb else wb if bb>aa else (wa+wb)/2.0)
            power.append((f(r,'mean_power_shortfalls_a')+f(r,'mean_power_shortfalls_b'))/2.0)
            deltas.append(abs(aa-bb))
            family_pairs.append('-'.join(sorted((r['side_a_family'],r['side_b_family']))))
        bundle_rows.append({
            'bundle_id':bid,
            'weight':weight,
            'advanced_win_rate':statistics.fmean(adv_win),
            'power_shortfall':statistics.fmean(power),
            'advanced_delta':max(deltas),
            'composition':composition,
            'progression':progression,
            'space_pair':space_pair,
            'family_matchup':statistics.mode(family_pairs),
        })

    population_cells={r['population_cell'] for r in stat}
    if len(population_cells)!=EXPECTED_POPULATION_CELLS:
        failures.append('population-cell-coverage')
    weight_total=sum(r['weight'] for r in bundle_rows)
    if abs(weight_total-EXPECTED_POPULATION_WEIGHT)>0.5:
        failures.append('population-weight-total')
    weighted_adv=sum(r['weight']*r['advanced_win_rate'] for r in bundle_rows)/weight_total if weight_total else 0.0
    weighted_power=sum(r['weight']*r['power_shortfall'] for r in bundle_rows)/weight_total if weight_total else 0.0

    composition_rows=weighted_breakdown(bundle_rows,'composition')
    progression_rows=weighted_breakdown(bundle_rows,'progression')
    space_rows=weighted_breakdown(bundle_rows,'space_pair')
    family_rows=weighted_breakdown(bundle_rows,'family_matchup')

    dominance=[]
    for r in bundle_rows:
        signal='neutral'
        if r['advanced_delta']>0 and r['advanced_win_rate']>=0.65:
            signal='advanced_advantage'
        elif r['advanced_delta']>0 and r['advanced_win_rate']<=0.35:
            signal='advanced_disadvantage'
        if signal!='neutral':
            dominance.append({**r,'signal':signal})

    overlay_groups={}
    for r in overlay:
        key=r['bundle_id']
        if key.endswith('-forward'):
            base=key[:-8]
        elif key.endswith('-reverse'):
            base=key[:-8]
        else:
            base=key
        overlay_groups.setdefault(base,[]).append(r)
    overlay_diagnostics=[]
    for base,rows in sorted(overlay_groups.items()):
        forward_side_win=[]; power=[]
        for r in rows:
            is_reverse=r['bundle_id'].endswith('-reverse')
            forward_side_win.append(f(r,'win_rate_b') if is_reverse else f(r,'win_rate_a'))
            power.append((f(r,'mean_power_shortfalls_a')+f(r,'mean_power_shortfalls_b'))/2.0)
        overlay_diagnostics.append({
            'diagnostic':base,
            'variants':len(rows),
            'forward_side_win_rate':statistics.fmean(forward_side_win),
            'mean_power_shortfall_events':statistics.fmean(power),
        })
    if len(overlay_diagnostics)!=EXPECTED_OVERLAY_DIAGNOSTICS or any(r['variants']!=4 for r in overlay_diagnostics):
        failures.append('overlay-diagnostic-shape')

    outdir=outpath.parent
    outdir.mkdir(parents=True,exist_ok=True)
    write_csv(outdir/'analysis_composition.csv',composition_rows)
    write_csv(outdir/'analysis_progression.csv',progression_rows)
    write_csv(outdir/'analysis_space_breakpoints.csv',space_rows)
    write_csv(outdir/'analysis_family_matchups.csv',family_rows)
    write_csv(outdir/'analysis_dominance_screen.csv',dominance)
    write_csv(outdir/'analysis_legacy_overlay.csv',overlay_diagnostics)

    result={
        'primary_variants':len(primary),
        'primary_source_counts':source_counts,
        'primary_statistical_bundles':len(bundle_rows),
        'primary_population_cells':len(population_cells),
        'primary_population_weight_total':weight_total,
        'population_weighted_advanced_side_win_rate':weighted_adv,
        'population_weighted_mean_power_shortfall_events':weighted_power,
        'screening_dominance_signals':{
            'advanced_advantage':sum(1 for r in dominance if r['signal']=='advanced_advantage'),
            'advanced_disadvantage':sum(1 for r in dominance if r['signal']=='advanced_disadvantage'),
            'threshold':'matched statistical bundles with TL3-frontier delta > 0 and mover/orientation-neutral advanced-side win rate >= 0.65 or <= 0.35',
        },
        'overlay_variants':len(overlay),
        'overlay_diagnostics':len(overlay_diagnostics),
        'failed_gates':sorted(set(failures)),
        'automatic_promotion':False,
        'interpretation':'Research-screen evidence only. Breakdown CSVs screen composition, progression distance, Space breakpoints, family matchups, power pressure, matched-pair dominance signals, and legacy-stack diagnostics; no result automatically changes a game-facing technology value.'
    }
    outpath.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result


def environment_report():
    import sys
    return {'python':sys.version.split()[0],'implementation':platform.python_implementation(),'executable':sys.executable,'stdlib_only':True,'platform':platform.platform()}


def analyze_cp104(diagnostic_csv:Path, cp103_primary_csv:Path, outpath:Path):
    """Targeted CP104 diagnostic closure. No automatic promotion or balance gates."""
    def read(p):
        with p.open(newline='',encoding='utf-8') as f: return list(csv.DictReader(f))
    def ff(r,k): return float(r[k])
    def ii(r,k): return int(r[k])
    diagnostic=read(diagnostic_csv); cp103=read(cp103_primary_csv)
    failures=[]
    EXPECTED_VARIANTS=256
    EXPECTED_COMPARISONS={'legacy-response':16,'movement':10,'energy-synergy':22,'power-hotspot':14,'control':2}
    if len(diagnostic)!=EXPECTED_VARIANTS: failures.append('diagnostic-variant-count')
    if sum(ii(r,'errors') for r in diagnostic): failures.append('diagnostic-trial-errors')
    groups={}
    for r in diagnostic:
        b=r['bundle_id']
        if not b.startswith('named-'):
            failures.append('diagnostic-bundle-prefix'); continue
        key=b[6:]
        if key.endswith('__forward'): key=key[:-9]
        elif key.endswith('__reverse'): key=key[:-9]
        groups.setdefault(key,[]).append(r)
    summary_rows=[]
    category_counts={}
    for key,rows in sorted(groups.items()):
        if '__' not in key:
            failures.append('diagnostic-bundle-shape'); continue
        category,comparison=key.split('__',1)
        category_counts[category]=category_counts.get(category,0)+1
        if len(rows)!=4: failures.append('diagnostic-comparison-shape')
        cw=[]; bw=[]; dr=[]; first=[]; second=[]; cp=[]; bp=[]
        baseline_builds=set(); challenger_builds=set()
        for r in rows:
            rev=r['bundle_id'].endswith('__reverse')
            challenger_win=ff(r,'win_rate_a') if rev else ff(r,'win_rate_b')
            baseline_win=ff(r,'win_rate_b') if rev else ff(r,'win_rate_a')
            cw.append(challenger_win); bw.append(baseline_win); dr.append(ff(r,'draw_rate'))
            ch_first=(r['movement_order']=='SideAFirst') if rev else (r['movement_order']=='SideBFirst')
            (first if ch_first else second).append(challenger_win)
            cp.append(ff(r,'mean_power_shortfalls_a') if rev else ff(r,'mean_power_shortfalls_b'))
            bp.append(ff(r,'mean_power_shortfalls_b') if rev else ff(r,'mean_power_shortfalls_a'))
            challenger_builds.add(r['side_a_build'] if rev else r['side_b_build'])
            baseline_builds.add(r['side_b_build'] if rev else r['side_a_build'])
        summary_rows.append({
            'category':category,'comparison':comparison,'variants':len(rows),
            'baseline_build':';'.join(sorted(baseline_builds)),'challenger_build':';'.join(sorted(challenger_builds)),
            'challenger_win_rate':statistics.fmean(cw),'baseline_win_rate':statistics.fmean(bw),'draw_rate':statistics.fmean(dr),
            'challenger_win_rate_moves_first':statistics.fmean(first) if first else 0.0,
            'challenger_win_rate_moves_second':statistics.fmean(second) if second else 0.0,
            'movement_order_swing_second_minus_first':(statistics.fmean(second)-statistics.fmean(first)) if first and second else 0.0,
            'challenger_mean_power_shortfalls':statistics.fmean(cp),'baseline_mean_power_shortfalls':statistics.fmean(bp),
        })
    if category_counts!=EXPECTED_COMPARISONS: failures.append('diagnostic-category-counts')

    # CP103 weighting sensitivity using accepted statistical bundles.
    stat=[r for r in cp103 if r.get('source')=='statistical']
    if len(cp103)!=1152 or len(stat)!=960: failures.append('cp103-reweight-source-shape')
    bundles={}
    for r in stat: bundles.setdefault(r['bundle_id'],[]).append(r)
    if len(bundles)!=240 or any(len(x)!=4 for x in bundles.values()): failures.append('cp103-reweight-bundle-shape')
    br=[]
    for bid,rows in bundles.items():
        cell=rows[0]['population_cell']; parts=cell.split('~')
        if len(parts)!=3: failures.append('cp103-reweight-cell-format'); continue
        adv=[]; power=[]
        for r in rows:
            aa=ii(r,'side_a_advanced'); bb=ii(r,'side_b_advanced'); wa=ff(r,'win_rate_a'); wb=ff(r,'win_rate_b')
            adv.append(wa if aa>bb else wb if bb>aa else (wa+wb)/2.0)
            power.append((ff(r,'mean_power_shortfalls_a')+ff(r,'mean_power_shortfalls_b'))/2.0)
        br.append({'bundle_id':bid,'weight':ff(rows[0],'representative_weight'),'cell':cell,'composition':parts[0],'progression':parts[1],'space_pair':parts[2],'advanced_win':statistics.fmean(adv),'power':statistics.fmean(power)})
    if len({x['cell'] for x in br})!=96: failures.append('cp103-reweight-cell-count')
    def scheme(name, fn):
        ws=[fn(x) for x in br]; den=sum(ws)
        return {'weighting_scheme':name,'bundle_count':len(br),'advanced_side_win_rate':sum(w*x['advanced_win'] for w,x in zip(ws,br))/den if den else 0.0,'mean_power_shortfall_events':sum(w*x['power'] for w,x in zip(ws,br))/den if den else 0.0}
    from collections import Counter
    celln=Counter(x['cell'] for x in br); compn=Counter(x['composition'] for x in br); progn=Counter(x['progression'] for x in br); spn=Counter(x['space_pair'] for x in br)
    sensitivity=[
        scheme('combinatorial_population',lambda x:x['weight']),
        scheme('equal_statistical_bundle',lambda x:1.0),
        scheme('equal_population_cell',lambda x:1.0/celln[x['cell']]),
        scheme('equal_composition_class',lambda x:1.0/compn[x['composition']]),
        scheme('equal_progression_stratum',lambda x:1.0/progn[x['progression']]),
        scheme('equal_space_pair_stratum',lambda x:1.0/spn[x['space_pair']]),
    ]

    outdir=outpath.parent; outdir.mkdir(parents=True,exist_ok=True)
    write_csv(outdir/'cp104_comparison_summary.csv',summary_rows)
    for cat,fn in [('legacy_response','legacy-response'),('movement_order','movement'),('energy_synergy','energy-synergy'),('power_hotspots','power-hotspot'),('controls','control')]:
        write_csv(outdir/f'cp104_{cat}.csv',[r for r in summary_rows if r['category']==fn])
    write_csv(outdir/'cp104_population_weight_sensitivity.csv',sensitivity)
    result={
        'diagnostic_variants':len(diagnostic),'diagnostic_comparisons':len(summary_rows),'category_counts':category_counts,
        'trial_errors':sum(ii(r,'errors') for r in diagnostic),
        'population_weight_sensitivity':sensitivity,
        'failed_gates':sorted(set(failures)),'automatic_promotion':False,
        'higher_tl_expansion_gate':{'next_phase':'extend basic subsystem Technology-Level chart beyond TL3','additional_tl3_calibration_only_for_architectural_defect':True},
        'interpretation':'CP104 is targeted diagnostic closure only. Results can identify architectural defects or future design questions but do not automatically change TL3 values. Absent an architectural defect, proceed to higher-TL chart expansion rather than further TL3 tuning.'
    }
    outpath.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result
