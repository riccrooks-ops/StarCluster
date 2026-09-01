#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

CP127_MANIFEST_SHA = '95265aea173636720e83a6a5f36dc5c2c023bef6f8f8160851559aa873ba3d7f'
CP127_RESULTS_SHA = 'ebf5c8c8a38e74d14302f26f5138fe71b14e6565e8043605834cce7de78899bf'
CP125_RESULTS_SHA = 'e26f4a79075cd3bb395213d9a4da7d9e3708fecd3dbd3b5a29911c24ea63ecf0'
CP126_RESULTS_SHA = 'a82e8e1f98f9af5589666d091f4773cd3f98b881c82c108a7da7ab2d1c74edb0'


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
    roots = [repo / 'tools/simulation', repo / 'tools/checkpoints/checkpoint-128']
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
    req(not violations, 'non-stdlib Python dependency on CP128 acceptance surface: ' + ', '.join(violations[:8]))
    return len(files)


def read_xlsx_table(path: Path):
    ns = {
        'x': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
        'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
        'p': 'http://schemas.openxmlformats.org/package/2006/relationships',
    }
    with zipfile.ZipFile(path) as z:
        workbook = ET.fromstring(z.read('xl/workbook.xml'))
        rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        relmap = {e.attrib['Id']: e.attrib['Target'].lstrip('/') for e in rels}
        sheets = []
        for sh in workbook.find('x:sheets', ns):
            rid = sh.attrib['{' + ns['r'] + '}id']
            sheets.append((sh.attrib['name'], relmap[rid]))
        req([n for n, _ in sheets] == ['Overview', 'Lineage Map', 'Numerical Baseline', 'Optional Components', 'CP128 Baseline'], 'workbook sheets')
        target = dict(sheets)['Numerical Baseline']
        root = ET.fromstring(z.read(target))
        dim = root.find('x:dimension', ns)
        req(dim is not None and dim.attrib.get('ref') == 'A1:E181', 'workbook numerical shape')
        rows = []
        for row in root.findall('x:sheetData/x:row', ns):
            vals = [None] * 5
            for cell in row.findall('x:c', ns):
                ref = cell.attrib.get('r', '')
                m = re.match(r'([A-E])([0-9]+)$', ref)
                if not m:
                    continue
                idx = ord(m.group(1)) - ord('A')
                ctype = cell.attrib.get('t')
                if ctype == 'inlineStr':
                    vals[idx] = ''.join((node.text or '') for node in cell.findall('.//x:t', ns))
                else:
                    v = cell.find('x:v', ns)
                    raw = '' if v is None or v.text is None else v.text
                    if ctype == 'n' and raw != '':
                        num = float(raw)
                        vals[idx] = int(num) if num.is_integer() else num
                    else:
                        vals[idx] = raw
            rows.append(vals)
    req(len(rows) == 181 and rows[0] == ['Profile', 'TL', 'Technology', 'Characteristics', 'Notes'], 'workbook numerical rows/header')
    return rows


def validate_cp127_native(repo: Path):
    base = repo / 'docs/validation/evidence/checkpoint-128/curated-predecessor-native-evidence/cp127'
    s = js(base / 'CP127_NATIVE_ACCEPTANCE_SUMMARY.json')
    req(s['checkpoint'] == 127 and s['repositoryOnly'] is False and s['failedGates'] == [], 'CP127 native identity')
    req(s['dotnetSdk'] == '8.0.423' and s['buildPassed'] and s['buildWarningsAsErrors'], 'CP127 native build')
    req(s['pythonTestsPassed'] == 170 and s['xunitPassed'] == 907 and s['xunitFailed'] == 0 and s['xunitSkipped'] == 0, 'CP127 tests')
    req(s['scenarioRunnerSelfTestsPassed'] == 70 and s['researchParityPassed'] == 25, 'CP127 parity/self-tests')
    req(s['generatedVariants'] == 86584 and s['pipelineSmokeTrials'] == 86584 and s['substantiveTrials'] == 8658400, 'CP127 workload')
    req(s['symmetryComparisons'] == 2250 and s['symmetryMismatches'] == 0, 'CP127 symmetry')
    req(s['stlMoveEqualsDriveTl'] and s['missileMoveEqualsDriveTlPlusOne'] and s['tl8EnergyDamageCandidate'] == '7/10/12', 'CP127 accepted decisions')
    a = js(base / 'main-subsystem-stabilization-study/analysis.json')
    req(a['failedGates'] == [] and a['trialErrors'] == 0 and a['totalTrials'] == 8658400, 'CP127 substantive evidence')


def validate_frozen_cp127_surfaces(repo: Path):
    p = repo / 'docs/validation/evidence/checkpoint-127/CP127_REPOSITORY_SHA256SUMS.txt'
    req(sha(p) == CP127_MANIFEST_SHA, 'frozen CP127 repository manifest hash')
    old = manifest(p)
    prefixes = ('src/', 'tests/StarCluster.Tests/', 'tools/simulation/starcluster_research/')
    singles = {
        'tools/simulation/run_starcluster_research.py',
        'docs/archive/testing/pre-cp165-active/cp127_main_subsystem_tl_stabilization_study_v0_1.json',
        'docs/archive/testing/pre-cp165-active/telemetry_instrumentation_contract_v0_2.json',
        'docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_4.json',
        'docs/archive/player_technology/pre-cp165-active/technology_component_table_v0_6.json',
        'docs/archive/player_technology/pre-cp165-active/Technology_Component_Table_v0_6.md',
        'docs/archive/player_technology/pre-cp165-active/StarCluster_Stabilized_TL1_TL9_Technology_Component_Table_v0_6.xlsx',
    }
    expected = sorted(rel for rel in old if rel.startswith(prefixes) or rel in singles)
    current = []
    for rel in expected:
        path = repo / rel
        req(path.is_file(), f'frozen CP127 path missing: {rel}')
        req(sha(path) == old[rel], f'frozen CP127 surface drift: {rel}')
        current.append(rel)
    req(len(current) > 50, 'frozen CP127 surface unexpectedly small')
    return len(current)


def validate_matrix(repo: Path):
    old = js(repo / 'docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_4.json')
    new = js(repo / 'docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_5.json')
    req(new['schemaVersion'].endswith('v0.5') and new['authorityBoundary']['referenceCheckpoint'] == 128, 'v0.5 matrix identity')
    req(old['profiles'].keys() == new['profiles'].keys(), 'profile families')
    string_diffs = []
    for fam in old['profiles']:
        req(old['profiles'][fam].keys() == new['profiles'][fam].keys(), f'{fam} TL keys')
        for tl in old['profiles'][fam]:
            a, b = old['profiles'][fam][tl], new['profiles'][fam][tl]
            req(a.keys() == b.keys(), f'{fam} TL{tl} fields')
            for key in a:
                if a[key] != b[key]:
                    req(key in {'notes', 'technology'}, f'operational/numerical drift {fam} TL{tl} {key}: {a[key]} -> {b[key]}')
                    string_diffs.append((fam, tl, key))
    req(set(string_diffs) == {
        *{('stl', str(t), 'notes') for t in range(1, 10)},
        *{('missile_delivery', str(t), 'notes') for t in range(1, 10)},
        ('missile_delivery', '5', 'technology'),
        ('missile_delivery', '8', 'technology'),
    }, f'unexpected profile prose delta: {string_diffs}')
    for key in ('branches', 'hardPrerequisites', 'lowerTlReconciliation', 'overview', 'wholeShipSanity', 'damagePointScale', 'profileOrder'):
        req(old[key] == new[key], f'non-metadata matrix drift: {key}')
    p = new['profiles']
    req([p['stl'][str(t)]['move'] for t in range(1, 10)] == list(range(1, 10)), 'STL invariant')
    req([p['missile_delivery'][str(t)]['missileMove'] for t in range(1, 10)] == list(range(2, 11)), 'Missile invariant')
    req([p['ftl'][str(t)]['strategicMove'] for t in range(1, 10)] == [1,2,3,4,4,6,7,9,12], 'FTL ladder')
    e = p['energy_main']['8']
    req((e['lowDamage'], e['standardDamage'], e['highDamage'], e['apen']) == (7,10,12,3), 'TL8 Energy stabilized state')
    for stale in ('Maturation holds Move', 'nonuniform movement frontier', 'Deliberate larger frontier jump'):
        req(stale not in text(repo / 'docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_5.json'), f'stale current matrix prose: {stale}')


def validate_table_and_workbook(repo: Path):
    old = js(repo / 'docs/archive/player_technology/pre-cp165-active/technology_component_table_v0_6.json')
    new = js(repo / 'docs/archive/player_technology/pre-cp165-active/technology_component_table_v0_7.json')
    req(new['checkpoint'] == 128 and new['lineageEntries'] == old['lineageEntries'], 'Tech Table lineage entries changed')
    req(new['optionalComponents'] == old['optionalComponents'], 'optional component entries changed')
    req(len(new['lineageEntries']) == 218 and len(new['optionalComponents']) == 35, 'Tech Table shape')
    canon = js(repo / 'docs/archive/player_technology/pre-cp165-active/canonical_numerical_authority_v0_4.json')
    req(canon['checkpoint'] == 128 and canon['acceptedEvidenceBaseline'] == 127, 'canonical authority identity')
    req(canon['primaryReferenceMatrix'] == 'technology_numerical_matrix_v0_5.json' and canon['primaryTechnologyTable'] == 'technology_component_table_v0_7.json', 'canonical current pointers')
    req(canon['technologyValuesChanged'] is False and canon['numericLeafChangesFromV0_4'] == 0, 'canonical zero-delta declaration')

    sheet_rows = read_xlsx_table(repo / 'docs/archive/player_technology/pre-cp165-active/StarCluster_Stabilized_TL1_TL9_Technology_Component_Table_v0_7.xlsx')
    matrix = js(repo / 'docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_5.json')
    rows = {(str(r[0]), int(r[1])): (r[2], json.loads(r[3]), r[4]) for r in sheet_rows[1:]}
    req(len(rows) == 180, 'workbook numerical rows')
    for fam, tiers in matrix['profiles'].items():
        for tl, row in tiers.items():
            tech, stats, notes = rows[(fam, int(tl))]
            expected = {k:v for k,v in row.items() if k not in {'tl','technology','notes'}}
            req(tech == row.get('technology','') and stats == expected and (notes or '') == row.get('notes',''), f'workbook matrix mismatch {fam} TL{tl}')


def validate_concept_and_docs(repo: Path):
    active = sorted((repo / 'docs').glob('Star_Cluster_Game_Concept_v0.7*.docx'))
    req([p.name for p in active] == ['Star_Cluster_Game_Concept_v0.7s.docx'], f'active Concept set: {[p.name for p in active]}')
    with zipfile.ZipFile(active[0]) as z:
        doc = ''.join(z.read(n).decode('utf-8','ignore') for n in z.namelist() if n.startswith('word/') and n.endswith('.xml'))
        header = ''.join(z.read(n).decode('utf-8','ignore') for n in z.namelist() if n.startswith('word/header') and n.endswith('.xml'))
        core = z.read('docProps/core.xml').decode('utf-8','ignore')
    for phrase in ('standard Move equals its installed Drive TL', 'Operational Missile Move equals the installed Missile Drive TL plus 1', '7/10/12', 'has passed the bounded pure-TL stabilization gate'):
        req(phrase in doc, f'Concept missing {phrase}')
    req('v0.7s' in header and 'Star Cluster Game Concept v0.7s' in core and '<cp:version>0.7s</cp:version>' in core, 'Concept version metadata')
    for rel in ('README.md','CHAT_README.md','docs/README.md','docs/design/README.md','docs/design/testing/README.md','docs/design/player_technology/README.md','docs/validation/README.md','docs/Prototype_TODO.md'):
        content = text(repo / rel)
        req('128' in content or 'cp128' in content.lower(), f'{rel} not CP128-aware')
    req('## Evidence-retention and full-repository packaging hygiene' in text(repo / 'docs/development/Simulation_Development_Guidelines.md'), 'durable evidence-retention guideline')


def parse_contents_manifest(path: Path) -> dict[str, str]:
    return manifest(path)


def validate_evidence_retention(repo: Path):
    ledger = js(repo / 'docs/validation/evidence/checkpoint-128/CP128_EVIDENCE_RETENTION_LEDGER.json')
    req(ledger['checkpoint'] == 128 and ledger['referencesExcludedFromLimit'] is True, 'evidence ledger identity')
    req(ledger['validationEvidenceZipLimits'] == {'maxSingleBytes': 5242880, 'maxTotalBytes': 16777216}, 'evidence ZIP limits')
    all_records = ledger['externalizedNativeArchives'] + [ledger['acceptedCp127Evidence']]
    expected = {125: CP125_RESULTS_SHA, 126: CP126_RESULTS_SHA, 127: CP127_RESULTS_SHA}
    req({int(x['checkpoint']) for x in all_records} == {125,126,127}, 'evidence checkpoints')
    for record in all_records:
        cp = int(record['checkpoint'])
        req(record['originalArchiveSha256'] == expected[cp] and record['archiveBundledInCp128'] is False, f'CP{cp} archive provenance')
        content_manifest = repo / record['contentsManifest']
        entries = parse_contents_manifest(content_manifest)
        req(len(entries) > 10, f'CP{cp} contents manifest too small')
        for item in record['curatedFiles']:
            cp_path = repo / item['curatedPath']
            req(cp_path.is_file(), f'curated CP{cp} file missing: {item["curatedPath"]}')
            req(sha(cp_path) == item['sha256'] and cp_path.stat().st_size == item['bytes'], f'curated CP{cp} hash/size: {item["curatedPath"]}')
            req(entries.get(item['sourcePath']) == item['sha256'], f'curated CP{cp} file not proven by contents manifest: {item["sourcePath"]}')
    req(not (repo / 'docs/validation/evidence/checkpoint-126/CP125_NATIVE_RESULTS_ORIGINAL.zip').exists(), 'CP125 raw native archive still recursively bundled')
    req(not (repo / 'docs/validation/evidence/checkpoint-127/CP126_NATIVE_RESULTS_ORIGINAL.zip').exists(), 'CP126 raw native archive still recursively bundled')
    req((repo / 'docs/validation/evidence/checkpoint-126/CP125_NATIVE_RESULTS_EXTERNALIZED_BY_CP128.md').is_file(), 'CP125 externalization note')
    req((repo / 'docs/validation/evidence/checkpoint-127/CP126_NATIVE_RESULTS_EXTERNALIZED_BY_CP128.md').is_file(), 'CP126 externalization note')

    sys.path.insert(0, str(repo / 'tools/checkpoints'))
    import prepackage_repository_hygiene as hygiene
    errors = hygiene.check_repository_hygiene(repo)
    req(errors == [], 'packaging hygiene: ' + '; '.join(errors))
    req(hygiene.validation_evidence_archive_total_bytes(repo) <= 16 * 1024 * 1024, 'validation ZIP total')


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', required=True)
    args = ap.parse_args()
    repo = Path(args.repo).resolve()
    try:
        d = js(repo / 'tools/checkpoints/checkpoint-128/checkpoint_128_definition.json')
        req(d['checkpoint'] == 128 and d['expectedPythonTests'] == 171 and d['expectedNumericLeafChangesFromAcceptedCp127'] == 0, 'definition')
        req(d['pythonDependencyPolicy'] == 'stdlib-only' and d['thirdPartyPythonPackagesAllowed'] == [], 'Python dependency policy')
        count = validate_stdlib_only_python_surface(repo)
        print(f'       Validating stdlib-only CP128 Python acceptance surface ({count} files; no third-party packages)...')
        print('       Validating accepted CP127 native evidence and frozen production/research surfaces...')
        validate_cp127_native(repo)
        frozen = validate_frozen_cp127_surfaces(repo)
        print(f'       Frozen CP127 implementation/research files verified: {frozen}.')
        print('       Validating zero numerical/operational drift and corrected movement metadata...')
        validate_matrix(repo)
        print('       Validating current Tech Table, workbook, canonical authority, Concept, and documentation...')
        validate_table_and_workbook(repo)
        validate_concept_and_docs(repo)
        print('       Validating curated predecessor evidence and repository packaging limits...')
        validate_evidence_retention(repo)
        print('       CP128 preflight: accepted CP127 main-subsystem values frozen; 0 numerical leaves changed; current movement prose synchronized; CP125/126/127 evidence provenance preserved without large recursive raw-results ZIPs; no new Monte Carlo study; most AUX tuning remains deferred.')
        return 0
    except Exception as exc:
        print(f'CP128 preflight failure: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
