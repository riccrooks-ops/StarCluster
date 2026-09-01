from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SIM = REPO / "tools" / "simulation"
if str(SIM) not in sys.path:
    sys.path.insert(0, str(SIM))

from starcluster_research.canonical_combat import CombatBlackboard, _choose_order
from starcluster_research.combat_surface_deep_reconciliation import build_deep_resource_matrix
from starcluster_research.ecology import _create_side
from starcluster_research.stage_a_integration_analysis import _read_csv, _resource_rows, bind_scenario

FIXTURE = REPO / "docs/archive/testing/pre-cp165-active/cp144_engage_adaptive_policy_parity_fixtures_v0_1.json"
CP143_STUDY = REPO / "docs/archive/testing/pre-cp165-active/cp143_missile_mirror_pacing_attribution_study_v0_1.json"


class Cp144EngageAdaptivePolicyParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        doc = json.loads(CP143_STUDY.read_text(encoding="utf-8"))
        er, tr = _resource_rows(REPO, doc)
        cls.matrix = build_deep_resource_matrix(REPO, doc["matrix"], "R1_CENTRAL_NO_MAJOR", er, tr)
        manifest = _read_csv(REPO / doc["stageAExperimentManifest"])
        row = next(r for r in manifest if int(r["tl"]) == 1 and r["side_a_weapon"] == "M_GP" and r["resource_ensemble_id"] == "R1_CENTRAL_NO_MAJOR" and r["scenario_stratum"] == "BALANCED_CORE_NO_PDS")
        cls.bound = bind_scenario(cls.matrix, row)
        cls.side = _create_side(cls.matrix, cls.bound.variant.side_a, -5)
        cls.assert_range = int(cls.matrix.p("missile_delivery", 1)["range"])

    def test_01_fixture_uses_tl1_missile_outer_range(self):
        self.assertEqual(self.fixture["ownMaximumWeaponRange"], self.assert_range)

    def test_02_python_policy_matches_shared_csharp_fixture(self):
        order_map = {"Close": "Close", "Open": "Open", "MaintainPreferredRange": "MaintainPreferredRange"}
        for case in self.fixture["cases"]:
            with self.subTest(case=case["id"]):
                bb = CombatBlackboard(contact_established=True, contact_turn=1)
                if case["lastTrack"] is not None:
                    bb.last_track = case["lastTrack"]
                    bb.last_track_range = int(case["lastTrackRange"])
                if case["ownDemonstrated"] is not None:
                    bb.maximum_own_attack_range = int(case["ownDemonstrated"])
                if case["opponentDemonstrated"] is not None:
                    bb.maximum_observed_opponent_attack_range = int(case["opponentDemonstrated"])
                plan, reason = _choose_order(self.matrix, self.side, int(case["currentRange"]), bb)
                self.assertEqual(order_map[case["expectedOrder"]], plan.range_order.value)
                self.assertEqual(int(case["expectedDesiredRange"]), plan.desired_range)
                self.assertEqual(case["expectedPythonReasonClass"], reason)


if __name__ == "__main__":
    unittest.main()
