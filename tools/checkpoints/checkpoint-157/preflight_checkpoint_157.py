#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json,sys,unittest
from pathlib import Path
CP156_MAN='docs/validation/evidence/checkpoint-156/CP156_REPOSITORY_SHA256SUMS.txt'
CP156_MAN_SHA='dc0fe0f349e327bf9df2d0c09ccc53fcabb57ee76342b8bd1da915a23f028ea6'
MATRIX_SHA='3088b0a9eb45f6bf505c24513e8bb2ac878819db4ab464ccfea330243c82f194'
CONCEPT_SHA='f76ca6ce488ccb5ad1352f7d38b8c3d4657c12ed64d0c93cc45d2db605cc632f'
PDS_SHA='1a731834a3956267aacbdde030561df2cef18121d91860cfbef1c5e851c10c99'
ALLOWED={'README.md','CHAT_README.md','docs/README.md','docs/Prototype_TODO.md','docs/validation/README.md','docs/design/testing/README.md','docs/design/player_technology/README.md'}
def req(x,m):
 if not x: raise AssertionError(m)
def sha(p):h=hashlib.sha256();h.update(p.read_bytes());return h.hexdigest()
def js(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def rows(p):
 with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def manifest(p):
 out={}
 for l in p.read_text(encoding='utf-8-sig').splitlines():
  if l.strip():h,r=l.split('  ',1);out[r]=h
 return out
def count_suite(s): return sum(count_suite(x) if isinstance(x,unittest.TestSuite) else 1 for x in s)
def ps_balanced(path):
 text=path.read_text(encoding='utf-8-sig'); stack=[];pairs={')':'(',']':'[','}':'{'};state='normal';i=0
 while i<len(text):
  ch=text[i]
  if state=='comment':
   if ch=='\n':state='normal'
  elif state=='single':
   if ch=="'":
    if i+1<len(text) and text[i+1]=="'":i+=1
    else:state='normal'
  elif state=='double':
   if ch=='`':i+=1
   elif ch=='"':state='normal'
  else:
   if ch=='#':state='comment'
   elif ch=="'":state='single'
   elif ch=='"':state='double'
   elif ch in '([{':stack.append(ch)
   elif ch in ')]}':
    if not stack or stack[-1]!=pairs[ch]:return False
    stack.pop()
  i+=1
 return state in ('normal','comment') and not stack
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);a=ap.parse_args();repo=Path(a.repo).resolve()
 try:
  d=js(repo/'tools/checkpoints/checkpoint-157/checkpoint_157_definition.json');req(d['checkpoint']==157 and d['baseCheckpoint']==156,'identity');req(d['expectedPythonTests']==544 and d['expectedPythonTestModules']==48,'python contract');req(d['substantiveCombatTrials']==0 and d['researchExecutionAuthorityChangesAllowed'] and not d['productionAuthorityChangesAllowed'],'authority boundary')
  req(ps_balanced(repo/'tools/checkpoints/checkpoint-157/apply_checkpoint_157.ps1'),'PowerShell delimiter/static parse guard')
  wrapper=(repo/'tools/checkpoints/checkpoint-157/apply_checkpoint_157.ps1').read_text(encoding='utf-8-sig');req("tools\\simulation\\run_starcluster_research.py" in wrapper and "starcluster_research\\cli.py" not in wrapper,'CP157 parity must use package-safe research entrypoint')
  req(sha(repo/'docs/design/player_technology/technology_numerical_matrix_v0_9.json')==MATRIX_SHA,'production matrix drift');req(sha(repo/'docs/archive/concepts/Star_Cluster_Game_Concept_v0.7x.docx')==CONCEPT_SHA,'Concept drift');req(sha(repo/'src/StarCluster.Core/Combat/Missiles/MissileInterceptionPhaseContext.cs')==PDS_SHA,'production PDS drift')
  pm=repo/CP156_MAN; req(pm.is_file() and sha(pm)==CP156_MAN_SHA,'CP156 manifest drift');base=manifest(pm)
  for rel,h in base.items():
   req((repo/rel).is_file(),f'missing CP156 file {rel}')
   if rel not in ALLOWED:req(sha(repo/rel)==h,f'unexpected CP156 drift: {rel}')
  ns=js(repo/'docs/validation/evidence/checkpoint-157/accepted-cp156/CP156_NATIVE_ACCEPTANCE_SUMMARY.json');req(ns['checkpoint']==156 and ns['pythonTestsPassed']==520 and ns['xunitPassed']==934 and ns['continuityAuditCompleted'],'CP156 native evidence')
  st=js(repo/'docs/archive/testing/pre-cp165-active/cp157_pending_finalization_research_execution_baseline_v0_1.json');req(st['acceptedCp156NativeResultsArchiveSha256']=='5c76df2ed64d718ed4aa7e8ec79d87a7838555e401a163c333e07a8a3e799fba','CP156 archive provenance');req(st['baselineId']=='CP157-PF1' and st['substantiveCombatTrials']==0,'study')
  bm=js(repo/'docs/validation/evidence/checkpoint-157/research_execution_baseline_manifest_v0_1.json');bp=repo/bm['materializedMatrix'];req(sha(bp)==bm['materializedMatrixSha256'],'baseline hash');req(bm['baselineId']=='CP157-PF1' and not bm['productionAuthorityReplaced'],'baseline manifest')
  sys.path.insert(0,str(repo/'tools/simulation'));from starcluster_research.research_execution_baseline import load_research_execution_baseline;m=load_research_execution_baseline(repo)
  req([int(m.p('kinetic_main',t)['damage']) for t in range(1,10)]==[9,10,12,13,14,15,15,19,20],'K1 materialization');req(int(m.p('energy_main',9)['standardDamage'])==18 and int(m.p('energy_main',9)['overloadDamage'])==24,'E7 materialization');req(int(m.p('amm_pds',7)['reactionCapacity'])==3 and bool(m.p('amm_pds',7)['rangeOneAttempt']),'AMM materialization')
  vr=rows(repo/'docs/validation/evidence/checkpoint-157/viable_ladder_register_v0_2.csv');req(len(vr)==447,'viable ladder rows');prim={r['ladder_id'] for r in vr if r['promotion_status']=='PENDING_FINALIZATION_PRIMARY'};req({'K1','E7','M2','SW2','K155P06','E155P08','A155P07'}<=prim,'primary set')
  diff=rows(repo/'docs/validation/evidence/checkpoint-157/research_execution_baseline_diff_v0_1.csv');req(len(diff)==538,'baseline diff rows')
  g=js(repo/'docs/validation/evidence/checkpoint-157/guardrail_registry_v0_2.json');gids={x['id'] for x in g['principles']};req({'BALANCE_NOT_EQUALITY','NO_GLOBAL_PDS_50','RESEARCH_EXECUTION_BASELINE_REQUIRED','NO_STALE_NUMERICAL_MIX'}<=gids,'guardrails')
  f=js(repo/'docs/validation/evidence/checkpoint-157/future_pass_contract_v0_2.json');req(f['researchExecutionBaseline']['required'] and not f['researchExecutionBaseline']['rawProductionMatrixAllowedForSubstantive'],'future baseline gate')
  tests=sorted((repo/'tools/simulation/tests').glob('test_*.py'));req(len(tests)==48,f'Python modules {len(tests)}');suite=unittest.defaultTestLoader.discover(str(repo/'tools/simulation/tests'),pattern='test_*.py');n=count_suite(suite);req(n==544,f'Python tests {n}')
  print('CP157 preflight PASS: CP156 native continuity accepted; CP157-PF1 materialized and hash-locked; K1/E7/M2/SW2 plus K155P06/E155P08/A155P07 promoted to pending-finalization research execution authority; 447 viable ladder rows preserved; 544/48 Python tests discovered; production authority unchanged; 0 substantive combats.')
  return 0
 except Exception as e:print(f'CP157 preflight failure: {e}',file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
