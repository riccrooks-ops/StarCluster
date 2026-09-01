from __future__ import annotations
import json, tempfile, unittest
from pathlib import Path

from starcluster_research.power_closure_sweep import (
    SCHEMA, STACK_TIERS, MAIN_LEVELS, PAIRINGS, apu_tp, validate_study,
    combat_contexts, plan, static_analysis, smoke,
)
from starcluster_research.research_execution_baseline_pf4 import load_research_execution_baseline_pf4
from starcluster_research.reactor_tp_equilibrium import enumerate_loadouts

ROOT=Path(__file__).resolve().parents[3]
STUDY=ROOT/'docs/archive/testing/pre-cp165-active/cp164_final_isolated_power_economy_closure_study_v0_1.json'

def doc(): return json.loads(STUDY.read_text(encoding='utf-8-sig'))

class CP164PowerClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=doc(); cls.m=load_research_execution_baseline_pf4(ROOT)

    def test_01_schema(self): self.assertEqual(self.d['schemaVersion'],SCHEMA)
    def test_02_checkpoint(self): self.assertEqual(self.d['checkpoint'],164)
    def test_03_accepted_base(self): self.assertEqual(self.d['acceptedBaselineCheckpoint'],163)
    def test_04_pf4(self): self.assertEqual(self.d['pendingFinalizationBaselineId'],'CP160-PF4')
    def test_05_main_space(self): self.assertEqual(self.d['mainReactorSpace'],6)
    def test_06_main_offsets(self): self.assertEqual(tuple(self.d['mainReactorOffsetsFromPf4']),MAIN_LEVELS)
    def test_07_apu_space(self): self.assertEqual(self.d['apuSpace'],2)
    def test_08_apu_early(self): self.assertTrue(all(apu_tp(t)==1 for t in range(1,5)))
    def test_09_apu_mature(self): self.assertTrue(all(apu_tp(t)==2 for t in range(5,10)))
    def test_10_no_plus3(self): self.assertNotIn(3,self.d['selectedApuOperationalTpByTl'])
    def test_11_tiers(self): self.assertEqual(tuple(self.d['stackTiers']),STACK_TIERS)
    def test_12_pairings(self): self.assertEqual(len(PAIRINGS),3)
    def test_13_pair_low_center(self): self.assertEqual(PAIRINGS[0],('LOW_vs_CENTER',-1,0))
    def test_14_pair_center_high(self): self.assertEqual(PAIRINGS[1],('CENTER_vs_HIGH',0,1))
    def test_15_pair_low_high(self): self.assertEqual(PAIRINGS[2],('LOW_vs_HIGH',-1,1))
    def test_16_stoch_samples(self): self.assertEqual(self.d['stochasticTurnSamplesPerVariant'],5000)
    def test_17_combat_trials(self): self.assertEqual(self.d['combatTrialsPerCell'],2000)
    def test_18_validate(self): self.assertEqual(validate_study(self.d),[])
    def test_19_policy_final(self): self.assertTrue(self.d['interpretationPolicy']['finalIsolatedPowerSweep'])
    def test_20_policy_next(self): self.assertTrue(self.d['interpretationPolicy']['wholeSystemIntegrationNext'])
    def test_21_no_promotion(self): self.assertFalse(self.d['interpretationPolicy']['automaticPromotion'])
    def test_22_main_space_all_tl(self): self.assertTrue(all(int(self.m.p('reactor',t)['space'])==6 for t in range(1,10)))
    def test_23_pf4_ladder(self): self.assertEqual([int(self.m.p('reactor',t)['operationalTp']) for t in range(1,10)],[5,6,7,8,9,10,11,12,13])
    def test_24_legal_population(self): self.assertEqual(len(enumerate_loadouts(self.m,reactor_space=6)),22482)
    def test_25_one_reactor_population(self): self.assertEqual(sum(x.reactor_count==1 for x in enumerate_loadouts(self.m,reactor_space=6)),16741)
    def test_26_contexts_tl1(self): self.assertEqual(len(combat_contexts(ROOT,1)),90)
    def test_27_contexts_tl9(self): self.assertEqual(len(combat_contexts(ROOT,9)),90)
    def test_28_context_has_direct_delta(self):
        v,p,lo,hi,tier,cnt=combat_contexts(ROOT,5)[0]
        self.assertGreater(v.side_a.auxiliary_power_tp-v.side_b.auxiliary_power_tp,0)
    def test_29_zero_tier_present(self): self.assertTrue(any(str(x[4])=='0' for x in combat_contexts(ROOT,5)))
    def test_30_max_tier_present(self): self.assertTrue(any(str(x[4])=='MAX' for x in combat_contexts(ROOT,5)))
    def test_31_plan_scale(self):
        with tempfile.TemporaryDirectory() as td:
            s=plan(ROOT,STUDY,Path(td))
            self.assertEqual((s['stochasticVariants'],s['stochasticTurnSamples'],s['combatCells'],s['combatTrials']),(810,4050000,810,1620000))
    def test_32_smoke(self):
        with tempfile.TemporaryDirectory() as td:
            s=smoke(ROOT,STUDY,Path(td)); self.assertTrue(s['passed'])

if __name__=='__main__': unittest.main()
