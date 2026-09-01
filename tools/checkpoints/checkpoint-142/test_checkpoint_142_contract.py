#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json,sys
from pathlib import Path
SKIP='docs/validation/evidence/checkpoint-142/CP142_REPOSITORY_SHA256SUMS.txt'

def req(v,m):
    if not v:raise AssertionError(m)
def sha(p):
    h=hashlib.sha256();h.update(p.read_bytes());return h.hexdigest()
def js(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def manifest(p):
    out={}
    for line in p.read_text(encoding='utf-8-sig').splitlines():
        if line.strip():h,r=line.split('  ',1);out[r]=h
    return out
def owned(repo):
    out=[]
    for p in repo.rglob('*'):
        if not p.is_file():continue
        rel=p.relative_to(repo).as_posix();w='/'+rel
        if rel.startswith(('out/','.git/')) or '/__pycache__/' in w or rel.endswith('.pyc') or '/bin/' in w or '/obj/' in w or '/TestResults/' in w:continue
        if rel==SKIP:continue
        out.append(rel)
    return sorted(out)
def validate_manifest(repo):
    entries=manifest(repo/SKIP);cur=owned(repo)
    req(set(entries)==set(cur),f'manifest path drift missing={sorted(set(entries)-set(cur))[:8]} extra={sorted(set(cur)-set(entries))[:8]}')
    for rel,h in entries.items():req(sha(repo/rel)==h,f'manifest hash drift {rel}')
    return len(entries)
def unwrap(p):
    x=js(p);return x.get('analysis',x)
def no_failed_gates(v): return v==0 or v==[]
def read_rows(p):
    with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def validate_merge(root,dirname='reconciliation-merged'):
    base=root/dirname;p=base/'summary.json';req(p.is_file(),f'{dirname} summary missing');a=unwrap(p)
    req(a['passed'] is True and no_failed_gates(a.get('failedGates')),f'{dirname} gates')
    req(a['stageAScenarios']==8220 and a['hardTurnSentinel']==60,f'{dirname} coverage/sentinel')
    req(a['sourceMatrixUnmodified'] is True and a['stageASubstantiveMeasurementReady'] is True,f'{dirname} matrix/readiness')
    req(a['substantiveCombatTrials']==0 and a['promotionAllowed'] is False,f'{dirname} scope boundary')
    req(a['reconciliationLedgerRows']==531 and a['changedVsCp141LedgerRows']==72 and a['explicitUnresolvedLedgerRows']==7,f'{dirname} reconciliation ledger')
    smoke=read_rows(base/'duration_smoke_results.csv');req(len(smoke)==8220 and all(int(r['turns'])<=60 for r in smoke),f'{dirname} smoke sentinel')
    req(all(not r['error'] for r in smoke),f'{dirname} smoke errors')
    ledger=read_rows(base/'reconciliation_field_ledger.csv');req(len(ledger)==531,f'{dirname} ledger rows')
    changed=[r for r in ledger if int(r['changed_vs_cp141'])];req(len(changed)==72,f'{dirname} changed rows')
    req(sum(r['stage_a_executable']=='YES' for r in changed)==66,f'{dirname} executable changed rows')
    req(sum(r['classification']=='UNRESOLVED_CONFLICT_GAP' for r in ledger)==7,f'{dirname} unresolved rows')
    # Critical regressions caught by the deep pass.
    k2=next(r for r in ledger if r['system']=='Kinetic PDS' and r['field']=='baseChancePp' and r['tl']=='2')
    req('effective 34' in k2['cp141_value'] and 'effective 22' in k2['cp142_value'],'PDS computer-double-count correction evidence')
    s9=next(r for r in ledger if r['system']=='Shield' and r['field']=='baseRecharge' and r['tl']=='9')
    req(str(s9['cp141_value'])=='6' and str(s9['cp142_value'])=='0','Shield recharge reconciliation evidence')
    return a
def validate_native(path,final):
    name='CP142_NATIVE_ACCEPTANCE_SUMMARY.json' if final else 'CP142_REPOSITORY_ONLY_ACCEPTANCE.json';s=js(path/name)
    req(s['checkpoint']==142 and s['failedGates']==[],'native identity')
    req(s['python'].startswith('Python 3.13') and s['dotnetSdk']=='8.0.423' and s['buildPassed'] is True,'runtimes/build')
    req(s['pythonTestsPassed']==275 and s['xunitPassed']==915 and s['xunitFailed']==0 and s['xunitSkipped']==0,'unit tests')
    req(s['scenarioRunnerSelfTestsPassed']==70 and s['researchParityPassed']==25,'deterministic/parity gates')
    req(s['cp139FocusedTestsPassed']==9 and s['cp140FocusedTestsPassed']==10 and s['cp141FocusedTestsPassed']==10 and s['cp142FocusedTestsPassed']==12,'focused tests')
    req(s['defResFixturesPassed']==8 and s['cp139ReconciliationSmokeVariants']==82 and s['cp139ReconciliationSmokeErrors']==0,'CP139 regression')
    req(s['reconciliationScenarios']==8220 and s['reconciliationSmokeErrors']==0 and s['reconciliationSmokeBatches']==9,'reconciliation native smoke')
    req(s['reconciliationLedgerRows']==531 and s['changedVsCp141LedgerRows']==72 and s['explicitUnresolvedLedgerRows']==7,'native ledger')
    req(s['sourceMatrixUnmodified'] is True and s['stageASubstantiveMeasurementReady'] is True,'native matrix/readiness')
    req(s['substantiveCombatTrials']==0 and s['automaticPromotion'] is False,'native scope boundary')
    if final:
        req(s['repositoryOnlyAccepted'] is True,'final must carry repository-only acceptance')
        req(s['deterministicReconciliationSmokeReproduced'] is True,'final reconciliation deterministic replay')
    return s
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);ap.add_argument('--native-results');a=ap.parse_args();repo=Path(a.repo).resolve()
    try:
        d=js(repo/'tools/checkpoints/checkpoint-142/checkpoint_142_definition.json')
        req(d['checkpoint']==142 and d['expectedPythonTests']==275 and d['expectedXunitTests']==915 and d['expectedStageAScenarios']==8220,'definition')
        count=validate_manifest(repo);json_count=0
        for p in repo.rglob('*.json'):
            rel=p.relative_to(repo).as_posix();w='/'+rel
            if rel.startswith('out/') or '/bin/' in w or '/obj/' in w:continue
            json.loads(p.read_text(encoding='utf-8-sig'));json_count+=1
        if a.native_results:
            n=Path(a.native_results).resolve();final=(n/'CP142_NATIVE_ACCEPTANCE_SUMMARY.json').is_file();validate_native(n,final);validate_merge(n,'reconciliation-final-merged' if final else 'reconciliation-merged')
        print(f'       CP142 contract verified: {count} repository-owned files; {json_count} JSON files; deep combat-surface reconciliation is research-only, source-matrix frozen, and promotion-disabled.')
        return 0
    except Exception as e:
        print(f'CP142 contract failure: {e}',file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
