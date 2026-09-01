from __future__ import annotations
import csv, json, tempfile, unittest
from pathlib import Path

from starcluster_research.direct_fire_joint_refinement import (
    K_CANDIDATES_PER_TL,E_CANDIDATES_PER_TL,K_COMBATS,E_COMBATS,JOINT_COMBATS,SUBSTANTIVE_COMBATS,SMOKE_COMBATS,
    K_FACTORS,E_FACTORS,k_candidate_ledger,e_candidate_ledger,k_factor_levels,e_factor_levels,energy_space_envelope,
    validate_study,validate_population,run_lane_batch,run_plan,_apply_cp151_center,_base_matrix,
)
from starcluster_research.study import load_json
from starcluster_research.whole_combat_stage_a_response_surface import SIDE_TELEMETRY_FIELDS

ROOT=Path(__file__).resolve().parents[3]
STUDY=ROOT/'docs/archive/testing/pre-cp165-active/cp152_direct_fire_joint_refinement_study_v0_1.json'

class Cp152DirectFireJointRefinementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=load_json(STUDY)
        cls.k=k_candidate_ledger(ROOT,cls.doc)
        cls.e=e_candidate_ledger(ROOT,cls.doc)

    def test_01_study_contract_and_scale(self):
        self.assertEqual([],validate_study(self.doc)); self.assertEqual([],validate_population(ROOT,self.doc))
        self.assertEqual(48195000,SUBSTANTIVE_COMBATS); self.assertEqual(218700,SMOKE_COMBATS)
    def test_02_k_is_full_five_factor_cube(self):
        self.assertEqual(243,K_CANDIDATES_PER_TL); self.assertEqual(2187,len(self.k)); self.assertEqual(5,len(K_FACTORS))
        for tl in range(1,10): self.assertEqual(243,sum(int(r['tl'])==tl for r in self.k))
    def test_03_energy_is_broad_eleven_factor_oa(self):
        self.assertEqual(243,E_CANDIDATES_PER_TL); self.assertEqual(2187,len(self.e)); self.assertEqual(11,len(E_FACTORS))
        for tl in range(1,10): self.assertEqual(243,sum(int(r['tl'])==tl for r in self.e))
    def test_04_k_damage_uses_new_integer_half_steps(self):
        for tl in range(1,10):
            vals=set(k_factor_levels(ROOT,self.doc,tl)['damage'].values()); self.assertEqual(3,len(vals)); self.assertTrue(all(isinstance(v,int) for v in vals))
    def test_05_k_late_accuracy_includes_non_regressing_options(self):
        self.assertGreaterEqual(max(k_factor_levels(ROOT,self.doc,7)['accuracy'].values()),30)
        self.assertGreaterEqual(max(k_factor_levels(ROOT,self.doc,8)['accuracy'].values()),30)
        self.assertGreaterEqual(max(k_factor_levels(ROOT,self.doc,9)['accuracy'].values()),30)
    def test_06_k_spen_tp_ammo_space_not_swept(self):
        self.assertEqual(('damage','accuracy','standard_range','max_range','apen'),K_FACTORS)
    def test_07_energy_damage_bounds_are_broader_late(self):
        for tl in range(6,10):
            lev=e_factor_levels(ROOT,self.doc,tl)['standard_damage']; self.assertEqual(6,lev[1]-lev[-1])
    def test_08_energy_accuracy_can_recover_late(self):
        for tl in (7,8,9): self.assertGreaterEqual(e_factor_levels(ROOT,self.doc,tl)['accuracy'][1],35 if tl>=8 else 37)
    def test_09_energy_sweeps_all_three_power_modes_and_strain(self):
        for name in ('low_tp_delta','standard_gap_delta','overload_gap_delta','strain_limit'): self.assertIn(name,E_FACTORS)
    def test_10_energy_apen_remains_zero_and_spen_is_swept(self):
        self.assertIn('spen',E_FACTORS); self.assertNotIn('apen',E_FACTORS)
    def test_11_energy_mode_telemetry_is_exported(self):
        for f in ('energy_low_shots','energy_standard_shots','energy_overload_shots','energy_overload_strain_added','energy_max_strain'): self.assertIn(f,SIDE_TELEMETRY_FIELDS)
    def test_12_defenses_missiles_and_reactor_are_held_fixed(self):
        self.assertEqual(['Hull capacity','Shield capacity','Armor capacity','Shield Regen=2','Armor Repair=2','GP Missile center','Swarmer integer center','PDS','AUX','ECM/ECCM/Sensor','Reactor ladder','DEF/RES'],self.doc['heldFixed'])
    def test_13_cp151_center_uses_x2_and_neutral_regen(self):
        m=_apply_cp151_center(_base_matrix(ROOT,self.doc,'R1_CENTRAL_NO_MAJOR'))
        self.assertEqual(24,m.p('hull',1)['hullPoints']); self.assertEqual(2,m.p('shield',1)['tacticalRechargePerTp'])
    def test_14_energy_space_is_separate_headroom_lane(self):
        rows=energy_space_envelope(ROOT,self.doc); self.assertEqual(2250,len(rows)); self.assertTrue(all(int(r['combat_effect_modeled'])==0 for r in rows))
    def test_15_plan_writes_expected_scale(self):
        with tempfile.TemporaryDirectory() as td:
            s=run_plan(ROOT,STUDY,Path(td)); self.assertTrue(s['passed']); self.assertEqual(K_COMBATS,s['kCombatTrials']); self.assertEqual(E_COMBATS,s['eCombatTrials']); self.assertEqual(JOINT_COMBATS,s['jointCombatTrials'])
    def test_16_live_k_candidate_executes_real_context(self):
        with tempfile.TemporaryDirectory() as td:
            s=run_lane_batch(ROOT,STUDY,Path(td),'K',jobs=1,tl=1,candidate_start=121,candidate_end=122,trials=1,smoke_panel=True); self.assertTrue(s['passed']); self.assertEqual(50,s['combatTrials']); self.assertEqual(0,s['errors'])
    def test_17_live_energy_candidate_executes_real_context(self):
        with tempfile.TemporaryDirectory() as td:
            s=run_lane_batch(ROOT,STUDY,Path(td),'E',jobs=1,tl=9,candidate_start=121,candidate_end=122,trials=1,smoke_panel=True); self.assertTrue(s['passed']); self.assertEqual(50,s['combatTrials']); self.assertEqual(0,s['errors'])
    def test_18_no_automatic_promotion_or_stage_b(self):
        self.assertFalse(self.doc['automaticPromotion']); self.assertFalse(self.doc['stageBAutomatic']); self.assertFalse(self.doc['tuningAllowed'])

if __name__=='__main__': unittest.main()
