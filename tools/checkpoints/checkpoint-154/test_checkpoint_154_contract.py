#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path

MATRIX_SHA='3088b0a9eb45f6bf505c24513e8bb2ac878819db4ab464ccfea330243c82f194'
CONCEPT_SHA='f76ca6ce488ccb5ad1352f7d38b8c3d4657c12ed64d0c93cc45d2db605cc632f'
PRODUCTION_PDS_SHA='1a731834a3956267aacbdde030561df2cef18121d91860cfbef1c5e851c10c99'
CP153_RESULTS_SHA='e1c0e18f2f99bd80df9cd45ac340cac96b7fe500882782bb978201a14e0bc588'
SKIP='docs/validation/evidence/checkpoint-154/CP154_REPOSITORY_SHA256SUMS.txt'

def req(x,m):
 if not x: raise AssertionError(m)
def sha(p): h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()
def js(p): return json.loads(p.read_text(encoding='utf-8-sig'))
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
 p=repo/SKIP;req(p.is_file(),'CP154 manifest missing');m=manifest(p);cur=owned(repo)
 req(set(m)==set(cur),f'manifest path drift missing={sorted(set(m)-set(cur))[:8]} extra={sorted(set(cur)-set(m))[:8]}')
 for r,h in m.items():req(sha(repo/r)==h,f'manifest hash drift {r}')
 return len(m)
def validate_plan(root):
 s=js(root/'pds-plan/summary.json');req(s['passed'] is True and not s.get('gates',{}).get('failed',[]),'plan gates')
 req(s['candidateTlRows']==14748 and s['broadContexts']==612 and s['deepContextsPerLadder']==3060,'plan population')
 req(s['screenCandidateContextCells']==1015416 and s['screenCombatTrials']==25385400,'screen scale')
 req(s['deepLadders']==24 and s['deepCombatTrials']==7344000 and s['substantiveCombatTrials']==32729400,'deep/total scale')
 req((root/'pds-plan/pds_matrix_history_audit.csv').is_file(),'history audit missing')
 req(len(rows(root/'pds-plan/pds_candidate_ledger.csv'))==14748,'plan candidate ledger rows')
 return s
def validate_smoke(root):
 specs=(('Kinetic','tl06_0241',12),('Energy','tl06_0248',36),('AMM','tl07_0669',24));total=0
 for fam,name,combats in specs:
  d=root/'pds-smoke'/fam.lower()/name;s=js(d/'summary.json');rr=rows(d/'pds_candidate_context_results.csv')
  req(s['passed'] is True and s['mode']=='candidate-smoke' and s['family']==fam and s['errors']==0,f'{fam} smoke gates')
  req(s['combatTrials']==combats,f'{fam} smoke scale');req(len(rr)*int(s['trialsPerCell'])==combats,f'{fam} smoke rows');total+=combats
 if total!=72:raise AssertionError('smoke total')
 return total
def validate_candidate_merge(root):
 d=root/'pds-candidate-merged';s=js(d/'summary.json')
 req(s['passed'] is True and s['candidates']==14748 and s['candidateContextCells']==1015416,'candidate merge population')
 req(s['combatTrials']==25385400 and s['errorTrials']==0,'candidate merge combat/errors')
 sr=rows(d/'pds_candidate_summary.csv');req(len(sr)==14748,'candidate summary rows')
 req((d/'pds_candidate_attacker_response.csv').is_file() and (d/'batch_merge_audit.csv').is_file(),'candidate merged outputs')
 fam={f:sum(1 for r in sr if r['family']==f) for f in ('Kinetic','Energy','AMM')};req(fam=={'Kinetic':3696,'Energy':4224,'AMM':6828},f'family candidate totals {fam}')
 return s
def validate_synthesis(root):
 d=root/'pds-ladder-synthesis';s=js(d/'summary.json');rr=rows(d/'pds_ladder_candidates.csv')
 req(s['passed'] is True and s['laddersPerFamily']==8 and s['deepLadders']==24 and s['ladderTlRows']==216,'ladder synthesis')
 req(len(rr)==216,'ladder rows');ids={r['ladder_id'] for r in rr};req(len(ids)==24,'ladder ids')
 fam={f:len({r['ladder_id'] for r in rr if r['family']==f}) for f in ('Kinetic','Energy','AMM')};req(fam=={'Kinetic':8,'Energy':8,'AMM':8},f'ladder families {fam}')
 req(all(int(float(r['reaction_capacity']))<=2 and int(float(r['range_one']))==0 for r in rr if r['family'] in ('Kinetic','Energy')),'K/E RC/range rule')
 req(all((int(float(r['reaction_capacity']))==3)==(int(float(r['range_one']))==1) for r in rr if r['family']=='AMM'),'AMM RC3/range-one rule')
 return s
def validate_deep(root):
 d=root/'pds-deep-merged';s=js(d/'summary.json');sr=rows(d/'pds_deep_ladder_summary.csv');resp=rows(d/'pds_deep_response.csv');tri=rows(d/'pds_triad_shortlist.csv')
 req(s['passed'] is True and s['ladders']==24 and s['ladderContextCells']==73440,'deep coverage')
 req(s['combatTrials']==7344000 and s['errorTrials']==0 and s['triadCombinations']==512,'deep combat/errors/triads')
 req(len(sr)==24 and len(tri)==512 and len(resp)>0,'deep output rows')
 req({f:sum(1 for r in sr if r['family']==f) for f in ('Kinetic','Energy','AMM')}=={'Kinetic':8,'Energy':8,'AMM':8},'deep family rows')
 return s
def validate_native(root,final):
 n='CP154_NATIVE_ACCEPTANCE_SUMMARY.json' if final else 'CP154_REPOSITORY_ONLY_ACCEPTANCE.json';s=js(root/n)
 req(s['checkpoint']==154 and not s.get('failedGates',[]),'native gates')
 req(str(s['python']).startswith('Python 3.13') and s['dotnetSdk']=='8.0.423' and s['buildPassed'] is True,'runtime/build')
 req(s['pythonTestsPassed']==472 and s['xunitPassed']==934 and s['xunitFailed']==0 and s['xunitSkipped']==0,'tests')
 req(s['scenarioRunnerSelfTestsPassed']==70 and s['researchParityPassed']==25,'runner/parity')
 req(s['cp153FocusedTestsPassed']==21 and s['cp154FocusedTestsPassed']==25,'focused')
 req(s['acceptedCp153EvidenceHashLocked'] is True and s['sourceMatrixUnmodified'] is True and s['conceptUnmodified'] is True and s['productionCSharpUnmodified'] is True,'provenance/authorities')
 req(s['pdsCandidateTlRows']==14748 and s['deepLadders']==24,'PDS population')
 req(s['pdsSmokeCombatTrials']==72 and s['smokeErrors']==0,'smoke')
 req(s['automaticPromotion'] is False and s['stageBAutomatic'] is False and s['tuningAllowed'] is False,'promotion')
 if final:
  req(s['repositoryOnlyAccepted'] is True and s['substantiveSweepCompleted'] is True,'final state')
  req(s['candidateScreenCombatTrials']==25385400 and s['deepConfirmationCombatTrials']==7344000 and s['substantiveCombatTrials']==32729400 and s['substantiveErrorTrials']==0,'final combat scale')
 else:req(s['substantiveCombatTrials']==0,'RepositoryOnly substantive')
 return s

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);ap.add_argument('--native-results');a=ap.parse_args();repo=Path(a.repo).resolve()
 try:
  d=js(repo/'tools/checkpoints/checkpoint-154/checkpoint_154_definition.json');req(d['checkpoint']==154 and d['expectedPythonTests']==472 and d['expectedXunitTests']==934 and d['substantiveCombatTrials']==32729400,'definition')
  count=validate_manifest(repo)
  req(sha(repo/'docs/design/player_technology/technology_numerical_matrix_v0_9.json')==MATRIX_SHA,'matrix drift')
  req(sha(repo/'docs/archive/concepts/Star_Cluster_Game_Concept_v0.7x.docx')==CONCEPT_SHA,'Concept drift')
  req(sha(repo/'src/StarCluster.Core/Combat/Missiles/MissileInterceptionPhaseContext.cs')==PRODUCTION_PDS_SHA,'production PDS drift')
  study=js(repo/'docs/archive/testing/pre-cp165-active/cp154_pds_lifecycle_closure_study_v0_1.json');req(study['acceptedCp153NativeResultsArchiveSha256']==CP153_RESULTS_SHA,'CP153 provenance')
  if a.native_results:
   root=Path(a.native_results).resolve();final=(root/'CP154_NATIVE_ACCEPTANCE_SUMMARY.json').is_file();validate_native(root,final);validate_plan(root);validate_smoke(root)
   if final:validate_candidate_merge(root);validate_synthesis(root);validate_deep(root)
  print(f'       CP154 contract verified: {count} repository-owned files; CP153 evidence hash-locked; 72 architecture smoke combats; 14,748 PDS candidate-TL points; 32,729,400 substantive combats; no automatic promotion.')
  return 0
 except Exception as e:
  print(f'CP154 contract failure: {e}');return 1
if __name__=='__main__':raise SystemExit(main())
