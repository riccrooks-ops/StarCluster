import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools/simulation"))

from starcluster_research.baseline_foundation import BaselineCatalog, _build_to_ecology, enumerate_legal_builds
from starcluster_research.canonical_combat import (
    CANONICAL_COMBAT_KERNEL_VERSION,
    CANONICAL_VISIBLE_PHASES,
    STANDARD_START_RANGE,
    run_trial_full_map,
)
from starcluster_research.canonical_mechanics import CANONICAL_DAMAGE_MODEL, resolve_layered_damage
from starcluster_research.ecology import EcologyVariant


class Cp132CanonicalKernelTests(unittest.TestCase):

    def test_shared_fixture_matches_python_damage_contract(self):
        fixture = json.loads((ROOT / "docs/archive/testing/pre-cp165-active/canonical_combat_kernel_fixtures_v0_1.json").read_text())
        self.assertEqual("0.1", fixture["kernelVersion"])
        self.assertEqual(CANONICAL_DAMAGE_MODEL, fixture["damageModel"])
        for case in fixture["damageCases"]:
            initial = case["initial"]
            packet = case["packet"]
            expected = case["expected"]
            r = resolve_layered_damage(
                shield=initial["shield"],
                shield_armor=initial["shieldArmor"],
                armor_integrity=initial["armorIntegrity"],
                armor_protection=initial["armorProtection"],
                hull=initial["hull"],
                damage=packet["damage"],
                spen=packet["spen"],
                apen=packet["apen"],
            )
            observed = {
                "effectiveSpen": r.effective_spen,
                "shieldPenetrationResisted": r.shield_penetration_resisted,
                "shieldBypass": r.shield_bypass,
                "shieldAbsorbed": r.shield_absorbed,
                "damageToArmor": r.damage_to_armor,
                "effectiveApen": r.effective_apen,
                "armorPenetrationResisted": r.armor_penetration_resisted,
                "armorBypass": r.armor_bypass,
                "armorIntegrityDamage": r.armor_absorbed,
                "hullDamage": r.hull_damage,
                "finalShield": r.final_shield,
                "finalArmorIntegrity": r.final_armor_integrity,
                "finalArmorProtection": initial["armorProtection"],
                "finalHull": r.final_hull,
            }
            self.assertEqual(expected, observed, case["id"])

    def test_damage_one_spen_one_apen_reaches_hull_when_unhardened(self):
        r = resolve_layered_damage(
            shield=6, armor_integrity=8, armor_protection=0, hull=12,
            damage=8, spen=1, apen=1, shield_armor=0,
        )
        self.assertEqual(CANONICAL_DAMAGE_MODEL, "penetration-hardening-v1")
        self.assertEqual(1, r.shield_bypass)
        self.assertEqual(1, r.armor_bypass)
        self.assertEqual(1, r.hull_damage)
        self.assertEqual(0, r.final_shield)
        self.assertEqual(7, r.final_armor_integrity)

    def test_sa_and_ap_reduce_penetration_not_ordinary_damage(self):
        r = resolve_layered_damage(
            shield=6, armor_integrity=8, armor_protection=1, hull=12,
            damage=8, spen=2, apen=2, shield_armor=1,
        )
        self.assertEqual(1, r.effective_spen)
        self.assertEqual(1, r.shield_penetration_resisted)
        self.assertEqual(1, r.shield_bypass)
        # Six shield points are still lost; SA did not delete facing damage.
        self.assertEqual(6, r.shield_absorbed)
        self.assertEqual(0, r.final_shield)
        # Three damage reaches Armor: 1 SPEN bypass + 1 shield overflow? Actually
        # 7 facing - 6 shield = 1 overflow, so 2 reaches Armor; AP1 leaves APEN1.
        self.assertEqual(2, r.damage_to_armor)
        self.assertEqual(1, r.effective_apen)
        self.assertEqual(1, r.armor_penetration_resisted)
        self.assertEqual(1, r.armor_bypass)
        self.assertEqual(1, r.armor_absorbed)
        self.assertEqual(1, r.hull_damage)

    def test_collapsed_layers_turn_off_hardening(self):
        r = resolve_layered_damage(
            shield=0, armor_integrity=0, armor_protection=9, hull=12,
            damage=4, spen=9, apen=9, shield_armor=9,
        )
        self.assertEqual(0, r.shield_hardening)
        self.assertEqual(0, r.armor_hardening)
        self.assertEqual(4, r.hull_damage)

    def test_ap_is_not_destructible_hit_points(self):
        r = resolve_layered_damage(
            shield=0, armor_integrity=2, armor_protection=3, hull=12,
            damage=5, spen=0, apen=0, shield_armor=0,
        )
        self.assertEqual(2, r.armor_absorbed)
        self.assertEqual(3, r.hull_damage)
        # The pure resolver reports no AP durability mutation; AP remains an input
        # hardening rating for any later restored AI.
        self.assertEqual(3, r.armor_hardening)

    def test_standard_kernel_exposes_phase_order_and_one_hex_search(self):
        catalog = BaselineCatalog(ROOT)
        _, builds = enumerate_legal_builds(catalog)
        candidates = [b for b in builds if b.tl == 1 and b.weapon_family == "Kinetic"]
        left = candidates[len(candidates) // 3]
        right = candidates[(2 * len(candidates)) // 3]
        variant = EcologyVariant(
            "cp132-kernel-smoke", 1,
            _build_to_ecology(left, "cp132-kernel-smoke"),
            _build_to_ecology(right, "cp132-kernel-smoke"),
            "SideAFirst", geometry="radius5_full_hex_adaptive",
            population="cp132_kernel", scenario_group="cp132_kernel",
            physical_id_a="cp132-ship-1", physical_id_b="cp132-ship-2",
            max_turns=1,
        )
        events = []
        result = run_trial_full_map(catalog.matrix, variant, 13220260819, 0, events)
        self.assertEqual("", result.error)
        self.assertEqual(10, STANDARD_START_RANGE)
        phases = [e["phase"] for e in events if e.get("event") == "phase"]
        self.assertEqual(
            ["TurnRefresh", "PreMovementTacticalPower", *CANONICAL_VISIBLE_PHASES],
            phases,
        )
        movement = [e for e in events if e.get("event") == "movement"]
        self.assertEqual(2, len(movement))
        self.assertTrue(all(int(e["movement_hexes"]) <= 1 for e in movement))
        self.assertEqual("0.7", CANONICAL_COMBAT_KERNEL_VERSION)


if __name__ == "__main__":
    unittest.main()
