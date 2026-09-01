import json
import unittest
from pathlib import Path

from starcluster_research.baseline_foundation import BaselineCatalog, enumerate_legal_builds, _build_to_ecology
from starcluster_research.ecology import EcologyVariant
from starcluster_research.fidelity_attribution_analysis import (
    ALL_TELEMETRY_CONTRACT,
    DEFAULT_STUDY,
    _composition_key,
    _plans_for_task,
    build_plan,
    generate_tasks,
    validate_study,
)
from starcluster_research.canonical_combat import FULL_MAP_GEOMETRY, mirror_equivalent, run_trial_full_map

ROOT = Path(__file__).resolve().parents[3]
STUDY = ROOT / DEFAULT_STUDY


class Cp126FidelityAttributionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(STUDY.read_text(encoding="utf-8"))
        cls.catalog = BaselineCatalog(ROOT)
        _, cls.builds = enumerate_legal_builds(cls.catalog)
        cls.build_map = {b.id: b for b in cls.builds}

    def test_study_and_plan_counts(self):
        self.assertEqual([], validate_study(self.doc))
        plan = build_plan(ROOT, STUDY, None)
        self.assertEqual([], plan["summary"]["failedGates"])
        self.assertEqual(25678, plan["summary"]["compactTasks"])
        self.assertEqual(139000, plan["summary"]["generatedVariants"])
        self.assertEqual(34750000, plan["summary"]["plannedSubstantiveTrials"])
        self.assertEqual(61, plan["summary"]["telemetryMetrics"])

    def test_all_planned_ships_are_pure_tl_and_matched_lane_holds_composition(self):
        tasks = generate_tasks(self.builds, int(self.doc["pairingSeed"]))
        matched = 0
        for task in tasks:
            ids = [task.build_1_id, task.build_2_id]
            if task.build_3_id:
                ids.extend([task.build_3_id, task.build_4_id])
            for bid in ids:
                self.assertEqual(self.build_map[bid].tl, task.tl_low if task.tl_low == task.tl_high else self.build_map[bid].tl)
            if task.group == "matched_composition":
                matched += 1
                self.assertEqual(_composition_key(self.build_map[task.build_1_id]), _composition_key(self.build_map[task.build_2_id]))
                self.assertEqual(self.build_map[task.build_1_id].tl + 1, self.build_map[task.build_2_id].tl)
        self.assertEqual(7699, matched)

    def test_telemetry_contract_extends_cp124_to_61_raw_metrics(self):
        names = [row["metric"] for row in ALL_TELEMETRY_CONTRACT]
        self.assertEqual(61, len(names))
        self.assertEqual(61, len(set(names)))
        for required in (
            "adaptive_standoff_orders", "missile_movement_hexes", "missile_target_movement_reroutes",
            "missile_range_exhausted", "maximum_observed_opponent_attack_range",
        ):
            self.assertIn(required, names)

    def test_each_study_lane_executes_a_full_mirror_set_without_trial_errors(self):
        tasks = generate_tasks(self.builds, int(self.doc["pairingSeed"]))
        seen = set()
        for task in tasks:
            if task.group in seen:
                continue
            seen.add(task.group)
            plans = _plans_for_task(task, self.build_map)
            self.assertIn(len(plans), (4, 16))
            for plan in plans:
                self.assertEqual(FULL_MAP_GEOMETRY, plan.variant.geometry)
                self.assertEqual(plan.side_a_tl, plan.variant.side_a.tl)
                self.assertEqual(plan.side_b_tl, plan.variant.side_b.tl)
                result = run_trial_full_map(self.catalog.matrix, plan.variant, int(self.doc["masterSeed"]), 0)
                self.assertEqual("", result.error, plan.variant.id)
        self.assertEqual({"adjacent_population","matched_composition","movement_hotspot","swarmer_lifecycle","energy_isolation","late_missile_geometry"}, seen)

    def test_identical_build_physical_identity_mirror_is_exact(self):
        build = next(b for b in self.builds if b.tl == 7 and b.weapon_family == "Energy")
        e = _build_to_ecology(build, "cp126-identical")
        scenario = "cp126-identical-build-symmetry"
        for first, mirrored in (("SideAFirst","SideBFirst"),("SideBFirst","SideAFirst")):
            for trial in range(10):
                a = EcologyVariant("identical-a",7,e,e,first,geometry=FULL_MAP_GEOMETRY,population="test",scenario_group=scenario,
                                   physical_id_a=scenario+":ship1",physical_id_b=scenario+":ship2")
                b = EcologyVariant("identical-b",7,e,e,mirrored,geometry=FULL_MAP_GEOMETRY,population="test",scenario_group=scenario,
                                   physical_id_a=scenario+":ship2",physical_id_b=scenario+":ship1")
                r1 = run_trial_full_map(self.catalog.matrix,a,12620260816,trial)
                r2 = run_trial_full_map(self.catalog.matrix,b,12620260816,trial)
                self.assertTrue(mirror_equivalent(r1,r2), f"{first} trial {trial}")


if __name__ == "__main__":
    unittest.main()
