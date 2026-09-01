import math
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools/simulation"))

from starcluster_research.canonical_mechanics import (
    DIRECT_FIRE_APPROXIMATE_TRACK_PENALTY_PP,
    DIRECT_FIRE_EXTENDED_RANGE_PENALTY_PP,
    direct_fire_accuracy_modifier,
    energy_output_modes,
)
from starcluster_research.ecology import CandidateMatrix, EcologyBuild, _armor_profile, _apply_armor_regeneration, _begin_turn_recharge, _create_side, _hit_chance, build_space

MATRIX = "docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_6.json"


def build(tl=6, family="Energy", armor="mainline", pds=None):
    matrix = CandidateMatrix(REPO, MATRIX)
    cap = matrix.capacity(tl)
    combat = build_space(matrix, tl, "Missile" if family in ("GP", "Swarmer") else family, 1, 1, True, False, False, pds, False)
    return EcologyBuild(
        id=f"test-tl{tl}-{family}-{armor}-{pds or 'off'}", tl=tl, archetype="cp134-test",
        weapon_family="Missile" if family in ("GP", "Swarmer") else family,
        main_count=1, reactor_count=1, shield=True, ecm=False, eccm=False,
        pds_family=pds, shield_hardener=False, capacity=cap, combat_space=combat,
        mission_aux_space=cap-combat, missile_payload="Swarmer" if family=="Swarmer" else "GP",
        armor_profile=armor,
    )


class Cp134CandidateBaselineKernelTests(unittest.TestCase):
    def test_universal_direct_fire_penalties(self):
        self.assertEqual(-25, DIRECT_FIRE_APPROXIMATE_TRACK_PENALTY_PP)
        self.assertEqual(-10, DIRECT_FIRE_EXTENDED_RANGE_PENALTY_PP)
        self.assertEqual(0, direct_fire_accuracy_modifier(track="Firm", range_hex=2, standard_range=2, max_range=4))
        self.assertEqual(-25, direct_fire_accuracy_modifier(track="Approximate", range_hex=2, standard_range=2, max_range=4))
        self.assertEqual(-10, direct_fire_accuracy_modifier(track="Firm", range_hex=3, standard_range=2, max_range=4))
        self.assertEqual(-35, direct_fire_accuracy_modifier(track="Approximate", range_hex=3, standard_range=2, max_range=4))

    def test_out_of_range_and_no_track_are_hard_gates(self):
        with self.assertRaises(ValueError):
            direct_fire_accuracy_modifier(track="Firm", range_hex=5, standard_range=2, max_range=4)
        with self.assertRaises(ValueError):
            direct_fire_accuracy_modifier(track="None", range_hex=2, standard_range=2, max_range=4)

    def test_energy_modes_round_up(self):
        self.assertEqual({"Low": (1, 3), "Standard": (2, 5), "Overload": (3, 8)}, energy_output_modes(2, 5))
        self.assertEqual({"Low": (2, 5), "Standard": (4, 9), "Overload": (6, 14)}, energy_output_modes(4, 9))

    def test_candidate_hit_chance_uses_only_named_range_track_modifiers(self):
        matrix = CandidateMatrix(REPO, MATRIX)
        b = build(tl=1, family="Kinetic")
        # 50 base +20 K ACC +10 computer =80; extended is -10; Approx is -25.
        self.assertEqual(80, _hit_chance(matrix, b, 2, 20, "Firm", 2, 3))
        self.assertEqual(70, _hit_chance(matrix, b, 3, 20, "Firm", 2, 3))
        self.assertEqual(55, _hit_chance(matrix, b, 2, 20, "Approximate", 2, 3))
        self.assertEqual(45, _hit_chance(matrix, b, 3, 20, "Approximate", 2, 3))

    def test_shield_can_use_full_tactical_recharge_cap_when_power_allows(self):
        matrix = CandidateMatrix(REPO, MATRIX)
        a = _create_side(matrix, build(tl=2, family="Kinetic"), -5)
        b = _create_side(matrix, build(tl=2, family="Kinetic"), 5)
        a.shield = 0
        remaining, spent = _begin_turn_recharge(matrix, a, b, 0)
        # TL2: base 2 + three TP at 1/TP = full SC5.
        self.assertEqual(5, a.shield)
        self.assertEqual(3, spent)
        self.assertEqual(1, a.telemetry.shield_reconstitutions)
        self.assertEqual(4, remaining)  # TL2 reactor 7 - 3 tactical recharge

    def test_mainline_tl6_armor_regenerates_and_crystalline_does_not(self):
        matrix = CandidateMatrix(REPO, MATRIX)
        main = _create_side(matrix, build(tl=6, family="Kinetic", armor="mainline"), -5)
        crystal = _create_side(matrix, build(tl=6, family="Kinetic", armor="A_b1"), -5)
        main.armor_integrity -= 3
        crystal.armor_integrity -= 3
        self.assertEqual(1, _apply_armor_regeneration(matrix, main, 5))
        self.assertEqual(8, main.armor_integrity)  # 10 max -> 7 -> +1
        self.assertEqual(0, _apply_armor_regeneration(matrix, crystal, 5))
        self.assertEqual(9, crystal.armor_integrity)

    def test_tl6_crystalline_seed_is_passive_high_hardening(self):
        matrix = CandidateMatrix(REPO, MATRIX)
        p = _armor_profile(matrix, build(tl=6, family="Kinetic", armor="A_b1"))
        self.assertEqual((2, 12, 0), (p["ap"], p["ai"], p["tacticalRegenerationCapTp"]))

    def test_reference_builds_fit_with_mandatory_shield_armor_and_amm(self):
        matrix = CandidateMatrix(REPO, MATRIX)
        for tl in range(1, 10):
            for family in ("Kinetic", "Energy", "Missile"):
                used = build_space(matrix, tl, family, 1, 1, True, False, False, "AMM", False)
                self.assertLessEqual(used, matrix.capacity(tl), (tl, family, used, matrix.capacity(tl)))


if __name__ == "__main__":
    unittest.main()
