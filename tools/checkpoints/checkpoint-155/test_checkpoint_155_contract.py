#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json
from collections import defaultdict
from pathlib import Path

MATRIX_SHA='3088b0a9eb45f6bf505c24513e8bb2ac878819db4ab464ccfea330243c82f194'
CONCEPT_SHA='f76ca6ce488ccb5ad1352f7d38b8c3d4657c12ed64d0c93cc45d2db605cc632f'
PRODUCTION_PDS_SHA='1a731834a3956267aacbdde030561df2cef18121d91860cfbef1c5e851c10c99'
CP154_RESULTS_SHA='c93bbcb72fd0dba4625bdd5022f493a73daf239da53144d634cac345cae0e9bc'
SKIP='docs/validation/evidence/checkpoint-155/CP155_REPOSITORY_SHA256SUMS.txt'

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
 p=repo/SKIP;req(p.is_file(),'CP155 manifest missing');m=manifest(p);cur=owned(repo)
 req(set(m)==set(cur),f'manifest path drift missing={sorted(set(m)-set(cur))[:8]} extra={sorted(set(cur)-set(m))[:8]}')
 for r,h in m.items():req(sha(repo/r)==h,f'manifest hash drift {r}')
 return len(m)
def validate_plan(root):
 s=js(root/'pds-plan/summary.json');req(s['passed'] is True and not s.get('gates',{}).get('failed',[]),'plan gates')
 req(s['candidateTlRows']==1846 and s['primaryContexts']==1560 and s['robustnessContexts']==300 and s['deepContextsPerLadder']==1860,'plan population')
 req(s['baselineCombatTrials']==312000 and s['screenCandidateContextCells']==320640 and s['screenCombatTrials']==9619200,'baseline/screen scale')
 req(s['deepLadders']==30 and s['deepCombatTrials']==5580000 and s['substantiveCombatTrials']==15511200,'deep/total scale')
 req(len(rows(root/'pds-plan/pds_candidate_ledger.csv'))==1846,'plan candidate ledger rows')
 return s
def validate_smoke(root):
 specs=(('Kinetic','tl06_krc2_low',12),('Energy','tl06_eoc',24),('AMM','tl07_arc3',12));total=0
 for fam,name,combats in specs:
  d=root/'pds-smoke'/fam.lower()/name;s=js(d/'summary.json');rr=rows(d/'pds_candidate_context_results.csv')
  req(s['passed'] is True and s['mode']=='candidate-smoke' and s['family']==fam and s['errors']==0,f'{fam} smoke gates')
  req(s['combatTrials']==combats,f'{fam} smoke scale');req(len(rr)*int(s['trialsPerCell'])==combats,f'{fam} smoke rows');total+=combats
 req(total==48,'smoke total')
 return total
def validate_baseline(root):
 d=root/'pds-no-pds-baseline';s=js(d/'summary.json');rr=rows(d/'pds_no_pds_baseline.csv')
 req(s['passed'] is True and s['mode']=='no-pds-baseline' and s['contexts']==1560,'baseline population')
 req(s['trialsPerCell']==200 and s['combatTrials']==312000 and s['errors']==0,'baseline trials/errors')
 req(len(rr)==1560,'baseline rows')
 return s
def validate_candidate_merge(root):
 d=root/'pds-candidate-merged';s=js(d/'summary.json');sr=rows(d/'pds_candidate_summary.csv')
 req(s['passed'] is True and s['candidates']==1846 and s['candidateContextCells']==320640,'candidate merge population')
 req(s['combatTrials']==9619200 and s['errorTrials']==0,'candidate merge combat/errors')
 req(len(sr)==1846,'candidate summary rows')
 fam={f:sum(1 for r in sr if r['family']==f) for f in ('Kinetic','Energy','AMM')};req(fam=={'Kinetic':576,'Energy':945,'AMM':325},f'family candidate totals {fam}')
 req({int(float(r['ammo'])) for r in sr if r['family']=='Kinetic'}=={75},'K ammo varied')
 req({int(float(r['ammo'])) for r in sr if r['family']=='AMM'}=={25},'AMM ammo varied')
 req((d/'pds_candidate_response.csv').is_file() and (d/'batch_merge_audit.csv').is_file(),'candidate merged outputs')
 return s
def _n(r,k):
 v=r.get(k,'');return 0 if v in ('',None) else int(float(v))
def validate_synthesis(root):
 d=root/'pds-ladder-synthesis';s=js(d/'summary.json');rr=rows(d/'pds_ladder_candidates.csv')
 req(s['passed'] is True and s['laddersPerFamily']==10 and s['deepLadders']==30 and s['ladderTlRows']==270,'ladder synthesis')
 req(len(rr)==270,'ladder rows');ids={r['ladder_id'] for r in rr};req(len(ids)==30,'ladder ids')
 fam={f:len({r['ladder_id'] for r in rr if r['family']==f}) for f in ('Kinetic','Energy','AMM')};req(fam=={'Kinetic':10,'Energy':10,'AMM':10},f'ladder families {fam}')
 req(all(_n(r,'reaction_capacity')<=2 and _n(r,'range_one')==0 for r in rr if r['family'] in ('Kinetic','Energy')),'K/E RC/range rule')
 req(all((_n(r,'reaction_capacity')==3)==(_n(r,'range_one')==1) for r in rr if r['family']=='AMM'),'AMM RC3/range-one rule')
 req(all(_n(r,'ammo')==75 for r in rr if r['family']=='Kinetic'),'K ladder ammo')
 req(all(_n(r,'ammo')==25 for r in rr if r['family']=='AMM'),'AMM ladder ammo')
 by=defaultdict(list)
 for r in rr:by[r['ladder_id']].append(r)
 for lid,rs in by.items():
  rs.sort(key=lambda r:_n(r,'tl'));req([_n(r,'tl') for r in rs]==list(range(1,10)),f'{lid} TL coverage')
  req(all(_n(rs[i+1],'base_chance_pp')>=_n(rs[i],'base_chance_pp') for i in range(8)),f'{lid} chance regression')
  req(all(_n(rs[i+1],'reaction_capacity')>=_n(rs[i],'reaction_capacity') for i in range(8)),f'{lid} RC regression')
  if rs[0]['family']=='Energy':
   safe=False
   for r in rs:
    if r['mode']=='RC2_SAFE':safe=True
    if safe:req(r['mode']=='RC2_SAFE',f'{lid} safe Energy regressed')
  if rs[0]['family']=='AMM':
   seen=False
   for r in rs:
    if _n(r,'range_one'):seen=True
    if seen:req(_n(r,'range_one')==1,f'{lid} range-one regressed')
 return s
def validate_deep(root):
 d=root/'pds-deep-merged';s=js(d/'summary.json');sr=rows(d/'pds_deep_ladder_summary.csv');resp=rows(d/'pds_deep_response.csv');tri=rows(d/'pds_triad_viability_map.csv')
 req(s['passed'] is True and s['ladders']==30 and s['ladderContextCells']==55800,'deep coverage')
 req(s['combatTrials']==5580000 and s['errorTrials']==0 and s['triadCombinations']==1000,'deep combat/errors/triads')
 req(s['equalizationObjectiveUsed'] is False,'equalization objective leak')
 req(len(sr)==30 and len(tri)==1000 and len(resp)>0,'deep output rows')
 req({f:sum(1 for r in sr if r['family']==f) for f in ('Kinetic','Energy','AMM')}=={'Kinetic':10,'Energy':10,'AMM':10},'deep family rows')
 req('triad_selection_score' not in tri[0],'equality score unexpectedly exported')
 return s
def validate_native(root,final):
 n='CP155_NATIVE_ACCEPTANCE_SUMMARY.json' if final else 'CP155_REPOSITORY_ONLY_ACCEPTANCE.json';s=js(root/n)
 req(s['checkpoint']==155 and not s.get('failedGates',[]),'native gates')
 req(str(s['python']).startswith('Python 3.13') and s['dotnetSdk']=='8.0.423' and s['buildPassed'] is True,'runtime/build')
 req(s['pythonTestsPassed']==500 and s['xunitPassed']==934 and s['xunitFailed']==0 and s['xunitSkipped']==0,'tests')
 req(s['scenarioRunnerSelfTestsPassed']==70 and s['researchParityPassed']==25,'runner/parity')
 req(s['cp154FocusedTestsPassed']==25 and s['cp155FocusedTestsPassed']==28,'focused')
 req(s['acceptedCp154EvidenceHashLocked'] is True and s['sourceMatrixUnmodified'] is True and s['conceptUnmodified'] is True and s['productionCSharpUnmodified'] is True,'provenance/authorities')
 req(s['pdsCandidateTlRows']==1846 and s['deepLadders']==30,'PDS population')
 req(s['pdsSmokeCombatTrials']==48 and s['smokeErrors']==0,'smoke')
 req(s['equalizationObjectiveUsed'] is False and s['kAmmoFixed']==75 and s['ammAmmoFixed']==25,'philosophy/ammo')
 req(s['automaticPromotion'] is False and s['stageBAutomatic'] is False and s['tuningAllowed'] is False,'promotion')
 if final:
  req(s['repositoryOnlyAccepted'] is True and s['substantiveSweepCompleted'] is True,'final state')
  req(s['noPdsBaselineCombatTrials']==312000 and s['candidateScreenCombatTrials']==9619200 and s['deepConfirmationCombatTrials']==5580000 and s['substantiveCombatTrials']==15511200 and s['substantiveErrorTrials']==0,'final combat scale')
  req(s['triadCombinations']==1000,'triad count')
 else:req(s['substantiveCombatTrials']==0,'RepositoryOnly substantive')
 return s

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);ap.add_argument('--native-results');a=ap.parse_args();repo=Path(a.repo).resolve()
 try:
  d=js(repo/'tools/checkpoints/checkpoint-155/checkpoint_155_definition.json');req(d['checkpoint']==155 and d['expectedPythonTests']==500 and d['expectedXunitTests']==934 and d['substantiveCombatTrials']==15511200,'definition')
  count=validate_manifest(repo)
  req(sha(repo/'docs/design/player_technology/technology_numerical_matrix_v0_9.json')==MATRIX_SHA,'matrix drift')
  req(sha(repo/'docs/archive/concepts/Star_Cluster_Game_Concept_v0.7x.docx')==CONCEPT_SHA,'Concept drift')
  req(sha(repo/'src/StarCluster.Core/Combat/Missiles/MissileInterceptionPhaseContext.cs')==PRODUCTION_PDS_SHA,'production PDS drift')
  study=js(repo/'docs/archive/testing/pre-cp165-active/cp155_pds_architecture_resynthesis_study_v0_1.json');req(study['acceptedCp154NativeResultsArchiveSha256']==CP154_RESULTS_SHA,'CP154 provenance')
  if a.native_results:
   root=Path(a.native_results).resolve();final=(root/'CP155_NATIVE_ACCEPTANCE_SUMMARY.json').is_file();validate_native(root,final);validate_plan(root);validate_smoke(root)
   if final:validate_baseline(root);validate_candidate_merge(root);validate_synthesis(root);validate_deep(root)
  print(f'       CP155 contract verified: {count} repository-owned files; CP154 evidence hash-locked; 48 architecture smoke combats; 1,846 focused PDS candidate-TL points; 15,511,200 substantive combats; no equalization objective or automatic promotion.')
  return 0
 except Exception as e:
  print(f'CP155 contract failure: {e}');return 1
if __name__=='__main__':raise SystemExit(main())
