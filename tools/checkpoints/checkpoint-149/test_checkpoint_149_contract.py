#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path
MATRIX_SHA='3088b0a9eb45f6bf505c24513e8bb2ac878819db4ab464ccfea330243c82f194'
CP148_NATIVE_SHA='b00c97b620cc7824760a8af5b41e0e888bb1d7ace16e3d51d426473c6a86788e'
SKIP='docs/validation/evidence/checkpoint-149/CP149_REPOSITORY_SHA256SUMS.txt'

def req(x,m):
    if not x: raise AssertionError(m)
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
    p=repo/SKIP;req(p.is_file(),'CP149 manifest missing');m=manifest(p);cur=owned(repo)
    req(set(m)==set(cur),f'manifest path drift missing={sorted(set(m)-set(cur))[:5]} extra={sorted(set(cur)-set(m))[:5]}')
    for r,h in m.items():req(sha(repo/r)==h,f'manifest hash drift {r}')
    return len(m)
def validate_plan(root):
    s=js(root/'kinetic-sweep-plan/summary.json');req(s['passed'] is True and not s['failedGates'],'plan gates')
    req(s['kineticContexts']==2600 and s['factors']==7 and s['candidatesPerTl']==163 and s['tlCandidateCount']==1467,'plan design')
    req(s['candidateContextCells']==423800 and s['substantiveCombatTrials']==42380000 and s['spaceEnvelopeRows']==2250,'plan scale')
    return s
def validate_smoke(root):
    base=root/'kinetic-sweep-smoke';total_rows=total_trials=total_caps=0;seen=set()
    for tl in range(1,10):
        d=base/f'tl{tl:02d}';s=js(d/'summary.json');rr=rows(d/'kinetic_candidate_context_results.csv')
        expected_contexts=20 if tl==1 else 30;expected_rows=163*expected_contexts
        req(s['passed'] is True and not s['failedGates'] and s['checkpoint']==149 and s['smokePanel'] is True,'smoke batch gates')
        req(s['tl']==tl and s['candidateStart']==0 and s['candidateEnd']==163 and s['candidates']==163,'smoke candidates')
        req(s['contextsPerCandidate']==expected_contexts and s['candidateContextCells']==expected_rows and s['trialsPerContext']==1 and s['combatTrials']==expected_rows,'smoke scale')
        req(s['errors']==0 and len(rr)==expected_rows and all(int(r['error_trials'])==0 and int(r['trials'])==1 for r in rr),'smoke rows/errors')
        ids={r['candidate_id'] for r in rr};req(len(ids)==163,'smoke candidate coverage');seen.update((tl,x) for x in ids)
        total_rows+=len(rr);total_trials+=int(s['combatTrials']);total_caps+=int(s['turnCapSentinels'])
    req(len(seen)==1467 and total_rows==42380 and total_trials==42380,'smoke total coverage')
    return {'rows':total_rows,'trials':total_trials,'turnCaps':total_caps}
def validate_substantive(root):
    b=root/'kinetic-sweep-merged';s=js(b/'summary.json')
    req(s['passed'] is True and not s['failedGates'] and s['checkpoint']==149 and s['mode']=='merged-substantive','substantive gates')
    req(s['candidateContextCells']==423800 and s['kineticContexts']==2600 and s['candidatesPerTl']==163 and s['tlCandidateCount']==1467,'substantive population')
    req(s['trialsPerCandidateContext']==100 and s['substantiveCombatTrials']==42380000 and s['errorTrials']==0,'substantive trial coverage')
    req(s['tuningAllowed'] is False and s['automaticPromotion'] is False and s['stageBAutomatic'] is False,'substantive promotion boundary')
    sr=rows(b/'kinetic_candidate_context_results.csv');req(len(sr)==423800 and all(int(r['trials'])==100 and int(r['error_trials'])==0 and int(r['k_spen'])==0 for r in sr),'candidate-context surface')
    expected={
      'kinetic_candidate_tl_response.csv':1467,'kinetic_candidate_opponent_response.csv':4238,'kinetic_candidate_stratum_response.csv':14670,'kinetic_candidate_resource_response.csv':7335,'kinetic_candidate_armor_role_response.csv':1467,
      'kinetic_axial_effects.csv':126,'kinetic_pairwise_interactions.csv':189,'kinetic_combat_pareto_candidates.csv':1467,'kinetic_candidate_ledger.csv':1467,'kinetic_space_envelope.csv':2250,
    }
    for name,n in expected.items():req(len(rows(b/name))==n,f'{name} row count')
    led=rows(b/'kinetic_candidate_ledger.csv');req(all(int(r['candidate_spen'])==0 and int(r['promotion_allowed'])==0 for r in led),'ledger SPEN/promotion')
    return s
def validate_native(root,final):
    n='CP149_NATIVE_ACCEPTANCE_SUMMARY.json' if final else 'CP149_REPOSITORY_ONLY_ACCEPTANCE.json';s=js(root/n)
    req(s['checkpoint']==149 and not s.get('failedGates',[]),'native identity/gates')
    req(s['python'].startswith('Python 3.13') and s['dotnetSdk']=='8.0.423' and s['buildPassed'] is True,'runtimes/build')
    req(s['pythonTestsPassed']==374 and s['xunitPassed']==934 and s['xunitFailed']==0 and s['xunitSkipped']==0,'unit tests')
    req(s['scenarioRunnerSelfTestsPassed']==70 and s['researchParityPassed']==25,'runner/parity')
    req(s['cp148FocusedTestsPassed']==12 and s['cp149FocusedTestsPassed']==16 and s['cp146DoctrineFixtureCases']==9 and s['cp147UtilityFixtureCases']==10,'focused/fixtures')
    req(s['acceptedCp148EvidenceHashLocked'] is True and s['sourceMatrixUnmodified'] is True,'provenance/matrix')
    req(s['kineticContexts']==2600 and s['factors']==7 and s['candidatesPerTl']==163 and s['tlCandidateCount']==1467,'native design')
    req(s['smokeCombatTrials']==42380 and s['smokeErrors']==0,'native smoke')
    req(s['tuningAllowed'] is False and s['automaticPromotion'] is False and s['stageBAutomatic'] is False,'native boundary')
    if final:req(s['repositoryOnlyAccepted'] is True and s['substantiveSweepCompleted'] is True and s['substantiveCombatTrials']==42380000 and s['substantiveErrorTrials']==0,'final substantive completion')
    else:req(s['substantiveCombatTrials']==0,'RepositoryOnly ran substantive sweep')
    return s

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);ap.add_argument('--native-results');a=ap.parse_args();repo=Path(a.repo).resolve()
    try:
        d=js(repo/'tools/checkpoints/checkpoint-149/checkpoint_149_definition.json');req(d['checkpoint']==149 and d['expectedPythonTests']==374 and d['expectedXunitTests']==934 and d['substantiveCombatTrials']==42380000,'definition')
        count=validate_manifest(repo);req(sha(repo/'docs/design/player_technology/technology_numerical_matrix_v0_9.json')==MATRIX_SHA,'matrix drift')
        study=js(repo/'docs/archive/testing/pre-cp165-active/cp149_kinetic_full_characteristic_multivariate_sweep_v0_1.json');req(study['acceptedCp148NativeResultsArchiveSha256']==CP148_NATIVE_SHA,'CP148 provenance')
        if a.native_results:
            root=Path(a.native_results).resolve();final=(root/'CP149_NATIVE_ACCEPTANCE_SUMMARY.json').is_file();validate_native(root,final);validate_plan(root);validate_smoke(root)
            if final:validate_substantive(root)
        print(f'       CP149 contract verified: {count} repository-owned files; CP148 accepted baseline hash-locked; 42,380 smoke combats and 42,380,000 substantive Kinetic sweep contract; SPEN fixed zero; no auto-promotion.')
        return 0
    except Exception as e:
        print(f'CP149 contract failure: {e}');return 1
if __name__=='__main__':raise SystemExit(main())
