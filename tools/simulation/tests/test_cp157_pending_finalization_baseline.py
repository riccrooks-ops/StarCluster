import csv, hashlib, json, unittest
from pathlib import Path
from starcluster_research.research_execution_baseline import load_research_execution_baseline, baseline_identity, BASELINE_ID
ROOT=Path(__file__).resolve().parents[3]
EV=ROOT/'docs/validation/evidence/checkpoint-157'
BASE=ROOT/'docs/archive/player_technology/pre-cp165-active/technology_research_execution_baseline_pending_finalization_v0_1.json'
PROD=ROOT/'docs/design/player_technology/technology_numerical_matrix_v0_9.json'
def js(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def rows(p):
    with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def sha(p): h=hashlib.sha256();h.update(p.read_bytes());return h.hexdigest()
class Cp157PendingFinalizationBaselineTests(unittest.TestCase):
    def test_01_zero_combat_research_authority_checkpoint(self):
        d=js(ROOT/'tools/checkpoints/checkpoint-157/checkpoint_157_definition.json'); self.assertEqual(d['substantiveCombatTrials'],0); self.assertTrue(d['researchExecutionAuthorityChangesAllowed']); self.assertFalse(d['productionAuthorityChangesAllowed'])
    def test_02_cp156_native_evidence_is_accepted(self):
        s=js(EV/'accepted-cp156/CP156_NATIVE_ACCEPTANCE_SUMMARY.json'); self.assertEqual(s['checkpoint'],156); self.assertEqual(s['pythonTestsPassed'],520); self.assertTrue(s['continuityAuditCompleted'])
    def test_03_production_matrix_is_still_cp137_hash(self): self.assertEqual(sha(PROD),'3088b0a9eb45f6bf505c24513e8bb2ac878819db4ab464ccfea330243c82f194')
    def test_04_baseline_identity_and_status(self):
        b=js(BASE); self.assertEqual(b['pendingFinalizationResearchBaseline']['baselineId'],BASELINE_ID); self.assertEqual(b['status'],'PENDING_FINALIZATION_RESEARCH_AUTHORITY')
    def test_05_baseline_manifest_hash_matches(self):
        m=js(EV/'research_execution_baseline_manifest_v0_1.json'); self.assertEqual(m['materializedMatrixSha256'],sha(BASE)); self.assertFalse(m['productionAuthorityReplaced'])
    def test_06_loader_returns_cp157_pf1(self): self.assertEqual(baseline_identity(ROOT)['baselineId'],'CP157-PF1')
    def test_07_kinetic_main_is_k1(self):
        m=load_research_execution_baseline(ROOT); self.assertEqual([m.p('kinetic_main',t)['damage'] for t in range(1,10)],[9,10,12,13,14,15,15,19,20]); self.assertEqual(m.p('kinetic_main',9)['apen'],14)
    def test_08_energy_main_is_e7(self):
        m=load_research_execution_baseline(ROOT); self.assertEqual(m.p('energy_main',1)['strainLimit'],1); self.assertEqual(m.p('energy_main',9)['strainLimit'],2); self.assertEqual(m.p('energy_main',9)['standardDamage'],18); self.assertEqual(m.p('energy_main',9)['overloadDamage'],24); self.assertEqual(m.p('energy_main',9)['overloadTp'],8)
    def test_09_gp_primary_is_m2_and_m3_preserved(self):
        m=load_research_execution_baseline(ROOT); self.assertEqual([m.p('missile_gp_warhead',t)['damage'] for t in range(1,10)],[12,13,15,17,19,21,23,25,27]); a=js(EV/'research_execution_baseline_manifest_v0_1.json'); self.assertIn('M3',a['requiredAlternatives']['gpMissileMain'])
    def test_10_swarmer_primary_is_sw2(self):
        m=load_research_execution_baseline(ROOT); self.assertEqual([m.p('missile_swarmer',t)['packetDamage'] for t in range(2,10)],[7,7,8,9,9,10,11,12])
    def test_11_defensive_point_scale_is_materialized(self):
        m=load_research_execution_baseline(ROOT); self.assertEqual([m.p('hull',t)['hullPoints'] for t in range(1,10)],[24,24,26,26,28,28,30,30,32]); self.assertEqual([m.p('shield',t)['capacity'] for t in range(1,10)],[16,18,20,22,24,26,28,30,32]); self.assertEqual([m.p('armor',t)['ai'] for t in range(1,10)],[12,14,16,18,20,18,20,22,24])
    def test_12_def_res_is_loader_authority(self):
        m=load_research_execution_baseline(ROOT); self.assertEqual([m.def_res_shield_def_pp[t] for t in range(1,10)],[20,22,24,26,28,30,32,34,36]); self.assertEqual(m.def_res_shield_def_pp,m.def_res_armor_res_pp)
    def test_13_reactor_is_explicit_provisional_scaffold(self):
        m=load_research_execution_baseline(ROOT); self.assertEqual([m.p('reactor',t)['operationalTp'] for t in range(1,10)],[5,6,7,8,9,10,11,12,13]); r={x['topic']:x for x in rows(EV/'pending_finalization_promotion_register_v0_1.csv')}; self.assertEqual(r['REACTOR_TP']['status'],'PROVISIONAL_SCAFFOLD')
    def test_14_k_pds_is_k155p06(self):
        m=load_research_execution_baseline(ROOT); self.assertEqual(m.p('kinetic_pds',6)['reactionCapacity'],1); self.assertEqual(m.p('kinetic_pds',7)['reactionCapacity'],2); self.assertEqual(m.p('kinetic_pds',7)['baseChancePp'],12); self.assertEqual(m.p('kinetic_pds',7)['ammo'],75)
    def test_15_e_pds_is_e155p08_lifecycle(self):
        m=load_research_execution_baseline(ROOT); self.assertEqual(m.p('energy_pds',3)['reactionCapacity'],1); self.assertEqual(m.p('energy_pds',4)['extraReactionStrain'],1); self.assertEqual(m.p('energy_pds',4)['strainLimit'],2); self.assertEqual(m.p('energy_pds',7)['safeReactionCapacity'],2); self.assertEqual(m.p('energy_pds',7)['extraReactionStrain'],0)
    def test_16_amm_is_a155p07_range_one_rc3(self):
        m=load_research_execution_baseline(ROOT); self.assertEqual(m.p('amm_pds',3)['reactionCapacity'],2); self.assertEqual(m.p('amm_pds',7)['reactionCapacity'],3); self.assertTrue(m.p('amm_pds',7)['rangeOneAttempt']); self.assertEqual(m.p('amm_pds',7)['ammo'],25)
    def test_17_required_alternates_are_preserved(self):
        a=js(EV/'research_execution_baseline_register_v0_1.json')['requiredAlternates']; self.assertIn('M3',a['GpMissileMain']); self.assertIn('K155P03',a['KineticPds']); self.assertIn('E155P07',a['EnergyPds']); self.assertIn('A155P09',a['AmmPds'])
    def test_18_all_447_viable_rows_survive(self): self.assertEqual(len(rows(EV/'viable_ladder_register_v0_2.csv')),447)
    def test_19_primary_rows_are_labeled_pending(self):
        r=rows(EV/'viable_ladder_register_v0_2.csv'); ids={x['ladder_id'] for x in r if x['promotion_status']=='PENDING_FINALIZATION_PRIMARY'}; self.assertTrue({'K1','E7','M2','SW2','K155P06','E155P08','A155P07'}<=ids)
    def test_20_diff_is_large_and_classified(self):
        r=rows(EV/'research_execution_baseline_diff_v0_1.csv'); self.assertGreaterEqual(len(r),500); self.assertTrue({'PENDING_FINALIZATION_SELECTED','PENDING_FINALIZATION_VALIDATED_ENVIRONMENT','PROVISIONAL_RESEARCH_SCAFFOLD'}<={x['status'] for x in r})
    def test_21_guardrail_requires_research_baseline(self):
        g=js(EV/'guardrail_registry_v0_2.json'); ids={x['id'] for x in g['principles']}; self.assertIn('RESEARCH_EXECUTION_BASELINE_REQUIRED',ids); self.assertIn('NO_STALE_NUMERICAL_MIX',ids)
    def test_22_future_aux_pass_forbids_raw_v09(self):
        f=js(EV/'future_pass_contract_v0_2.json'); self.assertTrue(f['researchExecutionBaseline']['required']); self.assertFalse(f['researchExecutionBaseline']['rawProductionMatrixAllowedForSubstantive'])
    def test_23_no_global_pds_50_guardrail_survives(self):
        g=js(EV/'guardrail_registry_v0_2.json'); self.assertIn('NO_GLOBAL_PDS_50',{x['id'] for x in g['principles']})
    def test_24_no_final_production_promotion(self):
        s=js(ROOT/'docs/archive/testing/pre-cp165-active/cp157_pending_finalization_research_execution_baseline_v0_1.json'); self.assertFalse(s['promotionSemantics']['productionAuthorityReplacement']); self.assertFalse(s['automaticFinalProductionPromotion'])
        wrapper=(ROOT/'tools/checkpoints/checkpoint-157/apply_checkpoint_157.ps1').read_text(encoding='utf-8-sig'); self.assertIn(r'tools\simulation\run_starcluster_research.py',wrapper); self.assertNotIn(r'starcluster_research\cli.py',wrapper)
if __name__=='__main__': unittest.main()
