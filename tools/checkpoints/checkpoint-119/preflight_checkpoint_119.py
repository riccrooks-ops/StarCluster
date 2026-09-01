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
        from starcluster_research.weapon_integration_analysis import validate_study
        from starcluster_research.weapon_family_analysis import build_variants
        analysis_path=repo/'tools/simulation/starcluster_research/weapon_integration_analysis.py'
        tree=ast.parse(analysis_path.read_text(encoding='utf-8')); v=TrialDependentFailureGateVisitor(); v.visit(tree)
        req(not v.bad,f'trial-count-dependent CP119 blocking gate(s): {v.bad}')
        study=json.loads((repo/'docs/archive/testing/pre-cp165-active/campaign_weapon_integration_study_v0_1.json').read_text(encoding='utf-8'))
        req(validate_study(study)==[],f'CP119 study validation: {validate_study(study)}')
        req(study.get('checkpoint')==119 and int(study.get('acceptedBaseline',0))==118,'study identity drift')
        req(int(study.get('trialsPerVariant',0))==2000 and int(study.get('authoringTrialsPerVariant',0))==50,'trial-count contract drift')
        req(study.get('primaryCalibrationTls')==[1,2,3,4,5,6] and study.get('advancedValidationTls')==[7] and study.get('endpointStressTls')==[8,9],'TL weighting drift')
        req(not study.get('specialistPairingIds') and not study.get('adaptivePairingIds'),'standing specialist/adaptive Missile menu reintroduced')
        req(study.get('workingSwarmerByTl',{}).get('1') is None and study.get('workingSwarmerByTl',{}).get('2')=='swarmer-early-tl2','TL2 Swarmer introduction drift')
        for p in study.get('missileProfiles',[]):
            pid=str(p.get('id',''))
            if pid.startswith('missile-working-'):
                req((int(p.get('spen',-1)),int(p.get('apen',-1)))==(1,2),f'working GP penetration creep: {pid}')
                req(int(p.get('packets',1))==1 and int(p.get('guidanceDelta',0))==0 and int(p.get('pdsInterceptPenaltyPp',0))==0,f'working GP specialist leakage: {pid}')
            if pid.startswith('swarmer-'):
                req(int(p.get('packets',0))==2,f'Swarmer packet count drift: {pid}')
                req(int(p.get('spen',-1))==0 and int(p.get('apen',-1))==0,f'Swarmer penetration creep: {pid}')
                req(0<=int(p.get('guidanceDelta',0))<=15 and 0<=int(p.get('pdsInterceptPenaltyPp',0))<=15,f'Swarmer bounded-trait drift: {pid}')
        kp=next(p for p in study['kineticProfiles'] if p['id']=='kinetic-working-smart-plus5')
        req(int(kp.get('accuracyDelta',0))==5,'Kinetic +5 ACC working candidate drift')
        req(all(int(kp.get(k,0))==0 for k in ('damageDelta','spenDelta','apenDelta')),'Kinetic multi-axis drift')
        req(int(kp.get('packets',1))==1 and not kp.get('orderedPackets'),'Kinetic ammo-menu/packet drift')
        req(all(x.get('classification')=='legal_build' for x in study['targetFixtures']),'controlled fixture leaked into CP119 integration ecology')
        builds,variants=build_variants(repo,study)
        req(len(builds)==108 and all(b.used_space==b.capacity for b in builds),'exact-fill build shape drift')
        req(len(variants)==1152,'variant shape drift')
        cli=(repo/'tools/simulation/starcluster_research/cli.py').read_text(encoding='utf-8')
        req("add_parser('weapon-integration-study')" in cli and "args.cmd=='weapon-integration-study'" in cli,'CLI parser/dispatch path missing')
        wrapper=(repo/'tools/checkpoints/checkpoint-119/apply_checkpoint_119.ps1')
        if wrapper.exists():
            wt=wrapper.read_text(encoding='utf-8-sig')
            req("'--trials','2000'" in wt and '2304000' in wt and 'Study output tail:' in wt,'native wrapper substantive/capture path missing')
        print('       CP119 preflight: no trial-count-dependent blocking gates; TL2 two-packet Swarmer bounded; working GP is yield-only at SP1/AP2; Kinetic is +5 ACC only; all six targets are legal exact-fill builds.')
        return 0
    except Exception as exc:
        print(f'CP119 preflight failure: {exc}',file=sys.stderr); return 1
if __name__=='__main__': raise SystemExit(main())
