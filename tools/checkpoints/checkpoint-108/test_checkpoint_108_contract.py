#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ALLOWED_EXPRESSIONS = {
    'automatic_architecture', 'automatic_capability', 'installed_component',
    'optional_component', 'operating_mode', 'payload_variant', 'campaign_capability',
    'infrastructure', 'supporting_research', 'deferred_concept', 'precursor_exception'
}

EXCLUDED_PARTS = {'.git', '.vs', '.vscode', '.idea', 'out', 'bin', 'obj', 'TestResults', '__pycache__'}
EXCLUDED_FILES = {'.DS_Store', 'Thumbs.db'}
EXCLUDED_SUFFIXES = {'.pyc', '.user', '.userosscache', '.sln.docstates', '.uid', '.suo'}


def die(message: str) -> None:
    raise AssertionError(message)


def require(condition: bool, message: str) -> None:
    if not condition:
        die(message)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path):
    require(path.is_file(), f"Required JSON file is missing: {path}")
    return json.loads(path.read_text(encoding='utf-8-sig'))


def read_text(path: Path) -> str:
    require(path.is_file(), f"Required text file is missing: {path}")
    return path.read_text(encoding='utf-8-sig')


def is_repo_owned(rel: str) -> bool:
    p = Path(rel)
    if any(part in EXCLUDED_PARTS for part in p.parts):
        return False
    if p.name in EXCLUDED_FILES:
        return False
    low = p.name.lower()
    if any(low.endswith(s) for s in EXCLUDED_SUFFIXES):
        return False
    return True


def docx_text(path: Path) -> str:
    require(path.is_file(), f"Concept document missing: {path}")
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    with zipfile.ZipFile(path) as zf:
        xml = zf.read('word/document.xml')
    root = ET.fromstring(xml)
    chunks = []
    for p in root.findall('.//w:p', ns):
        text = ''.join(t.text or '' for t in p.findall('.//w:t', ns))
        if text:
            chunks.append(text)
    return '\n'.join(chunks)


def find_entry(entries, discipline, lineage, tl, technology=None):
    found = [e for e in entries if e['discipline'] == discipline and e['lineageId'] == lineage and int(e['tl']) == tl]
    if technology is not None:
        found = [e for e in found if e['technology'] == technology]
    require(len(found) == 1, f"Expected exactly one entry for {discipline}/{lineage}/TL{tl}/{technology or '*'}, found {len(found)}")
    return found[0]


def validate_frozen_hashes(repo: Path) -> int:
    evidence = repo / 'docs/validation/evidence/checkpoint-108/CP107B_FROZEN_NUMERICAL_EXECUTABLE_SHA256SUMS.txt'
    count = 0
    for line in read_text(evidence).splitlines():
        if not line.strip():
            continue
        m = re.fullmatch(r'([0-9a-f]{64})  (.+)', line.strip())
        require(m is not None, f"Malformed frozen-hash row: {line}")
        expected, rel = m.groups()
        path = repo / rel
        require(path.is_file(), f"Frozen numerical/executable file missing: {rel}")
        require(sha256(path) == expected, f"Frozen numerical/executable hash drifted: {rel}")
        count += 1
    require(count == 133, f"Expected 133 frozen numerical/executable hashes, found {count}")
    return count


def validate_production_boundary(repo: Path) -> None:
    for project in ('src/StarCluster.Game', 'src/StarCluster.Core'):
        root = repo / project
        require(root.is_dir(), f"Production runtime directory missing: {project}")
        py = list(root.rglob('*.py'))
        if py:
            die(f"Python source leaked into production runtime tree: {py[0].relative_to(repo)}")
        for path in root.rglob('*'):
            if not path.is_file() or path.suffix.lower() not in {'.cs', '.csproj', '.props', '.targets'}:
                continue
            text = path.read_text(encoding='utf-8-sig', errors='ignore').lower()
            forbidden = ('python.runtime', 'pythonnet', 'ironpython', 'python.exe', 'python3.exe')
            for marker in forbidden:
                require(marker not in text, f"Production runtime references forbidden Python dependency marker '{marker}': {path.relative_to(repo)}")


def validate_manifest(repo: Path) -> int:
    manifest = repo / 'CHECKPOINT_108_SHA256SUMS.txt'
    require(manifest.is_file(), 'CHECKPOINT_108_SHA256SUMS.txt is missing.')
    listed = {}
    for line in read_text(manifest).splitlines():
        if not line.strip():
            continue
        m = re.fullmatch(r'([0-9a-f]{64})  (.+)', line)
        require(m is not None, f"Malformed manifest row: {line}")
        h, rel = m.groups()
        require(rel not in listed, f"Manifest duplicate: {rel}")
        listed[rel] = h
    actual = {}
    for path in repo.rglob('*'):
        if not path.is_file():
            continue
        rel = path.relative_to(repo).as_posix()
        if rel == 'CHECKPOINT_108_SHA256SUMS.txt' or not is_repo_owned(rel):
            continue
        actual[rel] = sha256(path)
    require(set(actual) == set(listed), f"Manifest path set mismatch: actual {len(actual)}, manifest {len(listed)}")
    for rel, h in actual.items():
        require(listed[rel] == h, f"Manifest hash mismatch: {rel}")
    return len(actual)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', required=True)
    args = ap.parse_args()
    repo = Path(args.repo).resolve()

    print('       Validating accepted CP107b provenance and frozen numerical/executable authority...')
    require(sha256(repo / 'CHECKPOINT_107B_SHA256SUMS.txt') == '92751a27ad8726cd2ce5ff2b24afb8eeb11d715e56d363bed3a4fd5dbda60bb5', 'Accepted CP107b manifest hash drifted.')
    frozen_count = validate_frozen_hashes(repo)
    require(sha256(repo / 'docs/archive/concepts/Star_Cluster_Game_Concept_v0.7g.docx') == '20dd862e2364c1d68c7487037941bf28cc179ac04a24862c30f002b0c4c7520a', 'Archived CP107b Concept v0.7g hash drifted.')
    require(sha256(repo / 'docs/archive/player_technology/pre-cp165-active/technology_component_table_v0_1.json') == '6b78ac530d63e2cb16c2627427a30d8774df9c2aa4d9ab24af56861cc09b1331', 'Historical CP107 table v0.1 hash drifted.')

    print('       Validating CP108 qualitative technology architecture...')
    definition = read_json(repo / 'tools/checkpoints/checkpoint-108/checkpoint_108_architecture_definition.json')
    require(definition['checkpointId'] == '108' and definition['acceptedBaseline'] == '107b', 'CP108 definition identity drifted.')
    require(definition['productionRuntime'] == 'C# / Godot', 'Production runtime boundary drifted.')
    require(definition['pythonAllowedForTestingSimulationAndCheckpointValidation'] is True, 'Python testing/simulation permission missing.')
    require(definition['pythonRequiredByProductionRuntime'] is False, 'Python must not be a production runtime dependency.')
    require(not definition['numericalTlTableChanged'] and not definition['newTl4Tl9BalanceValuesAssigned'] and not definition['simulationOrCalibrationRun'] and int(definition['declaredTrials']) == 0, 'CP108 must remain qualitative architecture only.')

    table = read_json(repo / 'docs/archive/player_technology/pre-cp165-active/technology_component_table_v0_2.json')
    entries = table['lineageEntries']
    grid = table['grid']
    require(str(table['checkpoint']) == '108', 'Technology table must be CP108 v0.2.')
    require(len(grid) == 90 and len(entries) == 214, 'Technology table must contain 90 grid rows and 214 Storyboard beats.')
    require(len(set((e['disciplineId'], e['lineageId']) for e in entries)) == 32, 'Technology table must preserve 32 source lineages.')
    require(len(table['standardLineages']) == 10, 'Technology table must preserve 10 visible disciplines.')
    require(all(e.get('playerExpression') in ALLOWED_EXPRESSIONS for e in entries), 'Every Storyboard beat must have a valid player-expression class.')
    require(all(len(e.get('hardExternalPrerequisites', [])) == 0 for e in entries), 'CP108 must promote zero hard external prerequisites.')
    require(table['contracts']['balanceCalibrationRun'] is False and table['contracts']['simulationOrCalibrationRun'] is False, 'CP108 table may not claim calibration/simulation.')
    require(table['contracts']['existingTl1Tl3NumericalValuesChanged'] is False and table['contracts']['newTl4Tl9NumericalValuesAssigned'] is False, 'CP108 numerical boundary drifted.')
    require(table['contracts']['startingShuttles'] == 1 and table['contracts']['workingTacticalFuelCapacity'] == 100 and table['contracts']['workingFuelPerTraversedHex'] == 2 and table['contracts']['workingEvasiveManeuverFuelPerTurn'] == 1 and table['contracts']['ablativeArmorSpace'] == 1, 'Foundation working values drifted.')
    require(table['contracts']['hardExternalPrerequisitesPromotedByCp108'] == 0, 'CP108 hard prerequisite count drifted.')
    require(len(table['optionalComponents']) == 35, 'CP108 optional/support catalog must contain 35 candidates.')

    # Targeted corrections that define CP108.
    armor7 = find_entry(entries, 'Armor', 'armor-enhancements', 7, 'Adaptive reactive armor architecture')
    armor8 = find_entry(entries, 'Armor', 'armor-enhancements', 8, 'Field-assisted armor reinforcement')
    require(armor7['playerExpression'] == 'optional_component' and armor8['playerExpression'] == 'optional_component', 'Powered Armor enhancements must remain optional components.')
    em = find_entry(entries, 'Armor', 'armor-enhancements', 7, 'Electromagnetic particle screen')
    require(em['adoptedInProvisionalTable'] is False and em['playerExpression'] == 'deferred_concept', 'Duplicate Armor EM screen must remain consolidated/deferred.')
    kin2 = find_entry(entries, 'Projectile Weapons', 'kinetic-ammunition', 2, 'Improved penetrator/projectile materials')
    require(kin2['adoptedInProvisionalTable'] is True, 'TL2 penetrator materials must belong to Kinetic Ammunition.')
    macron = find_entry(entries, 'Projectile Weapons', 'kinetic-main', 7, 'Macron/dust accelerator branch')
    require(macron['structuralRole'] == 'branch' and macron['tableDisposition'] == 'provisional_branch_or_specialist', 'Macron accelerator must remain a branch.')
    find_entry(entries, 'Sensors / EW', 'sensors', 9, 'Pinnacle multi-domain inference suite')
    find_entry(entries, 'Sensors / EW', 'ecm', 9, 'Pinnacle adaptive cross-spectrum deception')
    find_entry(entries, 'Sensors / EW', 'eccm', 9, 'Pinnacle provenance-weighted track validation')
    comp9 = find_entry(entries, 'Computing / Fire Control', 'tactical-computing', 9, 'Pinnacle self-verifying battle synthesis')
    require('precog' in comp9['boundary'].lower() or 'causal' in comp9['boundary'].lower(), 'TL9 Computing boundary must explicitly reject causal/precognitive knowledge.')
    missile9 = find_entry(entries, 'Missile Weapons', 'missile-delivery', 9, 'Integrated field-coupled strike vehicle')
    require('intercept' in missile9['boundary'].lower() and 'micro-jump' in missile9['boundary'].lower(), 'TL9 Missile endpoint must preserve interception and reject micro-jump bypass.')
    energy9 = find_entry(entries, 'Energy Weapons', 'coherent-beam', 9, 'Pinnacle coherent-energy lance')
    require('matter-conversion damage' in energy9['boundary'].lower(), 'TL9 Energy boundary must not infer matter-conversion damage.')

    aux = read_json(repo / 'docs/archive/player_technology/pre-cp165-active/auxiliary_component_catalog_v0_3.json')
    require(len(aux['components']) == 35, 'Auxiliary/support catalog v0.3 must contain 35 candidates.')
    ids = {c['id'] for c in aux['components']}
    for cid in ('probe-survey-drone', 'particle-deflection-screen', 'field-stabilizer'):
        require(cid in ids, f"Missing CP108 support candidate: {cid}")
    require('em-particle-screen' not in ids, 'Duplicate Armor EM particle screen must not remain an active optional catalog entry.')

    story = read_json(repo / 'docs/archive/player_technology/pre-cp165-active/technology_family_storyboard_v1_2.json')
    require(len(story['disciplines']) == 10, 'Storyboard must preserve 10 disciplines.')
    story_entries = [b for d in story['disciplines'] for lin in d['lineages'] for b in lin['beats']]
    require(len(story_entries) == 214 and all(b.get('playerExpression') in ALLOWED_EXPRESSIONS for b in story_entries), 'Storyboard v1.2 must contain 214 expression-classified beats.')
    ideas = read_json(repo / 'docs/design/player_technology/technology_idea_register_v1_3.json')
    require(len(ideas['ideas']) == 136, 'Idea Register v1.3 must preserve 136 ideas.')
    foundation = read_json(repo / 'docs/design/player_technology/Technology_Foundation_Completeness_Audit_v1_2.json')
    require(len(foundation['domains']) == 20, 'Foundation Audit v1.2 must preserve 20 domains.')

    print('       Validating Concept/document consistency and runtime/testing boundary...')
    active = sorted(p.name for p in (repo / 'docs').glob('Star_Cluster_Game_Concept*.docx'))
    require(active == ['Star_Cluster_Game_Concept_v0.7h.docx'], f"Exactly Concept v0.7h must be active; found {active}")
    concept = docx_text(repo / 'docs/Star_Cluster_Game_Concept_v0.7h.docx')
    for phrase in (
        'Version 0.7h', 'Checkpoint 107b native-validated', 'Checkpoint 108 qualitatively reviews',
        'Every Storyboard beat now has a provisional player-expression class',
        'one starting shuttle', '100 / 2 per traversed hex / +1 per EvM turn', '1-Space TL1 Ablative Armor',
        'C-078', 'Player expression'
    ):
        require(phrase in concept, f"Concept v0.7h is missing required text: {phrase}")
    for rel in ('README.md','CHAT_README.md','docs/README.md','docs/design/player_technology/README.md','docs/design/testing/README.md','docs/validation/README.md','docs/Prototype_TODO.md'):
        text = read_text(repo / rel)
        require('108' in text and '107b' in text, f"Active document must recognize CP107b baseline and CP108 candidate: {rel}")
    validate_production_boundary(repo)

    print('       Validating full repository manifest...')
    manifest_count = validate_manifest(repo)
    print(f'       CP108 contract verified: {manifest_count} repository-owned files; {frozen_count} frozen numerical/executable files; 10 disciplines / 32 source lineages / 214 beats / 136 ideas / 20 foundation domains / 35 support candidates; zero hard gates; zero trials; zero new TL4-TL9 numerical values.')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f'CP108 CONTRACT FAILURE: {exc}', file=sys.stderr)
        raise SystemExit(1)
