[CmdletBinding()]
param()

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
function Assert-True {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) { throw $Message }
}
function Read-Json {
    param([string]$RelativePath)
    Get-Content -LiteralPath (Join-Path $repositoryRoot $RelativePath) -Raw | ConvertFrom-Json
}
function Get-ExpectedCp75Penalty {
    param([string]$ProfileLabel, [string]$Family)
    switch ($ProfileLabel) {
        'kinetic-p20' { if ($Family -eq 'Kinetic') { return 20 } else { return 0 } }
        'kinetic-p25' { if ($Family -eq 'Kinetic') { return 25 } else { return 0 } }
        'energy-p20' { if ($Family -eq 'Energy') { return 20 } else { return 0 } }
        'energy-p25' { if ($Family -eq 'Energy') { return 25 } else { return 0 } }
        'both-p20' { return 20 }
        'both-p25' { return 25 }
        'kinetic-p20-energy-p25' { if ($Family -eq 'Kinetic') { return 20 } else { return 25 } }
        'kinetic-p25-energy-p20' { if ($Family -eq 'Kinetic') { return 25 } else { return 20 } }
        default { return 0 }
    }
}

Write-Host '       Validating native-dependency declarations...'
$guard = Join-Path $repositoryRoot 'tools\checkpoints\Test-NativeAcceptanceDependencies.ps1'
$normalRel = 'tools/calibration/checkpoints/checkpoint-75a.json'
$deepRel = 'tools/calibration/checkpoints/checkpoint-75a-deep-calibration.json'
$guardedPs = @(
    'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
    'tools/checkpoints/checkpoint-75a/apply_checkpoint_75a.ps1',
    'tools/checkpoints/checkpoint-75a/test_checkpoint_75a_contract.ps1',
    'tools/calibration/run_calibration_checkpoint.ps1'
)
$guardedDefs = @($normalRel, $deepRel)
& $guard -RepositoryRoot $repositoryRoot -PowerShellPaths $guardedPs -CheckpointDefinitionPaths $guardedDefs

Write-Host '       Validating Checkpoint 75a definitions and unchanged workload accounting...'
$normal = Read-Json $normalRel
$deep = Read-Json $deepRel
Assert-True ([string]$normal.checkpointId -eq '75a' -and [string]$deep.checkpointId -eq '75a') 'Checkpoint 75a definition ID mismatch.'
Assert-True ([string]$normal.manifestFile -eq 'CHECKPOINT_75A_SHA256SUMS.txt' -and [string]$deep.manifestFile -eq 'CHECKPOINT_75A_SHA256SUMS.txt') 'Checkpoint 75a manifest binding mismatch.'
Assert-True ([string]$normal.outputRoot -eq 'out/checkpoint-75a' -and [string]$deep.outputRoot -eq 'out/checkpoint-75a-deep-calibration') 'Checkpoint 75a output-root binding mismatch.'
Assert-True ((@($normal.nativeDependencyPrecheck.powerShellPaths) -join '|') -eq ($guardedPs -join '|')) 'Checkpoint 75a normal native-dependency PowerShell path binding mismatch.'
Assert-True ((@($deep.nativeDependencyPrecheck.powerShellPaths) -join '|') -eq ($guardedPs -join '|')) 'Checkpoint 75a deep native-dependency PowerShell path binding mismatch.'
Assert-True ((@($normal.nativeDependencyPrecheck.checkpointDefinitionPaths) -join '|') -eq ($guardedDefs -join '|')) 'Checkpoint 75a normal native-dependency definition binding mismatch.'
Assert-True ((@($deep.nativeDependencyPrecheck.checkpointDefinitionPaths) -join '|') -eq ($guardedDefs -join '|')) 'Checkpoint 75a deep native-dependency definition binding mismatch.'
Assert-True (@($normal.stages).Count -eq 11 -and @($deep.stages).Count -eq 30) 'Checkpoint 75a stage-count mismatch.'
Assert-True ([int]$normal.checkpointMetrics.stageCount -eq 11 -and [int]$normal.checkpointMetrics.monteCarloVariantCount -eq 40 -and [int]$normal.checkpointMetrics.trialsAtDefault -eq 400000 -and [int]$normal.checkpointMetrics.smokeVariantExecutions -eq 40 -and [int]$normal.checkpointMetrics.smokeTrialsAtDefault -eq 40 -and [int]$normal.checkpointMetrics.totalTrialExecutionsAtDefault -eq 400040) 'Checkpoint 75a normal workload mismatch.'
Assert-True ([int]$deep.checkpointMetrics.stageCount -eq 30 -and [int]$deep.checkpointMetrics.monteCarloVariantCount -eq 1584 -and [int]$deep.checkpointMetrics.trialsAtDefault -eq 15840000 -and [int]$deep.checkpointMetrics.smokeVariantExecutions -eq 40 -and [int]$deep.checkpointMetrics.smokeTrialsAtDefault -eq 40 -and [int]$deep.checkpointMetrics.totalTrialExecutionsAtDefault -eq 15840040) 'Checkpoint 75a Deep Calibration workload mismatch.'
Assert-True ([string]$normal.primaryStudy.id -eq 'tl1-itc17-applied-degraded-fire-family-candidates' -and [int]$normal.primaryStudy.variantCount -eq 40) 'Checkpoint 75a normal primary-study binding mismatch.'
Assert-True ([string]$deep.primaryStudy.id -eq 'tl1-itc17-applied-degraded-fire-family-candidates' -and [int]$deep.primaryStudy.variantCount -eq 40) 'Checkpoint 75a deep primary-study binding mismatch.'
$normalStageIds = @($normal.stages | ForEach-Object { [string]$_.id })
$expectedNormalStageIds = @(
    'deterministic',
    'tl1-phase-a',
    'tl1-phase-b',
    'tl1-installation-space-envelope',
    'tl1-sensor-ew-foundation',
    'tl1-applied-degraded-fire-preflight',
    'tl1-applied-degraded-fire-smoke',
    'tl1-applied-degraded-fire',
    'auxiliary-resource-endurance',
    'checkpoint-53-resource-semantics-lock',
    'runner-self-tests'
)
Assert-True (($normalStageIds -join '|') -eq ($expectedNormalStageIds -join '|')) 'Checkpoint 75a normal stage ordering mismatch.'
$normalSelfTests = @($normal.stages | Where-Object { [string]$_.id -eq 'runner-self-tests' })
$deepSelfTests = @($deep.stages | Where-Object { [string]$_.id -eq 'runner-self-tests' })
Assert-True ($normalSelfTests.Count -eq 1 -and [int]$normalSelfTests[0].metrics.selfTestCount -eq 47) 'Checkpoint 75a normal ScenarioRunner self-test count mismatch.'
Assert-True ($deepSelfTests.Count -eq 1 -and [int]$deepSelfTests[0].metrics.selfTestCount -eq 47) 'Checkpoint 75a deep ScenarioRunner self-test count mismatch.'
foreach ($definition in @($normal, $deep)) {
    foreach ($docPath in @($definition.documentation)) {
        Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot ([string]$docPath)) -PathType Leaf) "Checkpoint 75 definition references missing documentation/input '$docPath'."
    }
}

Write-Host '       Validating suite policy and accepted AI-doctrine controls...'
$policy = Read-Json 'docs/design/testing/checkpoint_75_validation_suite_policy_v0_1.json'
Assert-True ([int]$policy.checkpoint -eq 75 -and [string]$policy.acceptedBaseline -eq '74d' -and [string]$policy.suiteTier -eq 'must_always_run' -and -not [bool]$policy.blockingBalanceTargets) 'Checkpoint 75 suite-policy identity mismatch.'
Assert-True ([int]$policy.normal.stageCount -eq 11 -and [int]$policy.normal.monteCarloVariantCount -eq 40 -and [int]$policy.normal.substantiveTrials -eq 400000 -and [int]$policy.normal.smokeTrials -eq 40 -and [int]$policy.normal.totalTrialExecutions -eq 400040) 'Checkpoint 75 normal suite-policy workload mismatch.'
Assert-True ([int]$policy.deepCalibration.stageCount -eq 30 -and [int]$policy.deepCalibration.monteCarloVariantCount -eq 1584 -and [int]$policy.deepCalibration.substantiveTrials -eq 15840000 -and [int]$policy.deepCalibration.smokeTrials -eq 40 -and [int]$policy.deepCalibration.totalTrialExecutions -eq 15840040) 'Checkpoint 75 deep suite-policy workload mismatch.'
Assert-True ([string]$policy.aiDoctrineControls.registryVersion -eq '0.2' -and [string]$policy.aiDoctrineControls.defaultEwDoctrine -eq 'tl1-ew-preserve-combat-package-v1' -and -not [bool]$policy.aiDoctrineControls.cp73RerunRequired -and [bool]$policy.aiDoctrineControls.playerInformationParityRequired) 'Checkpoint 75 AI-doctrine policy mismatch.'
Assert-True ([string]$policy.studyControls.studyId -eq 'tl1-itc17-applied-degraded-fire-family-candidates' -and (@($policy.studyControls.appliedWeaponFamilies) -join '|') -eq 'Kinetic|Energy' -and (@($policy.studyControls.penaltiesPercentagePoints) -join '|') -eq '20|25' -and -not [bool]$policy.studyControls.degradedFireProductionAssignment -and -not [bool]$policy.studyControls.missilesUseDegradedDirectFire -and [bool]$policy.studyControls.candidatePromotionRequiresHumanReview) 'Checkpoint 75 applied degraded-fire policy mismatch.'
Assert-True ([bool]$policy.missileTerminalControls.terminalAttackRequiresFirmSolution -and [bool]$policy.missileTerminalControls.baselineCommandGuidedRequiresLiveLauncherFirmDatalink -and -not [bool]$policy.missileTerminalControls.baselineCommandGuidedMaySubstitutePeerGuidance -and [bool]$policy.missileTerminalControls.peerTerminalGuidanceRequiresExplicitProfileCapability -and [bool]$policy.missileTerminalControls.sensorPlusSeekerApproximateRefinementRequiresMissileLocalTrack -and -not [bool]$policy.missileTerminalControls.remoteApproximateAloneMayRefineSensorPlusSeekerToFirm -and [bool]$policy.missileTerminalControls.seekerOnlyCoLocatedAcquisitionFromRemoteCueRemainsDistinct -and [bool]$policy.missileTerminalControls.coLocationAloneIsNotImpact) 'Checkpoint 75 missile terminal policy mismatch.'
Assert-True ([bool]$policy.productionControls.degradedFireFoundationImplementedByCheckpoint74 -and [bool]$policy.productionControls.appliedDegradedFireStudyImplementedByCheckpoint75 -and -not [bool]$policy.productionControls.productionWeaponDegradedFireEnabledByCheckpoint75 -and -not [bool]$policy.productionControls.missileDegradedFireEnabledByCheckpoint75 -and -not [bool]$policy.productionControls.movementPhaseFireImplementedByCheckpoint75) 'Checkpoint 75 production/deferred-feature policy mismatch.'

$registry = Read-Json 'docs/archive/ai/pre-cp165-active/ai_doctrine_registry_v0_2.json'
Assert-True ([string]$registry.registryVersion -eq '0.2' -and [string]$registry.defaults.'electronic-warfare' -eq 'tl1-ew-preserve-combat-package-v1') 'Checkpoint 75 registry default mismatch.'
$doctrines = @($registry.doctrines)
$defaultDoctrine = @($doctrines | Where-Object { [string]$_.id -eq 'tl1-ew-preserve-combat-package-v1' })
$reactiveDoctrine = @($doctrines | Where-Object { [string]$_.id -eq 'tl1-ew-reactive-eccm-v1' })
$rejectedDoctrine = @($doctrines | Where-Object { [string]$_.id -eq 'tl1-ew-preserve-offense-v1' })
Assert-True ($defaultDoctrine.Count -eq 1 -and [string]$defaultDoctrine[0].status -eq 'accepted' -and [string]$defaultDoctrine[0].acceptedCheckpoint -eq '73') 'Checkpoint 75 must preserve the accepted CP73 ECM default.'
Assert-True ($reactiveDoctrine.Count -eq 1 -and [string]$reactiveDoctrine[0].status -eq 'accepted') 'Checkpoint 75 must preserve accepted reactive ECCM.'
Assert-True ($rejectedDoctrine.Count -eq 1 -and [string]$rejectedDoctrine[0].status -eq 'rejected') 'Checkpoint 75 must preserve rejected preserve-offense evidence.'
Assert-True (@($doctrines | Where-Object { [bool]$_.informationPolicy.usesHiddenEnemyRatings }).Count -eq 0) 'Checkpoint 75 AI doctrine must preserve player information parity.'
$cp73Evidence = @($registry.evidence | Where-Object { [string]$_.checkpoint -eq '73' })
Assert-True ($cp73Evidence.Count -eq 3 -and @($cp73Evidence | Where-Object { [string]$_.resultSha256 -ne '667b553760b16ec63a67db52748a98bcb6daf7640bce21b3b7e4fc7d88da8613' }).Count -eq 0) 'Checkpoint 75 CP73 doctrine evidence provenance mismatch.'

Write-Host '       Validating frozen CP74 degraded-fire foundation...'
$frozenHashes = @{
    'src/StarCluster.Core/Combat/DirectFire/DirectFireWeaponProfile.cs' = '489424003edc74f046c799dcb7cb04653b2b083f68a8f0efe79ecfe47d4a0ea0'
    'src/StarCluster.Core/Combat/DirectFire/DirectFireTargetEligibility.cs' = 'b4bee53b3ff506dbf94fd3e5bc0eef3110be336b73c7b4a46dfc1841497eadb7'
    'src/StarCluster.Core/Combat/DirectFire/DirectFireTargetEligibilityResult.cs' = '96833294e88e8c55fe92afd7971a311a0834426df0dac5b08184e41fd67803aa'
    'src/StarCluster.Core/Combat/Tracking/DirectFireTrackEligibility.cs' = '8fbf1a553ccf4a6460b92d532e0e701af062332281fd259558587a84e66349ed'
    'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatDocuments.cs' = '7984535b5fc2b19cd76f253514b6b04cf522a8b47f55f86aac5cd4bdaf6c133c'
    'src/StarCluster.ScenarioRunner/Scenarios/TL1Calibration/tl1-itc16-approximate-track-degraded-fire.json' = '30ee161f598bbe4ced7d9ae197564ac941247fd0b86d08964f52e8dafcd68840'
    'docs/design/player_technology/tl1_integrated_tactical_combat_schema_v0_18.json' = 'd97943ea093e70b0cbd0c16a8176cbf2bb09c509b96cbd2c301c7504b6bd5add'
    'docs/archive/ai/pre-cp165-active/ai_doctrine_registry_v0_2.json' = 'c4a54db2fe84f2487efdb4998f8d17de0a029aaaaf71e13d10f493a90f69068a'
    'tests/StarCluster.Tests/Combat/DirectFire/DirectFireTargetEligibilityTests.cs' = 'eead08a6ddd3baa31a2b32f4c83498556711cd2ccc8178bc72f39f903ac13423'
    'src/StarCluster.ScenarioRunner/ScenarioRunnerSelfTests.cs' = '0ebea63b61c22aa474cdfb87715fa28d56c45107df5491748333c1d68388b843'
}
foreach ($entry in $frozenHashes.GetEnumerator()) {
    $actualHash = (Get-FileHash -LiteralPath (Join-Path $repositoryRoot $entry.Key) -Algorithm SHA256).Hash.ToLowerInvariant()
    Assert-True ($actualHash -eq [string]$entry.Value) "Checkpoint 75 unintentionally changed frozen CP74 degraded-fire/AI authority: $($entry.Key)."
}
$schema = Read-Json 'docs/design/player_technology/tl1_integrated_tactical_combat_schema_v0_18.json'
Assert-True ([string]$schema.'$id' -eq 'star-cluster-tl1-integrated-tactical-combat-schema-v0-18' -and $null -ne $schema.'$defs'.variant.properties.sideAAllowsApproximateDirectFire -and $null -ne $schema.'$defs'.variant.properties.sideAApproximateDirectFireAccuracyPenalty -and $null -ne $schema.'$defs'.variant.properties.sideBAllowsApproximateDirectFire -and $null -ne $schema.'$defs'.variant.properties.sideBApproximateDirectFireAccuracyPenalty) 'Checkpoint 75 integrated schema degraded-fire fields missing.'

Write-Host '       Validating the 40-variant applied degraded-fire study independently...'
$study = Read-Json 'src/StarCluster.ScenarioRunner/Scenarios/TL1Calibration/tl1-itc17-applied-degraded-fire-family-candidates.json'
Assert-True ([string]$study.id -eq 'tl1-itc17-applied-degraded-fire-family-candidates' -and [int]$study.trialsPerVariant -eq 10000 -and [int64]$study.masterSeed -eq 750100 -and @($study.variants).Count -eq 40) 'Checkpoint 75 applied-study identity/workload mismatch.'
$variants = @($study.variants)
Assert-True (@($variants | Group-Object id | Where-Object { $_.Count -ne 1 }).Count -eq 0) 'Checkpoint 75 applied-study variant IDs must be unique.'
$expectedLabels = @(
    'firm-reference',
    'approx-firm-only',
    'kinetic-p20',
    'kinetic-p25',
    'energy-p20',
    'energy-p25',
    'both-p20',
    'both-p25',
    'kinetic-p20-energy-p25',
    'kinetic-p25-energy-p20'
)
$contexts = @{
    'c75-kve-r2' = @('Kinetic', 'Energy', 2, 'HoldRange2')
    'c75-kve-r3' = @('Kinetic', 'Energy', 3, 'HoldRange3')
    'c75-evk-r2' = @('Energy', 'Kinetic', 2, 'HoldRange2')
    'c75-evk-r3' = @('Energy', 'Kinetic', 3, 'HoldRange3')
}
Assert-True (@($variants | Group-Object comparisonGroup).Count -eq 4) 'Checkpoint 75 must expose exactly four comparison contexts.'
foreach ($contextName in $contexts.Keys) {
    $context = @($variants | Where-Object { [string]$_.comparisonGroup -eq $contextName })
    $expected = $contexts[$contextName]
    Assert-True ($context.Count -eq 10) "Checkpoint 75 context '$contextName' must contain ten variants."
    Assert-True (@($context | Where-Object { [string]$_.sideAFamily -ne [string]$expected[0] -or [string]$_.sideBFamily -ne [string]$expected[1] -or [int]$_.initialRangeHexes -ne [int]$expected[2] -or [string]$_.movementMode -ne [string]$expected[3] }).Count -eq 0) "Checkpoint 75 context '$contextName' family/range/movement fixture mismatch."
    foreach ($label in $expectedLabels) {
        Assert-True (@($context | Where-Object { [string]$_.profileLabel -eq $label }).Count -eq 1) "Checkpoint 75 context '$contextName' must contain exactly one '$label' variant."
    }
}
Assert-True (@($variants | Where-Object { [string]$_.sideAFamily -eq 'Missile' -or [string]$_.sideBFamily -eq 'Missile' }).Count -eq 0) 'Checkpoint 75 degraded-fire study must exclude missiles.'
Assert-True (@($variants | Where-Object { ($_.PSObject.Properties.Name -contains 'sideASecondaryFamily' -and $null -ne $_.sideASecondaryFamily) -or ($_.PSObject.Properties.Name -contains 'sideBSecondaryFamily' -and $null -ne $_.sideBSecondaryFamily) }).Count -eq 0) 'Checkpoint 75 degraded-fire study must exclude secondary weapon families.'
foreach ($variant in $variants) {
    Assert-True ([string]$variant.sensorEwProfileId -eq 'balanced-0' -and [string]$variant.sideATrackPolicy -eq 'AcquisitionFirstAutoActive' -and [string]$variant.sideBTrackPolicy -eq 'AcquisitionFirstAutoActive' -and [int]$variant.sideANetEwRangePenalty -eq 0 -and [int]$variant.sideBNetEwRangePenalty -eq 0 -and [string]$variant.sideASensorOverloadPolicy -eq 'None' -and [string]$variant.sideBSensorOverloadPolicy -eq 'None' -and [string]$variant.sideAStlOverloadPolicy -eq 'None' -and [string]$variant.sideBStlOverloadPolicy -eq 'None') "Checkpoint 75 variant '$($variant.id)' drifted from the controlled Balanced-0/no-overload fixture."
    if ([string]$variant.profileLabel -eq 'firm-reference') {
        Assert-True ([string]$variant.sideAEcmPolicy -eq 'None' -and [string]$variant.sideBEcmPolicy -eq 'None' -and [string]$variant.sideAEccmPolicy -eq 'None' -and [string]$variant.sideBEccmPolicy -eq 'None' -and -not [bool]$variant.sideAAllowsApproximateDirectFire -and -not [bool]$variant.sideBAllowsApproximateDirectFire -and [int]$variant.sideAApproximateDirectFireAccuracyPenalty -eq 0 -and [int]$variant.sideBApproximateDirectFireAccuracyPenalty -eq 0) "Checkpoint 75 Firm reference '$($variant.id)' fixture mismatch."
        continue
    }
    Assert-True ([string]$variant.sideAEcmPolicy -eq 'Normal' -and [string]$variant.sideBEcmPolicy -eq 'Normal' -and [string]$variant.sideAEccmPolicy -eq 'None' -and [string]$variant.sideBEccmPolicy -eq 'None') "Checkpoint 75 Approximate-track variant '$($variant.id)' must use bilateral ECM with no ECCM."
    if ([string]$variant.profileLabel -eq 'approx-firm-only') {
        Assert-True (-not [bool]$variant.sideAAllowsApproximateDirectFire -and -not [bool]$variant.sideBAllowsApproximateDirectFire -and [int]$variant.sideAApproximateDirectFireAccuracyPenalty -eq 0 -and [int]$variant.sideBApproximateDirectFireAccuracyPenalty -eq 0) "Checkpoint 75 Firm-only Approximate control '$($variant.id)' must keep degraded fire disabled."
        continue
    }
    $expectedA = Get-ExpectedCp75Penalty ([string]$variant.profileLabel) ([string]$variant.sideAFamily)
    $expectedB = Get-ExpectedCp75Penalty ([string]$variant.profileLabel) ([string]$variant.sideBFamily)
    Assert-True ($expectedA -in @(0,20,25) -and $expectedB -in @(0,20,25) -and ($expectedA -gt 0 -or $expectedB -gt 0)) "Checkpoint 75 applied variant '$($variant.id)' has an unrecognized family package."
    Assert-True ([int]$variant.sideAApproximateDirectFireAccuracyPenalty -eq $expectedA -and [int]$variant.sideBApproximateDirectFireAccuracyPenalty -eq $expectedB -and [bool]$variant.sideAAllowsApproximateDirectFire -eq ($expectedA -gt 0) -and [bool]$variant.sideBAllowsApproximateDirectFire -eq ($expectedB -gt 0)) "Checkpoint 75 applied variant '$($variant.id)' family/penalty mapping mismatch."
}

Write-Host '       Auditing CP75 cross-study ScenarioRunner integration...'
$runnerPath = Join-Path $repositoryRoot 'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs'
$runner = Get-Content -LiteralPath $runnerPath -Raw
Assert-True ($runner.Contains('Tl1AppliedDegradedFireFamilyCandidateStudyId') -and $runner.Contains('tl1-itc17-applied-degraded-fire-family-candidates') -and $runner.Contains('RequiredTl1AppliedDegradedFireFamilyCandidateVariantCount = 40')) 'Checkpoint 75 ScenarioRunner study identity/count registration missing.'
Assert-True (([regex]::Matches($runner, 'Tl1AppliedDegradedFireFamilyCandidateStudyId')).Count -ge 12) 'Checkpoint 75 ScenarioRunner registration is incomplete across shared/global study classifications.'
Assert-True ($runner.Contains('ValidateTl1AppliedDegradedFireFamilyCandidateCoverage(') -and $runner.Contains('ValidateCheckpoint75FamilyPenalty(')) 'Checkpoint 75 pre-run actual-consumer validator missing.'
Assert-True ($runner.Contains('WriteTl1AppliedDegradedFireFamilyCandidateReview(') -and $runner.Contains('degraded-fire-applied-review.csv') -and $runner.Contains('AppliedDegradedFireProfileOrder(')) 'Checkpoint 75 applied-study report writer/output routing missing.'
$familyHelperStart = $runner.IndexOf('private static WeaponFamily[] RequiredWeaponFamiliesForStudy')
$familyHelperEnd = $runner.IndexOf('private static IReadOnlyList<Tl1IntegratedTacticalCombatGate> BuildGates', $familyHelperStart)
Assert-True ($familyHelperStart -ge 0 -and $familyHelperEnd -gt $familyHelperStart) 'Checkpoint 75 could not isolate the shared weapon-family helper.'
$familyHelper = $runner.Substring($familyHelperStart, $familyHelperEnd - $familyHelperStart)
Assert-True ($familyHelper.Contains('Tl1ApproximateTrackDegradedFireStudyId') -and $familyHelper.Contains('Tl1AppliedDegradedFireFamilyCandidateStudyId') -and $familyHelper.Contains('WeaponFamily.Kinetic, WeaponFamily.Energy') -and $familyHelper.Contains('WeaponFamily.Missile')) 'Checkpoint 75 must share Kinetic/Energy-only family coverage with CP74 while preserving Missile coverage for unrelated integrated studies.'
$buildGatesStart = $runner.IndexOf('private static IReadOnlyList<Tl1IntegratedTacticalCombatGate> BuildGates')
Assert-True ($buildGatesStart -ge 0) 'Checkpoint 75a could not locate BuildGates.'
$gateStart = $runner.IndexOf('if (study.Id == Tl1AppliedDegradedFireFamilyCandidateStudyId)', $buildGatesStart)
$gateEnd = $runner.IndexOf('if (IsCheckpoint57Study', $gateStart)
Assert-True ($gateStart -gt $buildGatesStart -and $gateEnd -gt $gateStart) 'Checkpoint 75a could not isolate the CP75 release-gate block inside BuildGates.'
$gateBlock = $runner.Substring($gateStart, $gateEnd - $gateStart)
$requiredGates = @(
    'tl1-c75-variant-coverage',
    'tl1-c75-firm-reference-clean',
    'tl1-c75-firm-only-approx-blocked',
    'tl1-c75-family-package-wiring',
    'tl1-c75-no-missile-degraded-fire',
    'tl1-c75-outcomes-review-only'
)
foreach ($gateName in $requiredGates) {
    $firstGateOccurrence = $gateBlock.IndexOf($gateName, [System.StringComparison]::Ordinal)
    $lastGateOccurrence = $gateBlock.LastIndexOf($gateName, [System.StringComparison]::Ordinal)
    Assert-True ($firstGateOccurrence -ge 0 -and $firstGateOccurrence -eq $lastGateOccurrence) "Checkpoint 75a release-gate block must contain exactly one '$gateName' gate."
}
Assert-True ($gateBlock.Contains('Tl1ApproximateTrackFirmReferenceIsClean(') -and $gateBlock.Contains('new[] { 0, 20, 25 }') -and $gateBlock.Contains('MeanDirectShotsFired') -and $gateBlock.Contains('MeanPreventedTrackUnavailable')) 'Checkpoint 75a CP75 gate block telemetry/wiring mismatch.'
Assert-True ($gateBlock.Contains('Family assignment, -20 versus -25 preference') -and $gateBlock.Contains('missile and torpedo terminal requirements are independent and remain Firm-gated')) 'Checkpoint 75a must preserve CP75 outcome-review and missile-separation gate semantics.'

Write-Host '       Freezing accepted Checkpoint 75 mechanics, study inputs, tests, and Concept...'
$cp75FrozenHashes = @{
    'src/StarCluster.Core/Combat/Missiles/MissileTerminalProfile.cs' = '96e01f92d92c77f6910dce68418eb2e0284e1cd7a03bb4f877ed2a3512d4f488'
    'src/StarCluster.Core/Combat/Missiles/MissileTerminalResolutionService.cs' = '6321c3a2e38ae3e2c4d6bfcd5cc440bd953d0ca2e4793d6b204f48fb8078dab6'
    'tests/StarCluster.Tests/Combat/Missiles/MissileTerminalResolutionTests.cs' = '55f5e05a724a4bfdaa9c85244679ffe7d3c750e921efaebf10d8db833ed6b84a'
    'tests/StarCluster.Tests/Combat/DirectFire/DirectFireTargetEligibilityTests.cs' = 'eead08a6ddd3baa31a2b32f4c83498556711cd2ccc8178bc72f39f903ac13423'
    'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs' = '95092d870ec00bc13f5ae0c7929eb1df03eab348159f33ffc33aef452bd54ddc'
    'src/StarCluster.ScenarioRunner/Scenarios/TL1Calibration/tl1-itc17-applied-degraded-fire-family-candidates.json' = '447c3e9605760076663d7a0adabecf105af3b313bb9fbfcd9fca1bb76258dfeb'
    'docs/design/player_technology/TL1_Applied_Degraded_Fire_Family_Candidate_Study_v0_1.md' = 'cffad1fa952680983e81a9200ff15ba8c6195a8475c6ce560ba8cfe7683cada6'
    'docs/design/player_technology/tl1_integrated_tactical_combat_schema_v0_18.json' = 'd97943ea093e70b0cbd0c16a8176cbf2bb09c509b96cbd2c301c7504b6bd5add'
    'docs/design/Missile_Guidance_Datalink_Sensor_And_Seeker_Architecture.md' = '12ed128b92516c86f91bbf0dd18a2209470fcfa24bd36ce2328b32aaaaf26305'
    'docs/design/testing/checkpoint_75_validation_suite_policy_v0_1.json' = 'cb2755a4cee7897c9c7515cd16799f71619afe3e1842df01d815dd2e593c4299'
    'docs/archive/ai/pre-cp165-active/ai_doctrine_registry_v0_2.json' = 'c4a54db2fe84f2487efdb4998f8d17de0a029aaaaf71e13d10f493a90f69068a'
    'docs/Star_Cluster_Game_Concept_v0.6n.docx' = '9e60cc5e8d7998d341dd84fdf393828226e2bcd83baa1f4723c8ed56c754b665'
}
foreach ($entry in $cp75FrozenHashes.GetEnumerator()) {
    $actual = (Get-FileHash -LiteralPath (Join-Path $repositoryRoot $entry.Key) -Algorithm SHA256).Hash.ToLowerInvariant()
    Assert-True ($actual -eq [string]$entry.Value) "Checkpoint 75a contract-only hotfix changed frozen CP75 authority/input: $($entry.Key)."
}

Write-Host '       Validating missile terminal-guidance capability gates and regressions...'
$terminalProfile = Get-Content -LiteralPath (Join-Path $repositoryRoot 'src/StarCluster.Core/Combat/Missiles/MissileTerminalProfile.cs') -Raw
$terminalResolver = Get-Content -LiteralPath (Join-Path $repositoryRoot 'src/StarCluster.Core/Combat/Missiles/MissileTerminalResolutionService.cs') -Raw
$terminalTests = Get-Content -LiteralPath (Join-Path $repositoryRoot 'tests/StarCluster.Tests/Combat/Missiles/MissileTerminalResolutionTests.cs') -Raw
Assert-True ($terminalProfile.Contains('bool allowsPeerTerminalGuidance = false') -and $terminalProfile.Contains('AllowsPeerTerminalGuidance = allowsPeerTerminalGuidance;') -and $terminalProfile.Contains('public bool AllowsPeerTerminalGuidance { get; }')) 'Checkpoint 75 missile profile must capability-gate peer terminal guidance and default it off.'
Assert-True ($terminalResolver.Contains('reportSource == MissileGuidanceReportSource.FreshDatalink') -and $terminalResolver.Contains('datalinkState == MissileDatalinkState.Live') -and $terminalResolver.Contains('reportSource == MissileGuidanceReportSource.PeerGuidance') -and $terminalResolver.Contains('salvo.TerminalProfile.AllowsPeerTerminalGuidance')) 'Checkpoint 75 command/peer Firm terminal-source gating missing.'
Assert-True ($terminalResolver.Contains('bool seekerOnly = seekerInstalled && !onboardNavigationSensorInstalled;') -and $terminalResolver.Contains('salvo.LocalSensorTrack?.CreateGuidanceSnapshot()') -and $terminalResolver.Contains('seekerCueSource = MissileGuidanceReportSource.LocalSensor;') -and $terminalResolver.Contains('requires at least an Approximate missile-local navigation track')) 'Checkpoint 75 sensor-plus-seeker local-track refinement guardrail missing.'
foreach ($testName in @(
    'CommandGuidedMissileAcceptsLiveFirmDatalink',
    'PeerGuidanceCannotAuthorizeBaselineCommandGuidedTerminalAttack',
    'PeerGuidanceCanAuthorizeTerminalAttackWhenProfileExplicitlyAllowsIt',
    'SeekerOnlyMissileCanUseRemoteApproximateCueForCoLocatedAcquisition',
    'SensorPlusSeekerRejectsRemoteApproximateCueWithoutLocalNavigationTrack',
    'SensorPlusSeekerCanRefineLocalApproximateNavigationTrackIntoFirm')) {
    Assert-True ($terminalTests.Contains($testName)) "Checkpoint 75 missile regression '$testName' missing."
}
Assert-True (-not $terminalTests.Contains('PeerGuidanceMaySupplyFirmTerminalSolution')) 'Checkpoint 75 must not retain the obsolete unconditional peer-guidance terminal test.'
$directFireTests = Get-Content -LiteralPath (Join-Path $repositoryRoot 'tests/StarCluster.Tests/Combat/DirectFire/DirectFireTargetEligibilityTests.cs') -Raw
Assert-True ($directFireTests.Contains('MissileInterceptionRemainsFirmOnlyEvenForTraitWeapon')) 'Checkpoint 75 must retain the deterministic proof that degraded direct-fire permission does not relax missile interception Firm gating.'

Write-Host '       Validating active documentation and clean repository presentation...'
$concepts = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs') -File -Filter 'Star_Cluster_Game_Concept_v*.docx')
Assert-True ($concepts.Count -eq 1 -and $concepts[0].Name -eq 'Star_Cluster_Game_Concept_v0.6n.docx') 'Checkpoint 75a must expose exactly one active Concept v0.6n.'
Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot 'docs/archive/Star_Cluster_Game_Concept_v0.6m.docx') -PathType Leaf) 'Checkpoint 75a must retain archived Concept v0.6m.'
$conceptHash = (Get-FileHash -LiteralPath (Join-Path $repositoryRoot 'docs/Star_Cluster_Game_Concept_v0.6n.docx') -Algorithm SHA256).Hash.ToLowerInvariant()
Assert-True ($conceptHash -eq '9e60cc5e8d7998d341dd84fdf393828226e2bcd83baa1f4723c8ed56c754b665') 'Checkpoint 75a active Concept v0.6n content hash mismatch.'
Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot 'docs/validation/archive/Checkpoint_74d_Degraded_Fire_Firm_Reference_Gate_Semantics_Hotfix.md') -PathType Leaf) 'Checkpoint 75a must retain the archived accepted CP74d validation runbook.'
Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot 'docs/validation/archive/Checkpoint_75_Applied_Degraded_Fire_Family_Candidates_And_Missile_Terminal_Guardrails.md') -PathType Leaf) 'Checkpoint 75a must archive the original CP75 validation runbook.'
$validationFiles = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs\validation') -File -Filter 'Checkpoint_*.md')
Assert-True ($validationFiles.Count -eq 1 -and $validationFiles[0].Name -eq 'Checkpoint_75a_Release_Gate_Block_Isolation_Hotfix.md') 'Checkpoint 75a must expose exactly one active validation runbook.'
$rootTxt = @(Get-ChildItem -LiteralPath $repositoryRoot -File -Filter '*.txt')
Assert-True ($rootTxt.Count -eq 1 -and $rootTxt[0].Name -eq 'CHECKPOINT_75A_SHA256SUMS.txt') 'Repository root must contain only CHECKPOINT_75A_SHA256SUMS.txt as .txt.'
$rootReadme = Get-Content -LiteralPath (Join-Path $repositoryRoot 'README.md') -Raw
$docsReadme = Get-Content -LiteralPath (Join-Path $repositoryRoot 'docs/README.md') -Raw
$todo = Get-Content -LiteralPath (Join-Path $repositoryRoot 'docs/Prototype_TODO.md') -Raw
Assert-True ($rootReadme.Contains('Checkpoint 75a') -and $rootReadme.Contains('Concept v0.6n') -and $rootReadme.Contains('checkpoint-75a/apply_checkpoint_75a.ps1')) 'Checkpoint 75a root README is stale.'
Assert-True ($docsReadme.Contains('Checkpoint 75a') -and $docsReadme.Contains('Star_Cluster_Game_Concept_v0.6n.docx') -and $docsReadme.Contains('Checkpoint_75a_Release_Gate_Block_Isolation_Hotfix.md')) 'Checkpoint 75a documentation README is stale.'
Assert-True ($todo.Contains('Checkpoint 75a') -and $todo.Contains('400,000') -and $todo.Contains('degraded-fire-applied-review.csv')) 'Checkpoint 75a prototype TODO is stale.'

Write-Host '       Checkpoint 75a hotfix scope: release-gate block isolation in the native contract audit only.'
Write-Host '       CP75 applied study, missile guardrails, ScenarioRunner behavior, tests, doctrine, and Concept v0.6n are frozen.'
Write-Host '       The corrected audit is anchored inside BuildGates and verifies all six CP75 study-specific gates exactly once.'
Write-Host 'Checkpoint 75a release-gate block isolation hotfix validation passed.'
