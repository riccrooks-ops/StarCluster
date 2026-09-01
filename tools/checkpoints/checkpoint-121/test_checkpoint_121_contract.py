#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json,re,sys,zipfile
from pathlib import Path

MATRIX_SHA='91cb29f7e1e0f792e5a2258b1ab0655fe9924c768f4d80b645269fae52384000'
REACTOR_SHA='ebed51fa16d0ee1c9721b55ca135eb81e23c321a8373dfcb826a1a096371e9a6'
CP119_NATIVE_ZIP_SHA='1cd438a3ab74a47a20cee20115f972fa92bf4ac6f2b7a592cf54327ee8f3e18c'
EXCLUDED_PARTS={'.git','.vs','.vscode','.idea','out','bin','obj','TestResults','__pycache__'}
EXCLUDED_FILES={'.DS_Store','Thumbs.db'}
EXCLUDED_SUFFIXES={'.pyc','.user','.userosscache','.sln.docstates','.uid','.suo'}
ROOT_STALE=(re.compile(r'^CHECKPOINT_\d+[A-Za-z]*_SHA256SUMS\.txt$',re.I),re.compile(r'^SHA256SUMS(?:[-_].*)?\.txt$',re.I))


def req(v,msg):
    if not v: raise AssertionError(msg)
def sha(p:Path):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()
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
    for h,r in rr:
        req((repo/r).is_file(),f'frozen file missing {r}'); req(sha(repo/r)==h,f'frozen file drift {r}')


def validate_baseline(repo:Path,e:dict):
    s=js(repo/'docs/validation/evidence/checkpoint-121/CP121_ACCEPTED_CP119_NATIVE_SUMMARY.json')
    req(s['acceptedCheckpoint']==119 and s['status']=='accepted_native_baseline_for_cp121','CP119 baseline summary identity')
    req(s['archiveSha256']==CP119_NATIVE_ZIP_SHA,'CP119 baseline summary SHA')
    z=repo/s['archivePath']; req(sha(z)==CP119_NATIVE_ZIP_SHA,'CP119 native archive drift')
    with zipfile.ZipFile(z) as zz:
        a=json.loads(zz.read('checkpoint-119/native-weapon-integration-study/analysis.json').decode('utf-8-sig'))
        p=json.loads(zz.read('checkpoint-119/parity/summary.json').decode('utf-8-sig'))
    req(a['checkpoint']==119 and a['variants']==1152 and a['totalTrials']==2304000 and a['failedGates']==[],'CP119 native evidence invalid')
    req(p['passed'] is True and p['cases']==e['parityCases'] and p['errors']==[],'CP119 parity invalid')


def validate_frozen(repo:Path,e:dict):
    base='docs/validation/evidence/checkpoint-120/'
    hashlist(repo,base+'CP120_FROZEN_CP119_CSHARP_AND_TESTS_SHA256SUMS.txt',e['frozenCSharpAndTests'])
    hashlist(repo,base+'CP120_FROZEN_CP119_PLAYER_AUTHORITY_SHA256SUMS.txt',e['frozenPlayerAuthorityFiles'])
    hashlist(repo,base+'CP120_FROZEN_CP119_CP119_CHECKPOINT_AUTHORITY_SHA256SUMS.txt',e['frozenCp119CheckpointAuthorityFiles'])
    req(sha(repo/'docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_1.json')==MATRIX_SHA,'CP109 numerical matrix drift')
    req(sha(repo/'docs/archive/player_technology/pre-cp165-active/power_reactor_calibration_profile_v0_1.json')==REACTOR_SHA,'CP110 Reactor profile drift')


def validate_correction(repo:Path,e:dict):
    z=repo/'docs/validation/evidence/checkpoint-121/CP120_NATIVE_RESULTS_ORIGINAL.zip'
    req(sha(z)==e['cp120NativeArchiveSha256'],'CP120 native archive SHA drift')
    with zipfile.ZipFile(z) as zz:
        raw=zz.read('checkpoint-120/native-weapon-sensitivity-study/variants.csv')
        a=json.loads(zz.read('checkpoint-120/native-weapon-sensitivity-study/analysis.json').decode('utf-8-sig'))
    req(hashlib.sha256(raw).hexdigest()==e['cp120NativeVariantsSha256'],'CP120 native variants SHA drift')
    req(a['checkpoint']==120 and a['variants']==4284 and a['totalTrials']==8568000 and a['failedGates']==[],'preserved CP120 native analysis invalid')
    c=repo/'docs/validation/evidence/checkpoint-121/cp120-corrected'
    summary=js(c/'correction_summary.json')
    req(summary['sourceArchiveSha256']==e['cp120NativeArchiveSha256'] and summary['sourceVariantsSha256']==e['cp120NativeVariantsSha256'],'correction provenance SHA')
    req(summary['sourceTrials']==8568000 and summary['combatRerun'] is False and summary['correctedGuidanceComparisonRows']==14,'correction summary shape')
    for name in summary['outputFiles']: req((c/name).is_file(),f'corrected output missing {name}')
    rows=csv_rows(c/'sensitivity_delta_summary.csv')
    acc10=[r for r in rows if r['axis']=='swarmer_accuracy' and 'acc-10' in r['comparison_id']]
    req(len(acc10)==6,'corrected +10 guidance row count')
    req(all(0.095<=float(r['delta_missile_hit_per_guidance_attempt'])<=0.105 for r in acc10),'corrected +10 terminal guidance-hit slope')


def validate_study(repo:Path,e:dict):
    sys.path.insert(0,str(repo/'tools/simulation'))
    from starcluster_research.damage_resolution_analysis import build_halfstep_variants,validate_study
    from starcluster_research.study import load_json
    s=load_json(repo/'docs/archive/testing/pre-cp165-active/damage_resolution_scaling_study_v0_1.json')
    errs=validate_study(s); req(errs==[],f'CP121 study invalid: {errs}')
    req(s['damageScale']==2 and s['acceptedBaseline']==119 and s['supersedesCandidate']==120,'study identity/scale')
    req(s['trialsPerVariant']==e['nativeTrialsPerVariant'] and s['equivalenceTrialsPerVariant']==e['nativeEquivalenceTrialsPerVariant'],'native trial contract')
    req(s['authoringTrialsPerVariant']==e['authoringTrialsPerVariant'] and s['authoringEquivalenceTrialsPerVariant']==e['authoringEquivalenceTrialsPerVariant'],'authoring trial contract')
    req(s['primaryCalibrationTls']==e['primaryCalibrationTls'] and s['advancedValidationTls']==e['advancedValidationTls'] and s['endpointStressTls']==e['endpointStressTls'],'TL weighting')
    req(len(s['missileProfiles'])==e['missileProfiles'] and len(s['kineticProfiles'])==e['kineticProfiles'],'profile count')
    req(len(s['targetFixtures'])==e['targetFixtures'] and sum(x['classification']=='legal_build' for x in s['targetFixtures'])==e['legalFixtures'] and sum(x['classification']=='controlled_fixture' for x in s['targetFixtures'])==e['controlledFixtures'],'fixture count')
    req(len(s['offenseSeries'])==e['offenseSeries'] and len(s['defenseSeries'])==e['defenseSeries'],'series count')
    builds,variants=build_halfstep_variants(repo,s)
    req(len(builds)==e['exactFillBuilds'] and all(b.used_space==b.capacity for b in builds),'build shape')
    req(len(variants)==e['studyVariants'],'variant count')
    groups={}
    priorities={'primary':0,'advanced':0,'endpoint_stress':0}
    for v in variants:
        groups[v.scenario_group]=groups.get(v.scenario_group,0)+1
        priorities['primary' if v.tl in (2,3,4,5,6) else ('advanced' if v.tl==7 else 'endpoint_stress')]+=1
    req(groups=={'energy_family_reference':e['energyVariants'],'kinetic_family_characteristic':e['kineticVariants'],'missile_family_characteristic':e['missileVariants']},'variant family shape')
    req(priorities=={'primary':e['primaryVariants'],'advanced':e['advancedVariants'],'endpoint_stress':e['endpointVariants']},'variant priority shape')


def validate_authoring(repo:Path,e:dict):
    r=repo/'docs/validation/evidence/checkpoint-121/authoring-damage-resolution-study'; a=js(r/'analysis.json')
    req(a['checkpoint']==121 and a['acceptedBaseline']==119 and a['supersedesCandidate']==120,'authoring identity')
    req(a['damageScale']==2 and a['equivalenceExact'] is True and a['equivalenceMismatchedTrials']==0,'authoring equivalence')
    req(a['equivalenceVariants']==e['equivalenceVariants'] and a['equivalenceTrialsPerVariant']==e['authoringEquivalenceTrialsPerVariant'] and a['equivalencePairedTrials']==e['authoringEquivalencePairedTrials'],'authoring equivalence shape')
    req(a['variants']==e['studyVariants'] and a['trialsPerVariant']==e['authoringTrialsPerVariant'] and a['totalTrials']==e['authoringEngagements'],'authoring half-step workload')
    req(a['variantCounts']=={'energy_family_reference':e['energyVariants'],'kinetic_family_characteristic':e['kineticVariants'],'missile_family_characteristic':e['missileVariants']},'authoring family shape')
    req(a['priorityVariantCounts']=={'advanced':e['advancedVariants'],'endpoint_stress':e['endpointVariants'],'primary':e['primaryVariants']},'authoring priority shape')
    req(a['failedGates']==[] and a['trialErrors']==0 and a['automaticPromotion'] is False,'authoring gates')
    expected={'builds.csv':108,'defense_halfstep_summary.csv':75,'equivalence_variants.csv':4284,'integration_summary.csv':1212,'offense_halfstep_summary.csv':23,'packet_resolution_surface.csv':165,'target_fixtures.csv':128,'variants.csv':2424}
    for name,n in expected.items(): req(len(csv_rows(r/name))==n,f'authoring {name} rows')
    surface=csv_rows(r/'packet_resolution_surface.csv'); idx={(int(x['tl']),int(x['spen_scaled']),int(x['apen_scaled']),int(x['damage_scaled'])):x for x in surface}
    triples=distinct=between=0
    keys=('shield_armor_prevented','shield_absorbed','armor_prevented','armor_integrity_damage','armor_protection_damage','hull_damage')
    st=lambda x: tuple(int(x[k]) for k in keys)
    for tl in range(3,8):
        for sp,ap in ((2,4),(3,4),(2,5)):
            for odd in (9,11,13,15,17):
                aa=idx.get((tl,sp,ap,odd-1)); bb=idx.get((tl,sp,ap,odd)); cc=idx.get((tl,sp,ap,odd+1))
                if not (aa and bb and cc):continue
                triples+=1; sa,sb,sc=st(aa),st(bb),st(cc)
                if sb!=sa and sb!=sc: distinct+=1
                if all(min(x,z)<=y<=max(x,z) for x,y,z in zip(sa,sb,sc)): between+=1
    req((triples,distinct,between)==(75,75,75),'odd deterministic layer surface')
    s=js(repo/'docs/validation/evidence/checkpoint-121/CP121_AUTHORING_SUMMARY.json')
    req(s['equivalenceMismatchedTrials']==0 and s['halfStepEngagements']==e['authoringEngagements'] and s['failedGates']==[],'authoring summary')


def validate_docs(repo:Path):
    required=(
      'README.md','CHAT_README.md','docs/README.md','docs/design/testing/README.md','docs/validation/README.md','tools/simulation/README.md','docs/development/Simulation_Development_Guidelines.md',
      'docs/validation/Checkpoint_121_Damage_Resolution_Scaling.md','docs/archive/testing/pre-cp165-active/Damage_Resolution_Scaling_Study_Architecture_v0_1.md','docs/archive/testing/pre-cp165-active/damage_resolution_scaling_study_v0_1.json','docs/archive/testing/pre-cp165-active/damage_domain_scaling_audit_v0_1.json','docs/validation/evidence/checkpoint-121/Damage_Resolution_Scaling_Report_v1.md')
    for r in required:req((repo/r).is_file(),f'missing CP121 doc {r}')
    for r in ('README.md','CHAT_README.md','docs/README.md','docs/design/testing/README.md','docs/validation/README.md','tools/simulation/README.md','docs/development/Simulation_Development_Guidelines.md'):
        req('121' in text(repo/r),f'{r} missing CP121 pointer')
    rb=text(repo/'README.md').lower()
    for x in ('2,424','4,848,000','171,360','hull','x2','checkpoint-121'):
        req(x in rb,f'root README missing {x}')
    cp120=text(repo/'docs/validation/Checkpoint_120_Weapon_Progression_Sensitivity_Mapping.md').lower()
    req('superseded by checkpoint 121' in cp120 and 'attacking side' in cp120 and 'target side' in cp120,'CP120 supersession note missing')


def validate_wrapper(repo:Path):
    t=text(repo/'tools/checkpoints/checkpoint-121/apply_checkpoint_121.ps1')
    helper=text(repo/'tools/checkpoints/checkpoint-121/reanalyze_cp120_native.py')
    req("Path(__file__).resolve().parents[3]" in helper and "sys.path.insert(0, str(_SIMULATION_ROOT))" in helper, 'standalone CP120 reanalysis helper must bootstrap tools/simulation')
    req("correction_summary.json').write_bytes" in helper, 'CP120 correction summary must use canonical UTF-8/LF byte serialization')
    req("correction_summary.json').write_text" not in helper, 'CP120 correction summary must not use platform-translated text serialization')
    for x in ('damage-resolution-study','weapon-sensitivity-study','weapon-integration-study','payload-study','weapon-family-study','warhead-generation-study','simplified-weapon-study',"'--trials','2000'", "'--equivalence-trials','20'",'4848000','85680','reanalyze_cp120_native.py','Study output tail:','prepackage_repository_hygiene.py','preflight_checkpoint_121.py','test_checkpoint_121_contract.py'):
        req(x in t,f'wrapper missing {x}')
    req('[switch]$RepositoryOnly' in t and '[switch]$NoClean' in t,'wrapper interface')


def validate_root_hygiene(repo:Path):
    stale=[]
    for p in repo.iterdir():
        if p.is_file() and (p.name.lower() in {'repository_manifest.txt','manifest.sha256','sha256sums.txt'} or any(rx.match(p.name) for rx in ROOT_STALE)):stale.append(p.name)
    req(not stale,f'stale root checksum/manifest artifacts: {stale}')
    req((repo/'tools/checkpoints/prepackage_repository_hygiene.py').is_file(),'hygiene tool missing')


def validate_json(repo:Path):
    n=0
    for p in repo.rglob('*.json'):
        r=p.relative_to(repo).as_posix()
        if not owned(r):continue
        try:json.loads(p.read_text(encoding='utf-8-sig'))
        except Exception as exc:raise AssertionError(f'JSON parse {r}: {exc}')
        n+=1
    return n


def validate_native(path:Path,e:dict):
    a=js(path/'analysis.json')
    req(a['checkpoint']==121 and a['acceptedBaseline']==119 and a['supersedesCandidate']==120,'native identity')
    req(a['damageScale']==2 and a['equivalenceExact'] is True and a['equivalenceMismatchedTrials']==0,'native x2 equivalence')
    req(a['equivalenceVariants']==e['equivalenceVariants'] and a['equivalenceTrialsPerVariant']==e['nativeEquivalenceTrialsPerVariant'] and a['equivalencePairedTrials']==e['nativeEquivalencePairedTrials'],'native equivalence workload')
    req(a['variants']==e['studyVariants'] and a['trialsPerVariant']==e['nativeTrialsPerVariant'] and a['totalTrials']==e['nativeEngagements'],'native half-step workload')
    req(a['variantCounts']=={'energy_family_reference':e['energyVariants'],'kinetic_family_characteristic':e['kineticVariants'],'missile_family_characteristic':e['missileVariants']},'native family shape')
    req(a['priorityVariantCounts']=={'advanced':e['advancedVariants'],'endpoint_stress':e['endpointVariants'],'primary':e['primaryVariants']},'native priority shape')
    req(a['failedGates']==[] and a['trialErrors']==0 and a['automaticPromotion'] is False,'native gates')
    req(len(csv_rows(path/'equivalence_variants.csv'))==e['equivalenceVariants'],'native equivalence rows')
    req(len(csv_rows(path/'variants.csv'))==e['studyVariants'],'native variant rows')
    for name in ('offense_halfstep_summary.csv','defense_halfstep_summary.csv','packet_resolution_surface.csv','integration_summary.csv'):req((path/name).is_file(),f'native output missing {name}')


def validate_manifest(repo:Path,count:int):
    rel='docs/validation/evidence/checkpoint-121/CP121_REPOSITORY_SHA256SUMS.txt'; mf=repo/rel; exp={}
    for line in text(mf).splitlines():
        if not line.strip():continue
        m=re.fullmatch(r'([0-9a-f]{64})  (.+)',line); req(m is not None,f'bad manifest row {line}'); h,r=m.groups(); exp[r]=h
    req(len(exp)==count,f'manifest count {len(exp)} != {count}')
    actual=sorted(p.relative_to(repo).as_posix() for p in repo.rglob('*') if p.is_file() and p.relative_to(repo).as_posix()!=rel and owned(p.relative_to(repo).as_posix()))
    req(actual==sorted(exp),f'manifest path mismatch missing={sorted(set(exp)-set(actual))[:8]} extra={sorted(set(actual)-set(exp))[:8]}')
    for r in actual:req(sha(repo/r)==exp[r],f'manifest hash mismatch {r}')


def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);ap.add_argument('--native-results');ap.add_argument('--skip-manifest',action='store_true');a=ap.parse_args();repo=Path(a.repo).resolve()
    try:
        d=js(repo/'tools/checkpoints/checkpoint-121/checkpoint_121_definition.json');e=d['expected']
        req(d['checkpoint']==121 and d['acceptedBaseline']==119 and d['supersedesCandidate']==120 and d.get('revision')=='corrected_replacement_1','definition identity/revision')
        req(d['automaticPromotion'] is False and d['productionSourceChanged'] is False and d['simulationResearchChanged'] is True and d['numericalMatrixChanged'] is False and d['conceptChanged'] is False and d['playerAuthorityChanged'] is False,'scope drift')
        req(d['substantiveMonteCarloTrials']==e['nativeEngagements'] and d['substantiveResearchCombatExecutions']==e['nativeEngagements']+e['nativeEquivalenceCombatExecutions'],'workload definition')
        print('       Validating accepted CP119 baseline and frozen C#/player/checkpoint authority...');validate_baseline(repo,e);validate_frozen(repo,e)
        print('       Validating preserved/reanalyzed CP120 native evidence...');validate_correction(repo,e)
        print('       Validating CP121 x2 study shape and bounded authoring evidence...');validate_study(repo,e);validate_authoring(repo,e)
        print('       Validating docs, wrapper, hygiene, JSON corpus, and production-language boundary...');validate_docs(repo);validate_wrapper(repo);validate_root_hygiene(repo);n=validate_json(repo);req(n>=e['jsonFilesMinimum'],f'JSON count {n} below {e["jsonFilesMinimum"]}')
        for rel in ('src/StarCluster.Game','src/StarCluster.Core'):req(not list((repo/rel).rglob('*.py')),f'Python leaked into production runtime {rel}')
        if a.native_results:print('       Validating substantive CP121 native result shape...');validate_native(Path(a.native_results).resolve(),e)
        if not a.skip_manifest:print('       Validating full repository manifest...');validate_manifest(repo,int(e['repositoryOwnedFiles']))
        print(f"       CP121 contract verified: {e['repositoryOwnedFiles'] if not a.skip_manifest else 'pre-manifest'} repository-owned files; {n} JSON files parsed; exact x2 equivalence gate; {e['studyVariants']} half-step variants; no automatic promotion.")
        return 0
    except Exception as exc:
        print(f'CP121 contract failure: {exc}',file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
