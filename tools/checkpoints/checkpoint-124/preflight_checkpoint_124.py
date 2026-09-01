#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, subprocess, sys, tempfile, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

CP123_NATIVE_SUMMARY_SHA='09a9fc8dd1e36ff80db7e256a8b4a20cc3cdb09477eede9a1982e26838fdc9a1'
FROZEN_PREFIXES=('src/','tests/StarCluster.Tests/')
FROZEN_CP123_AUTHORITIES=(
 'docs/archive/player_technology/pre-cp165-active/canonical_numerical_authority_v0_2.json',
 'docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_3.json',
 'docs/archive/player_technology/pre-cp165-active/technology_family_storyboard_v1_5.json',
 'docs/archive/player_technology/pre-cp165-active/technology_component_table_v0_5.json',
 'docs/archive/player_technology/pre-cp165-active/technology_idea_register_v1_6.json',
 'docs/archive/player_technology/pre-cp165-active/weapon_ammunition_missile_family_architecture_v0_4.json',
 'docs/archive/player_technology/pre-cp165-active/StarCluster_Revised_TL1_TL9_Technology_Component_Table_v0_5.xlsx',
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

def validate_cp123(repo:Path):
    raw=repo/'docs/validation/evidence/checkpoint-124/CP123_NATIVE_ACCEPTANCE_SUMMARY_ORIGINAL.json'
    req(raw.is_file() and sha(raw)==CP123_NATIVE_SUMMARY_SHA,'accepted CP123 native summary hash')
    s=js(repo/'docs/validation/evidence/checkpoint-124/CP124_ACCEPTED_CP123_NATIVE_SUMMARY.json')
    req(s['acceptedCheckpoint']==123 and s['sourceSummarySha256']==CP123_NATIVE_SUMMARY_SHA,'CP123 provenance identity')
    req(s['pythonTestsPassed']==124 and s['storyboardBeats']==218 and s['technologyTableEntries']==218,'CP123 accepted reference counts')
    req(s['numericalProfileFamilies']==20 and s['numericalProfileRows']==180 and s['damagePointScale']==2,'CP123 numerical authority')
    req(s['failedGates']==[] and s['balanceValidated'] is False and s['substantiveMonteCarloTrials']==0,'CP123 acceptance semantics')

def validate_frozen(repo:Path):
    old=manifest(repo/'docs/validation/evidence/checkpoint-123/CP123_REPOSITORY_SHA256SUMS.txt')
    for pref in FROZEN_PREFIXES:
        expected={r:h for r,h in old.items() if r.startswith(pref)}
        current=[]
        base=repo/pref.rstrip('/')
        if base.exists():
            current=[p.relative_to(repo).as_posix() for p in base.rglob('*') if p.is_file() and 'bin' not in p.parts and 'obj' not in p.parts]
        req(set(current)==set(expected),f'frozen production/scenario path drift for {pref}')
        for rel,h in expected.items(): req(sha(repo/rel)==h,f'frozen production/scenario drift: {rel}')
    for rel in FROZEN_CP123_AUTHORITIES:
        req(rel in old and sha(repo/rel)==old[rel],f'accepted CP123 authority drift: {rel}')
    archived=repo/'docs/archive/concepts/Star_Cluster_Game_Concept_v0.7n.docx'
    req('docs/Star_Cluster_Game_Concept_v0.7n.docx' in old and archived.is_file() and sha(archived)==old['docs/Star_Cluster_Game_Concept_v0.7n.docx'],'archived CP123 Concept not byte-preserved')

def docx_text(path:Path):
    with zipfile.ZipFile(path) as z:
        root=ET.fromstring(z.read('word/document.xml'))
        return ''.join((e.text or '') for e in root.iter() if e.tag.endswith('}t'))

def validate_docs(repo:Path):
    active=list((repo/'docs').glob('Star_Cluster_Game_Concept_v0.7*.docx'))
    req([p.name for p in active]==['Star_Cluster_Game_Concept_v0.7o.docx'],f'active Concept {active}')
    dt=docx_text(active[0]).lower()
    for phrase in ('checkpoint 124','executable technology and instrumentation foundation','9,427 legal builds','70 zero-weight pipeline','instrumentation acceptance gate','balance evidence'):
        req(phrase.lower() in dt,f'Concept missing {phrase}')
    with zipfile.ZipFile(active[0]) as z:
        header=''.join(z.read(n).decode('utf-8','ignore') for n in z.namelist() if n.startswith('word/header') and n.endswith('.xml'))
        core=z.read('docProps/core.xml').decode('utf-8','ignore')
    req('v0.7o' in header and 'Star Cluster Game Concept v0.7o' in core and '<cp:version>0.7o</cp:version>' in core,'Concept metadata')
    for rel in ('README.md','CHAT_README.md','tools/simulation/README.md','docs/archive/testing/pre-cp165-active/Telemetry_Instrumentation_Contract_v0_1.md','docs/archive/testing/pre-cp165-active/CP123_Executable_Baseline_And_Instrumentation_Foundation_v0_1.md'):
        t=text(repo/rel).lower(); req('124' in t or 'cp124' in t,f'active documentation not CP124-aware: {rel}')

def validate_foundation(repo:Path):
    sys.path.insert(0,str(repo/'tools/simulation'))
    from starcluster_research.baseline_foundation import BaselineCatalog, TELEMETRY_CONTRACT, enumerate_legal_builds, run_baseline_foundation, validate_study
    study=js(repo/'docs/archive/testing/pre-cp165-active/cp123_executable_baseline_instrumentation_foundation_v0_1.json')
    req(validate_study(study)==[],'CP124 study validation')
    c=BaselineCatalog(repo,study['sourceMatrix']); raw,builds=enumerate_legal_builds(c)
    req(len(c.profile_rows())==180 and raw==14112 and len(builds)==9427,'catalog/build counts')
    req(len(TELEMETRY_CONTRACT)==47,'telemetry contract count')
    static=js(repo/'docs/archive/testing/pre-cp165-active/telemetry_instrumentation_contract_v0_1.json')
    req(len(static['metrics'])==47 and {x['metric'] for x in static['metrics']}=={x['metric'] for x in TELEMETRY_CONTRACT},'static/runtime telemetry contract drift')
    with tempfile.TemporaryDirectory() as td:
        res=run_baseline_foundation(repo,repo/'docs/archive/testing/pre-cp165-active/cp123_executable_baseline_instrumentation_foundation_v0_1.json',Path(td))
        req(res['failedGates']==[] and res['legalBuilds']==9427 and res['pipelineSmokeVariants']==70 and res['instrumentationProbeCount']==9,'foundation deterministic run')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo',required=True); a=ap.parse_args(); repo=Path(a.repo).resolve()
    try:
        d=js(repo/'tools/checkpoints/checkpoint-124/checkpoint_124_definition.json'); req(d['checkpoint']==124 and d['acceptedReferenceBaseline']==123 and d['acceptedImplementationBaseline']==122,'definition')
        print('       Validating accepted CP123 provenance and frozen C#/scenario/reference surfaces...'); validate_cp123(repo); validate_frozen(repo)
        print('       Validating CP123 executable catalog, legal-build envelope, and telemetry acceptance contract...'); validate_foundation(repo)
        print('       Validating active documentation and Concept metadata...'); validate_docs(repo)
        print('       CP124 preflight: accepted CP123 reference verified; production/C# scenario surfaces frozen; 20x9 executable profiles; 14,112 raw / 9,427 legal same-TL builds; 70 zero-weight smoke variants; 47 raw telemetry metrics; 9 instrumentation probes; 0 substantive Monte Carlo trials.')
        return 0
    except Exception as e:
        print(f'CP124 preflight failure: {e}',file=sys.stderr); return 1
if __name__=='__main__': raise SystemExit(main())
