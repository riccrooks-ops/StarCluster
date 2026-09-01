#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, hashlib, json, re, sys, unittest
from pathlib import Path

def req(v,m):
    if not v: raise AssertionError(m)
def text(p): req(p.is_file(),f'missing {p}'); return p.read_text(encoding='utf-8-sig')
def js(p): return json.loads(text(p))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def count_suite(suite):
    return sum(count_suite(x) if isinstance(x,unittest.TestSuite) else 1 for x in suite)

def manifest(path):
    out={}
    for line in text(path).splitlines():
        if line.strip(): h,r=line.split('  ',1); out[r]=h
    return out

def validate_wrapper(repo):
    d=repo/'tools/checkpoints/checkpoint-138'; w=text(d/'apply_checkpoint_138.ps1')
    req("$preflight=Join-Path $PSScriptRoot 'preflight_checkpoint_138.py'" in w,'wrapper preflight binding')
    req("$contract=Join-Path $PSScriptRoot 'test_checkpoint_138_contract.py'" in w,'wrapper contract binding')
    req('preflight_checkpoint_137.py' not in w and 'test_checkpoint_137_contract.py' not in w,'stale CP137 wrapper dependency')
    for name in ('preflight_checkpoint_138.py','test_checkpoint_138_contract.py','checkpoint_138_definition.json'):
        req((d/name).is_file(),f'wrapper dependency {name}')

def validate_cp137(repo):
    z=repo/'docs/validation/evidence/checkpoint-138/accepted-cp137/checkpoint-137-native-results.zip'
    req(sha(z)=='4d4f3edb3dd583024034b8fb61c00960d5ae25c0987c9f2c4a3fbdd4b08972d5','accepted CP137 ZIP hash')
    s=js(repo/'docs/validation/evidence/checkpoint-138/accepted-cp137/CP137_NATIVE_ACCEPTANCE_SUMMARY.json')
    req(s['checkpoint']==137 and s['substantiveTrials']==1960000 and s['substantiveTrialErrors']==0 and s['substantiveMechanicsFlags']==0 and s['failedGates']==[],'accepted CP137 summary')

def validate_frozen(repo):
    req(sha(repo/'docs/design/player_technology/technology_numerical_matrix_v0_9.json')=='3088b0a9eb45f6bf505c24513e8bb2ac878819db4ab464ccfea330243c82f194','matrix v0.9 drift')
    req(sha(repo/'docs/archive/player_technology/pre-cp165-active/technology_component_table_v0_8d.json')=='788ee796857cf73cd41f8fae736be45678d3c5b44f1b987db2532232c2b03f37','component table drift')
    req(sha(repo/'docs/archive/player_technology/pre-cp165-active/StarCluster_Revised_TL1_TL9_Technology_Component_Table_v0_8d.xlsx')=='d940e4dc47f813bee6697e247e707d7792eec1b24fed3cb357f6672067b5918b','workbook drift')
    req(sha(repo/'docs/archive/concepts/Star_Cluster_Game_Concept_v0.7x.docx')=='f76ca6ce488ccb5ad1352f7d38b8c3d4657c12ed64d0c93cc45d2db605cc632f','Concept v0.7x drift')
    old=manifest(repo/'docs/validation/evidence/checkpoint-137/CP137_REPOSITORY_SHA256SUMS.txt')
    for rel,h in old.items():
        if rel.startswith('src/') or rel.startswith('tests/StarCluster.Tests/'):
            p=repo/rel; req(p.is_file(),f'frozen production file missing {rel}'); req(sha(p)==h,f'production C# drift {rel}')

def validate_catalog(repo):
    c=js(repo/'docs/archive/player_technology/pre-cp165-active/auxiliary_component_catalog_v0_4.json'); comps=c['components']
    req(c['checkpoint']==138 and len(comps)==35 and len({x['id'] for x in comps})==35,'AUX catalog identity/count')
    req(all(x.get('referenceBasis') and x.get('referencePhilosophies') and x.get('sweepDisposition') for x in comps),'AUX references/philosophy/disposition')
    req(sorted(x['id'] for x in c['integratedStandardAuxSystems'])==['eccm','ecm'],'integrated ECM/ECCM')
    req(sorted(x['id'] for x in comps if x.get('cp138CombatExecution'))==['energy-pds','kinetic-pds','local-amm-pds','shield-hardener'],'combat execution boundary')
    p=js(repo/'docs/archive/player_technology/pre-cp165-active/auxiliary_reference_philosophies_v0_1.json'); req(len(p['philosophies'])==10,'philosophy count')
    covered={x for ph in p['philosophies'] for x in ph['catalogComponents']}; req(covered=={x['id'] for x in comps},'35/35 philosophy coverage')
    with (repo/'docs/archive/player_technology/pre-cp165-active/shield_auxiliary_cp138_vetting_v0_1.csv').open(newline='',encoding='utf-8') as f: rows={r['component']:r for r in csv.DictReader(f)}
    req(rows['shield-battery']['status']=='reject_legacy_numeric_rederive_later' and rows['shield-booster']['status']=='reject_legacy_numeric_rederive_later','legacy Shield support rejection')
    req(rows['shield-hardener']['cp138_execution']=='yes' and rows['particle-deflection-screen']['cp138_execution']=='no' and rows['field-stabilizer']['cp138_execution']=='no','Shield execution boundary')

def validate_study(repo):
    s=js(repo/'docs/archive/testing/pre-cp165-active/cp138_aux_reference_full_ship_integration_study_v0_1.json')
    req(s['checkpoint']==138 and s['canonicalKernelVersion']=='0.4' and s['masterSeed']==138001,'study identity')
    req(s['reactorTuningEnabled'] is False and s['powerAuxExecutionEnabled'] is False,'Reactor/power AUX must be frozen')
    e=s['expected']; req((e['logicalContexts'],e['generatedVariants'],e['substantiveTrials'],e['catalogComponents'],e['referencePhilosophies'])==(787,1574,3148000,35,10),'study expected shape')

def validate_code(repo):
    a=text(repo/'tools/simulation/starcluster_research/auxiliary_integration_analysis.py')
    for x in ('role-marginal','ew-counterplay','pds-threat','generalist-cross-family','hardener-focus','reactorTuningEnabled'):
        req(x in a,f'analysis missing {x}')
    cli=text(repo/'tools/simulation/starcluster_research/cli.py'); req("auxiliary-integration-study" in cli,'CLI command')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo',required=True); a=ap.parse_args(); repo=Path(a.repo).resolve()
    try:
        validate_wrapper(repo); validate_cp137(repo); validate_frozen(repo); validate_catalog(repo); validate_study(repo); validate_code(repo)
        suite=unittest.defaultTestLoader.discover(str(repo/'tools/simulation/tests'),pattern='test_*.py'); n=count_suite(suite); req(n==234,f'Python discovery expected 234 got {n}')
        print('       CP138 preflight passed: wrapper dependencies verified; accepted CP137 evidence pinned; production C#/Concept/numerical authorities frozen; 35/35 AUX catalog reference coverage; Shield AUX vetting enforced; Reactor/power AUX frozen; 787 contexts / 1574 variants / 3,148,000 trials; 234 Python tests discovered.')
        return 0
    except Exception as e:
        print(f'CP138 preflight failure: {e}',file=sys.stderr); return 1
if __name__=='__main__': raise SystemExit(main())
