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
$normalRel = 'tools/calibration/checkpoints/checkpoint-69.json'
$deepRel = 'tools/calibration/checkpoints/checkpoint-69-deep-calibration.json'
$guardedPs = @(
    'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
    'tools/checkpoints/checkpoint-69/apply_checkpoint_69.ps1',
    'tools/checkpoints/checkpoint-69/test_checkpoint_69_contract.ps1',
    'tools/calibration/run_calibration_checkpoint.ps1'
)
& $guard -RepositoryRoot $repositoryRoot -PowerShellPaths $guardedPs -CheckpointDefinitionPaths @($normalRel, $deepRel)

$normal = Get-Content -LiteralPath (Join-Path $repositoryRoot $normalRel) -Raw | ConvertFrom-Json
$deep = Get-Content -LiteralPath (Join-Path $repositoryRoot $deepRel) -Raw | ConvertFrom-Json
Assert-True ([string]$normal.checkpointId -eq '69') 'Checkpoint 69 normal definition ID mismatch.'
Assert-True ([string]$deep.checkpointId -eq '69') 'Checkpoint 69 deep definition ID mismatch.'
Assert-True ([string]$normal.manifestFile -eq 'CHECKPOINT_69_SHA256SUMS.txt') 'Checkpoint 69 normal manifest binding mismatch.'
Assert-True ([string]$deep.manifestFile -eq 'CHECKPOINT_69_SHA256SUMS.txt') 'Checkpoint 69 deep manifest binding mismatch.'
Assert-True ([string]$normal.outputRoot -eq 'out/checkpoint-69') 'Checkpoint 69 normal output root mismatch.'
Assert-True ([string]$deep.outputRoot -eq 'out/checkpoint-69-deep-calibration') 'Checkpoint 69 deep output root mismatch.'
Assert-True (@($normal.stages).Count -eq 9) 'Checkpoint 69 normal suite must contain 9 stages.'
Assert-True (@($deep.stages).Count -eq 28) 'Checkpoint 69 Deep Calibration must contain 28 stages.'
Assert-True ([int]$normal.checkpointMetrics.monteCarloVariantCount -eq 72 -and [int]$normal.checkpointMetrics.trialsAtDefault -eq 720000) 'Checkpoint 69 normal Monte Carlo workload mismatch.'
Assert-True ([int]$deep.checkpointMetrics.monteCarloVariantCount -eq 1616 -and [int]$deep.checkpointMetrics.trialsAtDefault -eq 16160000) 'Checkpoint 69 Deep Calibration workload mismatch.'

$normalSensorStage = @($normal.stages | Where-Object { [string]$_.id -eq 'tl1-sensor-ew-foundation' })
$normalCombatStage = @($normal.stages | Where-Object { [string]$_.id -eq 'tl1-sensor-ew-candidate-operational-combat' })
Assert-True ($normalSensorStage.Count -eq 1 -and $normalCombatStage.Count -eq 1) 'Checkpoint 69 normal suite must contain one deterministic Sensor/EW stage and one operational candidate combat stage.'
Assert-True ([int]$normalSensorStage[0].metrics.profileCount -eq 7 -and [int]$normalSensorStage[0].metrics.deterministicRowCount -eq 924) 'Checkpoint 69 deterministic Sensor/EW matrix mismatch.'
Assert-True ([bool]$normalSensorStage[0].metrics.sameHexLosUnoccludable -and [bool]$normalSensorStage[0].metrics.sameHexEwStillResolves) 'Checkpoint 69 same-hex Sensor/EW metrics are not bound.'
Assert-True ([int]$normalCombatStage[0].metrics.variantCount -eq 72 -and [int]$normalCombatStage[0].metrics.candidateCount -eq 3) 'Checkpoint 69 operational candidate stage matrix mismatch.'
Assert-True (-not [bool]$normalCombatStage[0].metrics.balanceTargetsBlocking) 'Checkpoint 69 candidate combat outcomes must remain diagnostic rather than target-win release gates.'

$studyPath = Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\Scenarios\SensorEw\tl1-sew02-sensor-ew-foundation-range-sweep.json'
$study = Get-Content -LiteralPath $studyPath -Raw | ConvertFrom-Json
Assert-True ([string]$study.schemaVersion -eq 'star-cluster-tl1-sensor-ew-foundation-v1') 'Checkpoint 69 Sensor/EW schema version mismatch.'
Assert-True ([string]$study.id -eq 'tl1-sew02-sensor-ew-foundation-range-sweep') 'Checkpoint 69 Sensor/EW study ID mismatch.'
Assert-True ([int]$study.checkpoint -eq 69 -and [int]$study.maxTacticalSeparationHexes -eq 10) 'Checkpoint 69 Sensor/EW map/range identity mismatch.'
Assert-True (@($study.candidates).Count -eq 7) 'Checkpoint 69 Sensor/EW study must contain one historical control and six forward candidates.'
$forward = @($study.candidates | Where-Object { -not [bool]$_.isHistoricalControl })
Assert-True ($forward.Count -eq 6) 'Checkpoint 69 must contain six forward TL1 sensor candidates.'
Assert-True (@($forward | Where-Object { [int]$_.activePowerCost -ne 1 -or [int]$_.activeOverloadAdditionalPowerCost -ne 1 }).Count -eq 0) 'Forward TL1 candidates must use one 1-TP normal Active mode plus one +1-TP overload.'
$balanced0 = @($study.candidates | Where-Object { [string]$_.id -eq 'balanced-0' })
Assert-True ($balanced0.Count -eq 1) 'Checkpoint 69 must contain exactly one balanced-0 candidate.'
Assert-True ([int]$balanced0[0].passiveFirmRange -eq 1 -and [int]$balanced0[0].passiveApproximateRange -eq 3 -and [int]$balanced0[0].activeFirmRange -eq 3 -and [int]$balanced0[0].activeApproximateRange -eq 4 -and [int]$balanced0[0].activeOverloadFirmBonus -eq 1 -and [int]$balanced0[0].activeOverloadApproximateBonus -eq 1) 'Balanced-0 must remain Passive 1/3, Active 3/4, Overload 4/5.'

$historicalStudyPath = Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\Scenarios\SensorEw\tl1-sew01-sensor-ew-foundation-range-sweep.json'
$historicalHash = (Get-FileHash -LiteralPath $historicalStudyPath -Algorithm SHA256).Hash.ToLowerInvariant()
Assert-True ($historicalHash -eq '986b07d7408883aae7d41c8405a212499023a578b897d4408b9b544af8054b53') 'Checkpoint 68 Sensor/EW study must remain byte-for-byte frozen historical evidence.'

$combatPath = Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\Scenarios\TL1Calibration\tl1-itc11-sensor-ew-candidate-operational-combat.json'
$combat = Get-Content -LiteralPath $combatPath -Raw | ConvertFrom-Json
Assert-True ([string]$combat.id -eq 'tl1-itc11-sensor-ew-candidate-operational-combat') 'Checkpoint 69 operational Sensor/EW study ID mismatch.'
Assert-True ([int]$combat.trialsPerVariant -eq 10000 -and @($combat.variants).Count -eq 72) 'Checkpoint 69 operational Sensor/EW study must define 72 variants at 10,000 trials each by default.'
Assert-True ([string]$combat.sensorEwProfileCatalog -eq 'src/StarCluster.ScenarioRunner/Scenarios/SensorEw/tl1-sew02-sensor-ew-foundation-range-sweep.json') 'Checkpoint 69 operational study must bind the CP69 Sensor/EW profile catalog.'
Assert-True (@($combat.builds).Count -eq 1 -and [string]$combat.builds[0].id -eq 'balanced_generalist_ew_major' -and [int]$combat.builds[0].usedSpace -eq 35) 'Checkpoint 69 operational study must hold the accepted 35-Space EW-capable build fixed.'
foreach ($profileId in @('balanced-0','balanced-1','balanced-2')) {
    Assert-True (@($combat.variants | Where-Object { [string]$_.sensorEwProfileId -eq $profileId }).Count -eq 24) "Checkpoint 69 profile $profileId must have exactly 24 variants."
}
Assert-True (@($combat.variants | Where-Object { [int]$_.startingFuel -ne 100 -or [int]$_.sideAReactorOutputOverride -ne 5 -or [int]$_.sideBReactorOutputOverride -ne 5 }).Count -eq 0) 'Checkpoint 69 operational study must preserve 100 fuel and 5-TP reactor controls.'
Assert-True (@($combat.variants | Where-Object { [int]$_.sideANetEwRangePenalty -ne 0 -or [int]$_.sideBNetEwRangePenalty -ne 0 }).Count -eq 0) 'Checkpoint 69 must not reintroduce static net-EW range penalties.'
$clearNormal = @($combat.variants | Where-Object {
    [string]$_.sideASensorOverloadPolicy -eq 'None' -and
    [string]$_.sideBSensorOverloadPolicy -eq 'None' -and
    [string]$_.sideBEcmPolicy -eq 'None' -and
    [string]$_.sideAEccmPolicy -eq 'None'
})
$clearOverload = @($combat.variants | Where-Object {
    [string]$_.sideASensorOverloadPolicy -eq 'SafeWhenNeeded' -and
    [string]$_.sideBSensorOverloadPolicy -eq 'SafeWhenNeeded' -and
    [string]$_.sideBEcmPolicy -eq 'None' -and
    [string]$_.sideAEccmPolicy -eq 'None'
})
$jammedNoCounter = @($combat.variants | Where-Object {
    [string]$_.sideASensorOverloadPolicy -eq 'SafeWhenNeeded' -and
    [string]$_.sideBSensorOverloadPolicy -eq 'SafeWhenNeeded' -and
    [string]$_.sideBEcmPolicy -eq 'Normal' -and
    [string]$_.sideAEccmPolicy -eq 'None'
})
$jammedEccm = @($combat.variants | Where-Object {
    [string]$_.sideASensorOverloadPolicy -eq 'SafeWhenNeeded' -and
    [string]$_.sideBSensorOverloadPolicy -eq 'SafeWhenNeeded' -and
    [string]$_.sideBEcmPolicy -eq 'Normal' -and
    [string]$_.sideAEccmPolicy -eq 'Normal'
})
Assert-True ($clearNormal.Count -eq 18 -and $clearOverload.Count -eq 18 -and $jammedNoCounter.Count -eq 18 -and $jammedEccm.Count -eq 18) 'Checkpoint 69 operational Sensor/EW package matrix must contain exactly 18 clear-normal, clear-overload, jammed-no-counter, and jammed-ECCM variants.'

$coreSource = Get-Content -LiteralPath (Join-Path $repositoryRoot 'src\StarCluster.Core\Combat\Tracking\SensorEwFoundationResolver.cs') -Raw
Assert-True ($coreSource.Contains('bool hasLineOfSight = distanceHexes == 0 || context.HasLineOfSight;')) 'Same-hex LOS must be explicitly unoccludable.'
Assert-True (-not $coreSource.Contains('if (distanceHexes == 0)')) 'Range zero must not use an early Firm-track return.'
Assert-True ($coreSource.Contains('context.TargetEcmRating - context.ObserverEccmRating')) 'Sensor/EW resolver must compute net ECM from target ECM minus observer ECCM.'
Assert-True ($coreSource.Contains('emissionAssisted == SensorEwFoundationTrackState.Firm')) 'ECM must degrade Firm discrimination rather than subtract physical sensor range.'

$runnerSource = Get-Content -LiteralPath (Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\TL1Calibration\Tl1IntegratedTacticalCombatRunner.cs') -Raw
Assert-True ($runnerSource.Contains('tl1-itc11-sensor-ew-candidate-operational-combat')) 'Integrated runner must register the Checkpoint 69 operational Sensor/EW study.'
Assert-True ($runnerSource.Contains('ValidateTl1SensorEwCandidateCombatCoverage')) 'Integrated runner must bind Checkpoint 69 pre-run matrix validation.'
Assert-True ($runnerSource.Contains('ResolveFoundationTrackQuality')) 'Integrated combat must call the causal Sensor/EW resolver for CP69 candidate profiles.'
Assert-True ($runnerSource.Contains('WriteTl1SensorEwCandidateCombatReview')) 'Integrated runner must write the CP69 candidate review output.'
Assert-True ($runnerSource.Contains('study.Id == Tl1SensorEwCandidateCombatStudyId')) 'Integrated runner must classify the CP69 study in shared release-gate logic.'
Assert-True ($runnerSource -match 'if\s*\(variant\.SideAEcmPolicy\s*!=\s*Tl1IntegratedEwPowerPolicy\.None\s*\|\|\s*variant\.SideBEccmPolicy\s*!=\s*Tl1IntegratedEwPowerPolicy\.None\)') 'Checkpoint 69 package classifier guard must allow Side A ECCM so jammed-ECCM variants are not rejected before classification.'

$programSource = Get-Content -LiteralPath (Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\Program.cs') -Raw
Assert-True ($programSource.Contains('tl1-sew02-sensor-ew-foundation-range-sweep.json')) 'ScenarioRunner default Sensor/EW foundation command must point at the CP69 successor study.'

$concept = Join-Path $repositoryRoot 'docs\Star_Cluster_Game_Concept_v0.6h.docx'
$archivedConcept = Join-Path $repositoryRoot 'docs\archive\Star_Cluster_Game_Concept_v0.6g.docx'
Assert-True (Test-Path -LiteralPath $concept -PathType Leaf) 'Concept v0.6h must be active.'
Assert-True (Test-Path -LiteralPath $archivedConcept -PathType Leaf) 'Concept v0.6g must be archived.'

# Compile-adjacent regression checks learned from prior checkpoint failures.
$changedCs = @(
    'src/StarCluster.Core/Combat/Tracking/SensorEwFoundationResolver.cs',
    'src/StarCluster.ScenarioRunner/TL1SensorEw/Tl1SensorEwFoundationRunner.cs',
    'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatDocuments.cs',
    'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs',
    'src/StarCluster.ScenarioRunner/Program.cs',
    'tests/StarCluster.Tests/Combat/Tracking/SensorEwFoundationResolverTests.cs'
)
foreach ($rel in $changedCs) {
    $source = Get-Content -LiteralPath (Join-Path $repositoryRoot $rel) -Raw
    Assert-True ($source -notmatch '\b(?:ref|out)\s+[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*\b') "Compile-adjacent regression: ordinary properties must not be passed directly by ref/out in $rel."
}

$validationFiles = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs\validation') -File -Filter 'Checkpoint_*.md')
Assert-True ($validationFiles.Count -eq 1 -and $validationFiles[0].Name -eq 'Checkpoint_69_TL1_Sensor_EW_Candidate_Operational_Combat.md') 'Exactly one Checkpoint 69 active validation runbook must remain.'
$rootTxt = @(Get-ChildItem -LiteralPath $repositoryRoot -File -Filter '*.txt')
Assert-True ($rootTxt.Count -eq 1 -and $rootTxt[0].Name -eq 'CHECKPOINT_69_SHA256SUMS.txt') 'Repository root must contain only CHECKPOINT_69_SHA256SUMS.txt as .txt.'
$archivedTxt = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs\archive') -Recurse -File -Filter '*.txt')
Assert-True ($archivedTxt.Count -eq 0) 'Generated historical checkpoint .txt artifacts must not remain under docs/archive.'

Write-Host '       Checkpoint 69 native dependency contract: PowerShell + pinned .NET only; active Python runtime dependencies are rejected before native work.'
Write-Host '       Sensor/EW foundation: 7 profiles x 12 contexts x 11 ranges = 924 deterministic rows; Balanced-0 adds Passive Approximate range without extending Passive Firm range.'
Write-Host '       Same-hex guardrail: LOS cannot be occluded, but emissions and ECM/ECCM discrimination still resolve normally at range zero.'
Write-Host '       Operational candidate study: Balanced-0/1/2 x 3 weapon pairings x 2 movement orders x 4 Sensor/EW packages = 72 variants / 720,000 default trials.'
Write-Host '       Validation tiers: 9 normal stages / 72 MC variants; Deep Calibration 28 stages / 1,616 MC variants.'
Write-Host 'Checkpoint 69 contract validation passed.'
