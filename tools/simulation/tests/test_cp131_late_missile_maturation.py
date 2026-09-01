from __future__ import annotations

import csv
import json
import shutil
import unittest
from pathlib import Path

from starcluster_research.missile_late_maturation_analysis import (
    _apen6_effects,
    _candidate_rows,
    _pair_summary,
    build_plan,
    validate_study,
)
from starcluster_research.missile_progression_analysis import _accepted_baseline, _candidate_overrides, _context_rows, _run_candidate
from starcluster_research.study import load_json
from starcluster_research.whole_ladder_analysis import _write_csv

REPO = Path(__file__).resolve().parents[3]
STUDY = REPO / "docs/archive/testing/pre-cp165-active/cp131_late_missile_warhead_maturation_study_v0_1.json"


class Cp131LateMissileMaturationTests(unittest.TestCase):
    def test_study_contract_and_plan_counts(self):
        doc = load_json(STUDY)
        self.assertEqual([], validate_study(doc))
        plan = build_plan(REPO, STUDY, None)
        self.assertEqual(9427, plan["summary"]["legalBuilds"])
        self.assertEqual({"8": 20, "9": 26}, plan["summary"]["candidateCountsByTl"])
        self.assertEqual(476936, plan["summary"]["generatedVariants"])
        self.assertEqual(47693600, plan["summary"]["substantiveTrials"])
        self.assertEqual([], plan["summary"]["failedGates"])

    def test_population_is_same_tl_missile_involving_and_late_only(self):
        plan = build_plan(REPO, STUDY, None)
        bm = {b.id: b for b in plan["builds"]}
        self.assertEqual({8, 9}, set(plan["tasks"]))
        for tl, tasks in plan["tasks"].items():
            self.assertTrue(tasks)
            for task in tasks:
                a, b = bm[task.build_1_id], bm[task.build_2_id]
                self.assertEqual(tl, a.tl)
                self.assertEqual(tl, b.tl)
                self.assertIn("Missile", {a.weapon_family, b.weapon_family})
                self.assertNotEqual({a.weapon_family, b.weapon_family}, {"Kinetic", "Energy"})

    def test_primary_damage_spen_grids_are_exact(self):
        doc = load_json(STUDY)
        rows = _candidate_rows(doc)
        tl8 = {(r["damage"], r["spen"], r["apen"]) for r in rows[8]}
        self.assertEqual({(d, s, 4) for d in range(15, 20) for s in range(3, 7)}, tl8)
        tl9_primary = {(r["damage"], r["spen"], r["apen"]) for r in rows[9] if not r["isApen6Probe"]}
        self.assertEqual({(d, s, 5) for d in range(16, 21) for s in range(4, 8)}, tl9_primary)

    def test_tl9_apen6_threshold_probes_are_bounded(self):
        rows = _candidate_rows(load_json(STUDY))[9]
        probes = [(r["damage"], r["spen"], r["apen"]) for r in rows if r["isApen6Probe"]]
        self.assertEqual([(16,4,6),(17,5,6),(18,4,6),(18,6,6),(19,6,6),(20,7,6)], probes)
        self.assertEqual(6, len(probes))

    def test_candidate_overrides_touch_only_gp_warhead_characteristics(self):
        rows = _candidate_rows(load_json(STUDY))
        for tl in (8, 9):
            for candidate in rows[tl]:
                overrides = _candidate_overrides(candidate)
                self.assertEqual(3, len(overrides))
                self.assertEqual({"missile_gp_warhead"}, {r["profile"] for r in overrides})
                self.assertEqual({"damage", "spen", "apen"}, {r["field"] for r in overrides})
                self.assertEqual({tl}, {r["tl"] for r in overrides})

    def test_accepted_cp130_reference_evidence_is_complete(self):
        with (REPO / "docs/validation/evidence/checkpoint-131/accepted-cp130/tl1_7_plus2_baseline.csv").open(newline="", encoding="utf-8") as f:
            plus = list(csv.DictReader(f))
        with (REPO / "docs/validation/evidence/checkpoint-131/accepted-cp130/late_anchor_baseline.csv").open(newline="", encoding="utf-8") as f:
            anchors = list(csv.DictReader(f))
        self.assertEqual(list(range(1, 8)), [int(r["tl"]) for r in plus])
        self.assertTrue(all(r["candidate"] == "damage_plus_2" for r in plus))
        self.assertEqual([(8, 17, 3, 4), (9, 18, 4, 5)], [(int(r["tl"]), int(r["gp_damage"]), int(r["gp_spen"]), int(r["gp_apen"])) for r in anchors])

    def test_actual_consumer_micro_smoke(self):
        plan = build_plan(REPO, STUDY, None)
        out = REPO / "out" / "cp131-unit-actual-consumer-smoke"
        shutil.rmtree(out, ignore_errors=True)
        try:
            accepted = _accepted_baseline(REPO, plan["doc"]["acceptedCp130LateAnchorBaseline"])
            build_map = {b.id: b for b in plan["builds"]}
            matrix = load_json(REPO / plan["doc"]["sourceMatrix"])
            flights = int(matrix["profiles"]["missile_delivery"]["1"]["flights"])
            candidates = [
                next(r for r in plan["candidates"][8] if (r["damage"], r["spen"], r["apen"]) == (17, 3, 4)),
                next(r for r in plan["candidates"][9] if (r["damage"], r["spen"], r["apen"]) == (18, 4, 5)),
                next(r for r in plan["candidates"][9] if (r["damage"], r["spen"], r["apen"]) == (18, 4, 6)),
            ]
            summaries = []
            contexts = []
            for candidate in candidates:
                pairs, variants, _ = _run_candidate(REPO, plan["doc"], plan["tasks"][candidate["tl"]][:2], candidate, out / "candidates", 1, 1)
                self.assertEqual(2, len(pairs))
                self.assertEqual(8, len(variants))
                self.assertEqual(0, sum(int(r["errors"]) for r in variants))
                summaries.append(_pair_summary(pairs, build_map, candidate, accepted))
                contexts.extend(_context_rows(variants, build_map, candidate, flights))
            _write_csv(out / "family_plot_inputs.csv", summaries)
            _write_csv(out / "missile_context_telemetry.csv", contexts)
            effects = _apen6_effects(summaries)
            _write_csv(out / "tl9_apen6_threshold_effects.csv", effects)
            self.assertEqual(3, len(summaries))
            self.assertTrue(contexts)
            self.assertEqual(1, len(effects))
            derived = json.loads((out / "candidates" / "tl9" / "d18_sp4_ap6" / "derived_matrix.json").read_text())
            gp = derived["profiles"]["missile_gp_warhead"]["9"]
            self.assertEqual((18, 4, 6), (gp["damage"], gp["spen"], gp["apen"]))
        finally:
            shutil.rmtree(out, ignore_errors=True)



if __name__ == "__main__":
    unittest.main()
