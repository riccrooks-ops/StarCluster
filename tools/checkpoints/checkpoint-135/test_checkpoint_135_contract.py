#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
SKIP='docs/validation/evidence/checkpoint-135/CP135_REPOSITORY_SHA256SUMS.txt'
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
        if not p.is_file():continue
        rel=p.relative_to(repo).as_posix();w='/'+rel
        if rel.startswith(('out/','.git/')) or '/__pycache__/' in w or rel.endswith('.pyc') or '/bin/' in w or '/obj/' in w or '/TestResults/' in w:continue
        if rel==SKIP:continue
        out.append(rel)
    return sorted(out)
def validate_manifest(repo):
    entries=manifest(repo/SKIP);cur=owned(repo)
    req(set(entries)==set(cur),f'manifest path drift missing={sorted(set(entries)-set(cur))[:6]} extra={sorted(set(cur)-set(entries))[:6]}')
    for rel,h in entries.items(): req(sha(repo/rel)==h,f'manifest hash drift {rel}')
    return len(entries)
def validate_native(native,final=False):
    name='CP135_NATIVE_ACCEPTANCE_SUMMARY.json' if final else 'CP135_REPOSITORY_ONLY_ACCEPTANCE.json';s=js(native/name)
    req(s['checkpoint']==135 and s['failedGates']==[],'native identity')
    req(s['python'].startswith('Python 3.13') and s['dotnetSdk']=='8.0.423' and s['buildPassed'] is True,'runtimes/build')
    req(s['pythonTestsPassed']==211 and s['xunitPassed']==913 and s['xunitFailed']==0 and s['xunitSkipped']==0,'unit tests')
    req(s['scenarioRunnerSelfTestsPassed']==70 and s['researchParityPassed']==25 and s['cp135KernelTestsPassed']==7,'standing deterministic gates')
    req(s['deterministicScenarioCorpusPassed'] is True and s['tl1PhaseACorpusPassed'] is True,'scenario corpora')
    req(s['canonicalKernelVersion']=='0.3' and s['canonicalDamageModel']=='penetration-hardening-v1','kernel identity')
    req(s['logicalContexts']==196 and s['generatedVariants']==392 and s['tl6Variants']==136,'plan shape')
    req(s['symmetryComparisons']==50 and s['symmetryMismatches']==0 and s['smokeTrials']==392 and s['smokeTrialErrors']==0 and s['smokeMechanicsFlags']==0,'symmetry/smoke')
    req(s['mandatoryDefenses']==['shield','armor'] and s['tl6ArmorProfiles']==['mainline','A_b1'],'defense controls')
    req(s['damageControlStudyDoctrine']=='HullOnlyWhenDamaged' and s['commonRandomNumberBaseline']==134 and s['masterSeed']==134001,'DamCon/CRN boundary')
    req(s['mixedTlShipsExecuted'] is False and s['automaticPromotion'] is False and s['balanceTargets'] is None,'interpretation boundary')
    if final:
        req(s['substantiveVariants']==392 and s['substantiveLogicalContexts']==196 and s['substantiveTrialsPerVariant']==5000 and s['substantiveTrials']==1960000,'substantive shape')
        req(s['substantiveTrialErrors']==0 and s['substantiveMechanicsFlags']==0,'substantive mechanics gates')
        req(s['pdsComparisons']==80 and s['tl6ArmorContexts']==68,'diagnostic strata')
        req(s['damageControlTelemetryPresent'] is True,'DamCon telemetry marker')
    else:req(s['substantiveTrials']==0,'repository-only must not run substantive study')
    return s
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);ap.add_argument('--native-results');a=ap.parse_args();repo=Path(a.repo).resolve()
    try:
        d=js(repo/'tools/checkpoints/checkpoint-135/checkpoint_135_definition.json');req(d['checkpoint']==135 and d['declaredSubstantiveTrials']==1960000 and d['expectedVariants']==392,'definition')
        json_count=0
        for p in repo.rglob('*.json'):
            rel=p.relative_to(repo).as_posix();w='/'+rel
            if rel.startswith('out/') or '/bin/' in w or '/obj/' in w:continue
            json.loads(p.read_text(encoding='utf-8-sig'));json_count+=1
        count=validate_manifest(repo)
        if a.native_results:
            n=Path(a.native_results).resolve();final=(n/'CP135_NATIVE_ACCEPTANCE_SUMMARY.json').is_file();validate_native(n,final)
        print(f'       CP135 contract verified: {count} repository-owned files; {json_count} JSON files; kernel 0.3; 196 contexts / 392 variants / 136 TL6 variants; Shield/DamCon rebaseline remains diagnostic.')
        return 0
    except Exception as e:
        print(f'CP135 contract failure: {e}',file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
