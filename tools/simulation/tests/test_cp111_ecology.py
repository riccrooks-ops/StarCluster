from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from starcluster_research.ecology import (
    DAMAGE_MODEL,
    MAP_RADIUS,
    CandidateMatrix,
    EcologyVariant,
    _apply_damage,
    _create_side,
    _maybe_reactor_overload,
    _move_one,
    _plan_once,
    generate_primary_builds,
    generate_primary_variants,
    load_json,
    run_overload_instrumentation_probes,
    run_trial,
    validate_study,
)


REPO = Path(__file__).resolve().parents[3]
STUDY = REPO / "docs/archive/testing/pre-cp165-active/same_tl_build_ecology_instrumentation_study_v0_1.json"


class Checkpoint111SameTlEcologyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = CandidateMatrix(REPO)
        cls.builds = generate_primary_builds(cls.matrix)
        cls.by_id = {b.id: b for b in cls.builds}

    def test_study_contract_is_valid_and_damage_scope_is_explicit(self):
        study = load_json(STUDY)
        self.assertEqual([], validate_study(study))
        self.assertEqual("layered_defense_hull_only", study["damageModel"])
        self.assertFalse(study["internalDamageCriticalsSimulated"])
        self.assertEqual(DAMAGE_MODEL, study["damageModel"])

    def test_primary_population_has_twelve_exact_fill_builds_per_tl(self):
        self.assertEqual(108, len(self.builds))
        for tl in range(1, 10):
            rows = [b for b in self.builds if b.tl == tl]
            self.assertEqual(12, len(rows), f"TL{tl}")
            self.assertEqual({"Kinetic", "Energy", "Missile"}, {b.weapon_family for b in rows})
            for b in rows:
                self.assertEqual(b.capacity, b.used_space, b.id)
                self.assertGreaterEqual(b.mission_aux_space, 0, b.id)

    def test_same_tl_pairing_matrix_is_complete_and_mirrored(self):
        variants = generate_primary_variants(self.builds)
        self.assertEqual(1188, len(variants))
        keys = {}
        for v in variants:
            self.assertEqual(v.side_a.tl, v.side_b.tl)
            base = v.id.rsplit("-", 1)[0]
            keys.setdefault(base, set()).add(v.movement_order)
        self.assertEqual(594, len(keys))
        self.assertTrue(all(x == {"SideAFirst", "SideBFirst"} for x in keys.values()))

    def test_mixed_tl_population_is_registered_but_zero_weight(self):
        study = load_json(STUDY)
        mixed = study["mixedTlPopulation"]
        self.assertTrue(mixed["registered"])
        self.assertFalse(mixed["executed"])
        self.assertEqual(0, mixed["populationWeight"])

    def test_pds_readiness_is_reserved_against_known_missile_family(self):
        defender = _create_side(self.matrix, self.by_id["tl3-energy-defense-specialist"], -1)
        attacker = _create_side(self.matrix, self.by_id["tl3-missile-balanced"], 1)
        plan = _plan_once(self.matrix, defender, attacker, 2, inbound=0, available_power=7, opponent_ecm_on=False)
        self.assertTrue(plan["pds_threat"])
        self.assertGreater(plan["pds_rc"], 0)
        self.assertGreater(plan["pds_power"], 0)

    def test_terminal_missiles_receive_pds_window_even_when_fast(self):
        a = self.by_id["tl3-missile-balanced"]
        b = self.by_id["tl3-missile-missile-defense"]
        v = EcologyVariant("cp111-fast-terminal-pds", 3, a, b, "SideAFirst", population="test")
        total_launch = total_pds = total_terminal = 0
        for i in range(8):
            r = run_trial(self.matrix, v, 111002, i)
            self.assertEqual("", r.error)
            total_launch += r.side_a.missile_launches + r.side_b.missile_launches
            total_pds += r.side_a.pds_attempts + r.side_b.pds_attempts
            total_terminal += r.side_a.missile_terminal_arrivals + r.side_b.missile_terminal_arrivals
        self.assertGreater(total_launch, 0)
        self.assertGreater(total_terminal, 0)
        self.assertGreater(total_pds, 0)

    def test_damage_consumer_stops_at_layered_defense_and_hull(self):
        target = _create_side(self.matrix, self.by_id["tl1-energy-balanced"], 0)
        before_hull = target.hull
        result = _apply_damage(target, 20, 20, 20, 0, "direct")
        self.assertIn("hull", result)
        self.assertLess(target.hull, before_hull)
        self.assertFalse(any("critical" in name.lower() or "subsystem" in name.lower() for name in target.__dataclass_fields__))

    def test_movement_is_radius_bounded_and_fuel_accounted(self):
        side = _create_side(self.matrix, self.by_id["tl9-kinetic-balanced"], -MAP_RADIUS)
        target = _create_side(self.matrix, self.by_id["tl9-energy-balanced"], MAP_RADIUS)
        start_fuel = side.fuel
        _move_one(side, target, self.matrix, contact_before=True)
        self.assertGreaterEqual(side.q, -MAP_RADIUS)
        self.assertLessEqual(side.q, MAP_RADIUS)
        self.assertEqual(start_fuel - side.fuel, side.telemetry.movement_fuel)
        self.assertEqual(side.telemetry.movement_hexes * 2, side.telemetry.movement_fuel)


    def test_same_hex_burnthrough_prevents_permanent_matched_ecm_deadlock(self):
        side = _create_side(self.matrix, self.by_id["tl2-energy-dual-reactor"], 0)
        target = _create_side(self.matrix, self.by_id["tl2-kinetic-dual-reactor"], 0)
        plan = _plan_once(self.matrix, side, target, 0, inbound=0, available_power=14, opponent_ecm_on=True)
        self.assertEqual("Firm", plan["track"])
        self.assertTrue(plan["burnthrough_preserved"])

    def test_approximate_contact_drives_later_closure_instead_of_range_hold(self):
        side = _create_side(self.matrix, self.by_id["tl2-energy-dual-reactor"], -3)
        target = _create_side(self.matrix, self.by_id["tl2-kinetic-dual-reactor"], 3)
        side.contact = True
        side.last_track = "Approximate"
        old_range = abs(side.q - target.q)
        _move_one(side, target, self.matrix, contact_before=True)
        self.assertLess(abs(side.q - target.q), old_range)
        self.assertGreater(side.telemetry.track_driven_closure_hexes, 0)

    def test_shield_hardener_consumes_real_tactical_power(self):
        side = _create_side(self.matrix, self.by_id["tl3-energy-defense-specialist"], -1)
        target = _create_side(self.matrix, self.by_id["tl3-kinetic-balanced"], 1)
        plan = _plan_once(self.matrix, side, target, 2, inbound=0, available_power=7, opponent_ecm_on=False)
        self.assertTrue(plan["hardener_active"])
        self.assertEqual(1, plan["hardener_power"])

    def test_safe_reactor_overload_can_unlock_a_real_combat_action(self):
        side = _create_side(self.matrix, self.by_id["tl1-kinetic-balanced"], 0)
        target = _create_side(self.matrix, self.by_id["tl1-energy-balanced"], 1)
        plan, power = _maybe_reactor_overload(self.matrix, side, target, 1, inbound=0, base_power=0, opponent_ecm_hint=False)
        self.assertEqual(1, power)
        self.assertEqual(1, side.telemetry.reactor_overload_activations)
        self.assertGreaterEqual(sum(p is not None for p in plan["weapon_plans"]), 1)

    def test_zero_weight_overload_probes_cover_all_supported_paths(self):
        with tempfile.TemporaryDirectory() as td:
            result = run_overload_instrumentation_probes(REPO, Path(td))
            self.assertEqual(5, result["probes"])
            self.assertEqual(5, result["passed"])
            self.assertEqual([], result["failed"])
            self.assertTrue((Path(td) / "overload_instrumentation_probes.csv").is_file())


if __name__ == "__main__":
    unittest.main()
