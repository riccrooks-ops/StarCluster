#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def req(value, message):
    if not value:
        raise AssertionError(message)


def text(path: Path) -> str:
    req(path.is_file(), f'Missing {path}')
    return path.read_text(encoding='utf-8-sig')


def js(path: Path):
    return json.loads(text(path))


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def manifest(path: Path) -> dict[str, str]:
    out = {}
    for line in text(path).splitlines():
        if line.strip():
            digest, rel = line.split('  ', 1)
            out[rel] = digest
    return out


def owned_files(repo: Path):
    out = []
    skip_manifest = 'docs/validation/evidence/checkpoint-129/CP129_REPOSITORY_SHA256SUMS.txt'
    for path in repo.rglob('*'):
        if not path.is_file():
            continue
        rel = path.relative_to(repo).as_posix()
        wrapped = '/' + rel
        if rel.startswith(('out/', '.git/')) or '/__pycache__/' in wrapped or rel.endswith('.pyc') or '/bin/' in wrapped or '/obj/' in wrapped or '/TestResults/' in wrapped:
            continue
        if rel == skip_manifest:
            continue
        out.append(rel)
    return sorted(out)


def validate_manifest(repo: Path) -> int:
    p = repo / 'docs/validation/evidence/checkpoint-129/CP129_REPOSITORY_SHA256SUMS.txt'
    m = manifest(p)
    current = owned_files(repo)
    req(set(current) == set(m), f'manifest path drift missing={sorted(set(m)-set(current))[:5]} extra={sorted(set(current)-set(m))[:5]}')
    for rel, digest in m.items():
        req(sha(repo / rel) == digest, f'manifest hash drift: {rel}')
    return len(m)


def validate_repo_only(native: Path):
    s = js(native / 'CP129_REPOSITORY_ONLY_ACCEPTANCE.json')
    req(s['checkpoint'] == 129 and s['repositoryOnly'] is True and s['failedGates'] == [], 'repository-only identity')
    req(s['python'].startswith('Python 3.13') and s['dotnetSdk'] == '8.0.423', 'runtime versions')
    req(s['buildPassed'] and s['buildWarningsAsErrors'], 'native build')
    req(s['pythonTestsPassed'] == 177 and s['xunitPassed'] == 907 and s['xunitFailed'] == 0 and s['xunitSkipped'] == 0, 'test counts')
    req(s['scenarioRunnerSelfTestsPassed'] == 70 and s['researchParityPassed'] == 25, 'self-test/parity')
    req(s['technologyValuesChanged'] is False and s['productionSourceChanged'] is False and s['scenarioDefinitionsChanged'] is False, 'frozen production/value boundary')
    req(s['researchSimulationChanged'] is True and s['mixedTlShipsExecuted'] is False and s['counterfactualHoldbacksAreLegalMixedTlBuilds'] is False, 'research boundary')
    req(s['legalBuilds'] == 9427 and s['wholeLadderBasePairings'] == 70034 and s['generatedVariants'] == 626028, 'plan counts')
    req(s['pipelineSmokeTrials'] == 626028 and s['pipelineSmokeTrialErrors'] == 0, 'pipeline smoke')
    req(s['symmetryComparisons'] == 2250 and s['symmetryCombatExecutions'] == 4500 and s['symmetryMismatches'] == 0, 'symmetry gate')
    req(1 <= int(s.get('repositoryOnlyJobs', 0)) <= 61, 'repository-only Jobs range')
    req(s['substantiveTrials'] == 0, 'repository-only substantive boundary')
    for rel, mode in [('plan/analysis.json','plan'),('symmetry/analysis.json','symmetry_gate'),('smoke/analysis.json','smoke')]:
        a = js(native / rel)
        req(a['checkpoint'] == 129 and a['mode'] == mode and a['failedGates'] == [], f'{rel} gates')
    return s


def validate_final(native: Path):
    prior = validate_repo_only(native)
    s = js(native / 'CP129_NATIVE_ACCEPTANCE_SUMMARY.json')
    req(s['checkpoint'] == 129 and s['repositoryOnly'] is False and s['failedGates'] == [], 'final native identity')
    for key in ('python','dotnetSdk','pythonTestsPassed','xunitPassed','scenarioRunnerSelfTestsPassed','researchParityPassed','generatedVariants','pipelineSmokeTrials','symmetryComparisons','symmetryMismatches'):
        req(s[key] == prior[key], f'final/prior acceptance mismatch {key}')
    req(s['technologyValuesChanged'] is False and s['productionSourceChanged'] is False and s['scenarioDefinitionsChanged'] is False, 'final frozen production/value boundary')
    req(s['mixedTlShipsExecuted'] is False and s['counterfactualHoldbacksAreLegalMixedTlBuilds'] is False, 'final mixed-TL boundary')
    req(1 <= int(s.get('repositoryOnlyJobs', 0)) <= 61 and 1 <= int(s.get('substantiveJobs', 0)) <= 61, 'final Jobs range')
    req(s['substantiveTrials'] == 45665000 and s['substantiveTrialErrors'] == 0, 'substantive workload')
    a = js(native / 'substantive/analysis.json')
    req(a['checkpoint'] == 129 and a['mode'] == 'substantive' and a['failedGates'] == [], 'substantive gates')
    req(a['variants'] == 626028 and a['totalTrials'] == 45665000 and a['trialErrors'] == 0, 'substantive counts')
    req(a['wholeLadderVariants'] == 280136 and a['mainOnlyAdjacentVariants'] == 7136 and a['sensitivityVariants'] == 338756, 'substantive lane counts')
    req(a['mixedTlShipsExecuted'] is False and a['technologyValuesChanged'] is False, 'substantive frozen/mixed boundary')
    rep = native / 'substantive/whole-ladder/cp127_adjacent_replication.csv'
    req(rep.is_file(), 'accepted CP127 adjacent replication output missing')
    return s


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', required=True)
    ap.add_argument('--native-results')
    args = ap.parse_args()
    repo = Path(args.repo).resolve()
    try:
        print('       Validating CP129 definition and accepted CP128 evidence...')
        d = js(repo / 'tools/checkpoints/checkpoint-129/checkpoint_129_definition.json')
        req(d['checkpoint'] == 129 and d['expectedPythonTests'] == 177 and d['monteCarloStudy'] is True, 'definition')
        req(d['expectedGeneratedVariants'] == 626028 and d['expectedSubstantiveTrials'] == 45665000, 'definition workload')
        req(d.get('jobsConfigurable') is True and d.get('defaultJobs') == 24 and d.get('minimumJobs') == 1 and d.get('maximumJobs') == 61, 'definition Jobs contract')
        cp128 = js(repo / 'docs/validation/evidence/checkpoint-129/CP128_NATIVE_ACCEPTANCE_SUMMARY.json')
        req(cp128['checkpoint'] == 128 and cp128['failedGates'] == [] and cp128['pythonTestsPassed'] == 171, 'accepted CP128 evidence')
        if args.native_results:
            native = Path(args.native_results).resolve()
            if (native / 'CP129_NATIVE_ACCEPTANCE_SUMMARY.json').is_file():
                validate_final(native)
            else:
                validate_repo_only(native)
        print('       Parsing repository JSON corpus...')
        njson = 0
        for path in repo.rglob('*.json'):
            rel = path.relative_to(repo).as_posix()
            if rel.startswith('out/') or '/bin/' in '/' + rel or '/obj/' in '/' + rel:
                continue
            json.loads(path.read_text(encoding='utf-8-sig'))
            njson += 1
        print('       Validating full CP129 repository manifest...')
        count = validate_manifest(repo)
        print(f'       CP129 contract verified: {count} repository-owned files; {njson} JSON files; CP128 numerical authority frozen; pure-TL sensitivity study bounded; mixed-TL ships excluded.')
        return 0
    except Exception as exc:
        print(f'CP129 contract failure: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
