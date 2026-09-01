import json
import unittest
from pathlib import Path

from starcluster_research.study import load_json
from starcluster_research.ecology import CandidateMatrix, _weapon
from starcluster_research.weapon_family_analysis import FamilyCatalog, build_variants, _effective_profile, validate_study as validate_cp115_study
from starcluster_research.role_generation_analysis import validate_study, _packet_probe_rows

REPO = Path(__file__).resolve().parents[3]
STUDY = REPO / 'docs/archive/testing/pre-cp165-active/warhead_role_generation_study_v0_1.json'
CP115_STUDY = REPO / 'docs/archive/testing/pre-cp165-active/weapon_family_payload_study_v0_2.json'


class CP116RoleGenerationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = load_json(STUDY)
        cls.catalog = FamilyCatalog(cls.doc)
        cls.matrix = CandidateMatrix(REPO)
        cls.builds, cls.variants = build_variants(REPO, cls.doc)

    def test_study_valid(self):
        self.assertEqual([], validate_study(self.doc))

    def test_variant_shape_and_exact_fill(self):
        self.assertEqual(2976, len(self.variants))
        counts = {}
        for v in self.variants:
            counts[v.scenario_group] = counts.get(v.scenario_group, 0) + 1
        self.assertEqual(2176, counts['missile_family_characteristic'])
        self.assertEqual(672, counts['kinetic_family_characteristic'])
        self.assertEqual(128, counts['energy_family_reference'])
        self.assertEqual(138, len(self.builds))
        self.assertTrue(all(b.used_space == b.capacity for b in self.builds))

    def test_pure_gp_holds_penetration_constant(self):
        baseline = self.doc['gpBaselinePenetration']
        ids = {pid for rows in self.doc['pureGpByTl'].values() for pid in rows}
        for pid in ids:
            p = self.catalog.missile[pid]
            self.assertEqual(int(baseline['spen']), p.spen)
            self.assertEqual(int(baseline['apen']), p.apen)

    def test_generation_anchor_yield_increases_without_penetration_growth(self):
        ids = [self.doc['generationGpAnchor'][x] for x in self.doc['generationOrder']]
        profiles = [self.catalog.missile[x] for x in ids]
        self.assertEqual([7, 8, 10], [p.damage for p in profiles])
        self.assertEqual([1, 1, 1], [p.spen for p in profiles])
        self.assertEqual([2, 2, 2], [p.apen for p in profiles])

    def test_penetration_bundled_gp_is_explicit_control(self):
        pure = self.catalog.missile['missile-antimatter-gp-yield-a']
        leak = self.catalog.missile['missile-antimatter-gp-penetration-control']
        self.assertEqual(pure.damage, leak.damage)
        self.assertGreater(leak.spen, pure.spen)
        self.assertGreater(leak.apen, pure.apen)

    def test_single_axis_gp_controls_isolate_spen_and_apen(self):
        pure = self.catalog.missile['missile-antimatter-gp-yield-a']
        sp = self.catalog.missile['missile-antimatter-gp-spen-control']
        ap = self.catalog.missile['missile-antimatter-gp-apen-control']
        self.assertEqual(pure.damage, sp.damage)
        self.assertEqual(pure.damage, ap.damage)
        self.assertGreater(sp.spen, pure.spen)
        self.assertEqual(sp.apen, pure.apen)
        self.assertEqual(ap.spen, pure.spen)
        self.assertGreater(ap.apen, pure.apen)

    def test_generation_specialists_pay_opportunity_cost(self):
        for tl, ids in self.doc['specialistPairingIdsByTl'].items():
            anchor = self.catalog.missile[self.doc['contemporaryGpByTl'][tl][0]]
            for pid in ids:
                p = self.catalog.missile[pid]
                self.assertFalse(p.damage >= anchor.damage and p.spen >= anchor.spen and p.apen >= anchor.apen, pid)

    def test_generation_pairing_does_not_cross_tl(self):
        tl4 = [v.side_a_profile for v in self.variants if v.tl == 4 and v.scenario_group == 'missile_family_characteristic']
        self.assertTrue(any('pair::missile-fission-gp-yield-b::missile-fission-specialist-armor' == x for x in tl4))
        self.assertFalse(any('fusion-specialist' in x or 'antimatter-specialist' in x for x in tl4))

    def test_packet_probe_exposes_penetration_leakage(self):
        rows = _packet_probe_rows(REPO, self.doc)
        def row(pid):
            return next(r for r in rows if r['family']=='Missile' and r['tl']==9 and r['profile_id']==pid and r['target_fixture']=='shield-heavy-legal')
        pure = row('missile-antimatter-gp-yield-a')
        leak = row('missile-antimatter-gp-penetration-control')
        self.assertEqual(pure['effective_damage'], leak['effective_damage'])
        self.assertGreater(leak['effective_spen'], pure['effective_spen'])
        self.assertGreaterEqual(leak['armor_integrity_damage'] + leak['hull_damage'], pure['armor_integrity_damage'] + pure['hull_damage'])

    def test_generational_specialist_not_frozen_at_cp115_packet(self):
        modern = self.catalog.missile['missile-antimatter-specialist-armor']
        static = self.catalog.missile['missile-static-specialist-armor']
        self.assertGreater(modern.damage, static.damage)
        self.assertGreater(modern.apen, static.apen)

    def test_kinetic_saturation_packet_matures_at_tl9(self):
        tl6 = self.catalog.kinetic['kinetic-saturation-tl6-a']
        tl9 = self.catalog.kinetic['kinetic-saturation-tl9-a']
        self.assertGreater(tl9.damage, tl6.damage)
        self.assertGreaterEqual(tl9.accuracy_delta, tl6.accuracy_delta)
        self.assertEqual(2, tl9.packets)

    def test_tandem_reverse_preserves_packet_budget(self):
        a = self.catalog.kinetic['kinetic-tandem-tl9']
        b = self.catalog.kinetic['kinetic-tandem-tl9-reverse']
        self.assertEqual(sorted(a.ordered_packets), sorted(b.ordered_packets))
        self.assertNotEqual(a.ordered_packets, b.ordered_packets)

    def test_cp115_study_remains_valid_after_pairing_extension(self):
        self.assertEqual([], validate_cp115_study(load_json(CP115_STUDY)))
        _, variants = build_variants(REPO, load_json(CP115_STUDY))
        self.assertEqual(4064, len(variants))


if __name__ == '__main__':
    unittest.main()
