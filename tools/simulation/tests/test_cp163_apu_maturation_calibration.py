from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from starcluster_research.apu_maturation_calibration import (
    STACK_TIERS,
    _stoch_one,
    apu_tp_for_trajectory,
    candidate_tps_for_tl,
    combat_contexts,
    plan,
    smoke,
    static_analysis,
    trajectories,
    validate_study,
)
from starcluster_research.reactor_aux_power_calibration import _base_cruiser_space, max_stack, select_carrier
from starcluster_research.reactor_tp_equilibrium import enumerate_loadouts
from starcluster_research.research_execution_baseline_pf4 import load_research_execution_baseline_pf4
from starcluster_research.study import load_json

ROOT = Path(__file__).resolve().parents[3]
STUDY = ROOT / "docs/archive/testing/pre-cp165-active/cp163_apu_maturation_and_stacking_resilience_study_v0_1.json"
PF4 = ROOT / "docs/design/player_technology/technology_research_execution_baseline_pending_finalization_v0_4.json"
PROD = ROOT / "docs/design/player_technology/technology_numerical_matrix_v0_9.json"
CONCEPT = ROOT / "docs/archive/concepts/Star_Cluster_Game_Concept_v0.7x.docx"
CATALOG = ROOT / "docs/archive/player_technology/pre-cp165-active/auxiliary_component_catalog_v0_4.json"
CP162_NATIVE = ROOT / "docs/validation/evidence/checkpoint-163/accepted-cp162/CP162_NATIVE_ACCEPTANCE_SUMMARY.json"
CP162_HASH = ROOT / "docs/validation/evidence/checkpoint-163/accepted-cp162/CP162_NATIVE_RESULTS_ARCHIVE_SHA256.txt"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


class Cp163ApuMaturationCalibrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = load_json(STUDY)
        cls.m = load_research_execution_baseline_pf4(ROOT)
        cls.all = enumerate_loadouts(cls.m, reactor_space=6)
        cls.one = [x for x in cls.all if x.reactor_count == 1]

    def test_01_study_validates(self):
        self.assertEqual(validate_study(self.doc), [])

    def test_02_pf4_baseline_locked(self):
        self.assertEqual(sha(PF4), "7fd4dfbbe375586de2605361006db84b68f89767c76ba4b76da6cf5f48253155")

    def test_03_production_authority_unchanged(self):
        self.assertEqual(sha(PROD), "3088b0a9eb45f6bf505c24513e8bb2ac878819db4ab464ccfea330243c82f194")

    def test_04_concept_unchanged(self):
        self.assertEqual(sha(CONCEPT), "f76ca6ce488ccb5ad1352f7d38b8c3d4657c12ed64d0c93cc45d2db605cc632f")

    def test_05_cp162_native_acceptance_preserved(self):
        n = json.loads(CP162_NATIVE.read_text(encoding="utf-8-sig"))
        self.assertEqual(n["checkpoint"], 162)
        self.assertEqual(n["pythonTestsPassed"], 692)
        self.assertEqual(n["xunitPassed"], 934)
        self.assertEqual(n["substantiveCombatTrials"], 4140000)
        self.assertEqual(n["stochasticTurnSamples"], 16560000)
        self.assertEqual(n["combatErrorTrials"], 0)

    def test_06_cp162_archive_hash_locked(self):
        self.assertEqual(CP162_HASH.read_text(encoding="utf-8-sig").strip(), "f782cd9a12a920c8582b13d0628b0da4733b6098d041edbfa2177f58fc8a8e67  StarCluster_CP162_native_results_20260830_182536.zip")

    def test_07_main_reactor_space_fixed_six(self):
        self.assertTrue(all(int(self.m.p("reactor", t)["space"]) == 6 for t in range(1, 10)))

    def test_08_main_offsets_exact(self):
        self.assertEqual(self.doc["mainReactorOffsetsFromPf4"], [-1, 0, 1])

    def test_09_apu_space_fixed_two(self):
        self.assertEqual(self.doc["apuSpace"], 2)

    def test_10_trajectory_count(self):
        self.assertEqual(len(trajectories(self.doc)), 5)

    def test_11_flat_control_exact(self):
        self.assertEqual(trajectories(self.doc)["APU_FLAT_1"], [1]*9)

    def test_12_tl5_maturation_exact(self):
        self.assertEqual(trajectories(self.doc)["APU_MATURE_TL5"], [1,1,1,1,2,2,2,2,2])

    def test_13_tl6_maturation_exact(self):
        self.assertEqual(trajectories(self.doc)["APU_MATURE_TL6"], [1,1,1,1,1,2,2,2,2])

    def test_14_tl7_maturation_exact(self):
        self.assertEqual(trajectories(self.doc)["APU_MATURE_TL7"], [1,1,1,1,1,1,2,2,2])

    def test_15_tl8_maturation_exact(self):
        self.assertEqual(trajectories(self.doc)["APU_MATURE_TL8"], [1,1,1,1,1,1,1,2,2])

    def test_16_tl5_lower_bound_is_present(self):
        self.assertEqual(apu_tp_for_trajectory(self.doc, "APU_MATURE_TL5", 4), 1)
        self.assertEqual(apu_tp_for_trajectory(self.doc, "APU_MATURE_TL5", 5), 2)

    def test_17_unique_tl_local_candidate_sets(self):
        self.assertEqual(candidate_tps_for_tl(self.doc, 4), [1])
        self.assertEqual(candidate_tps_for_tl(self.doc, 5), [1,2])
        self.assertEqual(candidate_tps_for_tl(self.doc, 7), [1,2])
        self.assertEqual(candidate_tps_for_tl(self.doc, 8), [1,2,3])
        self.assertEqual(candidate_tps_for_tl(self.doc, 9), [1,2,3])

    def test_18_unique_tl_local_point_count(self):
        self.assertEqual(sum(len(candidate_tps_for_tl(self.doc, t)) for t in range(1,10)), 16)

    def test_19_plus3_is_boundary_only(self):
        self.assertNotIn(3, [v for row in trajectories(self.doc).values() for v in row])
        self.assertEqual(candidate_tps_for_tl(self.doc, 8)[-1], 3)
        self.assertEqual(candidate_tps_for_tl(self.doc, 9)[-1], 3)

    def test_20_no_count_cap_is_imposed(self):
        self.assertFalse(self.doc["stackingPolicy"]["installationCountCapImposed"])

    def test_21_stack_tiers_include_max(self):
        self.assertEqual(STACK_TIERS, (1,2,3,"MAX"))

    def test_22_architecture_population_unchanged(self):
        self.assertEqual(len(self.all), 22482)
        self.assertEqual(len(self.one), 16741)

    def test_23_tl1_base_cruiser_space_unchanged(self):
        self.assertEqual(_base_cruiser_space(self.m, 1), 31)

    def test_24_tl1_intact_base_fits_two_apus(self):
        cap = int(self.m.p("hull", 1)["capacity"])
        self.assertEqual((cap - _base_cruiser_space(self.m, 1)) // 2, 2)

    def test_25_broad_legal_space_contains_three_apu_carrier(self):
        x = select_carrier(self.m, self.one, tl=1, space_each=2, count=3, weapon="K")
        self.assertIsNotNone(x)

    def test_26_high_tl_broad_space_contains_larger_stack(self):
        self.assertGreaterEqual(max(max_stack(x,2) for x in self.one if x.tl==9), 5)

    def test_27_catalog_naming_collision_is_frozen_not_silently_changed(self):
        doc = json.loads(CATALOG.read_text(encoding="utf-8-sig"))
        text = json.dumps(doc)
        self.assertIn("Auxiliary Power Unit", text)
        self.assertIn("Auxiliary Reactor", text)
        self.assertTrue(self.doc["namingPolicy"]["authorityNamingReconciliationDeferred"])

    def test_28_resilience_uses_zero_flexible_tp_when_degraded(self):
        self.assertEqual(self.doc["resiliencePolicy"]["apuFlexibleTpWhenDegraded"], 0)
        self.assertTrue(self.doc["resiliencePolicy"]["fullIntegratedComponentDamageExecutionDeferred"])

    def test_29_combat_contexts_cover_tl5_plus1_and_plus2(self):
        c = combat_contexts(ROOT, STUDY, 5)
        self.assertEqual({tp for _,tp,_,_,_ in c}, {1,2})

    def test_30_combat_contexts_cover_tl8_plus3_boundary(self):
        c = combat_contexts(ROOT, STUDY, 8)
        self.assertEqual({tp for _,tp,_,_,_ in c}, {1,2,3})

    def test_31_combat_contexts_are_mirrored(self):
        c = combat_contexts(ROOT, STUDY, 8)
        self.assertTrue(any(v.side_a.auxiliary_reactor_count > 0 and v.side_b.auxiliary_reactor_count == 0 for v,*_ in c))
        self.assertTrue(any(v.side_b.auxiliary_reactor_count > 0 and v.side_a.auxiliary_reactor_count == 0 for v,*_ in c))

    def test_32_apu_power_is_additive(self):
        v,tp,tier,cnt,swap = next(x for x in combat_contexts(ROOT, STUDY, 8) if x[1]==3 and x[3]==2)
        stack = v.side_a if v.side_a.auxiliary_reactor_count else v.side_b
        self.assertEqual(stack.auxiliary_power_tp, 6)

    def test_33_static_products_exact_scale(self):
        with tempfile.TemporaryDirectory() as td:
            r = static_analysis(ROOT, STUDY, Path(td))
        self.assertEqual(r["trajectoryRows"], 45)
        self.assertEqual(r["densityRows"], 16)
        self.assertEqual(r["baseCruiserRows"], 9)
        self.assertEqual(r["legalStackSupportRows"], 288)
        self.assertEqual(r["resilienceRows"], 330)
        self.assertEqual(r["carrierRows"], 64)

    def test_34_plan_exact_scale(self):
        with tempfile.TemporaryDirectory() as td:
            r = plan(ROOT, STUDY, Path(td))
        self.assertEqual(r["stochasticVariants"], 1152)
        self.assertEqual(r["stochasticTurnSamples"], 5760000)
        self.assertEqual(r["combatContexts"], 384)
        self.assertEqual(r["combatCells"], 1152)
        self.assertEqual(r["combatTrials"], 2304000)

    def test_35_real_stochastic_variant_executes(self):
        l = select_carrier(self.m, self.one, tl=5, space_each=2, count=2, weapon="E")
        self.assertIsNotNone(l)
        d = dict(self.doc)
        d["stochasticTurnSamplesPerVariant"] = 20
        row, alloc = _stoch_one(str(ROOT), d, l, 2, 2, 2, 0, "DAMAGE_CRISIS")
        self.assertEqual(row["samples"], 20)
        self.assertEqual(row["total_apu_tp"], 4)
        self.assertTrue(alloc)

    def test_36_smoke_passes(self):
        with tempfile.TemporaryDirectory() as td:
            r = smoke(ROOT, STUDY, Path(td))
        self.assertTrue(r["passed"])
        self.assertEqual(r["probes"], 6)


if __name__ == "__main__":
    unittest.main()
