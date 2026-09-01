from __future__ import annotations
import hashlib, json, tempfile, unittest
from pathlib import Path

from starcluster_research.research_execution_baseline_pf4 import load_research_execution_baseline_pf4
from starcluster_research.reactor_tp_equilibrium import enumerate_loadouts, demand_states
from starcluster_research.reactor_aux_power_calibration import (
    STACK_TIERS, _base_cruiser_space, _stoch_one, aux_specs, combat_contexts, main_supply,
    max_stack, plan, resolved_tier_count, select_carrier, static_analysis,
    validate_study,
)
from starcluster_research.study import load_json

ROOT=Path(__file__).resolve().parents[3]
STUDY=ROOT/'docs/archive/testing/pre-cp165-active/cp162_main_aux_reactor_joint_calibration_study_v0_1.json'
PF4=ROOT/'docs/design/player_technology/technology_research_execution_baseline_pending_finalization_v0_4.json'
PROD=ROOT/'docs/design/player_technology/technology_numerical_matrix_v0_9.json'
CP161_NATIVE=ROOT/'docs/validation/evidence/checkpoint-162/accepted-cp161/CP161_NATIVE_ACCEPTANCE_SUMMARY.json'
CP161_HASH=ROOT/'docs/validation/evidence/checkpoint-162/accepted-cp161/CP161_NATIVE_RESULTS_ARCHIVE_SHA256.txt'

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()

class Cp162ReactorAuxPowerCalibrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=load_json(STUDY);cls.m=load_research_execution_baseline_pf4(ROOT)
        cls.all=enumerate_loadouts(cls.m,reactor_space=6);cls.one=[x for x in cls.all if x.reactor_count==1]
        cls._plan_cache=None
    @classmethod
    def _cached_plan(cls):
        if cls._plan_cache is None:
            with tempfile.TemporaryDirectory() as td: cls._plan_cache=plan(ROOT,STUDY,Path(td))
        return cls._plan_cache
    def test_01_study_validates(self):self.assertEqual(validate_study(self.doc),[])
    def test_02_pf4_baseline_locked(self):self.assertEqual(sha(PF4),'7fd4dfbbe375586de2605361006db84b68f89767c76ba4b76da6cf5f48253155')
    def test_03_production_authority_unchanged(self):self.assertEqual(sha(PROD),'3088b0a9eb45f6bf505c24513e8bb2ac878819db4ab464ccfea330243c82f194')
    def test_04_cp161_native_acceptance_preserved(self):
        n=json.loads(CP161_NATIVE.read_text(encoding='utf-8-sig'));self.assertEqual(n['checkpoint'],161);self.assertEqual(n['pythonTestsPassed'],660);self.assertEqual(n['xunitPassed'],934);self.assertEqual(n['substantiveCombatTrials'],4536000);self.assertEqual(n['combatErrorTrials'],0)
    def test_05_cp161_archive_hash_locked(self):self.assertEqual(CP161_HASH.read_text(encoding='utf-8-sig').strip(),'10f1e967374f005087c93f16a72807069428869d82cdc2cac98d849ec14b363c  StarCluster_CP161_native_results_20260830_171756.zip')
    def test_06_main_reactor_space_fixed_six(self):self.assertTrue(all(int(self.m.p('reactor',t)['space'])==6 for t in range(1,10)))
    def test_07_main_offsets_exact(self):self.assertEqual(self.doc['mainReactorOffsetsFromPf4'],[-1,0,1])
    def test_08_main_supply_examples(self):self.assertEqual([main_supply(self.m,1,o) for o in (-1,0,1)],[4,5,6]);self.assertEqual([main_supply(self.m,9,o) for o in (-1,0,1)],[12,13,14])
    def test_09_aux_sweep_is_full_factorial(self):self.assertEqual(len(aux_specs(self.doc)),16);self.assertEqual(aux_specs(self.doc)[0],(1,1));self.assertEqual(aux_specs(self.doc)[-1],(4,4))
    def test_10_no_count_cap_is_imposed(self):self.assertFalse(self.doc['stackingPolicy']['installationCountCapImposed'])
    def test_11_stack_tiers_include_max(self):self.assertEqual(STACK_TIERS,(1,2,3,'MAX'))
    def test_12_architecture_population_unchanged(self):self.assertEqual(len(self.all),22482);self.assertEqual(len(self.one),16741)
    def test_13_tl1_intact_base_cruiser_space(self):self.assertEqual(_base_cruiser_space(self.m,1),31)
    def test_14_tl1_base_cannot_fit_second_main_reactor(self):self.assertGreater(_base_cruiser_space(self.m,1,reactors=2),int(self.m.p('hull',1)['capacity']))
    def test_15_tl7_base_can_fit_second_main_reactor(self):self.assertLessEqual(_base_cruiser_space(self.m,7,reactors=2),int(self.m.p('hull',7)['capacity']))
    def test_16_tl1_base_can_stack_four_one_space_aux(self):self.assertEqual((int(self.m.p('hull',1)['capacity'])-_base_cruiser_space(self.m,1))//1,4)
    def test_17_unrestricted_legal_population_contains_large_stack_carriers(self):self.assertGreaterEqual(max(max_stack(x,1) for x in self.one if x.tl==9),10)
    def test_18_max_tier_resolves_to_population_max(self):
        rows=[x for x in self.one if x.tl==9];self.assertEqual(resolved_tier_count(rows,1,'MAX'),max(max_stack(x,1) for x in rows))
    def test_19_carrier_selection_is_space_legal(self):
        x=select_carrier(self.m,self.one,tl=9,space_each=2,count=3,weapon='E');self.assertIsNotNone(x);self.assertGreaterEqual(x.free_space,6)
    def test_20_carrier_selection_is_power_hungry(self):
        x=select_carrier(self.m,self.one,tl=7,space_each=1,count=3,weapon='E');self.assertGreaterEqual(demand_states(self.m,x)['full'],demand_states(self.m,x)['core'])
    def test_21_combat_contexts_cover_all_aux_specs_somewhere(self):
        c=combat_contexts(ROOT,STUDY,9);self.assertEqual({(s,tp) for _,s,tp,_,_ in c},set(aux_specs(self.doc)))
    def test_22_combat_contexts_are_mirrored(self):
        c=combat_contexts(ROOT,STUDY,9);self.assertTrue(any(v.side_a.auxiliary_reactor_count>0 and v.side_b.auxiliary_reactor_count==0 for v,*_ in c));self.assertTrue(any(v.side_b.auxiliary_reactor_count>0 and v.side_a.auxiliary_reactor_count==0 for v,*_ in c))
    def test_23_combat_builds_respect_space(self):
        for tl in (1,7,9):
            for v,*_ in combat_contexts(ROOT,STUDY,tl):self.assertLessEqual(v.side_a.combat_space,v.side_a.capacity);self.assertLessEqual(v.side_b.combat_space,v.side_b.capacity)
    def test_24_aux_power_is_additive_not_main_reactor_count(self):
        v,s,tp,cnt,swap=next(x for x in combat_contexts(ROOT,STUDY,9) if x[3]>=2);stack=v.side_a if v.side_a.auxiliary_reactor_count else v.side_b;self.assertEqual(stack.auxiliary_power_tp,stack.auxiliary_reactor_count*tp)
        l=select_carrier(self.m,self.one,tl=9,space_each=2,count=2,weapon='E');doc=dict(self.doc);doc['stochasticTurnSamplesPerVariant']=20;r,a=_stoch_one(str(ROOT),doc,l,2,2,2,0,'DAMAGE_CRISIS');self.assertEqual(r['samples'],20);self.assertTrue(a)
    def test_25_all_three_weapon_families_present_in_combat(self):
        c=combat_contexts(ROOT,STUDY,9);self.assertEqual({v.side_a.weapon_family for v,*_ in c}|{v.side_b.weapon_family for v,*_ in c},{'Kinetic','Energy','Missile'})
    def test_26_static_products_exact_scale(self):
        with tempfile.TemporaryDirectory() as td:r=static_analysis(ROOT,STUDY,Path(td))
        self.assertEqual(r['densityRows'],144);self.assertEqual(r['baseCruiserRows'],36);self.assertEqual(r['legalStackSupportRows'],2496);self.assertEqual(r['carrierRows'],528)
    def test_27_plan_exact_stochastic_scale(self):
        r=self._cached_plan()
        self.assertEqual(r['stochasticVariants'],8280);self.assertEqual(r['stochasticTurnSamples'],16560000)
    def test_28_plan_exact_combat_scale(self):
        r=self._cached_plan()
        self.assertEqual(r['combatContexts'],2760);self.assertEqual(r['combatCells'],8280);self.assertEqual(r['combatTrials'],4140000)
    def test_29_main_reactor_equivalence_risk_is_explicit(self):
        self.assertTrue(self.doc['interpretationPolicy']['auxiliaryReactorMustNotEconomicallyReplaceFullMainReactor'])
    def test_30_count_cap_is_evidence_driven_only(self):self.assertTrue(self.doc['interpretationPolicy']['countCapMayBeRecommendedOnlyIfEconomicsFailToBoundStacking'])
    def test_31_no_auto_promotion_or_tuning(self):self.assertFalse(self.doc['interpretationPolicy']['automaticPromotion']);self.assertFalse(self.doc['interpretationPolicy']['tuningAllowed'])
    def test_32_player_and_broad_legal_envelopes_both_required(self):self.assertTrue(self.doc['interpretationPolicy']['playerBaseCruiserAndBroadLegalEnvelopeBothRetained'])

if __name__=='__main__':unittest.main()
