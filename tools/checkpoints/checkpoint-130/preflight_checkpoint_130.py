#!/usr/bin/env python3
from __future__ import annotations
import argparse, ast, hashlib, json, sys
from pathlib import Path

ROOTS_FROZEN = ("src/", "tests/", "docs/design/player_technology/")
RESEARCH_ROOT = "tools/simulation/starcluster_research/"
TEST_ROOT = "tools/simulation/tests/"


def req(v, m):
    if not v: raise AssertionError(m)

def text(p: Path):
    req(p.is_file(), f"missing {p}"); return p.read_text(encoding="utf-8-sig")

def js(p: Path): return json.loads(text(p))

def sha(p: Path):
    h=hashlib.sha256();
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def manifest(p: Path):
    out={}
    for line in text(p).splitlines():
        if line.strip():
            d,r=line.split('  ',1); out[r]=d
    return out

def validate_cp129_native(repo: Path):
    s=js(repo/'docs/validation/evidence/checkpoint-130/CP129_NATIVE_ACCEPTANCE_SUMMARY.json')
    req(s['checkpoint']==129 and s['failedGates']==[], 'accepted CP129 native summary')
    req(s['pythonTestsPassed']==177 and s['xunitPassed']==907 and s['scenarioRunnerSelfTestsPassed']==70 and s['researchParityPassed']==25, 'accepted CP129 native counts')
    req(s['substantiveTrials']==45665000 and s['substantiveTrialErrors']==0 and s['symmetryMismatches']==0, 'accepted CP129 substantive evidence')
    prov=js(repo/'docs/validation/evidence/checkpoint-130/accepted-cp129/CP129_NATIVE_RESULTS_ARCHIVE_PROVENANCE.json')
    req(prov['sha256']=='95c36ee5082096978fb80285f856045fcb9d123514e5c0f608e35b889ff65c0e', 'accepted CP129 result archive hash')

def validate_frozen_cp129(repo: Path) -> int:
    mp=repo/'docs/validation/evidence/checkpoint-129/CP129_REPOSITORY_SHA256SUMS.txt'
    req(sha(mp)=='bfd76d383ece24d18adecf8c08e7aa9c73564d86f3784aed0b840bc9daad4bf8','CP129 repository manifest hash')
    m=manifest(mp); checked=0
    for rel,digest in m.items():
        freeze = rel.startswith(ROOTS_FROZEN)
        freeze = freeze or (rel.startswith(RESEARCH_ROOT) and rel != RESEARCH_ROOT+'cli.py')
        freeze = freeze or (rel.startswith(TEST_ROOT))
        freeze = freeze or rel in {
            'docs/Star_Cluster_Game_Concept_v0.7s.docx',
            'tools/checkpoints/prepackage_repository_hygiene.py',
            'docs/archive/testing/pre-cp165-active/cp129_whole_ladder_pure_tl_sensitivity_study_v0_1.json',
        }
        if not freeze: continue
        p=repo/rel; req(p.is_file(),f'frozen CP129 file missing: {rel}'); req(sha(p)==digest,f'frozen CP129 file drift: {rel}'); checked+=1
    req(checked>600, f'frozen CP129 surface unexpectedly small: {checked}')
    return checked

def validate_stdlib(repo: Path) -> int:
    files=list((repo/'tools/simulation/starcluster_research').glob('*.py')) + list((repo/'tools/checkpoints/checkpoint-130').glob('*.py'))
    allowed=set(sys.stdlib_module_names)|{'starcluster_research'}
    bad=[]
    for p in files:
        tree=ast.parse(p.read_text(encoding='utf-8-sig'),filename=str(p))
        for n in ast.walk(tree):
            names=[]
            if isinstance(n,ast.Import): names=[x.name.split('.')[0] for x in n.names]
            elif isinstance(n,ast.ImportFrom) and n.level==0 and n.module: names=[n.module.split('.')[0]]
            for name in names:
                if name not in allowed: bad.append(f'{p.relative_to(repo)}:{name}')
    req(not bad,'third-party Python import(s): '+', '.join(bad[:8])); return len(files)

def validate_plan(repo: Path):
    sys.path.insert(0,str(repo/'tools/simulation'))
    from starcluster_research.missile_progression_analysis import build_plan
    study=repo/'docs/archive/testing/pre-cp165-active/cp130_missile_main_progression_and_family_viability_study_v0_1.json'
    p=build_plan(repo,study,None)['summary']
    req(p['failedGates']==[],'CP130 plan gates')
    req(p['legalBuilds']==9427 and p['generatedVariants']==240996 and p['substantiveTrials']==24099600,'CP130 plan counts')
    return p

def validate_docs(repo: Path):
    for rel in ('CHAT_README.md','README.md','docs/Prototype_TODO.md','docs/README.md','docs/validation/README.md','docs/archive/testing/pre-cp165-active/CP130_Missile_Main_Progression_And_Family_Viability_Study_v0_1.md'):
        t=text(repo/rel); req('130' in t or 'CP130' in t, f'{rel} not CP130-aware')
    baseline=list(__import__('csv').DictReader((repo/'docs/validation/evidence/checkpoint-130/accepted-cp129/same_tl_family_chart_baseline.csv').open(newline='',encoding='utf-8')))
    req(len(baseline)==9 and [int(r['tl']) for r in baseline]==list(range(1,10)),'accepted CP129 chart baseline')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo',required=True); a=ap.parse_args(); repo=Path(a.repo).resolve()
    try:
        d=js(repo/'tools/checkpoints/checkpoint-130/checkpoint_130_definition.json')
        req(d['checkpoint']==130 and d['expectedPythonTests']==183,'checkpoint definition')
        req(d['technologyValuesChanged'] is False and d['productionSourceChanged'] is False and d['scenarioDefinitionsChanged'] is False,'frozen production/value boundary')
        req(d['jobsConfigurable'] and d['minimumJobs']==1 and d['maximumJobs']==61,'Jobs contract')
        print('       Validating accepted CP129 native evidence...'); validate_cp129_native(repo)
        print('       Validating frozen CP129 production/numerical/pre-existing research surfaces...'); n=validate_frozen_cp129(repo); print(f'       Frozen CP129 files verified: {n}.')
        print('       Validating stdlib-only active Python surface...'); n=validate_stdlib(repo); print(f'       Active Python files inspected: {n}; no third-party packages.')
        print('       Reconstructing CP130 Missile progression plan...'); p=validate_plan(repo); print(f"       CP130 plan: {p['legalBuilds']} legal builds; {p['generatedVariants']} variants; {p['substantiveTrials']} substantive engagements.")
        print('       Validating CP130 documentation and accepted chart baseline...'); validate_docs(repo)
        print('       CP130 preflight passed: CP129 accepted; current Tech Table frozen; Missile candidates research-only; no legal mixed-TL ships.')
        return 0
    except Exception as e:
        print(f'CP130 preflight failure: {e}',file=sys.stderr); return 1
if __name__=='__main__': raise SystemExit(main())
