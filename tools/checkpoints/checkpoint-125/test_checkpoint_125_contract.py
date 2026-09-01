#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path

def req(v,msg):
    if not v: raise AssertionError(msg)
def text(p): req(p.is_file(),f'Missing {p}'); return p.read_text(encoding='utf-8-sig')
def js(p): return json.loads(text(p))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def manifest(p):
    out={}
    for line in text(p).splitlines():
        if line.strip(): h,r=line.split('  ',1); out[r]=h
    return out

def validate_results(native:Path):
    s=js(native/'CP125_NATIVE_ACCEPTANCE_SUMMARY.json')
    req(s['checkpoint']==125 and s['acceptedInstrumentationBaseline']==124 and s['acceptedReferenceBaseline']==123,'native summary identity')
    req(s['pythonTestsPassed']==152 and s['researchParityPassed']==25,'test/parity counts')
    req(s['legalBuilds']==9427 and s['basePairings']==70034 and s['generatedVariants']==280136,'plan counts')
    req(s['buildOpponentTlCoverage']==84843 and s['pipelineSmokeTrials']==280136,'coverage/smoke counts')
    req(s['mixedTlShipsExecuted'] is False and s['sameTlComponentsPerShip'] is True,'pure-TL semantics')
    req(s['failedGates']==[],'native summary gates')
    plan=js(native/'pairing-plan/analysis.json')
    req(plan['failedGates']==[] and plan['canonicalPairPopulation']==44429451 and plan['plannedSubstantiveTrials']==56027200,'pairing plan')
    smoke=js(native/'full-pipeline-smoke/analysis.json')
    req(smoke['failedGates']==[] and smoke['totalTrials']==280136 and smoke['trialErrors']==0 and smoke['orderedTlCells']==81,'full pipeline smoke')
    if not s['repositoryOnly']:
        req(s['substantiveTrials']==56027200 and s['substantiveTrialsPerVariant']==200,'substantive workload')
        a=js(native/'pure-tl-whole-ladder-study/analysis.json')
        req(a['failedGates']==[] and a['variants']==280136 and a['basePairings']==70034,'substantive counts')
        req(a['totalTrials']==56027200 and a['trialErrors']==0 and a['orderedTlCells']==81,'substantive trial integrity')
        req(a['buildOpponentTlRows']==84843 and a['telemetryMetrics']==47,'analysis coverage')
        for f in ('variants.csv','tl_matchup_summary.csv','delta_tl_summary.csv','family_matchup_summary.csv','tl_telemetry_summary.csv','pairing_outcomes.csv','build_opponent_tl_summary.csv','movement_order_summary.csv'):
            req((native/'pure-tl-whole-ladder-study'/f).is_file(),f'missing substantive output {f}')
    else:
        req(s['substantiveTrials']==0,'RepositoryOnly must not run substantive trials')

def validate_manifest(repo:Path):
    p=repo/'docs/validation/evidence/checkpoint-125/CP125_REPOSITORY_SHA256SUMS.txt'; m=manifest(p)
    current=[]
    for path in repo.rglob('*'):
        if not path.is_file(): continue
        rel=path.relative_to(repo).as_posix()
        if rel.startswith(('out/','.git/')) or '/__pycache__/' in '/'+rel or rel.endswith('.pyc') or '/bin/' in '/'+rel or '/obj/' in '/'+rel: continue
        if rel=='docs/validation/evidence/checkpoint-125/CP125_REPOSITORY_SHA256SUMS.txt': continue
        current.append(rel)
    req(set(current)==set(m),f'manifest path drift missing={sorted(set(m)-set(current))[:5]} extra={sorted(set(current)-set(m))[:5]}')
    for rel,h in m.items(): req(sha(repo/rel)==h,f'manifest hash drift: {rel}')
    return len(m)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo',required=True); ap.add_argument('--native-results'); a=ap.parse_args(); repo=Path(a.repo).resolve()
    try:
        print('       Validating CP125 definition, accepted CP124 provenance, and whole-ladder authorities...')
        d=js(repo/'tools/checkpoints/checkpoint-125/checkpoint_125_definition.json'); req(d['checkpoint']==125,'definition')
        s=js(repo/'docs/validation/evidence/checkpoint-125/CP125_ACCEPTED_CP124_NATIVE_SUMMARY.json'); req(s['acceptedCheckpoint']==124 and s['failedGates']==[],'CP124 provenance')
        if a.native_results: validate_results(Path(a.native_results).resolve())
        print('       Parsing owned JSON corpus...')
        njson=0
        for p in repo.rglob('*.json'):
            rel=p.relative_to(repo).as_posix()
            if rel.startswith('out/') or '/bin/' in '/'+rel or '/obj/' in '/'+rel: continue
            json.loads(p.read_text(encoding='utf-8-sig')); njson+=1
        print('       Validating full repository manifest...')
        n=validate_manifest(repo)
        print(f'       CP125 contract verified: {n} repository-owned files; {njson} JSON files; 9,427 pure-TL builds; 70,034 weighted pairings; 280,136 symmetry variants; 280,136 one-trial smoke; 56,027,200 substantive trials when normal; mixed-TL ships excluded.')
        return 0
    except Exception as e:
        print(f'CP125 contract failure: {e}',file=sys.stderr); return 1
if __name__=='__main__': raise SystemExit(main())
