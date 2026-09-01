[CmdletBinding()]
param()

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path

function Assert-True {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) { throw $Message }
}

function Get-OptionalPropertyValue {
    param(
        [Parameter(Mandatory = $true)]$Object,
        [Parameter(Mandatory = $true)][string]$Name
    )
    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) { return $null }
    return $property.Value
}

$guard = Join-Path $repositoryRoot 'tools\checkpoints\Test-NativeAcceptanceDependencies.ps1'
$normalRel = 'tools/calibration/checkpoints/checkpoint-71.json'
$deepRel = 'tools/calibration/checkpoints/checkpoint-71-deep-calibration.json'
$guardedPs = @(
    'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
    'tools/checkpoints/checkpoint-71/apply_checkpoint_71.ps1',
    'tools/checkpoints/checkpoint-71/test_checkpoint_71_contract.ps1',
    'tools/calibration/run_calibration_checkpoint.ps1'
)
& $guard -RepositoryRoot $repositoryRoot -PowerShellPaths $guardedPs -CheckpointDefinitionPaths @($normalRel, $deepRel)

$normal = Get-Content -LiteralPath (Join-Path $repositoryRoot $normalRel) -Raw | ConvertFrom-Json
$deep = Get-Content -LiteralPath (Join-Path $repositoryRoot $deepRel) -Raw | ConvertFrom-Json
Assert-True ([string]$normal.checkpointId -eq '71' -and [string]$deep.checkpointId -eq '71') 'Checkpoint 71 definition ID mismatch.'
Assert-True ([string]$normal.manifestFile -eq 'CHECKPOINT_71_SHA256SUMS.txt' -and [string]$deep.manifestFile -eq 'CHECKPOINT_71_SHA256SUMS.txt') 'Checkpoint 71 manifest binding mismatch.'
Assert-True ([string]$normal.outputRoot -eq 'out/checkpoint-71' -and [string]$deep.outputRoot -eq 'out/checkpoint-71-deep-calibration') 'Checkpoint 71 output-root binding mismatch.'
Assert-True (@($normal.stages).Count -eq 11) 'Checkpoint 71 normal suite must contain 11 stages.'
Assert-True (@($deep.stages).Count -eq 30) 'Checkpoint 71 Deep Calibration must contain 30 stages.'
Assert-True ([int]$normal.checkpointMetrics.monteCarloVariantCount -eq 27 -and [int]$normal.checkpointMetrics.trialsAtDefault -eq 270000 -and [int]$normal.checkpointMetrics.smokeTrialsAtDefault -eq 27 -and [int]$normal.checkpointMetrics.totalTrialExecutionsAtDefault -eq 270027) 'Checkpoint 71 normal workload mismatch.'
Assert-True ([int]$deep.checkpointMetrics.monteCarloVariantCount -eq 1571 -and [int]$deep.checkpointMetrics.trialsAtDefault -eq 15710000 -and [int]$deep.checkpointMetrics.smokeTrialsAtDefault -eq 27 -and [int]$deep.checkpointMetrics.totalTrialExecutionsAtDefault -eq 15710027) 'Checkpoint 71 Deep Calibration workload mismatch.'

$expectedGuardedDefinitions = @($normalRel, $deepRel)
foreach ($definitionDocument in @($normal, $deep)) {
    Assert-True ([bool]$definitionDocument.nativeDependencyPrecheck.required) 'Checkpoint 71 definitions must require native dependency precheck.'
    Assert-True ((@($definitionDocument.nativeDependencyPrecheck.powerShellPaths) -join '|') -eq ($guardedPs -join '|')) 'Checkpoint 71 native dependency PowerShell path binding mismatch.'
    Assert-True ((@($definitionDocument.nativeDependencyPrecheck.checkpointDefinitionPaths) -join '|') -eq ($expectedGuardedDefinitions -join '|')) 'Checkpoint 71 native dependency definition path binding mismatch.'
}

$policy = Get-Content -LiteralPath (Join-Path $repositoryRoot 'docs\design\testing\checkpoint_71_validation_suite_policy_v0_1.json') -Raw | ConvertFrom-Json
Assert-True ([int]$policy.normal.stageCount -eq 11 -and [int]$policy.normal.monteCarloVariantCount -eq 27 -and [int]$policy.normal.smokeTrials -eq 27 -and [int]$policy.normal.totalTrialExecutions -eq 270027) 'Checkpoint 71 normal validation-policy mismatch.'
Assert-True ([int]$policy.deepCalibration.stageCount -eq 30 -and [int]$policy.deepCalibration.monteCarloVariantCount -eq 1571 -and [int]$policy.deepCalibration.smokeTrials -eq 27 -and [int]$policy.deepCalibration.totalTrialExecutions -eq 15710027) 'Checkpoint 71 Deep Calibration validation-policy mismatch.'
Assert-True (-not [bool]$policy.blockingBalanceTargets) 'Checkpoint 71 outcome targets must remain non-blocking.'
Assert-True ([int]$policy.productionControls.ecmNormalPowerCost -eq 1 -and [int]$policy.productionControls.eccmNormalPowerCost -eq 1) 'Checkpoint 71 must retain normal ECM/ECCM at 1 TP.'
Assert-True (-not [bool]$policy.productionControls.degradedFireImplementedByCheckpoint71) 'Checkpoint 71 must not implement degraded fire.'

$catalogRel = 'src/StarCluster.ScenarioRunner/Scenarios/SensorEw/tl1-sew03-sensor-ew-discrimination-burnthrough.json'
$catalog = Get-Content -LiteralPath (Join-Path $repositoryRoot $catalogRel) -Raw | ConvertFrom-Json
Assert-True ([string]$catalog.id -eq 'tl1-sew03-sensor-ew-discrimination-burnthrough' -and [int]$catalog.checkpoint -eq 71) 'Checkpoint 71 Sensor/EW catalog identity mismatch.'
Assert-True (@($catalog.candidates).Count -eq 7) 'Checkpoint 71 Sensor/EW catalog must retain seven profiles.'
Assert-True (@($catalog.candidates | Where-Object { [int]$_.discriminationResistance -ne 0 -or [int]$_.pointBlankBurnThroughResistance -ne 1 }).Count -eq 0) 'Checkpoint 71 TL1 profiles must use Discrimination Resistance 0 and same-hex Burn-through +1.'
$balanced0 = @($catalog.candidates | Where-Object { [string]$_.id -eq 'balanced-0' })
Assert-True ($balanced0.Count -eq 1 -and [int]$balanced0[0].passiveFirmRange -eq 1 -and [int]$balanced0[0].passiveApproximateRange -eq 3 -and [int]$balanced0[0].activeFirmRange -eq 3 -and [int]$balanced0[0].activeApproximateRange -eq 4) 'Checkpoint 71 Balanced-0 range fixture mismatch.'

$studyRel = 'src/StarCluster.ScenarioRunner/Scenarios/TL1Calibration/tl1-itc13-sensor-discrimination-burnthrough.json'
$study = Get-Content -LiteralPath (Join-Path $repositoryRoot $studyRel) -Raw | ConvertFrom-Json
Assert-True ([string]$study.id -eq 'tl1-itc13-sensor-discrimination-burnthrough' -and [int]$study.trialsPerVariant -eq 10000 -and @($study.variants).Count -eq 27) 'Checkpoint 71 study identity/workload mismatch.'
Assert-True ([int64]$study.masterSeed -eq 700100) 'Checkpoint 71 must preserve CP70 master seed for paired evidence.'
Assert-True ([string]$study.sensorEwProfileCatalog -eq $catalogRel) 'Checkpoint 71 Sensor/EW catalog binding mismatch.'
$variants = @($study.variants)
$operational = @($variants | Where-Object { [int]$_.initialRangeHexes -eq 4 })
$pointBlank = @($variants | Where-Object { [int]$_.initialRangeHexes -eq 0 })
Assert-True ($operational.Count -eq 18 -and $pointBlank.Count -eq 9) 'Checkpoint 71 geometry coverage must be 18 operational / 9 point-blank.'
$clear = @($variants | Where-Object { [string]$_.sideBEcmPolicy -eq 'None' -and [string]$_.sideAEccmPolicy -eq 'None' })
$jammed = @($variants | Where-Object { [string]$_.sideBEcmPolicy -eq 'Normal' -and [string]$_.sideAEccmPolicy -eq 'None' })
$countered = @($variants | Where-Object { [string]$_.sideBEcmPolicy -eq 'Normal' -and [string]$_.sideAEccmPolicy -eq 'Normal' })
Assert-True ($clear.Count -eq 9 -and $jammed.Count -eq 9 -and $countered.Count -eq 9) 'Checkpoint 71 requires nine clear, nine jammed, and nine countered variants.'
$badJammerCost = @($jammed + $countered | Where-Object {
    $value = Get-OptionalPropertyValue -Object $_ -Name 'sideBEcmNormalPowerCostOverride'
    $null -eq $value -or [int]$value -ne 1
})
Assert-True ($badJammerCost.Count -eq 0) 'Checkpoint 71 jammed/countered variants must explicitly use 1-TP normal ECM.'
$badCounterCost = @($countered | Where-Object {
    $value = Get-OptionalPropertyValue -Object $_ -Name 'sideAEccmNormalPowerCostOverride'
    $null -eq $value -or [int]$value -ne 1
})
Assert-True ($badCounterCost.Count -eq 0) 'Checkpoint 71 countered variants must explicitly use 1-TP normal ECCM.'
Assert-True (@($pointBlank | Where-Object { [int]$_.sideAStlMovementHexes -ne 0 -or [int]$_.sideBStlMovementHexes -ne 0 -or [string]$_.movementOrder -ne 'Simultaneous' }).Count -eq 0) 'Checkpoint 71 point-blank geometry must remain fixed at range zero.'
Assert-True (@($variants | Where-Object { [string]$_.sensorEwProfileId -ne 'balanced-0' }).Count -eq 0) 'Checkpoint 71 must isolate Balanced-0.'
Assert-True (@($variants | Where-Object { [int]$_.sideAReactorOutputOverride -ne 5 -or [int]$_.sideBReactorOutputOverride -ne 5 }).Count -eq 0) 'Checkpoint 71 must retain the 5-TP reactor baseline.'
Assert-True (@($variants | Where-Object { [string]$_.sideASensorOverloadPolicy -ne 'None' -or [string]$_.sideBSensorOverloadPolicy -ne 'None' -or [string]$_.sideAStlOverloadPolicy -ne 'None' -or [string]$_.sideBStlOverloadPolicy -ne 'None' }).Count -eq 0) 'Checkpoint 71 must isolate normal Sensor/EW behavior without overload.'
Assert-True (@($variants | Where-Object { [int]$_.sideANetEwRangePenalty -ne 0 -or [int]$_.sideBNetEwRangePenalty -ne 0 }).Count -eq 0) 'Checkpoint 71 must not use the historical static EW range penalty.'
Assert-True (@($variants | Where-Object { -not ([string]$_.comparisonGroup).StartsWith('c70-', [StringComparison]::Ordinal) }).Count -eq 0) 'Checkpoint 71 comparison groups must remain paired to CP70 cost-1 lanes.'

$preflight = @($normal.stages | Where-Object { [string]$_.id -eq 'tl1-sensor-discrimination-burnthrough-preflight' })
$smoke = @($normal.stages | Where-Object { [string]$_.id -eq 'tl1-sensor-discrimination-burnthrough-smoke' })
$full = @($normal.stages | Where-Object { [string]$_.id -eq 'tl1-sensor-discrimination-burnthrough' })
Assert-True ($preflight.Count -eq 1 -and [string]$preflight[0].command -eq 'tl1-integrated-tactical-combat-preflight' -and -not [bool]$preflight[0].metrics.usesTrials -and -not [bool]$preflight[0].metrics.countTowardVariantAggregate) 'Checkpoint 71 must run one actual-consumer preflight.'
Assert-True ($smoke.Count -eq 1 -and [int]$smoke[0].metrics.trialsPerVariant -eq 1 -and [int]$smoke[0].metrics.variantCount -eq 27 -and -not [bool]$smoke[0].metrics.countTowardVariantAggregate) 'Checkpoint 71 must run one trial for all 27 variants before the substantive study.'
Assert-True ($full.Count -eq 1 -and [int]$full[0].metrics.variantCount -eq 27 -and -not [bool]$full[0].metrics.balanceTargetsBlocking) 'Checkpoint 71 substantive stage binding mismatch.'

$resolverSource = Get-Content -LiteralPath (Join-Path $repositoryRoot 'src\StarCluster.Core\Combat\Tracking\SensorEwFoundationResolver.cs') -Raw
Assert-True ($resolverSource.Contains('public int DiscriminationResistance { get; }') -and $resolverSource.Contains('public int PointBlankBurnThroughResistance { get; }')) 'Checkpoint 71 resolver profile fields are missing.'
Assert-True ($resolverSource.Contains('observerProfile.DiscriminationResistance + burnThroughResistance') -and $resolverSource.Contains('netEcm - totalDiscriminationResistance')) 'Checkpoint 71 jamming-margin calculation is missing.'
Assert-True ($resolverSource.Contains('distanceHexes == 0') -and $resolverSource.Contains('PointBlankBurnThroughResistance')) 'Checkpoint 71 point-blank burn-through calculation is missing.'
Assert-True ($resolverSource.Contains('bool hasLineOfSight = distanceHexes == 0 || context.HasLineOfSight;')) 'Checkpoint 71 must preserve unoccludable same-hex LOS.'

$runnerSource = Get-Content -LiteralPath (Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\TL1Calibration\Tl1IntegratedTacticalCombatRunner.cs') -Raw
Assert-True ($runnerSource.Contains('Tl1SensorDiscriminationBurnthroughStudyId') -and $runnerSource.Contains('RequiredTl1SensorDiscriminationBurnthroughVariantCount = 27')) 'Checkpoint 71 runner study registration is incomplete.'
Assert-True ($runnerSource.Contains('ValidateTl1SensorDiscriminationBurnthroughCoverage(') -and $runnerSource.Contains('WriteTl1SensorDiscriminationBurnthroughReview(')) 'Checkpoint 71 actual-consumer validation/report path is incomplete.'
Assert-True ($runnerSource.Contains('candidate.DiscriminationResistance') -and $runnerSource.Contains('candidate.PointBlankBurnThroughResistance')) 'Checkpoint 71 integrated catalog loader must carry new profile fields.'

$testSource = Get-Content -LiteralPath (Join-Path $repositoryRoot 'tests\StarCluster.Tests\Combat\Tracking\SensorEwFoundationResolverTests.cs') -Raw
foreach ($testName in @('PointBlankBurnThroughPreservesFirmAgainstTl1Ecm','PointBlankBurnThroughDoesNotDefeatStrongerEcm','IntrinsicDiscriminationResistanceCanDefeatLowerEcmWithoutEccm','PointBlankBurnThroughDoesNotExtendBeyondSameHex')) {
    Assert-True ($testSource.Contains($testName)) "Checkpoint 71 unit regression is missing: $testName."
}

$programSource = Get-Content -LiteralPath (Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\Program.cs') -Raw
Assert-True ($programSource.Contains('Console.Error.WriteLine($"ERROR: {exception}");')) 'Checkpoint 71 must retain full top-level exception diagnostics.'

# Historical CP70/CP69 inputs remain byte-for-byte reproducible while CP71 opts into new profile fields through sew03.
$frozenHashes = @{
    'src\StarCluster.ScenarioRunner\Scenarios\SensorEw\tl1-sew02-sensor-ew-foundation-range-sweep.json' = '1639d45cedf941925d25cdff91b77c2636ef82a15f389f05916f1efef3d13875'
    'src\StarCluster.ScenarioRunner\Scenarios\TL1Calibration\tl1-itc12-ecm-power-cost-point-blank-counterplay.json' = '950905f28be3c7399582bb2e5d22db009609ff42512e108e7dc1243a2e408835'
    'docs\archive\player_technology\pre-cp165-active\tl1_core_combat_numerical_baseline_v0_3.csv' = 'd3020245a1fe2d28f6795c96c3c331d905ed02ef5210f3ab661e3475f70cf5be'
    'docs\design\player_technology\tl1_integrated_tactical_combat_schema_v0_15.json' = 'bbb444bbfb8c044019d0cf1fce800bc5d036f5e0b56ca2d90c2441e5d20f7d8e'
}
foreach ($entry in $frozenHashes.GetEnumerator()) {
    $actual = (Get-FileHash -LiteralPath (Join-Path $repositoryRoot $entry.Key) -Algorithm SHA256).Hash.ToLowerInvariant()
    Assert-True ($actual -eq [string]$entry.Value) "Checkpoint 71 changed frozen historical input: $($entry.Key)."
}
$archivedConcept = Join-Path $repositoryRoot 'docs\archive\Star_Cluster_Game_Concept_v0.6i.docx'
Assert-True (Test-Path -LiteralPath $archivedConcept -PathType Leaf) 'Concept v0.6i must be archived.'
Assert-True (((Get-FileHash -LiteralPath $archivedConcept -Algorithm SHA256).Hash.ToLowerInvariant()) -eq '9bff5cbc25dba470fc27646a4f2cbb435dc9e0aef193bfd3608ed7e245c05c50') 'Archived Concept v0.6i must remain byte-for-byte frozen.'
Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot 'docs\Star_Cluster_Game_Concept_v0.6j.docx') -PathType Leaf) 'Concept v0.6j must be active.'
Assert-True (-not (Test-Path -LiteralPath (Join-Path $repositoryRoot 'docs\Star_Cluster_Game_Concept_v0.6i.docx') -PathType Leaf)) 'Concept v0.6i must not remain duplicated as an active concept.'
$activeConceptFiles = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs') -File -Filter 'Star_Cluster_Game_Concept_v*.docx')
Assert-True ($activeConceptFiles.Count -eq 1 -and $activeConceptFiles[0].Name -eq 'Star_Cluster_Game_Concept_v0.6j.docx') 'Exactly one active Concept must remain: Star_Cluster_Game_Concept_v0.6j.docx.'

$validationFiles = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs\validation') -File -Filter 'Checkpoint_*.md')
Assert-True ($validationFiles.Count -eq 1 -and $validationFiles[0].Name -eq 'Checkpoint_71_Sensor_Discrimination_Resistance_And_Burnthrough.md') 'Exactly one Checkpoint 71 active validation runbook must remain.'
$rootTxt = @(Get-ChildItem -LiteralPath $repositoryRoot -File -Filter '*.txt')
Assert-True ($rootTxt.Count -eq 1 -and $rootTxt[0].Name -eq 'CHECKPOINT_71_SHA256SUMS.txt') 'Repository root must contain only CHECKPOINT_71_SHA256SUMS.txt as .txt.'

Write-Host '       Checkpoint 71 native dependency contract: PowerShell + pinned .NET only; active Python runtime dependencies are rejected before native work.'
Write-Host '       Accepted baseline: Checkpoint 70a; normal ECM/ECCM remain rating 1 at 1 TP under the 5-TP reactor.'
Write-Host '       Sensor discrimination: TL1 intrinsic resistance 0; same-hex Burn-through Resistance +1; range > 0 burn-through 0.'
Write-Host '       Paired study: 18 operational + 9 fixed point-blank variants = 27 variants / 270,000 substantive default trials + 27 smoke trials.'
Write-Host '       Degraded fire is Concept-only and is not implemented in Checkpoint 71.'
Write-Host '       Validation tiers: 11 normal stages; Deep Calibration 30 stages / 1,571 substantive MC variants + 27 smoke trials.'
Write-Host 'Checkpoint 71 contract validation passed.'
