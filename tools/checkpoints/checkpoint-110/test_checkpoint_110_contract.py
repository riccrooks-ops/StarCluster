#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

EXCLUDED_PARTS = {'.git', '.vs', '.vscode', '.idea', 'out', 'bin', 'obj', 'TestResults', '__pycache__'}
EXCLUDED_FILES = {'.DS_Store', 'Thumbs.db'}
EXCLUDED_SUFFIXES = {'.pyc', '.user', '.userosscache', '.sln.docstates', '.uid', '.suo'}
EXPECTED_CP109_MANIFEST_SHA = '7dd092d8e4b46263168f41b668d4556d4392f0bbac601c74bd96218cac9aa21c'
EXPECTED_MATRIX_SHA = '91cb29f7e1e0f792e5a2258b1ab0655fe9924c768f4d80b645269fae52384000'
EXPECTED_ARTIFACT_SHA = {
    'docs/archive/player_technology/pre-cp165-active/power_reactor_calibration_profile_v0_1.json': 'ebed51fa16d0ee1c9721b55ca135eb81e23c321a8373dfcb826a1a096371e9a6',
    'docs/design/player_technology/Power_Reactor_Calibration_Report_v1.md': 'c7fbc7a42a8bf8a4961fcd06469aa8af3233e63015f2f3fa31752b7e75a0ce97',
    'docs/design/player_technology/StarCluster_CP110_Power_Reactor_Calibration_v0_1.xlsx': 'd0d4ec63c17275722d001d2137c620ad172d916402514951e10619877dce0fec',
    'docs/Star_Cluster_Game_Concept_v0.7j.docx': '50f522b6cf5c11d89b5e8e93b33f47da36baa0c1d267acfe8be07872f93a461d',
    'docs/archive/testing/pre-cp165-active/power_reactor_calibration_study_v0_1.json': 'f49c40e0cdb46c27db0c05f5bcc24a9bd2f6dee94c78f760dc7e9c177ce764bf',
    'docs/validation/evidence/checkpoint-110/power-reactor-calibration/analysis.json': '3b5e9d969a3724a864282b37bfbf56c8bc8f151f3b86b160380390ee97734282',
}
EXPECTED_BUILD_COUNTS = {'1': 294, '2': 294, '3': 609, '4': 843, '5': 1140, '6': 2730, '7': 4032, '8': 4032, '9': 4032}
EXPECTED_REACTORS = {
    1: ('Peak Fission', 6, 5, 3, 1),
    2: ('Early Practical Fusion', 6, 7, 3, 0),
    3: ('Mature Compact Fusion', 5, 7, 4, 1),
    4: ('High-Output Fusion', 5, 9, 5, 1),
    5: ('Early Antimatter Reactor', 5, 12, 4, 0),
    6: ('Mature Antimatter', 4, 12, 7, 1),
    7: ('High-Output Antimatter', 4, 15, 8, 1),
    8: ('Fractional / Direct Matter-Conversion Reactor', 4, 17, 6, 0),
    9: ('Total Matter Conversion', 3, 20, 12, 2),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read_text(path: Path) -> str:
    require(path.is_file(), f'Missing text file: {path}')
    return path.read_text(encoding='utf-8-sig')


def read_json(path: Path):
    require(path.is_file(), f'Missing JSON file: {path}')
    return json.loads(path.read_text(encoding='utf-8-sig'))


def is_repo_owned(rel: str) -> bool:
    p = Path(rel)
    if any(part in EXCLUDED_PARTS for part in p.parts) or p.name in EXCLUDED_FILES:
        return False
    return not any(p.name.lower().endswith(suffix) for suffix in EXCLUDED_SUFFIXES)


def validate_hash_list(repo: Path, rel: str, expected_rows: int, label: str) -> int:
    count = 0
    seen = set()
    for line in read_text(repo / rel).splitlines():
        if not line.strip():
            continue
        m = re.fullmatch(r'([0-9a-f]{64})  (.+)', line)
        require(m is not None, f'Malformed {label} hash row: {line}')
        expected, path_rel = m.groups()
        require(path_rel not in seen, f'Duplicate {label} frozen path: {path_rel}')
        seen.add(path_rel)
        p = repo / path_rel
        require(p.is_file(), f'{label} frozen file missing: {path_rel}')
        require(sha256(p) == expected, f'{label} frozen file drifted: {path_rel}')
        count += 1
    require(count == expected_rows, f'Expected {expected_rows} {label} frozen files, found {count}')
    return count


def validate_production_boundary(repo: Path) -> None:
    # Python is allowed in simulation/test/checkpoint infrastructure, but not in the shipped C#/Godot game runtime.
    for rel in ('src/StarCluster.Game', 'src/StarCluster.Core'):
        root = repo / rel
        require(root.is_dir(), f'Missing production tree: {rel}')
        py = list(root.rglob('*.py'))
        require(not py, f'Python source leaked into production runtime: {py[0].relative_to(repo) if py else ""}')
        for p in root.rglob('*'):
            if not p.is_file() or p.suffix.lower() not in {'.cs', '.csproj', '.props', '.targets'}:
                continue
            text = p.read_text(encoding='utf-8-sig', errors='ignore').lower()
            for marker in ('python.runtime', 'pythonnet', 'ironpython', 'python.exe', 'python3.exe'):
                require(marker not in text, f'Production runtime references Python marker {marker}: {p.relative_to(repo)}')


def office_text(path: Path) -> str:
    require(path.is_file(), f'Missing Office artifact: {path}')
    pieces = []
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            if not name.startswith('word/') or not name.endswith('.xml'):
                continue
            try:
                root = ET.fromstring(z.read(name))
            except ET.ParseError:
                continue
            for elem in root.iter():
                if elem.tag.endswith('}t') and elem.text:
                    pieces.append(elem.text)
    return '\n'.join(pieces)


def csv_data_rows(path: Path) -> int:
    require(path.is_file(), f'Missing CSV evidence: {path}')
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        return sum(1 for _ in csv.DictReader(f))


def validate_analysis(repo: Path, analysis_path: Path, label: str) -> dict:
    data = read_json(analysis_path)
    # Accept either analysis.json itself or the summary wrapper written by the command.
    if 'analysis' in data:
        require(data.get('passed') is True and int(data.get('failedGates', -1)) == 0, f'{label} summary did not pass.')
        data = data['analysis']
    require(data['schemaVersion'] == 'star-cluster-power-reactor-calibration-results-v1', f'{label} schema drifted.')
    require(data['checkpoint'] == '110', f'{label} checkpoint id drifted.')
    require(data['legalBuildCounts'] == EXPECTED_BUILD_COUNTS, f'{label} legal build counts drifted: {data["legalBuildCounts"]}')
    expected = {
        'reactorCandidates': 11,
        'frontierRows': 53,
        'envelopeRows': 108,
        'sensitivityRows': 180,
        'representativeLoadouts': 72,
        'stochasticVariants': 288,
        'turnSamples': 7025000,
        'overloadEncounterVariants': 288,
        'overloadEncounterTurns': 14400000,
        'branchHotspotRows': 9,
        'legacyStackRows': 88,
        'currentStackRows': 9,
        'trialErrors': 0,
    }
    for key, value in expected.items():
        require(int(data[key]) == value, f'{label} {key} drifted: expected {value}, found {data[key]}')
    require(data['automaticPromotion'] is False, f'{label} may not auto-promote candidate values.')
    require(data['blockingBalanceTargets'] is False, f'{label} may not create blocking target balance bands.')
    require(data['failedGates'] == [], f'{label} has failed gates: {data["failedGates"]}')
    signals = data['interpretationSignals']
    require(len(signals) == 9, f'{label} must contain nine TL interpretation signals.')
    for tl, signal in enumerate(signals, 1):
        require(int(signal['tl']) == tl, f'{label} interpretation signal order/TL drifted.')
        require(signal['reactor'] == f'reactor-tl{tl}', f'{label} primary reactor id drifted at TL{tl}.')
        require(signal['pareto_frontier'] is True, f'Primary Reactor candidate TL{tl} is no longer Pareto-relevant at introduction.')
        require(float(signal['branch_hotspot_power_gap']) > 0.0, f'TL{tl} no longer exposes branch-heavy power pressure.')
    return data


def validate_manifest(repo: Path) -> int:
    manifest = repo / 'CHECKPOINT_110_SHA256SUMS.txt'
    require(manifest.is_file(), 'CHECKPOINT_110_SHA256SUMS.txt missing.')
    listed = {}
    for line in read_text(manifest).splitlines():
        if not line.strip():
            continue
        m = re.fullmatch(r'([0-9a-f]{64})  (.+)', line)
        require(m is not None, f'Malformed CP110 manifest row: {line}')
        h, rel = m.groups()
        require(rel not in listed, f'Duplicate CP110 manifest path: {rel}')
        listed[rel] = h
    actual = {}
    for p in repo.rglob('*'):
        if not p.is_file():
            continue
        rel = p.relative_to(repo).as_posix()
        if rel == 'CHECKPOINT_110_SHA256SUMS.txt' or not is_repo_owned(rel):
            continue
        actual[rel] = sha256(p)
    require(set(actual) == set(listed), f'CP110 manifest path-set mismatch: actual {len(actual)}, manifest {len(listed)}')
    for rel, h in actual.items():
        require(listed[rel] == h, f'CP110 manifest hash mismatch: {rel}')
    return len(actual)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', required=True)
    ap.add_argument('--skip-manifest', action='store_true')
    ap.add_argument('--runtime-output')
    args = ap.parse_args()
    repo = Path(args.repo).resolve()

    print('       Validating accepted CP109 provenance and frozen production/test/simulation surfaces...')
    require(sha256(repo / 'CHECKPOINT_109_SHA256SUMS.txt') == EXPECTED_CP109_MANIFEST_SHA, 'Accepted CP109 manifest hash drifted.')
    require(sha256(repo / 'docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_1.json') == EXPECTED_MATRIX_SHA, 'Accepted CP109 whole-ladder numerical matrix drifted.')
    frozen_prod = validate_hash_list(repo, 'docs/validation/evidence/checkpoint-110/CP109_FROZEN_PRODUCTION_TEST_SHA256SUMS.txt', 561, 'production/test')
    frozen_sim = validate_hash_list(repo, 'docs/validation/evidence/checkpoint-110/CP109_FROZEN_SIMULATION_BASE_SHA256SUMS.txt', 13, 'simulation-base')

    print('       Validating CP110 Power/Reactor study architecture and calibrated-candidate evidence...')
    definition = read_json(repo / 'tools/checkpoints/checkpoint-110/checkpoint_110_architecture_definition.json')
    require(definition['checkpointId'] == '110' and definition['acceptedBaseline'] == '109', 'CP110 checkpoint identity/baseline drifted.')
    require(definition['checkpointType'] == 'substantive_power_reactor_first_pass_calibration', 'CP110 checkpoint type drifted.')
    require(definition['productionRuntime'] == 'C# / Godot' and definition['pythonAllowedForTestingSimulationAndCheckpointValidation'] is True and definition['pythonRequiredByProductionRuntime'] is False, 'CP110 production/testing language boundary drifted.')
    require(definition['productionSourceChanged'] is False and definition['automaticPromotion'] is False and definition['productionPromotion'] is False, 'CP110 may not change/promote production runtime values.')
    require(definition['energyStorageCalibrated'] is False and definition['auxiliaryGenerationCalibrated'] is False, 'CP110 scope must exclude Energy Storage and auxiliary generation.')
    declared = definition['declaredLocalEvidence']
    require(declared == {
        'exhaustiveLegalStandardBuilds': 18006,
        'representativeLoadouts': 72,
        'stochasticVariants': 288,
        'adaptiveTurnDemandSamples': 7025000,
        'equivalentSafeOverloadEncounterTurns': 14400000,
        'reactorCandidates': 11,
        'currentStackRows': 9,
        'legacyStackRows': 88,
        'branchHotspotRows': 9,
    }, f'CP110 declared evidence counts drifted: {declared}')
    guard = definition['interpretationGuardrails']
    require(guard['targetWinRate'] is False and guard['requireOneReactorToMeetFullSimultaneousDemand'] is False and guard['humanReviewRequiredForPromotion'] is True and guard['highTlMultiReactorAvailabilityIsIntegrationWatch'] is True, 'CP110 interpretation guardrails drifted.')

    runtime = read_json(repo / 'tools/checkpoints/checkpoint-110/PYTHON_RUNTIME.json')
    require(runtime == {
        'schemaVersion': 1,
        'implementation': 'CPython',
        'majorMinor': '3.13',
        'stdlibOnly': True,
        'purpose': 'Deterministic Star Cluster checkpoint validation and testing infrastructure',
        'productionBoundary': 'The shipped C# / Godot game runtime must not require Python.'
    }, 'CP110 Python runtime contract drifted.')
    validate_production_boundary(repo)

    study = read_json(repo / 'docs/archive/testing/pre-cp165-active/power_reactor_calibration_study_v0_1.json')
    require(study['schemaVersion'] == 'star-cluster-power-reactor-calibration-v1' and study['checkpoint'] == '110', 'CP110 study schema/identity drifted.')
    require(study['matrixPath'] == 'docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_1.json', 'CP110 study matrix source drifted.')
    require(study['masterSeed'] == 11020260815, 'CP110 deterministic study seed drifted.')
    require((study['reactorCountMaximum'], study['mainWeaponCountMaximum'], study['maxPdsBatteries']) == (2, 2, 5), 'CP110 enumeration bounds drifted.')
    require((study['minimumTurnSamples'], study['maximumTurnSamples'], study['turnSampleBatch']) == (20000, 60000, 5000), 'CP110 adaptive sampling bounds drifted.')
    require(abs(float(study['targetWilsonHalfWidth']) - 0.004) < 1e-12, 'CP110 Wilson half-width target drifted.')
    require((study['encountersPerVariant'], study['turnsPerEncounter']) == (2500, 20), 'CP110 overload encounter scale drifted.')
    require(study['doctrines'] == ['offense', 'ew_contested', 'defense', 'mixed'], 'CP110 doctrine set/order drifted.')
    policy = study['interpretationPolicy']
    require(policy['noTargetWinRate'] is True and policy['noRequiredFullSimultaneousDemandCoverage'] is True and policy['candidateValuesMayChangeAfterHumanReview'] is True and policy['automaticPromotion'] is False, 'CP110 study interpretation policy drifted.')
    require(policy['productionRuntime'] == 'C# / Godot' and policy['simulationRuntime'] == 'CPython 3.13 stdlib-only', 'CP110 study runtime boundary drifted.')

    matrix = read_json(repo / 'docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_1.json')
    reactor_rows = matrix['profiles']['reactor']
    profile = read_json(repo / 'docs/archive/player_technology/pre-cp165-active/power_reactor_calibration_profile_v0_1.json')
    require(profile['schemaVersion'] == 'star-cluster-power-reactor-calibrated-candidate-profile-v0.1' and profile['checkpoint'] == '110', 'CP110 calibrated-candidate profile identity drifted.')
    require(profile['status'] == 'first_pass_calibration_evidence_retains_cp109_values_no_production_promotion', 'CP110 calibrated-candidate lifecycle status drifted.')
    decision = profile['decision']
    require(decision['primaryReactorNumericalChanges'] == 0 and decision['retainAllCp109PrimaryReactorCandidates'] is True and decision['promoteToProductionRuntime'] is False, 'CP110 primary Reactor decision drifted.')
    scale = profile['studyScale']
    require(scale == {
        'exhaustiveLegalBuildsAcrossTls': 18006,
        'representativeLoadouts': 72,
        'stochasticVariants': 288,
        'adaptiveTurnDemandSamples': 7025000,
        'equivalentSafeOverloadEncounterTurns': 14400000,
        'doctrines': 4,
        'wilsonHalfWidthTarget': 0.004,
    }, f'CP110 profile study-scale summary drifted: {scale}')
    primary = profile['primaryReactors']
    require(len(primary) == 9, 'CP110 calibrated-candidate profile must cover TL1-TL9 primary Reactors.')
    for row in primary:
        tl = int(row['tl'])
        technology, space, op, degraded, emergency = EXPECTED_REACTORS[tl]
        source = reactor_rows[str(tl)]
        require((source['technology'], source['space'], source['operationalTp'], source['degradedTp'], source['emergencyTp']) == (technology, space, op, degraded, emergency), f'CP109 source Reactor candidate drifted at TL{tl}.')
        require((row['technology'], row['space'], row['operationalTp'], row['degradedTp'], row['emergencyTp']) == (technology, space, op, degraded, emergency), f'CP110 calibrated-candidate profile changed Reactor numbers at TL{tl}.')
        require(row['candidateStatus'] == 'retained_after_cp110_first_pass_calibration' and row['paretoFrontierAtIntroduction'] is True, f'CP110 calibrated status/frontier flag drifted at TL{tl}.')

    for rel, expected in EXPECTED_ARTIFACT_SHA.items():
        require(sha256(repo / rel) == expected, f'CP110 reviewed artifact drifted: {rel}')

    print('       Validating checked-in self-tests, parity fixtures, stochastic evidence, and interpretation guardrails...')
    selftest = read_json(repo / 'docs/validation/evidence/checkpoint-110/CP110_PYTHON_SELF_TEST_SUMMARY.json')
    require(selftest['passed'] is True and selftest['tests'] == {'run': 18, 'failures': 0, 'errors': 0, 'skipped': 0} and selftest['failedGates'] == 0, f'CP110 self-test evidence drifted: {selftest}')
    parity = read_json(repo / 'docs/validation/evidence/checkpoint-110/CP110_PARITY_SUMMARY.json')
    require(parity['passed'] is True and parity['cases'] == 25 and parity['errors'] == [] and parity['failedGates'] == 0, f'CP110 parity evidence drifted: {parity}')
    local_env = read_json(repo / 'docs/validation/evidence/checkpoint-110/CP110_LOCAL_ENVIRONMENT_SUMMARY.json')
    require(local_env['passed'] is True and local_env['environment']['implementation'] == 'CPython' and local_env['environment']['stdlib_only'] is True, 'CP110 local environment evidence drifted.')

    evidence_dir = repo / 'docs/validation/evidence/checkpoint-110/power-reactor-calibration'
    analysis = validate_analysis(repo, evidence_dir / 'analysis.json', 'checked-in CP110 analysis')
    summary = validate_analysis(repo, evidence_dir / 'summary.json', 'checked-in CP110 summary')
    for key in ('turnSamples', 'stochasticVariants', 'representativeLoadouts', 'currentStackRows', 'legacyStackRows', 'branchHotspotRows'):
        require(analysis[key] == summary[key], f'Checked-in CP110 analysis/summary mismatch for {key}.')
    expected_csv_rows = {
        'reactor_frontier.csv': 53,
        'power_envelope.csv': 108,
        'operational_sensitivity.csv': 180,
        'representative_loadouts.csv': 72,
        'stochastic_variants.csv': 288,
        'overload_encounters.csv': 288,
        'current_reactor_stacking.csv': 9,
        'legacy_reactor_stacking.csv': 88,
        'branch_power_hotspots.csv': 9,
        'interpretation_signals.csv': 9,
        'stochastic_tl_summary.csv': 9,
    }
    for name, expected_rows in expected_csv_rows.items():
        require(csv_data_rows(evidence_dir / name) == expected_rows, f'CP110 evidence row count drifted for {name}.')

    # Explicitly preserve the integration-watch signal rather than treating it as a balance failure.
    stack_rows = list(csv.DictReader((evidence_dir / 'current_reactor_stacking.csv').open('r', encoding='utf-8-sig', newline='')))
    stack_fraction = {int(r['tl']): float(r['same_package_two_reactor_legal_fraction']) for r in stack_rows}
    require(stack_fraction[6] > 0.45 and stack_fraction[7] > 0.70 and stack_fraction[8] > 0.95 and stack_fraction[9] == 1.0, 'High-TL current-Reactor stacking integration-watch evidence drifted.')

    overload_rows = list(csv.DictReader((evidence_dir / 'overload_encounters.csv').open('r', encoding='utf-8-sig', newline='')))
    by_tl = {}
    for r in overload_rows:
        tl = int(r['tl'])
        by_tl.setdefault(tl, []).append(r)
    for tl, rows in by_tl.items():
        raw = sum(float(r['raw_shortfall_rate']) for r in rows) / len(rows)
        assisted = sum(float(r['safe_overload_assisted_shortfall_rate']) for r in rows) / len(rows)
        require(assisted <= raw + 1e-12, f'Safe overload worsened mean shortfall at TL{tl}.')
        require(assisted > 0.0 or raw == 0.0, f'Safe overload unexpectedly erased all sustained shortfall at TL{tl}.')

    sim_module = read_text(repo / 'tools/simulation/starcluster_research/power_calibration.py')
    cli = read_text(repo / 'tools/simulation/starcluster_research/cli.py')
    test_text = read_text(repo / 'tools/simulation/tests/test_cp110_power.py')
    require('power-calibrate' in cli and 'def ' in sim_module and 'closed' in sim_module.lower(), 'CP110 simulation/CLI integration markers missing.')
    require('test_' in test_text and 'Power' in test_text, 'CP110 Power calibration unit tests missing.')
    # New CP110 Python research code must remain stdlib-only. Local-package imports are permitted.
    forbidden_imports = ('numpy', 'pandas', 'scipy', 'sklearn', 'polars', 'numba')
    lower_sim = sim_module.lower() + '\n' + test_text.lower()
    for pkg in forbidden_imports:
        require(re.search(rf'(^|\n)\s*(from|import)\s+{re.escape(pkg)}\b', lower_sim) is None, f'CP110 simulation introduced non-stdlib dependency: {pkg}')

    print('       Validating Concept/document consistency and calibration lifecycle...')
    concept = office_text(repo / 'docs/Star_Cluster_Game_Concept_v0.7j.docx')
    for phrase in (
        'Version 0.7j',
        'Checkpoint 110 performs',
        '7,025,000',
        'first-pass calibrated working candidates',
        'Energy Storage and auxiliary generation',
        'C-080',
    ):
        require(phrase in concept, f'Concept v0.7j missing required CP110 text: {phrase}')
    validation_files = sorted(p.name for p in (repo / 'docs/validation').glob('Checkpoint_*.md'))
    require(validation_files == ['Checkpoint_110_Power_Reactor_First_Pass_Calibration.md'], f'Only CP110 active checkpoint runbook expected; found {validation_files}')
    for rel in ('README.md', 'CHAT_README.md', 'docs/README.md', 'docs/design/player_technology/README.md', 'docs/design/testing/README.md', 'docs/validation/README.md', 'docs/Prototype_TODO.md', 'tools/simulation/README.md'):
        text = read_text(repo / rel)
        require('110' in text and '109' in text, f'Active documentation must recognize CP109 accepted baseline and CP110 candidate: {rel}')

    if args.runtime_output:
        print('       Validating freshly reproduced native/runtime study output...')
        out = Path(args.runtime_output)
        if not out.is_absolute():
            out = repo / out
        require(out.is_dir(), f'Runtime output directory missing: {out}')
        runtime_analysis = validate_analysis(repo, out / 'analysis.json', 'fresh CP110 runtime output')
        require(runtime_analysis['turnSamples'] == analysis['turnSamples'], 'Fresh runtime adaptive sample count differs from checked-in deterministic evidence.')
        require(runtime_analysis['legalBuildCounts'] == analysis['legalBuildCounts'], 'Fresh runtime legal-build counts differ from checked-in evidence.')

    count = -1
    if not args.skip_manifest:
        print('       Validating full repository manifest...')
        count = validate_manifest(repo)
    else:
        print('       Skipping full repository manifest during local construction.')

    manifest_text = f'{count} repository-owned files' if count >= 0 else 'manifest skipped'
    print(f'       CP110 contract verified: {manifest_text}; {frozen_prod} frozen production/test files + {frozen_sim} frozen simulation-base files; 18 self-tests / 25 parity cases; 18,006 legal builds / 72 representatives / 288 stochastic variants / 7,025,000 adaptive demand samples; 14,400,000 equivalent bounded-overload encounter turns; nine primary Reactor candidates retained unchanged; zero production promotion.')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f'CP110 CONTRACT FAILURE: {exc}', file=sys.stderr)
        raise SystemExit(1)
