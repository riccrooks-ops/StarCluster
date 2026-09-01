#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
SKIP='docs/validation/evidence/checkpoint-133/CP133_REPOSITORY_SHA256SUMS.txt'

def req(v,m):
    if not v: raise AssertionError(m)
def text(p): req(p.is_file(),f'missing {p}'); return p.read_text(encoding='utf-8-sig')
def js(p): return json.loads(text(p))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def manifest(p):
    out={}
    for line in text(p).splitlines():
        if line.strip(): h,r=line.split('  ',1);out[r]=h
    return out
def owned(repo):
    out=[]
    for p in repo.rglob('*'):
        if not p.is_file(): continue
        rel=p.relative_to(repo).as_posix(); w='/'+rel
        if rel.startswith(('out/','.git/')) or '/__pycache__/' in w or rel.endswith('.pyc') or '/bin/' in w or '/obj/' in w or '/TestResults/' in w: continue
        if rel==SKIP: continue
        out.append(rel)
    return sorted(out)
def validate_manifest(repo):
    entries=manifest(repo/SKIP); cur=owned(repo); req(set(entries)==set(cur),f'manifest path drift missing={sorted(set(entries)-set(cur))[:5]} extra={sorted(set(cur)-set(entries))[:5]}')
    for rel,h in entries.items(): req(sha(repo/rel)==h,f'manifest hash drift {rel}')
    return len(entries)
def validate_native(native,final=False):
    name='CP133_NATIVE_ACCEPTANCE_SUMMARY.json' if final else 'CP133_REPOSITORY_ONLY_ACCEPTANCE.json'; s=js(native/name)
    req(s['checkpoint']==133 and s['failedGates']==[],'native identity')
    req(s['python'].startswith('Python 3.13') and s['dotnetSdk']=='8.0.423','runtimes')
    req(s['pythonTestsPassed']==196 and s['xunitPassed']==910 and s['xunitFailed']==0 and s['xunitSkipped']==0,'unit tests')
    req(s['scenarioRunnerSelfTestsPassed']==70 and s['researchParityPassed']==25 and s['canonicalKernelTestsPassed']==6,'standing deterministic gates')
    req(s['technologyValuesChanged'] is True and s['productionSourceChanged'] is False and s['researchSimulationChanged'] is False and s['scenarioDefinitionsChanged'] is False and s['conceptChanged'] is False,'change boundary')
    req(s['monteCarloStudy'] is False and s['substantiveTrials']==0 and s['balanceCalibrationRun'] is False,'zero-study boundary')
    return s
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);ap.add_argument('--native-results');a=ap.parse_args();repo=Path(a.repo).resolve()
    try:
        d=js(repo/'tools/checkpoints/checkpoint-133/checkpoint_133_definition.json');req(d['checkpoint']==133 and d['technologyValuesChanged'] is True and d['declaredSubstantiveTrials']==0,'definition')
        json_count=0
        for p in repo.rglob('*.json'):
            rel=p.relative_to(repo).as_posix(); w='/'+rel
            if rel.startswith('out/') or '/bin/' in w or '/obj/' in w: continue
            json.loads(p.read_text(encoding='utf-8-sig'));json_count+=1
        count=validate_manifest(repo)
        if a.native_results:
            n=Path(a.native_results).resolve(); final=(n/'CP133_NATIVE_ACCEPTANCE_SUMMARY.json').is_file(); validate_native(n,final)
        print(f'       CP133 contract verified: {count} repository-owned files; {json_count} JSON files; revised candidate tables synchronized; production/simulation/Concept/Storyboard frozen; zero substantive trials.')
        return 0
    except Exception as e:
        print(f'CP133 contract failure: {e}',file=sys.stderr);return 1
if __name__=='__main__': raise SystemExit(main())
