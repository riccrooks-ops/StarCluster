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
function Assert-Sequence {
    param([object[]]$Actual,[string[]]$Expected,[string]$Message)
    Assert-True ($Actual.Count -eq $Expected.Count) $Message
    for($i=0;$i -lt $Expected.Count;$i++){ Assert-True ([string]$Actual[$i] -eq $Expected[$i]) $Message }
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

Write-Host '       Validating native-dependency declarations and proven wrapper interface...'
$guard=RelPath 'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1'
$normalRel='tools/calibration/checkpoints/checkpoint-96.json'
$deepRel='tools/calibration/checkpoints/checkpoint-96-deep-calibration.json'
$guardedPs=@(
    'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
    'tools/checkpoints/checkpoint-96/apply_checkpoint_96.ps1',
    'tools/checkpoints/checkpoint-96/test_checkpoint_96_contract.ps1',
    'tools/calibration/run_calibration_checkpoint.ps1'
)
& $guard -RepositoryRoot $repositoryRoot -PowerShellPaths $guardedPs -CheckpointDefinitionPaths @($normalRel,$deepRel)
$applyText=Read-Text 'tools/checkpoints/checkpoint-96/apply_checkpoint_96.ps1'
$provenHarnessCall='& $harness -CheckpointDefinition $definition -Trials $Trials -Jobs $Jobs -RepositoryOnly:$RepositoryOnly -NoClean:$NoClean'
Require-Contains $applyText $provenHarnessCall 'Checkpoint 96 wrapper must preserve the proven direct named-parameter harness invocation.'
Assert-True (-not [regex]::IsMatch($applyText,'&\s+\$harness\s+@[A-Za-z_][A-Za-z0-9_]*',[System.Text.RegularExpressions.RegexOptions]::IgnoreCase)) 'Checkpoint 96 wrapper must not invoke the calibration harness through splatted arguments.'

Write-Host '       Validating Checkpoint 96 definitions and exact accepted-CP95 replay...'
$normal=Read-Json $normalRel
$deep=Read-Json $deepRel
$expectedStageIds=@(
    'deterministic','tl1-phase-a','tl1-phase-b','tl1-installation-space-envelope','tl1-sensor-ew-foundation',
    'cross-tl-build-permutation-preflight','cross-tl-build-permutation-generation','cross-tl-generated-study-preflight',
    'cross-tl-generated-study-smoke','cross-tl-build-permutation-screening','auxiliary-resource-endurance',
    'checkpoint-53-resource-semantics-lock','runner-self-tests'
)
foreach($d in @($normal,$deep)){
    Assert-True ([string]$d.checkpointId -eq '96') 'Checkpoint 96 definition ID mismatch.'
    Assert-True ([string]$d.manifestFile -eq 'CHECKPOINT_96_SHA256SUMS.txt') 'Checkpoint 96 manifest binding mismatch.'
    Assert-True ([int]$d.defaultTrials -eq 1500 -and [int]$d.defaultJobs -eq 24) 'Checkpoint 96 default Trials/Jobs mismatch.'
    Assert-True (@($d.stages).Count -eq 13 -and [int]$d.checkpointMetrics.stageCount -eq 13) 'Checkpoint 96 must contain exactly 13 configured runner stages.'
    Assert-True ([int]$d.checkpointMetrics.monteCarloVariantCount -eq 1440 -and [long]$d.checkpointMetrics.trialsAtDefault -eq 2160000 -and [long]$d.checkpointMetrics.totalTrialExecutionsAtDefault -eq 2161440) 'Checkpoint 96 workload accounting mismatch.'
    Assert-True ([bool]$d.checkpointMetrics.cohortSemanticsClosure -and [bool]$d.checkpointMetrics.referenceContextReadinessSeparated -and [bool]$d.checkpointMetrics.observedReadyWindowSeparated -and [bool]$d.checkpointMetrics.runtimeBilateralActivitySeparated -and [bool]$d.checkpointMetrics.causalReplayOfCheckpoint95 -and [bool]$d.checkpointMetrics.broaderDevelopmentResumesAfterCheckpoint96 -and -not [bool]$d.checkpointMetrics.deepCalibrationApplicable) 'Checkpoint 96 cohort-semantics/closure metrics mismatch.'
    Assert-Sequence @($d.stages | ForEach-Object { [string]$_.id }) $expectedStageIds 'Checkpoint 96 configured runner-stage order drifted.'
    Assert-Sequence @($d.nativeDependencyPrecheck.powerShellPaths) $guardedPs 'Checkpoint 96 native-dependency PowerShell path list drifted.'
    Assert-Sequence @($d.nativeDependencyPrecheck.checkpointDefinitionPaths) @($normalRel,$deepRel) 'Checkpoint 96 native-dependency definition list drifted.'
    $self=@($d.stages | Where-Object { [string]$_.id -eq 'runner-self-tests' })
    Assert-True ($self.Count -eq 1 -and [int]$self[0].metrics.selfTestCount -eq 59) 'Checkpoint 96 must expect 59 ScenarioRunner self-tests.'
    $pre=@($d.stages | Where-Object { [string]$_.id -eq 'cross-tl-build-permutation-preflight' })
    $gen=@($d.stages | Where-Object { [string]$_.id -eq 'cross-tl-build-permutation-generation' })
    $screen=@($d.stages | Where-Object { [string]$_.id -eq 'cross-tl-build-permutation-screening' })
    Assert-True ([string]$pre[0].arguments[1] -eq 'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/cross-tl-build-permutation-foundation-v0_6.json') 'Checkpoint 96 must reuse accepted CP95 foundation v0.6 exactly.'
    Assert-True ([long]$gen[0].metrics.cp94PairSelectionSeedPreserved -eq 940177 -and [long]$gen[0].metrics.cp94CombatMasterSeedPreserved -eq 940100) 'Checkpoint 96 must preserve accepted pair-selection/combat seeds.'
    Assert-True ([int]$screen[0].metrics.variantCount -eq 1440 -and [bool]$screen[0].metrics.referenceContextReadinessReported -and [bool]$screen[0].metrics.observedReferenceReadyWindowReported -and [bool]$screen[0].metrics.runtimeBilateralActivityReported -and [bool]$screen[0].metrics.legacyCp95ObservedActiveCompatibilityCohort -and -not [bool]$screen[0].metrics.gameplayChangesExpected) 'Checkpoint 96 substantive cohort-reporting metrics mismatch.'
}

Write-Host '       Validating accepted Checkpoint 95 provenance and frozen baseline...'
$acceptedManifestRel='docs/validation/evidence/checkpoint-95/CHECKPOINT_95_SHA256SUMS.txt'
$acceptedManifest=Read-Manifest $acceptedManifestRel
Assert-True ($acceptedManifest.EntryCount -eq 1861 -and $acceptedManifest.PhysicalLineCount -eq 1861) 'Accepted Checkpoint 95 embedded manifest must contain exactly 1,861 entries.'
Assert-True ((Hash-Rel $acceptedManifestRel) -eq '3753fb2b41ff55027eef0bd37ba5ab2304f3022c67cd7fdda43da18041c3dcdf') 'Accepted Checkpoint 95 embedded manifest SHA-256 mismatch.'
$accepted=Read-Json 'docs/validation/evidence/checkpoint-95/checkpoint-95-native-acceptance-provenance.json'
Assert-True ([string]$accepted.checkpointId -eq '95' -and [string]$accepted.status -eq 'Success') 'Accepted Checkpoint 95 provenance status mismatch.'
Assert-True ([string]$accepted.checkpointDefinitionSha256 -eq 'de57c2069e7e20cf1fb8e4ec6af26f32f9d18df3fae4e758cbc5c406e7e091d3' -and [string]$accepted.checkpointManifestSha256 -eq '3753fb2b41ff55027eef0bd37ba5ab2304f3022c67cd7fdda43da18041c3dcdf') 'Accepted Checkpoint 95 hash provenance mismatch.'
Assert-True ([string]$accepted.sourceResultsArchiveSha256 -eq 'dcbe31976263bb70a8ba3c04a67a08452471d619989356f4ff6931de17b29026' -and [string]$accepted.acceptedRepositoryArchiveSha256 -eq 'df057daf4d431b104447032d905628ba902b758b2b0efbd8c5e8d66c0a7f94d2') 'Accepted Checkpoint 95 archive provenance mismatch.'
Assert-True ([int]$accepted.tests.total -eq 863 -and [int]$accepted.tests.passed -eq 863 -and [int]$accepted.aggregates.runnerStagesPassed -eq 13 -and [int]$accepted.aggregates.selfTests -eq 59 -and [int]$accepted.aggregates.failedGates -eq 0) 'Accepted Checkpoint 95 native acceptance metrics mismatch.'

$mutable=@{}
foreach($p in @(
    'CHAT_README.md','README.md','docs/README.md','docs/design/testing/README.md','docs/development/Simulation_Development_Guidelines.md',
    'src/StarCluster.ScenarioRunner/ScenarioRunnerSelfTests.cs',
    'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs',
    'docs/design/testing/Checkpoint_95_Validation_Tiers.md',
    'docs/design/testing/checkpoint_95_validation_suite_policy_v0_1.json',
    'docs/validation/Checkpoint_95_Post_Movement_Readiness_Instrumentation_Hardening.md'
)){ $mutable[$p]=$true }
$frozenCount=0
foreach($entry in $acceptedManifest.Entries.GetEnumerator()){
    $rel=[string]$entry.Key
    if($mutable.ContainsKey($rel)){ continue }
    Assert-True (Test-Path -LiteralPath (RelPath $rel) -PathType Leaf) "Accepted CP95 frozen file '$rel' is missing."
    Assert-True ((Hash-Rel $rel) -eq [string]$entry.Value) "Accepted CP95 frozen file '$rel' changed unexpectedly."
    $frozenCount++
}
Assert-True ($frozenCount -eq 1851) "Checkpoint 96 expected 1,851 frozen CP95 files; observed $frozenCount."
# Removed active CP95 authorities must be archived byte-identically.
$archivePairs=@(
    @('docs/design/testing/Checkpoint_95_Validation_Tiers.md','docs/archive/testing/Checkpoint_95_Validation_Tiers.md'),
    @('docs/design/testing/checkpoint_95_validation_suite_policy_v0_1.json','docs/archive/testing/checkpoint_95_validation_suite_policy_v0_1.json'),
    @('docs/validation/Checkpoint_95_Post_Movement_Readiness_Instrumentation_Hardening.md','docs/validation/archive/Checkpoint_95_Post_Movement_Readiness_Instrumentation_Hardening.md')
)
foreach($pair in $archivePairs){
    $old=[string]$pair[0]; $arch=[string]$pair[1]
    Assert-True ($acceptedManifest.Entries.ContainsKey($old)) "Accepted CP95 manifest lacks '$old'."
    Assert-True ((Hash-Rel $arch) -eq [string]$acceptedManifest.Entries[$old]) "Archived CP95 authority '$arch' is not byte-identical to accepted '$old'."
}
$referenceCount=0
foreach($entry in $acceptedManifest.Entries.GetEnumerator()){
    $rel=[string]$entry.Key
    if($rel.StartsWith('docs/references/',[System.StringComparison]::OrdinalIgnoreCase)){
        Assert-True ((Hash-Rel $rel) -eq [string]$entry.Value) "Accepted reference file '$rel' changed."
        $referenceCount++
    }
}
Assert-True ($referenceCount -eq 81) "Expected 81 accepted reference files; observed $referenceCount."

Write-Host '       Validating CP96 reporting semantics and causal non-interference...'
$consumer=Read-Text 'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs'
foreach($needle in @(
    'CrossTlObservedReferenceReadyWindow','CrossTlRuntimeBilateralActive','CrossTlReferenceRuntimeRelation',
    'reference_context_mutual_ready','observed_reference_ready_window','runtime_bilateral_active','legacy_cp95_reference_expected_runtime_active',
    'reference_not_expected_runtime_active','reference_expected_runtime_inactive',
    'cross-tl-cp96-paired-review.csv','cross-tl-cp96-population-weighted-review.csv','cross-tl-cp96-activity-review.csv',
    'cross-tl-cp96-mover-neutral-review.csv','cross-tl-cp96-mover-neutral-summary.csv','cross-tl-cp96-outlier-review.csv',
    'reference_not_expected_runtime_bilateral_active')){
    Require-Contains $consumer $needle "Integrated combat consumer is missing CP96 reporting contract '$needle'."
}
Require-NotContains $consumer 'Path.Combine(outputDirectory, "cross-tl-cp95-paired-review.csv")' 'CP96 must emit CP96 paired review filename.'
Require-Contains $consumer 'text = $"paired|{variant.ComparisonGroup}";' 'CP96 causal replay requires paired combat RNG salt to remain comparison-group based rather than variant-ID based.'
$selfTests=Read-Text 'src/StarCluster.ScenarioRunner/ScenarioRunnerSelfTests.cs'
foreach($needle in @('CP96 readiness cohorts separate reference context','CP96 observed firing-window readiness','CP96 runtime bilateral activity','reference-context false-negative')){ Require-Contains $selfTests $needle "ScenarioRunner self-tests are missing CP96 regression '$needle'." }

Write-Host '       Validating CP96 policy, durable methodology, and active authority hygiene...'
$policy=Read-Json 'docs/design/testing/checkpoint_96_validation_suite_policy_v0_1.json'
Assert-True ([string]$policy.checkpoint -eq '96' -and [bool]$policy.cohortSemantics.referenceContextMutualReady -and [bool]$policy.cohortSemantics.observedReferenceReadyWindow -and [bool]$policy.cohortSemantics.runtimeBilateralActive -and [bool]$policy.cohortSemantics.runtimeBilateralActivityIndependentOfReferenceEstimate -and [string]$policy.cohortSemantics.legacyCp95ObservedActiveCompatibilityName -eq 'legacy_cp95_reference_expected_runtime_active' -and [bool]$policy.completionBoundary.broaderMechanicsAndTechnologyWorkResumesNext -and -not [bool]$policy.authorityBoundary.gameplayRuleChanges -and -not [bool]$policy.deepCalibration.applicable) 'Checkpoint 96 policy semantics/authority boundary mismatch.'
$review=Read-Json 'docs/validation/evidence/checkpoint-95/cp95-readiness-cohort-review.json'
Assert-True ([int]$review.dynamicReferenceFalseNegativeBundleCount -eq 4) 'CP95 embedded cohort review must retain four weighted dynamic reference false-negative bundles.'
$dyn=$review.geometryMetrics.'dynamic-a-first'
Assert-True ([math]::Abs([double]$dyn.referenceContextMutualReadyPopulationPercent - 84.37154870048403) -lt 0.0000001) 'CP95 reference-context mutual-ready evidence drifted.'
Assert-True ([math]::Abs([double]$dyn.observedReferenceReadyWindowPopulationPercent - 56.57622046312827) -lt 0.0000001) 'CP95 observed reference-ready-window evidence drifted.'
Assert-True ([math]::Abs([double]$dyn.legacyCp95ObservedActivePopulationPercent - 58.72712778501672) -lt 0.0000001) 'CP95 legacy observed-active evidence drifted.'
Assert-True ([math]::Abs([double]$dyn.runtimeBilateralActivePopulationPercent - 60.64837704553557) -lt 0.0000001) 'CP95 runtime-bilateral-active evidence drifted.'
$guidelines=Read-Text 'docs/development/Simulation_Development_Guidelines.md'
foreach($needle in @('three observables separate','reference-context mutual readiness','observed reference-ready firing-window reach','true runtime bilateral activity','false negative of the screening estimate')){ Require-Contains $guidelines $needle "Simulation Development Guidelines are missing CP96 durable methodology '$needle'." }
Assert-ExactFileSet 'docs/design/testing' @('Checkpoint_96_Validation_Tiers.md','README.md','Technology_Integration_Permutation_Suite_Architecture_v0_12.md','checkpoint_96_validation_suite_policy_v0_1.json','technology_integration_permutation_suite_v0_12.json')
$activeValidation=@(Get-ChildItem -LiteralPath (RelPath 'docs/validation') -File -Filter 'Checkpoint_*.md')
Assert-True ($activeValidation.Count -eq 1 -and $activeValidation[0].Name -eq 'Checkpoint_96_Readiness_Cohort_Semantics_Closure.md') 'Exactly one active CP96 validation runbook must remain.'
$runbook=Read-Text 'docs/validation/Checkpoint_96_Readiness_Cohort_Semantics_Closure.md'
foreach($needle in @('de57c2069e7e20cf1fb8e4ec6af26f32f9d18df3fae4e758cbc5c406e7e091d3','3753fb2b41ff55027eef0bd37ba5ab2304f3022c67cd7fdda43da18041c3dcdf','940177','940100','reference_context_mutual_ready','observed_reference_ready_window','runtime_bilateral_active','2,160,000','59 ScenarioRunner','resume broader Star Cluster development')){ Require-Contains $runbook $needle "CP96 runbook is missing '$needle'." }
$rootReadme=Read-Text 'README.md'; foreach($needle in @('Checkpoint 96 Candidate','CP95 remains the latest accepted','v0.12','v0.6','2,161,440','59 ScenarioRunner','broader overall game mechanics')){ Require-Contains $rootReadme $needle "Root README is missing '$needle'." }
$chat=Read-Text 'CHAT_README.md'; foreach($needle in @('CP95','reference-context readiness','runtime bilateral activity','CP96 is the planned closure')){ Require-Contains $chat $needle "CHAT_README is missing CP96 bootstrap guardrail '$needle'." }

$rootTxt=@(Get-ChildItem -LiteralPath $repositoryRoot -File -Filter '*.txt')
Assert-True ($rootTxt.Count -eq 1 -and $rootTxt[0].Name -eq 'CHECKPOINT_96_SHA256SUMS.txt') 'Repository root must contain only CHECKPOINT_96_SHA256SUMS.txt as .txt.'
$rootManifest=Read-Manifest 'CHECKPOINT_96_SHA256SUMS.txt'
Assert-True (-not $rootManifest.Entries.ContainsKey('CHECKPOINT_96_SHA256SUMS.txt')) 'Checkpoint 96 root manifest must not contain itself.'
Assert-True ($rootManifest.EntryCount -eq 1871 -and $rootManifest.PhysicalLineCount -eq 1871) 'Checkpoint 96 root manifest entry count mismatch.'

Write-Host "Checkpoint 96 repository contracts passed ($frozenCount CP95 files frozen; $referenceCount accepted reference files byte-preserved; readiness-cohort semantics closure locked)."
