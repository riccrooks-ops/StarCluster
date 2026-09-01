#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

def req(v,msg):
    if not v: raise AssertionError(msg)
def js(p): return json.loads(p.read_text(encoding='utf-8-sig'))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo',required=True); a=ap.parse_args(); repo=Path(a.repo).resolve()
    try:
        arch=js(repo/'docs/archive/player_technology/pre-cp165-active/weapon_ammunition_missile_family_architecture_v0_3.json')
        req(arch.get('checkpoint')==117 and arch.get('automaticPromotion') is False,'CP117 architecture identity/promotion drift')
        req(arch['familyIdentity']['Kinetic']['normalAmmoSelector'] is False,'Kinetic normal ammo selector reintroduced')
        req(arch['familyIdentity']['Missile']['normalWarheadSelector'] is False,'Missile normal warhead selector reintroduced')
        req(arch['swarmer']['window']==[5,7] and arch['swarmer']['oneFlightCounter'] and arch['swarmer']['oneTerminalAttackRoll'],'Swarmer KISS window/package drift')
        req(not arch['swarmer']['extraPdsWindows'] and not arch['swarmer']['automaticApproximateTargetCapability'],'Swarmer complexity/targeting creep')
        table=js(repo/'docs/archive/player_technology/pre-cp165-active/technology_component_table_v0_4.json')
        entries=table['lineageEntries']
        kin=[e for e in entries if e.get('lineageId')=='kinetic-ammunition' and e.get('adoptedInProvisionalTable')]
        req(kin and all(e.get('playerExpression')=='automatic_capability' for e in kin),'active Kinetic ammunition contains a selector/non-automatic mode')
        war=[e for e in entries if e.get('lineageId')=='warheads']
        normal=[e for e in war if e.get('adoptedInProvisionalTable')]
        req(normal and all(e.get('playerExpression')=='automatic_capability' for e in normal),'active normal Missile warhead selector remains')
        for tl in (3,4):
            e=next(x for x in war if x['tl']==tl)
            req(e.get('playerExpression')=='deferred_concept' and not e.get('adoptedInProvisionalTable'),f'TL{tl} specialist warhead not deferred')
        swarm=next(e for e in entries if e.get('lineageId')=='missile-delivery' and e.get('tl')==5)
        req('Swarmer Missile' in swarm.get('technology','') and swarm.get('playerExpression')=='installed_component','Swarmer is not a distinct installed Missile family')
        print('       CP117 KISS preflight passed: no routine Kinetic/Missile payload selector; Swarmer remains one Flight / one terminal attack package; TL8-TL9 remain endpoint-only calibration emphasis.')
        return 0
    except Exception as exc:
        print(f'CP117 preflight failure: {exc}',file=sys.stderr); return 1
if __name__=='__main__': raise SystemExit(main())
