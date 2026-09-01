#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re, sys
from pathlib import Path

REPO_MANIFEST_SHA_CP113='0a772742bf720551c3fcdb47b4aa9f5c69e6b56302f0b8088ea4cf8d5c7701ee'
MATRIX_SHA='91cb29f7e1e0f792e5a2258b1ab0655fe9924c768f4d80b645269fae52384000'
REACTOR_SHA='ebed51fa16d0ee1c9721b55ca135eb81e23c321a8373dfcb826a1a096371e9a6'
EXCLUDED_PARTS={'.git','.vs','.vscode','.idea','out','bin','obj','TestResults','__pycache__'}
EXCLUDED_FILES={'.DS_Store','Thumbs.db'}
EXCLUDED_SUFFIXES={'.pyc','.user','.userosscache','.sln.docstates','.uid','.suo'}
ROOT_STALE=(re.compile(r'^CHECKPOINT_\d+[A-Za-z]*_SHA256SUMS\.txt$',re.I),re.compile(r'^SHA256SUMS(?:[-_].*)?\.txt$',re.I))

def req(v,msg):
    if not v: raise AssertionError(msg)
def sha(p:Path): return hashlib.sha256(p.read_bytes()).hexdigest()
def text(p:Path): req(p.is_file(),f'Missing {p}'); return p.read_text(encoding='utf-8-sig')
def js(p:Path): return json.loads(text(p))
def owned(rel:str)->bool:
    p=Path(rel)
    if any(x in EXCLUDED_PARTS for x in p.parts) or p.name in EXCLUDED_FILES:return False
    return not any(p.name.lower().endswith(s) for s in EXCLUDED_SUFFIXES)

def validate_hash_list(repo:Path,rel:str,expected:int):
    rows=[x for x in text(repo/rel).splitlines() if x.strip()]
    req(len(rows)==expected,f'{rel} count {len(rows)} != {expected}')
    for line in rows:
        m=re.fullmatch(r'([0-9a-f]{64})  (.+)',line); req(m is not None,f'bad hash row {line}')
        h,r=m.groups(); p=repo/r; req(p.is_file(),f'missing frozen {r}'); req(sha(p)==h,f'frozen drift {r}')

def validate_cp113(repo:Path):
    mf=repo/'docs/validation/evidence/checkpoint-113/REPOSITORY_MANIFEST_SHA256SUMS.txt'
    req(sha(mf)==REPO_MANIFEST_SHA_CP113,'CP113 archived manifest hash drift')
    n=js(repo/'docs/validation/evidence/checkpoint-113/CP113_NATIVE_ACCEPTANCE_SUMMARY.json')
    req(n.get('nativeAccepted') is True and n.get('pythonVersion')=='3.13.14','CP113 native acceptance provenance')
    req(n.get('repositoryOwnedFiles')==2281 and n.get('storyboardBeats')==214,'CP113 accepted scale')
    req(n.get('trials')==0 and n.get('numericalPromotion') is False,'CP113 architecture-only boundary')

def validate_root_hygiene(repo:Path):
    stale=[]
    for p in repo.iterdir():
        if p.is_file() and (p.name.lower() in {'repository_manifest.txt','manifest.sha256','sha256sums.txt'} or any(rx.match(p.name) for rx in ROOT_STALE)):
            stale.append(p.name)
    req(not stale,f'stale root checksum/manifest artifacts remain: {stale}')
    h=repo/'tools/checkpoints/prepackage_repository_hygiene.py'; req(h.is_file(),'missing reusable prepackage hygiene tool')
    src=text(h)
    req('docs' in src and 'validation' in src and 'evidence' in src and '--apply' in src and '--check' in src,'prepackage hygiene contract incomplete')

def validate_study(repo:Path,d:dict):
    sys.path.insert(0,str(repo/'tools/simulation'))
    from starcluster_research.payload_analysis import validate_study, build_variants
    from starcluster_research.study import load_json
    sp=repo/'docs/archive/testing/pre-cp165-active/payload_characteristic_space_study_v0_1.json'
    study=load_json(sp); errs=validate_study(study); req(not errs,f'payload study invalid: {errs}')
    req(study['checkpoint']==114 and study['acceptedBaseline']==113,'study identity')
    req(study['damageModel']=='layered_defense_hull_only' and study['internalDamageCriticalsSimulated'] is False,'damage boundary')
    req(study['automaticPromotion'] is False,'automatic promotion must remain false')
    req(study['trialsPerVariant']==d['expected']['nativeTrialsPerVariant'],'native trial count')
    req(len(study['payloadProfiles'])==d['expected']['payloadProfiles'],'payload profile count')
    ids={x['id'] for x in study['payloadProfiles']}
    for pid in ('gp-current','missile-shaped-a','missile-shaped-b','missile-shield-a4','missile-shield-b','missile-shield-c4','missile-adaptive-c2','missile-mixed-a4-gp','missile-mixed-b-gp','missile-mixed-c4-gp','missile-fusion-gp-b','missile-antimatter-gp-c','kinetic-smart-auto-plus5','kinetic-dense-b','kinetic-saturation-b'):
        req(pid in ids,f'missing payload profile {pid}')
    builds,variants=build_variants(repo,study)
    req(len(builds)==d['expected']['exactFillBuilds'],f'build count {len(builds)}')
    req(len(variants)==d['expected']['variants'],f'variant count {len(variants)}')
    m=sum(v.scenario_group=='missile_payload_characteristic' for v in variants)
    k=sum(v.scenario_group=='kinetic_ammunition_characteristic' for v in variants)
    req(m==d['expected']['missileVariants'] and k==d['expected']['kineticVariants'],f'family variants {m}/{k}')
    # Every generated build must fill its hull capacity exactly.
    for b in builds:
        req(b.used_space==b.capacity,f'non-exact-fill build {b.id}: used {b.used_space} / capacity {b.capacity}')

def validate_authoring(repo:Path,d:dict):
    root=repo/'docs/validation/evidence/checkpoint-114/authoring'
    a=js(root/'analysis.json')
    req(a.get('checkpoint')==114 and a.get('variants')==d['expected']['variants'],'authoring identity')
    req(a.get('trialsPerVariant')==d['expected']['authoringTrialsPerVariant'] and a.get('totalTrials')==d['expected']['authoringEngagements'],'authoring workload')
    req(a.get('failedGates')==[] and a.get('automaticPromotion') is False,'authoring gates/promotion')
    req(a.get('damageModel')=='layered_defense_hull_only' and a.get('internalDamageCriticalsSimulated') is False,'authoring damage scope')
    for f in ('summary.json','variants.csv','builds.csv','missile_payload_summary.csv','kinetic_ammunition_summary.csv'):
        req((root/f).is_file(),f'missing authoring evidence {f}')
    report=text(repo/'docs/validation/evidence/checkpoint-114/Payload_Characteristic_Space_Report_v1.md')
    for needle in ('GP maturation','anti-Shield','automatic compatible ammunition maturation','Saturation/submunition'):
        req(needle.lower() in report.lower(),f'report missing {needle}')

def validate_native(path:Path|None,d:dict):
    if path is None:return
    a=js(path/'analysis.json')
    req(a.get('checkpoint')==114 and a.get('variants')==d['expected']['variants'],'native result identity')
    req(a.get('trialsPerVariant')==d['expected']['nativeTrialsPerVariant'] and a.get('totalTrials')==d['expected']['nativeEngagements'],'native workload')
    req(a.get('failedGates')==[],'native failed gates')
    req(a.get('automaticPromotion') is False,'native automatic promotion')

def validate_docs(repo:Path):
    req((repo/'docs/validation/Checkpoint_114_Payload_Characteristic_Space_And_Prepackage_Hygiene.md').is_file(),'active CP114 runbook')
    req(not (repo/'docs/validation/Checkpoint_113_Weapon_Ammunition_Warhead_Architecture_And_Docs_Hygiene.md').exists(),'CP113 runbook still active')
    req((repo/'docs/validation/archive/Checkpoint_113_Weapon_Ammunition_Warhead_Architecture_And_Docs_Hygiene.md').is_file(),'CP113 runbook archive continuity')
    for rel in ('README.md','CHAT_README.md','docs/README.md','docs/validation/README.md','docs/design/testing/README.md'):
        req('114' in text(repo/rel),f'{rel} not updated for CP114')
    req('49 Python self-tests' in text(repo/'tools/simulation/README.md'),'simulation README self-test count')
    # CP114 is a research-consumer checkpoint; Concept and technology architecture remain CP113 authority.
    req((repo/'docs/Star_Cluster_Game_Concept_v0.7k.docx').is_file(),'Concept v0.7k missing')
    req(sha(repo/'docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_1.json')==MATRIX_SHA,'CP109 matrix drift')
    req(sha(repo/'docs/archive/player_technology/pre-cp165-active/power_reactor_calibration_profile_v0_1.json')==REACTOR_SHA,'CP110 Reactor drift')

def validate_json(repo:Path):
    count=0
    for p in repo.rglob('*.json'):
        rel=p.relative_to(repo).as_posix()
        if not owned(rel):continue
        try:json.loads(p.read_text(encoding='utf-8-sig'))
        except Exception as e:raise AssertionError(f'JSON parse {rel}: {e}')
        count+=1
    req(count>650,f'unexpected JSON count {count}')
    return count

def validate_manifest(repo:Path,expected_count:int):
    rel='docs/validation/evidence/checkpoint-114/CP114_REPOSITORY_SHA256SUMS.txt'; mf=repo/rel
    exp={}
    for line in text(mf).splitlines():
        if not line.strip():continue
        m=re.fullmatch(r'([0-9a-f]{64})  (.+)',line); req(m is not None,f'bad manifest row {line}')
        h,r=m.groups(); exp[r]=h
    req(len(exp)==expected_count,f'manifest count {len(exp)} != {expected_count}')
    actual=[]
    for p in repo.rglob('*'):
        if p.is_file():
            r=p.relative_to(repo).as_posix()
            if r!=rel and owned(r):actual.append(r)
    actual=sorted(actual); req(actual==sorted(exp),f'manifest path mismatch missing={sorted(set(exp)-set(actual))[:8]} extra={sorted(set(actual)-set(exp))[:8]}')
    for r in actual:req(sha(repo/r)==exp[r],f'manifest hash mismatch {r}')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo',required=True); ap.add_argument('--native-results'); a=ap.parse_args(); repo=Path(a.repo).resolve()
    try:
        print('       Validating accepted CP113 provenance and frozen production/numerical authority...')
        d=js(repo/'tools/checkpoints/checkpoint-114/checkpoint_114_definition.json')
        req(d['acceptedBaseline']==113 and d['automaticPromotion'] is False,'CP114 definition identity')
        validate_cp113(repo)
        validate_hash_list(repo,'docs/validation/evidence/checkpoint-114/CP113_FROZEN_CSHARP_PRODUCTION_TEST_SHA256SUMS.txt',d['expected']['frozenCSharpAndTests'])
        validate_hash_list(repo,'docs/validation/evidence/checkpoint-114/CP113_FROZEN_UNCHANGED_SIMULATION_SHA256SUMS.txt',d['expected']['frozenUnchangedSimulationFiles'])
        print('       Validating payload characteristic-space architecture, bounded evidence, and information boundary...')
        validate_study(repo,d); validate_authoring(repo,d); validate_native(Path(a.native_results).resolve() if a.native_results else None,d)
        print('       Validating documentation and automatic pre-package repository hygiene...')
        validate_root_hygiene(repo); validate_docs(repo); j=validate_json(repo)
        for rel in ('src/StarCluster.Game','src/StarCluster.Core'):
            py=list((repo/rel).rglob('*.py')); req(not py,f'Python leaked into production runtime: {py[:1]}')
        print('       Validating full repository manifest...')
        validate_manifest(repo,int(d['repositoryOwnedFiles']))
        print(f"       CP114 contract verified: {d['repositoryOwnedFiles']} repository-owned files; {j} JSON files parsed; {d['expected']['payloadProfiles']} payload profiles / {d['expected']['variants']} variants ({d['expected']['missileVariants']} Missile + {d['expected']['kineticVariants']} Kinetic); {d['expected']['authoringEngagements']} checked-in authoring engagements; no production promotion.")
        return 0
    except Exception as e:
        print(f'CP114 contract failure: {e}',file=sys.stderr); return 1
if __name__=='__main__': raise SystemExit(main())
