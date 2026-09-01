#!/usr/bin/env python3
from __future__ import annotations
import argparse, ast, json, sys
from pathlib import Path

class TrialDependentFailureGateVisitor(ast.NodeVisitor):
    def __init__(self): self.bad=[]
    def visit_If(self,node:ast.If):
        names={n.id for n in ast.walk(node.test) if isinstance(n,ast.Name)}
        if 'trials' in names:
            for n in ast.walk(ast.Module(body=node.body,type_ignores=[])):
                if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='append' and isinstance(n.func.value,ast.Name) and n.func.value.id in {'failures','failed_gates'}:
                    self.bad.append((node.lineno,ast.unparse(node.test) if hasattr(ast,'unparse') else 'trial-dependent'))
        self.generic_visit(node)

def req(v,msg):
    if not v: raise AssertionError(msg)

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--repo',required=True); a=ap.parse_args(); repo=Path(a.repo).resolve()
    try:
        sys.path.insert(0,str(repo/'tools/simulation'))
        from starcluster_research.weapon_sensitivity_analysis import validate_study
        from starcluster_research.weapon_family_analysis import build_variants
        analysis_path=repo/'tools/simulation/starcluster_research/weapon_sensitivity_analysis.py'
        tree=ast.parse(analysis_path.read_text(encoding='utf-8')); v=TrialDependentFailureGateVisitor(); v.visit(tree)
        req(not v.bad,f'trial-count-dependent CP120 blocking gate(s): {v.bad}')
        study=json.loads((repo/'docs/archive/testing/pre-cp165-active/weapon_progression_sensitivity_study_v0_1.json').read_text(encoding='utf-8'))
        errs=validate_study(study); req(errs==[],f'CP120 study validation: {errs}')
        req(study.get('checkpoint')==120 and int(study.get('acceptedBaseline',0))==119,'study identity drift')
        req(int(study.get('trialsPerVariant',0))==2000 and int(study.get('authoringTrialsPerVariant',0))==5,'trial-count contract drift')
        req(study.get('primaryCalibrationTls')==[1,2,3,4,5,6] and study.get('advancedValidationTls')==[7] and study.get('endpointStressTls')==[8,9],'TL weighting drift')
        req(not study.get('specialistPairingIds') and not study.get('adaptivePairingIds'),'standing specialist/adaptive Missile menu reintroduced')
        req(len(study.get('targetFixtures',[]))==9 and sum(x.get('classification')=='controlled_fixture' for x in study['targetFixtures'])==3,'target fixture shape drift')
        pds=next(x for x in study['targetFixtures'] if x['id']=='missile-defense-no-pds-control'); req(pds.get('removePds') is True,'PDS isolation control drift')
        for p in study.get('missileProfiles',[]):
            pid=str(p.get('id',''))
            if pid.startswith('missile-gp-'):
                req((int(p.get('spen',-1)),int(p.get('apen',-1)),int(p.get('packets',1)))==(1,2,1),f'GP yield-only boundary drift: {pid}')
                req(int(p.get('guidanceDelta',0))==0 and int(p.get('pdsInterceptPenaltyPp',0))==0,f'GP specialist leakage: {pid}')
            if pid.startswith('sw-'):
                req(int(p.get('packets',0))==2,f'Swarmer packet count drift: {pid}')
                req(int(p.get('spen',-1))==0 and int(p.get('apen',-1))==0,f'Swarmer penetration creep: {pid}')
                req(0<=int(p.get('guidanceDelta',0))<=15 and 0<=int(p.get('pdsInterceptPenaltyPp',0))<=15,f'Swarmer bounded-trait drift: {pid}')
                req(1 not in [int(x) for x in p.get('studyTls',[])],f'Swarmer pre-TL2 drift: {pid}')
        for p in study.get('kineticProfiles',[]):
            if p['id']=='gp-current': continue
            vals=[int(p.get(k,0)) for k in ('accuracyDelta','damageDelta','spenDelta','apenDelta')]
            req(sum(x!=0 for x in vals)==1,f'Kinetic multi-axis drift: {p["id"]}')
            req(int(p.get('spenDelta',0))==0 and int(p.get('packets',1))==1 and not p.get('orderedPackets'),f'Kinetic KISS boundary drift: {p["id"]}')
        req(len(study.get('sensitivityComparisons',[]))==22,'sensitivity comparison count drift')
        req(len(study.get('candidateProgressionPaths',[]))==9,'candidate path count drift')
        builds,variants=build_variants(repo,study)
        req(len(builds)==135 and all(b.used_space==b.capacity for b in builds),'exact-fill build shape drift')
        req(len(variants)==4284,'variant shape drift')
        groups={}
        for x in variants: groups[x.scenario_group]=groups.get(x.scenario_group,0)+1
        req(groups=={'energy_family_reference':324,'kinetic_family_characteristic':1008,'missile_family_characteristic':2952},f'family shape {groups}')
        pr={'primary':0,'advanced':0,'endpoint':0}
        for x in variants: pr['primary' if x.tl<=6 else ('advanced' if x.tl==7 else 'endpoint')]+=1
        req(pr=={'primary':3060,'advanced':576,'endpoint':648},f'priority shape {pr}')
        cli=(repo/'tools/simulation/starcluster_research/cli.py').read_text(encoding='utf-8')
        req("add_parser('weapon-sensitivity-study')" in cli and "args.cmd=='weapon-sensitivity-study'" in cli,'CLI parser/dispatch path missing')
        wrapper=repo/'tools/checkpoints/checkpoint-120/apply_checkpoint_120.ps1'
        if wrapper.exists():
            wt=wrapper.read_text(encoding='utf-8-sig')
            req("'--trials','2000'" in wt and '8568000' in wt and 'Study output tail:' in wt,'native wrapper substantive/capture path missing')
        print('       CP120 preflight: 4,284 variants; GP yield-only controls; TL2+ exactly-two-packet Swarmer; single-axis Kinetic controls; 3 controlled fixtures; no trial-dependent blocking gates.')
        return 0
    except Exception as exc:
        print(f'CP120 preflight failure: {exc}',file=sys.stderr); return 1
if __name__=='__main__': raise SystemExit(main())
