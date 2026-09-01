import hashlib
import tempfile
import unittest
from pathlib import Path

from starcluster_research.kinetic_viable_region_refinement import (
    DEFAULT_TRIALS,
    EXPECTED_CANDIDATES_BY_TL,
    EXPECTED_CANDIDATE_CONTEXT_CELLS,
    EXPECTED_SMOKE_COMBATS,
    EXPECTED_SUBSTANTIVE_COMBATS,
    EXPECTED_TL_CANDIDATES,
    TL_REFINEMENT,
    _grid_rows_for_tl,
    candidate_ledger,
    refinement_design_summary,
    run_batch,
    run_plan,
    validate_population,
    validate_study,
)
from starcluster_research.study import load_json


class Cp150KineticViableRegionRefinementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = Path(__file__).resolve().parents[3]
        cls.study_path = cls.repo / 'docs/archive/testing/pre-cp165-active/cp150_kinetic_viable_region_refinement_v0_1.json'
        cls.doc = load_json(cls.study_path)
        cls.ledger = candidate_ledger(cls.repo, cls.doc)

    def test_01_study_and_population_validate(self):
        self.assertEqual([], validate_study(self.doc))
        self.assertEqual([], validate_population(self.repo, self.doc))

    def test_02_candidate_counts_are_exact_and_tl_specific(self):
        self.assertEqual(EXPECTED_TL_CANDIDATES, len(self.ledger))
        for tl, expected in EXPECTED_CANDIDATES_BY_TL.items():
            self.assertEqual(expected, sum(int(r['tl']) == tl for r in self.ledger))
            self.assertEqual(expected, len(_grid_rows_for_tl(tl)))

    def test_03_refinement_contains_missing_damage_plus_one_every_tl(self):
        for tl in range(1, 10):
            self.assertIn(1, {int(r['damage_delta']) for r in self.ledger if int(r['tl']) == tl})

    def test_04_accuracy_resolution_stops_at_energy_identity_ceiling(self):
        for r in self.ledger:
            self.assertLessEqual(int(r['candidate_accuracyPp']), int(r['central_energy_accuracyPp']))
        self.assertEqual({0, 2, 5}, set(TL_REFINEMENT[1]['accuracy']))
        self.assertEqual({0, 5, 10}, set(TL_REFINEMENT[2]['accuracy']))
        self.assertEqual({0, 5, 10}, set(TL_REFINEMENT[3]['accuracy']))

    def test_05_range_resolution_stops_at_energy_identity_ceiling(self):
        for r in self.ledger:
            self.assertLessEqual(int(r['candidate_standardRange']), int(r['central_energy_standardRange']))
            self.assertLessEqual(int(r['candidate_maxRange']), int(r['central_energy_maxRange']))

    def test_06_tl4_and_tl8_expand_damage_headroom(self):
        self.assertIn(3, set(TL_REFINEMENT[4]['damage']))
        self.assertIn(4, set(TL_REFINEMENT[8]['damage']))
        self.assertEqual(72, EXPECTED_CANDIDATES_BY_TL[4])
        self.assertEqual(45, EXPECTED_CANDIDATES_BY_TL[8])

    def test_07_cp149_nonbinding_factors_are_frozen(self):
        self.assertTrue(all(int(r['firing_tp_delta']) == 0 for r in self.ledger))
        self.assertTrue(all(int(r['ammo_level']) == 100 for r in self.ledger))
        self.assertTrue(all(int(r['candidate_spen']) == 0 for r in self.ledger))

    def test_08_all_candidates_preserve_identity_and_forbid_promotion(self):
        self.assertTrue(all(int(r['identity_preserved']) == 1 for r in self.ledger))
        self.assertTrue(all(int(r['promotion_allowed']) == 0 for r in self.ledger))
        self.assertTrue(any(int(r['identity_boundary_touch']) == 1 for r in self.ledger))

    def test_09_accepted_cp149_evidence_is_hash_locked_and_42_38m_complete(self):
        summary = load_json(self.repo / 'docs/validation/evidence/checkpoint-150/CP149_NATIVE_ACCEPTANCE_SUMMARY.json')
        self.assertEqual(149, int(summary['checkpoint']))
        self.assertEqual(42380000, int(summary['substantiveCombatTrials']))
        self.assertEqual(0, int(summary['substantiveErrorTrials']))

    def test_10_plan_declares_20_58m_substantive_combats(self):
        with tempfile.TemporaryDirectory() as td:
            s = run_plan(self.repo, self.study_path, Path(td))
        self.assertTrue(s['passed'])
        self.assertEqual(EXPECTED_CANDIDATE_CONTEXT_CELLS, int(s['candidateContextCells']))
        self.assertEqual(DEFAULT_TRIALS, int(s['trialsPerCandidateContext']))
        self.assertEqual(EXPECTED_SUBSTANTIVE_COMBATS, int(s['substantiveCombatTrials']))
        self.assertEqual(EXPECTED_SMOKE_COMBATS, int(s['smokeCombatTrials']))

    def test_11_design_summary_is_complete_and_identity_preserving(self):
        rows = refinement_design_summary(self.repo, self.doc)
        self.assertEqual(9, len(rows))
        self.assertTrue(all(int(r['identity_preserved']) == 1 for r in rows))
        self.assertEqual(EXPECTED_TL_CANDIDATES, sum(int(r['candidates']) for r in rows))

    def test_12_tl6_refinement_drops_flat_dimensions(self):
        rows = [r for r in self.ledger if int(r['tl']) == 6]
        self.assertEqual(4, len(rows))
        self.assertEqual({0, 1, 2, 3}, {int(r['damage_delta']) for r in rows})
        self.assertEqual({0}, {int(r['accuracy_delta_pp']) for r in rows})
        self.assertEqual({0}, {int(r['apen_delta']) for r in rows})
        self.assertEqual({'STD+0_EXT+0'}, {r['range_profile'] for r in rows})

    def test_13_tl5_retains_all_cp149_material_secondary_dimensions(self):
        rows = [r for r in self.ledger if int(r['tl']) == 5]
        self.assertEqual({0, 1, 2}, {int(r['damage_delta']) for r in rows})
        self.assertEqual({0, 2, 5}, {int(r['accuracy_delta_pp']) for r in rows})
        self.assertEqual({0, 1, 2}, {int(r['apen_delta']) for r in rows})
        self.assertEqual({'STD+0_EXT+0', 'STD+1_EXT+0', 'STD+0_EXT+1'}, {r['range_profile'] for r in rows})

    def test_14_tiny_live_refinement_context_executes_without_error(self):
        with tempfile.TemporaryDirectory() as td:
            s = run_batch(self.repo, self.study_path, Path(td), jobs=1, tl=1, candidate_start=0, candidate_end=1, trials=1, smoke_panel=True)
        self.assertTrue(s['passed'])
        self.assertEqual(20, int(s['candidateContextCells']))
        self.assertEqual(20, int(s['combatTrials']))
        self.assertEqual(0, int(s['errors']))

    def test_15_source_numerical_matrix_is_unchanged_by_probe(self):
        p = self.repo / self.doc['matrix']
        before = hashlib.sha256(p.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory() as td:
            run_batch(self.repo, self.study_path, Path(td), jobs=1, tl=6, candidate_start=0, candidate_end=1, trials=1, smoke_panel=True)
        self.assertEqual(before, hashlib.sha256(p.read_bytes()).hexdigest())

    def test_16_checkpoint_wrapper_runs_cp150_commands_and_preserves_py_path_helper(self):
        wrapper = (self.repo / 'tools/checkpoints/checkpoint-150/apply_checkpoint_150.ps1').read_text(encoding='utf-8-sig')
        self.assertIn('kinetic-viable-region-plan', wrapper)
        self.assertIn('kinetic-viable-region-sweep', wrapper)
        self.assertIn('kinetic-viable-region-merge', wrapper)
        self.assertIn('function Invoke-PythonWithSimulationPath', wrapper)
        self.assertIn('Invoke-PythonFocusedPattern $pattern', wrapper)


if __name__ == '__main__':
    unittest.main()
