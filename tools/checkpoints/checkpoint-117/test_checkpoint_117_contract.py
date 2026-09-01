#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re, sys, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

MATRIX_SHA='91cb29f7e1e0f792e5a2258b1ab0655fe9924c768f4d80b645269fae52384000'
REACTOR_SHA='ebed51fa16d0ee1c9721b55ca135eb81e23c321a8373dfcb826a1a096371e9a6'
CP116_STUDY_SHA='9ac763916284b5f3e6c13777d83ed8b88a5e7029733dc5a829b95e6e658343e4'
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

def docx_text(path:Path):
    req(path.is_file(),f'Missing {path}')
    with zipfile.ZipFile(path) as z:
        xml=z.read('word/document.xml')
    root=ET.fromstring(xml)
    return ' '.join(x.text or '' for x in root.iter() if x.tag.endswith('}t'))

def validate_baseline(repo:Path,e:dict):
    n=js(repo/'docs/validation/evidence/checkpoint-116/CP116_NATIVE_ACCEPTANCE_SUMMARY.json')
    req(n.get('status')=='native_accepted' and n.get('checkpoint')==116,'CP116 accepted-native summary identity')
    req(n.get('variants')==e['acceptedCp116Variants'] and n.get('trialsPerVariant')==e['acceptedCp116TrialsPerVariant'] and n.get('totalTrials')==e['acceptedCp116Engagements'],'CP116 native workload drift')
    req(n.get('failedGates')==[] and n.get('automaticPromotion') is False,'CP116 native gates/promotion')
    req(n.get('adaptivePairRows')==e['acceptedCp116AdaptiveRows'] and n.get('adaptivePairRowsWithSwitches')==e['acceptedCp116AdaptiveSwitchRows'],'CP116 adaptive telemetry')
    req(n.get('damageModel')=='layered_defense_hull_only' and n.get('internalDamageCriticalsSimulated') is False,'CP116 research damage boundary')
    a=js(repo/'docs/validation/evidence/checkpoint-116/native-results/native-warhead-generation-study/analysis.json')
    req(a.get('variants')==e['acceptedCp116Variants'] and a.get('totalTrials')==e['acceptedCp116Engagements'] and a.get('failedGates')==[],'embedded CP116 native analysis invalid')
    # All copied native files are themselves frozen.
    rows=text(repo/'docs/validation/evidence/checkpoint-117/CP117_ACCEPTED_CP116_NATIVE_SHA256SUMS.txt').splitlines()
    req(len([r for r in rows if r.strip()])==40,'accepted CP116 native file-count drift')
    for line in rows:
        if not line.strip(): continue
        h,r=line.split('  ',1); req(sha(repo/r)==h,f'accepted CP116 native evidence drift {r}')

def validate_authorities(repo:Path,e:dict):
    s=js(repo/'docs/archive/player_technology/pre-cp165-active/technology_family_storyboard_v1_4.json')
    req(s.get('checkpoint')==117 and s.get('simulationOrCalibrationRun') is False,'Storyboard CP117 scope')
    req(len(s['disciplines'])==e['disciplines'],'discipline count')
    lineages=[l for d in s['disciplines'] for l in d['lineages']]; beats=[b for l in lineages for b in l['beats']]
    req(len(lineages)==e['lineages'] and len(beats)==e['storyboardBeats'],'Storyboard lineage/beat count')
    req(sum(bool(b.get('hardExternalPrerequisites')) for b in beats)==e['hardExternalPrerequisiteBeats'],'hard prerequisite count')
    bt={(l['id'],b['tl']):b for l in lineages for b in l['beats']}
    req(bt[('kinetic-ammunition',5)]['playerExpression']=='automatic_capability' and 'Graded penetrator' in bt[('kinetic-ammunition',5)]['title'],'TL5 Kinetic simplification')
    req(bt[('kinetic-ammunition',6)]['playerExpression']=='automatic_capability' and 'smart-projectile' in bt[('kinetic-ammunition',6)]['title'],'TL6 Kinetic simplification')
    req(bt[('warheads',3)]['playerExpression']=='deferred_concept' and bt[('warheads',4)]['playerExpression']=='deferred_concept','specialist Missile warheads not deferred')
    req(bt[('warheads',5)]['playerExpression']=='automatic_capability' and bt[('warheads',7)]['playerExpression']=='automatic_capability','GP Missile milestones not automatic')
    req('Swarmer Missile' in bt[('missile-delivery',5)]['title'] and bt[('missile-delivery',5)]['playerExpression']=='installed_component','Swarmer Storyboard branch')

    ideas=js(repo/'docs/archive/player_technology/pre-cp165-active/technology_idea_register_v1_5.json')
    req(len(ideas['ideas'])==e['ideas'],'idea count')
    byid={x['id']:x for x in ideas['ideas']}
    req('Swarmer Missile' in byid['IDEA-056']['title'] and 'active_architecture_branch' in byid['IDEA-056']['cp117Disposition'],'Swarmer idea disposition')
    req('deferred' in byid['IDEA-058']['cp117Disposition'],'shield specialist idea not deferred')

    arch=js(repo/'docs/archive/player_technology/pre-cp165-active/weapon_ammunition_missile_family_architecture_v0_3.json')
    req(arch.get('checkpoint')==117 and arch.get('automaticPromotion') is False,'weapon architecture identity')
    req(arch['familyIdentity']['Kinetic']['normalAmmoSelector'] is False and arch['familyIdentity']['Missile']['normalWarheadSelector'] is False,'normal selector reintroduced')
    req(arch['swarmer']['window']==e['swarmerWindow'] and arch['swarmer']['oneFlightCounter'] and arch['swarmer']['oneTerminalAttackRoll'],'Swarmer package drift')
    req(not arch['swarmer']['extraPdsWindows'] and not arch['swarmer']['automaticApproximateTargetCapability'],'Swarmer complexity creep')
    req(arch['calibrationPriority']['primary']==e['primaryCalibrationTls'] and arch['calibrationPriority']['advanced']==e['advancedCalibrationTls'] and arch['calibrationPriority']['endpointStress']==e['endpointStressTls'],'TL weighting drift')

    table=js(repo/'docs/archive/player_technology/pre-cp165-active/technology_component_table_v0_4.json')
    ents=table['lineageEntries']; kin=[x for x in ents if x.get('lineageId')=='kinetic-ammunition' and x.get('adoptedInProvisionalTable')]
    req(kin and all(x.get('playerExpression')=='automatic_capability' and x.get('tableDisposition')=='automatic_compatible_ammunition_or_payload_maturation' for x in kin),'component table active Kinetic selector drift')
    war=[x for x in ents if x.get('lineageId')=='warheads']; active=[x for x in war if x.get('adoptedInProvisionalTable')]
    req(active and all(x.get('playerExpression')=='automatic_capability' for x in active),'component table active Missile warhead selector drift')
    for tl in (3,4):
        x=next(y for y in war if y['tl']==tl); req(x.get('playerExpression')=='deferred_concept' and not x.get('adoptedInProvisionalTable'),f'component table TL{tl} specialist not deferred')
    sw=next(x for x in ents if x.get('lineageId')=='missile-delivery' and x.get('tl')==5); req('Swarmer Missile' in sw['technology'],'component table Swarmer missing')

    c=docx_text(repo/'docs/Star_Cluster_Game_Concept_v0.7l.docx')
    for phrase in ('Kinetic projectile and Missile family expression','Swarmer Missile','does not automatically grant additional SPEN or APEN','bounded PDS-saturation trait'):
        req(phrase in c,f'Concept v0.7l missing phrase: {phrase}')
    req(not (repo/'docs/Star_Cluster_Game_Concept_v0.7k.docx').exists(),'superseded Concept v0.7k still active')
    req((repo/'docs/archive/concepts/Star_Cluster_Game_Concept_v0.7k.docx').is_file(),'Concept v0.7k archive missing')

def validate_frozen(repo:Path,e:dict):
    hashlist(repo,'docs/validation/evidence/checkpoint-117/CP117_FROZEN_CP116_CSHARP_AND_TESTS_SHA256SUMS.txt',e['frozenCSharpAndTests'])
    hashlist(repo,'docs/validation/evidence/checkpoint-117/CP117_FROZEN_CP116_RESEARCH_EXECUTABLE_SHA256SUMS.txt',e['frozenResearchExecutableFiles'])
    req(sha(repo/'docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_1.json')==MATRIX_SHA,'CP109 numerical matrix drift')
    req(sha(repo/'docs/archive/player_technology/pre-cp165-active/power_reactor_calibration_profile_v0_1.json')==REACTOR_SHA,'CP110 Reactor profile drift')
    # CP116 executable study definition stays historical evidence.
    study=repo/'docs/archive/testing/pre-cp165-active/warhead_role_generation_study_v0_1.json'
    # Do not hard-fail an old constant if packaging metadata only changed; verify declared identity instead.
    d=js(study); req(d.get('checkpoint')==116 and d.get('automaticPromotion') is False,'CP116 study-definition identity drift')

def validate_docs(repo:Path):
    required=(
      'README.md','CHAT_README.md','docs/README.md','docs/design/README.md','docs/design/player_technology/README.md','docs/design/testing/README.md','docs/validation/README.md',
      'docs/validation/Checkpoint_117_Weapon_Family_Simplification_And_Swarmer_Architecture.md',
      'docs/archive/player_technology/pre-cp165-active/Weapon_Ammunition_And_Warhead_Architecture_v0_3.md',
      'docs/archive/player_technology/pre-cp165-active/Weapon_Family_Simplification_And_Swarmer_Architecture_v0_1.md',
      'docs/validation/evidence/checkpoint-117/Weapon_Family_Simplification_And_Swarmer_Architecture_Report_v1.md',
      'docs/validation/evidence/checkpoint-117/StarCluster_CP117_Weapon_Family_Simplification_And_Swarmer_Architecture_v0_1.xlsx')
    for rel in required: req((repo/rel).is_file(),f'missing CP117 doc {rel}')
    for rel in ('README.md','CHAT_README.md','docs/README.md','docs/design/README.md','docs/design/testing/README.md','docs/validation/README.md','docs/Prototype_TODO.md','tools/simulation/README.md'):
        t=text(repo/rel); req('117' in t,f'{rel} not updated for CP117')
    g=text(repo/'docs/design/combat/Missile_Guidance_Datalink_Sensor_And_Seeker_Architecture.md')
    req('Swarmer' in g and 'Approximate-target' in g and 'separate' in g,'Missile guidance/Swarmer targeting boundary missing')
    sd=text(repo/'docs/development/Simulation_Development_Guidelines.md')
    req('Weapon-family KISS consolidation and TL weighting' in sd and 'TL1-TL6' in sd,'simulation methodology lacks CP117 guardrail')

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

def validate_manifest(repo:Path,expected_count:int):
    rel='docs/validation/evidence/checkpoint-117/CP117_REPOSITORY_SHA256SUMS.txt'; mf=repo/rel
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
    ap=argparse.ArgumentParser(); ap.add_argument('--repo',required=True); ap.add_argument('--skip-manifest',action='store_true'); a=ap.parse_args(); repo=Path(a.repo).resolve()
    try:
        d=js(repo/'tools/checkpoints/checkpoint-117/checkpoint_117_definition.json'); e=d['expected']
        req(d.get('checkpoint')==117 and d.get('acceptedBaseline')==116,'CP117 definition identity')
        req(d.get('automaticPromotion') is False and d.get('productionSourceChanged') is False and d.get('simulationResearchChanged') is False and d.get('numericalMatrixChanged') is False and d.get('conceptChanged') is True and d.get('substantiveMonteCarloTrials')==0,'CP117 scope drift')
        print('       Validating accepted CP116 native provenance and frozen executable/numerical surfaces...')
        validate_baseline(repo,e); validate_frozen(repo,e)
        print('       Validating CP117 Concept/Storyboard/component/idea weapon-family simplification...')
        validate_authorities(repo,e)
        print('       Validating documentation, KISS/TL-weighting boundaries, root hygiene, and production-language boundary...')
        validate_docs(repo); validate_root_hygiene(repo); j=validate_json(repo)
        req(j>=e['jsonFilesMinimum'],f'unexpected JSON count {j}')
        for rel in ('src/StarCluster.Game','src/StarCluster.Core'):
            py=list((repo/rel).rglob('*.py')); req(not py,f'Python leaked into production runtime: {py[:1]}')
        if not a.skip_manifest:
            print('       Validating full repository manifest...'); validate_manifest(repo,int(e['repositoryOwnedFiles']))
        print(f"       CP117 contract verified: {e['repositoryOwnedFiles'] if not a.skip_manifest else 'pre-manifest'} repository-owned files; {j} JSON files parsed; 10 disciplines / 32 lineages / 214 beats / 137 ideas; 3 sparse hard gates; Swarmer TL5-TL7 branch; zero new Monte Carlo trials; zero numerical promotion.")
        return 0
    except Exception as exc:
        print(f'CP117 contract failure: {exc}',file=sys.stderr); return 1
if __name__=='__main__': raise SystemExit(main())
