from __future__ import annotations
import csv, json, tempfile, unittest
from unittest.mock import patch
from pathlib import Path

from starcluster_research.study import load_json
from starcluster_research.ecology import _pds_readiness_options, _cp147_expected_intercepted
from starcluster_research.pds_lifecycle_closure import (
    FAMILIES, pds_candidate_ledger, pds_contexts, validate_study, validate_population,
    run_plan, run_candidate_batch, merge_deep, _matrix_profile_audit, _cp153_package_row,
)

ROOT=Path(__file__).resolve().parents[3]
STUDY=ROOT/'docs/archive/testing/pre-cp165-active/cp154_pds_lifecycle_closure_study_v0_1.json'

class _DummySide:
    def __init__(self,ammo=None,strain=0): self.pds_ammo=ammo; self.pds_strain=strain

class Cp154PdsLifecycleClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=load_json(STUDY); cls.rows=pds_candidate_ledger(ROOT,cls.doc)

    def test_01_study_and_population_contract(self):
        self.assertEqual([],validate_study(self.doc)); self.assertEqual([],validate_population(ROOT,self.doc))
    def test_02_oversweep_population_is_14748_candidate_tl_points(self):
        self.assertEqual(14748,len(self.rows))
    def test_03_exact_family_tl_candidate_counts(self):
        expected={
            'Kinetic':[378,378,420,420,420,420,420,420,420],
            'Energy':[480,480,480,432,432,480,480,480,480],
            'AMM':[432,432,432,432,1020,1020,1020,1020,1020],
        }
        for fam,vals in expected.items():
            self.assertEqual(vals,[sum(r['family']==fam and r['tl']==tl for r in self.rows) for tl in range(1,10)])
    def test_04_kinetic_is_local_rc1_rc2_only(self):
        ks=[r for r in self.rows if r['family']=='Kinetic']; self.assertEqual({1,2},{r['reaction_capacity'] for r in ks}); self.assertFalse(any(r['range_one'] for r in ks))
    def test_05_kinetic_ammo_is_broadly_swept(self):
        for tl in range(1,10): self.assertEqual({15,25,35,50,60,75,100},{r['ammo'] for r in self.rows if r['family']=='Kinetic' and r['tl']==tl})
    def test_06_energy_has_safe_and_overcharged_rc2(self):
        es=[r for r in self.rows if r['family']=='Energy']; self.assertTrue(any(r['mode']=='RC2_SAFE' for r in es)); self.assertTrue(any(r['mode']=='RC2_OVERCHARGED' for r in es))
    def test_07_energy_strain_limits_one_through_four(self):
        for tl in range(1,10): self.assertEqual({1,2,3,4},{r['strain_limit'] for r in self.rows if r['family']=='Energy' and r['tl']==tl and r['mode']=='RC2_OVERCHARGED'})
    def test_08_energy_has_no_ammo_or_range_one(self):
        self.assertTrue(all(r['ammo']=='' and not r['range_one'] for r in self.rows if r['family']=='Energy'))
    def test_09_amm_rc3_is_range_one_and_not_early(self):
        a=[r for r in self.rows if r['family']=='AMM']; self.assertFalse(any(r['reaction_capacity']==3 for r in a if r['tl']<5)); self.assertTrue(any(r['reaction_capacity']==3 for r in a if r['tl']>=5)); self.assertTrue(all((r['reaction_capacity']==3)==bool(r['range_one']) for r in a))
    def test_10_amm_ammo_is_overswept(self):
        for tl in range(1,10): self.assertEqual({6,12,18,25,35,50},{r['ammo'] for r in self.rows if r['family']=='AMM' and r['tl']==tl})
    def test_11_broad_and_deep_context_counts(self):
        self.assertEqual(612,len(pds_contexts(ROOT,self.doc,True))); self.assertEqual(3060,len(pds_contexts(ROOT,self.doc,False)))
    def test_12_tl1_respects_swarmer_unlock(self):
        tl1=[r for r in pds_contexts(ROOT,self.doc,False) if r['tl']==1]; self.assertFalse(any(r['attacker']=='SW2' or r['defender']=='SW2' for r in tl1))
    def test_13_deep_contexts_cross_all_five_resources(self):
        rows=pds_contexts(ROOT,self.doc,False); self.assertEqual(5,len({r['resource_ensemble_id'] for r in rows}))
    def test_14_broad_panel_rotates_all_resources(self):
        rows=pds_contexts(ROOT,self.doc,True); self.assertEqual(5,len({r['resource_ensemble_id'] for r in rows}))
    def test_15_current_matrix_history_really_kept_k_at_rc1(self):
        rows=_matrix_profile_audit(ROOT); ks=[r for r in rows if r['family']=='Kinetic']; self.assertEqual(9,len({r['matrix'] for r in ks})); self.assertEqual({1},{int(r['reaction_capacity']) for r in ks})
    def test_16_cp153_mains_are_explicitly_consumed(self):
        r=_cp153_package_row(ROOT,9,'M2'); self.assertEqual(20,r['k_damage']); self.assertEqual(18,r['e_standard_damage']); self.assertEqual(27,r['m_damage']); self.assertEqual(12,r['sw_packet_damage'])
    def test_17_tiered_readiness_respects_energy_strain_limit(self):
        p={'reactionCapacity':2,'readinessTp':2,'rc1Tp':1,'rc2Tp':2,'safeReactionCapacity':1,'extraReactionStrain':1,'strainLimit':2}
        self.assertIn(("pds2",2,2),_pds_readiness_options(p,_DummySide(strain=1))); self.assertNotIn(("pds2",2,2),_pds_readiness_options(p,_DummySide(strain=2))); self.assertIn(("pds1",1,1),_pds_readiness_options(p,_DummySide(strain=2)))
    def test_18_three_amm_windows_are_stronger_than_two_when_rc3(self):
        two=_cp147_expected_intercepted(1,0,0.0,3,0.4,2); three=_cp147_expected_intercepted(1,0,0.0,3,0.4,3); self.assertGreater(three,two); self.assertAlmostEqual(three,1-(0.6**3),places=10)
    def test_19_plan_reproduces_32729400_substantive_combats(self):
        with tempfile.TemporaryDirectory() as td:
            s=run_plan(ROOT,STUDY,Path(td)); self.assertTrue(s['passed']); self.assertEqual(25385400,s['screenCombatTrials']); self.assertEqual(7344000,s['deepCombatTrials']); self.assertEqual(32729400,s['substantiveCombatTrials'])
        # CR1 regression: exercise the deep finalizer itself with a minimal
        # three-family synthetic surface. This catches dimension-key drift such
        # as scenario_stratum vs stratum without running substantive combats.
        with tempfile.TemporaryDirectory() as td:
            d=Path(td); ledger=d/'ladders.csv'; batch=d/'batches'/'b0'; out=d/'merged'; batch.mkdir(parents=True)
            with ledger.open('w',newline='',encoding='utf-8') as f:
                w=csv.DictWriter(f,fieldnames=['ladder_id','family','tl']); w.writeheader()
                for lid,fam in [('K01','Kinetic'),('E01','Energy'),('A01','AMM')]: w.writerow({'ladder_id':lid,'family':fam,'tl':1})
            fields=['ladder_id','scenario_id','trials','b_wins','a_wins','draws','mean_b_pds_attempts','mean_b_pds_intercepts','mean_b_power_pds','mean_b_pds_overcharge_attempts','mean_b_pds_range_one_attempts','attacker','defender','resource_ensemble_id','scenario_stratum','tl','turn_cap_sentinels','error_trials']
            with (batch/'pds_deep_context_results.csv').open('w',newline='',encoding='utf-8') as f:
                w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
                for lid in ('K01','E01','A01'):
                    w.writerow({'ladder_id':lid,'scenario_id':'s1','trials':100,'b_wins':50,'a_wins':50,'draws':0,'mean_b_pds_attempts':1,'mean_b_pds_intercepts':0.5,'mean_b_power_pds':1,'mean_b_pds_overcharge_attempts':0,'mean_b_pds_range_one_attempts':0,'attacker':'GP_M2','defender':'K1','resource_ensemble_id':'R1','scenario_stratum':'BALANCED_CORE','tl':1,'turn_cap_sentinels':0,'error_trials':0})
            (batch/'summary.json').write_text(json.dumps({'passed':True,'mode':'deep-batch','errors':0}),encoding='utf-8')
            with patch('starcluster_research.pds_lifecycle_closure.DEEP_LADDERS',3), patch('starcluster_research.pds_lifecycle_closure.pds_contexts',return_value=[{}]):
                merged=merge_deep(ROOT,STUDY,ledger,d/'batches',out)
            self.assertTrue(merged['passed']); self.assertEqual(3,merged['ladders']); self.assertEqual(1,merged['triadCombinations'])
    def test_20_live_kinetic_rc2_smoke(self):
        with tempfile.TemporaryDirectory() as td:
            s=run_candidate_batch(ROOT,STUDY,Path(td),'Kinetic',6,241,242,jobs=1,trials=1,smoke=True); self.assertTrue(s['passed']); self.assertEqual(6,s['combatTrials'])
    def test_21_live_energy_overcharge_adds_strain_only_on_extra_attempt(self):
        with tempfile.TemporaryDirectory() as td:
            d=Path(td); s=run_candidate_batch(ROOT,STUDY,d,'Energy',6,248,249,jobs=1,trials=4,smoke=True); self.assertTrue(s['passed'])
            with (d/'pds_candidate_context_results.csv').open(newline='',encoding='utf-8') as f: rows=list(csv.DictReader(f))
            self.assertGreater(sum(float(r['mean_b_pds_overcharge_attempts']) for r in rows),0.0); self.assertGreater(max(int(float(r['max_pds_strain'])) for r in rows),0)
    def test_22_live_amm_rc3_uses_range_one_window(self):
        with tempfile.TemporaryDirectory() as td:
            d=Path(td); s=run_candidate_batch(ROOT,STUDY,d,'AMM',7,669,670,jobs=1,trials=2,smoke=True); self.assertTrue(s['passed'])
            with (d/'pds_candidate_context_results.csv').open(newline='',encoding='utf-8') as f: rows=list(csv.DictReader(f))
            self.assertGreater(sum(float(r['mean_b_pds_range_one_attempts']) for r in rows),0.0)
    def test_23_no_k_or_e_rc3_and_no_non_amm_range_one(self):
        self.assertFalse(any(r['family']!='AMM' and (r['reaction_capacity']>2 or r['range_one']) for r in self.rows))
    def test_24_simultaneous_flight_value_is_explicitly_deferred(self):
        self.assertIn('simultaneous multi-Flight arrival balance weighting',self.doc['deferred'])
    def test_25_no_automatic_promotion_or_final_tp_tuning(self):
        self.assertFalse(self.doc['automaticPromotion']); self.assertFalse(self.doc['tuningAllowed']); self.assertIn('final Reactor/TP supply tuning',self.doc['deferred'])
        wrapper=(ROOT/'tools/checkpoints/checkpoint-154/apply_checkpoint_154.ps1').read_text(encoding='utf-8-sig')
        self.assertIn("$ErrorActionPreference = 'Continue'",wrapper); self.assertIn('CP154 deep merge',wrapper)

if __name__=='__main__': unittest.main()
