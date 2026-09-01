#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,csv
from pathlib import Path
MAN='docs/validation/evidence/checkpoint-157/CP157_REPOSITORY_SHA256SUMS.txt'
def req(x,m):
 if not x:raise AssertionError(m)
def sha(p):h=hashlib.sha256();h.update(p.read_bytes());return h.hexdigest()
def js(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def owned(repo):
 out=set()
 for p in repo.rglob('*'):
  if not p.is_file():continue
  r=p.relative_to(repo).as_posix();w='/'+r
  if r.startswith(('out/','.git/')) or '/__pycache__/' in w or r.endswith('.pyc') or '/bin/' in w or '/obj/' in w or '/TestResults/' in w or r==MAN:continue
  if r.startswith('StarCluster_CP157_native_results_') and r.endswith('.zip'):continue
  out.add(r)
 return out
def manifest(p):
 out={}
 for l in p.read_text(encoding='utf-8-sig').splitlines():
  if l.strip():h,r=l.split('  ',1);out[r]=h
 return out
def rows(p):
 with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);ap.add_argument('--native-results',required=True);a=ap.parse_args();repo=Path(a.repo).resolve();nr=Path(a.native_results).resolve()
 try:
  man=manifest(repo/MAN);cur=owned(repo);req(set(man)==cur,f'manifest path drift added={sorted(cur-set(man))[:10]} missing={sorted(set(man)-cur)[:10]}');req(all(sha(repo/r)==h for r,h in man.items()),'manifest hash mismatch');req(len(man)>3242,'owned count did not advance')
  p=nr/'CP157_NATIVE_ACCEPTANCE_SUMMARY.json'; ro=nr/'CP157_REPOSITORY_ONLY_ACCEPTANCE.json';s=js(p if p.exists() else ro);req(s['checkpoint']==157 and s['pythonTestsPassed']==544 and s['xunitPassed']==934 and s['researchParityPassed']==25,'regression acceptance');req(s['substantiveCombatTrials']==0 and s['researchExecutionAuthorityPromoted'] and not s['productionAuthorityChanged'],'promotion boundary');req(s['pendingFinalizationBaselineId']=='CP157-PF1' and s['viableLadderRowsPreserved']==447 and s['fieldDiffRows']==538,'baseline acceptance')
  print(f"CP157 contract PASS: {len(man)} repository-owned files; CP157-PF1 research execution authority promoted pending finalization; 447 viable ladder rows preserved; production authority unchanged; zero combat/tuning.")
  return 0
 except Exception as e:print(f'CP157 contract failure: {e}',file=__import__('sys').stderr);return 1
if __name__=='__main__':raise SystemExit(main())
