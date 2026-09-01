from __future__ import annotations
import json, sys, unittest
from pathlib import Path
REPO=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(REPO/"tools/simulation"))
from starcluster_research.ecology import CandidateMatrix, EcologyBuild, _create_side, _attempt_hull_damage_control, _begin_turn_recharge
from starcluster_research.canonical_combat import CANONICAL_COMBAT_KERNEL_VERSION
from starcluster_research.same_tl_candidate_baseline_analysis import validate_study, build_plan

MATRIX='docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_7.json'
STUDY=REPO/'docs/archive/testing/pre-cp165-active/cp135_recharge_damcon_rebaseline_study_v0_1.json'

def build(tl:int)->EcologyBuild:
    m=CandidateMatrix(REPO,MATRIX); cap=m.capacity(tl)
    return EcologyBuild(f'tl{tl}-probe',tl,'probe','Kinetic',1,1,True,False,False,None,False,cap,0,cap,armor_profile='mainline')

class Cp135RechargeDamconTests(unittest.TestCase):
    def test_kernel_version(self): self.assertEqual('0.7',CANONICAL_COMBAT_KERNEL_VERSION)
    def test_study_shape(self):
        doc=json.loads(STUDY.read_text()); self.assertEqual([],validate_study(doc)); p=build_plan(REPO,STUDY,None)['summary']; self.assertEqual(196,p['logicalContexts']); self.assertEqual(392,p['generatedVariants']); self.assertEqual(136,p['tl6Variants'])
    def test_shields_cannot_full_reset_from_zero(self):
        m=CandidateMatrix(REPO,MATRIX)
        for tl in range(1,10):
            p=m.p('shield',tl); self.assertLess(int(p['baseRecharge'])+int(p['tacticalRechargePerTp'])*int(p['tacticalRechargeCapTp']),int(p['capacity']))
    def test_repair_kit_progression(self):
        m=CandidateMatrix(REPO,MATRIX); self.assertEqual([3,3,4,4,5,5,6,6,7],[int(m.p('damage_control',tl)['preparedRepairKits']) for tl in range(1,10)])
    def test_hull_attempt_spends_tp_and_kit_even_on_failure(self):
        m=CandidateMatrix(REPO,MATRIX); s=_create_side(m,build(3),-5); s.hull-=2; before=s.repair_kits_remaining
        spent=_attempt_hull_damage_control(m,s,1,100); self.assertEqual(1,spent); self.assertEqual(before-1,s.repair_kits_remaining); self.assertEqual(1,s.telemetry.damage_control_attempts); self.assertEqual(0,s.telemetry.damage_control_successes); self.assertEqual(1,s.telemetry.damage_control_kits_consumed)
    def test_success_queues_then_activates_at_refresh(self):
        m=CandidateMatrix(REPO,MATRIX); a=_create_side(m,build(7),-5); b=_create_side(m,build(7),5); a.hull-=5
        spent=_attempt_hull_damage_control(m,a,1,1); self.assertEqual(1,spent); self.assertEqual(2,a.pending_hull_repair); before=a.hull
        _begin_turn_recharge(m,a,b,0); self.assertEqual(before+2,a.hull); self.assertEqual(0,a.pending_hull_repair); self.assertEqual(2,a.telemetry.damage_control_hull_restored)
    def test_full_hull_does_not_consume_kit(self):
        m=CandidateMatrix(REPO,MATRIX); s=_create_side(m,build(9),-5); before=s.repair_kits_remaining; self.assertEqual(0,_attempt_hull_damage_control(m,s,10,1)); self.assertEqual(before,s.repair_kits_remaining)


if __name__=='__main__': unittest.main()
