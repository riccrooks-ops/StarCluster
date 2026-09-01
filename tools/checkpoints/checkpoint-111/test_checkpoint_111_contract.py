#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

EXCLUDED_PARTS = {'.git', '.vs', '.vscode', '.idea', 'out', 'bin', 'obj', 'TestResults', '__pycache__'}
EXCLUDED_FILES = {'.DS_Store', 'Thumbs.db'}
EXCLUDED_SUFFIXES = {'.pyc', '.user', '.userosscache', '.sln.docstates', '.uid', '.suo'}
EXPECTED_CP110_MANIFEST_SHA = '7a9fbed4997a64aef559566d749bf5e2d94470925083009abc3dea1c08557b3d'
EXPECTED_MATRIX_SHA = '91cb29f7e1e0f792e5a2258b1ab0655fe9924c768f4d80b645269fae52384000'
EXPECTED_REACTOR_PROFILE_SHA = 'ebed51fa16d0ee1c9721b55ca135eb81e23c321a8373dfcb826a1a096371e9a6'
EXPECTED_LOCAL_ROWS = {
    'builds.csv': 108,
    'variants.csv': 1188,
    'movement_neutral_bundles.csv': 594,
    'build_summary.csv': 108,
    'build_mechanics.csv': 108,
    'family_matchups.csv': 27,
    'tl_summary.csv': 9,
    'instrumentation_coverage.csv': 65,
    'instrumentation_probes.csv': 4,
    'overload_instrumentation_probes.csv': 5,
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


def csv_rows(path: Path) -> list[dict[str, str]]:
    require(path.is_file(), f'Missing CSV: {path}')
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def validate_ecology_output(root: Path, trials: int, label: str) -> dict:
    analysis = read_json(root / 'analysis.json')
    summary = read_json(root / 'summary.json')
    require(summary.get('passed') is True and summary.get('failedGates') == 0, f'{label} summary failed: {summary}')
    require(summary.get('analysis', {}).get('checkpoint') == '111', f'{label} summary does not contain CP111 analysis.')
    require(analysis['schemaVersion'] == 'star-cluster-same-tl-build-ecology-results-v0.1', f'{label} result schema drifted.')
    require(analysis['checkpoint'] == '111', f'{label} checkpoint identity drifted.')
    require(analysis['damageModel'] == 'layered_defense_hull_only', f'{label} damage model drifted.')
    require(analysis['internalDamageCriticalsSimulated'] is False, f'{label} unexpectedly simulated internal criticals.')
    require(analysis['primaryPopulation'] == 'same_tl_frontier_exact_fill', f'{label} primary population drifted.')
    require(analysis['mixedTlPopulationExecuted'] is False, f'{label} mixed-TL population must remain separate.')
    require((analysis['builds'], analysis['movementNeutralBundles'], analysis['variants']) == (108, 594, 1188), f'{label} population counts drifted.')
    require(analysis['trialsPerVariant'] == trials and analysis['totalTrials'] == 1188 * trials, f'{label} trial scale drifted.')
    require(analysis['failedGates'] == [] and analysis['automaticPromotion'] is False, f'{label} gates/promotion drifted.')
    require(len(analysis['tlSummary']) == 9 and [r['tl'] for r in analysis['tlSummary']] == list(range(1, 10)), f'{label} TL summary coverage drifted.')

    for name, expected in EXPECTED_LOCAL_ROWS.items():
        rows = csv_rows(root / name)
        require(len(rows) == expected, f'{label} row count drifted for {name}: {len(rows)} != {expected}')

    builds = csv_rows(root / 'builds.csv')
    by_tl = defaultdict(list)
    for r in builds:
        tl = int(r['tl'])
        by_tl[tl].append(r)
        require(int(r['free_space']) == 0, f'{label} build does not exactly fill Space: {r["build_id"]}')
        require(int(r['used_space']) == int(r['capacity']), f'{label} build used/capacity mismatch: {r["build_id"]}')
        require(int(r['mission_aux_space']) >= 0, f'{label} negative mission AUX accounting: {r["build_id"]}')
    require(sorted(by_tl) == list(range(1, 10)), f'{label} build TL coverage drifted.')
    for tl, rows in by_tl.items():
        require(len(rows) == 12, f'{label} TL{tl} build count drifted.')
        require(Counter(r['weapon_family'] for r in rows) == Counter({'Energy': 4, 'Kinetic': 4, 'Missile': 4}), f'{label} TL{tl} family coverage drifted.')

    variants = csv_rows(root / 'variants.csv')
    required_cols = {
        'mean_a_direct_shots','mean_a_direct_hits','mean_a_missile_launches','mean_a_missile_hits',
        'mean_a_pds_attempts','mean_a_pds_intercepts','mean_a_ecm_downgrade_events','mean_a_eccm_restore_events',
        'mean_a_burnthrough_preservation_events','mean_a_track_driven_closure_hexes',
        'mean_a_power_weapons','mean_a_power_ecm','mean_a_power_eccm','mean_a_power_pds',
        'mean_a_reactor_overload_activations','mean_a_power_shield_hardener',
        'mean_a_movement_hexes','mean_a_movement_fuel','mean_a_map_boundary_blocks',
        'mean_a_shield_absorbed','mean_a_armor_prevented','mean_a_armor_integrity_damage','mean_a_hull_damage'
    }
    require(required_cols.issubset(set(variants[0])), f'{label} required instrumentation columns missing from variants.csv.')
    forbidden = [c for c in variants[0] if any(k in c.lower() for k in ('critical', 'subsystem_hit', 'internal_track', 'magazine_critical'))]
    require(not forbidden, f'{label} exposes internal-damage telemetry despite Hull-only scope: {forbidden}')
    for r in variants:
        require(int(r['trials']) == trials and int(r['errors']) == 0, f'{label} variant trial/error mismatch: {r["variant_id"]}')
        require(r['damage_model'] == 'layered_defense_hull_only', f'{label} variant damage model drifted: {r["variant_id"]}')

    bundles = csv_rows(root / 'movement_neutral_bundles.csv')
    require(all(int(r['variants']) == 2 for r in bundles), f'{label} movement-order mirror bundle incomplete.')

    coverage = {r['metric']: r for r in csv_rows(root / 'instrumentation_coverage.csv')}
    must_be_nonzero = [
        'direct_shots','direct_hits','missile_launches','missile_hits','pds_attempts','pds_intercepts',
        'ecm_active_turns','eccm_active_turns','ecm_downgrade_events','eccm_restore_events',
        'burnthrough_preservation_events','track_driven_closure_hexes','reactor_overload_activations',
        'power_sensor','power_ecm','power_eccm','power_pds','power_weapons','power_shield_recharge','power_shield_hardener',
        'movement_hexes','movement_fuel','map_boundary_blocks','shield_absorbed','armor_prevented','armor_integrity_damage','hull_damage'
    ]
    for metric in must_be_nonzero:
        require(metric in coverage and coverage[metric]['nonzero'] == 'True', f'{label} required telemetry path not exercised: {metric}')
    intentionally_zero = ['sensor_overload_activations','ecm_overload_activations','eccm_overload_activations','stl_overload_activations']
    for metric in intentionally_zero:
        require(coverage.get(metric, {}).get('nonzero') == 'False', f'{label} risky overload unexpectedly entered primary doctrine: {metric}')

    probes = csv_rows(root / 'instrumentation_probes.csv')
    require(len(probes) == 4 and sum(int(r['pds_attempts']) for r in probes) > 0 and sum(int(r['eccm_restores']) for r in probes) > 0, f'{label} combat probes failed to exercise PDS/ECCM.')
    overload = csv_rows(root / 'overload_instrumentation_probes.csv')
    require({r['subsystem'] for r in overload} == {'STL','Sensor','ECM','ECCM','Reactor'}, f'{label} overload probe coverage drifted.')
    require(all(r['passed'] == 'True' for r in overload), f'{label} overload instrumentation probe failed.')
    return analysis


def validate_manifest(repo: Path, expected_count: int) -> int:
    manifest = repo / 'CHECKPOINT_111_SHA256SUMS.txt'
    require(manifest.is_file(), 'Missing CP111 repository manifest.')
    expected = {}
    for line in read_text(manifest).splitlines():
        if not line.strip():
            continue
        m = re.fullmatch(r'([0-9a-f]{64})  (.+)', line)
        require(m is not None, f'Malformed CP111 manifest row: {line}')
        h, rel = m.groups()
        require(rel != 'CHECKPOINT_111_SHA256SUMS.txt', 'CP111 manifest must not hash itself.')
        require(rel not in expected, f'Duplicate CP111 manifest path: {rel}')
        expected[rel] = h
    require(len(expected) == expected_count, f'CP111 manifest expected {expected_count} rows, found {len(expected)}.')
    actual = {}
    for p in repo.rglob('*'):
        if not p.is_file():
            continue
        rel = p.relative_to(repo).as_posix()
        if rel == 'CHECKPOINT_111_SHA256SUMS.txt' or not is_repo_owned(rel):
            continue
        actual[rel] = sha256(p)
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    require(not missing and not extra, f'CP111 manifest file-set mismatch. Missing={missing[:8]} Extra={extra[:8]}')
    bad = [rel for rel in expected if expected[rel] != actual[rel]]
    require(not bad, f'CP111 manifest hash mismatch: {bad[:8]}')
    return len(actual)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', required=True)
    ap.add_argument('--runtime-output')
    args = ap.parse_args()
    repo = Path(args.repo).resolve()

    try:
        print('       Validating accepted CP110 provenance and frozen production/test/simulation surfaces...')
        require(sha256(repo / 'CHECKPOINT_110_SHA256SUMS.txt') == EXPECTED_CP110_MANIFEST_SHA, 'Accepted CP110 manifest provenance drifted.')
        require(sha256(repo / 'docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_1.json') == EXPECTED_MATRIX_SHA, 'CP109 numerical matrix drifted.')
        require(sha256(repo / 'docs/archive/player_technology/pre-cp165-active/power_reactor_calibration_profile_v0_1.json') == EXPECTED_REACTOR_PROFILE_SHA, 'CP110 Reactor profile drifted.')
        validate_hash_list(repo, 'docs/validation/evidence/checkpoint-111/CP110_FROZEN_PRODUCTION_TEST_SHA256SUMS.txt', 561, 'CP110 production/test')
        validate_hash_list(repo, 'docs/validation/evidence/checkpoint-111/CP110_FROZEN_SIMULATION_BASE_SHA256SUMS.txt', 15, 'CP110 simulation-base')
        validate_production_boundary(repo)

        print('       Validating CP111 study architecture, exact-fill population, damage scope, and instrumentation contract...')
        definition = read_json(repo / 'tools/checkpoints/checkpoint-111/checkpoint_111_architecture_definition.json')
        require(definition['checkpointId'] == '111' and definition['acceptedBaseline'] == '110', 'CP111 definition identity/baseline drifted.')
        require(definition['checkpointType'] == 'same_tl_build_ecology_instrumentation_foundation', 'CP111 checkpoint type drifted.')
        require(definition['productionRuntime'] == 'C# / Godot' and definition['pythonRequiredByProductionRuntime'] is False, 'CP111 runtime boundary drifted.')
        require(definition['productionSourceChanged'] is False and definition['conceptChanged'] is False and definition['numericalMatrixChanged'] is False and definition['reactorCandidateChanged'] is False, 'CP111 must not change production/numerical/Concept authority.')
        require(definition['damageModel'] == 'layered_defense_hull_only' and definition['internalDamageCriticalsSimulated'] is False, 'CP111 damage scope drifted.')
        pop = definition['primaryPopulation']
        require(pop == {'technologyLevels':9,'builds':108,'buildsPerTl':12,'unorderedPairings':594,'movementOrderMirrors':2,'variants':1188,'exactFill':True,'missionAuxFillerHasTacticalEffect':False}, f'CP111 population definition drifted: {pop}')
        require(definition['localBoundedEvidence']['trialsPerVariant'] == 100 and definition['localBoundedEvidence']['totalEngagements'] == 118800, 'CP111 local evidence scale drifted.')
        require(definition['nativeSubstantiveWorkload']['trialsPerVariant'] == 1000 and definition['nativeSubstantiveWorkload']['totalEngagements'] == 1188000, 'CP111 native workload scale drifted.')
        require(definition['mixedTlPopulation'] == {'registered':True,'executed':False,'populationWeight':0}, 'CP111 mixed-TL separation drifted.')
        require(definition['overloadInstrumentationProbes'] == 5 and definition['automaticPromotion'] is False and definition['productionPromotion'] is False, 'CP111 promotion/probe contract drifted.')

        study = read_json(repo / 'docs/archive/testing/pre-cp165-active/same_tl_build_ecology_instrumentation_study_v0_1.json')
        require(study['schemaVersion'] == 'star-cluster-same-tl-build-ecology-v0.1' and study['checkpoint'] == '111', 'CP111 study identity drifted.')
        require(study['technologyLevels'] == list(range(1,10)) and study['trialsPerVariant'] == 1000 and study['masterSeed'] == 11120260815, 'CP111 study scale/seed drifted.')
        require(study['damageModel'] == 'layered_defense_hull_only' and study['internalDamageCriticalsSimulated'] is False, 'CP111 study damage scope drifted.')
        require(study['missionAuxFiller']['enabled'] is True and study['missionAuxFiller']['unitSpace'] == 1 and study['missionAuxFiller']['tacticalEffect'] is False, 'CP111 exact-fill mission-AUX rule drifted.')
        require(study['mixedTlPopulation'] == {'registered':True,'executed':False,'populationWeight':0,'reason':'Keep the first instrumentation/ecology inference population same-TL. Mixed-TL and legacy-component populations will be separate overlays so they cannot contaminate same-TL inference.'}, 'CP111 mixed-TL study separation drifted.')
        require(study['geometry']['map'] == 'radius-5 tactical hex map' and study['geometry']['movementOrder'] == ['SideAFirst','SideBFirst'], 'CP111 geometry/movement-order contract drifted.')
        require('close on later' in study['geometry']['postContactMovement'], 'CP111 track-aware closure rule missing.')
        require('+1 same-hex Burn-through Resistance' in study['geometry']['sameHexBurnthroughBaseline'], 'CP111 accepted same-hex burn-through baseline missing.')
        require(study['automaticPromotion'] is False, 'CP111 study may not auto-promote.')

        print('       Validating checked-in bounded ecology evidence and mechanic probes...')
        validate_ecology_output(repo / 'docs/validation/evidence/checkpoint-111/local-bounded-ecology', 100, 'checked-in CP111 bounded ecology')
        selftest = read_json(repo / 'docs/validation/evidence/checkpoint-111/CP111_PYTHON_SELF_TEST_SUMMARY.json')
        require(selftest.get('passed') is True and selftest.get('tests') == {'run':31,'failures':0,'errors':0,'skipped':0} and selftest.get('failedGates') == 0, f'CP111 self-test evidence drifted: {selftest}')
        parity = read_json(repo / 'docs/validation/evidence/checkpoint-111/CP111_PARITY_SUMMARY.json')
        require(parity.get('passed') is True and parity.get('cases') == 25 and parity.get('errors') == [] and parity.get('failedGates') == 0, f'CP111 parity evidence drifted: {parity}')

        print('       Validating documentation/runtime boundary and full repository manifest...')
        for rel, needles in {
            'README.md':['Checkpoint 111 Candidate','1,188,000','layered_defense_hull_only'],
            'CHAT_README.md':['Checkpoint 110 is the current native-accepted','Checkpoint 111 is the active candidate','internal criticals/subsystem hits'],
            'docs/README.md':['Checkpoint 110 is the native-accepted','Checkpoint 111 is the active'],
            'docs/development/Simulation_Development_Guidelines.md':['Build-ecology instrumentation and population separation','zero-effect mission/AUX accounting'],
            'tools/simulation/README.md':['Thirty-one Python self-tests','CP111 same-TL build ecology'],
            'docs/archive/testing/pre-cp165-active/Same_TL_Build_Ecology_Architecture_v0_1.md':['subsystem critical selection','Exact-fill construction'],
            'docs/design/testing/Same_TL_Build_Ecology_Instrumentation_Report_v1.md':['118,800','1,188,000','No candidate numerical value should be promoted'],
        }.items():
            txt = read_text(repo / rel)
            for needle in needles:
                require(needle in txt, f'CP111 documentation missing expected text {needle!r} in {rel}.')
        require((repo / 'docs/Star_Cluster_Game_Concept_v0.7j.docx').is_file(), 'CP111 must preserve Concept v0.7j.')
        expected_count = int(definition['repositoryOwnedFiles'])
        manifest_count = validate_manifest(repo, expected_count)

        if args.runtime_output:
            runtime = Path(args.runtime_output)
            if not runtime.is_absolute():
                runtime = repo / runtime
            print('       Validating native substantive CP111 ecology output...')
            validate_ecology_output(runtime, 1000, 'native CP111 substantive ecology')

        print(f'       CP111 contract verified: {manifest_count} repository-owned files; 561 frozen production/test files; 15 frozen simulation-base files; 108 exact-fill builds / 594 mirrored bundles / 1,188 variants; layered-defense/Hull-only damage; 31 self-tests / 25 parity fixtures; no numerical promotion.')
        return 0
    except Exception as exc:
        print(f'CP111 contract failure: {type(exc).__name__}: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
