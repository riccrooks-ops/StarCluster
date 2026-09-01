from __future__ import annotations
import csv, json, sys, unittest
from pathlib import Path
REPO=Path(__file__).resolve().parents[3]
SIM=REPO/'tools/simulation'
if str(SIM) not in sys.path: sys.path.insert(0,str(SIM))
from starcluster_research.ecology import CandidateMatrix
from starcluster_research.auxiliary_integration_analysis import ROLE_SPECS, build_contexts, build_plan, make_build, validate_study

MATRIX='docs/design/player_technology/technology_numerical_matrix_v0_9.json'
STUDY=REPO/'docs/archive/testing/pre-cp165-active/cp138_aux_reference_full_ship_integration_study_v0_1.json'
CAT=REPO/'docs/archive/player_technology/pre-cp165-active/auxiliary_component_catalog_v0_4.json'
PH=REPO/'docs/archive/player_technology/pre-cp165-active/auxiliary_reference_philosophies_v0_1.json'
SHIELD=REPO/'docs/archive/player_technology/pre-cp165-active/shield_auxiliary_cp138_vetting_v0_1.csv'

class Cp138AuxiliaryIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.matrix=CandidateMatrix(REPO,MATRIX)
    def test_catalog_has_35_unique_reference_swept_components(self):
        d=json.loads(CAT.read_text()); comps=d['components']
        self.assertEqual(35,len(comps)); self.assertEqual(35,len({c['id'] for c in comps}))
        self.assertTrue(all(c.get('referenceBasis') and c.get('referencePhilosophies') and c.get('sweepDisposition') for c in comps))
        self.assertEqual(['eccm','ecm'],sorted(x['id'] for x in d['integratedStandardAuxSystems']))
    def test_all_catalog_components_are_covered_by_reference_philosophy(self):
        d=json.loads(PH.read_text()); self.assertEqual(10,len(d['philosophies']))
        covered={c for p in d['philosophies'] for c in p['catalogComponents']}
        catalog={c['id'] for c in json.loads(CAT.read_text())['components']}
        self.assertEqual(catalog,covered)
    def test_mission_control_exact_fills_every_tl_and_family(self):
        for tl in range(1,10):
            for fam in (('Kinetic','Energy','GP') if tl==1 else ('Kinetic','Energy','GP','Swarmer')):
                b=make_build(self.matrix,tl,fam,'mission-control'); self.assertEqual(b.capacity,b.used_space); self.assertTrue(b.shield); self.assertEqual('mainline',b.armor_profile)
    def test_combat_generalist_is_legal_and_role_selective(self):
        for tl in range(1,10):
            for fam in (('Kinetic','Energy','GP') if tl==1 else ('Kinetic','Energy','GP','Swarmer')):
                b=make_build(self.matrix,tl,fam,'combat-generalist'); self.assertEqual(b.capacity,b.used_space); self.assertTrue(b.ecm and b.eccm); self.assertEqual('AMM',b.pds_family); self.assertEqual(tl>=3,b.shield_hardener)
                self.assertGreaterEqual(b.mission_aux_space,0)
    def test_role_mechanics_match_existing_executable_aux(self):
        expected={
            'electronic-attack':(True,False,None,False),'counter-ew':(False,True,None,False),'information-control':(True,True,None,False),
            'amm-escort':(False,True,'AMM',False),'energy-screen':(False,True,'Energy',False),'kinetic-screen':(False,True,'Kinetic',False),
        }
        for role,e in expected.items():
            b=make_build(self.matrix,5,'Kinetic',role); self.assertEqual(e,(b.ecm,b.eccm,b.pds_family,b.shield_hardener))
    def test_shield_guard_starts_at_tl3_and_hardener_seed_is_unchanged(self):
        with self.assertRaises(ValueError): make_build(self.matrix,2,'Energy','shield-guard')
        b=make_build(self.matrix,3,'Energy','shield-guard'); self.assertTrue(b.shield_hardener); self.assertTrue(b.eccm)
        br=self.matrix.branches['shield-hardener']; self.assertEqual((3,1),(int(br['tl']),int(br['space']))); self.assertIn('ShieldArmor2',br['numeric'].replace(' ',''))
    def test_study_shape_and_every_reference_build_is_exact_fill(self):
        doc=json.loads(STUDY.read_text()); self.assertEqual([],validate_study(doc)); p=build_plan(REPO,STUDY,None)
        self.assertEqual((787,1574,3148000),(p['summary']['logicalContexts'],p['summary']['generatedVariants'],p['summary']['plannedSubstantiveTrials']))
        self.assertEqual({'ew-counterplay':105,'generalist-cross-family':86,'hardener-focus':84,'pds-threat':204,'role-baseline':35,'role-marginal':273},p['summary']['layerContexts'])
        self.assertTrue(all(b.used_space==b.capacity for c in p['contexts'] for b in (c.build_a,c.build_b)))
    def test_shield_aux_vetting_rejects_legacy_reset_seeds_and_defers_specialists(self):
        with SHIELD.open(newline='',encoding='utf-8') as f: rows={r['component']:r for r in csv.DictReader(f)}
        self.assertEqual('reject_legacy_numeric_rederive_later',rows['shield-battery']['status']); self.assertIn('full SC',rows['shield-battery']['reason'])
        self.assertEqual('reject_legacy_numeric_rederive_later',rows['shield-booster']['status'])
        self.assertEqual('yes',rows['shield-hardener']['cp138_execution'])
        self.assertEqual('no',rows['particle-deflection-screen']['cp138_execution']); self.assertEqual('no',rows['field-stabilizer']['cp138_execution'])

if __name__=='__main__': unittest.main()
