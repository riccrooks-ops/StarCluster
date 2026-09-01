from __future__ import annotations

import hashlib
import sys
import unittest
from pathlib import Path

REPO=Path(__file__).resolve().parents[3]
SIM=REPO/'tools/simulation'
if str(SIM) not in sys.path: sys.path.insert(0,str(SIM))

from starcluster_research.canonical_mechanics import resolve_def_res_damage
from starcluster_research.combat_model_reconciliation import apply_combat_model_candidate
from starcluster_research.ecology import CandidateMatrix, EcologyBuild, _begin_turn_recharge, _create_side, _weapon
from starcluster_research.def_res_reconciliation_analysis import _fixture_rows, _smoke_rows, _swarmer_rows

MATRIX='docs/design/player_technology/technology_numerical_matrix_v0_9.json'

class Cp139DefResReconciliationTests(unittest.TestCase):
    def test_01_fixture_set_passes(self):
        rows=_fixture_rows(); self.assertEqual(8,len(rows)); self.assertTrue(all(r['status']=='PASS' for r in rows))
    def test_02_boundary_deflection(self):
        r=resolve_def_res_damage(shield=8,armor_integrity=6,hull=12,damage=4,shield_def_pp=20,armor_res_pp=20,defense_roll=20)
        self.assertTrue(r.deflected); self.assertEqual(8,r.final_shield)
    def test_03_spen_reduces_def(self):
        r=resolve_def_res_damage(shield=4,armor_integrity=6,hull=12,damage=6,spen=5,shield_def_pp=20,armor_res_pp=20,defense_roll=16)
        self.assertEqual(15,r.effective_def_pp); self.assertAlmostEqual(4.4,r.final_armor_integrity)
    def test_04_apen_reduces_res(self):
        r=resolve_def_res_damage(shield=0,armor_integrity=6,hull=12,damage=4,apen=5,armor_res_pp=20,defense_roll=100)
        self.assertEqual(15,r.effective_res_pp); self.assertAlmostEqual(2.6,r.final_armor_integrity)
    def test_05_candidate_overlay_does_not_write_source_matrix(self):
        p=REPO/MATRIX; before=hashlib.sha256(p.read_bytes()).hexdigest(); m=CandidateMatrix(REPO,MATRIX); apply_combat_model_candidate(m); after=hashlib.sha256(p.read_bytes()).hexdigest(); self.assertEqual(before,after)
    def test_06_candidate_weapon_ladders(self):
        m=CandidateMatrix(REPO,MATRIX); apply_combat_model_candidate(m)
        b=EcologyBuild('k',9,'x','Kinetic',1,1,True,False,False,None,False,m.capacity(9),0,0)
        self.assertEqual(8,_weapon(m,b)['damage']); self.assertEqual(14,_weapon(m,b)['apen'])
    def test_07_swarmer_is_two_pds_visible_subflights(self):
        rows=_swarmer_rows(); self.assertEqual([2,5,9],[r['tl'] for r in rows]); self.assertTrue(all(r['pds_visible_subflights']==2 and r['pds_penalty_pp']==0 for r in rows))
    def test_08_candidate_shield_collapse_lockout(self):
        m=CandidateMatrix(REPO,MATRIX); apply_combat_model_candidate(m)
        cap=m.capacity(5); b=EcologyBuild('s',5,'x','Energy',1,1,True,False,False,None,False,cap,0,0); side=_create_side(m,b,-5); target=_create_side(m,b,5); side.shield=0
        before=side.shield; _begin_turn_recharge(m,side,target,0); self.assertEqual(before,side.shield)
    def test_09_full_map_smoke_executes_all_82(self):
        rows=_smoke_rows(REPO,MATRIX); self.assertEqual(82,len(rows)); self.assertFalse(any(r['error'] for r in rows)); self.assertGreater(sum(r['def_res_packets_a']+r['def_res_packets_b'] for r in rows),0)

if __name__=='__main__': unittest.main()
