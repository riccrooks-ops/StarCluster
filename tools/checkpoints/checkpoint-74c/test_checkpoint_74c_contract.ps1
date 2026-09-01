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

$guard = Join-Path $repositoryRoot 'tools\checkpoints\Test-NativeAcceptanceDependencies.ps1'
$normalRel = 'tools/calibration/checkpoints/checkpoint-74c.json'
$deepRel = 'tools/calibration/checkpoints/checkpoint-74c-deep-calibration.json'
$guardedPs = @(
    'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
    'tools/checkpoints/checkpoint-74c/apply_checkpoint_74c.ps1',
    'tools/checkpoints/checkpoint-74c/test_checkpoint_74c_contract.ps1',
    'tools/calibration/run_calibration_checkpoint.ps1'
)
& $guard -RepositoryRoot $repositoryRoot -PowerShellPaths $guardedPs -CheckpointDefinitionPaths @($normalRel, $deepRel)

$guardedDefs = @($normalRel, $deepRel)
$normal = Read-Json $normalRel
$deep = Read-Json $deepRel
Assert-True ([string]$normal.checkpointId -eq '74c' -and [string]$deep.checkpointId -eq '74c') 'Checkpoint 74c definition ID mismatch.'
Assert-True ([string]$normal.manifestFile -eq 'CHECKPOINT_74C_SHA256SUMS.txt' -and [string]$deep.manifestFile -eq 'CHECKPOINT_74C_SHA256SUMS.txt') 'Checkpoint 74c manifest binding mismatch.'
Assert-True ([string]$normal.outputRoot -eq 'out/checkpoint-74c' -and [string]$deep.outputRoot -eq 'out/checkpoint-74c-deep-calibration') 'Checkpoint 74c output-root binding mismatch.'
Assert-True ((@($normal.nativeDependencyPrecheck.powerShellPaths) -join '|') -eq ($guardedPs -join '|')) 'Checkpoint 74c normal native-dependency PowerShell path binding mismatch.'
Assert-True ((@($deep.nativeDependencyPrecheck.powerShellPaths) -join '|') -eq ($guardedPs -join '|')) 'Checkpoint 74c deep native-dependency PowerShell path binding mismatch.'
Assert-True ((@($normal.nativeDependencyPrecheck.checkpointDefinitionPaths) -join '|') -eq ($guardedDefs -join '|')) 'Checkpoint 74c normal native-dependency definition binding mismatch.'
Assert-True ((@($deep.nativeDependencyPrecheck.checkpointDefinitionPaths) -join '|') -eq ($guardedDefs -join '|')) 'Checkpoint 74c deep native-dependency definition binding mismatch.'
Assert-True (@($normal.stages).Count -eq 11 -and @($deep.stages).Count -eq 30) 'Checkpoint 74c stage-count mismatch.'
Assert-True ([int]$normal.checkpointMetrics.monteCarloVariantCount -eq 20 -and [int]$normal.checkpointMetrics.trialsAtDefault -eq 200000 -and [int]$normal.checkpointMetrics.smokeTrialsAtDefault -eq 20 -and [int]$normal.checkpointMetrics.totalTrialExecutionsAtDefault -eq 200020) 'Checkpoint 74c normal workload mismatch.'
Assert-True ([int]$deep.checkpointMetrics.monteCarloVariantCount -eq 1564 -and [int]$deep.checkpointMetrics.trialsAtDefault -eq 15640000 -and [int]$deep.checkpointMetrics.smokeTrialsAtDefault -eq 20 -and [int]$deep.checkpointMetrics.totalTrialExecutionsAtDefault -eq 15640020) 'Checkpoint 74c Deep Calibration workload mismatch.'

$policy = Read-Json 'docs/design/testing/checkpoint_74_validation_suite_policy_v0_1.json'
Assert-True ([string]$policy.aiDoctrineControls.registryVersion -eq '0.2' -and [string]$policy.aiDoctrineControls.defaultEwDoctrine -eq 'tl1-ew-preserve-combat-package-v1' -and -not [bool]$policy.aiDoctrineControls.cp73RerunRequired) 'Checkpoint 74c AI doctrine-promotion policy mismatch.'
Assert-True ([bool]$policy.productionControls.degradedFireFoundationImplementedByCheckpoint74 -and -not [bool]$policy.productionControls.productionWeaponDegradedFireEnabledByCheckpoint74 -and -not [bool]$policy.productionControls.movementPhaseFireImplementedByCheckpoint74) 'Checkpoint 74c production/deferred-feature policy mismatch.'

$registry = Read-Json 'docs/archive/ai/pre-cp165-active/ai_doctrine_registry_v0_2.json'
Assert-True ([string]$registry.registryVersion -eq '0.2' -and [string]$registry.defaults.'electronic-warfare' -eq 'tl1-ew-preserve-combat-package-v1') 'Checkpoint 74c registry default mismatch.'
$doctrines = @($registry.doctrines)
$default = @($doctrines | Where-Object { [string]$_.id -eq 'tl1-ew-preserve-combat-package-v1' })
Assert-True ($default.Count -eq 1 -and [string]$default[0].status -eq 'accepted' -and [string]$default[0].acceptedCheckpoint -eq '73') 'Preserve-combat-package must remain accepted from CP73.'
$reactive = @($doctrines | Where-Object { [string]$_.id -eq 'tl1-ew-reactive-eccm-v1' })
Assert-True ($reactive.Count -eq 1 -and [string]$reactive[0].status -eq 'accepted') 'Reactive ECCM must remain accepted.'
$rejected = @($doctrines | Where-Object { [string]$_.id -eq 'tl1-ew-preserve-offense-v1' })
Assert-True ($rejected.Count -eq 1 -and [string]$rejected[0].status -eq 'rejected') 'Preserve-offense must remain recorded as rejected evidence.'
Assert-True (@($doctrines | Where-Object { [bool]$_.informationPolicy.usesHiddenEnemyRatings }).Count -eq 0) 'AI doctrine must preserve player information parity.'
$cp73Evidence = @($registry.evidence | Where-Object { [string]$_.checkpoint -eq '73' })
Assert-True ($cp73Evidence.Count -eq 3 -and @($cp73Evidence | Where-Object { [string]$_.resultSha256 -ne '667b553760b16ec63a67db52748a98bcb6daf7640bce21b3b7e4fc7d88da8613' }).Count -eq 0) 'CP73 doctrine evidence hash/provenance mismatch.'

$schema = Read-Json 'docs/design/player_technology/tl1_integrated_tactical_combat_schema_v0_18.json'
Assert-True ([string]$schema.'$id' -eq 'star-cluster-tl1-integrated-tactical-combat-schema-v0-18' -and $null -ne $schema.'$defs'.variant.properties.sideAAllowsApproximateDirectFire -and $null -ne $schema.'$defs'.variant.properties.sideAApproximateDirectFireAccuracyPenalty) 'Checkpoint 74c integrated schema degraded-fire controls missing.'

$study = Read-Json 'src/StarCluster.ScenarioRunner/Scenarios/TL1Calibration/tl1-itc16-approximate-track-degraded-fire.json'
Assert-True ([string]$study.id -eq 'tl1-itc16-approximate-track-degraded-fire' -and [int]$study.trialsPerVariant -eq 10000 -and @($study.variants).Count -eq 20 -and [int64]$study.masterSeed -eq 740100) 'Checkpoint 74c study identity/workload mismatch.'
$variants = @($study.variants)
foreach ($group in @($variants | Group-Object comparisonGroup)) {
    Assert-True ($group.Count -eq 5) "CP74c group '$($group.Name)' must contain five variants."
}
Assert-True (@($variants | Where-Object { [string]$_.profileLabel -eq 'firm-reference' }).Count -eq 4 -and @($variants | Where-Object { [string]$_.profileLabel -eq 'approx-firm-only' }).Count -eq 4 -and @($variants | Where-Object { [string]$_.profileLabel -match '^approx-p(10|20|30)$' }).Count -eq 12) 'Checkpoint 74c control/penalty coverage mismatch.'
Assert-True (@($variants | Where-Object { [string]$_.sideAFamily -eq 'Missile' -or [string]$_.sideBFamily -eq 'Missile' }).Count -eq 0) 'Checkpoint 74c degraded-fire study must exclude missiles.'

# CP74c retains the CP74a cross-file degraded-fire contract correction. The implementation places the
# public AccuracyModifier on the result record, while DirectFireTargetEligibility
# carries the lowercase accuracyModifier plumbing into that result. Validate the
# actual cross-file contract instead of requiring the public property name to
# appear in the wrong source file.
$core = Get-Content -LiteralPath (Join-Path $repositoryRoot 'src/StarCluster.Core/Combat/DirectFire/DirectFireWeaponProfile.cs') -Raw
$elig = Get-Content -LiteralPath (Join-Path $repositoryRoot 'src/StarCluster.Core/Combat/DirectFire/DirectFireTargetEligibility.cs') -Raw
$eligResult = Get-Content -LiteralPath (Join-Path $repositoryRoot 'src/StarCluster.Core/Combat/DirectFire/DirectFireTargetEligibilityResult.cs') -Raw
$trackElig = Get-Content -LiteralPath (Join-Path $repositoryRoot 'src/StarCluster.Core/Combat/Tracking/DirectFireTrackEligibility.cs') -Raw
$eligTests = Get-Content -LiteralPath (Join-Path $repositoryRoot 'tests/StarCluster.Tests/Combat/DirectFire/DirectFireTargetEligibilityTests.cs') -Raw
$runner = Get-Content -LiteralPath (Join-Path $repositoryRoot 'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs') -Raw
Assert-True ($core.Contains('AllowsApproximateTrackFire') -and $core.Contains('ApproximateTrackAccuracyPenalty')) 'Core weapon degraded-fire trait missing.'
Assert-True ($elig.Contains('TacticalTrackQuality.Approximate') -and $elig.Contains('weapon.AllowsApproximateTrackFire') -and $elig.Contains('weapon.ApproximateTrackAccuracyPenalty') -and $elig.Contains('accuracyModifier')) 'Core degraded-fire eligibility calculation/plumbing missing.'
Assert-True ($eligResult.Contains('AccuracyModifier') -and $eligResult.Contains('UsesApproximateTrackFire')) 'Core degraded-fire eligibility result fields missing.'
Assert-True ($trackElig.Contains('TacticalTrackQuality.Approximate') -and $trackElig.Contains('weapon.AllowsApproximateTrackFire')) 'Core track eligibility degraded-fire opt-in missing.'
Assert-True ($eligTests.Contains('TraitWeaponMayFireOnApproximateTrackWithListedPenalty') -and $eligTests.Contains('Assert.Equal(-20, result.AccuracyModifier)') -and $eligTests.Contains('TraitWeaponFirmTrackUsesNoDegradedFirePenalty') -and $eligTests.Contains('MissileInterceptionRemainsFirmOnlyEvenForTraitWeapon')) 'Core degraded-fire deterministic regression coverage missing.'
Assert-True ($runner.Contains('Tl1ApproximateTrackDegradedFireStudyId') -and $runner.Contains('WriteTl1ApproximateTrackDegradedFireReview') -and $runner.Contains('approximateTrackAccuracyPenalty')) 'Integrated CP74c study wiring missing.'
Assert-True (-not $runner.Contains('Tl1OperationalSensorEnvelope')) 'CP74c stale nonexistent Tl1OperationalSensorEnvelope type must not remain in ScenarioRunner.'
Assert-True ($runner.Contains('IReadOnlyDictionary<string, SensorEwFoundationProfile> sensorEwProfiles)')) 'CP74c degraded-fire validator must use the loaded SensorEwFoundationProfile catalog type.'
Assert-True ($runner.Contains('private static double ConditionalSideAWinPercent(')) 'CP74c degraded-fire review writer must include its conditional Side-A win helper.'
Assert-True ($runner.Contains('private static WeaponFamily[] RequiredWeaponFamiliesForStudy(string studyId)')) 'CP74c shared family-coverage helper missing.'
Assert-True ($runner.Contains('studyId == Tl1ApproximateTrackDegradedFireStudyId') -and $runner.Contains('? new[] { WeaponFamily.Kinetic, WeaponFamily.Energy }') -and $runner.Contains(': new[] { WeaponFamily.Kinetic, WeaponFamily.Energy, WeaponFamily.Missile }')) 'CP74c must require Kinetic/Energy for the degraded-fire study while preserving three-family coverage for existing integrated studies.'
Assert-True ($runner.Contains('RequiredWeaponFamiliesForStudy(study.Id)') -and $runner.Contains('weapon-family coverage:')) 'CP74c release gate and preflight status must consume the same study-aware family scope.'

# Release-gate-only hotfix: freeze CP74 mechanics, study, doctrine registry, Concept,
# deterministic tests, and the corrected ScenarioRunner after the study-aware family-scope fix.
$cp74FrozenHashes = @{
    'src/StarCluster.Core/Combat/DirectFire/DirectFireWeaponProfile.cs' = '489424003edc74f046c799dcb7cb04653b2b083f68a8f0efe79ecfe47d4a0ea0'
    'src/StarCluster.Core/Combat/DirectFire/DirectFireTargetEligibility.cs' = 'b4bee53b3ff506dbf94fd3e5bc0eef3110be336b73c7b4a46dfc1841497eadb7'
    'src/StarCluster.Core/Combat/DirectFire/DirectFireTargetEligibilityResult.cs' = '96833294e88e8c55fe92afd7971a311a0834426df0dac5b08184e41fd67803aa'
    'src/StarCluster.Core/Combat/Tracking/DirectFireTrackEligibility.cs' = '8fbf1a553ccf4a6460b92d532e0e701af062332281fd259558587a84e66349ed'
    'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatDocuments.cs' = '7984535b5fc2b19cd76f253514b6b04cf522a8b47f55f86aac5cd4bdaf6c133c'
    'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs' = '7408e21160a110952748a9e5019406855f7d63701784446350c30bf9249b7060'
    'src/StarCluster.ScenarioRunner/Scenarios/TL1Calibration/tl1-itc16-approximate-track-degraded-fire.json' = '30ee161f598bbe4ced7d9ae197564ac941247fd0b86d08964f52e8dafcd68840'
    'docs/design/player_technology/tl1_integrated_tactical_combat_schema_v0_18.json' = 'd97943ea093e70b0cbd0c16a8176cbf2bb09c509b96cbd2c301c7504b6bd5add'
    'docs/archive/ai/pre-cp165-active/ai_doctrine_registry_v0_2.json' = 'c4a54db2fe84f2487efdb4998f8d17de0a029aaaaf71e13d10f493a90f69068a'
    'docs/Star_Cluster_Game_Concept_v0.6m.docx' = '6d526965af54ed7a6c51a38483ab830f41c3e7341b73416f908eb3d2f94ebbf5'
    'tests/StarCluster.Tests/Combat/DirectFire/DirectFireTargetEligibilityTests.cs' = 'eead08a6ddd3baa31a2b32f4c83498556711cd2ccc8178bc72f39f903ac13423'
}
foreach ($entry in $cp74FrozenHashes.GetEnumerator()) {
    $actual = (Get-FileHash -LiteralPath (Join-Path $repositoryRoot $entry.Key) -Algorithm SHA256).Hash.ToLowerInvariant()
    Assert-True ($actual -eq [string]$entry.Value) "CP74c release-gate-only hotfix changed frozen CP74 authority/input: $($entry.Key)."
}

$concepts = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs') -File -Filter 'Star_Cluster_Game_Concept_v*.docx')
Assert-True ($concepts.Count -eq 1 -and $concepts[0].Name -eq 'Star_Cluster_Game_Concept_v0.6m.docx') 'Checkpoint 74c must expose exactly one active Concept v0.6m.'
Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot 'docs/archive/Star_Cluster_Game_Concept_v0.6l.docx') -PathType Leaf) 'Checkpoint 74c must retain archived Concept v0.6l.'

$validationFiles = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs\validation') -File -Filter 'Checkpoint_*.md')
Assert-True ($validationFiles.Count -eq 1 -and $validationFiles[0].Name -eq 'Checkpoint_74c_Degraded_Fire_Family_Coverage_Gate_Hotfix.md') 'Exactly one Checkpoint 74c active family-coverage hotfix validation runbook must remain.'
$rootTxt = @(Get-ChildItem -LiteralPath $repositoryRoot -File -Filter '*.txt')
Assert-True ($rootTxt.Count -eq 1 -and $rootTxt[0].Name -eq 'CHECKPOINT_74C_SHA256SUMS.txt') 'Repository root must contain only CHECKPOINT_74C_SHA256SUMS.txt as .txt.'

Write-Host '       Checkpoint 74c hotfix scope: release-gate-only; CP74 mechanics, study, doctrine registry, and Concept remain frozen.'
Write-Host '       Shared weapon-family coverage is study-aware: CP74 requires Kinetic/Energy; existing integrated studies retain Kinetic/Energy/Missile.'
Write-Host '       Checkpoint 74 study remains 20 one-trial smoke executions plus 20 substantive variants / 200,000 default trials; production weapons remain Firm-only.'
Write-Host 'Checkpoint 74c degraded-fire family-coverage gate hotfix validation passed.'
