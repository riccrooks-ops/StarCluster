#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path

MATRIX_SHA='3088b0a9eb45f6bf505c24513e8bb2ac878819db4ab464ccfea330243c82f194'
CP150_NATIVE_SHA='79dd7051103ad4796c1664d21fe03c740a4c3369404a57fe0dc7754bf3ca5c07'
SKIP='docs/validation/evidence/checkpoint-151/CP151_REPOSITORY_SHA256SUMS.txt'
COUNTS={1:261,2:263,3:263,4:263,5:263,6:265,7:265,8:265,9:265}
CONTEXTS={1:450,2:800,3:800,4:800,5:800,6:800,7:800,8:800,9:800}

def req(x,m):
    if not x: raise AssertionError(m)
def sha(p): h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()
def js(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def rows(p):
    with p.open(encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))
def manifest(p):
    out={}
    for l in p.read_text(encoding='utf-8-sig').splitlines():
        if l.strip(): h,r=l.split('  ',1); out[r]=h
    return out
def owned(repo):
    out=[]
    for p in repo.rglob('*'):
        if not p.is_file(): continue
        r=p.relative_to(repo).as_posix(); w='/'+r
        if r.startswith(('out/','.git/')) or '/__pycache__/' in w or r.endswith('.pyc') or '/bin/' in w or '/obj/' in w or '/TestResults/' in w: continue
        if r==SKIP: continue
        out.append(r)
    return sorted(out)
def validate_manifest(repo):
    p=repo/SKIP; req(p.is_file(),'CP151 manifest missing'); m=manifest(p); cur=owned(repo)
    req(set(m)==set(cur),f'manifest path drift missing={sorted(set(m)-set(cur))[:5]} extra={sorted(set(cur)-set(m))[:5]}')
    for r,h in m.items(): req(sha(repo/r)==h,f'manifest hash drift {r}')
    return len(m)
def validate_plan(root):
    s=js(root/'point-scale-plan/summary.json'); req(s['passed'] is True and not s['failedGates'],'plan gates')
    req(s['tlCandidateCount']==2373 and s['candidateContextCells']==1807050,'plan design')
    req(s['trialsPerCandidateContext']==25 and s['substantiveCombatTrials']==45176250 and s['smokeCombatTrials']==118650,'plan scale')
    return s
def validate_equivalence(root):
    base=root/'point-scale-equivalence'; s=js(base/'summary.json'); rr=rows(base/'point_scale_equivalence_audit.csv')
    req(s['passed'] is True and not s['failedGates'] and s['checkpoint']==151,'equivalence gates')
    req(s['pairedScenarioIdentities']==6850 and s['legacyCombatExecutions']==6850 and s['scaledCombatExecutions']==6850 and s['mismatchedScenarioIdentities']==0,'equivalence coverage')
    req(len(rr)==6850 and all(int(r['mismatch'])==0 for r in rr),'equivalence rows')
    return s
def validate_smoke(root):
    base=root/'point-scale-smoke'; total_rows=total_trials=total_caps=0; seen=set()
    for tl in range(1,10):
        d=base/f'tl{tl:02d}'; s=js(d/'summary.json'); rr=rows(d/'point_scale_candidate_context_results.csv'); expected=COUNTS[tl]*50
        req(s['passed'] is True and not s['failedGates'] and s['checkpoint']==151 and s['smokePanel'] is True,'smoke gates')
        req(s['tl']==tl and s['candidateStart']==0 and s['candidateEnd']==COUNTS[tl] and s['candidates']==COUNTS[tl],'smoke candidates')
        req(s['contextsPerCandidate']==50 and s['candidateContextCells']==expected and s['trialsPerContext']==1 and s['combatTrials']==expected,'smoke scale')
        req(s['errors']==0 and len(rr)==expected and all(int(r['error_trials'])==0 and int(r['trials'])==1 for r in rr),'smoke rows/errors')
        ids={r['candidate_id'] for r in rr}; req(len(ids)==COUNTS[tl],'smoke candidate coverage'); seen.update((tl,x) for x in ids)
        total_rows+=len(rr); total_trials+=int(s['combatTrials']); total_caps+=int(s['turnCapSentinels'])
    req(len(seen)==2373 and total_rows==118650 and total_trials==118650,'smoke total coverage')
    return {'rows':total_rows,'trials':total_trials,'turnCaps':total_caps}
def validate_substantive(root):
    b=root/'point-scale-merged'; s=js(b/'summary.json')
    req(s['passed'] is True and not s['failedGates'] and s['checkpoint']==151 and s['mode']=='merged-substantive','substantive gates')
    req(s['tlCandidateCount']==2373 and s['candidateContextCells']==1807050,'substantive population')
    req(s['trialsPerCandidateContext']==25 and s['substantiveCombatTrials']==45176250 and s['errorTrials']==0,'substantive coverage')
    req(s['tuningAllowed'] is False and s['automaticPromotion'] is False and s['stageBAutomatic'] is False,'promotion boundary')
    expected_files={
        'batch_merge_audit.csv','point_scale_candidate_ledger.csv','point_scale_design_summary.csv','point_scale_aux_scaling_audit.csv',
        'point_scale_candidate_summary.csv','point_scale_candidate_family_response.csv','point_scale_candidate_pair_response.csv',
        'point_scale_candidate_resource_response.csv','point_scale_candidate_stratum_response.csv','point_scale_factor_family_marginals.csv',
        'point_scale_pairwise_factor_family_response.csv','point_scale_axial_family_effects.csv','research_center_scenario_response.csv'
    }
    for n in expected_files: req((b/n).is_file(),f'missing substantive artifact {n}')
    req(len(rows(b/'point_scale_candidate_ledger.csv'))==2373,'ledger rows')
    req(len(rows(b/'point_scale_design_summary.csv'))==9,'design rows')
    req(len(rows(b/'research_center_scenario_response.csv'))==6850,'center scenario rows')
    req(len(rows(b/'batch_merge_audit.csv'))==153,'batch audit rows')
    return s
def validate_native(root,final):
    n='CP151_NATIVE_ACCEPTANCE_SUMMARY.json' if final else 'CP151_REPOSITORY_ONLY_ACCEPTANCE.json'; s=js(root/n)
    req(s['checkpoint']==151 and not s.get('failedGates',[]),'native identity/gates')
    req(s['python'].startswith('Python 3.13') and s['dotnetSdk']=='8.0.423' and s['buildPassed'] is True,'runtimes/build')
    req(s['pythonTestsPassed']==408 and s['xunitPassed']==934 and s['xunitFailed']==0 and s['xunitSkipped']==0,'unit tests')
    req(s['scenarioRunnerSelfTestsPassed']==70 and s['researchParityPassed']==25,'runner/parity')
    req(s['cp150FocusedTestsPassed']==16 and s['cp151FocusedTestsPassed']==18 and s['cp146DoctrineFixtureCases']==9 and s['cp147UtilityFixtureCases']==10,'focused/fixtures')
    req(s['acceptedCp150EvidenceHashLocked'] is True and s['sourceMatrixUnmodified'] is True,'provenance/matrix')
    req(s['pointScale']==2 and s['tlCandidateCount']==2373 and s['candidateContextCells']==1807050,'native design')
    req(s['equivalencePairedScenarioIdentities']==6850 and s['equivalenceMismatches']==0,'native equivalence')
    req(s['smokeCombatTrials']==118650 and s['smokeErrors']==0,'native smoke')
    req(s['tuningAllowed'] is False and s['automaticPromotion'] is False and s['stageBAutomatic'] is False,'native boundary')
    if final: req(s['repositoryOnlyAccepted'] is True and s['substantiveSweepCompleted'] is True and s['substantiveCombatTrials']==45176250 and s['substantiveErrorTrials']==0,'final substantive completion')
    else: req(s['substantiveCombatTrials']==0,'RepositoryOnly ran substantive sweep')
    return s

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo',required=True); ap.add_argument('--native-results'); a=ap.parse_args(); repo=Path(a.repo).resolve()
    try:
        d=js(repo/'tools/checkpoints/checkpoint-151/checkpoint_151_definition.json'); req(d['checkpoint']==151 and d['expectedPythonTests']==408 and d['expectedXunitTests']==934 and d['substantiveCombatTrials']==45176250,'definition')
        count=validate_manifest(repo); req(sha(repo/'docs/design/player_technology/technology_numerical_matrix_v0_9.json')==MATRIX_SHA,'matrix drift')
        study=js(repo/'docs/archive/testing/pre-cp165-active/cp151_point_scale_multivariate_response_v0_1.json'); req(study['acceptedCp150NativeResultsArchiveSha256']==CP150_NATIVE_SHA,'CP150 provenance')
        if a.native_results:
            root=Path(a.native_results).resolve(); final=(root/'CP151_NATIVE_ACCEPTANCE_SUMMARY.json').is_file(); validate_native(root,final); validate_plan(root); validate_equivalence(root); validate_smoke(root)
            if final: validate_substantive(root)
        print(f'       CP151 contract verified: {count} repository-owned files; accepted CP150 evidence hash-locked; 6,850 paired x2-equivalence identities; 118,650 smoke combats; 45,176,250 substantive point-scale response combats; no auto-promotion.')
        return 0
    except Exception as e:
        print(f'CP151 contract failure: {e}'); return 1
if __name__=='__main__': raise SystemExit(main())
