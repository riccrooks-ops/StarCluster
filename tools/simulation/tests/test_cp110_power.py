from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from starcluster_research.power_calibration import (
    branch_hotspot,
    demand_vector,
    enumerate_loadouts,
    load_json,
    reactor_catalog,
    representative_loadouts,
    sample_turn_demand,
    standard_reactor,
    validate_study,
    _pareto_frontier,
    _expected_capped_binomial_uses,
)
from starcluster_research.rng import XorShift64, derive_seed


REPO = Path(__file__).resolve().parents[3]
MATRIX_PATH = REPO / "docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_1.json"
STUDY_PATH = REPO / "docs/archive/testing/pre-cp165-active/power_reactor_calibration_study_v0_1.json"


class Checkpoint110PowerCalibrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = load_json(MATRIX_PATH)
        cls.study = load_json(STUDY_PATH)

    def test_study_contract_is_valid(self):
        self.assertEqual([], validate_study(self.study))
        self.assertFalse(self.study["interpretationPolicy"]["automaticPromotion"])
        self.assertTrue(self.study["interpretationPolicy"]["noRequiredFullSimultaneousDemandCoverage"])

    def test_reactor_catalog_and_family_frontiers(self):
        reactors = reactor_catalog(self.matrix)
        self.assertEqual(11, len(reactors))
        frontier2 = {x.id for x in _pareto_frontier(reactors, 2)}
        self.assertTrue({"reactor-tl1", "reactor-tl2"}.issubset(frontier2))
        frontier5 = {x.id for x in _pareto_frontier(reactors, 5)}
        self.assertIn("reactor-tl4", frontier5)
        self.assertIn("reactor-tl5", frontier5)
        self.assertIn("power-fission-revival-tl5", frontier5)
        frontier8 = {x.id for x in _pareto_frontier(reactors, 8)}
        self.assertIn("reactor-tl7", frontier8)
        self.assertIn("reactor-tl8", frontier8)
        self.assertIn("power-fission-revival-tl7", frontier8)

    def test_exact_legal_build_counts(self):
        expected = {1: 294, 2: 294, 3: 609, 4: 843, 5: 1140, 6: 2730, 7: 4032, 8: 4032, 9: 4032}
        actual = {}
        for tl in range(1, 10):
            reactor = standard_reactor(self.matrix, tl)
            actual[tl] = len(enumerate_loadouts(self.matrix, tl, reactor, self.study["maxPdsBatteries"]))
        self.assertEqual(expected, actual)

    def test_branch_hotspots_preserve_power_pressure(self):
        for tl in range(1, 10):
            reactor = standard_reactor(self.matrix, tl)
            hotspot = branch_hotspot(self.matrix, tl, reactor, self.study["maxPdsBatteries"])
            self.assertGreater(hotspot["maximum_full_demand"], reactor.operational, f"TL{tl}")
            self.assertGreater(hotspot["examined_legal_branch_combinations"], 0, f"TL{tl}")

    def test_representative_selection_is_nonempty_and_bounded(self):
        for tl in range(1, 10):
            reactor = standard_reactor(self.matrix, tl)
            rows = enumerate_loadouts(self.matrix, tl, reactor, self.study["maxPdsBatteries"])
            reps = representative_loadouts(self.matrix, rows)
            self.assertGreaterEqual(len(reps), 6, f"TL{tl}")
            self.assertLessEqual(len(reps), 8, f"TL{tl}")
            for _name, loadout in reps:
                self.assertLessEqual(loadout.used_space, loadout.capacity)
                self.assertGreaterEqual(demand_vector(self.matrix, loadout).full, demand_vector(self.matrix, loadout).routine)


    def test_safe_overload_closed_form_bounds(self):
        self.assertEqual(0.0, _expected_capped_binomial_uses(20, 0.0, 2))
        self.assertEqual(2.0, _expected_capped_binomial_uses(20, 1.0, 2))
        mid = _expected_capped_binomial_uses(20, 0.10, 2)
        self.assertGreater(mid, 0.0)
        self.assertLess(mid, 2.0)

    def test_turn_demand_rng_is_reproducible(self):
        reactor = standard_reactor(self.matrix, 6)
        rows = enumerate_loadouts(self.matrix, 6, reactor, self.study["maxPdsBatteries"])
        name, loadout = representative_loadouts(self.matrix, rows)[0]
        seed = derive_seed(self.study["masterSeed"], "test-cp110", 6, name)
        a = XorShift64(seed)
        b = XorShift64(seed)
        seq_a = [sample_turn_demand(self.matrix, loadout, "mixed", a) for _ in range(100)]
        seq_b = [sample_turn_demand(self.matrix, loadout, "mixed", b) for _ in range(100)]
        self.assertEqual(seq_a, seq_b)

    def test_study_rejects_automatic_promotion_and_wrong_limits(self):
        bad = json.loads(json.dumps(self.study))
        bad["reactorCountMaximum"] = 3
        self.assertTrue(validate_study(bad))
        bad = json.loads(json.dumps(self.study))
        bad["doctrines"] = ["offense"]
        self.assertTrue(validate_study(bad))


if __name__ == "__main__":
    unittest.main()
