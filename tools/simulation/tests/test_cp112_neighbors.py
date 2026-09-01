from __future__ import annotations
import unittest
from pathlib import Path
from starcluster_research.ecology import CandidateMatrix, EcologyVariant, generate_primary_builds, run_trial
from starcluster_research.neighbor_analysis import build_variants, energy_ablation_builds, missile_defense_ablation_builds, validate_study
from starcluster_research.study import load_json

REPO=Path(__file__).resolve().parents[3]
STUDY=REPO/'docs/archive/testing/pre-cp165-active/build_neighbor_ablation_study_v0_1.json'

class Checkpoint112NeighborTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix=CandidateMatrix(REPO); cls.doc=load_json(STUDY)
    def test_study_contract(self):
        self.assertEqual([],validate_study(self.doc)); self.assertFalse(self.doc['automaticPromotion']); self.assertFalse(self.doc['internalDamageCriticalsSimulated'])
    def test_variant_shape(self):
        builds,variants=build_variants(REPO,self.doc)
        counts={}
        for v in variants: counts[v.scenario_group]=counts.get(v.scenario_group,0)+1
        self.assertEqual({'energy_defense_ablation':1056,'movement_order_geometry':24,'missile_attrition_ablation':120},counts)
        self.assertEqual(1200,len(variants))
        self.assertTrue(all(b.used_space==b.capacity for b in builds))
    def test_energy_ablation_is_exact_fill_and_component_local(self):
        rows=energy_ablation_builds(self.matrix,5); self.assertEqual(8,len(rows)); self.assertTrue(all(b.used_space==b.capacity for b in rows))
        full=next(b for b in rows if b.archetype.endswith('-full')); noh=next(b for b in rows if b.archetype.endswith('-no-hardener'))
        self.assertTrue(full.shield_hardener); self.assertFalse(noh.shield_hardener); self.assertEqual(full.weapon_family,noh.weapon_family)
    def test_missile_defense_ablation_exact_fill(self):
        rows=missile_defense_ablation_builds(self.matrix,9); self.assertEqual(5,len(rows)); self.assertTrue(all(b.used_space==b.capacity for b in rows))
    def test_start_range_and_horizon_controls_reach_trial(self):
        by={b.id:b for b in generate_primary_builds(self.matrix)}
        v=EcologyVariant('cp112-range4',7,by['tl7-kinetic-dual-main'],by['tl7-missile-dual-main'],'SideAFirst',start_q_a=-2,start_q_b=2,max_turns=20,scenario_group='test',perturbation='range4')
        r=run_trial(self.matrix,v,112,0); self.assertEqual('',r.error); self.assertLessEqual(r.turns,20); self.assertLessEqual(r.min_range,4)

if __name__=='__main__': unittest.main()
