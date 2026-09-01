from __future__ import annotations

import csv
import hashlib
import json
import sys
import unittest
from dataclasses import replace
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SIM = REPO / "tools" / "simulation"
if str(SIM) not in sys.path:
    sys.path.insert(0, str(SIM))

from starcluster_research.canonical_combat import (
    CANONICAL_COMBAT_KERNEL_VERSION, FullMapMissile,
    _resolve_cp146_held_main_layer, run_trial_full_map,
)
from starcluster_research.combat_resource_doctrine import decide_contract_case
from starcluster_research.combat_resource_doctrine_validation import validate_population, validate_study
from starcluster_research.combat_surface_deep_reconciliation import build_deep_resource_matrix
from starcluster_research.ecology import (
    CONTEXTUAL_COMBAT_DOCTRINE, LEGACY_COMBAT_DOCTRINE, _create_side, _plan_once,
)
from starcluster_research.stage_a_diagnostic_attribution import _diag_task, _worker_init
from starcluster_research.rng import XorShift64
from starcluster_research.tactical_geometry import HexCoord
from starcluster_research.stage_a_integration_analysis import _read_csv, _resource_rows, bind_scenario
from starcluster_research.study import load_json

STUDY = REPO / "docs/archive/testing/pre-cp165-active/cp146_combat_resource_doctrine_study_v0_1.json"
FIXTURE = REPO / "docs/archive/testing/pre-cp165-active/cp146_combat_resource_doctrine_parity_fixtures_v0_1.json"


class Cp146CombatResourceDoctrineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = load_json(STUDY)
        cls.cp144 = load_json(REPO / cls.doc["stageAStudy"])
        cls.selection = _read_csv(REPO / cls.doc["diagnosticReplayManifest"])
        cls.stage = _read_csv(REPO / cls.doc["stageAExperimentManifest"])
        cls.stage_by_id = {r["scenario_id"]: r for r in cls.stage}
        cls.ensemble, cls.ensemble_tl = _resource_rows(REPO, cls.cp144)
        cls.accepted = _read_csv(REPO / cls.doc["acceptedCp145DiagnosticResults"])
        cls.accepted_by_id = {r["scenario_id"]: r for r in cls.accepted}

    @classmethod
    def full_source(cls, selection_row):
        source = dict(cls.stage_by_id[selection_row["scenario_id"]])
        source.update(selection_row)
        return source

    @classmethod
    def bound_from_selection(cls, pred):
        sel = next(r for r in cls.selection if pred(r))
        source = cls.full_source(sel)
        matrix = build_deep_resource_matrix(REPO, cls.doc["matrix"], source["resource_ensemble_id"], cls.ensemble, cls.ensemble_tl)
        return source, matrix, bind_scenario(matrix, source)

    def test_01_study_is_logic_only_and_hash_locked(self):
        self.assertEqual([], validate_study(self.doc))
        self.assertEqual([], validate_population(REPO, self.doc))
        self.assertFalse(self.doc["tuningAllowed"])
        self.assertFalse(self.doc["automaticPromotion"])
        self.assertFalse(self.doc["stageBAutomatic"])
        self.assertEqual(12600, self.doc["expectedTotalCombatTrials"])
        self.assertEqual(self.doc["matrixSha256"], hashlib.sha256((REPO/self.doc["matrix"]).read_bytes()).hexdigest())

    def test_02_shared_doctrine_fixture_matches_python_semantic_contract(self):
        fixture = load_json(FIXTURE)
        self.assertGreaterEqual(len(fixture["cases"]), 8)
        for case in fixture["cases"]:
            self.assertEqual(case["expected"], decide_contract_case(case), case["id"])

    def test_03_legacy_doctrine_remains_default_and_reproduces_one_accepted_cp145_row(self):
        sel = self.selection[0]; source = self.full_source(sel)
        _worker_init(str(REPO), self.doc["matrix"], self.ensemble, self.ensemble_tl)
        implicit = _diag_task((source, 25, int(self.doc["masterSeed"])))
        explicit = _diag_task((source, 25, int(self.doc["masterSeed"]), LEGACY_COMBAT_DOCTRINE))
        self.assertEqual(implicit, explicit)
        old = self.accepted_by_id[source["scenario_id"]]
        for key, value in old.items():
            if value == "": self.assertEqual("", str(explicit.get(key, "")))
            else:
                try: self.assertAlmostEqual(float(value), float(explicit[key]), places=12, msg=key)
                except ValueError: self.assertEqual(value, str(explicit[key]), key)

    def test_04_contextual_planner_does_not_inspect_hidden_weapon_family_while_unknown(self):
        source, matrix, bound = self.bound_from_selection(lambda r: r["side_b_weapon"] == "E" and r["resource_ensemble_id"] == "R1_CENTRAL_NO_MAJOR")
        own = _create_side(matrix, bound.variant.side_b, 0)
        target_e = _create_side(matrix, bound.variant.side_a, 1)
        target_k = _create_side(matrix, replace(bound.variant.side_a, weapon_family="Kinetic", missile_payload="GP"), 1)
        own.known_opponent_weapon_family = None
        pe = _plan_once(matrix, own, target_e, 2, 0, 8, False, CONTEXTUAL_COMBAT_DOCTRINE)
        pk = _plan_once(matrix, own, target_k, 2, 0, 8, False, CONTEXTUAL_COMBAT_DOCTRINE)
        keys = ("sensor_mode","sensor_cost","pds_power","pds_rc","pds_reason","hardener_active","hardener_reason","ecm_on","eccm_on","weapon_plans","weapon_actions")
        self.assertEqual({k:pe[k] for k in keys}, {k:pk[k] for k in keys})
        self.assertEqual("Unknown", pe["opponent_weapon_knowledge"])

    def test_05_known_non_missile_suppresses_pds_and_known_kinetic_suppresses_hardener(self):
        _, matrix, bound = self.bound_from_selection(lambda r: r["side_b_weapon"] == "E" and r["resource_ensemble_id"] == "R1_CENTRAL_NO_MAJOR")
        own_build = replace(bound.variant.side_b, pds_family="Energy", shield_hardener=True)
        own = _create_side(matrix, own_build, 0); target = _create_side(matrix, bound.variant.side_a, 1)
        own.known_opponent_weapon_family = "Kinetic"
        p = _plan_once(matrix, own, target, 2, 0, 10, False, CONTEXTUAL_COMBAT_DOCTRINE)
        self.assertEqual("KNOWN_NON_MISSILE", p["pds_reason"]); self.assertEqual(0, p["pds_power"])
        self.assertEqual("KNOWN_IRRELEVANT", p["hardener_reason"]); self.assertFalse(p["hardener_active"])

    def test_06_known_energy_keeps_hardener_relevant_but_pds_off(self):
        _, matrix, bound = self.bound_from_selection(lambda r: r["side_b_weapon"] == "E" and r["resource_ensemble_id"] == "R1_CENTRAL_NO_MAJOR")
        own = _create_side(matrix, replace(bound.variant.side_b, pds_family="Energy", shield_hardener=True), 0); target = _create_side(matrix, bound.variant.side_a, 1)
        own.known_opponent_weapon_family = "Energy"
        p = _plan_once(matrix, own, target, 2, 0, 10, False, CONTEXTUAL_COMBAT_DOCTRINE)
        self.assertEqual("KNOWN_ENERGY_THREAT", p["hardener_reason"]); self.assertTrue(p["hardener_active"])
        self.assertEqual("KNOWN_NON_MISSILE", p["pds_reason"]); self.assertEqual(0, p["pds_power"])

    def test_07_active_sensor_is_default_but_passive_can_preserve_main_weapon(self):
        _, matrix, bound = self.bound_from_selection(lambda r: r["side_b_weapon"] == "E" and r["resource_ensemble_id"] == "R1_CENTRAL_NO_MAJOR")
        own = _create_side(matrix, bound.variant.side_b, 0); target = _create_side(matrix, bound.variant.side_a, 1)
        high = _plan_once(matrix, own, target, 1, 0, 10, False, CONTEXTUAL_COMBAT_DOCTRINE)
        self.assertNotEqual("passive", high["sensor_mode"])
        low = _plan_once(matrix, own, target, 1, 0, 3, False, CONTEXTUAL_COMBAT_DOCTRINE)
        self.assertTrue(any(x is not None for x in low["weapon_plans"]))
        self.assertIn(low["sensor_mode"], {"passive","low","high"})

    def test_08_exhausted_finite_main_ammo_stops_drawing_weapon_power(self):
        _, matrix, bound = self.bound_from_selection(lambda r: r["side_a_weapon"] == "M_GP" and r["resource_ensemble_id"] == "R1_CENTRAL_NO_MAJOR")
        own = _create_side(matrix, bound.variant.side_a, 0); target = _create_side(matrix, bound.variant.side_b, 1)
        own.weapon_ammo = 0
        p = _plan_once(matrix, own, target, 1, 0, 10, False, CONTEXTUAL_COMBAT_DOCTRINE)
        self.assertFalse(p["weapon_has_ammo"]); self.assertFalse(p["weapon_core_opportunity"])
        self.assertTrue(all(x is None for x in p["weapon_plans"]))

    def test_09_exhausted_pds_ammo_stops_readiness_power(self):
        _, matrix, bound = self.bound_from_selection(lambda r: r["scenario_stratum"] == "KINETIC_PDS_PRESSURE" and r["side_b_weapon"] == "E")
        own = _create_side(matrix, bound.variant.side_b, 0); target = _create_side(matrix, bound.variant.side_a, 1)
        self.assertIsNotNone(own.pds_ammo); own.pds_ammo = 0; own.known_opponent_weapon_family = "Missile"; own.known_opponent_missile_profile = "GP"
        p = _plan_once(matrix, own, target, 1, 1, 10, False, CONTEXTUAL_COMBAT_DOCTRINE)
        self.assertFalse(p["pds_has_ammo"]); self.assertEqual(0, p["pds_power"]); self.assertEqual(0, p["pds_rc"])

    def test_10_single_main_stays_offensive_when_pds_capacity_is_funded(self):
        _, matrix, bound = self.bound_from_selection(lambda r: r["scenario_stratum"] == "ENERGY_PDS_PRESSURE" and r["side_b_weapon"] == "E" and r["resource_ensemble_id"] == "R1_CENTRAL_NO_MAJOR")
        own = _create_side(matrix, bound.variant.side_b, 0); target = _create_side(matrix, bound.variant.side_a, 1)
        own.known_opponent_weapon_family = "Missile"; own.known_opponent_missile_profile = "Swarmer"
        p = _plan_once(matrix, own, target, 1, 2, 10, False, CONTEXTUAL_COMBAT_DOCTRINE)
        self.assertGreater(p["pds_rc"], 0); self.assertEqual(["ship"], p["weapon_actions"])

    def test_11_single_main_preserves_legal_ship_attack_even_without_pds(self):
        _, matrix, bound = self.bound_from_selection(lambda r: r["side_b_weapon"] == "E" and r["resource_ensemble_id"] == "R1_CENTRAL_NO_MAJOR")
        own = _create_side(matrix, replace(bound.variant.side_b, pds_family=None), 0); target = _create_side(matrix, bound.variant.side_a, 1)
        own.known_opponent_weapon_family = "Missile"; own.known_opponent_missile_profile = "GP"
        p = _plan_once(matrix, own, target, 1, 1, 10, False, CONTEXTUAL_COMBAT_DOCTRINE)
        self.assertEqual(0, p["pds_rc"]); self.assertEqual(["ship"], p["weapon_actions"])

    def test_11b_k_or_e_main_holds_when_no_legal_ship_attack_and_pds_cannot_cover(self):
        _, matrix, bound = self.bound_from_selection(lambda r: r["side_b_weapon"] == "E" and r["resource_ensemble_id"] == "R1_CENTRAL_NO_MAJOR")
        own = _create_side(matrix, replace(bound.variant.side_b, pds_family=None), 0); target = _create_side(matrix, bound.variant.side_a, 1)
        own.known_opponent_weapon_family = "Missile"; own.known_opponent_missile_profile = "GP"
        weapon_range = int(matrix.weapon_profile("Energy", own.build.tl).get("maxRange", matrix.weapon_profile("Energy", own.build.tl).get("range")))
        p = _plan_once(matrix, own, target, weapon_range + 1, 1, 10, False, CONTEXTUAL_COMBAT_DOCTRINE)
        self.assertFalse(p["weapon_core_opportunity"]); self.assertIn("hold_missile", p["weapon_actions"])

    def test_11c_held_main_resolver_attempts_firm_tracked_missile_when_ship_fire_is_illegal(self):
        _, matrix, bound = self.bound_from_selection(lambda r: r["side_b_weapon"] == "E" and r["resource_ensemble_id"] == "R1_CENTRAL_NO_MAJOR")
        own = _create_side(matrix, replace(bound.variant.side_b, pds_family=None), 0)
        target = _create_side(matrix, bound.variant.side_a, 1)
        own.known_opponent_weapon_family = "Missile"
        own.known_opponent_missile_profile = "GP"
        weapon_range = int(matrix.weapon_profile("Energy", own.build.tl).get("maxRange", matrix.weapon_profile("Energy", own.build.tl).get("range")))
        plan = _plan_once(matrix, own, target, weapon_range + 1, 1, 10, False, CONTEXTUAL_COMBAT_DOCTRINE)
        self.assertIn("hold_missile", plan["weapon_actions"])

        target_coord = HexCoord(0, 0)
        missile = FullMapMissile(
            owner="A", target="B", coordinate=HexCoord(1, 0),
            last_target_coordinate=target_coord, damage=4.0, spen=0, apen=0,
            guidance=0, speed=1, maximum_travel=10, profile_id="GP",
            flight_id=9001, magazine_flight_id=9001, launch_turn=1,
        )
        terminal = [missile]
        in_flight = []
        events = []
        _resolve_cp146_held_main_layer(
            matrix, "B", own, plan, terminal, in_flight, target_coord,
            XorShift64(1), 2, events,
        )
        held_events = [e for e in events if e.get("event") == "held_main_interception"]
        self.assertEqual(1, own.telemetry.cp146_held_main_attempts)
        self.assertEqual(1, len(held_events))
        self.assertEqual("Firm", held_events[0]["missile_track"])
        self.assertEqual(9001, held_events[0]["magazine_flight_id"])
        self.assertLessEqual(int(held_events[0]["range"]), weapon_range)
        self.assertEqual(int(bool(held_events[0]["intercepted"])), own.telemetry.cp146_held_main_intercepts)
        self.assertEqual(1 - int(bool(held_events[0]["intercepted"])), len(terminal))

    def test_12_tl2_starvation_signature_is_improved_by_contextual_doctrine_without_number_change(self):
        sel = next(r for r in self.selection if r["diagnostic_family"] == "TP_STARVATION" and r["tl"] == "2" and r["scenario_stratum"] == "POWER_CRISIS")
        source = self.full_source(sel); matrix = build_deep_resource_matrix(REPO, self.doc["matrix"], source["resource_ensemble_id"], self.ensemble, self.ensemble_tl); bound = bind_scenario(matrix, source); v=replace(bound.variant,max_turns=60)
        legacy=run_trial_full_map(matrix,v,int(self.doc["masterSeed"]),0,combat_doctrine=LEGACY_COMBAT_DOCTRINE)
        contextual=run_trial_full_map(matrix,v,int(self.doc["masterSeed"]),0,combat_doctrine=CONTEXTUAL_COMBAT_DOCTRINE)
        self.assertTrue(legacy.unresolved); self.assertEqual(60,legacy.turns)
        self.assertFalse(contextual.unresolved); self.assertLess(contextual.turns,60)
        self.assertEqual(self.doc["matrixSha256"], hashlib.sha256((REPO/self.doc["matrix"]).read_bytes()).hexdigest())

    def test_13_capability_is_revealed_only_after_observable_attack(self):
        source, matrix, bound = self.bound_from_selection(lambda r: r["side_a_weapon"] == "M_GP" and r["side_b_weapon"] == "E" and r["resource_ensemble_id"] == "R1_CENTRAL_NO_MAJOR")
        events=[]; run_trial_full_map(matrix,replace(bound.variant,max_turns=20),int(self.doc["masterSeed"]),0,event_sink=events,combat_doctrine=CONTEXTUAL_COMBAT_DOCTRINE)
        reveals=[e for e in events if e.get("event")=="opponent_capability_revealed"]
        self.assertTrue(reveals)
        for reveal in reveals:
            source_event = "missile_launch" if reveal["source"]=="missile_launch" else "direct_fire"
            self.assertTrue(any(e.get("event")==source_event and int(e["turn"])==int(reveal["turn"]) for e in events))

    def test_14_pds_telemetry_distinguishes_magazine_flights_and_visible_subflights(self):
        source, matrix, bound = self.bound_from_selection(lambda r: r["side_a_weapon"] == "M_SWARMER" and r["scenario_stratum"] == "ENERGY_PDS_PRESSURE" and r["resource_ensemble_id"] == "R1_CENTRAL_NO_MAJOR")
        events=[]; run_trial_full_map(matrix,replace(bound.variant,max_turns=30),int(self.doc["masterSeed"]),0,event_sink=events,combat_doctrine=CONTEXTUAL_COMBAT_DOCTRINE)
        phases=[e for e in events if e.get("event")=="pds_terminal_phase" and e.get("target")=="B"]
        self.assertTrue(phases)
        required={"pds_visible_subflights","terminal_magazine_flights","magazine_flights_with_any_pds_attempt","magazine_flights_fully_covered","magazine_flights_partially_covered","subflights_with_0_attempts","subflights_with_1_attempt","subflights_with_2_attempts"}
        self.assertTrue(required.issubset(phases[0]))
        self.assertTrue(any(int(p["pds_visible_subflights"]) >= int(p["terminal_magazine_flights"]) for p in phases))

    def test_15_contextual_telemetry_does_not_label_out_of_range_turns_as_weapon_starvation(self):
        source, matrix, bound = self.bound_from_selection(lambda r: r["side_b_weapon"] == "E" and r["resource_ensemble_id"] == "R1_CENTRAL_NO_MAJOR")
        turns=[]; result=run_trial_full_map(matrix,replace(bound.variant,max_turns=1),int(self.doc["masterSeed"]),0,turn_telemetry_sink=turns,combat_doctrine=CONTEXTUAL_COMBAT_DOCTRINE)
        self.assertEqual(0,result.side_a.cp146_weapon_core_starved_turns + result.side_b.cp146_weapon_core_starved_turns)

    def test_16_kernel_version_marks_doctrine_and_held_main_semantic_change(self):
        self.assertEqual("0.7", CANONICAL_COMBAT_KERNEL_VERSION)


if __name__ == "__main__":
    unittest.main()
