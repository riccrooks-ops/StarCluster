#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json,sys,unittest
from collections import Counter
from pathlib import Path

MATRIX_SHA='3088b0a9eb45f6bf505c24513e8bb2ac878819db4ab464ccfea330243c82f194'
CONCEPT_SHA='f76ca6ce488ccb5ad1352f7d38b8c3d4657c12ed64d0c93cc45d2db605cc632f'
PROD_DAMAGE_SHA='ae0ec150f8a04823f3b5d703e9ba4e58a23ad9a21f1b69e60cc4483f4cbde45d'
CP142_REF_SHA='07752e40076604e16e1a525a999cfcc248e2716bbdd8d7138d0b0f805afa5e94'

def req(v,m):
    if not v: raise AssertionError(m)
def sha(p):
    h=hashlib.sha256();h.update(p.read_bytes());return h.hexdigest()
def js(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def rows(p):
    with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def count_suite(s):return sum(count_suite(x) if isinstance(x,unittest.TestSuite) else 1 for x in s)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);a=ap.parse_args();repo=Path(a.repo).resolve()
    try:
        d=js(repo/'tools/checkpoints/checkpoint-143/checkpoint_143_definition.json')
        req(d['checkpoint']==143 and d['baseCheckpoint']==142,'checkpoint identity')
        req(d['expectedMissileMirrorScenarios']==1980 and d['expectedAttributionBatches']==4,'attribution scope')
        req(d['hardTurnSentinel']==60 and d['longResolvedTurn']==25,'duration boundaries')
        req(d['declaredSubstantiveTrials']==0 and d['tuningAllowed'] is False and d['automaticPromotion'] is False,'scope boundary')
        req(sha(repo/'docs/design/player_technology/technology_numerical_matrix_v0_9.json')==MATRIX_SHA,'matrix v0.9 drift')
        req(sha(repo/'docs/archive/concepts/Star_Cluster_Game_Concept_v0.7x.docx')==CONCEPT_SHA,'Concept v0.7x drift')
        req(sha(repo/'src/StarCluster.Core/Combat/Damage/LayeredDamageResolver.cs')==PROD_DAMAGE_SHA,'production LayeredDamageResolver drift')
        # Freeze every accepted CP142 C# production/test file byte-for-byte.
        cp142_manifest={}
        p=repo/'docs/validation/evidence/checkpoint-142/CP142_REPOSITORY_SHA256SUMS.txt';req(p.is_file(),'CP142 manifest missing')
        for line in p.read_text(encoding='utf-8-sig').splitlines():
            if line.strip():h,r=line.split('  ',1);cp142_manifest[r]=h
        frozen=0
        for rel,h in cp142_manifest.items():
            if rel.startswith('src/') or rel.startswith('tests/StarCluster.Tests/'):
                req((repo/rel).is_file(),f'missing frozen CP142 C# file {rel}')
                req(sha(repo/rel)==h,f'CP142 C# drift {rel}');frozen+=1
        req(frozen>500,'unexpected CP142 C# freeze surface')
        required=(
            'docs/archive/testing/pre-cp165-active/cp142_combat_surface_deep_reconciliation_study_v0_1.json',
            'docs/archive/testing/pre-cp165-active/cp143_missile_mirror_pacing_attribution_study_v0_1.json',
            'docs/archive/testing/pre-cp165-active/cp143_cp142_native_missile_mirror_reference.csv',
            'tools/simulation/starcluster_research/missile_mirror_pacing_attribution.py',
            'tools/simulation/tests/test_cp143_missile_mirror_pacing_attribution.py',
            'docs/validation/Checkpoint_143_Missile_Mirror_Pacing_Attribution.md',
        )
        for rel in required:req((repo/rel).is_file(),f'missing CP143 dependency {rel}')
        study=js(repo/'docs/archive/testing/pre-cp165-active/cp143_missile_mirror_pacing_attribution_study_v0_1.json')
        req(study['checkpoint']==143 and study['baseCheckpoint']==142 and study['scope']=='missile-mirror-attribution-only','study identity')
        req(study['expectedMissileMirrorScenarios']==1980,'study scenario count')
        req(study['hardTurnSentinel']==60 and study['longResolvedTurn']==25,'study duration boundary')
        req(study['substantiveCombatTrials']==0 and study['tuningAllowed'] is False and study['automaticPromotion'] is False,'study scope boundary')
        ref=repo/study['pairedBaselineReference'];req(sha(ref)==CP142_REF_SHA,'CP142 paired reference hash drift')
        ref_rows=rows(ref);req(len(ref_rows)==1980 and len({r['scenario_id'] for r in ref_rows})==1980,'CP142 paired reference coverage')
        manifest=rows(repo/'docs/archive/testing/pre-cp165-active/cp140_v22c_stage_a_experiment_manifest.csv')
        missile=[r for r in manifest if r['side_a_weapon'].startswith('M_') and r['side_b_weapon'].startswith('M_')]
        req(len(manifest)==8220 and len(missile)==1980 and {r['scenario_id'] for r in missile}=={r['scenario_id'] for r in ref_rows},'paired Stage-A population')
        req(len(Counter(r['scenario_stratum'] for r in missile))==10,'ten-stratum paired crossing')
        req(len(Counter(r['resource_ensemble_id'] for r in missile))==6,'six-resource paired crossing')
        src=(repo/'tools/simulation/starcluster_research/canonical_combat.py').read_text(encoding='utf-8')
        for marker in ('missile_launch_decision','missile_launch','missile_terminal','missile_range_exhausted','missile_inventory','missile_turn_state'):
            req(marker in src,f'observation event marker missing: {marker}')
        attr=(repo/'tools/simulation/starcluster_research/missile_mirror_pacing_attribution.py').read_text(encoding='utf-8')
        for marker in ('SENSOR_WEAPON_ENVELOPE_OSCILLATION','TP_LAUNCH_DENIAL','cp142-paired-outcome-drift','instrumentation-nonneutral'):
            req(marker in attr,f'attribution marker missing: {marker}')
        suite=unittest.defaultTestLoader.discover(str(repo/'tools/simulation/tests'),pattern='test_*.py');n=count_suite(suite);req(n==287,f'Python discovery expected 287 got {n}')
        print(f'       CP143 preflight passed: CP142 production controls frozen across {frozen} C# files; exact 1,980 native-CP142 Missile-mirror reference present; optional pacing instrumentation active; 287 Python tests discovered; zero tuning/substantive trials.')
        return 0
    except Exception as e:
        print(f'CP143 preflight failure: {e}',file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
