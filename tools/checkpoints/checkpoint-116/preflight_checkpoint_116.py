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
                if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='append' and isinstance(n.func.value,ast.Name) and n.func.value.id=='failures':
                    self.bad.append((node.lineno,ast.unparse(node.test) if hasattr(ast,'unparse') else 'trials-dependent gate'))
        self.generic_visit(node)

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--repo',required=True); a=ap.parse_args(); repo=Path(a.repo).resolve()
    try:
        analysis_path=repo/'tools/simulation/starcluster_research/role_generation_analysis.py'
        src=analysis_path.read_text(encoding='utf-8')
        tree=ast.parse(src); v=TrialDependentFailureGateVisitor(); v.visit(tree)
        if v.bad: raise AssertionError(f'trial-count-dependent CP116 blocking gate(s): {v.bad}')
        study=json.loads((repo/'docs/archive/testing/pre-cp165-active/warhead_role_generation_study_v0_1.json').read_text(encoding='utf-8'))
        if study.get('checkpoint')!=116 or study.get('acceptedBaseline')!='115a': raise AssertionError('CP116 study identity drift')
        base=study.get('gpBaselinePenetration',{})
        spen,apen=int(base.get('spen',-1)),int(base.get('apen',-1))
        if (spen,apen)!=(1,2): raise AssertionError(f'unexpected CP116 diagnostic GP baseline {(spen,apen)}')
        profiles={p['id']:p for p in study.get('missileProfiles',[])}
        pure={pid for ids in study.get('pureGpByTl',{}).values() for pid in ids}
        if len(pure)!=6: raise AssertionError(f'pure GP profile count {len(pure)} != 6')
        for pid in pure:
            p=profiles.get(pid)
            if not p or p.get('profileClass')!='gp_pure_yield': raise AssertionError(f'pure GP declaration mismatch: {pid}')
            if (int(p.get('spen',-1)),int(p.get('apen',-1)))!=(spen,apen): raise AssertionError(f'pure GP leaked penetration: {pid}')
        for key in ('spenOnlyGpByTl','apenOnlyGpByTl','penetrationBundledGpByTl'):
            if set(study.get(key,{}))!={'4','5','7','9'}: raise AssertionError(f'{key} missing TL control coverage')
        for tl,pid in study['spenOnlyGpByTl'].items():
            p=profiles[pid]
            if int(p['apen'])!=apen or int(p['spen'])<=spen: raise AssertionError(f'SPEN-only control malformed at TL{tl}: {pid}')
        for tl,pid in study['apenOnlyGpByTl'].items():
            p=profiles[pid]
            if int(p['spen'])!=spen or int(p['apen'])<=apen: raise AssertionError(f'APEN-only control malformed at TL{tl}: {pid}')
        for tl,pid in study['penetrationBundledGpByTl'].items():
            p=profiles[pid]
            if int(p['spen'])<=spen or int(p['apen'])<=apen: raise AssertionError(f'bundled control malformed at TL{tl}: {pid}')
        generation={4:'fission',5:'fusion',7:'antimatter',9:'antimatter'}
        for tl,ids in study.get('specialistPairingIdsByTl',{}).items():
            for pid in ids:
                if profiles[pid].get('generation')!=generation[int(tl)]: raise AssertionError(f'cross-generation specialist pairing TL{tl}: {pid}')
        print('       CP116 preflight: no trial-count-dependent blocking gates; pure GP preserves SP1/AP2 diagnostic baseline; SPEN-only/APEN-only/bundled controls explicit; specialist pairings generation-consistent.')
        return 0
    except Exception as exc:
        print(f'CP116 preflight failure: {exc}',file=sys.stderr); return 1
if __name__=='__main__': raise SystemExit(main())
