from __future__ import annotations
import tempfile, unittest
from pathlib import Path

from starcluster_research.study import load_json
from starcluster_research.four_main_ladder_synthesis import (
    E_FACTORS, E_PAIRWISE_CANDIDATES_PER_TL, E_TOTAL_CANDIDATES_PER_TL,
    E_COMBATS, E_SMOKE_COMBATS, SCREEN_COMBATS, DEEP_COMBATS, SUBSTANTIVE_COMBATS,
    PACKAGE_COUNT, SCREEN_CONTEXTS, energy_candidate_ledger, energy_factor_levels,
    validate_study, validate_population, run_plan, run_energy_batch,
    _screen_contexts, _k_ladders, _missile_ladder_options, _read_cp152_evidence,
)

ROOT=Path(__file__).resolve().parents[3]
STUDY=ROOT/'docs/archive/testing/pre-cp165-active/cp153_four_main_ladder_synthesis_study_v0_1.json'

class Cp153FourMainLadderSynthesisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=load_json(STUDY)
        cls.ledger=energy_candidate_ledger(ROOT,cls.doc)

    def test_01_study_contract_and_total_scale(self):
        self.assertEqual([],validate_study(self.doc)); self.assertEqual([],validate_population(ROOT,self.doc))
        self.assertEqual(102346800,SUBSTANTIVE_COMBATS)
    def test_02_energy_design_has_eleven_active_dimensions(self):
        self.assertEqual(11,len(E_FACTORS)); self.assertIn('strain_limit',E_FACTORS); self.assertIn('standard_damage',E_FACTORS)
    def test_03_energy_design_is_422_per_tl(self):
        self.assertEqual(422,E_TOTAL_CANDIDATES_PER_TL); self.assertEqual(3798,len(self.ledger))
        for tl in range(1,10): self.assertEqual(422,sum(int(r['tl'])==tl for r in self.ledger))
    def test_04_pairwise_isolation_core_is_264_per_tl(self):
        self.assertEqual(264,E_PAIRWISE_CANDIDATES_PER_TL)
        for tl in range(1,10): self.assertEqual(264,sum(int(r['tl'])==tl and str(r['design_class']).startswith('pairwise_') for r in self.ledger))
    def test_05_strain_limit_sweeps_one_through_four(self):
        for tl in range(1,10): self.assertEqual({1,2,3,4},{int(r['candidate_strain_limit']) for r in self.ledger if int(r['tl'])==tl})
    def test_06_strain_is_pairwise_crossed_with_every_other_factor(self):
        tl=6; rows=[r for r in self.ledger if int(r['tl'])==tl and str(r['design_class']).startswith('pairwise_')]; center=self.doc['energyClosureCenters'][str(tl)]
        for f in E_FACTORS:
            if f=='strain_limit': continue
            vals=energy_factor_levels(self.doc,tl)[f]; seen=set()
            for r in rows:
                others=[x for x in E_FACTORS if x not in (f,'strain_limit')]
                if all(int(r[f'candidate_{x}'])==int(center[x]) for x in others): seen.add((int(r[f'candidate_{f}']),int(r['candidate_strain_limit'])))
            self.assertEqual(12,len(seen),f)
    def test_07_asymmetric_early_tp_gap_levels_keep_distinct_codes(self):
        rows=[r for r in self.ledger if int(r['tl'])==1]
        by={int(r['candidate_standard_gap']):int(r['code_standard_gap']) for r in rows if int(r['active_factor_count'])==1 and int(r['candidate_standard_gap'])!=1}
        self.assertEqual({2:1,3:2},by)
    def test_08_compound_blocks_both_survive_dedup(self):
        for tl in range(1,10):
            classes={r['design_class'] for r in self.ledger if int(r['tl'])==tl}
            self.assertIn('compound_oa81_A',classes); self.assertIn('compound_oa81_B',classes)
    def test_09_compound_b_reaches_strain_four(self):
        self.assertTrue(any(r['design_class']=='compound_oa81_B' and int(r['candidate_strain_limit'])==4 for r in self.ledger))
    def test_10_energy_mode_order_is_physical_for_every_tested_candidate(self):
        for r in self.ledger: self.assertLess(int(r['candidate_low_damage']),int(r['candidate_standard_damage'])); self.assertLessEqual(int(r['candidate_standard_damage']),int(r['candidate_overload_damage']))
    def test_11_energy_doctrine_preserves_low_standard_overload_roles(self):
        d=self.doc['energyClosureDoctrine']; self.assertIn('power-conservation',d['Low']); self.assertIn('normal',d['Standard']); self.assertIn('reserved',d['Overload']); self.assertIn('emergency',d['ForcedOverload'])
    def test_12_energy_safe_only_forced_overload_policy_is_explicit(self):
        self.assertTrue(all('safe_only' in r['forced_overload_policy'] for r in self.ledger))
    def test_13_fixed_environment_defers_aux_and_reactor_tuning(self):
        self.assertIn('AUX',self.doc['heldFixed']); self.assertIn('Reactor ladder',self.doc['heldFixed']); self.assertIn('AUX lifetime-value sweep',self.doc['deferred']); self.assertIn('final Reactor/TP supply tuning',self.doc['deferred'])
    def test_14_cp152_native_evidence_is_hash_locked(self):
        s=_read_cp152_evidence(ROOT); self.assertEqual(152,int(s['checkpoint'])); self.assertEqual(48195000,int(s['substantiveCombatTrials']))
    def test_15_screen_panel_is_full_pair_stratum_with_one_resource(self):
        rows=_screen_contexts(ROOT,self.doc); self.assertEqual(SCREEN_CONTEXTS,len(rows)); self.assertEqual(1370,len({(r['tl'],r['side_a_weapon'],r['side_b_weapon'],r['scenario_stratum']) for r in rows}))
    def test_16_kinetic_is_synthesized_from_cp152_without_resweep(self):
        ladders=_k_ladders(ROOT,self.doc); self.assertEqual(6,len(ladders)); self.assertTrue(all(len(x)==9 for x in ladders))
    def test_17_gp_missile_has_three_coherent_whole_ladder_options(self):
        opts=_missile_ladder_options(ROOT,self.doc,'M_GP'); self.assertEqual(3,len(opts)); self.assertTrue(all(all(o[t]>=o[t-1] for t in range(2,10)) for o in opts))
    def test_18_swarmer_has_three_coherent_tl2_tl9_options(self):
        opts=_missile_ladder_options(ROOT,self.doc,'M_SWARMER'); self.assertEqual(3,len(opts)); self.assertTrue(all(set(o)==set(range(2,10)) for o in opts))
    def test_19_plan_reproduces_all_stage_counts(self):
        with tempfile.TemporaryDirectory() as td:
            s=run_plan(ROOT,STUDY,Path(td)); self.assertTrue(s['passed']); self.assertEqual(E_COMBATS,s['energyCombatTrials']); self.assertEqual(E_SMOKE_COMBATS,s['energySmokeCombatTrials']); self.assertEqual(SCREEN_COMBATS,s['screenCombatTrials']); self.assertEqual(DEEP_COMBATS,s['deepCombatTrials']); self.assertEqual(PACKAGE_COUNT,s['wholeLadderPackages'])
    def test_20_live_energy_center_executes_real_stage_a_smoke_contexts(self):
        with tempfile.TemporaryDirectory() as td:
            s=run_energy_batch(ROOT,STUDY,Path(td),jobs=1,tl=1,candidate_start=0,candidate_end=1,trials=1,smoke_panel=True); self.assertTrue(s['passed']); self.assertEqual(50,s['combatTrials']); self.assertEqual(0,s['errors'])
    def test_21_no_automatic_promotion_or_stage_b(self):
        self.assertFalse(self.doc['automaticPromotion']); self.assertFalse(self.doc['stageBAutomatic']); self.assertFalse(self.doc['tuningAllowed'])

if __name__=='__main__': unittest.main()
