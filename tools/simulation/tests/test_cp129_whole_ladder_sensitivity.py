from __future__ import annotations

import csv
import json
import shutil
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools/simulation"))

from starcluster_research.baseline_foundation import BaselineCatalog, enumerate_legal_builds
from starcluster_research.fidelity_attribution_analysis import generate_tasks
from starcluster_research.whole_ladder_sensitivity_analysis import (
    _main_only_adjacent_tasks,
    _matched_tasks,
    _run_holdback,
    _run_tasks,
    _smoke_lane_row,
    _whole_ladder_tasks,
    build_plan,
    construction_overrides_for_transition,
    performance_overrides_for_transition,
    validate_study,
)
from starcluster_research.whole_ladder_analysis import _write_csv

STUDY = REPO / "docs/archive/testing/pre-cp165-active/cp129_whole_ladder_pure_tl_sensitivity_study_v0_1.json"
MATRIX = "docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_5.json"


class Cp129WholeLadderSensitivityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(STUDY.read_text(encoding="utf-8"))
        cls.catalog = BaselineCatalog(REPO, MATRIX)
        cls.raw, cls.builds = enumerate_legal_builds(cls.catalog)

    def test_01_study_schema_and_plan_counts(self):
        self.assertEqual([], validate_study(self.doc))
        result = build_plan(REPO, STUDY, None)["summary"]
        self.assertEqual([], result["failedGates"])
        self.assertEqual(9427, result["legalBuilds"])
        self.assertEqual(626028, result["generatedVariants"])
        self.assertEqual(45665000, result["substantiveTrials"])
        self.assertFalse(result["mixedTlShipsExecuted"])
        self.assertFalse(result["counterfactualHoldbacksAreLegalMixedTlBuilds"])

    def test_02_control_populations_and_cp127_adjacent_pair_identity(self):
        whole, coverage = _whole_ladder_tasks(self.builds, int(self.doc["pairingSeed"]))
        main_builds, main_tasks = _main_only_adjacent_tasks(self.builds, int(self.doc["pairingSeed"]))
        matched = _matched_tasks(self.builds)
        self.assertEqual(70034, len(whole))
        self.assertEqual([], coverage["missingCoverage"])
        self.assertEqual(1856, len(main_builds))
        self.assertEqual(1784, len(main_tasks))
        self.assertEqual(7699, len(matched))
        self.assertTrue(all(not b.pds_family and not b.shield_hardener for b in main_builds))
        cp127_adj = sorted(
            (t.task_id, t.build_1_id, t.build_2_id, t.design_weight)
            for t in generate_tasks(self.builds, int(self.doc["pairingSeed"]))
            if t.group == "adjacent_population"
        )
        cp129_adj = sorted(
            (t.task_id, t.build_1_id, t.build_2_id, t.design_weight)
            for t in whole if t.tl_high == t.tl_low + 1
        )
        self.assertEqual(cp127_adj, cp129_adj)

    def test_03_holdbacks_are_transition_local_and_separate_performance_from_construction(self):
        perf_forbidden = {"space", "profileSourceTl", "technology", "notes", "newTech", "hardPrereq", "special"}
        for high in range(2, 10):
            for package in [p["id"] for p in self.doc["performanceHoldbackBoundary"]["packages"]]:
                rows = performance_overrides_for_transition(REPO, self.doc, package, high)
                self.assertTrue(all(int(r["tl"]) == high for r in rows))
                self.assertTrue(all(r["field"] not in perf_forbidden for r in rows))
                self.assertTrue(all(not (r["profile"] == "hull" and r["field"] == "capacity") for r in rows))
            for package in [p["id"] for p in self.doc["constructionEnvelopeSensitivity"]["packages"]]:
                rows = construction_overrides_for_transition(REPO, self.doc, package, high)
                self.assertTrue(all(int(r["tl"]) == high for r in rows))
                self.assertTrue(all(r["field"] in {"space", "capacity"} for r in rows))
        tl6_sensor = performance_overrides_for_transition(REPO, self.doc, "sensor", 6)
        self.assertTrue(tl6_sensor)
        self.assertEqual({6}, {int(r["tl"]) for r in tl6_sensor})
        self.assertTrue(any(r["field"] == "dr" for r in tl6_sensor))

    def test_04_frozen_main_authority_invariants(self):
        d = json.loads((REPO / MATRIX).read_text(encoding="utf-8"))
        self.assertEqual(list(range(1, 10)), [d["profiles"]["stl"][str(t)]["move"] for t in range(1, 10)])
        self.assertEqual(list(range(2, 11)), [d["profiles"]["missile_delivery"][str(t)]["missileMove"] for t in range(1, 10)])
        self.assertEqual([1,2,3,4,4,6,7,9,12], [d["profiles"]["ftl"][str(t)]["strategicMove"] for t in range(1, 10)])
        e8 = d["profiles"]["energy_main"]["8"]
        self.assertEqual((7, 10, 12, 3), (e8["lowDamage"], e8["standardDamage"], e8["highDamage"], e8["apen"]))

    def test_05_actual_consumer_micro_smoke_and_noop_common_random_numbers(self):
        plan = build_plan(REPO, STUDY, None)
        out = REPO / "out" / "cp129-unit-actual-consumer-smoke"
        shutil.rmtree(out, ignore_errors=True)
        try:
            task = plan["matchedTasks"][0]
            baseline_path, _ = _run_tasks(REPO, self.doc["sourceMatrix"], int(self.doc["masterSeed"]), [task], out / "baseline", 1, 1)
            with baseline_path.open(newline="", encoding="utf-8") as f:
                baseline = list(csv.DictReader(f))
            self.assertEqual(4, len(baseline))
            self.assertEqual(0, sum(int(r["errors"]) for r in baseline))
            # TL1->2 Hull points are held, so this package is an exact no-op at this transition.
            held_path, _, changed = _run_holdback(REPO, self.doc, [task], "hull", 2, out / "noop", 1, 1)
            with held_path.open(newline="", encoding="utf-8") as f:
                held = list(csv.DictReader(f))
            self.assertEqual(0, changed)
            self.assertEqual(baseline, held)
        finally:
            shutil.rmtree(out, ignore_errors=True)

    def test_06_smoke_lane_summary_schema_and_configurable_jobs_wrapper(self):
        out = REPO / "out" / "cp129-unit-smoke-summary-schema"
        shutil.rmtree(out, ignore_errors=True)
        out.mkdir(parents=True, exist_ok=True)
        try:
            variants = out / "variants.csv"
            variants.write_text("errors\n0\n", encoding="utf-8")
            baseline = _smoke_lane_row("whole_ladder", variants, 0.1)
            holdback = _smoke_lane_row("holdback_tl1_tl2_sensor", variants, 0.2)
            holdback["changed_fields"] = 3
            summary = out / "smoke_lane_summary.csv"
            fields = ["lane", "variants", "trial_errors", "elapsed_seconds", "changed_fields"]
            _write_csv(summary, [baseline, holdback], fields)
            with summary.open(newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(fields, list(rows[0].keys()))
            self.assertEqual("0", rows[0]["changed_fields"])
            self.assertEqual("3", rows[1]["changed_fields"])

            wrapper = (REPO / "tools/checkpoints/checkpoint-129/apply_checkpoint_129.ps1").read_text(encoding="utf-8-sig")
            self.assertIn("[ValidateRange(1,61)][int]$Jobs=24", wrapper)
            self.assertGreaterEqual(wrapper.count("'--jobs',$Jobs"), 4)
            self.assertNotIn("'--jobs','24'", wrapper)
        finally:
            shutil.rmtree(out, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
