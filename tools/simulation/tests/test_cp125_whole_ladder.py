from __future__ import annotations

import unittest
from collections import defaultdict
from pathlib import Path

from starcluster_research.baseline_foundation import BaselineCatalog, enumerate_legal_builds
from starcluster_research.ecology import run_trial
from starcluster_research.study import load_json
from starcluster_research.whole_ladder_analysis import (
    build_plan,
    generate_pairings,
    generate_variants,
    pairing_coverage,
    validate_study,
)

REPO = Path(__file__).resolve().parents[3]
STUDY = REPO / "docs/archive/testing/pre-cp165-active/cp125_pure_tl_whole_ladder_integrated_progression_study_v0_1.json"


class CP125WholeLadderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = load_json(STUDY)
        cls.catalog = BaselineCatalog(REPO, cls.doc["sourceMatrix"])
        cls.raw, cls.builds = enumerate_legal_builds(cls.catalog)
        cls.pairings = generate_pairings(cls.builds, int(cls.doc["pairingSeed"]))
        cls.coverage = pairing_coverage(cls.builds, cls.pairings)
        cls.plans = generate_variants(cls.pairings)

    def test_study_contract(self):
        self.assertEqual([], validate_study(self.doc))
        self.assertFalse(self.doc["mixedTlShipsExecuted"])
        self.assertFalse(self.doc["automaticPromotion"])
        self.assertFalse(self.doc["balanceValidated"])
        self.assertEqual(200, self.doc["substantiveTrialsPerVariant"])
        self.assertEqual(24, self.doc["recommendedJobs"])

    def test_cp124_build_universe_is_reused_exactly(self):
        self.assertEqual(14112, self.raw)
        self.assertEqual(9427, len(self.builds))
        self.assertEqual({1:207,2:276,3:616,4:736,5:864,6:1544,7:1728,8:1728,9:1728},
                         {tl:sum(b.tl==tl for b in self.builds) for tl in range(1,10)})

    def test_pairing_counts_cover_all_45_canonical_tl_cells(self):
        self.assertEqual(45, self.coverage["canonicalTlCells"])
        self.assertEqual(70034, len(self.pairings))
        self.assertEqual(414, self.coverage["pairCounts"]["TL1-TL1"])
        self.assertEqual(1728, self.coverage["pairCounts"]["TL1-TL9"])
        self.assertEqual(3456, self.coverage["pairCounts"]["TL9-TL9"])

    def test_every_build_is_covered_against_every_opponent_tl(self):
        self.assertEqual([], self.coverage["missingCoverage"])
        self.assertEqual(84843, self.coverage["buildOpponentTlCoverage"])
        self.assertEqual(84843, self.coverage["expectedBuildOpponentTlCoverage"])

    def test_pairing_weights_reconstruct_full_44m_population(self):
        cells = defaultdict(lambda: [0.0, 0])
        for p in self.pairings:
            k=(p.tl_1,p.tl_2)
            cells[k][0] += p.design_weight
            cells[k][1] = p.canonical_population_pairs
        self.assertEqual(45, len(cells))
        for total,pop in cells.values():
            self.assertAlmostEqual(pop,total,places=6)
        self.assertEqual(44429451, sum(pop for _,pop in cells.values()))

    def test_diagonal_pairings_are_distinct_and_have_two_rounds(self):
        for tl in range(1,10):
            ps=[p for p in self.pairings if p.tl_1==tl and p.tl_2==tl]
            expected=2*sum(b.tl==tl for b in self.builds)
            self.assertEqual(expected,len(ps))
            keys={tuple(sorted((p.build_1.id,p.build_2.id))) for p in ps}
            self.assertEqual(len(ps),len(keys))
            self.assertEqual({1,2},{p.sample_round for p in ps})

    def test_off_diagonal_coverage_uses_larger_tl_count(self):
        counts={tl:sum(b.tl==tl for b in self.builds) for tl in range(1,10)}
        for a in range(1,10):
            for b in range(a+1,10):
                ps=[p for p in self.pairings if p.tl_1==a and p.tl_2==b]
                self.assertEqual(max(counts[a],counts[b]),len(ps))

    def test_every_pairing_has_four_symmetry_mirrors(self):
        self.assertEqual(280136,len(self.plans))
        counts=defaultdict(int)
        orientations=defaultdict(set)
        moves=defaultdict(set)
        for p in self.plans:
            counts[p.pairing_id]+=1
            orientations[p.pairing_id].add(p.orientation)
            moves[p.pairing_id].add(p.variant.movement_order)
        self.assertTrue(all(n==4 for n in counts.values()))
        self.assertTrue(all(v=={"forward","reverse"} for v in orientations.values()))
        self.assertTrue(all(v=={"SideAFirst","SideBFirst"} for v in moves.values()))

    def test_each_ship_remains_pure_tl_even_in_cross_tl_matchups(self):
        cross=next(p for p in self.plans if p.side_a_tl != p.side_b_tl)
        self.assertEqual(cross.side_a_tl,cross.variant.side_a.tl)
        self.assertEqual(cross.side_b_tl,cross.variant.side_b.tl)
        self.assertNotEqual(cross.variant.side_a.tl,cross.variant.side_b.tl)
        # All installed component values are resolved later from each ship's single build.tl.
        self.assertEqual("cp125-pure-tl",cross.variant.side_a.archetype)
        self.assertEqual("cp125-pure-tl",cross.variant.side_b.archetype)

    def test_ordered_and_mirror_weights_are_correct(self):
        cross=next(p for p in self.plans if p.canonical_tl_1==1 and p.canonical_tl_2==2)
        self.assertAlmostEqual(cross.base_design_weight/2,cross.ordered_cell_variant_weight)
        self.assertAlmostEqual(cross.base_design_weight/4,cross.mirror_variant_weight)
        diag=next(p for p in self.plans if p.canonical_tl_1==1 and p.canonical_tl_2==1)
        self.assertAlmostEqual(diag.base_design_weight/4,diag.ordered_cell_variant_weight)
        self.assertAlmostEqual(diag.base_design_weight/4,diag.mirror_variant_weight)

    def test_cross_tl_consumer_executes_with_cp123_matrix(self):
        # Use a small deterministic sample here; the checkpoint wrapper performs the full 280,136-trial smoke.
        sample=[]
        seen=set()
        for p in self.plans:
            k=(p.side_a_tl,p.side_b_tl,p.side_a_meta["weapon_profile"],p.side_b_meta["weapon_profile"])
            if k in seen:
                continue
            seen.add(k); sample.append(p)
            if len(sample)>=40:
                break
        self.assertEqual(40,len(sample))
        for i,p in enumerate(sample):
            r=run_trial(self.catalog.matrix,p.variant,int(self.doc["masterSeed"]),i)
            self.assertEqual("",r.error)
            self.assertGreaterEqual(r.turns,1)

    def test_full_plan_runner_has_no_structural_gates(self):
        res=build_plan(REPO,STUDY)["summary"]
        self.assertEqual([],res["failedGates"])
        self.assertEqual(280136,res["pipelineSmokeTrials"])
        self.assertEqual(56027200,res["plannedSubstantiveTrials"])
        self.assertEqual(81,res["orderedTlCells"])

    def test_no_balance_threshold_is_a_blocking_gate(self):
        self.assertFalse(self.doc["analysis"]["balanceSignalsAreBlockingGates"])
        self.assertFalse(self.doc["analysis"]["internalCriticalDamageSimulated"])
        self.assertFalse(self.doc["analysis"]["fullCSharpMissileRangeExhaustionParityClaimed"])
        self.assertFalse(self.doc["analysis"]["damageControlScheduledInCombat"])


if __name__ == "__main__":
    unittest.main()
