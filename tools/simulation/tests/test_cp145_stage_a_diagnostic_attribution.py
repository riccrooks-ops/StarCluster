from __future__ import annotations

import hashlib
import sys
import unittest
from dataclasses import replace
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SIM = REPO / "tools" / "simulation"
if str(SIM) not in sys.path:
    sys.path.insert(0, str(SIM))

from starcluster_research.canonical_combat import run_trial_full_map
from starcluster_research.combat_surface_deep_reconciliation import build_deep_resource_matrix
from starcluster_research.stage_a_diagnostic_attribution import (
    DIAGNOSTIC_TRIALS_PER_SCENARIO,
    EXPECTED_DIAGNOSTIC_SCENARIOS,
    EXPECTED_DIAGNOSTIC_TRIALS,
    EXPECTED_PDS_SCENARIOS,
    EXPECTED_TP_SCENARIOS,
    _accepted_analyses,
    _accepted_surfaces,
    _diag_task,
    _worker_init,
    validate_population,
    validate_study,
)
from starcluster_research.stage_a_integration_analysis import _read_csv, _resource_rows, bind_scenario
from starcluster_research.study import load_json

STUDY = REPO / "docs/archive/testing/pre-cp165-active/cp145_stage_a_diagnostic_attribution_study_v0_1.json"
MATRIX = REPO / "docs/design/player_technology/technology_numerical_matrix_v0_9.json"


class Cp145StageADiagnosticAttributionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = load_json(STUDY)
        cls.cp144 = load_json(REPO / cls.doc["stageAStudy"])
        cls.selection = _read_csv(REPO / cls.doc["diagnosticReplayManifest"])
        cls.stage = _read_csv(REPO / cls.doc["stageAExperimentManifest"])
        cls.stage_by_id = {r["scenario_id"]: r for r in cls.stage}
        cls.ensemble, cls.ensemble_tl = _resource_rows(REPO, cls.cp144)
        cls.accepted_rows, cls.accepted_pareto, cls.accepted_summary = _accepted_surfaces(REPO, cls.doc)
        cls.analyses = _accepted_analyses(cls.accepted_rows, cls.accepted_pareto)

    @classmethod
    def full_source(cls, selection_row):
        source = dict(cls.stage_by_id[selection_row["scenario_id"]])
        source.update(selection_row)
        return source

    def test_01_study_contract_is_exact_seed_and_zero_tuning(self):
        self.assertEqual([], validate_study(self.doc))
        self.assertEqual(145, self.doc["checkpoint"])
        self.assertEqual(144, self.doc["baseCheckpoint"])
        self.assertEqual(int(self.cp144["masterSeed"]), int(self.doc["masterSeed"]))
        self.assertEqual(140001, int(self.doc["masterSeed"]))
        self.assertEqual(EXPECTED_DIAGNOSTIC_SCENARIOS, self.doc["expectedDiagnosticScenarios"])
        self.assertEqual(DIAGNOSTIC_TRIALS_PER_SCENARIO, self.doc["diagnosticTrialsPerScenario"])
        self.assertEqual(EXPECTED_DIAGNOSTIC_TRIALS, self.doc["diagnosticCombatTrials"])
        self.assertFalse(self.doc["tuningAllowed"])
        self.assertFalse(self.doc["automaticPromotion"])
        self.assertFalse(self.doc["stageBAutomatic"])

    def test_02_replay_manifest_is_exact_unique_and_bound_to_cp144_identities(self):
        self.assertEqual([], validate_population(REPO, self.doc))
        self.assertEqual(EXPECTED_DIAGNOSTIC_SCENARIOS, len(self.selection))
        self.assertEqual(EXPECTED_DIAGNOSTIC_SCENARIOS, len({r["scenario_id"] for r in self.selection}))
        self.assertEqual(EXPECTED_PDS_SCENARIOS, sum(r["diagnostic_family"] == "PDS_OPPORTUNITY" for r in self.selection))
        self.assertEqual(EXPECTED_TP_SCENARIOS, sum(r["diagnostic_family"] == "TP_STARVATION" for r in self.selection))
        for r in self.selection:
            source = self.stage_by_id[r["scenario_id"]]
            for field in ("tl", "side_a_weapon", "side_b_weapon", "resource_ensemble_id", "scenario_stratum"):
                self.assertEqual(source[field], r[field])

    def test_03_accepted_cp144_tables_are_hash_locked_and_complete(self):
        self.assertEqual(6850, len(self.accepted_rows))
        self.assertEqual(3425000, sum(int(r["trials"]) for r in self.accepted_rows))
        self.assertEqual(144, int(self.accepted_summary["checkpoint"]))
        self.assertTrue(self.accepted_summary["substantiveStageACompleted"])
        self.assertEqual(3425000, int(self.accepted_summary["substantiveCombatTrials"]))
        self.assertGreater(len(self.accepted_pareto), 1000)

    def test_04_original_pareto_objectives_are_empirically_redundant(self):
        diag = self.analyses["pareto_objective_diagnostics"]
        wf = next(r for r in diag if r["objective_x"] == "win_rate" and r["objective_y"] == "fast_win_rate")
        self.assertGreater(float(wf["pearson_correlation"]), 0.99)

    def test_05_strategic_viability_adds_resource_endurance_and_pacing_dimensions(self):
        rows = self.analyses["strategic_viability_surface"]
        self.assertEqual(35, len(rows))
        for tl in range(1, 10):
            level = [r for r in rows if int(r["tl"]) == tl]
            self.assertTrue(any(int(r["strategic_pareto_viable"]) == 1 for r in level))
        required = {"mean_tp_fulfillment_rate", "mean_primary_ammo_exhausted_rate", "mean_duration_concern_rate", "p25_win_rate", "p90_win_rate", "worst_resource_mean_win_rate", "worst_stratum_mean_win_rate", "combat_pareto_viable", "resource_or_robustness_only_frontier"}
        self.assertTrue(required.issubset(rows[0]))
        self.assertTrue(any(int(r["resource_or_robustness_only_frontier"]) == 1 for r in rows))

    def test_06_kinetic_and_energy_attribution_surfaces_cover_full_tl_ladder(self):
        kinetic_tl = self.analyses["kinetic_tl_summary"]
        matched = self.analyses["kinetic_vs_energy_attribution"]
        matched_tl = self.analyses["kinetic_vs_energy_tl_summary"]
        energy = self.analyses["energy_resource_attribution"]
        self.assertEqual(list(range(1, 10)), sorted(int(r["tl"]) for r in kinetic_tl))
        self.assertEqual(350, len(matched))
        self.assertEqual(9, len(matched_tl))
        self.assertTrue(all("k_minus_e_win_rate" in r and "k_minus_e_direct_hull_conversion" in r for r in matched))
        self.assertEqual(45, len(energy))
        self.assertEqual(5, len({r["resource_ensemble_id"] for r in energy}))
        self.assertTrue(all("delta_win_rate_vs_r1" in r and "delta_tp_conflict_vs_r1" in r for r in energy))

    def test_07_accepted_pds_attribution_covers_family_resource_and_missile_crossing(self):
        pds = self.analyses["pds_baseline_attribution"]
        self.assertEqual(255, len(pds))
        self.assertEqual({"KineticPDS", "EnergyPDS", "AMM"}, {r["pds_family"] for r in pds})
        self.assertEqual(5, len({r["resource_ensemble_id"] for r in pds}))
        self.assertTrue(all(float(r["attempts_per_launch"]) >= 0.0 for r in pds))
        self.assertTrue(all(float(r["intercepts_per_attempt"]) >= 0.0 for r in pds))

    def test_08_turn_telemetry_exposes_requested_and_denied_tp_by_subsystem(self):
        sel = next(r for r in self.selection if r["diagnostic_family"] == "TP_STARVATION")
        source = self.full_source(sel)
        matrix = build_deep_resource_matrix(REPO, self.doc["matrix"], source["resource_ensemble_id"], self.ensemble, self.ensemble_tl)
        bound = bind_scenario(matrix, source)
        turns = []
        run_trial_full_map(matrix, replace(bound.variant, max_turns=60), int(self.cp144["masterSeed"]), 0, turn_telemetry_sink=turns, telemetry_context={"scenario_id": source["scenario_id"]})
        self.assertTrue(turns)
        for cat in ("weapon", "pds", "sensor", "ecm", "eccm", "shield", "armor", "damage_control"):
            self.assertIn(f"tp_requested_{cat}", turns[0])
            self.assertIn(f"tp_denied_{cat}", turns[0])
        self.assertIn("pds_threat_flag", turns[0])
        self.assertIn("pds_reaction_capacity_planned", turns[0])

    def test_09_pds_terminal_phase_records_opportunity_capacity_attempts_and_ammo(self):
        sel = next(r for r in self.selection if r["scenario_stratum"] == "ENERGY_PDS_PRESSURE" and r["resource_ensemble_id"] == "R1_CENTRAL_NO_MAJOR")
        source = self.full_source(sel)
        matrix = build_deep_resource_matrix(REPO, self.doc["matrix"], source["resource_ensemble_id"], self.ensemble, self.ensemble_tl)
        bound = bind_scenario(matrix, source)
        events = []
        run_trial_full_map(matrix, replace(bound.variant, max_turns=60), int(self.cp144["masterSeed"]), 0, event_sink=events)
        phases = [e for e in events if e.get("event") == "pds_terminal_phase"]
        self.assertTrue(phases)
        required = {"threat_flights", "configured_reaction_capacity", "planned_reaction_capacity", "reaction_attempts_used", "zero_attempt_flights", "one_attempt_flights", "two_attempt_flights", "unserved_attempt_opportunities", "pds_ammo_before", "pds_ammo_after"}
        self.assertTrue(required.issubset(phases[0]))
        for p in phases:
            self.assertLessEqual(int(p["planned_reaction_capacity"]), int(p["configured_reaction_capacity"]))
            self.assertLessEqual(int(p["reaction_attempts_used"]), int(p["planned_reaction_capacity"]))
            self.assertEqual(int(p["threat_flights"]), int(p["zero_attempt_flights"]) + int(p["one_attempt_flights"]) + int(p["two_attempt_flights"]))

    def test_10_observation_telemetry_is_outcome_neutral_for_same_seed_trial(self):
        sel = next(r for r in self.selection if r["scenario_stratum"] == "ENERGY_PDS_PRESSURE" and r["resource_ensemble_id"] == "R1_CENTRAL_NO_MAJOR")
        source = self.full_source(sel)
        matrix = build_deep_resource_matrix(REPO, self.doc["matrix"], source["resource_ensemble_id"], self.ensemble, self.ensemble_tl)
        bound = bind_scenario(matrix, source)
        variant = replace(bound.variant, max_turns=60)
        plain = run_trial_full_map(matrix, variant, int(self.cp144["masterSeed"]), 0)
        events, turns = [], []
        observed = run_trial_full_map(matrix, variant, int(self.cp144["masterSeed"]), 0, event_sink=events, turn_telemetry_sink=turns, telemetry_context={"scenario_id": source["scenario_id"]})
        self.assertEqual(plain, observed)
        self.assertTrue(events)
        self.assertTrue(turns)

    def test_11_diagnostic_worker_joins_full_cp144_source_and_aggregates_new_metrics(self):
        sel = next(r for r in self.selection if r["scenario_stratum"] == "ENERGY_PDS_PRESSURE" and r["resource_ensemble_id"] == "R1_CENTRAL_NO_MAJOR")
        source = self.full_source(sel)
        _worker_init(str(REPO), self.doc["matrix"], self.ensemble, self.ensemble_tl)
        out = _diag_task((source, 2, int(self.cp144["masterSeed"])))
        self.assertEqual(2, int(out["trials"]))
        self.assertEqual(0, int(out["error_trials"]))
        self.assertEqual(0, int(out["nonstandoff_open_orders"]))
        self.assertGreater(int(out["b_pds_threat_flights"]), 0)
        self.assertGreaterEqual(float(out["b_pds_attempts_per_threat_flight"]), 0.0)
        self.assertGreaterEqual(float(out["b_pds_configured_rc_per_phase"]), float(out["b_pds_planned_rc_per_phase"]))
        self.assertGreaterEqual(float(out["b_pds_rc_funding_ratio"]), 0.0)
        self.assertLessEqual(float(out["b_pds_rc_funding_ratio"]), 1.0)
        self.assertIn("b_pds_ammo_constrained_phase_rate", out)
        self.assertIn("b_tp_denied_pds_per_turn", out)

    def test_12_diagnostic_observation_does_not_modify_source_numerical_matrix(self):
        before = hashlib.sha256(MATRIX.read_bytes()).hexdigest()
        sel = next(r for r in self.selection if r["diagnostic_family"] == "TP_STARVATION")
        source = self.full_source(sel)
        _worker_init(str(REPO), self.doc["matrix"], self.ensemble, self.ensemble_tl)
        out = _diag_task((source, 1, int(self.cp144["masterSeed"])))
        self.assertEqual(0, int(out["error_trials"]))
        self.assertEqual(before, hashlib.sha256(MATRIX.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
