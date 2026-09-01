#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys, unittest
from pathlib import Path

MATRIX_SHA='3088b0a9eb45f6bf505c24513e8bb2ac878819db4ab464ccfea330243c82f194'
CONCEPT_SHA='f76ca6ce488ccb5ad1352f7d38b8c3d4657c12ed64d0c93cc45d2db605cc632f'
CP152_MANIFEST='docs/validation/evidence/checkpoint-152/CP152_REPOSITORY_SHA256SUMS.txt'
CP152_MANIFEST_SHA='2ebe1f4a7406bc77ea2c63b10edd8ae3ff8242aef88d6190a545a6344b98ad92'
CP153_MANIFEST='docs/validation/evidence/checkpoint-153/CP153_REPOSITORY_SHA256SUMS.txt'
CP152_NATIVE_RESULTS_SHA='001f26f68494bf5c57d44df8244e686b1d4821c436129ccadff42ceaccf20f08'
ALLOWED={
 'README.md','CHAT_README.md','docs/README.md','docs/Prototype_TODO.md','docs/validation/README.md','docs/design/testing/README.md',
 'tools/simulation/starcluster_research/cli.py',
}
ADDITIONS={
 'docs/archive/testing/pre-cp165-active/cp153_four_main_ladder_synthesis_study_v0_1.json',
 'docs/validation/Checkpoint_153_Four_Main_Whole_Ladder_Synthesis_And_Energy_Closure.md',
 'tools/simulation/starcluster_research/four_main_ladder_synthesis.py',
 'tools/simulation/tests/test_cp153_four_main_ladder_synthesis.py',
 'tools/checkpoints/checkpoint-153/apply_checkpoint_153.ps1',
 'tools/checkpoints/checkpoint-153/checkpoint_153_definition.json',
 'tools/checkpoints/checkpoint-153/preflight_checkpoint_153.py',
 'tools/checkpoints/checkpoint-153/test_checkpoint_153_contract.py',
 'docs/validation/evidence/checkpoint-153/accepted-cp152/CP152_NATIVE_ACCEPTANCE_SUMMARY.json',
 'docs/validation/evidence/checkpoint-153/accepted-cp152/CP152_DIRECT_FIRE_K_CANDIDATE_SUMMARY.csv',
 'docs/validation/evidence/checkpoint-153/accepted-cp152/CP152_DIRECT_FIRE_K_FACTOR_MARGINALS.csv',
 'docs/validation/evidence/checkpoint-153/accepted-cp152/CP152_DIRECT_FIRE_K_PAIRWISE_RESPONSE.csv',
 'docs/validation/evidence/checkpoint-153/accepted-cp152/CP152_DIRECT_FIRE_E_CANDIDATE_SUMMARY.csv',
 'docs/validation/evidence/checkpoint-153/accepted-cp152/CP152_DIRECT_FIRE_E_FACTOR_MARGINALS.csv',
 'docs/validation/evidence/checkpoint-153/accepted-cp152/CP152_DIRECT_FIRE_E_PAIRWISE_RESPONSE.csv',
 'docs/validation/evidence/checkpoint-153/accepted-cp152/CP152_DIRECT_FIRE_JOINT_RESPONSE.csv',
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
  if r==CP153_MANIFEST: continue
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
  d=js(repo/'tools/checkpoints/checkpoint-153/checkpoint_153_definition.json')
  req(d['checkpoint']==153 and d['baseCheckpoint']==152,'identity')
  req(d['expectedPythonTests']==447 and d['expectedPythonTestModules']==44,'python contract')
  req(d['expectedXunitTests']==934 and d['expectedFocusedCp153Tests']==21,'native contract')
  req(d['energyCandidatesPerTl']==422 and d['energyPairwiseCandidatesPerTl']==264 and d['energyTlCandidates']==3798,'Energy design')
  req(d['substantiveCombatTrials']==102346800 and d['energySmokeCombatTrials']==189900,'study scale')
  req(powershell_delimiters_balanced(repo/'tools/checkpoints/checkpoint-153/apply_checkpoint_153.ps1'),'CP153 PowerShell delimiter/static parse guard')
  req('Low conserves TP' in d['energyModeDoctrine'] and 'Overload is reserved' in d['energyModeDoctrine'],'Energy doctrine')
  req(sha(repo/'docs/design/player_technology/technology_numerical_matrix_v0_9.json')==MATRIX_SHA,'matrix drift')
  req(sha(repo/'docs/archive/concepts/Star_Cluster_Game_Concept_v0.7x.docx')==CONCEPT_SHA,'Concept drift')
  p=repo/CP152_MANIFEST; req(p.is_file() and sha(p)==CP152_MANIFEST_SHA,'CP152 manifest drift'); base=manifest(p)
  for rel,h in base.items():
   req((repo/rel).is_file(),f'missing CP152 file {rel}')
   if rel not in ALLOWED: req(sha(repo/rel)==h,f'unexpected CP152 baseline drift: {rel}')
  base_cs={r for r in base if r.endswith('.cs')}; cur_cs={p.relative_to(repo).as_posix() for p in repo.rglob('*.cs') if '/bin/' not in '/'+p.relative_to(repo).as_posix() and '/obj/' not in '/'+p.relative_to(repo).as_posix()}
  req(cur_cs==base_cs,'CP153 must add/change no C# path')
  for rel in base_cs: req(sha(repo/rel)==base[rel],f'C# drift {rel}')
  expected=set(base)|{CP152_MANIFEST}|ADDITIONS; cur=owned(repo)
  req(cur==expected,f'path drift added={sorted(cur-expected)[:8]} missing={sorted(expected-cur)[:8]}')
  study=js(repo/'docs/archive/testing/pre-cp165-active/cp153_four_main_ladder_synthesis_study_v0_1.json'); req(study['acceptedCp152NativeResultsArchiveSha256']==CP152_NATIVE_RESULTS_SHA,'CP152 native provenance')
  sys.path.insert(0,str(repo/'tools/simulation'))
  from starcluster_research.four_main_ladder_synthesis import validate_study,validate_population,energy_candidate_ledger,E_COMBATS,E_SMOKE_COMBATS,SCREEN_COMBATS,DEEP_COMBATS,SUBSTANTIVE_COMBATS,PACKAGE_COUNT
  req(validate_study(study)==[],'study validation'); req(validate_population(repo,study)==[],'population validation')
  req(len(energy_candidate_ledger(repo,study))==3798,'Energy candidate ledger')
  req(E_COMBATS==82290000 and E_SMOKE_COMBATS==189900 and SCREEN_COMBATS==11836800 and DEEP_COMBATS==8220000 and SUBSTANTIVE_COMBATS==102346800 and PACKAGE_COUNT==432,'constants')
  tests=sorted((repo/'tools/simulation/tests').glob('test_*.py')); req(len(tests)==44,f'Python module count {len(tests)}')
  suite=unittest.defaultTestLoader.discover(str(repo/'tools/simulation/tests'),pattern='test_*.py'); req(count_suite(suite)==447,f'Python test count {count_suite(suite)}')
  print('CP153 preflight PASS: CP152 frozen/native evidence hash-locked; 447/44 Python tests discovered; 422 E candidates/TL with complete pairwise Strain 1-4 closure; 432 four-main ladder packages; 102,346,800 substantive combats; no numerical promotion.')
  return 0
 except Exception as e:
  print(f'CP153 preflight failure: {e}',file=sys.stderr); return 1
if __name__=='__main__': raise SystemExit(main())
