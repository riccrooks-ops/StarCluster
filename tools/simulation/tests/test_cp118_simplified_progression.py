import unittest
from pathlib import Path

from starcluster_research.ecology import CandidateMatrix, _weapon
from starcluster_research.simplified_progression_analysis import validate_study, _pds_probe_rows
from starcluster_research.study import load_json
from starcluster_research.weapon_family_analysis import FamilyCatalog, build_variants, _effective_profile

REPO = Path(__file__).resolve().parents[3]
STUDY = REPO / 'docs/archive/testing/pre-cp165-active/simplified_weapon_progression_study_v0_1.json'


class CP118SimplifiedProgressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = load_json(STUDY)
        cls.catalog = FamilyCatalog(cls.doc)
        cls.matrix = CandidateMatrix(REPO)
        cls.builds, cls.variants = build_variants(REPO, cls.doc)

    def test_study_valid(self):
        self.assertEqual([], validate_study(self.doc))

    def test_variant_shape_and_exact_fill(self):
        self.assertEqual(1824, len(self.variants))
        counts = {}
        for v in self.variants:
            counts[v.scenario_group] = counts.get(v.scenario_group, 0) + 1
        self.assertEqual(936, counts['missile_family_characteristic'])
        self.assertEqual(888, counts['kinetic_family_characteristic'])
        self.assertNotIn('energy_family_reference', counts)
        self.assertEqual(135, len(self.builds))
        self.assertTrue(all(b.used_space == b.capacity for b in self.builds))

    def test_tl_priority_is_campaign_weighted(self):
        self.assertEqual([1,2,3,4,5,6], self.doc['primaryCalibrationTls'])
        self.assertEqual([7], self.doc['advancedValidationTls'])
        self.assertEqual([8,9], self.doc['endpointStressTls'])

    def test_gp_yield_candidates_do_not_gain_penetration(self):
        for p in self.catalog.missile.values():
            if '-gp-' in p.id:
                self.assertEqual(1, p.spen, p.id)
                self.assertEqual(2, p.apen, p.id)
                self.assertEqual(1, p.packets, p.id)
                self.assertEqual(0, p.guidance_delta, p.id)
                self.assertEqual(0, p.pds_intercept_penalty_pp, p.id)

    def test_swarmer_introduction_search_reaches_tl1(self):
        tls = {tl for p in self.catalog.missile.values() if p.id.startswith('swarmer-') for tl in p.study_tls}
        self.assertTrue({1,2,3,4,5,6,7}.issubset(tls))

    def test_swarmer_is_one_attack_package_with_small_packets(self):
        for p in self.catalog.missile.values():
            if p.id.startswith('swarmer-'):
                self.assertGreaterEqual(p.packets, 2)
                self.assertLessEqual(int(p.damage), 4)
                self.assertGreater(p.guidance_delta, 0)
                self.assertLessEqual(p.pds_intercept_penalty_pp, 20)

    def test_pds_saturation_penalty_reduces_intercept_chance(self):
        rows = _pds_probe_rows(REPO, self.doc)
        gp = next(r for r in rows if r['tl'] == 5 and r['profile'] == 'gp-current')
        swarm = next(r for r in rows if r['tl'] == 5 and r['profile'] == 'swarmer-mid-b')
        self.assertEqual(gp['native_pds_intercept_chance'], swarm['native_pds_intercept_chance'])
        self.assertLess(swarm['effective_pds_intercept_chance'], gp['effective_pds_intercept_chance'])
        self.assertGreater(swarm['effective_guidance'], gp['effective_guidance'])

    def test_kinetic_controls_are_single_axis(self):
        for p in self.catalog.kinetic.values():
            if p.id == 'gp-current':
                continue
            changes = sum(bool(x) for x in (p.accuracy_delta, p.damage_delta, p.apen_delta))
            self.assertEqual(1, changes, p.id)
            self.assertEqual(0, p.spen_delta, p.id)
            self.assertEqual(1, p.packets, p.id)

    def test_kinetic_smart_control_only_changes_accuracy(self):
        base_weapon = _weapon(self.matrix, next(b for b in self.builds if b.id == 'tl6-kinetic-balanced'))
        smart = _effective_profile(base_weapon, self.catalog.kinetic['kinetic-smart-plus10'])
        current = _effective_profile(base_weapon, self.catalog.kinetic['gp-current'])
        self.assertEqual(current['damage'], smart['damage'])
        self.assertEqual(current['spen'], smart['spen'])
        self.assertEqual(current['apen'], smart['apen'])
        self.assertEqual(current['accuracy'] + 10, smart['accuracy'])

    def test_no_legacy_warhead_pairing_menu(self):
        self.assertEqual([], self.doc['specialistPairingIds'])
        self.assertEqual([], self.doc['adaptivePairingIds'])
        self.assertFalse(any(v.side_a_profile.startswith('pair::') or v.side_a_profile.startswith('adaptive-pair::') for v in self.variants))


if __name__ == '__main__':
    unittest.main()
