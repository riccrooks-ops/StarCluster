from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from starcluster_research.study import load_json
from starcluster_research.pds_architecture_resynthesis import (
    AMM_AMMO,
    BASELINE_TRIALS,
    DEEP_LADDERS,
    K_AMMO,
    LADDERS_PER_FAMILY,
    SCREEN_TRIALS,
    _compatible,
    _template_filter,
    _templates,
    candidate_ledger,
    deep_contexts,
    merge_deep,
    primary_contexts,
    robustness_contexts,
    run_candidate_batch,
    run_plan,
    synthesize_ladders,
    validate_population,
    validate_study,
)

ROOT = Path(__file__).resolve().parents[3]
STUDY = ROOT / "docs/archive/testing/pre-cp165-active/cp155_pds_architecture_resynthesis_study_v0_1.json"


class Cp155PdsArchitectureResynthesisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = load_json(STUDY)
        cls.rows = candidate_ledger(ROOT, cls.doc)

    def test_01_study_and_population_contract(self):
        self.assertEqual([], validate_study(self.doc))
        self.assertEqual([], validate_population(ROOT, self.doc))

    def test_02_population_is_1846_candidate_tl_points(self):
        self.assertEqual(1846, len(self.rows))

    def test_03_exact_family_totals(self):
        got = {f: sum(r["family"] == f for r in self.rows) for f in ("Kinetic", "Energy", "AMM")}
        self.assertEqual({"Kinetic": 576, "Energy": 945, "AMM": 325}, got)

    def test_04_exact_family_tl_counts(self):
        self.assertEqual([64] * 9, [sum(r["family"] == "Kinetic" and r["tl"] == tl for r in self.rows) for tl in range(1, 10)])
        self.assertEqual([105] * 9, [sum(r["family"] == "Energy" and r["tl"] == tl for r in self.rows) for tl in range(1, 10)])
        self.assertEqual([25, 25, 25, 25, 45, 45, 45, 45, 45], [sum(r["family"] == "AMM" and r["tl"] == tl for r in self.rows) for tl in range(1, 10)])

    def test_05_k_boundary_reaches_zero_and_rc2(self):
        ks = [r for r in self.rows if r["family"] == "Kinetic"]
        self.assertEqual(0, min(r["base_chance_pp"] for r in ks))
        self.assertEqual({1, 2}, {r["reaction_capacity"] for r in ks})
        self.assertEqual({1, 2, 3, 4}, {r["readiness_tp"] for r in ks})

    def test_06_k_ammo_is_fixed_not_swept(self):
        self.assertEqual({K_AMMO}, {r["ammo"] for r in self.rows if r["family"] == "Kinetic"})
        self.assertEqual(75, K_AMMO)

    def test_07_energy_keeps_rc1_overcharged_and_safe_states(self):
        es = [r for r in self.rows if r["family"] == "Energy"]
        self.assertEqual({"RC1", "RC2_OVERCHARGED", "RC2_SAFE"}, {r["mode"] for r in es})

    def test_08_energy_overcharge_is_strain_one_or_two_only(self):
        vals = {r["strain_limit"] for r in self.rows if r["family"] == "Energy" and r["mode"] == "RC2_OVERCHARGED"}
        self.assertEqual({1, 2}, vals)

    def test_09_energy_rc2_always_costs_more_tp_than_rc1(self):
        for r in self.rows:
            if r["family"] == "Energy" and r["reaction_capacity"] == 2:
                self.assertGreater(int(r["rc2_tp"]), int(r["rc1_tp"]))

    def test_10_amm_ammo_is_fixed_and_deliberately_exhaustible(self):
        self.assertEqual(25, AMM_AMMO)
        self.assertEqual({AMM_AMMO}, {r["ammo"] for r in self.rows if r["family"] == "AMM"})

    def test_11_amm_rc3_is_range_one_and_not_before_tl5(self):
        aa = [r for r in self.rows if r["family"] == "AMM"]
        self.assertFalse(any(r["reaction_capacity"] == 3 for r in aa if r["tl"] < 5))
        self.assertTrue(all((r["reaction_capacity"] == 3) == bool(r["range_one"]) for r in aa))

    def test_12_k_and_e_never_acquire_rc3_or_range_one(self):
        self.assertFalse(any(r["family"] != "AMM" and (r["reaction_capacity"] > 2 or r["range_one"]) for r in self.rows))

    def test_13_primary_contexts_are_direct_fire_defenders_only(self):
        rows = primary_contexts(ROOT, self.doc)
        self.assertEqual(1560, len(rows))
        self.assertEqual({"K1", "E7"}, {r["defender"] for r in rows})
        self.assertEqual({"PRIMARY"}, {r["context_class"] for r in rows})

    def test_14_primary_contexts_cross_all_five_resources(self):
        self.assertEqual(5, len({r["resource_ensemble_id"] for r in primary_contexts(ROOT, self.doc)}))

    def test_15_robustness_contexts_are_secondary_missile_defenders(self):
        rows = robustness_contexts(ROOT, self.doc)
        self.assertEqual(300, len(rows))
        self.assertEqual({"ROBUSTNESS"}, {r["context_class"] for r in rows})
        self.assertTrue({r["defender"] for r in rows}.issubset({"M2", "SW2"}))
        self.assertEqual({"R1_CENTRAL_NO_MAJOR"}, {r["resource_ensemble_id"] for r in rows})

    def test_16_deep_context_count_is_1860(self):
        self.assertEqual(1860, len(deep_contexts(ROOT, self.doc)))

    def test_17_tl1_respects_swarmer_unlock(self):
        self.assertFalse(any(r["attacker"] == "SW2" or r["defender"] == "SW2" for r in deep_contexts(ROOT, self.doc) if r["tl"] == 1))

    def test_18_plan_reproduces_exact_15511200_scale(self):
        with tempfile.TemporaryDirectory() as td:
            s = run_plan(ROOT, STUDY, Path(td))
        self.assertTrue(s["passed"])
        self.assertEqual(312000, s["baselineCombatTrials"])
        self.assertEqual(9619200, s["screenCombatTrials"])
        self.assertEqual(5580000, s["deepCombatTrials"])
        self.assertEqual(15511200, s["substantiveCombatTrials"])
        self.assertEqual(SCREEN_TRIALS, 30)
        self.assertEqual(BASELINE_TRIALS, 200)

    def test_19_selector_guardrail_explicitly_forbids_global_equalization(self):
        text = self.doc["balancePhilosophy"]["forbiddenSelectorObjective"].lower()
        self.assertIn("no global distance-to-50", text)
        self.assertIn("no inter-family", text)
        code = (ROOT / "tools/simulation/starcluster_research/pds_architecture_resynthesis.py").read_text(encoding="utf-8")
        self.assertNotIn("triad_selection_score", code)
        self.assertNotIn("abs(decisive-.5)", code)

    def test_20_cp142_registers_v17_v19_as_latest_full_combat_reference(self):
        d = load_json(ROOT / "docs/archive/testing/pre-cp165-active/cp142_combat_surface_deep_reconciliation_study_v0_1.json")
        self.assertEqual("Combat Model Lab v17-v19", d["latestFullCombatEvidence"])
        self.assertIn("effective per-attempt probability", d["pdsChanceSemanticRule"])

    def test_21_templates_force_architecture_coverage(self):
        t = _templates()
        self.assertEqual(10, len(t["Kinetic"]))
        self.assertEqual(10, len(t["Energy"]))
        self.assertEqual(10, len(t["AMM"]))
        self.assertTrue(any("RC2-TL6" in x[0] for x in t["Kinetic"]))
        self.assertTrue(any("SAFE" in x[0] for x in t["Energy"]))
        self.assertTrue(any("RC3-TL7" in x[0] for x in t["AMM"]))

    def test_22_template_filters_match_intended_states(self):
        k1 = {"reaction_capacity": 1}; k2 = {"reaction_capacity": 2}
        self.assertTrue(_template_filter("Kinetic", "K-RC2-TL6-LOW", 5, k1))
        self.assertTrue(_template_filter("Kinetic", "K-RC2-TL6-LOW", 6, k2))
        eoc = {"mode": "RC2_OVERCHARGED", "strain_limit": 1}; esafe = {"mode": "RC2_SAFE", "strain_limit": 0}
        self.assertTrue(_template_filter("Energy", "E-OC-TL4-SL1-SAFE-TL7", 6, eoc))
        self.assertTrue(_template_filter("Energy", "E-OC-TL4-SL1-SAFE-TL7", 7, esafe))
        a3 = {"reaction_capacity": 3, "range_one": 1}
        self.assertTrue(_template_filter("AMM", "A-RC2-TL3-RC3-TL7", 7, a3))

    def test_23_hard_technology_constraints_reject_regression(self):
        a = {"base_chance_pp": 10, "reaction_capacity": 2, "readiness_tp": 2, "range_one": 0}
        b = {"base_chance_pp": 5, "reaction_capacity": 2, "readiness_tp": 2, "range_one": 0}
        self.assertFalse(_compatible(a, b, "Kinetic"))
        c = {"base_chance_pp": 10, "reaction_capacity": 2, "readiness_tp": 3, "range_one": 0}
        self.assertFalse(_compatible(a, c, "Kinetic"))

    def test_24_synthesis_can_build_all_30_stratified_ladders(self):
        fields = [
            "family", "candidate_id", "tl", "candidate_index", "base_chance_pp", "reaction_capacity", "rc1_tp", "rc2_tp", "rc3_tp", "readiness_tp", "ammo", "range_one", "safe_rc", "extra_strain", "strain_limit", "mode", "promotion_allowed",
            "trials", "defender_wins", "attacker_wins", "draws", "candidate_defender_decisive_share", "no_pds_defender_decisive_share", "protection_uplift", "gp_protection_uplift", "sw_protection_uplift", "k_defender_uplift", "e_defender_uplift", "pds_attempts", "pds_intercepts", "intercept_rate_per_attempt", "pds_tp_per_attempt", "overcharge_attempt_share", "range_one_attempt_share",
        ]
        with tempfile.TemporaryDirectory() as td:
            d = Path(td); merged = d / "merged"; out = d / "out"; merged.mkdir()
            with (merged / "pds_candidate_summary.csv").open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
                for r in self.rows:
                    uplift = 0.01 * int(r["base_chance_pp"]) + 0.04 * (int(r["reaction_capacity"]) - 1)
                    x = {k: r.get(k, "") for k in fields}
                    x.update({"trials": 100, "defender_wins": 55, "attacker_wins": 45, "draws": 0, "candidate_defender_decisive_share": .55, "no_pds_defender_decisive_share": .40, "protection_uplift": uplift, "gp_protection_uplift": uplift, "sw_protection_uplift": uplift, "k_defender_uplift": uplift, "e_defender_uplift": uplift, "pds_attempts": 10, "pds_intercepts": 2, "intercept_rate_per_attempt": .2, "pds_tp_per_attempt": max(1, int(r["readiness_tp"])) / 2, "overcharge_attempt_share": .15 if r["mode"] == "RC2_OVERCHARGED" else 0, "range_one_attempt_share": .2 if r["range_one"] else 0})
                    w.writerow(x)
            s = synthesize_ladders(ROOT, STUDY, merged, out)
            self.assertTrue(s["passed"], s["failedGates"])
            with (out / "pds_ladder_candidates.csv").open(encoding="utf-8-sig", newline="") as f:
                rr = list(csv.DictReader(f))
        self.assertEqual(DEEP_LADDERS * 9, len(rr))
        self.assertEqual(30, len({r["ladder_id"] for r in rr}))
        self.assertEqual(LADDERS_PER_FAMILY, 10)

    def test_25_live_kinetic_zero_base_rc2_smoke(self):
        with tempfile.TemporaryDirectory() as td:
            s = run_candidate_batch(ROOT, STUDY, Path(td), "Kinetic", 6, 7, 8, jobs=1, trials=1, smoke=True)
            self.assertTrue(s["passed"]); self.assertEqual(6, s["combatTrials"])

    def test_26_live_energy_overcharged_rc2_smoke(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td); s = run_candidate_batch(ROOT, STUDY, d, "Energy", 6, 24, 25, jobs=1, trials=3, smoke=True); self.assertTrue(s["passed"])
            with (d / "pds_candidate_context_results.csv").open(encoding="utf-8-sig", newline="") as f:
                rr = list(csv.DictReader(f))
        self.assertGreater(sum(float(r["mean_b_pds_overcharge_attempts"]) for r in rr), 0.0)
        self.assertGreater(max(int(float(r["max_pds_strain"])) for r in rr), 0)

    def test_27_live_amm_rc3_range_one_smoke(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td); s = run_candidate_batch(ROOT, STUDY, d, "AMM", 7, 14, 15, jobs=1, trials=2, smoke=True); self.assertTrue(s["passed"])
            with (d / "pds_candidate_context_results.csv").open(encoding="utf-8-sig", newline="") as f:
                rr = list(csv.DictReader(f))
        self.assertGreater(sum(float(r["mean_b_pds_range_one_attempts"]) for r in rr), 0.0)

    def test_28_no_automatic_promotion_and_deferred_final_tp(self):
        self.assertFalse(self.doc["automaticPromotion"])
        self.assertFalse(self.doc["tuningAllowed"])
        self.assertIn("final Reactor/TP supply tuning", self.doc["deferred"])
        self.assertIn("simultaneous multi-Flight arrival balance weighting", self.doc["deferred"])


if __name__ == "__main__":
    unittest.main()
