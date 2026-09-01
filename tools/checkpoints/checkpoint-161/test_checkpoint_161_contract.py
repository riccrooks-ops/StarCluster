#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

MAN='docs/validation/evidence/checkpoint-161/CP161_REPOSITORY_SHA256SUMS.txt'
PF4_SHA='7fd4dfbbe375586de2605361006db84b68f89767c76ba4b76da6cf5f48253155'

def req(v,msg):
    if not v: raise AssertionError(msg)

def sha(path:Path)->str:
    h=hashlib.sha256();h.update(path.read_bytes());return h.hexdigest()

def js(path:Path):return json.loads(path.read_text(encoding='utf-8-sig'))

def manifest(path:Path):
    out={}
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        if line.strip():h,rel=line.split('  ',1);out[rel]=h
    return out

def owned(repo:Path):
    out=set()
    for path in repo.rglob('*'):
        if not path.is_file():continue
        rel=path.relative_to(repo).as_posix();wrapped='/'+rel
        if rel.startswith(('out/','.git/')) or '/__pycache__/' in wrapped or rel.endswith('.pyc') or '/bin/' in wrapped or '/obj/' in wrapped or '/TestResults/' in wrapped or rel==MAN:continue
        if rel.startswith('StarCluster_CP161_native_results_') and rel.endswith('.zip'):continue
        out.add(rel)
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);ap.add_argument('--native-results',required=True);args=ap.parse_args();repo=Path(args.repo).resolve();nr=Path(args.native_results).resolve()
    try:
        man=manifest(repo/MAN);cur=owned(repo)
        req(set(man)==cur,f'manifest path drift added={sorted(cur-set(man))[:10]} missing={sorted(set(man)-cur)[:10]}')
        req(all(sha(repo/rel)==expected for rel,expected in man.items()),'manifest hash mismatch')
        req(len(man)>3320,'owned count did not advance')
        req(sha(repo/'docs/design/player_technology/technology_research_execution_baseline_pending_finalization_v0_4.json')==PF4_SHA,'PF4 hash drift')

        final_path=nr/'CP161_NATIVE_ACCEPTANCE_SUMMARY.json';repo_path=nr/'CP161_REPOSITORY_ONLY_ACCEPTANCE.json'
        summary=js(final_path if final_path.exists() else repo_path)
        req(summary['checkpoint']==161 and summary['pythonTestsPassed']==660 and summary['xunitPassed']==934 and summary['researchParityPassed']==25 and summary['cp161FocusedTestsPassed']==32,'regression acceptance')
        req(summary['pendingFinalizationBaselineId']=='CP160-PF4' and summary['pendingFinalizationMatrixSha256']==PF4_SHA,'PF4 execution authority')
        req(summary['legalPoweredArchitectures']==22482 and summary['oneReactorArchitectures']==16741 and summary['twoReactorArchitectures']==5741,'architecture contract')
        req(summary['representativeLoadouts']==108 and summary['stochasticVariants']==648 and summary['plannedStochasticTurnSamples']==7776000,'stochastic plan')
        req(summary['combatContexts']==324 and summary['combatCells']==2268 and summary['plannedSubstantiveCombatTrials']==4536000,'combat plan')
        req(summary['optionalSecondReactorIncluded'] and summary['isolatedAuxMagnitudeArchitectureRemainClosed'],'architecture/AUX boundary')
        req(summary['poweredAuxTpCostsRemainProvisional'] and summary['repairDroneIntegratedComponentDamageExecutionDeferred'],'resource/integration boundary')
        req(not summary['tuningAllowed'] and not summary['automaticPromotion'] and not summary['productionAuthorityChanged'],'promotion boundary')
        req(summary['selectionDeferredToNextCheckpoint'],'selection boundary')

        plan=js(nr/'reactor-tp-plan/summary.json');smoke=js(nr/'reactor-tp-smoke/summary.json');static=js(nr/'static-demand/summary.json')
        req(plan['combatTrials']==4536000 and plan['stochasticTurnSamples']==7776000,'native plan')
        req(smoke['passed'] and smoke['combatTrials']==3 and smoke['probes']==5,'native smoke')
        req(static['passed'] and static['legalPoweredArchitectures']==22482 and static['staticSupplyRows']==3132 and static['reactorSpaceRows']==45 and static['costSensitivityRows']==1368,'native static surface')
        transcript=nr/'CP161_console_output.txt';req(transcript.is_file() and transcript.stat().st_size>0,'console transcript')

        if final_path.exists():
            req(summary['repositoryOnlyAccepted'] and summary['studyCompleted'],'final acceptance state')
            req(summary['stochasticTurnSamples']==7776000 and summary['stochasticVariantsCompleted']==648,'final stochastic scale')
            req(summary['substantiveCombatTrials']==4536000 and summary['combatCellsCompleted']==2268 and summary['combatErrorTrials']==0,'final combat scale/error contract')
            ss=js(nr/'stochastic-demand/summary.json');cm=js(nr/'combat-merged/summary.json')
            req(ss['passed'] and ss['turnSamples']==7776000 and ss['variants']==648,'stochastic outputs')
            req(cm['passed'] and cm['batches']==9 and cm['cells']==2268 and cm['combatTrials']==4536000 and cm['errorTrials']==0,'combat merged outputs')
            for tl in range(1,10):
                b=js(nr/f'combat-batches/TL{tl}/summary.json');req(b['passed'] and b['contexts']==36 and b['cells']==252 and b['combatTrials']==504000 and b['errorTrials']==0,f'TL{tl} combat batch')

        print(f'CP161 contract PASS: {len(man)} repository-owned files; CP160-PF4 preserved; 2-30 TP/Space 4-8 diagnostic; 22,482 architectures; 7.776M planned stochastic samples; 4.536M planned combats; no tuning or automatic promotion.')
        return 0
    except Exception as exc:
        print(f'CP161 contract failure: {exc}',file=__import__('sys').stderr);return 1

if __name__=='__main__':raise SystemExit(main())
