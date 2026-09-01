[CmdletBinding()]
param()

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path

function Assert-True([bool]$Condition, [string]$Message) { if (-not $Condition) { throw $Message } }
function Read-Json([string]$Path) { Assert-True (Test-Path -LiteralPath $Path -PathType Leaf) "Missing JSON file: $Path"; return (Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json) }
function Find-ById($Items, [string]$Id) { foreach ($item in @($Items)) { if ([string]$item.id -eq $Id) { return $item } }; return $null }
function Assert-Hash([string]$RelativePath, [string]$Expected) {
    $path = Join-Path $repositoryRoot $RelativePath
    Assert-True (Test-Path -LiteralPath $path -PathType Leaf) "Missing frozen historical file: $RelativePath"
    $actual = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    Assert-True ($actual -eq $Expected) "Historical file drifted: $RelativePath ($actual expected $Expected)."
}

$guard = Join-Path $repositoryRoot 'tools\checkpoints\Test-NativeAcceptanceDependencies.ps1'
$guardedPowerShellPaths = @(
    'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
    'tools/checkpoints/checkpoint-66b/apply_checkpoint_66b.ps1',
    'tools/checkpoints/checkpoint-66b/test_checkpoint_66b_contract.ps1',
    'tools/calibration/run_calibration_checkpoint.ps1'
)
$guardedDefinitionPaths = @(
    'tools/calibration/checkpoints/checkpoint-66b.json',
    'tools/calibration/checkpoints/checkpoint-66b-deep-calibration.json'
)
& $guard -RepositoryRoot $repositoryRoot -PowerShellPaths $guardedPowerShellPaths -CheckpointDefinitionPaths $guardedDefinitionPaths

$baseline = Read-Json (Join-Path $repositoryRoot 'docs\design\player_technology\tl1_35_space_player_cruiser_baseline_v0_8.json')
$study = Read-Json (Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\Scenarios\TL1Calibration\tl1-itc09-scripted-overload-tactics.json')
$schema = Read-Json (Join-Path $repositoryRoot 'docs\design\player_technology\tl1_integrated_tactical_combat_schema_v0_12.json')
$policy = Read-Json (Join-Path $repositoryRoot 'docs\design\testing\checkpoint_66_validation_suite_policy_v0_1.json')
$active = Read-Json (Join-Path $repositoryRoot 'tools\calibration\checkpoints\checkpoint-66b.json')
$deep = Read-Json (Join-Path $repositoryRoot 'tools\calibration\checkpoints\checkpoint-66b-deep-calibration.json')
$numericRows = Import-Csv -LiteralPath (Join-Path $repositoryRoot 'docs\archive\player_technology\pre-cp165-active\tl1_core_combat_numerical_baseline_v0_2.csv')

Assert-Hash 'docs\archive\Star_Cluster_Game_Concept_v0.6d.docx' '931f5c4810c1d68588afe84f1c0f9e14627efdf1cab71dab839ab61d11d9f8e5'
Assert-Hash 'docs\design\player_technology\tl1_integrated_tactical_combat_schema_v0_11.json' '62c0a380ebb446c5332620188a9701bd993085dce47c605f33aee63fc59107cc'
Assert-Hash 'docs\design\player_technology\tl1_35_space_player_cruiser_baseline_v0_7.json' '8e7832787bf8f21f984fbc407121ed837826cc5f9f0de2d8bbe7fb193095a044'
Assert-Hash 'src\StarCluster.ScenarioRunner\Scenarios\TL1Calibration\tl1-itc08-bilateral-tactical-geometry-fuel-movement-order.json' '1b5abacd9051130c7dd4b7de1f0064e487a636d351a809cf71a671f09911e75e'

Assert-True ([int]$baseline.checkpoint -eq 66) 'TL1 baseline must identify Checkpoint 66.'
Assert-True ([int]$baseline.installationSpace.playerCruiserTotal -eq 35) 'TL1 construction baseline changed unexpectedly.'
Assert-True ([int]$baseline.scriptedOverloadTacticsStudy.variantCount -eq 80) 'Checkpoint 66 baseline must define 80 variants.'
Assert-True ([int]$baseline.scriptedOverloadTacticsStudy.productionReactorOutput -eq 5) 'Production TL1 reactor must remain 5 TP.'
Assert-True ([int]$baseline.scriptedOverloadTacticsStudy.map.radius -eq 5 -and [int]$baseline.scriptedOverloadTacticsStudy.map.cellCount -eq 91) 'Checkpoint 66 map baseline mismatch.'
Assert-True ([int]$baseline.scriptedOverloadTacticsStudy.fuel.startingFuel -eq 200 -and [int]$baseline.scriptedOverloadTacticsStudy.fuel.fuelPerTraversedHex -eq 2 -and [int]$baseline.scriptedOverloadTacticsStudy.fuel.evasiveManeuverFlatFuelPerTurn -eq 1) 'Checkpoint 66 fuel baseline mismatch.'
Assert-True ([int]$baseline.scriptedOverloadTacticsStudy.stlOverload.additionalTacticalPower -eq 1 -and [int]$baseline.scriptedOverloadTacticsStudy.stlOverload.movementBonus -eq 1 -and [int]$baseline.scriptedOverloadTacticsStudy.stlOverload.extraFuel -eq 2 -and [int]$baseline.scriptedOverloadTacticsStudy.stlOverload.strainLimit -eq 2) 'TL1 STL overload baseline mismatch.'
Assert-True ([int]$baseline.scriptedOverloadTacticsStudy.activeSensorOverload.overloadTotalPower -eq 3 -and [int]$baseline.scriptedOverloadTacticsStudy.activeSensorOverload.firmAndApproximateRangeBonus -eq 2 -and [int]$baseline.scriptedOverloadTacticsStudy.activeSensorOverload.strainLimit -eq 2) 'TL1 Active Sensor overload baseline mismatch.'
Assert-True (-not [bool]$baseline.scriptedOverloadTacticsStudy.balanceTargetsBlocking -and [bool]$baseline.scriptedOverloadTacticsStudy.fullTacticalAiDeferred) 'Checkpoint 66 must remain diagnostic and defer full tactical AI.'

# Import-Csv uses the authoritative v0.2 header `parameter_id`, not `key`.
# Validate the schema before reading rows so StrictMode reports a useful contract
# failure if the numerical-baseline format ever drifts again.
Assert-True (@($numericRows).Count -gt 0) 'Numerical baseline CSV must contain at least one data row.'
$numericColumns = @($numericRows[0].PSObject.Properties.Name)
Assert-True ($numericColumns -contains 'parameter_id' -and $numericColumns -contains 'value') 'Numerical baseline CSV must contain parameter_id and value columns.'
function Numeric-Value([string]$ParameterId) {
    $row = @($numericRows | Where-Object { [string]$_.parameter_id -eq $ParameterId })
    Assert-True ($row.Count -eq 1) "Expected exactly one numerical-baseline row for $ParameterId."
    return [double]$row[0].value
}
Assert-True ((Numeric-Value 'fuel_capacity') -eq 200 -and (Numeric-Value 'stl_fuel_per_hex') -eq 2 -and (Numeric-Value 'evasive_flat_fuel_cost') -eq 1) 'Numerical fuel baseline mismatch.'
Assert-True ((Numeric-Value 'stl_overload_move_bonus') -eq 1 -and (Numeric-Value 'stl_overload_power_cost') -eq 1 -and (Numeric-Value 'stl_overload_extra_fuel') -eq 2 -and (Numeric-Value 'stl_overload_strain_cost') -eq 1 -and (Numeric-Value 'stl_strain_limit') -eq 2) 'Numerical STL overload baseline mismatch.'
Assert-True ((Numeric-Value 'active_sensor_overload_range') -eq 2 -and (Numeric-Value 'active_sensor_overload_power_cost') -eq 1 -and (Numeric-Value 'active_sensor_overload_strain_cost') -eq 1 -and (Numeric-Value 'active_sensor_strain_limit') -eq 2) 'Numerical Active Sensor overload baseline mismatch.'

Assert-True ([string]$study.id -eq 'tl1-itc09-scripted-overload-tactics') 'Unexpected Checkpoint 66/66b study ID.'
Assert-True (@($study.variants).Count -eq 80) 'Checkpoint 66/66b study must define exactly 80 variants.'
$pairs = @(@('Kinetic','Missile'), @('Missile','Kinetic'), @('Energy','Missile'), @('Missile','Energy'), @('Missile','Missile'))
$ewValues = @(0,1)
$plans = @(
    @{ Stl='None'; Sensor='None' },
    @{ Stl='SafeRangePressure'; Sensor='None' },
    @{ Stl='None'; Sensor='SafeWhenNeeded' },
    @{ Stl='SafeRangePressure'; Sensor='SafeWhenNeeded' }
)
$orders = @('SideAFirst','SideBFirst')
foreach ($pair in $pairs) {
    foreach ($ew in $ewValues) {
        $lane = @($study.variants | Where-Object { [string]$_.sideAFamily -eq $pair[0] -and [string]$_.sideBFamily -eq $pair[1] -and [int]$_.sideANetEwRangePenalty -eq $ew -and [int]$_.sideBNetEwRangePenalty -eq $ew })
        Assert-True ($lane.Count -eq 8) "Expected 8 variants for $($pair[0])/$($pair[1])/EW$ew."
        Assert-True (@($lane | ForEach-Object { [string]$_.comparisonGroup } | Select-Object -Unique).Count -eq 1) 'Each weapon/EW lane must share one comparison group.'
        foreach ($plan in $plans) {
            foreach ($order in $orders) {
                $matches = @($lane | Where-Object { [string]$_.sideAStlOverloadPolicy -eq $plan.Stl -and [string]$_.sideASensorOverloadPolicy -eq $plan.Sensor -and [string]$_.movementOrder -eq $order })
                Assert-True ($matches.Count -eq 1) "Missing overload plan/order combination for $($pair[0])/$($pair[1])/EW$ew/$($plan.Stl)/$($plan.Sensor)/$order."
                $v = $matches[0]
                Assert-True ([string]$v.sideBStlOverloadPolicy -eq 'None' -and [string]$v.sideBSensorOverloadPolicy -eq 'None') "Variant $($v.id) must keep Side B overload disabled."
                Assert-True ([string]$v.movementMode -eq 'TrackAwareOpponentRange' -and [string]$v.sideATrackPolicy -eq 'AcquisitionFirstAutoActive' -and [string]$v.sideBTrackPolicy -eq 'AcquisitionFirstAutoActive') "Variant $($v.id) bilateral sensing mismatch."
                Assert-True ([int]$v.tacticalMapRadius -eq 5 -and [int]$v.initialRangeHexes -eq 4 -and [int]$v.startingFuel -eq 200 -and [int]$v.movementFuelPerHex -eq 2) "Variant $($v.id) geometry/fuel mismatch."
                Assert-True ([int]$v.sideAReactorOutputOverride -eq 5 -and [int]$v.sideBReactorOutputOverride -eq 5) "Variant $($v.id) reactor mismatch."
                Assert-True ([string]$v.sideATacticalPowerDoctrine -eq 'FullVolleyFirst' -and [string]$v.sideBTacticalPowerDoctrine -eq 'FullVolleyFirst') "Variant $($v.id) power doctrine mismatch."
                Assert-True (-not [bool]$v.evasiveManeuversEnabled -and -not [bool]$v.escapeDisengagementEnabled) "Variant $($v.id) must keep EvM/disengagement off."
            }
        }
    }
}

$variantProps = $schema.'$defs'.variant.properties
Assert-True (@($variantProps.sideAStlOverloadPolicy.enum) -contains 'SafeRangePressure' -and @($variantProps.sideBStlOverloadPolicy.enum) -contains 'SafeRangePressure') 'Schema v0.12 missing STL overload policy.'
Assert-True (@($variantProps.sideASensorOverloadPolicy.enum) -contains 'SafeWhenNeeded' -and @($variantProps.sideBSensorOverloadPolicy.enum) -contains 'SafeWhenNeeded') 'Schema v0.12 missing sensor overload policy.'

Assert-True ([string]$active.checkpointId -eq '66b' -and [string]$deep.checkpointId -eq '66b') 'Checkpoint definitions must identify 66b.'
Assert-True ([string]$active.manifestFile -eq 'CHECKPOINT_66B_SHA256SUMS.txt' -and [string]$deep.manifestFile -eq 'CHECKPOINT_66B_SHA256SUMS.txt') 'Checkpoint definitions must bind the CP66b manifest.'
Assert-True ([string]$active.outputRoot -eq 'out/checkpoint-66b' -and [string]$deep.outputRoot -eq 'out/checkpoint-66b-deep-calibration') 'Checkpoint 66b output roots mismatch.'
Assert-True ([string]$active.primaryStudy.id -eq 'tl1-scripted-overload-tactics' -and [int]$active.primaryStudy.variantCount -eq 80) 'Normal primaryStudy metadata mismatch.'
Assert-True ([string]$deep.primaryStudy.id -eq 'tl1-scripted-overload-tactics' -and [int]$deep.primaryStudy.variantCount -eq 80) 'Deep primaryStudy metadata mismatch.'
Assert-True ([int]$active.checkpointMetrics.stageCount -eq 8 -and [int]$active.checkpointMetrics.monteCarloVariantCount -eq 80 -and [int]$active.checkpointMetrics.trialsAtDefault -eq 800000) 'Checkpoint 66 normal workload mismatch.'
Assert-True ([int]$deep.checkpointMetrics.stageCount -eq 25 -and [int]$deep.checkpointMetrics.monteCarloVariantCount -eq 1484 -and [int]$deep.checkpointMetrics.trialsAtDefault -eq 14840000) 'Checkpoint 66 Deep workload mismatch.'
Assert-True (@($policy.mustAlwaysRunStageIds).Count -eq 8 -and @($policy.deepCalibrationStageIds).Count -eq 17) 'Checkpoint 66 tier policy count mismatch.'

foreach ($definition in @($active,$deep)) {
    $pre = $definition.nativeDependencyPrecheck
    Assert-True ([bool]$pre.required -and [string]$pre.script -eq 'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1') 'CP66b definitions must require the shared native dependency precheck.'
    Assert-True (@($pre.powerShellPaths) -contains 'tools/calibration/run_calibration_checkpoint.ps1' -and @($pre.powerShellPaths) -contains 'tools/checkpoints/checkpoint-66b/apply_checkpoint_66b.ps1' -and @($pre.powerShellPaths) -contains 'tools/checkpoints/checkpoint-66b/test_checkpoint_66b_contract.ps1') 'CP66b dependency precheck must inspect apply/contract/shared harness.'
    Assert-True (@($pre.checkpointDefinitionPaths) -contains 'tools/calibration/checkpoints/checkpoint-66b.json' -and @($pre.checkpointDefinitionPaths) -contains 'tools/calibration/checkpoints/checkpoint-66b-deep-calibration.json') 'CP66b dependency precheck must inspect normal and deep definitions.'
}

$applySource = Get-Content -LiteralPath (Join-Path $repositoryRoot 'tools\checkpoints\checkpoint-66b\apply_checkpoint_66b.ps1') -Raw
$guardCallIndex = $applySource.IndexOf('& $dependencyGuard')
$contractCallIndex = $applySource.LastIndexOf('& $contractCheck')
$harnessCallIndex = $applySource.LastIndexOf('& $harness')
Assert-True ($guardCallIndex -ge 0 -and $guardCallIndex -lt $contractCallIndex -and $contractCallIndex -lt $harnessCallIndex) 'CP66b apply script must run the native dependency precheck before contract and harness.'
Assert-True ($applySource -notmatch '\$LASTEXITCODE') 'CP66b apply script must not read LASTEXITCODE.'
$harnessSource = Get-Content -LiteralPath (Join-Path $repositoryRoot 'tools\calibration\run_calibration_checkpoint.ps1') -Raw
Assert-True ($harnessSource -match 'Invoke-RequiredNativeDependencyPrecheck' -and $harnessSource -match '\$checkpointNumber -lt 66' -and $harnessSource -match "Register-CalibrationOperation -Name 'NativeDependencyPrecheck'") 'Shared harness must enforce the native dependency precheck for CP66+.'

$contractSource = Get-Content -LiteralPath (Join-Path $repositoryRoot 'tools\checkpoints\checkpoint-66b\test_checkpoint_66b_contract.ps1') -Raw
Assert-True ($contractSource -notmatch '\$_\.key') 'CP66b contract must not read the nonexistent numerical-baseline .key property.'
Assert-True ($contractSource -match 'parameter_id' -and $contractSource -match 'numericColumns') 'CP66b contract must validate the numerical-baseline parameter_id/value schema before row lookup.'

$runner = Get-Content -LiteralPath (Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\TL1Calibration\Tl1IntegratedTacticalCombatRunner.cs') -Raw
$documents = Get-Content -LiteralPath (Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\TL1Calibration\Tl1IntegratedTacticalCombatDocuments.cs') -Raw
Assert-True ($documents -match 'Tl1IntegratedStlOverloadPolicy' -and $documents -match 'SafeRangePressure' -and $documents -match 'Tl1IntegratedSensorOverloadPolicy' -and $documents -match 'SafeWhenNeeded') 'Integrated document model missing CP66 overload policy enums.'
Assert-True ($runner -match 'tl1-itc09-scripted-overload-tactics' -and $runner -match 'PrepareSafeStlOverload' -and $runner -match 'ActiveSensorOverloadService' -and $runner -match 'tl1-c66-no-overload-control') 'Integrated runner missing CP66 overload mechanics/gates.'
Assert-True ($runner -match 'scripted-overload-tactics-review.csv') 'Integrated runner missing CP66 review output.'
$buildGatesStart = $runner.IndexOf('private static IReadOnlyList<Tl1IntegratedTacticalCombatGate> BuildGates(')
$buildGatesEnd = $runner.IndexOf('private static bool IsFixedRange(', $buildGatesStart + 1)
$c66GateMarker = $runner.IndexOf('"tl1-c66-variant-coverage"')
$validateStart = $runner.IndexOf('private static void Validate(')
$validateEnd = $runner.IndexOf('private static void ValidateTl2CandidateCoverage(', $validateStart + 1)
Assert-True ($buildGatesStart -ge 0 -and $buildGatesEnd -gt $buildGatesStart) 'Unable to locate BuildGates source span.'
Assert-True ($c66GateMarker -gt $buildGatesStart -and $c66GateMarker -lt $buildGatesEnd) 'CP66 result-dependent gate block must live inside BuildGates where gates/results/tolerance are in scope.'
if ($validateStart -ge 0 -and $validateEnd -gt $validateStart) {
    $validateSpan = $runner.Substring($validateStart, $validateEnd - $validateStart)
    Assert-True ($validateSpan -notmatch 'tl1-c66-variant-coverage' -and $validateSpan -notmatch 'gates\.Add') 'Pre-run Validate method must not contain CP66 result-dependent gates.Add logic.'
}

$validationFiles = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs\validation') -File -Filter 'Checkpoint_*.md')
Assert-True ($validationFiles.Count -eq 1 -and $validationFiles[0].Name -eq 'Checkpoint_66b_Integrated_Gate_Scope_Compile_Hotfix.md') 'Exactly one CP66b active validation runbook must remain.'
$rootTxt = @(Get-ChildItem -LiteralPath $repositoryRoot -File -Filter '*.txt')
Assert-True ($rootTxt.Count -eq 1 -and $rootTxt[0].Name -eq 'CHECKPOINT_66B_SHA256SUMS.txt') 'Repository root must contain only CHECKPOINT_66B_SHA256SUMS.txt as .txt.'
$archivedTxt = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs\archive') -Recurse -File -Filter '*.txt')
Assert-True ($archivedTxt.Count -eq 0) 'Generated historical checkpoint .txt artifacts must not remain under docs/archive.'

Write-Host '       Checkpoint 66b native dependency contract: shared harness + checkpoint guard reject Python runtime dependencies for CP66+.'
Write-Host '       Concept v0.6e preserves existing TP windows/Strain rules and records bounded TL1 STL, Active Sensor, and EW overload modes.'
Write-Host '       Scripted overload study: 5 ordered weapon pairs x 2 EW regimes x 4 Side-A plans x 2 movement orders = 80 variants.'
Write-Host '       Safe-only overload doctrine stops before Forced Overload; full tactical-response AI and overload-damage integration remain deferred.'
Write-Host '       Historical CP65b Concept/schema/baseline/study inputs are frozen by SHA-256.'
Write-Host '       Validation tiers: 8 normal stages / 80 MC variants; Deep Calibration 25 stages / 1,484 MC variants.'
Write-Host '       Hotfix: CP66 result-dependent gates are scoped inside BuildGates; numerical-baseline and no-Python guards remain intact.'
