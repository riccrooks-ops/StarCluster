#!/usr/bin/env python3
from __future__ import annotations
import argparse, ast, hashlib, json, re, sys
from pathlib import Path

REPO_MANIFEST_SHA_CP114='484614c0daf20451b1cc5406d58934130c259a39a310d2da4db1c0856b099507'
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

def validate_cp114(repo:Path):
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

def validate_hotfix(repo:Path,d:dict):
    e=d['expected']
    study=repo/'docs/archive/testing/pre-cp165-active/weapon_family_payload_study_v0_2.json'
    req(sha(study)==CP115_STUDY_SHA,'CP115 study changed in hotfix')
    doc=js(study)
    req(doc['checkpoint']==115 and doc['acceptedBaseline']==114,'study identity drift')
    req(doc['trialsPerVariant']==e['nativeTrialsPerVariant'] and doc['authoringTrialsPerVariant']==e['authoringTrialsPerVariant'],'trial workload drift')
    req(len(doc['missileProfiles'])==e['missileProfiles'] and len(doc['kineticProfiles'])==e['kineticProfiles'] and len(doc['targetFixtures'])==e['targetFixtures'],'candidate/fixture count drift')
    src=text(repo/'tools/simulation/starcluster_research/weapon_family_analysis.py')
    req('adaptive-pair-switch-telemetry' not in src,'obsolete stochastic adaptive switch blocking gate remains')
    for needle in ('adaptivePairRows','adaptivePairRowsWithSwitches','adaptivePairSwitchTelemetryObserved'):
        req(needle in src,f'missing info-only adaptive telemetry {needle}')
    tree=ast.parse(src)
    for node in ast.walk(tree):
        if not isinstance(node,ast.If): continue
        names={n.id for n in ast.walk(node.test) if isinstance(n,ast.Name)}
        if 'trials' not in names: continue
        for n in ast.walk(ast.Module(body=node.body,type_ignores=[])):
            if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='append' and isinstance(n.func.value,ast.Name) and n.func.value.id=='failures':
                raise AssertionError(f'trial-count-dependent blocking gate remains at line {node.lineno}')
    tst=text(repo/'tools/simulation/tests/test_cp115_weapon_family.py')
    req('self.assertEqual(0, side.telemetry.payload_switches)' in tst and 'self.assertGreaterEqual(side.telemetry.payload_switches, 1)' in tst,'deterministic adaptive non-switch/switch probe missing')
    ps=text(repo/'tools/checkpoints/checkpoint-115a/apply_checkpoint_115a.ps1')
    for needle in ('summary.json','Failed gates:','Study output tail:','preflight_checkpoint_115a.py'):
        req(needle in ps,f'wrapper failure diagnostics/preflight missing {needle}')

def validate_study_shape(repo:Path,d:dict):
    sys.path.insert(0,str(repo/'tools/simulation'))
    from starcluster_research.weapon_family_analysis import validate_study, build_variants
    from starcluster_research.study import load_json
    study=load_json(repo/'docs/archive/testing/pre-cp165-active/weapon_family_payload_study_v0_2.json')
    errs=validate_study(study); req(not errs,f'weapon-family study invalid: {errs}')
    e=d['expected']; builds,variants=build_variants(repo,study)
    req(len(builds)==e['exactFillBuilds'],f'build count {len(builds)}')
    req(len(variants)==e['variants'],f'variant count {len(variants)}')
    counts={k:sum(v.scenario_group==k for v in variants) for k in ('missile_family_characteristic','kinetic_family_characteristic','energy_family_reference')}
    req(counts['missile_family_characteristic']==e['missileVariants'],'Missile variant count')
    req(counts['kinetic_family_characteristic']==e['kineticVariants'],'Kinetic variant count')
    req(counts['energy_family_reference']==e['energyReferenceVariants'],'Energy reference variant count')
    for b in builds:req(b.used_space==b.capacity,f'non-exact-fill build {b.id}: {b.used_space}/{b.capacity}')

def validate_authoring(repo:Path,d:dict):
    root=repo/'docs/validation/evidence/checkpoint-115/authoring'; e=d['expected']; a=js(root/'analysis.json')
    req(a.get('checkpoint')==115 and a.get('variants')==e['variants'],'authoring identity')
    req(a.get('trialsPerVariant')==e['authoringTrialsPerVariant'] and a.get('totalTrials')==e['authoringEngagements'],'authoring workload')
    req(a.get('failedGates')==[] and a.get('automaticPromotion') is False,'authoring gates/promotion')
    import csv
    rows=list(csv.DictReader((root/'variants.csv').open(encoding='utf-8-sig',newline='')))
    adaptive=[r for r in rows if str(r.get('side_a_profile','')).startswith('adaptive-pair::')]
    req(len(adaptive)==e['authoringAdaptiveRows'],f'authoring adaptive row count {len(adaptive)}')
    req(sum(float(r.get('mean_a_payload_switches') or 0)>0 for r in adaptive)==e['authoringAdaptiveRowsWithSwitches'],'historical authoring adaptive switches should remain zero')

def validate_native(path:Path|None,d:dict):
    if path is None:return
    e=d['expected']; a=js(path/'analysis.json')
    req(a.get('checkpoint')==115 and a.get('variants')==e['variants'],'native identity')
    req(a.get('trialsPerVariant')==e['nativeTrialsPerVariant'] and a.get('totalTrials')==e['nativeEngagements'],'native workload')
    req(a.get('failedGates')==[] and a.get('automaticPromotion') is False,'native gates/promotion')
    req(isinstance(a.get('adaptivePairRowsWithSwitches'),int),'native adaptive switch telemetry missing')

def validate_docs(repo:Path):
    req((repo/'docs/validation/Checkpoint_115a_Weapon_Family_Substantive_Gate_Hotfix.md').is_file(),'active CP115a runbook missing')
    req(not (repo/'docs/validation/Checkpoint_115_Weapon_Family_Payload_Characteristic_Space_Refinement.md').exists(),'failed CP115 runbook still active')
    req((repo/'docs/validation/archive/Checkpoint_115_Weapon_Family_Payload_Characteristic_Space_Refinement.md').is_file(),'CP115 runbook archive continuity missing')
    for rel in ('README.md','CHAT_README.md','docs/README.md','docs/validation/README.md','tools/simulation/README.md'):
        req('115a' in text(repo/rel).lower(),f'{rel} not updated for CP115a')
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
    req(count>650,f'unexpected JSON count {count}'); return count

def validate_manifest(repo:Path,expected_count:int):
    rel='docs/validation/evidence/checkpoint-115a/CP115A_REPOSITORY_SHA256SUMS.txt'; mf=repo/rel
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
        d=js(repo/'tools/checkpoints/checkpoint-115a/checkpoint_115a_definition.json'); e=d['expected']
        req(d['checkpoint']=='115a' and d['acceptedBaseline']==114 and d['correctsCandidateCheckpoint']==115,'CP115a definition identity')
        req(d['automaticPromotion'] is False and d['studyPopulationChanged'] is False and d['studyMechanicsChanged'] is False,'hotfix scope drift')
        print('       Validating accepted CP114 native provenance and frozen production/numerical surfaces...')
        validate_cp114(repo)
        validate_hash_list(repo,'docs/validation/evidence/checkpoint-115/CP114_FROZEN_CSHARP_PRODUCTION_TEST_SHA256SUMS.txt',e['frozenCSharpAndTests'])
        validate_hash_list(repo,'docs/validation/evidence/checkpoint-115/CP114_FROZEN_PRIOR_SIMULATION_SHA256SUMS.txt',e['frozenPriorSimulationFiles'])
        print('       Validating CP115a substantive-gate correction and unchanged study population...')
        validate_hotfix(repo,d); validate_study_shape(repo,d); validate_authoring(repo,d); validate_native(Path(a.native_results).resolve() if a.native_results else None,d)
        print('       Validating docs, root hygiene, JSON, and production-language boundary...')
        validate_root_hygiene(repo); validate_docs(repo); j=validate_json(repo)
        for rel in ('src/StarCluster.Game','src/StarCluster.Core'):
            py=list((repo/rel).rglob('*.py')); req(not py,f'Python leaked into production runtime: {py[:1]}')
        print('       Validating full repository manifest...')
        validate_manifest(repo,int(d['repositoryOwnedFiles']))
        print(f"       CP115a contract verified: {d['repositoryOwnedFiles']} repository-owned files; {j} JSON files parsed; unchanged 4,064-variant / 8,128,000-engagement CP115 study; stochastic adaptive switching is info-only; no production promotion.")
        return 0
    except Exception as exc:
        print(f'CP115a contract failure: {exc}',file=sys.stderr); return 1
if __name__=='__main__': raise SystemExit(main())
