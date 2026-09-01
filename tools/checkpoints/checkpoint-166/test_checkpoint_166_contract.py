#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def j(path: Path):return json.loads(path.read_text(encoding='utf-8-sig'))


def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);ap.add_argument('--native-results',required=True)
    a=ap.parse_args();repo=Path(a.repo).resolve();out=Path(a.native_results).resolve();errors=[]
    def req(cond,msg):
        if not cond:errors.append(msg)
    definition=j(repo/'tools/checkpoints/checkpoint-166/checkpoint_166_definition.json')
    req(definition['checkpoint']==166,'definition checkpoint')
    rop=out/'CP166_REPOSITORY_ONLY_ACCEPTANCE.json';req(rop.is_file(),'missing RepositoryOnly acceptance')
    if rop.is_file():
        ro=j(rop)
        req(ro.get('repositoryOnly') is True,'RepositoryOnly flag')
        req(ro.get('pythonTestsPassed')==824,'Python count')
        req(ro.get('xunitPassed')==934 and ro.get('xunitFailed')==0 and ro.get('xunitSkipped')==0,'xUnit count')
        req(ro.get('scenarioRunnerSelfTestsPassed')==70,'ScenarioRunner count')
        req(ro.get('researchParityPassed')==25,'parity count')
        req(ro.get('cp166FocusedTestsPassed')==32,'focused count')
        req(ro.get('architectureSkeletons')==101207,'skeleton count')
        req(ro.get('effectDistinctStackCombinations')==635428,'stack population')
        req(ro.get('representatives')==252,'representatives')
        req(ro.get('plannedTotalDiagnosticCombatTrials')==2995200,'planned combat scale')
        req(ro.get('substantiveCombatTrials')==0,'RepositoryOnly substantive combat must be zero')
        req(ro.get('tuningAllowed') is False and ro.get('automaticPromotion') is False,'promotion boundary')
    plan=out/'planning/summary.json';static=out/'static-census/summary.json';smoke=out/'smoke/summary.json'
    for pth,name in ((plan,'plan'),(static,'static'),(smoke,'smoke')):req(pth.is_file(),f'missing {name}')
    if plan.is_file():
        x=j(plan);req(x.get('passed') is True,'plan failed');req(x.get('combatVariants')==14616 and x.get('monotonicityVariants')==288,'plan variants');req(x.get('totalDiagnosticCombatTrials')==2995200,'plan scale')
    if static.is_file():
        x=j(static);req(x.get('passed') is True,'static failed');req(x.get('skeletons')==101207,'static skeletons');req(x.get('effectDistinctStackCombinations')==635428,'static stacks');req(x.get('representatives')==252,'static representatives');req(x.get('coverageRows')==16,'coverage rows')
    if smoke.is_file():
        x=j(smoke);req(x.get('passed') is True and x.get('liveCombatTrials')==8 and x.get('errors')==0,'smoke')

    finalp=out/'CP166_NATIVE_ACCEPTANCE_SUMMARY.json'
    if finalp.is_file():
        final=j(finalp);merge=out/'combat-merged/summary.json';req(merge.is_file(),'missing merged summary')
        if merge.is_file():
            m=j(merge);req(m.get('passed') is True,'merge failed');req(m.get('representatives')==252,'merged reps');req(m.get('pairGroups')==3654,'merged pairs');req(m.get('combatVariants')==14616,'merged variants');req(m.get('substantiveCombatTrials')==2923200,'merged main trials');req(m.get('monotonicityVariants')==288 and m.get('monotonicityCombatTrials')==72000,'merged mono');req(m.get('totalDiagnosticCombatTrials')==2995200,'merged total');req(m.get('errors')==0,'combat errors');req(m.get('symmetryFailures')==0,'symmetry failures')
        req(final.get('repositoryOnlyAccepted') is True,'final RepositoryOnly');req(final.get('studyCompleted') is True,'study completed');req(final.get('totalDiagnosticCombatTrials')==2995200,'final total');req(final.get('combatErrorTrials')==0,'final errors');req(final.get('symmetryFailures')==0,'final symmetry');req(final.get('tuningAllowed') is False and final.get('automaticPromotion') is False,'final promotion boundary')
        for tl in range(1,10):
            p=out/f'combat-batches/tl{tl}/summary.json';req(p.is_file(),f'missing TL{tl} batch')
            if p.is_file():
                b=j(p);req(b.get('passed') is True,f'TL{tl} failed');req(b.get('combatTrials')==324800,f'TL{tl} main scale');req(b.get('monotonicityCombatTrials')==8000,f'TL{tl} mono scale');req(b.get('errors')==0,f'TL{tl} errors');req(b.get('symmetryFailures')==0,f'TL{tl} symmetry')
    result={'checkpoint':166,'passed':not errors,'errors':errors,'finalPresent':finalp.is_file()}
    print(json.dumps(result,indent=2));return 0 if not errors else 1


if __name__=='__main__':raise SystemExit(main())
