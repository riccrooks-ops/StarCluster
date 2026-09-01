#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json,re,sys
from collections import Counter
from pathlib import Path

EXCLUDED_PARTS={'.git','.vs','.vscode','.idea','out','bin','obj','TestResults','__pycache__'}
EXCLUDED_FILES={'.DS_Store','Thumbs.db'}
EXCLUDED_SUFFIXES={'.pyc','.user','.userosscache','.sln.docstates','.uid','.suo'}
EXPECTED_CP111_MANIFEST_SHA='4e4fbc1e5422a102308b6a4c229b78867320bff98a3770e60680c879a78a1e36'
EXPECTED_MATRIX_SHA='91cb29f7e1e0f792e5a2258b1ab0655fe9924c768f4d80b645269fae52384000'
EXPECTED_REACTOR_SHA='ebed51fa16d0ee1c9721b55ca135eb81e23c321a8373dfcb826a1a096371e9a6'
EXPECTED_CONCEPT_SHA='50f522b6cf5c11d89b5e8e93b33f47da36baa0c1d267acfe8be07872f93a461d'

def req(x,msg):
    if not x: raise AssertionError(msg)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def text(p): req(p.is_file(),f'Missing {p}'); return p.read_text(encoding='utf-8-sig')
def js(p): return json.loads(text(p))
def csvrows(p):
    req(p.is_file(),f'Missing {p}')
    with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def owned(rel):
    p=Path(rel)
    if any(x in EXCLUDED_PARTS for x in p.parts) or p.name in EXCLUDED_FILES:return False
    return not any(p.name.lower().endswith(s) for s in EXCLUDED_SUFFIXES)

def validate_hash_list(repo,rel,expected):
    rows=[x for x in text(repo/rel).splitlines() if x.strip()]; req(len(rows)==expected,f'{rel} count {len(rows)} != {expected}')
    for line in rows:
        m=re.fullmatch(r'([0-9a-f]{64})  (.+)',line); req(m is not None,f'bad hash row {line}')
        h,r=m.groups(); p=repo/r; req(p.is_file(),f'missing frozen {r}'); req(sha(p)==h,f'frozen drift {r}')

def validate_cp111_native(repo):
    root=repo/'docs/validation/evidence/checkpoint-111/native'
    st=js(root/'self-test/summary.json'); req(st.get('passed') is True and st['tests']=={'run':31,'failures':0,'errors':0,'skipped':0},'CP111 native self-test evidence')
    pa=js(root/'parity/summary.json'); req(pa.get('passed') is True and pa.get('cases')==25 and pa.get('errors')==[],'CP111 native parity evidence')
    an=js(root/'same-tl-ecology/analysis.json'); req(an.get('checkpoint')=='111' and an.get('totalTrials')==1188000 and an.get('trialsPerVariant')==1000,'CP111 native substantive scale')
    req(an.get('failedGates')==[] and an.get('automaticPromotion') is False,'CP111 native substantive gates')

def validate_output(root,trials,label):
    an=js(root/'analysis.json'); req(an.get('checkpoint')=='112',f'{label} checkpoint'); req(an.get('damageModel')=='layered_defense_hull_only' and an.get('internalDamageCriticalsSimulated') is False,f'{label} damage scope')
    req(an.get('variants')==1200 and an.get('trialsPerVariant')==trials and an.get('totalTrials')==1200*trials,f'{label} scale')
    req(an.get('scenarioVariantCounts')=={'energy_defense_ablation':1056,'movement_order_geometry':24,'missile_attrition_ablation':120},f'{label} variant shape')
    req(an.get('failedGates')==[] and an.get('automaticPromotion') is False,f'{label} gates')
    req(len(csvrows(root/'variants.csv'))==1200,f'{label} variants rows')
    req(len(csvrows(root/'energy_defense_ablation.csv'))==48,f'{label} energy rows')
    req(len(csvrows(root/'movement_order_geometry.csv'))==12,f'{label} movement rows')
    req(len(csvrows(root/'missile_attrition_ablation.csv'))==60,f'{label} missile rows')
    for r in csvrows(root/'builds.csv'):
        req(int(r['free_space'])==0 and int(r['used_space'])==int(r['capacity']),f'{label} non exact-fill {r["build_id"]}')

def validate_manifest(repo,expected_count):
    mf=repo/'CHECKPOINT_112_SHA256SUMS.txt'; req(mf.is_file(),'missing CP112 manifest')
    exp={}
    for line in text(mf).splitlines():
        if not line.strip():continue
        m=re.fullmatch(r'([0-9a-f]{64})  (.+)',line);req(m is not None,f'bad manifest row {line}')
        h,r=m.groups();exp[r]=h
    req(len(exp)==expected_count,f'manifest count {len(exp)} != {expected_count}')
    actual=[]
    for p in repo.rglob('*'):
        if p.is_file():
            r=p.relative_to(repo).as_posix()
            if r!='CHECKPOINT_112_SHA256SUMS.txt' and owned(r):actual.append(r)
    actual=sorted(actual); req(actual==sorted(exp),f'manifest path-set mismatch missing={sorted(set(exp)-set(actual))[:5]} extra={sorted(set(actual)-set(exp))[:5]}')
    for r in actual:req(sha(repo/r)==exp[r],f'manifest hash mismatch {r}')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);ap.add_argument('--runtime-output');a=ap.parse_args();repo=Path(a.repo).resolve()
    try:
        print('       Validating accepted CP111 native provenance and frozen authorities...')
        req(sha(repo/'CHECKPOINT_111_SHA256SUMS.txt')==EXPECTED_CP111_MANIFEST_SHA,'CP111 manifest hash drift')
        validate_cp111_native(repo)
        validate_hash_list(repo,'docs/validation/evidence/checkpoint-112/CP111_FROZEN_CSHARP_PRODUCTION_TEST_SHA256SUMS.txt',561)
        req(sha(repo/'docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_1.json')==EXPECTED_MATRIX_SHA,'matrix drift')
        req(sha(repo/'docs/archive/player_technology/pre-cp165-active/power_reactor_calibration_profile_v0_1.json')==EXPECTED_REACTOR_SHA,'reactor profile drift')
        req(sha(repo/'docs/Star_Cluster_Game_Concept_v0.7j.docx')==EXPECTED_CONCEPT_SHA,'Concept drift')

        print('       Validating CP112 causal study architecture and bounded evidence...')
        d=js(repo/'tools/checkpoints/checkpoint-112/checkpoint_112_architecture_definition.json')
        req(d['acceptedBaseline']=='111' and d['checkpointType']=='causal_build_neighbor_ablation_diagnostics','definition identity')
        req(d['productionSourceChanged'] is False and d['conceptChanged'] is False and d['numericalMatrixChanged'] is False and d['reactorCandidateChanged'] is False,'authority change flags')
        req(d['variantPopulations']=={'energyDefenseAblation':1056,'movementOrderGeometry':24,'missileAttritionAblation':120,'total':1200},'definition population')
        req(d['nativeSubstantiveWorkload']=={'trialsPerVariant':2000,'totalEngagements':2400000},'native workload')
        study=js(repo/'docs/archive/testing/pre-cp165-active/build_neighbor_ablation_study_v0_1.json')
        req(study['schemaVersion']=='star-cluster-build-neighbor-ablation-v0.1' and study['checkpoint']=='112','study identity')
        req(study['trialsPerVariant']==2000 and study['masterSeed']==11220260815,'study scale/seed')
        req(study['mixedTlPopulation']=={'registered':True,'executed':False,'populationWeight':0},'mixed TL separation')
        req(study['automaticPromotion'] is False and study['internalDamageCriticalsSimulated'] is False,'study guardrails')
        sys.path.insert(0,str(repo/'tools/simulation'))
        from starcluster_research.neighbor_analysis import build_variants,validate_study
        req(validate_study(study)==[],'study validator')
        builds,variants=build_variants(repo,study); req(len(variants)==1200,'generated variants')
        req(all(b.used_space==b.capacity for b in builds),'generated exact-fill')
        req(Counter(v.scenario_group for v in variants)==Counter({'energy_defense_ablation':1056,'movement_order_geometry':24,'missile_attrition_ablation':120}),'generated scenario counts')
        validate_output(repo/'docs/validation/evidence/checkpoint-112/local-authoring',100,'checked-in CP112 authoring')
        st=js(repo/'docs/validation/evidence/checkpoint-112/CP112_PYTHON_SELF_TEST_SUMMARY.json'); req(st.get('passed') is True and st['tests']=={'run':36,'failures':0,'errors':0,'skipped':0},'CP112 self tests')
        pa=js(repo/'docs/validation/evidence/checkpoint-112/CP112_PARITY_SUMMARY.json'); req(pa.get('passed') is True and pa.get('cases')==25 and pa.get('errors')==[],'CP112 parity')

        print('       Validating documentation, runtime boundary, and full repository manifest...')
        req('Checkpoint 111 is the current native-accepted' in text(repo/'CHAT_README.md'),'chat handoff')
        req('2,400,000 engagements' in text(repo/'docs/validation/Checkpoint_112_Build_Neighbor_And_Ablation_Diagnostics.md'),'runbook workload')
        for rel in ('src/StarCluster.Game','src/StarCluster.Core'):
            py=list((repo/rel).rglob('*.py')); req(not py,f'Python leaked into production {py[:1]}')
        validate_manifest(repo,int(d['repositoryOwnedFiles']))
        if a.runtime_output:
            print('       Validating native CP112 substantive output...')
            validate_output((repo/a.runtime_output).resolve() if not Path(a.runtime_output).is_absolute() else Path(a.runtime_output),2000,'native CP112')
        print(f"       CP112 contract verified: {d['repositoryOwnedFiles']} repository-owned files; 561 frozen C#/test files; 1,200 targeted variants; 2,400,000 native engagements; zero automatic promotion.")
        return 0
    except Exception as e:
        print(f'CP112 contract failure: {e}',file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
