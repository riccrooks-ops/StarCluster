import unittest
from collections import Counter
from pathlib import Path

from starcluster_research.ecology import CandidateMatrix, _weapon
from starcluster_research.study import load_json
from starcluster_research.weapon_family_analysis import FamilyCatalog, build_variants, _effective_profile
from starcluster_research.weapon_sensitivity_analysis import validate_study, _summary_rows

REPO = Path(__file__).resolve().parents[3]
STUDY = REPO / 'docs/archive/testing/pre-cp165-active/weapon_progression_sensitivity_study_v0_1.json'


class CP120WeaponSensitivityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = load_json(STUDY)
        cls.catalog = FamilyCatalog(cls.doc)
        cls.matrix = CandidateMatrix(REPO)
        cls.builds, cls.variants = build_variants(REPO, cls.doc)
        cls.by_build = {b.id: b for b in cls.builds}

    def test_study_valid(self):
        self.assertEqual([], validate_study(self.doc))

    def test_variant_shape(self):
        self.assertEqual(4284, len(self.variants))
        counts = Counter(v.scenario_group for v in self.variants)
        self.assertEqual(2952, counts['missile_family_characteristic'])
        self.assertEqual(1008, counts['kinetic_family_characteristic'])
        self.assertEqual(324, counts['energy_family_reference'])

    def test_primary_population_dominates(self):
        counts = Counter('primary' if v.tl <= 6 else ('advanced' if v.tl == 7 else 'endpoint') for v in self.variants)
        self.assertEqual(3060, counts['primary'])
        self.assertEqual(576, counts['advanced'])
        self.assertEqual(648, counts['endpoint'])
        self.assertGreater(counts['primary'], counts['advanced'] + counts['endpoint'])

    def test_underlying_builds_are_exact_fill(self):
        self.assertEqual(135, len(self.builds))
        self.assertTrue(all(b.used_space == b.capacity for b in self.builds))

    def test_gp_yield_sensitivity_is_yield_only(self):
        for pid in ('missile-gp-d4','missile-gp-d6','missile-gp-d7','missile-gp-d8','missile-gp-d9'):
            p = self.catalog.missile[pid]
            self.assertEqual(1, p.spen)
            self.assertEqual(2, p.apen)
            self.assertEqual(1, p.packets)
            self.assertEqual(0, p.guidance_delta)
            self.assertEqual(0, p.pds_intercept_penalty_pp)

    def test_swarmer_is_tl2_plus_two_packet_only(self):
        sw = [p for p in self.catalog.missile.values() if p.id.startswith('sw-')]
        self.assertTrue(sw)
        self.assertNotIn(1, {tl for p in sw for tl in p.study_tls})
        self.assertIn(2, {tl for p in sw for tl in p.study_tls})
        self.assertTrue(all(p.packets == 2 for p in sw))
        self.assertTrue(all(p.spen == 0 and p.apen == 0 for p in sw))
        self.assertTrue(all(p.guidance_delta in (0,5,10,15) for p in sw))
        self.assertTrue(all(p.pds_intercept_penalty_pp in (0,5,10,15) for p in sw))

    def test_pds_isolation_fixture_changes_only_pds_installation(self):
        fixtures = {x['id']: x for x in self.doc['targetFixtures']}
        f = fixtures['missile-defense-no-pds-control']
        self.assertEqual('Missile', f['baseFamily'])
        self.assertEqual('missile-defense', f['baseArchetype'])
        self.assertTrue(f['removePds'])
        self.assertEqual('controlled_fixture', f['classification'])

    def test_kinetic_sensitivity_is_single_axis(self):
        for pid, expected in {
            'kinetic-acc-plus5': ('accuracy', 5),
            'kinetic-acc-plus10': ('accuracy', 10),
            'kinetic-acc-plus15': ('accuracy', 15),
            'kinetic-damage-plus1': ('damage', 1),
            'kinetic-apen-plus1': ('apen', 1),
        }.items():
            p = self.catalog.kinetic[pid]
            vals = {'accuracy':p.accuracy_delta,'damage':p.damage_delta,'spen':p.spen_delta,'apen':p.apen_delta}
            nonzero = {k:v for k,v in vals.items() if v}
            self.assertEqual({expected[0]: expected[1]}, nonzero)
            self.assertEqual(1, p.packets)
            self.assertFalse(p.ordered_packets)

    def test_kinetic_plus5_is_only_accuracy_change_at_tl6(self):
        base = _weapon(self.matrix, self.by_build['tl6-kinetic-balanced'])
        current = _effective_profile(base, self.catalog.kinetic['gp-current'])
        smart = _effective_profile(base, self.catalog.kinetic['kinetic-acc-plus5'])
        self.assertEqual(current['accuracy'] + 5, smart['accuracy'])
        self.assertEqual(current['damage'], smart['damage'])
        self.assertEqual(current['spen'], smart['spen'])
        self.assertEqual(current['apen'], smart['apen'])

    def test_sensitivity_comparisons_are_declared_and_profile_valid(self):
        comps = self.doc['sensitivityComparisons']
        self.assertEqual(22, len(comps))
        ids = [x['id'] for x in comps]
        self.assertEqual(len(ids), len(set(ids)))
        families = {'Missile': set(self.catalog.missile), 'Kinetic': set(self.catalog.kinetic)}
        for c in comps:
            self.assertIn(c['baseline'], families[c['family']])
            self.assertIn(c['comparison'], families[c['family']])
            self.assertTrue(c['tls'])

    def test_candidate_paths_cover_all_tls_without_new_mechanics(self):
        paths = self.doc['candidateProgressionPaths']
        self.assertEqual(9, len(paths))
        for p in paths:
            self.assertEqual(list(range(1,10)), sorted(int(k) for k in p['profilesByTl']))
        self.assertIn('gp-maturity-delayed', {p['id'] for p in paths})
        self.assertIn('swarmer-payload-conservative', {p['id'] for p in paths})
        self.assertIn('kinetic-smart-plus5', {p['id'] for p in paths})

    def test_no_selectable_specialist_menu_reintroduced(self):
        self.assertEqual([], self.doc['specialistPairingIds'])
        self.assertEqual([], self.doc['adaptivePairingIds'])
        self.assertFalse(any(v.side_a_profile.startswith('pair::') or v.side_a_profile.startswith('adaptive-pair::') for v in self.variants))
        self.assertFalse(self.doc['automaticPromotion'])

    def test_missile_hit_summary_reads_terminal_target_side(self):
        row = {
            'scenario_group': 'missile_family_characteristic', 'tl': 3, 'side_a_profile': 'gp-current',
            'target_fixture': 'energy-balanced-legal', 'side_a_archetype': 'balanced',
            'mean_a_direct_shots': 0.0, 'mean_a_direct_hits': 0.0,
            'mean_a_missile_launches': 10.0,
            'mean_a_missile_guidance_attempts': 999.0, 'mean_a_missile_hits': 999.0,
            'mean_b_missile_guidance_attempts': 8.0, 'mean_b_missile_hits': 6.0,
            'mean_b_pds_attempts': 2.0, 'mean_b_pds_intercepts': 1.0,
            'conditional_win_rate_a': 0.5, 'unresolved_rate': 0.0, 'mean_turns': 4.0,
            'mean_b_hull_damage': 3.0, 'mean_b_armor_integrity_damage': 2.0, 'mean_b_shield_absorbed': 4.0,
        }
        meta = {(3, 'Missile', 'gp-current'): {'damage': 5, 'spen': 1, 'apen': 2, 'packets': 1, 'classification': 'reference'}}
        summary = _summary_rows([row], self.doc, meta)
        self.assertEqual(1, len(summary))
        self.assertAlmostEqual(0.6, summary[0]['missile_hit_per_launch'])
        self.assertAlmostEqual(0.75, summary[0]['missile_hit_per_guidance_attempt'])
        self.assertAlmostEqual(0.5, summary[0]['pds_intercept_per_attempt'])


if __name__ == '__main__':
    unittest.main()
