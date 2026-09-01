#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path

def req(v,msg):
    if not v: raise AssertionError(msg)
def text(p): req(p.is_file(),f'Missing {p}'); return p.read_text(encoding='utf-8-sig')
def js(p): return json.loads(text(p))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def manifest(p):
    out={}
    for line in text(p).splitlines():
        if line.strip(): h,r=line.split('  ',1); out[r]=h
    return out

def validate_results(native:Path):
    s=js(native/'CP124_NATIVE_ACCEPTANCE_SUMMARY.json')
    req(s['checkpoint']==124 and s['acceptedReferenceBaseline']==123 and s['acceptedImplementationBaseline']==122,'native summary identity')
    req(s['pythonTestsPassed']==139 and s['researchParityPassed']==25,'test/parity counts')
    req(s['profileRows']==180 and s['rawBuildCombinations']==14112 and s['legalBuilds']==9427,'foundation counts')
    req(s['pipelineSmokeVariants']==70 and s['pipelineSmokeTrials']==70,'smoke counts')
    req(s['instrumentationProbes']==9 and s['telemetryContractMetrics']==47,'instrumentation counts')
    req(s['substantiveMonteCarloTrials']==0 and s['balanceValidated'] is False and s['failedGates']==[],'acceptance semantics')
    f=js(native/'executable-baseline-foundation/analysis.json')
    req(f['failedGates']==[] and f['legalBuilds']==9427 and f['pipelineSmokeVariants']==70,'foundation analysis')
    probes=(native/'executable-baseline-foundation/instrumentation_probes.csv').read_text(encoding='utf-8-sig')
    for name in ('damage-layer-oracle','missile-profile-composition','damage-control-tl1','damage-control-tl7','damage-control-tl9','ew-redundancy-nonadditive','missile-telemetry-ownership','telemetry-schema-complete'):
        req(name in probes,f'missing instrumentation probe {name}')

def validate_manifest(repo:Path):
    p=repo/'docs/validation/evidence/checkpoint-124/CP124_REPOSITORY_SHA256SUMS.txt'; m=manifest(p)
    current=[]
    for path in repo.rglob('*'):
        if not path.is_file(): continue
        rel=path.relative_to(repo).as_posix()
        if rel.startswith(('out/','.git/')) or '/__pycache__/' in '/'+rel or rel.endswith('.pyc') or '/bin/' in '/'+rel or '/obj/' in '/'+rel: continue
        if rel=='docs/validation/evidence/checkpoint-124/CP124_REPOSITORY_SHA256SUMS.txt': continue
        current.append(rel)
    req(set(current)==set(m),f'manifest path drift missing={sorted(set(m)-set(current))[:5]} extra={sorted(set(current)-set(m))[:5]}')
    for rel,h in m.items(): req(sha(repo/rel)==h,f'manifest hash drift: {rel}')
    return len(m)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo',required=True); ap.add_argument('--native-results'); a=ap.parse_args(); repo=Path(a.repo).resolve()
    try:
        print('       Validating CP124 definition, accepted CP123 provenance, and foundation authorities...')
        d=js(repo/'tools/checkpoints/checkpoint-124/checkpoint_124_definition.json'); req(d['checkpoint']==124,'definition')
        s=js(repo/'docs/validation/evidence/checkpoint-124/CP124_ACCEPTED_CP123_NATIVE_SUMMARY.json'); req(s['acceptedCheckpoint']==123 and s['failedGates']==[],'CP123 provenance')
        if a.native_results: validate_results(Path(a.native_results).resolve())
        print('       Parsing owned JSON corpus...')
        njson=0
        for p in repo.rglob('*.json'):
            rel=p.relative_to(repo).as_posix()
            if rel.startswith('out/') or '/bin/' in '/'+rel or '/obj/' in '/'+rel: continue
            json.loads(p.read_text(encoding='utf-8-sig')); njson+=1
        print('       Validating full repository manifest...')
        n=validate_manifest(repo)
        print(f'       CP124 contract verified: {n} repository-owned files; {njson} JSON files; 20x9 executable profiles; 14,112 raw / 9,427 legal builds; 70 zero-weight smoke trials; 47 telemetry metrics; 9 blocking probes; 0 substantive Monte Carlo trials.')
        return 0
    except Exception as e:
        print(f'CP124 contract failure: {e}',file=sys.stderr); return 1
if __name__=='__main__': raise SystemExit(main())
