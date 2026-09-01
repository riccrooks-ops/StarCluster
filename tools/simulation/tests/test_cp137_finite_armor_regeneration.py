from __future__ import annotations
import json, sys, unittest
from pathlib import Path
REPO=Path(__file__).resolve().parents[3]
SIM=REPO/'tools/simulation'
if str(SIM) not in sys.path: sys.path.insert(0,str(SIM))
from starcluster_research.ecology import CandidateMatrix, EcologyBuild, _armor_profile, _apply_armor_regeneration, _create_side
from starcluster_research.canonical_combat import CANONICAL_COMBAT_KERNEL_VERSION
from starcluster_research.same_tl_candidate_baseline_analysis import validate_study, build_plan

MATRIX='docs/design/player_technology/technology_numerical_matrix_v0_9.json'
STUDY=REPO/'docs/archive/testing/pre-cp165-active/cp137_finite_armor_regeneration_study_v0_1.json'

def build(tl:int, armor='mainline')->EcologyBuild:
    m=CandidateMatrix(REPO,MATRIX); cap=m.capacity(tl)
    return EcologyBuild(f'tl{tl}-{armor}',tl,'probe','Kinetic',1,1,True,False,False,None,False,cap,0,cap,armor_profile=armor)

class Cp137FiniteArmorRegenerationTests(unittest.TestCase):
    def test_kernel_version(self): self.assertEqual('0.7',CANONICAL_COMBAT_KERNEL_VERSION)
    def test_study_shape(self):
        doc=json.loads(STUDY.read_text()); self.assertEqual([],validate_study(doc)); p=build_plan(REPO,STUDY,None)['summary']; self.assertEqual((196,392,136),(p['logicalContexts'],p['generatedVariants'],p['tl6Variants']))
    def test_reserve_progression_and_per_turn_caps(self):
        m=CandidateMatrix(REPO,MATRIX)
        self.assertEqual([3,4,5,6],[int(m.p('armor',tl)['combatRegenerationReserveAi']) for tl in (6,7,8,9)])
        self.assertEqual([1,1,1,2],[int(m.p('armor',tl)['tacticalRegenerationCapTp']) for tl in (6,7,8,9)])
        self.assertEqual([1,1,1,1],[int(m.p('armor',tl)['tacticalRegenerationPerTp']) for tl in (6,7,8,9)])
    def test_tl6_reserve_exhausts_after_three_ai(self):
        m=CandidateMatrix(REPO,MATRIX); side=_create_side(m,build(6),-5); side.armor_integrity=4
        self.assertEqual(3,side.armor_regen_reserve_remaining)
        for _ in range(3): self.assertEqual(1,_apply_armor_regeneration(m,side,10))
        self.assertEqual(7,side.armor_integrity); self.assertEqual(0,side.armor_regen_reserve_remaining)
        self.assertEqual(0,_apply_armor_regeneration(m,side,10)); self.assertEqual(3,side.telemetry.armor_regen_reserve_spent)
        self.assertEqual(1,side.telemetry.armor_regen_reserve_exhaustions); self.assertEqual(1,side.telemetry.armor_regen_denied_exhausted)
    def test_tl9_can_restore_two_per_turn_but_only_six_total(self):
        m=CandidateMatrix(REPO,MATRIX); side=_create_side(m,build(9),-5); side.armor_integrity=2
        self.assertEqual(2,_apply_armor_regeneration(m,side,10)); self.assertEqual((4,4),(side.armor_integrity,side.armor_regen_reserve_remaining))
        self.assertEqual(2,_apply_armor_regeneration(m,side,10)); self.assertEqual(2,_apply_armor_regeneration(m,side,10))
        self.assertEqual(8,side.armor_integrity); self.assertEqual(0,side.armor_regen_reserve_remaining); self.assertEqual(6,side.telemetry.armor_regen_restored)
    def test_crystalline_has_no_regeneration_or_reserve(self):
        m=CandidateMatrix(REPO,MATRIX); p=_armor_profile(m,build(6,'A_b1'))
        self.assertEqual((2,11,0,0,0),(int(p['ap']),int(p['ai']),int(p['tacticalRegenerationPerTp']),int(p['tacticalRegenerationCapTp']),int(p['combatRegenerationReserveAi'])))
    def test_tl1_to_tl5_remain_nonregenerative(self):
        m=CandidateMatrix(REPO,MATRIX)
        for tl in range(1,6):
            p=m.p('armor',tl); self.assertEqual((0,0,0),(int(p['tacticalRegenerationPerTp']),int(p['tacticalRegenerationCapTp']),int(p['combatRegenerationReserveAi'])))
    def test_out_of_combat_recovery_is_not_part_of_study(self):
        doc=json.loads(STUDY.read_text()); self.assertFalse(doc['armorRegenerationDoctrine']['outOfCombatRecoverySimulated'])
        rule=CandidateMatrix(REPO,MATRIX).doc['armorRegenerationCandidateRule']; self.assertIn('deferred',rule['outOfCombatRecovery'].lower())

if __name__=='__main__': unittest.main()
