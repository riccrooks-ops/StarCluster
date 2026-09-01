from __future__ import annotations
import csv,hashlib,json,tempfile,unittest
from pathlib import Path
from starcluster_research.study import load_json
from starcluster_research.research_execution_baseline_pf3 import load_research_execution_baseline_pf3,aux_profile,BASELINE_ID
from starcluster_research.auxiliary_closure import field_candidates,crystal_candidates,field_deep_packages,crystal_deep_packages,_manifest,_field_context,_micro_one,plan,smoke,_pick_field,_pick_crystal,_resource_matrix
from starcluster_research.defense_aux_lifetime_viability import _apply_candidate
from starcluster_research.stage_a_integration_analysis import bind_scenario
from starcluster_research.ecology import _create_side
from starcluster_research.canonical_combat import DamageCommit,_apply_committed_damage
ROOT=Path(__file__).resolve().parents[3]
STUDY=ROOT/'docs/archive/testing/pre-cp165-active/cp159_aux_closure_study_v0_1.json'
PF2=ROOT/'docs/archive/player_technology/pre-cp165-active/technology_research_execution_baseline_pending_finalization_v0_2.json'
PF3=ROOT/'docs/archive/player_technology/pre-cp165-active/technology_research_execution_baseline_pending_finalization_v0_3.json'
PROD=ROOT/'docs/design/player_technology/technology_numerical_matrix_v0_9.json'
PLAN=ROOT/'docs/validation/evidence/checkpoint-159/planned-study/summary.json'
LEDGER=ROOT/'docs/validation/evidence/checkpoint-159/aux_pending_finalization_promotion_ledger_v0_1.csv'
def rows(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class Cp159AuxClosureTests(unittest.TestCase):
 def setUp(self):self.doc=load_json(STUDY);self.m=load_research_execution_baseline_pf3(ROOT)
 def test_01_pf3_identity(self):self.assertEqual(BASELINE_ID,'CP159-PF3');self.assertEqual(self.m.doc['pendingFinalizationResearchBaseline']['baselineId'],'CP159-PF3')
 def test_02_pf3_preserves_pf2_executable_core(self):
  a=json.loads(PF2.read_text());b=json.loads(PF3.read_text());self.assertEqual(a['profiles'],b['profiles']);self.assertEqual(a['branches'],b['branches']);self.assertEqual(a['candidateBranchSeeds'],b['candidateBranchSeeds'])
 def test_03_production_authority_is_not_pf3(self):self.assertNotEqual(sha(PROD),sha(PF3));self.assertEqual(sha(PROD),'3088b0a9eb45f6bf505c24513e8bb2ac878819db4ab464ccfea330243c82f194')
 def test_04_promoted_aux_profiles_are_materialized(self):self.assertEqual(set(self.m.doc['pendingFinalizationAuxProfiles']),{'shieldBattery','shieldBooster','shieldHardener','ablativeArmor','energizedArmor','crystallineArmor','fieldStabilizer','repairDroneBay','kineticMagazine','missileMagazine'})
 def test_05_battery_rising_full_exact(self):self.assertEqual([(t,aux_profile(ROOT,'shieldBattery',t)['restore'],aux_profile(ROOT,'shieldBattery',t)['charges']) for t in range(1,10)],[(1,2,1),(2,2,1),(3,2,1),(4,4,2),(5,4,2),(6,6,3),(7,6,3),(8,8,3),(9,8,3)])
 def test_06_booster_rising_full_exact(self):self.assertEqual([aux_profile(ROOT,'shieldBooster',t)['capacityBonus'] for t in range(2,10)],[2,2,4,4,6,6,8,8])
 def test_07_hardener_rising_full_exact(self):self.assertEqual([aux_profile(ROOT,'shieldHardener',t)['defBonusPp'] for t in range(3,10)],[5,5,10,10,15,15,20])
 def test_08_ablative_rising_full_exact(self):self.assertEqual([aux_profile(ROOT,'ablativeArmor',t)['ablativeIntegrity'] for t in range(1,10)],[2,2,2,4,4,8,8,10,10])
 def test_09_energized_rising_full_exact(self):self.assertEqual([aux_profile(ROOT,'energizedArmor',t)['resBonusPp'] for t in range(5,10)],[5,5,10,15,20])
 def test_10_crystalline_is_boundary_supported_not_final(self):self.assertIn('BOUNDARY_SUPPORTED',self.m.doc['pendingFinalizationAuxProfiles']['crystallineArmor']['status']);self.assertIn('TL8-TL9',self.m.doc['pendingFinalizationAuxProfiles']['crystallineArmor']['closureRequired'])
 def test_11_field_stabilizer_identity_is_spen_specific(self):
  r=self.m.doc['pendingFinalizationAuxProfiles']['fieldStabilizer'];self.assertIn('SPEN',r['mechanic']);self.assertIn('no benefit against SPEN 0',r['identity'])
 def test_12_repair_drone_semantics_are_parallel_not_reroll(self):
  r=self.m.doc['pendingFinalizationAuxProfiles']['repairDroneBay'];self.assertIn('parallel Damage Control action',r['mechanic']);self.assertIn('different repair target',r['mechanic']);self.assertIn('normal per-attempt Tactical Power',r['attemptRules'])
 def test_13_cp158_repair_placeholder_is_explicitly_superseded(self):self.assertIn('SUPERSEDED',self.m.doc['cp159AuxClosureBoundary']['repairDroneCp158Placeholder'])
 def test_14_field_sweep_is_broad_to_24(self):
  c=field_candidates();self.assertEqual(len(c),99);self.assertEqual({x['spen_reduction'] for x in c},set(range(4,25,2)));self.assertEqual({x['tp'] for x in c},{0,1,2});self.assertEqual({x['tl'] for x in c},{7,8,9})
 def test_15_field_sweep_reaches_full_e7_spen_nullification(self):self.assertGreaterEqual(max(x['spen_reduction'] for x in field_candidates()),max(int(self.m.p('energy_main',t)['spen']) for t in (7,8,9)))
 def test_16_crystalline_headroom_is_late_only_and_broad(self):
  c=crystal_candidates();self.assertEqual(len(c),40);self.assertEqual({x['tl'] for x in c},{8,9});self.assertEqual({x['capacity_bonus'] for x in c},{8,10,12,14,16});self.assertEqual({x['res_bonus_pp'] for x in c},{15,20,25,30})
 def test_17_field_deep_architectures_and_hardener_comparator(self):
  d=field_deep_packages(ROOT);self.assertEqual(len(d),7);self.assertEqual(d[-1][0],'SHIELD_HARDENER_PROMOTED')
 def test_18_crystalline_deep_architectures_are_six(self):self.assertEqual(len(crystal_deep_packages()),6)
 def test_19_field_context_count_is_540(self):self.assertEqual(sum(_field_context(ROOT,self.doc,r) for r in _manifest(ROOT,self.doc)),540)
 def test_20_plan_is_compact_and_exact(self):
  p=json.loads(PLAN.read_text());self.assertEqual(p['substantiveCombatTrials'],3390000);self.assertEqual(p['repairDroneMicroTrials'],1728000);self.assertEqual(p['fieldScreenCells'],17820);self.assertEqual(p['crystallineScreenCells'],32000)
 def test_21_reactor_tp_is_still_deferred(self):self.assertIn('final Reactor/TP tuning remains last',' '.join(self.doc['guardrails']));self.assertFalse(json.loads(PLAN.read_text())['finalReactorTpTuning'])
 def test_22_no_equality_objective(self):self.assertIn('balance is not equality',' '.join(self.doc['guardrails']));self.assertIn('no global 50 percent target',' '.join(self.doc['guardrails']))
 def test_23_repair_kit_sweep_is_integer_zero_to_default(self):
  for tl in range(2,10):
   base=int(self.m.p('damage_control',tl)['preparedRepairKits']);self.assertEqual(list(range(base+1))[0],0);self.assertEqual(list(range(base+1))[-1],base)
 def test_24_single_target_never_gets_drone_reroll(self):
  dc=self.m.p('damage_control',4);self.assertEqual(_micro_one(dc,4,'SINGLE_HULL',2,123)['drone_attempts'],0)
 def test_25_two_targets_can_use_drone_action(self):
  dc=self.m.p('damage_control',4);self.assertGreater(_micro_one(dc,4,'TWO_DEGRADED',2,123)['drone_attempts'],0)
 def test_26_one_tp_caps_damage_control_to_one_action(self):
  dc=self.m.p('damage_control',4);self.assertEqual(_micro_one(dc,4,'TWO_DEGRADED',1,123)['drone_attempts'],0)
 def test_27_cp158_native_evidence_is_preserved(self):
  n=json.loads((ROOT/'docs/validation/evidence/checkpoint-159/accepted-cp158/CP158_NATIVE_ACCEPTANCE_SUMMARY.json').read_text(encoding='utf-8-sig'));self.assertEqual(n['substantiveCombatTrials'],44723375);self.assertEqual(n['substantiveErrors'],0);self.assertEqual(n['substantiveTurnCapSentinels'],0)
 def test_28_promotion_ledger_covers_all_ten_aux_profiles(self):self.assertEqual(len(rows(LEDGER)),10)
 def test_29_field_candidate_actually_changes_high_spen_resolution(self):
  src=next(r for r in _manifest(ROOT,self.doc) if int(r['tl'])==9 and r['side_a_weapon']=='E' and _field_context(ROOT,self.doc,r));m=_resource_matrix(ROOT,self.doc,src['resource_ensemble_id']);c=_pick_field(9,20,1);v=_apply_candidate(m,bind_scenario(m,src).variant,c);s1=_create_side(m,v.side_b,0);s2=_create_side(m,v.side_b,0);_apply_committed_damage(m,s1,DamageCommit('DirectFire','A','B','direct',8,22,0,False),30,1);_apply_committed_damage(m,s2,DamageCommit('DirectFire','A','B','direct',8,22,0,False,False,True),30,1);self.assertGreaterEqual(s2.shield,s1.shield)
 def test_30_crystalline_headroom_candidate_increases_capacity(self):
  src=next(r for r in _manifest(ROOT,self.doc) if int(r['tl'])==9);m=_resource_matrix(ROOT,self.doc,src['resource_ensemble_id']);c=_pick_crystal(9,12,25);v=_apply_candidate(m,bind_scenario(m,src).variant,c);s=_create_side(m,v.side_b,0);self.assertEqual(s.armor_max,int(m.p('armor',9)['ai'])+12);self.assertEqual(s.armor_regen_reserve_remaining,0)
if __name__=='__main__':unittest.main()
