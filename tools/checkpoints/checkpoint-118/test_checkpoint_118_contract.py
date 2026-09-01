#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, hashlib, json, re, sys, zipfile
from pathlib import Path

MATRIX_SHA='91cb29f7e1e0f792e5a2258b1ab0655fe9924c768f4d80b645269fae52384000'
REACTOR_SHA='ebed51fa16d0ee1c9721b55ca135eb81e23c321a8373dfcb826a1a096371e9a6'
CP117_NATIVE_ZIP_SHA='65f4cb224c5feba4d7389b5b5b0a11dc743254d35bbd5d5df44ab9900ac34bf0'
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

def hashlist(repo:Path,rel:str,expected:int):
    rows=[]
    for line in text(repo/rel).splitlines():
        if not line.strip(): continue
        m=re.fullmatch(r'([0-9a-f]{64})  (.+)',line); req(m is not None,f'bad hash-list row in {rel}: {line}')
        rows.append(m.groups())
    req(len(rows)==expected,f'{rel} count {len(rows)} != {expected}')
    for h,r in rows:
        req((repo/r).is_file(),f'frozen file missing {r}')
        req(sha(repo/r)==h,f'frozen file drift {r}')

def csv_rows(path:Path):
    req(path.is_file(),f'Missing {path}')
    with path.open('r',encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))

def validate_baseline(repo:Path,e:dict):
    summ=js(repo/'docs/validation/evidence/checkpoint-118/CP118_ACCEPTED_CP117_NATIVE_SUMMARY.json')
    req(summ.get('checkpoint')==117 and summ.get('acceptedForCp118') is True,'CP117 accepted-native summary identity')
    req(summ.get('sourceArchiveSha256')==CP117_NATIVE_ZIP_SHA,'CP117 native archive declared SHA drift')
    zpath=repo/'docs/validation/evidence/checkpoint-118/checkpoint-117-native-results.zip'
    req(sha(zpath)==CP117_NATIVE_ZIP_SHA,'CP117 native archive bytes drift')
    with zipfile.ZipFile(zpath) as z:
        names=z.namelist(); p=next((n for n in names if n.endswith('/parity/summary.json')),None)
        req(p is not None,'CP117 native parity summary missing')
        parity=json.loads(z.read(p).decode('utf-8-sig'))
    req(parity.get('passed') is True and int(parity.get('cases',0))==e['parityCases'] and parity.get('errors')==[],'CP117 native parity evidence invalid')
    req(parity.get('gates',{}).get('failed')==[],'CP117 native failed gates')

def validate_frozen(repo:Path,e:dict):
    hashlist(repo,'docs/validation/evidence/checkpoint-118/CP118_FROZEN_CP117_CSHARP_AND_TESTS_SHA256SUMS.txt',e['frozenCSharpAndTests'])
    hashlist(repo,'docs/validation/evidence/checkpoint-118/CP118_FROZEN_CP117_RESEARCH_UNCHANGED_SHA256SUMS.txt',e['frozenResearchUnchanged'])
    hashlist(repo,'docs/validation/evidence/checkpoint-118/CP118_FROZEN_CP117_PLAYER_AUTHORITY_SHA256SUMS.txt',e['frozenPlayerAuthorityFiles'])
    req(sha(repo/'docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_1.json')==MATRIX_SHA,'CP109 numerical matrix drift')
    req(sha(repo/'docs/archive/player_technology/pre-cp165-active/power_reactor_calibration_profile_v0_1.json')==REACTOR_SHA,'CP110 Reactor profile drift')

def validate_study(repo:Path,e:dict):
    sys.path.insert(0,str(repo/'tools/simulation'))
    from starcluster_research.simplified_progression_analysis import validate_study
    from starcluster_research.weapon_family_analysis import build_variants
    study=js(repo/'docs/archive/testing/pre-cp165-active/simplified_weapon_progression_study_v0_1.json')
    errs=validate_study(study); req(not errs,f'CP118 study invalid: {errs}')
    req(int(study['trialsPerVariant'])==e['nativeTrialsPerVariant'] and int(study['authoringTrialsPerVariant'])==e['authoringTrialsPerVariant'],'CP118 trial contract drift')
    req(study['primaryCalibrationTls']==e['primaryCalibrationTls'] and study['advancedValidationTls']==e['advancedValidationTls'] and study['endpointStressTls']==e['endpointStressTls'],'TL priority drift')
    builds,variants=build_variants(repo,study)
    req(len(builds)==e['exactFillBuilds'],f'CP118 build count {len(builds)} != {e["exactFillBuilds"]}')
    req(all(b.used_space==b.capacity for b in builds),'CP118 underlying build not exact-fill')
    req(len(variants)==e['studyVariants'],f'CP118 variant count {len(variants)} != {e["studyVariants"]}')
    groups={}
    for v in variants: groups[v.scenario_group]=groups.get(v.scenario_group,0)+1
    req(groups.get('missile_family_characteristic')==e['missileVariants'],'CP118 Missile variant count')
    req(groups.get('kinetic_family_characteristic')==e['kineticVariants'],'CP118 Kinetic variant count')
    pr={'primary':0,'advanced':0,'endpoint_stress':0}
    for v in variants:
        key='primary' if v.tl<=6 else ('advanced' if v.tl==7 else 'endpoint_stress'); pr[key]+=1
    req(pr=={'primary':e['primaryVariants'],'advanced':e['advancedVariants'],'endpoint_stress':e['endpointVariants']},f'priority counts {pr}')
    req(len(study['missileProfiles'])==e['missileProfiles'] and len(study['kineticProfiles'])==e['kineticProfiles'],'profile count drift')
    req(len(study['targetFixtures'])==e['targetFixtures'] and sum(x['classification']=='controlled_fixture' for x in study['targetFixtures'])==e['controlledFixtures'],'target fixture count drift')
    # Strong KISS invariants.
    req(not study.get('specialistPairingIds') and not study.get('adaptivePairingIds'),'normal specialist/adaptive Missile menu reintroduced')
    for p in study['missileProfiles']:
        if '-gp-' in p['id']:
            req((int(p['spen']),int(p['apen']))==(1,2),f'GP penetration creep {p["id"]}')
            req(int(p.get('packets',1))==1 and int(p.get('guidanceDelta',0))==0 and int(p.get('pdsInterceptPenaltyPp',0))==0,f'GP specialist leakage {p["id"]}')
        if p['id'].startswith('swarmer-'):
            req(int(p.get('packets',1)) in (2,3),f'Swarmer packet scope {p["id"]}')
            req(0<=int(p.get('pdsInterceptPenaltyPp',0))<=15,f'Swarmer PDS bound {p["id"]}')
    for p in study['kineticProfiles']:
        if p['id']=='gp-current': continue
        req(sum(bool(int(p.get(k,0))) for k in ('accuracyDelta','damageDelta','apenDelta'))==1,f'Kinetic multi-axis control {p["id"]}')
        req(int(p.get('spenDelta',0))==0 and int(p.get('packets',1))==1 and not p.get('orderedPackets'),f'Kinetic ammo-menu/Shield drift {p["id"]}')

def validate_authoring(repo:Path,e:dict):
    root=repo/'docs/validation/evidence/checkpoint-118/authoring'
    a=js(root/'analysis.json')
    req(a.get('checkpoint')==118 and a.get('acceptedBaseline')==117,'authoring identity')
    req(a.get('damageModel')=='layered_defense_hull_only' and a.get('internalDamageCriticalsSimulated') is False,'authoring damage boundary')
    req(int(a.get('variants',0))==e['studyVariants'] and int(a.get('trialsPerVariant',0))==e['authoringTrialsPerVariant'] and int(a.get('totalTrials',0))==e['authoringEngagements'],'authoring workload drift')
    req(a.get('variantCounts',{}).get('missile_family_characteristic')==e['missileVariants'] and a.get('variantCounts',{}).get('kinetic_family_characteristic')==e['kineticVariants'],'authoring family shape')
    req(a.get('priorityVariantCounts')=={'advanced':e['advancedVariants'],'endpoint_stress':e['endpointVariants'],'primary':e['primaryVariants']},'authoring priority shape')
    req(a.get('failedGates')==[] and a.get('automaticPromotion') is False,'authoring gates/promotion')
    req(len(csv_rows(root/'variants.csv'))==e['studyVariants'],'authoring variants.csv row count')
    req(len(csv_rows(root/'builds.csv'))==e['exactFillBuilds'],'authoring builds.csv row count')
    req(len(csv_rows(root/'profile_catalog.csv'))==e['missileProfiles']+e['kineticProfiles'],'authoring profile catalog row count')
    req(len(csv_rows(root/'target_fixtures.csv'))==9*e['targetFixtures'],'authoring target fixture rows')
    summ=js(repo/'docs/validation/evidence/checkpoint-118/CP118_AUTHORING_SUMMARY.json')
    req(int(summ.get('totalTrials',0))==e['authoringEngagements'] and summ.get('failedGates')==[] and summ.get('automaticPromotion') is False,'authoring summary drift')

def validate_docs(repo:Path):
    required=(
      'README.md','CHAT_README.md','docs/README.md','docs/design/README.md','docs/design/player_technology/README.md','docs/design/testing/README.md','docs/validation/README.md','docs/Prototype_TODO.md','tools/simulation/README.md',
      'docs/validation/Checkpoint_118_Simplified_Weapon_Progression.md',
      'docs/archive/testing/pre-cp165-active/Simplified_Weapon_Progression_Study_Architecture_v0_1.md',
      'docs/archive/testing/pre-cp165-active/simplified_weapon_progression_study_v0_1.json',
      'docs/validation/evidence/checkpoint-118/Simplified_Weapon_Progression_Report_v1.md',
      'docs/validation/evidence/checkpoint-118/StarCluster_CP118_Simplified_Weapon_Progression_v0_1.xlsx',
      'docs/validation/evidence/checkpoint-118/CP118_CROSS_STUDY_INTEGRATION_AUDIT.md')
    for rel in required: req((repo/rel).is_file(),f'missing CP118 doc {rel}')
    for rel in ('README.md','CHAT_README.md','docs/README.md','docs/design/README.md','docs/design/testing/README.md','docs/validation/README.md','docs/Prototype_TODO.md','tools/simulation/README.md','docs/development/Simulation_Development_Guidelines.md'):
        req('118' in text(repo/rel),f'{rel} not updated for CP118')
    runbook=text(repo/'docs/validation/Checkpoint_118_Simplified_Weapon_Progression.md')
    for phrase in ('3,648,000','1,824','Swarmer','Kinetic','no automatic'):
        req(phrase.lower() in runbook.lower(),f'CP118 runbook missing {phrase}')

def validate_root_hygiene(repo:Path):
    stale=[]
    for p in repo.iterdir():
        if p.is_file() and (p.name.lower() in {'repository_manifest.txt','manifest.sha256','sha256sums.txt'} or any(rx.match(p.name) for rx in ROOT_STALE)): stale.append(p.name)
    req(not stale,f'stale root checksum/manifest artifacts remain: {stale}')
    req((repo/'tools/checkpoints/prepackage_repository_hygiene.py').is_file(),'prepackage hygiene tool missing')

def validate_json(repo:Path):
    count=0
    for p in repo.rglob('*.json'):
        r=p.relative_to(repo).as_posix()
        if not owned(r): continue
        try: json.loads(p.read_text(encoding='utf-8-sig'))
        except Exception as exc: raise AssertionError(f'JSON parse {r}: {exc}')
        count+=1
    return count

def validate_native(path:Path,e:dict):
    a=js(path/'analysis.json')
    req(a.get('checkpoint')==118 and a.get('acceptedBaseline')==117,'native CP118 identity')
    req(int(a.get('variants',0))==e['studyVariants'] and int(a.get('trialsPerVariant',0))==e['nativeTrialsPerVariant'] and int(a.get('totalTrials',0))==e['nativeEngagements'],'native CP118 workload shape')
    req(a.get('failedGates')==[] and a.get('automaticPromotion') is False,'native CP118 gates/promotion')
    req(a.get('damageModel')=='layered_defense_hull_only' and a.get('internalDamageCriticalsSimulated') is False,'native CP118 damage boundary')
    req(a.get('variantCounts',{}).get('missile_family_characteristic')==e['missileVariants'] and a.get('variantCounts',{}).get('kinetic_family_characteristic')==e['kineticVariants'],'native family shape')
    req(len(csv_rows(path/'variants.csv'))==e['studyVariants'],'native variants.csv shape')

def validate_manifest(repo:Path,expected_count:int):
    rel='docs/validation/evidence/checkpoint-118/CP118_REPOSITORY_SHA256SUMS.txt'; mf=repo/rel
    exp={}
    for line in text(mf).splitlines():
        if not line.strip(): continue
        m=re.fullmatch(r'([0-9a-f]{64})  (.+)',line); req(m is not None,f'bad manifest row {line}')
        h,r=m.groups(); exp[r]=h
    req(len(exp)==expected_count,f'manifest count {len(exp)} != {expected_count}')
    actual=[]
    for p in repo.rglob('*'):
        if p.is_file():
            r=p.relative_to(repo).as_posix()
            if r!=rel and owned(r): actual.append(r)
    actual=sorted(actual); req(actual==sorted(exp),f'manifest paths mismatch missing={sorted(set(exp)-set(actual))[:8]} extra={sorted(set(actual)-set(exp))[:8]}')
    for r in actual: req(sha(repo/r)==exp[r],f'manifest hash mismatch {r}')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo',required=True); ap.add_argument('--native-results'); ap.add_argument('--skip-manifest',action='store_true'); a=ap.parse_args(); repo=Path(a.repo).resolve()
    try:
        d=js(repo/'tools/checkpoints/checkpoint-118/checkpoint_118_definition.json'); e=d['expected']
        req(d.get('checkpoint')==118 and d.get('acceptedBaseline')==117,'CP118 definition identity')
        req(d.get('automaticPromotion') is False and d.get('productionSourceChanged') is False and d.get('simulationResearchChanged') is True and d.get('numericalMatrixChanged') is False and d.get('conceptChanged') is False,'CP118 scope drift')
        req(int(d.get('substantiveMonteCarloTrials',0))==e['nativeEngagements'],'CP118 substantive workload definition')
        print('       Validating accepted CP117 native provenance and frozen production/numerical/player-authority surfaces...')
        validate_baseline(repo,e); validate_frozen(repo,e)
        print('       Validating CP118 study shape, KISS weapon-family boundaries, and checked-in authoring evidence...')
        validate_study(repo,e); validate_authoring(repo,e)
        print('       Validating documentation, root hygiene, JSON corpus, and production-language boundary...')
        validate_docs(repo); validate_root_hygiene(repo); j=validate_json(repo)
        req(j>=e['jsonFilesMinimum'],f'unexpected JSON count {j}')
        for rel in ('src/StarCluster.Game','src/StarCluster.Core'):
            py=list((repo/rel).rglob('*.py')); req(not py,f'Python leaked into production runtime: {py[:1]}')
        if a.native_results:
            print('       Validating substantive CP118 native result shape...'); validate_native(Path(a.native_results).resolve(),e)
        if not a.skip_manifest:
            print('       Validating full repository manifest...'); validate_manifest(repo,int(e['repositoryOwnedFiles']))
        print(f"       CP118 contract verified: {e['repositoryOwnedFiles'] if not a.skip_manifest else 'pre-manifest'} repository-owned files; {j} JSON files parsed; {e['studyVariants']} variants ({e['missileVariants']} Missile + {e['kineticVariants']} Kinetic); {e['authoringEngagements']} checked-in authoring engagements; no automatic promotion.")
        return 0
    except Exception as exc:
        print(f'CP118 contract failure: {exc}',file=sys.stderr); return 1
if __name__=='__main__': raise SystemExit(main())
