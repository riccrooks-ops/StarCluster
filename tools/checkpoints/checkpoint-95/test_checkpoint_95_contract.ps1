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
    for($i=0;$i -lt $Expected.Count;$i++){ Assert-True ([string]$Actual[$i] -eq $Expected[$i]) $Message }
}

Write-Host '       Validating native-dependency declarations and proven wrapper interface...'
$guard=RelPath 'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1'
$normalRel='tools/calibration/checkpoints/checkpoint-95.json'
$deepRel='tools/calibration/checkpoints/checkpoint-95-deep-calibration.json'
$guardedPs=@(
    'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
    'tools/checkpoints/checkpoint-95/apply_checkpoint_95.ps1',
    'tools/checkpoints/checkpoint-95/test_checkpoint_95_contract.ps1',
    'tools/calibration/run_calibration_checkpoint.ps1'
)
& $guard -RepositoryRoot $repositoryRoot -PowerShellPaths $guardedPs -CheckpointDefinitionPaths @($normalRel,$deepRel)
$applyText=Read-Text 'tools/checkpoints/checkpoint-95/apply_checkpoint_95.ps1'
$provenHarnessCall='& $harness -CheckpointDefinition $definition -Trials $Trials -Jobs $Jobs -RepositoryOnly:$RepositoryOnly -NoClean:$NoClean'
Require-Contains $applyText $provenHarnessCall 'Checkpoint 95 wrapper must preserve the proven direct named-parameter harness invocation.'
Assert-True (-not [regex]::IsMatch($applyText,'&\s+\$harness\s+@[A-Za-z_][A-Za-z0-9_]*',[System.Text.RegularExpressions.RegexOptions]::IgnoreCase)) 'Checkpoint 95 wrapper must not invoke the calibration harness through splatted arguments.'

Write-Host '       Validating Checkpoint 95 definitions and exact CP94 causal replay...'
$normal=Read-Json $normalRel
$deep=Read-Json $deepRel
$expectedStageIds=@(
    'deterministic','tl1-phase-a','tl1-phase-b','tl1-installation-space-envelope','tl1-sensor-ew-foundation',
    'cross-tl-build-permutation-preflight','cross-tl-build-permutation-generation','cross-tl-generated-study-preflight',
    'cross-tl-generated-study-smoke','cross-tl-build-permutation-screening','auxiliary-resource-endurance',
    'checkpoint-53-resource-semantics-lock','runner-self-tests'
)
foreach($d in @($normal,$deep)){
    Assert-True ([string]$d.checkpointId -eq '95') 'Checkpoint 95 definition ID mismatch.'
    Assert-True ([string]$d.manifestFile -eq 'CHECKPOINT_95_SHA256SUMS.txt') 'Checkpoint 95 manifest binding mismatch.'
    Assert-True ([int]$d.defaultTrials -eq 1500 -and [int]$d.defaultJobs -eq 24) 'Checkpoint 95 default Trials/Jobs mismatch.'
    Assert-True (@($d.stages).Count -eq 13 -and [int]$d.checkpointMetrics.stageCount -eq 13) 'Checkpoint 95 must contain exactly 13 configured runner stages.'
    Assert-True ([int]$d.checkpointMetrics.monteCarloVariantCount -eq 1440 -and [long]$d.checkpointMetrics.trialsAtDefault -eq 2160000) 'Checkpoint 95 substantive workload accounting mismatch.'
    Assert-True ([int]$d.checkpointMetrics.smokeVariantExecutions -eq 1440 -and [long]$d.checkpointMetrics.totalTrialExecutionsAtDefault -eq 2161440) 'Checkpoint 95 smoke/total workload accounting mismatch.'
    Assert-True ([bool]$d.checkpointMetrics.instrumentationHardening -and [bool]$d.checkpointMetrics.postMovementReadinessTelemetry -and [bool]$d.checkpointMetrics.causalReplayOfCheckpoint94 -and -not [bool]$d.checkpointMetrics.deepCalibrationApplicable) 'Checkpoint 95 must remain an instrumentation-hardening causal replay with Deep Calibration not applicable.'
    Assert-Sequence @($d.stages | ForEach-Object { [string]$_.id }) $expectedStageIds 'Checkpoint 95 configured runner-stage order drifted.'
    Assert-Sequence @($d.nativeDependencyPrecheck.powerShellPaths) $guardedPs 'Checkpoint 95 native-dependency PowerShell path list drifted.'
    Assert-Sequence @($d.nativeDependencyPrecheck.checkpointDefinitionPaths) @($normalRel,$deepRel) 'Checkpoint 95 native-dependency definition list drifted.'
    $self=@($d.stages | Where-Object { [string]$_.id -eq 'runner-self-tests' })
    Assert-True ($self.Count -eq 1 -and [int]$self[0].metrics.selfTestCount -eq 59) 'Checkpoint 95 must expect 59 ScenarioRunner self-tests.'
    $pre=@($d.stages | Where-Object { [string]$_.id -eq 'cross-tl-build-permutation-preflight' })
    $gen=@($d.stages | Where-Object { [string]$_.id -eq 'cross-tl-build-permutation-generation' })
    $screen=@($d.stages | Where-Object { [string]$_.id -eq 'cross-tl-build-permutation-screening' })
    Assert-True ([string]$pre[0].arguments[1] -eq 'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/cross-tl-build-permutation-foundation-v0_6.json') 'Checkpoint 95 preflight must bind foundation v0.6.'
    Assert-True ([bool]$pre[0].metrics.explicitRuntimeReadinessMetadata -and [bool]$pre[0].metrics.postMovementFiringWindowTelemetry -and [bool]$pre[0].metrics.pathClosestApproachSeparated) 'Checkpoint 95 preflight instrumentation metrics mismatch.'
    Assert-True ([long]$gen[0].metrics.cp94PairSelectionSeedPreserved -eq 940177 -and [long]$gen[0].metrics.cp94CombatMasterSeedPreserved -eq 940100) 'Checkpoint 95 must preserve CP94 selection/combat seeds.'
    Assert-True ([int]$screen[0].metrics.variantCount -eq 1440 -and [bool]$screen[0].metrics.postMovementFiringWindowTelemetry -and [bool]$screen[0].metrics.consolidatedOutlierReview -and -not [bool]$screen[0].metrics.gameplayChangesExpected) 'Checkpoint 95 substantive instrumentation metrics mismatch.'
}

Write-Host '       Validating accepted Checkpoint 94 provenance and frozen baseline...'
$acceptedManifestRel='docs/validation/evidence/checkpoint-94/CHECKPOINT_94_SHA256SUMS.txt'
$acceptedManifest=Read-Manifest $acceptedManifestRel
Assert-True ($acceptedManifest.EntryCount -eq 1848 -and $acceptedManifest.PhysicalLineCount -eq 1848) 'Accepted Checkpoint 94 embedded manifest must contain exactly 1,848 entries.'
Assert-True ((Hash-Rel $acceptedManifestRel) -eq '10003c7bdc8ee167ec2ab02d547de87fe2dec7293e03872f96a61dbca64c763a') 'Accepted Checkpoint 94 embedded manifest SHA-256 mismatch.'
$accepted=Read-Json 'docs/validation/evidence/checkpoint-94/checkpoint-94-native-acceptance-provenance.json'
Assert-True ([string]$accepted.checkpointId -eq '94' -and [string]$accepted.status -eq 'Success') 'Accepted Checkpoint 94 provenance status mismatch.'
Assert-True ([string]$accepted.sdk.expected -eq '8.0.423' -and [string]$accepted.sdk.actual -eq '8.0.423') 'Accepted Checkpoint 94 SDK provenance mismatch.'
Assert-True ([bool]$accepted.build.succeeded -and [int]$accepted.build.warnings -eq 0 -and [int]$accepted.build.errors -eq 0) 'Accepted Checkpoint 94 build provenance mismatch.'
Assert-True ([int]$accepted.tests.total -eq 863 -and [int]$accepted.tests.passed -eq 863 -and [int]$accepted.tests.failed -eq 0 -and [int]$accepted.tests.skipped -eq 0) 'Accepted Checkpoint 94 test provenance mismatch.'
Assert-True ([int]$accepted.aggregates.configuredRunnerStages -eq 13 -and [int]$accepted.aggregates.runnerStagesPassed -eq 13 -and [int]$accepted.aggregates.selfTests -eq 58 -and [int]$accepted.aggregates.failedGates -eq 0) 'Accepted Checkpoint 94 runner provenance mismatch.'
Assert-True ([int]$accepted.primaryStudy.variantCount -eq 1440 -and [int]$accepted.primaryStudy.trialsPerVariant -eq 1500 -and [long]$accepted.primaryStudy.totalTrials -eq 2160000) 'Accepted Checkpoint 94 substantive-study provenance mismatch.'
Assert-True ([string]$accepted.checkpointDefinitionSha256 -eq 'a121176b8525827ebbd7335b0f89a83d2bef9a6c194ef06a277b5a63335920f1' -and [string]$accepted.checkpointManifestSha256 -eq '10003c7bdc8ee167ec2ab02d547de87fe2dec7293e03872f96a61dbca64c763a') 'Accepted Checkpoint 94 hash provenance mismatch.'
$review=Read-Json 'docs/validation/evidence/checkpoint-94/cp94-instrumentation-review.json'
Assert-True ([string]$review.representativeAcceptedResult.variant_id -eq 'c94-1061-dynamic-a-first' -and [string]$review.representativeAcceptedResult.observed_engagement_diagnosis -eq 'ready_geometry_reached_but_one_side_inactive') 'CP94 instrumentation-review evidence must retain the representative accepted misclassification pattern.'

$allowedAcceptedChanges=@(
    'CHAT_README.md','README.md','docs/README.md',
    'docs/design/player_technology/Technology_Architecture_Matrix_v1.md',
    'docs/archive/player_technology/pre-cp165-active/technology_architecture_matrix_v1.json',
    'docs/design/testing/README.md','docs/development/Simulation_Development_Guidelines.md',
    'src/StarCluster.ScenarioRunner/CrossTlIntegration/CrossTlBuildPermutationRunner.cs',
    'src/StarCluster.ScenarioRunner/ScenarioRunnerSelfTests.cs',
    'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatDocuments.cs',
    'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs',
    'docs/design/testing/Checkpoint_94_Validation_Tiers.md',
    'docs/design/testing/Technology_Integration_Permutation_Suite_Architecture_v0_11.md',
    'docs/design/testing/checkpoint_94_validation_suite_policy_v0_1.json',
    'docs/design/testing/technology_integration_permutation_suite_v0_11.json',
    'docs/validation/Checkpoint_94_Adaptive_Sampling_And_Mover_Neutral_Cross_TL_Screening.md'
)
$allowedSet=@{}; foreach($rel in $allowedAcceptedChanges){ $allowedSet[$rel]=$true }
$frozenCount=0
foreach($rel in $acceptedManifest.Entries.Keys){
    if ($allowedSet.ContainsKey($rel)) { continue }
    $p=RelPath $rel
    Assert-True (Test-Path -LiteralPath $p -PathType Leaf) "Checkpoint 95 unexpectedly removed accepted CP94 file '$rel'."
    $actual=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()
    Assert-True ($actual -eq [string]$acceptedManifest.Entries[$rel]) "Checkpoint 95 unexpectedly changed accepted CP94 file '$rel'."
    $frozenCount++
}
Assert-True ($frozenCount -eq 1832) "Checkpoint 95 must byte-freeze exactly 1,832 accepted CP94 paths outside its 16-path change/move allowlist; observed $frozenCount."
$archiveMap=@{
    'docs/design/testing/Checkpoint_94_Validation_Tiers.md'='docs/archive/testing/Checkpoint_94_Validation_Tiers.md';
    'docs/design/testing/Technology_Integration_Permutation_Suite_Architecture_v0_11.md'='docs/archive/testing/Technology_Integration_Permutation_Suite_Architecture_v0_11.md';
    'docs/design/testing/checkpoint_94_validation_suite_policy_v0_1.json'='docs/archive/testing/checkpoint_94_validation_suite_policy_v0_1.json';
    'docs/design/testing/technology_integration_permutation_suite_v0_11.json'='docs/archive/testing/technology_integration_permutation_suite_v0_11.json';
    'docs/validation/Checkpoint_94_Adaptive_Sampling_And_Mover_Neutral_Cross_TL_Screening.md'='docs/validation/archive/Checkpoint_94_Adaptive_Sampling_And_Mover_Neutral_Cross_TL_Screening.md'
}
foreach($old in $archiveMap.Keys){
    $archived=[string]$archiveMap[$old]
    Assert-True (-not (Test-Path -LiteralPath (RelPath $old) -PathType Leaf)) "Superseded CP94 active file '$old' must not remain active."
    Assert-True ((Hash-Rel $archived) -eq [string]$acceptedManifest.Entries[$old]) "Archived CP94 file '$archived' must be byte-identical to accepted '$old'."
}
$referenceCount=0
foreach($rel in $acceptedManifest.Entries.Keys){
    if (-not $rel.StartsWith('docs/references/',[System.StringComparison]::Ordinal)) { continue }
    Assert-True ((Hash-Rel $rel) -eq [string]$acceptedManifest.Entries[$rel]) "Checkpoint 95 must byte-preserve accepted reference file '$rel'."
    $referenceCount++
}
Assert-True ($referenceCount -eq 81) "Checkpoint 95 must byte-preserve exactly 81 accepted CP94 reference files; observed $referenceCount."

Write-Host '       Validating foundation v0.6, explicit readiness metadata, and post-Movement telemetry...'
$study=Read-Json 'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/cross-tl-build-permutation-foundation-v0_6.json'
Assert-True ([string]$study.schemaVersion -eq 'star-cluster-cross-tl-build-permutation-v5' -and [string]$study.id -eq 'cross-tl-build-permutation-foundation-v0_6' -and [string]$study.checkpoint -eq '95') 'Cross-TL foundation v0.6 identity mismatch.'
Assert-True ([string]$study.variantIdPrefix -eq 'c95' -and [long]$study.masterSeed -eq 940100 -and [long]$study.stratifiedPairingSelection.seed -eq 940177 -and [int]$study.trialsPerVariant -eq 1500) 'CP95 foundation must preserve CP94 combat/selection seeds and trials.'
Assert-True ([int]$study.expectedLegalBuildCount -eq 22592 -and [long]$study.expectedUnorderedDistinctPairingEnvelope -eq 255187936 -and [int]$study.expectedGeneratedVariantCount -eq 1440 -and [int]$study.stratifiedPairingSelection.expectedBasePairCount -eq 192 -and [int]$study.stratifiedPairingSelection.expectedDiversityBasePairCount -eq 24) 'CP95 foundation must preserve the accepted CP94 legal/sampling envelope.'
$documents=Read-Text 'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatDocuments.cs'
foreach($needle in @('sideAEngagementReadinessClass','sideBEngagementReadinessClass','sideAMaximumReadyRangeHexes','sideBMaximumReadyRangeHexes')){ Require-Contains $documents $needle "Runtime variant document is missing '$needle'." }
$generator=Read-Text 'src/StarCluster.ScenarioRunner/CrossTlIntegration/CrossTlBuildPermutationRunner.cs'
foreach($needle in @('SideAEngagementReadinessClass = pairing.SideAReadiness','SideBEngagementReadinessClass = pairing.SideBReadiness','SideAMaximumReadyRangeHexes = pairing.SideAMaximumReadyRangeHexes','generated-runtime-readiness-metadata-complete')){ Require-Contains $generator $needle "Cross-TL generator is missing CP95 runtime readiness contract '$needle'." }
$consumer=Read-Text 'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs'
foreach($needle in @(
    'minimumPostMovementRange','postMovementFiringWindows','postMovementReadyWindowsA','postMovementReadyWindowsB','postMovementReadyWindowsMutual',
    'PostMovementReadyTrialsPercentA','PostMovementReadyTrialsPercentB','PostMovementReadyTrialsPercentMutual',
    'PostMovementReadyWindowReached','RuntimeActionOutsideStructuralReadyEstimate','cross-tl-cp95-explicit-readiness-metadata','cross-tl-cp95-firing-window-telemetry','cross-tl-cp95-runtime-action-vs-structural-readiness-review',
    'cross-tl-cp95-fixed-reference-firing-window-observed','cross-tl-cp95-contextual-combat-activity','cross-tl-cp95-individual-observed-engagement',
    'fixed_reference_ready_geometry_not_observed','movement_did_not_reach_mutual_ready_range','ready_geometry_reached_but_one_side_inactive','ready_geometry_reached_but_no_actions',
    'cross-tl-cp95-paired-review.csv','cross-tl-cp95-population-weighted-review.csv','cross-tl-cp95-activity-review.csv',
    'cross-tl-cp95-mover-neutral-review.csv','cross-tl-cp95-mover-neutral-summary.csv','cross-tl-cp95-outlier-review.csv',
    'mean_path_closest_approach_range','mean_minimum_post_movement_range','post_movement_ready_trials_percent_mutual','runtime_action_outside_structural_ready_estimate','side_a_action_outside_structural_ready_estimate','side_b_action_outside_structural_ready_estimate')){
    Require-Contains $consumer $needle "Integrated combat consumer is missing CP95 instrumentation contract '$needle'."
}
Assert-True ([regex]::IsMatch($consumer,'minimumRange\s*=\s*Math\.Min\(\s*minimumRange\s*,\s*Math\.Min\(\s*moveA\.ClosestApproachHexes\s*,\s*moveB\.ClosestApproachHexes\s*\)\s*\)\s*;',[System.Text.RegularExpressions.RegexOptions]::IgnoreCase)) 'CP95 must preserve movement-path closest-approach telemetry as a distinct diagnostic.'
Require-NotContains $consumer 'meanMinimumRange > mutualReadyRange' 'CP95 observed-engagement diagnosis must not infer post-Movement ready geometry from path minimum range.'
Require-NotContains $consumer 'cross-tl-cp94-activity-review.csv' 'CP95 active consumer must emit CP95 review filenames.'
Require-Contains $consumer 'text = $"paired|{variant.ComparisonGroup}";' 'CP95 causal replay requires paired combat RNG salt to remain comparison-group based rather than variant-ID based.'
$selfTests=Read-Text 'src/StarCluster.ScenarioRunner/ScenarioRunnerSelfTests.cs'
foreach($needle in @('CP95 post-Movement readiness telemetry ignores movement-path closest approach','TestCp95PostMovementReadinessTelemetry','fixed-reference readiness must fail explicitly','runtime action outside the static structural ready-range estimate as review telemetry')){ Require-Contains $selfTests $needle "ScenarioRunner self-tests are missing CP95 regression '$needle'." }

Write-Host '       Validating standing suite v0.12, CP95 policy, and durable methodology...'
$suite=Read-Json 'docs/design/testing/technology_integration_permutation_suite_v0_12.json'
Assert-True ([string]$suite.id -eq 'technology-integration-permutation-suite-v0_12' -and [int]$suite.checkpoint -eq 95 -and [string]$suite.supersedesForCurrentPlanning -eq 'technology-integration-permutation-suite-v0_11') 'Standing suite v0.12 identity mismatch.'
Assert-True ([string]$suite.legalBuildEnumeration.currentFoundation -eq 'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/cross-tl-build-permutation-foundation-v0_6.json' -and [int]$suite.legalBuildEnumeration.currentBoundedScreen.generatedVariantCount -eq 1440) 'Standing suite v0.12 foundation/workload mismatch.'
$bounded=$suite.legalBuildEnumeration.currentBoundedScreen
Assert-True ([bool]$bounded.postMovementFiringWindowTelemetry -and [bool]$bounded.pathClosestApproachReportedSeparately -and [bool]$bounded.sideSpecificReadyWindowTrialPercent -and [bool]$bounded.explicitRuntimeReadinessMetadata -and [bool]$bounded.consolidatedOutlierReview -and [long]$bounded.cp94PairSelectionSeedPreserved -eq 940177 -and [long]$bounded.cp94CombatMasterSeedPreserved -eq 940100) 'Standing suite v0.12 instrumentation/causal-replay controls mismatch.'
$policy=Read-Json 'docs/design/testing/checkpoint_95_validation_suite_policy_v0_1.json'
Assert-True ([string]$policy.checkpoint -eq '95' -and [bool]$policy.readiness.postMovementFiringWindowTelemetry -and [bool]$policy.readiness.pathClosestApproachSeparate -and [bool]$policy.readiness.explicitRuntimeReadinessMetadata -and [bool]$policy.activityGuards.consolidatedOutlierReview -and -not [bool]$policy.activityGuards.actionsRequireObservedReadyWindow -and [bool]$policy.activityGuards.runtimeActionOutsideStructuralReadyEstimateReviewOnly -and -not [bool]$policy.authorityBoundary.gameplayRuleChanges -and -not [bool]$policy.deepCalibration.applicable) 'Checkpoint 95 validation policy instrumentation/authority boundary mismatch.'
$guidelines=Read-Text 'docs/development/Simulation_Development_Guidelines.md'
foreach($needle in @('Movement-path closest approach and final post-Movement combat geometry are different telemetry','per-trial firing-window geometry','profile labels are provenance','outlier review queue')){ Require-Contains $guidelines $needle "Simulation Development Guidelines are missing CP95 durable methodology '$needle'." }
$matrixMd=Read-Text 'docs/design/player_technology/Technology_Architecture_Matrix_v1.md'
Require-Contains $matrixMd 'standing suite v0.12 and cross-TL foundation v0.6' 'Technology Matrix current integration pointer is stale.'
$matrix=Read-Json 'docs/archive/player_technology/pre-cp165-active/technology_architecture_matrix_v1.json'
Assert-True ([string]$matrix.integrationCoverage.standingPermutationSuite -eq 'v0.12' -and [string]$matrix.integrationCoverage.crossTlBuildFoundation -eq 'v0.6' -and [int]$matrix.integrationCoverage.boundedCombatScreenVariants -eq 1440) 'Technology Matrix machine integration pointer is stale.'

Write-Host '       Validating active documentation authority, archives, and checkpoint hygiene...'
Assert-ExactFileSet 'docs/design/testing' @('Checkpoint_95_Validation_Tiers.md','README.md','Technology_Integration_Permutation_Suite_Architecture_v0_12.md','checkpoint_95_validation_suite_policy_v0_1.json','technology_integration_permutation_suite_v0_12.json')
$activeValidation=@(Get-ChildItem -LiteralPath (RelPath 'docs/validation') -File -Filter 'Checkpoint_*.md')
Assert-True ($activeValidation.Count -eq 1 -and $activeValidation[0].Name -eq 'Checkpoint_95_Post_Movement_Readiness_Instrumentation_Hardening.md') 'Exactly one active CP95 validation runbook must remain.'
$runbook=Read-Text 'docs/validation/Checkpoint_95_Post_Movement_Readiness_Instrumentation_Hardening.md'
foreach($needle in @('a121176b8525827ebbd7335b0f89a83d2bef9a6c194ef06a277b5a63335920f1','10003c7bdc8ee167ec2ab02d547de87fe2dec7293e03872f96a61dbca64c763a','940177','940100','movement-path closest approach','post-Movement','cross-tl-cp95-outlier-review.csv','2,160,000','59 ScenarioRunner')){ Require-Contains $runbook $needle "CP95 runbook is missing '$needle'." }
$rootReadme=Read-Text 'README.md'; foreach($needle in @('Checkpoint 95 Candidate','CP94 remains the latest accepted','v0.12','v0.6','2,161,440','59 ScenarioRunner')){ Require-Contains $rootReadme $needle "Root README is missing '$needle'." }
$chat=Read-Text 'CHAT_README.md'; foreach($needle in @('CP94','movement-path closest approach','post-Movement firing-window geometry')){ Require-Contains $chat $needle "CHAT_README is missing CP95 bootstrap guardrail '$needle'." }

$rootTxt=@(Get-ChildItem -LiteralPath $repositoryRoot -File -Filter '*.txt')
Assert-True ($rootTxt.Count -eq 1 -and $rootTxt[0].Name -eq 'CHECKPOINT_95_SHA256SUMS.txt') 'Repository root must contain only CHECKPOINT_95_SHA256SUMS.txt as .txt.'
$rootManifest=Read-Manifest 'CHECKPOINT_95_SHA256SUMS.txt'
Assert-True (-not $rootManifest.Entries.ContainsKey('CHECKPOINT_95_SHA256SUMS.txt')) 'Checkpoint 95 root manifest must not contain itself.'
Assert-True ($rootManifest.EntryCount -eq 1861 -and $rootManifest.PhysicalLineCount -eq 1861) 'Checkpoint 95 root manifest entry count mismatch.'

Write-Host "Checkpoint 95 repository contracts passed ($frozenCount CP94 files frozen; $referenceCount accepted reference files byte-preserved; post-Movement readiness instrumentation/outlier architecture locked)."
