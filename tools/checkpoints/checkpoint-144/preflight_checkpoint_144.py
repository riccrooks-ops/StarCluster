#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json,sys,unittest
from collections import Counter
from pathlib import Path

MATRIX_SHA='3088b0a9eb45f6bf505c24513e8bb2ac878819db4ab464ccfea330243c82f194'
CONCEPT_SHA='f76ca6ce488ccb5ad1352f7d38b8c3d4657c12ed64d0c93cc45d2db605cc632f'
PROD_DAMAGE_SHA='ae0ec150f8a04823f3b5d703e9ba4e58a23ad9a21f1b69e60cc4483f4cbde45d'
EXPECTED_RESOURCES={'R0_CP138_HISTORICAL','R1_CENTRAL_NO_MAJOR','R2_CENTRAL_PROPULSION','R3_LOWER_DEMAND','R4_TIGHT_HIGH_DEMAND'}

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
        d=js(repo/'tools/checkpoints/checkpoint-144/checkpoint_144_definition.json')
        req(d['checkpoint']==144 and d['baseCheckpoint']==143,'checkpoint identity')
        req(d['expectedStageAScenarios']==6850 and d['expectedResourceEnvironments']==5 and d['expectedScenarioStrata']==10 and d['expectedOrderedSameTlWeaponPairings']==137,'Stage-A scope')
        req(d['substantiveTrialsPerScenario']==500 and d['expectedSubstantiveCombatTrials']==3425000,'substantive scope')
        req(d['hardTurnSentinel']==60 and d['longResolvedTurn']==25,'duration boundaries')
        req(d['tuningAllowed'] is False and d['automaticPromotion'] is False and d['stageBAutomatic'] is False,'promotion boundary')
        req(sha(repo/'docs/design/player_technology/technology_numerical_matrix_v0_9.json')==MATRIX_SHA,'matrix v0.9 drift')
        req(sha(repo/'docs/archive/concepts/Star_Cluster_Game_Concept_v0.7x.docx')==CONCEPT_SHA,'Concept v0.7x drift')
        req(sha(repo/'src/StarCluster.Core/Combat/Damage/LayeredDamageResolver.cs')==PROD_DAMAGE_SHA,'production LayeredDamageResolver drift')

        # Freeze all CP143 production C# and every pre-existing CP143 C# test file.
        cp143_manifest={};mp=repo/'docs/validation/evidence/checkpoint-143/CP143_REPOSITORY_SHA256SUMS.txt';req(mp.is_file(),'CP143 manifest missing')
        for line in mp.read_text(encoding='utf-8-sig').splitlines():
            if line.strip():h,r=line.split('  ',1);cp143_manifest[r]=h
        frozen_src=frozen_tests=0
        for rel,h in cp143_manifest.items():
            if rel.startswith('src/'):
                req((repo/rel).is_file(),f'missing frozen CP143 production file {rel}');req(sha(repo/rel)==h,f'CP143 production C# drift {rel}');frozen_src+=1
            elif rel.startswith('tests/StarCluster.Tests/'):
                req((repo/rel).is_file(),f'missing frozen CP143 C# test {rel}');req(sha(repo/rel)==h,f'pre-existing CP143 C# test drift {rel}');frozen_tests+=1
        req(frozen_src>450 and frozen_tests>80,'unexpected CP143 C# freeze surface')
        new_cs=repo/'tests/StarCluster.Tests/Combat/Tactics/AdaptiveEngageResearchParityTests.cs';req(new_cs.is_file(),'CP144 C# parity test missing')
        req(new_cs.relative_to(repo).as_posix() not in cp143_manifest,'CP144 parity test unexpectedly present in CP143 manifest')

        required=(
            'docs/archive/testing/pre-cp165-active/cp144_engage_adaptive_policy_parity_fixtures_v0_1.json',
            'docs/archive/testing/pre-cp165-active/cp144_stage_a_experiment_manifest.csv',
            'docs/archive/testing/pre-cp165-active/cp144_stage_a_resource_ensemble.csv',
            'docs/archive/testing/pre-cp165-active/cp144_stage_a_resource_ensemble_tl.csv',
            'docs/archive/testing/pre-cp165-active/cp144_whole_combat_stage_a_response_surface_study_v0_1.json',
            'tools/simulation/starcluster_research/whole_combat_stage_a_response_surface.py',
            'tools/simulation/tests/test_cp144_engage_adaptive_policy_parity.py',
            'tools/simulation/tests/test_cp144_whole_combat_stage_a_response_surface.py',
            'docs/validation/Checkpoint_144_EngageAdaptive_Missile_Parity_And_Whole_Combat_Stage_A_Response_Surface.md',
        )
        for rel in required:req((repo/rel).is_file(),f'missing CP144 dependency {rel}')

        study=js(repo/'docs/archive/testing/pre-cp165-active/cp144_whole_combat_stage_a_response_surface_study_v0_1.json')
        req(study['checkpoint']==144 and study['baseCheckpoint']==143 and study['scope']=='whole-combat-stage-a-substantive-response-surface','study identity')
        req(study['canonicalCombatKernelVersion']=='0.5','kernel version in study')
        req(study['expectedStageAScenarios']==6850 and study['expectedResourceEnvironments']==5 and study['expectedScenarioStrata']==10 and study['expectedOrderedSameTlWeaponPairings']==137,'study factorial')
        req(study['substantiveTrialsPerScenario']==500 and study['substantiveCombatTrials']==3425000,'study trials')
        req(study['tuningAllowed'] is False and study['automaticPromotion'] is False and study['stageBAutomatic'] is False,'study promotion boundary')

        fixture=js(repo/study['engageAdaptiveParityFixture']);req(len(fixture['cases'])==10,'shared policy fixture cases')
        py=(repo/'tools/simulation/starcluster_research/canonical_combat.py').read_text(encoding='utf-8')
        req('CANONICAL_COMBAT_KERNEL_VERSION = "0.5"' in py or "CANONICAL_COMBAT_KERNEL_VERSION = '0.5'" in py,'canonical kernel 0.5 marker')
        req('envelope_hold' in py and 'track_close' in py and 'standoff' in py,'EngageAdaptive parity reason markers')
        # The obsolete generic preferred-range reopen branch must not survive in _choose_order.
        choose=py.split('def _choose_order',1)[1].split('\ndef ',1)[0]
        req('preferred = _preferred_weapon_range' not in choose,'obsolete preferred-range reopen branch remains')

        ensemble=rows(repo/study['resourceEnsemble']);tl_rows=rows(repo/study['resourceEnsembleTl']);manifest=rows(repo/study['stageAExperimentManifest'])
        ids={r['ensemble_id'] for r in ensemble};req(ids==EXPECTED_RESOURCES,f'five-resource ensemble mismatch {ids}')
        req('R5_CENTRAL_HIGH_DEMAND' not in ids,'R5 duplicate must be collapsed')
        req(len(tl_rows)==45 and {r['ensemble_id'] for r in tl_rows}==EXPECTED_RESOURCES,'resource TL crossing')
        req(len(manifest)==6850 and len({r['scenario_id'] for r in manifest})==6850,'Stage-A manifest coverage')
        req({r['resource_ensemble_id'] for r in manifest}==EXPECTED_RESOURCES,'manifest resource crossing')
        req(len(Counter(r['scenario_stratum'] for r in manifest))==10,'ten-stratum crossing')
        req(len({(int(r['tl']),r['side_a_weapon'],r['side_b_weapon']) for r in manifest})==137,'137 ordered same-TL pairings')
        req(all(int(r['planned_trials'])==500 for r in manifest),'planned trial count')

        suite=unittest.defaultTestLoader.discover(str(repo/'tools/simulation/tests'),pattern='test_*.py');n=count_suite(suite);req(n==298,f'Python discovery expected 298 got {n}')
        print(f'       CP144 preflight passed: CP143 production C# frozen across {frozen_src} src files and {frozen_tests} pre-existing C# tests; shared 10-case EngageAdaptive parity fixture present; 6,850-cell/5-resource Stage-A population valid; 298 Python tests discovered; 3,425,000 substantive trials declared with tuning/promotion disabled.')
        return 0
    except Exception as e:
        print(f'CP144 preflight failure: {e}',file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
