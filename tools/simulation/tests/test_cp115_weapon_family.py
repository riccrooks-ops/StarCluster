import unittest
from pathlib import Path

from starcluster_research.study import load_json
from starcluster_research.ecology import CandidateMatrix, _weapon, _create_side
from starcluster_research.weapon_family_analysis import (
    FamilyCatalog,
    validate_study,
    build_variants,
    _effective_profile,
    _apply_profile_hit,
    _apply_fixture_state,
    _missile_profile_for_launch,
    run_family_trial,
)


REPO = Path(__file__).resolve().parents[3]
STUDY = REPO / 'docs/archive/testing/pre-cp165-active/weapon_family_payload_study_v0_2.json'


class CP115WeaponFamilyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = load_json(STUDY)
        cls.catalog = FamilyCatalog(cls.doc)
        cls.matrix = CandidateMatrix(REPO)
        cls.builds, cls.variants = build_variants(REPO, cls.doc)

    def test_study_valid(self):
        self.assertEqual([], validate_study(self.doc))

    def test_variant_shape_and_exact_fill(self):
        self.assertEqual(4064, len(self.variants))
        counts = {}
        for v in self.variants:
            counts[v.scenario_group] = counts.get(v.scenario_group, 0) + 1
        self.assertEqual(2272, counts['missile_family_characteristic'])
        self.assertEqual(1664, counts['kinetic_family_characteristic'])
        self.assertEqual(128, counts['energy_family_reference'])
        self.assertTrue(all(b.used_space == b.capacity for b in self.builds))

    def test_fixture_shape(self):
        self.assertEqual(8, len(self.catalog.fixtures))
        self.assertEqual(3, sum(f.classification == 'controlled_fixture' for f in self.catalog.fixtures.values()))
        self.assertEqual('legal_build', self.catalog.fixtures['shield-heavy-legal'].classification)
        self.assertEqual('controlled_fixture', self.catalog.fixtures['armor-heavy-fixture'].classification)

    def test_energy_generation_profiles_increase_payload_envelope(self):
        fission = self.catalog.missile['missile-fission-gp-c']
        fusion = self.catalog.missile['missile-fusion-gp-c']
        antimatter = self.catalog.missile['missile-antimatter-gp-c']
        self.assertLess(fission.damage, fusion.damage)
        self.assertLess(fusion.damage, antimatter.damage)
        self.assertLessEqual(fission.apen, fusion.apen)
        self.assertLessEqual(fusion.apen, antimatter.apen)

    def test_gp_current_preserves_matrix_weapon_packet(self):
        build = next(b for b in self.builds if b.id == 'tl7-missile-balanced')
        w = _weapon(self.matrix, build)
        p = _effective_profile(w, self.catalog.missile['gp-current'])
        self.assertEqual(w['damage'], p['damage'])
        self.assertEqual(w['spen'], p['spen'])
        self.assertEqual(w['apen'], p['apen'])

    def test_saturation_adds_accuracy_but_keeps_single_profile_hit_roll(self):
        build = next(b for b in self.builds if b.id == 'tl6-kinetic-balanced')
        w = _weapon(self.matrix, build)
        p = _effective_profile(w, self.catalog.kinetic['kinetic-saturation-a'])
        self.assertEqual(w['accuracy'] + 10, p['accuracy'])
        self.assertEqual(2, p['packets'])
        self.assertEqual((), p['ordered_packets'])

    def test_tandem_uses_one_profile_with_ordered_packets(self):
        build = next(b for b in self.builds if b.id == 'tl6-kinetic-balanced')
        w = _weapon(self.matrix, build)
        p = _effective_profile(w, self.catalog.kinetic['kinetic-tandem-a'])
        self.assertEqual(w['accuracy'] + 5, p['accuracy'])
        self.assertEqual(((3, 2, 0), (3, 0, 2)), p['ordered_packets'])

    def test_tandem_order_can_change_layer_resolution(self):
        target_build = next(b for b in self.builds if b.id.startswith('tl6-energy-defense-specialist-armor-exposed-legal'))
        a = _create_side(self.matrix, target_build, 0)
        b = _create_side(self.matrix, target_build, 0)
        # Keep both defensive layers barely active. Under the CP132 hardening
        # model, packet order can still matter because an earlier packet may
        # collapse a layer and disable its hardening before the later packet.
        for side in (a, b):
            side.shield = side.shield_max = 2
            side.armor_protection = 0
            side.armor_integrity = 2
        pa = {'damage': 0, 'spen': 0, 'apen': 0, 'packets': 1, 'ordered_packets': ((2,2,0),(4,0,3)), 'shield_bonus_damage':0, 'shield_armor_reduction':0, 'recharge_suppression':0}
        pb = {'damage': 0, 'spen': 0, 'apen': 0, 'packets': 1, 'ordered_packets': ((4,0,3),(2,2,0)), 'shield_bonus_damage':0, 'shield_armor_reduction':0, 'recharge_suppression':0}
        ra = _apply_profile_hit(a, pa, 1, 'direct')
        rb = _apply_profile_hit(b, pb, 1, 'direct')
        self.assertNotEqual(ra['hull'], rb['hull'])

    def test_armor_heavy_fixture_strengthens_armor_only(self):
        fixture = self.catalog.fixtures['armor-heavy-fixture']
        build = next(b for b in self.builds if b.id.startswith('tl7-energy-defense-specialist-armor-heavy-fixture'))
        side = _create_side(self.matrix, build, 0)
        base_ap = side.armor_protection
        base_ai = side.armor_integrity
        _apply_fixture_state(side, fixture)
        self.assertEqual(base_ap + 1, side.armor_protection)
        self.assertEqual(base_ai + 4, side.armor_integrity)
        self.assertEqual(0, side.shield)

    def test_light_fixture_removes_flat_armor_barrier(self):
        fixture = self.catalog.fixtures['light-fixture']
        build = next(b for b in self.builds if b.id.startswith('tl7-energy-defense-specialist-light-fixture'))
        side = _create_side(self.matrix, build, 0)
        _apply_fixture_state(side, fixture)
        self.assertEqual(0, side.armor_protection)
        self.assertEqual(2, side.armor_integrity)
        self.assertEqual(0, side.shield)

    def test_shield_overmatch_fixture_increases_capacity_and_recharge_contract(self):
        fixture = self.catalog.fixtures['shield-overmatch-fixture']
        build = next(b for b in self.builds if b.id.startswith('tl7-energy-defense-specialist-shield-overmatch-fixture'))
        side = _create_side(self.matrix, build, 0)
        base = side.shield_max
        _apply_fixture_state(side, fixture)
        self.assertEqual(base + 6, side.shield_max)
        self.assertEqual(1, fixture.shield_recharge_bonus)
        self.assertIsNone(build.pds_family)

    def test_pair_selects_specialist_then_contemporary_gp(self):
        build = next(b for b in self.builds if b.id == 'tl7-missile-dual-main')
        side = _create_side(self.matrix, build, 0)
        doctrine = 'pair::missile-antimatter-gp-b::missile-shield-pressure'
        p0 = _missile_profile_for_launch(side, self.catalog, doctrine, 0)
        p1 = _missile_profile_for_launch(side, self.catalog, doctrine, 1)
        self.assertEqual('missile-shield-pressure', p0.id)
        self.assertEqual('missile-antimatter-gp-b', p1.id)

    def test_adaptive_pair_uses_observed_effect_not_hidden_values(self):
        build = next(b for b in self.builds if b.id == 'tl7-missile-dual-main')
        side = _create_side(self.matrix, build, 0)
        doctrine = 'adaptive-pair::missile-antimatter-gp-b::missile-shield-recharge'
        p0 = _missile_profile_for_launch(side, self.catalog, doctrine, 0)
        self.assertEqual('missile-antimatter-gp-b', p0.id)
        self.assertEqual(0, side.telemetry.payload_switches)
        side.observed_shield_absorption = True
        side.observed_no_penetration_streak = 2
        p1 = _missile_profile_for_launch(side, self.catalog, doctrine, 0)
        self.assertEqual('missile-shield-recharge', p1.id)
        self.assertGreaterEqual(side.telemetry.payload_switches, 1)

    def test_pair_trial_records_both_payload_classes(self):
        v = next(v for v in self.variants if v.scenario_group == 'missile_family_characteristic' and v.tl == 7 and v.side_a.archetype == 'dual-main' and v.target_fixture == 'shield-isolated-legal' and v.side_a_profile == 'pair::missile-antimatter-gp-b::missile-shield-pressure' and v.movement_order == 'SideAFirst')
        results = [run_family_trial(self.matrix, self.catalog, v, int(self.doc['masterSeed']), i) for i in range(8)]
        self.assertTrue(all(not r.error for r in results))
        self.assertGreater(sum(r.side_a.payload_gp_launches for r in results), 0)
        self.assertGreater(sum(r.side_a.payload_specialist_launches for r in results), 0)

    def test_energy_reference_is_native_not_payload_profile(self):
        refs = [v for v in self.variants if v.scenario_group == 'energy_family_reference']
        self.assertEqual(128, len(refs))
        self.assertTrue(all(v.side_a_profile == 'energy-native' for v in refs))


if __name__ == '__main__':
    unittest.main()
