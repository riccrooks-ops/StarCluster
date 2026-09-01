#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, hashlib, json, re, sys
from pathlib import Path

MATRIX_SHA='91cb29f7e1e0f792e5a2258b1ab0655fe9924c768f4d80b645269fae52384000'
REACTOR_SHA='ebed51fa16d0ee1c9721b55ca135eb81e23c321a8373dfcb826a1a096371e9a6'
CP114_STUDY_SHA='f88f8079d0fb2429837f7e880ce09194d622f49e00b2dede1fd923187bf080a9'
CP114_PAYLOAD_ANALYSIS_SHA='8ff46ff94b4e51a48d0be13c0301b466aca8cb1eb207e8df0c9f12322b7d1438'
CP115_STUDY_SHA='8c45cf0d3666231471c43119c42270c9a5f5cabeb5c95450a9b9a1f654bbd10b'
EXCLUDED_PARTS={'.git','.vs','.vscode','.idea','out','bin','obj','TestResults','__pycache__'}
EXCLUDED_FILES={'.DS_Store','Thumbs.db'}
EXCLUDED_SUFFIXES={'.pyc','.user','.userosscache','.sln.docstates','.uid','.suo'}
ROOT_STALE=(re.compile(r'^CHECKPOINT_\d+[A-Za-z]*_SHA256SUMS\.txt$',re.I),re.compile(r'^SHA256SUMS(?:[-_].*)?\.txt$',re.I))

def req(v,msg):
    if not v: raise AssertionError(msg)
def sha(p:Path): return hashlib.sha256(p.read_bytes()).hexdigest()
def text(p:Path): req(p.is_file(),f'Missing {p}'); return p.read_text(encoding='utf-8-sig')
def js(p:Path): return json.loads(text(p))
def owned(rel:str):
    p=Path(rel)
    return not any(x in EXCLUDED_PARTS for x in p.parts) and p.name not in EXCLUDED_FILES and p.suffix.lower() not in EXCLUDED_SUFFIXES

def validate_hash_list(repo:Path,rel:str,expected:int):
    rows=[]
    for line in text(repo/rel).splitlines():
        if not line.strip(): continue
        m=re.fullmatch(r'([0-9a-f]{64})  (.+)',line); req(m is not None,f'bad hash-list row {rel}: {line}')
        h,r=m.groups(); rows.append((h,r)); req((repo/r).is_file(),f'hash-list missing {r}'); req(sha(repo/r)==h,f'hash-list drift {r}')
    req(len(rows)==expected,f'{rel} count {len(rows)} != {expected}')

def validate_accepted_baseline(repo:Path,e:dict):
    s=js(repo/'docs/validation/evidence/checkpoint-115a/CP115A_NATIVE_ACCEPTANCE_SUMMARY.json')
    req(s.get('checkpoint')=='115a' and s.get('nativeAccepted') is True,'CP115a native acceptance summary invalid')
    req(s.get('variants')==4064 and s.get('totalTrials')==8128000 and s.get('failedGates')==[],'CP115a native workload/gates invalid')
    req(s.get('adaptivePairRows')==384 and s.get('adaptivePairRowsWithSwitches')==0,'CP115a adaptive telemetry drift')
    native=repo/'docs/validation/evidence/checkpoint-115a/native-results/native-weapon-family-study/analysis.json'
    n=js(native); req(n.get('variants')==4064 and n.get('totalTrials')==8128000 and n.get('failedGates')==[],'embedded CP115a native analysis invalid')
    req(sha(repo/'docs/archive/testing/pre-cp165-active/weapon_family_payload_study_v0_2.json')==CP115_STUDY_SHA,'CP115 study drift')
    req(sha(repo/'docs/archive/testing/pre-cp165-active/payload_characteristic_space_study_v0_1.json')==CP114_STUDY_SHA,'CP114 study drift')
    req(sha(repo/'tools/simulation/starcluster_research/payload_analysis.py')==CP114_PAYLOAD_ANALYSIS_SHA,'CP114 payload consumer drift')
    validate_hash_list(repo,'docs/validation/evidence/checkpoint-115/CP114_FROZEN_CSHARP_PRODUCTION_TEST_SHA256SUMS.txt',e['frozenCSharpAndTests'])
    validate_hash_list(repo,'docs/validation/evidence/checkpoint-115/CP114_FROZEN_PRIOR_SIMULATION_SHA256SUMS.txt',e['frozenCp114PriorSimulationFiles'])

def validate_study(repo:Path,e:dict):
    doc=js(repo/'docs/archive/testing/pre-cp165-active/warhead_role_generation_study_v0_1.json')
    req(doc.get('checkpoint')==116 and doc.get('acceptedBaseline')=='115a','CP116 study identity')
    req(doc.get('trialsPerVariant')==e['nativeTrialsPerVariant'] and doc.get('authoringTrialsPerVariant')==e['authoringTrialsPerVariant'],'CP116 trial workload drift')
    req(doc.get('automaticPromotion') is False and doc.get('damageModel')=='layered_defense_hull_only' and doc.get('internalDamageCriticalsSimulated') is False,'CP116 scope drift')
    req(len(doc.get('missileProfiles',[]))==e['missileProfiles'],'Missile profile count')
    req(len(doc.get('kineticProfiles',[]))==e['kineticProfiles'],'Kinetic profile count')
    req(len(doc.get('targetFixtures',[]))==e['targetFixtures'],'target fixture count')
    req(sum(x.get('classification')=='controlled_fixture' for x in doc['targetFixtures'])==e['controlledFixtures'],'controlled fixture count')
    base=doc['gpBaselinePenetration']; req((base['spen'],base['apen'])==(1,2),'GP baseline penetration drift')
    profiles={p['id']:p for p in doc['missileProfiles']}
    pure={p for ids in doc['pureGpByTl'].values() for p in ids}; req(len(pure)==e['pureGpProfiles'],'pure GP count')
    for pid in pure:
        p=profiles[pid]; req(p.get('profileClass')=='gp_pure_yield' and (p.get('spen'),p.get('apen'))==(1,2),f'pure GP specialization leakage {pid}')
    bundled=set(doc['penetrationBundledGpByTl'].values()); req(len(bundled)==e['bundledPenetrationControls'],'bundled control count')
    gen=[p for p in doc['missileProfiles'] if str(p.get('profileClass','')).startswith('specialist_')]; req(len(gen)==e['generationalSpecialists'],'generational specialist count')
    sys.path.insert(0,str(repo/'tools/simulation'))
    from starcluster_research.role_generation_analysis import validate_study, build_variants, _packet_probe_rows
    errs=validate_study(doc); req(not errs,f'CP116 study validation errors: {errs}')
    builds,variants=build_variants(repo,doc)
    req(len(builds)==e['exactFillBuilds'],f'build count {len(builds)}')
    req(len(variants)==e['variants'],f'variant count {len(variants)}')
    counts={k:sum(v.scenario_group==k for v in variants) for k in ('missile_family_characteristic','kinetic_family_characteristic','energy_family_reference')}
    req(counts['missile_family_characteristic']==e['missileVariants'],'Missile variant count')
    req(counts['kinetic_family_characteristic']==e['kineticVariants'],'Kinetic variant count')
    req(counts['energy_family_reference']==e['energyReferenceVariants'],'Energy variant count')
    for b in builds: req(b.used_space==b.capacity,f'non-exact-fill build {b.id}: {b.used_space}/{b.capacity}')
    probe=_packet_probe_rows(repo,doc); req(len(probe)==e['packetLayerProbeRows'],f'packet probe count {len(probe)}')

def validate_authoring(repo:Path,e:dict):
    root=repo/'docs/validation/evidence/checkpoint-116/authoring'; a=js(root/'analysis.json')
    req(a.get('checkpoint')==116 and a.get('variants')==e['variants'],'authoring identity/variant count')
    req(a.get('trialsPerVariant')==e['authoringTrialsPerVariant'] and a.get('totalTrials')==e['authoringEngagements'],'authoring workload')
    req(a.get('failedGates')==[] and a.get('automaticPromotion') is False,'authoring gates/promotion')
    req(a.get('packetLayerProbeRows')==e['packetLayerProbeRows'],'authoring probe rows')
    req(a.get('adaptivePairRows')==e['authoringAdaptiveRows'] and a.get('adaptivePairRowsWithSwitches')==e['authoringAdaptiveRowsWithSwitches'],'authoring adaptive telemetry')
    rows=list(csv.DictReader((root/'variants.csv').open(encoding='utf-8-sig',newline=''))); req(len(rows)==e['variants'],'authoring variants.csv count')
    findings=js(repo/'docs/validation/evidence/checkpoint-116/CP116_AUTHORING_FINDINGS.json')
    req(findings.get('variants')==e['variants'] and findings.get('totalTrials')==e['authoringEngagements'] and findings.get('failedGates')==[],'authoring findings summary')

def validate_native(path:Path|None,e:dict):
    if path is None:return
    a=js(path/'analysis.json')
    req(a.get('checkpoint')==116 and a.get('variants')==e['variants'],'native CP116 identity')
    req(a.get('trialsPerVariant')==e['nativeTrialsPerVariant'] and a.get('totalTrials')==e['nativeEngagements'],'native CP116 workload')
    req(a.get('failedGates')==[] and a.get('automaticPromotion') is False,'native CP116 gates/promotion')
    req(a.get('packetLayerProbeRows')==e['packetLayerProbeRows'],'native packet probe rows')

def validate_docs(repo:Path):
    for rel in (
      'docs/validation/Checkpoint_116_Warhead_Role_Orthogonality_And_Generational_Scaling.md',
      'docs/archive/testing/pre-cp165-active/Warhead_Role_Orthogonality_And_Generational_Scaling_Study_Architecture_v0_1.md',
      'docs/archive/player_technology/pre-cp165-active/Weapon_Ammunition_And_Warhead_Architecture_v0_2.md',
      'docs/validation/evidence/checkpoint-116/Warhead_Role_Orthogonality_And_Generational_Scaling_Report_v1.md'):
        req((repo/rel).is_file(),f'missing CP116 doc {rel}')
    for rel in ('README.md','CHAT_README.md','docs/README.md','docs/validation/README.md','docs/design/testing/README.md','tools/simulation/README.md'):
        t=text(repo/rel).lower(); req('116' in t,f'{rel} not updated for CP116')
    req((repo/'docs/Star_Cluster_Game_Concept_v0.7k.docx').is_file(),'Concept v0.7k missing')
    req(sha(repo/'docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_1.json')==MATRIX_SHA,'CP109 matrix drift')
    req(sha(repo/'docs/archive/player_technology/pre-cp165-active/power_reactor_calibration_profile_v0_1.json')==REACTOR_SHA,'CP110 Reactor drift')

def validate_root_hygiene(repo:Path):
    stale=[]
    for p in repo.iterdir():
        if p.is_file() and (p.name.lower() in {'repository_manifest.txt','manifest.sha256','sha256sums.txt'} or any(rx.match(p.name) for rx in ROOT_STALE)): stale.append(p.name)
    req(not stale,f'stale root checksum/manifest artifacts remain: {stale}')
    req((repo/'tools/checkpoints/prepackage_repository_hygiene.py').is_file(),'missing reusable prepackage hygiene tool')

def validate_json(repo:Path):
    count=0
    for p in repo.rglob('*.json'):
        r=p.relative_to(repo).as_posix()
        if not owned(r):continue
        try: json.loads(p.read_text(encoding='utf-8-sig'))
        except Exception as exc: raise AssertionError(f'JSON parse {r}: {exc}')
        count+=1
    req(count>670,f'unexpected JSON count {count}'); return count

def validate_manifest(repo:Path,expected_count:int):
    rel='docs/validation/evidence/checkpoint-116/CP116_REPOSITORY_SHA256SUMS.txt'; mf=repo/rel
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
            if r!=rel and owned(r): actual.append(r)
    actual=sorted(actual); req(actual==sorted(exp),f'manifest path mismatch missing={sorted(set(exp)-set(actual))[:8]} extra={sorted(set(actual)-set(exp))[:8]}')
    for r in actual:req(sha(repo/r)==exp[r],f'manifest hash mismatch {r}')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo',required=True); ap.add_argument('--native-results'); a=ap.parse_args(); repo=Path(a.repo).resolve()
    try:
        d=js(repo/'tools/checkpoints/checkpoint-116/checkpoint_116_definition.json'); e=d['expected']
        req(d.get('checkpoint')==116 and d.get('acceptedBaseline')=='115a','CP116 definition identity')
        req(d.get('automaticPromotion') is False and d.get('productionSourceChanged') is False and d.get('numericalMatrixChanged') is False and d.get('conceptChanged') is False,'CP116 scope drift')
        print('       Validating accepted CP115a native provenance and frozen production/numerical surfaces...')
        validate_accepted_baseline(repo,e)
        print('       Validating CP116 role-orthogonality study, exact-fill population, and bounded evidence...')
        validate_study(repo,e); validate_authoring(repo,e); validate_native(Path(a.native_results).resolve() if a.native_results else None,e)
        print('       Validating documentation, root hygiene, JSON, and production-language boundary...')
        validate_root_hygiene(repo); validate_docs(repo); j=validate_json(repo)
        for rel in ('src/StarCluster.Game','src/StarCluster.Core'):
            py=list((repo/rel).rglob('*.py')); req(not py,f'Python leaked into production runtime: {py[:1]}')
        print('       Validating full repository manifest...')
        validate_manifest(repo,int(d['repositoryOwnedFiles']))
        print(f"       CP116 contract verified: {d['repositoryOwnedFiles']} repository-owned files; {j} JSON files parsed; 32 Missile + 15 Kinetic profiles; 2,976 variants; 74,400 checked-in authoring engagements; GP yield/penetration axes separated; no production promotion.")
        return 0
    except Exception as exc:
        print(f'CP116 contract failure: {exc}',file=sys.stderr); return 1
if __name__=='__main__': raise SystemExit(main())
