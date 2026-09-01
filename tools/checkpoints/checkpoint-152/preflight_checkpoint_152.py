#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,sys,unittest
from pathlib import Path

MATRIX_SHA='3088b0a9eb45f6bf505c24513e8bb2ac878819db4ab464ccfea330243c82f194'
CONCEPT_SHA='f76ca6ce488ccb5ad1352f7d38b8c3d4657c12ed64d0c93cc45d2db605cc632f'
CP151_NATIVE_SHA='d660617c734404c5f9528f590d90d81b5e23fbb5591b0ebcc5662cb9e8fdaf6a'
CP151_MANIFEST='docs/validation/evidence/checkpoint-151/CP151_REPOSITORY_SHA256SUMS.txt'
CP151_MANIFEST_SHA='dc603c7d5c7a078354a15d2f8fd8c53e08697494c504b4407e3de1b6c26afb19'
CP152_MANIFEST='docs/validation/evidence/checkpoint-152/CP152_REPOSITORY_SHA256SUMS.txt'
ALLOWED={
 'README.md','CHAT_README.md','docs/README.md','docs/Prototype_TODO.md','docs/validation/README.md','docs/design/testing/README.md',
 'tools/simulation/starcluster_research/cli.py','tools/simulation/starcluster_research/whole_combat_stage_a_response_surface.py',
}
ADDITIONS={
 'docs/archive/testing/pre-cp165-active/cp152_direct_fire_joint_refinement_study_v0_1.json',
 'docs/validation/Checkpoint_152_Direct_Fire_K_Completion_And_Broad_Energy_Remapping.md',
 'tools/simulation/starcluster_research/direct_fire_joint_refinement.py',
 'tools/simulation/tests/test_cp152_direct_fire_joint_refinement.py',
 'tools/checkpoints/checkpoint-152/apply_checkpoint_152.ps1','tools/checkpoints/checkpoint-152/checkpoint_152_definition.json',
 'tools/checkpoints/checkpoint-152/preflight_checkpoint_152.py','tools/checkpoints/checkpoint-152/test_checkpoint_152_contract.py',
 'docs/validation/evidence/checkpoint-152/accepted-cp151/CP151_NATIVE_ACCEPTANCE_SUMMARY.json',
 'docs/validation/evidence/checkpoint-152/accepted-cp151/CP151_POINT_SCALE_AXIAL_FAMILY_EFFECTS.CSV',
 'docs/validation/evidence/checkpoint-152/accepted-cp151/CP151_POINT_SCALE_CANDIDATE_FAMILY_RESPONSE.CSV',
 'docs/validation/evidence/checkpoint-152/accepted-cp151/CP151_POINT_SCALE_CANDIDATE_LEDGER.CSV',
 'docs/validation/evidence/checkpoint-152/accepted-cp151/CP151_POINT_SCALE_CANDIDATE_PAIR_RESPONSE.CSV',
 'docs/validation/evidence/checkpoint-152/accepted-cp151/CP151_POINT_SCALE_FACTOR_FAMILY_MARGINALS.CSV',
 'docs/validation/evidence/checkpoint-152/accepted-cp151/CP151_POINT_SCALE_PAIRWISE_FACTOR_FAMILY_RESPONSE.CSV',
}
def req(x,m):
 if not x: raise AssertionError(m)
def sha(p): h=hashlib.sha256();h.update(p.read_bytes());return h.hexdigest()
def js(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def manifest(p):
 out={}
 for l in p.read_text(encoding='utf-8-sig').splitlines():
  if l.strip(): h,r=l.split('  ',1);out[r]=h
 return out
def owned(repo):
 out=set()
 for p in repo.rglob('*'):
  if not p.is_file():continue
  r=p.relative_to(repo).as_posix();w='/'+r
  if r.startswith(('out/','.git/')) or '/__pycache__/' in w or r.endswith('.pyc') or '/bin/' in w or '/obj/' in w or '/TestResults/' in w:continue
  if r==CP152_MANIFEST:continue
  out.add(r)
 return out
def count_suite(s):return sum(count_suite(x) if isinstance(x,unittest.TestSuite) else 1 for x in s)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);a=ap.parse_args();repo=Path(a.repo).resolve()
 try:
  d=js(repo/'tools/checkpoints/checkpoint-152/checkpoint_152_definition.json');req(d['checkpoint']==152 and d['baseCheckpoint']==151,'identity');req(d['expectedPythonTests']==426 and d['expectedPythonTestModules']==43,'python contract');req(d['expectedXunitTests']==934 and d['expectedFocusedCp152Tests']==18,'native contract');req(d['substantiveCombatTrials']==48195000 and d['smokeCombatTrials']==218700,'study scale');req(d['technologyProgressionRule'].startswith('intrinsic capability'),'progression rule')
  req(sha(repo/'docs/design/player_technology/technology_numerical_matrix_v0_9.json')==MATRIX_SHA,'matrix drift');req(sha(repo/'docs/archive/concepts/Star_Cluster_Game_Concept_v0.7x.docx')==CONCEPT_SHA,'Concept drift')
  p=repo/CP151_MANIFEST;req(p.is_file() and sha(p)==CP151_MANIFEST_SHA,'CP151 manifest drift');base=manifest(p)
  for rel,h in base.items():
   req((repo/rel).is_file(),f'missing CP151 file {rel}')
   if rel not in ALLOWED:req(sha(repo/rel)==h,f'unexpected CP151 baseline drift: {rel}')
  base_cs={r for r in base if r.endswith('.cs')};cur_cs={p.relative_to(repo).as_posix() for p in repo.rglob('*.cs') if '/bin/' not in '/'+p.relative_to(repo).as_posix() and '/obj/' not in '/'+p.relative_to(repo).as_posix()};req(cur_cs==base_cs,'CP152 must add/change no C# path')
  for rel in base_cs:req(sha(repo/rel)==base[rel],f'C# drift {rel}')
  expected=set(base)|{CP151_MANIFEST}|ADDITIONS;cur=owned(repo);req(cur==expected,f'path drift added={sorted(cur-expected)[:8]} missing={sorted(expected-cur)[:8]}')
  study=js(repo/'docs/archive/testing/pre-cp165-active/cp152_direct_fire_joint_refinement_study_v0_1.json');req(study['acceptedCp151NativeResultsArchiveSha256']==CP151_NATIVE_SHA,'CP151 provenance')
  sys.path.insert(0,str(repo/'tools/simulation'));from starcluster_research.direct_fire_joint_refinement import validate_study,validate_population,k_candidate_ledger,e_candidate_ledger,SUBSTANTIVE_COMBATS,SMOKE_COMBATS
  req(validate_study(study)==[],'study validation');req(validate_population(repo,study)==[],'population validation');req(len(k_candidate_ledger(repo,study))==2187 and len(e_candidate_ledger(repo,study))==2187,'candidate ledgers');req(SUBSTANTIVE_COMBATS==48195000 and SMOKE_COMBATS==218700,'constants')
  tests=sorted((repo/'tools/simulation/tests').glob('test_*.py'));req(len(tests)==43,f'Python module count {len(tests)}');suite=unittest.defaultTestLoader.discover(str(repo/'tools/simulation/tests'),pattern='test_*.py');req(count_suite(suite)==426,f'Python test count {count_suite(suite)}')
  print('CP152 preflight PASS: CP151 frozen/native evidence hash-locked; 426/43 Python tests discovered; K 3^5 completion + E 11-factor OA + data-selected K/E joint confirmation; 48,195,000 substantive combats; no numerical promotion.')
  return 0
 except Exception as e:
  print(f'CP152 preflight failure: {e}',file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
