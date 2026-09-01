import unittest
from collections import Counter
from pathlib import Path

from starcluster_research.damage_resolution_analysis import (
    DAMAGE_TELEMETRY_FIELDS,
    DamageScaledMatrix,
    _equivalence_task,
    _init_equivalence_worker,
    build_halfstep_variants,
    scale_family_study_doc,
    validate_study,
)
from starcluster_research.ecology import CandidateMatrix, SideTelemetry, _create_side, _shield_armor, _weapon, generate_primary_builds
from starcluster_research.study import load_json
from starcluster_research.weapon_family_analysis import FamilyCatalog, _apply_fixture_state, _effective_profile, build_variants

REPO = Path(__file__).resolve().parents[3]
STUDY = REPO / 'docs/archive/testing/pre-cp165-active/damage_resolution_scaling_study_v0_1.json'
SOURCE = REPO / 'docs/archive/testing/pre-cp165-active/weapon_progression_sensitivity_study_v0_1.json'


class CP121DamageResolutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = load_json(STUDY)
        cls.source = load_json(SOURCE)
        cls.legacy = CandidateMatrix(REPO)
        cls.scaled = DamageScaledMatrix(REPO, 2)
        cls.builds, cls.variants = build_halfstep_variants(REPO, cls.doc)
        cls.catalog = FamilyCatalog(cls.doc)
        cls.by = {b.id: b for b in cls.builds}

    def test_study_valid(self):
        self.assertEqual([], validate_study(self.doc))

    def test_variant_shape_and_weighting(self):
        self.assertEqual(2424, len(self.variants))
        counts = Counter(v.scenario_group for v in self.variants)
        self.assertEqual(1240, counts['missile_family_characteristic'])
        self.assertEqual(832, counts['kinetic_family_characteristic'])
        self.assertEqual(352, counts['energy_family_reference'])
        priority = Counter('primary' if v.tl in (2,3,4,5,6) else ('advanced' if v.tl == 7 else 'endpoint') for v in self.variants)
        self.assertEqual(1548, priority['primary'])
        self.assertEqual(420, priority['advanced'])
        self.assertEqual(456, priority['endpoint'])
        self.assertGreater(priority['primary'], priority['advanced'] + priority['endpoint'])

    def test_scaled_matrix_doubles_only_point_domain(self):
        for tl in (1, 3, 6, 9):
            for family, names in {
                'hull': ('hullPoints',), 'armor': ('ap','ai'),
                'shield': ('capacity','baseRecharge','tacticalRechargePerTp','shieldArmor'),
                'kinetic_main': ('damage','spen','apen'),
                'energy_main': ('lowDamage','standardDamage','highDamage','spen','apen'),
                'missile_delivery': ('warheadDamage','spen','apen'),
            }.items():
                old = self.legacy.p(family, tl)
                new = self.scaled.p(family, tl)
                for name in names:
                    self.assertEqual(int(old[name]) * 2, int(new[name]), (tl, family, name))
        # Representative non-point quantities must be byte/number equivalent.
        self.assertEqual(self.legacy.p('kinetic_main', 6)['accuracyPp'], self.scaled.p('kinetic_main', 6)['accuracyPp'])
        self.assertEqual(self.legacy.p('kinetic_main', 6)['range'], self.scaled.p('kinetic_main', 6)['range'])
        self.assertEqual(self.legacy.p('reactor', 6)['operationalTp'], self.scaled.p('reactor', 6)['operationalTp'])
        self.assertEqual(self.legacy.p('hull', 6)['capacity'], self.scaled.p('hull', 6)['capacity'])

    def test_source_study_scaling_doubles_fixture_and_profile_points(self):
        scaled_doc = scale_family_study_doc(self.source, 2)
        source_profile = next(x for x in self.source['missileProfiles'] if x['id'] == 'missile-gp-d7')
        scaled_profile = next(x for x in scaled_doc['missileProfiles'] if x['id'] == 'missile-gp-d7')
        self.assertEqual((14,2,4), (scaled_profile['damage'], scaled_profile['spen'], scaled_profile['apen']))
        self.assertEqual(source_profile['guidanceDelta'] if 'guidanceDelta' in source_profile else 0, scaled_profile.get('guidanceDelta',0))
        source_fixture = next(x for x in self.source['targetFixtures'] if x['id'] == 'armor-heavy-control')
        scaled_fixture = next(x for x in scaled_doc['targetFixtures'] if x['id'] == 'armor-heavy-control')
        self.assertEqual(source_fixture['armorProtectionDelta'] * 2, scaled_fixture['armorProtectionDelta'])
        self.assertEqual(source_fixture['armorIntegrityDelta'] * 2, scaled_fixture['armorIntegrityDelta'])

    def test_hardener_flat_shield_armor_scales_for_equivalence(self):
        b = next(b for b in generate_primary_builds(self.scaled) if b.id == 'tl5-energy-defense-specialist')
        self.assertTrue(b.shield_hardener)
        side = _create_side(self.scaled, b, 0)
        self.assertGreaterEqual(_shield_armor(self.scaled, side, True), 2)

    def test_half_step_profiles_use_odd_scaled_points(self):
        self.assertEqual(11, self.catalog.missile['missile-gp-x2-d11'].damage)
        self.assertEqual(1, self.catalog.kinetic['kinetic-damage-half'].damage_delta)
        base = _weapon(self.scaled, self.by['tl5-kinetic-balanced'])
        half = _effective_profile(base, self.catalog.kinetic['kinetic-damage-half'])
        full = _effective_profile(base, self.catalog.kinetic['kinetic-damage-full'])
        self.assertEqual(int(base['damage']) + 1, half['damage'])
        self.assertEqual(int(base['damage']) + 2, full['damage'])

    def test_hull_half_step_fixture_adds_one_scaled_point(self):
        fixture = self.catalog.fixtures['hull-half-control']
        b = self.by['tl5-energy-balanced']
        side = _create_side(self.scaled, b, 0)
        before = side.hull
        _apply_fixture_state(side, fixture)
        self.assertEqual(before + 1, side.hull)

    def test_exact_equivalence_representative_trials(self):
        _, source_variants = build_variants(REPO, self.source)
        wanted = []
        for group in ('missile_family_characteristic','kinetic_family_characteristic','energy_family_reference'):
            wanted.append(next(v for v in source_variants if v.scenario_group == group and v.tl == 5 and v.target_classification == 'legal_build'))
        _init_equivalence_worker(str(REPO), self.source, 2)
        for variant in wanted:
            row = _equivalence_task((variant, int(self.source['masterSeed']), 4))
            self.assertEqual(0, row['mismatched_trials'], row)

    def test_telemetry_damage_domain_is_explicit_and_complete_for_current_fields(self):
        expected = {
            'shield_base_restored','shield_tactical_restored','raw_damage_on_hit','shield_armor_prevented','shield_absorbed',
            'armor_prevented','armor_integrity_damage','armor_protection_damage','hull_damage','direct_raw_damage',
            'direct_hull_damage','missile_raw_damage','missile_hull_damage','payload_shield_bonus_damage','shield_recharge_suppressed',
            'shield_penetration_bypassed','armor_penetration_bypassed','damage_control_hull_restored',
        }
        self.assertEqual(expected, DAMAGE_TELEMETRY_FIELDS)
        telemetry_names = set(SideTelemetry.__dataclass_fields__)
        self.assertTrue(DAMAGE_TELEMETRY_FIELDS <= telemetry_names)

    def test_no_automatic_promotion_or_internal_critical_claim(self):
        self.assertFalse(self.doc['automaticPromotion'])
        self.assertFalse(self.doc['internalDamageCriticalsSimulated'])
        self.assertEqual(119, self.doc['acceptedBaseline'])
        self.assertEqual(120, self.doc['supersedesCandidate'])


if __name__ == '__main__':
    unittest.main()
