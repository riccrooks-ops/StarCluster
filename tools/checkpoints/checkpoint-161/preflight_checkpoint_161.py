#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys, unittest
from pathlib import Path

CP160_MAN = 'docs/validation/evidence/checkpoint-160/CP160_REPOSITORY_SHA256SUMS.txt'
CP160_MAN_SHA = '3beb2ae50320911c68d8541213010404fdd5ed2a8a62181ac4bcfc0190c4cee2'
PROD_SHA = '3088b0a9eb45f6bf505c24513e8bb2ac878819db4ab464ccfea330243c82f194'
CONCEPT_SHA = 'f76ca6ce488ccb5ad1352f7d38b8c3d4657c12ed64d0c93cc45d2db605cc632f'
PDS_SHA = '1a731834a3956267aacbdde030561df2cef18121d91860cfbef1c5e851c10c99'
PF4_SHA = '7fd4dfbbe375586de2605361006db84b68f89767c76ba4b76da6cf5f48253155'
CP160_NATIVE_ARCHIVE_SHA = 'a15271ce19677b152c6181306354c0c3e204a2c3d36ec7a5d02e8a22df1d1fbf'
ALLOWED_DRIFT = {
    'README.md','CHAT_README.md','docs/README.md','docs/Prototype_TODO.md',
    'docs/validation/README.md','docs/design/testing/README.md',
    'docs/validation/Checkpoint_160_AUX_Closure_Promotion_And_PF4_Research_Baseline.md'
}

def req(v,msg):
    if not v: raise AssertionError(msg)

def sha(path:Path)->str:
    h=hashlib.sha256();h.update(path.read_bytes());return h.hexdigest()

def js(path:Path): return json.loads(path.read_text(encoding='utf-8-sig'))

def manifest(path:Path):
    out={}
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        if line.strip():
            h,rel=line.split('  ',1);out[rel]=h
    return out

def count_suite(suite): return sum(count_suite(x) if isinstance(x,unittest.TestSuite) else 1 for x in suite)

def ps_balanced(path:Path)->bool:
    text=path.read_text(encoding='utf-8-sig');stack=[];pairs={')':'(',']':'[','}':'{'};state='normal';i=0
    while i<len(text):
        ch=text[i]
        if state=='comment':
            if ch=='\n': state='normal'
        elif state=='single':
            if ch=="'":
                if i+1<len(text) and text[i+1]=="'": i+=1
                else: state='normal'
        elif state=='double':
            if ch=='`': i+=1
            elif ch=='"': state='normal'
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
    ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);args=ap.parse_args();repo=Path(args.repo).resolve()
    try:
        d=js(repo/'tools/checkpoints/checkpoint-161/checkpoint_161_definition.json')
        req(d['checkpoint']==161 and d['baseCheckpoint']==160,'identity')
        req(d['expectedPythonTests']==660 and d['expectedPythonTestModules']==52,'Python contract')
        req(d['expectedFocusedCp161Tests']==32 and d['expectedXunitTests']==934,'regression contract')
        req(d['substantiveCombatTrials']==4536000 and d['stochasticTurnSamples']==7776000,'study scale')
        req(d['combatContextsPerTl']==36 and d['combatCells']==2268,'combat design scale')
        req(d['operationalSupplySweepMinTp']==2 and d['operationalSupplySweepMaxTp']==30,'supply sweep')
        req(d['reactorSpaceSweep']==[4,5,6,7,8] and d['combatSupplyOffsetsFromPf4']==[-4,-2,0,2,4,6,8],'supply/space bounds')
        req(not d['tuningAllowed'] and not d['automaticPromotion'] and not d['productionAuthorityChangesAllowed'],'promotion boundary')
        req(d['optionalSecondReactorIncluded'] and d['isolatedAuxMagnitudeArchitectureRemainClosed'],'architecture/AUX boundary')

        wrapper=repo/'tools/checkpoints/checkpoint-161/apply_checkpoint_161.ps1'
        req(wrapper.is_file() and ps_balanced(wrapper),'PowerShell delimiter/static parse guard')
        wt=wrapper.read_text(encoding='utf-8-sig')
        req('starcluster_research.reactor_tp_equilibrium' in wt,'CP161 module entrypoint')
        req('Start-Transcript' in wt and 'CP161_console_output.txt' in wt,'console transcript requirement')
        req('tools\\simulation\\run_starcluster_research.py' in wt and 'starcluster_research\\cli.py' not in wt,'package-safe parity entrypoint')

        req(sha(repo/'docs/design/player_technology/technology_numerical_matrix_v0_9.json')==PROD_SHA,'production matrix drift')
        req(sha(repo/'docs/archive/concepts/Star_Cluster_Game_Concept_v0.7x.docx')==CONCEPT_SHA,'Concept drift')
        req(sha(repo/'src/StarCluster.Core/Combat/Missiles/MissileInterceptionPhaseContext.cs')==PDS_SHA,'production PDS drift')
        req(sha(repo/'docs/design/player_technology/technology_research_execution_baseline_pending_finalization_v0_4.json')==PF4_SHA,'PF4 drift')

        pm=repo/CP160_MAN
        req(pm.is_file() and sha(pm)==CP160_MAN_SHA,'CP160 repository manifest drift')
        for rel,expected in manifest(pm).items():
            req((repo/rel).is_file(),f'missing CP160 file {rel}')
            if rel not in ALLOWED_DRIFT: req(sha(repo/rel)==expected,f'unexpected CP160 drift: {rel}')

        acc=repo/'docs/validation/evidence/checkpoint-161/accepted-cp160'
        req((acc/'CP160_NATIVE_RESULTS_ARCHIVE_SHA256.txt').read_text(encoding='utf-8-sig').strip()==CP160_NATIVE_ARCHIVE_SHA+'  StarCluster_CP160_native_results_20260830_162554.zip','CP160 native archive hash record')
        ns=js(acc/'CP160_NATIVE_ACCEPTANCE_SUMMARY.json')
        req(ns['checkpoint']==160 and ns['pythonTestsPassed']==628 and ns['xunitPassed']==934 and ns['researchParityPassed']==25,'CP160 native regression')
        req(ns['pendingFinalizationBaselineId']=='CP160-PF4' and ns['baselinePromotionCompleted'],'CP160 PF4 promotion')
        req(ns['substantiveCombatTrials']==0 and ns['productionAuthorityChanged'] is False,'CP160 authority boundary')

        sys.path.insert(0,str(repo/'tools/simulation'))
        from starcluster_research.reactor_tp_equilibrium import validate_study, enumerate_loadouts, representative_loadouts, combat_contexts
        from starcluster_research.research_execution_baseline_pf4 import load_research_execution_baseline_pf4
        study=js(repo/'docs/archive/testing/pre-cp165-active/cp161_reactor_tp_equilibrium_study_v0_1.json')
        req(validate_study(study)==[],'study contract invalid')
        m=load_research_execution_baseline_pf4(repo); loads=enumerate_loadouts(m,reactor_space=6)
        req(len(loads)==22482 and sum(x.reactor_count==1 for x in loads)==16741 and sum(x.reactor_count==2 for x in loads)==5741,'architecture population')
        reps=representative_loadouts(m,[x for x in loads if x.reactor_count==1],12)
        req(len(reps)==108,'representative count')
        req(all(len(combat_contexts(repo,tl))==36 for tl in range(1,10)),'combat contexts')
        req(any(v.side_a.reactor_count==2 or v.side_b.reactor_count==2 for v in combat_contexts(repo,9)),'second-Reactor combat coverage')

        plan=js(repo/'docs/validation/evidence/checkpoint-161/planned-study/summary.json')
        req(plan['legalPoweredArchitectures']==22482 and plan['stochasticTurnSamples']==7776000,'planned architecture/stochastic scale')
        req(plan['combatContexts']==324 and plan['combatCells']==2268 and plan['combatTrials']==4536000,'planned combat scale')
        req(not plan['automaticPromotion'] and not plan['tuningAllowed'],'plan promotion boundary')

        contract=js(repo/'docs/validation/evidence/checkpoint-161/cp161_reactor_tp_study_contract_v0_1.json')
        req(contract['acceptedBaseNativeArchiveSha256']==CP160_NATIVE_ARCHIVE_SHA and contract['researchExecutionMatrixSha256']==PF4_SHA,'study provenance')
        req(contract['fullMapCombat']['includesMirroredOneVsTwoReactorContests'],'second-Reactor contract')
        req(contract['interpretation']['currentReactorLadderIsScaffoldNotAnswer'] and not contract['interpretation']['automaticPromotion'],'interpretation contract')

        tests=sorted((repo/'tools/simulation/tests').glob('test_*.py'))
        req(len(tests)==52,f'Python modules {len(tests)}')
        suite=unittest.defaultTestLoader.discover(str(repo/'tools/simulation/tests'),pattern='test_*.py')
        req(count_suite(suite)==660,f'Python tests {count_suite(suite)}')
        req(not any(repo.glob('StarCluster_CP160_native_results_*.zip')),'raw CP160 results archive must remain externalized')

        print('CP161 preflight PASS: CP160 native acceptance/PF4 hash-locked; production/Concept/PDS frozen; 22,482 powered architectures; 2-30 TP and Reactor Space 4-8 surfaces; 108 representatives/7,776,000 stochastic turn samples; 36 contexts/TL including mirrored 1R-vs-2R; 4,536,000 planned combats; 660/52 Python tests; no tuning or automatic promotion.')
        return 0
    except Exception as exc:
        print(f'CP161 preflight failure: {exc}',file=sys.stderr);return 1

if __name__=='__main__': raise SystemExit(main())
