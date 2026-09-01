[CmdletBinding()]
param(
    [string]$RepositoryRoot
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($RepositoryRoot)) {
    $repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
} else {
    $repositoryRoot = (Resolve-Path $RepositoryRoot).Path
}

function Assert-True { param([bool]$Condition,[string]$Message) if (-not $Condition) { throw $Message } }
function RelPath { param([string]$RelativePath) return (Join-Path $repositoryRoot ($RelativePath.Replace('/','\'))) }
function Read-Text { param([string]$RelativePath) $p=RelPath $RelativePath; Assert-True (Test-Path -LiteralPath $p -PathType Leaf) "Required file '$RelativePath' is missing."; return [System.IO.File]::ReadAllText($p) }
function Read-Json { param([string]$RelativePath) return ((Read-Text $RelativePath) | ConvertFrom-Json) }
function Hash-Rel { param([string]$RelativePath) $p=RelPath $RelativePath; Assert-True (Test-Path -LiteralPath $p -PathType Leaf) "Hash target '$RelativePath' is missing."; return (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant() }
function Require-Contains { param([string]$Text,[string]$Needle,[string]$Message) Assert-True ($Text.IndexOf($Needle,[System.StringComparison]::OrdinalIgnoreCase) -ge 0) $Message }
function Require-NotContains { param([string]$Text,[string]$Needle,[string]$Message) Assert-True ($Text.IndexOf($Needle,[System.StringComparison]::OrdinalIgnoreCase) -lt 0) $Message }
function Has-Property { param($Object,[string]$Name) return ($null -ne $Object -and $null -ne $Object.PSObject.Properties[$Name]) }
function Require-Property { param($Object,[string]$Name,[string]$Context) Assert-True (Has-Property $Object $Name) "$Context is missing property '$Name'." }
function Read-Manifest {
    param([string]$RelativePath)
    $p=RelPath $RelativePath
    Assert-True (Test-Path -LiteralPath $p -PathType Leaf) "Manifest '$RelativePath' is missing."
    $lines=@(Get-Content -LiteralPath $p)
    $map=@{}
    $lineNo=0
    foreach($line in $lines){
        $lineNo++
        Assert-True (-not [string]::IsNullOrWhiteSpace([string]$line)) "Manifest '$RelativePath' contains blank line $lineNo."
        $m=[regex]::Match([string]$line,'^([0-9a-fA-F]{64})  (.+)$')
        Assert-True $m.Success "Manifest '$RelativePath' has malformed line $lineNo."
        $rel=$m.Groups[2].Value.Replace('\','/')
        Assert-True (-not $map.ContainsKey($rel)) "Manifest '$RelativePath' duplicates '$rel'."
        $map[$rel]=$m.Groups[1].Value.ToLowerInvariant()
    }
    return [pscustomobject]@{ PhysicalLineCount=$lines.Count; EntryCount=$map.Count; Entries=$map }
}
function Assert-ExactFileSet {
    param([string]$RelativeDirectory,[string[]]$Expected)
    $p=RelPath $RelativeDirectory
    Assert-True (Test-Path -LiteralPath $p -PathType Container) "Directory '$RelativeDirectory' is missing."
    $actual=@(Get-ChildItem -LiteralPath $p -File | ForEach-Object { $_.Name } | Sort-Object)
    $want=@($Expected | Sort-Object)
    Assert-True ($actual.Count -eq $want.Count) "Directory '$RelativeDirectory' has $($actual.Count) active files; expected $($want.Count)."
    for($i=0;$i -lt $want.Count;$i++){
        Assert-True ([string]$actual[$i] -eq [string]$want[$i]) "Directory '$RelativeDirectory' active file set drifted: expected '$($want[$i])', found '$($actual[$i])'."
    }
}
function Assert-Sequence {
    param([object[]]$Actual,[string[]]$Expected,[string]$Message)
    Assert-True ($Actual.Count -eq $Expected.Count) $Message
    for($i=0;$i -lt $Expected.Count;$i++){
        Assert-True ([string]$Actual[$i] -eq $Expected[$i]) $Message
    }
}

Write-Host '       Validating native-dependency declarations and proven wrapper interface...'
$guard=RelPath 'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1'
$normalRel='tools/calibration/checkpoints/checkpoint-94.json'
$deepRel='tools/calibration/checkpoints/checkpoint-94-deep-calibration.json'
$guardedPs=@(
    'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
    'tools/checkpoints/checkpoint-94/apply_checkpoint_94.ps1',
    'tools/checkpoints/checkpoint-94/test_checkpoint_94_contract.ps1',
    'tools/calibration/run_calibration_checkpoint.ps1'
)
& $guard -RepositoryRoot $repositoryRoot -PowerShellPaths $guardedPs -CheckpointDefinitionPaths @($normalRel,$deepRel)
$applyText=Read-Text 'tools/checkpoints/checkpoint-94/apply_checkpoint_94.ps1'
$provenHarnessCall='& $harness -CheckpointDefinition $definition -Trials $Trials -Jobs $Jobs -RepositoryOnly:$RepositoryOnly -NoClean:$NoClean'
Require-Contains $applyText $provenHarnessCall 'Checkpoint 94 wrapper must preserve the proven direct named-parameter harness invocation.'
Assert-True (-not [regex]::IsMatch($applyText,'&\s+\$harness\s+@[A-Za-z_][A-Za-z0-9_]*',[System.Text.RegularExpressions.RegexOptions]::IgnoreCase)) 'Checkpoint 94 wrapper must not invoke the calibration harness through splatted arguments.'
$guardText=Read-Text 'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1'
Require-Contains $guardText 'Assert-ProvenCheckpointHarnessInvocation' 'Native dependency/archive precheck must continue validating the checkpoint-wrapper harness interface.'
Require-Contains $guardText 'array splatting can silently become positional binding' 'Native dependency/archive precheck must retain the array-splat positional-binding failure explanation.'

Write-Host '       Validating Checkpoint 94 definitions and bounded workload accounting...'
$normal=Read-Json $normalRel
$deep=Read-Json $deepRel
$expectedStageIds=@(
    'deterministic','tl1-phase-a','tl1-phase-b','tl1-installation-space-envelope','tl1-sensor-ew-foundation',
    'cross-tl-build-permutation-preflight','cross-tl-build-permutation-generation','cross-tl-generated-study-preflight',
    'cross-tl-generated-study-smoke','cross-tl-build-permutation-screening','auxiliary-resource-endurance',
    'checkpoint-53-resource-semantics-lock','runner-self-tests'
)
foreach($d in @($normal,$deep)){
    Assert-True ([string]$d.checkpointId -eq '94') 'Checkpoint 94 definition ID mismatch.'
    Assert-True ([string]$d.manifestFile -eq 'CHECKPOINT_94_SHA256SUMS.txt') 'Checkpoint 94 manifest binding mismatch.'
    Assert-True ([int]$d.defaultTrials -eq 1500 -and [int]$d.defaultJobs -eq 24) 'Checkpoint 94 default Trials/Jobs mismatch.'
    Assert-True (@($d.stages).Count -eq 13 -and [int]$d.checkpointMetrics.stageCount -eq 13) 'Checkpoint 94 must contain exactly 13 configured runner stages.'
    Assert-True ([int]$d.checkpointMetrics.monteCarloVariantCount -eq 1440 -and [long]$d.checkpointMetrics.trialsAtDefault -eq 2160000) 'Checkpoint 94 substantive workload accounting mismatch.'
    Assert-True ([int]$d.checkpointMetrics.smokeVariantExecutions -eq 1440 -and [long]$d.checkpointMetrics.smokeTrialsAtDefault -eq 1440 -and [long]$d.checkpointMetrics.totalTrialExecutionsAtDefault -eq 2161440) 'Checkpoint 94 smoke/total workload accounting mismatch.'
    Assert-True ([bool]$d.checkpointMetrics.architectureHardening -and [bool]$d.checkpointMetrics.samplingQuality -and [bool]$d.checkpointMetrics.boundedRepresentativeStudy -and -not [bool]$d.checkpointMetrics.deepCalibrationApplicable) 'Checkpoint 94 must remain a bounded sampling-quality/architecture-hardening study with Deep Calibration not applicable.'
    Assert-True ([string]$d.primaryStudy.id -eq 'tl2-itc16-cross-tl-matched-readiness-space-screening' -and [int]$d.primaryStudy.variantCount -eq 1440) 'Checkpoint 94 primary-study metadata mismatch.'
    Assert-Sequence @($d.stages | ForEach-Object { [string]$_.id }) $expectedStageIds 'Checkpoint 94 configured runner-stage order drifted.'
    Assert-Sequence @($d.nativeDependencyPrecheck.powerShellPaths) $guardedPs 'Checkpoint 94 native-dependency PowerShell path list drifted.'
    Assert-Sequence @($d.nativeDependencyPrecheck.checkpointDefinitionPaths) @($normalRel,$deepRel) 'Checkpoint 94 native-dependency checkpoint-definition list drifted.'

    $self=@($d.stages | Where-Object { [string]$_.id -eq 'runner-self-tests' })
    Assert-True ($self.Count -eq 1 -and [int]$self[0].metrics.selfTestCount -eq 58) 'Checkpoint 94 must expect 58 ScenarioRunner self-tests.'
    $pre=@($d.stages | Where-Object { [string]$_.id -eq 'cross-tl-build-permutation-preflight' })
    $gen=@($d.stages | Where-Object { [string]$_.id -eq 'cross-tl-build-permutation-generation' })
    $consumer=@($d.stages | Where-Object { [string]$_.id -eq 'cross-tl-generated-study-preflight' })
    $smoke=@($d.stages | Where-Object { [string]$_.id -eq 'cross-tl-generated-study-smoke' })
    $screen=@($d.stages | Where-Object { [string]$_.id -eq 'cross-tl-build-permutation-screening' })
    Assert-True ($pre.Count -eq 1 -and $gen.Count -eq 1 -and $consumer.Count -eq 1 -and $smoke.Count -eq 1 -and $screen.Count -eq 1) 'Checkpoint 94 cross-TL stage multiplicity mismatch.'
    Assert-True ([string]$pre[0].arguments[1] -eq 'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/cross-tl-build-permutation-foundation-v0_5.json') 'Checkpoint 94 preflight must bind foundation v0.5.'
    Assert-True ([int]$pre[0].metrics.legalBuildCount -eq 22592 -and [int]$pre[0].metrics.basePopulationCellCount -eq 96 -and [int]$pre[0].metrics.statisticalUnorderedBasePairCount -eq 192 -and [int]$pre[0].metrics.diversityUnorderedBasePairCount -eq 24 -and [int]$pre[0].metrics.generatedVariantCount -eq 1440) 'Checkpoint 94 preflight sampling metrics mismatch.'
    Assert-True ([int]$gen[0].metrics.statisticalUnorderedBasePairCount -eq 192 -and [int]$gen[0].metrics.statisticalLogicalPairingCount -eq 384 -and [int]$gen[0].metrics.diversityUnorderedBasePairCount -eq 24 -and [int]$gen[0].metrics.diversityLogicalPairingCount -eq 48 -and [int]$gen[0].metrics.stratifiedLogicalPairingCount -eq 432 -and [int]$gen[0].metrics.logicalPairingCount -eq 480 -and [int]$gen[0].metrics.generatedVariantCount -eq 1440) 'Checkpoint 94 generator adaptive/diversity metrics mismatch.'
    Assert-True ([bool]$gen[0].metrics.matchedBidirectional -and [bool]$gen[0].metrics.adaptivePopulationSampling -and [bool]$gen[0].metrics.diversityOverlayDiagnosticOnly -and [bool]$gen[0].metrics.readyRangeClassification -and [bool]$gen[0].metrics.secondaryCoverageOutput) 'Checkpoint 94 generator analysis controls mismatch.'
    Assert-True ([int]$consumer[0].metrics.variantCount -eq 1440 -and [bool]$consumer[0].metrics.actualConsumerDeserializer -and [bool]$consumer[0].metrics.sideSpecificActivityTelemetry -and [bool]$consumer[0].metrics.individualObservedEngagementDiagnostics -and [bool]$consumer[0].metrics.moverOrderNeutralReporting) 'Checkpoint 94 generated-study actual-consumer preflight metrics mismatch.'
    Assert-True ([int]$smoke[0].metrics.variantCount -eq 1440 -and [int]$smoke[0].metrics.trialsPerVariant -eq 1 -and [int]$smoke[0].metrics.totalSmokeTrials -eq 1440 -and [bool]$smoke[0].metrics.fullPipelineExecution) 'Checkpoint 94 full-pipeline smoke metrics mismatch.'
    Assert-True ([int]$screen[0].metrics.variantCount -eq 1440 -and [int]$screen[0].metrics.logicalPairingCount -eq 480 -and [string]$screen[0].metrics.standingPermutationSuite -eq 'v0.11' -and [bool]$screen[0].metrics.populationWeightedReporting -and [bool]$screen[0].metrics.moverOrderNeutralReporting -and [bool]$screen[0].metrics.individualObservedEngagementDiagnostics) 'Checkpoint 94 substantive screening metrics mismatch.'
}

Write-Host '       Validating accepted Checkpoint 93 provenance and frozen baseline...'
$acceptedManifestRel='docs/validation/evidence/checkpoint-93/CHECKPOINT_93_SHA256SUMS.txt'
$acceptedManifest=Read-Manifest $acceptedManifestRel
Assert-True ($acceptedManifest.EntryCount -eq 1836 -and $acceptedManifest.PhysicalLineCount -eq 1836) 'Accepted Checkpoint 93 embedded manifest must contain exactly 1,836 entries.'
Assert-True ((Hash-Rel $acceptedManifestRel) -eq 'b1653b049655961474518872286c6bb044d83bcf3d349c5ecdce0224f118baec') 'Accepted Checkpoint 93 embedded manifest SHA-256 mismatch.'
$accepted=Read-Json 'docs/validation/evidence/checkpoint-93/checkpoint-93-native-acceptance-provenance.json'
Assert-True ([string]$accepted.checkpointId -eq '93' -and [string]$accepted.status -eq 'Success') 'Accepted Checkpoint 93 provenance status mismatch.'
Assert-True ([string]$accepted.sdk.expected -eq '8.0.423' -and [string]$accepted.sdk.actual -eq '8.0.423') 'Accepted Checkpoint 93 SDK provenance mismatch.'
Assert-True ([bool]$accepted.build.succeeded -and [int]$accepted.build.warnings -eq 0 -and [int]$accepted.build.errors -eq 0) 'Accepted Checkpoint 93 build provenance mismatch.'
Assert-True ([int]$accepted.tests.total -eq 863 -and [int]$accepted.tests.passed -eq 863 -and [int]$accepted.tests.failed -eq 0 -and [int]$accepted.tests.skipped -eq 0) 'Accepted Checkpoint 93 test provenance mismatch.'
Assert-True ([int]$accepted.runner.configuredStages -eq 13 -and [int]$accepted.runner.passedStages -eq 13 -and [int]$accepted.runner.failedStages -eq 0 -and [int]$accepted.runner.selfTests -eq 57 -and [int]$accepted.runner.failedGates -eq 0) 'Accepted Checkpoint 93 runner provenance mismatch.'
Assert-True ([int]$accepted.primaryStudy.variantCount -eq 720 -and [int]$accepted.primaryStudy.trialsPerVariant -eq 2000 -and [long]$accepted.primaryStudy.totalTrials -eq 1440000) 'Accepted Checkpoint 93 substantive-study provenance mismatch.'
Assert-True ([string]$accepted.checkpointDefinitionSha256 -eq '160adb4fee4fb419136916da0b99e7ebeb2f495c43513033fc93dd0852e970cb' -and [string]$accepted.repositoryManifestSha256 -eq 'b1653b049655961474518872286c6bb044d83bcf3d349c5ecdce0224f118baec') 'Accepted Checkpoint 93 hash provenance mismatch.'

$allowedAcceptedChanges=@(
    'CHAT_README.md',
    'README.md',
    'docs/README.md',
    'docs/design/testing/README.md',
    'docs/development/Simulation_Development_Guidelines.md',
    'src/StarCluster.ScenarioRunner/CrossTlIntegration/CrossTlBuildPermutationRunner.cs',
    'src/StarCluster.ScenarioRunner/ScenarioRunnerSelfTests.cs',
    'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs',
    'docs/design/testing/Checkpoint_93_Validation_Tiers.md',
    'docs/design/testing/Technology_Integration_Permutation_Suite_Architecture_v0_10.md',
    'docs/design/testing/checkpoint_93_validation_suite_policy_v0_1.json',
    'docs/design/testing/technology_integration_permutation_suite_v0_10.json',
    'docs/validation/Checkpoint_93_Matched_Readiness_Space_And_Population_Weighted_Cross_TL_Screening.md'
)
$allowedSet=@{}
foreach($rel in $allowedAcceptedChanges){ $allowedSet[$rel]=$true }
$frozenCount=0
foreach($rel in $acceptedManifest.Entries.Keys){
    if ($allowedSet.ContainsKey($rel)) { continue }
    $p=RelPath $rel
    Assert-True (Test-Path -LiteralPath $p -PathType Leaf) "Checkpoint 94 unexpectedly removed accepted CP93 file '$rel'."
    $actual=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()
    Assert-True ($actual -eq [string]$acceptedManifest.Entries[$rel]) "Checkpoint 94 unexpectedly changed accepted CP93 file '$rel'."
    $frozenCount++
}
Assert-True ($frozenCount -eq 1823) "Checkpoint 94 must byte-freeze exactly 1,823 accepted CP93 paths outside its 13-path change/move allowlist; observed $frozenCount."

$archiveMap=@{
    'docs/design/testing/Checkpoint_93_Validation_Tiers.md'='docs/archive/testing/Checkpoint_93_Validation_Tiers.md';
    'docs/design/testing/Technology_Integration_Permutation_Suite_Architecture_v0_10.md'='docs/archive/testing/Technology_Integration_Permutation_Suite_Architecture_v0_10.md';
    'docs/design/testing/checkpoint_93_validation_suite_policy_v0_1.json'='docs/archive/testing/checkpoint_93_validation_suite_policy_v0_1.json';
    'docs/design/testing/technology_integration_permutation_suite_v0_10.json'='docs/archive/testing/technology_integration_permutation_suite_v0_10.json';
    'docs/validation/Checkpoint_93_Matched_Readiness_Space_And_Population_Weighted_Cross_TL_Screening.md'='docs/validation/archive/Checkpoint_93_Matched_Readiness_Space_And_Population_Weighted_Cross_TL_Screening.md'
}
foreach($old in $archiveMap.Keys){
    $archived=[string]$archiveMap[$old]
    Assert-True (-not (Test-Path -LiteralPath (RelPath $old) -PathType Leaf)) "Superseded CP93 active file '$old' must not remain active."
    Assert-True ((Hash-Rel $archived) -eq [string]$acceptedManifest.Entries[$old]) "Archived CP93 file '$archived' must be byte-identical to accepted '$old'."
}
$referenceCount=0
foreach($rel in $acceptedManifest.Entries.Keys){
    if (-not $rel.StartsWith('docs/references/',[System.StringComparison]::Ordinal)) { continue }
    Assert-True ((Hash-Rel $rel) -eq [string]$acceptedManifest.Entries[$rel]) "Checkpoint 94 must byte-preserve accepted reference/reference-mining file '$rel'."
    $referenceCount++
}
Assert-True ($referenceCount -eq 81) "Checkpoint 94 must byte-preserve exactly 81 accepted CP93 reference/reference-mining files; observed $referenceCount."

Write-Host '       Validating cross-TL foundation v0.5 and adaptive sample accounting...'
$studyRel='src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/cross-tl-build-permutation-foundation-v0_5.json'
$study=Read-Json $studyRel
Assert-True ([string]$study.schemaVersion -eq 'star-cluster-cross-tl-build-permutation-v5' -and [string]$study.id -eq 'cross-tl-build-permutation-foundation-v0_5' -and [string]$study.checkpoint -eq '94') 'Cross-TL foundation v0.5 identity mismatch.'
Assert-True ([string]$study.variantIdPrefix -eq 'c94' -and [long]$study.masterSeed -eq 940100 -and [int]$study.trialsPerVariant -eq 1500) 'Cross-TL foundation v0.5 seed/trials mismatch.'
Assert-True (@($study.axes).Count -eq 9 -and [int]$study.expectedRawCombinationCount -eq 82944 -and [int]$study.expectedLegalBuildCount -eq 22592 -and [int]$study.expectedExactFillBuildCount -eq 4672 -and [int]$study.expectedNearFillBuildCount -eq 11328 -and [int]$study.expectedUnderfilledBuildCount -eq 6592) 'Cross-TL foundation v0.5 legal-build envelope mismatch.'
Assert-True ([long]$study.expectedUnorderedDistinctPairingEnvelope -eq 255187936 -and [long]$study.expectedOrientedDistinctPairingEnvelope -eq 510375872) 'Cross-TL foundation v0.5 distinct-pair envelope mismatch.'
Assert-True ([int]$study.expectedNamedLogicalPairingCount -eq 48 -and [int]$study.expectedStratifiedLogicalPairingCount -eq 432 -and [int]$study.expectedLogicalPairingCount -eq 480 -and [int]$study.expectedGeneratedVariantCount -eq 1440 -and [int]$study.expectedGeometryCount -eq 3) 'Cross-TL foundation v0.5 pairing/variant accounting mismatch.'
$selection=$study.stratifiedPairingSelection
Assert-True ([bool]$selection.enabled -and [bool]$selection.matchedBidirectional -and [long]$selection.seed -eq 940177) 'Cross-TL foundation v0.5 matched sampler configuration mismatch.'
Assert-True ([bool]$selection.adaptiveAllocationEnabled -and [int]$selection.targetBasePairBudget -eq 192 -and [int]$selection.expectedBasePairCount -eq 192 -and [int]$selection.expectedSampleCount -eq 384 -and [int]$selection.minimumPerPopulationCell -eq 1 -and [double]$selection.allocationExponent -eq 0.5 -and [int]$selection.maximumPerPopulationCell -eq 5) 'Cross-TL foundation v0.5 adaptive statistical allocation mismatch.'
Assert-True ([bool]$selection.diversityOverlayEnabled -and [int]$selection.diversityOverlayTopCellCount -eq 12 -and [int]$selection.diversityOverlayPairsPerCell -eq 2 -and [int]$selection.expectedDiversityBasePairCount -eq 24 -and [int]$selection.expectedDiversitySampleCount -eq 48) 'Cross-TL foundation v0.5 diversity-overlay accounting mismatch.'
Assert-True ([int]$selection.informationControlNearDistanceMaximum -eq 2 -and [int]$selection.maxAttempts -eq 500000) 'Cross-TL foundation v0.5 information-control/attempt bounds mismatch.'
Assert-Sequence @($selection.compositionClasses) @('single-no-ew-redundancy','ew-redundancy','weapon-reactor-duplication','combined-duplication') 'Cross-TL v0.5 composition-cell axis drifted.'
Assert-Sequence @($selection.progressionMagnitudeStrata) @('equal_low','equal_high','near','far') 'Cross-TL v0.5 progression-cell axis drifted.'
Assert-Sequence @($selection.spaceUtilizationClasses) @('exact_fill','near_fill','underfilled') 'Cross-TL v0.5 Space-utilization axis drifted.'
Assert-True (@($selection.spacePairStrata).Count -eq 6) 'Cross-TL v0.5 must retain six unordered Space-pair strata.'

Write-Host '       Validating CP94 runtime integration, exact readiness, activity diagnostics, and mover-neutral routing...'
$generator=Read-Text 'src/StarCluster.ScenarioRunner/CrossTlIntegration/CrossTlBuildPermutationRunner.cs'
foreach($needle in @(
    'SchemaVersionV5','AllocateAdaptiveCellQuotas','SelectAdaptiveMatchedPairings','"statistical"','"diversity"',
    'PopulationRepresentativeWeight','InformationControlDistanceBand','SideAMaximumReadyRangeHexes','SideBMaximumReadyRangeHexes',
    'WriteSecondaryCoverage','ready-range-classification-complete','adaptive-statistical-population-weight-splitting',
    'diversity-overlay-zero-inference-weight','secondary-diversity-overlay-coverage','DeserializeSensorEwFoundationCatalog',
    'PropertyNameCaseInsensitive = true')){
    Require-Contains $generator $needle "Cross-TL v0.5 generator is missing '$needle'."
}
Require-NotContains $generator 'JsonSerializer.Deserialize<Tl1SensorEwFoundationStudy>(json, JsonOptions())' 'Cross-TL v0.5 must not regress to the strict case-sensitive Sensor/EW catalog binding path.'
$consumerText=Read-Text 'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs'
foreach($needle in @(
    'RequiredCrossTlMatchedReadinessSpaceScreeningVariantCount = 1440','cross-tl-cp94-contextual-combat-activity','cross-tl-cp94-individual-observed-engagement',
    'movement_did_not_reach_mutual_ready_range','ready_geometry_reached_but_one_side_inactive','ready_geometry_reached_but_no_actions',
    'cross-tl-cp94-paired-review.csv','cross-tl-cp94-population-weighted-review.csv','cross-tl-cp94-activity-review.csv',
    'cross-tl-cp94-mover-neutral-review.csv','cross-tl-cp94-mover-neutral-summary.csv',
    'populationRepresentativeWeight','populationSampleCount','infoBand','readyRangeA','readyRangeB','secondaryKey',
    'SensitivityClass','dynamic-a-first','dynamic-b-first')){
    Require-Contains $consumerText $needle "Integrated combat consumer is missing CP94 contract '$needle'."
}
Require-Contains $consumerText 'result.Trials > 1' 'CP94 substantive no-action gate must remain nonblocking for the one-trial smoke.'
Require-NotContains $consumerText 'row.HigherAdvancedWin.HasValue ? F(row.HigherAdvancedWin.Value)' 'CP94 paired-review nullable values must use single-evaluation pattern matching; repeated nullable tuple-member access triggers warning-as-error CS8629 on the native compiler.'
Require-NotContains $consumerText 'row.HigherAdvancedNeutralWin.HasValue ? F(row.HigherAdvancedNeutralWin.Value)' 'CP94 mover-neutral nullable values must use single-evaluation pattern matching; repeated nullable tuple-member access triggers warning-as-error CS8629 on the native compiler.'
Require-Contains $consumerText 'row.HigherAdvancedWin is double higherAdvancedWin ? F(higherAdvancedWin) : string.Empty' 'CP94 paired-review nullable formatting must retain the native-warning-safe single-evaluation pattern.'
Require-Contains $consumerText 'row.HigherAdvancedNeutralWin is double higherAdvancedNeutralWin ? F(higherAdvancedNeutralWin) : string.Empty' 'CP94 mover-neutral nullable formatting must retain the native-warning-safe single-evaluation pattern.'
$selfTests=Read-Text 'src/StarCluster.ScenarioRunner/ScenarioRunnerSelfTests.cs'
foreach($needle in @(
    'CP94 adaptive cross-TL quotas and information-control bands remain deterministic',
    'TestCp94AdaptiveCrossTlSampling','AllocateAdaptiveQuotasForSelfTest','InformationControlDistanceBandForSelfTest',
    'case-insensitive Sensor/EW catalog binding contract','population-cell keys must remain safe inside pipe-delimited profile-label metadata')){
    Require-Contains $selfTests $needle "ScenarioRunner self-tests are missing '$needle'."
}

Write-Host '       Validating standing suite v0.11, CP94 policy, and durable methodology...'
$suite=Read-Json 'docs/design/testing/technology_integration_permutation_suite_v0_11.json'
Assert-True ([string]$suite.id -eq 'technology-integration-permutation-suite-v0_11' -and [int]$suite.checkpoint -eq 94 -and [string]$suite.supersedesForCurrentPlanning -eq 'technology-integration-permutation-suite-v0_10') 'Standing suite v0.11 identity/supersession mismatch.'
$enum=$suite.legalBuildEnumeration
Assert-True ([string]$enum.schema -eq 'star-cluster-cross-tl-build-permutation-v5' -and [string]$enum.currentFoundation -eq $studyRel -and [int]$enum.currentLegalBuildCount -eq 22592 -and [int]$enum.exactFill35BuildCount -eq 4672 -and [long]$enum.unorderedDistinctPairingEnvelope -eq 255187936) 'Standing suite v0.11 legal-build envelope mismatch.'
$bounded=$enum.currentBoundedScreen
Assert-True ([int]$bounded.basePopulationCells -eq 96 -and [int]$bounded.statisticalUnorderedDistinctBasePairs -eq 192 -and [int]$bounded.statisticalLogicalPairings -eq 384 -and [int]$bounded.diversityUnorderedDistinctBasePairs -eq 24 -and [int]$bounded.diversityLogicalPairings -eq 48 -and [int]$bounded.namedLogicalPairings -eq 48 -and [int]$bounded.logicalPairings -eq 480 -and [int]$bounded.geometryCount -eq 3 -and [int]$bounded.generatedVariantCount -eq 1440 -and [int]$bounded.substantiveTrialsPerVariantAtCp94 -eq 1500 -and [int]$bounded.smokeTrialsPerVariant -eq 1) 'Standing suite v0.11 bounded-screen metrics mismatch.'
Assert-True ([int]$bounded.minimumStatisticalPairsPerCell -eq 1 -and [int]$bounded.maximumStatisticalPairsPerCell -eq 5 -and [double]$bounded.adaptiveAllocationExponent -eq 0.5 -and [int]$bounded.diversityOverlayTopPopulationCells -eq 12 -and [int]$bounded.diversityPairsPerSelectedCell -eq 2 -and [int]$bounded.diversityPopulationInferenceWeight -eq 0) 'Standing suite v0.11 adaptive/diversity settings mismatch.'
Require-Contains ([string]$suite.currentCoverage.combatActivityGuard) 'ready_geometry_reached_but_one_side_inactive' 'Standing suite v0.11 must retain the partial-activity diagnostic and side/family/context activity guard.'
$suiteText=Read-Text 'docs/design/testing/Technology_Integration_Permutation_Suite_Architecture_v0_11.md'
foreach($needle in @('22,592 legal','255,187,936','96 primary population cells','192 unordered distinct statistical base pairs','square root','maximum of five','24 diversity base pairs','zero population-inference weight','maximum ready range','movement_did_not_reach_mutual_ready_range','ready_geometry_reached_but_one_side_inactive','ready_geometry_reached_but_no_actions','mover-order-neutral','1,440 generated','2,160,000')){
    Require-Contains $suiteText $needle "Standing suite v0.11 narrative is missing semantic concept '$needle'."
}
$policy=Read-Json 'docs/design/testing/checkpoint_94_validation_suite_policy_v0_1.json'
Assert-True ([string]$policy.checkpoint -eq '94' -and [bool]$policy.mustAlwaysRun.crossTlGeneratorPreflight -and [bool]$policy.mustAlwaysRun.generatedStudyActualConsumerPreflight -and [bool]$policy.mustAlwaysRun.generatedStudyOneTrialSmoke -and [bool]$policy.mustAlwaysRun.boundedCrossTlPrimaryStudy) 'Checkpoint 94 validation policy must require the full changed-study consumer pipeline.'
$p=$policy.adaptiveScreen
Assert-True ([int]$p.populationCellCount -eq 96 -and [int]$p.statisticalBasePairBudget -eq 192 -and [int]$p.statisticalLogicalPairings -eq 384 -and [int]$p.diversityBasePairCount -eq 24 -and [int]$p.diversityLogicalPairings -eq 48 -and [int]$p.namedLogicalPairings -eq 48 -and [int]$p.logicalPairings -eq 480 -and [int]$p.generatedVariantCount -eq 1440 -and [int]$p.defaultTrialsPerVariant -eq 1500 -and [long]$p.defaultPrimaryTrials -eq 2160000 -and [int]$p.oneTrialSmokeExecutions -eq 1440 -and [long]$p.totalTrialExecutionsAtDefault -eq 2161440) 'Checkpoint 94 validation policy workload mismatch.'
Assert-True ([bool]$policy.populationAnalysis.statisticalWeightSplitWithinCell -and [long]$policy.populationAnalysis.statisticalForwardWeightMustRecoverUnorderedDistinctPopulation -eq 255187936 -and [int]$policy.populationAnalysis.diversityOverlayInferenceWeight -eq 0 -and [int]$policy.populationAnalysis.namedDiagnosticsInferenceWeight -eq 0 -and [bool]$policy.populationAnalysis.rawAndPopulationWeightedReports) 'Checkpoint 94 validation policy population-weight controls mismatch.'
Assert-True ([bool]$policy.readiness.exactMaximumReadyRangeReported -and [bool]$policy.readiness.movementDidNotReachMutualReadyRangeDiagnostic -and [bool]$policy.readiness.readyGeometryReachedButNoActionsBlockingForSubstantiveRun -and [bool]$policy.readiness.oneTrialSmokeZeroActionNotBalanceBlocking -and [bool]$policy.readiness.oneSideInactiveDiagnostic -and [bool]$policy.readiness.observedActiveRequiresBothSides) 'Checkpoint 94 validation policy readiness/activity controls mismatch.'
Assert-True ([bool]$policy.moverOrder.retainBothBounds -and [bool]$policy.moverOrder.neutralEstimate -and [bool]$policy.moverOrder.initiativeGapReported -and -not [bool]$policy.moverOrder.sensitivityIsGameplayGate) 'Checkpoint 94 validation policy mover-order controls mismatch.'
Assert-True ([bool]$policy.activityGuards.sideSpecificTelemetry -and [bool]$policy.activityGuards.aggregateTelemetryReconciliation -and [bool]$policy.activityGuards.individualMatchedDiagnostics -and [bool]$policy.activityGuards.familyAppropriateActions -and [bool]$policy.activityGuards.familyContextualGates -and [bool]$policy.activityGuards.readyGeometryReachedFilter -and [bool]$policy.activityGuards.movementDeniedExcludedFromBlockingCohort) 'Checkpoint 94 validation policy activity-guard controls mismatch.'
Assert-True (-not [bool]$policy.authorityBoundary.componentTuning -and -not [bool]$policy.authorityBoundary.gameplayRuleChanges -and -not [bool]$policy.authorityBoundary.aiDoctrineChanges -and -not [bool]$policy.authorityBoundary.technologyPromotion -and -not [bool]$policy.authorityBoundary.spacedockCandidatePromotion -and -not [bool]$policy.authorityBoundary.referenceMiningChanges -and -not [bool]$policy.authorityBoundary.automaticCandidatePromotion -and -not [bool]$policy.deepCalibration.applicable) 'Checkpoint 94 validation policy authority/deep-calibration boundary mismatch.'
$guidelines=Read-Text 'docs/development/Simulation_Development_Guidelines.md'
foreach($needle in @('number of statistical representatives inside important cells','deterministic, bounded','diagnostic diversity overlays','zero population-inference weight','maximum range','movement_did_not_reach_mutual_ready_range','mover-order-neutral matched estimate')){
    Require-Contains $guidelines $needle "Simulation Development Guidelines are missing durable CP94 methodology '$needle'."
}

Write-Host '       Validating active documentation authority, archives, and checkpoint hygiene...'
Assert-True (-not (Test-Path -LiteralPath (RelPath 'docs/checkpoints'))) 'The obsolete docs/checkpoints tree must remain absent.'
Assert-ExactFileSet 'docs/design/testing' @(
    'Checkpoint_94_Validation_Tiers.md','README.md','Technology_Integration_Permutation_Suite_Architecture_v0_11.md',
    'checkpoint_94_validation_suite_policy_v0_1.json','technology_integration_permutation_suite_v0_11.json')
$activeConcepts=@(Get-ChildItem -LiteralPath (RelPath 'docs') -File -Filter 'Star_Cluster_Game_Concept_v*.docx')
Assert-True ($activeConcepts.Count -eq 1 -and $activeConcepts[0].Name -eq 'Star_Cluster_Game_Concept_v0.6z.docx') 'Concept authority must remain exactly v0.6z.'
$activeValidation=@(Get-ChildItem -LiteralPath (RelPath 'docs/validation') -File -Filter 'Checkpoint_*.md')
Assert-True ($activeValidation.Count -eq 1 -and $activeValidation[0].Name -eq 'Checkpoint_94_Adaptive_Sampling_And_Mover_Neutral_Cross_TL_Screening.md') 'Exactly one active CP94 validation runbook must remain.'
$activeAi=@(Get-ChildItem -LiteralPath (RelPath 'docs/design/ai') -File -Filter 'AI_Doctrine_Registry_Architecture_v*.md')
Assert-True ($activeAi.Count -eq 1 -and $activeAi[0].Name -eq 'AI_Doctrine_Registry_Architecture_v0_5.md') 'Exactly one active AI Doctrine Architecture v0.5 must remain.'
$runbook=Read-Text 'docs/validation/Checkpoint_94_Adaptive_Sampling_And_Mover_Neutral_Cross_TL_Screening.md'
foreach($needle in @('Checkpoint 94','160adb4fee4fb419136916da0b99e7ebeb2f495c43513033fc93dd0852e970cb','b1653b049655961474518872286c6bb044d83bcf3d349c5ecdce0224f118baec','22,592','192 unordered statistical','24 diversity','480','1,440','2,160,000','2,161,440','does **not** change')){
    Require-Contains $runbook $needle "Checkpoint 94 runbook is missing semantic/provenance concept '$needle'."
}
Assert-True (-not [regex]::IsMatch($runbook,'[\x00-\x08\x0B\x0C\x0E-\x1F]')) 'Active Checkpoint 94 validation runbook contains unexpected ASCII control characters.'
Require-Contains $runbook '.\tools\checkpoints\checkpoint-94\apply_checkpoint_94.ps1 -RepositoryOnly' 'Checkpoint 94 runbook must contain the literal repository-only native command.'
$tiers=Read-Text 'docs/design/testing/Checkpoint_94_Validation_Tiers.md'
foreach($needle in @('58 expected','192 statistical','24 diversity','480 total logical','1,440 generated','2,160,000','2,161,440','Deep Calibration','not applicable','direct named-parameter')){ Require-Contains $tiers $needle "Checkpoint 94 validation tiers are missing semantic concept '$needle'." }
$rootReadme=Read-Text 'README.md'
foreach($needle in @('Checkpoint 94 Candidate','CP93 remains the latest accepted','192 unordered base pairs','24 additional unordered','1,440 actual-consumer variants','2,161,440','direct named','Spacedock')){ Require-Contains $rootReadme $needle "Root README is missing semantic concept '$needle'." }
$docsReadme=Read-Text 'docs/README.md'
foreach($needle in @('Technology_Integration_Permutation_Suite_Architecture_v0_11.md','Checkpoint_94_Adaptive_Sampling_And_Mover_Neutral_Cross_TL_Screening.md','Checkpoint 93 remains the latest native-accepted','Reference-mining material is **not** game authority')){ Require-Contains $docsReadme $needle "docs/README is missing semantic concept '$needle'." }
$chat=Read-Text 'CHAT_README.md'
foreach($needle in @('CP93','statistical-sample population','diagnostic diversity overlays','Escalate sample quality','exact ready geometry','mover-order bounds','side/family/context activity guards','proven direct named-parameter','full-repository archive','docs/references/reference-mining/README.md')){ Require-Contains $chat $needle "CHAT_README is missing durable guardrail '$needle'." }
$testingReadme=Read-Text 'docs/design/testing/README.md'
foreach($needle in @('checkpoint-94/apply_checkpoint_94.ps1','Technology_Integration_Permutation_Suite_Architecture_v0_11.md','cross-tl-build-permutation-foundation-v0_5.json','mover-order-neutral','zero population-inference weight')){ Require-Contains $testingReadme $needle "Testing README is missing semantic concept '$needle'." }

$rootTxt=@(Get-ChildItem -LiteralPath $repositoryRoot -File -Filter '*.txt')
Assert-True ($rootTxt.Count -eq 1 -and $rootTxt[0].Name -eq 'CHECKPOINT_94_SHA256SUMS.txt') 'Repository root must contain only CHECKPOINT_94_SHA256SUMS.txt as .txt.'
$rootManifest=Read-Manifest 'CHECKPOINT_94_SHA256SUMS.txt'
Assert-True (-not $rootManifest.Entries.ContainsKey('CHECKPOINT_94_SHA256SUMS.txt')) 'Checkpoint 94 root manifest must not contain itself.'
Assert-True ($rootManifest.EntryCount -eq 1848 -and $rootManifest.PhysicalLineCount -eq 1848) 'Checkpoint 94 root manifest must contain exactly 1,848 repository-owned file entries.'

Write-Host "Checkpoint 94 repository contracts passed ($frozenCount CP93 files frozen; $referenceCount accepted reference files byte-preserved; adaptive sampling/readiness/mover-neutral architecture locked)."
