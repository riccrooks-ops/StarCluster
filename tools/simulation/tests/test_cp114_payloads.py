from __future__ import annotations
import json, unittest
from pathlib import Path

from starcluster_research.ecology import CandidateMatrix, EcologyVariant, generate_primary_builds, run_trial, _create_side, _begin_turn_recharge
from starcluster_research.payload_analysis import (
    PayloadCatalog, PayloadProfile, PayloadVariant, _apply_payload_hit, _effective_profile,
    _observe_resolution, _payload_for_launch, build_variants, run_payload_trial, validate_study,
)

REPO=Path(__file__).resolve().parents[3]
STUDY=REPO/'docs/archive/testing/pre-cp165-active/payload_characteristic_space_study_v0_1.json'

class CP114PayloadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=json.loads(STUDY.read_text())
        cls.matrix=CandidateMatrix(REPO)
        cls.catalog=PayloadCatalog(cls.doc)
        cls.builds={b.id:b for b in generate_primary_builds(cls.matrix)}

    def test_study_valid(self):
        self.assertEqual(validate_study(self.doc),[])

    def test_variant_shape_and_exact_fill(self):
        builds,variants=build_variants(REPO,self.doc)
        self.assertEqual(len(variants),3184)
        self.assertEqual(sum(v.scenario_group=='missile_payload_characteristic' for v in variants),2720)
        self.assertEqual(sum(v.scenario_group=='kinetic_ammunition_characteristic' for v in variants),464)
        self.assertTrue(all(b.used_space==b.capacity for b in builds))

    def test_baseline_gp_matches_ecology_trial(self):
        a=self.builds['tl5-missile-balanced']; b=self.builds['tl5-energy-defense-specialist']
        eid='cp114-baseline-parity'
        ev=EcologyVariant(eid,5,a,b,'SideAFirst')
        pv=PayloadVariant(eid,5,a,b,'SideAFirst','gp-current','gp-current')
        old=run_trial(self.matrix,ev,1234,0)
        new=run_payload_trial(self.matrix,self.catalog,pv,1234,0)
        self.assertEqual((old.winner,old.turns,old.hull_a,old.hull_b,old.armor_a,old.armor_b,old.shield_a,old.shield_b),
                         (new.winner,new.turns,new.hull_a,new.hull_b,new.armor_a,new.armor_b,new.shield_a,new.shield_b))
        for name in ('direct_shots','direct_hits','missile_launches','missile_hits','pds_attempts','pds_intercepts','hull_damage','shield_absorbed'):
            self.assertEqual(getattr(old.side_a,name),getattr(new.side_a,name),name)
            self.assertEqual(getattr(old.side_b,name),getattr(new.side_b,name),name)

    def test_shield_bonus_has_no_structural_spill(self):
        target=_create_side(self.matrix,self.builds['tl9-energy-defense-specialist'],5)
        target.shield=5
        res=_apply_payload_hit(target,{'damage':0,'spen':0,'apen':0,'packets':1,'shield_bonus_damage':3,'shield_armor_reduction':0,'recharge_suppression':0},1,'missile')
        self.assertEqual(res['shield_bonus_damage'],3)
        self.assertEqual(target.shield,2)
        self.assertEqual(res['hull'],0)

    def test_recharge_suppression_consumes_next_recharge(self):
        side=_create_side(self.matrix,self.builds['tl9-energy-defense-specialist'],5)
        target=_create_side(self.matrix,self.builds['tl9-missile-balanced'],-5)
        side.shield=5; side.recharge_suppression_pending=2
        before=side.shield
        _begin_turn_recharge(self.matrix,side,target,0)
        self.assertEqual(side.recharge_suppression_pending,0)
        self.assertGreaterEqual(side.telemetry.shield_recharge_suppressed,1)
        self.assertGreaterEqual(side.shield,before)

    def test_adaptive_switch_uses_observation_only(self):
        side=_create_side(self.matrix,self.builds['tl9-missile-balanced'],-5)
        base={'family':'Missile','damage':5,'spen':1,'apen':2}
        p=_payload_for_launch(side,base,self.catalog,'missile-adaptive-a3')
        self.assertEqual(p.id,'gp-current')
        side.observed_shield_absorption=True; side.observed_no_penetration_streak=2
        p=_payload_for_launch(side,base,self.catalog,'missile-adaptive-a3')
        self.assertEqual(p.id,'missile-shield-a3')
        self.assertEqual(side.telemetry.payload_switches,1)

    def test_firm_assessment_tracks_effect_not_hidden_value(self):
        side=_create_side(self.matrix,self.builds['tl7-missile-balanced'],-5)
        _observe_resolution(side,{'shield_armor_prevented':1,'shield_absorbed':3,'shield_bonus_damage':0,'armor_prevented':0,'armor_integrity':0,'armor_protection':0,'hull':0},True)
        self.assertTrue(side.observed_shield_absorption)
        self.assertEqual(side.observed_no_penetration_streak,1)
        self.assertFalse(side.observed_armor_contact)

    def test_armor_contact_without_damage_still_allows_no_penetration_learning(self):
        side=_create_side(self.matrix,self.builds['tl9-missile-balanced'],-5)
        _observe_resolution(side,{'shield_armor_prevented':1,'shield_absorbed':3,'shield_bonus_damage':0,'armor_prevented':1,'armor_integrity':0,'armor_protection':0,'hull':0},True)
        self.assertTrue(side.observed_armor_contact)
        self.assertEqual(side.observed_no_penetration_streak,1)

    def test_adaptive_can_return_to_gp_after_observed_no_shield_effect(self):
        side=_create_side(self.matrix,self.builds['tl9-missile-balanced'],-5)
        base={'family':'Missile','damage':5,'spen':1,'apen':2}
        side.observed_shield_absorption=True; side.observed_no_penetration_streak=2
        self.assertEqual(_payload_for_launch(side,base,self.catalog,'missile-adaptive-a3').id,'missile-shield-a3')
        _observe_resolution(side,{'shield_armor_prevented':0,'shield_absorbed':0,'shield_bonus_damage':0,'armor_prevented':3,'armor_integrity':0,'armor_protection':0,'hull':0},True)
        self.assertTrue(side.observed_no_shield_effect_latest)
        self.assertEqual(_payload_for_launch(side,base,self.catalog,'missile-adaptive-a3').id,'gp-current')

    def test_dense_penetrator_trades_damage_for_apen(self):
        base={'family':'Kinetic','damage':5,'spen':1,'apen':1,'accuracy':20}
        p=_effective_profile(base,self.catalog.get('kinetic-dense-a'))
        self.assertLess(p['damage'],base['damage']); self.assertGreater(p['apen'],base['apen'])

    def test_saturation_is_multiple_smaller_packets(self):
        base={'family':'Kinetic','damage':5,'spen':2,'apen':1,'accuracy':25}
        p=_effective_profile(base,self.catalog.get('kinetic-saturation-a'))
        self.assertEqual(p['packets'],2); self.assertLess(p['damage'],base['damage'])

    def test_shaped_warhead_not_strict_gp_dominance(self):
        base={'family':'Missile','damage':5,'spen':1,'apen':2}
        p=_effective_profile(base,self.catalog.get('missile-shaped-a'))
        self.assertLess(p['damage'],base['damage']); self.assertGreater(p['apen'],base['apen']); self.assertLess(p['spen'],base['spen'])

    def test_anti_shield_candidates_pay_structural_cost(self):
        base={'family':'Missile','damage':5,'spen':1,'apen':2}
        for pid in ('missile-shield-a3','missile-shield-b','missile-shield-c2'):
            p=_effective_profile(base,self.catalog.get(pid))
            self.assertTrue(p['damage']<base['damage'] or p['apen']<base['apen'])

if __name__=='__main__': unittest.main()
