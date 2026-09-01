#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path

MATRIX_SHA='3088b0a9eb45f6bf505c24513e8bb2ac878819db4ab464ccfea330243c82f194'
CP151_NATIVE_SHA='d660617c734404c5f9528f590d90d81b5e23fbb5591b0ebcc5662cb9e8fdaf6a'
SKIP='docs/validation/evidence/checkpoint-152/CP152_REPOSITORY_SHA256SUMS.txt'

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
 p=repo/SKIP;req(p.is_file(),'CP152 manifest missing');m=manifest(p);cur=owned(repo);req(set(m)==set(cur),f'manifest path drift missing={sorted(set(m)-set(cur))[:5]} extra={sorted(set(cur)-set(m))[:5]}')
 for r,h in m.items():req(sha(repo/r)==h,f'manifest hash drift {r}')
 return len(m)
def validate_plan(root):
 s=js(root/'direct-fire-plan/summary.json');req(s['passed'] is True and not s['failedGates'],'plan gates');req(s['kTlCandidates']==2187 and s['eTlCandidates']==2187,'candidate counts');req(s['kCombatTrials']==15795000 and s['eCombatTrials']==31590000 and s['jointCombatTrials']==810000 and s['totalCombatTrials']==48195000,'plan combat scale');req(s['smokeCombatTrials']==218700,'smoke scale');return s
def validate_smoke(root):
 total=0
 for lane in ('K','E'):
  for tl in range(1,10):
   d=root/'direct-fire-smoke'/lane/f'tl{tl:02d}';s=js(d/'summary.json');rp=d/f'direct_fire_{lane.lower()}_candidate_context_results.csv';rr=rows(rp);req(s['passed'] is True and s['lane']==lane and s['smokePanel'] is True,'smoke gates');req(s['candidates']==243 and s['contextsPerCandidate']==50 and s['combatTrials']==12150 and s['errors']==0,'smoke scale');req(len(rr)==12150 and all(int(r['error_trials'])==0 for r in rr),'smoke rows');total+=int(s['combatTrials'])
 req(total==218700,'smoke total');return total
def validate_lane(root,lane,expected_trials,expected_combats):
 d=root/f'direct-fire-{lane.lower()}-merged';s=js(d/'summary.json');req(s['passed'] is True and s['lane']==lane,'lane merge');req(s['combatTrials']==expected_combats and s['errorTrials']==0,'lane combats/errors');req((d/f'direct_fire_{lane.lower()}_candidate_summary.csv').is_file(),'candidate summary missing');req((d/f'direct_fire_{lane.lower()}_candidate_opponent_response.csv').is_file(),'opponent response missing');req((d/f'direct_fire_{lane.lower()}_factor_marginals.csv').is_file(),'marginals missing');req((d/f'direct_fire_{lane.lower()}_pairwise_response.csv').is_file(),'pairwise missing');return s
def validate_joint(root):
 sel=js(root/'direct-fire-joint-select/summary.json');req(sel['passed'] is True and sel['jointTlCandidates']==81,'joint selection');req(len(rows(root/'direct-fire-joint-select/direct_fire_k_shortlist.csv'))==27,'K shortlist');req(len(rows(root/'direct-fire-joint-select/direct_fire_e_shortlist.csv'))==27,'E shortlist');req(len(rows(root/'direct-fire-joint-select/direct_fire_joint_candidate_ledger.csv'))==81,'joint ledger');d=root/'direct-fire-joint-merged';s=js(d/'summary.json');req(s['passed'] is True and s['jointCombatTrials']==810000 and s['errorTrials']==0,'joint merge');req(len(rows(d/'direct_fire_joint_response.csv'))==81,'joint response rows');return s
def validate_native(root,final):
 n='CP152_NATIVE_ACCEPTANCE_SUMMARY.json' if final else 'CP152_REPOSITORY_ONLY_ACCEPTANCE.json';s=js(root/n);req(s['checkpoint']==152 and not s.get('failedGates',[]),'native gates');req(s['python'].startswith('Python 3.13') and s['dotnetSdk']=='8.0.423' and s['buildPassed'] is True,'runtime/build');req(s['pythonTestsPassed']==426 and s['xunitPassed']==934 and s['xunitFailed']==0 and s['xunitSkipped']==0,'tests');req(s['scenarioRunnerSelfTestsPassed']==70 and s['researchParityPassed']==25,'runner/parity');req(s['cp151FocusedTestsPassed']==18 and s['cp152FocusedTestsPassed']==18,'focused');req(s['acceptedCp151EvidenceHashLocked'] is True and s['sourceMatrixUnmodified'] is True,'provenance/matrix');req(s['smokeCombatTrials']==218700 and s['smokeErrors']==0,'smoke');req(s['automaticPromotion'] is False and s['stageBAutomatic'] is False and s['tuningAllowed'] is False,'promotion')
 if final:req(s['repositoryOnlyAccepted'] is True and s['substantiveSweepCompleted'] is True and s['substantiveCombatTrials']==48195000 and s['substantiveErrorTrials']==0 and s['jointTlCandidates']==81,'final completion')
 else:req(s['substantiveCombatTrials']==0,'RepositoryOnly substantive')
 return s
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);ap.add_argument('--native-results');a=ap.parse_args();repo=Path(a.repo).resolve()
 try:
  d=js(repo/'tools/checkpoints/checkpoint-152/checkpoint_152_definition.json');req(d['checkpoint']==152 and d['expectedPythonTests']==426 and d['expectedXunitTests']==934 and d['substantiveCombatTrials']==48195000,'definition');count=validate_manifest(repo);req(sha(repo/'docs/design/player_technology/technology_numerical_matrix_v0_9.json')==MATRIX_SHA,'matrix drift');study=js(repo/'docs/archive/testing/pre-cp165-active/cp152_direct_fire_joint_refinement_study_v0_1.json');req(study['acceptedCp151NativeResultsArchiveSha256']==CP151_NATIVE_SHA,'CP151 provenance')
  if a.native_results:
   root=Path(a.native_results).resolve();final=(root/'CP152_NATIVE_ACCEPTANCE_SUMMARY.json').is_file();validate_native(root,final);validate_plan(root);validate_smoke(root)
   if final:validate_lane(root,'K',25,15795000);validate_lane(root,'E',50,31590000);validate_joint(root)
  print(f'       CP152 contract verified: {count} repository-owned files; CP151 evidence hash-locked; 218,700 smoke combats; 48,195,000 substantive K/E/joint combats; no automatic promotion.')
  return 0
 except Exception as e:
  print(f'CP152 contract failure: {e}');return 1
if __name__=='__main__':raise SystemExit(main())
