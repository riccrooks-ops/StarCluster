import csv, hashlib, json, unittest
from pathlib import Path
from starcluster_research.study import resolve_relocated_path
ROOT=Path(__file__).resolve().parents[3]
EV=ROOT/'docs/validation/evidence/checkpoint-156'

def js(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def rows(p):
    with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def sha(p):
    p=resolve_relocated_path(p)
    h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()

class Cp156ResearchContinuityTests(unittest.TestCase):
    def test_01_definition_is_zero_combat(self):
        d=js(ROOT/'tools/checkpoints/checkpoint-156/checkpoint_156_definition.json'); self.assertEqual(d['checkpoint'],156); self.assertEqual(d['substantiveCombatTrials'],0); self.assertFalse(d['automaticPromotion'])
    def test_02_study_is_preservation_only(self):
        s=js(ROOT/'docs/archive/testing/pre-cp165-active/cp156_research_continuity_audit_v0_1.json'); self.assertEqual(s['substantiveCombatTrials'],0); self.assertFalse(s['authorityChangesAllowed'])
    def test_03_cp155_native_is_hash_locked(self):
        s=js(ROOT/'docs/archive/testing/pre-cp165-active/cp156_research_continuity_audit_v0_1.json'); p=EV/'accepted-cp155/CP155_NATIVE_ACCEPTANCE_SUMMARY.json'; self.assertEqual(s['acceptedCp155NativeResultsArchiveSha256'],'f368612abdbf44b1eb78f0695cc6b72be491834c22564be063a74f8823298b52'); self.assertEqual(js(p)['substantiveCombatTrials'],15511200)
    def test_04_recent_promotion_audit_has_all_checkpoints(self):
        r=rows(EV/'promotion_audit_v0_1.csv'); recent=[x for x in r if 149<=int(x['checkpoint'])<=155]; self.assertEqual([int(x['checkpoint']) for x in recent],list(range(149,156))); self.assertTrue(all(x['automatic_promotion'].lower()=='false' for x in recent))
    def test_05_recent_research_has_no_missed_promotion(self):
        r=rows(EV/'promotion_audit_v0_1.csv'); recent=[x for x in r if 149<=int(x['checkpoint'])<=155]; self.assertTrue(all(x['audit_result']=='NO_MISSED_PROMOTION' for x in recent))
    def test_06_authority_snapshot_matches_files(self):
        a=js(EV/'authority_snapshot_v0_1.json'); self.assertEqual(a['activeNumericalAuthority']['sha256'],sha(ROOT/a['activeNumericalAuthority']['path'])); self.assertEqual(a['conceptAuthority']['sha256'],sha(ROOT/a['conceptAuthority']['path']))
    def test_07_findings_cover_mains_and_pds(self):
        topics={x['topic'] for x in rows(EV/'research_findings_ledger_v0_1.csv')}; self.assertTrue({'KINETIC_MAIN','ENERGY_MAIN','GP_MISSILE_MAIN','SWARMER_MAIN','KINETIC_PDS','ENERGY_PDS','AMM_PDS'}<=topics)
    def test_08_findings_preserve_open_aux_and_tp(self):
        d={x['topic']:x for x in rows(EV/'research_findings_ledger_v0_1.csv')}; self.assertEqual(d['AUX']['status'],'OPEN_NEXT'); self.assertEqual(d['REACTOR_TP']['status'],'OPEN_FINAL')
    def test_09_no_pds_missile_threat_is_guardrail(self):
        d={x['topic']:x for x in rows(EV/'research_findings_ledger_v0_1.csv')}; self.assertEqual(d['NO_PDS_MISSILE_THREAT']['status'],'GUARDRAIL')
    def test_10_viable_ladders_preserved(self):
        r=rows(EV/'viable_ladder_register_v0_1.csv'); ids={x['ladder_id'] for x in r}; self.assertTrue({'E7','M2','M3','SW2','K155P03','K155P06','E155P08','A155P07'}<=ids)
    def test_11_all_viable_ladders_are_research_only(self):
        self.assertTrue(all(x['promotion_status']=='RESEARCH_ONLY_NOT_PROMOTED' for x in rows(EV/'viable_ladder_register_v0_1.csv')))
    def test_12_pds_50_guardrail_exists(self):
        g=js(EV/'guardrail_registry_v0_1.json'); rules={x['id']:x['rule'] for x in g['principles']}; self.assertIn('NO_GLOBAL_PDS_50',rules); self.assertIn('50%',rules['NO_GLOBAL_PDS_50'])
    def test_13_balance_not_equality_guardrail_exists(self):
        g=js(EV/'guardrail_registry_v0_1.json'); ids={x['id'] for x in g['principles']}; self.assertIn('BALANCE_NOT_EQUALITY',ids); self.assertIn('PARETO_MULTI_OBJECTIVE',ids)
    def test_14_closed_surface_reuse_guardrail_exists(self):
        g=js(EV/'guardrail_registry_v0_1.json'); ids={x['id'] for x in g['principles']}; self.assertIn('REUSE_CLOSED_SURFACES',ids)
    def test_15_energy_and_pds_identity_guardrails_exist(self):
        g=js(EV/'guardrail_registry_v0_1.json'); ids={x['id'] for x in g['principles']}; self.assertIn('E_MAIN_IDENTITY',ids); self.assertIn('PDS_IDENTITIES',ids)
    def test_16_tp_is_explicitly_last(self):
        g=js(EV/'guardrail_registry_v0_1.json'); ids={x['id'] for x in g['principles']}; self.assertIn('TP_LAST',ids); f=js(EV/'future_pass_contract_v0_1.json'); self.assertEqual(f['nextSubstantivePass']['name'],'Defense/AUX Lifetime Viability')
    def test_17_future_pass_forbids_resweeps(self):
        f=js(EV/'future_pass_contract_v0_1.json'); banned=' '.join(f['nextSubstantivePass']['mustNotDo']); self.assertIn('broad K/E/M/Swarmer resweep',banned); self.assertIn('broad PDS resweep',banned)
    def test_18_evidence_hash_chain_is_nontrivial_and_valid(self):
        r=rows(EV/'evidence_chain_sha256_v0_1.csv'); self.assertGreaterEqual(len(r),50); self.assertTrue(all(sha(ROOT/x['path'])==x['sha256'] for x in r))
    def test_19_cp155_key_outputs_are_preserved(self):
        names={p.name for p in (EV/'accepted-cp155').iterdir() if p.is_file()}; self.assertTrue({'CP155_NATIVE_ACCEPTANCE_SUMMARY.json','CP155_PDS_LADDER_CANDIDATES.csv','CP155_PDS_TRIAD_VIABILITY_MAP.csv','CP155_NO_PDS_BASELINE.csv'}<=names)
    def test_20_register_points_to_aux_then_tp(self):
        r=js(EV/'research_continuity_register_v0_1.json'); self.assertEqual(r['acceptedBaseline'],155); self.assertIn('Defense/AUX',r['nextStage']); self.assertIn('Reactor/TP',r['nextStage'])

if __name__=='__main__': unittest.main()
