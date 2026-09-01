#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re, subprocess, sys
from pathlib import Path
EXCLUDED_PARTS={'.git','.vs','.vscode','.idea','out','bin','obj','TestResults','__pycache__'}
EXCLUDED_FILES={'.DS_Store','Thumbs.db'}; EXCLUDED_SUFFIXES={'.pyc','.user','.userosscache','.sln.docstates','.uid','.suo'}
MANIFEST_REL='docs/validation/evidence/checkpoint-123/CP123_REPOSITORY_SHA256SUMS.txt'
def req(v,m):
    if not v: raise AssertionError(m)
def text(p): req(p.is_file(),f'Missing {p}'); return p.read_text(encoding='utf-8-sig')
def js(p): return json.loads(text(p))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def owned(rel):
    p=Path(rel); return not any(x in EXCLUDED_PARTS for x in p.parts) and p.name not in EXCLUDED_FILES and p.suffix.lower() not in EXCLUDED_SUFFIXES
def validate_definition(d):
    e=d['expected']; req(d['checkpoint']==123 and d['acceptedBaseline']==122 and d['referenceOnly'] and not d['automaticPromotion'],'definition identity')
    req(not d['productionSourceChanged'] and not d['scenarioDefinitionsChanged'] and not d['simulationMechanicsChanged'],'frozen implementation boundary')
    req(d['damagePointScale']==2 and not d['balanceCalibrationRun'] and d['newScenarioCount']==0 and d['substantiveMonteCarloTrials']==0 and not d['criticalCadenceMigrated'],'reference-only boundary')
    req(d['productionRepairHullPerKitTl1']==1,'DamCon TL1')
    req((e['pythonTests'],e['disciplines'],e['lineages'],e['storyboardBeats'],e['technologyTableEntries'],e['ideaRegisterEntries'],e['numericalProfileFamilies'])==(124,10,33,218,218,138,20),'expected counts')
    req(e['acceptedCp122XunitTests']==905 and e['acceptedCp122ScenarioRunnerSelfTests']==70 and e['acceptedCp122ResearchParityCases']==25 and e['acceptedCp122CanonicalParityCases']==234138 and e['acceptedCp122CanonicalParityMismatches']==0,'CP122 expected counts')
def validate_preflight(repo):
    r=subprocess.run([sys.executable,'-B',str(repo/'tools/checkpoints/checkpoint-123/preflight_checkpoint_123.py'),'--repo',str(repo)],capture_output=True,text=True)
    req(r.returncode==0,f'preflight failed\n{r.stdout}\n{r.stderr}')
def validate_docs(repo,d):
    for rel in d['primaryAuthorities']: req((repo/rel).is_file(),f'primary authority missing {rel}')
    for rel in ('README.md','CHAT_README.md','docs/README.md','docs/design/README.md','docs/design/player_technology/README.md','docs/design/testing/README.md','docs/validation/README.md','docs/Prototype_TODO.md'):
        t=text(repo/rel).lower(); req('123' in t,f'{rel} missing CP123')
    rb=text(repo/'README.md').lower()
    for phrase in ('reference-only','scenario definitions','0 substantive monte carlo','218 unique','swarmer','maneuvering','damage control'): req(phrase in rb,f'root README missing {phrase}')
def validate_wrapper(repo):
    t=text(repo/'tools/checkpoints/checkpoint-123/apply_checkpoint_123.ps1')
    for tok in ('[switch]$RepositoryOnly','Python 3.13','preflight_checkpoint_123.py','test_checkpoint_123_contract.py','124/124','CP123_NATIVE_ACCEPTANCE_SUMMARY.json','substantiveMonteCarloTrials=0','newScenarioCount=0','prepackage_repository_hygiene.py'): req(tok in t,f'wrapper missing {tok}')
    for bad in ('dotnet build','dotnet test','scenario-study.py','weapon_family_analysis.py','--trials'): req(bad not in t.lower(),f'wrapper unexpectedly invokes {bad}')
def validate_json(repo):
    n=0
    for p in repo.rglob('*.json'):
        rel=p.relative_to(repo).as_posix()
        if not owned(rel): continue
        json.loads(p.read_text(encoding='utf-8-sig')); n+=1
    return n
def validate_native(path):
    s=js(path/'CP123_NATIVE_ACCEPTANCE_SUMMARY.json')
    req(s['checkpoint']==123 and s['acceptedBaseline']==122 and s['referenceOnly'],'native identity')
    req(not s['productionSourceChanged'] and not s['scenarioDefinitionsChanged'] and not s['simulationMechanicsChanged'],'native frozen boundary')
    req(s['pythonTests']==124 and s['pythonTestsPassed']==124,'native Python tests')
    req((s['disciplines'],s['lineages'],s['storyboardBeats'],s['technologyTableEntries'],s['ideaRegisterEntries'],s['numericalProfileFamilies'])==(10,33,218,218,138,20),'native counts')
    req(s['damagePointScale']==2 and s['productionRepairHullPerKitTl1']==1 and not s['criticalCadenceMigrated'],'native scale/DamCon')
    req(s['newScenarioCount']==0 and s['substantiveMonteCarloTrials']==0 and not s['balanceValidated'] and s['failedGates']==[],'native no-study')
def validate_manifest(repo,count):
    mf=repo/MANIFEST_REL; exp={}
    for line in text(mf).splitlines():
        if not line.strip(): continue
        mm=re.fullmatch(r'([0-9a-f]{64})  (.+)',line); req(mm is not None,f'bad manifest row {line}'); h,r=mm.groups(); exp[r]=h
    req(len(exp)==count,f'manifest count {len(exp)} != {count}')
    actual=sorted(p.relative_to(repo).as_posix() for p in repo.rglob('*') if p.is_file() and p.relative_to(repo).as_posix()!=MANIFEST_REL and owned(p.relative_to(repo).as_posix()))
    req(actual==sorted(exp),f'manifest path mismatch')
    for rel in actual: req(sha(repo/rel)==exp[rel],f'manifest hash mismatch {rel}')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo',required=True); ap.add_argument('--native-results'); ap.add_argument('--skip-manifest',action='store_true'); a=ap.parse_args(); repo=Path(a.repo).resolve()
    try:
        d=js(repo/'tools/checkpoints/checkpoint-123/checkpoint_123_definition.json'); validate_definition(d)
        print('       Validating CP123 preflight/reference authorities and documentation...'); validate_preflight(repo); validate_docs(repo,d); validate_wrapper(repo)
        print('       Parsing owned JSON corpus...'); n=validate_json(repo); req(n>=d['expected']['jsonFilesMinimum'],f'JSON count {n} below minimum')
        if a.native_results: print('       Validating compact CP123 native/reference evidence...'); validate_native(Path(a.native_results).resolve())
        if not a.skip_manifest: print('       Validating full repository manifest...'); validate_manifest(repo,int(d['expected']['repositoryOwnedFiles']))
        print(f"       CP123 contract verified: {d['expected']['repositoryOwnedFiles'] if not a.skip_manifest else 'pre-manifest'} repository-owned files; {n} JSON files; 218 exact Storyboard/Tech-Table beats; 20x9 reference profiles; frozen implementation/scenario surface; 0 Monte Carlo trials.")
        return 0
    except Exception as e:
        print(f'CP123 contract failure: {e}',file=sys.stderr); return 1
if __name__=='__main__': raise SystemExit(main())
