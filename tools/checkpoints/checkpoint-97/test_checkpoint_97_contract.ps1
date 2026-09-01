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
$normalRel='tools/calibration/checkpoints/checkpoint-97.json'
$deepRel='tools/calibration/checkpoints/checkpoint-97-deep-calibration.json'
$guardedPs=@(
    'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
    'tools/checkpoints/checkpoint-97/apply_checkpoint_97.ps1',
    'tools/checkpoints/checkpoint-97/test_checkpoint_97_contract.ps1',
    'tools/calibration/run_calibration_checkpoint.ps1'
)
& $guard -RepositoryRoot $repositoryRoot -PowerShellPaths $guardedPs -CheckpointDefinitionPaths @($normalRel,$deepRel)
$applyText=Read-Text 'tools/checkpoints/checkpoint-97/apply_checkpoint_97.ps1'
$provenHarnessCall='& $harness -CheckpointDefinition $definition -Trials $Trials -Jobs $Jobs -RepositoryOnly:$RepositoryOnly -NoClean:$NoClean'
Require-Contains $applyText $provenHarnessCall 'Checkpoint 97 wrapper must preserve the proven direct named-parameter harness invocation.'
Assert-True (-not [regex]::IsMatch($applyText,'&\s+\$harness\s+@[A-Za-z_][A-Za-z0-9_]*',[System.Text.RegularExpressions.RegexOptions]::IgnoreCase)) 'Checkpoint 97 wrapper must not invoke the calibration harness through splatted arguments.'

Write-Host '       Validating Checkpoint 97 definitions and bounded broader-development workload...'
$normal=Read-Json $normalRel
$deep=Read-Json $deepRel
$expectedStageIds=@(
    'deterministic','tl1-phase-a','tl1-phase-b','tl1-installation-space-envelope','tl1-sensor-ew-foundation',
    'cross-tl-build-permutation-preflight','cross-tl-build-permutation-generation','cross-tl-generated-study-preflight',
    'cross-tl-generated-study-smoke','adaptive-engage-preflight','adaptive-engage-smoke','adaptive-engage-study',
    'auxiliary-resource-endurance','checkpoint-53-resource-semantics-lock','runner-self-tests'
)
foreach($d in @($normal,$deep)){
    Assert-True ([string]$d.checkpointId -eq '97') 'Checkpoint 97 definition ID mismatch.'
    Assert-True ([string]$d.manifestFile -eq 'CHECKPOINT_97_SHA256SUMS.txt') 'Checkpoint 97 manifest binding mismatch.'
    Assert-True ([int]$d.defaultTrials -eq 3000 -and [int]$d.defaultJobs -eq 24) 'Checkpoint 97 default Trials/Jobs mismatch.'
    Assert-True (@($d.stages).Count -eq 15 -and [int]$d.checkpointMetrics.stageCount -eq 15) 'Checkpoint 97 must contain exactly 15 configured runner stages.'
    Assert-Sequence @($d.stages | ForEach-Object { [string]$_.id }) $expectedStageIds 'Checkpoint 97 configured runner-stage order drifted.'
    Assert-Sequence @($d.nativeDependencyPrecheck.powerShellPaths) $guardedPs 'Checkpoint 97 native-dependency PowerShell path list drifted.'
    Assert-Sequence @($d.nativeDependencyPrecheck.checkpointDefinitionPaths) @($normalRel,$deepRel) 'Checkpoint 97 native-dependency definition list drifted.'
    Assert-True ([int]$d.checkpointMetrics.monteCarloVariantCount -eq 36 -and [long]$d.checkpointMetrics.trialsAtDefault -eq 108000 -and [long]$d.checkpointMetrics.smokeTrialsAtDefault -eq 1476 -and [long]$d.checkpointMetrics.totalTrialExecutionsAtDefault -eq 109476) 'Checkpoint 97 workload accounting mismatch.'
    Assert-True ([bool]$d.checkpointMetrics.broaderMechanicsPass -and [bool]$d.checkpointMetrics.adaptiveEncounterFoundation -and [bool]$d.checkpointMetrics.playerInformationParity -and [bool]$d.checkpointMetrics.targetSpecificCombatBlackboard -and [bool]$d.checkpointMetrics.preContactNeutralSearch -and [bool]$d.checkpointMetrics.adaptiveClosureAfterFailedFirm -and [bool]$d.checkpointMetrics.observedAsymmetricStandoffPreserved -and [bool]$d.checkpointMetrics.eccmOverloadBeforeActiveSensorOverload -and [bool]$d.checkpointMetrics.failedOverloadRangeStateMemory -and [bool]$d.checkpointMetrics.cp96CrossTlOneTrialRegressionSmoke -and -not [bool]$d.checkpointMetrics.cp96CrossTlSubstantiveReplayRequired -and -not [bool]$d.checkpointMetrics.deepCalibrationApplicable -and -not [bool]$d.checkpointMetrics.technologyPromotionAutomatic) 'Checkpoint 97 architecture/boundary metrics mismatch.'
    Assert-True ([string]$d.primaryStudy.id -eq 'tl2-itc17-adaptive-engage-encounter-foundation' -and [int]$d.primaryStudy.variantCount -eq 36) 'Checkpoint 97 primary-study binding mismatch.'
    $self=@($d.stages | Where-Object { [string]$_.id -eq 'runner-self-tests' })
    Assert-True ($self.Count -eq 1 -and [int]$self[0].metrics.selfTestCount -eq 62) 'Checkpoint 97 must expect 62 ScenarioRunner self-tests.'
    $regSmoke=@($d.stages | Where-Object { [string]$_.id -eq 'cross-tl-generated-study-smoke' })
    Assert-True ($regSmoke.Count -eq 1 -and [string]$regSmoke[0].arguments[5] -eq '1') 'Checkpoint 97 must retain the accepted CP96 generated consumer as a one-trial regression smoke.'
    $engage=@($d.stages | Where-Object { [string]$_.id -eq 'adaptive-engage-study' })
    Assert-True ($engage.Count -eq 1 -and [int]$engage[0].metrics.variantCount -eq 36 -and [long]$engage[0].metrics.trialsAtDefault -eq 108000 -and -not [bool]$engage[0].metrics.balanceTargetsBlocking -and -not [bool]$engage[0].metrics.technologyPromotionAutomatic) 'Checkpoint 97 substantive Engage stage metrics mismatch.'
}

Write-Host '       Validating accepted Checkpoint 96 provenance and frozen baseline...'
$acceptedManifestRel='docs/validation/evidence/checkpoint-96/CHECKPOINT_96_SHA256SUMS.txt'
$acceptedManifest=Read-Manifest $acceptedManifestRel
Assert-True ($acceptedManifest.EntryCount -eq 1871 -and $acceptedManifest.PhysicalLineCount -eq 1871) 'Accepted Checkpoint 96 embedded manifest must contain exactly 1,871 entries.'
Assert-True ((Hash-Rel $acceptedManifestRel) -eq 'f4906ecdc98a782e16ce0be3e5230261d9a867653abc8489505b4edc00d0f512') 'Accepted Checkpoint 96 embedded manifest SHA-256 mismatch.'
$accepted=Read-Json 'docs/validation/evidence/checkpoint-96/checkpoint-96-native-acceptance-provenance.json'
Assert-True ([string]$accepted.checkpointId -eq '96' -and [string]$accepted.status -eq 'Success') 'Accepted Checkpoint 96 provenance status mismatch.'
Assert-True ([string]$accepted.checkpointDefinitionSha256 -eq '6c5ffdd09669137f892e88c678c9b3536ac61a456174eea24e85fd1108377d89' -and [string]$accepted.checkpointManifestSha256 -eq 'f4906ecdc98a782e16ce0be3e5230261d9a867653abc8489505b4edc00d0f512') 'Accepted Checkpoint 96 hash provenance mismatch.'
Assert-True ([string]$accepted.sourceResultsArchiveSha256 -eq 'a04e25825151dfaa69d4fb24d532cb64c4019a884cdcb36030739fc99f74972d' -and [string]$accepted.acceptedRepositoryArchiveSha256 -eq '945e1da63b714a36ee9aabe29575cc85e827f4d7537ab38e609a3760eef05fa0') 'Accepted Checkpoint 96 archive provenance mismatch.'
Assert-True ([int]$accepted.tests.total -eq 863 -and [int]$accepted.tests.passed -eq 863 -and [int]$accepted.aggregates.runnerStagesPassed -eq 13 -and [int]$accepted.aggregates.selfTests -eq 59 -and [int]$accepted.aggregates.failedGates -eq 0) 'Accepted Checkpoint 96 native acceptance metrics mismatch.'

$mutable=@{}
foreach($p in @(
    'CHAT_README.md','README.md','docs/README.md','docs/Prototype_TODO.md','docs/design/README.md','docs/design/testing/README.md','docs/development/Simulation_Development_Guidelines.md',
    'docs/design/ai/AI_Doctrine_Registry_Architecture_v0_5.md',
    'docs/design/testing/Checkpoint_96_Validation_Tiers.md','docs/design/testing/checkpoint_96_validation_suite_policy_v0_1.json','docs/validation/Checkpoint_96_Readiness_Cohort_Semantics_Closure.md',
    'src/StarCluster.Core/Combat/Tactics/TacticalDecisionContext.cs','src/StarCluster.Core/Combat/Tactics/TacticalOrderPolicy.cs',
    'src/StarCluster.ScenarioRunner/ScenarioRunnerSelfTests.cs','src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatDocuments.cs','src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs',
    'tests/StarCluster.Tests/Combat/Tactics/TacticalOrderPolicyTests.cs'
)){ $mutable[$p]=$true }
$frozenCount=0
$mutableAcceptedCount=0
foreach($entry in $acceptedManifest.Entries.GetEnumerator()){
    $rel=[string]$entry.Key
    if($mutable.ContainsKey($rel)){ $mutableAcceptedCount++; continue }
    Assert-True (Test-Path -LiteralPath (RelPath $rel) -PathType Leaf) "Accepted CP96 frozen file '$rel' is missing."
    Assert-True ((Hash-Rel $rel) -eq [string]$entry.Value) "Accepted CP96 frozen file '$rel' changed unexpectedly."
    $frozenCount++
}
Assert-True ($frozenCount -eq ($acceptedManifest.EntryCount - $mutableAcceptedCount)) 'Checkpoint 97 CP96 frozen-file accounting mismatch.'
$archivePairs=@(
    @('docs/design/ai/AI_Doctrine_Registry_Architecture_v0_5.md','docs/archive/ai/AI_Doctrine_Registry_Architecture_v0_5.md'),
    @('docs/design/testing/Checkpoint_96_Validation_Tiers.md','docs/archive/testing/Checkpoint_96_Validation_Tiers.md'),
    @('docs/design/testing/checkpoint_96_validation_suite_policy_v0_1.json','docs/archive/testing/checkpoint_96_validation_suite_policy_v0_1.json'),
    @('docs/validation/Checkpoint_96_Readiness_Cohort_Semantics_Closure.md','docs/validation/archive/Checkpoint_96_Readiness_Cohort_Semantics_Closure.md')
)
foreach($pair in $archivePairs){
    $old=[string]$pair[0]; $arch=[string]$pair[1]
    Assert-True ($acceptedManifest.Entries.ContainsKey($old)) "Accepted CP96 manifest lacks '$old'."
    Assert-True ((Hash-Rel $arch) -eq [string]$acceptedManifest.Entries[$old]) "Archived CP96 authority '$arch' is not byte-identical to accepted '$old'."
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

Write-Host '       Validating Adaptive Engage information parity, combat memory, and escalation architecture...'
$blackboard=Read-Text 'src/StarCluster.Core/Combat/Tactics/TacticalCombatBlackboard.cs'
foreach($needle in @('TacticalCombatBlackboard','MaximumOwnAttackRangeHexes','MaximumObservedOpponentAttackRangeHexes','RecordTrackObservation','RecordOverloadFailure','CanAttemptOverload','currentRangeHexes < failure.RangeHexes','failure.ObservableState != observableState','public enum TacticalEscalationKind','EccmOverload','ActiveSensorOverload')){ Require-Contains $blackboard $needle "Combat blackboard is missing CP97 contract '$needle'." }
foreach($forbidden in @('TechnologyLevel','JammingMargin','EcmRating','EccmRating')){ Require-NotContains $blackboard $forbidden "Combat blackboard must not cache hidden opponent '$forbidden'." }
$search=Read-Text 'src/StarCluster.Core/Combat/Tactics/EncounterSearchMovementResolver.cs'
foreach($needle in @('ResolveTowardCenter','availableMovementHexes == 0','origin == HexCoord.Zero','map.NeighborsOf(origin)','MovementHexes')){ Require-Contains $search $needle "Pre-contact search resolver is missing '$needle'." }
Require-NotContains $search 'HexCoord target' 'Pre-contact center-search resolver must not accept a target coordinate.'
Require-NotContains $search 'targetCoordinate' 'Pre-contact center-search resolver must not inspect a target coordinate.'
$policyText=Read-Text 'src/StarCluster.Core/Combat/Tactics/TacticalOrderPolicy.cs'
foreach($needle in @('AdaptiveEngageTacticalPolicy','LastTrackQuality','LastTrackRangeHexes','MaximumOwnAttackRangeHexes','MaximumObservedOpponentAttackRangeHexes','one-sided engagement envelope','own known physical weapon reach')){ Require-Contains $policyText $needle "Adaptive Engage policy is missing '$needle'." }
Require-NotContains $policyText 'AdaptiveEngageTacticalPolicy : OpponentAwareRangeTacticalPolicy' 'Adaptive Engage must not inherit the old opponent-family range policy.'
$documents=Read-Text 'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatDocuments.cs'
Require-Contains $documents 'EngageAdaptive' 'Integrated movement-mode schema is missing EngageAdaptive.'
$consumer=Read-Text 'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs'
foreach($needle in @('AdaptiveEngageEncounterStudyId','tl2-itc17-adaptive-engage-encounter-foundation','UpdateAdaptiveEncounterContact','ResolveEncounterMovement','EncounterSearchMovementResolver.ResolveTowardCenter','BuildAdaptiveObservableState','AdaptiveSensorOverloadPolicy','TryAdaptiveEccmOverload','RecordObservedOpponentAttack','RecordOwnAttack','closureExhaustedA','closureExhaustedB','adaptive-engage-review.csv','cp97-eccm-overload-probe-exercised','cp97-active-sensor-overload-probe-exercised')){ Require-Contains $consumer $needle "Integrated Engage consumer is missing '$needle'." }
Require-Contains $consumer 'blackboard.LastFirmTrackDegradedByObservedEcm' 'Active Sensor overload must yield to ECCM overload when observable ECM degradation makes ECCM the preferred escalation.'
Require-Contains $consumer 'TacticalEscalationKind.EccmOverload' 'CP97 must remember failed ECCM overloads.'
Require-Contains $consumer 'TacticalEscalationKind.ActiveSensorOverload' 'CP97 must remember failed Active Sensor overloads.'
Require-Contains $consumer 'targetKnownOverride' 'Adaptive decision context must carry explicit observed-contact state.'
Require-Contains $consumer 'IsSingleSourcePolicyTelemetryStudy(study.Id)' 'CP97 actual-consumer preflight and policy gate must share the single-source policy telemetry classifier.'
Assert-True ([regex]::Matches($consumer,'IsSingleSourcePolicyTelemetryStudy\(study\.Id\)').Count -ge 2) 'CP97 actual-consumer preflight and full policy-telemetry gate must both call the shared classifier.'
Require-Contains $consumer 'studyId == AdaptiveEngageEncounterStudyId' 'Adaptive Engage must be registered in the shared single-source policy telemetry classifier.'
Require-Contains $consumer 'CP97 Engage actual-consumer preflight must classify Adaptive Engage as a single-source policy telemetry study.' 'CP97 preflight must fail before Monte Carlo if Adaptive Engage policy telemetry classification is missing.'

Write-Host '       Validating CP97 bounded study, harness-fixture isolation, and player-information contract...'
$study=Read-Json 'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/tl2-itc17-adaptive-engage-encounter-foundation.json'
Assert-True ([string]$study.id -eq 'tl2-itc17-adaptive-engage-encounter-foundation' -and [long]$study.masterSeed -eq 970100 -and [int]$study.trialsPerVariant -eq 3000) 'CP97 Engage study identity/seed/trial definition mismatch.'

# Mirror the actual TechnologyCombatProfileCatalog loader contract here so an
# incompatible study/catalog baseline binding fails in RepositoryOnly before
# the native build and ScenarioRunner stages begin.
$baselineRel='docs/archive/player_technology/pre-cp165-active/tl1_core_combat_numerical_baseline_v0_3.csv'
$baselineHash=Hash-Rel $baselineRel
Assert-True ([string]$study.baselineSha256 -eq $baselineHash) 'CP97 Engage study baselineSha256 does not match the authoritative TL1 baseline file.'
$technologyCatalogRel=[string]$study.technologyProfileCatalog
Assert-True (-not [string]::IsNullOrWhiteSpace($technologyCatalogRel)) 'CP97 Engage study must bind an explicit technologyProfileCatalog.'
$technologyCatalog=Read-Json $technologyCatalogRel
Assert-True ([string]$technologyCatalog.schemaVersion -eq 'star-cluster-architecture-runtime-profile-catalog-v1') 'CP97 technologyProfileCatalog must use the architecture runtime profile catalog schema.'
Assert-True ([string]$technologyCatalog.id -eq 'tl1-tl2-standard-runtime-profiles-v0_4') 'CP97 must use the current-baseline compatibility bridge technology catalog v0.4.'
Assert-True ([string]$technologyCatalog.baselineSha256 -eq $baselineHash -and [string]$technologyCatalog.baselineSha256 -eq [string]$study.baselineSha256) 'CP97 technology profile catalog baseline hash must match both the authoritative TL1 baseline and the study baselineSha256.'
Assert-True ([bool]$technologyCatalog.policy.cp97CurrentBaselineCompatibilityBridge -and [bool]$technologyCatalog.policy.numericProfilesUnchangedFromV0_3) 'CP97 technology profile bridge policy markers are missing.'

$technologyProfilesById=@{}
foreach($profile in @($technologyCatalog.profiles)){
    $id=[string]$profile.id
    Assert-True (-not [string]::IsNullOrWhiteSpace($id)) 'CP97 technology profile catalog contains a blank profile ID.'
    Assert-True (-not $technologyProfilesById.ContainsKey($id)) "CP97 technology profile catalog duplicates profile '$id'."
    $technologyProfilesById[$id]=$profile
}
Assert-True ($technologyProfilesById.Count -eq 2 -and $technologyProfilesById.ContainsKey('tl1-production') -and $technologyProfilesById.ContainsKey('tl2-production')) 'CP97 technology profile bridge must contain exactly TL1 and TL2 production profiles.'
$tl1Profile=$technologyProfilesById['tl1-production']
Assert-True ([int]$tl1Profile.technologyLevel -eq 1 -and [string]$tl1Profile.source -eq $baselineRel) 'CP97 TL1 runtime profile must identify the current authoritative TL1 baseline source.'
$baselineValues=@{}
foreach($row in @(Import-Csv -LiteralPath (RelPath $baselineRel))){ $baselineValues[[string]$row.parameter_id]=[string]$row.value }
function Baseline-Int { param([string]$Id) Assert-True ($baselineValues.ContainsKey($Id)) "Authoritative TL1 baseline is missing '$Id'."; return [int]$baselineValues[$Id] }
Assert-True (
    [int]$tl1Profile.defense.hull -eq (Baseline-Int 'hull_points') -and
    [int]$tl1Profile.defense.armorIntegrity -eq (Baseline-Int 'armor_integrity') -and
    [int]$tl1Profile.defense.armorProtection -eq (Baseline-Int 'armor_protection') -and
    [int]$tl1Profile.defense.shieldCapacity -eq (Baseline-Int 'shield_capacity') -and
    [int]$tl1Profile.defense.shieldBaseRecharge -eq (Baseline-Int 'shield_base_recharge') -and
    [int]$tl1Profile.defense.shieldArmor -eq 0 -and
    [int]$tl1Profile.powerAndControl.reactorOutput -eq (Baseline-Int 'reactor_output') -and
    [int]$tl1Profile.powerAndControl.targetingBonus -eq (Baseline-Int 'targeting_accuracy_bonus') -and
    [int]$tl1Profile.powerAndControl.effectivePdsChance -eq ((Baseline-Int 'kinetic_pds_chance') + (Baseline-Int 'targeting_accuracy_bonus')) -and
    [int]$tl1Profile.powerAndControl.pdsPower -eq (Baseline-Int 'kinetic_pds_power') -and
    [int]$tl1Profile.powerAndControl.standardCombatPowerCommitment -eq ((Baseline-Int 'kinetic_power') + (Baseline-Int 'kinetic_pds_power')) -and
    [int]$tl1Profile.movement.shipMove -eq (Baseline-Int 'stl_move') -and
    [int]$tl1Profile.movement.missileMove -eq (Baseline-Int 'missile_speed') -and
    [int]$tl1Profile.weapons.kinetic.damage -eq (Baseline-Int 'kinetic_damage') -and
    [int]$tl1Profile.weapons.kinetic.shieldPenetration -eq (Baseline-Int 'kinetic_spen') -and
    [int]$tl1Profile.weapons.kinetic.armorPenetration -eq (Baseline-Int 'kinetic_apen') -and
    [int]$tl1Profile.weapons.kinetic.accuracyBonus -eq (Baseline-Int 'kinetic_accuracy') -and
    [int]$tl1Profile.weapons.kinetic.guidanceChance -eq 0 -and
    [int]$tl1Profile.weapons.kinetic.maximumRange -eq (Baseline-Int 'kinetic_range') -and
    [int]$tl1Profile.weapons.kinetic.powerCost -eq (Baseline-Int 'kinetic_power') -and
    [int]$tl1Profile.weapons.kinetic.ammunition -eq (Baseline-Int 'kinetic_ammo') -and
    [int]$tl1Profile.weapons.energy.damage -eq (Baseline-Int 'energy_standard_damage') -and
    [int]$tl1Profile.weapons.energy.shieldPenetration -eq (Baseline-Int 'energy_spen') -and
    [int]$tl1Profile.weapons.energy.armorPenetration -eq (Baseline-Int 'energy_apen') -and
    [int]$tl1Profile.weapons.energy.accuracyBonus -eq (Baseline-Int 'energy_accuracy') -and
    [int]$tl1Profile.weapons.energy.guidanceChance -eq 0 -and
    [int]$tl1Profile.weapons.energy.maximumRange -eq (Baseline-Int 'energy_range') -and
    [int]$tl1Profile.weapons.energy.powerCost -eq (Baseline-Int 'energy_standard_power') -and
    $null -eq $tl1Profile.weapons.energy.ammunition -and
    [int]$tl1Profile.weapons.missile.damage -eq (Baseline-Int 'missile_warhead_damage') -and
    [int]$tl1Profile.weapons.missile.shieldPenetration -eq (Baseline-Int 'missile_warhead_spen') -and
    [int]$tl1Profile.weapons.missile.armorPenetration -eq (Baseline-Int 'missile_warhead_apen') -and
    [int]$tl1Profile.weapons.missile.accuracyBonus -eq 0 -and
    [int]$tl1Profile.weapons.missile.guidanceChance -eq (Baseline-Int 'missile_guidance_hit') -and
    [int]$tl1Profile.weapons.missile.maximumRange -eq (Baseline-Int 'missile_range') -and
    [int]$tl1Profile.weapons.missile.powerCost -eq (Baseline-Int 'missile_launch_power') -and
    [int]$tl1Profile.weapons.missile.ammunition -eq (Baseline-Int 'missile_ammo')
) 'CP97 TL1 runtime technology profile no longer reproduces the authoritative baseline values used by the native loader.'

$previousTechnologyCatalog=Read-Json 'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/tl1-tl2-standard-runtime-profiles-v0_3.json'
$previousTl2=@($previousTechnologyCatalog.profiles | Where-Object { [string]$_.id -eq 'tl2-production' })
Assert-True ($previousTl2.Count -eq 1) 'Frozen runtime catalog v0.3 must contain the accepted TL2 production profile.'
Assert-True (($technologyProfilesById['tl2-production'] | ConvertTo-Json -Depth 32 -Compress) -eq ($previousTl2[0] | ConvertTo-Json -Depth 32 -Compress)) 'CP97 compatibility bridge must not change the accepted TL2 production runtime vector.'

# Check cross-catalog referential integrity before ScenarioRunner is invoked.
$auxCatalogRel=[string]$study.auxiliaryProfileCatalog
$sensorCatalogRel=[string]$study.sensorEwProfileCatalog
$doctrineCatalogRel=[string]$study.aiDoctrineCatalog
Assert-True (-not [string]::IsNullOrWhiteSpace($auxCatalogRel) -and -not [string]::IsNullOrWhiteSpace($sensorCatalogRel) -and -not [string]::IsNullOrWhiteSpace($doctrineCatalogRel)) 'CP97 Engage study must bind technology, auxiliary, Sensor/EW, and AI doctrine catalogs explicitly.'
$auxCatalog=Read-Json $auxCatalogRel
$sensorCatalog=Read-Json $sensorCatalogRel
$doctrineCatalog=Read-Json $doctrineCatalogRel
$auxIds=@{}; foreach($p in @($auxCatalog.profiles)){ $auxIds[[string]$p.id]=$true }
$sensorIds=@{}; foreach($p in @($sensorCatalog.candidates)){ $sensorIds[[string]$p.id]=$true }
$doctrineIds=@{}; foreach($p in @($doctrineCatalog.doctrines)){ $doctrineIds[[string]$p.id]=$true }
foreach($variant in @($study.variants)){
    foreach($id in @([string]$variant.sideAProfileId,[string]$variant.sideBProfileId)){ Assert-True ($technologyProfilesById.ContainsKey($id)) "CP97 variant '$($variant.id)' references missing technology profile '$id'." }
    foreach($id in @([string]$variant.sideAAuxiliaryProfileId,[string]$variant.sideBAuxiliaryProfileId)){ Assert-True ($auxIds.ContainsKey($id)) "CP97 variant '$($variant.id)' references missing auxiliary profile '$id'." }
    foreach($id in @([string]$variant.sideASensorEwProfileId,[string]$variant.sideBSensorEwProfileId)){ Assert-True ($sensorIds.ContainsKey($id)) "CP97 variant '$($variant.id)' references missing Sensor/EW profile '$id'." }
    foreach($id in @([string]$variant.sideAAiDoctrineId,[string]$variant.sideBAiDoctrineId)){ Assert-True ($doctrineIds.ContainsKey($id)) "CP97 variant '$($variant.id)' references missing AI doctrine '$id'." }
}
Assert-True (@($study.builds).Count -eq 4 -and @($study.variants).Count -eq 36) 'CP97 Engage study must contain four harness builds and 36 variants.'
$groups=@($study.variants | Group-Object -Property comparisonGroup)
Assert-True ($groups.Count -eq 18) 'CP97 Engage study must contain 18 comparison groups.'
foreach($group in $groups){
    Assert-True ($group.Count -eq 2) "CP97 comparison group '$($group.Name)' must contain exactly two mover-order mirrors."
    Assert-True (@($group.Group | Where-Object { [string]$_.movementOrder -eq 'SideAFirst' }).Count -eq 1 -and @($group.Group | Where-Object { [string]$_.movementOrder -eq 'SideBFirst' }).Count -eq 1) "CP97 comparison group '$($group.Name)' must contain one A-first and one B-first variant."
}
Assert-True (@($study.variants | Where-Object { [string]$_.movementMode -ne 'EngageAdaptive' -or [int]$_.initialRangeHexes -ne 10 -or [int]$_.tacticalMapRadius -ne 5 -or [int]$_.startingFuel -ne 100 }).Count -eq 0) 'Every CP97 Engage variant must use EngageAdaptive at opposite radius-5 edges with 100 fuel.'
Assert-True (@($study.variants | Where-Object { [string]$_.movementOrder -eq 'Simultaneous' }).Count -eq 0) 'CP97 must preserve mirrored mover-order bounds rather than invent production simultaneous initiative.'
$eccmProbe=@($study.variants | Where-Object { [string]$_.profileLabel -eq 'cp97-eccm_overload_probe' })
$sensorProbe=@($study.variants | Where-Object { [string]$_.profileLabel -eq 'cp97-active_sensor_overload_probe' })
Assert-True ($eccmProbe.Count -eq 4 -and $sensorProbe.Count -eq 4) 'CP97 requires exactly four ECCM-overload and four Active-Sensor-overload diagnostic variants.'
$buildById=@{}; foreach($b in @($study.builds)){ $buildById[[string]$b.id]=$b }
foreach($variant in @($study.variants)){
    foreach($id in @([string]$variant.sideABuildId,[string]$variant.sideBBuildId)){ Assert-True ($buildById.ContainsKey($id)) "CP97 variant '$($variant.id)' references missing harness build '$id'." }
}
Assert-True ([bool]$buildById['cp97-no-ew'].activeSensor -and [bool]$buildById['cp97-counter-eccm1'].activeSensor -and -not [bool]$buildById['cp97-jammer-ecm2'].activeSensor -and -not [bool]$buildById['cp97-jammer-ecm3-diagnostic'].activeSensor) 'CP97 ordinary/counter and jammer build Active-Sensor roles drifted.'
Assert-True ([int]$buildById['cp97-no-ew'].usedSpace -eq 31 -and [int]$buildById['cp97-no-ew'].freeSupportSpace -eq 4 -and [int]$buildById['cp97-counter-eccm1'].usedSpace -eq 32 -and [int]$buildById['cp97-counter-eccm1'].freeSupportSpace -eq 3 -and [int]$buildById['cp97-jammer-ecm2'].usedSpace -eq 29 -and [int]$buildById['cp97-jammer-ecm2'].freeSupportSpace -eq 6 -and [int]$buildById['cp97-jammer-ecm3-diagnostic'].usedSpace -eq 29 -and [int]$buildById['cp97-jammer-ecm3-diagnostic'].freeSupportSpace -eq 6) 'CP97 harness build Space accounting drifted.'
Assert-True (@($study.variants | Where-Object { [string]$_.profileLabel -ne 'cp97-eccm_overload_probe' -and (([string]$_.sideABuildId -eq 'cp97-jammer-ecm3-diagnostic') -or ([string]$_.sideBBuildId -eq 'cp97-jammer-ecm3-diagnostic')) }).Count -eq 0) 'Harness-only ECM3 build leaked outside the ECCM-overload probe.'
Assert-True (@($study.variants | Where-Object { [string]$_.profileLabel -ne 'cp97-active_sensor_overload_probe' -and (([string]$_.sideASensorEwProfileId -eq 'cp97-active-overload-probe') -or ([string]$_.sideASensorEwProfileId -eq 'cp97-standoff-passive-firm4-control') -or ([string]$_.sideBSensorEwProfileId -eq 'cp97-active-overload-probe') -or ([string]$_.sideBSensorEwProfileId -eq 'cp97-standoff-passive-firm4-control')) }).Count -eq 0) 'Harness-only Active-Sensor overload profiles leaked outside their probe.'
$sensorFixtures=Read-Json 'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/cp97-adaptive-engage-sensor-ew-fixtures-v0_1.json'
Assert-True (@($sensorFixtures.candidates).Count -eq 4) 'CP97 Sensor/EW fixture catalog must contain four profiles.'
$fixtureText=Read-Text 'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/cp97-adaptive-engage-sensor-ew-fixtures-v0_1.json'
foreach($needle in @('Harness-only','Not a production sensor candidate','cp97-active-overload-probe','cp97-standoff-passive-firm4-control')){ Require-Contains $fixtureText $needle "CP97 fixture catalog is missing isolation marker '$needle'." }

Write-Host '       Validating tests, durable AI authority, and active documentation hygiene...'
$selfTests=Read-Text 'src/StarCluster.ScenarioRunner/ScenarioRunnerSelfTests.cs'
foreach($needle in @('CP97 pre-contact search advances one hex toward center without target input','CP97 failed overload memory blocks same-or-farther retry but permits closer retry','CP97 material observable-state change re-enables a failed overload')){ Require-Contains $selfTests $needle "ScenarioRunner self-tests are missing CP97 regression '$needle'." }
$blackboardTests=Read-Text 'tests/StarCluster.Tests/Combat/Tactics/TacticalCombatBlackboardTests.cs'
foreach($needle in @('FailedOverloadIsNotRepeatedAtSameOrGreaterRange','FailedOverloadMayBeRetriedAfterClosing','MaterialObservableStateChangeReenablesOverload','RecordObservedOpponentAttack')){ Require-Contains $blackboardTests $needle "Blackboard tests are missing '$needle'." }
$searchTests=Read-Text 'tests/StarCluster.Tests/Combat/Tactics/EncounterSearchMovementResolverTests.cs'
Require-Contains $searchTests 'EdgeSearchMovesExactlyOneHexTowardCenter' 'Encounter search tests must lock the one-hex pre-contact rule.'
$policyTests=Read-Text 'tests/StarCluster.Tests/Combat/Tactics/TacticalOrderPolicyTests.cs'
foreach($needle in @('AdaptiveEngageClosesAfterObservedTrackFailure','AdaptiveEngagePreservesObservedStandoffAdvantage','AdaptiveEngageUsesOnlyOwnReachBeforeCombatEvidence')){ Require-Contains $policyTests $needle "Adaptive Engage policy tests are missing '$needle'." }
$ai=Read-Text 'docs/design/ai/AI_Doctrine_Registry_Architecture_v0_6.md'
foreach($needle in @('Information parity is absolute','Encounter state model','Target-specific combat blackboard','Preserve demonstrated asymmetric standoff','ECCM overload first','Active Sensor overload','Failed-overload memory','not technology candidates')){ Require-Contains $ai $needle "AI architecture v0.6 is missing '$needle'." }
$aiPolicy=Read-Json 'docs/design/ai/adaptive_engage_policy_v0_1.json'
Assert-True ([string]$aiPolicy.id -eq 'adaptive-engage-policy-v0_1' -and [bool]$aiPolicy.combatBlackboard.targetSpecific -and -not [bool]$aiPolicy.informationParity.hiddenOpponentTechnologyLevelsAllowed -and -not [bool]$aiPolicy.informationParity.hiddenOpponentEcmEccmRatingsAllowed -and -not [bool]$aiPolicy.informationParity.internalJammingMarginAllowed -and [bool]$aiPolicy.movement.failedFirmAtRangeDrivesLaterClosure -and [bool]$aiPolicy.escalation.ordinaryMovementBeforeOverload -and [string]$aiPolicy.escalation.preferredOverloadOrder[0] -eq 'eccm_overload' -and [string]$aiPolicy.escalation.preferredOverloadOrder[1] -eq 'active_sensor_overload' -and -not [bool]$aiPolicy.promotionBoundary.diagnosticFixtureTechnologyPromotion) 'Adaptive Engage machine policy semantics drifted.'
$policy=Read-Json 'docs/design/testing/checkpoint_97_validation_suite_policy_v0_1.json'
Assert-True ([string]$policy.checkpoint -eq '97' -and [bool]$policy.informationParity.targetSpecificCombatBlackboard -and -not [bool]$policy.informationParity.hiddenOpponentTlAllowed -and [bool]$policy.engage.preserveObservedAsymmetricStandoff -and [bool]$policy.engage.eccmOverloadBeforeActiveSensorOverloadWhenBothPlausible -and [long]$policy.study.totalTrialExecutionsAtDefault -eq 109476 -and -not [bool]$policy.authorityBoundary.componentTuning -and -not [bool]$policy.authorityBoundary.technologyPromotion -and -not [bool]$policy.deepCalibration.applicable) 'Checkpoint 97 validation policy semantics mismatch.'
$guidelines=Read-Text 'docs/development/Simulation_Development_Guidelines.md'
foreach($needle in @('General encounter and adaptive tactical-AI methodology','one hex toward map center','target-specific combat blackboard','ECCM overload precedes Active Sensor overload','failed overload at range X','CP96 closed the dedicated narrow instrumentation sequence')){ Require-Contains $guidelines $needle "Simulation Development Guidelines are missing CP97 durable methodology '$needle'." }
Assert-ExactFileSet 'docs/design/testing' @('Checkpoint_97_Validation_Tiers.md','README.md','Technology_Integration_Permutation_Suite_Architecture_v0_12.md','checkpoint_97_validation_suite_policy_v0_1.json','technology_integration_permutation_suite_v0_12.json')
Assert-True (-not (Test-Path -LiteralPath (RelPath 'docs/design/ai/AI_Doctrine_Registry_Architecture_v0_5.md'))) 'Superseded AI architecture v0.5 must not remain active.'
Assert-True (Test-Path -LiteralPath (RelPath 'docs/design/ai/AI_Doctrine_Registry_Architecture_v0_6.md') -PathType Leaf) 'AI architecture v0.6 must be active.'
$activeValidation=@(Get-ChildItem -LiteralPath (RelPath 'docs/validation') -File -Filter 'Checkpoint_*.md')
Assert-True ($activeValidation.Count -eq 1 -and $activeValidation[0].Name -eq 'Checkpoint_97_Encounter_And_Adaptive_Engage_AI_Foundation.md') 'Exactly one active CP97 validation runbook must remain.'
$runbook=Read-Text 'docs/validation/Checkpoint_97_Encounter_And_Adaptive_Engage_AI_Foundation.md'
foreach($needle in @('6c5ffdd09669137f892e88c678c9b3536ac61a456174eea24e85fd1108377d89','f4906ecdc98a782e16ce0be3e5230261d9a867653abc8489505b4edc00d0f512','970100','109,476','875','62','ECCM overload','Active Sensor overload','player information')){ Require-Contains $runbook $needle "CP97 runbook is missing '$needle'." }
$rootReadme=Read-Text 'README.md'; foreach($needle in @('Checkpoint 97 Candidate','CP96 remains the latest accepted','109,476','875 xUnit','62 ScenarioRunner','broader development track')){ Require-Contains $rootReadme $needle "Root README is missing '$needle'." }
$chat=Read-Text 'CHAT_README.md'; foreach($needle in @('CP97 candidate','CP96','Tactical AI gets memory, not omniscience','Preserve real asymmetric standoff','Overload is late escalation')){ Require-Contains $chat $needle "CHAT_README is missing CP97 bootstrap guardrail '$needle'." }

$rootTxt=@(Get-ChildItem -LiteralPath $repositoryRoot -File -Filter '*.txt')
Assert-True ($rootTxt.Count -eq 1 -and $rootTxt[0].Name -eq 'CHECKPOINT_97_SHA256SUMS.txt') 'Repository root must contain only CHECKPOINT_97_SHA256SUMS.txt as .txt.'
$rootManifest=Read-Manifest 'CHECKPOINT_97_SHA256SUMS.txt'
Assert-True (-not $rootManifest.Entries.ContainsKey('CHECKPOINT_97_SHA256SUMS.txt')) 'Checkpoint 97 root manifest must not contain itself.'
foreach($entry in $rootManifest.Entries.GetEnumerator()){
    $rel=[string]$entry.Key
    Assert-True (Test-Path -LiteralPath (RelPath $rel) -PathType Leaf) "Checkpoint 97 manifest entry '$rel' is missing."
    Assert-True ((Hash-Rel $rel) -eq [string]$entry.Value) "Checkpoint 97 manifest hash mismatch for '$rel'."
}

Write-Host "Checkpoint 97 repository contracts passed ($frozenCount CP96 files frozen; $referenceCount accepted reference files byte-preserved; Adaptive Engage information-parity/encounter architecture locked)."
