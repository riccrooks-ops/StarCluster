#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re, sys
from pathlib import Path

REPO_MANIFEST_SHA_CP114='484614c0daf20451b1cc5406d58934130c259a39a310d2da4db1c0856b099507'
MATRIX_SHA='91cb29f7e1e0f792e5a2258b1ab0655fe9924c768f4d80b645269fae52384000'
REACTOR_SHA='ebed51fa16d0ee1c9721b55ca135eb81e23c321a8373dfcb826a1a096371e9a6'
CP114_STUDY_SHA='f88f8079d0fb2429837f7e880ce09194d622f49e00b2dede1fd923187bf080a9'
CP114_PAYLOAD_ANALYSIS_SHA='8ff46ff94b4e51a48d0be13c0301b466aca8cb1eb207e8df0c9f12322b7d1438'
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

def validate_cp114(repo:Path,d:dict):
    mf=repo/'docs/validation/evidence/checkpoint-114/CP114_REPOSITORY_SHA256SUMS.txt'
    req(sha(mf)==REPO_MANIFEST_SHA_CP114,'CP114 archived manifest hash drift')
    n=js(repo/'docs/validation/evidence/checkpoint-114/CP114_NATIVE_ACCEPTANCE_SUMMARY.json')
    req(n.get('nativeAccepted') is True and n.get('pythonVersion')=='3.13.14','CP114 native acceptance provenance')
    req(n.get('variants')==3184 and n.get('totalTrials')==6368000 and n.get('failedGates')==[],'CP114 native workload/gates')
    req(n.get('automaticPromotion') is False and n.get('internalDamageCriticalsSimulated') is False,'CP114 promotion/damage boundary')
    req(sha(repo/'docs/archive/testing/pre-cp165-active/payload_characteristic_space_study_v0_1.json')==CP114_STUDY_SHA,'CP114 study drift')
    req(sha(repo/'tools/simulation/starcluster_research/payload_analysis.py')==CP114_PAYLOAD_ANALYSIS_SHA,'CP114 payload consumer drift')

def validate_root_hygiene(repo:Path):
    stale=[]
    for p in repo.iterdir():
        if p.is_file() and (p.name.lower() in {'repository_manifest.txt','manifest.sha256','sha256sums.txt'} or any(rx.match(p.name) for rx in ROOT_STALE)):
            stale.append(p.name)
    req(not stale,f'stale root checksum/manifest artifacts remain: {stale}')
    h=repo/'tools/checkpoints/prepackage_repository_hygiene.py'; req(h.is_file(),'missing reusable prepackage hygiene tool')
    src=text(h); req('--apply' in src and '--check' in src and 'validation' in src and 'evidence' in src,'prepackage hygiene contract incomplete')

def validate_study(repo:Path,d:dict):
    sys.path.insert(0,str(repo/'tools/simulation'))
    from starcluster_research.weapon_family_analysis import validate_study, build_variants
    from starcluster_research.study import load_json
    sp=repo/'docs/archive/testing/pre-cp165-active/weapon_family_payload_study_v0_2.json'
    study=load_json(sp); errs=validate_study(study); req(not errs,f'weapon-family study invalid: {errs}')
    e=d['expected']
    req(study['checkpoint']==115 and study['acceptedBaseline']==114,'study identity')
    req(study['damageModel']=='layered_defense_hull_only' and study['internalDamageCriticalsSimulated'] is False,'damage boundary')
    req(study['automaticPromotion'] is False,'automatic promotion must remain false')
    req(study['trialsPerVariant']==e['nativeTrialsPerVariant'] and study['authoringTrialsPerVariant']==e['authoringTrialsPerVariant'],'trial counts')
    req(len(study['missileProfiles'])==e['missileProfiles'] and len(study['kineticProfiles'])==e['kineticProfiles'],'profile counts')
    req(len(study['targetFixtures'])==e['targetFixtures'],'fixture count')
    controlled=sum(1 for x in study['targetFixtures'] if str(x.get('classification','')).startswith('controlled'))
    req(controlled==e['controlledFixtures'],f'controlled fixture count {controlled}')
    mids={x['id'] for x in study['missileProfiles']}; kids={x['id'] for x in study['kineticProfiles']}
    for pid in ('gp-current','missile-fission-gp-c','missile-fusion-gp-c','missile-antimatter-gp-c','missile-shaped','missile-shield-pressure','missile-shield-recharge','missile-shield-armor'):
        req(pid in mids,f'missing Missile profile {pid}')
    for pid in ('gp-current','kinetic-smart-plus10','kinetic-dense-b','kinetic-saturation-b','kinetic-tandem-b','kinetic-tandem-b-reverse'):
        req(pid in kids,f'missing Kinetic profile {pid}')
    builds,variants=build_variants(repo,study)
    req(len(builds)==e['exactFillBuilds'],f'build count {len(builds)}')
    req(len(variants)==e['variants'],f'variant count {len(variants)}')
    counts={k:sum(v.scenario_group==k for v in variants) for k in ('missile_family_characteristic','kinetic_family_characteristic','energy_family_reference')}
    req(counts['missile_family_characteristic']==e['missileVariants'],'Missile variant count')
    req(counts['kinetic_family_characteristic']==e['kineticVariants'],'Kinetic variant count')
    req(counts['energy_family_reference']==e['energyReferenceVariants'],'Energy reference variant count')
    for b in builds:req(b.used_space==b.capacity,f'non-exact-fill build {b.id}: {b.used_space}/{b.capacity}')

def validate_authoring(repo:Path,d:dict):
    root=repo/'docs/validation/evidence/checkpoint-115/authoring'; e=d['expected']
    a=js(root/'analysis.json')
    req(a.get('checkpoint')==115 and a.get('variants')==e['variants'],'authoring identity')
    req(a.get('trialsPerVariant')==e['authoringTrialsPerVariant'] and a.get('totalTrials')==e['authoringEngagements'],'authoring workload')
    req(a.get('failedGates')==[] and a.get('automaticPromotion') is False,'authoring gates/promotion')
    req(a.get('targetFixtureCount')==e['targetFixtures'] and a.get('controlledFixtureCount')==e['controlledFixtures'],'authoring fixture counts')
    vc=a.get('variantCounts',{})
    req(vc.get('missile_family_characteristic')==e['missileVariants'] and vc.get('kinetic_family_characteristic')==e['kineticVariants'] and vc.get('energy_family_reference')==e['energyReferenceVariants'],'authoring group counts')
    for f in ('summary.json','variants.csv','builds.csv','target_fixtures.csv','missile_family_summary.csv','kinetic_family_summary.csv','energy_reference_summary.csv'):
        req((root/f).is_file(),f'missing authoring evidence {f}')
    report=text(repo/'docs/validation/evidence/checkpoint-115/Weapon_Family_Payload_Characteristic_Space_Report_v1.md').lower()
    for needle in ('energetic gp maturation','accuracy-enhanced submunitions','tandem packets','family-identity'):
        req(needle in report,f'report missing {needle}')
    req((repo/'docs/validation/evidence/checkpoint-115/StarCluster_CP115_Weapon_Family_Payload_Characteristic_Space_v0_1.xlsx').is_file(),'missing CP115 workbook')

def validate_native(path:Path|None,d:dict):
    if path is None:return
    e=d['expected']; a=js(path/'analysis.json')
    req(a.get('checkpoint')==115 and a.get('variants')==e['variants'],'native identity')
    req(a.get('trialsPerVariant')==e['nativeTrialsPerVariant'] and a.get('totalTrials')==e['nativeEngagements'],'native workload')
    req(a.get('failedGates')==[] and a.get('automaticPromotion') is False,'native gates/promotion')
    req(a.get('targetFixtureCount')==e['targetFixtures'] and a.get('controlledFixtureCount')==e['controlledFixtures'],'native fixture counts')

def validate_docs(repo:Path):
    req((repo/'docs/validation/Checkpoint_115_Weapon_Family_Payload_Characteristic_Space_Refinement.md').is_file(),'active CP115 runbook')
    req(not (repo/'docs/validation/Checkpoint_114_Payload_Characteristic_Space_And_Prepackage_Hygiene.md').exists(),'CP114 runbook still active')
    req((repo/'docs/validation/archive/Checkpoint_114_Payload_Characteristic_Space_And_Prepackage_Hygiene.md').is_file(),'CP114 runbook archive continuity')
    for rel in ('README.md','CHAT_README.md','docs/README.md','docs/validation/README.md','docs/design/testing/README.md'):
        req('115' in text(repo/rel),f'{rel} not updated for CP115')
    sr=text(repo/'tools/simulation/README.md'); req('64 Python self-tests' in sr and 'weapon-family-study' in sr,'simulation README CP115 boundary')
    req((repo/'docs/Star_Cluster_Game_Concept_v0.7k.docx').is_file(),'Concept v0.7k missing')
    req(sha(repo/'docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_1.json')==MATRIX_SHA,'CP109 matrix drift')
    req(sha(repo/'docs/archive/player_technology/pre-cp165-active/power_reactor_calibration_profile_v0_1.json')==REACTOR_SHA,'CP110 Reactor drift')

def validate_json(repo:Path):
    count=0
    for p in repo.rglob('*.json'):
        rel=p.relative_to(repo).as_posix()
        if not owned(rel):continue
        try:json.loads(p.read_text(encoding='utf-8-sig'))
        except Exception as exc:raise AssertionError(f'JSON parse {rel}: {exc}')
        count+=1
    req(count>650,f'unexpected JSON count {count}')
    return count

def validate_manifest(repo:Path,expected_count:int):
    rel='docs/validation/evidence/checkpoint-115/CP115_REPOSITORY_SHA256SUMS.txt'; mf=repo/rel
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
        d=js(repo/'tools/checkpoints/checkpoint-115/checkpoint_115_definition.json'); e=d['expected']
        req(d['acceptedBaseline']==114 and d['automaticPromotion'] is False,'CP115 definition identity')
        print('       Validating accepted CP114 native provenance and frozen executable/numerical surfaces...')
        validate_cp114(repo,d)
        validate_hash_list(repo,'docs/validation/evidence/checkpoint-115/CP114_FROZEN_CSHARP_PRODUCTION_TEST_SHA256SUMS.txt',e['frozenCSharpAndTests'])
        validate_hash_list(repo,'docs/validation/evidence/checkpoint-115/CP114_FROZEN_PRIOR_SIMULATION_SHA256SUMS.txt',e['frozenPriorSimulationFiles'])
        print('       Validating family-characteristic study, bounded evidence, and information/damage boundaries...')
        validate_study(repo,d); validate_authoring(repo,d); validate_native(Path(a.native_results).resolve() if a.native_results else None,d)
        print('       Validating documentation and automatic pre-package repository hygiene...')
        validate_root_hygiene(repo); validate_docs(repo); j=validate_json(repo)
        for rel in ('src/StarCluster.Game','src/StarCluster.Core'):
            py=list((repo/rel).rglob('*.py')); req(not py,f'Python leaked into production runtime: {py[:1]}')
        print('       Validating full repository manifest...')
        validate_manifest(repo,int(d['repositoryOwnedFiles']))
        print(f"       CP115 contract verified: {d['repositoryOwnedFiles']} repository-owned files; {j} JSON files parsed; {e['missileProfiles']} Missile + {e['kineticProfiles']} Kinetic profiles; {e['targetFixtures']} target fixtures ({e['controlledFixtures']} controlled); {e['variants']} variants ({e['missileVariants']} Missile + {e['kineticVariants']} Kinetic + {e['energyReferenceVariants']} Energy reference); {e['authoringEngagements']} checked-in authoring engagements; no production promotion.")
        return 0
    except Exception as exc:
        print(f'CP115 contract failure: {exc}',file=sys.stderr); return 1
if __name__=='__main__': raise SystemExit(main())
