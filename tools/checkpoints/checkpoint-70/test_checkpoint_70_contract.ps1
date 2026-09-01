[CmdletBinding()]
param()

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path

function Assert-True {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) { throw $Message }
}

$guard = Join-Path $repositoryRoot 'tools\checkpoints\Test-NativeAcceptanceDependencies.ps1'
$normalRel = 'tools/calibration/checkpoints/checkpoint-70.json'
$deepRel = 'tools/calibration/checkpoints/checkpoint-70-deep-calibration.json'
$guardedPs = @(
    'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
    'tools/checkpoints/checkpoint-70/apply_checkpoint_70.ps1',
    'tools/checkpoints/checkpoint-70/test_checkpoint_70_contract.ps1',
    'tools/calibration/run_calibration_checkpoint.ps1'
)
& $guard -RepositoryRoot $repositoryRoot -PowerShellPaths $guardedPs -CheckpointDefinitionPaths @($normalRel, $deepRel)

$normal = Get-Content -LiteralPath (Join-Path $repositoryRoot $normalRel) -Raw | ConvertFrom-Json
$deep = Get-Content -LiteralPath (Join-Path $repositoryRoot $deepRel) -Raw | ConvertFrom-Json
Assert-True ([string]$normal.checkpointId -eq '70' -and [string]$deep.checkpointId -eq '70') 'Checkpoint 70 definition ID mismatch.'
Assert-True ([string]$normal.manifestFile -eq 'CHECKPOINT_70_SHA256SUMS.txt' -and [string]$deep.manifestFile -eq 'CHECKPOINT_70_SHA256SUMS.txt') 'Checkpoint 70 manifest binding mismatch.'
Assert-True ([string]$normal.outputRoot -eq 'out/checkpoint-70' -and [string]$deep.outputRoot -eq 'out/checkpoint-70-deep-calibration') 'Checkpoint 70 output-root binding mismatch.'
Assert-True (@($normal.stages).Count -eq 11) 'Checkpoint 70 normal suite must contain 11 stages.'
Assert-True (@($deep.stages).Count -eq 30) 'Checkpoint 70 Deep Calibration must contain 30 stages.'
Assert-True ([int]$normal.checkpointMetrics.monteCarloVariantCount -eq 99 -and [int]$normal.checkpointMetrics.trialsAtDefault -eq 990000 -and [int]$normal.checkpointMetrics.smokeTrialsAtDefault -eq 99 -and [int]$normal.checkpointMetrics.totalTrialExecutionsAtDefault -eq 990099) 'Checkpoint 70 normal workload mismatch.'
Assert-True ([int]$deep.checkpointMetrics.monteCarloVariantCount -eq 1643 -and [int]$deep.checkpointMetrics.trialsAtDefault -eq 16430000 -and [int]$deep.checkpointMetrics.smokeTrialsAtDefault -eq 99 -and [int]$deep.checkpointMetrics.totalTrialExecutionsAtDefault -eq 16430099) 'Checkpoint 70 Deep Calibration workload mismatch.'

$expectedGuardedDefs = @($normalRel, $deepRel)
foreach ($definitionDocument in @($normal, $deep)) {
    Assert-True ([bool]$definitionDocument.nativeDependencyPrecheck.required) 'Checkpoint 70 definitions must require native dependency precheck.'
    Assert-True ((@($definitionDocument.nativeDependencyPrecheck.powerShellPaths) -join '|') -eq ($guardedPs -join '|')) 'Checkpoint 70 native dependency PowerShell path binding mismatch.'
    Assert-True ((@($definitionDocument.nativeDependencyPrecheck.checkpointDefinitionPaths) -join '|') -eq ($expectedGuardedDefs -join '|')) 'Checkpoint 70 native dependency definition path binding mismatch.'
}

$policyPath = Join-Path $repositoryRoot 'docs\design\testing\checkpoint_70_validation_suite_policy_v0_1.json'
$policy = Get-Content -LiteralPath $policyPath -Raw | ConvertFrom-Json
Assert-True ([int]$policy.normal.stageCount -eq 11 -and [int]$policy.normal.smokeTrials -eq 99 -and [int]$policy.normal.totalTrialExecutions -eq 990099) 'Checkpoint 70 normal validation-policy workload mismatch.'
Assert-True ([int]$policy.deepCalibration.stageCount -eq 30 -and [int]$policy.deepCalibration.smokeTrials -eq 99 -and [int]$policy.deepCalibration.totalTrialExecutions -eq 16430099) 'Checkpoint 70 Deep Calibration policy workload mismatch.'
Assert-True (-not [bool]$policy.blockingBalanceTargets) 'Checkpoint 70 outcome targets must remain non-blocking.'
Assert-True ([int]$policy.productionControls.ecmNormalPowerCost -eq 1 -and -not [bool]$policy.productionControls.ecmPowerCostChangedByCheckpoint70) 'Checkpoint 70 must not promote a new production ECM cost.'

$studyRel = 'src/StarCluster.ScenarioRunner/Scenarios/TL1Calibration/tl1-itc12-ecm-power-cost-point-blank-counterplay.json'
$study = Get-Content -LiteralPath (Join-Path $repositoryRoot $studyRel) -Raw | ConvertFrom-Json
Assert-True ([string]$study.id -eq 'tl1-itc12-ecm-power-cost-point-blank-counterplay') 'Checkpoint 70 study ID mismatch.'
Assert-True ([int]$study.trialsPerVariant -eq 10000 -and @($study.variants).Count -eq 99) 'Checkpoint 70 study workload mismatch.'
Assert-True ([string]$study.sensorEwProfileCatalog -eq 'src/StarCluster.ScenarioRunner/Scenarios/SensorEw/tl1-sew02-sensor-ew-foundation-range-sweep.json') 'Checkpoint 70 Sensor/EW catalog binding mismatch.'
Assert-True (@($study.builds).Count -eq 1 -and [string]$study.builds[0].id -eq 'balanced_generalist_ew_major') 'Checkpoint 70 fixed build mismatch.'

$variants = @($study.variants)
$operational = @($variants | Where-Object { [int]$_.initialRangeHexes -eq 4 })
$pointBlank = @($variants | Where-Object { [int]$_.initialRangeHexes -eq 0 })
Assert-True ($operational.Count -eq 66 -and $pointBlank.Count -eq 33) 'Checkpoint 70 geometry coverage must be 66 operational / 33 point-blank.'
foreach ($cost in 1..5) {
    Assert-True (@($variants | Where-Object { $_.sideBEcmNormalPowerCostOverride -eq $cost }).Count -eq 18) "Checkpoint 70 ECM cost $cost must have exactly 18 variants."
}
$clear = @($variants | Where-Object { [string]$_.sideBEcmPolicy -eq 'None' -and [string]$_.sideAEccmPolicy -eq 'None' })
Assert-True ($clear.Count -eq 9) 'Checkpoint 70 requires exactly nine clear controls.'
$counter = @($variants | Where-Object { [string]$_.sideBEcmPolicy -eq 'Normal' -and [string]$_.sideAEccmPolicy -eq 'Normal' })
Assert-True ($counter.Count -eq 45 -and @($counter | Where-Object { [int]$_.sideAEccmNormalPowerCostOverride -ne 1 }).Count -eq 0) 'Checkpoint 70 matched ECCM variants must hold normal ECCM cost at 1 TP.'
Assert-True (@($pointBlank | Where-Object { [int]$_.sideAStlMovementHexes -ne 0 -or [int]$_.sideBStlMovementHexes -ne 0 -or [string]$_.movementOrder -ne 'Simultaneous' }).Count -eq 0) 'Checkpoint 70 point-blank geometry must remain fixed at range zero.'
Assert-True (@($variants | Where-Object { [string]$_.sensorEwProfileId -ne 'balanced-0' }).Count -eq 0) 'Checkpoint 70 must isolate the Balanced-0 sensor envelope.'
Assert-True (@($variants | Where-Object { [int]$_.sideAReactorOutputOverride -ne 5 -or [int]$_.sideBReactorOutputOverride -ne 5 }).Count -eq 0) 'Checkpoint 70 must retain the 5-TP reactor baseline.'
Assert-True (@($variants | Where-Object { [string]$_.sideASensorOverloadPolicy -ne 'None' -or [string]$_.sideBSensorOverloadPolicy -ne 'None' -or [string]$_.sideAStlOverloadPolicy -ne 'None' -or [string]$_.sideBStlOverloadPolicy -ne 'None' }).Count -eq 0) 'Checkpoint 70 must isolate normal ECM/ECCM cost without STL/Sensor overload.'
Assert-True (@($variants | Where-Object { [int]$_.sideANetEwRangePenalty -ne 0 -or [int]$_.sideBNetEwRangePenalty -ne 0 }).Count -eq 0) 'Checkpoint 70 must not use the historical static net-EW range penalty.'

$schemaSource = Get-Content -LiteralPath (Join-Path $repositoryRoot 'docs\design\player_technology\tl1_integrated_tactical_combat_schema_v0_15.json') -Raw
foreach ($field in @('sideAEcmNormalPowerCostOverride','sideBEcmNormalPowerCostOverride','sideAEccmNormalPowerCostOverride','sideBEccmNormalPowerCostOverride')) {
    Assert-True ($schemaSource.Contains('"' + $field + '"')) "Checkpoint 70 schema is missing $field."
}

$runnerPath = Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\TL1Calibration\Tl1IntegratedTacticalCombatRunner.cs'
$runnerSource = Get-Content -LiteralPath $runnerPath -Raw
Assert-True ($runnerSource.Contains('Tl1EcmPowerCostCounterplayStudyId')) 'Checkpoint 70 runner is missing its study identifier.'
Assert-True ($runnerSource.Contains('RequiredTl1EcmPowerCostCounterplayVariantCount = 99')) 'Checkpoint 70 runner must require 99 variants.'
Assert-True ($runnerSource.Contains('ecmNormalPowerCostOverride ?? 1')) 'Checkpoint 70 runner must preserve 1 TP as default normal ECM cost.'
Assert-True ($runnerSource.Contains('eccmNormalPowerCostOverride ?? 1')) 'Checkpoint 70 runner must preserve 1 TP as default normal ECCM cost.'
Assert-True ($runnerSource.Contains('checked(baseNormalPowerCost +')) 'Checkpoint 70 EW allocation must apply the study cost through the existing component-condition power path.'
Assert-True ($runnerSource.Contains('ValidateTl1EcmPowerCostCounterplayCoverage(')) 'Checkpoint 70 actual-consumer coverage validator is missing.'
Assert-True ($runnerSource.Contains('WriteTl1EcmPowerCostCounterplayReview(')) 'Checkpoint 70 dedicated review writer is missing.'
Assert-True ($runnerSource.Contains('MeanMaximumRange')) 'Checkpoint 70 point-blank gate must be able to lock maximum range.'
Assert-True ($runnerSource.Contains('tl1-c70-outcomes-review-only')) 'Checkpoint 70 balance outcomes must remain diagnostic.'

# Regression checks learned from CP69/69a/69b/69c/69d native failures.
Assert-True (-not $runnerSource.Contains('v.ProtectedCompartmentation || !v.BaseShieldRechargeEnabled ||')) 'Compile regression: nullable BaseShieldRechargeEnabled must be coalesced.'
Assert-True ($runnerSource.Contains('!(v.BaseShieldRechargeEnabled ?? true)')) 'Compile regression: shield default-true coalescing is missing.'
Assert-True (-not $runnerSource.Contains('v.EvasiveManeuversEnabled || !v.PdsEnabled || v.EscapeDisengagementEnabled ||')) 'Compile regression: nullable tactical controls may not be raw bool operands.'
Assert-True ($runnerSource.Contains('v.EvasiveManeuversEnabled != false || v.PdsEnabled != true ||')) 'Compile regression: explicit Evasive/PDS controls are missing.'
$loadSensorStart = $runnerSource.IndexOf('private static IReadOnlyDictionary<string, SensorEwFoundationProfile>', [StringComparison]::Ordinal)
$loadSensorEnd = $runnerSource.IndexOf('private static Tl1SensorEnvelope ResolveSensorEnvelope(', [StringComparison]::Ordinal)
Assert-True ($loadSensorStart -ge 0 -and $loadSensorEnd -gt $loadSensorStart) 'Catalog-binding regression: unable to isolate Sensor/EW loader.'
$loadSensorText = $runnerSource.Substring($loadSensorStart, $loadSensorEnd - $loadSensorStart)
Assert-True ($loadSensorText.Contains('PropertyNameCaseInsensitive = true') -and $loadSensorText.Contains('if (catalog.Candidates is null)')) 'Catalog-binding regression: actual consumer must bind camelCase candidates and reject null collection.'

# Acceptance summary must honor stage-specific smoke trial counts.
$harnessSource = Get-Content -LiteralPath (Join-Path $repositoryRoot 'tools\calibration\run_calibration_checkpoint.ps1') -Raw
Assert-True ($harnessSource.Contains("Test-DefinitionProperty -Definition `$metrics -Name 'trialsPerVariant'")) 'Checkpoint 70 acceptance accounting must inspect stage-specific trialsPerVariant.'
Assert-True ($harnessSource.Contains('$Summary.aggregates.trials += [long]$variantCount * $stageTrials')) 'Checkpoint 70 acceptance accounting must use the resolved per-stage trial count.'
Assert-True ($harnessSource.Contains("Test-DefinitionProperty -Definition `$metrics -Name 'countTowardVariantAggregate'")) 'Checkpoint 70 acceptance accounting must allow preflight/smoke variants to stay out of the substantive variant headline.'
Assert-True (-not $harnessSource.Contains('$Summary.aggregates.trials += [long]$variantCount * [long]$Trials')) 'Checkpoint 70 must reject obsolete smoke trial over-counting.'

$preflight = @($normal.stages | Where-Object { [string]$_.id -eq 'tl1-ecm-power-cost-counterplay-preflight' })
$smoke = @($normal.stages | Where-Object { [string]$_.id -eq 'tl1-ecm-power-cost-counterplay-smoke' })
$full = @($normal.stages | Where-Object { [string]$_.id -eq 'tl1-ecm-power-cost-point-blank-counterplay' })
Assert-True ($preflight.Count -eq 1 -and [string]$preflight[0].command -eq 'tl1-integrated-tactical-combat-preflight' -and -not [bool]$preflight[0].metrics.usesTrials -and -not [bool]$preflight[0].metrics.countTowardVariantAggregate) 'Checkpoint 70 must run one actual-consumer preflight before simulation.'
Assert-True ($smoke.Count -eq 1 -and [string]$smoke[0].command -eq 'tl1-integrated-tactical-combat' -and [int]$smoke[0].metrics.trialsPerVariant -eq 1 -and [int]$smoke[0].metrics.variantCount -eq 99 -and -not [bool]$smoke[0].metrics.countTowardVariantAggregate) 'Checkpoint 70 must run one trial for all 99 variants before the substantive study.'
Assert-True ($full.Count -eq 1 -and [int]$full[0].metrics.variantCount -eq 99 -and -not [bool]$full[0].metrics.balanceTargetsBlocking) 'Checkpoint 70 substantive stage binding mismatch.'

$programSource = Get-Content -LiteralPath (Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\Program.cs') -Raw
Assert-True ($programSource.Contains('Console.Error.WriteLine($"ERROR: {exception}");')) 'Checkpoint 70 must retain full top-level exception diagnostics.'

$concept = Join-Path $repositoryRoot 'docs\Star_Cluster_Game_Concept_v0.6i.docx'
$archivedConcept = Join-Path $repositoryRoot 'docs\archive\Star_Cluster_Game_Concept_v0.6h.docx'
Assert-True (Test-Path -LiteralPath $concept -PathType Leaf) 'Concept v0.6i must be active.'
Assert-True (Test-Path -LiteralPath $archivedConcept -PathType Leaf) 'Concept v0.6h must be archived.'

# Freeze CP69d causal authority and accepted study evidence while CP70 changes only the new sensitivity path.
$frozenHashes = @{
    'src/StarCluster.Core/Combat/Tracking/SensorEwFoundationResolver.cs' = '2bb38d44bf50774210deaa4f0fc9ba5815f24fab392b8c2f7e9674901e9e25dd'
    'src/StarCluster.ScenarioRunner/Scenarios/SensorEw/tl1-sew02-sensor-ew-foundation-range-sweep.json' = '1639d45cedf941925d25cdff91b77c2636ef82a15f389f05916f1efef3d13875'
    'src/StarCluster.ScenarioRunner/Scenarios/TL1Calibration/tl1-itc11-sensor-ew-candidate-operational-combat.json' = '8da880a9da997d019d3a98bd1c0ea89aebecbbb7e41b0057799cb572827daf58'
    'docs/archive/player_technology/pre-cp165-active/tl1_core_combat_numerical_baseline_v0_3.csv' = 'd3020245a1fe2d28f6795c96c3c331d905ed02ef5210f3ab661e3475f70cf5be'
}
foreach ($entry in $frozenHashes.GetEnumerator()) {
    $actual = (Get-FileHash -LiteralPath (Join-Path $repositoryRoot $entry.Key) -Algorithm SHA256).Hash.ToLowerInvariant()
    Assert-True ($actual -eq [string]$entry.Value) "Checkpoint 70 changed frozen CP69d authority/input: $($entry.Key)."
}

$changedCs = @(
    'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatDocuments.cs',
    'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs'
)
foreach ($rel in $changedCs) {
    $source = Get-Content -LiteralPath (Join-Path $repositoryRoot $rel) -Raw
    Assert-True ($source -notmatch '\b(?:ref|out)\s+[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*\b') "Compile-adjacent regression: ordinary properties must not be passed directly by ref/out in $rel."
}

$validationFiles = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs\validation') -File -Filter 'Checkpoint_*.md')
Assert-True ($validationFiles.Count -eq 1 -and $validationFiles[0].Name -eq 'Checkpoint_70_TL1_ECM_Power_Cost_And_Point_Blank_Counterplay.md') 'Exactly one Checkpoint 70 active validation runbook must remain.'
$rootTxt = @(Get-ChildItem -LiteralPath $repositoryRoot -File -Filter '*.txt')
Assert-True ($rootTxt.Count -eq 1 -and $rootTxt[0].Name -eq 'CHECKPOINT_70_SHA256SUMS.txt') 'Repository root must contain only CHECKPOINT_70_SHA256SUMS.txt as .txt.'
$archivedTxt = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs\archive') -Recurse -File -Filter '*.txt')
Assert-True ($archivedTxt.Count -eq 0) 'Generated historical checkpoint .txt artifacts must not remain under docs/archive.'

Write-Host '       Checkpoint 70 native dependency contract: PowerShell + pinned .NET only; active Python runtime dependencies are rejected before native work.'
Write-Host '       Accepted baseline: Checkpoint 69d; 5-TP reactor, 100 fuel, causal same-hex Sensor/EW semantics preserved.'
Write-Host '       ECM sweep: normal cost 1-5 TP, matched normal ECCM fixed at 1 TP; costs above 1 are calibration-only.'
Write-Host '       Point-blank guardrail study: 33 fixed range-zero variants with unoccludable LOS and normal ECM/ECCM discrimination.'
Write-Host '       Operational study: 66 range-control variants; total 99 variants / 990,000 substantive default trials + 99 smoke trials.'
Write-Host '       Validation tiers: 11 normal stages; Deep Calibration 30 stages / 1,643 substantive MC variants + 99 smoke trials.'
Write-Host 'Checkpoint 70 contract validation passed.'
