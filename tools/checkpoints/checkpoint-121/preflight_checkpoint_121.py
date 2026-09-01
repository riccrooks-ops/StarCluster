#!/usr/bin/env python3
from __future__ import annotations
import argparse, ast, csv, hashlib, json, subprocess, sys, tempfile, zipfile
from pathlib import Path


def req(v, msg):
    if not v:
        raise AssertionError(msg)


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


class TrialDependentFailureGateVisitor(ast.NodeVisitor):
    def __init__(self):
        self.bad = []

    def visit_If(self, node: ast.If):
        names = {n.id for n in ast.walk(node.test) if isinstance(n, ast.Name)}
        if {'trials', 'eq_trials'} & names:
            for n in ast.walk(ast.Module(body=node.body, type_ignores=[])):
                if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == 'append'
                        and isinstance(n.func.value, ast.Name) and n.func.value.id in {'failures', 'failed_gates'}):
                    self.bad.append((node.lineno, ast.unparse(node.test) if hasattr(ast, 'unparse') else 'trial-dependent'))
        self.generic_visit(node)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', required=True)
    a = ap.parse_args()
    repo = Path(a.repo).resolve()
    try:
        sys.path.insert(0, str(repo / 'tools/simulation'))
        from starcluster_research.damage_resolution_analysis import (
            DamageScaledMatrix, _equivalence_task, _init_equivalence_worker,
            build_halfstep_variants, validate_study,
        )
        from starcluster_research.ecology import CandidateMatrix
        from starcluster_research.study import load_json
        from starcluster_research.weapon_family_analysis import build_variants

        definition = json.loads((repo/'tools/checkpoints/checkpoint-121/checkpoint_121_definition.json').read_text())
        e = definition['expected']
        study = load_json(repo/'docs/archive/testing/pre-cp165-active/damage_resolution_scaling_study_v0_1.json')
        errs = validate_study(study)
        req(errs == [], f'CP121 study validation: {errs}')
        req(study['checkpoint'] == 121 and study['acceptedBaseline'] == 119 and study['supersedesCandidate'] == 120, 'study identity')
        req(study['damageScale'] == 2 and study['internalDamageCriticalsSimulated'] is False and study['automaticPromotion'] is False, 'scale/damage boundary')
        req(study['trialsPerVariant'] == e['nativeTrialsPerVariant'] and study['authoringTrialsPerVariant'] == e['authoringTrialsPerVariant'], 'half-step trial counts')
        req(study['equivalenceTrialsPerVariant'] == e['nativeEquivalenceTrialsPerVariant'] and study['authoringEquivalenceTrialsPerVariant'] == e['authoringEquivalenceTrialsPerVariant'], 'equivalence trial counts')

        analysis_path = repo/'tools/simulation/starcluster_research/damage_resolution_analysis.py'
        tree = ast.parse(analysis_path.read_text(encoding='utf-8'))
        visitor = TrialDependentFailureGateVisitor(); visitor.visit(tree)
        req(not visitor.bad, f'trial-count-dependent CP121 blocking gates: {visitor.bad}')

        builds, variants = build_halfstep_variants(repo, study)
        req(len(builds) == e['exactFillBuilds'] and all(b.used_space == b.capacity for b in builds), 'exact-fill build shape')
        req(len(variants) == e['studyVariants'], 'half-step variant count')
        groups = {}
        priorities = {'primary': 0, 'advanced': 0, 'endpoint': 0}
        for v in variants:
            groups[v.scenario_group] = groups.get(v.scenario_group, 0) + 1
            priorities['primary' if v.tl in (2,3,4,5,6) else ('advanced' if v.tl == 7 else 'endpoint')] += 1
        req(groups == {'energy_family_reference': e['energyVariants'], 'kinetic_family_characteristic': e['kineticVariants'], 'missile_family_characteristic': e['missileVariants']}, f'family shape {groups}')
        req(priorities == {'primary': e['primaryVariants'], 'advanced': e['advancedVariants'], 'endpoint': e['endpointVariants']}, f'priority shape {priorities}')

        source = load_json(repo/study['equivalenceSourceStudy'])
        _, source_variants = build_variants(repo, source)
        req(len(source_variants) == e['equivalenceVariants'], 'equivalence population count')
        _init_equivalence_worker(str(repo), source, 2)
        for group in ('missile_family_characteristic','kinetic_family_characteristic','energy_family_reference'):
            v = next(x for x in source_variants if x.scenario_group == group and x.tl == 5 and x.target_classification == 'legal_build')
            row = _equivalence_task((v, int(source['masterSeed']), 2))
            req(row['mismatched_trials'] == 0, f'representative equivalence failure {row}')

        legacy = CandidateMatrix(repo); scaled = DamageScaledMatrix(repo, 2)
        req(scaled.p('hull', 5)['hullPoints'] == legacy.p('hull', 5)['hullPoints'] * 2, 'Hull not doubled')
        req(scaled.p('shield', 5)['capacity'] == legacy.p('shield', 5)['capacity'] * 2, 'Shield capacity not doubled')
        req(scaled.p('armor', 5)['ap'] == legacy.p('armor', 5)['ap'] * 2, 'Armor Protection not doubled')
        req(scaled.p('kinetic_main', 5)['accuracyPp'] == legacy.p('kinetic_main', 5)['accuracyPp'], 'accuracy incorrectly scaled')
        req(scaled.p('reactor', 5)['operationalTp'] == legacy.p('reactor', 5)['operationalTp'], 'Tactical Power incorrectly scaled')

        correction_zip = repo/'docs/validation/evidence/checkpoint-121/CP120_NATIVE_RESULTS_ORIGINAL.zip'
        req(sha(correction_zip) == e['cp120NativeArchiveSha256'], 'preserved CP120 native archive SHA')
        with zipfile.ZipFile(correction_zip) as zf:
            member = 'checkpoint-120/native-weapon-sensitivity-study/variants.csv'
            req(member in zf.namelist(), 'CP120 native variants member missing')
            req(hashlib.sha256(zf.read(member)).hexdigest() == e['cp120NativeVariantsSha256'], 'CP120 variants member SHA')
        corr = json.loads((repo/'docs/validation/evidence/checkpoint-121/cp120-corrected/correction_summary.json').read_text())
        req(corr['sourceTrials'] == 8568000 and corr['sourceVariants'] == 4284 and corr['combatRerun'] is False, 'CP120 correction provenance')
        req(corr['correctedGuidanceComparisonRows'] == 14 and 0.095 <= corr['maxAbsCorrectedGuidanceHitDelta'] <= 0.105, 'CP120 corrected guidance signal')
        sensitivity = list(csv.DictReader((repo/'docs/validation/evidence/checkpoint-121/cp120-corrected/sensitivity_delta_summary.csv').open(newline='', encoding='utf-8-sig')))
        acc10 = [r for r in sensitivity if r['axis'] == 'swarmer_accuracy' and 'acc-10' in r['comparison_id']]
        req(len(acc10) == 6 and all(0.095 <= float(r['delta_missile_hit_per_guidance_attempt']) <= 0.105 for r in acc10), 'corrected +10 guidance rows')

        audit = json.loads((repo/'docs/archive/testing/pre-cp165-active/damage_domain_scaling_audit_v0_1.json').read_text())
        ids = {x['id'] for x in audit['canonicalAdoptionConsumers']}
        req({'hx-cadence','damage-control-hull-repair','degraded-energy-damage-rounding','natural-100-point-bonuses'} <= ids, 'scaling adoption audit incomplete')
        req(audit['cp121Boundary']['researchHullScaled'] is True and audit['cp121Boundary']['internalCriticalsSimulated'] is False, 'audit boundary drift')

        cli = (repo/'tools/simulation/starcluster_research/cli.py').read_text(encoding='utf-8')
        req("add_parser('damage-resolution-study')" in cli and "args.cmd=='damage-resolution-study'" in cli and '--equivalence-trials' in cli, 'CLI route missing')
        helper = repo/'tools/checkpoints/checkpoint-121/reanalyze_cp120_native.py'
        helper_probe = subprocess.run([sys.executable, '-B', str(helper), '--help'], cwd=repo, capture_output=True, text=True)
        req(helper_probe.returncode == 0 and '--source-zip' in helper_probe.stdout, f'standalone CP120 reanalysis helper import/CLI failed: {helper_probe.stderr.strip()}')
        helper_text = helper.read_text(encoding='utf-8')
        req("correction_summary.json').write_bytes" in helper_text, 'CP120 correction summary must use canonical byte output, not platform-translated text newlines')
        with tempfile.TemporaryDirectory(prefix='starcluster-cp121-correction-preflight-') as tmp:
            generated = Path(tmp) / 'corrected'
            repro = subprocess.run(
                [sys.executable, '-B', str(helper), '--repo', str(repo), '--source-zip', str(correction_zip), '--output-dir', str(generated)],
                cwd=repo, capture_output=True, text=True
            )
            req(repro.returncode == 0, f'CP120 correction reproducibility preflight failed: {repro.stderr.strip()}')
            checked = repo/'docs/validation/evidence/checkpoint-121/cp120-corrected'
            reproducible_names = ('correction_summary.json','integration_summary.csv','sensitivity_delta_summary.csv','swarmer_sensitivity.csv','pds_isolation_summary.csv')
            for name in reproducible_names:
                req(sha(generated/name) == sha(checked/name), f'CP120 corrected output is not byte-reproducible on this platform: {name}')

        wrapper = (repo/'tools/checkpoints/checkpoint-121/apply_checkpoint_121.ps1')
        if wrapper.exists():
            wt = wrapper.read_text(encoding='utf-8-sig')
            for token in ("'--trials','2000'", "'--equivalence-trials','20'", '4848000', '85680', 'reanalyze_cp120_native.py'):
                req(token in wt, f'wrapper missing {token}')

        print('       CP121 preflight: CP120 telemetry provenance verified; 4,284-variant exact x2 equivalence population; 2,424 half-step variants; Hull/Shield/Armor/weapon point domains scaled; non-point domains held; critical-adoption audit present.')
        return 0
    except Exception as exc:
        print(f'CP121 preflight failure: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
