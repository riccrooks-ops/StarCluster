#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
SKIP='docs/validation/evidence/checkpoint-139/CP139_REPOSITORY_SHA256SUMS.txt'
def req(v,m):
    if not v: raise AssertionError(m)
def sha(p):
    h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()
def js(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def manifest(p):
    out={}
    for line in p.read_text(encoding='utf-8-sig').splitlines():
        if line.strip(): h,r=line.split('  ',1); out[r]=h
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
    entries=manifest(repo/SKIP); cur=owned(repo)
    req(set(entries)==set(cur),f'manifest path drift missing={sorted(set(entries)-set(cur))[:6]} extra={sorted(set(cur)-set(entries))[:6]}')
    for rel,h in entries.items(): req(sha(repo/rel)==h,f'manifest hash drift {rel}')
    return len(entries)
def validate_native(path,final):
    name='CP139_NATIVE_ACCEPTANCE_SUMMARY.json' if final else 'CP139_REPOSITORY_ONLY_ACCEPTANCE.json'; s=js(path/name)
    req(s['checkpoint']==139 and s['failedGates']==[],'native identity')
    req(s['python'].startswith('Python 3.13') and s['dotnetSdk']=='8.0.423' and s['buildPassed'] is True,'runtimes/build')
    req(s['pythonTestsPassed']==243 and s['xunitPassed']==915 and s['xunitFailed']==0 and s['xunitSkipped']==0,'unit tests')
    req(s['scenarioRunnerSelfTestsPassed']==70 and s['researchParityPassed']==25 and s['cp139FocusedTestsPassed']==9,'deterministic/focused gates')
    req(s['defResFixturesPassed']==8 and s['reconciliationSmokeVariants']==82 and s['reconciliationSmokeErrors']==0,'DEF/RES smoke')
    req(s['productionDamageModel']=='penetration-hardening-v1' and s['researchDamageModel']=='def-res-v1','damage models')
    req(s['sourceMatrixUnmodified'] is True and s['substantiveCombatTrials']==0 and s['automaticPromotion'] is False,'scope boundary')
    req(s['stageAReady'] is False and len(s['stageABlockers'])==3,'Stage A blockers')
    if final: req(s['repositoryOnlyAccepted'] is True,'final must carry repository-only acceptance')
    return s
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo',required=True); ap.add_argument('--native-results'); a=ap.parse_args(); repo=Path(a.repo).resolve()
    try:
        d=js(repo/'tools/checkpoints/checkpoint-139/checkpoint_139_definition.json'); req(d['checkpoint']==139 and d['expectedPythonTests']==243 and d['expectedXunitTests']==915 and d['expectedSmokeVariants']==82,'definition')
        count=validate_manifest(repo)
        json_count=0
        for p in repo.rglob('*.json'):
            rel=p.relative_to(repo).as_posix(); w='/'+rel
            if rel.startswith('out/') or '/bin/' in w or '/obj/' in w: continue
            json.loads(p.read_text(encoding='utf-8-sig')); json_count+=1
        if a.native_results:
            n=Path(a.native_results).resolve(); final=(n/'CP139_NATIVE_ACCEPTANCE_SUMMARY.json').is_file(); validate_native(n,final)
        print(f'       CP139 contract verified: {count} repository-owned files; {json_count} JSON files; production penetration-hardening preserved; research DEF/RES candidate opt-in only; zero substantive trials.')
        return 0
    except Exception as e:
        print(f'CP139 contract failure: {e}',file=sys.stderr); return 1
if __name__=='__main__': raise SystemExit(main())
