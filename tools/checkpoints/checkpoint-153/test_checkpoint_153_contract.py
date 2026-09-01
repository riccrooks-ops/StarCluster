#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path

MATRIX_SHA='3088b0a9eb45f6bf505c24513e8bb2ac878819db4ab464ccfea330243c82f194'
CP152_RESULTS_SHA='001f26f68494bf5c57d44df8244e686b1d4821c436129ccadff42ceaccf20f08'
SKIP='docs/validation/evidence/checkpoint-153/CP153_REPOSITORY_SHA256SUMS.txt'

def req(x,m):
 if not x: raise AssertionError(m)
def sha(p): h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()
def js(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def rows(p):
 with p.open(encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))
def manifest(p):
 out={}
 for l in p.read_text(encoding='utf-8-sig').splitlines():
  if l.strip(): h,r=l.split('  ',1); out[r]=h
 return out
def owned(repo):
 out=[]
 for p in repo.rglob('*'):
  if not p.is_file(): continue
  r=p.relative_to(repo).as_posix(); w='/'+r
  if r.startswith(('out/','.git/')) or '/__pycache__/' in w or r.endswith('.pyc') or '/bin/' in w or '/obj/' in w or '/TestResults/' in w: continue
  if r==SKIP: continue
  out.append(r)
 return sorted(out)
def validate_manifest(repo):
 p=repo/SKIP; req(p.is_file(),'CP153 manifest missing'); m=manifest(p); cur=owned(repo)
 req(set(m)==set(cur),f'manifest path drift missing={sorted(set(m)-set(cur))[:5]} extra={sorted(set(cur)-set(m))[:5]}')
 for r,h in m.items(): req(sha(repo/r)==h,f'manifest hash drift {r}')
 return len(m)
def validate_plan(root):
 s=js(root/'four-main-plan/summary.json'); req(s['passed'] is True and not s['failedGates'],'plan gates')
 req(s['energyTlCandidates']==3798 and s['wholeLadderPackages']==432,'plan candidates/packages')
 req(s['energyCombatTrials']==82290000 and s['screenCombatTrials']==11836800 and s['deepCombatTrials']==8220000 and s['totalCombatTrials']==102346800,'plan combat scale')
 req(s['energySmokeCombatTrials']==189900,'smoke scale'); return s
def validate_smoke(root):
 total=0
 for tl in range(1,10):
  d=root/'energy-closure-smoke'/f'tl{tl:02d}'; s=js(d/'summary.json'); rr=rows(d/'energy_closure_candidate_context_results.csv')
  req(s['passed'] is True and s['lane']=='E' and s['smokePanel'] is True,'smoke gates')
  req(s['candidates']==422 and s['contextsPerCandidate']==50 and s['combatTrials']==21100 and s['errors']==0,'smoke scale')
  req(len(rr)==21100 and all(int(r['error_trials'])==0 for r in rr),'smoke rows'); total+=int(s['combatTrials'])
 req(total==189900,'smoke total'); return total
def validate_energy(root):
 d=root/'energy-closure-merged'; s=js(d/'summary.json'); req(s['passed'] is True and s['combatTrials']==82290000 and s['errorTrials']==0,'Energy merge')
 req(len(rows(d/'energy_closure_candidate_summary.csv'))==3798,'Energy candidate summary rows')
 for f in ('energy_closure_candidate_opponent_response.csv','energy_closure_candidate_resource_response.csv','energy_closure_candidate_stratum_response.csv','energy_closure_factor_marginals.csv','energy_closure_pairwise_response.csv','energy_closure_isolated_factor_response.csv','energy_closure_isolated_pairwise_response.csv'): req((d/f).is_file(),f'Energy output missing {f}')
 return s
def validate_synthesis(root):
 d=root/'four-main-ladder-synthesis'; s=js(d/'summary.json'); req(s['passed'] is True and s['kLadders']==6 and s['eLadders']==8 and s['gpLadders']==3 and s['swLadders']==3 and s['packages']==432,'ladder synthesis')
 req(len(rows(d/'kinetic_ladder_candidates.csv'))==54,'K ladder rows'); req(len(rows(d/'energy_ladder_candidates.csv'))==72,'E ladder rows'); req(len(rows(d/'missile_ladder_candidates.csv'))==51,'missile ladder rows'); req(len(rows(d/'four_main_package_tl_ledger.csv'))==3888,'package ledger rows'); return s
def validate_package_merge(root,mode):
 d=root/f'four-main-{mode}-merged'; s=js(d/'summary.json'); expected=11836800 if mode=='screen' else 8220000; packages=432 if mode=='screen' else 12
 req(s['passed'] is True and s['combatTrials']==expected and s['errorTrials']==0 and s['packages']==packages,'package merge')
 req(len(rows(d/f'four_main_{mode}_package_summary.csv'))==packages,f'{mode} package summary rows')
 for f in (f'four_main_{mode}_family_response.csv',f'four_main_{mode}_pair_response.csv',f'four_main_{mode}_stratum_response.csv'): req((d/f).is_file(),f'{mode} output missing {f}')
 return s
def validate_deep_selection(root):
 d=root/'four-main-deep-select'; s=js(d/'summary.json'); req(s['passed'] is True and s['deepPackages']==12 and s['packageTlRows']==108 and s['energyLaddersRepresented']==8,'deep selection')
 req(len(rows(d/'four_main_deep_shortlist.csv'))==12,'deep shortlist rows'); req(len(rows(d/'four_main_deep_package_tl_ledger.csv'))==108,'deep ledger rows'); return s
def validate_native(root,final):
 n='CP153_NATIVE_ACCEPTANCE_SUMMARY.json' if final else 'CP153_REPOSITORY_ONLY_ACCEPTANCE.json'; s=js(root/n)
 req(s['checkpoint']==153 and not s.get('failedGates',[]),'native gates'); req(s['python'].startswith('Python 3.13') and s['dotnetSdk']=='8.0.423' and s['buildPassed'] is True,'runtime/build')
 req(s['pythonTestsPassed']==447 and s['xunitPassed']==934 and s['xunitFailed']==0 and s['xunitSkipped']==0,'tests'); req(s['scenarioRunnerSelfTestsPassed']==70 and s['researchParityPassed']==25,'runner/parity')
 req(s['cp152FocusedTestsPassed']==18 and s['cp153FocusedTestsPassed']==21,'focused'); req(s['acceptedCp152EvidenceHashLocked'] is True and s['sourceMatrixUnmodified'] is True and s['conceptUnmodified'] is True,'provenance/authorities')
 req(s['energySmokeCombatTrials']==189900 and s['smokeErrors']==0,'smoke'); req(s['automaticPromotion'] is False and s['stageBAutomatic'] is False and s['tuningAllowed'] is False,'promotion')
 if final: req(s['repositoryOnlyAccepted'] is True and s['substantiveSweepCompleted'] is True and s['substantiveCombatTrials']==102346800 and s['substantiveErrorTrials']==0 and s['wholeLadderPackages']==432 and s['deepPackages']==12,'final completion')
 else: req(s['substantiveCombatTrials']==0,'RepositoryOnly substantive')
 return s
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--repo',required=True); ap.add_argument('--native-results'); a=ap.parse_args(); repo=Path(a.repo).resolve()
 try:
  d=js(repo/'tools/checkpoints/checkpoint-153/checkpoint_153_definition.json'); req(d['checkpoint']==153 and d['expectedPythonTests']==447 and d['expectedXunitTests']==934 and d['substantiveCombatTrials']==102346800,'definition')
  count=validate_manifest(repo); req(sha(repo/'docs/design/player_technology/technology_numerical_matrix_v0_9.json')==MATRIX_SHA,'matrix drift')
  study=js(repo/'docs/archive/testing/pre-cp165-active/cp153_four_main_ladder_synthesis_study_v0_1.json'); req(study['acceptedCp152NativeResultsArchiveSha256']==CP152_RESULTS_SHA,'CP152 provenance')
  if a.native_results:
   root=Path(a.native_results).resolve(); final=(root/'CP153_NATIVE_ACCEPTANCE_SUMMARY.json').is_file(); validate_native(root,final); validate_plan(root); validate_smoke(root)
   if final: validate_energy(root); validate_synthesis(root); validate_package_merge(root,'screen'); validate_deep_selection(root); validate_package_merge(root,'deep')
  print(f'       CP153 contract verified: {count} repository-owned files; CP152 evidence hash-locked; 189,900 smoke combats; 102,346,800 substantive E-closure/four-main combats; no automatic promotion.')
  return 0
 except Exception as e:
  print(f'CP153 contract failure: {e}'); return 1
if __name__=='__main__': raise SystemExit(main())
