from __future__ import annotations
import hashlib, json, tempfile, unittest
from pathlib import Path

from starcluster_research.study import load_json
from starcluster_research.research_execution_baseline_pf4 import load_research_execution_baseline_pf4
from starcluster_research.reactor_tp_equilibrium import (
    DOCTRINES, PRIORITY, Request, _allocate, _aux, _costs, _lever_overrides,
    _pf4_aux_registry, combat_contexts, demand_states, enumerate_loadouts,
    plan, representative_loadouts, validate_study,
)

ROOT = Path(__file__).resolve().parents[3]
STUDY = ROOT / 'docs/archive/testing/pre-cp165-active/cp161_reactor_tp_equilibrium_study_v0_1.json'
PF4 = ROOT / 'docs/design/player_technology/technology_research_execution_baseline_pending_finalization_v0_4.json'
PROD = ROOT / 'docs/design/player_technology/technology_numerical_matrix_v0_9.json'
CP160_NATIVE = ROOT / 'docs/validation/evidence/checkpoint-161/accepted-cp160/CP160_NATIVE_ACCEPTANCE_SUMMARY.json'
CP160_HASH = ROOT / 'docs/validation/evidence/checkpoint-161/accepted-cp160/CP160_NATIVE_RESULTS_ARCHIVE_SHA256.txt'

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

class Cp161ReactorTpEquilibriumTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = load_json(STUDY)
        cls.m = load_research_execution_baseline_pf4(ROOT)
        cls.rows = enumerate_loadouts(cls.m, reactor_space=6)
        cls.one = [x for x in cls.rows if x.reactor_count == 1]
        cls.two = [x for x in cls.rows if x.reactor_count == 2]
        cls.reps = representative_loadouts(cls.m, cls.one, 12)

    def test_01_study_validates(self):
        self.assertEqual(validate_study(self.doc), [])

    def test_02_pf4_is_mandatory_baseline(self):
        self.assertEqual(self.doc['pendingFinalizationBaselineId'], 'CP160-PF4')
        self.assertEqual(sha(PF4), '7fd4dfbbe375586de2605361006db84b68f89767c76ba4b76da6cf5f48253155')

    def test_03_production_authority_is_unchanged(self):
        self.assertEqual(sha(PROD), '3088b0a9eb45f6bf505c24513e8bb2ac878819db4ab464ccfea330243c82f194')
        self.assertNotEqual(sha(PROD), sha(PF4))

    def test_04_cp160_native_acceptance_is_preserved(self):
        n = json.loads(CP160_NATIVE.read_text(encoding='utf-8-sig'))
        self.assertEqual(n['checkpoint'], 160)
        self.assertEqual(n['pythonTestsPassed'], 628)
        self.assertEqual(n['xunitPassed'], 934)
        self.assertEqual(n['pendingFinalizationBaselineId'], 'CP160-PF4')
        self.assertTrue(n['baselinePromotionCompleted'])

    def test_05_cp160_native_archive_hash_is_locked(self):
        self.assertEqual(CP160_HASH.read_text(encoding='utf-8-sig').strip(), 'a15271ce19677b152c6181306354c0c3e204a2c3d36ec7a5d02e8a22df1d1fbf  StarCluster_CP160_native_results_20260830_162554.zip')

    def test_06_current_reactor_scaffold_exact(self):
        got=[(t,int(self.m.p('reactor',t)['operationalTp']),int(self.m.p('reactor',t)['degradedTp']),int(self.m.p('reactor',t)['emergencyTp'])) for t in range(1,10)]
        self.assertEqual(got,[(1,5,3,1),(2,6,4,2),(3,7,5,2),(4,8,6,3),(5,9,6,3),(6,10,7,3),(7,11,8,4),(8,12,8,4),(9,13,9,5)])

    def test_07_current_reactor_space_is_six(self):
        self.assertEqual([int(self.m.p('reactor',t)['space']) for t in range(1,10)],[6]*9)

    def test_08_supply_sweep_is_deliberately_broad(self):
        self.assertEqual(self.doc['operationalSupplySweep'], {'minimumTp':2,'maximumTp':30,'note':self.doc['operationalSupplySweep']['note']})
        self.assertLess(self.doc['operationalSupplySweep']['minimumTp'], 5)
        self.assertGreater(self.doc['operationalSupplySweep']['maximumTp'], 20)

    def test_09_reactor_space_sweep_is_four_through_eight(self):
        self.assertEqual(self.doc['reactorSpaceSweep'], [4,5,6,7,8])

    def test_10_combat_offsets_are_matched_and_broad(self):
        self.assertEqual(self.doc['combatSupplyOffsetsFromPf4'],[-4,-2,0,2,4,6,8])

    def test_11_exact_architecture_population(self):
        self.assertEqual(len(self.rows),22482)
        self.assertEqual(len(self.one),16741)
        self.assertEqual(len(self.two),5741)

    def test_12_architectures_respect_space_capacity(self):
        self.assertTrue(all(x.used_space <= x.capacity and x.free_space == x.capacity-x.used_space for x in self.rows))

    def test_13_two_reactor_architectures_exist_every_tl(self):
        self.assertEqual({x.tl for x in self.two},set(range(1,10)))

    def test_14_crystalline_zeroes_armor_regen_demand(self):
        x=next(r for r in self.one if r.tl==9 and r.crystalline and r.weapon=='K')
        self.assertEqual(_costs(self.m,x)['armor_regen'],0)

    def test_15_field_stabilizer_is_late_and_powered(self):
        self.assertIsNone(_aux(self.m,'fieldStabilizer',6))
        self.assertEqual([(_aux(self.m,'fieldStabilizer',t)['spenReduction'],_aux(self.m,'fieldStabilizer',t)['tp']) for t in (7,8,9)],[(16,1),(18,1),(20,1)])

    def test_16_repair_drone_uses_normal_damcon_tp(self):
        for t in range(2,10):
            x=next(r for r in self.one if r.tl==t and r.drone)
            self.assertEqual(_costs(self.m,x)['drone'],int(self.m.p('damage_control',t)['attemptTp']))

    def test_17_demand_states_are_ordered_stress_not_required_full_coverage(self):
        x=next(r for r in self.one if r.tl==9 and r.weapon=='E' and r.main_count==2 and r.shield and r.ecm and r.eccm and r.drone)
        d=demand_states(self.m,x)
        self.assertGreater(d['full'],d['core'])
        self.assertGreaterEqual(d['offense'],d['routine'])
        self.assertTrue(self.doc['interpretationPolicy']['noRequiredFullSimultaneousDemandCoverage'])

    def test_18_energy_overload_cost_is_distinct_from_standard_somewhere(self):
        self.assertTrue(any(int(self.m.p('energy_main',t)['overloadTp']) > int(self.m.p('energy_main',t)['standardTp']) for t in range(1,10)))

    def test_19_weapon_tp_identity_is_preserved(self):
        self.assertEqual(int(self.m.p('kinetic_main',1)['firingTp']),2)
        self.assertEqual(int(self.m.p('energy_main',1)['standardTp']),3)
        self.assertEqual(int(self.m.p('missile_delivery',1)['launchTp']),1)

    def test_20_one_factor_weapon_override_changes_only_relevant_family(self):
        k=next(r for r in self.one if r.tl==5 and r.weapon=='K')
        e=next(r for r in self.one if r.tl==5 and r.weapon=='E')
        self.assertIn('weapon_standard',_lever_overrides(self.m,k,'kinetic_weapon',1))
        self.assertEqual(_lever_overrides(self.m,e,'kinetic_weapon',1),{})

    def test_21_damage_control_sensitivity_includes_drone_when_present(self):
        x=next(r for r in self.one if r.tl==8 and r.drone)
        ov=_lever_overrides(self.m,x,'damage_control',1)
        self.assertIn('damage_control',ov);self.assertIn('drone',ov)

    def test_22_doctrine_set_is_complete(self):
        self.assertEqual(list(DOCTRINES),self.doc['doctrines'])
        self.assertEqual(set(PRIORITY),set(DOCTRINES))

    def test_23_allocator_honors_priority_under_scarcity(self):
        r=[Request('weapon',3),Request('sensor',2),Request('stl_overload',1)]
        a=_allocate(r,3,'OFFENSE')
        self.assertEqual(a['funded']['sensor'],1)
        self.assertEqual(a['funded']['weapon'],0)

    def test_24_allocator_uses_energy_style_fallback(self):
        r=[Request('sensor',1),Request('weapon',5,5,3)]
        a=_allocate(r,4,'OFFENSE')
        self.assertEqual(a['funded']['weapon'],1)
        self.assertEqual(a['fallback']['weapon'],1)

    def test_25_representatives_are_twelve_per_tl(self):
        self.assertEqual(len(self.reps),108)
        for t in range(1,10): self.assertEqual(sum(l.tl==t for _,l in self.reps),12)

    def test_26_representatives_cover_all_three_primary_weapon_families_each_tl(self):
        for t in range(1,10):
            self.assertTrue({'K','E','M'} <= {l.weapon for _,l in self.reps if l.tl==t})

    def test_27_combat_contexts_are_thirty_six_per_tl(self):
        for t in range(1,10): self.assertEqual(len(combat_contexts(ROOT,t)),36)

    def test_28_combat_contexts_include_mirrored_second_reactor_contests(self):
        c=combat_contexts(ROOT,9)
        groups={v.scenario_group for v in c}
        for g in ('K_1R_vs_K_2R','K_2R_vs_K_1R','E_1R_vs_E_2R','E_2R_vs_E_1R','M_1R_vs_M_2R','M_2R_vs_M_1R'):
            self.assertIn(g,groups)
        self.assertTrue(any(v.side_a.reactor_count==2 or v.side_b.reactor_count==2 for v in c))

    def test_29_combat_builds_are_space_legal(self):
        for t in range(1,10):
            for v in combat_contexts(ROOT,t):
                self.assertLessEqual(v.side_a.combat_space,v.side_a.capacity)
                self.assertLessEqual(v.side_b.combat_space,v.side_b.capacity)

    def test_30_pf4_aux_registry_materializes_all_ten_families(self):
        m=load_research_execution_baseline_pf4(ROOT);ids=_pf4_aux_registry(m)
        self.assertEqual({k for k,_ in ids},set(m.doc['pendingFinalizationAuxProfiles']))
        self.assertGreater(len(ids),40)

    def test_31_plan_scale_is_exact_and_no_auto_promotion(self):
        with tempfile.TemporaryDirectory() as td:
            p=plan(ROOT,STUDY,Path(td))
        self.assertEqual(p['combatContexts'],324)
        self.assertEqual(p['combatCells'],2268)
        self.assertEqual(p['combatTrials'],4536000)
        self.assertEqual(p['stochasticTurnSamples'],7776000)
        self.assertFalse(p['automaticPromotion']);self.assertFalse(p['tuningAllowed'])

    def test_32_interpretation_rejects_equality_and_scaffold_confirmation(self):
        p=self.doc['interpretationPolicy']
        self.assertTrue(p['noTargetWinRate'])
        self.assertTrue(p['noUniversalUtilizationTarget'])
        self.assertTrue(p['balanceMeansDistinctViableChoices'])
        self.assertTrue(p['currentReactorLadderIsScaffoldNotAnswer'])
        self.assertTrue(p['auxMagnitudeArchitectureRemainClosedUnlessIntegrationInvalidates'])

if __name__ == '__main__':
    unittest.main()
