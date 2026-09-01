from __future__ import annotations

import hashlib
import sys
import unittest
from dataclasses import replace
from pathlib import Path

REPO=Path(__file__).resolve().parents[3]
SIM=REPO/'tools'/'simulation'
if str(SIM) not in sys.path: sys.path.insert(0,str(SIM))

from starcluster_research.canonical_combat import CANONICAL_COMBAT_KERNEL_VERSION, _cp147_expected_terminal_loss, run_trial_full_map
from starcluster_research.combat_surface_deep_reconciliation import build_deep_resource_matrix
from starcluster_research.ecology import CONTEXTUAL_COMBAT_DOCTRINE, UTILITY_COMBAT_DOCTRINE, _begin_turn_recharge, _create_side, _plan_once
from starcluster_research.stage_a_diagnostic_attribution import _diag_task, _worker_init
from starcluster_research.stage_a_integration_analysis import _read_csv, _resource_rows, bind_scenario
from starcluster_research.study import load_json
from starcluster_research.tactical_package_utility import TacticalPackageCandidate, choose_tactical_package, decide_contract_case
from starcluster_research.tactical_package_utility_validation import validate_population, validate_study
from starcluster_research.canonical_combat import FullMapMissile
from starcluster_research.tactical_geometry import HexCoord

STUDY=REPO/'docs/archive/testing/pre-cp165-active/cp147_tactical_package_utility_study_v0_1.json'
FIXTURE=REPO/'docs/archive/testing/pre-cp165-active/cp147_tactical_package_utility_parity_fixtures_v0_1.json'

class Cp147TacticalPackageUtilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=load_json(STUDY); cls.cp144=load_json(REPO/cls.doc['stageAStudy'])
        cls.selection=_read_csv(REPO/cls.doc['diagnosticReplayManifest']); cls.stage=_read_csv(REPO/cls.doc['stageAExperimentManifest']); cls.stage_by={r['scenario_id']:r for r in cls.stage}
        cls.er,cls.tr=_resource_rows(REPO,cls.cp144); cls.accepted=_read_csv(REPO/cls.doc['acceptedCp146ContextualResults']); cls.accepted_by={r['scenario_id']:r for r in cls.accepted}
    @classmethod
    def source(cls,sel):
        x=dict(cls.stage_by[sel['scenario_id']]);x.update(sel);return x
    @classmethod
    def bound(cls,pred):
        sel=next(r for r in cls.selection if pred(r)); src=cls.source(sel); m=build_deep_resource_matrix(REPO,cls.doc['matrix'],src['resource_ensemble_id'],cls.er,cls.tr); return src,m,bind_scenario(m,src)

    def test_01_study_is_logic_only_hash_locked_and_full_population(self):
        self.assertEqual([],validate_study(self.doc)); self.assertEqual([],validate_population(REPO,self.doc))
        self.assertFalse(self.doc['tuningAllowed']); self.assertFalse(self.doc['automaticPromotion']); self.assertFalse(self.doc['stageBAutomatic']); self.assertEqual(12600,self.doc['expectedTotalCombatTrials'])
        self.assertEqual(self.doc['matrixSha256'],hashlib.sha256((REPO/self.doc['matrix']).read_bytes()).hexdigest())

    def test_02_shared_selector_fixture_matches_python_contract(self):
        fx=load_json(FIXTURE); self.assertGreaterEqual(len(fx['cases']),8)
        for case in fx['cases']: self.assertEqual(case['expectedSelectedId'],decide_contract_case(case)['selectedId'],case['id'])

    def test_03_selector_validates_inputs(self):
        with self.assertRaises(ValueError): TacticalPackageCandidate('',1,1,1,1,0,0)
        with self.assertRaises(ValueError): TacticalPackageCandidate('bad',1,1,1,0,1,0)
        with self.assertRaises(ValueError): choose_tactical_package([TacticalPackageCandidate('a',2,1,1,1,0,0)],1)

    def test_04_cp146_replay_reproduces_accepted_native_row(self):
        sel=self.selection[0]; src=self.source(sel); _worker_init(str(REPO),self.doc['matrix'],self.er,self.tr)
        got=_diag_task((src,25,int(self.doc['masterSeed']),CONTEXTUAL_COMBAT_DOCTRINE)); old=self.accepted_by[src['scenario_id']]
        for key,value in old.items():
            if value=='': self.assertEqual('',str(got.get(key,'')))
            else:
                try:self.assertAlmostEqual(float(value),float(got[key]),places=12,msg=key)
                except ValueError:self.assertEqual(value,str(got[key]),key)

    def test_05_unknown_hidden_weapon_family_does_not_change_utility_plan(self):
        _,m,b=self.bound(lambda r:r['side_b_weapon']=='E' and r['resource_ensemble_id']=='R1_CENTRAL_NO_MAJOR')
        own=_create_side(m,b.variant.side_b,0); te=_create_side(m,b.variant.side_a,1); tk=_create_side(m,replace(b.variant.side_a,weapon_family='Kinetic',missile_payload='GP'),1); own.known_opponent_weapon_family=None
        pe=_plan_once(m,own,te,2,0,8,False,UTILITY_COMBAT_DOCTRINE); pk=_plan_once(m,own,tk,2,0,8,False,UTILITY_COMBAT_DOCTRINE)
        keys=('sensor_mode','pds_power','pds_rc','hardener_active','ecm_on','eccm_on','weapon_plans','weapon_actions','package_id')
        self.assertEqual({k:pe[k] for k in keys},{k:pk[k] for k in keys}); self.assertEqual('Unknown',pe['opponent_weapon_knowledge'])

    def test_06_active_sensor_is_normal_and_passive_is_only_a_package_fallback(self):
        _,m,b=self.bound(lambda r:r['side_b_weapon']=='E' and r['resource_ensemble_id']=='R1_CENTRAL_NO_MAJOR')
        own=_create_side(m,b.variant.side_b,0); target=_create_side(m,b.variant.side_a,1)
        hi=_plan_once(m,own,target,1,0,10,False,UTILITY_COMBAT_DOCTRINE); self.assertNotEqual('passive',hi['sensor_mode'])
        low=_plan_once(m,own,target,1,0,3,False,UTILITY_COMBAT_DOCTRINE); self.assertTrue(any(x is not None for x in low['weapon_plans']))

    def test_07_distant_inbound_missile_does_not_force_terminal_pds_package(self):
        _,m,b=self.bound(lambda r:r['side_b_weapon']=='E' and r['resource_ensemble_id']=='R1_CENTRAL_NO_MAJOR')
        own=_create_side(m,b.variant.side_b,0); target=_create_side(m,b.variant.side_a,1); own.known_opponent_weapon_family='Missile'; own.known_opponent_missile_profile='GP'; own.cp147_terminal_threats=()
        p=_plan_once(m,own,target,2,1,8,False,UTILITY_COMBAT_DOCTRINE)
        self.assertEqual(0,p['terminal_threat_subflights']); self.assertEqual(0,p['pds_rc'])

    def test_08_non_hull_terminal_threat_does_not_divert_sole_legal_main(self):
        _,m,b=self.bound(lambda r:r['side_b_weapon']=='E' and r['resource_ensemble_id']=='R1_CENTRAL_NO_MAJOR')
        own=_create_side(m,replace(b.variant.side_b,pds_family=None),0);target=_create_side(m,b.variant.side_a,1);own.known_opponent_weapon_family='Missile';own.cp147_terminal_threats=((20.0,0,0.0),)
        p=_plan_once(m,own,target,1,1,10,False,UTILITY_COMBAT_DOCTRINE)
        self.assertTrue(p['weapon_core_opportunity']); self.assertEqual(['ship'],p['weapon_actions']); self.assertFalse(p['critical_hull_threat'])

    def test_09_immediate_hull_risk_can_divert_sole_legal_main_when_defense_utility_wins(self):
        _,m,b=self.bound(lambda r:r['side_b_weapon']=='E' and r['resource_ensemble_id']=='R1_CENTRAL_NO_MAJOR')
        own=_create_side(m,replace(b.variant.side_b,pds_family=None),0);target=_create_side(m,b.variant.side_a,1);own.known_opponent_weapon_family='Missile';own.cp147_terminal_threats=((100.0,0,10.0),)
        p=_plan_once(m,own,target,1,1,10,False,UTILITY_COMBAT_DOCTRINE)
        self.assertTrue(p['critical_hull_threat']); self.assertIn('hold_missile',p['weapon_actions'])

    def test_10_held_main_uses_terminal_missile_track_not_distant_ship_track(self):
        _,m,b=self.bound(lambda r:r['side_b_weapon']=='E' and r['resource_ensemble_id']=='R1_CENTRAL_NO_MAJOR')
        own=_create_side(m,replace(b.variant.side_b,pds_family=None),0);target=_create_side(m,b.variant.side_a,1);own.known_opponent_weapon_family='Missile';own.cp147_terminal_threats=((20.0,0,1.0),)
        rng=int(m.weapon_profile('Energy',own.build.tl).get('maxRange',m.weapon_profile('Energy',own.build.tl).get('range')))
        p=_plan_once(m,own,target,rng+1,1,10,False,UTILITY_COMBAT_DOCTRINE); self.assertFalse(p['weapon_core_opportunity']); self.assertIn('hold_missile',p['weapon_actions'])

    def test_11_expected_terminal_loss_uses_current_layers_not_raw_yield(self):
        _,m,b=self.bound(lambda r:r['side_b_weapon']=='E' and r['resource_ensemble_id']=='R1_CENTRAL_NO_MAJOR')
        own=_create_side(m,b.variant.side_b,0); missile=FullMapMissile('A','B',HexCoord(0,0),HexCoord(0,0),100.0,0,0,100,1,10)
        structural,hull=_cp147_expected_terminal_loss(m,own,missile); self.assertGreater(structural,0); self.assertLessEqual(hull,structural); self.assertLessEqual(structural,own.shield+own.armor_integrity+own.hull)

    def test_12_naturally_exercises_held_main_on_matched_diagnostic_identity(self):
        sel=next(r for r in self.selection if r['scenario_id']=='SCN-32971254580E1875');src=self.source(sel);_worker_init(str(REPO),self.doc['matrix'],self.er,self.tr)
        got=_diag_task((src,25,int(self.doc['masterSeed']),UTILITY_COMBAT_DOCTRINE)); self.assertGreater(float(got['b_cp147_held_package_selections']),0); self.assertGreater(float(got['b_cp146_held_main_attempts']),0)

    def test_13_no_invalid_sole_main_diversion_in_natural_held_identity(self):
        sel=next(r for r in self.selection if r['scenario_id']=='SCN-32971254580E1875');src=self.source(sel);_worker_init(str(REPO),self.doc['matrix'],self.er,self.tr)
        got=_diag_task((src,25,int(self.doc['masterSeed']),UTILITY_COMBAT_DOCTRINE)); self.assertEqual(0,float(got['b_cp147_sole_main_diversions_without_hull_risk']))

    def test_14_cp147_does_not_regress_tl2_power_crisis(self):
        sel=next(r for r in self.selection if r['diagnostic_family']=='TP_STARVATION' and r['tl']=='2' and r['scenario_stratum']=='POWER_CRISIS');src=self.source(sel);_worker_init(str(REPO),self.doc['matrix'],self.er,self.tr)
        got=_diag_task((src,25,int(self.doc['masterSeed']),UTILITY_COMBAT_DOCTRINE)); self.assertEqual(0,int(got['turn_cap_sentinels']))

    def test_15_ammo_exhaustion_stops_utility_power_requests(self):
        _,m,b=self.bound(lambda r:r['side_a_weapon']=='M_GP' and r['resource_ensemble_id']=='R1_CENTRAL_NO_MAJOR')
        own=_create_side(m,b.variant.side_a,0);target=_create_side(m,b.variant.side_b,1);own.weapon_ammo=0
        p=_plan_once(m,own,target,1,0,10,False,UTILITY_COMBAT_DOCTRINE); self.assertFalse(p['weapon_has_ammo']); self.assertTrue(all(x is None for x in p['weapon_plans']))

    def test_16_cp147_turn_refresh_reserve_does_not_let_optional_recharge_preconsume_core(self):
        _,m,b=self.bound(lambda r:r['side_b_weapon']=='E' and r['resource_ensemble_id']=='R4_TIGHT_HIGH_DEMAND')
        own=_create_side(m,b.variant.side_b,0); target=_create_side(m,b.variant.side_a,1); own.shield=max(0,own.shield-2); own.known_opponent_weapon_family='Missile'; own.known_opponent_missile_profile='GP'
        available,spent=_begin_turn_recharge(m,own,target,1,UTILITY_COMBAT_DOCTRINE); p=_plan_once(m,own,target,1,1,available,False,UTILITY_COMBAT_DOCTRINE)
        self.assertTrue(any(x is not None for x in p['weapon_plans'])); self.assertLessEqual(spent,int(m.p('shield',own.build.tl).get('tacticalRechargeCapTp',0)))

    def test_17_exact_selector_tie_favors_continued_offense(self):
        direct=TacticalPackageCandidate('direct',4,3000,1000,1,0,0,True,True);held=TacticalPackageCandidate('held',4,2000,2000,1,1,0,True,True)
        self.assertEqual('direct',choose_tactical_package([held,direct],4).id)

    def test_18_kernel_version_marks_tactical_utility_semantic_change(self): self.assertEqual('0.7',CANONICAL_COMBAT_KERNEL_VERSION)

if __name__=='__main__': unittest.main()
