#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys, unittest
from pathlib import Path

MATRIX_SHA='3088b0a9eb45f6bf505c24513e8bb2ac878819db4ab464ccfea330243c82f194'
CONCEPT_SHA='f76ca6ce488ccb5ad1352f7d38b8c3d4657c12ed64d0c93cc45d2db605cc632f'
PRODUCTION_PDS_SHA='1a731834a3956267aacbdde030561df2cef18121d91860cfbef1c5e851c10c99'
CP154_MANIFEST='docs/validation/evidence/checkpoint-154/CP154_REPOSITORY_SHA256SUMS.txt'
CP154_MANIFEST_SHA='4f5dcf7614d4fbc29066f325a91db75e54da9adb08441daaa9b433ed222df64f'
CP155_MANIFEST='docs/validation/evidence/checkpoint-155/CP155_REPOSITORY_SHA256SUMS.txt'
CP154_NATIVE_RESULTS_SHA='c93bbcb72fd0dba4625bdd5022f493a73daf239da53144d634cac345cae0e9bc'
ALLOWED={
 'README.md','CHAT_README.md','docs/README.md','docs/Prototype_TODO.md','docs/validation/README.md','docs/design/testing/README.md',
 'tools/simulation/starcluster_research/cli.py',
}
ADDITIONS={
 'docs/archive/testing/pre-cp165-active/cp155_pds_architecture_resynthesis_study_v0_1.json',
 'docs/validation/Checkpoint_155_PDS_Architecture_Constrained_Resynthesis_And_Kinetic_Boundary_Extension.md',
 'tools/simulation/starcluster_research/pds_architecture_resynthesis.py',
 'tools/simulation/tests/test_cp155_pds_architecture_resynthesis.py',
 'tools/checkpoints/checkpoint-155/apply_checkpoint_155.ps1',
 'tools/checkpoints/checkpoint-155/checkpoint_155_definition.json',
 'tools/checkpoints/checkpoint-155/preflight_checkpoint_155.py',
 'tools/checkpoints/checkpoint-155/test_checkpoint_155_contract.py',
 'docs/validation/evidence/checkpoint-155/accepted-cp154/CP154_NATIVE_ACCEPTANCE_SUMMARY.json',
 'docs/validation/evidence/checkpoint-155/accepted-cp154/CP154_PDS_CANDIDATE_SUMMARY.csv',
 'docs/validation/evidence/checkpoint-155/accepted-cp154/CP154_PDS_CANDIDATE_ATTACKER_RESPONSE.csv',
 'docs/validation/evidence/checkpoint-155/accepted-cp154/CP154_PDS_LADDER_CANDIDATES.csv',
 'docs/validation/evidence/checkpoint-155/accepted-cp154/CP154_PDS_DEEP_LADDER_SUMMARY.csv',
 'docs/validation/evidence/checkpoint-155/accepted-cp154/CP154_PDS_DEEP_RESPONSE.csv',
 'docs/validation/evidence/checkpoint-155/accepted-cp154/CP154_PDS_TRIAD_SHORTLIST.csv',
}

def req(x,m):
 if not x: raise AssertionError(m)
def sha(p): h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()
def js(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def manifest(p):
 out={}
 for l in p.read_text(encoding='utf-8-sig').splitlines():
  if l.strip(): h,r=l.split('  ',1); out[r]=h
 return out
def owned(repo):
 out=set()
 for p in repo.rglob('*'):
  if not p.is_file(): continue
  r=p.relative_to(repo).as_posix(); w='/'+r
  if r.startswith(('out/','.git/')) or '/__pycache__/' in w or r.endswith('.pyc') or '/bin/' in w or '/obj/' in w or '/TestResults/' in w: continue
  if r==CP155_MANIFEST: continue
  out.add(r)
 return out
def count_suite(s): return sum(count_suite(x) if isinstance(x,unittest.TestSuite) else 1 for x in s)
def powershell_delimiters_balanced(path):
 text=path.read_text(encoding='utf-8-sig'); stack=[]; pairs={')':'(',']':'[','}':'{'}; state='normal'; i=0
 while i<len(text):
  ch=text[i]
  if state=='comment':
   if ch=='\n': state='normal'
  elif state=='single':
   if ch=="'":
    if i+1<len(text) and text[i+1]=="'": i+=1
    else: state='normal'
  elif state=='double':
   if ch=='`': i+=1
   elif ch=='"': state='normal'
  else:
   if ch=='#': state='comment'
   elif ch=="'": state='single'
   elif ch=='"': state='double'
   elif ch in '([{': stack.append(ch)
   elif ch in ')]}':
    if not stack or stack[-1]!=pairs[ch]: return False
    stack.pop()
  i+=1
 return state in ('normal','comment') and not stack

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--repo',required=True); a=ap.parse_args(); repo=Path(a.repo).resolve()
 try:
  d=js(repo/'tools/checkpoints/checkpoint-155/checkpoint_155_definition.json')
  req(d['checkpoint']==155 and d['baseCheckpoint']==154,'identity')
  req(d['expectedPythonTests']==500 and d['expectedPythonTestModules']==46,'Python contract')
  req(d['expectedXunitTests']==934 and d['expectedFocusedCp155Tests']==28,'native test contract')
  req(d['pdsCandidateTlRows']==1846 and d['primaryContexts']==1560 and d['robustnessContexts']==300,'candidate/context design')
  req(d['baselineCombatTrials']==312000 and d['screenCombatTrials']==9619200 and d['deepCombatTrials']==5580000 and d['substantiveCombatTrials']==15511200,'study scale')
  req(d['deepLadders']==30 and d['laddersPerFamily']==10,'ladder contract')
  req(d['multiFlightBalanceDeferred'] is True and not d['automaticPromotion'],'scope contract')
  req('No global PDS equality target' in d['balancePhilosophy'],'non-equality definition guard')
  req(powershell_delimiters_balanced(repo/'tools/checkpoints/checkpoint-155/apply_checkpoint_155.ps1'),'CP155 PowerShell delimiter/static parse guard')
  req(sha(repo/'docs/design/player_technology/technology_numerical_matrix_v0_9.json')==MATRIX_SHA,'matrix drift')
  req(sha(repo/'docs/archive/concepts/Star_Cluster_Game_Concept_v0.7x.docx')==CONCEPT_SHA,'Concept drift')
  req(sha(repo/'src/StarCluster.Core/Combat/Missiles/MissileInterceptionPhaseContext.cs')==PRODUCTION_PDS_SHA,'production PDS C# drift')
  p=repo/CP154_MANIFEST; req(p.is_file() and sha(p)==CP154_MANIFEST_SHA,'CP154 manifest drift'); base=manifest(p)
  for rel,h in base.items():
   req((repo/rel).is_file(),f'missing CP154 file {rel}')
   if rel not in ALLOWED: req(sha(repo/rel)==h,f'unexpected CP154 baseline drift: {rel}')
  base_cs={r for r in base if r.endswith('.cs')}; cur_cs={p.relative_to(repo).as_posix() for p in repo.rglob('*.cs') if '/bin/' not in '/'+p.relative_to(repo).as_posix() and '/obj/' not in '/'+p.relative_to(repo).as_posix()}
  req(cur_cs==base_cs,'CP155 must add/change no C# path')
  for rel in base_cs: req(sha(repo/rel)==base[rel],f'C# drift {rel}')
  expected=set(base)|ADDITIONS|{CP154_MANIFEST}; cur=owned(repo)
  req(cur==expected,f'path drift added={sorted(cur-expected)[:12]} missing={sorted(expected-cur)[:12]}')
  study=js(repo/'docs/archive/testing/pre-cp165-active/cp155_pds_architecture_resynthesis_study_v0_1.json')
  req(study['acceptedCp154NativeResultsArchiveSha256']==CP154_NATIVE_RESULTS_SHA,'CP154 native provenance')
  req('No global distance-to-50' in study['balancePhilosophy']['forbiddenSelectorObjective'],'equality guardrail')
  req(study['candidateDesign']['kinetic']['ammo']==75 and study['candidateDesign']['amm']['ammo']==25,'ammo fixed policy')
  req(study['deepConfirmation']['triadAnalysis'].startswith('All 10 x 10 x 10'),'triad design')
  sys.path.insert(0,str(repo/'tools/simulation'))
  from starcluster_research.pds_architecture_resynthesis import validate_study,validate_population,candidate_ledger,primary_contexts,robustness_contexts,run_plan,CP154_EVIDENCE_HASHES
  req(validate_study(study)==[],'study validation')
  req(validate_population(repo,study)==[],'population validation')
  ledger=candidate_ledger(repo,study); req(len(ledger)==1846,'candidate ledger')
  req(sum(r['family']=='Kinetic' for r in ledger)==576,'K total')
  req(sum(r['family']=='Energy' for r in ledger)==945,'E total')
  req(sum(r['family']=='AMM' for r in ledger)==325,'AMM total')
  req(min(int(r['base_chance_pp']) for r in ledger if r['family']=='Kinetic')==0,'K lower boundary')
  req({int(r['ammo']) for r in ledger if r['family']=='Kinetic'}=={75},'K ammo sweep forbidden')
  req({int(r['ammo']) for r in ledger if r['family']=='AMM'}=={25},'AMM ammo sweep forbidden')
  primary=primary_contexts(repo,study); robust=robustness_contexts(repo,study)
  req(len(primary)==1560 and len(robust)==300,'context counts')
  req({r['defender'] for r in primary}=={'K1','E7'},'primary defender scope')
  req({r['context_class'] for r in robust}=={'ROBUSTNESS'},'robustness class')
  import tempfile
  with tempfile.TemporaryDirectory() as td:
   plan=run_plan(repo,repo/'docs/archive/testing/pre-cp165-active/cp155_pds_architecture_resynthesis_study_v0_1.json',Path(td))
  req(plan['baselineCombatTrials']==312000 and plan['screenCombatTrials']==9619200 and plan['deepCombatTrials']==5580000 and plan['substantiveCombatTrials']==15511200,'planner scale')
  req(all((repo/r).is_file() and sha(repo/r)==h for r,h in CP154_EVIDENCE_HASHES.items()),'accepted CP154 evidence hashes')
  cp142=js(repo/'docs/archive/testing/pre-cp165-active/cp142_combat_surface_deep_reconciliation_study_v0_1.json')
  req(cp142['latestFullCombatEvidence']=='Combat Model Lab v17-v19','historical PDS evidence registration')
  code=(repo/'tools/simulation/starcluster_research/pds_architecture_resynthesis.py').read_text(encoding='utf-8')
  req('triad_selection_score' not in code and 'abs(decisive-.5)' not in code,'hidden equality objective')
  tests=sorted((repo/'tools/simulation/tests').glob('test_*.py')); req(len(tests)==46,f'Python module count {len(tests)}')
  suite=unittest.defaultTestLoader.discover(str(repo/'tools/simulation/tests'),pattern='test_*.py'); n=count_suite(suite); req(n==500,f'Python test count {n}')
  print('CP155 preflight PASS: CP154 native PDS evidence hash-locked; 500/46 Python tests discovered; 1,846 focused PDS candidate-TL points; K RC2 lower boundary extended to base chance 0; K/AMM ammo fixed; no global equalization objective; 15,511,200 substantive combats; no production promotion.')
  return 0
 except Exception as e:
  print(f'CP155 preflight failure: {e}',file=sys.stderr); return 1
if __name__=='__main__': raise SystemExit(main())
