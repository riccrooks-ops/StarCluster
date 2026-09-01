#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,csv
from pathlib import Path
MAN='docs/validation/evidence/checkpoint-158/CP158_REPOSITORY_SHA256SUMS.txt'
def req(x,m):
 if not x:raise AssertionError(m)
def sha(p):h=hashlib.sha256();h.update(p.read_bytes());return h.hexdigest()
def js(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def manifest(p):
 out={}
 for l in p.read_text(encoding='utf-8-sig').splitlines():
  if l.strip():h,r=l.split('  ',1);out[r]=h
 return out
def owned(repo):
 out=set()
 for p in repo.rglob('*'):
  if not p.is_file():continue
  r=p.relative_to(repo).as_posix();w='/'+r
  if r.startswith(('out/','.git/')) or '/__pycache__/' in w or r.endswith('.pyc') or '/bin/' in w or '/obj/' in w or '/TestResults/' in w or r==MAN:continue
  if r.startswith('StarCluster_CP158_native_results_') and r.endswith('.zip'):continue
  out.add(r)
 return out
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);ap.add_argument('--native-results',required=True);a=ap.parse_args();repo=Path(a.repo).resolve();nr=Path(a.native_results).resolve()
 try:
  man=manifest(repo/MAN);cur=owned(repo);req(set(man)==cur,f'manifest path drift added={sorted(cur-set(man))[:10]} missing={sorted(set(man)-cur)[:10]}');req(all(sha(repo/r)==h for r,h in man.items()),'manifest hash mismatch');req(len(man)>3271,'owned count did not advance')
  p=nr/'CP158_NATIVE_ACCEPTANCE_SUMMARY.json';ro=nr/'CP158_REPOSITORY_ONLY_ACCEPTANCE.json';s=js(p if p.exists() else ro);req(s['checkpoint']==158 and s['pythonTestsPassed']==574 and s['xunitPassed']==934 and s['researchParityPassed']==25 and s['cp158FocusedTestsPassed']==30,'regression acceptance');req(s['pendingFinalizationBaselineId']=='CP158-PF2' and not s['productionAuthorityChanged'] and not s['automaticPromotion'],'authority boundary');req(s['architectureSmokeCombats']==8 and s['candidateTlPoints']==703,'architecture/plan')
  if p.exists():
   req(s['repositoryOnlyAccepted'] and s['substantiveCombatTrials']==44723375,'full scale');req(s['baselineCombatTrials']==342500 and s['screenCombatTrials']==12438875 and s['deepCombatTrials']==27716000 and s['pairwiseCombatTrials']==4226000,'stage totals');req(s['substantiveErrors']==0,'substantive errors');req(s['deepLadders']==64 and s['pairwiseCells']==169040,'deep/pair structure')
  print(f"CP158 contract PASS: {len(man)} repository-owned files; CP158-PF2 research execution authority preserved; AUX lifecycle sweep contract 44,723,375 combats; production authority unchanged; no automatic promotion.")
  return 0
 except Exception as e:print(f'CP158 contract failure: {e}',file=__import__('sys').stderr);return 1
if __name__=='__main__':raise SystemExit(main())
