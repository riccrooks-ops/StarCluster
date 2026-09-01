from __future__ import annotations

import csv
import hashlib
import json
import sys
import unittest
from dataclasses import asdict, replace
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SIM = REPO / "tools/simulation"
if str(SIM) not in sys.path:
    sys.path.insert(0, str(SIM))

from starcluster_research.canonical_combat import run_trial_full_map
from starcluster_research.stage_a_integration_analysis import (
    STAGE_A_SCENARIOS,
    _features_for_stratum,
    _instrumentation_equivalence_rows,
    _read_csv,
    _resource_rows,
    bind_scenario,
    build_resource_matrix,
    validate_study,
)
from starcluster_research.study import load_json

MATRIX = "docs/design/player_technology/technology_numerical_matrix_v0_9.json"
STUDY = REPO / "docs/archive/testing/pre-cp165-active/cp140_stage_a_integration_study_v0_1.json"


class Cp140StageAIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = load_json(STUDY)
        cls.manifest = _read_csv(REPO / cls.doc["stageAExperimentManifest"])
        cls.ensemble_rows, cls.tl_rows = _resource_rows(REPO, cls.doc)
        cls.ensemble_ids = sorted({r["ensemble_id"] for r in cls.ensemble_rows})
        cls.matrices = {
            eid: build_resource_matrix(REPO, MATRIX, eid, cls.ensemble_rows, cls.tl_rows)
            for eid in cls.ensemble_ids
        }

    def _row(self, *, ensemble: str | None = None, stratum: str | None = None,
             tl: int | None = None, a: str | None = None, b: str | None = None):
        for row in self.manifest:
            if ensemble is not None and row["resource_ensemble_id"] != ensemble: continue
            if stratum is not None and row["scenario_stratum"] != stratum: continue
            if tl is not None and int(row["tl"]) != tl: continue
            if a is not None and row["side_a_weapon"] != a: continue
            if b is not None and row["side_b_weapon"] != b: continue
            return row
        self.fail("requested Stage A row not found")

    def test_01_study_and_full_factor_crossing(self):
        self.assertEqual([], validate_study(self.doc))
        self.assertEqual(STAGE_A_SCENARIOS, len(self.manifest))
        self.assertEqual(STAGE_A_SCENARIOS, len({r["scenario_id"] for r in self.manifest}))
        self.assertEqual({500}, {int(r["planned_trials"]) for r in self.manifest})
        self.assertEqual({0}, {int(r["promotion_allowed"]) for r in self.manifest})
        by_resource = {eid: sum(r["resource_ensemble_id"] == eid for r in self.manifest) for eid in self.ensemble_ids}
        self.assertEqual({1370}, set(by_resource.values()))
        strata = sorted({r["scenario_stratum"] for r in self.manifest})
        self.assertEqual(10, len(strata))
        self.assertEqual({822}, {sum(r["scenario_stratum"] == s for r in self.manifest) for s in strata})
        pairing_keys = {(int(r["tl"]), r["side_a_weapon"], r["side_b_weapon"]) for r in self.manifest}
        self.assertEqual(137, len(pairing_keys))
        self.assertTrue(all(sum((int(r["tl"]), r["side_a_weapon"], r["side_b_weapon"]) == key for r in self.manifest) == 60 for key in pairing_keys))

    def test_02_all_8220_scenarios_bind_to_legal_exact_fill_builds(self):
        for row in self.manifest:
            bound = bind_scenario(self.matrices[row["resource_ensemble_id"]], row)
            self.assertEqual(bound.variant.side_a.capacity, bound.variant.side_a.used_space)
            self.assertEqual(bound.variant.side_b.capacity, bound.variant.side_b.used_space)
            self.assertLessEqual(bound.variant.side_a.combat_space, bound.variant.side_a.capacity)
            self.assertLessEqual(bound.variant.side_b.combat_space, bound.variant.side_b.capacity)

    def test_03_resource_control_binds_exact_tp_and_never_writes_source_matrix(self):
        p = REPO / MATRIX
        before = hashlib.sha256(p.read_bytes()).hexdigest()
        m = self.matrices["R0_CP138_HISTORICAL"]
        self.assertEqual(5, m.p("reactor", 1)["operationalTp"])
        self.assertEqual(3, m.p("reactor", 1)["degradedTp"])
        self.assertEqual(1, m.p("reactor", 1)["emergencyTp"])
        self.assertEqual(1, m.p("kinetic_main", 1)["firingTp"])
        self.assertEqual((1, 2, 3), (m.p("energy_main", 1)["lowTp"], m.p("energy_main", 1)["standardTp"], m.p("energy_main", 1)["overloadTp"]))
        self.assertEqual(0, m.p("missile_delivery", 1)["launchTp"])
        after = hashlib.sha256(p.read_bytes()).hexdigest()
        self.assertEqual(before, after)

    def test_04_central_candidate_binds_reactor_weapon_tp_and_space(self):
        m = self.matrices["R1_CENTRAL_NO_MAJOR"]
        self.assertEqual((5, 3, 1), (m.p("reactor", 1)["operationalTp"], m.p("reactor", 1)["degradedTp"], m.p("reactor", 1)["emergencyTp"]))
        self.assertEqual((13, 9, 5), (m.p("reactor", 9)["operationalTp"], m.p("reactor", 9)["degradedTp"], m.p("reactor", 9)["emergencyTp"]))
        self.assertEqual(6, m.p("kinetic_main", 9)["space"])
        self.assertEqual(6, m.p("energy_main", 9)["space"])
        self.assertEqual(6, m.p("missile_delivery", 9)["space"])
        # Selective_NoMajorMini freezes Reactor/STL/FTL at their TL1 footprint.
        for key in ("reactor", "stl", "ftl"):
            self.assertEqual({m.p(key, 1)["space"]}, {m.p(key, tl)["space"] for tl in range(1, 10)})
        # Energy Standard TP is authoritative from v22C; Low/Overload preserve the accepted 0.5x/1.5x ordering.
        self.assertEqual((2, 3, 5), (m.p("energy_main", 1)["lowTp"], m.p("energy_main", 1)["standardTp"], m.p("energy_main", 1)["overloadTp"]))
        self.assertEqual((3, 6, 9), (m.p("energy_main", 9)["lowTp"], m.p("energy_main", 9)["standardTp"], m.p("energy_main", 9)["overloadTp"]))

    def test_05_power_crisis_uses_real_installed_systems_not_fake_aux_tp(self):
        row = self._row(ensemble="R4_TIGHT_HIGH_DEMAND", stratum="POWER_CRISIS", tl=5, a="E", b="M_GP")
        bound = bind_scenario(self.matrices[row["resource_ensemble_id"]], row)
        for build in (bound.variant.side_a, bound.variant.side_b):
            self.assertTrue(build.ecm)
            self.assertTrue(build.eccm)
            self.assertEqual("AMM", build.pds_family)
            self.assertTrue(build.shield_hardener)
        self.assertEqual(3, bound.start_range)
        self.assertEqual("metadata_only_no_fake_tp_demand", bound.aux_proxy_binding)
        features = _features_for_stratum("POWER_CRISIS", 5)
        self.assertEqual((-2, 1), features["start"])

    def test_06_instrumentation_is_strictly_outcome_and_rng_neutral(self):
        rows = [bind_scenario(self.matrices[r["resource_ensemble_id"]], r) for r in self.manifest]
        audit = _instrumentation_equivalence_rows(self.matrices, rows, int(self.doc["masterSeed"]))
        self.assertEqual(12, len(audit))
        self.assertTrue(all(int(r["result_identical"]) == 1 for r in audit))
        self.assertTrue(all(not r["error_without"] and not r["error_with"] for r in audit))

    def test_07_default_and_standoff_start_geometry_execute(self):
        normal_row = self._row(ensemble="R0_CP138_HISTORICAL", stratum="BALANCED_CORE_NO_PDS", tl=5, a="K", b="E")
        normal = bind_scenario(self.matrices[normal_row["resource_ensemble_id"]], normal_row)
        self.assertEqual((-5, 5), (normal.variant.start_q_a, normal.variant.start_q_b))
        r0 = run_trial_full_map(self.matrices[normal_row["resource_ensemble_id"]], normal.variant, 140001, 71)
        self.assertFalse(r0.error)
        standoff_row = self._row(ensemble="R0_CP138_HISTORICAL", stratum="MOBILITY_STANDOFF", tl=5, a="K", b="E")
        standoff = bind_scenario(self.matrices[standoff_row["resource_ensemble_id"]], standoff_row)
        self.assertEqual((-3, 3), (standoff.variant.start_q_a, standoff.variant.start_q_b))
        self.assertEqual(6, standoff.start_range)
        r1 = run_trial_full_map(self.matrices[standoff_row["resource_ensemble_id"]], standoff.variant, 140001, 72)
        self.assertFalse(r1.error)

    def test_08_turn_telemetry_has_all_47_contract_fields_and_conflict_semantics(self):
        contract = load_json(REPO / self.doc["telemetryContract"])
        self.assertEqual(47, len(contract["turn_fields"]))
        row = self._row(ensemble="R4_TIGHT_HIGH_DEMAND", stratum="POWER_CRISIS", tl=5, a="E", b="M_GP")
        bound = bind_scenario(self.matrices[row["resource_ensemble_id"]], row)
        sink = []
        ctx = {"scenario_id": row["scenario_id"], "resource_ensemble_id": row["resource_ensemble_id"], "weapon_a": row["side_a_weapon"], "weapon_b": row["side_b_weapon"]}
        result = run_trial_full_map(self.matrices[row["resource_ensemble_id"]], bound.variant, 140001, 80, turn_telemetry_sink=sink, telemetry_context=ctx)
        self.assertFalse(result.error)
        self.assertEqual(2 * result.turns, len(sink))
        required = {x["field"] for x in contract["turn_fields"]}
        self.assertTrue(required.issubset(sink[0].keys()))
        for tr in sink:
            expected = int(int(tr["desirable_action_count"]) >= 2 and int(tr["tp_denied_total"]) > 0 and int(tr["tp_requested_total"]) > int(tr["reactor_tp_available"]) + int(tr["tp_overload"]))
            self.assertEqual(expected, int(tr["tp_conflict_flag"]))
            self.assertEqual(0, int(tr["aux_tp_supply"]))
            self.assertEqual(0, int(tr["tp_aux"]))

    def test_09_each_stratum_binds_expected_mechanical_signature(self):
        expected = {
            "BALANCED_CORE_NO_PDS": (10, 60, None, False, False, False),
            "KINETIC_PDS_PRESSURE": (10, 60, "Kinetic", False, False, False),
            "ENERGY_PDS_PRESSURE": (10, 60, "Energy", False, False, False),
            "AMM_PDS_PRESSURE": (10, 60, "AMM", False, False, False),
            "SHIELD_PRESSURE": (10, 60, None, False, False, True),
            "ARMOR_PRESSURE": (10, 60, None, False, False, False),
            "EW_CONTEST": (10, 60, None, True, True, False),
            "MOBILITY_STANDOFF": (6, 60, None, False, False, False),
            "RECOVERY_ATTRITION": (10, 90, None, False, False, True),
            "POWER_CRISIS": (3, 60, "AMM", True, True, True),
        }
        for stratum, sig in expected.items():
            row = self._row(ensemble="R1_CENTRAL_NO_MAJOR", stratum=stratum, tl=5, a="K", b="E")
            b = bind_scenario(self.matrices[row["resource_ensemble_id"]], row)
            got = (b.start_range, b.variant.max_turns, b.variant.side_a.pds_family, b.variant.side_a.ecm, b.variant.side_a.eccm, b.variant.side_a.shield_hardener)
            self.assertEqual(sig, got, stratum)
            if stratum == "ARMOR_PRESSURE":
                self.assertFalse(b.variant.side_a.shield)
            else:
                self.assertTrue(b.variant.side_a.shield)

    def test_10_high_aux_demand_axis_is_metadata_only_until_real_mechanics_exist(self):
        r1 = next(r for r in self.ensemble_rows if r["ensemble_id"] == "R1_CENTRAL_NO_MAJOR")
        r5 = next(r for r in self.ensemble_rows if r["ensemble_id"] == "R5_CENTRAL_HIGH_DEMAND")
        self.assertEqual("Moderate", r1["aux_proxy_profile"])
        self.assertEqual("ModerateHighDemand", r5["aux_proxy_profile"])
        m1, m5 = self.matrices[r1["ensemble_id"]], self.matrices[r5["ensemble_id"]]
        self.assertEqual("metadata_only_no_fake_tp_demand", m1.resource_aux_proxy_execution)
        self.assertEqual("metadata_only_no_fake_tp_demand", m5.resource_aux_proxy_execution)
        for tl in range(1, 10):
            for key in ("reactor", "kinetic_main", "energy_main", "missile_delivery", "stl", "ftl"):
                self.assertEqual(m1.p(key, tl), m5.p(key, tl), (tl, key))


if __name__ == "__main__":
    unittest.main()
