#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys, unittest
from pathlib import Path

CP163_MAN='docs/validation/evidence/checkpoint-163/CP163_REPOSITORY_SHA256SUMS.txt'
CP163_MAN_SHA='e70cd774073a6e450e6ad09e9c0c92a727526314e064b86ab6b24a8f579c0458'
PF4_SHA='7fd4dfbbe375586de2605361006db84b68f89767c76ba4b76da6cf5f48253155'
PROD_SHA='3088b0a9eb45f6bf505c24513e8bb2ac878819db4ab464ccfea330243c82f194'
CONCEPT_SHA='f76ca6ce488ccb5ad1352f7d38b8c3d4657c12ed64d0c93cc45d2db605cc632f'
PDS_SHA='1a731834a3956267aacbdde030561df2cef18121d91860cfbef1c5e851c10c99'
CP163_NATIVE_SHA='bf5d01dc0e8ea7770227ab359771a35148bfb431746e1560648ef9fa155ff1af'
ALLOWED_DRIFT={'README.md','CHAT_README.md','docs/README.md','docs/Prototype_TODO.md','docs/validation/README.md','docs/design/testing/README.md','tools/simulation/README.md'}

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
        d=js(repo/'tools/checkpoints/checkpoint-164/checkpoint_164_definition.json')
        req(d['checkpoint']==164 and d['baseCheckpoint']==163,'identity')
        req(d['expectedPythonTests']==760 and d['expectedPythonTestModules']==55 and d['expectedFocusedCp164Tests']==32,'Python contract')
        req(d['expectedXunitTests']==934 and d['expectedScenarioRunnerSelfTests']==70 and d['expectedResearchParityCases']==25,'native regression')
        req(d['mainReactorSpace']==6 and d['mainReactorOffsetsFromPf4']==[-1,0,1],'Main Reactor surface')
        req(d['apuSpace']==2 and d['selectedApuOperationalTpByTl']==[1,1,1,1,2,2,2,2,2],'selected APU')
        req(d['stackTiers']==[0,1,2,3,'MAX'] and d['installationCountCapImposed'] is False,'stack surface')
        req(d['stochasticVariants']==810 and d['stochasticTurnSamples']==4050000,'stochastic scale')
        req(d['combatContexts']==810 and d['combatCells']==810 and d['substantiveCombatTrials']==1620000,'combat scale')
        req(d['finalIsolatedPowerSweep'] and d['wholeSystemIntegrationNext'] and not d['tuningAllowed'] and not d['automaticPromotion'],'closure boundary')
        w=repo/'tools/checkpoints/checkpoint-164/apply_checkpoint_164.ps1';req(w.is_file() and ps_balanced(w),'PowerShell parse guard')
        wt=w.read_text(encoding='utf-8-sig');req('starcluster_research.power_closure_sweep' in wt,'CP164 module entrypoint');req('CP164_console_output.txt' in wt and 'Start-Transcript' in wt,'console transcript');req('tools\\simulation\\run_starcluster_research.py' in wt,'parity entrypoint')
        req(sha(repo/'docs/design/player_technology/technology_research_execution_baseline_pending_finalization_v0_4.json')==PF4_SHA,'PF4 drift')
        req(sha(repo/'docs/design/player_technology/technology_numerical_matrix_v0_9.json')==PROD_SHA,'production drift')
        req(sha(repo/'docs/archive/concepts/Star_Cluster_Game_Concept_v0.7x.docx')==CONCEPT_SHA,'Concept drift')
        req(sha(repo/'src/StarCluster.Core/Combat/Missiles/MissileInterceptionPhaseContext.cs')==PDS_SHA,'PDS drift')
        pm=repo/CP163_MAN;req(pm.is_file() and sha(pm)==CP163_MAN_SHA,'CP163 manifest drift')
        for rel,expected in manifest(pm).items():
            req((repo/rel).is_file(),f'missing CP163 file {rel}')
            if rel not in ALLOWED_DRIFT:req(sha(repo/rel)==expected,f'unexpected CP163 drift: {rel}')
        acc=repo/'docs/validation/evidence/checkpoint-164/accepted-cp163'
        req((acc/'CP163_NATIVE_RESULTS_ARCHIVE_SHA256.txt').read_text(encoding='utf-8-sig').strip()==CP163_NATIVE_SHA+'  StarCluster_CP163_native_results_20260830_191327.zip','CP163 native hash')
        ns=js(acc/'CP163_NATIVE_ACCEPTANCE_SUMMARY.json');req(ns['checkpoint']==163 and ns['pythonTestsPassed']==728 and ns['xunitPassed']==934 and ns['stochasticTurnSamples']==5760000 and ns['substantiveCombatTrials']==2304000 and ns['combatErrorTrials']==0,'CP163 acceptance')
        sys.path.insert(0,str(repo/'tools/simulation'))
        from starcluster_research.power_closure_sweep import validate_study
        study=js(repo/'docs/archive/testing/pre-cp165-active/cp164_final_isolated_power_economy_closure_study_v0_1.json');req(validate_study(study)==[],'study invalid')
        planned=js(repo/'docs/validation/evidence/checkpoint-164/planned-study/summary.json');req(planned['stochasticVariants']==810 and planned['stochasticTurnSamples']==4050000 and planned['combatCells']==810 and planned['combatTrials']==1620000,'plan scale')
        contract=js(repo/'docs/validation/evidence/checkpoint-164/cp164_final_power_closure_study_contract_v0_1.json');req(contract['acceptedBaseNativeArchiveSha256']==CP163_NATIVE_SHA and contract['researchExecutionMatrixSha256']==PF4_SHA,'contract provenance');req(contract['apu']['space']==2 and contract['apu']['operationalTpByTl']==[1,1,1,1,2,2,2,2,2] and contract['apu']['installationCountCapImposed'] is False,'contract APU')
        tests=sorted((repo/'tools/simulation/tests').glob('test_*.py'));req(len(tests)==55,f'Python modules {len(tests)}')
        suite=unittest.defaultTestLoader.discover(str(repo/'tools/simulation/tests'),pattern='test_*.py');req(count_suite(suite)==760,f'Python tests {count_suite(suite)}')
        req(not any(repo.glob('StarCluster_CP163_native_results_*.zip')),'raw CP163 results archive must remain externalized')
        print('CP164 preflight PASS: CP163 accepted; PF4/production/Concept frozen; final isolated 6-Space Main Reactor PF4-1/PF4/PF4+1 sweep; selected 2-Space APU +1 TL1-4/+2 TL5-9; 0/1/2/3/MAX stacks; 4.05M demand samples; 1.62M direct marginal combats; 760/55 Python tests; whole-system integration next.')
        return 0
    except Exception as exc:
        print(f'CP164 preflight failure: {exc}',file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
