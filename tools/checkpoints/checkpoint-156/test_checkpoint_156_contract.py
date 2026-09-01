#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
MAN='docs/validation/evidence/checkpoint-156/CP156_REPOSITORY_SHA256SUMS.txt'
def req(x,m):
 if not x: raise AssertionError(m)
def sha(p):h=hashlib.sha256();h.update(p.read_bytes());return h.hexdigest()
def js(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def owned(repo):
 out=set()
 for p in repo.rglob('*'):
  if not p.is_file():continue
  r=p.relative_to(repo).as_posix();w='/'+r
  if r.startswith(('out/','.git/')) or '/__pycache__/' in w or r.endswith('.pyc') or '/bin/' in w or '/obj/' in w or '/TestResults/' in w or r==MAN:continue
  out.add(r)
 return out
def manifest(p):
 out={}
 for l in p.read_text(encoding='utf-8-sig').splitlines():
  if l.strip():h,r=l.split('  ',1);out[r]=h
 return out
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);ap.add_argument('--native-results',required=True);a=ap.parse_args();repo=Path(a.repo).resolve();nr=Path(a.native_results).resolve()
 try:
  man=manifest(repo/MAN);cur=owned(repo);req(set(man)==cur,f'manifest paths drift added={sorted(cur-set(man))[:10]} missing={sorted(set(man)-cur)[:10]}');req(all(sha(repo/r)==h for r,h in man.items()),'manifest hash mismatch');req(len(man)==3242,f'owned count {len(man)}')
  ro=nr/'CP156_REPOSITORY_ONLY_ACCEPTANCE.json';final=nr/'CP156_NATIVE_ACCEPTANCE_SUMMARY.json';p=final if final.exists() else ro;req(p.exists(),'missing acceptance summary');s=js(p);req(s['checkpoint']==156 and s['pythonTestsPassed']==520 and s['xunitPassed']==934 and s['researchParityPassed']==25,'acceptance regression contract');req(s['substantiveCombatTrials']==0 and s['automaticPromotion']==False and s['authorityChanges']==False,'zero-combat promotion contract');req(s['cp155NativeEvidencePreserved']==True and s['promotionAuditPassed']==True and s['guardrailsFrozen']==True and s['viableLadderRowsPreserved']==447,'continuity acceptance contract')
  print('CP156 contract PASS: 3242 repository-owned files; CP155 accepted evidence preserved; 447 viable ladder rows and guardrails frozen; zero combat/tuning/promotion.')
  return 0
 except Exception as e:
  print(f'CP156 contract failure: {e}',file=__import__('sys').stderr);return 1
if __name__=='__main__':raise SystemExit(main())
