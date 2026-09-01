import hashlib
import tempfile
import unittest
from pathlib import Path

from starcluster_research.combat_surface_deep_reconciliation import build_deep_resource_matrix
from starcluster_research.kinetic_full_characteristic_sweep import (
    EXPECTED_CANDIDATES_PER_TL, EXPECTED_CONTEXTS, FACTORS, _apply_candidate,
    _design_vectors, _space_envelope, candidate_ledger, kinetic_contexts,
    run_batch, run_plan, validate_population, validate_study, _worker_init, _trial_aggregate,
)
from starcluster_research.stage_a_integration_analysis import _resource_rows
from starcluster_research.study import load_json


class Cp149KineticFullCharacteristicSweepTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo=Path(__file__).resolve().parents[3]
        cls.study_path=cls.repo/'docs/archive/testing/pre-cp165-active/cp149_kinetic_full_characteristic_multivariate_sweep_v0_1.json'
        cls.doc=load_json(cls.study_path)

    def test_01_study_and_population_validate(self):
        self.assertEqual([],validate_study(self.doc)); self.assertEqual([],validate_population(self.repo,self.doc))

    def test_02_design_is_163_points_with_expected_classes(self):
        rows=_design_vectors(); self.assertEqual(EXPECTED_CANDIDATES_PER_TL,len(rows))
        counts={k:sum(r['design_class']==k for r in rows) for k in ('baseline','axial','pairwise','fractional_factorial')}
        self.assertEqual({'baseline':1,'axial':14,'pairwise':84,'fractional_factorial':64},counts)

    def test_03_context_population_is_complete_k_vs_non_k(self):
        rows=kinetic_contexts(self.repo,self.doc); self.assertEqual(EXPECTED_CONTEXTS,len(rows))
        self.assertTrue(all((r['side_a_weapon']=='K') ^ (r['side_b_weapon']=='K') for r in rows))
        self.assertEqual(200,sum(int(r['tl'])==1 for r in rows)); self.assertTrue(all(sum(int(r['tl'])==tl for r in rows)==300 for tl in range(2,10)))

    def test_04_candidate_ledger_covers_all_tls_and_is_unique(self):
        rows=candidate_ledger(self.repo,self.doc); self.assertEqual(9*EXPECTED_CANDIDATES_PER_TL,len(rows)); self.assertEqual(len(rows),len({r['candidate_id'] for r in rows}))
        self.assertEqual(set(range(1,10)),{int(r['tl']) for r in rows})

    def test_05_spen_is_frozen_zero_for_every_candidate(self):
        self.assertEqual({0},{int(r['candidate_spen']) for r in candidate_ledger(self.repo,self.doc)})

    def test_06_baseline_candidate_matches_executable_cp148_central_profile(self):
        er,tr=_resource_rows(self.repo,self.doc); m=build_deep_resource_matrix(self.repo,self.doc['matrix'],'R1_CENTRAL_NO_MAJOR',er,tr)
        ledger=candidate_ledger(self.repo,self.doc)
        for tl in range(1,10):
            r=next(x for x in ledger if int(x['tl'])==tl and x['design_class']=='baseline'); k=m.p('kinetic_main',tl)
            self.assertEqual(int(k['accuracyPp']),int(r['candidate_accuracyPp'])); self.assertEqual(int(k['damage']),int(r['candidate_damage'])); self.assertEqual(int(k['apen']),int(r['candidate_apen']))
            self.assertEqual(int(k['standardRange']),int(r['candidate_standardRange'])); self.assertEqual(int(k['maxRange']),int(r['candidate_maxRange'])); self.assertEqual(int(k['ammo']),int(r['candidate_ammo']))

    def test_07_resource_relative_tp_delta_preserves_ensemble_difference(self):
        er,tr=_resource_rows(self.repo,self.doc); r0=build_deep_resource_matrix(self.repo,self.doc['matrix'],'R0_CP138_HISTORICAL',er,tr); r1=build_deep_resource_matrix(self.repo,self.doc['matrix'],'R1_CENTRAL_NO_MAJOR',er,tr)
        c=next(x for x in candidate_ledger(self.repo,self.doc) if int(x['tl'])==1 and x['design_class']=='axial' and int(x['code_firing_tp_delta'])==1)
        self.assertEqual(2,_apply_candidate(r0,1,c).p('kinetic_main',1)['firingTp']); self.assertEqual(3,_apply_candidate(r1,1,c).p('kinetic_main',1)['firingTp'])

    def test_08_range_parameterization_never_inverts_standard_and_max(self):
        er,tr=_resource_rows(self.repo,self.doc); m=build_deep_resource_matrix(self.repo,self.doc['matrix'],'R1_CENTRAL_NO_MAJOR',er,tr)
        for c in candidate_ledger(self.repo,self.doc):
            if int(c['tl']) not in (1,5,9): continue
            k=_apply_candidate(m,int(c['tl']),c).p('kinetic_main',int(c['tl']))
            self.assertGreaterEqual(int(k['standardRange']),1); self.assertGreaterEqual(int(k['maxRange']),int(k['standardRange']))

    def test_09_ammo_axis_includes_25_100_200(self):
        self.assertEqual({25,100,200},{int(r['ammo_level']) for r in candidate_ledger(self.repo,self.doc)})

    def test_10_identity_stress_is_flagged_not_removed(self):
        rows=candidate_ledger(self.repo,self.doc); stress=[r for r in rows if int(r['identity_stress'])]
        self.assertTrue(stress); self.assertTrue(any('ACC_GT_E' in r['identity_stress_flags'] for r in stress))
        self.assertTrue(all(int(r['promotion_allowed'])==0 for r in rows))

    def test_11_space_lane_is_full_and_baseline_is_legal(self):
        rows=_space_envelope(self.repo,self.doc); self.assertEqual(2250,len(rows)); baseline=[r for r in rows if int(r['space_delta'])==0]
        self.assertTrue(baseline); self.assertTrue(all(int(r['legal'])==1 for r in baseline))

    def test_12_space_lane_exposes_early_power_crisis_infeasibility(self):
        rows=_space_envelope(self.repo,self.doc)
        self.assertTrue(any(int(r['tl'])<=4 and r['scenario_stratum']=='POWER_CRISIS' and int(r['space_delta'])>0 and int(r['legal'])==0 for r in rows))

    def test_13_candidate_application_does_not_mutate_base_matrix(self):
        er,tr=_resource_rows(self.repo,self.doc); m=build_deep_resource_matrix(self.repo,self.doc['matrix'],'R1_CENTRAL_NO_MAJOR',er,tr); before=dict(m.p('kinetic_main',4))
        c=next(x for x in candidate_ledger(self.repo,self.doc) if int(x['tl'])==4 and x['design_class']=='fractional_factorial'); _apply_candidate(m,4,c)
        self.assertEqual(before,m.p('kinetic_main',4))

    def test_14_plan_has_declared_42_38m_substantive_combats(self):
        with tempfile.TemporaryDirectory() as td:
            r=run_plan(self.repo,self.study_path,Path(td)); self.assertTrue(r['passed']); self.assertEqual(42380000,int(r['substantiveCombatTrials']))

    def _one_live_result(self):
        c=next(x for x in candidate_ledger(self.repo,self.doc) if int(x['tl'])==1 and x['design_class']=='baseline')
        src=next(x for x in kinetic_contexts(self.repo,self.doc) if int(x['tl'])==1)
        _worker_init(str(self.repo),self.doc,[c])
        return _trial_aggregate((0,src,c,int(self.doc['masterSeed']),1))

    def test_15_tiny_live_context_executes_utility_combat_without_errors(self):
        r=self._one_live_result(); self.assertEqual(0,int(r['error_trials'])); self.assertEqual(1,int(r['trials']))

    def test_16_source_numerical_matrix_remains_unchanged_by_plan_and_probe(self):
        p=self.repo/self.doc['matrix']; before=hashlib.sha256(p.read_bytes()).hexdigest(); self._one_live_result()
        self.assertEqual(before,hashlib.sha256(p.read_bytes()).hexdigest())
        wrapper=(self.repo/'tools/checkpoints/checkpoint-149/apply_checkpoint_149.ps1').read_text(encoding='utf-8-sig')
        self.assertIn('function Invoke-PythonWithSimulationPath',wrapper)
        self.assertIn('function Invoke-PythonFocusedPattern',wrapper)
        self.assertIn("Invoke-PythonFocusedPattern $pattern",wrapper)

if __name__=='__main__': unittest.main()
