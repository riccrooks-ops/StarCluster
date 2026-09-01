from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path
import sys

REPO=Path(__file__).resolve().parents[3]
SIM=REPO/'tools'/'simulation'
if str(SIM) not in sys.path: sys.path.insert(0,str(SIM))

from starcluster_research.combat_surface_deep_reconciliation import build_deep_resource_matrix
from starcluster_research.ecology import UTILITY_COMBAT_DOCTRINE
from starcluster_research.stage_a_integration_analysis import _read_csv,_resource_rows,bind_scenario
from starcluster_research.study import load_json
from starcluster_research.whole_combat_stage_a_response_surface import (
    EXPECTED_SCENARIOS,EXPECTED_SUBSTANTIVE_TRIALS,_base_max_installed_tp_demand,
    _combat_gated_strategic_viability,_role_response_summary,_tp_load_surfaces,
    run_smoke_batch,run_substantive_batch,validate_population,validate_study,
)

STUDY=REPO/'docs/archive/testing/pre-cp165-active/cp148_whole_combat_stage_a_tactical_utility_response_surface_study_v0_1.json'
CP144=REPO/'docs/archive/testing/pre-cp165-active/cp144_whole_combat_stage_a_response_surface_study_v0_1.json'
MATRIX=REPO/'docs/design/player_technology/technology_numerical_matrix_v0_9.json'

class Cp148WholeCombatStageATacticalUtilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=load_json(STUDY);cls.manifest=_read_csv(REPO/cls.doc['stageAExperimentManifest']);cls.er,cls.tr=_resource_rows(REPO,cls.doc)

    def test_01_study_is_exact_broad_utility_and_non_promoting(self):
        self.assertEqual([],validate_study(self.doc));self.assertEqual(148,self.doc['checkpoint']);self.assertEqual(147,self.doc['baseCheckpoint'])
        self.assertEqual(UTILITY_COMBAT_DOCTRINE,self.doc['combatDoctrine']);self.assertEqual(EXPECTED_SCENARIOS,self.doc['expectedStageAScenarios']);self.assertEqual(EXPECTED_SUBSTANTIVE_TRIALS,self.doc['substantiveCombatTrials'])
        self.assertEqual('all-installed-normal-combat-demand-no-overload',self.doc['baseMaxTpDemandPolicy']);self.assertEqual('combat-gated-before-resource-robustness',self.doc['strategicParetoPolicy'])
        self.assertFalse(self.doc['tuningAllowed']);self.assertFalse(self.doc['automaticPromotion']);self.assertFalse(self.doc['stageBAutomatic'])

    def test_02_population_reuses_exact_accepted_6850_cells(self):
        self.assertEqual([],validate_population(REPO,self.doc));self.assertEqual(6850,len(self.manifest));self.assertEqual(self.manifest,_read_csv(REPO/load_json(CP144)['stageAExperimentManifest']))

    def test_03_base_max_tp_demand_excludes_overload_and_sums_normal_components(self):
        src=self.manifest[0];m=build_deep_resource_matrix(REPO,self.doc['matrix'],src['resource_ensemble_id'],self.er,self.tr);b=bind_scenario(m,src).variant.side_a
        total,parts=_base_max_installed_tp_demand(m,b)
        self.assertEqual(total,sum(parts.values()));self.assertEqual(int(m.weapon_profile(b.weapon_family,b.tl)['standardTp']),parts['weapon'])
        self.assertEqual(int(m.p('sensor',b.tl)['activeLowTp']),parts['sensor']);self.assertNotIn('overload',parts)
        self.assertLess(total,int(m.p('reactor',b.tl)['operationalTp'])+10) # bounded sanity; not an overload-supply construction

    def test_04_cp148_smoke_actually_uses_cp147_utility_doctrine(self):
        with tempfile.TemporaryDirectory() as td:
            s=run_smoke_batch(REPO,STUDY,Path(td),jobs=1,batch_start=0,batch_end=2);rows=_read_csv(Path(td)/'whole_combat_smoke_results.csv')
        self.assertTrue(s['passed'],s);self.assertEqual(2,len(rows));self.assertEqual(148,s['checkpoint']);self.assertTrue(all(int(r['nonstandoff_open_orders'])==0 for r in rows))

    def test_05_substantive_rows_export_allocated_vs_base_max_tp(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td);s=run_substantive_batch(REPO,STUDY,out,jobs=1,batch_start=0,batch_end=2,trials_per_scenario=3);rows=_read_csv(out/'scenario_response_surface.csv')
        self.assertTrue(s['passed'],s);r=rows[0]
        for side in ('a','b'):
            for field in ('base_reactor_tp','base_max_installed_tp_demand','mean_tp_allocated_per_turn','peak_tp_allocated_per_turn','mean_allocated_vs_base_max_demand','peak_allocated_vs_base_max_demand','base_max_demand_vs_reactor'):
                self.assertIn(f'{side}_{field}',r)
            self.assertGreater(float(r[f'{side}_base_max_installed_tp_demand']),0);self.assertGreaterEqual(float(r[f'{side}_mean_tp_allocated_per_turn']),0)
        self.assertGreater(float(r['mean_a_cp147_package_decisions']),0) # proves the broad runner selected utility doctrine

    def test_06_base_max_tp_breakdown_is_auditable_in_result_row(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td);run_substantive_batch(REPO,STUDY,out,jobs=1,batch_start=0,batch_end=1,trials_per_scenario=2);r=_read_csv(out/'scenario_response_surface.csv')[0]
        parts=sum(float(r[f'a_base_max_tp_{x}']) for x in ('weapon','sensor','ecm','eccm','pds','shield_hardener','shield_recharge','armor_regen','damage_control'))
        self.assertAlmostEqual(float(r['a_base_max_installed_tp_demand']),parts,places=12)

    def test_07_tp_load_surfaces_preserve_allocated_vs_max_metrics(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td);run_substantive_batch(REPO,STUDY,out,jobs=1,batch_start=0,batch_end=4,trials_per_scenario=2);rows=_read_csv(out/'scenario_response_surface.csv')
        detail,tl=_tp_load_surfaces(rows);self.assertTrue(detail and tl)
        self.assertIn('mean_mean_tp_allocated_per_turn',detail[0]);self.assertIn('mean_mean_allocated_vs_base_max_demand',detail[0]);self.assertIn('mean_base_max_demand_vs_reactor',tl[0])

    def test_08_combat_gate_prevents_resource_only_strategic_resurrection(self):
        # Four TL1 weapons with synthetic contexts. K is strictly combat-dominated by E.
        base=[]
        for w,win,dmg,fulfill in [('K',.25,-2,1.0),('E',.60,2,.7),('M_GP',.50,1,.8),('M_SWARMER',.45,.5,.9)]:
            for opp in ('K','E','M_GP','M_SWARMER'):
                base.append({'tl':1,'resource_ensemble_id':'R1','scenario_stratum':'BALANCED_CORE_NO_PDS','side_a_weapon':w,'side_b_weapon':opp,'trials':100,
                    'a_wins':int(win*100),'b_wins':int((1-win)*100),'draws':0,'a_damage_advantage_mean':dmg,'gameplay_duration_concern_rate':0,
                    'a_mean_allocated_vs_base_max_demand':.2 if w=='K' else .8,'b_mean_allocated_vs_base_max_demand':.8,'a_tp_fulfillment_rate':fulfill,'b_tp_fulfillment_rate':.8,
                    'a_primary_ammo_exhausted_rate':0,'b_primary_ammo_exhausted_rate':0})
        # Force reverse rows to preserve the same candidate rates when oriented B.
        idx={(r['side_a_weapon'],r['side_b_weapon']):r for r in base}
        for a in ('K','E','M_GP','M_SWARMER'):
            for b in ('K','E','M_GP','M_SWARMER'):
                if a==b: continue
                idx[(b,a)]['b_wins']=idx[(a,b)]['a_wins']
        out=_combat_gated_strategic_viability(base);k=next(r for r in out if r['weapon']=='K')
        self.assertEqual(0,k['combat_viability_gate']);self.assertEqual(0,k['strategic_pareto_eligible']);self.assertEqual(0,k['strategic_pareto_viable']);self.assertEqual(0,k['resource_or_robustness_only_frontier'])

    def test_09_role_response_uses_designated_specialization_strata(self):
        rows=[]
        # Self match rows are sufficient to exercise role filtering.
        for w,stratum in [('K','ARMOR_PRESSURE'),('E','SHIELD_PRESSURE'),('M_GP','BALANCED_CORE_NO_PDS'),('M_SWARMER','AMM_PDS_PRESSURE')]:
            rows.append({'tl':3,'resource_ensemble_id':'R1','scenario_stratum':stratum,'side_a_weapon':w,'side_b_weapon':w,'trials':100,'a_wins':50,'b_wins':50,'draws':0,'a_damage_advantage_mean':0,'gameplay_duration_concern_rate':0,
                         'a_mean_allocated_vs_base_max_demand':.5,'b_mean_allocated_vs_base_max_demand':.5,'a_tp_fulfillment_rate':1,'b_tp_fulfillment_rate':1,'a_primary_ammo_exhausted_rate':0,'b_primary_ammo_exhausted_rate':0})
        out=_role_response_summary(rows);self.assertEqual({'K','E','M_GP','M_SWARMER'},{r['weapon'] for r in out})

    def test_10_cp144_historical_study_still_validates_as_legacy(self):
        old=load_json(CP144);self.assertEqual([],validate_study(old));self.assertNotIn('combatDoctrine',old)
        with tempfile.TemporaryDirectory() as td:
            s=run_smoke_batch(REPO,CP144,Path(td),jobs=1,batch_start=0,batch_end=1)
        self.assertTrue(s['passed']);self.assertEqual(144,s['checkpoint']);self.assertEqual('star-cluster-cp144-whole-combat-stage-a-response-surface-result-v0.1',s['schemaVersion'])

    def test_11_source_matrix_is_not_modified_by_cp148_execution(self):
        before=hashlib.sha256(MATRIX.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory() as td: run_substantive_batch(REPO,STUDY,Path(td),jobs=1,batch_start=5,batch_end=6,trials_per_scenario=2)
        self.assertEqual(before,hashlib.sha256(MATRIX.read_bytes()).hexdigest())

    def test_12_cp147_action_telemetry_is_carried_into_broad_rows(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td);run_substantive_batch(REPO,STUDY,out,jobs=1,batch_start=0,batch_end=1,trials_per_scenario=2);r=_read_csv(out/'scenario_response_surface.csv')[0]
        for field in ('mean_a_cp147_package_decisions','mean_a_cp147_direct_package_selections','mean_a_cp147_pds_package_selections','mean_a_cp147_held_package_selections','mean_a_cp147_passive_utility_fallbacks','mean_a_cp147_terminal_hull_risk_turns'):
            self.assertIn(field,r)

if __name__=='__main__': unittest.main()
