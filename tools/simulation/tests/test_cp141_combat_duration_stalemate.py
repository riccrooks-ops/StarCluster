from __future__ import annotations

import copy
import hashlib
import sys
import unittest
from dataclasses import replace
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SIM = REPO / "tools/simulation"
if str(SIM) not in sys.path:
    sys.path.insert(0, str(SIM))

from starcluster_research.canonical_combat import CANONICAL_COMBAT_KERNEL_VERSION, run_trial_full_map
from starcluster_research.combat_duration_stalemate_analysis import (
    HARD_TURN_SENTINEL,
    LONG_RESOLVED_TURN,
    _cap_diagnostic,
    validate_study,
)
from starcluster_research.stage_a_integration_analysis import _read_csv, _resource_rows, bind_scenario, build_resource_matrix
from starcluster_research.study import load_json

MATRIX = "docs/design/player_technology/technology_numerical_matrix_v0_9.json"
STUDY = REPO / "docs/archive/testing/pre-cp165-active/cp141_combat_duration_stalemate_study_v0_1.json"


class Cp141CombatDurationStalemateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = load_json(STUDY)
        cls.manifest = _read_csv(REPO / cls.doc["stageAExperimentManifest"])
        cls.ensemble_rows, cls.tl_rows = _resource_rows(REPO, cls.doc)
        cls.matrices = {
            eid: build_resource_matrix(REPO, MATRIX, eid, cls.ensemble_rows, cls.tl_rows)
            for eid in sorted({r["ensemble_id"] for r in cls.ensemble_rows})
        }
        cls.by_id = {r["scenario_id"]: r for r in cls.manifest}

    def _run(self, scenario_id: str, *, matrix=None, max_turns: int = HARD_TURN_SENTINEL):
        row = self.by_id[scenario_id]
        matrix = matrix or self.matrices[row["resource_ensemble_id"]]
        bound = bind_scenario(matrix, row)
        turns = []
        ctx = {"scenario_id":row["scenario_id"],"resource_ensemble_id":row["resource_ensemble_id"],"weapon_a":row["side_a_weapon"],"weapon_b":row["side_b_weapon"]}
        result = run_trial_full_map(matrix, replace(bound.variant,max_turns=max_turns), int(self.doc["masterSeed"]), 0, turn_telemetry_sink=turns, telemetry_context=ctx)
        return row, result, turns

    def test_01_study_forbids_turn_cap_extension(self):
        self.assertEqual([], validate_study(self.doc))
        self.assertEqual(60, HARD_TURN_SENTINEL)
        self.assertEqual(25, LONG_RESOLVED_TURN)
        self.assertFalse(self.doc["extendTurnCap"])

    def test_02_cp141_standardizes_recovery_attrition_to_60_sentinel(self):
        recovery = next(r for r in self.manifest if r["scenario_stratum"] == "RECOVERY_ATTRITION")
        bound = bind_scenario(self.matrices[recovery["resource_ensemble_id"]], recovery)
        self.assertEqual(90, bound.variant.max_turns)  # frozen CP140 source binding
        self.assertEqual(60, replace(bound.variant,max_turns=HARD_TURN_SENTINEL).max_turns)  # CP141 measurement binding

    def test_03_mutual_finite_offense_exhaustion_terminates_conservatively(self):
        row = next(r for r in self.manifest if int(r["tl"]) == 1 and r["side_a_weapon"] == "K" and r["side_b_weapon"] == "K" and r["scenario_stratum"] == "BALANCED_CORE_NO_PDS")
        matrix = copy.deepcopy(self.matrices[row["resource_ensemble_id"]])
        matrix.p("kinetic_main",1)["ammo"] = 0
        bound = bind_scenario(matrix,row)
        result = run_trial_full_map(matrix,replace(bound.variant,max_turns=60),140001,0)
        self.assertEqual("STALEMATE_MUTUAL_OFFENSIVE_EXHAUSTION", result.termination_cause)
        self.assertTrue(result.unresolved)
        self.assertEqual(1,result.turns)
        self.assertEqual(0,result.final_missiles_in_flight)

    def test_04_one_live_energy_weapon_prevents_false_stalemate(self):
        row = next(r for r in self.manifest if int(r["tl"]) == 1 and r["side_a_weapon"] == "K" and r["side_b_weapon"] == "E" and r["scenario_stratum"] == "BALANCED_CORE_NO_PDS")
        matrix = copy.deepcopy(self.matrices[row["resource_ensemble_id"]])
        matrix.p("kinetic_main",1)["ammo"] = 0
        bound = bind_scenario(matrix,row)
        result = run_trial_full_map(matrix,replace(bound.variant,max_turns=60),140001,0)
        self.assertNotEqual("STALEMATE_MUTUAL_OFFENSIVE_EXHAUSTION",result.termination_cause)

    def test_05_pending_missiles_delay_mutual_exhaustion(self):
        row = next(r for r in self.manifest if int(r["tl"]) == 1 and r["side_a_weapon"] == "M_GP" and r["side_b_weapon"] == "M_GP" and r["scenario_stratum"] == "BALANCED_CORE_NO_PDS")
        matrix = copy.deepcopy(self.matrices[row["resource_ensemble_id"]])
        matrix.p("missile_delivery",1)["flights"] = 1
        bound = bind_scenario(matrix,row)
        close = replace(bound.variant,start_q_a=-2,start_q_b=2,max_turns=60)
        result = run_trial_full_map(matrix,close,140001,0)
        if result.termination_cause == "STALEMATE_MUTUAL_OFFENSIVE_EXHAUSTION":
            self.assertGreater(result.turns,1)
            self.assertEqual(0,result.final_missiles_in_flight)
        else:
            self.assertIn(result.termination_cause,{"SIDE_A_DESTROYED","SIDE_B_DESTROYED","MUTUAL_DESTRUCTION","TURN_CAP_SENTINEL"})

    def test_06_normal_destruction_has_explicit_termination_cause(self):
        _, result, _ = self._run("SCN-EC961B28AABB5FCC")
        self.assertFalse(result.error)
        self.assertIn(result.termination_cause,{"SIDE_A_DESTROYED","SIDE_B_DESTROYED","MUTUAL_DESTRUCTION"})
        self.assertFalse(result.unresolved)

    def test_07_known_cp140_cap_case_remains_60_turn_sentinel_not_auto_stalemate(self):
        _, result, turns = self._run("SCN-9C811ABA39DF0E72")
        self.assertEqual("TURN_CAP_SENTINEL",result.termination_cause)
        self.assertEqual(60,result.turns)
        self.assertEqual(120,len(turns))

    def test_08_known_cap_case_exposes_recovery_diagnostic_without_auto_termination(self):
        _, result, turns = self._run("SCN-636A2FCDF84D7F5B")
        self.assertEqual("TURN_CAP_SENTINEL",result.termination_cause)
        diag = _cap_diagnostic(result,turns)
        self.assertEqual("DEFENSIVE_RECOVERY_LOOP",diag["dominant_cap_signal"])
        self.assertGreater(diag["recovery_fraction_of_gross_damage"],0.75)

    def test_09_known_missile_duel_respects_duration_classification_after_policy_updates(self):
        _, result, _ = self._run("SCN-D6406D516940E479")
        self.assertFalse(result.unresolved)
        self.assertLessEqual(result.turns,HARD_TURN_SENTINEL)
        # This fixture was >=25 turns under the CP141 kernel. CP144 deliberately
        # closes the EngageAdaptive research-policy parity defect, so historical
        # duration is evidence, not a frozen current-kernel outcome.
        if CANONICAL_COMBAT_KERNEL_VERSION in {"0.5", "0.6", "0.7"}:
            self.assertLess(result.turns,LONG_RESOLVED_TURN)
        else:
            self.assertGreaterEqual(result.turns,LONG_RESOLVED_TURN)

    def test_10_duration_instrumentation_never_writes_source_matrix(self):
        path = REPO / MATRIX
        before = hashlib.sha256(path.read_bytes()).hexdigest()
        self._run("SCN-CC28A1D7C0707747")
        after = hashlib.sha256(path.read_bytes()).hexdigest()
        self.assertEqual(before,after)


if __name__ == "__main__":
    unittest.main()
