#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import sys
from pathlib import Path


def sha(path: Path) -> str:
    h=hashlib.sha256();h.update(path.read_bytes());return h.hexdigest()


def load_module(path: Path, name: str):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None: raise RuntimeError(f"unable to load {path}")
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod


def main() -> int:
    ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);ap.add_argument('--out')
    args=ap.parse_args();repo=Path(args.repo).resolve()
    sim=repo/'tools/simulation'
    if str(sim) not in sys.path:sys.path.insert(0,str(sim))
    from starcluster_research.current_working_combat import authority_identity, execution_coverage
    from starcluster_research.same_tl_whole_system import plan, validate_study

    checks=[]
    def ck(name,passed,detail=''):
        checks.append({'name':name,'passed':bool(passed),'detail':str(detail)})

    definition=json.loads((repo/'tools/checkpoints/checkpoint-166/checkpoint_166_definition.json').read_text())
    study_path=repo/'docs/validation/evidence/checkpoint-166/cp166_same_tl_whole_system_study_v0_1.json'
    study=json.loads(study_path.read_text())
    prov=json.loads((repo/'docs/validation/evidence/checkpoint-166/CP165_ACCEPTED_NATIVE_PROVENANCE.json').read_text())
    authority_manifest=json.loads((repo/'docs/validation/evidence/checkpoint-166/CP166_CURRENT_AUTHORITY_SHA256.json').read_text())

    ck('definition-checkpoint',definition.get('checkpoint')==166 and definition.get('baseCheckpoint')==165)
    ck('accepted-base-revision',definition.get('acceptedBaseRevision')=='CP165-CR3')
    ck('python-module-contract',definition.get('expectedPythonTestModules')==57)
    ck('python-test-contract',definition.get('expectedPythonTests')==824)
    ck('xunit-contract',definition.get('expectedXunitTests')==934)
    ck('scenario-contract',definition.get('expectedScenarioRunnerSelfTests')==70)
    ck('parity-contract',definition.get('expectedResearchParityCases')==25)
    ck('focused-contract',definition.get('expectedFocusedCp166Tests')==32)
    ck('diagnostic-only',definition.get('tuningAllowed') is False and definition.get('automaticProductionPromotion') is False)
    ck('same-tl-only',definition.get('sameTlOnly') is True and definition.get('differentTlCombatsExecuted') is False and definition.get('mixedTlShipsExecuted') is False)

    ck('cp165-native-results-sha',prov['nativeResultsArchive']['sha256']=='f3bb765629aead0ca733854f1ee7adc6b14e92fe2a7cf0638c41d0fba635fa7f')
    ck('cp165-repository-sha',prov['repositoryArchive']['sha256']=='0fbd74321cde0c97b640c52ecdbd9d17941eb63b7f43b651d9fce1a680085a7c')
    ns=prov['acceptedNativeSummary']
    ck('cp165-native-accepted',ns['pythonTestsPassed']==792 and ns['xunitPassed']==934 and ns['xunitFailed']==0 and ns['scenarioRunnerSelfTestsPassed']==70 and ns['researchParityPassed']==25 and ns['cp165FocusedTestsPassed']==32)
    ck('cp165-whole-system-next',ns['wholeSystemIntegrationNext'] is True and ns['productionRuntimeMechanicsChanged'] is False)

    ident=authority_identity(repo)
    ck('combat-authority-hashes',ident['passed'],[r['path'] for r in ident['files'] if not r['matches']])
    bad=[]
    for row in authority_manifest['files']:
        p=repo/row['path'];actual=sha(p) if p.is_file() else 'MISSING'
        if actual!=row['sha256']:bad.append(row['path'])
    ck('all-current-authority-hashes',not bad,bad)
    ck('current-authority-mutation-disabled',authority_manifest['authorityMutationAllowed'] is False and authority_manifest['productionPromotion'] is False)

    cp165audit=load_module(repo/'tools/checkpoints/checkpoint-165/document_authority_audit.py','cp165audit')
    audit=cp165audit.report(repo)
    ck('cp165-authority-structure-retained',audit['passed'],[x['name'] for x in audit['failed']])

    study_errors=validate_study(study)
    ck('study-valid',not study_errors,study_errors)
    expected=study['expected']
    exact={
        'skeletons':101207,'effectDistinctStackCombinations':635428,'representatives':252,'pairGroups':3654,
        'combatVariants':14616,'substantiveCombatTrials':2923200,'monotonicityVariants':288,
        'monotonicityCombatTrials':72000,'totalDiagnosticCombatTrials':2995200,
    }
    ck('study-exact-scale',all(int(expected.get(k,-1))==v for k,v in exact.items()),expected)
    ck('study-no-cross-tl',study['differentTlCombatsExecuted'] is False and study['mixedTlShipsExecuted'] is False)
    ck('study-no-tuning',study['tuningAllowed'] is False and study['automaticPromotion'] is False)

    p=plan(repo,study_path)
    ck('plan-passed',p['passed'])
    ck('plan-skeletons',p['skeletons']==101207)
    ck('plan-representatives',p['representatives']==252)
    ck('plan-variants',p['combatVariants']==14616 and p['monotonicityVariants']==288)
    ck('plan-combats',p['substantiveCombatTrials']==2923200 and p['monotonicityCombatTrials']==72000 and p['totalDiagnosticCombatTrials']==2995200)
    family_ok=True
    for row in p['perTl']:
        want={'K':10,'E':9,'GP':9} if row['tl']==1 else {'K':7,'E':7,'GP':7,'SW':7}
        family_ok = family_ok and row.get('weaponRepresentativeCounts')==want
    ck('plan-family-quota',family_ok,[x.get('weaponRepresentativeCounts') for x in p['perTl']])

    coverage=execution_coverage();statuses={x['system']:x['status'] for x in coverage}
    ck('coverage-row-count',len(coverage)==16)
    ck('reactor-component-states-deferred',statuses['Main Reactor Degraded/Emergency transitions']=='DEFERRED_SAME_TL_INTEGRATION')
    ck('apu-component-states-deferred',statuses['APU damaged/distributed resilience']=='DEFERRED_SAME_TL_INTEGRATION')
    ck('repair-drone-component-action-deferred',statuses['Repair Drone distinct-target component action']=='DEFERRED_SAME_TL_INTEGRATION')
    ck('mixed-main-deferred',statuses['mixed-family multiple Main Weapons']=='DEFERRED_SAME_TL_INTEGRATION')
    ck('multi-pds-deferred',statuses['multiple simultaneous PDS installations/families']=='DEFERRED_SAME_TL_INTEGRATION')

    modules=sorted((repo/'tools/simulation/tests').glob('test_*.py'))
    ck('python-module-count',len(modules)==57,len(modules))
    method_count=sum(p.read_text(encoding='utf-8').count('def test_') for p in modules)
    ck('python-test-method-count',method_count==824,method_count)
    focused=(repo/'tools/simulation/tests/test_cp166_same_tl_whole_system.py').read_text()
    ck('focused-test-method-count',focused.count('    def test_')==32,focused.count('    def test_'))

    prod_manifest=repo/'docs/validation/evidence/checkpoint-165/CP164_FROZEN_PRODUCTION_RUNTIME_SHA256.csv'
    prod_bad=[]
    with prod_manifest.open(newline='') as f:
        for row in csv.DictReader(f):
            pth=repo/row['path']
            if not pth.is_file() or sha(pth)!=row['sha256']:prod_bad.append(row['path'])
    ck('production-runtime-still-frozen',not prod_bad,prod_bad[:10])

    result={'checkpoint':166,'passed':all(x['passed'] for x in checks),'checksPassed':sum(x['passed'] for x in checks),'checksTotal':len(checks),'failed':[x for x in checks if not x['passed']],'checks':checks}
    if args.out:
        out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'passed':result['passed'],'checksPassed':result['checksPassed'],'checksTotal':result['checksTotal'],'failed':[x['name'] for x in result['failed']]},indent=2))
    return 0 if result['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
