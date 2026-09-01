#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys, unittest
from pathlib import Path

CP161_MAN='docs/validation/evidence/checkpoint-161/CP161_REPOSITORY_SHA256SUMS.txt'
CP161_MAN_SHA='9e4f9c8ffba86650636483c78a42b770878f59e780f4824ab293fccbaae556c0'
PF4_SHA='7fd4dfbbe375586de2605361006db84b68f89767c76ba4b76da6cf5f48253155'
PROD_SHA='3088b0a9eb45f6bf505c24513e8bb2ac878819db4ab464ccfea330243c82f194'
CONCEPT_SHA='f76ca6ce488ccb5ad1352f7d38b8c3d4657c12ed64d0c93cc45d2db605cc632f'
PDS_SHA='1a731834a3956267aacbdde030561df2cef18121d91860cfbef1c5e851c10c99'
CP161_NATIVE_SHA='10f1e967374f005087c93f16a72807069428869d82cdc2cac98d849ec14b363c'
ALLOWED_DRIFT={
 'README.md','CHAT_README.md','docs/README.md','docs/Prototype_TODO.md','docs/validation/README.md','docs/design/testing/README.md',
 'tools/simulation/README.md','tools/simulation/starcluster_research/ecology.py'
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
        d=js(repo/'tools/checkpoints/checkpoint-162/checkpoint_162_definition.json')
        req(d['checkpoint']==162 and d['baseCheckpoint']==161,'identity')
        req(d['expectedPythonTests']==692 and d['expectedPythonTestModules']==53 and d['expectedFocusedCp162Tests']==32,'Python contract')
        req(d['expectedXunitTests']==934 and d['expectedScenarioRunnerSelfTests']==70 and d['expectedResearchParityCases']==25,'native regression contract')
        req(d['mainReactorSpace']==6 and d['mainReactorOffsetsFromPf4']==[-1,0,1],'Main Reactor sweep')
        req(d['auxiliaryReactorSpaceSweep']==[1,2,3,4] and d['auxiliaryReactorTpSweep']==[1,2,3,4],'Aux Reactor sweep')
        req(d['installationCountCapImposed'] is False,'stacking cap must not be assumed')
        req(d['stochasticVariants']==8280 and d['stochasticTurnSamples']==16560000,'stochastic scale')
        req(d['combatContexts']==2760 and d['combatCells']==8280 and d['substantiveCombatTrials']==4140000,'combat scale')
        req(not d['tuningAllowed'] and not d['automaticPromotion'] and not d['productionAuthorityChangesAllowed'],'promotion boundary')

        w=repo/'tools/checkpoints/checkpoint-162/apply_checkpoint_162.ps1';req(w.is_file() and ps_balanced(w),'PowerShell static parse guard')
        wt=w.read_text(encoding='utf-8-sig');req('starcluster_research.reactor_aux_power_calibration' in wt,'CP162 module entrypoint');req('CP162_console_output.txt' in wt and 'Start-Transcript' in wt,'console transcript')
        req('tools\\simulation\\run_starcluster_research.py' in wt,'package-safe parity entrypoint')

        req(sha(repo/'docs/design/player_technology/technology_research_execution_baseline_pending_finalization_v0_4.json')==PF4_SHA,'PF4 drift')
        req(sha(repo/'docs/design/player_technology/technology_numerical_matrix_v0_9.json')==PROD_SHA,'production matrix drift')
        req(sha(repo/'docs/archive/concepts/Star_Cluster_Game_Concept_v0.7x.docx')==CONCEPT_SHA,'Concept drift')
        req(sha(repo/'src/StarCluster.Core/Combat/Missiles/MissileInterceptionPhaseContext.cs')==PDS_SHA,'PDS drift')

        pm=repo/CP161_MAN;req(pm.is_file() and sha(pm)==CP161_MAN_SHA,'CP161 repository manifest drift')
        for rel,expected in manifest(pm).items():
            req((repo/rel).is_file(),f'missing CP161 file {rel}')
            if rel not in ALLOWED_DRIFT:req(sha(repo/rel)==expected,f'unexpected CP161 drift: {rel}')

        acc=repo/'docs/validation/evidence/checkpoint-162/accepted-cp161';req((acc/'CP161_NATIVE_RESULTS_ARCHIVE_SHA256.txt').read_text(encoding='utf-8-sig').strip()==CP161_NATIVE_SHA+'  StarCluster_CP161_native_results_20260830_171756.zip','CP161 native archive hash')
        ns=js(acc/'CP161_NATIVE_ACCEPTANCE_SUMMARY.json');req(ns['checkpoint']==161 and ns['pythonTestsPassed']==660 and ns['xunitPassed']==934 and ns['substantiveCombatTrials']==4536000 and ns['combatErrorTrials']==0,'CP161 native acceptance')

        sys.path.insert(0,str(repo/'tools/simulation'))
        from starcluster_research.reactor_aux_power_calibration import validate_study,plan
        study=js(repo/'docs/archive/testing/pre-cp165-active/cp162_main_aux_reactor_joint_calibration_study_v0_1.json');req(validate_study(study)==[],'study invalid')
        planned=js(repo/'docs/validation/evidence/checkpoint-162/planned-study/summary.json');req(planned['stochasticTurnSamples']==16560000 and planned['combatTrials']==4140000 and planned['combatCells']==8280,'planned scale')
        contract=js(repo/'docs/validation/evidence/checkpoint-162/cp162_reactor_aux_study_contract_v0_1.json');req(contract['acceptedBaseNativeArchiveSha256']==CP161_NATIVE_SHA and contract['researchExecutionMatrixSha256']==PF4_SHA,'study provenance');req(contract['auxiliaryReactor']['installationCountCapImposed'] is False,'contract stacking cap')

        tests=sorted((repo/'tools/simulation/tests').glob('test_*.py'));req(len(tests)==53,f'Python modules {len(tests)}')
        suite=unittest.defaultTestLoader.discover(str(repo/'tools/simulation/tests'),pattern='test_*.py');req(count_suite(suite)==692,f'Python tests {count_suite(suite)}')
        req(not any(repo.glob('StarCluster_CP161_native_results_*.zip')),'raw CP161 results archive must remain externalized')
        print('CP162 preflight PASS: CP161 accepted; PF4/production/Concept frozen; 6-Space Main Reactor -1/0/+1; Aux Reactor 1-4 Space x +1-4 TP; unrestricted legal stacking; 16.56M planned demand samples; 4.14M planned combats; 692/53 Python tests; no tuning or automatic promotion.')
        return 0
    except Exception as exc:
        print(f'CP162 preflight failure: {exc}',file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
