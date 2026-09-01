#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json,sys,unittest
from collections import Counter
from pathlib import Path
CP157_MAN='docs/validation/evidence/checkpoint-157/CP157_REPOSITORY_SHA256SUMS.txt'
CP157_MAN_SHA='6f86be122cc062d3a7870692064a820dfc77bcde8be943a1cf34dc7986feefe5'
PROD_SHA='3088b0a9eb45f6bf505c24513e8bb2ac878819db4ab464ccfea330243c82f194'
CONCEPT_SHA='f76ca6ce488ccb5ad1352f7d38b8c3d4657c12ed64d0c93cc45d2db605cc632f'
PDS_SHA='1a731834a3956267aacbdde030561df2cef18121d91860cfbef1c5e851c10c99'
PF2_SHA='9d7d7b562926a924d996b4166db40c04e9023d22f30982f306c12d796ad729f9'
ALLOWED={'README.md','CHAT_README.md','docs/README.md','docs/Prototype_TODO.md','docs/validation/README.md','docs/design/testing/README.md','docs/design/player_technology/README.md','tools/simulation/starcluster_research/canonical_combat.py','tools/simulation/starcluster_research/ecology.py'}
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
def count_suite(s):return sum(count_suite(x) if isinstance(x,unittest.TestSuite) else 1 for x in s)
def ps_balanced(path):
 text=path.read_text(encoding='utf-8-sig');stack=[];pairs={')':'(',']':'[','}':'{'};state='normal';i=0
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
  d=js(repo/'tools/checkpoints/checkpoint-158/checkpoint_158_definition.json');req(d['checkpoint']==158 and d['baseCheckpoint']==157,'identity');req(d['expectedPythonTests']==574 and d['expectedPythonTestModules']==49,'python contract');req(d['substantiveCombatTrials']==44723375 and not d['automaticPromotion'] and not d['tuningAllowed'],'study boundary')
  wrapper=repo/'tools/checkpoints/checkpoint-158/apply_checkpoint_158.ps1';req(ps_balanced(wrapper),'PowerShell delimiter/static parse guard');wt=wrapper.read_text(encoding='utf-8-sig');req('tools\\simulation\\run_starcluster_research.py' in wt and 'starcluster_research\\cli.py' not in wt,'package-safe parity entrypoint')
  req(sha(repo/'docs/design/player_technology/technology_numerical_matrix_v0_9.json')==PROD_SHA,'production matrix drift');req(sha(repo/'docs/archive/concepts/Star_Cluster_Game_Concept_v0.7x.docx')==CONCEPT_SHA,'Concept drift');req(sha(repo/'src/StarCluster.Core/Combat/Missiles/MissileInterceptionPhaseContext.cs')==PDS_SHA,'production PDS drift')
  pm=repo/CP157_MAN;req(pm.is_file() and sha(pm)==CP157_MAN_SHA,'CP157 manifest drift');base=manifest(pm)
  for rel,h in base.items():
   req((repo/rel).is_file(),f'missing CP157 file {rel}')
   if rel not in ALLOWED:req(sha(repo/rel)==h,f'unexpected CP157 drift: {rel}')
  ns=js(repo/'docs/validation/evidence/checkpoint-158/accepted-cp157/CP157_NATIVE_ACCEPTANCE_SUMMARY.json');req(ns['checkpoint']==157 and ns['pythonTestsPassed']==544 and ns['xunitPassed']==934 and ns['baselinePromotionCompleted'],'CP157 native evidence')
  bm=js(repo/'docs/validation/evidence/checkpoint-158/research_execution_baseline_manifest_v0_2.json');bp=repo/bm['materializedMatrix'];req(bm['baselineId']=='CP158-PF2' and sha(bp)==PF2_SHA==bm['materializedMatrixSha256'],'PF2 identity/hash');req(not bm['productionAuthorityReplaced'] and bm['substantiveCombatTrials']==44723375,'PF2 authority boundary')
  dif=rows(repo/'docs/validation/evidence/checkpoint-158/research_execution_baseline_diff_v0_2.csv');cc=Counter(r['status'] for r in dif);req(cc==Counter({'PENDING_FINALIZATION_SELECTED':348,'PENDING_FINALIZATION_VALIDATED_ENVIRONMENT':54,'FROZEN_RESEARCH_MECHANIC':73,'PROVISIONAL_RESOURCE_SCAFFOLD':63}),'PF2 classification split')
  conf=js(repo/'docs/validation/evidence/checkpoint-158/pf2_conformance_report_v0_1.json');req(conf['matrixSha256']==PF2_SHA and conf['substantiveResearchMustUseThisBaseline'],'PF2 conformance');req(conf['kineticDamage']==[9,10,12,13,14,15,15,19,20] and conf['gpMissileDamage']==[12,13,15,17,19,21,23,25,27],'main conformance');req(conf['shieldCapacity']==[16.0,18.0,20.0,22.0,24.0,26.0,28.0,30.0,32.0] and conf['armorCapacity']==[12.0,14.0,16.0,18.0,20.0,18.0,20.0,22.0,24.0],'defense conformance');req(conf['kineticPdsRc']==[1,1,1,1,1,1,2,2,2] and conf['ammRc'][6:]==[3,3,3] and all(conf['ammRangeOne'][6:]),'PDS conformance')
  sys.path.insert(0,str(repo/'tools/simulation'));from starcluster_research.research_execution_baseline_pf2 import load_research_execution_baseline_pf2;from starcluster_research.defense_aux_lifetime_viability import candidate_ledger
  m=load_research_execution_baseline_pf2(repo);req(int(m.p('energy_main',9)['standardDamage'])==18 and int(m.p('amm_pds',7)['reactionCapacity'])==3,'PF2 loader conformance');c=candidate_ledger();req(len(c)==703 and len({x['candidate_id'] for x in c})==703,'candidate population')
  st=js(repo/'docs/archive/testing/pre-cp165-active/cp158_defense_aux_lifetime_viability_study_v0_1.json');req(st['researchExecutionBaseline']=='CP158-PF2' and st['substantiveCombatTrials']==44723375,'study baseline/scale');req(not st['automaticPromotion'] and not st['tuningAllowed'],'study promotion boundary');txt=json.dumps(st).lower();req('balance is not equality' in txt and 'global 50' in txt and 'final reactor/tp tuning remains last' in txt,'method guardrails')
  pl=js(repo/'docs/validation/evidence/checkpoint-158/planned-study/summary.json');req(pl['candidateTlPoints']==703 and pl['screenLegalCells']==497555 and pl['plannedDeepCells']==277160 and pl['pairwiseLegalCells']==169040 and pl['substantiveCombatTrials']==44723375,'planned study counts')
  tests=sorted((repo/'tools/simulation/tests').glob('test_*.py'));req(len(tests)==49,f'Python modules {len(tests)}');suite=unittest.defaultTestLoader.discover(str(repo/'tools/simulation/tests'),pattern='test_*.py');n=count_suite(suite);req(n==574,f'Python tests {n}')
  print('CP158 preflight PASS: CP157 native PF1 accepted; CP158-PF2 classification split and conformance locked; 703 AUX candidate-TL points; 497,555 broad cells; 64 architecture-stratified deep ladders; 169,040 pairwise cells; 44,723,375 substantive combats; 574/49 Python tests discovered; production authority unchanged; no automatic promotion.')
  return 0
 except Exception as e:print(f'CP158 preflight failure: {e}',file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
