#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,sys,unittest
from pathlib import Path

def req(v,m):
    if not v: raise AssertionError(m)
def sha(p):
    h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()
def js(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def count_suite(s): return sum(count_suite(x) if isinstance(x,unittest.TestSuite) else 1 for x in s)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo',required=True); a=ap.parse_args(); repo=Path(a.repo).resolve()
    try:
        d=js(repo/'tools/checkpoints/checkpoint-139/checkpoint_139_definition.json')
        req(d['checkpoint']==139 and d['baseCheckpoint']==138,'checkpoint identity')
        req(d['declaredSubstantiveTrials']==0 and d['automaticPromotion'] is False,'promotion/trial boundary')
        req(sha(repo/'docs/design/player_technology/technology_numerical_matrix_v0_9.json')=='3088b0a9eb45f6bf505c24513e8bb2ac878819db4ab464ccfea330243c82f194','matrix v0.9 drift')
        req(sha(repo/'docs/archive/concepts/Star_Cluster_Game_Concept_v0.7x.docx')=='f76ca6ce488ccb5ad1352f7d38b8c3d4657c12ed64d0c93cc45d2db605cc632f','Concept v0.7x drift')
        req(sha(repo/'src/StarCluster.Core/Combat/Damage/LayeredDamageResolver.cs')=='ae0ec150f8a04823f3b5d703e9ba4e58a23ad9a21f1b69e60cc4483f4cbde45d','production LayeredDamageResolver drift')
        old={}
        for line in (repo/'docs/validation/evidence/checkpoint-138/CP138_REPOSITORY_SHA256SUMS.txt').read_text(encoding='utf-8-sig').splitlines():
            if line.strip(): h,r=line.split('  ',1); old[r]=h
        allowed={'src/StarCluster.Core/Combat/Damage/DefResDamageResolver.cs','tests/StarCluster.Tests/Combat/Damage/DefResDamageResolverTests.cs'}
        for rel,h in old.items():
            if rel.startswith('src/') or rel.startswith('tests/StarCluster.Tests/'):
                req((repo/rel).is_file(),f'missing frozen production/test file {rel}')
                req(sha(repo/rel)==h,f'pre-existing C# drift {rel}')
        req((repo/'src/StarCluster.Core/Combat/Damage/DefResDamageResolver.cs').is_file(),'research C# DEF/RES resolver missing')
        req((repo/'tests/StarCluster.Tests/Combat/Damage/DefResDamageResolverTests.cs').is_file(),'research C# DEF/RES tests missing')
        for rel in ('docs/archive/testing/pre-cp165-active/cp139_combat_model_reconciliation_profile_v0_1.json','docs/archive/testing/pre-cp165-active/cp139_def_res_reconciliation_study_v0_1.json','docs/archive/testing/pre-cp165-active/def_res_research_parity_fixtures_v0_1.json','tools/simulation/starcluster_research/combat_model_reconciliation.py','tools/simulation/starcluster_research/def_res_reconciliation_analysis.py','tools/simulation/tests/test_cp139_def_res_reconciliation.py'):
            req((repo/rel).is_file(),f'missing CP139 file {rel}')
        suite=unittest.defaultTestLoader.discover(str(repo/'tools/simulation/tests'),pattern='test_*.py'); n=count_suite(suite); req(n==243,f'Python discovery expected 243 got {n}')
        print('       CP139 preflight passed: CP138 production matrix/Concept/C# resolver frozen; research-only DEF/RES path present; 243 Python tests discovered; zero substantive trials; Stage A remains blocked on three declared integration items.')
        return 0
    except Exception as e:
        print(f'CP139 preflight failure: {e}',file=sys.stderr); return 1
if __name__=='__main__': raise SystemExit(main())
