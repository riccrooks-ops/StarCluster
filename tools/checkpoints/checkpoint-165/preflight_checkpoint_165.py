#!/usr/bin/env python3
import argparse,importlib.util,json
from pathlib import Path
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);a=ap.parse_args();r=Path(a.repo).resolve();fail=[];d=json.loads((r/'tools/checkpoints/checkpoint-165/checkpoint_165_definition.json').read_text())
 if d['checkpoint']!=165 or d['substantiveCombatTrials']!=0 or not d['zeroSubstantiveCombat']:fail.append('definition')
 mods=list((r/'tools/simulation/tests').glob('test_*.py'))
 if len(mods)!=56:fail.append('python module count '+str(len(mods)))
 sp=importlib.util.spec_from_file_location('a',r/'tools/checkpoints/checkpoint-165/document_authority_audit.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);q=m.report(r)
 if not q['passed']:fail+=['audit:'+x['name'] for x in q['failed']]
 if fail:[print('FAIL:',x) for x in fail];return 1
 print(f"CP165 preflight PASS: {q['checksPassed']}/{q['checksTotal']} authority checks; 56 Python modules; zero substantive combat.");return 0
if __name__=='__main__':raise SystemExit(main())
