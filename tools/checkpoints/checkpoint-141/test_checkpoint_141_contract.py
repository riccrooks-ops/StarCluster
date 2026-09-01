#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json,sys
from pathlib import Path
SKIP='docs/validation/evidence/checkpoint-141/CP141_REPOSITORY_SHA256SUMS.txt'

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
def unwrap(p):
    x=js(p); return x.get('analysis',x)
def read_rows(p):
    with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def validate_duration_merge(root):
    p=root/'duration-merged'/'summary.json'; req(p.is_file(),'duration merge summary missing')
    a=unwrap(p)
    req(a['passed'] is True and list(a['failedGates'])==[],'duration merge gates')
    req(a['stageAScenarios']==8220 and a['hardTurnSentinel']==60 and a['longResolvedTurn']==25,'duration coverage/boundaries')
    req(a['sourceMatrixUnmodified'] is True and a['stageASubstantiveMeasurementReady'] is True,'matrix/measurement readiness')
    req(a['substantiveCombatTrials']==0 and a['promotionAllowed'] is False,'scope boundary')
    smoke=read_rows(root/'duration-merged'/'duration_smoke_results.csv')
    req(len(smoke)==8220 and all(int(r['turns'])<=60 for r in smoke),'duration smoke sentinel')
    req(all(not r['error'] for r in smoke),'duration smoke errors')
    req(any(int(r['resolved_ge25_flag']) for r in smoke),'long-resolved metric unexercised')
    req(any(int(r['turn_cap_flag']) for r in smoke),'turn-cap sentinel unexercised')
    signals={r['dominant_cap_signal']:int(r['scenarios']) for r in read_rows(root/'duration-merged'/'turn_cap_signal_summary.csv')}
    req(signals.get('DEFENSIVE_RECOVERY_LOOP',0)>0,'defensive recovery signal unexercised')
    req(signals.get('ACTIVE_ATTRITION_AT_CAP',0)>0,'active attrition cap signal unexercised')
    return a
def validate_native(path,final):
    name='CP141_NATIVE_ACCEPTANCE_SUMMARY.json' if final else 'CP141_REPOSITORY_ONLY_ACCEPTANCE.json'; s=js(path/name)
    req(s['checkpoint']==141 and s['failedGates']==[],'native identity')
    req(s['python'].startswith('Python 3.13') and s['dotnetSdk']=='8.0.423' and s['buildPassed'] is True,'runtimes/build')
    req(s['pythonTestsPassed']==263 and s['xunitPassed']==915 and s['xunitFailed']==0 and s['xunitSkipped']==0,'unit tests')
    req(s['scenarioRunnerSelfTestsPassed']==70 and s['researchParityPassed']==25,'deterministic/parity gates')
    req(s['cp139FocusedTestsPassed']==9 and s['cp140FocusedTestsPassed']==10 and s['cp141FocusedTestsPassed']==10,'focused tests')
    req(s['defResFixturesPassed']==8 and s['cp139ReconciliationSmokeVariants']==82 and s['cp139ReconciliationSmokeErrors']==0,'CP139 regression')
    req(s['durationScenarios']==8220 and s['durationSmokeErrors']==0 and s['durationSmokeBatches']==9,'duration native smoke')
    req(s['hardTurnSentinel']==60 and s['longResolvedTurn']==25,'duration native boundaries')
    req(s['sourceMatrixUnmodified'] is True and s['stageASubstantiveMeasurementReady'] is True,'native matrix/readiness')
    req(s['substantiveCombatTrials']==0 and s['automaticPromotion'] is False,'native scope boundary')
    if final:
        req(s['repositoryOnlyAccepted'] is True,'final must carry repository-only acceptance')
        req(s['deterministicDurationSmokeReproduced'] is True,'final duration deterministic replay')
    return s
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo',required=True); ap.add_argument('--native-results'); a=ap.parse_args(); repo=Path(a.repo).resolve()
    try:
        d=js(repo/'tools/checkpoints/checkpoint-141/checkpoint_141_definition.json')
        req(d['checkpoint']==141 and d['expectedPythonTests']==263 and d['expectedXunitTests']==915 and d['expectedStageAScenarios']==8220,'definition')
        count=validate_manifest(repo)
        json_count=0
        for p in repo.rglob('*.json'):
            rel=p.relative_to(repo).as_posix(); w='/'+rel
            if rel.startswith('out/') or '/bin/' in w or '/obj/' in w: continue
            json.loads(p.read_text(encoding='utf-8-sig')); json_count+=1
        if a.native_results:
            n=Path(a.native_results).resolve(); final=(n/'CP141_NATIVE_ACCEPTANCE_SUMMARY.json').is_file(); validate_native(n,final); validate_duration_merge(n)
        print(f'       CP141 contract verified: {count} repository-owned files; {json_count} JSON files; 60-turn gameplay sentinel and conservative stalemate semantics are measurement-only, promotion-disabled.')
        return 0
    except Exception as e:
        print(f'CP141 contract failure: {e}',file=sys.stderr); return 1
if __name__=='__main__': raise SystemExit(main())
