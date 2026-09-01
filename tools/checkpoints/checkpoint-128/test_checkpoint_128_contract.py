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
    for path in repo.rglob('*'):
        if not path.is_file():
            continue
        rel = path.relative_to(repo).as_posix()
        wrapped = '/' + rel
        if rel.startswith(('out/', '.git/')) or '/__pycache__/' in wrapped or rel.endswith('.pyc') or '/bin/' in wrapped or '/obj/' in wrapped or '/TestResults/' in wrapped:
            continue
        if rel == 'docs/validation/evidence/checkpoint-128/CP128_REPOSITORY_SHA256SUMS.txt':
            continue
        out.append(rel)
    return sorted(out)


def validate_manifest(repo: Path) -> int:
    p = repo / 'docs/validation/evidence/checkpoint-128/CP128_REPOSITORY_SHA256SUMS.txt'
    m = manifest(p)
    current = owned_files(repo)
    req(set(current) == set(m), f'manifest path drift missing={sorted(set(m)-set(current))[:5]} extra={sorted(set(current)-set(m))[:5]}')
    for rel, digest in m.items():
        req(sha(repo / rel) == digest, f'manifest hash drift: {rel}')
    return len(m)


def validate_native(native: Path):
    s = js(native / 'CP128_NATIVE_ACCEPTANCE_SUMMARY.json')
    req(s['checkpoint'] == 128 and s['acceptedEvidenceCheckpoint'] == 127 and s['repositoryOnly'] is True, 'native identity')
    req(s['python'].startswith('Python 3.13') and s['dotnetSdk'] == '8.0.423', 'runtime versions')
    req(s['buildPassed'] is True and s['buildWarningsAsErrors'] is True, 'native build')
    req(s['pythonTestsPassed'] == 171 and s['xunitPassed'] == 907 and s['xunitFailed'] == 0 and s['xunitSkipped'] == 0, 'test counts')
    req(s['scenarioRunnerSelfTestsPassed'] == 70 and s['researchParityPassed'] == 25, 'self-test/parity')
    req(s['technologyValuesChanged'] is False and s['numericLeafChangesFromAcceptedCp127'] == 0, 'zero numerical drift')
    req(s['productionSourceChanged'] is False and s['scenarioDefinitionsChanged'] is False and s['researchSimulationChanged'] is False, 'frozen executable surfaces')
    req(s['monteCarloStudy'] is False and s['substantiveTrials'] == 0 and s['generatedVariants'] == 0, 'no Monte Carlo')
    req(s['mainSubsystemPureTlStabilized'] is True and s['mixedTlShipsExecuted'] is False and s['auxiliaryNumericalStabilizationDeferred'] is True, 'baseline boundary')
    req(s['largePredecessorNativeArchivesExternalized'] == 2 and s['failedGates'] == [], 'packaging/evidence status')


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', required=True)
    ap.add_argument('--native-results')
    args = ap.parse_args()
    repo = Path(args.repo).resolve()
    try:
        print('       Validating CP128 definition and curated accepted CP127 evidence...')
        d = js(repo / 'tools/checkpoints/checkpoint-128/checkpoint_128_definition.json')
        req(d['checkpoint'] == 128 and d['expectedPythonTests'] == 171 and d['monteCarloStudy'] is False, 'definition')
        cp127 = js(repo / 'docs/validation/evidence/checkpoint-128/curated-predecessor-native-evidence/cp127/CP127_NATIVE_ACCEPTANCE_SUMMARY.json')
        req(cp127['checkpoint'] == 127 and cp127['substantiveTrials'] == 8658400 and cp127['failedGates'] == [], 'accepted CP127 evidence')
        if args.native_results:
            validate_native(Path(args.native_results).resolve())
        print('       Parsing repository JSON corpus...')
        njson = 0
        for path in repo.rglob('*.json'):
            rel = path.relative_to(repo).as_posix()
            if rel.startswith('out/') or '/bin/' in '/' + rel or '/obj/' in '/' + rel:
                continue
            json.loads(path.read_text(encoding='utf-8-sig'))
            njson += 1
        print('       Validating full CP128 repository manifest...')
        count = validate_manifest(repo)
        print(f'       CP128 contract verified: {count} repository-owned files; {njson} JSON files; accepted CP127 numerical baseline unchanged; no Monte Carlo; curated evidence packaging active.')
        return 0
    except Exception as exc:
        print(f'CP128 contract failure: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
