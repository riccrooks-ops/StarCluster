#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys, unittest
from pathlib import Path

CP162_MAN='docs/validation/evidence/checkpoint-162/CP162_REPOSITORY_SHA256SUMS.txt'
CP162_MAN_SHA='a10d3627f3eb6d81d9b014ab6af068753915c495a5d261017335befed7a62d64'
PF4_SHA='7fd4dfbbe375586de2605361006db84b68f89767c76ba4b76da6cf5f48253155'
PROD_SHA='3088b0a9eb45f6bf505c24513e8bb2ac878819db4ab464ccfea330243c82f194'
CONCEPT_SHA='f76ca6ce488ccb5ad1352f7d38b8c3d4657c12ed64d0c93cc45d2db605cc632f'
PDS_SHA='1a731834a3956267aacbdde030561df2cef18121d91860cfbef1c5e851c10c99'
CP162_NATIVE_SHA='f782cd9a12a920c8582b13d0628b0da4733b6098d041edbfa2177f58fc8a8e67'
ALLOWED_DRIFT={
 'README.md','CHAT_README.md','docs/README.md','docs/Prototype_TODO.md','docs/validation/README.md','docs/design/testing/README.md','tools/simulation/README.md'
}

def req(v,msg):
    if not v: raise AssertionError(msg)
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def js(p:Path):return json.loads(p.read_text(encoding='utf-8-sig'))
def manifest(p:Path):
    out={}
    for line in p.read_text(encoding='utf-8-sig').splitlines():
        if line.strip():h,rel=line.split('  ',1);out[rel]=h
    return out
def count_suite(s):return sum(count_suite(x) if isinstance(x,unittest.TestSuite) else 1 for x in s)
def ps_balanced(p:Path)->bool:
    text=p.read_text(encoding='utf-8-sig');stack=[];pairs={')':'(',']':'[','}':'{'};state='normal';i=0
    while i<len(text):
        ch=text[i]
        if state=='comment':
            if ch=='\n':state='normal'
        elif state=='single':
            if ch=="'":
                if i+1<len(text) and text[i+1]=="'":i+=1
                else:state='normal'
        elif state=='double':
            if ch=='`':i+=1
            elif ch=='"':state='normal'
        else:
            if ch=='#':state='comment'
            elif ch=="'":state='single'
            elif ch=='"':state='double'
            elif ch in '([{':stack.append(ch)
            elif ch in ')]}':
                if not stack or stack[-1]!=pairs[ch]:return False
                stack.pop()
        i+=1
    return state in ('normal','comment') and not stack

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);a=ap.parse_args();repo=Path(a.repo).resolve()
    try:
        d=js(repo/'tools/checkpoints/checkpoint-163/checkpoint_163_definition.json')
        req(d['checkpoint']==163 and d['baseCheckpoint']==162,'identity')
        req(d['expectedPythonTests']==728 and d['expectedPythonTestModules']==54 and d['expectedFocusedCp163Tests']==36,'Python contract')
        req(d['expectedXunitTests']==934 and d['expectedScenarioRunnerSelfTests']==70 and d['expectedResearchParityCases']==25,'native regression contract')
        req(d['mainReactorSpace']==6 and d['mainReactorOffsetsFromPf4']==[-1,0,1],'Main Reactor local sweep')
        req(d['apuSpace']==2 and d['apuTrajectoryCount']==5 and d['apuMaturationBounds']==[5,6,7,8],'APU maturation surface')
        req(d['latePlus3BoundaryTls']==[8,9] and d['installationCountCapImposed'] is False,'APU boundary/stacking')
        req(d['uniqueTlLocalApuPoints']==16 and d['staticLegalStackSupportRows']==288 and d['staticResilienceRows']==330,'static scale')
        req(d['stochasticVariants']==1152 and d['stochasticTurnSamples']==5760000,'stochastic scale')
        req(d['combatContexts']==384 and d['combatCells']==1152 and d['substantiveCombatTrials']==2304000,'combat scale')
        req(not d['tuningAllowed'] and not d['automaticPromotion'] and not d['productionAuthorityChangesAllowed'],'promotion boundary')

        w=repo/'tools/checkpoints/checkpoint-163/apply_checkpoint_163.ps1';req(w.is_file() and ps_balanced(w),'PowerShell static parse guard')
        wt=w.read_text(encoding='utf-8-sig');req('starcluster_research.apu_maturation_calibration' in wt,'CP163 module entrypoint');req('CP163_console_output.txt' in wt and 'Start-Transcript' in wt,'console transcript')
        req('tools\\simulation\\run_starcluster_research.py' in wt,'package-safe parity entrypoint')

        req(sha(repo/'docs/design/player_technology/technology_research_execution_baseline_pending_finalization_v0_4.json')==PF4_SHA,'PF4 drift')
        req(sha(repo/'docs/design/player_technology/technology_numerical_matrix_v0_9.json')==PROD_SHA,'production matrix drift')
        req(sha(repo/'docs/archive/concepts/Star_Cluster_Game_Concept_v0.7x.docx')==CONCEPT_SHA,'Concept drift')
        req(sha(repo/'src/StarCluster.Core/Combat/Missiles/MissileInterceptionPhaseContext.cs')==PDS_SHA,'PDS drift')

        pm=repo/CP162_MAN;req(pm.is_file() and sha(pm)==CP162_MAN_SHA,'CP162 repository manifest drift')
        for rel,expected in manifest(pm).items():
            req((repo/rel).is_file(),f'missing CP162 file {rel}')
            if rel not in ALLOWED_DRIFT:req(sha(repo/rel)==expected,f'unexpected CP162 drift: {rel}')

        acc=repo/'docs/validation/evidence/checkpoint-163/accepted-cp162'
        req((acc/'CP162_NATIVE_RESULTS_ARCHIVE_SHA256.txt').read_text(encoding='utf-8-sig').strip()==CP162_NATIVE_SHA+'  StarCluster_CP162_native_results_20260830_182536.zip','CP162 native archive hash')
        ns=js(acc/'CP162_NATIVE_ACCEPTANCE_SUMMARY.json');req(ns['checkpoint']==162 and ns['pythonTestsPassed']==692 and ns['xunitPassed']==934 and ns['substantiveCombatTrials']==4140000 and ns['stochasticTurnSamples']==16560000 and ns['combatErrorTrials']==0,'CP162 native acceptance')

        sys.path.insert(0,str(repo/'tools/simulation'))
        from starcluster_research.apu_maturation_calibration import validate_study
        study=js(repo/'docs/archive/testing/pre-cp165-active/cp163_apu_maturation_and_stacking_resilience_study_v0_1.json');req(validate_study(study)==[],'study invalid')
        planned=js(repo/'docs/validation/evidence/checkpoint-163/planned-study/summary.json');req(planned['uniqueTlLocalApuPoints']==16 and planned['stochasticTurnSamples']==5760000 and planned['combatTrials']==2304000 and planned['combatCells']==1152,'planned scale')
        contract=js(repo/'docs/validation/evidence/checkpoint-163/cp163_apu_maturation_study_contract_v0_1.json');req(contract['acceptedBaseNativeArchiveSha256']==CP162_NATIVE_SHA and contract['researchExecutionMatrixSha256']==PF4_SHA,'study provenance');req(contract['apu']['space']==2 and contract['apu']['installationCountCapImposed'] is False,'APU contract')

        tests=sorted((repo/'tools/simulation/tests').glob('test_*.py'));req(len(tests)==54,f'Python modules {len(tests)}')
        suite=unittest.defaultTestLoader.discover(str(repo/'tools/simulation/tests'),pattern='test_*.py');req(count_suite(suite)==728,f'Python tests {count_suite(suite)}')
        req(not any(repo.glob('StarCluster_CP162_native_results_*.zip')),'raw CP162 results archive must remain externalized')
        print('CP163 preflight PASS: CP162 accepted; PF4/production/Concept frozen; 6-Space Main Reactor -1/0/+1; 2-Space APU flat/TL5/TL6/TL7/TL8 maturation plus TL8/TL9 +3 boundary; unrestricted stacking; 5.76M planned demand samples; 2.304M planned combats; 728/54 Python tests; no tuning or automatic promotion.')
        return 0
    except Exception as exc:
        print(f'CP163 preflight failure: {exc}',file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
