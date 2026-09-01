#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
MAN='docs/validation/evidence/checkpoint-159/CP159_REPOSITORY_SHA256SUMS.txt'
def req(x,m):
    if not x: raise AssertionError(m)
def sha(p):
    h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()
def js(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def manifest(p):
    out={}
    for line in p.read_text(encoding='utf-8-sig').splitlines():
        if line.strip(): h,r=line.split('  ',1); out[r]=h
    return out
def owned(repo):
    out=set()
    for p in repo.rglob('*'):
        if not p.is_file(): continue
        r=p.relative_to(repo).as_posix(); w='/'+r
        if r.startswith(('out/','.git/')) or '/__pycache__/' in w or r.endswith('.pyc') or '/bin/' in w or '/obj/' in w or '/TestResults/' in w or r==MAN: continue
        if r.startswith('StarCluster_CP159_native_results_') and r.endswith('.zip'): continue
        out.add(r)
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo',required=True); ap.add_argument('--native-results',required=True); a=ap.parse_args(); repo=Path(a.repo).resolve(); nr=Path(a.native_results).resolve()
    try:
        man=manifest(repo/MAN); cur=owned(repo); req(set(man)==cur,f'manifest path drift added={sorted(cur-set(man))[:10]} missing={sorted(set(man)-cur)[:10]}'); req(all(sha(repo/r)==h for r,h in man.items()),'manifest hash mismatch'); req(len(man)>3295,'owned count did not advance')
        p=nr/'CP159_NATIVE_ACCEPTANCE_SUMMARY.json'; ro=nr/'CP159_REPOSITORY_ONLY_ACCEPTANCE.json'; s=js(p if p.exists() else ro)
        req(s['checkpoint']==159 and s['pythonTestsPassed']==604 and s['xunitPassed']==934 and s['researchParityPassed']==25 and s['cp159FocusedTestsPassed']==30,'regression acceptance')
        req(s['pendingFinalizationBaselineId']=='CP159-PF3' and not s['productionAuthorityChanged'] and not s['automaticPostStudyPromotion'],'authority boundary')
        req(s['architectureSmokeCombats']==2 and s['architectureSmokeMicroProbes']==1 and s['fieldCandidateTlPoints']==99 and s['crystallineCandidateTlPoints']==40,'plan/smoke')
        if p.exists():
            req(s['repositoryOnlyAccepted'] and s['substantiveCombatTrials']==3390000 and s['repairDroneMicroTrials']==1728000,'full scale')
            req(s['baselineCombatTrials']==120000 and s['fieldScreenCombatTrials']==891000 and s['crystallineScreenCombatTrials']==960000 and s['fieldDeepCombatTrials']==378000 and s['crystallineDeepCombatTrials']==960000 and s['fieldHardenerInteractionCombatTrials']==81000,'stage totals')
            req(s['substantiveErrors']==0 and s['substantiveTurnCapSentinels']==0,'substantive errors/caps')
            req(s['fieldDeepPackages']==7 and s['crystallineDeepPackages']==6 and s['fieldHardenerInteractionPackages']==9,'deep structure')
            req(s['repairDroneSameTargetRerollAllowed']==False and s['repairDroneExtraKitMaximumEqualsDefault']==True,'Drone semantics')
        print(f'CP159 contract PASS: {len(man)} repository-owned files; CP159-PF3 pending-finalization AUX authority preserved; 3,390,000 specialist/headroom combats + 1,728,000 Damage-Control Drone microtrials; production authority unchanged; Reactor/TP deferred.')
        return 0
    except Exception as e:
        print(f'CP159 contract failure: {e}',file=__import__('sys').stderr); return 1
if __name__=='__main__': raise SystemExit(main())
