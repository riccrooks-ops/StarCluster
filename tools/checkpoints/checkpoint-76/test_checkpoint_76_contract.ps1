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
function Get-OptionalPropertyValue {
    param($Object, [string]$Name)
    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) { return $null }
    return $property.Value
}

Write-Host '       Validating native-dependency declarations...'
$guard = Join-Path $repositoryRoot 'tools\checkpoints\Test-NativeAcceptanceDependencies.ps1'
$normalRel = 'tools/calibration/checkpoints/checkpoint-76.json'
$deepRel = 'tools/calibration/checkpoints/checkpoint-76-deep-calibration.json'
$guardedPs = @(
    'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
    'tools/checkpoints/checkpoint-76/apply_checkpoint_76.ps1',
    'tools/checkpoints/checkpoint-76/test_checkpoint_76_contract.ps1',
    'tools/calibration/run_calibration_checkpoint.ps1'
)
$guardedDefs = @($normalRel, $deepRel)
& $guard -RepositoryRoot $repositoryRoot -PowerShellPaths $guardedPs -CheckpointDefinitionPaths $guardedDefs

Write-Host '       Validating Checkpoint 76 definitions and workload accounting...'
$normal = Read-Json $normalRel
$deep = Read-Json $deepRel
Assert-True ([string]$normal.checkpointId -eq '76' -and [string]$deep.checkpointId -eq '76') 'Checkpoint 76 definition ID mismatch.'
Assert-True ([string]$normal.manifestFile -eq 'CHECKPOINT_76_SHA256SUMS.txt' -and [string]$deep.manifestFile -eq 'CHECKPOINT_76_SHA256SUMS.txt') 'Checkpoint 76 manifest binding mismatch.'
Assert-True ([string]$normal.outputRoot -eq 'out/checkpoint-76' -and [string]$deep.outputRoot -eq 'out/checkpoint-76-deep-calibration') 'Checkpoint 76 output-root binding mismatch.'
Assert-True ((@($normal.nativeDependencyPrecheck.powerShellPaths) -join '|') -eq ($guardedPs -join '|')) 'Checkpoint 76 normal native-dependency PowerShell path binding mismatch.'
Assert-True ((@($deep.nativeDependencyPrecheck.powerShellPaths) -join '|') -eq ($guardedPs -join '|')) 'Checkpoint 76 deep native-dependency PowerShell path binding mismatch.'
Assert-True ((@($normal.nativeDependencyPrecheck.checkpointDefinitionPaths) -join '|') -eq ($guardedDefs -join '|')) 'Checkpoint 76 normal native-dependency definition binding mismatch.'
Assert-True ((@($deep.nativeDependencyPrecheck.checkpointDefinitionPaths) -join '|') -eq ($guardedDefs -join '|')) 'Checkpoint 76 deep native-dependency definition binding mismatch.'
Assert-True (@($normal.stages).Count -eq 11 -and @($deep.stages).Count -eq 30) 'Checkpoint 76 stage-count mismatch.'
Assert-True ([int]$normal.checkpointMetrics.stageCount -eq 11 -and [int]$normal.checkpointMetrics.monteCarloVariantCount -eq 54 -and [int]$normal.checkpointMetrics.trialsAtDefault -eq 540000 -and [int]$normal.checkpointMetrics.smokeVariantExecutions -eq 54 -and [int]$normal.checkpointMetrics.smokeTrialsAtDefault -eq 54 -and [int]$normal.checkpointMetrics.totalTrialExecutionsAtDefault -eq 540054) 'Checkpoint 76 normal workload mismatch.'
Assert-True ([int]$deep.checkpointMetrics.stageCount -eq 30 -and [int]$deep.checkpointMetrics.monteCarloVariantCount -eq 1598 -and [int]$deep.checkpointMetrics.trialsAtDefault -eq 15980000 -and [int]$deep.checkpointMetrics.smokeVariantExecutions -eq 54 -and [int]$deep.checkpointMetrics.smokeTrialsAtDefault -eq 54 -and [int]$deep.checkpointMetrics.totalTrialExecutionsAtDefault -eq 15980054) 'Checkpoint 76 Deep Calibration workload mismatch.'
Assert-True ([string]$normal.primaryStudy.id -eq 'tl1-itc18-degraded-fire-eccm-value-counterplay' -and [int]$normal.primaryStudy.variantCount -eq 54) 'Checkpoint 76 normal primary-study binding mismatch.'
Assert-True ([string]$deep.primaryStudy.id -eq 'tl1-itc18-degraded-fire-eccm-value-counterplay' -and [int]$deep.primaryStudy.variantCount -eq 54) 'Checkpoint 76 deep primary-study binding mismatch.'
$normalStageIds = @($normal.stages | ForEach-Object { [string]$_.id })
$expectedNormalStageIds = @(
    'deterministic',
    'tl1-phase-a',
    'tl1-phase-b',
    'tl1-installation-space-envelope',
    'tl1-sensor-ew-foundation',
    'tl1-degraded-fire-eccm-value-preflight',
    'tl1-degraded-fire-eccm-value-smoke',
    'tl1-degraded-fire-eccm-value',
    'auxiliary-resource-endurance',
    'checkpoint-53-resource-semantics-lock',
    'runner-self-tests'
)
Assert-True (($normalStageIds -join '|') -eq ($expectedNormalStageIds -join '|')) 'Checkpoint 76 normal stage ordering mismatch.'
$normalSelfTests = @($normal.stages | Where-Object { [string]$_.id -eq 'runner-self-tests' })
$deepSelfTests = @($deep.stages | Where-Object { [string]$_.id -eq 'runner-self-tests' })
Assert-True ($normalSelfTests.Count -eq 1 -and [int]$normalSelfTests[0].metrics.selfTestCount -eq 47) 'Checkpoint 76 normal ScenarioRunner self-test count mismatch.'
Assert-True ($deepSelfTests.Count -eq 1 -and [int]$deepSelfTests[0].metrics.selfTestCount -eq 47) 'Checkpoint 76 deep ScenarioRunner self-test count mismatch.'
foreach ($definition in @($normal, $deep)) {
    foreach ($docPath in @($definition.documentation)) {
        Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot ([string]$docPath)) -PathType Leaf) "Checkpoint 76 definition references missing documentation/input '$docPath'."
    }
}

Write-Host '       Validating suite policy and accepted doctrine dependencies...'
$policy = Read-Json 'docs/design/testing/checkpoint_76_validation_suite_policy_v0_1.json'
Assert-True ([int]$policy.checkpoint -eq 76 -and [string]$policy.acceptedBaseline -eq '75a' -and [string]$policy.suiteTier -eq 'must_always_run' -and -not [bool]$policy.blockingBalanceTargets) 'Checkpoint 76 suite-policy identity mismatch.'
Assert-True ([int]$policy.normal.stageCount -eq 11 -and [int]$policy.normal.monteCarloVariantCount -eq 54 -and [int]$policy.normal.substantiveTrials -eq 540000 -and [int]$policy.normal.smokeTrials -eq 54 -and [int]$policy.normal.totalTrialExecutions -eq 540054) 'Checkpoint 76 normal suite-policy workload mismatch.'
Assert-True ([int]$policy.deepCalibration.stageCount -eq 30 -and [int]$policy.deepCalibration.monteCarloVariantCount -eq 1598 -and [int]$policy.deepCalibration.substantiveTrials -eq 15980000 -and [int]$policy.deepCalibration.smokeTrials -eq 54 -and [int]$policy.deepCalibration.totalTrialExecutions -eq 15980054) 'Checkpoint 76 deep suite-policy workload mismatch.'
Assert-True ([string]$policy.aiDoctrineControls.registryVersion -eq '0.2' -and [string]$policy.aiDoctrineControls.hostileEcmDoctrine -eq 'tl1-ew-preserve-combat-package-v1' -and [string]$policy.aiDoctrineControls.reactiveEccmDoctrine -eq 'tl1-ew-reactive-eccm-v1' -and [bool]$policy.aiDoctrineControls.aggressiveEccmIsDiagnosticControl -and -not [bool]$policy.aiDoctrineControls.cp73RerunRequired -and [bool]$policy.aiDoctrineControls.playerInformationParityRequired) 'Checkpoint 76 AI-doctrine policy mismatch.'
Assert-True ([string]$policy.studyControls.studyId -eq 'tl1-itc18-degraded-fire-eccm-value-counterplay' -and [bool]$policy.studyControls.degradedFireCapabilityIsWeaponSpecific -and [bool]$policy.studyControls.degradedFireMayBeUpgradePathCapability -and [bool]$policy.studyControls.eccmValueGuardrailRequired -and (@($policy.studyControls.penaltiesPercentagePoints) -join '|') -eq '20|25' -and (@($policy.studyControls.directFireFamilies) -join '|') -eq 'Kinetic|Energy' -and [string]$policy.studyControls.opponentFamily -eq 'Missile' -and -not [bool]$policy.studyControls.degradedFireProductionAssignment -and -not [bool]$policy.studyControls.missilesUseDegradedDirectFire -and [bool]$policy.studyControls.futureMissileApproximateTerminalCapabilityRequiresSeparateProfile -and -not [bool]$policy.studyControls.outcomeThresholdsAreReleaseBlocking) 'Checkpoint 76 degraded-fire/ECCM policy mismatch.'
Assert-True ([bool]$policy.missileTerminalControls.terminalAttackRequiresFirmSolutionByDefault -and [bool]$policy.missileTerminalControls.baselineCommandGuidedRequiresLiveLauncherFirmDatalink -and -not [bool]$policy.missileTerminalControls.baselineCommandGuidedMaySubstitutePeerGuidance -and [bool]$policy.missileTerminalControls.peerTerminalGuidanceRequiresExplicitProfileCapability -and [bool]$policy.missileTerminalControls.sensorPlusSeekerApproximateRefinementRequiresMissileLocalTrack -and -not [bool]$policy.missileTerminalControls.remoteApproximateAloneMayRefineSensorPlusSeekerToFirm -and -not [bool]$policy.missileTerminalControls.directFireApproximateTraitAppliesToMissiles -and -not [bool]$policy.missileTerminalControls.approximateTerminalMissileCapabilityImplementedByCheckpoint76 -and [bool]$policy.missileTerminalControls.coLocationAloneIsNotImpact) 'Checkpoint 76 missile terminal policy mismatch.'

$registry = Read-Json 'docs/archive/ai/pre-cp165-active/ai_doctrine_registry_v0_2.json'
Assert-True ([string]$registry.registryVersion -eq '0.2' -and [string]$registry.defaults.'electronic-warfare' -eq 'tl1-ew-preserve-combat-package-v1') 'Checkpoint 76 registry default mismatch.'
$doctrines = @($registry.doctrines)
$preserveCombat = @($doctrines | Where-Object { [string]$_.id -eq 'tl1-ew-preserve-combat-package-v1' })
$reactive = @($doctrines | Where-Object { [string]$_.id -eq 'tl1-ew-reactive-eccm-v1' })
$none = @($doctrines | Where-Object { [string]$_.id -eq 'tl1-ew-none-v1' })
Assert-True ($preserveCombat.Count -eq 1 -and [string]$preserveCombat[0].status -eq 'accepted' -and [string]$preserveCombat[0].acceptedCheckpoint -eq '73') 'Checkpoint 76 must consume the accepted CP73 preserve-combat-package doctrine.'
Assert-True ($reactive.Count -eq 1 -and [string]$reactive[0].status -eq 'accepted' -and [string]$reactive[0].acceptedCheckpoint -eq '72') 'Checkpoint 76 must consume the accepted reactive-ECCM doctrine.'
Assert-True ($none.Count -eq 1 -and [string]$none[0].status -eq 'control') 'Checkpoint 76 requires the no-EW control doctrine.'
Assert-True (@($doctrines | Where-Object { [bool]$_.informationPolicy.usesHiddenEnemyRatings }).Count -eq 0) 'Checkpoint 76 AI doctrine must preserve player information parity.'

Write-Host '       Freezing accepted Checkpoint 75a combat and missile authority...'
$frozenHashes = @{
    'src/StarCluster.Core/Combat/DirectFire/DirectFireWeaponProfile.cs' = '489424003edc74f046c799dcb7cb04653b2b083f68a8f0efe79ecfe47d4a0ea0'
    'src/StarCluster.Core/Combat/DirectFire/DirectFireTargetEligibility.cs' = 'b4bee53b3ff506dbf94fd3e5bc0eef3110be336b73c7b4a46dfc1841497eadb7'
    'src/StarCluster.Core/Combat/DirectFire/DirectFireTargetEligibilityResult.cs' = '96833294e88e8c55fe92afd7971a311a0834426df0dac5b08184e41fd67803aa'
    'src/StarCluster.Core/Combat/Tracking/DirectFireTrackEligibility.cs' = '8fbf1a553ccf4a6460b92d532e0e701af062332281fd259558587a84e66349ed'
    'src/StarCluster.Core/Combat/Missiles/MissileTerminalProfile.cs' = '96e01f92d92c77f6910dce68418eb2e0284e1cd7a03bb4f877ed2a3512d4f488'
    'src/StarCluster.Core/Combat/Missiles/MissileTerminalResolutionService.cs' = '6321c3a2e38ae3e2c4d6bfcd5cc440bd953d0ca2e4793d6b204f48fb8078dab6'
    'tests/StarCluster.Tests/Combat/Missiles/MissileTerminalResolutionTests.cs' = '55f5e05a724a4bfdaa9c85244679ffe7d3c750e921efaebf10d8db833ed6b84a'
    'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatDocuments.cs' = '7984535b5fc2b19cd76f253514b6b04cf522a8b47f55f86aac5cd4bdaf6c133c'
    'src/StarCluster.ScenarioRunner/Scenarios/TL1Calibration/tl1-itc16-approximate-track-degraded-fire.json' = '30ee161f598bbe4ced7d9ae197564ac941247fd0b86d08964f52e8dafcd68840'
    'src/StarCluster.ScenarioRunner/Scenarios/TL1Calibration/tl1-itc17-applied-degraded-fire-family-candidates.json' = '447c3e9605760076663d7a0adabecf105af3b313bb9fbfcd9fca1bb76258dfeb'
    'docs/design/player_technology/tl1_integrated_tactical_combat_schema_v0_18.json' = 'd97943ea093e70b0cbd0c16a8176cbf2bb09c509b96cbd2c301c7504b6bd5add'
    'docs/archive/ai/pre-cp165-active/ai_doctrine_registry_v0_2.json' = 'c4a54db2fe84f2487efdb4998f8d17de0a029aaaaf71e13d10f493a90f69068a'
    'src/StarCluster.ScenarioRunner/ScenarioRunnerSelfTests.cs' = '0ebea63b61c22aa474cdfb87715fa28d56c45107df5491748333c1d68388b843'
    'docs/design/player_technology/TL1_Applied_Degraded_Fire_Family_Candidate_Study_v0_1.md' = 'cffad1fa952680983e81a9200ff15ba8c6195a8475c6ce560ba8cfe7683cada6'
    'docs/archive/Star_Cluster_Game_Concept_v0.6n.docx' = '9e60cc5e8d7998d341dd84fdf393828226e2bcd83baa1f4723c8ed56c754b665'
}
foreach ($entry in $frozenHashes.GetEnumerator()) {
    $actualHash = (Get-FileHash -LiteralPath (Join-Path $repositoryRoot $entry.Key) -Algorithm SHA256).Hash.ToLowerInvariant()
    Assert-True ($actualHash -eq [string]$entry.Value) "Checkpoint 76 unintentionally changed frozen Checkpoint 75a authority/input: $($entry.Key)."
}

Write-Host '       Validating the 54-variant degraded-fire/ECCM study independently...'
$study = Read-Json 'src/StarCluster.ScenarioRunner/Scenarios/TL1Calibration/tl1-itc18-degraded-fire-eccm-value-counterplay.json'
Assert-True ([string]$study.id -eq 'tl1-itc18-degraded-fire-eccm-value-counterplay' -and [string]$study.schemaVersion -eq 'star-cluster-tl1-integrated-tactical-combat-v2' -and [int]$study.trialsPerVariant -eq 10000 -and [int64]$study.masterSeed -eq 760100 -and @($study.variants).Count -eq 54) 'Checkpoint 76 study identity/workload mismatch.'
Assert-True ([string]$study.baselineSha256 -eq 'd3020245a1fe2d28f6795c96c3c331d905ed02ef5210f3ab661e3475f70cf5be' -and [string]$study.auxiliaryProfileCatalog -eq 'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/tl1-tl2-auxiliary-runtime-profiles-v0_3.json' -and [string]$study.sensorEwProfileCatalog -eq 'src/StarCluster.ScenarioRunner/Scenarios/SensorEw/tl1-sew03-sensor-ew-discrimination-burnthrough.json' -and [string]$study.aiDoctrineCatalog -eq 'docs/archive/ai/pre-cp165-active/ai_doctrine_registry_v0_2.json') 'Checkpoint 76 study baseline/catalog binding mismatch.'
Assert-True (@($study.builds).Count -eq 1 -and [string]$study.builds[0].id -eq 'balanced_generalist_ew_major' -and [int]$study.builds[0].mainWeaponCount -eq 1 -and [int]$study.builds[0].mainReactorCount -eq 1 -and [bool]$study.builds[0].activeSensor -and [bool]$study.builds[0].shieldGenerator -and [int]$study.builds[0].kineticPdsCount -eq 1 -and [bool]$study.builds[0].ecmSuite -and [bool]$study.builds[0].eccmSuite -and [int]$study.builds[0].usedSpace -eq 35 -and [int]$study.builds[0].freeSupportSpace -eq 0) 'Checkpoint 76 study build fixture mismatch.'
$variants = @($study.variants)
$expectedGroups = @('c76-kvm-r3','c76-evm-r3','c76-kvm-afirst','c76-kvm-bfirst','c76-evm-afirst','c76-evm-bfirst')
$expectedModes = @('firm-reference','jammed-firm-only-no-eccm','jammed-firm-only-reactive-eccm','p20-no-eccm','p20-reactive-eccm','p20-aggressive-eccm','p25-no-eccm','p25-reactive-eccm','p25-aggressive-eccm')
Assert-True (@($variants | Group-Object id | Where-Object { $_.Count -ne 1 }).Count -eq 0) 'Checkpoint 76 study variant IDs must be unique.'
foreach ($group in $expectedGroups) {
    $context = @($variants | Where-Object { [string]$_.comparisonGroup -eq $group })
    Assert-True ($context.Count -eq 9) "Checkpoint 76 comparison group '$group' must contain nine variants."
    foreach ($mode in $expectedModes) {
        Assert-True (@($context | Where-Object { [string]$_.profileLabel -eq $mode }).Count -eq 1) "Checkpoint 76 group '$group' must contain exactly one '$mode' variant."
    }
    $expectedFamily = if ($group.StartsWith('c76-evm-')) { 'Energy' } else { 'Kinetic' }
    Assert-True (@($context | Where-Object { [string]$_.sideAFamily -ne $expectedFamily -or [string]$_.sideBFamily -ne 'Missile' }).Count -eq 0) "Checkpoint 76 group '$group' family binding mismatch."
    if ($group.EndsWith('-r3')) {
        Assert-True (@($context | Where-Object { [int]$_.initialRangeHexes -ne 3 -or [string]$_.movementMode -ne 'HoldRange3' -or [string]$_.movementOrder -ne 'Simultaneous' }).Count -eq 0) "Checkpoint 76 fixed-range group '$group' geometry mismatch."
    }
    else {
        $expectedOrder = if ($group.EndsWith('-afirst')) { 'SideAFirst' } else { 'SideBFirst' }
        Assert-True (@($context | Where-Object { [int]$_.initialRangeHexes -ne 4 -or [string]$_.movementMode -ne 'TrackAwareOpponentRange' -or [string]$_.movementOrder -ne $expectedOrder }).Count -eq 0) "Checkpoint 76 dynamic group '$group' geometry mismatch."
    }
}
foreach ($variant in $variants) {
    Assert-True ([string]$variant.sensorEwProfileId -eq 'balanced-0' -and [int]$variant.startingFuel -eq 100 -and [bool]$variant.pdsEnabled -and [int]$variant.sideAReactorOutputOverride -eq 5 -and [int]$variant.sideBReactorOutputOverride -eq 5 -and [string]$variant.sideATacticalPowerDoctrine -eq 'FullVolleyFirst' -and [string]$variant.sideBTacticalPowerDoctrine -eq 'FullVolleyFirst' -and [string]$variant.sideATrackPolicy -eq 'AcquisitionFirstAutoActive' -and [string]$variant.sideBTrackPolicy -eq 'AcquisitionFirstAutoActive') "Checkpoint 76 variant '$($variant.id)' drifted from the accepted operational fixture."
    Assert-True (-not [bool]$variant.sideBAllowsApproximateDirectFire -and [int]$variant.sideBApproximateDirectFireAccuracyPenalty -eq 0 -and [string]$variant.sideBFamily -eq 'Missile') "Checkpoint 76 variant '$($variant.id)' must not grant degraded fire to missiles."
    $mode = [string]$variant.profileLabel
    $isFirmReference = $mode -eq 'firm-reference'
    $isReactive = $mode.EndsWith('-reactive-eccm')
    $isAggressive = $mode.EndsWith('-aggressive-eccm')
    $expectedPenalty = 0
    if ($mode.StartsWith('p20-')) { $expectedPenalty = 20 }
    elseif ($mode.StartsWith('p25-')) { $expectedPenalty = 25 }
    Assert-True ([bool]$variant.sideAAllowsApproximateDirectFire -eq ($expectedPenalty -gt 0) -and [int]$variant.sideAApproximateDirectFireAccuracyPenalty -eq $expectedPenalty) "Checkpoint 76 variant '$($variant.id)' degraded-fire package mismatch."
    $doctrineA = Get-OptionalPropertyValue $variant 'sideAAiDoctrineId'
    $doctrineB = Get-OptionalPropertyValue $variant 'sideBAiDoctrineId'
    if ($isFirmReference) {
        Assert-True ([string]$variant.sideBEcmPolicy -eq 'None' -and [string]$variant.sideAEccmPolicy -eq 'None' -and [string]$doctrineA -eq 'tl1-ew-none-v1' -and [string]$doctrineB -eq 'tl1-ew-none-v1') "Checkpoint 76 Firm reference '$($variant.id)' EW binding mismatch."
    }
    else {
        Assert-True ([string]$variant.sideBEcmPolicy -eq 'Normal' -and [string]$doctrineB -eq 'tl1-ew-preserve-combat-package-v1') "Checkpoint 76 jammed variant '$($variant.id)' must use the accepted hostile ECM affordability doctrine."
        if ($isReactive) {
            Assert-True ([string]$variant.sideAEccmPolicy -eq 'ReactiveNormal' -and [string]$doctrineA -eq 'tl1-ew-reactive-eccm-v1') "Checkpoint 76 reactive variant '$($variant.id)' doctrine mismatch."
        }
        elseif ($isAggressive) {
            Assert-True ([string]$variant.sideAEccmPolicy -eq 'Normal' -and $null -eq $doctrineA) "Checkpoint 76 aggressive variant '$($variant.id)' must remain a raw-policy diagnostic without an AI-doctrine binding."
        }
        else {
            Assert-True ([string]$variant.sideAEccmPolicy -eq 'None' -and [string]$doctrineA -eq 'tl1-ew-none-v1') "Checkpoint 76 no-ECCM variant '$($variant.id)' doctrine mismatch."
        }
    }
}

Write-Host '       Auditing CP76 ScenarioRunner integration and release gates...'
$runnerPath = Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\TL1Calibration\Tl1IntegratedTacticalCombatRunner.cs'
$runner = Get-Content -LiteralPath $runnerPath -Raw
Assert-True (($runner.Split('Tl1DegradedFireEccmValueStudyId')).Count -ge 13) 'Checkpoint 76 ScenarioRunner registration is incomplete across shared/global study classifications.'
Assert-True ($runner.Contains('ValidateTl1DegradedFireEccmValueCoverage(') -and $runner.Contains('RequiredTl1DegradedFireEccmValueVariantCount = 54')) 'Checkpoint 76 actual-consumer validator registration missing.'
Assert-True ($runner.Contains('bool doctrineEwA') -and $runner.Contains('bool doctrineEwB') -and $runner.Contains('tl1-ew-preserve-combat-package-v1') -and $runner.Contains('tl1-ew-reactive-eccm-v1')) 'Checkpoint 76 mixed accepted-doctrine/raw-policy EW execution wiring missing.'
Assert-True ($runner.Contains('WriteTl1DegradedFireEccmValueReview(') -and $runner.Contains('degraded-fire-eccm-value-review.csv') -and $runner.Contains('DegradedFireEccmProfileOrder(')) 'Checkpoint 76 review writer/output routing missing.'
$buildGatesStart = $runner.IndexOf('private static IReadOnlyList<Tl1IntegratedTacticalCombatGate> BuildGates', [System.StringComparison]::Ordinal)
Assert-True ($buildGatesStart -ge 0) 'Checkpoint 76 could not locate BuildGates.'
$gateStart = $runner.IndexOf('if (study.Id == Tl1DegradedFireEccmValueStudyId)', $buildGatesStart, [System.StringComparison]::Ordinal)
$gateEnd = $runner.IndexOf('if (IsCheckpoint57Study', $gateStart, [System.StringComparison]::Ordinal)
Assert-True ($gateStart -gt $buildGatesStart -and $gateEnd -gt $gateStart) 'Checkpoint 76 could not isolate its release-gate block inside BuildGates.'
$gateBlock = $runner.Substring($gateStart, $gateEnd - $gateStart)
$requiredGates = @(
    'tl1-c76-variant-coverage',
    'tl1-c76-firm-reference-clean',
    'tl1-c76-fixed-range-firm-only-blocked',
    'tl1-c76-fixed-range-reactive-eccm-restores-firm',
    'tl1-c76-fixed-range-degraded-fire-exercised',
    'tl1-c76-reactive-and-aggressive-eccm-exercised',
    'tl1-c76-no-missile-degraded-fire',
    'tl1-c76-outcomes-review-only'
)
foreach ($gateName in $requiredGates) {
    $firstOccurrence = $gateBlock.IndexOf($gateName, [System.StringComparison]::Ordinal)
    $lastOccurrence = $gateBlock.LastIndexOf($gateName, [System.StringComparison]::Ordinal)
    Assert-True ($firstOccurrence -ge 0 -and $firstOccurrence -eq $lastOccurrence) "Checkpoint 76 release-gate block must contain exactly one '$gateName' gate."
}
Assert-True ($gateBlock.Contains('MeanEccmPowerCommittedA') -and $gateBlock.Contains('MeanEcmPowerCommittedB') -and $gateBlock.Contains('MeanPdsAttempts') -and $gateBlock.Contains('no combat outcome automatically promotes')) 'Checkpoint 76 gate block must preserve EW/PDS telemetry and review-only semantics.'

Write-Host '       Validating weapon-specific regression and frozen missile guardrails...'
$directFireTests = Get-Content -LiteralPath (Join-Path $repositoryRoot 'tests\StarCluster.Tests\Combat\DirectFire\DirectFireTargetEligibilityTests.cs') -Raw
Assert-True ($directFireTests.Contains('ApproximateTrackPermissionIsSpecificToTheWeaponProfile') -and $directFireTests.Contains('MissileInterceptionRemainsFirmOnlyEvenForTraitWeapon')) 'Checkpoint 76 must prove per-weapon degraded-fire isolation and preserve Firm-only missile interception.'
$terminalResolver = Get-Content -LiteralPath (Join-Path $repositoryRoot 'src\StarCluster.Core\Combat\Missiles\MissileTerminalResolutionService.cs') -Raw
$terminalTests = Get-Content -LiteralPath (Join-Path $repositoryRoot 'tests\StarCluster.Tests\Combat\Missiles\MissileTerminalResolutionTests.cs') -Raw
Assert-True ($terminalResolver.Contains('salvo.TerminalProfile.AllowsPeerTerminalGuidance') -and $terminalResolver.Contains('requires at least an Approximate missile-local navigation track')) 'Checkpoint 76 must preserve Checkpoint 75 missile terminal-source/local-track guardrails.'
foreach ($testName in @('CommandGuidedMissileAcceptsLiveFirmDatalink','PeerGuidanceCannotAuthorizeBaselineCommandGuidedTerminalAttack','PeerGuidanceCanAuthorizeTerminalAttackWhenProfileExplicitlyAllowsIt','SeekerOnlyMissileCanUseRemoteApproximateCueForCoLocatedAcquisition','SensorPlusSeekerRejectsRemoteApproximateCueWithoutLocalNavigationTrack','SensorPlusSeekerCanRefineLocalApproximateNavigationTrackIntoFirm')) {
    Assert-True ($terminalTests.Contains($testName)) "Checkpoint 76 missile regression '$testName' missing."
}

Write-Host '       Validating Concept, design notes, and clean repository presentation...'
$concepts = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs') -File -Filter 'Star_Cluster_Game_Concept_v*.docx')
Assert-True ($concepts.Count -eq 1 -and $concepts[0].Name -eq 'Star_Cluster_Game_Concept_v0.6o.docx') 'Checkpoint 76 must expose exactly one active Concept v0.6o.'
$conceptHash = (Get-FileHash -LiteralPath (Join-Path $repositoryRoot 'docs/Star_Cluster_Game_Concept_v0.6o.docx') -Algorithm SHA256).Hash.ToLowerInvariant()
Assert-True ($conceptHash -eq '51c29cb4caf78c8a69e0477fc876e07051d6b159266ea2b84065acb7399b3e6a') 'Checkpoint 76 active Concept v0.6o content hash mismatch.'
$studyNote = Get-Content -LiteralPath (Join-Path $repositoryRoot 'docs\design\player_technology\TL1_Degraded_Fire_ECCM_Value_Counterplay_Study_v0_1.md') -Raw
$missileNote = Get-Content -LiteralPath (Join-Path $repositoryRoot 'docs\design\Missile_Guidance_Datalink_Sensor_And_Seeker_Architecture.md') -Raw
Assert-True ($studyNote.Contains('explicit weapon-profile, variant, or upgrade capability') -and $studyNote.Contains('material combat penalty') -and $studyNote.Contains('Swarmer Missile') -and $studyNote.Contains('540,000')) 'Checkpoint 76 degraded-fire/ECCM study note is incomplete.'
Assert-True ($missileNote.Contains('Future missile-specific Approximate-terminal capability') -and $missileNote.Contains('does **not** apply to missiles') -and $missileNote.Contains('implements no missile Approximate-terminal attack')) 'Checkpoint 76 missile architecture future-capability boundary is incomplete.'
$validationFiles = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs\validation') -File -Filter 'Checkpoint_*.md')
Assert-True ($validationFiles.Count -eq 1 -and $validationFiles[0].Name -eq 'Checkpoint_76_Degraded_Fire_ECCM_Value_Counterplay_And_Upgrade_Path_Guardrails.md') 'Checkpoint 76 must expose exactly one active validation runbook.'
Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot 'docs/validation/archive/Checkpoint_75a_Release_Gate_Block_Isolation_Hotfix.md') -PathType Leaf) 'Checkpoint 76 must archive the accepted Checkpoint 75a validation runbook.'
$rootTxt = @(Get-ChildItem -LiteralPath $repositoryRoot -File -Filter '*.txt')
Assert-True ($rootTxt.Count -eq 1 -and $rootTxt[0].Name -eq 'CHECKPOINT_76_SHA256SUMS.txt') 'Repository root must contain only CHECKPOINT_76_SHA256SUMS.txt as .txt.'
$rootReadme = Get-Content -LiteralPath (Join-Path $repositoryRoot 'README.md') -Raw
$docsReadme = Get-Content -LiteralPath (Join-Path $repositoryRoot 'docs/README.md') -Raw
$todo = Get-Content -LiteralPath (Join-Path $repositoryRoot 'docs/Prototype_TODO.md') -Raw
Assert-True ($rootReadme.Contains('Checkpoint 76') -and $rootReadme.Contains('Concept v0.6o') -and $rootReadme.Contains('checkpoint-76/apply_checkpoint_76.ps1')) 'Checkpoint 76 root README is stale.'
Assert-True ($docsReadme.Contains('Checkpoint 76') -and $docsReadme.Contains('Star_Cluster_Game_Concept_v0.6o.docx') -and $docsReadme.Contains('Checkpoint_76_Degraded_Fire_ECCM_Value_Counterplay_And_Upgrade_Path_Guardrails.md')) 'Checkpoint 76 documentation README is stale.'
Assert-True ($todo.Contains('Checkpoint 76') -and $todo.Contains('540,000') -and $todo.Contains('degraded-fire-eccm-value-review.csv')) 'Checkpoint 76 prototype TODO is stale.'

Write-Host '       Checkpoint 76 scope: operational degraded-fire/ECCM value evidence plus explicit upgrade-path and missile-future-capability guardrails.'
Write-Host '       Production direct-fire weapon data and ordinary missile terminal mechanics remain unchanged.'
Write-Host 'Checkpoint 76 contract validation passed.'
