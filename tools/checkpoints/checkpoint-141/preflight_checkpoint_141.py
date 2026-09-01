#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json,sys,unittest
from collections import Counter
from pathlib import Path

def req(v,m):
    if not v: raise AssertionError(m)
def sha(p):
    h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()
def js(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def rows(p):
    with p.open(newline='',encoding='utf-8-sig') as f: return list(csv.DictReader(f))
def count_suite(s): return sum(count_suite(x) if isinstance(x,unittest.TestSuite) else 1 for x in s)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo',required=True); a=ap.parse_args(); repo=Path(a.repo).resolve()
    try:
        d=js(repo/'tools/checkpoints/checkpoint-141/checkpoint_141_definition.json')
        req(d['checkpoint']==141 and d['baseCheckpoint']==140,'checkpoint identity')
        req(d['hardTurnSentinel']==60 and d['longResolvedTurn']==25,'duration boundaries')
        req(d['declaredSubstantiveTrials']==0 and d['automaticPromotion'] is False,'promotion/trial boundary')
        req(sha(repo/'docs/design/player_technology/technology_numerical_matrix_v0_9.json')=='3088b0a9eb45f6bf505c24513e8bb2ac878819db4ab464ccfea330243c82f194','matrix v0.9 drift')
        req(sha(repo/'docs/archive/concepts/Star_Cluster_Game_Concept_v0.7x.docx')=='f76ca6ce488ccb5ad1352f7d38b8c3d4657c12ed64d0c93cc45d2db605cc632f','Concept v0.7x drift')
        req(sha(repo/'src/StarCluster.Core/Combat/Damage/LayeredDamageResolver.cs')=='ae0ec150f8a04823f3b5d703e9ba4e58a23ad9a21f1b69e60cc4483f4cbde45d','production LayeredDamageResolver drift')
        cp140_manifest={}
        for line in (repo/'docs/validation/evidence/checkpoint-140/CP140_REPOSITORY_SHA256SUMS.txt').read_text(encoding='utf-8-sig').splitlines():
            if line.strip(): h,r=line.split('  ',1); cp140_manifest[r]=h
        for rel,h in cp140_manifest.items():
            if rel.startswith('src/') or rel.startswith('tests/StarCluster.Tests/'):
                req((repo/rel).is_file(),f'missing frozen CP140 C# file {rel}')
                req(sha(repo/rel)==h,f'CP140 C# drift {rel}')
        required=(
            'docs/archive/testing/pre-cp165-active/cp139_def_res_reconciliation_study_v0_1.json',
            'docs/archive/testing/pre-cp165-active/cp140_stage_a_integration_study_v0_1.json',
            'docs/archive/testing/pre-cp165-active/cp140_v22c_stage_a_experiment_manifest.csv',
            'docs/archive/testing/pre-cp165-active/cp140_v22c_resource_ensemble.csv',
            'docs/archive/testing/pre-cp165-active/cp140_v22c_resource_ensemble_tl.csv',
            'docs/archive/testing/pre-cp165-active/cp141_combat_duration_stalemate_study_v0_1.json',
            'tools/simulation/starcluster_research/combat_duration_stalemate_analysis.py',
            'tools/simulation/tests/test_cp139_def_res_reconciliation.py',
            'tools/simulation/tests/test_cp140_stage_a_integration.py',
            'tools/simulation/tests/test_cp141_combat_duration_stalemate.py',
        )
        for rel in required: req((repo/rel).is_file(),f'missing CP141 dependency {rel}')
        study=js(repo/'docs/archive/testing/pre-cp165-active/cp141_combat_duration_stalemate_study_v0_1.json')
        req(study['checkpoint']==141 and study['baseCheckpoint']==140,'study identity')
        req(study['expectedStageAScenarios']==8220 and study['integrationSmokeTrials']==8220,'study smoke size')
        req(study['hardTurnSentinel']==60 and study['longResolvedTurn']==25 and study['extendTurnCap'] is False,'study duration semantics')
        req(study['substantiveCombatTrials']==0 and study['automaticPromotion'] is False,'study trial/promotion boundary')
        manifest=rows(repo/'docs/archive/testing/pre-cp165-active/cp140_v22c_stage_a_experiment_manifest.csv')
        req(len(manifest)==8220 and len({r['scenario_id'] for r in manifest})==8220,'Stage A manifest identity')
        req({int(r['planned_trials']) for r in manifest}=={500} and {int(r['promotion_allowed']) for r in manifest}=={0},'Stage A planned/promotion columns')
        resources=Counter(r['resource_ensemble_id'] for r in manifest); strata=Counter(r['scenario_stratum'] for r in manifest)
        req(len(resources)==6 and set(resources.values())=={1370},'resource crossing')
        req(len(strata)==10 and set(strata.values())=={822},'stratum crossing')
        cp140=js(repo/'docs/archive/testing/pre-cp165-active/cp140_stage_a_integration_study_v0_1.json')
        req(cp140['checkpoint']==140 and cp140['substantiveCombatTrials']==0,'frozen CP140 study identity')
        text=(repo/'tools/simulation/starcluster_research/canonical_combat.py').read_text(encoding='utf-8')
        req('STALEMATE_MUTUAL_OFFENSIVE_EXHAUSTION' in text and 'TURN_CAP_SENTINEL' in text,'termination semantics missing')
        suite=unittest.defaultTestLoader.discover(str(repo/'tools/simulation/tests'),pattern='test_*.py'); n=count_suite(suite); req(n==263,f'Python discovery expected 263 got {n}')
        print('       CP141 preflight passed: CP140/CP139 production controls frozen; 60-turn hard sentinel and conservative mutual-offense-exhaustion stalemate semantics present; 8,220-scenario duration matrix bound; 263 Python tests discovered; zero substantive trials.')
        return 0
    except Exception as e:
        print(f'CP141 preflight failure: {e}',file=sys.stderr); return 1
if __name__=='__main__': raise SystemExit(main())
