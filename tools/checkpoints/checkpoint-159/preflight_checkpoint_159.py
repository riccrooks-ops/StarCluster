#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys, unittest
from pathlib import Path

CP158_MAN='docs/validation/evidence/checkpoint-158/CP158_REPOSITORY_SHA256SUMS.txt'
CP158_MAN_SHA='36f7eddbc7fa607b41362b53fedd30233e359fc795052706113cfc4d47e007c8'
PROD_SHA='3088b0a9eb45f6bf505c24513e8bb2ac878819db4ab464ccfea330243c82f194'
CONCEPT_SHA='f76ca6ce488ccb5ad1352f7d38b8c3d4657c12ed64d0c93cc45d2db605cc632f'
PDS_SHA='1a731834a3956267aacbdde030561df2cef18121d91860cfbef1c5e851c10c99'
PF3_SHA='9158c44c6c66d84997696f3415612f1f3bba70960b738b0344ecb8e09062d8e2'
ALLOWED={'README.md','CHAT_README.md','docs/README.md','docs/Prototype_TODO.md','docs/validation/README.md','docs/design/testing/README.md','docs/design/player_technology/README.md'}

def req(x,m):
    if not x: raise AssertionError(m)
def sha(p):
    h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()
def js(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def manifest(p):
    out={}
    for line in p.read_text(encoding='utf-8-sig').splitlines():
        if line.strip():
            h,r=line.split('  ',1); out[r]=h
    return out
def count_suite(s): return sum(count_suite(x) if isinstance(x,unittest.TestSuite) else 1 for x in s)
def ps_balanced(path):
    text=path.read_text(encoding='utf-8-sig'); stack=[]; pairs={')':'(',']':'[','}':'{'}; state='normal'; i=0
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
            if ch=='#': state='comment'
            elif ch=="'": state='single'
            elif ch=='"': state='double'
            elif ch in '([{': stack.append(ch)
            elif ch in ')]}':
                if not stack or stack[-1]!=pairs[ch]: return False
                stack.pop()
        i+=1
    return state in ('normal','comment') and not stack

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo',required=True); a=ap.parse_args(); repo=Path(a.repo).resolve()
    try:
        d=js(repo/'tools/checkpoints/checkpoint-159/checkpoint_159_definition.json')
        req(d['checkpoint']==159 and d['baseCheckpoint']==158,'identity')
        req(d['expectedPythonTests']==604 and d['expectedPythonTestModules']==50,'Python contract')
        req(d['substantiveCombatTrials']==3390000 and d['repairDroneMicroTrials']==1728000,'study scale')
        req(not d['automaticPostStudyPromotion'] and not d['tuningAllowed'] and not d['finalReactorTpTuningAllowed'],'closure boundary')
        wrapper=repo/'tools/checkpoints/checkpoint-159/apply_checkpoint_159.ps1'; req(wrapper.is_file() and ps_balanced(wrapper),'PowerShell delimiter/static parse guard')
        wt=wrapper.read_text(encoding='utf-8-sig'); req('tools\\simulation\\run_starcluster_research.py' in wt and 'starcluster_research\\cli.py' not in wt,'package-safe parity entrypoint')
        req(sha(repo/'docs/design/player_technology/technology_numerical_matrix_v0_9.json')==PROD_SHA,'production matrix drift')
        req(sha(repo/'docs/archive/concepts/Star_Cluster_Game_Concept_v0.7x.docx')==CONCEPT_SHA,'Concept drift')
        req(sha(repo/'src/StarCluster.Core/Combat/Missiles/MissileInterceptionPhaseContext.cs')==PDS_SHA,'production PDS drift')
        pm=repo/CP158_MAN; req(pm.is_file() and sha(pm)==CP158_MAN_SHA,'CP158 manifest drift'); base=manifest(pm)
        for rel,h in base.items():
            req((repo/rel).is_file(),f'missing CP158 file {rel}')
            if rel not in ALLOWED: req(sha(repo/rel)==h,f'unexpected CP158 drift: {rel}')
        ns=js(repo/'docs/validation/evidence/checkpoint-159/accepted-cp158/CP158_NATIVE_ACCEPTANCE_SUMMARY.json')
        req(ns['checkpoint']==158 and ns['pythonTestsPassed']==574 and ns['xunitPassed']==934 and ns['substantiveCombatTrials']==44723375 and ns['substantiveErrors']==0,'CP158 native evidence')
        pf3=repo/'docs/archive/player_technology/pre-cp165-active/technology_research_execution_baseline_pending_finalization_v0_3.json'; req(sha(pf3)==PF3_SHA,'PF3 matrix hash')
        bm=js(repo/'docs/validation/evidence/checkpoint-159/research_execution_baseline_manifest_v0_3.json'); req(bm['baselineId']=='CP159-PF3' and bm['materializedMatrixSha256']==PF3_SHA and not bm['productionAuthorityReplaced'],'PF3 manifest')
        sys.path.insert(0,str(repo/'tools/simulation'))
        from starcluster_research.research_execution_baseline_pf3 import load_research_execution_baseline_pf3, aux_profile
        from starcluster_research.auxiliary_closure import plan, field_candidates, crystal_candidates, _micro_one
        m=load_research_execution_baseline_pf3(repo)
        req(int(m.p('kinetic_main',9)['damage'])==20 and int(m.p('energy_main',9)['standardDamage'])==18,'main conformance')
        req(float(m.p('shield',9)['capacity'])==32 and float(m.p('armor',9)['ai'])==24,'defense conformance')
        req(int(m.p('kinetic_pds',7)['reactionCapacity'])==2 and int(m.p('amm_pds',7)['reactionCapacity'])==3,'PDS conformance')
        pp=m.pending_finalization_aux_profiles
        req(pp['shieldBattery']['status']=='PENDING_FINALIZATION_SELECTED_CP158','AUX promotion missing')
        req(pp['fieldStabilizer']['status']=='PENDING_FINALIZATION_MECHANIC_MAGNITUDE_OPEN','Field status')
        req(pp['repairDroneBay']['status']=='PENDING_FINALIZATION_MECHANIC_KIT_ENDURANCE_OPEN','Drone status')
        req(len(field_candidates())==99 and max(c['spen_reduction'] for c in field_candidates())==24,'Field sweep bounds')
        req(len(crystal_candidates())==40 and max(c['capacity_bonus'] for c in crystal_candidates())==16 and max(c['res_bonus_pp'] for c in crystal_candidates())==30,'Crystalline bounds')
        dc=m.p('damage_control',4); one=_micro_one(dc,0,'SINGLE_HULL',2,123); two=_micro_one(dc,0,'TWO_DEGRADED',2,123)
        req(one['drone_attempts']==0 and two['drone_attempts']>0,'distinct-target Drone semantics')
        st=js(repo/'docs/archive/testing/pre-cp165-active/cp159_aux_closure_study_v0_1.json'); req(st['researchExecutionBaseline']=='CP159-PF3' and st['plannedScale']['substantiveCombatTrials']==3390000 and st['plannedScale']['repairDroneMicroTrials']==1728000,'study baseline/scale')
        txt=json.dumps(st).lower(); req('balance is not equality' in txt and 'no global 50' in txt and 'final reactor/tp tuning remains last' in txt,'method guardrails')
        pl=js(repo/'docs/validation/evidence/checkpoint-159/planned-study/summary.json'); req(pl['fieldCandidateTlPoints']==99 and pl['crystallineCandidateTlPoints']==40 and pl['substantiveCombatTrials']==3390000 and pl['repairDroneMicroTrials']==1728000,'planned counts')
        tests=sorted((repo/'tools/simulation/tests').glob('test_*.py')); req(len(tests)==50,f'Python modules {len(tests)}')
        suite=unittest.defaultTestLoader.discover(str(repo/'tools/simulation/tests'),pattern='test_*.py'); n=count_suite(suite); req(n==604,f'Python tests {n}')
        print('CP159 preflight PASS: CP158 native AUX evidence accepted; CP159-PF3 materialized; five well-bracketed AUX trajectories promoted pending finalization; Field Stabilizer 4-24 SPEN reduction, Crystalline TL8-9 headroom, and +1 distinct-target Damage-Control Drone with 100-200% kit endurance closure planned; 3,390,000 substantive combats + 1,728,000 microtrials; 604/50 Python tests discovered; production authority unchanged; Reactor/TP deferred.')
        return 0
    except Exception as e:
        print(f'CP159 preflight failure: {e}',file=sys.stderr); return 1
if __name__=='__main__': raise SystemExit(main())
