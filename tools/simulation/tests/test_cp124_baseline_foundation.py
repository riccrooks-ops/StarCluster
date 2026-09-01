from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path

from starcluster_research.baseline_foundation import (
    BaselineCatalog,
    TELEMETRY_CONTRACT,
    enumerate_legal_builds,
    instrumentation_probes,
    pipeline_smoke,
    resolve_hull_repair,
    run_baseline_foundation,
    validate_study,
)
from starcluster_research.ecology import SideTelemetry, _weapon
from starcluster_research.study import load_json

REPO=Path(__file__).resolve().parents[3]
STUDY=REPO/'docs/archive/testing/pre-cp165-active/cp123_executable_baseline_instrumentation_foundation_v0_1.json'

class CP124BaselineFoundationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=load_json(STUDY)
        cls.catalog=BaselineCatalog(REPO,cls.doc['sourceMatrix'])
        cls.raw,cls.builds=enumerate_legal_builds(cls.catalog)
        cls.smoke_rows,cls.smoke_variants=pipeline_smoke(REPO,cls.catalog,cls.builds)

    def test_study_contract(self):
        self.assertEqual([],validate_study(self.doc))
        self.assertFalse(self.doc['balanceValidated'])
        self.assertFalse(self.doc['automaticPromotion'])
        self.assertEqual(0,self.doc['substantiveMonteCarloTrials'])

    def test_exact_executable_catalog_shape(self):
        rows=self.catalog.profile_rows()
        self.assertEqual(20,len(self.catalog.profiles))
        self.assertEqual(180,len(rows))
        self.assertEqual(set(range(1,10)),{r['tl'] for r in rows})

    def test_exhaustive_build_envelope_counts(self):
        self.assertEqual(14112,self.raw)
        self.assertEqual(9427,len(self.builds))
        expected={1:207,2:276,3:616,4:736,5:864,6:1544,7:1728,8:1728,9:1728}
        self.assertEqual(expected,{tl:sum(b.tl==tl for b in self.builds) for tl in range(1,10)})

    def test_all_legal_builds_fill_via_explicit_mission_aux(self):
        self.assertTrue(all(b.combat_space<=b.capacity for b in self.builds))
        self.assertTrue(all(b.used_space==b.capacity for b in self.builds))
        self.assertTrue(any(b.mission_aux_space>0 for b in self.builds))

    def test_family_and_swarmer_coverage(self):
        for tl in range(1,10):
            bs=[b for b in self.builds if b.tl==tl]
            self.assertEqual({'Kinetic','Energy','Missile'},{b.weapon_family for b in bs})
            self.assertTrue(any(b.weapon_family=='Missile' and b.missile_payload=='GP' for b in bs))
            self.assertEqual(tl>=2,any(b.weapon_family=='Missile' and b.missile_payload=='Swarmer' for b in bs))

    def test_duplicate_ew_is_nonadditive(self):
        b=next(b for b in self.builds if b.tl==5 and b.ecm_count==2 and b.eccm_count==2)
        self.assertEqual(self.catalog.p('ecm',5)['rating'],b.effective_ecm_rating)
        self.assertEqual(self.catalog.p('eccm',5)['rating'],b.effective_eccm_rating)

    def test_power_pressure_is_diagnostic_not_legality(self):
        self.assertTrue(any(b.tl<=3 and b.nominal_power_margin<0 for b in self.builds))
        self.assertFalse(any(b.tl>=5 and b.nominal_power_margin<0 for b in self.builds))
        self.assertTrue(any(b.tl>=7 and b.nominal_power_margin>=5 for b in self.builds))

    def test_split_gp_missile_profile_composes_correctly(self):
        b=next(b for b in self.builds if b.tl==5 and b.weapon_family=='Missile' and b.missile_payload=='GP')
        from starcluster_research.baseline_foundation import _build_to_ecology
        w=_weapon(self.catalog.matrix,_build_to_ecology(b,'test'))
        self.assertEqual(13,w['damage'])
        self.assertEqual(2,w['spen'])
        self.assertEqual(4,w['apen'])
        self.assertEqual(60,w['guidance'])
        self.assertEqual(1,w['packets'])

    def test_swarmer_profile_preserves_one_flight_two_packets(self):
        p=self.catalog.missile_operational_profile(5,'Swarmer')
        self.assertEqual(2,p['packets'])
        self.assertEqual(7,p['damage'])
        self.assertEqual(70,p['guidance'])
        self.assertEqual(10,p['pdsInterceptPenaltyPp'])

    def test_pipeline_smoke_has_all_expected_mirrors(self):
        self.assertEqual(70,len(self.smoke_rows))
        self.assertFalse(any(int(r['errors']) for r in self.smoke_rows))
        groups={g:sum(r['scenario_group']==g for r in self.smoke_rows) for g in {r['scenario_group'] for r in self.smoke_rows}}
        self.assertEqual({'kinetic_vs_energy':18,'energy_vs_kinetic':18,'missile_gp_vs_defense':18,'swarmer_vs_defense':16},groups)
        self.assertEqual({'SideAFirst','SideBFirst'},{r['movement_order'] for r in self.smoke_rows})

    def test_pipeline_exercises_new_raw_telemetry(self):
        self.assertTrue(any(float(r['mean_a_direct_fire_eligible_actions'])>0 for r in self.smoke_rows))
        self.assertTrue(any(float(r['mean_a_missile_launch_eligible_actions'])>0 for r in self.smoke_rows))
        self.assertTrue(any(float(r['mean_b_damage_packets_resolved'])>=2 for r in self.smoke_rows if r['scenario_group']=='swarmer_vs_defense'))
        self.assertTrue(any(float(r['mean_b_shield_penetration_bypassed'])>0 for r in self.smoke_rows))

    def test_instrumentation_probes_are_blocking_and_green(self):
        probes=instrumentation_probes(REPO,self.catalog,self.builds,self.smoke_rows)
        self.assertEqual(9,len(probes))
        self.assertTrue(all(p['passed'] for p in probes),probes)
        self.assertIn('missile-telemetry-ownership',{p['probe'] for p in probes})
        self.assertIn('damage-layer-oracle',{p['probe'] for p in probes})

    def test_damage_control_yield_is_reference_characteristic(self):
        for tl,expected in ((1,1),(7,2),(9,3)):
            t=SideTelemetry()
            self.assertEqual(expected,resolve_hull_repair(self.catalog.p('damage_control',tl),10,1,t))
            self.assertEqual(1,t.damage_control_attempts)
            self.assertEqual(1,t.damage_control_successes)
            self.assertEqual(expected,t.damage_control_hull_restored)

    def test_telemetry_contract_is_raw_and_complete(self):
        metrics={r['metric'] for r in TELEMETRY_CONTRACT}
        self.assertEqual(47,len(metrics))
        self.assertTrue(metrics<=set(SideTelemetry.__dataclass_fields__))
        self.assertTrue(all(r['kind'].startswith('raw_') for r in TELEMETRY_CONTRACT))

    def test_full_foundation_runner(self):
        with tempfile.TemporaryDirectory() as td:
            res=run_baseline_foundation(REPO,STUDY,Path(td))
            self.assertEqual([],res['failedGates'])
            self.assertEqual(9427,res['legalBuilds'])
            self.assertEqual(70,res['pipelineSmokeVariants'])
            self.assertEqual(0,res['substantiveMonteCarloTrials'])
            self.assertTrue((Path(td)/'legal_builds.csv').is_file())
            self.assertTrue((Path(td)/'telemetry_contract.json').is_file())

if __name__=='__main__': unittest.main()
