#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json,sys
from pathlib import Path

def req(v,m):
    if not v: raise AssertionError(m)
def text(p:Path): req(p.is_file(),f'missing {p}'); return p.read_text(encoding='utf-8-sig')
def js(p:Path): return json.loads(text(p))
def sha(p:Path):
    h=hashlib.sha256();
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def manifest(p:Path):
    out={}
    for line in text(p).splitlines():
        if line.strip(): d,r=line.split('  ',1);out[r]=d
    return out
def owned_files(repo:Path):
    out=[]; skip='docs/validation/evidence/checkpoint-130/CP130_REPOSITORY_SHA256SUMS.txt'
    for p in repo.rglob('*'):
        if not p.is_file(): continue
        rel=p.relative_to(repo).as_posix(); wrapped='/'+rel
        if rel.startswith(('out/','.git/')) or '/__pycache__/' in wrapped or rel.endswith('.pyc') or '/bin/' in wrapped or '/obj/' in wrapped or '/TestResults/' in wrapped: continue
        if rel==skip: continue
        out.append(rel)
    return sorted(out)
def validate_manifest(repo:Path):
    p=repo/'docs/validation/evidence/checkpoint-130/CP130_REPOSITORY_SHA256SUMS.txt'; m=manifest(p); cur=owned_files(repo)
    req(set(cur)==set(m),f'manifest path drift missing={sorted(set(m)-set(cur))[:5]} extra={sorted(set(cur)-set(m))[:5]}')
    for rel,d in m.items(): req(sha(repo/rel)==d,f'manifest hash drift: {rel}')
    return len(m)
def validate_repo_only(native:Path):
    s=js(native/'CP130_REPOSITORY_ONLY_ACCEPTANCE.json')
    req(s['checkpoint']==130 and s['repositoryOnly'] is True and s['failedGates']==[],'repository-only identity')
    req(s['python'].startswith('Python 3.13') and s['dotnetSdk']=='8.0.423','runtime versions')
    req(s['pythonTestsPassed']==183 and s['xunitPassed']==907 and s['xunitFailed']==0 and s['xunitSkipped']==0,'test counts')
    req(s['scenarioRunnerSelfTestsPassed']==70 and s['researchParityPassed']==25,'self-test/parity')
    req(s['technologyValuesChanged'] is False and s['productionSourceChanged'] is False and s['scenarioDefinitionsChanged'] is False,'frozen values/production')
    req(s['missileCandidatesResearchOnly'] is True and s['auxMagazineExecuted'] is False and s['swarmerChanged'] is False,'candidate boundary')
    req(s['legalBuilds']==9427 and s['generatedVariants']==240996 and s['pipelineSmokeTrials']==240996 and s['pipelineSmokeTrialErrors']==0,'plan/smoke')
    req(s['symmetryComparisons']==2250 and s['symmetryCombatExecutions']==4500 and s['symmetryMismatches']==0,'symmetry')
    req(1<=int(s['repositoryOnlyJobs'])<=61 and s['substantiveTrials']==0,'repository-only Jobs/substantive boundary')
    plan=js(native/'plan/analysis.json'); smoke=js(native/'smoke/analysis.json'); sym=js(native/'symmetry/analysis.json')
    req(plan['checkpoint']==130 and plan['mode']=='plan' and plan['failedGates']==[],'plan output')
    req(smoke['checkpoint']==130 and smoke['mode']=='smoke' and smoke['variants']==240996 and smoke['trialErrors']==0 and smoke['failedGates']==[],'smoke output')
    req(sym['checkpoint']==129 and sym['mode']=='symmetry_gate' and sym['mismatches']==0 and sym['failedGates']==[],'inherited symmetry output')
    return s
def validate_final(native:Path):
    prior=validate_repo_only(native); s=js(native/'CP130_NATIVE_ACCEPTANCE_SUMMARY.json')
    req(s['checkpoint']==130 and s['repositoryOnly'] is False and s['failedGates']==[],'final identity')
    for k in ('python','dotnetSdk','pythonTestsPassed','xunitPassed','scenarioRunnerSelfTestsPassed','researchParityPassed','generatedVariants','pipelineSmokeTrials','symmetryComparisons','symmetryMismatches'):
        req(s[k]==prior[k],f'final/prior mismatch {k}')
    req(1<=int(s['substantiveJobs'])<=61 and s['substantiveTrials']==24099600 and s['substantiveTrialErrors']==0,'substantive workload')
    req(s['technologyValuesChanged'] is False and s['missileCandidatesResearchOnly'] is True and s['cp129ControlReplicationPassed'] is True,'final boundary/replication')
    a=js(native/'substantive/analysis.json')
    req(a['checkpoint']==130 and a['mode']=='substantive' and a['variants']==240996 and a['totalTrials']==24099600 and a['trialErrors']==0 and a['failedGates']==[],'substantive analysis')
    rows=list(csv.DictReader((native/'substantive/family_plot_inputs.csv').open(newline='',encoding='utf-8')))
    req(len(rows)==34,'family plot candidate row count')
    rep=list(csv.DictReader((native/'substantive/cp129_control_replication.csv').open(newline='',encoding='utf-8')))
    req(len(rep)==36 and all(abs(float(r['delta']))<=1e-12 for r in rep),'accepted CP129 control replication')
    req((native/'substantive/missile_context_telemetry.csv').is_file(),'context telemetry missing')
    req(not list((native/'substantive/candidates').rglob('variants.csv')),'raw substantive variant detail should be discarded on success')
    return s
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);ap.add_argument('--native-results');a=ap.parse_args();repo=Path(a.repo).resolve()
    try:
        d=js(repo/'tools/checkpoints/checkpoint-130/checkpoint_130_definition.json')
        req(d['checkpoint']==130 and d['expectedPythonTests']==183 and d['monteCarloStudy'] is True,'definition')
        req(d['expectedGeneratedVariants']==240996 and d['expectedSubstantiveTrials']==24099600,'definition workload')
        accepted=js(repo/'docs/validation/evidence/checkpoint-130/CP129_NATIVE_ACCEPTANCE_SUMMARY.json')
        req(accepted['checkpoint']==129 and accepted['failedGates']==[] and accepted['substantiveTrials']==45665000,'accepted CP129 evidence')
        if a.native_results:
            native=Path(a.native_results).resolve()
            if (native/'CP130_NATIVE_ACCEPTANCE_SUMMARY.json').is_file(): validate_final(native)
            else: validate_repo_only(native)
        njson=0
        for p in repo.rglob('*.json'):
            rel=p.relative_to(repo).as_posix(); wrapped='/'+rel
            if rel.startswith('out/') or '/bin/' in wrapped or '/obj/' in wrapped: continue
            json.loads(p.read_text(encoding='utf-8-sig'));njson+=1
        count=validate_manifest(repo)
        print(f'       CP130 contract verified: {count} repository-owned files; {njson} JSON files; CP129 accepted; current numerical authority frozen; Missile candidates research-only.')
        return 0
    except Exception as e:
        print(f'CP130 contract failure: {e}',file=sys.stderr);return 1
if __name__=='__main__': raise SystemExit(main())
