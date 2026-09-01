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
    param([Parameter(Mandatory = $true)]$Object,[Parameter(Mandatory = $true)][string]$Name)
    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) { return $null }
    return $property.Value
}

$guard = Join-Path $repositoryRoot 'tools\checkpoints\Test-NativeAcceptanceDependencies.ps1'
$normalRel = 'tools/calibration/checkpoints/checkpoint-72.json'
$deepRel = 'tools/calibration/checkpoints/checkpoint-72-deep-calibration.json'
$guardedPs = @(
    'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
    'tools/checkpoints/checkpoint-72/apply_checkpoint_72.ps1',
    'tools/checkpoints/checkpoint-72/test_checkpoint_72_contract.ps1',
    'tools/calibration/run_calibration_checkpoint.ps1'
)
& $guard -RepositoryRoot $repositoryRoot -PowerShellPaths $guardedPs -CheckpointDefinitionPaths @($normalRel, $deepRel)

$normal = Get-Content -LiteralPath (Join-Path $repositoryRoot $normalRel) -Raw | ConvertFrom-Json
$deep = Get-Content -LiteralPath (Join-Path $repositoryRoot $deepRel) -Raw | ConvertFrom-Json
Assert-True ([string]$normal.checkpointId -eq '72' -and [string]$deep.checkpointId -eq '72') 'Checkpoint 72 definition ID mismatch.'
Assert-True ([string]$normal.manifestFile -eq 'CHECKPOINT_72_SHA256SUMS.txt' -and [string]$deep.manifestFile -eq 'CHECKPOINT_72_SHA256SUMS.txt') 'Checkpoint 72 manifest binding mismatch.'
Assert-True (@($normal.stages).Count -eq 11) 'Checkpoint 72 normal suite must contain 11 stages.'
Assert-True (@($deep.stages).Count -eq 30) 'Checkpoint 72 Deep Calibration must contain 30 stages.'
Assert-True ([int]$normal.checkpointMetrics.monteCarloVariantCount -eq 39 -and [int]$normal.checkpointMetrics.trialsAtDefault -eq 390000 -and [int]$normal.checkpointMetrics.smokeTrialsAtDefault -eq 39 -and [int]$normal.checkpointMetrics.totalTrialExecutionsAtDefault -eq 390039) 'Checkpoint 72 normal workload mismatch.'
Assert-True ([int]$deep.checkpointMetrics.monteCarloVariantCount -eq 1583 -and [int]$deep.checkpointMetrics.trialsAtDefault -eq 15830000 -and [int]$deep.checkpointMetrics.smokeTrialsAtDefault -eq 39 -and [int]$deep.checkpointMetrics.totalTrialExecutionsAtDefault -eq 15830039) 'Checkpoint 72 Deep Calibration workload mismatch.'
foreach ($definitionDocument in @($normal, $deep)) {
    Assert-True ([bool]$definitionDocument.nativeDependencyPrecheck.required) 'Checkpoint 72 definitions must require native dependency precheck.'
    Assert-True ((@($definitionDocument.nativeDependencyPrecheck.powerShellPaths) -join '|') -eq ($guardedPs -join '|')) 'Checkpoint 72 native dependency PowerShell binding mismatch.'
    Assert-True ((@($definitionDocument.nativeDependencyPrecheck.checkpointDefinitionPaths) -join '|') -eq (@($normalRel,$deepRel) -join '|')) 'Checkpoint 72 native dependency definition binding mismatch.'
}

$policyRel = 'docs/design/testing/checkpoint_72_validation_suite_policy_v0_1.json'
$policy = Get-Content -LiteralPath (Join-Path $repositoryRoot $policyRel) -Raw | ConvertFrom-Json
Assert-True ([int]$policy.normal.stageCount -eq 11 -and [int]$policy.normal.monteCarloVariantCount -eq 39 -and [int]$policy.normal.smokeTrials -eq 39 -and [int]$policy.normal.totalTrialExecutions -eq 390039) 'Checkpoint 72 normal validation-policy mismatch.'
Assert-True ([int]$policy.deepCalibration.stageCount -eq 30 -and [int]$policy.deepCalibration.monteCarloVariantCount -eq 1583 -and [int]$policy.deepCalibration.smokeTrials -eq 39 -and [int]$policy.deepCalibration.totalTrialExecutions -eq 15830039) 'Checkpoint 72 Deep Calibration validation-policy mismatch.'
Assert-True (-not [bool]$policy.blockingBalanceTargets) 'Checkpoint 72 outcomes must remain non-blocking.'
Assert-True ([bool]$policy.studyControls.ecmBeforeEccm -and -not [bool]$policy.studyControls.ewInitiativeReroll -and [bool]$policy.studyControls.reservedPowerMeansUncommittedPower) 'Checkpoint 72 EW timing policy mismatch.'
Assert-True (-not [bool]$policy.productionControls.movementPhaseFireImplementedByCheckpoint72 -and -not [bool]$policy.productionControls.degradedFireImplementedByCheckpoint72) 'Checkpoint 72 must keep movement-phase fire and degraded fire Concept-only.'

$schemaRel = 'docs/design/player_technology/tl1_integrated_tactical_combat_schema_v0_16.json'
$schema = Get-Content -LiteralPath (Join-Path $repositoryRoot $schemaRel) -Raw | ConvertFrom-Json
Assert-True ([string]$schema.'$id' -eq 'star-cluster-tl1-integrated-tactical-combat-schema-v0-16') 'Checkpoint 72 schema identity mismatch.'
$schemaVariantProperties = $schema.'$defs'.variant.properties
Assert-True (@($schemaVariantProperties.sideAEccmPolicy.enum) -contains 'ReactiveNormal' -and @($schemaVariantProperties.sideBEccmPolicy.enum) -contains 'ReactiveNormal') 'Checkpoint 72 schema must permit ReactiveNormal ECCM.'
Assert-True (-not (@($schemaVariantProperties.sideAEcmPolicy.enum) -contains 'ReactiveNormal') -and -not (@($schemaVariantProperties.sideBEcmPolicy.enum) -contains 'ReactiveNormal')) 'ReactiveNormal must never be an ECM policy.'

$catalogRel = 'src/StarCluster.ScenarioRunner/Scenarios/SensorEw/tl1-sew03-sensor-ew-discrimination-burnthrough.json'
$catalog = Get-Content -LiteralPath (Join-Path $repositoryRoot $catalogRel) -Raw | ConvertFrom-Json
$balanced0 = @($catalog.candidates | Where-Object { [string]$_.id -eq 'balanced-0' })
Assert-True ($balanced0.Count -eq 1 -and [int]$balanced0[0].passiveFirmRange -eq 1 -and [int]$balanced0[0].passiveApproximateRange -eq 3 -and [int]$balanced0[0].activeFirmRange -eq 3 -and [int]$balanced0[0].activeApproximateRange -eq 4 -and [int]$balanced0[0].discriminationResistance -eq 0 -and [int]$balanced0[0].pointBlankBurnThroughResistance -eq 1) 'Checkpoint 72 must preserve the accepted CP71 Balanced-0 EW foundation.'

$studyRel = 'src/StarCluster.ScenarioRunner/Scenarios/TL1Calibration/tl1-itc14-reactive-ew-subphase.json'
$study = Get-Content -LiteralPath (Join-Path $repositoryRoot $studyRel) -Raw | ConvertFrom-Json
Assert-True ([string]$study.id -eq 'tl1-itc14-reactive-ew-subphase' -and [int]$study.trialsPerVariant -eq 10000 -and @($study.variants).Count -eq 39) 'Checkpoint 72 study identity/workload mismatch.'
Assert-True ([int64]$study.masterSeed -eq 720100) 'Checkpoint 72 master seed mismatch.'
Assert-True ([string]$study.sensorEwProfileCatalog -eq $catalogRel) 'Checkpoint 72 Sensor/EW catalog binding mismatch.'
$variants = @($study.variants)
$operational = @($variants | Where-Object { [int]$_.initialRangeHexes -eq 4 })
$pointBlank = @($variants | Where-Object { [int]$_.initialRangeHexes -eq 0 })
Assert-True ($operational.Count -eq 30 -and $pointBlank.Count -eq 9) 'Checkpoint 72 geometry coverage must be 30 operational / 9 point-blank.'
$clear = @($variants | Where-Object { [string]$_.profileLabel -eq 'balanced-0-c72-clear' })
$uniAuto = @($variants | Where-Object { [string]$_.profileLabel -eq 'balanced-0-c72-unilateral-auto' })
$uniReactive = @($variants | Where-Object { [string]$_.profileLabel -eq 'balanced-0-c72-unilateral-reactive' })
$biAuto = @($variants | Where-Object { [string]$_.profileLabel -eq 'balanced-0-c72-bilateral-auto' })
$biReactive = @($variants | Where-Object { [string]$_.profileLabel -eq 'balanced-0-c72-bilateral-reactive' })
Assert-True ($clear.Count -eq 9 -and $uniAuto.Count -eq 9 -and $uniReactive.Count -eq 9 -and $biAuto.Count -eq 6 -and $biReactive.Count -eq 6) 'Checkpoint 72 package coverage mismatch.'
Assert-True (@($variants | Where-Object { [string]$_.sideAEcmPolicy -eq 'ReactiveNormal' -or [string]$_.sideBEcmPolicy -eq 'ReactiveNormal' }).Count -eq 0) 'Checkpoint 72 may not use ReactiveNormal as ECM.'
Assert-True (@($uniReactive | Where-Object { [string]$_.sideAEccmPolicy -ne 'ReactiveNormal' -or [string]$_.sideBEccmPolicy -ne 'None' }).Count -eq 0) 'Checkpoint 72 unilateral reactive ECCM binding mismatch.'
Assert-True (@($biReactive | Where-Object { [string]$_.sideAEccmPolicy -ne 'ReactiveNormal' -or [string]$_.sideBEccmPolicy -ne 'ReactiveNormal' }).Count -eq 0) 'Checkpoint 72 bilateral reactive ECCM binding mismatch.'
Assert-True (@($pointBlank | Where-Object { [int]$_.sideAStlMovementHexes -ne 0 -or [int]$_.sideBStlMovementHexes -ne 0 -or [string]$_.movementOrder -ne 'Simultaneous' }).Count -eq 0) 'Checkpoint 72 point-blank geometry must remain fixed at range zero.'
Assert-True (@($variants | Where-Object { [string]$_.sensorEwProfileId -ne 'balanced-0' -or [int]$_.sideAReactorOutputOverride -ne 5 -or [int]$_.sideBReactorOutputOverride -ne 5 }).Count -eq 0) 'Checkpoint 72 must hold Balanced-0 and 5-TP reactors fixed.'
Assert-True (@($variants | Where-Object { [string]$_.sideASensorOverloadPolicy -ne 'None' -or [string]$_.sideBSensorOverloadPolicy -ne 'None' -or [string]$_.sideAStlOverloadPolicy -ne 'None' -or [string]$_.sideBStlOverloadPolicy -ne 'None' -or [int]$_.sideANetEwRangePenalty -ne 0 -or [int]$_.sideBNetEwRangePenalty -ne 0 }).Count -eq 0) 'Checkpoint 72 must isolate timing without overload/static EW range penalties.'
foreach ($v in @($uniAuto + $uniReactive)) {
    $ecm = Get-OptionalPropertyValue -Object $v -Name 'sideBEcmNormalPowerCostOverride'
    $eccm = Get-OptionalPropertyValue -Object $v -Name 'sideAEccmNormalPowerCostOverride'
    Assert-True ($null -ne $ecm -and [int]$ecm -eq 1 -and $null -ne $eccm -and [int]$eccm -eq 1) "Checkpoint 72 unilateral EW cost override mismatch in $($v.id)."
}
foreach ($v in @($biAuto + $biReactive)) {
    foreach ($name in @('sideAEcmNormalPowerCostOverride','sideBEcmNormalPowerCostOverride','sideAEccmNormalPowerCostOverride','sideBEccmNormalPowerCostOverride')) {
        $value = Get-OptionalPropertyValue -Object $v -Name $name
        Assert-True ($null -ne $value -and [int]$value -eq 1) "Checkpoint 72 bilateral EW cost override mismatch in $($v.id): $name."
    }
}

$preflight = @($normal.stages | Where-Object { [string]$_.id -eq 'tl1-reactive-ew-subphase-preflight' })
$smoke = @($normal.stages | Where-Object { [string]$_.id -eq 'tl1-reactive-ew-subphase-smoke' })
$full = @($normal.stages | Where-Object { [string]$_.id -eq 'tl1-reactive-ew-subphase' })
Assert-True ($preflight.Count -eq 1 -and [string]$preflight[0].command -eq 'tl1-integrated-tactical-combat-preflight' -and -not [bool]$preflight[0].metrics.usesTrials -and -not [bool]$preflight[0].metrics.countTowardVariantAggregate) 'Checkpoint 72 must run one actual-consumer preflight.'
Assert-True ($smoke.Count -eq 1 -and [int]$smoke[0].metrics.trialsPerVariant -eq 1 -and [int]$smoke[0].metrics.variantCount -eq 39 -and -not [bool]$smoke[0].metrics.countTowardVariantAggregate) 'Checkpoint 72 must smoke all 39 variants before substantive trials.'
Assert-True ($full.Count -eq 1 -and [int]$full[0].metrics.variantCount -eq 39 -and -not [bool]$full[0].metrics.balanceTargetsBlocking) 'Checkpoint 72 substantive stage binding mismatch.'

$preCombatSource = Get-Content -LiteralPath (Join-Path $repositoryRoot 'src\StarCluster.Core\Combat\Tracking\PreCombatElectronicWarfareResolver.cs') -Raw
Assert-True ($preCombatSource.Contains('ResolveAfterEcmDeclarations') -and $preCombatSource.Contains('ResolveAfterEccmResponses')) 'Checkpoint 72 pre-combat EW resolver steps are missing.'
Assert-True (-not $preCombatSource.Contains('initiativeOrder') -and -not $preCombatSource.Contains('InitiativeOrder')) 'Checkpoint 72 pre-combat EW resolver must not depend on initiative order.'
$runnerSource = Get-Content -LiteralPath (Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\TL1Calibration\Tl1IntegratedTacticalCombatRunner.cs') -Raw
Assert-True ($runnerSource.Contains('Tl1ReactiveEwSubphaseStudyId') -and $runnerSource.Contains('RequiredTl1ReactiveEwSubphaseVariantCount = 39')) 'Checkpoint 72 runner study registration is incomplete.'
Assert-True ($runnerSource.Contains('AllocateOperationalEcm(') -and $runnerSource.Contains('AllocateOperationalEccm(') -and $runnerSource.Contains('PreCombatElectronicWarfareResolver.ResolveAfterEcmDeclarations(') -and $runnerSource.Contains('PreCombatElectronicWarfareResolver.ResolveAfterEccmResponses(')) 'Checkpoint 72 actual EW timing path is incomplete.'
Assert-True ($runnerSource.Contains('policy == Tl1IntegratedEwPowerPolicy.ReactiveNormal && !reactiveNeeded')) 'Checkpoint 72 reactive ECCM skip condition is missing.'
Assert-True ($runnerSource.Contains('ValidateTl1ReactiveEwSubphaseCoverage(') -and $runnerSource.Contains('WriteTl1ReactiveEwSubphaseReview(')) 'Checkpoint 72 validation/report integration is incomplete.'
$documentSource = Get-Content -LiteralPath (Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\TL1Calibration\Tl1IntegratedTacticalCombatDocuments.cs') -Raw
Assert-True ($documentSource.Contains('ReactiveNormal')) 'Checkpoint 72 EW policy enum is missing ReactiveNormal.'
$testSource = Get-Content -LiteralPath (Join-Path $repositoryRoot 'tests\StarCluster.Tests\Combat\Tracking\PreCombatElectronicWarfareResolverTests.cs') -Raw
foreach ($testName in @('BothEcmDeclarationsResolveBeforeEitherEccmResponse','PointBlankBurnThroughCanMakeEccmResponseUnnecessary','StrongerPointBlankEcmCanStillCreateAnEccmResponseNeed','SymmetricEwResolutionDoesNotDependOnAnInitiativeOrder')) {
    Assert-True ($testSource.Contains($testName)) "Checkpoint 72 unit regression is missing: $testName."
}
$programSource = Get-Content -LiteralPath (Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\Program.cs') -Raw
Assert-True ($programSource.Contains('Console.Error.WriteLine($"ERROR: {exception}");')) 'Checkpoint 72 must retain full top-level exception diagnostics.'

# Freeze CP71 evidence while CP72 changes the successor timing path.
$frozenHashes = @{
    'src\StarCluster.ScenarioRunner\Scenarios\SensorEw\tl1-sew03-sensor-ew-discrimination-burnthrough.json' = 'a8840493f4b5684251b72fb564685fd767cdc182b64715b6ab18f1b487fe2cb0'
    'src\StarCluster.ScenarioRunner\Scenarios\TL1Calibration\tl1-itc13-sensor-discrimination-burnthrough.json' = '01b675b0f27bd646438e64f3e251833430ba97cbf37c81becc34f0d973f5ebd2'
    'docs\archive\player_technology\pre-cp165-active\tl1_core_combat_numerical_baseline_v0_3.csv' = 'd3020245a1fe2d28f6795c96c3c331d905ed02ef5210f3ab661e3475f70cf5be'
    'docs\design\player_technology\tl1_integrated_tactical_combat_schema_v0_15.json' = 'bbb444bbfb8c044019d0cf1fce800bc5d036f5e0b56ca2d90c2441e5d20f7d8e'
    'src\StarCluster.Core\Combat\Tracking\SensorEwFoundationResolver.cs' = '67a26752491f1a91d48dc250f6dd36372a51daa6e1d40ca9947ee614e936dec6'
    'docs\archive\Star_Cluster_Game_Concept_v0.6j.docx' = 'd0d372b06c6a9be8edd5b5e313505e8aba34a569046cc5b7172bbcee0348dae0'
}
foreach ($entry in $frozenHashes.GetEnumerator()) {
    $actual = (Get-FileHash -LiteralPath (Join-Path $repositoryRoot $entry.Key) -Algorithm SHA256).Hash.ToLowerInvariant()
    Assert-True ($actual -eq [string]$entry.Value) "Checkpoint 72 changed frozen CP71 evidence: $($entry.Key)."
}

$sfbRel = 'docs\references\StarfleetBattlesRules.pdf'
Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot $sfbRel) -PathType Leaf) 'Checkpoint 72 must preserve the user-provided SFB reference.'
Assert-True (((Get-FileHash -LiteralPath (Join-Path $repositoryRoot $sfbRel) -Algorithm SHA256).Hash.ToLowerInvariant()) -eq '69c8edab142859cc05f21976092c357c0c43bc9c20b72bdd13a97894dc8b4dae') 'Checkpoint 72 SFB reference hash mismatch.'
$referenceSums = Get-Content -LiteralPath (Join-Path $repositoryRoot 'docs\references\SHA256SUMS.txt') -Raw
Assert-True ($referenceSums.Contains('69c8edab142859cc05f21976092c357c0c43bc9c20b72bdd13a97894dc8b4dae  StarfleetBattlesRules.pdf')) 'SFB reference must be indexed in docs/references/SHA256SUMS.txt.'
$referenceLedger = Get-Content -LiteralPath (Join-Path $repositoryRoot 'docs\design\player_technology\player_reference_library_v0_1.csv') -Raw
Assert-True ($referenceLedger.Contains('SFB_MASTER_2012') -and $referenceLedger.Contains('StarfleetBattlesRules.pdf')) 'Checkpoint 72 reference ledger must index SFB.'

Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot 'docs\Star_Cluster_Game_Concept_v0.6k.docx') -PathType Leaf) 'Concept v0.6k must be active.'
Assert-True (-not (Test-Path -LiteralPath (Join-Path $repositoryRoot 'docs\Star_Cluster_Game_Concept_v0.6j.docx') -PathType Leaf)) 'Concept v0.6j must not remain duplicated as an active concept.'
$activeConceptFiles = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs') -File -Filter 'Star_Cluster_Game_Concept_v*.docx')
Assert-True ($activeConceptFiles.Count -eq 1 -and $activeConceptFiles[0].Name -eq 'Star_Cluster_Game_Concept_v0.6k.docx') 'Exactly one active Concept must remain: v0.6k.'
$validationFiles = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs\validation') -File -Filter 'Checkpoint_*.md')
Assert-True ($validationFiles.Count -eq 1 -and $validationFiles[0].Name -eq 'Checkpoint_72_Reactive_PreCombat_EW_Subphase.md') 'Exactly one Checkpoint 72 active validation runbook must remain.'
$rootTxt = @(Get-ChildItem -LiteralPath $repositoryRoot -File -Filter '*.txt')
Assert-True ($rootTxt.Count -eq 1 -and $rootTxt[0].Name -eq 'CHECKPOINT_72_SHA256SUMS.txt') 'Repository root must contain only CHECKPOINT_72_SHA256SUMS.txt as .txt.'

Write-Host '       Checkpoint 72 native dependency contract: PowerShell + pinned .NET only; active Python runtime dependencies are rejected before native work.'
Write-Host '       EW sequence: post-Movement observation -> ECM declarations -> one ECCM response -> finalized tracks -> combat; no EW initiative reroll.'
Write-Host '       Tactical Power terminology: reserved TP means ordinary Available/uncommitted TP, never a separate pool.'
Write-Host '       Study: 30 operational + 9 point-blank = 39 variants / 390,000 substantive default trials + 39 smoke trials.'
Write-Host '       SFB-inspired intermediate movement engagement windows remain Concept-only; no impulse system or movement-phase fire is implemented.'
Write-Host '       Validation tiers: 11 normal stages; Deep Calibration 30 stages / 1,583 substantive MC variants + 39 smoke trials.'
Write-Host 'Checkpoint 72 contract validation passed.'
