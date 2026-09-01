#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path

MAN='docs/validation/evidence/checkpoint-164/CP164_REPOSITORY_SHA256SUMS.txt'
PF4_SHA='7fd4dfbbe375586de2605361006db84b68f89767c76ba4b76da6cf5f48253155'

def req(v,msg):
    if not v: raise AssertionError(msg)
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def js(p:Path):return json.loads(p.read_text(encoding='utf-8-sig'))
def manifest(p:Path):
    out={}
    for line in p.read_text(encoding='utf-8-sig').splitlines():
        if line.strip():h,rel=line.split('  ',1);out[rel]=h
    return out
def owned(repo:Path):
    out=set()
    for path in repo.rglob('*'):
        if not path.is_file():continue
        rel=path.relative_to(repo).as_posix();wrapped='/'+rel
        if rel.startswith(('out/','.git/')) or '/__pycache__/' in wrapped or rel.endswith('.pyc') or '/bin/' in wrapped or '/obj/' in wrapped or '/TestResults/' in wrapped or rel==MAN:continue
        if rel.startswith('StarCluster_CP164_native_results_') and rel.endswith('.zip'):continue
        out.add(rel)
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);ap.add_argument('--native-results',required=True);a=ap.parse_args();repo=Path(a.repo).resolve();nr=Path(a.native_results).resolve()
    try:
        man=manifest(repo/MAN);cur=owned(repo);req(set(man)==cur,f'manifest path drift added={sorted(cur-set(man))[:10]} missing={sorted(set(man)-cur)[:10]}');req(all(sha(repo/r)==h for r,h in man.items()),'manifest hash mismatch');req(len(man)>3380,'owned count did not advance')
        req(sha(repo/'docs/design/player_technology/technology_research_execution_baseline_pending_finalization_v0_4.json')==PF4_SHA,'PF4 hash drift')
        final=nr/'CP164_NATIVE_ACCEPTANCE_SUMMARY.json';ro=nr/'CP164_REPOSITORY_ONLY_ACCEPTANCE.json';s=js(final if final.exists() else ro)
        req(s['checkpoint']==164 and s['pythonTestsPassed']==760 and s['xunitPassed']==934 and s['researchParityPassed']==25 and s['cp164FocusedTestsPassed']==32,'regression acceptance')
        req(s['pendingFinalizationBaselineId']=='CP160-PF4' and s['pendingFinalizationMatrixSha256']==PF4_SHA,'PF4 authority')
        req(s['acceptedBaseCheckpoint']==163 and s['mainReactorSpace']==6 and s['mainReactorOffsets']=='-1,0,+1 from PF4','Main Reactor contract')
        req(s['apuSpace']==2 and s['apuOperationalTpByTl']=='1,1,1,1,2,2,2,2,2' and s['installationCountCapImposed'] is False and s['stackTiers']=='0,1,2,3,MAX','APU contract')
        req(s['plannedStochasticTurnSamples']==4050000 and s['plannedSubstantiveCombatTrials']==1620000 and s['combatCells']==810,'study scale')
        req(not s['tuningAllowed'] and not s['automaticPromotion'] and not s['productionAuthorityChanged'],'promotion boundary');req(s['finalIsolatedPowerSweep'] and s['wholeSystemIntegrationNext'] and s['selectionDeferredToAssessment'],'closure boundary')
        pl=js(nr/'power-closure-plan/summary.json');sm=js(nr/'power-closure-smoke/summary.json');st=js(nr/'static-power/summary.json')
        req(pl['stochasticVariants']==810 and pl['stochasticTurnSamples']==4050000 and pl['combatCells']==810 and pl['combatTrials']==1620000,'native plan')
        req(sm['passed'] and sm['probes']==4 and sm['combatTrials']==2,'native smoke')
        req(st['passed'] and st['legalPoweredArchitectures']==22482 and st['oneMainReactorArchitectures']==16741,'native static surface')
        tr=nr/'CP164_console_output.txt';req(tr.is_file() and tr.stat().st_size>0,'console transcript')
        if final.exists():
            req(s['repositoryOnlyAccepted'] and s['studyCompleted'],'final acceptance state');req(s['stochasticTurnSamples']==4050000 and s['stochasticVariantsCompleted']==810,'final stochastic scale');req(s['substantiveCombatTrials']==1620000 and s['combatCellsCompleted']==810 and s['combatErrorTrials']==0,'final combat scale')
            ss=js(nr/'stochastic-power/summary.json');cm=js(nr/'combat-merged/summary.json');req(ss['passed'] and ss['variants']==810 and ss['turnSamples']==4050000,'stochastic outputs');req(cm['passed'] and cm['batches']==9 and cm['cells']==810 and cm['combatTrials']==1620000 and cm['errorTrials']==0,'combat outputs')
            for tl in range(1,10):
                b=js(nr/f'combat-batches/TL{tl}/summary.json');req(b['passed'] and b['contexts']==90 and b['cells']==90 and b['combatTrials']==180000 and b['errorTrials']==0,f'TL{tl} batch')
        print(f'CP164 contract PASS: {len(man)} repository-owned files; PF4 frozen; final isolated 6-Space Main Reactor PF4-1/PF4/PF4+1 discrimination; selected 2-Space APU +1 TL1-4/+2 TL5-9; unrestricted 0/1/2/3/MAX stack surface; 4.05M demand samples; 1.62M direct marginal combats; whole-system integration next.')
        return 0
    except Exception as exc:
        print(f'CP164 contract failure: {exc}',file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
