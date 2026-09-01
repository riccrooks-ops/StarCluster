#!/usr/bin/env python3
from __future__ import annotations
import argparse, ast, json, sys
from pathlib import Path

class TrialDependentFailureGateVisitor(ast.NodeVisitor):
    def __init__(self): self.bad=[]
    def visit_If(self,node:ast.If):
        names={n.id for n in ast.walk(node.test) if isinstance(n,ast.Name)}
        if 'trials' in names:
            body=ast.Module(body=node.body,type_ignores=[])
            for n in ast.walk(body):
                if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='append' and isinstance(n.func.value,ast.Name) and n.func.value.id in {'failures','failed_gates'}:
                    self.bad.append((node.lineno,ast.unparse(node.test) if hasattr(ast,'unparse') else 'trials-dependent gate'))
        self.generic_visit(node)

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--repo',required=True); a=ap.parse_args(); repo=Path(a.repo).resolve()
    try:
        sys.path.insert(0,str(repo/'tools/simulation'))
        from starcluster_research.simplified_progression_analysis import validate_study
        analysis_path=repo/'tools/simulation/starcluster_research/simplified_progression_analysis.py'
        tree=ast.parse(analysis_path.read_text(encoding='utf-8'))
        v=TrialDependentFailureGateVisitor(); v.visit(tree)
        if v.bad: raise AssertionError(f'trial-count-dependent CP118 blocking gate(s): {v.bad}')
        study=json.loads((repo/'docs/archive/testing/pre-cp165-active/simplified_weapon_progression_study_v0_1.json').read_text(encoding='utf-8'))
        errs=validate_study(study)
        if errs: raise AssertionError('study validation: '+','.join(errs))
        if study.get('checkpoint')!=118 or int(study.get('acceptedBaseline',0))!=117: raise AssertionError('CP118 study identity drift')
        if int(study.get('trialsPerVariant',0))!=2000 or int(study.get('authoringTrialsPerVariant',0))!=50: raise AssertionError('CP118 trial-count contract drift')
        if study.get('specialistPairingIds') or study.get('adaptivePairingIds'): raise AssertionError('legacy normal Missile payload menu reintroduced')
        # Explicit GP candidates may change yield, but not penetration or family mechanics.
        for p in study.get('missileProfiles',[]):
            pid=str(p.get('id',''))
            if '-gp-' in pid:
                if (int(p.get('spen',-1)),int(p.get('apen',-1)))!=(1,2): raise AssertionError(f'GP penetration creep: {pid}')
                if int(p.get('guidanceDelta',0)) or int(p.get('pdsInterceptPenaltyPp',0)) or int(p.get('packets',1))!=1: raise AssertionError(f'GP specialist leakage: {pid}')
        swarm=[p for p in study['missileProfiles'] if str(p['id']).startswith('swarmer-')]
        swarm_tls={int(tl) for p in swarm for tl in p.get('studyTls',[])}
        if not {1,2,3,5,6,7} <= swarm_tls: raise AssertionError('Swarmer early/maturation TL coverage missing')
        for p in swarm:
            if int(p.get('packets',1)) not in (2,3): raise AssertionError(f'Swarmer packet-count scope: {p["id"]}')
            if int(p.get('pdsInterceptPenaltyPp',0))>15: raise AssertionError(f'Swarmer PDS penalty exceeds CP118 study bound: {p["id"]}')
        for p in study.get('kineticProfiles',[]):
            if p['id']=='gp-current': continue
            changed=sum(bool(int(p.get(k,0))) for k in ('accuracyDelta','damageDelta','apenDelta'))
            if changed!=1 or int(p.get('spenDelta',0))!=0: raise AssertionError(f'Kinetic single-axis/Shield-identity drift: {p["id"]}')
            if int(p.get('packets',1))!=1 or p.get('orderedPackets'): raise AssertionError(f'Kinetic ammunition menu creep: {p["id"]}')
        print('       CP118 preflight: no trial-count-dependent blocking gates; GP candidates isolate yield at SP1/AP2; Swarmer remains one bounded Flight package with early/mature coverage; Kinetic controls are automatic single-axis progression only.')
        return 0
    except Exception as exc:
        print(f'CP118 preflight failure: {exc}',file=sys.stderr); return 1
if __name__=='__main__': raise SystemExit(main())
