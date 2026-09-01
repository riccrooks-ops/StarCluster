from __future__ import annotations

import csv
import hashlib
import json
import tempfile
import unittest
import sys
from pathlib import Path

REPO=Path(__file__).resolve().parents[3]
SIM=REPO / "tools/simulation"
if str(SIM) not in sys.path:
    sys.path.insert(0,str(SIM))

from starcluster_research.combat_model_reconciliation import apply_combat_model_candidate
from starcluster_research.combat_surface_deep_reconciliation import (
    ARMOR_AI, ARMOR_REGEN_CAP_TP, ARMOR_REGEN_RESERVE, HULL_POINTS,
    PDS_EFFECTIVE, SHIELD_BASE_RECHARGE, SHIELD_CAPACITY,
    SHIELD_TACTICAL_CAP_TP, SHIELD_TACTICAL_PER_TP,
    apply_deep_combat_surface_reconciliation, build_deep_resource_matrix,
)
from starcluster_research.combat_surface_reconciliation_analysis import write_reconciliation_evidence
from starcluster_research.ecology import CandidateMatrix
from starcluster_research.stage_a_integration_analysis import _read_csv, _resource_rows, bind_scenario
from starcluster_research.study import load_json

MATRIX='docs/design/player_technology/technology_numerical_matrix_v0_9.json'
STUDY='docs/archive/testing/pre-cp165-active/cp142_combat_surface_deep_reconciliation_study_v0_1.json'

class Cp142CombatSurfaceReconciliationTests(unittest.TestCase):
    def _raw(self): return CandidateMatrix(REPO,MATRIX)
    def _deep(self):
        m=self._raw(); apply_deep_combat_surface_reconciliation(m); return m

    def test_01_source_matrix_never_modified(self):
        p=REPO/MATRIX; before=hashlib.sha256(p.read_bytes()).hexdigest(); self._deep(); after=hashlib.sha256(p.read_bytes()).hexdigest(); self.assertEqual(before,after)

    def test_02_shield_package_matches_latest_full_combat_reference(self):
        m=self._deep()
        for tl in range(1,10):
            r=m.p('shield',tl); i=tl-1
            self.assertEqual((r['capacity'],r['baseRecharge'],r['tacticalRechargePerTp'],r['tacticalRechargeCapTp']),
                             (SHIELD_CAPACITY[i],SHIELD_BASE_RECHARGE[i],SHIELD_TACTICAL_PER_TP[i],SHIELD_TACTICAL_CAP_TP[i]))

    def test_03_armor_and_hull_match_latest_full_combat_reference(self):
        m=self._deep()
        for tl in range(1,10):
            i=tl-1; a=m.p('armor',tl)
            self.assertEqual(m.p('hull',tl)['hullPoints'],HULL_POINTS[i])
            self.assertEqual(a['ai'],ARMOR_AI[i]); self.assertEqual(a['tacticalRegenerationCapTp'],ARMOR_REGEN_CAP_TP[i]); self.assertEqual(a['combatRegenerationReserveAi'],ARMOR_REGEN_RESERVE[i])

    def test_04_hull_installation_capacity_and_major_resource_fields_are_not_rewritten(self):
        raw=self._raw(); deep=self._deep()
        for tl in range(1,10):
            self.assertEqual(raw.p('hull',tl)['capacity'],deep.p('hull',tl)['capacity'])
            self.assertEqual(raw.p('shield',tl)['space'],deep.p('shield',tl)['space'])
            self.assertEqual(raw.p('armor',tl)['space'],deep.p('armor',tl)['space'])

    def test_05_damage_control_computer_ammo_and_missile_flights_are_exact_continuities(self):
        raw=self._raw(); deep=self._deep()
        for tl in range(1,10):
            for f in ('preparedRepairKits','hullRepairChancePp','hullRestoredPerSuccessfulKit','capacity','attemptTp'):
                self.assertEqual(raw.p('damage_control',tl).get(f),deep.p('damage_control',tl).get(f))
            self.assertEqual(raw.p('computer',tl)['targetingPp'],deep.p('computer',tl)['targetingPp'])
            self.assertEqual(deep.p('kinetic_main',tl)['ammo'],100); self.assertEqual(deep.p('missile_delivery',tl)['flights'],25)

    def test_06_pds_lab_effective_chance_is_not_double_counted_with_computer(self):
        m=self._deep()
        keys={'Kinetic':'kinetic_pds','Energy':'energy_pds','AMM':'amm_pds'}
        for fam,key in keys.items():
            for tl in range(1,10):
                effective=min(95,int(m.p(key,tl)['baseChancePp'])+int(m.p('computer',tl)['targetingPp']))
                self.assertEqual(effective,PDS_EFFECTIVE[fam]['chance'][tl-1],(fam,tl,effective))

    def test_07_pds_reaction_and_ammo_match_latest_candidate_but_readiness_space_remain_cp138(self):
        raw=self._raw(); m=self._deep(); keys={'Kinetic':'kinetic_pds','Energy':'energy_pds','AMM':'amm_pds'}
        for fam,key in keys.items():
            for tl in range(1,10):
                i=tl-1; self.assertEqual(m.p(key,tl)['reactionCapacity'],PDS_EFFECTIVE[fam]['rc'][i]); self.assertEqual(m.p(key,tl)['ammo'],PDS_EFFECTIVE[fam]['ammo'][i])
                self.assertEqual(m.p(key,tl)['space'],raw.p(key,tl)['space']); self.assertEqual(m.p(key,tl)['readinessTp'],raw.p(key,tl)['readinessTp'])

    def test_08_cp141_candidate_remains_reproducible_as_historical_control(self):
        raw=self._raw(); old=self._raw(); apply_combat_model_candidate(old)
        # Deep reconciliation must not mutate the old overlay function or source matrix.
        self.assertEqual(old.p('shield',9)['baseRecharge'],raw.p('shield',9)['baseRecharge'])
        self.assertEqual(old.p('hull',9)['hullPoints'],raw.p('hull',9)['hullPoints'])
        self.assertEqual(old.p('kinetic_pds',2)['baseChancePp'],22)

    def test_09_v22c_resource_ensemble_still_overlays_supply_weapon_tp_and_space(self):
        doc=load_json(REPO/STUDY); er,tr=_resource_rows(REPO,doc); m=build_deep_resource_matrix(REPO,MATRIX,'R1_CENTRAL_NO_MAJOR',er,tr)
        rows={int(r['tl']):r for r in tr if r['ensemble_id']=='R1_CENTRAL_NO_MAJOR'}
        for tl in range(1,10):
            r=rows[tl]; self.assertEqual(m.p('reactor',tl)['operationalTp'],int(r['reactor_undamaged_operational_tp']))
            self.assertEqual(m.p('kinetic_main',tl)['firingTp'],int(r['K_weapon_tp'])); self.assertEqual(m.p('energy_main',tl)['standardTp'],int(r['E_weapon_tp'])); self.assertEqual(m.p('missile_delivery',tl)['launchTp'],int(r['M_weapon_tp']))
            self.assertEqual(m.p('kinetic_main',tl)['space'],6)

    def test_10_all_8220_stage_a_scenarios_still_bind_legally(self):
        doc=load_json(REPO/STUDY); manifest=_read_csv(REPO/doc['stageAExperimentManifest']); er,tr=_resource_rows(REPO,doc)
        mats={eid:build_deep_resource_matrix(REPO,MATRIX,eid,er,tr) for eid in sorted({r['ensemble_id'] for r in er})}
        self.assertEqual(len(manifest),8220)
        for r in manifest:
            b=bind_scenario(mats[r['resource_ensemble_id']],r)
            self.assertLessEqual(b.variant.side_a.combat_space,b.variant.side_a.capacity); self.assertLessEqual(b.variant.side_b.combat_space,b.variant.side_b.capacity)

    def test_11_aux_resource_proxies_are_explicitly_unresolved_not_promoted(self):
        with tempfile.TemporaryDirectory() as td:
            summary=write_reconciliation_evidence(REPO,MATRIX,Path(td)); self.assertTrue(summary['passed']); self.assertGreater(summary['explicitUnresolvedRows'],0)
            with (Path(td)/'reconciliation_field_ledger.csv').open(newline='',encoding='utf-8-sig') as fh:
                rows=list(csv.DictReader(fh))
            self.assertTrue(any(r['system']=='PoweredReactiveArmorSystem' and r['classification']=='UNRESOLVED_CONFLICT_GAP' for r in rows))
            self.assertTrue(any(r['system']=='AblativeArmorLayer' and r['classification']=='UNRESOLVED_CONFLICT_GAP' for r in rows))

    def test_12_reconciliation_profile_and_ledger_are_complete(self):
        with tempfile.TemporaryDirectory() as td:
            summary=write_reconciliation_evidence(REPO,MATRIX,Path(td)); self.assertGreaterEqual(summary['ledgerRows'],500)
            with (Path(td)/'reconciliation_profile.json').open(encoding='utf-8') as fh:
                profile=json.load(fh)
            self.assertEqual(profile['profile'],'cp142-combat-surface-deep-reconciliation-v0.1'); self.assertEqual(len(profile['unresolvedExperimental']),4)

if __name__=='__main__': unittest.main()
