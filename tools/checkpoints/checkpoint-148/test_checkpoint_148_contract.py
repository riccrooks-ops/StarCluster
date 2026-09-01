#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json,sys
from pathlib import Path
MATRIX_SHA='3088b0a9eb45f6bf505c24513e8bb2ac878819db4ab464ccfea330243c82f194'
CP147_NATIVE_SHA='a33b7fa137b2b17d8c4f5d45900cdc5073e0a4116147f521b40948a172730bd6'
SKIP='docs/validation/evidence/checkpoint-148/CP148_REPOSITORY_SHA256SUMS.txt'

def req(x,m):
    if not x:raise AssertionError(m)
def sha(p):h=hashlib.sha256();h.update(p.read_bytes());return h.hexdigest()
def js(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def rows(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def manifest(p):
    out={}
    for l in p.read_text(encoding='utf-8-sig').splitlines():
        if l.strip():h,r=l.split('  ',1);out[r]=h
    return out
def owned(repo):
    out=[]
    for p in repo.rglob('*'):
        if not p.is_file():continue
        r=p.relative_to(repo).as_posix();w='/'+r
        if r.startswith(('out/','.git/')) or '/__pycache__/' in w or r.endswith('.pyc') or '/bin/' in w or '/obj/' in w or '/TestResults/' in w:continue
        if r==SKIP:continue
        out.append(r)
    return sorted(out)
def validate_manifest(repo):
    p=repo/SKIP;req(p.is_file(),'CP148 manifest missing');m=manifest(p);cur=owned(repo);req(set(m)==set(cur),f'manifest path drift missing={sorted(set(m)-set(cur))[:5]} extra={sorted(set(cur)-set(m))[:5]}')
    for r,h in m.items():req(sha(repo/r)==h,f'manifest hash drift {r}')
    return len(m)
def validate_smoke(root):
    b=root/'stage-a-smoke-merged';s=js(b/'summary.json');req(s['passed'] is True and int(s.get('failedGates',0))==0,'smoke gates');req(s['checkpoint']==148 and s['stageAScenarios']==6850 and s['integrationSmokeTrials']==6850 and s['executionErrors']==0,'smoke coverage');req(s['resolved']==6850 and s['resolvedGe25']==0 and s['turnCapSentinels']==0 and s['safeStalemates']==0 and s['nonstandoffOpenOrders']==0,'smoke signature');req(s['sourceMatrixUnmodified'] is True,'smoke matrix');rr=rows(b/'whole_combat_smoke_results.csv');req(len(rr)==6850 and all(not r['error'] and int(r['nonstandoff_open_orders'])==0 for r in rr),'smoke rows');return s
def validate_substantive(root):
    b=root/'stage-a-substantive-merged';s=js(b/'summary.json');req(s['passed'] is True and int(s.get('failedGates',0))==0,'substantive gates');req(s['checkpoint']==148 and s['stageAScenarios']==6850 and s['trialsPerScenario']==500 and s['substantiveCombatTrials']==3425000,'substantive coverage');req(s['combatDoctrine']=='cp147_tactical_utility' and s['baseMaxTpDemandPolicy']=='all-installed-normal-combat-demand-no-overload' and s['strategicParetoPolicy']=='combat-gated-before-resource-robustness','substantive policies');req(s['sourceMatrixUnmodified'] is True and s['tuningAllowed'] is False and s['automaticPromotion'] is False and s['stageBAutomatic'] is False,'substantive boundary')
    sr=rows(b/'scenario_response_surface.csv');req(len(sr)==6850,'scenario surface rows')
    parts=('weapon','sensor','ecm','eccm','pds','shield_hardener','shield_recharge','armor_regen','damage_control')
    for r in sr:
        req(int(r['error_trials'])==0,'substantive trial error')
        for side in ('a','b'):
            demand=float(r[f'{side}_base_max_installed_tp_demand']);req(demand>0,'max TP demand nonpositive')
            total=sum(float(r[f'{side}_base_max_tp_{x}']) for x in parts);req(abs(total-demand)<1e-9,'max TP breakdown mismatch')
            req(float(r[f'{side}_mean_tp_allocated_per_turn'])>=0 and float(r[f'{side}_peak_tp_allocated_per_turn'])>=0,'allocated TP negative')
    tp=rows(b/'tp_load_response_surface.csv');tptl=rows(b/'tp_load_weapon_tl_summary.csv');strategic=rows(b/'combat_gated_strategic_viability.csv');roles=rows(b/'role_response_summary.csv')
    req(len(tp)==1750 and len(tptl)==35 and len(strategic)==35 and len(roles)==35,'CP148 analysis artifact row counts')
    req(all(not(int(r['strategic_pareto_viable']) and not int(r['combat_viability_gate'])) for r in strategic),'strategic frontier bypassed combat gate')
    req(all(int(r['resource_or_robustness_only_frontier'])==0 for r in strategic),'resource-only frontier resurrected')
    return s
def validate_native(root,final):
    n='CP148_NATIVE_ACCEPTANCE_SUMMARY.json' if final else 'CP148_REPOSITORY_ONLY_ACCEPTANCE.json';s=js(root/n);req(s['checkpoint']==148 and not s.get('failedGates',[]),'native identity/gates');req(s['python'].startswith('Python 3.13') and s['dotnetSdk']=='8.0.423' and s['buildPassed'] is True,'runtimes/build');req(s['pythonTestsPassed']==358 and s['xunitPassed']==934 and s['xunitFailed']==0 and s['xunitSkipped']==0,'unit tests');req(s['scenarioRunnerSelfTestsPassed']==70 and s['researchParityPassed']==25,'runner/parity');req(s['cp147FocusedTestsPassed']==18 and s['cp148FocusedTestsPassed']==12 and s['cp146DoctrineFixtureCases']==9 and s['cp147UtilityFixtureCases']==10,'focused/fixtures');req(s['sourceMatrixUnmodified'] is True and s['tuningAllowed'] is False and s['automaticPromotion'] is False and s['stageBAutomatic'] is False,'native boundary');req(s['smokeResolved']==6850 and s['smokeResolvedGe25']==0 and s['smokeTurnCapSentinels']==0 and s['smokeSafeStalemates']==0 and s['smokeNonstandoffOpenOrders']==0,'native smoke signature')
    if final:req(s['repositoryOnlyAccepted'] is True and s['substantiveStageACompleted'] is True and s['substantiveCombatTrials']==3425000,'final substantive completion')
    else:req(s['substantiveCombatTrials']==0,'RepositoryOnly ran substantive study')
    return s

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);ap.add_argument('--native-results');a=ap.parse_args();repo=Path(a.repo).resolve()
    try:
        d=js(repo/'tools/checkpoints/checkpoint-148/checkpoint_148_definition.json');req(d['checkpoint']==148 and d['expectedPythonTests']==358 and d['expectedXunitTests']==934 and d['substantiveCombatTrials']==3425000,'definition')
        count=validate_manifest(repo);req(sha(repo/'docs/design/player_technology/technology_numerical_matrix_v0_9.json')==MATRIX_SHA,'matrix drift')
        study=js(repo/'docs/archive/testing/pre-cp165-active/cp148_whole_combat_stage_a_tactical_utility_response_surface_study_v0_1.json');req(study['submittedCp147NativeResultsArchiveSha256']==CP147_NATIVE_SHA,'CP147 provenance')
        if a.native_results:
            root=Path(a.native_results).resolve();final=(root/'CP148_NATIVE_ACCEPTANCE_SUMMARY.json').is_file();validate_native(root,final);validate_smoke(root)
            if final:validate_substantive(root)
        print(f'       CP148 contract verified: {count} repository-owned files; CP147 accepted baseline hash-locked; 6,850 utility smoke + 3,425,000 substantive trial contract; no-overload max-TP and combat-gated Pareto enforced.')
        return 0
    except Exception as e:print(f'CP148 contract failure: {e}',file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
