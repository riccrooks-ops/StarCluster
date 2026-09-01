#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json,sys
from pathlib import Path
SKIP='docs/validation/evidence/checkpoint-143/CP143_REPOSITORY_SHA256SUMS.txt'
REF_SHA='07752e40076604e16e1a525a999cfcc248e2716bbdd8d7138d0b0f805afa5e94'

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
def read_rows(p):
    with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def validate_merge(root,dirname='attribution-merged'):
    base=root/dirname;p=base/'summary.json';req(p.is_file(),f'{dirname} summary missing');a=js(p)
    req(a['passed'] is True and a.get('failedGates',[])==[],f'{dirname} gates')
    req(a['missileMirrorScenarios']==1980 and a['executionErrors']==0,f'{dirname} scenario coverage')
    req(a['resolved']==1751 and a['resolvedGe25']==1085 and a['turnCapSentinels']==228 and a['safeStalemates']==1,f'{dirname} paired outcomes')
    req(a['hardTurnSentinel']==60 and a['longResolvedTurn']==25,f'{dirname} duration boundary')
    req(a['instrumentationEquivalenceCases']==12 and a['instrumentationEquivalencePassed']==12,f'{dirname} instrumentation equivalence')
    req(a['cp142PairedOutcomeReferenceCases']==1980 and a['cp142PairedOutcomeMatches']==1980,f'{dirname} CP142 paired equivalence')
    req(a['cp142PairedOutcomeReferenceSha256']==REF_SHA,f'{dirname} CP142 reference hash')
    req(a['sourceMatrixUnmodified'] is True and a['substantiveCombatTrials']==0 and a['tuningAllowed'] is False and a['promotionAllowed'] is False,f'{dirname} scope boundary')
    rows=read_rows(base/'missile_mirror_attribution_results.csv');req(len(rows)==1980 and len({r['scenario_id'] for r in rows})==1980,f'{dirname} attribution rows')
    req(all(not r['error'] and int(r['turns'])<=60 and int(r['turn_telemetry_coverage_pass']) for r in rows),f'{dirname} execution/telemetry')
    eq=read_rows(base/'instrumentation_equivalence.csv');req(len(eq)==12 and all(int(r['result_equivalent']) and int(r['turn_telemetry_equivalent']) for r in eq),f'{dirname} observation neutrality')
    paired=read_rows(base/'cp142_paired_outcome_equivalence.csv');req(len(paired)==1980 and all(int(r['exact_cp142_outcome_match']) for r in paired),f'{dirname} CP142 paired drift')
    signals=read_rows(base/'missile_mirror_pacing_signal_summary.csv')
    overall={r['signal']:int(r['scenarios']) for r in signals if r['group_type']=='OVERALL' and r['group_key']=='ALL'}
    req(overall=={'HEALTHY_UNDER25':666,'OFFENSIVE_EXHAUSTION':1,'SENSOR_WEAPON_ENVELOPE_OSCILLATION':1284,'TP_LAUNCH_DENIAL':29},f'{dirname} pacing signal signature {overall}')
    groups=read_rows(base/'missile_mirror_group_summary.csv');overall_group=next(r for r in groups if r['group_type']=='OVERALL')
    req(float(overall_group['mean_terminal_transit_turns'])<0.1,'launch-to-terminal should remain negligible')
    req(int(float(overall_group['range_exhaustions']))==0,'missile range exhaustion should be zero')
    req(float(overall_group['no_firm_geometry_or_acquisition_turn_fraction'])>0.70,'Firm-track geometry/acquisition signal unexpectedly weak')
    req(float(overall_group['no_firm_ew_downgrade_turn_fraction'])==0.0,'EW downgrade unexpectedly dominates paired population')
    return a
def validate_native(path,final):
    name='CP143_NATIVE_ACCEPTANCE_SUMMARY.json' if final else 'CP143_REPOSITORY_ONLY_ACCEPTANCE.json';s=js(path/name)
    req(s['checkpoint']==143 and s['failedGates']==[],'native identity')
    req(s['python'].startswith('Python 3.13') and s['dotnetSdk']=='8.0.423' and s['buildPassed'] is True,'runtimes/build')
    req(s['pythonTestsPassed']==287 and s['xunitPassed']==915 and s['xunitFailed']==0 and s['xunitSkipped']==0,'unit tests')
    req(s['scenarioRunnerSelfTestsPassed']==70 and s['researchParityPassed']==25,'deterministic/parity gates')
    req(s['cp139FocusedTestsPassed']==9 and s['cp140FocusedTestsPassed']==10 and s['cp141FocusedTestsPassed']==10 and s['cp142FocusedTestsPassed']==12 and s['cp143FocusedTestsPassed']==12,'focused tests')
    req(s['defResFixturesPassed']==8 and s['cp139ReconciliationSmokeVariants']==82 and s['cp139ReconciliationSmokeErrors']==0,'CP139 regression')
    req(s['cp142ReconciliationLedgerRows']==531 and s['cp142ChangedRows']==72 and s['cp142ExplicitUnresolvedRows']==7,'CP142 reconciliation regression')
    req(s['missileMirrorScenarios']==1980 and s['attributionErrors']==0 and s['attributionBatches']==4,'native attribution')
    req(s['instrumentationEquivalencePassed']==12 and s['cp142PairedOutcomeMatches']==1980,'native equivalence')
    req(s['resolved']==1751 and s['resolvedGe25']==1085 and s['turnCapSentinels']==228 and s['safeStalemates']==1,'native paired outcomes')
    req(s['sourceMatrixUnmodified'] is True and s['substantiveCombatTrials']==0 and s['tuningAllowed'] is False and s['automaticPromotion'] is False,'native scope')
    if final:
        req(s['repositoryOnlyAccepted'] is True,'final must carry RepositoryOnly acceptance')
        req(s['deterministicAttributionReproduced'] is True,'final deterministic attribution replay')
    return s
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);ap.add_argument('--native-results');a=ap.parse_args();repo=Path(a.repo).resolve()
    try:
        d=js(repo/'tools/checkpoints/checkpoint-143/checkpoint_143_definition.json')
        req(d['checkpoint']==143 and d['expectedPythonTests']==287 and d['expectedXunitTests']==915 and d['expectedMissileMirrorScenarios']==1980,'definition')
        count=validate_manifest(repo);json_count=0
        for p in repo.rglob('*.json'):
            rel=p.relative_to(repo).as_posix();w='/'+rel
            if rel.startswith('out/') or '/bin/' in w or '/obj/' in w:continue
            json.loads(p.read_text(encoding='utf-8-sig'));json_count+=1
        ref=repo/'docs/archive/testing/pre-cp165-active/cp143_cp142_native_missile_mirror_reference.csv';req(sha(ref)==REF_SHA,'paired reference drift')
        if a.native_results:
            n=Path(a.native_results).resolve();final=(n/'CP143_NATIVE_ACCEPTANCE_SUMMARY.json').is_file();validate_native(n,final);validate_merge(n,'attribution-final-merged' if final else 'attribution-merged')
        print(f'       CP143 contract verified: {count} repository-owned files; {json_count} JSON files; attribution is observation-only, exactly paired to native CP142, source-matrix frozen, and tuning/promotion disabled.')
        return 0
    except Exception as e:
        print(f'CP143 contract failure: {e}',file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
