#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
SKIP='docs/validation/evidence/checkpoint-140/CP140_REPOSITORY_SHA256SUMS.txt'

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
    req(set(entries)==set(cur),f'manifest path drift missing={sorted(set(entries)-set(cur))[:8]} extra={sorted(set(cur)-set(entries))[:8]}')
    for rel,h in entries.items(): req(sha(repo/rel)==h,f'manifest hash drift {rel}')
    return len(entries)
def unwrap_summary(p):
    x=js(p); return x.get('analysis',x)
def validate_stage_merge(root):
    p=root/'stage-a-merged'/'summary.json'; req(p.is_file(),'merged Stage-A summary missing')
    a=unwrap_summary(p)
    req(a['passed'] is True and list(a['failedGates'])==[],'merged Stage-A gates')
    req(a['stageAScenarios']==8220 and a['boundScenarios']==8220 and a['integrationSmokeTrials']==8220 and a['smokeErrors']==0,'Stage-A smoke coverage')
    req(a['batchCount']==9 and a['isolatedProcessBatching'] is True,'Stage-A batch execution')
    req(a['turnTelemetrySchemaConsistencyPass']==8220 and a['battleTelemetryRows']==16440,'telemetry coverage')
    req(a['instrumentationEquivalenceCases']==12 and a['instrumentationEquivalencePass']==12,'instrumentation equivalence')
    req(a['tpConflictTurnsObserved']>0 and a['powerCrisisTpConflictTurnsObserved']>0,'TP conflict telemetry unexercised')
    req(a['sourceMatrixUnmodified'] is True and a['stageAExecutionReady'] is True,'matrix/Stage-A readiness')
    req(a['substantiveCombatTrials']==0 and a['promotionAllowed'] is False,'scope boundary')
    return a
def validate_native(path,final):
    name='CP140_NATIVE_ACCEPTANCE_SUMMARY.json' if final else 'CP140_REPOSITORY_ONLY_ACCEPTANCE.json'; s=js(path/name)
    req(s['checkpoint']==140 and s['failedGates']==[],'native identity')
    req(s['python'].startswith('Python 3.13') and s['dotnetSdk']=='8.0.423' and s['buildPassed'] is True,'runtimes/build')
    req(s['pythonTestsPassed']==253 and s['xunitPassed']==915 and s['xunitFailed']==0 and s['xunitSkipped']==0,'unit tests')
    req(s['scenarioRunnerSelfTestsPassed']==70 and s['researchParityPassed']==25,'deterministic/parity gates')
    req(s['cp139FocusedTestsPassed']==9 and s['cp140FocusedTestsPassed']==10,'focused test gates')
    req(s['defResFixturesPassed']==8 and s['cp139ReconciliationSmokeVariants']==82 and s['cp139ReconciliationSmokeErrors']==0,'CP139 regression')
    req(s['stageAScenarios']==8220 and s['stageAIntegrationSmokeTrials']==8220 and s['stageASmokeErrors']==0,'Stage-A native smoke')
    req(s['stageASmokeBatches']==9 and s['battleTelemetryRows']==16440 and s['turnTelemetrySchemaConsistencyPass']==8220,'Stage-A native telemetry')
    req(s['instrumentationEquivalencePassed']==12 and s['tpConflictTurnsObserved']>0 and s['powerCrisisTpConflictTurnsObserved']>0,'TP/equivalence native gates')
    req(s['sourceMatrixUnmodified'] is True and s['stageAExecutionReady'] is True,'native matrix/readiness')
    req(s['substantiveCombatTrials']==0 and s['automaticPromotion'] is False,'native scope boundary')
    if final:
        req(s['repositoryOnlyAccepted'] is True,'final must carry repository-only acceptance')
        req(s['deterministicStageASmokeReproduced'] is True,'final Stage-A deterministic replay')
    return s
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo',required=True); ap.add_argument('--native-results'); a=ap.parse_args(); repo=Path(a.repo).resolve()
    try:
        d=js(repo/'tools/checkpoints/checkpoint-140/checkpoint_140_definition.json')
        req(d['checkpoint']==140 and d['expectedPythonTests']==253 and d['expectedXunitTests']==915 and d['expectedStageAScenarios']==8220,'definition')
        count=validate_manifest(repo)
        json_count=0
        for p in repo.rglob('*.json'):
            rel=p.relative_to(repo).as_posix(); w='/'+rel
            if rel.startswith('out/') or '/bin/' in w or '/obj/' in w: continue
            json.loads(p.read_text(encoding='utf-8-sig')); json_count+=1
        if a.native_results:
            n=Path(a.native_results).resolve(); final=(n/'CP140_NATIVE_ACCEPTANCE_SUMMARY.json').is_file(); validate_native(n,final); validate_stage_merge(n)
        print(f'       CP140 contract verified: {count} repository-owned files; {json_count} JSON files; CP139 production/control authority frozen; v22C Stage-A integration smoke is execution-only and promotion-disabled.')
        return 0
    except Exception as e:
        print(f'CP140 contract failure: {e}',file=sys.stderr); return 1
if __name__=='__main__': raise SystemExit(main())
