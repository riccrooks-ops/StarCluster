from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SIM = REPO / "tools" / "simulation"
if str(SIM) not in sys.path:
    sys.path.insert(0, str(SIM))

from starcluster_research.canonical_combat import CANONICAL_COMBAT_KERNEL_VERSION
from starcluster_research.combat_surface_deep_reconciliation import build_deep_resource_matrix
from starcluster_research.stage_a_integration_analysis import _read_csv, _resource_rows, bind_scenario
from starcluster_research.study import load_json
from starcluster_research.whole_combat_stage_a_response_surface import (
    DEFAULT_TRIALS_PER_SCENARIO,
    EXPECTED_PAIRINGS,
    EXPECTED_RESOURCES,
    EXPECTED_SCENARIOS,
    EXPECTED_STRATA,
    EXPECTED_SUBSTANTIVE_TRIALS,
    _pairwise_symmetric,
    _pareto,
    run_smoke_batch,
    run_substantive_batch,
    validate_population,
    validate_study,
)

STUDY = REPO / "docs/archive/testing/pre-cp165-active/cp144_whole_combat_stage_a_response_surface_study_v0_1.json"
MATRIX = REPO / "docs/design/player_technology/technology_numerical_matrix_v0_9.json"


class Cp144WholeCombatStageAResponseSurfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = load_json(STUDY)
        cls.manifest = _read_csv(REPO / cls.doc["stageAExperimentManifest"])
        cls.ensemble, cls.ensemble_tl = _resource_rows(REPO, cls.doc)

    def test_01_study_contract_is_exact_and_non_promoting(self):
        self.assertEqual([], validate_study(self.doc))
        self.assertEqual("0.7", CANONICAL_COMBAT_KERNEL_VERSION)
        self.assertEqual(EXPECTED_SCENARIOS, self.doc["expectedStageAScenarios"])
        self.assertEqual(EXPECTED_RESOURCES, self.doc["expectedResourceEnvironments"])
        self.assertEqual(EXPECTED_STRATA, self.doc["expectedScenarioStrata"])
        self.assertEqual(EXPECTED_PAIRINGS, self.doc["expectedOrderedSameTlWeaponPairings"])
        self.assertEqual(DEFAULT_TRIALS_PER_SCENARIO, self.doc["substantiveTrialsPerScenario"])
        self.assertEqual(EXPECTED_SUBSTANTIVE_TRIALS, self.doc["substantiveCombatTrials"])
        self.assertFalse(self.doc["tuningAllowed"])
        self.assertFalse(self.doc["automaticPromotion"])
        self.assertFalse(self.doc["stageBAutomatic"])

    def test_02_population_collapses_r5_and_preserves_full_crossing(self):
        self.assertEqual([], validate_population(REPO, self.doc))
        self.assertEqual(EXPECTED_SCENARIOS, len(self.manifest))
        resources = {r["resource_ensemble_id"] for r in self.manifest}
        self.assertEqual(EXPECTED_RESOURCES, len(resources))
        self.assertNotIn("R5_CENTRAL_HIGH_DEMAND", resources)
        self.assertEqual(EXPECTED_STRATA, len({r["scenario_stratum"] for r in self.manifest}))
        self.assertEqual(
            EXPECTED_PAIRINGS,
            len({(int(r["tl"]), r["side_a_weapon"], r["side_b_weapon"]) for r in self.manifest}),
        )

    def test_03_five_resource_environments_have_distinct_executable_signatures(self):
        ids = sorted({r["ensemble_id"] for r in self.ensemble})
        self.assertEqual(EXPECTED_RESOURCES, len(ids))
        signatures = set()
        for eid in ids:
            matrix = build_deep_resource_matrix(REPO, self.doc["matrix"], eid, self.ensemble, self.ensemble_tl)
            sig = tuple(
                (
                    int(matrix.p("reactor", tl)["operationalTp"]),
                    int(matrix.p("kinetic_main", tl)["firingTp"]),
                    int(matrix.p("energy_main", tl)["standardTp"]),
                    int(matrix.p("missile_delivery", tl)["launchTp"]),
                    int(matrix.p("stl", tl)["space"]), int(matrix.p("ftl", tl)["space"]),
                )
                for tl in range(1, 10)
            )
            signatures.add(sig)
        self.assertEqual(EXPECTED_RESOURCES, len(signatures))

    def test_04_all_6850_cells_bind_legally_under_reconciled_matrix(self):
        mats = {
            eid: build_deep_resource_matrix(REPO, self.doc["matrix"], eid, self.ensemble, self.ensemble_tl)
            for eid in sorted({r["ensemble_id"] for r in self.ensemble})
        }
        for row in self.manifest:
            bound = bind_scenario(mats[row["resource_ensemble_id"]], row)
            self.assertLessEqual(bound.variant.side_a.combat_space, bound.variant.side_a.capacity)
            self.assertLessEqual(bound.variant.side_b.combat_space, bound.variant.side_b.capacity)

    def test_05_smoke_runner_exercises_turn_telemetry_and_forbids_nonstandoff_open(self):
        before = hashlib.sha256(MATRIX.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory() as td:
            summary = run_smoke_batch(REPO, STUDY, Path(td), jobs=1, batch_start=0, batch_end=3)
            rows = _read_csv(Path(td) / "whole_combat_smoke_results.csv")
        self.assertTrue(summary["passed"], summary)
        self.assertEqual(3, len(rows))
        self.assertTrue(all(int(r["turn_telemetry_coverage_pass"]) == 1 for r in rows))
        self.assertTrue(all(int(r["nonstandoff_open_orders"]) == 0 for r in rows))
        self.assertEqual(before, hashlib.sha256(MATRIX.read_bytes()).hexdigest())

    def test_06_substantive_runner_aggregates_multiple_trials_without_raw_turn_rows(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            summary = run_substantive_batch(REPO, STUDY, out, jobs=1, batch_start=0, batch_end=2, trials_per_scenario=3)
            rows = _read_csv(out / "scenario_response_surface.csv")
            self.assertTrue(summary["passed"], summary)
            self.assertEqual(6, summary["combatTrials"])
            self.assertEqual(2, len(rows))
            self.assertTrue(all(int(r["trials"]) == 3 for r in rows))
            self.assertTrue(all(int(r["error_trials"]) == 0 for r in rows))
            self.assertTrue(all(float(r["a_nonstandoff_open_orders_mean"]) == 0.0 for r in rows))
            self.assertFalse((out / "turn_telemetry.csv").exists())
            for field in ("a_win_rate", "gameplay_duration_concern_rate", "a_tp_conflict_turn_rate", "a_firm_track_turn_rate", "a_damage_advantage_mean"):
                self.assertIn(field, rows[0])

    def test_07_pairwise_symmetric_surface_removes_side_order_bias_explicitly(self):
        base = {
            "tl": "4", "resource_ensemble_id": "R1_CENTRAL_NO_MAJOR", "scenario_stratum": "BALANCED_CORE_NO_PDS",
            "trials": "100", "a_wins": "60", "b_wins": "40", "draws": "0", "a_win_rate": "0.60",
        }
        xy = dict(base, side_a_weapon="K", side_b_weapon="E")
        yx = dict(base, side_a_weapon="E", side_b_weapon="K", a_wins="45", b_wins="55", a_win_rate="0.45")
        out = _pairwise_symmetric([xy, yx])
        self.assertEqual(1, len(out))
        self.assertEqual(85, int(round(float(out[0]["weapon_x_win_rate"]) * int(out[0]["paired_trials"]))))
        self.assertAlmostEqual(0.05, float(out[0]["side_order_gap"]), places=12)

    def test_08_pareto_surface_retains_non_dominated_specialists(self):
        common = {
            "tl": "5", "resource_ensemble_id": "R1_CENTRAL_NO_MAJOR", "scenario_stratum": "BALANCED_CORE_NO_PDS",
            "side_b_weapon": "E", "trials": "100",
        }
        rows = [
            dict(common, side_a_weapon="K", a_win_rate="0.70", a_wins="70", b_wins="30", draws="0", a_fast_wins_under25="40", b_fast_wins_under25="20", a_damage_advantage_mean="1"),
            dict(common, side_a_weapon="E", a_win_rate="0.60", a_wins="60", b_wins="40", draws="0", a_fast_wins_under25="70", b_fast_wins_under25="20", a_damage_advantage_mean="2"),
            dict(common, side_a_weapon="M_GP", a_win_rate="0.50", a_wins="50", b_wins="50", draws="0", a_fast_wins_under25="30", b_fast_wins_under25="20", a_damage_advantage_mean="0"),
            dict(common, side_a_weapon="E", side_b_weapon="K", a_win_rate="0.30", a_wins="30", b_wins="70", draws="0", a_fast_wins_under25="20", b_fast_wins_under25="40", a_damage_advantage_mean="-1"),
            dict(common, side_a_weapon="E", side_b_weapon="M_GP", a_win_rate="0.50", a_wins="50", b_wins="50", draws="0", a_fast_wins_under25="20", b_fast_wins_under25="30", a_damage_advantage_mean="0"),
        ]
        detail, summary = _pareto(rows)
        context = [r for r in detail if r["opponent_weapon"] == "E"]
        viable = {r["candidate_weapon"] for r in context if int(r["pareto_viable"]) == 1}
        self.assertEqual({"K", "E"}, viable)
        self.assertTrue(all("side_symmetric_win_rate" in r for r in context))
        self.assertGreaterEqual(len(summary), 3)

    def test_09_substantive_aggregation_is_deterministic_for_same_seed_and_slice(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            sa = run_substantive_batch(REPO, STUDY, Path(a), jobs=1, batch_start=2, batch_end=4, trials_per_scenario=4)
            sb = run_substantive_batch(REPO, STUDY, Path(b), jobs=1, batch_start=2, batch_end=4, trials_per_scenario=4)
            self.assertTrue(sa["passed"] and sb["passed"])
            self.assertEqual(
                (Path(a) / "scenario_response_surface.csv").read_bytes(),
                (Path(b) / "scenario_response_surface.csv").read_bytes(),
            )


if __name__ == "__main__":
    unittest.main()
