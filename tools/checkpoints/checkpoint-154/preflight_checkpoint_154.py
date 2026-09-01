#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys, unittest
from pathlib import Path

MATRIX_SHA='3088b0a9eb45f6bf505c24513e8bb2ac878819db4ab464ccfea330243c82f194'
CONCEPT_SHA='f76ca6ce488ccb5ad1352f7d38b8c3d4657c12ed64d0c93cc45d2db605cc632f'
PRODUCTION_PDS_SHA='1a731834a3956267aacbdde030561df2cef18121d91860cfbef1c5e851c10c99'
CP153_MANIFEST='docs/validation/evidence/checkpoint-153/CP153_REPOSITORY_SHA256SUMS.txt'
CP153_MANIFEST_SHA='7f6c47578a0d69dbb98cad347ebf226bfa59bf7279c390e5e878ffd4ef69c14e'
CP154_MANIFEST='docs/validation/evidence/checkpoint-154/CP154_REPOSITORY_SHA256SUMS.txt'
CP153_NATIVE_RESULTS_SHA='e1c0e18f2f99bd80df9cd45ac340cac96b7fe500882782bb978201a14e0bc588'
ALLOWED={
 'README.md','CHAT_README.md','docs/README.md','docs/Prototype_TODO.md','docs/validation/README.md','docs/design/testing/README.md',
 'tools/simulation/starcluster_research/cli.py','tools/simulation/starcluster_research/ecology.py','tools/simulation/starcluster_research/canonical_combat.py',
}
ADDITIONS={
 CP153_MANIFEST,
 'docs/archive/testing/pre-cp165-active/cp154_pds_lifecycle_closure_study_v0_1.json',
 'docs/validation/Checkpoint_154_PDS_Family_Architecture_Reconciliation_And_Lifecycle_Closure.md',
 'tools/simulation/starcluster_research/pds_lifecycle_closure.py',
 'tools/simulation/tests/test_cp154_pds_lifecycle_closure.py',
 'tools/checkpoints/checkpoint-154/apply_checkpoint_154.ps1',
 'tools/checkpoints/checkpoint-154/checkpoint_154_definition.json',
 'tools/checkpoints/checkpoint-154/preflight_checkpoint_154.py',
 'tools/checkpoints/checkpoint-154/test_checkpoint_154_contract.py',
 'docs/validation/evidence/checkpoint-154/accepted-cp153/CP153_NATIVE_ACCEPTANCE_SUMMARY.json',
 'docs/validation/evidence/checkpoint-154/accepted-cp153/CP153_KINETIC_LADDER_CANDIDATES.csv',
 'docs/validation/evidence/checkpoint-154/accepted-cp153/CP153_ENERGY_LADDER_CANDIDATES.csv',
 'docs/validation/evidence/checkpoint-154/accepted-cp153/CP153_MISSILE_LADDER_CANDIDATES.csv',
 'docs/validation/evidence/checkpoint-154/accepted-cp153/CP153_DEEP_PACKAGE_SUMMARY.csv',
 'docs/validation/evidence/checkpoint-154/accepted-cp153/CP153_DEEP_FAMILY_RESPONSE.csv',
 'docs/validation/evidence/checkpoint-154/accepted-cp153/CP153_DEEP_PAIR_RESPONSE.csv',
 'docs/validation/evidence/checkpoint-154/accepted-cp153/CP153_DEEP_STRATUM_RESPONSE.csv',
 'docs/validation/evidence/checkpoint-154/accepted-cp153/CP153_SCREEN_PACKAGE_SUMMARY.csv',
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
  if r==CP154_MANIFEST: continue
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
  d=js(repo/'tools/checkpoints/checkpoint-154/checkpoint_154_definition.json')
  req(d['checkpoint']==154 and d['baseCheckpoint']==153,'identity')
  req(d['expectedPythonTests']==472 and d['expectedPythonTestModules']==45,'Python contract')
  req(d['expectedXunitTests']==934 and d['expectedFocusedCp154Tests']==25,'native test contract')
  req(d['pdsCandidateTlRows']==14748 and d['screenCandidateContextCells']==1015416,'candidate design')
  req(d['screenCombatTrials']==25385400 and d['deepCombatTrials']==7344000 and d['substantiveCombatTrials']==32729400,'study scale')
  req(d['deepLadders']==24 and d['laddersPerFamily']==8,'ladder contract')
  req(d['multiFlightBalanceDeferred'] is True and not d['automaticPromotion'],'scope contract')
  req(powershell_delimiters_balanced(repo/'tools/checkpoints/checkpoint-154/apply_checkpoint_154.ps1'),'CP154 PowerShell delimiter/static parse guard')
  req(sha(repo/'docs/design/player_technology/technology_numerical_matrix_v0_9.json')==MATRIX_SHA,'matrix drift')
  req(sha(repo/'docs/archive/concepts/Star_Cluster_Game_Concept_v0.7x.docx')==CONCEPT_SHA,'Concept drift')
  req(sha(repo/'src/StarCluster.Core/Combat/Missiles/MissileInterceptionPhaseContext.cs')==PRODUCTION_PDS_SHA,'production PDS C# drift')
  p=repo/CP153_MANIFEST; req(p.is_file() and sha(p)==CP153_MANIFEST_SHA,'CP153 manifest drift'); base=manifest(p)
  for rel,h in base.items():
   req((repo/rel).is_file(),f'missing CP153 file {rel}')
   if rel not in ALLOWED: req(sha(repo/rel)==h,f'unexpected CP153 baseline drift: {rel}')
  base_cs={r for r in base if r.endswith('.cs')}; cur_cs={p.relative_to(repo).as_posix() for p in repo.rglob('*.cs') if '/bin/' not in '/'+p.relative_to(repo).as_posix() and '/obj/' not in '/'+p.relative_to(repo).as_posix()}
  req(cur_cs==base_cs,'CP154 must add/change no C# path')
  for rel in base_cs: req(sha(repo/rel)==base[rel],f'C# drift {rel}')
  expected=set(base)|ADDITIONS; cur=owned(repo)
  req(cur==expected,f'path drift added={sorted(cur-expected)[:12]} missing={sorted(expected-cur)[:12]}')
  study=js(repo/'docs/archive/testing/pre-cp165-active/cp154_pds_lifecycle_closure_study_v0_1.json')
  req(study['acceptedCp153NativeResultsArchiveSha256']==CP153_NATIVE_RESULTS_SHA,'CP153 native provenance')
  arch=study['pdsArchitecture']
  req('first arriving Flight' in arch['reactionCapacity'],'RC ordering rule')
  req('two terminal opportunities' in arch['terminalWindows'],'K/E two-window rule')
  req('range-1 pre-terminal opportunity' in arch['ammRc3'],'AMM RC3/range-one rule')
  req('only when that extra reaction is actually fired' in arch['energyIdentity'],'Energy strain-on-use rule')
  req('simultaneous multi-Flight' in arch['singleArrivalScope'],'multi-Flight deferral')
  sys.path.insert(0,str(repo/'tools/simulation'))
  from starcluster_research.pds_lifecycle_closure import validate_study,validate_population,pds_candidate_ledger,pds_contexts,CP153_EVIDENCE_HASHES
  req(validate_study(study)==[],'study validation')
  req(validate_population(repo,study)==[],'population validation')
  ledger=pds_candidate_ledger(repo,study); req(len(ledger)==14748,'candidate ledger')
  by={(f,tl):0 for f in ('Kinetic','Energy','AMM') for tl in range(1,10)}
  for r in ledger: by[(r['family'],int(r['tl']))]+=1
  req([by[('Kinetic',tl)] for tl in range(1,10)]==[378,378,420,420,420,420,420,420,420],'K candidate counts')
  req([by[('Energy',tl)] for tl in range(1,10)]==[480,480,480,432,432,480,480,480,480],'E candidate counts')
  req([by[('AMM',tl)] for tl in range(1,10)]==[432,432,432,432,1020,1020,1020,1020,1020],'AMM candidate counts')
  broad=pds_contexts(repo,study,True); deep=pds_contexts(repo,study,False)
  req(len(broad)==612 and len(deep)==3060,'context counts')
  bc={tl:sum(1 for x in broad if int(x['tl'])==tl) for tl in range(1,10)}
  cells=sum(by[(fam,tl)]*bc[tl] for fam in ('Kinetic','Energy','AMM') for tl in range(1,10))
  req(cells==1015416 and cells*25==25385400,'screen scale')
  req(24*len(deep)*100==7344000 and cells*25+24*len(deep)*100==32729400,'deep/total scale')
  req(all((repo/r).is_file() and sha(repo/r)==h for r,h in CP153_EVIDENCE_HASHES.items()),'accepted CP153 evidence hashes')
  tests=sorted((repo/'tools/simulation/tests').glob('test_*.py')); req(len(tests)==45,f'Python module count {len(tests)}')
  suite=unittest.defaultTestLoader.discover(str(repo/'tools/simulation/tests'),pattern='test_*.py'); n=count_suite(suite); req(n==472,f'Python test count {n}')
  print('CP154 preflight PASS: CP153 frozen/native evidence hash-locked; 472/45 Python tests discovered; 14,748 PDS candidate-TL points; K/E two-window and AMM RC3/range-one architecture guarded; E TP/Strain RC2 covered; 32,729,400 substantive combats; no production promotion.')
  return 0
 except Exception as e:
  print(f'CP154 preflight failure: {e}',file=sys.stderr); return 1
if __name__=='__main__': raise SystemExit(main())
