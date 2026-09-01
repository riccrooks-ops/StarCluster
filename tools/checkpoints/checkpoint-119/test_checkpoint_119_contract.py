#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json,re,sys,zipfile
from pathlib import Path
MATRIX_SHA='91cb29f7e1e0f792e5a2258b1ab0655fe9924c768f4d80b645269fae52384000'
REACTOR_SHA='ebed51fa16d0ee1c9721b55ca135eb81e23c321a8373dfcb826a1a096371e9a6'
CP118_NATIVE_ZIP_SHA='6fee230850eeaf621c57450e353f06c5beb3aacd593937307d380ffd030f3337'
EXCLUDED_PARTS={'.git','.vs','.vscode','.idea','out','bin','obj','TestResults','__pycache__'}
EXCLUDED_FILES={'.DS_Store','Thumbs.db'}; EXCLUDED_SUFFIXES={'.pyc','.user','.userosscache','.sln.docstates','.uid','.suo'}
ROOT_STALE=(re.compile(r'^CHECKPOINT_\d+[A-Za-z]*_SHA256SUMS\.txt$',re.I),re.compile(r'^SHA256SUMS(?:[-_].*)?\.txt$',re.I))
def req(v,msg):
    if not v: raise AssertionError(msg)
def sha(p:Path): return hashlib.sha256(p.read_bytes()).hexdigest()
def text(p:Path): req(p.is_file(),f'Missing {p}'); return p.read_text(encoding='utf-8-sig')
def js(p:Path): return json.loads(text(p))
def owned(rel:str):
    p=Path(rel); return not any(x in EXCLUDED_PARTS for x in p.parts) and p.name not in EXCLUDED_FILES and p.suffix.lower() not in EXCLUDED_SUFFIXES
def csv_rows(path:Path):
    req(path.is_file(),f'Missing {path}')
    with path.open('r',encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def hashlist(repo:Path,rel:str,expected:int):
    rr=[]
    for line in text(repo/rel).splitlines():
        if not line.strip():continue
        m=re.fullmatch(r'([0-9a-f]{64})  (.+)',line); req(m is not None,f'bad hash list row {rel}: {line}'); rr.append(m.groups())
    req(len(rr)==expected,f'{rel} count {len(rr)} != {expected}')
    for h,r in rr: req((repo/r).is_file(),f'frozen file missing {r}'); req(sha(repo/r)==h,f'frozen file drift {r}')
def validate_baseline(repo:Path,e:dict):
    s=js(repo/'docs/validation/evidence/checkpoint-119/CP119_ACCEPTED_CP118_NATIVE_SUMMARY.json')
    req(s.get('acceptedCheckpoint')==118 and s.get('status')=='accepted_native_baseline_for_cp119','CP118 accepted summary identity')
    req(s.get('archiveSha256')==CP118_NATIVE_ZIP_SHA,'CP118 declared native zip sha drift')
    z=repo/'docs/validation/evidence/checkpoint-119/checkpoint-118-native-results.zip'; req(sha(z)==CP118_NATIVE_ZIP_SHA,'CP118 native archive bytes drift')
    with zipfile.ZipFile(z) as zz:
        a=json.loads(zz.read('checkpoint-118/native-simplified-weapon-study/analysis.json').decode('utf-8-sig'))
        p=json.loads(zz.read('checkpoint-118/parity/summary.json').decode('utf-8-sig'))
    req(a.get('checkpoint')==118 and int(a.get('variants',0))==1824 and int(a.get('totalTrials',0))==3648000 and a.get('failedGates')==[],'CP118 substantive native evidence invalid')
    req(p.get('passed') is True and int(p.get('cases',0))==e['parityCases'] and p.get('errors')==[],'CP118 native parity invalid')
def validate_frozen(repo:Path,e:dict):
    base='docs/validation/evidence/checkpoint-119/'
    hashlist(repo,base+'CP119_FROZEN_CP118_CSHARP_AND_TESTS_SHA256SUMS.txt',e['frozenCSharpAndTests'])
    hashlist(repo,base+'CP119_FROZEN_CP118_RESEARCH_UNCHANGED_SHA256SUMS.txt',e['frozenResearchUnchanged'])
    hashlist(repo,base+'CP119_FROZEN_CP118_PLAYER_AUTHORITY_SHA256SUMS.txt',e['frozenPlayerAuthorityFiles'])
    hashlist(repo,base+'CP119_FROZEN_CP118_CHECKPOINT_AUTHORITY_SHA256SUMS.txt',e['frozenCp118CheckpointAuthorityFiles'])
    req(sha(repo/'docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_1.json')==MATRIX_SHA,'CP109 numerical matrix drift')
    req(sha(repo/'docs/archive/player_technology/pre-cp165-active/power_reactor_calibration_profile_v0_1.json')==REACTOR_SHA,'CP110 Reactor profile drift')
def validate_study(repo:Path,e:dict):
    sys.path.insert(0,str(repo/'tools/simulation'))
    from starcluster_research.weapon_integration_analysis import validate_study
    from starcluster_research.weapon_family_analysis import build_variants
    s=js(repo/'docs/archive/testing/pre-cp165-active/campaign_weapon_integration_study_v0_1.json'); req(validate_study(s)==[],f'CP119 study invalid: {validate_study(s)}')
    req(int(s['trialsPerVariant'])==e['nativeTrialsPerVariant'] and int(s['authoringTrialsPerVariant'])==e['authoringTrialsPerVariant'],'trial contract drift')
    req(s['primaryCalibrationTls']==e['primaryCalibrationTls'] and s['advancedValidationTls']==e['advancedValidationTls'] and s['endpointStressTls']==e['endpointStressTls'],'TL weighting drift')
    builds,vars=build_variants(repo,s); req(len(builds)==e['exactFillBuilds'] and all(b.used_space==b.capacity for b in builds),'build/exact-fill shape drift'); req(len(vars)==e['studyVariants'],'variant count drift')
    groups={}
    for v in vars:groups[v.scenario_group]=groups.get(v.scenario_group,0)+1
    req(groups=={'energy_family_reference':e['energyVariants'],'kinetic_family_characteristic':e['kineticVariants'],'missile_family_characteristic':e['missileVariants']},f'family variant shape {groups}')
    pr={'primary':0,'advanced':0,'endpoint_stress':0}
    for v in vars: pr['primary' if v.tl<=6 else ('advanced' if v.tl==7 else 'endpoint_stress')]+=1
    req(pr=={'primary':e['primaryVariants'],'advanced':e['advancedVariants'],'endpoint_stress':e['endpointVariants']},f'priority shape {pr}')
    req(len(s['missileProfiles'])==e['missileProfiles'] and len(s['kineticProfiles'])==e['kineticProfiles'],'profile count drift'); req(len(s['targetFixtures'])==e['targetFixtures'] and all(x['classification']=='legal_build' for x in s['targetFixtures']),'target fixture drift')
    req(s['workingSwarmerByTl']['1'] is None and s['workingSwarmerByTl']['2']=='swarmer-early-tl2','TL2 Swarmer drift')
    req(not s.get('specialistPairingIds') and not s.get('adaptivePairingIds'),'specialist menu reintroduced')
    for p in s['missileProfiles']:
        pid=p['id']
        if pid.startswith('missile-working-'): req((int(p['spen']),int(p['apen']),int(p.get('packets',1)))==(1,2,1),'working GP yield-only boundary')
        if pid.startswith('swarmer-'): req(int(p.get('packets',0))==2 and int(p.get('spen',-1))==0 and int(p.get('apen',-1))==0,'Swarmer KISS boundary')
    kp=next(x for x in s['kineticProfiles'] if x['id']=='kinetic-working-smart-plus5'); req(int(kp['accuracyDelta'])==5 and all(int(kp.get(k,0))==0 for k in ('damageDelta','spenDelta','apenDelta')),'Kinetic +5-only boundary')
def validate_authoring(repo:Path,e:dict):
    r=repo/'docs/validation/evidence/checkpoint-119/authoring'; a=js(r/'analysis.json')
    req(a.get('checkpoint')==119 and a.get('acceptedBaseline')==118,'authoring identity')
    req(int(a.get('variants',0))==e['studyVariants'] and int(a.get('trialsPerVariant',0))==e['authoringTrialsPerVariant'] and int(a.get('totalTrials',0))==e['authoringEngagements'],'authoring workload')
    req(a.get('variantCounts')=={'energy_family_reference':e['energyVariants'],'kinetic_family_characteristic':e['kineticVariants'],'missile_family_characteristic':e['missileVariants']},'authoring family shape')
    req(a.get('priorityVariantCounts')=={'advanced':e['advancedVariants'],'endpoint_stress':e['endpointVariants'],'primary':e['primaryVariants']},'authoring priority shape')
    req(a.get('failedGates')==[] and a.get('automaticPromotion') is False,'authoring gates/promotion'); req(a.get('damageModel')=='layered_defense_hull_only' and a.get('internalDamageCriticalsSimulated') is False,'authoring damage boundary')
    req(len(csv_rows(r/'variants.csv'))==e['studyVariants'],'authoring variants rows'); req(len(csv_rows(r/'builds.csv'))==e['exactFillBuilds'],'authoring builds rows'); req(len(csv_rows(r/'profile_catalog.csv'))==e['missileProfiles']+e['kineticProfiles']+e['energyProfiles'],'profile catalog rows'); req(len(csv_rows(r/'target_fixtures.csv'))==9*e['targetFixtures'],'target rows')
    s=js(repo/'docs/validation/evidence/checkpoint-119/CP119_AUTHORING_SUMMARY.json'); req(int(s['totalTrials'])==e['authoringEngagements'] and s['failedGates']==[] and s['automaticPromotion'] is False,'authoring summary drift')
def validate_docs(repo:Path):
    required=(
      'README.md','CHAT_README.md','docs/README.md','docs/design/README.md','docs/design/testing/README.md','docs/validation/README.md','docs/Prototype_TODO.md','tools/simulation/README.md','docs/development/Simulation_Development_Guidelines.md',
      'docs/validation/Checkpoint_119_Campaign_Weighted_Weapon_Integration.md','docs/archive/testing/pre-cp165-active/Campaign_Weighted_Weapon_Integration_Study_Architecture_v0_1.md','docs/archive/testing/pre-cp165-active/campaign_weapon_integration_study_v0_1.json','docs/validation/evidence/checkpoint-119/Campaign_Weighted_Weapon_Integration_Report_v1.md','docs/validation/evidence/checkpoint-119/StarCluster_CP119_Campaign_Weighted_Weapon_Integration_v0_1.xlsx','docs/validation/evidence/checkpoint-119/CP119_CROSS_STUDY_INTEGRATION_AUDIT.md')
    for r in required:req((repo/r).is_file(),f'missing CP119 doc {r}')
    for r in ('README.md','CHAT_README.md','docs/README.md','docs/design/README.md','docs/design/testing/README.md','docs/validation/README.md','docs/Prototype_TODO.md','tools/simulation/README.md','docs/development/Simulation_Development_Guidelines.md'): req('119' in text(repo/r),f'{r} missing CP119 pointer')
    rb=text(repo/'docs/validation/Checkpoint_119_Campaign_Weighted_Weapon_Integration.md').lower()
    for x in ('2,304,000','1,152','tl2','swarmer','+5 acc','no automatic'):req(x in rb,f'runbook missing {x}')
def validate_wrapper(repo:Path):
    t=text(repo/'tools/checkpoints/checkpoint-119/apply_checkpoint_119.ps1')
    for x in ('weapon-integration-study','payload-study','weapon-family-study','warhead-generation-study','simplified-weapon-study',"'--trials','2000'",'2304000','Study output tail:','prepackage_repository_hygiene.py','preflight_checkpoint_119.py','test_checkpoint_119_contract.py'):req(x in t,f'wrapper missing {x}')
    req('[switch]$RepositoryOnly' in t and '[switch]$NoClean' in t,'wrapper interface drift')
def validate_root_hygiene(repo:Path):
    stale=[]
    for p in repo.iterdir():
        if p.is_file() and (p.name.lower() in {'repository_manifest.txt','manifest.sha256','sha256sums.txt'} or any(rx.match(p.name) for rx in ROOT_STALE)):stale.append(p.name)
    req(not stale,f'stale root checksum/manifest artifacts: {stale}'); req((repo/'tools/checkpoints/prepackage_repository_hygiene.py').is_file(),'hygiene tool missing')
def validate_json(repo:Path):
    n=0
    for p in repo.rglob('*.json'):
        r=p.relative_to(repo).as_posix()
        if not owned(r):continue
        try: json.loads(p.read_text(encoding='utf-8-sig'))
        except Exception as exc: raise AssertionError(f'JSON parse {r}: {exc}')
        n+=1
    return n
def validate_native(path:Path,e:dict):
    a=js(path/'analysis.json'); req(a.get('checkpoint')==119 and a.get('acceptedBaseline')==118,'native identity'); req(int(a.get('variants',0))==e['studyVariants'] and int(a.get('trialsPerVariant',0))==e['nativeTrialsPerVariant'] and int(a.get('totalTrials',0))==e['nativeEngagements'],'native workload'); req(a.get('failedGates')==[] and a.get('automaticPromotion') is False,'native gates/promotion'); req(a.get('damageModel')=='layered_defense_hull_only' and a.get('internalDamageCriticalsSimulated') is False,'native damage boundary'); req(len(csv_rows(path/'variants.csv'))==e['studyVariants'],'native variants.csv')
def validate_manifest(repo:Path,count:int):
    rel='docs/validation/evidence/checkpoint-119/CP119_REPOSITORY_SHA256SUMS.txt'; mf=repo/rel; exp={}
    for line in text(mf).splitlines():
        if not line.strip():continue
        m=re.fullmatch(r'([0-9a-f]{64})  (.+)',line); req(m is not None,f'bad manifest row {line}'); h,r=m.groups(); exp[r]=h
    req(len(exp)==count,f'manifest count {len(exp)} != {count}')
    actual=sorted(p.relative_to(repo).as_posix() for p in repo.rglob('*') if p.is_file() and p.relative_to(repo).as_posix()!=rel and owned(p.relative_to(repo).as_posix()))
    req(actual==sorted(exp),f'manifest path mismatch missing={sorted(set(exp)-set(actual))[:8]} extra={sorted(set(actual)-set(exp))[:8]}')
    for r in actual:req(sha(repo/r)==exp[r],f'manifest hash mismatch {r}')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo',required=True); ap.add_argument('--native-results'); ap.add_argument('--skip-manifest',action='store_true'); a=ap.parse_args(); repo=Path(a.repo).resolve()
    try:
        d=js(repo/'tools/checkpoints/checkpoint-119/checkpoint_119_definition.json'); e=d['expected']; req(d.get('checkpoint')==119 and d.get('acceptedBaseline')==118,'definition identity'); req(d.get('automaticPromotion') is False and d.get('productionSourceChanged') is False and d.get('simulationResearchChanged') is True and d.get('numericalMatrixChanged') is False and d.get('conceptChanged') is False and d.get('playerAuthorityChanged') is False,'scope drift'); req(int(d.get('substantiveMonteCarloTrials',0))==e['nativeEngagements'],'substantive workload definition')
        print('       Validating accepted CP118 native provenance and frozen production/player/research/checkpoint surfaces...'); validate_baseline(repo,e); validate_frozen(repo,e)
        print('       Validating CP119 KISS study shape and checked-in authoring evidence...'); validate_study(repo,e); validate_authoring(repo,e)
        print('       Validating documentation, wrapper, root hygiene, JSON corpus, and production-language boundary...'); validate_docs(repo); validate_wrapper(repo); validate_root_hygiene(repo); n=validate_json(repo); req(n>=e['jsonFilesMinimum'],f'JSON count {n} below {e["jsonFilesMinimum"]}')
        for rel in ('src/StarCluster.Game','src/StarCluster.Core'): req(not list((repo/rel).rglob('*.py')),f'Python leaked into production runtime {rel}')
        if a.native_results: print('       Validating substantive CP119 native result shape...'); validate_native(Path(a.native_results).resolve(),e)
        if not a.skip_manifest: print('       Validating full repository manifest...'); validate_manifest(repo,int(e['repositoryOwnedFiles']))
        print(f"       CP119 contract verified: {e['repositoryOwnedFiles'] if not a.skip_manifest else 'pre-manifest'} repository-owned files; {n} JSON files parsed; {e['studyVariants']} variants ({e['missileVariants']} Missile + {e['kineticVariants']} Kinetic + {e['energyVariants']} Energy); {e['authoringEngagements']} checked-in authoring engagements; no automatic promotion.")
        return 0
    except Exception as exc:
        print(f'CP119 contract failure: {exc}',file=sys.stderr); return 1
if __name__=='__main__': raise SystemExit(main())
