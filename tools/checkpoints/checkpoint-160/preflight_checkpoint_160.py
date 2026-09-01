#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, hashlib, json, sys, unittest
from pathlib import Path

CP159_MAN = 'docs/validation/evidence/checkpoint-159/CP159_REPOSITORY_SHA256SUMS.txt'
CP159_MAN_SHA = 'df579e4de746568f328009d0d34d736e07042990af20f8298751d457bf758a2a'
PROD_SHA = '3088b0a9eb45f6bf505c24513e8bb2ac878819db4ab464ccfea330243c82f194'
CONCEPT_SHA = 'f76ca6ce488ccb5ad1352f7d38b8c3d4657c12ed64d0c93cc45d2db605cc632f'
PDS_SHA = '1a731834a3956267aacbdde030561df2cef18121d91860cfbef1c5e851c10c99'
PF3_SHA = '9158c44c6c66d84997696f3415612f1f3bba70960b738b0344ecb8e09062d8e2'
PF4_SHA = '7fd4dfbbe375586de2605361006db84b68f89767c76ba4b76da6cf5f48253155'
CP159_NATIVE_ARCHIVE_SHA = 'e7c17f3aeb6d6833620e8f8ca72694fdc4be589ef9791fb73e7cc0cfbe771a65'
ALLOWED_DRIFT = {
    'README.md', 'CHAT_README.md', 'docs/README.md', 'docs/Prototype_TODO.md',
    'docs/validation/README.md', 'docs/design/testing/README.md',
    'docs/design/player_technology/README.md',
    'docs/validation/Checkpoint_159_AUX_Pending_Finalization_Promotion_And_Specialist_Closure.md'
}


def req(value, message):
    if not value:
        raise AssertionError(message)


def sha(path: Path) -> str:
    h = hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()


def js(path: Path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def rows(path: Path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def manifest(path: Path):
    out = {}
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        if line.strip():
            h, rel = line.split('  ', 1); out[rel] = h
    return out


def count_suite(suite):
    return sum(count_suite(x) if isinstance(x, unittest.TestSuite) else 1 for x in suite)


def ps_balanced(path: Path) -> bool:
    text = path.read_text(encoding='utf-8-sig'); stack = []; pairs = {')':'(',']':'[','}':'{'}; state='normal'; i=0
    while i < len(text):
        ch = text[i]
        if state == 'comment':
            if ch == '\n': state = 'normal'
        elif state == 'single':
            if ch == "'":
                if i + 1 < len(text) and text[i+1] == "'": i += 1
                else: state = 'normal'
        elif state == 'double':
            if ch == '`': i += 1
            elif ch == '"': state = 'normal'
        else:
            if ch == '#': state = 'comment'
            elif ch == "'": state = 'single'
            elif ch == '"': state = 'double'
            elif ch in '([{': stack.append(ch)
            elif ch in ')]}':
                if not stack or stack[-1] != pairs[ch]: return False
                stack.pop()
        i += 1
    return state in ('normal','comment') and not stack


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--repo', required=True); args = ap.parse_args(); repo = Path(args.repo).resolve()
    try:
        definition = js(repo/'tools/checkpoints/checkpoint-160/checkpoint_160_definition.json')
        req(definition['checkpoint'] == 160 and definition['baseCheckpoint'] == 159, 'identity')
        req(definition['expectedPythonTests'] == 628 and definition['expectedPythonTestModules'] == 51, 'Python contract')
        req(definition['substantiveCombatTrials'] == 0 and definition['repairDroneMicroTrials'] == 0, 'zero-combat contract')
        req(not definition['tuningAllowed'] and not definition['automaticFinalProductionPromotion'], 'promotion boundary')
        req(definition['isolatedAuxMagnitudeArchitectureClosed'] and definition['poweredAuxTpCostsRemainProvisional'], 'AUX/Reactor boundary')

        wrapper = repo/'tools/checkpoints/checkpoint-160/apply_checkpoint_160.ps1'
        req(wrapper.is_file() and ps_balanced(wrapper), 'PowerShell delimiter/static parse guard')
        text = wrapper.read_text(encoding='utf-8-sig')
        req('tools\\simulation\\run_starcluster_research.py' in text and 'starcluster_research\\cli.py' not in text, 'package-safe parity entrypoint')

        req(sha(repo/'docs/design/player_technology/technology_numerical_matrix_v0_9.json') == PROD_SHA, 'production matrix drift')
        req(sha(repo/'docs/archive/concepts/Star_Cluster_Game_Concept_v0.7x.docx') == CONCEPT_SHA, 'Concept drift')
        req(sha(repo/'src/StarCluster.Core/Combat/Missiles/MissileInterceptionPhaseContext.cs') == PDS_SHA, 'production PDS drift')

        previous_manifest = repo/CP159_MAN
        req(previous_manifest.is_file() and sha(previous_manifest) == CP159_MAN_SHA, 'CP159 repository manifest drift')
        base = manifest(previous_manifest)
        for rel, expected in base.items():
            req((repo/rel).is_file(), f'missing CP159 file {rel}')
            if rel not in ALLOWED_DRIFT:
                req(sha(repo/rel) == expected, f'unexpected CP159 drift: {rel}')

        pf3 = repo/'docs/archive/player_technology/pre-cp165-active/technology_research_execution_baseline_pending_finalization_v0_3.json'
        pf4 = repo/'docs/design/player_technology/technology_research_execution_baseline_pending_finalization_v0_4.json'
        req(sha(pf3) == PF3_SHA and sha(pf4) == PF4_SHA, 'PF3/PF4 hash mismatch')
        a, b = js(pf3), js(pf4)
        req(a['profiles'] == b['profiles'] and a['branches'] == b['branches'] and a['candidateBranchSeeds'] == b['candidateBranchSeeds'], 'PF4 changed executable core')

        accepted = repo/'docs/validation/evidence/checkpoint-160/accepted-cp159'
        archive_hash_line=(accepted/'CP159_NATIVE_RESULTS_ARCHIVE_SHA256.txt').read_text(encoding='utf-8-sig').strip()
        req(archive_hash_line == CP159_NATIVE_ARCHIVE_SHA + '  StarCluster_CP159_native_results_20260830_143917.zip', 'CP159 native archive hash record drift')
        ns = js(accepted/'CP159_NATIVE_ACCEPTANCE_SUMMARY.json')
        req(ns['checkpoint'] == 159 and ns['pythonTestsPassed'] == 604 and ns['xunitPassed'] == 934, 'CP159 regression evidence')
        req(ns['substantiveCombatTrials'] == 3390000 and ns['repairDroneMicroTrials'] == 1728000, 'CP159 study scale evidence')
        req(ns['substantiveErrors'] == 0 and ns['substantiveTurnCapSentinels'] == 0, 'CP159 substantive evidence')

        bm = js(repo/'docs/validation/evidence/checkpoint-160/research_execution_baseline_manifest_v0_4.json')
        req(bm['baselineId'] == 'CP160-PF4' and bm['materializedMatrixSha256'] == PF4_SHA and not bm['productionAuthorityReplaced'], 'PF4 manifest')
        req(bm['isolatedAuxMagnitudeArchitectureClosed'] and bm['openDependencies'] == ['FINAL_REACTOR_TP_SCARCITY'], 'PF4 dependency boundary')

        sel = js(repo/'docs/validation/evidence/checkpoint-160/cp159_aux_closure_selection_evidence_v0_1.json')
        req(sel['fieldStabilizer']['selectedPackage'] == 'FST_HIGH', 'Field selection')
        req(sel['crystallineArmor']['selectedPackage'] == 'CRY_RISE_A', 'Crystalline selection')
        req(sel['repairDroneBay']['selectedKitRule'].startswith('additional prepared kit load equals'), 'Drone kit selection')
        req(abs(sel['fieldStabilizer']['meanUplift'] - 0.08440190904348747) < 1e-12, 'Field evidence mismatch')
        req(abs(sel['crystallineArmor']['meanUplift'] - 0.09093030812741487) < 1e-12, 'Crystalline evidence mismatch')

        sys.path.insert(0, str(repo/'tools/simulation'))
        from starcluster_research.research_execution_baseline_pf4 import load_research_execution_baseline_pf4, aux_profile
        matrix = load_research_execution_baseline_pf4(repo)
        req(int(matrix.p('kinetic_main',9)['damage']) == 20 and int(matrix.p('energy_main',9)['standardDamage']) == 18, 'main conformance')
        req(float(matrix.p('shield',9)['capacity']) == 32 and float(matrix.p('armor',9)['ai']) == 24, 'defense conformance')
        req([(t,aux_profile(repo,'fieldStabilizer',t)['spenReduction']) for t in (7,8,9)] == [(7,16),(8,18),(9,20)], 'Field trajectory')
        req([(t,aux_profile(repo,'crystallineArmor',t)['capacityBonus'],aux_profile(repo,'crystallineArmor',t)['resBonusPp']) for t in (8,9)] == [(8,8,15),(9,10,20)], 'Crystalline trajectory')
        for tl in range(2,10):
            drone = aux_profile(repo,'repairDroneBay',tl); dc = matrix.p('damage_control',tl)
            req(drone['additionalActionsPerPhase'] == 1 and drone['differentTargetRequired'] and not drone['sameTargetRerollAllowed'], f'Drone semantic TL{tl}')
            req(drone['additionalPreparedRepairKits'] == int(dc['preparedRepairKits']) and drone['droneAttemptTp'] == int(dc['attemptTp']), f'Drone resource TL{tl}')

        ledger = rows(repo/'docs/validation/evidence/checkpoint-160/aux_pending_finalization_promotion_ledger_v0_2.csv')
        req(len(ledger) == 10 and not any('OPEN' in r['status'] or 'BOUNDARY_SUPPORTED' in r['status'] for r in ledger), 'AUX ledger closure')
        conf = js(repo/'docs/validation/evidence/checkpoint-160/pf4_conformance_report_v0_1.json')
        req(conf['passed'] and conf['profilesUnchangedFromPf3'] and conf['substantiveCombatTrials'] == 0, 'PF4 conformance')

        tests = sorted((repo/'tools/simulation/tests').glob('test_*.py'))
        req(len(tests) == 51, f'Python modules {len(tests)}')
        suite = unittest.defaultTestLoader.discover(str(repo/'tools/simulation/tests'), pattern='test_*.py')
        req(count_suite(suite) == 628, f'Python tests {count_suite(suite)}')

        print('CP160 preflight PASS: accepted CP159 native evidence hash-locked; CP160-PF4 materialized; FST_HIGH, CRY_RISE_A, and distinct-target Repair Drone + full default kit load promoted; all isolated AUX magnitude/architecture questions closed; 628/51 Python tests discovered; zero substantive combats; production authority unchanged; final Reactor/TP scarcity remains open.')
        return 0
    except Exception as exc:
        print(f'CP160 preflight failure: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
