#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

CP124_ZIP_SHA='dea7c9fdf9c60a6d8f487acd267ea85acd043c98ac6fb78c3be23c35f819f139'
CP124_SUMMARY_SHA='e35d3359c6ffe182926e11d938879e41e8121c5a82c1e070e153702f79b5c140'
FROZEN_PREFIXES=('src/','tests/StarCluster.Tests/')
FROZEN_AUTHORITIES=(
 'docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_3.json',
 'docs/archive/player_technology/pre-cp165-active/technology_family_storyboard_v1_5.json',
 'docs/archive/player_technology/pre-cp165-active/technology_component_table_v0_5.json',
 'docs/archive/player_technology/pre-cp165-active/technology_idea_register_v1_6.json',
 'docs/archive/testing/pre-cp165-active/telemetry_instrumentation_contract_v0_1.json',
)

def req(v,msg):
    if not v: raise AssertionError(msg)
def text(p): req(p.is_file(),f'Missing {p}'); return p.read_text(encoding='utf-8-sig')
def js(p): return json.loads(text(p))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def manifest(p):
    out={}
    for line in text(p).splitlines():
        if line.strip(): h,r=line.split('  ',1); out[r]=h
    return out

def validate_cp124(repo:Path):
    z=repo/'docs/validation/evidence/checkpoint-125/CP124_NATIVE_RESULTS_ACCEPTED.zip'
    raw=repo/'docs/validation/evidence/checkpoint-125/CP124_NATIVE_ACCEPTANCE_SUMMARY_ORIGINAL.json'
    req(z.is_file() and sha(z)==CP124_ZIP_SHA,'accepted CP124 native archive hash')
    req(raw.is_file() and sha(raw)==CP124_SUMMARY_SHA,'accepted CP124 native summary hash')
    s=js(raw)
    req(s['checkpoint']==124 and s['pythonTestsPassed']==139 and s['researchParityPassed']==25,'CP124 accepted test identity')
    req(s['legalBuilds']==9427 and s['pipelineSmokeTrials']==70 and s['instrumentationProbes']==9 and s['telemetryContractMetrics']==47,'CP124 foundation counts')
    req(s['failedGates']==[] and s['substantiveMonteCarloTrials']==0 and s['balanceValidated'] is False,'CP124 acceptance semantics')
    a=js(repo/'docs/validation/evidence/checkpoint-125/CP125_ACCEPTED_CP124_NATIVE_SUMMARY.json')
    req(a['acceptedCheckpoint']==124 and a['sourceArchiveSha256']==CP124_ZIP_SHA and a['sourceSummarySha256']==CP124_SUMMARY_SHA,'CP124 provenance summary')

def validate_frozen(repo:Path):
    old=manifest(repo/'docs/validation/evidence/checkpoint-124/CP124_REPOSITORY_SHA256SUMS.txt')
    for pref in FROZEN_PREFIXES:
        expected={r:h for r,h in old.items() if r.startswith(pref)}
        current=[]; base=repo/pref.rstrip('/')
        if base.exists(): current=[p.relative_to(repo).as_posix() for p in base.rglob('*') if p.is_file() and 'bin' not in p.parts and 'obj' not in p.parts]
        req(set(current)==set(expected),f'frozen path drift {pref}')
        for rel,h in expected.items(): req(sha(repo/rel)==h,f'frozen source drift: {rel}')
    for rel in FROZEN_AUTHORITIES:
        req(rel in old and sha(repo/rel)==old[rel],f'accepted authority drift: {rel}')

def docx_text(path:Path):
    with zipfile.ZipFile(path) as z:
        root=ET.fromstring(z.read('word/document.xml'))
        return ''.join((e.text or '') for e in root.iter() if e.tag.endswith('}t'))

def validate_docs(repo:Path):
    active=list((repo/'docs').glob('Star_Cluster_Game_Concept_v0.7*.docx'))
    req([p.name for p in active]==['Star_Cluster_Game_Concept_v0.7p.docx'],f'active Concept {active}')
    dt=docx_text(active[0]).lower()
    for phrase in ('checkpoint 125','pure-tl whole-ladder','56,027,200','280,136','mixed-tl ships','balance signals are not blocking gates'):
        req(phrase.lower() in dt,f'Concept missing {phrase}')
    with zipfile.ZipFile(active[0]) as z:
        header=''.join(z.read(n).decode('utf-8','ignore') for n in z.namelist() if n.startswith('word/header') and n.endswith('.xml'))
        core=z.read('docProps/core.xml').decode('utf-8','ignore')
    req('v0.7p' in header and 'Star Cluster Game Concept v0.7p' in core and '<cp:version>0.7p</cp:version>' in core,'Concept metadata')
    for rel in ('README.md','CHAT_README.md','tools/simulation/README.md','docs/design/testing/README.md','docs/design/player_technology/README.md','docs/archive/testing/pre-cp165-active/CP125_Pure_TL_Whole_Ladder_Integrated_Progression_Study_v0_1.md','docs/validation/Checkpoint_125_Pure_TL_Whole_Ladder_Integrated_Progression_Study.md'):
        t=text(repo/rel).lower(); req('125' in t or 'cp125' in t,f'active documentation not CP125-aware: {rel}')

def validate_plan(repo:Path):
    sys.path.insert(0,str(repo/'tools/simulation'))
    from starcluster_research.whole_ladder_analysis import build_plan, validate_study
    study=js(repo/'docs/archive/testing/pre-cp165-active/cp125_pure_tl_whole_ladder_integrated_progression_study_v0_1.json')
    req(validate_study(study)==[],'CP125 study validation')
    res=build_plan(repo,repo/'docs/archive/testing/pre-cp165-active/cp125_pure_tl_whole_ladder_integrated_progression_study_v0_1.json')['summary']
    req(res['failedGates']==[],'CP125 plan structural gates')
    req(res['legalBuilds']==9427 and res['basePairings']==70034 and res['generatedVariants']==280136,'CP125 plan counts')
    req(res['buildOpponentTlCoverage']==84843 and res['plannedSubstantiveTrials']==56027200,'CP125 coverage/workload')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo',required=True); a=ap.parse_args(); repo=Path(a.repo).resolve()
    try:
        d=js(repo/'tools/checkpoints/checkpoint-125/checkpoint_125_definition.json'); req(d['checkpoint']==125 and d['acceptedInstrumentationBaseline']==124,'definition')
        print('       Validating accepted CP124 native provenance and frozen implementation/reference surfaces...'); validate_cp124(repo); validate_frozen(repo)
        print('       Validating CP125 pure-TL pairing plan, population weights, and all-build/all-opponent-TL coverage...'); validate_plan(repo)
        print('       Validating active documentation and Concept metadata...'); validate_docs(repo)
        print('       CP125 preflight: accepted CP124 instrumentation foundation verified; 9,427 pure-TL legal builds; 44,429,451-pair population; 70,034 weighted base pairings; 280,136 symmetry variants; 84,843 build/opponent-TL coverage; 56,027,200 planned substantive trials; no mixed-TL ships.')
        return 0
    except Exception as e:
        print(f'CP125 preflight failure: {e}',file=sys.stderr); return 1
if __name__=='__main__': raise SystemExit(main())
