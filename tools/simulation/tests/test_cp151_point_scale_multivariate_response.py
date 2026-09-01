import hashlib
import itertools
import tempfile
import unittest
from collections import Counter
from pathlib import Path

import starcluster_research.point_scale_multivariate_response as ps
from starcluster_research.point_scale_multivariate_response import (
    EXPECTED_CANDIDATES_BY_TL,
    EXPECTED_CANDIDATE_CONTEXT_CELLS,
    EXPECTED_SMOKE_COMBATS,
    EXPECTED_SUBSTANTIVE_COMBATS,
    EXPECTED_TL_CANDIDATES,
    FACTORS,
    K_RESEARCH_DAMAGE_OLD_SCALE,
    _apply_exact_scale,
    _apply_research_candidate,
    _base_matrix,
    _candidate_codes_for_tl,
    _equivalence_worker_init,
    _eq_task,
    _oa_codes,
    _research_center_actual,
    active_factors,
    aux_scaling_audit,
    candidate_ledger,
    design_summary,
    run_batch,
    run_plan,
    validate_population,
    validate_study,
)
from starcluster_research.stage_a_integration_analysis import _read_csv
from starcluster_research.study import load_json


class Cp151PointScaleMultivariateResponseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = Path(__file__).resolve().parents[3]
        cls.study_path = cls.repo / 'docs/archive/testing/pre-cp165-active/cp151_point_scale_multivariate_response_v0_1.json'
        cls.doc = load_json(cls.study_path)
        cls.ledger = candidate_ledger(cls.repo, cls.doc)
        cls.central = _base_matrix(cls.repo, cls.doc, 'R1_CENTRAL_NO_MAJOR')

    def test_01_study_population_and_evidence_validate(self):
        self.assertEqual([], validate_study(self.doc))
        self.assertEqual([], validate_population(self.repo, self.doc))
        summary = load_json(self.repo / 'docs/validation/evidence/checkpoint-151/accepted-cp150/CP150_NATIVE_ACCEPTANCE_SUMMARY.json')
        self.assertEqual(150, int(summary['checkpoint']))
        self.assertEqual(20580000, int(summary['substantiveCombatTrials']))
        self.assertEqual(0, int(summary['substantiveErrorTrials']))

    def test_02_candidate_counts_and_full_compute_contract_are_exact(self):
        self.assertEqual({1:261,2:263,3:263,4:263,5:263,6:265,7:265,8:265,9:265}, EXPECTED_CANDIDATES_BY_TL)
        self.assertEqual(2373, EXPECTED_TL_CANDIDATES)
        self.assertEqual(EXPECTED_TL_CANDIDATES, len(self.ledger))
        self.assertEqual(1807050, EXPECTED_CANDIDATE_CONTEXT_CELLS)
        self.assertEqual(45176250, EXPECTED_SUBSTANTIVE_COMBATS)
        self.assertEqual(118650, EXPECTED_SMOKE_COMBATS)

    def test_03_oa243_is_strength_two_for_all_active_factor_pairs(self):
        for tl in (1, 2, 6, 9):
            names = active_factors(tl)
            rows = _oa_codes(names)
            self.assertEqual(243, len(rows))
            for f1, f2 in itertools.combinations(names, 2):
                counts = Counter((r[f1], r[f2]) for r in rows)
                self.assertEqual(set(itertools.product((-1,0,1), repeat=2)), set(counts))
                self.assertEqual({27}, set(counts.values()))

    def test_04_candidate_design_retains_every_unique_pure_axial_probe(self):
        for tl in range(1, 10):
            rows = _candidate_codes_for_tl(tl)
            for factor in active_factors(tl):
                for direction in (-1, 1):
                    matches = [r for r in rows if int(r[factor]) == direction and all(int(r[o]) == 0 for o in FACTORS if o != factor)]
                    self.assertEqual(1, len(matches), (tl, factor, direction))

    def test_05_k_research_center_is_cp150_damage_ladder_doubled(self):
        for tl in range(1, 10):
            c = _research_center_actual(self.central, tl)
            self.assertEqual(K_RESEARCH_DAMAGE_OLD_SCALE[tl] * 2, int(c['k_damage']))
        self.assertEqual([10,10,12,14,14,16,16,20,20], [_research_center_actual(self.central, tl)['k_damage'] for tl in range(1,10)])

    def test_06_core_point_factors_have_integer_minus_center_plus_one_resolution(self):
        for tl in range(1, 10):
            center = _research_center_actual(self.central, tl)
            rows = [r for r in self.ledger if int(r['tl']) == tl]
            for factor in active_factors(tl):
                vals = {int(r[f'candidate_{factor}']) for r in rows}
                expected = {int(center[factor])-1, int(center[factor]), int(center[factor])+1}
                self.assertTrue(expected.issubset(vals), (tl, factor, vals, expected))

    def test_07_exact_scaling_doubles_only_point_domain_and_preserves_penetration_def_res(self):
        m = _apply_exact_scale(self.central)
        for tl in range(1, 10):
            self.assertEqual(float(self.central.p('kinetic_main',tl)['damage'])*2, float(m.p('kinetic_main',tl)['damage']))
            self.assertEqual(float(self.central.p('hull',tl)['hullPoints'])*2, float(m.p('hull',tl)['hullPoints']))
            self.assertEqual(float(self.central.p('shield',tl)['capacity'])*2, float(m.p('shield',tl)['capacity']))
            self.assertEqual(float(self.central.p('armor',tl)['ai'])*2, float(m.p('armor',tl)['ai']))
            for profile, key in [('kinetic_main','accuracyPp'),('kinetic_main','apen'),('energy_main','spen'),('shield','defPp'),('armor','resPct')]:
                self.assertEqual(self.central.p(profile,tl).get(key), m.p(profile,tl).get(key), (tl,profile,key))

    def test_08_acc_def_res_tp_range_space_are_unchanged_by_research_candidate(self):
        c = next(r for r in self.ledger if int(r['tl']) == 8 and all(int(r[f'code_{f}']) == 0 for f in FACTORS))
        m = _apply_research_candidate(self.central, 8, c)
        for profile, keys in {
            'kinetic_main':('accuracyPp','tp','standardRange','maxRange','space'),
            'energy_main':('accuracyPp','tp','standardRange','maxRange','space'),
            'shield':('defPp','space'),
            'armor':('resPct','space'),
        }.items():
            for key in keys:
                self.assertEqual(self.central.p(profile,8).get(key), m.p(profile,8).get(key), (profile,key))

    def test_09_penetration_sweep_is_selective_and_never_creates_missile_penetration(self):
        for tl in range(1, 10):
            rows = [r for r in self.ledger if int(r['tl']) == tl]
            kc = int(_research_center_actual(self.central, tl)['k_apen']); ec = int(_research_center_actual(self.central, tl)['e_spen'])
            self.assertTrue({kc-1,kc,kc+1}.issubset({int(r['candidate_k_apen']) for r in rows}))
            self.assertTrue({ec-1,ec,ec+1}.issubset({int(r['candidate_e_spen']) for r in rows}))
            c = rows[-1]; m = _apply_research_candidate(self.central, tl, c)
            self.assertEqual(0, int(m.p('missile_gp_warhead',tl).get('apen',0))); self.assertEqual(0, int(m.p('missile_gp_warhead',tl).get('spen',0)))
            if tl >= 2:
                self.assertEqual(0, int(m.p('missile_swarmer',tl).get('apen',0))); self.assertEqual(0, int(m.p('missile_swarmer',tl).get('spen',0)))

    def test_10_shield_regen_and_late_armor_repair_are_one_two_three(self):
        for tl in range(1, 10):
            rows = [r for r in self.ledger if int(r['tl']) == tl]
            self.assertEqual({1,2,3}, {int(r['candidate_shield_regen']) for r in rows})
            armor = {r['candidate_armor_repair'] for r in rows}
            if tl < 6:
                self.assertEqual({0}, {int(x) for x in armor})
            else:
                self.assertEqual({1,2,3}, {int(x) for x in armor})

    def test_11_swarmer_equivalence_keeps_exact_float_while_research_is_integer(self):
        for tl in range(2, 10):
            center = _research_center_actual(self.central, tl)
            self.assertAlmostEqual(float(self.central.p('missile_swarmer',tl)['packetDamage'])*2, float(center['swarmer_exact_scaled_packet_damage']))
            self.assertIsInstance(center['swarmer_packet_damage'], int)
            self.assertLessEqual(abs(float(center['swarmer_packet_damage'])-float(center['swarmer_exact_scaled_packet_damage'])), 0.5)

    def test_12_crystalline_armor_scales_capacity_without_invented_regen(self):
        base_seed = next(x for x in self.central.doc['candidateBranchSeeds'] if x.get('id') == 'A_b1')['tl6']
        scaled = _apply_exact_scale(self.central)
        scaled_seed = next(x for x in scaled.doc['candidateBranchSeeds'] if x.get('id') == 'A_b1')['tl6']
        self.assertEqual(int(base_seed['ai'])*2, int(scaled_seed['ai']))
        self.assertEqual(base_seed.get('tacticalRegenerationPerTp',0), scaled_seed.get('tacticalRegenerationPerTp',0))

    def test_13_aux_audit_never_invents_unresolved_numeric_magnitudes(self):
        rows = aux_scaling_audit(self.repo)
        self.assertGreaterEqual(len(rows), 5)
        unresolved = [r for r in rows if 'TBD' in r['status']]
        self.assertTrue(unresolved)
        self.assertTrue(all(int(r['swept']) == 0 for r in unresolved))

    def test_14_plan_writes_full_45_17625m_contract(self):
        with tempfile.TemporaryDirectory() as td:
            s = run_plan(self.repo, self.study_path, Path(td))
        self.assertTrue(s['passed'])
        self.assertEqual(2373, int(s['tlCandidateCount']))
        self.assertEqual(1807050, int(s['candidateContextCells']))
        self.assertEqual(45176250, int(s['substantiveCombatTrials']))
        self.assertEqual(118650, int(s['smokeCombatTrials']))

    def test_15_representative_exact_x2_equivalence_is_same_seed_identical(self):
        _equivalence_worker_init(str(self.repo), self.doc)
        manifest = _read_csv(self.repo / self.doc['stageAExperimentManifest'])
        for i in (0, 449, 450, 3000, 6849):
            row = _eq_task((i, manifest[i], int(self.doc['equivalenceSeed'])))
            self.assertEqual(0, int(row['mismatch']), row)

    def test_16_tiny_live_multivariate_candidate_executes_without_error(self):
        with tempfile.TemporaryDirectory() as td:
            s = run_batch(self.repo, self.study_path, Path(td), jobs=1, tl=1, candidate_start=0, candidate_end=1, trials=1, smoke_panel=True)
        self.assertTrue(s['passed'])
        self.assertEqual(50, int(s['candidateContextCells']))
        self.assertEqual(50, int(s['combatTrials']))
        self.assertEqual(0, int(s['errors']))

    def test_17_source_numerical_matrix_is_unchanged_by_live_probe(self):
        p = self.repo / self.doc['matrix']; before = hashlib.sha256(p.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory() as td:
            run_batch(self.repo, self.study_path, Path(td), jobs=1, tl=6, candidate_start=0, candidate_end=1, trials=1, smoke_panel=True)
        self.assertEqual(before, hashlib.sha256(p.read_bytes()).hexdigest())

    def test_18_design_summary_covers_all_tl_no_promotion_and_wrapper_uses_shared_pythonpath(self):
        rows = design_summary(self.repo, self.doc)
        self.assertEqual(9, len(rows))
        self.assertEqual(EXPECTED_TL_CANDIDATES, sum(int(r['candidates']) for r in rows))
        self.assertTrue(all(int(r['promotion_allowed']) == 0 for r in self.ledger))
        wrapper = (self.repo / 'tools/checkpoints/checkpoint-151/apply_checkpoint_151.ps1').read_text(encoding='utf-8-sig')
        self.assertIn('point-scale-equivalence', wrapper)
        self.assertIn('point-scale-sweep', wrapper)
        self.assertIn('point-scale-merge', wrapper)
        self.assertIn('function Invoke-PythonWithSimulationPath', wrapper)
        self.assertIn('Invoke-PythonFocusedPattern $pattern', wrapper)


if __name__ == '__main__':
    unittest.main()
