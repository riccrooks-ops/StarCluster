#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import sys
from pathlib import Path

CP128_MANIFEST_SHA = '29e2a8617d0eecb149891b49cb39c64220c4371ae25ffcde0d0ddb7f71849da5'
CP128_RESULTS_SHA = '5a1d4fe869a465eec67ecd2653319b59ddc70a5b9e2d02831659806bf6bc283a'


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


def validate_stdlib_only_python_surface(repo: Path) -> int:
    roots = [repo / 'tools/simulation', repo / 'tools/checkpoints/checkpoint-129']
    files = []
    for root in roots:
        files.extend(sorted(root.rglob('*.py')))
    files.append(repo / 'tools/checkpoints/prepackage_repository_hygiene.py')
    files = sorted(set(files))
    stdlib = set(sys.stdlib_module_names) | {'__future__'}
    local_roots = {'starcluster_research', 'prepackage_repository_hygiene'}
    violations = []
    for path in files:
        tree = ast.parse(text(path), filename=str(path))
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name.split('.', 1)[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = [node.module.split('.', 1)[0]]
            for name in names:
                if name not in stdlib and name not in local_roots:
                    violations.append(f"{path.relative_to(repo).as_posix()}:{getattr(node, 'lineno', '?')}:{name}")
    req(not violations, 'non-stdlib Python dependency on CP129 acceptance surface: ' + ', '.join(violations[:8]))
    return len(files)


def validate_cp128_native(repo: Path):
    base = repo / 'docs/validation/evidence/checkpoint-129'
    s = js(base / 'CP128_NATIVE_ACCEPTANCE_SUMMARY.json')
    req(s['checkpoint'] == 128 and s['repositoryOnly'] is True and s['failedGates'] == [], 'CP128 native identity')
    req(s['dotnetSdk'] == '8.0.423' and s['buildPassed'] and s['buildWarningsAsErrors'], 'CP128 native build')
    req(s['pythonTestsPassed'] == 171 and s['xunitPassed'] == 907 and s['xunitFailed'] == 0 and s['xunitSkipped'] == 0, 'CP128 tests')
    req(s['scenarioRunnerSelfTestsPassed'] == 70 and s['researchParityPassed'] == 25, 'CP128 parity/self-tests')
    req(s['technologyValuesChanged'] is False and s['numericLeafChangesFromAcceptedCp127'] == 0, 'CP128 frozen values')
    provenance = text(base / 'CP129_PREDECESSOR_PROVENANCE.md')
    req(CP128_RESULTS_SHA in provenance, 'CP128 native archive hash provenance')
    contents = manifest(base / 'CP128_NATIVE_RESULTS_CONTENTS_SHA256SUMS.txt')
    summary_rel = 'checkpoint-128/CP128_NATIVE_ACCEPTANCE_SUMMARY.json'
    req(contents.get(summary_rel) == sha(base / 'CP128_NATIVE_ACCEPTANCE_SUMMARY.json'), 'CP128 curated summary content hash')


def validate_frozen_cp128_surfaces(repo: Path) -> int:
    p = repo / 'docs/validation/evidence/checkpoint-128/CP128_REPOSITORY_SHA256SUMS.txt'
    req(sha(p) == CP128_MANIFEST_SHA, 'accepted CP128 repository manifest hash')
    old = manifest(p)
    # Production, native tests, and current numerical/document authorities are frozen.
    singles = {
        'docs/Star_Cluster_Game_Concept_v0.7s.docx',
        'docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_5.json',
        'docs/archive/player_technology/pre-cp165-active/technology_component_table_v0_7.json',
        'docs/archive/player_technology/pre-cp165-active/Technology_Component_Table_v0_7.md',
        'docs/archive/player_technology/pre-cp165-active/StarCluster_Stabilized_TL1_TL9_Technology_Component_Table_v0_7.xlsx',
        'docs/archive/player_technology/pre-cp165-active/canonical_numerical_authority_v0_4.json',
        'docs/archive/player_technology/pre-cp165-active/Main_Subsystem_Technology_Stabilization_Review_v2.md',
        'tools/simulation/run_starcluster_research.py',
    }
    expected = []
    for rel in old:
        if rel.startswith(('src/', 'tests/StarCluster.Tests/')) or rel in singles:
            expected.append(rel)
        elif rel.startswith('tools/simulation/starcluster_research/') and rel != 'tools/simulation/starcluster_research/cli.py':
            expected.append(rel)
        elif rel.startswith('tools/simulation/tests/'):
            expected.append(rel)
    # New CP129 module/test do not exist in CP128 manifest, so existing files must remain byte-identical.
    for rel in sorted(expected):
        path = repo / rel
        req(path.is_file(), f'frozen CP128 path missing: {rel}')
        req(sha(path) == old[rel], f'frozen CP128 surface drift: {rel}')
    req(len(expected) > 600, 'frozen CP128 surface unexpectedly small')
    return len(expected)


def validate_study_plan(repo: Path):
    sys.path.insert(0, str(repo / 'tools/simulation'))
    from starcluster_research.whole_ladder_sensitivity_analysis import (
        build_plan, construction_overrides_for_transition, performance_overrides_for_transition, validate_study,
    )
    study_path = repo / 'docs/archive/testing/pre-cp165-active/cp129_whole_ladder_pure_tl_sensitivity_study_v0_1.json'
    doc = js(study_path)
    req(validate_study(doc) == [], 'CP129 study schema')
    plan = build_plan(repo, study_path, None)
    s = plan['summary']
    req(s['failedGates'] == [], 'CP129 plan gates')
    req(s['legalBuilds'] == 9427 and s['wholeLadderBasePairings'] == 70034, 'CP129 population/pairing counts')
    req(s['generatedVariants'] == 626028 and s['substantiveTrials'] == 45665000, 'CP129 workload counts')
    req(s['matchedCompositionTasks'] == 7699 and s['sensitivityVariants'] == 338756, 'CP129 matched sensitivity counts')
    req(s['mainOnlyLegalBuilds'] == 1856 and s['mainOnlyAdjacentVariants'] == 7136, 'CP129 main-only control counts')
    req(s['mixedTlShipsExecuted'] is False and s['counterfactualHoldbacksAreLegalMixedTlBuilds'] is False, 'CP129 mixed-TL boundary')
    # Holdbacks must affect only the high-TL row and separate combat from construction fields.
    for high in range(2, 10):
        for package in [x['id'] for x in doc['performanceHoldbackBoundary']['packages']]:
            for row in performance_overrides_for_transition(repo, doc, package, high):
                req(int(row['tl']) == high, f'performance holdback not transition-local {package} TL{high}')
                req(row['field'] != 'space' and not (row['profile'] == 'hull' and row['field'] == 'capacity'), f'construction field leaked into performance holdback {row}')
        for package in [x['id'] for x in doc['constructionEnvelopeSensitivity']['packages']]:
            for row in construction_overrides_for_transition(repo, doc, package, high):
                req(int(row['tl']) == high and row['field'] in {'space','capacity'}, f'non-construction field in envelope sensitivity {row}')
    return s


def validate_current_authority_invariants(repo: Path):
    d = js(repo / 'docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_5.json')['profiles']
    req([d['stl'][str(t)]['move'] for t in range(1,10)] == list(range(1,10)), 'STL Move invariant')
    req([d['missile_delivery'][str(t)]['missileMove'] for t in range(1,10)] == list(range(2,11)), 'Missile Move invariant')
    req([d['ftl'][str(t)]['strategicMove'] for t in range(1,10)] == [1,2,3,4,4,6,7,9,12], 'FTL ladder')
    e = d['energy_main']['8']
    req((e['lowDamage'],e['standardDamage'],e['highDamage'],e['apen']) == (7,10,12,3), 'TL8 Energy frozen state')


def validate_docs_and_hygiene(repo: Path):
    for rel in ('README.md','CHAT_README.md','docs/README.md','docs/design/README.md','docs/design/testing/README.md','docs/design/player_technology/README.md','docs/validation/README.md','docs/Prototype_TODO.md'):
        c = text(repo / rel)
        req('129' in c or 'cp129' in c.lower(), f'{rel} not CP129-aware')
    g = text(repo / 'docs/development/Simulation_Development_Guidelines.md')
    req('## Whole-ladder sensitivity before mixed-TL ecology' in g, 'CP129 durable methodology missing')
    sys.path.insert(0, str(repo / 'tools/checkpoints'))
    import prepackage_repository_hygiene as hygiene
    errors = hygiene.check_repository_hygiene(repo)
    req(errors == [], 'packaging hygiene: ' + '; '.join(errors))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', required=True)
    args = ap.parse_args()
    repo = Path(args.repo).resolve()
    try:
        d = js(repo / 'tools/checkpoints/checkpoint-129/checkpoint_129_definition.json')
        req(d['checkpoint'] == 129 and d['expectedPythonTests'] == 177, 'checkpoint definition')
        req(d['technologyValuesChanged'] is False and d['productionSourceChanged'] is False and d['scenarioDefinitionsChanged'] is False, 'frozen production/value boundary')
        req(d['researchSimulationChanged'] is True and d['mixedTlShipsExecuted'] is False, 'CP129 research boundary')
        req(d['pythonDependencyPolicy'] == 'stdlib-only' and d['thirdPartyPythonPackagesAllowed'] == [], 'Python dependency policy')
        req(d.get('jobsConfigurable') is True and d.get('defaultJobs') == 24 and d.get('minimumJobs') == 1 and d.get('maximumJobs') == 61, 'configurable Jobs contract')
        count = validate_stdlib_only_python_surface(repo)
        print(f'       Validating stdlib-only CP129 Python acceptance surface ({count} files; no third-party packages)...')
        print('       Validating native-accepted CP128 provenance...')
        validate_cp128_native(repo)
        print('       Validating frozen CP128 production, numerical, and pre-existing research surfaces...')
        frozen = validate_frozen_cp128_surfaces(repo)
        print(f'       Frozen CP128 files verified: {frozen}.')
        print('       Validating frozen main-subsystem invariants...')
        validate_current_authority_invariants(repo)
        print('       Reconstructing CP129 whole-ladder and sensitivity plan...')
        s = validate_study_plan(repo)
        print(f"       CP129 plan: {s['legalBuilds']} legal builds; {s['wholeLadderBasePairings']} whole-ladder pairings; {s['generatedVariants']} variants; {s['substantiveTrials']} substantive engagements.")
        print('       Validating checkpoint-aware documentation and evidence packaging hygiene...')
        validate_docs_and_hygiene(repo)
        print('       CP129 preflight passed: accepted CP128 table frozen; no legal mixed-TL ships; performance/construction sensitivity boundaries explicit; packaging budget preserved.')
        return 0
    except Exception as exc:
        print(f'CP129 preflight failure: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
