from __future__ import annotations
import csv,hashlib,json,unittest
from collections import Counter
from pathlib import Path
from dataclasses import replace
from starcluster_research.defense_aux_lifetime_viability import candidate_ledger,representative_designs,center_candidates,disposition,_manifest,_bind
from starcluster_research.research_execution_baseline_pf2 import load_research_execution_baseline_pf2,BASELINE_ID
from starcluster_research.study import load_json
from starcluster_research.ecology import _create_side,_begin_turn_recharge,_attempt_hull_damage_control
from starcluster_research.canonical_combat import DamageCommit,_apply_committed_damage

ROOT=Path(__file__).resolve().parents[3]
STUDY=ROOT/'docs/archive/testing/pre-cp165-active/cp158_defense_aux_lifetime_viability_study_v0_1.json'
PF1=ROOT/'docs/archive/player_technology/pre-cp165-active/technology_research_execution_baseline_pending_finalization_v0_1.json'
PF2=ROOT/'docs/archive/player_technology/pre-cp165-active/technology_research_execution_baseline_pending_finalization_v0_2.json'
PROD=ROOT/'docs/design/player_technology/technology_numerical_matrix_v0_9.json'
DIFF=ROOT/'docs/validation/evidence/checkpoint-158/research_execution_baseline_diff_v0_2.csv'
PLAN=ROOT/'docs/validation/evidence/checkpoint-158/planned-study/summary.json'

def rows(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

class Cp158DefenseAuxLifetimeTests(unittest.TestCase):
 def setUp(self):
  self.doc=load_json(STUDY);self.cands=candidate_ledger()
 def test_01_pf2_identity_and_no_numeric_rewrite_from_pf1(self):
  a=json.loads(PF1.read_text());b=json.loads(PF2.read_text());self.assertEqual(b['pendingFinalizationResearchBaseline']['baselineId'],'CP158-PF2')
  for k in ('branches','candidateBranchSeeds','combatModifiers','energyOutputRule','shieldRechargeInvariant','armorRegenerationRule'):
   self.assertEqual(a[k],b[k])
  for prof in a['profiles']:
   if prof!='missile_delivery': self.assertEqual(a['profiles'][prof],b['profiles'][prof])
  for tl,row in a['profiles']['missile_delivery'].items():
   aa=dict(row);bb=dict(b['profiles']['missile_delivery'][tl]);aa.pop('notes',None);bb.pop('notes',None);self.assertEqual(aa,bb)
 def test_02_pf2_loader_uses_selected_mains_and_pds(self):
  m=load_research_execution_baseline_pf2(ROOT);self.assertEqual(BASELINE_ID,'CP158-PF2');self.assertEqual([int(m.p('kinetic_main',t)['damage']) for t in range(1,10)],[9,10,12,13,14,15,15,19,20]);self.assertEqual(int(m.p('energy_main',9)['standardDamage']),18);self.assertEqual(int(m.p('amm_pds',7)['reactionCapacity']),3)
 def test_03_classification_split_is_exact(self):
  c=Counter(r['status'] for r in rows(DIFF));self.assertEqual(c['FROZEN_RESEARCH_MECHANIC'],73);self.assertEqual(c['PROVISIONAL_RESOURCE_SCAFFOLD'],63);self.assertEqual(c['PENDING_FINALIZATION_SELECTED'],348);self.assertEqual(c['PENDING_FINALIZATION_VALIDATED_ENVIRONMENT'],54)
 def test_04_swarmer_and_guidance_are_frozen_mechanics(self):
  r=rows(DIFF);f=[x for x in r if x['status']=='FROZEN_RESEARCH_MECHANIC'];self.assertEqual(len(f),73);self.assertEqual(Counter(x['profile'] for x in f),Counter({'missile_swarmer':64,'missile_guidance':9}))
 def test_05_reactor_and_resource_space_are_provisional_scaffold(self):
  r=rows(DIFF);self.assertTrue(all(x['status']=='PROVISIONAL_RESOURCE_SCAFFOLD' for x in r if x['profile']=='reactor'));self.assertTrue(any(x['profile']=='kinetic_main' and x['field']=='firingTp' and x['status']=='PROVISIONAL_RESOURCE_SCAFFOLD' for x in r))
 def test_06_stale_missile_note_is_cleaned_only_in_pf2(self):
  b=json.loads(PF2.read_text());self.assertTrue(all('profile-driven by TL' in x['notes'] for x in b['profiles']['missile_delivery'].values()));self.assertIn('0 Tactical Power to launch',json.loads(PROD.read_text())['profiles']['missile_delivery']['1']['notes'])
 def test_07_study_contract_is_nonpromoting_and_uses_pf2(self):
  self.assertEqual(self.doc['researchExecutionBaseline'],'CP158-PF2');self.assertFalse(self.doc['automaticPromotion']);self.assertFalse(self.doc['tuningAllowed']);self.assertEqual(self.doc['substantiveCombatTrials'],44723375)
 def test_08_candidate_population_is_703_unique_points(self):
  self.assertEqual(len(self.cands),703);self.assertEqual(len({x['candidate_id'] for x in self.cands}),703)
 def test_09_family_counts_are_exact(self):
  self.assertEqual(Counter(x['family'] for x in self.cands),Counter({'SHIELD_BATTERY':216,'ENERGIZED_ARMOR':120,'REPAIR_DRONE':72,'SHIELD_BOOSTER':64,'CRYSTALLINE_ARMOR':64,'SHIELD_HARDENER':56,'FIELD_STABILIZER':48,'ABLATIVE_ARMOR':45,'KINETIC_MAGAZINE':9,'MISSILE_MAGAZINE':9}))
 def test_10_hardener_sweep_is_broad(self):
  r=[x for x in self.cands if x['family']=='SHIELD_HARDENER'];self.assertEqual({x['def_bonus_pp'] for x in r},{5,10,15,20});self.assertEqual({x['tp'] for x in r},{1,2});self.assertEqual({x['tl'] for x in r},set(range(3,10)))
 def test_11_battery_sweep_crosses_restore_charges_space(self):
  r=[x for x in self.cands if x['family']=='SHIELD_BATTERY' and x['tl']==1];self.assertEqual(len(r),24);self.assertEqual({x['restore'] for x in r},{2,4,6,8});self.assertEqual({x['charges'] for x in r},{1,2,3});self.assertEqual({x['space'] for x in r},{1,2})
 def test_12_booster_and_ablative_bounds(self):
  self.assertEqual({x['capacity_bonus'] for x in self.cands if x['family']=='SHIELD_BOOSTER'},{2,4,6,8});self.assertEqual({x['ablative_integrity'] for x in self.cands if x['family']=='ABLATIVE_ARMOR'},{2,4,6,8,10})
 def test_13_crystalline_crosses_capacity_and_res_and_starts_tl6(self):
  r=[x for x in self.cands if x['family']=='CRYSTALLINE_ARMOR'];self.assertEqual({x['tl'] for x in r},{6,7,8,9});self.assertEqual({x['res_bonus_pp'] for x in r},{0,5,10,15});self.assertEqual({x['capacity_bonus'] for x in r},{2,4,6,8})
 def test_14_energized_armor_crosses_res_tp_space(self):
  r=[x for x in self.cands if x['family']=='ENERGIZED_ARMOR' and x['tl']==5];self.assertEqual(len(r),24);self.assertEqual({x['res_bonus_pp'] for x in r},{5,10,15,20});self.assertEqual({x['tp'] for x in r},{1,2,3});self.assertEqual({x['space'] for x in r},{1,2})
 def test_15_field_stabilizer_is_late_and_specific(self):
  r=[x for x in self.cands if x['family']=='FIELD_STABILIZER'];self.assertEqual({x['tl'] for x in r},{7,8,9});self.assertEqual({x['spen_reduction'] for x in r},{1,2,3,4})
 def test_16_repair_drone_window_and_bounds(self):
  r=[x for x in self.cands if x['family']=='REPAIR_DRONE'];self.assertEqual({x['tl'] for x in r},{4,5,6});self.assertEqual({x['chance_bonus_pp'] for x in r},{5,10,15,20});self.assertEqual({x['extra_repair_kits'] for x in r},{0,1,2})
 def test_17_ammo_is_fixed_audit_not_tuning_axis(self):
  k=[x for x in self.cands if x['family']=='KINETIC_MAGAZINE'];m=[x for x in self.cands if x['family']=='MISSILE_MAGAZINE'];self.assertEqual(len(k),9);self.assertEqual(len(m),9);self.assertTrue(all(x['ammo_bonus']==25 and x['audit_only']==1 for x in k+m))
 def test_18_representative_deep_designs_are_eight_per_swept_family(self):
  d=representative_designs();self.assertEqual(set(d),set(self.doc['broadSweepFamilies']));self.assertTrue(all(len(v)==8 for v in d.values()));self.assertTrue(all(any(name=='RISING_FULL' for name,_ in v) for v in d.values()));self.assertEqual(self.doc['pairwiseAnchors'],['CENTER','HIGH'])
 def test_19_plan_counts_are_exact(self):
  p=json.loads(PLAN.read_text());self.assertEqual(p['candidateTlPoints'],703);self.assertEqual(p['screenLegalCells'],497555);self.assertEqual(p['plannedDeepCells'],277160);self.assertEqual(p['pairwiseLegalCells'],169040);self.assertEqual(p['substantiveCombatTrials'],44723375)
 def test_20_core_mains_pds_and_defenses_are_fixed_by_study(self):
  txt=' '.join(self.doc['fixedEnvironment']);self.assertIn('K1/E7/M2/SW2',txt);self.assertIn('K155P06/E155P08/A155P07',txt);self.assertIn('Hull/Shield/Armor/DEF/RES',txt)
 def test_21_no_equality_objective_and_final_tp_is_deferred(self):
  g=' '.join(self.doc['guardrails']).lower();self.assertIn('balance is not equality',g);self.assertIn('no global 50',g);self.assertIn('final reactor/tp tuning remains last',g)
 def test_22_power_aux_and_fake_noncombat_effects_are_deferred(self):
  d=' '.join(self.doc['deferred']).lower();self.assertIn('power aux',d);self.assertIn('noncombat',d)
 def _one(self,fam,tl,scenario_filter=None):
  src=next(r for r in _manifest(ROOT,self.doc) if int(r['tl'])==tl and (scenario_filter is None or scenario_filter(r)));c=next(x for x in self.cands if x['family']==fam and x['tl']==tl);m,v=_bind(ROOT,self.doc,src,[c]);self.assertIsNotNone(v);return m,v,c
 def test_23_shield_booster_increases_only_candidate_side_capacity(self):
  m,v,c=self._one('SHIELD_BOOSTER',2);base=int(m.p('shield',2)['capacity']);s=_create_side(m,v.side_b,0);self.assertEqual(s.shield_max,base+int(c['capacity_bonus']))
 def test_24_battery_discharge_is_finite_and_observable(self):
  m,v,c=self._one('SHIELD_BATTERY',1);s=_create_side(m,v.side_b,0);t=_create_side(m,v.side_a,1);s.shield=max(1,int(s.shield_max*.4));before=s.shield;_begin_turn_recharge(m,s,t,0,'cp147_tactical_utility');self.assertGreaterEqual(s.telemetry.aux_shield_battery_discharges,1);self.assertGreater(s.shield,before)
 def test_25_ablative_outer_layer_absorbs_before_primary_armor(self):
  m,v,c=self._one('ABLATIVE_ARMOR',1,lambda r:r['scenario_stratum']=='ARMOR_PRESSURE');s=_create_side(m,v.side_b,0);a0=s.armor_integrity;abl=s.ablative_integrity;_apply_committed_damage(m,s,DamageCommit('DirectFire','A','B','direct',min(2,abl),0,0,False),100,1);self.assertEqual(s.armor_integrity,a0);self.assertGreater(s.telemetry.aux_ablative_absorbed,0)
 def test_26_crystalline_adds_capacity_and_suppresses_tactical_regen(self):
  m,v,c=self._one('CRYSTALLINE_ARMOR',6);s=_create_side(m,v.side_b,0);base=int(m.p('armor',6)['ai']);self.assertEqual(s.armor_max,base+int(c['capacity_bonus']));self.assertEqual(s.armor_regen_reserve_remaining,0)
 def test_27_energized_armor_reduces_armor_damage_when_active(self):
  m,v,c=self._one('ENERGIZED_ARMOR',5,lambda r:r['scenario_stratum']=='ARMOR_PRESSURE');s1=_create_side(m,v.side_b,0);s2=_create_side(m,v.side_b,0);d=DamageCommit('DirectFire','A','B','direct',10,0,0,False);_apply_committed_damage(m,s1,d,100,1);_apply_committed_damage(m,s2,DamageCommit('DirectFire','A','B','direct',10,0,0,False,True,False),100,1);self.assertGreaterEqual(s2.armor_integrity,s1.armor_integrity)
 def test_28_field_stabilizer_reduces_effective_spen_when_active(self):
  m,v,c=self._one('FIELD_STABILIZER',7);s1=_create_side(m,v.side_b,0);s2=_create_side(m,v.side_b,0);_apply_committed_damage(m,s1,DamageCommit('DirectFire','A','B','direct',8,10,0,False),30,1);_apply_committed_damage(m,s2,DamageCommit('DirectFire','A','B','direct',8,10,0,False,False,True),30,1);self.assertGreaterEqual(s2.shield,s1.shield)
 def test_29_repair_drone_can_turn_near_miss_into_dc_success(self):
  m,v,c=self._one('REPAIR_DRONE',4);s=_create_side(m,v.side_b,0);s.hull-=2;s.repair_kits_remaining=max(1,s.repair_kits_remaining);base=int(m.p('damage_control',4)['hullRepairChancePp']);c['chance_bonus_pp']=20;m.cp158_aux_profiles[c['candidate_id']]=c;spent=_attempt_hull_damage_control(m,s,99,base+10);self.assertGreater(spent,0);self.assertGreater(s.telemetry.damage_control_successes,0)
 def test_30_disposition_register_covers_catalog_and_reuses_closed_pds_ew(self):
  import tempfile
  with tempfile.TemporaryDirectory() as td:r=disposition(ROOT,Path(td)/'d.csv')
  ids={x['id']:x for x in r};self.assertEqual(ids['PDS']['disposition'],'REUSE_CLOSED_CP155');self.assertEqual(ids['ECM']['disposition'],'REUSE_CLOSED_INTEGRATED');self.assertEqual(ids['shield-battery']['disposition'],'BROAD_COMBAT_SWEEP')

if __name__=='__main__':unittest.main()
