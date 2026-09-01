from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from starcluster_research.current_working_combat import (
    apu_profile,
    authority_identity,
    aux_id,
    aux_row,
    execution_coverage,
    load_current_working_matrix,
)
from starcluster_research.same_tl_whole_system import (
    EXPECTED_SKELETONS_BY_TL,
    SCHEMA,
    _stack_solution_count,
    build_match_variants,
    build_monotonicity_variants,
    enumerate_skeletons,
    plan,
    representative_rows,
    select_representatives,
    smoke,
    to_ecology_build,
    validate_study,
)


REPO = Path(__file__).resolve().parents[3]
STUDY = REPO / "docs/validation/evidence/checkpoint-166/cp166_same_tl_whole_system_study_v0_1.json"


class Cp166SameTlWholeSystemTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.study = json.loads(STUDY.read_text(encoding="utf-8"))
        cls.matrix = load_current_working_matrix(REPO)
        cls.skeletons = {tl: enumerate_skeletons(cls.matrix, tl) for tl in range(1, 10)}
        cls.reps = {tl: select_representatives(cls.matrix, tl, 28, skeletons=cls.skeletons[tl]) for tl in range(1, 10)}

    def test_01_study_schema_and_checkpoint(self):
        self.assertEqual(self.study["schemaVersion"], SCHEMA)
        self.assertEqual(self.study["checkpoint"], 166)
        self.assertEqual(self.study["baseCheckpoint"], 165)

    def test_02_study_contract_validates(self):
        self.assertEqual(validate_study(self.study), [])

    def test_03_current_authority_hashes_match(self):
        identity = authority_identity(REPO)
        self.assertTrue(identity["passed"])
        self.assertEqual(len(identity["files"]), 4)

    def test_04_current_damage_model_is_def_res(self):
        self.assertEqual(self.matrix.damage_model, "def-res-v1")
        self.assertEqual(self.matrix.def_res_shield_def_pp[1], 20.0)
        self.assertEqual(self.matrix.def_res_shield_def_pp[9], 36.0)
        self.assertEqual(self.matrix.def_res_armor_res_pp[9], 36.0)

    def test_05_current_direct_fire_penalties(self):
        mods = self.matrix.doc["combatModifiers"]
        self.assertEqual(mods["directFireApproximateTrackPenaltyPp"], -25)
        self.assertEqual(mods["directFireExtendedRangePenaltyPp"], -10)

    def test_06_main_reactor_operational_ladder(self):
        self.assertEqual([self.matrix.p("reactor", tl)["operationalTp"] for tl in range(1,10)], list(range(5,14)))
        self.assertEqual({self.matrix.p("reactor", tl)["space"] for tl in range(1,10)}, {6})

    def test_07_apu_selected_ladder(self):
        self.assertEqual([apu_profile(self.matrix, tl)["operationalTp"] for tl in range(1,10)], [1,1,1,1,2,2,2,2,2])
        self.assertEqual({apu_profile(self.matrix, tl)["space"] for tl in range(1,10)}, {2})
        self.assertTrue(all(apu_profile(self.matrix, tl)["countCap"] is None for tl in range(1,10)))

    def test_08_selected_aux_registry_is_current(self):
        self.assertIsNotNone(aux_id(self.matrix, "shield_battery", 1))
        self.assertIsNotNone(aux_id(self.matrix, "repair_drone_bay", 2))
        self.assertIsNotNone(aux_id(self.matrix, "field_stabilizer", 9))
        self.assertIsNone(aux_id(self.matrix, "field_stabilizer", 6))

    def test_09_repair_drone_executes_kits_not_second_hull_reroll(self):
        row = aux_row(self.matrix, "repair_drone_bay", 9)
        self.assertEqual(row["extra_repair_kits"], 7)
        self.assertEqual(row["additional_actions_per_phase"], 1)
        self.assertFalse(row["same_target_reroll_allowed"])

    def test_10_skeleton_counts_by_tl(self):
        self.assertEqual({tl: len(v) for tl,v in self.skeletons.items()}, EXPECTED_SKELETONS_BY_TL)

    def test_11_total_skeleton_count(self):
        self.assertEqual(sum(len(v) for v in self.skeletons.values()), 101207)

    def test_12_tl1_has_no_swarmer(self):
        self.assertFalse(any(s.weapon == "SW" for s in self.skeletons[1]))

    def test_13_tl2_through_tl9_include_swarmer(self):
        for tl in range(2,10):
            self.assertTrue(any(s.weapon == "SW" for s in self.skeletons[tl]), tl)

    def test_14_all_skeletons_are_space_legal(self):
        for rows in self.skeletons.values():
            self.assertTrue(all(s.used_without_stacks <= s.capacity for s in rows))
            self.assertTrue(all(s.free_for_stacks >= 0 for s in rows))

    def test_15_unusual_legal_multimain_and_multireactor_are_retained(self):
        self.assertTrue(any(s.main_count >= 3 for s in self.skeletons[9]))
        self.assertTrue(any(s.reactor_count >= 3 for s in self.skeletons[9]))
        self.assertTrue(any((not s.shield) and s.main_count >= 2 for s in self.skeletons[9]))

    def test_16_stack_solution_count_preserves_apu_and_magazine_multiplicity(self):
        mag = next(s for s in self.skeletons[9] if s.weapon == "GP" and s.free_for_stacks >= 4)
        nonmag = next(s for s in self.skeletons[9] if s.weapon == "E" and s.free_for_stacks >= 4)
        self.assertGreater(_stack_solution_count(mag), mag.free_for_stacks + 1)
        self.assertEqual(_stack_solution_count(nonmag), nonmag.free_for_stacks // 2 + 1)

    def test_17_effect_distinct_stack_population_count(self):
        self.assertEqual(sum(_stack_solution_count(s) for rows in self.skeletons.values() for s in rows), 635428)

    def test_18_representative_count_is_28_per_tl(self):
        self.assertTrue(all(len(v) == 28 for v in self.reps.values()))
        self.assertEqual(sum(len(v) for v in self.reps.values()), 252)

    def test_19_representatives_cover_all_available_weapon_families(self):
        for tl,reps in self.reps.items():
            expected = {"K","E","GP"} | ({"SW"} if tl >= 2 else set())
            self.assertTrue(expected.issubset({a.weapon for a in reps}), tl)

    def test_20_representatives_cover_each_pds_family(self):
        for tl,reps in self.reps.items():
            self.assertTrue({"NONE","K","E","AMM"}.issubset({a.pds for a in reps}), tl)

    def test_21_representatives_cover_ew_and_shieldless_extremes(self):
        for tl,reps in self.reps.items():
            self.assertTrue(any(a.ecm and a.eccm for a in reps), tl)
            self.assertTrue(any(not a.shield for a in reps), tl)

    def test_22_representatives_cover_multimain_multireactor_and_apu_extremes(self):
        for tl,reps in self.reps.items():
            self.assertTrue(any(a.main_count >= 2 for a in reps), tl)
            self.assertTrue(any(a.reactor_count >= 2 for a in reps), tl)
            self.assertTrue(any(a.apu_count > 0 for a in reps), tl)

    def test_23_every_available_binary_aux_has_a_representative(self):
        for tl,reps in self.reps.items():
            available = {cid for cid in ("shield_battery","shield_booster","shield_hardener","ablative_armor","energized_armor","crystalline_armor","field_stabilizer","repair_drone_bay") if aux_id(self.matrix,cid,tl) is not None}
            present = {cid for a in reps for cid in a.aux_flags}
            self.assertTrue(available.issubset(present), (tl, available-present))

    def test_24_representatives_materialize_as_same_tl_legal_ecology_builds(self):
        for tl,reps in self.reps.items():
            for a in reps:
                b=to_ecology_build(self.matrix,a)
                self.assertEqual(b.tl, tl)
                self.assertLessEqual(b.combat_space, b.capacity)

    def test_25_player_base_envelope_is_tagged_separately(self):
        rows=representative_rows(self.matrix,self.reps[5])
        self.assertTrue(any(int(r["player_base_envelope"]) for r in rows))
        self.assertTrue(any(not int(r["player_base_envelope"]) for r in rows))

    def test_26_match_corpus_has_controlled_side_and_order_symmetry(self):
        rows=build_match_variants(self.matrix,self.reps[5])
        self.assertEqual(len(rows),1624)
        self.assertEqual(len({m.pair_id for _,m in rows}),406)
        self.assertEqual({m.orientation for _,m in rows}, {"12-AFIRST","12-BFIRST","21-AFIRST","21-BFIRST"})

    def test_27_monotonicity_corpus_is_exact(self):
        rows=build_monotonicity_variants(self.matrix,self.reps[8])
        self.assertEqual(len(rows),32)
        self.assertEqual({m["delta_tp"] for _,m in rows},{1,2})
        self.assertEqual(len({m["role_index"] for _,m in rows}),4)

    def test_28_monotonicity_power_is_free_diagnostic_capacity_only(self):
        rows=build_monotonicity_variants(self.matrix,self.reps[8])
        for v,m in rows:
            a=v.side_a; b=v.side_b
            if m["boost_side"] == "A":
                self.assertEqual(a.auxiliary_power_tp-b.auxiliary_power_tp,m["delta_tp"])
            else:
                self.assertEqual(b.auxiliary_power_tp-a.auxiliary_power_tp,m["delta_tp"])

    def test_29_execution_coverage_explicitly_reports_deferred_systems(self):
        coverage={r["system"]:r["status"] for r in execution_coverage()}
        self.assertEqual(coverage["Main Reactor Degraded/Emergency transitions"],"DEFERRED_SAME_TL_INTEGRATION")
        self.assertEqual(coverage["mixed-family multiple Main Weapons"],"DEFERRED_SAME_TL_INTEGRATION")
        self.assertEqual(coverage["multiple simultaneous PDS installations/families"],"DEFERRED_SAME_TL_INTEGRATION")

    def test_30_plan_matches_exact_study_scale(self):
        result=plan(REPO,STUDY)
        self.assertTrue(result["passed"])
        self.assertEqual(result["combatVariants"],14616)
        self.assertEqual(result["totalDiagnosticCombatTrials"],2995200)

    def test_31_smoke_runs_current_whole_system_kernel(self):
        with tempfile.TemporaryDirectory() as td:
            result=smoke(REPO,STUDY,Path(td))
            self.assertTrue(result["passed"])
            self.assertEqual(result["liveCombatTrials"],8)

    def test_32_cp166_is_diagnostic_not_tuning_or_promotion(self):
        self.assertFalse(self.study["tuningAllowed"])
        self.assertFalse(self.study["automaticPromotion"])
        self.assertFalse(self.study["differentTlCombatsExecuted"])
        self.assertFalse(self.study["mixedTlShipsExecuted"])


if __name__ == "__main__":
    unittest.main()
