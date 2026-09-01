from __future__ import annotations
import csv, hashlib, json, unittest
from pathlib import Path
from starcluster_research.research_execution_baseline_pf4 import (
    BASELINE_ID,
    aux_profile,
    baseline_identity,
    load_research_execution_baseline_pf4,
)

ROOT = Path(__file__).resolve().parents[3]
PF3 = ROOT / 'docs/archive/player_technology/pre-cp165-active/technology_research_execution_baseline_pending_finalization_v0_3.json'
PF4 = ROOT / 'docs/design/player_technology/technology_research_execution_baseline_pending_finalization_v0_4.json'
PROD = ROOT / 'docs/design/player_technology/technology_numerical_matrix_v0_9.json'
EVIDENCE = ROOT / 'docs/validation/evidence/checkpoint-160'
SELECT = EVIDENCE / 'cp159_aux_closure_selection_evidence_v0_1.json'
LEDGER = EVIDENCE / 'aux_pending_finalization_promotion_ledger_v0_2.csv'
MANIFEST = EVIDENCE / 'research_execution_baseline_manifest_v0_4.json'
CONFORMANCE = EVIDENCE / 'pf4_conformance_report_v0_1.json'
ACCEPTED = EVIDENCE / 'accepted-cp159'


def sha(path: Path) -> str:
    h = hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()


def rows(path: Path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


class Cp160AuxPf4PromotionTests(unittest.TestCase):
    def setUp(self):
        self.pf3 = json.loads(PF3.read_text(encoding='utf-8-sig'))
        self.pf4 = json.loads(PF4.read_text(encoding='utf-8-sig'))
        self.matrix = load_research_execution_baseline_pf4(ROOT)
        self.selection = json.loads(SELECT.read_text(encoding='utf-8-sig'))

    def test_01_pf4_identity(self):
        self.assertEqual(BASELINE_ID, 'CP160-PF4')
        self.assertEqual(self.pf4['pendingFinalizationResearchBaseline']['baselineId'], 'CP160-PF4')

    def test_02_pf4_supersedes_pf3(self):
        meta = self.pf4['pendingFinalizationResearchBaseline']
        self.assertEqual(meta['supersedes'], 'CP159-PF3')
        self.assertEqual(meta['baseBaselineId'], 'CP159-PF3')
        self.assertEqual(meta['acceptedContinuityCheckpoint'], 159)

    def test_03_executable_profiles_unchanged_from_pf3(self):
        self.assertEqual(self.pf3['profiles'], self.pf4['profiles'])

    def test_04_branches_unchanged_from_pf3(self):
        self.assertEqual(self.pf3['branches'], self.pf4['branches'])
        self.assertEqual(self.pf3['candidateBranchSeeds'], self.pf4['candidateBranchSeeds'])

    def test_05_production_authority_preserved(self):
        self.assertEqual(sha(PROD), '3088b0a9eb45f6bf505c24513e8bb2ac878819db4ab464ccfea330243c82f194')
        self.assertNotEqual(sha(PROD), sha(PF4))

    def test_06_all_ten_aux_profiles_materialized(self):
        self.assertEqual(set(self.matrix.pending_finalization_aux_profiles), {
            'shieldBattery','shieldBooster','shieldHardener','ablativeArmor','energizedArmor',
            'crystallineArmor','fieldStabilizer','repairDroneBay','kineticMagazine','missileMagazine'
        })

    def test_07_field_stabilizer_is_selected_cp159(self):
        row = self.matrix.pending_finalization_aux_profiles['fieldStabilizer']
        self.assertEqual(row['status'], 'PENDING_FINALIZATION_SELECTED_CP159')
        self.assertEqual(row['sourceLadder'], 'FST_HIGH')

    def test_08_field_stabilizer_exact_trajectory(self):
        got = [(t, aux_profile(ROOT,'fieldStabilizer',t)['spenReduction'], aux_profile(ROOT,'fieldStabilizer',t)['tp']) for t in (7,8,9)]
        self.assertEqual(got, [(7,16,1),(8,18,1),(9,20,1)])

    def test_09_field_stabilizer_not_available_before_tl7(self):
        self.assertIsNone(aux_profile(ROOT,'fieldStabilizer',6))

    def test_10_crystalline_is_selected_rise_a(self):
        row = self.matrix.pending_finalization_aux_profiles['crystallineArmor']
        self.assertEqual(row['status'], 'PENDING_FINALIZATION_SELECTED_CP159')
        self.assertEqual(row['sourceLadder'], 'CRY_RISE_A')

    def test_11_crystalline_exact_late_trajectory(self):
        got = [(t, aux_profile(ROOT,'crystallineArmor',t)['capacityBonus'], aux_profile(ROOT,'crystallineArmor',t)['resBonusPp']) for t in (8,9)]
        self.assertEqual(got, [(8,8,15),(9,10,20)])

    def test_12_crystalline_retains_lower_tl_cp158_values(self):
        got = [(t, aux_profile(ROOT,'crystallineArmor',t)['capacityBonus'], aux_profile(ROOT,'crystallineArmor',t)['resBonusPp']) for t in (6,7)]
        self.assertEqual(got, [(6,2,0),(7,4,5)])

    def test_13_repair_drone_is_selected_cp159(self):
        row = self.matrix.pending_finalization_aux_profiles['repairDroneBay']
        self.assertEqual(row['status'], 'PENDING_FINALIZATION_SELECTED_CP159')
        self.assertIn('different eligible repair targets', row['mechanic'])
        self.assertIn('normal Damage Control per-attempt Tactical Power cost', row['attemptRules'])

    def test_14_repair_drone_extra_action_and_no_same_target_reroll(self):
        for tl in range(2,10):
            row = aux_profile(ROOT,'repairDroneBay',tl)
            self.assertEqual(row['additionalActionsPerPhase'], 1)
            self.assertTrue(row['differentTargetRequired'])
            self.assertFalse(row['sameTargetRerollAllowed'])

    def test_15_repair_drone_extra_kits_equal_default_reserve(self):
        for tl in range(2,10):
            row = aux_profile(ROOT,'repairDroneBay',tl)
            self.assertEqual(row['additionalPreparedRepairKits'], int(self.matrix.p('damage_control',tl)['preparedRepairKits']))

    def test_16_repair_drone_uses_normal_attempt_tp(self):
        for tl in range(2,10):
            row = aux_profile(ROOT,'repairDroneBay',tl)
            self.assertEqual(row['droneAttemptTp'], int(self.matrix.p('damage_control',tl)['attemptTp']))

    def test_17_cp159_native_acceptance_is_imported_and_clean(self):
        n = json.loads((ACCEPTED/'CP159_NATIVE_ACCEPTANCE_SUMMARY.json').read_text(encoding='utf-8-sig'))
        self.assertEqual(n['checkpoint'], 159)
        self.assertEqual(n['substantiveCombatTrials'], 3390000)
        self.assertEqual(n['repairDroneMicroTrials'], 1728000)
        self.assertEqual(n['substantiveErrors'], 0)
        self.assertEqual(n['substantiveTurnCapSentinels'], 0)

    def test_18_cp159_native_archive_hash_locked(self):
        record=(ACCEPTED/'CP159_NATIVE_RESULTS_ARCHIVE_SHA256.txt').read_text(encoding='utf-8-sig').strip()
        self.assertEqual(record, 'e7c17f3aeb6d6833620e8f8ca72694fdc4be589ef9791fb73e7cc0cfbe771a65  StarCluster_CP159_native_results_20260830_143917.zip')

    def test_19_field_selection_evidence_matches_high_package(self):
        f = self.selection['fieldStabilizer']
        self.assertEqual(f['selectedPackage'], 'FST_HIGH')
        self.assertAlmostEqual(f['meanUplift'], 0.08440190904348747)
        self.assertAlmostEqual(f['maxMeanUplift'], 0.09513666226082305)

    def test_20_crystalline_selection_evidence_matches_rise_a(self):
        c = self.selection['crystallineArmor']
        self.assertEqual(c['selectedPackage'], 'CRY_RISE_A')
        self.assertAlmostEqual(c['meanUplift'], 0.09093030812741487)
        self.assertGreater(c['riseBMeanUplift'], c['meanUplift'])
        self.assertGreater(c['riseCMeanUplift'], c['riseBMeanUplift'])

    def test_21_repair_drone_selected_kit_endpoint_is_full_default_load(self):
        for tl, r in self.selection['repairDroneBay']['byTl'].items():
            self.assertEqual(r['defaultKits'], r['selectedAdditionalKits'])

    def test_22_aux_is_closed_but_reactor_tp_is_open(self):
        close = self.pf4['cp160AuxClosurePromotion']
        self.assertTrue(close['isolatedAuxMagnitudeArchitectureClosed'])
        self.assertTrue(close['poweredAuxTpCostsProvisional'])
        self.assertEqual(self.pf4['pendingFinalizationResearchBaseline']['openDependencies'], ['FINAL_REACTOR_TP_SCARCITY'])

    def test_23_promotion_ledger_covers_ten_profiles_and_no_open_aux_closure(self):
        rr = rows(LEDGER)
        self.assertEqual(len(rr), 10)
        self.assertFalse(any('OPEN' in r['status'] or 'BOUNDARY_SUPPORTED' in r['status'] for r in rr))

    def test_24_manifest_conformance_and_baseline_identity(self):
        man = json.loads(MANIFEST.read_text(encoding='utf-8-sig'))
        conf = json.loads(CONFORMANCE.read_text(encoding='utf-8-sig'))
        ident = baseline_identity(ROOT)
        self.assertEqual(man['materializedMatrixSha256'], sha(PF4))
        self.assertTrue(conf['passed'])
        self.assertTrue(conf['profilesUnchangedFromPf3'])
        self.assertEqual(ident['baselineId'], 'CP160-PF4')
        self.assertEqual(ident['openDependencies'], ['FINAL_REACTOR_TP_SCARCITY'])


if __name__ == '__main__':
    unittest.main()
