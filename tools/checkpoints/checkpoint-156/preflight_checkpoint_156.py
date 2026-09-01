#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json,sys,unittest
from pathlib import Path
CP155_MANIFEST='docs/validation/evidence/checkpoint-155/CP155_REPOSITORY_SHA256SUMS.txt'
CP155_MANIFEST_SHA='0052ad104c4f54c8188315510c7bd4dc2899410492195016c5a0e7b6f7ba9f16'
CP156_MANIFEST='docs/validation/evidence/checkpoint-156/CP156_REPOSITORY_SHA256SUMS.txt'
MATRIX_SHA='3088b0a9eb45f6bf505c24513e8bb2ac878819db4ab464ccfea330243c82f194'
CONCEPT_SHA='f76ca6ce488ccb5ad1352f7d38b8c3d4657c12ed64d0c93cc45d2db605cc632f'
PRODUCTION_PDS_SHA='1a731834a3956267aacbdde030561df2cef18121d91860cfbef1c5e851c10c99'
ALLOWED={'README.md','CHAT_README.md','docs/README.md','docs/Prototype_TODO.md','docs/validation/README.md','docs/design/testing/README.md'}
ADDITIONS={
 'docs/archive/testing/pre-cp165-active/cp156_research_continuity_audit_v0_1.json',
 'docs/validation/Checkpoint_156_Research_Continuity_Promotion_Audit_And_Future_Pass_Guardrails.md',
 'tools/simulation/tests/test_cp156_research_continuity.py',
 'tools/checkpoints/checkpoint-156/apply_checkpoint_156.ps1','tools/checkpoints/checkpoint-156/checkpoint_156_definition.json','tools/checkpoints/checkpoint-156/preflight_checkpoint_156.py','tools/checkpoints/checkpoint-156/test_checkpoint_156_contract.py',
 'docs/validation/evidence/checkpoint-156/accepted-cp155/CP155_NATIVE_ACCEPTANCE_SUMMARY.json',
 'docs/validation/evidence/checkpoint-156/accepted-cp155/CP155_PDS_LADDER_CANDIDATES.csv',
 'docs/validation/evidence/checkpoint-156/accepted-cp155/CP155_PDS_DEEP_LADDER_SUMMARY.csv',
 'docs/validation/evidence/checkpoint-156/accepted-cp155/CP155_PDS_TRIAD_VIABILITY_MAP.csv',
 'docs/validation/evidence/checkpoint-156/accepted-cp155/CP155_NO_PDS_BASELINE.csv',
 'docs/validation/evidence/checkpoint-156/accepted-cp155/CP155_PDS_CANDIDATE_SUMMARY.csv',
 'docs/validation/evidence/checkpoint-156/authority_snapshot_v0_1.json','docs/validation/evidence/checkpoint-156/promotion_audit_v0_1.csv','docs/validation/evidence/checkpoint-156/research_findings_ledger_v0_1.csv','docs/validation/evidence/checkpoint-156/viable_ladder_register_v0_1.csv','docs/validation/evidence/checkpoint-156/guardrail_registry_v0_1.json','docs/validation/evidence/checkpoint-156/future_pass_contract_v0_1.json','docs/validation/evidence/checkpoint-156/evidence_chain_sha256_v0_1.csv','docs/validation/evidence/checkpoint-156/research_continuity_register_v0_1.json'
}
def req(x,m):
 if not x: raise AssertionError(m)
def sha(p): h=hashlib.sha256();h.update(p.read_bytes());return h.hexdigest()
def js(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def rows(p):
 with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def manifest(p):
 out={}
 for l in p.read_text(encoding='utf-8-sig').splitlines():
  if l.strip(): h,r=l.split('  ',1);out[r]=h
 return out
def owned(repo):
 out=set()
 for p in repo.rglob('*'):
  if not p.is_file(): continue
  r=p.relative_to(repo).as_posix();w='/'+r
  if r.startswith(('out/','.git/')) or '/__pycache__/' in w or r.endswith('.pyc') or '/bin/' in w or '/obj/' in w or '/TestResults/' in w: continue
  if r==CP156_MANIFEST: continue
  out.add(r)
 return out
def count_suite(s): return sum(count_suite(x) if isinstance(x,unittest.TestSuite) else 1 for x in s)
def powershell_delimiters_balanced(path):
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
  d=js(repo/'tools/checkpoints/checkpoint-156/checkpoint_156_definition.json'); req(d['checkpoint']==156 and d['baseCheckpoint']==155,'identity');req(d['expectedPythonTests']==520 and d['expectedPythonTestModules']==47,'python count contract');req(d['substantiveCombatTrials']==0 and not d['automaticPromotion'] and not d['authorityChangesAllowed'],'zero-combat authority contract')
  req(powershell_delimiters_balanced(repo/'tools/checkpoints/checkpoint-156/apply_checkpoint_156.ps1'),'PowerShell delimiter/static parse guard')
  req(sha(repo/'docs/design/player_technology/technology_numerical_matrix_v0_9.json')==MATRIX_SHA,'matrix drift');req(sha(repo/'docs/archive/concepts/Star_Cluster_Game_Concept_v0.7x.docx')==CONCEPT_SHA,'Concept drift');req(sha(repo/'src/StarCluster.Core/Combat/Missiles/MissileInterceptionPhaseContext.cs')==PRODUCTION_PDS_SHA,'production PDS drift')
  p=repo/CP155_MANIFEST;req(p.is_file() and sha(p)==CP155_MANIFEST_SHA,'CP155 manifest drift');base=manifest(p)
  for rel,h in base.items():
   req((repo/rel).is_file(),f'missing CP155 file {rel}')
   if rel not in ALLOWED:req(sha(repo/rel)==h,f'unexpected CP155 drift: {rel}')
  expected=set(base)|ADDITIONS|{CP155_MANIFEST};cur=owned(repo);req(cur==expected,f'path drift added={sorted(cur-expected)[:20]} missing={sorted(expected-cur)[:20]}')
  s=js(repo/'docs/archive/testing/pre-cp165-active/cp156_research_continuity_audit_v0_1.json');req(s['substantiveCombatTrials']==0 and not s['automaticPromotion'],'study scope');req(s['acceptedCp155NativeResultsArchiveSha256']=='f368612abdbf44b1eb78f0695cc6b72be491834c22564be063a74f8823298b52','CP155 archive provenance')
  ns=js(repo/'docs/validation/evidence/checkpoint-156/accepted-cp155/CP155_NATIVE_ACCEPTANCE_SUMMARY.json');req(ns['substantiveCombatTrials']==15511200 and ns['substantiveErrorTrials']==0 and ns['substantiveTurnCapSentinels']==0 and ns['triadCombinations']==1000,'CP155 accepted evidence summary')
  pa=rows(repo/'docs/validation/evidence/checkpoint-156/promotion_audit_v0_1.csv');recent=[r for r in pa if 149<=int(r['checkpoint'])<=155];req(len(recent)==7 and all(r['automatic_promotion'].lower()=='false' and r['audit_result']=='NO_MISSED_PROMOTION' for r in recent),'promotion audit')
  vr=rows(repo/'docs/validation/evidence/checkpoint-156/viable_ladder_register_v0_1.csv');req(len(vr)==447 and all(r['promotion_status']=='RESEARCH_ONLY_NOT_PROMOTED' for r in vr),'viable ladder preservation');ids={r['ladder_id'] for r in vr};req({'E7','M2','M3','SW2','K155P03','K155P06','E155P08','A155P07'}<=ids,'preferred viable set missing')
  g=js(repo/'docs/validation/evidence/checkpoint-156/guardrail_registry_v0_1.json');gids={x['id'] for x in g['principles']};req({'BALANCE_NOT_EQUALITY','NO_GLOBAL_PDS_50','MISSILE_NON_PDS_THREAT','TECH_COHERENCE','PARETO_MULTI_OBJECTIVE','REUSE_CLOSED_SURFACES','TP_LAST'}<=gids,'guardrail set')
  f=js(repo/'docs/validation/evidence/checkpoint-156/future_pass_contract_v0_1.json');req(f['nextSubstantivePass']['name']=='Defense/AUX Lifetime Viability' and f['finalMajorPass']['name']=='Reactor/TP Scarcity and Whole-Ship Equilibrium','future sequence')
  ec=rows(repo/'docs/validation/evidence/checkpoint-156/evidence_chain_sha256_v0_1.csv');req(len(ec)>=50,'evidence chain too small');req(all((repo/r['path']).is_file() and sha(repo/r['path'])==r['sha256'] for r in ec),'evidence chain hash mismatch')
  tests=sorted((repo/'tools/simulation/tests').glob('test_*.py'));req(len(tests)==47,f'Python modules {len(tests)}');suite=unittest.defaultTestLoader.discover(str(repo/'tools/simulation/tests'),pattern='test_*.py');n=count_suite(suite);req(n==520,f'Python tests {n}')
  print('CP156 preflight PASS: CP155 native evidence hash-locked; CP149-CP155 promotion intent audited; 447 viable main/PDS ladder rows preserved; balance/technology/reuse guardrails frozen; 520/47 Python tests discovered; 0 substantive combats; no authority promotion.')
  return 0
 except Exception as e:
  print(f'CP156 preflight failure: {e}',file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
