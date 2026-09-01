#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re, sys
from pathlib import Path

parser=argparse.ArgumentParser(); parser.add_argument('--root',default=None); args=parser.parse_args()
ROOT=Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[3]
OUT=ROOT/'checkpoint-61-static-preflight.txt'
checks=[]
def ok(name, cond, detail=''): checks.append((name,bool(cond),'' if detail=='' else str(detail)))
def loadj(p): return json.loads(p.read_text(encoding='utf-8-sig'))

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
    return h.hexdigest()

required=[
 ROOT/'README.md', ROOT/'Checkpoint_61_Readme.txt', ROOT/'docs/README.md', ROOT/'docs/Prototype_TODO.md',
 ROOT/'docs/Star_Cluster_Game_Concept_v0.6c.docx',
 ROOT/'docs/design/player_technology/tl1_35_space_player_cruiser_baseline_v0_3.json',
 ROOT/'docs/design/player_technology/TL1_35_Space_Construction_Envelope_v0_1.md',
 ROOT/'docs/design/player_technology/TL1_35_Space_Composed_Ship_Odd_Build_Combat_Study_v0_1.md',
 ROOT/'docs/design/testing/checkpoint_61_validation_suite_policy_v0_1.json',
 ROOT/'docs/design/testing/Checkpoint_61_Validation_Tiers.md',
 ROOT/'docs/validation/Checkpoint_61_TL1_35_Space_Composed_Ship_And_Odd_Build_Combat_Study.md',
 ROOT/'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/tl1-space01-35-space-construction-envelope.json',
 ROOT/'src/StarCluster.ScenarioRunner/Scenarios/TL1Calibration/tl1-itc04-35-space-composed-ship-odd-build-matrix.json',
 ROOT/'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatDocuments.cs',
 ROOT/'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs',
 ROOT/'tools/calibration/checkpoints/checkpoint-61.json', ROOT/'tools/calibration/checkpoints/checkpoint-61-deep-calibration.json',
 ROOT/'tools/checkpoints/checkpoint-61/apply_checkpoint_61.ps1', ROOT/'tools/checkpoints/checkpoint-61/test_checkpoint_61_contract.ps1',
]
for p in required: ok(f'required {p.relative_to(ROOT)}', p.is_file())

for p in sorted(ROOT.rglob('*.json')):
    if any(x in {'out','bin','obj','.git'} for x in p.parts): continue
    try: loadj(p); ok(f'JSON parse {p.relative_to(ROOT)}', True)
    except Exception as e: ok(f'JSON parse {p.relative_to(ROOT)}', False, e)

baseline=loadj(ROOT/'docs/design/player_technology/tl1_35_space_player_cruiser_baseline_v0_3.json')
ok('baseline checkpoint', baseline['checkpoint']==61, baseline['checkpoint'])
ok('35/25 Space baseline', baseline['installationSpace']['playerCruiserTotal']==35 and baseline['installationSpace']['mandatoryCoreTotal']==25)
env=baseline['deterministicArchitectureEnvelope']
ok('frozen envelope counts', (env['macroLoadoutCount'],env['weaponPowerVariantCount'],env['exactFillMacroLoadoutCount'])==(27,96,4))
ok('frozen stacking extrema', (env['maximumMainWeapons'],env['maximumMainReactors'],env['maximumKineticPdsAtCurrentFootprint'])==(2,2,5))
ok('37-Space control', env['dualMainDualReactorCoreSpace']==37 and env['dualMainDualReactorCoreLegalAtTl1'] is False)
comp=baseline['composedShipCombatStudy']
ok('baseline composed cardinality', comp['legalBuildCount']==6 and comp['variantCount']==54)
ok('baseline outcomes nonblocking', comp['balanceTargetsBlocking'] is False)
ok('baseline sensor isolation', 'Firm-track' in comp['sensorIsolation'] or 'Firm track' in comp['sensorIsolation'])

study=loadj(ROOT/'src/StarCluster.ScenarioRunner/Scenarios/TL1Calibration/tl1-itc04-35-space-composed-ship-odd-build-matrix.json')
ok('combat study identity', study['id']=='tl1-itc04-35-space-composed-ship-odd-build-matrix')
ok('combat build/variant count', len(study['builds'])==6 and len(study['variants'])==54, (len(study['builds']),len(study['variants'])))
expected={
 'balanced_generalist_major':(1,1,True,True,1,33,2),
 'dual_main_striker_major':(2,1,True,False,0,34,1),
 'dual_reactor_power_core':(1,2,True,False,0,34,1),
 'pds_saturator':(1,1,False,False,5,35,0),
 'dual_main_dual_pds':(2,1,False,False,2,35,0),
 'shielded_pds_fortress':(1,1,False,True,3,34,1),
}
seen={b['id']:b for b in study['builds']}
ok('combat build IDs', set(seen)==set(expected), sorted(seen))
for bid,x in expected.items():
    b=seen.get(bid,{})
    observed=(b.get('mainWeaponCount'),b.get('mainReactorCount'),b.get('activeSensor'),b.get('shieldGenerator'),b.get('kineticPdsCount'),b.get('usedSpace'),b.get('freeSupportSpace'))
    recomputed=13+6*x[0]+6*x[1]+(3 if x[2] else 0)+(3 if x[3] else 0)+2*x[4]
    ok(f'build {bid}', observed==x and recomputed==x[5] and 35-recomputed==x[6], observed)

families={'Kinetic','Energy','Missile'}
keys=[]
for v in study['variants']:
    keys.append((v['sideABuildId'],v['sideAFamily'],v['sideBFamily']))
    ok(f"variant controls {v['id']}",
       v['sideBBuildId']=='balanced_generalist_major' and
       v['sideAProfileId']==v['sideBProfileId']=='tl1-production' and
       v['sideAAuxiliaryProfileId']==v['sideBAuxiliaryProfileId']=='aux-r53-none-tl1' and
       v['movementMode']=='OpponentAwareRange' and v['initialRangeHexes']==4 and
       v['damageControl']=='ComponentFirstReserveOne' and v['baseShieldRechargeEnabled'] is True and
       v['evasiveManeuversEnabled'] is False and v['pdsEnabled'] is True and
       v['escapeDisengagementEnabled'] is False)
    expected_secondary=v['sideAFamily'] if expected[v['sideABuildId']][0]==2 else None
    ok(f"secondary contract {v['id']}", v.get('sideASecondaryFamily')==expected_secondary and v.get('sideBSecondaryFamily') is None)
ok('54 unique build/family cells', len(keys)==54 and len(set(keys))==54 and all(a in expected and fa in families and fb in families for a,fa,fb in keys))

policy=loadj(ROOT/'docs/design/testing/checkpoint_61_validation_suite_policy_v0_1.json')
active=loadj(ROOT/'tools/calibration/checkpoints/checkpoint-61.json')
deep=loadj(ROOT/'tools/calibration/checkpoints/checkpoint-61-deep-calibration.json')
ok('policy counts', len(policy['mustAlwaysRunStageIds'])==8 and len(policy['deepCalibrationStageIds'])==12)
ok('active metrics', active['checkpointMetrics']=={'stageCount':8,'monteCarloVariantCount':54,'trialsAtDefault':540000,'suiteTier':'must_always_run'}, active['checkpointMetrics'])
ok('deep metrics', deep['checkpointMetrics']=={'stageCount':20,'monteCarloVariantCount':1080,'trialsAtDefault':10800000,'suiteTier':'deep_calibration'}, deep['checkpointMetrics'])
active_ids=[x['id'] for x in active['stages']]; deep_ids=[x['id'] for x in deep['stages']]
ok('active stage order', active_ids[3:5]==['tl1-installation-space-envelope','tl1-composed-ship-odd-build-combat'], active_ids)
ok('deep includes current study', 'tl1-composed-ship-odd-build-combat' in deep_ids and len(deep_ids)==20)

runner=(ROOT/'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs').read_text(encoding='utf-8')
docs=(ROOT/'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatDocuments.cs').read_text(encoding='utf-8')
ok('explicit build document', 'class Tl1IntegratedShipBuildDocument' in docs and 'SideABuildId' in docs)
ok('runner study constant', 'tl1-itc04-35-space-composed-ship-odd-build-matrix' in runner)
ok('runner composed PDS', 'ApplyComposedShipPds' in runner and 'ShuffleDeterministically' in runner and 'PdsReactionComponentIds' in runner)
ok('runner independent secondary support', 'IndependentMainWeaponSupport' in runner and 'secondary-support' in runner)
ok('runner review outputs', all(x in runner for x in ['composed-build-matrix.csv','composed-build-rollup.csv','composed-build-family-rollup.csv']))
ok('runner nonblocking balance', 'tl1-c61-outcomes-review-only' in runner)
ok('legacy missile path retained', 'AdvanceMissilesLegacy' in runner and 'sideA.Build is null && sideB.Build is null' in runner)
# Simple lexical sanity: braces outside string/comment parsing is approximated by raw counts, useful when no SDK is installed.
ok('runner brace count', runner.count('{')==runner.count('}'), (runner.count('{'),runner.count('}')))
ok('documents brace count', docs.count('{')==docs.count('}'), (docs.count('{'),docs.count('}')))

validation=list((ROOT/'docs/validation').glob('*.md'))
ok('one active validation runbook', len(validation)==1 and validation[0].name=='Checkpoint_61_TL1_35_Space_Composed_Ship_And_Odd_Build_Combat_Study.md', [p.name for p in validation])
ok('checkpoint60 runbook archived', (ROOT/'docs/validation/archive/Checkpoint_60_TL1_35_Space_Construction_Envelope_And_Odd_Build_Foundation.md').is_file())

manifest=ROOT/'CHECKPOINT_61_SHA256SUMS.txt'
if manifest.is_file():
    lines=[line for line in manifest.read_text(encoding='utf-8').splitlines() if line.strip()]
    malformed=[line for line in lines if not re.fullmatch(r'[0-9a-f]{64}  .+',line)]
    ok('manifest format', not malformed, malformed[:3])

failed=sum(1 for _,passed,_ in checks if not passed)
lines=[]
for name,passed,detail in checks:
    lines.append(('PASS' if passed else 'FAIL')+f' {name}'+(f': {detail}' if detail else ''))
lines.append(f'SUMMARY {len(checks)-failed}/{len(checks)} checks passed; {failed} failed.')
OUT.write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('\n'.join(lines))
sys.exit(1 if failed else 0)
