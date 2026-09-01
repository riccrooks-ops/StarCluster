#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json,sys
from pathlib import Path

SKIP='docs/validation/evidence/checkpoint-144/CP144_REPOSITORY_SHA256SUMS.txt'
MATRIX_SHA='3088b0a9eb45f6bf505c24513e8bb2ac878819db4ab464ccfea330243c82f194'

def req(v,m):
    if not v: raise AssertionError(m)
def sha(p):
    h=hashlib.sha256();h.update(p.read_bytes());return h.hexdigest()
def js(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def read_rows(p):
    with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def manifest(p):
    out={}
    for line in p.read_text(encoding='utf-8-sig').splitlines():
        if line.strip():h,r=line.split('  ',1);out[r]=h
    return out
def owned(repo):
    out=[]
    for p in repo.rglob('*'):
        if not p.is_file():continue
        rel=p.relative_to(repo).as_posix();w='/'+rel
        if rel.startswith(('out/','.git/')) or '/__pycache__/' in w or rel.endswith('.pyc') or '/bin/' in w or '/obj/' in w or '/TestResults/' in w:continue
        if rel==SKIP:continue
        out.append(rel)
    return sorted(out)
def validate_manifest(repo):
    entries=manifest(repo/SKIP);cur=owned(repo)
    req(set(entries)==set(cur),f'manifest path drift missing={sorted(set(entries)-set(cur))[:8]} extra={sorted(set(cur)-set(entries))[:8]}')
    for rel,h in entries.items():req(sha(repo/rel)==h,f'manifest hash drift {rel}')
    return len(entries)

def validate_smoke(root, dirname='stage-a-smoke-merged'):
    base=root/dirname;req((base/'summary.json').is_file(),f'{dirname} summary missing');s=js(base/'summary.json')
    req(s['passed'] is True and int(s.get('failedGates',0))==0 and not s.get('gates',{}).get('failed',[]),f'{dirname} gates')
    req(s['stageAScenarios']==6850 and s['integrationSmokeTrials']==6850 and s['executionErrors']==0,f'{dirname} coverage')
    req(s['resourceEnvironmentCount']==5 and s['scenarioStrataCount']==10 and s['orderedSameTlWeaponPairings']==137,f'{dirname} factorial')
    req(s['resolved']==6785 and s['resolvedGe25']==9 and s['turnCapSentinels']==65 and s['safeStalemates']==0,f'{dirname} deterministic smoke signature')
    req(s['nonstandoffOpenOrders']==0,f'{dirname} EngageAdaptive reopen regression')
    req(s['sourceMatrixUnmodified'] is True and s['substantiveCombatTrials']==0 and s['stageASubstantiveReady'] is True and s['promotionAllowed'] is False,f'{dirname} scope')
    rows=read_rows(base/'whole_combat_smoke_results.csv');req(len(rows)==6850 and len({r['scenario_id'] for r in rows})==6850,f'{dirname} result rows')
    req(all(not r['error'] and int(r['turns'])<=60 and int(r['turn_telemetry_coverage_pass']) and int(r['nonstandoff_open_orders'])==0 for r in rows),f'{dirname} execution/telemetry/movement')
    audit=read_rows(base/'batch_merge_audit.csv');req(len(audit)==7 and all(int(r['passed']) for r in audit),f'{dirname} batch audit')
    return s

def validate_substantive(root, dirname='stage-a-substantive-merged'):
    base=root/dirname;req((base/'summary.json').is_file(),f'{dirname} summary missing');s=js(base/'summary.json')
    req(s['passed'] is True and int(s.get('failedGates',0))==0 and not s.get('gates',{}).get('failed',[]),f'{dirname} gates')
    req(s['stageAScenarios']==6850 and s['resourceEnvironmentCount']==5 and s['scenarioStrataCount']==10 and s['orderedSameTlWeaponPairings']==137,f'{dirname} factorial')
    req(s['trialsPerScenario']==500 and s['substantiveCombatTrials']==3425000,f'{dirname} substantive trial count')
    req(s['sourceMatrixUnmodified'] is True and s['automaticPromotion'] is False and s['tuningAllowed'] is False and s['stageBAutomatic'] is False,f'{dirname} interpretation boundary')
    rows=read_rows(base/'scenario_response_surface.csv');req(len(rows)==6850 and len({r['scenario_id'] for r in rows})==6850,f'{dirname} scenario rows')
    req(sum(int(r['trials']) for r in rows)==3425000 and all(int(r['trials'])==500 for r in rows),f'{dirname} per-cell trial count')
    req(all(int(r['error_trials'])==0 for r in rows),f'{dirname} trial errors')
    req(all(float(r['a_nonstandoff_open_orders_mean'])==0.0 and float(r['b_nonstandoff_open_orders_mean'])==0.0 for r in rows),f'{dirname} EngageAdaptive reopen regression')
    audit=read_rows(base/'batch_merge_audit.csv');req(len(audit)==27 and all(int(r['passed']) for r in audit),f'{dirname} batch audit')
    req(sum(int(r['combat_trials']) for r in audit)==3425000,f'{dirname} batch trial sum')
    expected={
        'weapon_tl_response_curves.csv':35,
        'weapon_pair_tl_response_curves.csv':137,
        'stratum_response_surface.csv':350,
        'resource_response_surface.csv':175,
        'weapon_overall_response.csv':4,
        'counter_effects.csv':6165,
        'resource_effects.csv':5480,
        'pairwise_symmetric_response.csv':2550,
        'pareto_choice_surface.csv':6850,
        'pareto_participation_summary.csv':35,
    }
    for name,count in expected.items():
        p=base/name;req(p.is_file(),f'{dirname} missing response artifact {name}');rs=read_rows(p);req(len(rs)==count,f'{dirname} {name} expected {count} rows got {len(rs)}')
    pair=read_rows(base/'pairwise_symmetric_response.csv');req(all('weapon_x_win_rate' in r and 'weapon_y_win_rate' in r and 'draw_rate' in r and 'unresolved_rate' in r for r in pair),'pairwise symmetric schema')
    pareto=read_rows(base/'pareto_choice_surface.csv');req(all('side_symmetric_win_rate' in r and 'side_symmetric_fast_win_rate' in r and 'side_symmetric_damage_advantage_mean' in r for r in pareto),'Pareto side-symmetric schema')
    return s

def validate_native(path, final):
    name='CP144_NATIVE_ACCEPTANCE_SUMMARY.json' if final else 'CP144_REPOSITORY_ONLY_ACCEPTANCE.json';s=js(path/name)
    fg=s.get('failedGates',[]);req(s['checkpoint']==144 and (fg==[] or fg==0) and not s.get('gates',{}).get('failed',[]),'native identity')
    req(s['python'].startswith('Python 3.13') and s['dotnetSdk']=='8.0.423' and s['buildPassed'] is True,'runtimes/build')
    req(s['pythonTestsPassed']==298 and s['xunitPassed']==916 and s['xunitFailed']==0 and s['xunitSkipped']==0,'unit tests')
    req(s['scenarioRunnerSelfTestsPassed']==70 and s['researchParityPassed']==25,'deterministic/parity gates')
    req(s['cp139FocusedTestsPassed']==9 and s['cp140FocusedTestsPassed']==10 and s['cp141FocusedTestsPassed']==10 and s['cp142FocusedTestsPassed']==12 and s['cp143FocusedTestsPassed']==12 and s['cp144FocusedTestsPassed']==11,'focused tests')
    req(s['cp142ReconciliationLedgerRows']==531 and s['cp142ChangedRows']==72 and s['cp142ExplicitUnresolvedRows']==7,'CP142 reconciliation regression')
    req(s['sharedPolicyFixtureCases']==10 and s['pythonCsharpPolicyParityPassed'] is True,'policy parity')
    req(s['stageAScenarios']==6850 and s['resourceEnvironmentCount']==5 and s['scenarioStrataCount']==10 and s['orderedSameTlWeaponPairings']==137,'native Stage-A factorial')
    req(s['smokeResolved']==6785 and s['smokeResolvedGe25']==9 and s['smokeTurnCapSentinels']==65 and s['smokeSafeStalemates']==0 and s['smokeNonstandoffOpenOrders']==0,'native smoke signature')
    req(s['sourceMatrixUnmodified'] is True and s['automaticPromotion'] is False and s['tuningAllowed'] is False and s['stageBAutomatic'] is False,'native scope')
    if final:
        req(s['repositoryOnlyAccepted'] is True,'final must carry RepositoryOnly acceptance')
        req(s['substantiveStageACompleted'] is True and s['substantiveCombatTrials']==3425000 and s['trialsPerScenario']==500,'final substantive completion')
    else:
        req(s['substantiveCombatTrials']==0,'RepositoryOnly must not run substantive trials')
    return s

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);ap.add_argument('--native-results');a=ap.parse_args();repo=Path(a.repo).resolve()
    try:
        d=js(repo/'tools/checkpoints/checkpoint-144/checkpoint_144_definition.json')
        req(d['checkpoint']==144 and d['expectedPythonTests']==298 and d['expectedXunitTests']==916 and d['expectedStageAScenarios']==6850 and d['expectedSubstantiveCombatTrials']==3425000,'definition')
        count=validate_manifest(repo);json_count=0
        for p in repo.rglob('*.json'):
            rel=p.relative_to(repo).as_posix();w='/'+rel
            if rel.startswith('out/') or '/bin/' in w or '/obj/' in w:continue
            json.loads(p.read_text(encoding='utf-8-sig'));json_count+=1
        req(sha(repo/'docs/design/player_technology/technology_numerical_matrix_v0_9.json')==MATRIX_SHA,'source matrix drift')
        if a.native_results:
            n=Path(a.native_results).resolve();final=(n/'CP144_NATIVE_ACCEPTANCE_SUMMARY.json').is_file();validate_native(n,final);validate_smoke(n,'stage-a-smoke-merged');
            if final:validate_substantive(n,'stage-a-substantive-merged')
        print(f'       CP144 contract verified: {count} repository-owned files; {json_count} JSON files; 5-resource/6,850-cell Stage A bound; EngageAdaptive parity closure enforced; source matrix frozen; tuning/promotion disabled.')
        return 0
    except Exception as e:
        print(f'CP144 contract failure: {e}',file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
