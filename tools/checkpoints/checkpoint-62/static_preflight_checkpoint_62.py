from pathlib import Path
import json, hashlib, re, sys
ROOT=Path(__file__).resolve().parents[3]
errors=[]; checks=0

def ok(cond,msg):
    global checks
    checks += 1
    if not cond: errors.append(msg)

def load(rel):
    p=ROOT/rel
    ok(p.is_file(), f'missing {rel}')
    if not p.is_file(): return {}
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception as e:
        errors.append(f'json parse {rel}: {e}')
        return {}

required=[
 'README.md','docs/README.md','docs/Prototype_TODO.md',
 'docs/design/player_technology/tl1_35_space_player_cruiser_baseline_v0_4.json',
 'docs/design/player_technology/tl1_integrated_tactical_combat_schema_v0_8.json',
 'docs/design/player_technology/TL1_35_Space_Tactical_Power_Doctrine_And_Reactor_Sensitivity_v0_1.md',
 'docs/design/testing/checkpoint_62_validation_suite_policy_v0_1.json',
 'docs/design/testing/Checkpoint_62_Validation_Tiers.md',
 'docs/validation/Checkpoint_62_TL1_Tactical_Power_Doctrine_And_Reactor_Output_Sensitivity.md',
 'src/StarCluster.ScenarioRunner/Scenarios/TL1Calibration/tl1-itc05-35-space-power-doctrine-reactor-sensitivity.json',
 'tools/calibration/checkpoints/checkpoint-62.json','tools/calibration/checkpoints/checkpoint-62-deep-calibration.json',
 'tools/checkpoints/checkpoint-62/apply_checkpoint_62.ps1','tools/checkpoints/checkpoint-62/test_checkpoint_62_contract.ps1',
 'CHECKPOINT_62_SHA256SUMS.txt'
]
for r in required: ok((ROOT/r).is_file(), f'missing required path {r}')

study=load('src/StarCluster.ScenarioRunner/Scenarios/TL1Calibration/tl1-itc05-35-space-power-doctrine-reactor-sensitivity.json')
baseline=load('docs/design/player_technology/tl1_35_space_player_cruiser_baseline_v0_4.json')
profiles=load('src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/tl1-tl2-standard-runtime-profiles-v0_3.json')
policy=load('docs/design/testing/checkpoint_62_validation_suite_policy_v0_1.json')
active=load('tools/calibration/checkpoints/checkpoint-62.json')
deep=load('tools/calibration/checkpoints/checkpoint-62-deep-calibration.json')
schema=load('docs/design/player_technology/tl1_integrated_tactical_combat_schema_v0_8.json')

ok(study.get('id')=='tl1-itc05-35-space-power-doctrine-reactor-sensitivity','study id')
ok(len(study.get('builds',[]))==4,'build count')
ok(len(study.get('variants',[]))==108,'variant count')
ids=[v.get('id') for v in study.get('variants',[])]
ok(len(ids)==len(set(ids))==108,'variant ids unique')
expected_builds={'balanced_generalist_major','pds_saturator','dual_main_dual_pds','shielded_pds_fortress'}
ok({b.get('id') for b in study.get('builds',[])}==expected_builds,'build ids exact')
for build in sorted(expected_builds):
    for fam in ['Kinetic','Energy','Missile']:
        lane=[v for v in study['variants'] if v.get('sideABuildId')==build and v.get('sideAFamily')==fam]
        ok(len(lane)==9, f'paired lane count {build}/{fam}')
        ok(len({v.get('comparisonGroup') for v in lane})==1, f'paired comparison group {build}/{fam}')
        combos={(v.get('sideATacticalPowerDoctrine'),v.get('sideAReactorOutputOverride')) for v in lane}
        ok(combos=={(d,r) for d in ['DefenseFirst','PrimaryFireFirst','FullVolleyFirst'] for r in [4,5,6]}, f'combo coverage {build}/{fam}')
        ok(all(v.get('sideBBuildId')=='balanced_generalist_major' and v.get('sideBFamily')=='Missile' for v in lane),f'opponent control {build}/{fam}')
        ok(all(v.get('sideBTacticalPowerDoctrine')=='DefenseFirst' and v.get('sideBReactorOutputOverride')==5 for v in lane),f'B power control {build}/{fam}')

prod=next((p for p in profiles.get('profiles',[]) if p.get('id')=='tl1-production'),{})
ok(prod.get('powerAndControl',{}).get('reactorOutput')==5,'production reactor unchanged at 5')
ok(baseline.get('checkpoint')==62,'baseline checkpoint')
ok(baseline.get('powerDoctrineReactorSensitivityStudy',{}).get('productionReactorOutputRemains')==5,'baseline reactor interpretation')
ok(not baseline.get('powerDoctrineReactorSensitivityStudy',{}).get('balanceTargetsBlocking',True),'no balance target')
props=schema.get('$defs',{}).get('variant',{}).get('properties',{})
for key in ['sideATacticalPowerDoctrine','sideBTacticalPowerDoctrine','sideAReactorOutputOverride','sideBReactorOutputOverride']:
    ok(key in props, f'schema field {key}')
ok(active.get('checkpointMetrics',{}).get('stageCount')==8,'active stages')
ok(active.get('checkpointMetrics',{}).get('monteCarloVariantCount')==108,'active variants')
ok(active.get('checkpointMetrics',{}).get('trialsAtDefault')==1080000,'active trials')
ok(deep.get('checkpointMetrics',{}).get('stageCount')==21,'deep stages')
ok(deep.get('checkpointMetrics',{}).get('monteCarloVariantCount')==1188,'deep variants')
ok(deep.get('checkpointMetrics',{}).get('trialsAtDefault')==11880000,'deep trials')
ok(len(policy.get('mustAlwaysRunStageIds',[]))==8,'policy active count')
ok(len(policy.get('deepCalibrationStageIds',[]))==13,'policy deep-only count')

runner=(ROOT/'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs').read_text(encoding='utf-8')
docs=(ROOT/'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatDocuments.cs').read_text(encoding='utf-8')
for token in ['Tl1PowerDoctrineStudyId','RequiredTl1PowerDoctrineVariantCount','pdsPowerBudget','ReactorOutputPerMain','WriteTl1PowerDoctrineReview','tl1-c62-outcomes-review-only']:
    ok(token in runner,f'runner token {token}')
for token in ['Tl1TacticalPowerDoctrine','sideATacticalPowerDoctrine','sideAReactorOutputOverride']:
    ok(token in docs,f'doc model token {token}')
# Simple delimiter smoke checks; native .NET compile remains authoritative.
for text,name in [(runner,'runner'),(docs,'documents')]:
    ok(text.count('{')==text.count('}'),f'{name} brace count')
    ok(text.count('(')==text.count(')'),f'{name} paren count')

root_txt=[p.name for p in ROOT.glob('*.txt')]
ok(root_txt==['CHECKPOINT_62_SHA256SUMS.txt'],f'root txt hygiene {root_txt}')
archive_txt=list((ROOT/'docs/archive').rglob('*.txt'))
ok(not archive_txt,f'docs/archive txt hygiene: {[str(p.relative_to(ROOT)) for p in archive_txt[:5]]}')
active_runbooks=list((ROOT/'docs/validation').glob('*.md'))
ok(len(active_runbooks)==1 and active_runbooks[0].name.startswith('Checkpoint_62_'),'single active validation runbook')
ok((ROOT/'docs/validation/archive/Checkpoint_61_TL1_35_Space_Composed_Ship_And_Odd_Build_Combat_Study.md').is_file(),'CP61 runbook archived')

# Manifest format and hash verification.
manifest=ROOT/'CHECKPOINT_62_SHA256SUMS.txt'
if manifest.is_file():
    entries=[]
    for line in manifest.read_text(encoding='utf-8').splitlines():
        if not line.strip(): continue
        m=re.fullmatch(r'([0-9a-f]{64})  (.+)',line)
        ok(bool(m),f'manifest line format {line[:100]}')
        if m: entries.append((m.group(1),m.group(2)))
    ok(len(entries)>100,'manifest substantial')
    paths={r for _,r in entries}
    ok('CHECKPOINT_62_SHA256SUMS.txt' not in paths,'manifest excludes itself')
    for h,rel in entries:
        p=ROOT/rel
        ok(p.is_file(),f'manifest file exists {rel}')
        if p.is_file(): ok(hashlib.sha256(p.read_bytes()).hexdigest()==h,f'manifest hash {rel}')

print(f'Checkpoint 62 static preflight: {checks-errors.__len__()}/{checks} checks passed.')
if errors:
    for e in errors[:50]: print('FAIL:',e)
    sys.exit(1)
