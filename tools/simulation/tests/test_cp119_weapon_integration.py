import unittest
from collections import Counter
from pathlib import Path

from starcluster_research.ecology import CandidateMatrix, _weapon
from starcluster_research.study import load_json
from starcluster_research.weapon_family_analysis import FamilyCatalog, build_variants, _effective_profile
from starcluster_research.weapon_integration_analysis import validate_study

REPO = Path(__file__).resolve().parents[3]
STUDY = REPO / 'docs/archive/testing/pre-cp165-active/campaign_weapon_integration_study_v0_1.json'


class CP119WeaponIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = load_json(STUDY)
        cls.catalog = FamilyCatalog(cls.doc)
        cls.matrix = CandidateMatrix(REPO)
        cls.builds, cls.variants = build_variants(REPO, cls.doc)

    def test_study_valid(self):
        self.assertEqual([], validate_study(self.doc))

    def test_variant_shape(self):
        self.assertEqual(1152, len(self.variants))
        counts = Counter(v.scenario_group for v in self.variants)
        self.assertEqual(576, counts['missile_family_characteristic'])
        self.assertEqual(360, counts['kinetic_family_characteristic'])
        self.assertEqual(216, counts['energy_family_reference'])

    def test_primary_population_is_campaign_weighted(self):
        def priority(tl):
            return 'primary' if tl <= 6 else ('advanced' if tl == 7 else 'endpoint')
        counts = Counter(priority(v.tl) for v in self.variants)
        self.assertEqual(720, counts['primary'])
        self.assertEqual(144, counts['advanced'])
        self.assertEqual(288, counts['endpoint'])
        self.assertGreater(counts['primary'], counts['advanced'] + counts['endpoint'])

    def test_underlying_builds_are_exact_fill(self):
        self.assertEqual(108, len(self.builds))
        self.assertTrue(all(b.used_space == b.capacity for b in self.builds))

    def test_swarmer_starts_at_tl2_and_uses_two_packets(self):
        sw = [p for p in self.catalog.missile.values() if p.id.startswith('swarmer-')]
        self.assertNotIn(1, {tl for p in sw for tl in p.study_tls})
        self.assertIn(2, {tl for p in sw for tl in p.study_tls})
        self.assertTrue(all(p.packets == 2 for p in sw))
        self.assertEqual('swarmer-early-tl2', self.doc['workingSwarmerByTl']['2'])

    def test_swarmer_matures_without_penetration_creep(self):
        expected = {
            'swarmer-early-tl2': (2, 10, 10),
            'swarmer-mid': (3, 10, 10),
            'swarmer-mature': (4, 15, 15),
        }
        for pid, (damage, guidance, pds) in expected.items():
            p = self.catalog.missile[pid]
            self.assertEqual(damage, p.damage)
            self.assertEqual(0, p.spen)
            self.assertEqual(0, p.apen)
            self.assertEqual(guidance, p.guidance_delta)
            self.assertEqual(pds, p.pds_intercept_penalty_pp)

    def test_working_gp_progression_is_yield_only(self):
        expected_damage = {
            'missile-working-fission-d6': 6,
            'missile-working-fusion-d7': 7,
            'missile-working-antimatter-d8': 8,
        }
        for pid, damage in expected_damage.items():
            p = self.catalog.missile[pid]
            self.assertEqual(damage, p.damage)
            self.assertEqual(1, p.spen)
            self.assertEqual(2, p.apen)
            self.assertEqual(1, p.packets)
            self.assertEqual(0, p.guidance_delta)
            self.assertEqual(0, p.pds_intercept_penalty_pp)

    def test_kinetic_working_profile_is_plus5_accuracy_only(self):
        p = self.catalog.kinetic['kinetic-working-smart-plus5']
        self.assertEqual(5, p.accuracy_delta)
        self.assertEqual(0, p.damage_delta)
        self.assertEqual(0, p.spen_delta)
        self.assertEqual(0, p.apen_delta)
        base = _weapon(self.matrix, next(b for b in self.builds if b.id == 'tl6-kinetic-balanced'))
        working = _effective_profile(base, p)
        current = _effective_profile(base, self.catalog.kinetic['gp-current'])
        self.assertEqual(current['accuracy'] + 5, working['accuracy'])
        self.assertEqual(current['damage'], working['damage'])
        self.assertEqual(current['spen'], working['spen'])
        self.assertEqual(current['apen'], working['apen'])

    def test_all_targets_are_legal_primary_builds(self):
        self.assertEqual(6, len(self.doc['targetFixtures']))
        self.assertTrue(all(x['classification'] == 'legal_build' for x in self.doc['targetFixtures']))
        families = Counter(x['baseFamily'] for x in self.doc['targetFixtures'])
        self.assertEqual({'Energy': 2, 'Kinetic': 2, 'Missile': 2}, dict(families))

    def test_no_specialist_menu_or_hidden_outcome_gate_inputs(self):
        self.assertEqual([], self.doc['specialistPairingIds'])
        self.assertEqual([], self.doc['adaptivePairingIds'])
        self.assertFalse(any(v.side_a_profile.startswith('pair::') or v.side_a_profile.startswith('adaptive-pair::') for v in self.variants))
        self.assertFalse(self.doc['automaticPromotion'])


if __name__ == '__main__':
    unittest.main()
