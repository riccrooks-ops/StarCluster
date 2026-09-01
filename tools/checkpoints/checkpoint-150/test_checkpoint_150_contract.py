#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path

MATRIX_SHA='3088b0a9eb45f6bf505c24513e8bb2ac878819db4ab464ccfea330243c82f194'
CP149_NATIVE_SHA='18b60851e5138b8cb44f76b5f0e2bad533dbf8935d88c70a64565bcd1c46f565'
SKIP='docs/validation/evidence/checkpoint-150/CP150_REPOSITORY_SHA256SUMS.txt'
COUNTS={1:18,2:81,3:27,4:72,5:81,6:4,7:9,8:45,9:12}

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
    p=repo/SKIP;req(p.is_file(),'CP150 manifest missing');m=manifest(p);cur=owned(repo)
    req(set(m)==set(cur),f'manifest path drift missing={sorted(set(m)-set(cur))[:5]} extra={sorted(set(cur)-set(m))[:5]}')
    for r,h in m.items():req(sha(repo/r)==h,f'manifest hash drift {r}')
    return len(m)
def validate_plan(root):
    s=js(root/'kinetic-refinement-plan/summary.json');req(s['passed'] is True and not s['failedGates'],'plan gates')
    req(s['kineticContexts']==2600 and s['tlCandidateCount']==349,'plan design')
    req(s['candidateContextCells']==102900 and s['trialsPerCandidateContext']==200 and s['substantiveCombatTrials']==20580000 and s['smokeCombatTrials']==10290,'plan scale')
    return s
def validate_smoke(root):
    base=root/'kinetic-refinement-smoke';total_rows=total_trials=total_caps=0;seen=set()
    for tl in range(1,10):
        d=base/f'tl{tl:02d}';s=js(d/'summary.json');rr=rows(d/'kinetic_refinement_candidate_context_results.csv')
        expected_contexts=20 if tl==1 else 30;expected_rows=COUNTS[tl]*expected_contexts
        req(s['passed'] is True and not s['failedGates'] and s['checkpoint']==150 and s['smokePanel'] is True,'smoke batch gates')
        req(s['tl']==tl and s['candidateStart']==0 and s['candidateEnd']==COUNTS[tl] and s['candidates']==COUNTS[tl],'smoke candidates')
        req(s['contextsPerCandidate']==expected_contexts and s['candidateContextCells']==expected_rows and s['trialsPerContext']==1 and s['combatTrials']==expected_rows,'smoke scale')
        req(s['errors']==0 and len(rr)==expected_rows and all(int(r['error_trials'])==0 and int(r['trials'])==1 and int(r['k_spen'])==0 for r in rr),'smoke rows/errors')
        ids={r['candidate_id'] for r in rr};req(len(ids)==COUNTS[tl],'smoke candidate coverage');seen.update((tl,x) for x in ids)
        total_rows+=len(rr);total_trials+=int(s['combatTrials']);total_caps+=int(s['turnCapSentinels'])
    req(len(seen)==349 and total_rows==10290 and total_trials==10290,'smoke total coverage')
    return {'rows':total_rows,'trials':total_trials,'turnCaps':total_caps}
def validate_substantive(root):
    b=root/'kinetic-refinement-merged';s=js(b/'summary.json')
    req(s['passed'] is True and not s['failedGates'] and s['checkpoint']==150 and s['mode']=='merged-substantive','substantive gates')
    req(s['candidateContextCells']==102900 and s['kineticContexts']==2600 and s['tlCandidateCount']==349,'substantive population')
    req(s['trialsPerCandidateContext']==200 and s['substantiveCombatTrials']==20580000 and s['errorTrials']==0,'substantive trial coverage')
    req(s['tuningAllowed'] is False and s['automaticPromotion'] is False and s['stageBAutomatic'] is False,'substantive promotion boundary')
    sr=rows(b/'kinetic_refinement_candidate_context_results.csv');req(len(sr)==102900 and all(int(r['trials'])==200 and int(r['error_trials'])==0 and int(r['k_spen'])==0 for r in sr),'candidate-context surface')
    expected={
      'batch_merge_audit.csv':32,
      'kinetic_refinement_candidate_tl_response.csv':349,
      'kinetic_refinement_candidate_opponent_response.csv':1029,
      'kinetic_refinement_candidate_stratum_response.csv':3490,
      'kinetic_refinement_candidate_resource_response.csv':1745,
      'kinetic_refinement_candidate_armor_role_response.csv':349,
      'kinetic_refinement_combat_pareto.csv':349,
      'kinetic_refinement_parameter_marginals.csv':82,
      'kinetic_refinement_pairwise_response.csv':270,
      'kinetic_refinement_candidate_ledger.csv':349,
      'kinetic_refinement_design_summary.csv':9,
    }
    for name,n in expected.items():req(len(rows(b/name))==n,f'{name} row count')
    led=rows(b/'kinetic_refinement_candidate_ledger.csv');req(all(int(r['candidate_spen'])==0 and int(r['firing_tp_delta'])==0 and int(r['ammo_level'])==100 and int(r['identity_preserved'])==1 and int(r['promotion_allowed'])==0 for r in led),'ledger frozen factors/identity/promotion')
    return s
def validate_native(root,final):
    n='CP150_NATIVE_ACCEPTANCE_SUMMARY.json' if final else 'CP150_REPOSITORY_ONLY_ACCEPTANCE.json';s=js(root/n)
    req(s['checkpoint']==150 and not s.get('failedGates',[]),'native identity/gates')
    req(s['python'].startswith('Python 3.13') and s['dotnetSdk']=='8.0.423' and s['buildPassed'] is True,'runtimes/build')
    req(s['pythonTestsPassed']==390 and s['xunitPassed']==934 and s['xunitFailed']==0 and s['xunitSkipped']==0,'unit tests')
    req(s['scenarioRunnerSelfTestsPassed']==70 and s['researchParityPassed']==25,'runner/parity')
    req(s['cp149FocusedTestsPassed']==16 and s['cp150FocusedTestsPassed']==16 and s['cp146DoctrineFixtureCases']==9 and s['cp147UtilityFixtureCases']==10,'focused/fixtures')
    req(s['acceptedCp149EvidenceHashLocked'] is True and s['sourceMatrixUnmodified'] is True,'provenance/matrix')
    req(s['kineticContexts']==2600 and s['tlCandidateCount']==349 and s['candidateContextCells']==102900,'native design')
    req(s['smokeCombatTrials']==10290 and s['smokeErrors']==0,'native smoke')
    req(s['tuningAllowed'] is False and s['automaticPromotion'] is False and s['stageBAutomatic'] is False,'native boundary')
    if final:req(s['repositoryOnlyAccepted'] is True and s['substantiveSweepCompleted'] is True and s['substantiveCombatTrials']==20580000 and s['substantiveErrorTrials']==0,'final substantive completion')
    else:req(s['substantiveCombatTrials']==0,'RepositoryOnly ran substantive sweep')
    return s

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);ap.add_argument('--native-results');a=ap.parse_args();repo=Path(a.repo).resolve()
    try:
        d=js(repo/'tools/checkpoints/checkpoint-150/checkpoint_150_definition.json');req(d['checkpoint']==150 and d['expectedPythonTests']==390 and d['expectedXunitTests']==934 and d['substantiveCombatTrials']==20580000,'definition')
        count=validate_manifest(repo);req(sha(repo/'docs/design/player_technology/technology_numerical_matrix_v0_9.json')==MATRIX_SHA,'matrix drift')
        study=js(repo/'docs/archive/testing/pre-cp165-active/cp150_kinetic_viable_region_refinement_v0_1.json');req(study['acceptedCp149NativeResultsArchiveSha256']==CP149_NATIVE_SHA,'CP149 provenance')
        if a.native_results:
            root=Path(a.native_results).resolve();final=(root/'CP150_NATIVE_ACCEPTANCE_SUMMARY.json').is_file();validate_native(root,final);validate_plan(root);validate_smoke(root)
            if final:validate_substantive(root)
        print(f'       CP150 contract verified: {count} repository-owned files; accepted CP149 evidence hash-locked; 10,290 smoke combats and 20,580,000 substantive identity-preserving Kinetic refinement contract; TP/ammo/Space/SPEN frozen; no auto-promotion.')
        return 0
    except Exception as e:
        print(f'CP150 contract failure: {e}');return 1
if __name__=='__main__':raise SystemExit(main())
