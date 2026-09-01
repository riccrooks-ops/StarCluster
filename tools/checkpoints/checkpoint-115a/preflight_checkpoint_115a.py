#!/usr/bin/env python3
from __future__ import annotations
import argparse, ast, csv, json, sys
from pathlib import Path

class TrialDependentFailureGateVisitor(ast.NodeVisitor):
    def __init__(self):
        self.bad=[]
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
        src_path=repo/'tools/simulation/starcluster_research/weapon_family_analysis.py'
        src=src_path.read_text(encoding='utf-8')
        tree=ast.parse(src)
        v=TrialDependentFailureGateVisitor(); v.visit(tree)
        if v.bad: raise AssertionError(f'trial-count-dependent blocking gate(s) remain: {v.bad}')
        if 'adaptive-pair-switch-telemetry' in src: raise AssertionError('obsolete stochastic adaptive switch gate remains')
        for needle in ('adaptivePairRows','adaptivePairRowsWithSwitches','adaptivePairSwitchTelemetryObserved'):
            if needle not in src: raise AssertionError(f'missing info-only adaptive telemetry field {needle}')
        test=(repo/'tools/simulation/tests/test_cp115_weapon_family.py').read_text(encoding='utf-8')
        if 'self.assertEqual(0, side.telemetry.payload_switches)' not in test or 'self.assertGreaterEqual(side.telemetry.payload_switches, 1)' not in test:
            raise AssertionError('deterministic adaptive doctrine non-switch/switch probe incomplete')
        rows=list(csv.DictReader((repo/'docs/validation/evidence/checkpoint-115/authoring/variants.csv').open(encoding='utf-8-sig',newline='')))
        adaptive=[r for r in rows if str(r.get('side_a_profile','')).startswith('adaptive-pair::')]
        if len(adaptive)!=384: raise AssertionError(f'authoring adaptive row count {len(adaptive)} != 384')
        switch_rows=sum(float(r.get('mean_a_payload_switches') or 0)>0 for r in adaptive)
        if switch_rows!=0: raise AssertionError(f'expected CP115 bounded evidence to demonstrate zero natural switch rows; got {switch_rows}')
        analysis=json.loads((repo/'docs/validation/evidence/checkpoint-115/authoring/analysis.json').read_text(encoding='utf-8'))
        if analysis.get('failedGates')!=[]:
            raise AssertionError('historical CP115 authoring evidence unexpectedly contains failed gates')
        print('       CP115a substantive-gate preflight: no trial-count-dependent blocking gates; historical CP115 evidence has 384 adaptive rows / 0 natural switch rows, treated as info-only; deterministic trigger probe retained.')
        return 0
    except Exception as exc:
        print(f'CP115a preflight failure: {exc}',file=sys.stderr); return 1
if __name__=='__main__': raise SystemExit(main())
