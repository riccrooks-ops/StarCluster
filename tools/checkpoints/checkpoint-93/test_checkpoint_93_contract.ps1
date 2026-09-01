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
function Get-Axis {
    param($Study,[string]$Id)
    $matches=@($Study.axes | Where-Object { [string]$_.id -eq $Id })
    Assert-True ($matches.Count -eq 1) "Cross-TL foundation must contain exactly one '$Id' axis."
    return $matches[0]
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
$normalRel='tools/calibration/checkpoints/checkpoint-93.json'
$deepRel='tools/calibration/checkpoints/checkpoint-93-deep-calibration.json'
$guardedPs=@(
    'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
    'tools/checkpoints/checkpoint-93/apply_checkpoint_93.ps1',
    'tools/checkpoints/checkpoint-93/test_checkpoint_93_contract.ps1',
    'tools/calibration/run_calibration_checkpoint.ps1'
)
& $guard -RepositoryRoot $repositoryRoot -PowerShellPaths $guardedPs -CheckpointDefinitionPaths @($normalRel,$deepRel)
$applyText=Read-Text 'tools/checkpoints/checkpoint-93/apply_checkpoint_93.ps1'
$provenHarnessCall='& $harness -CheckpointDefinition $definition -Trials $Trials -Jobs $Jobs -RepositoryOnly:$RepositoryOnly -NoClean:$NoClean'
Require-Contains $applyText $provenHarnessCall 'Checkpoint 93 wrapper must preserve the proven direct named-parameter harness invocation.'
Assert-True (-not [regex]::IsMatch($applyText,'&\s+\$harness\s+@[A-Za-z_][A-Za-z0-9_]*',[System.Text.RegularExpressions.RegexOptions]::IgnoreCase)) 'Checkpoint 93 wrapper must not invoke the calibration harness through splatted arguments.'
$guardText=Read-Text 'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1'
Require-Contains $guardText 'Assert-ProvenCheckpointHarnessInvocation' 'Native dependency/archive precheck must continue validating the checkpoint-wrapper harness interface.'
Require-Contains $guardText 'array splatting can silently become positional binding' 'Native dependency/archive precheck must retain the array-splat positional-binding failure explanation.'

Write-Host '       Validating Checkpoint 93 definitions and bounded workload accounting...'
$normal=Read-Json $normalRel
$deep=Read-Json $deepRel
foreach($d in @($normal,$deep)){
    Assert-True ([string]$d.checkpointId -eq '93') 'Checkpoint 93 definition ID mismatch.'
    Assert-True ([string]$d.manifestFile -eq 'CHECKPOINT_93_SHA256SUMS.txt') 'Checkpoint 93 manifest binding mismatch.'
    Assert-True ([int]$d.defaultTrials -eq 2000 -and [int]$d.defaultJobs -eq 24) 'Checkpoint 93 default Trials/Jobs mismatch.'
    Assert-True (@($d.stages).Count -eq 13 -and [int]$d.checkpointMetrics.stageCount -eq 13) 'Checkpoint 93 must contain exactly 13 configured runner stages.'
    Assert-True ([int]$d.checkpointMetrics.monteCarloVariantCount -eq 720 -and [long]$d.checkpointMetrics.trialsAtDefault -eq 1440000) 'Checkpoint 93 substantive workload accounting mismatch.'
    Assert-True ([int]$d.checkpointMetrics.smokeVariantExecutions -eq 720 -and [long]$d.checkpointMetrics.smokeTrialsAtDefault -eq 720 -and [long]$d.checkpointMetrics.totalTrialExecutionsAtDefault -eq 1440720) 'Checkpoint 93 smoke/total workload accounting mismatch.'
    Assert-True ([bool]$d.checkpointMetrics.architectureHardening -and [bool]$d.checkpointMetrics.boundedRepresentativeStudy -and -not [bool]$d.checkpointMetrics.deepCalibrationApplicable) 'Checkpoint 93 must remain a bounded architecture-hardening study with Deep Calibration not applicable.'
    Assert-True ([string]$d.primaryStudy.id -eq 'tl2-itc16-cross-tl-matched-readiness-space-screening' -and [int]$d.primaryStudy.variantCount -eq 720) 'Checkpoint 93 primary-study metadata mismatch.'
    $ids=@($d.stages | ForEach-Object { [string]$_.id })
    foreach($id in @('deterministic','tl1-phase-a','tl1-phase-b','tl1-installation-space-envelope','tl1-sensor-ew-foundation','cross-tl-build-permutation-preflight','cross-tl-build-permutation-generation','cross-tl-generated-study-preflight','cross-tl-generated-study-smoke','cross-tl-build-permutation-screening','auxiliary-resource-endurance','checkpoint-53-resource-semantics-lock','runner-self-tests')){
        Assert-True ($ids -contains $id) "Checkpoint 93 is missing stage '$id'."
    }
    $self=@($d.stages | Where-Object { [string]$_.id -eq 'runner-self-tests' })
    Assert-True ($self.Count -eq 1 -and [int]$self[0].metrics.selfTestCount -eq 57) 'Checkpoint 93 must expect 57 ScenarioRunner self-tests.'
    $pre=@($d.stages | Where-Object { [string]$_.id -eq 'cross-tl-build-permutation-preflight' })
    $gen=@($d.stages | Where-Object { [string]$_.id -eq 'cross-tl-build-permutation-generation' })
    $consumer=@($d.stages | Where-Object { [string]$_.id -eq 'cross-tl-generated-study-preflight' })
    $smoke=@($d.stages | Where-Object { [string]$_.id -eq 'cross-tl-generated-study-smoke' })
    $screen=@($d.stages | Where-Object { [string]$_.id -eq 'cross-tl-build-permutation-screening' })
    Assert-True ($pre.Count -eq 1 -and $gen.Count -eq 1 -and $consumer.Count -eq 1 -and $smoke.Count -eq 1 -and $screen.Count -eq 1) 'Checkpoint 93 cross-TL stage multiplicity mismatch.'
    Assert-True ([string]$pre[0].arguments[1] -eq 'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/cross-tl-build-permutation-foundation-v0_4.json') 'Checkpoint 93 preflight must bind foundation v0.4.'
    Assert-True ([int]$pre[0].metrics.legalBuildCount -eq 22592 -and [int]$pre[0].metrics.basePopulationCellCount -eq 96 -and [int]$pre[0].metrics.generatedVariantCount -eq 720) 'Checkpoint 93 preflight metrics mismatch.'
    Assert-True ([int]$gen[0].metrics.sampledUnorderedBasePairCount -eq 96 -and [int]$gen[0].metrics.stratifiedLogicalPairingCount -eq 192 -and [int]$gen[0].metrics.logicalPairingCount -eq 240 -and [bool]$gen[0].metrics.matchedBidirectional -and [bool]$gen[0].metrics.populationCoverageOutput) 'Checkpoint 93 generator matched/population metrics mismatch.'
    Assert-True ([int]$consumer[0].metrics.variantCount -eq 720 -and [bool]$consumer[0].metrics.actualConsumerDeserializer -and [bool]$consumer[0].metrics.sideSpecificActivityTelemetry -and [bool]$consumer[0].metrics.contextualCombatActivityGatePresent) 'Checkpoint 93 generated-study actual-consumer preflight metrics mismatch.'
    Assert-True ([int]$smoke[0].metrics.variantCount -eq 720 -and [int]$smoke[0].metrics.trialsPerVariant -eq 1 -and [int]$smoke[0].metrics.totalSmokeTrials -eq 720 -and [bool]$smoke[0].metrics.fullPipelineExecution) 'Checkpoint 93 one-trial smoke metrics mismatch.'
    Assert-True ([int]$screen[0].metrics.variantCount -eq 720 -and [string]$screen[0].metrics.standingPermutationSuite -eq 'v0.10' -and [bool]$screen[0].metrics.contextualCombatActivityGate -and [bool]$screen[0].metrics.populationWeightedReporting -and [bool]$screen[0].metrics.allLegalAndActiveCombatReporting -and -not [bool]$screen[0].metrics.automaticCandidatePromotion) 'Checkpoint 93 substantive screen metrics mismatch.'
}
Assert-True ([string]$deep.title -like '*Deep Calibration Alias*') 'Checkpoint 93 Deep Calibration definition must identify itself as the bounded alias.'

Write-Host '       Validating accepted Checkpoint 92 provenance and frozen baseline...'
$cp92ManifestRel='docs/validation/evidence/checkpoint-92/CHECKPOINT_92_SHA256SUMS.txt'
$cp92Record=Read-Manifest $cp92ManifestRel
Assert-True ([int]$cp92Record.PhysicalLineCount -eq 1824 -and [int]$cp92Record.EntryCount -eq 1824) 'Embedded accepted CP92 evidence manifest must contain exactly 1,824 unique entries.'
Assert-True ((Hash-Rel $cp92ManifestRel) -eq 'fda73ad40d9f122dff1036bdadc874c30de67454ec89232810707ec53075f31b') 'Embedded CP92 evidence manifest bytes do not match the accepted CP92 repository manifest.'
$prov=Read-Json 'docs/validation/evidence/checkpoint-92/checkpoint-92-native-acceptance-provenance.json'
Assert-True ([string]$prov.checkpointId -eq '92' -and [string]$prov.status -eq 'Success') 'Embedded CP92 native provenance identity/status mismatch.'
Assert-True ([string]$prov.sdk.expected -eq '8.0.423' -and [string]$prov.sdk.actual -eq '8.0.423' -and [bool]$prov.build.succeeded -and [int]$prov.build.warnings -eq 0 -and [int]$prov.build.errors -eq 0) 'Embedded CP92 SDK/build provenance mismatch.'
Assert-True ([int]$prov.tests.total -eq 863 -and [int]$prov.tests.passed -eq 863 -and [int]$prov.tests.failed -eq 0 -and [int]$prov.tests.skipped -eq 0) 'Embedded CP92 unit-test provenance mismatch.'
Assert-True ([int]$prov.runner.configuredStages -eq 8 -and [int]$prov.runner.passedStages -eq 8 -and [int]$prov.runner.failedStages -eq 0 -and [int]$prov.runner.selfTests -eq 56 -and [int]$prov.runner.failedGates -eq 0) 'Embedded CP92 runner provenance mismatch.'
Assert-True ([string]$prov.checkpointDefinitionSha256 -eq '070b9e46446e68a4aaeb74773d9f9d9000618c119c8294f37567de9a6dae3ea1' -and [string]$prov.repositoryManifestSha256 -eq 'fda73ad40d9f122dff1036bdadc874c30de67454ec89232810707ec53075f31b') 'Embedded CP92 accepted hashes mismatch.'

$cp92=$cp92Record.Entries
$mutableCp92Paths=@(
    'CHAT_README.md',
    'README.md',
    'docs/README.md',
    'docs/design/testing/README.md',
    'docs/development/Simulation_Development_Guidelines.md',
    'src/StarCluster.ScenarioRunner/CrossTlIntegration/CrossTlBuildPermutationRunner.cs',
    'src/StarCluster.ScenarioRunner/ScenarioRunnerSelfTests.cs',
    'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs',
    'docs/design/testing/Checkpoint_92_Validation_Tiers.md',
    'docs/design/testing/Technology_Integration_Permutation_Suite_Architecture_v0_9.md',
    'docs/design/testing/checkpoint_92_validation_suite_policy_v0_1.json',
    'docs/design/testing/technology_integration_permutation_suite_v0_9.json',
    'docs/validation/Checkpoint_92_Expanded_Spacedock_Reference_Corpus_And_Completed_Queue.md'
)
$frozenCount=0
foreach($rel in @($cp92.Keys)){
    if ($mutableCp92Paths -contains $rel) { continue }
    Assert-True (Test-Path -LiteralPath (RelPath $rel) -PathType Leaf) "Checkpoint 93 removed frozen accepted CP92 file '$rel'."
    Assert-True ((Hash-Rel $rel) -eq [string]$cp92[$rel]) "Checkpoint 93 changed frozen accepted CP92 file '$rel'."
    $frozenCount++
}
Assert-True ($frozenCount -gt 1800) "Checkpoint 93 frozen CP92 audit unexpectedly covered only $frozenCount files."

foreach($pair in @(
    @('docs/archive/testing/Checkpoint_92_Validation_Tiers.md','docs/design/testing/Checkpoint_92_Validation_Tiers.md'),
    @('docs/archive/testing/Technology_Integration_Permutation_Suite_Architecture_v0_9.md','docs/design/testing/Technology_Integration_Permutation_Suite_Architecture_v0_9.md'),
    @('docs/archive/testing/checkpoint_92_validation_suite_policy_v0_1.json','docs/design/testing/checkpoint_92_validation_suite_policy_v0_1.json'),
    @('docs/archive/testing/technology_integration_permutation_suite_v0_9.json','docs/design/testing/technology_integration_permutation_suite_v0_9.json'),
    @('docs/validation/archive/Checkpoint_92_Expanded_Spacedock_Reference_Corpus_And_Completed_Queue.md','docs/validation/Checkpoint_92_Expanded_Spacedock_Reference_Corpus_And_Completed_Queue.md')
)){
    $archiveRel=[string]$pair[0]; $acceptedRel=[string]$pair[1]
    Assert-True ((Hash-Rel $archiveRel) -eq [string]$cp92[$acceptedRel]) "Archived CP92 artifact '$archiveRel' is not byte-identical to accepted '$acceptedRel'."
}

$referenceCount=0
foreach($rel in @($cp92.Keys | Where-Object { $_.StartsWith('docs/references/',[System.StringComparison]::Ordinal) })){
    Assert-True ((Hash-Rel $rel) -eq [string]$cp92[$rel]) "Checkpoint 93 changed accepted CP92 reference/reference-mining file '$rel'."
    $referenceCount++
}
Assert-True ($referenceCount -gt 40) "Checkpoint 93 CP92 reference-corpus freeze unexpectedly covered only $referenceCount files."

Write-Host '       Validating cross-TL foundation v0.4 and complete legal-envelope accounting...'
$studyRel='src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/cross-tl-build-permutation-foundation-v0_4.json'
$study=Read-Json $studyRel
Assert-True ([string]$study.schemaVersion -eq 'star-cluster-cross-tl-build-permutation-v4' -and [string]$study.id -eq 'cross-tl-build-permutation-foundation-v0_4' -and [string]$study.checkpoint -eq '93') 'Cross-TL foundation v0.4 identity/schema mismatch.'
Assert-True ([string]$study.generatedStudyId -eq 'tl2-itc16-cross-tl-matched-readiness-space-screening' -and [string]$study.variantIdPrefix -eq 'c93' -and [uint64]$study.masterSeed -eq 930100 -and [int]$study.trialsPerVariant -eq 2000) 'Cross-TL v0.4 generated-study identity/seed/trials mismatch.'
Assert-True ([int]$study.totalInstallationSpace -eq 35 -and [int]$study.fixedShellSpace -eq 10 -and [int]$study.fixedShell.stlDriveSpace -eq 5 -and [int]$study.fixedShell.ftlDriveSpace -eq 5 -and [int]$study.fixedShell.kineticPdsSpace -eq 0) 'Cross-TL v0.4 fixed shell/Installation Space mismatch.'
$g=$study.constructionGuardrails
Assert-True ([int]$g.minimumMainWeaponCount -eq 1 -and [int]$g.minimumReactorCount -eq 1 -and [bool]$g.additionalMainWeaponsOptional -and [bool]$g.additionalReactorsOptional -and [bool]$g.duplicationMustBeExplicit) 'Cross-TL v0.4 mandatory-core/optional-duplication guardrails mismatch.'
Assert-True ([bool]$g.redundantEwInstallationsAllowed -and -not [bool]$g.ecmSameTypeRatingsAdditive -and -not [bool]$g.eccmSameTypeRatingsAdditive -and [string]$g.ewDuplicateResolution -eq 'highest_applicable_functional_rating' -and -not [bool]$g.powerSufficiencyIsConstructionLegalityFilter) 'Cross-TL v0.4 EW/power construction guardrails mismatch.'
$axisCounts=@{}
foreach($id in @('weapon','reactor','computer','sensor','shield','armor','ecm','eccm','pds')){ $axisCounts[$id]=@((Get-Axis $study $id).options).Count }
Assert-True ($axisCounts['weapon'] -eq 8 -and $axisCounts['reactor'] -eq 4 -and $axisCounts['computer'] -eq 2 -and $axisCounts['sensor'] -eq 3 -and $axisCounts['shield'] -eq 3 -and $axisCounts['armor'] -eq 2 -and $axisCounts['ecm'] -eq 6 -and $axisCounts['eccm'] -eq 6 -and $axisCounts['pds'] -eq 2) 'Cross-TL v0.4 axis-option counts mismatch.'
$raw=[long]1; foreach($id in @('weapon','reactor','computer','sensor','shield','armor','ecm','eccm','pds')){ $raw=$raw * [long]$axisCounts[$id] }
Assert-True ($raw -eq 82944 -and [long]$study.expectedRawCombinationCount -eq 82944 -and [int]$study.expectedLegalBuildCount -eq 22592) 'Cross-TL v0.4 raw/legal build accounting mismatch.'
Assert-True ([int]$study.expectedExactFillBuildCount -eq 4672 -and [int]$study.expectedNearFillBuildCount -eq 11328 -and [int]$study.expectedUnderfilledBuildCount -eq 6592) 'Cross-TL v0.4 Space-utilization counts mismatch.'
Assert-True ([long]$study.expectedOrientedPairingEnvelope -eq 510398464 -and [long]$study.expectedUnorderedWithSelfPairingEnvelope -eq 255210528 -and [long]$study.expectedOrientedDistinctPairingEnvelope -eq 510375872 -and [long]$study.expectedUnorderedDistinctPairingEnvelope -eq 255187936) 'Cross-TL v0.4 pairing-envelope accounting mismatch.'
Assert-True (@($study.namedRecipes).Count -eq 20 -and [int]$study.expectedNamedRecipeCount -eq 20 -and [int]$study.expectedNamedLogicalPairingCount -eq 48) 'Cross-TL v0.4 named recipe/pairing counts mismatch.'
$pairingTotal=0; foreach($pg in @($study.pairingGroups)){ $pairingTotal += @($pg.sideARecipes).Count * @($pg.sideBRecipes).Count }
Assert-True ($pairingTotal -eq 48) 'Cross-TL v0.4 pairing-group expansion must produce exactly 48 named logical pairings.'
Assert-True (@($study.geometries).Count -eq 3 -and [int]$study.expectedGeometryCount -eq 3 -and [int]$study.expectedGeneratedVariantCount -eq 720) 'Cross-TL v0.4 geometry/generated-variant accounting mismatch.'
$sel=$study.stratifiedPairingSelection
Assert-True ([bool]$sel.enabled -and [uint64]$sel.seed -eq 930177 -and [int]$sel.targetPerCell -eq 1 -and [int]$sel.expectedBasePairCount -eq 96 -and [int]$sel.expectedSampleCount -eq 192 -and [int]$sel.maxAttempts -eq 500000 -and [bool]$sel.matchedBidirectional) 'Cross-TL v0.4 matched-sampling settings mismatch.'
Assert-True ([int]$sel.nearDistanceMaximum -eq 2 -and [int]$sel.equalLowAdvancedMaximum -eq 3 -and [int]$sel.nearFillMinimumUsedSpace -eq 32) 'Cross-TL v0.4 progression/Space thresholds mismatch.'
Assert-Sequence @($sel.compositionClasses) @('single-no-ew-redundancy','ew-redundancy','weapon-reactor-duplication','combined-duplication') 'Cross-TL v0.4 composition classes/order mismatch.'
Assert-Sequence @($sel.progressionMagnitudeStrata) @('equal_low','equal_high','near','far') 'Cross-TL v0.4 progression-magnitude strata/order mismatch.'
Assert-Sequence @($sel.spaceUtilizationClasses) @('exact_fill','near_fill','underfilled') 'Cross-TL v0.4 Space-utilization classes/order mismatch.'
Assert-Sequence @($sel.spacePairStrata) @('exact_fill-exact_fill','exact_fill-near_fill','exact_fill-underfilled','near_fill-near_fill','near_fill-underfilled','underfilled-underfilled') 'Cross-TL v0.4 Space-pair strata/order mismatch.'
Assert-True ((@($sel.compositionClasses).Count * @($sel.progressionMagnitudeStrata).Count * @($sel.spacePairStrata).Count) -eq 96 -and [int]$study.expectedStratifiedLogicalPairingCount -eq 192 -and [int]$study.expectedLogicalPairingCount -eq 240) 'Cross-TL v0.4 96-cell / 192-mirrored / 240-logical accounting mismatch.'
$studyText=Read-Text $studyRel
Require-NotContains $studyText 'technologyScore' 'Cross-TL v0.4 must not introduce a scalar universal technology score.'

Write-Host '       Validating CP93 runtime integration, side-specific telemetry, and review routing...'
$builder=Read-Text 'src/StarCluster.ScenarioRunner/CrossTlIntegration/CrossTlBuildPermutationRunner.cs'
foreach($needle in @('SchemaVersionV4','SelectMatchedStratifiedPairings','DeserializeSensorEwFoundationCatalog','BuildPopulationCells','EngagementReadinessClass','SensorEwFoundationResolver.Evaluate','sensorEwCatalogOptions.PropertyNameCaseInsensitive = true','Sensor/EW profile catalog candidates could not be bound','reference_ready','closing_ready','engagement_denied','population-coverage.csv','population-coverage-summary.json','PopulationUnorderedDistinctCount','InformationControlAdvancedCount','SpaceUtilizationClassForSelfTest','ProgressionMagnitudeStratumForSelfTest','SpacePairStratumForSelfTest','SensorEwCatalogCandidateCountForSelfTest','PopulationCellKeyForSelfTest')){
    Require-Contains $builder $needle "Cross-TL v0.4 runner is missing '$needle'."
}
Require-NotContains $builder 'TechnologyScore' 'Cross-TL runtime must not introduce a scalar TechnologyScore.'
Require-NotContains $builder 'File.ReadAllText(study.SensorEwProfileCatalog), JsonOptions()' 'Cross-TL readiness must not regress to the strict local serializer for the established camelCase Sensor/EW catalog.'
$combat=Read-Text 'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs'
foreach($needle in @('tl2-itc16-cross-tl-matched-readiness-space-screening','RequiredCrossTlMatchedReadinessSpaceScreeningVariantCount = 720','RecordDirectAction("A"','RecordDirectAction("B"','RecordMissileLaunch("A"','RecordMissileLaunch("B"','MeanDirectActionOpportunitiesA','MeanDirectActionOpportunitiesB','MeanMissileLaunchesA','MeanMissileLaunchesB','cross-tl-cp93-side-specific-activity-telemetry','cross-tl-cp93-contextual-combat-activity','cross-tl-cp93-paired-review.csv','cross-tl-cp93-population-weighted-review.csv','cross-tl-cp93-activity-review.csv','WriteCrossTlMatchedReadinessSpaceReview')){
    Require-Contains $combat $needle "CP93 combat consumer is missing '$needle'."
}
Require-Contains $combat 'study.Id == CrossTlMatchedReadinessSpaceScreeningStudyId' 'CP93 combat consumer must explicitly dispatch/validate the new study ID.'
Require-Contains $combat 'engagement-denied variants' 'CP93 global attack-layer telemetry gate must explicitly preserve structurally denied all-legal variants.'
$selfTests=Read-Text 'src/StarCluster.ScenarioRunner/ScenarioRunnerSelfTests.cs'
Require-Contains $selfTests 'TestCp93MatchedCrossTlStrata' 'ScenarioRunner self-tests must include CP93 matched/Space/progression arithmetic coverage.'
Require-Contains $selfTests '255187936L' 'ScenarioRunner CP93 self-test must lock unordered-distinct envelope arithmetic.'
Require-Contains $selfTests 'case-insensitive Sensor/EW catalog binding contract' 'ScenarioRunner CP93 self-test must lock the proven camelCase Sensor/EW catalog binding contract.'
Require-Contains $selfTests 'population-cell keys must remain safe inside pipe-delimited profile-label metadata' 'ScenarioRunner CP93 self-test must prevent population-cell keys from corrupting pipe-delimited profile-label metadata.'

Write-Host '       Validating standing suite v0.10, CP93 policy, and durable methodology...'
$suite=Read-Json 'docs/design/testing/technology_integration_permutation_suite_v0_10.json'
Assert-True ([string]$suite.id -eq 'technology-integration-permutation-suite-v0_10' -and [int]$suite.checkpoint -eq 93 -and [string]$suite.supersedesForCurrentPlanning -eq 'technology-integration-permutation-suite-v0_9') 'Standing suite v0.10 identity/supersession mismatch.'
$enum=$suite.legalBuildEnumeration
Assert-True ([string]$enum.schema -eq 'star-cluster-cross-tl-build-permutation-v4' -and [string]$enum.currentFoundation -eq $studyRel -and [int]$enum.currentLegalBuildCount -eq 22592 -and [int]$enum.exactFill35BuildCount -eq 4672 -and [int]$enum.nearFill32To34BuildCount -eq 11328 -and [int]$enum.underfilled31OrLessBuildCount -eq 6592 -and [long]$enum.unorderedDistinctPairingEnvelope -eq 255187936) 'Standing suite v0.10 legal-build envelope mismatch.'
$bounded=$enum.currentBoundedScreen
Assert-True ([int]$bounded.basePopulationCells -eq 96 -and [int]$bounded.sampledUnorderedDistinctBasePairs -eq 96 -and [bool]$bounded.matchedBidirectional -and [int]$bounded.stratifiedLogicalPairings -eq 192 -and [int]$bounded.namedLogicalPairings -eq 48 -and [int]$bounded.logicalPairings -eq 240 -and [int]$bounded.geometryCount -eq 3 -and [int]$bounded.generatedVariantCount -eq 720 -and [int]$bounded.substantiveTrialsPerVariantAtCp93 -eq 2000 -and [int]$bounded.smokeTrialsPerVariant -eq 1) 'Standing suite v0.10 bounded-screen metrics mismatch.'
Assert-Sequence @($bounded.readinessClasses) @('reference_ready','closing_ready','engagement_denied') 'Standing suite v0.10 readiness-class list mismatch.'
$suiteText=Read-Text 'docs/design/testing/Technology_Integration_Permutation_Suite_Architecture_v0_10.md'
foreach($needle in @('structural engagement readiness','observed activity','matched','both orientations','4,672 exact-fill','11,328 near-fill','6,592 underfilled','255,187,936 unordered distinct','population-weighted','No scalar universal','2,000 substantive trials','1,440,000')){
    Require-Contains $suiteText $needle "Standing suite v0.10 narrative is missing '$needle'."
}
# Keep narrative validation semantic rather than binding the contract to one exact sentence construction.
Require-Contains $suiteText 'one sampled pair' "Standing suite v0.10 narrative must state the limitation of a single sampled pair."
Require-Contains $suiteText 'exhaustive' "Standing suite v0.10 narrative must state that a single sampled pair is not exhaustive of its population cell."
$policy=Read-Json 'docs/design/testing/checkpoint_93_validation_suite_policy_v0_1.json'
Assert-True ([string]$policy.checkpoint -eq '93' -and [bool]$policy.mustAlwaysRun.crossTlGeneratorPreflight -and [bool]$policy.mustAlwaysRun.generatedStudyActualConsumerPreflight -and [bool]$policy.mustAlwaysRun.generatedStudyOneTrialSmoke -and [bool]$policy.mustAlwaysRun.boundedCrossTlPrimaryStudy) 'Checkpoint 93 validation policy must require the full changed-study consumer pipeline.'
Assert-True ([int]$policy.matchedScreen.populationCellCount -eq 96 -and [int]$policy.matchedScreen.generatedVariantCount -eq 720 -and [int]$policy.matchedScreen.defaultTrialsPerVariant -eq 2000 -and [int]$policy.matchedScreen.defaultPrimaryTrials -eq 1440000 -and [int]$policy.matchedScreen.oneTrialSmokeExecutions -eq 720) 'Checkpoint 93 validation policy workload mismatch.'
Assert-True ([bool]$policy.readiness.separateFromObservedActivity -and [bool]$policy.populationAnalysis.populationCountsAnalytical -and [bool]$policy.populationAnalysis.rawAndPopulationWeightedReports -and [bool]$policy.activityGuards.sideSpecificTelemetry -and [bool]$policy.activityGuards.familyContextualGates) 'Checkpoint 93 validation policy analysis controls mismatch.'
Assert-True (-not [bool]$policy.authorityBoundary.componentTuning -and -not [bool]$policy.authorityBoundary.gameplayRuleChanges -and -not [bool]$policy.authorityBoundary.aiDoctrineChanges -and -not [bool]$policy.authorityBoundary.spacedockCandidatePromotion -and -not [bool]$policy.authorityBoundary.automaticCandidatePromotion -and -not [bool]$policy.deepCalibration.applicable) 'Checkpoint 93 validation policy authority/deep-calibration boundary mismatch.'
$guidelines=Read-Text 'docs/development/Simulation_Development_Guidelines.md'
foreach($needle in @('Matched screening, readiness, and population accounting','structural engagement readiness','observed runtime activity','both A-vs-B and B-vs-A orientations','Space-utilization','population-weighted screening estimates','universal scalar technology score','side-specific')){
    Require-Contains $guidelines $needle "Simulation Development Guidelines are missing durable CP93 rule '$needle'."
}

Write-Host '       Validating active documentation authority, archives, and checkpoint hygiene...'
Assert-True (-not (Test-Path -LiteralPath (RelPath 'docs/checkpoints'))) 'The obsolete docs/checkpoints tree must remain absent.'
Assert-ExactFileSet 'docs/design/testing' @('Checkpoint_93_Validation_Tiers.md','README.md','Technology_Integration_Permutation_Suite_Architecture_v0_10.md','checkpoint_93_validation_suite_policy_v0_1.json','technology_integration_permutation_suite_v0_10.json')
$activeConcepts=@(Get-ChildItem -LiteralPath (RelPath 'docs') -File -Filter 'Star_Cluster_Game_Concept_v*.docx')
Assert-True ($activeConcepts.Count -eq 1 -and $activeConcepts[0].Name -eq 'Star_Cluster_Game_Concept_v0.6z.docx') 'Concept authority must remain exactly v0.6z.'
$activeValidation=@(Get-ChildItem -LiteralPath (RelPath 'docs/validation') -File -Filter 'Checkpoint_*.md')
Assert-True ($activeValidation.Count -eq 1 -and $activeValidation[0].Name -eq 'Checkpoint_93_Matched_Readiness_Space_And_Population_Weighted_Cross_TL_Screening.md') 'Exactly one active CP93 validation runbook must remain.'
$activeAi=@(Get-ChildItem -LiteralPath (RelPath 'docs/design/ai') -File -Filter 'AI_Doctrine_Registry_Architecture_v*.md')
Assert-True ($activeAi.Count -eq 1 -and $activeAi[0].Name -eq 'AI_Doctrine_Registry_Architecture_v0_5.md') 'Exactly one active AI Doctrine Architecture v0.5 must remain.'
$runbook=Read-Text 'docs/validation/Checkpoint_93_Matched_Readiness_Space_And_Population_Weighted_Cross_TL_Screening.md'
foreach($needle in @('Checkpoint 93','070b9e46446e68a4aaeb74773d9f9d9000618c119c8294f37567de9a6dae3ea1','fda73ad40d9f122dff1036bdadc874c30de67454ec89232810707ec53075f31b','22,592','96 cells','720 actual-consumer variants','1,440,000','Spacedock','does **not** change')){
    Require-Contains $runbook $needle "Checkpoint 93 runbook is missing '$needle'."
}
Assert-True (-not [regex]::IsMatch($runbook,'[\x00-\x08\x0B\x0C\x0E-\x1F]')) 'Active Checkpoint 93 validation runbook contains unexpected ASCII control characters.'
Require-Contains $runbook '.\tools\checkpoints\checkpoint-93\apply_checkpoint_93.ps1 -RepositoryOnly' 'Checkpoint 93 runbook must contain the literal repository-only native command.'
$tiers=Read-Text 'docs/design/testing/Checkpoint_93_Validation_Tiers.md'
foreach($needle in @('57 expected','720 generated variants','1,440,000','Deep Calibration','not applicable','direct named-parameter')){ Require-Contains $tiers $needle "Checkpoint 93 validation tiers are missing '$needle'." }
$rootReadme=Read-Text 'README.md'
foreach($needle in @('Checkpoint 93 Candidate','CP92 remains the latest accepted','82,944 raw / 22,592 legal','96 unordered sampled base pairs','1,440,000','direct named','Spacedock')){ Require-Contains $rootReadme $needle "Root README is missing '$needle'." }
$docsReadme=Read-Text 'docs/README.md'
foreach($needle in @('Technology_Integration_Permutation_Suite_Architecture_v0_10.md','Checkpoint_93_Matched_Readiness_Space_And_Population_Weighted_Cross_TL_Screening.md','Checkpoint 92 remains the latest native-accepted','Reference-mining material is **not** game authority')){ Require-Contains $docsReadme $needle "docs/README is missing '$needle'." }
$chat=Read-Text 'CHAT_README.md'
foreach($needle in @('CP92','structural engagement readiness','matched comparisons','population-weighted','side/family/context activity guards','universal scalar score','proven direct named-parameter','full-repository archive','docs/references/reference-mining/README.md')){ Require-Contains $chat $needle "CHAT_README is missing durable guardrail '$needle'." }
$testingReadme=Read-Text 'docs/design/testing/README.md'
foreach($needle in @('checkpoint-93/apply_checkpoint_93.ps1','Technology_Integration_Permutation_Suite_Architecture_v0_10.md','cross-tl-build-permutation-foundation-v0_4.json','population-weighted')){ Require-Contains $testingReadme $needle "Testing README is missing '$needle'." }

$rootTxt=@(Get-ChildItem -LiteralPath $repositoryRoot -File -Filter '*.txt')
Assert-True ($rootTxt.Count -eq 1 -and $rootTxt[0].Name -eq 'CHECKPOINT_93_SHA256SUMS.txt') 'Repository root must contain only CHECKPOINT_93_SHA256SUMS.txt as .txt.'
$rootManifest=Read-Manifest 'CHECKPOINT_93_SHA256SUMS.txt'
Assert-True (-not $rootManifest.Entries.ContainsKey('CHECKPOINT_93_SHA256SUMS.txt')) 'Checkpoint 93 root manifest must not contain itself.'
Assert-True ($rootManifest.EntryCount -gt $cp92Record.EntryCount) 'Checkpoint 93 root manifest should contain more repository-owned files than accepted CP92 because CP92 provenance and CP93 architecture files were added.'

Write-Host "Checkpoint 93 repository contracts passed ($frozenCount CP92 files frozen; $referenceCount accepted reference files byte-preserved; matched/readiness/Space/population architecture locked)."
