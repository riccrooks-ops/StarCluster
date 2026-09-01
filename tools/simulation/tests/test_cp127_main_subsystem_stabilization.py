from __future__ import annotations
import csv
import importlib.util
import json
import shutil
import unittest
from pathlib import Path

REPO=Path(__file__).resolve().parents[3]
import sys
sys.path.insert(0,str(REPO/'tools/simulation'))
from starcluster_research.baseline_foundation import BaselineCatalog, enumerate_legal_builds
from starcluster_research.main_subsystem_stabilization_analysis import _run_condition, build_plan, validate_study

STUDY=REPO/'docs/archive/testing/pre-cp165-active/cp127_main_subsystem_tl_stabilization_study_v0_1.json'
MATRIX=REPO/'docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_4.json'
OLD=REPO/'docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_3.json'

class Cp127MainSubsystemStabilizationTests(unittest.TestCase):
    def test_01_study_schema(self):
        doc=json.loads(STUDY.read_text(encoding='utf-8'))
        self.assertEqual([],validate_study(doc))

    def test_02_legal_build_envelope_is_stable(self):
        c=BaselineCatalog(REPO,MATRIX.relative_to(REPO).as_posix())
        raw,builds=enumerate_legal_builds(c)
        self.assertEqual((14112,9427),(raw,len(builds)))

    def test_03_stl_move_equals_tl(self):
        d=json.loads(MATRIX.read_text(encoding='utf-8'))
        self.assertEqual(list(range(1,10)),[d['profiles']['stl'][str(t)]['move'] for t in range(1,10)])

    def test_04_missile_move_equals_tl_plus_one(self):
        d=json.loads(MATRIX.read_text(encoding='utf-8'))
        self.assertEqual(list(range(2,11)),[d['profiles']['missile_delivery'][str(t)]['missileMove'] for t in range(1,10)])

    def test_05_ftl_is_explicit_strategic_exception(self):
        d=json.loads(MATRIX.read_text(encoding='utf-8'))
        self.assertEqual([1,2,3,4,4,6,7,9,12],[d['profiles']['ftl'][str(t)]['strategicMove'] for t in range(1,10)])

    def test_06_tl8_energy_damage_only_targeted_change(self):
        d=json.loads(MATRIX.read_text(encoding='utf-8'))['profiles']['energy_main']['8']
        self.assertEqual((7,10,12,35,3,5,9,5),(d['lowDamage'],d['standardDamage'],d['highDamage'],d['accuracyPp'],d['apen'],d['spen'],d['range'],d['space']))

    def test_07_exact_nine_numeric_leaf_changes(self):
        a=json.loads(OLD.read_text(encoding='utf-8'));b=json.loads(MATRIX.read_text(encoding='utf-8'))
        diffs=[]
        for fam in b['profiles']:
            for tl in b['profiles'][fam]:
                for k,v in b['profiles'][fam][tl].items():
                    av=a['profiles'][fam][tl].get(k)
                    if isinstance(v,(int,float)) and not isinstance(v,bool) and isinstance(av,(int,float)) and not isinstance(av,bool) and v!=av and k!='tl':
                        diffs.append((fam,tl,k,av,v))
        self.assertEqual(9,len(diffs))

    def test_08_plan_counts_and_pure_tl_boundary(self):
        result=build_plan(REPO,STUDY,None)['summary']
        self.assertEqual([],result['failedGates'])
        self.assertEqual(86584,result['generatedVariants'])
        self.assertEqual(8658400,result['plannedSubstantiveTrials'])
        self.assertFalse(result['mixedTlShipsExecuted'])

    def test_09_checkpoint_preflight_is_stdlib_only_and_workbook_sync_is_readable(self):
        path=REPO/'tools/checkpoints/checkpoint-127/preflight_checkpoint_127.py'
        spec=importlib.util.spec_from_file_location('cp127_preflight',path)
        self.assertIsNotNone(spec); self.assertIsNotNone(spec.loader)
        mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        self.assertGreater(mod.validate_stdlib_only_python_surface(REPO),0)
        rows=mod.read_xlsx_table(REPO/'docs/archive/player_technology/pre-cp165-active/StarCluster_Stabilized_TL1_TL9_Technology_Component_Table_v0_6.xlsx')
        self.assertEqual(181,len(rows))

    def test_10_actual_consumer_micro_smoke(self):
        plan=build_plan(REPO,STUDY,None)
        out=REPO/'out'/'cp127-unit-actual-consumer-smoke'
        shutil.rmtree(out,ignore_errors=True)
        try:
            csv_path,_=_run_condition(REPO,plan['doc']['sourceMatrix'],int(plan['doc']['masterSeed']),plan['finalTasks'][:1],[],out,1,1)
            with csv_path.open(newline='',encoding='utf-8') as f:
                rows=list(csv.DictReader(f))
            self.assertEqual(4,len(rows))
            self.assertEqual(0,sum(int(r['errors']) for r in rows))
        finally:
            shutil.rmtree(out,ignore_errors=True)

if __name__=='__main__': unittest.main()
