from __future__ import annotations

import json
import shutil
import unittest
from pathlib import Path

from starcluster_research.missile_progression_analysis import (
    _candidate_overrides,
    _run_candidate,
    build_plan,
    validate_study,
)
from starcluster_research.study import load_json

REPO = Path(__file__).resolve().parents[3]
STUDY = REPO / "docs/archive/testing/pre-cp165-active/cp130_missile_main_progression_and_family_viability_study_v0_1.json"


class Cp130MissileProgressionTests(unittest.TestCase):
    def test_study_contract_and_plan_counts(self):
        doc = load_json(STUDY)
        self.assertEqual([], validate_study(doc))
        plan = build_plan(REPO, STUDY, None)
        self.assertEqual(9427, plan["summary"]["legalBuilds"])
        self.assertEqual(240996, plan["summary"]["generatedVariants"])
        self.assertEqual(24099600, plan["summary"]["substantiveTrials"])
        self.assertEqual([], plan["summary"]["failedGates"])

    def test_population_is_same_tl_and_missile_involving(self):
        plan = build_plan(REPO, STUDY, None)
        bm = {b.id: b for b in plan["builds"]}
        for tl, tasks in plan["tasks"].items():
            self.assertTrue(tasks)
            for t in tasks:
                a, b = bm[t.build_1_id], bm[t.build_2_id]
                self.assertEqual(tl, a.tl)
                self.assertEqual(tl, b.tl)
                self.assertIn("Missile", {a.weapon_family, b.weapon_family})
                self.assertNotEqual({a.weapon_family, b.weapon_family}, {"Kinetic", "Energy"})

    def test_candidate_overrides_touch_only_gp_damage_penetration(self):
        plan = build_plan(REPO, STUDY, None)
        for tl in range(1, 10):
            for candidate in plan["candidates"][tl]:
                rows = _candidate_overrides(candidate)
                self.assertEqual(3, len(rows))
                self.assertEqual({"missile_gp_warhead"}, {r["profile"] for r in rows})
                self.assertEqual({"damage", "spen", "apen"}, {r["field"] for r in rows})
                self.assertEqual({tl}, {r["tl"] for r in rows})

    def test_tl1_to_7_are_damage_only_plus_zero_one_two(self):
        plan = build_plan(REPO, STUDY, None)
        for tl in range(1, 8):
            rows = plan["candidates"][tl]
            self.assertEqual([0, 1, 2], [r["damageDelta"] for r in rows])
            self.assertEqual({0}, {r["spenDelta"] for r in rows})
            self.assertEqual({0}, {r["apenDelta"] for r in rows})

    def test_late_candidate_space_is_nested_and_bounded(self):
        plan = build_plan(REPO, STUDY, None)
        self.assertEqual(6, len(plan["candidates"][8]))
        self.assertEqual(7, len(plan["candidates"][9]))
        for tl in (8, 9):
            rows = plan["candidates"][tl]
            self.assertEqual("control", rows[0]["id"])
            self.assertTrue(all(0 <= r["damageDelta"] <= 3 for r in rows))
            self.assertTrue(all(0 <= r["spenDelta"] <= 2 for r in rows))
            self.assertTrue(all(0 <= r["apenDelta"] <= 1 for r in rows))

    def test_actual_consumer_micro_smoke(self):
        plan = build_plan(REPO, STUDY, None)
        out = REPO / "out" / "cp130-unit-actual-consumer-smoke"
        shutil.rmtree(out, ignore_errors=True)
        try:
            candidate = plan["candidates"][8][-1]
            pairs, variants, _ = _run_candidate(REPO, plan["doc"], plan["tasks"][8][:2], candidate, out, 1, 1)
            self.assertEqual(2, len(pairs))
            self.assertEqual(8, len(variants))
            self.assertEqual(0, sum(int(r["errors"]) for r in variants))
            derived = json.loads((out / "tl8" / candidate["id"] / "derived_matrix.json").read_text())
            gp = derived["profiles"]["missile_gp_warhead"]["8"]
            self.assertEqual((17, 3, 5), (gp["damage"], gp["spen"], gp["apen"]))
        finally:
            shutil.rmtree(out, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
