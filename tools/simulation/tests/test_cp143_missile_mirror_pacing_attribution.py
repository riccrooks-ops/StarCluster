from __future__ import annotations

import hashlib
import json
import sys
import unittest
from dataclasses import asdict, replace
from pathlib import Path

REPO=Path(__file__).resolve().parents[3]
SIM=REPO/'tools/simulation'
if str(SIM) not in sys.path: sys.path.insert(0,str(SIM))

from starcluster_research.canonical_combat import run_trial_full_map
from starcluster_research.combat_surface_deep_reconciliation import build_deep_resource_matrix
from starcluster_research.missile_mirror_pacing_attribution import (
    EXPECTED_MISSILE_MIRROR_SCENARIOS, HARD_TURN_SENTINEL, _missile_rows,
    _result_row, validate_study,
)
from starcluster_research.stage_a_integration_analysis import _resource_rows, bind_scenario
from starcluster_research.study import load_json

STUDY=REPO/'docs/archive/testing/pre-cp165-active/cp143_missile_mirror_pacing_attribution_study_v0_1.json'
MATRIX='docs/design/player_technology/technology_numerical_matrix_v0_9.json'

class Cp143MissileMirrorPacingAttributionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=load_json(STUDY); cls.rows=_missile_rows(REPO,cls.doc); er,tr=_resource_rows(REPO,cls.doc)
        cls.mats={eid:build_deep_resource_matrix(REPO,MATRIX,eid,er,tr) for eid in sorted({r['ensemble_id'] for r in er})}

    def _row(self,tl,a,b,stratum,resource='R1_CENTRAL_NO_MAJOR'):
        return next(r for r in self.rows if int(r['tl'])==tl and r['side_a_weapon']==a and r['side_b_weapon']==b and r['scenario_stratum']==stratum and r['resource_ensemble_id']==resource)

    def _run(self,row,events=True):
        m=self.mats[row['resource_ensemble_id']]; b=bind_scenario(m,row); ev=[]; turns=[]
        ctx={'scenario_id':row['scenario_id'],'resource_ensemble_id':row['resource_ensemble_id'],'weapon_a':row['side_a_weapon'],'weapon_b':row['side_b_weapon']}
        r=run_trial_full_map(m,replace(b.variant,max_turns=60),int(self.doc['masterSeed']),0,event_sink=(ev if events else None),turn_telemetry_sink=turns,telemetry_context=ctx)
        return r,ev,turns

    def test_01_study_is_bounded_and_forbids_tuning(self):
        self.assertEqual([],validate_study(self.doc)); self.assertEqual('missile-mirror-attribution-only',self.doc['scope'])
        self.assertFalse(self.doc['tuningAllowed']); self.assertFalse(self.doc['automaticPromotion']); self.assertEqual(0,self.doc['substantiveCombatTrials'])

    def test_02_exact_1980_cp142_missile_mirror_scenarios_are_selected(self):
        self.assertEqual(EXPECTED_MISSILE_MIRROR_SCENARIOS,len(self.rows)); self.assertEqual(len(self.rows),len({r['scenario_id'] for r in self.rows}))
        self.assertEqual(10,len({r['scenario_stratum'] for r in self.rows})); self.assertEqual(6,len({r['resource_ensemble_id'] for r in self.rows}))
        self.assertEqual({'M_GP','M_SWARMER'},{r['side_a_weapon'] for r in self.rows if int(r['tl'])>=2})

    def test_03_event_instrumentation_is_result_and_turn_telemetry_neutral(self):
        row=self._row(5,'M_SWARMER','M_SWARMER','POWER_CRISIS')
        off,_,off_turns=self._run(row,events=False); on,events,on_turns=self._run(row,events=True)
        self.assertEqual(asdict(off),asdict(on)); self.assertEqual(off_turns,on_turns); self.assertTrue(events)

    def test_04_launch_decision_is_recorded_for_both_missile_sides_every_turn(self):
        row=self._row(3,'M_GP','M_SWARMER','BALANCED_CORE_NO_PDS'); result,events,_=self._run(row)
        decisions=[e for e in events if e.get('event')=='missile_launch_decision']
        self.assertEqual(2*result.turns,len(decisions)); self.assertEqual({'A','B'},{e['side'] for e in decisions})
        self.assertTrue({e['decision'] for e in decisions} <= {'LAUNCHED','NO_FIRM_TRACK','OUT_OF_RANGE','NO_WEAPON_PLAN','AMMO_EXHAUSTED','READY'})

    def test_05_launch_events_match_canonical_magazine_launch_telemetry(self):
        row=self._row(4,'M_GP','M_SWARMER','KINETIC_PDS_PRESSURE'); result,events,_=self._run(row)
        la=sum(e.get('event')=='missile_launch' and e.get('side')=='A' for e in events); lb=sum(e.get('event')=='missile_launch' and e.get('side')=='B' for e in events)
        self.assertEqual(result.side_a.missile_launches,la); self.assertEqual(result.side_b.missile_launches,lb)

    def test_06_terminal_events_match_target_side_terminal_and_pds_telemetry(self):
        row=self._row(6,'M_SWARMER','M_GP','AMM_PDS_PRESSURE'); result,events,_=self._run(row)
        a_out=[e for e in events if e.get('event')=='missile_terminal' and e.get('owner')=='A']; b_out=[e for e in events if e.get('event')=='missile_terminal' and e.get('owner')=='B']
        self.assertEqual(result.side_b.missile_terminal_arrivals,len(a_out)); self.assertEqual(result.side_a.missile_terminal_arrivals,len(b_out))
        self.assertEqual(result.side_b.pds_attempts,sum(int(e['pds_attempts']) for e in a_out)); self.assertEqual(result.side_a.pds_attempts,sum(int(e['pds_attempts']) for e in b_out))
        self.assertEqual(result.side_b.pds_intercepts,sum(int(e['pds_intercepted']) for e in a_out)); self.assertEqual(result.side_a.pds_intercepts,sum(int(e['pds_intercepted']) for e in b_out))

    def test_07_guidance_events_match_target_side_guidance_telemetry(self):
        row=self._row(7,'M_GP','M_GP','BALANCED_CORE_NO_PDS'); result,events,_=self._run(row)
        a=[e for e in events if e.get('event')=='missile_terminal' and e.get('owner')=='A']; b=[e for e in events if e.get('event')=='missile_terminal' and e.get('owner')=='B']
        self.assertEqual(result.side_b.missile_guidance_attempts,sum(int(e['guidance_attempted']) for e in a)); self.assertEqual(result.side_a.missile_guidance_attempts,sum(int(e['guidance_attempted']) for e in b))
        self.assertEqual(result.side_b.missile_hits,sum(int(e['guidance_success']) for e in a)); self.assertEqual(result.side_a.missile_hits,sum(int(e['guidance_success']) for e in b))

    def test_08_swarmer_launch_event_retains_two_pds_visible_subflights(self):
        row=self._row(5,'M_SWARMER','M_SWARMER','BALANCED_CORE_NO_PDS'); _,events,_=self._run(row)
        launches=[e for e in events if e.get('event')=='missile_launch']
        self.assertTrue(launches); self.assertEqual({2},{int(e['subflights']) for e in launches})

    def test_09_attribution_row_exposes_requested_pacing_axes_without_tuning(self):
        row=self._row(5,'M_GP','M_SWARMER','POWER_CRISIS'); result,events,turns=self._run(row)
        idx=self.rows.index(row); out=_result_row(idx,row,result,events,turns)
        for k in ('mean_terminal_transit_turns_combined','mean_launch_gap_turns_combined','mean_terminal_gap_turns_combined','pds_intercept_fraction_of_terminals','guidance_success_fraction','recovery_fraction_of_missile_raw_damage','dominant_pacing_signal'):
            self.assertIn(k,out)

    def test_10_source_matrix_is_never_written(self):
        p=REPO/MATRIX; before=hashlib.sha256(p.read_bytes()).hexdigest(); self._run(self._row(8,'M_SWARMER','M_GP','EW_CONTEST')); after=hashlib.sha256(p.read_bytes()).hexdigest(); self.assertEqual(before,after)

    def test_11_cp142_reconciled_shield_and_pds_values_remain_unchanged(self):
        m=self.mats['R1_CENTRAL_NO_MAJOR']; self.assertEqual((16,0,1,2),(m.p('shield',9)['capacity'],m.p('shield',9)['baseRecharge'],m.p('shield',9)['tacticalRechargePerTp'],m.p('shield',9)['tacticalRechargeCapTp']))
        # Effective PDS recomposes from translated base + contemporary Computer.
        for key in ('kinetic_pds','energy_pds','amm_pds'):
            eff=min(95,int(m.p(key,5)['baseChancePp'])+int(m.p('computer',5)['targetingPp'])); self.assertGreater(eff,0)

    def test_12_duplicate_resource_level_is_preserved_only_for_paired_attribution(self):
        self.assertIn('R1/R5 executable equivalence',self.doc['resourceTreatment']); self.assertIn('five distinct executable resource environments',self.doc['nextStage'])

if __name__=='__main__': unittest.main()
