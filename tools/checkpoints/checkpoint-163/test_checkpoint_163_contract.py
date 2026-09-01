#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

MAN='docs/validation/evidence/checkpoint-163/CP163_REPOSITORY_SHA256SUMS.txt'
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
        if rel.startswith('StarCluster_CP163_native_results_') and rel.endswith('.zip'):continue
        out.add(rel)
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);ap.add_argument('--native-results',required=True);a=ap.parse_args();repo=Path(a.repo).resolve();nr=Path(a.native_results).resolve()
    try:
        man=manifest(repo/MAN);cur=owned(repo);req(set(man)==cur,f'manifest path drift added={sorted(cur-set(man))[:10]} missing={sorted(set(man)-cur)[:10]}');req(all(sha(repo/r)==h for r,h in man.items()),'manifest hash mismatch');req(len(man)>3375,'owned count did not advance')
        req(sha(repo/'docs/design/player_technology/technology_research_execution_baseline_pending_finalization_v0_4.json')==PF4_SHA,'PF4 hash drift')
        final=nr/'CP163_NATIVE_ACCEPTANCE_SUMMARY.json';ro=nr/'CP163_REPOSITORY_ONLY_ACCEPTANCE.json';s=js(final if final.exists() else ro)
        req(s['checkpoint']==163 and s['pythonTestsPassed']==728 and s['xunitPassed']==934 and s['researchParityPassed']==25 and s['cp163FocusedTestsPassed']==36,'regression acceptance')
        req(s['pendingFinalizationBaselineId']=='CP160-PF4' and s['pendingFinalizationMatrixSha256']==PF4_SHA,'PF4 authority')
        req(s['acceptedBaseCheckpoint']==162 and s['mainReactorSpace']==6 and s['mainReactorOffsets']=='-1,0,+1 from PF4','Main Reactor contract')
        req(s['apuSpace']==2 and s['apuTrajectoryCount']==5 and s['uniqueTlLocalApuPoints']==16 and s['installationCountCapImposed'] is False,'APU maturation/stacking contract')
        req(s['staticLegalStackSupportRows']==288 and s['staticResilienceRows']==330,'static/resilience contract')
        req(s['plannedStochasticTurnSamples']==5760000 and s['plannedSubstantiveCombatTrials']==2304000 and s['combatCells']==1152,'study scale')
        req(not s['tuningAllowed'] and not s['automaticPromotion'] and not s['productionAuthorityChanged'],'promotion boundary');req(s['selectionDeferredToNextCheckpoint'],'selection boundary')
        pl=js(nr/'apu-maturation-plan/summary.json');sm=js(nr/'apu-maturation-smoke/summary.json');st=js(nr/'static-apu/summary.json')
        req(pl['stochasticVariants']==1152 and pl['stochasticTurnSamples']==5760000 and pl['combatCells']==1152 and pl['combatTrials']==2304000,'native plan')
        req(sm['passed'] and sm['probes']==6 and sm['combatTrials']==2,'native smoke')
        req(st['passed'] and st['legalPoweredArchitectures']==22482 and st['oneMainReactorArchitectures']==16741 and st['uniqueTlLocalApuPoints']==16 and st['legalStackSupportRows']==288 and st['resilienceRows']==330,'native static surface')
        tr=nr/'CP163_console_output.txt';req(tr.is_file() and tr.stat().st_size>0,'console transcript')
        if final.exists():
            req(s['repositoryOnlyAccepted'] and s['studyCompleted'],'final acceptance state');req(s['stochasticTurnSamples']==5760000 and s['stochasticVariantsCompleted']==1152,'final stochastic scale');req(s['substantiveCombatTrials']==2304000 and s['combatCellsCompleted']==1152 and s['combatErrorTrials']==0,'final combat scale')
            ss=js(nr/'stochastic-apu/summary.json');cm=js(nr/'combat-merged/summary.json');req(ss['passed'] and ss['variants']==1152 and ss['turnSamples']==5760000,'stochastic outputs');req(cm['passed'] and cm['batches']==9 and cm['cells']==1152 and cm['combatTrials']==2304000 and cm['errorTrials']==0,'combat outputs')
            exp={1:(24,72,144000),2:(24,72,144000),3:(24,72,144000),4:(24,72,144000),5:(48,144,288000),6:(48,144,288000),7:(48,144,288000),8:(72,216,432000),9:(72,216,432000)}
            for tl,(ctx,cells,trials) in exp.items():
                b=js(nr/f'combat-batches/TL{tl}/summary.json');req(b['passed'] and b['contexts']==ctx and b['cells']==cells and b['combatTrials']==trials and b['errorTrials']==0,f'TL{tl} batch')
        print(f'CP163 contract PASS: {len(man)} repository-owned files; PF4 frozen; 6-Space Main Reactor -1/0/+1; 2-Space APU maturation at TL5/TL6/TL7/TL8 plus late +3 boundary; unrestricted stacking; 5.76M demand samples; 2.304M combats; no tuning or automatic promotion.')
        return 0
    except Exception as exc:
        print(f'CP163 contract failure: {exc}',file=__import__('sys').stderr);return 1
if __name__=='__main__':raise SystemExit(main())
