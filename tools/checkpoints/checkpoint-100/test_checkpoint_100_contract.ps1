[CmdletBinding()]
param([string]$RepositoryRoot)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($RepositoryRoot)) { $repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path } else { $repositoryRoot = (Resolve-Path $RepositoryRoot).Path }

function Assert-True { param([bool]$Condition,[string]$Message) if (-not $Condition) { throw $Message } }
function RelPath { param([string]$RelativePath) Join-Path $repositoryRoot ($RelativePath.Replace('/','\')) }
function Read-Text { param([string]$RelativePath) $p=RelPath $RelativePath; Assert-True (Test-Path -LiteralPath $p -PathType Leaf) "Required file '$RelativePath' is missing."; [IO.File]::ReadAllText($p) }
function Read-Json { param([string]$RelativePath) (Read-Text $RelativePath) | ConvertFrom-Json }
function Hash-Rel { param([string]$RelativePath) (Get-FileHash -LiteralPath (RelPath $RelativePath) -Algorithm SHA256).Hash.ToLowerInvariant() }
function Require-Contains { param([string]$Text,[string]$Needle,[string]$Message) Assert-True ($Text.IndexOf($Needle,[StringComparison]::Ordinal) -ge 0) $Message }
function Require-NotContains { param([string]$Text,[string]$Needle,[string]$Message) Assert-True ($Text.IndexOf($Needle,[StringComparison]::Ordinal) -lt 0) $Message }
function Read-Manifest {
    param([string]$RelativePath)
    $map=@{}; $lines=@(Get-Content -LiteralPath (RelPath $RelativePath)); $n=0
    foreach($line in $lines){
        $n++; $m=[regex]::Match([string]$line,'^([0-9a-fA-F]{64})  (.+)$')
        Assert-True $m.Success "Manifest '$RelativePath' malformed at line $n."
        $r=$m.Groups[2].Value.Replace('\','/')
        Assert-True (-not $map.ContainsKey($r)) "Manifest '$RelativePath' duplicates '$r'."
        $map[$r]=$m.Groups[1].Value.ToLowerInvariant()
    }
    [pscustomobject]@{ EntryCount=$map.Count; PhysicalLineCount=$lines.Count; Entries=$map }
}
function Assert-Sequence { param($Actual,[string[]]$Expected,[string]$Message) $a=@($Actual); Assert-True ($a.Count -eq $Expected.Count) $Message; for($i=0;$i -lt $Expected.Count;$i++){ Assert-True ([string]$a[$i] -eq $Expected[$i]) $Message } }
function Assert-ExactFileSet { param([string]$RelativeDirectory,[string[]]$Expected) $a=@(Get-ChildItem -LiteralPath (RelPath $RelativeDirectory) -File | ForEach-Object Name | Sort-Object); $w=@($Expected|Sort-Object); Assert-True ($a.Count -eq $w.Count) "Directory '$RelativeDirectory' active file count drifted."; for($i=0;$i -lt $w.Count;$i++){ Assert-True ($a[$i] -eq $w[$i]) "Directory '$RelativeDirectory' active file set drifted: expected '$($w[$i])', found '$($a[$i])'." } }

Write-Host '       Validating native dependencies, wrapper interface, and checkpoint definitions...'
$normalRel='tools/calibration/checkpoints/checkpoint-100.json'
$deepRel='tools/calibration/checkpoints/checkpoint-100-deep-calibration.json'
$guarded=@(
    'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
    'tools/checkpoints/checkpoint-100/apply_checkpoint_100.ps1',
    'tools/checkpoints/checkpoint-100/test_checkpoint_100_contract.ps1',
    'tools/calibration/run_calibration_checkpoint.ps1'
)
& (RelPath 'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1') -RepositoryRoot $repositoryRoot -PowerShellPaths $guarded -CheckpointDefinitionPaths @($normalRel,$deepRel)
$apply=Read-Text 'tools/checkpoints/checkpoint-100/apply_checkpoint_100.ps1'
$typeCall='Assert-Cp100PowerShell51TypeCompatibility -Paths @($MyInvocation.MyCommand.Path, $contract)'
Require-Contains $apply 'function Assert-Cp100PowerShell51TypeCompatibility' 'CP100 wrapper must define the Windows PowerShell 5.1 type-token compatibility precheck.'
Require-Contains $apply $typeCall 'CP100 wrapper must invoke the Windows PowerShell 5.1 type-token compatibility precheck.'
Assert-True ($apply.IndexOf($typeCall,[StringComparison]::Ordinal) -lt $apply.IndexOf('& $guard -RepositoryRoot',[StringComparison]::Ordinal)) 'CP100 PowerShell 5.1 type-token precheck must run before the shared dependency guard.'
Assert-True ($apply.IndexOf('& $guard -RepositoryRoot',[StringComparison]::Ordinal) -lt $apply.IndexOf('& $contract -RepositoryRoot',[StringComparison]::Ordinal)) 'CP100 dependency guard must run before the repository contract.'
Assert-True ($apply.IndexOf('& $contract -RepositoryRoot',[StringComparison]::Ordinal) -lt $apply.IndexOf('& $harness -CheckpointDefinition',[StringComparison]::Ordinal)) 'CP100 repository contract must run before the checkpoint harness.'
Require-Contains $apply 'unreviewed token' 'CP100 wrapper must explicitly reject unreviewed PowerShell type tokens.'
Require-Contains $apply '& $harness -CheckpointDefinition $definition -Trials $Trials -Jobs $Jobs -RepositoryOnly:$RepositoryOnly -NoClean:$NoClean' 'CP100 wrapper must preserve direct named-parameter harness invocation.'
Assert-True (-not [regex]::IsMatch($apply,'&\s+\$harness\s+@[A-Za-z_]',[System.Text.RegularExpressions.RegexOptions]::IgnoreCase)) 'CP100 wrapper must not splat harness arguments.'

$stageIds=@(
    'deterministic','tl1-phase-a','tl1-phase-b','tl1-installation-space-envelope','tl1-sensor-ew-foundation',
    'cross-tl-cp99-exact-edge-preflight','cross-tl-cp99-exact-edge-generation','auxiliary-resource-endurance',
    'checkpoint-53-resource-semantics-lock','runner-self-tests'
)
foreach($d in @((Read-Json $normalRel),(Read-Json $deepRel))){
    Assert-True ([string]$d.checkpointId -eq '100' -and [string]$d.manifestFile -eq 'CHECKPOINT_100_SHA256SUMS.txt') 'CP100 definition/manifest binding mismatch.'
    Assert-True ([string]$d.sdkVersion -eq '8.0.423' -and [string]$d.outputRoot -eq 'out/checkpoint-100') 'CP100 SDK/outputRoot mismatch.'
    Assert-True ([int]$d.defaultTrials -eq 250 -and [int]$d.defaultJobs -eq 24) 'CP100 default trials/jobs mismatch.'
    Assert-True (@($d.stages).Count -eq 10 -and [int]$d.checkpointMetrics.stageCount -eq 10) 'CP100 must configure exactly 10 runner stages.'
    Assert-Sequence @($d.stages|ForEach-Object{[string]$_.id}) $stageIds 'CP100 stage order drifted.'
    Assert-Sequence @($d.nativeDependencyPrecheck.powerShellPaths) $guarded 'CP100 guarded PowerShell path list drifted.'
    Assert-Sequence @($d.nativeDependencyPrecheck.checkpointDefinitionPaths) @($normalRel,$deepRel) 'CP100 guarded definition list drifted.'
    Assert-True ([long]$d.checkpointMetrics.trialsAtDefault -eq 0 -and [long]$d.checkpointMetrics.smokeTrialsAtDefault -eq 0 -and [long]$d.checkpointMetrics.totalTrialExecutionsAtDefault -eq 0) 'CP100 must run no stochastic trials.'
    Assert-True ([int]$d.checkpointMetrics.monteCarloVariantCount -eq 0 -and [int]$d.checkpointMetrics.expectedXunitTests -eq 876 -and [int]$d.checkpointMetrics.expectedRunnerSelfTests -eq 63) 'CP100 deterministic acceptance metrics mismatch.'
    Assert-True ([string]$d.checkpointMetrics.acceptedExecutableFoundation -eq 'cross-tl-build-permutation-foundation-v0_8' -and [int]$d.checkpointMetrics.acceptedLegalBuildCount -eq 11776 -and [int]$d.checkpointMetrics.acceptedProgressionLegalEdges -eq 37184) 'CP100 must retain the accepted CP99 executable cross-progression foundation.'
    Assert-True ([bool]$d.checkpointMetrics.tl3CoreCandidateRegistered -and -not [bool]$d.checkpointMetrics.tl3CombatConsumerEnabled -and [bool]$d.checkpointMetrics.newTl3Values) 'CP100 must register TL3 candidates without runtime activation.'
    Assert-True (-not [bool]$d.checkpointMetrics.initiativeRuleChanged -and -not [bool]$d.checkpointMetrics.deepCalibrationApplicable -and -not [bool]$d.checkpointMetrics.technologyPromotionAutomatic) 'CP100 authority-boundary metrics drifted.'
}

Write-Host '       Validating accepted Checkpoint 99 provenance and frozen executable surface...'
$acceptedManifestRel='docs/validation/evidence/checkpoint-99/CHECKPOINT_99_SHA256SUMS.txt'
Assert-True ((Hash-Rel $acceptedManifestRel) -eq 'f04186733fa1631bc0ee8384fe4e49f18e65dc07aba04e877773e402d4d56894') 'Archived accepted CP99 manifest hash mismatch.'
$accepted=Read-Json 'docs/validation/evidence/checkpoint-99/checkpoint-99-native-acceptance-summary.json'
Assert-True ([string]$accepted.status -eq 'Success' -and [string]$accepted.sdk.actual -eq '8.0.423') 'Accepted CP99 native status/SDK evidence mismatch.'
Assert-True ([string]$accepted.checkpointDefinitionSha256 -eq 'e5bf5312ab520a425df0fbf63d796e98f35b51d5110260edab1856f54af7d508' -and [string]$accepted.checkpointManifestSha256 -eq 'f04186733fa1631bc0ee8384fe4e49f18e65dc07aba04e877773e402d4d56894') 'Accepted CP99 definition/manifest provenance mismatch.'
Assert-True ([int]$accepted.tests.passed -eq 876 -and [int]$accepted.tests.failed -eq 0 -and [int]$accepted.aggregates.runnerStagesPassed -eq 23 -and [int]$accepted.aggregates.selfTests -eq 63 -and [int]$accepted.aggregates.failedGates -eq 0 -and [long]$accepted.aggregates.trials -eq 184160) 'Accepted CP99 native metric evidence mismatch.'
$edgeEvidence=Read-Json 'docs/validation/evidence/checkpoint-99/cp99-exact-edge-progression-evidence.json'
Assert-True ([string]$edgeEvidence.status -eq 'accepted_native_windows' -and [string]$edgeEvidence.nativeResultsZipSha256 -eq '333ac8ee2f2f21aececfd4567556cd074d7f147d345c9272801e55f8f2abe3c4' -and [string]$edgeEvidence.substantiveStudy.summarySha256 -eq 'dd05e92896a273f55ea486e3ba8cbe340556fde75a018e19aea1e1877f9849a0') 'CP99 exact-edge evidence provenance mismatch.'

$acceptedManifest=Read-Manifest $acceptedManifestRel
Assert-True ($acceptedManifest.EntryCount -eq 1920) 'Accepted CP99 manifest must contain 1,920 entries.'
$allowedCp100Changes=@{
    'CHAT_README.md'=$true; 'README.md'=$true; 'docs/Prototype_TODO.md'=$true; 'docs/README.md'=$true;
    'docs/Star_Cluster_Game_Concept_v0.7a.docx'=$true; 'docs/design/README.md'=$true;
    'docs/design/player_technology/README.md'=$true; 'docs/design/player_technology/StarCluster_Technology_Architecture_Matrix_v1.xlsx'=$true;
    'docs/design/player_technology/Technology_Architecture_Matrix_v1.md'=$true; 'docs/archive/player_technology/pre-cp165-active/auxiliary_component_catalog_v0_1.json'=$true;
    'docs/archive/player_technology/pre-cp165-active/component_installation_space_catalog_v1.json'=$true; 'docs/archive/player_technology/pre-cp165-active/technology_architecture_matrix_v1.json'=$true;
    'docs/design/player_technology/checkpoint_54_tl3_runtime_profile_candidates_v0_1.json'=$true;
    'docs/design/player_technology/checkpoint_55_tl3_lowtech_profile_candidates_v0_1.json'=$true;
    'docs/design/testing/README.md'=$true; 'docs/design/testing/Checkpoint_99_Validation_Tiers.md'=$true;
    'docs/design/testing/Technology_Integration_Permutation_Suite_Architecture_v0_14.md'=$true;
    'docs/design/testing/checkpoint_99_validation_suite_policy_v0_1.json'=$true;
    'docs/design/testing/technology_integration_permutation_suite_v0_14.json'=$true;
    'docs/development/Simulation_Development_Guidelines.md'=$true; 'docs/validation/README.md'=$true;
    'docs/validation/Checkpoint_99_Mandatory_Sensor_And_Exact_Edge_Progression_Screening.md'=$true
}
$frozen=0
foreach($entry in $acceptedManifest.Entries.GetEnumerator()){
    $rel=[string]$entry.Key
    if($allowedCp100Changes.ContainsKey($rel)){ continue }
    Assert-True (Test-Path -LiteralPath (RelPath $rel) -PathType Leaf) "CP100 changed or removed frozen CP99 path '$rel'."
    Assert-True ((Hash-Rel $rel) -eq [string]$entry.Value) "CP100 changed frozen CP99 path '$rel'."
    $frozen++
}
Assert-True ($frozen -eq 1898) 'CP100 frozen CP99 file count drifted.'
foreach($rel in @(
    'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/cross-tl-build-permutation-foundation-v0_8.json',
    'tools/calibration/checkpoints/checkpoint-99.json','tools/calibration/checkpoints/checkpoint-99-deep-calibration.json',
    'tools/checkpoints/checkpoint-99/apply_checkpoint_99.ps1','tools/checkpoints/checkpoint-99/test_checkpoint_99_contract.ps1'
)){
    Assert-True ((Hash-Rel $rel) -eq [string]$acceptedManifest.Entries[$rel]) "Accepted CP99 executable/acceptance authority '$rel' changed."
}

Write-Host '       Validating archived superseded authorities byte-for-byte...'
$archivePairs=@(
    @('docs/Star_Cluster_Game_Concept_v0.7a.docx','docs/archive/concepts/Star_Cluster_Game_Concept_v0.7a.docx'),
    @('docs/design/testing/Technology_Integration_Permutation_Suite_Architecture_v0_14.md','docs/archive/testing/Technology_Integration_Permutation_Suite_Architecture_v0_14.md'),
    @('docs/design/testing/technology_integration_permutation_suite_v0_14.json','docs/archive/testing/technology_integration_permutation_suite_v0_14.json'),
    @('docs/design/testing/Checkpoint_99_Validation_Tiers.md','docs/archive/testing/Checkpoint_99_Validation_Tiers.md'),
    @('docs/design/testing/checkpoint_99_validation_suite_policy_v0_1.json','docs/archive/testing/checkpoint_99_validation_suite_policy_v0_1.json'),
    @('docs/validation/Checkpoint_99_Mandatory_Sensor_And_Exact_Edge_Progression_Screening.md','docs/validation/archive/Checkpoint_99_Mandatory_Sensor_And_Exact_Edge_Progression_Screening.md'),
    @('docs/design/player_technology/checkpoint_54_tl3_runtime_profile_candidates_v0_1.json','docs/archive/player_technology/studies/checkpoint_54_tl3_runtime_profile_candidates_v0_1.json'),
    @('docs/design/player_technology/checkpoint_55_tl3_lowtech_profile_candidates_v0_1.json','docs/archive/player_technology/studies/checkpoint_55_tl3_lowtech_profile_candidates_v0_1.json')
)
foreach($pair in $archivePairs){
    $old=[string]$pair[0]; $arch=[string]$pair[1]
    Assert-True (-not (Test-Path -LiteralPath (RelPath $old) -PathType Leaf)) "Superseded active authority '$old' must be removed."
    Assert-True (Test-Path -LiteralPath (RelPath $arch) -PathType Leaf) "Archived authority '$arch' is missing."
    Assert-True ((Hash-Rel $arch) -eq [string]$acceptedManifest.Entries[$old]) "Archived authority '$arch' is not byte-identical to accepted CP99 '$old'."
}

Write-Host '       Validating TL3 core candidate values and progression semantics...'
$tl3=Read-Json 'docs/design/player_technology/tl3_core_technology_candidates_v0_1.json'
Assert-True ([string]$tl3.status -eq 'initial_conceptual_candidates' -and -not [bool]$tl3.progressionSemantics.tl3CoreIsCompleteShipPackage -and -not [bool]$tl3.progressionSemantics.sameSpaceTransitionRequired) 'TL3 profile status/progression semantics mismatch.'
$tc=$tl3.tl3Candidates.tacticalComputer
Assert-True ([int]$tc.ordinaryTargetingAssistanceOperationalPp -eq 12 -and [int]$tc.approximateTrackPenaltyPp -eq -25 -and [int]$tc.evasiveCompensationPp -eq 5 -and [int]$tc.installationSpace -eq 3) 'TL3 Tactical Computer candidate mismatch.'
$sensor=$tl3.tl3Candidates.sensor
Assert-True ([int]$sensor.discriminationResistance -eq 1 -and [int]$sensor.passiveFirm -eq 1 -and [int]$sensor.passiveApproximate -eq 3 -and @($sensor.normalActiveModes).Count -eq 2 -and [string]$sensor.overloadBeyondHighActive -eq 'deferred_not_promoted') 'TL3 Sensor base candidate mismatch.'
$low=@($sensor.normalActiveModes|Where-Object id -eq 'low'); $high=@($sensor.normalActiveModes|Where-Object id -eq 'high')
Assert-True ($low.Count -eq 1 -and [int]$low[0].firm -eq 3 -and [int]$low[0].approximate -eq 4 -and [int]$low[0].tacticalPower -eq 1 -and [int]$low[0].strain -eq 0) 'TL3 Sensor Low Active mismatch.'
Assert-True ($high.Count -eq 1 -and [int]$high[0].firm -eq 4 -and [int]$high[0].approximate -eq 5 -and [int]$high[0].tacticalPower -eq 2 -and [int]$high[0].strain -eq 0) 'TL3 Sensor High Active mismatch.'
foreach($ew in @($tl3.tl3Candidates.ecm,$tl3.tl3Candidates.eccm)){
    Assert-True ([int]$ew.normalRatingCeiling -eq 2 -and [int]$ew.fullStrengthNormalTp -eq 1 -and [int]$ew.installationSpace -eq 1 -and -not [bool]$ew.sameTypeRatingsAdditive -and [string]$ew.sameTypeResolution -eq 'highest_applicable_functional_rating' -and [string]$ew.overload -eq 'deferred_not_promoted') 'TL3 ECM/ECCM efficiency candidate mismatch.'
}
$reactor=$tl3.tl3Candidates.powerReactor
Assert-True ([int]$reactor.installationSpace -eq 5 -and [int]$reactor.operationalTacticalPower -eq 6 -and [int]$reactor.degradedTacticalPowerHeld -eq 3 -and [int]$reactor.disabledEmergencyTacticalPowerHeld -eq 1 -and [int]$reactor.destroyedTacticalPowerHeld -eq 0) 'TL3 Mature Compact Fusion candidate mismatch.'
$shield=$tl3.tl3Candidates.shield
Assert-True ([int]$shield.primaryShield.installationSpace -eq 3 -and [int]$shield.primaryShield.shieldCapacity -eq 3 -and [int]$shield.primaryShield.shieldArmor -eq 0) 'TL3 primary Shield hold mismatch.'
Assert-True ([int]$shield.shieldHardener.installationSpace -eq 1 -and [int]$shield.shieldHardener.normalShieldArmor -eq 1 -and [int]$shield.shieldHardener.sustainedTacticalPower -eq 1 -and [string]$shield.shieldHardener.stacking -eq 'nonstacking_normal_operation' -and [string]$shield.shieldHardener.overload -eq 'deferred_not_promoted' -and $null -eq $shield.shieldHardener.externalPowerTlPrerequisite) 'TL3 Shield Hardener candidate mismatch.'
$armor=$tl3.tl3Candidates.armor
Assert-True ([int]$armor.installationSpace -eq 0 -and [int]$armor.armorProtection -eq 1 -and [int]$armor.armorIntegrity -eq 5) 'TL3 Armor AP1/AI5 candidate mismatch.'
Assert-True ([int]$tl3.weaponPenetrationHeld.kinetic.shieldPenetration -eq 1 -and [int]$tl3.weaponPenetrationHeld.kinetic.armorPenetration -eq 1 -and [int]$tl3.weaponPenetrationHeld.energy.shieldPenetration -eq 1 -and [int]$tl3.weaponPenetrationHeld.energy.armorPenetration -eq 1 -and [int]$tl3.weaponPenetrationHeld.missile.shieldPenetration -eq 1 -and [int]$tl3.weaponPenetrationHeld.missile.armorPenetration -eq 2) 'TL3 held weapon penetration profiles drifted.'
Assert-True (@($tl3.deferredOutsideThisPackage).Count -ge 5) 'TL3 profile must preserve deliberately deferred weapon/PDS/propulsion/broader-AUX work.'

$matrix=Read-Json 'docs/archive/player_technology/pre-cp165-active/technology_architecture_matrix_v1.json'
Assert-True ([int]$matrix.checkpoint -eq 100 -and [string]$matrix.authority.concept -eq 'docs/Star_Cluster_Game_Concept_v0.7b.docx') 'Technology Matrix CP100 authority mismatch.'
Assert-True ([string]$matrix.integrationCoverage.standingPermutationSuite -eq 'v0.15' -and [string]$matrix.integrationCoverage.crossTlBuildFoundation -like 'v0.8*' -and -not [bool]$matrix.integrationCoverage.tl3CombatConsumerEnabled) 'Technology Matrix TL3 integration boundary mismatch.'
Assert-True ([int]$matrix.integrationCoverage.legalBuildCount -eq 11776 -and [int]$matrix.integrationCoverage.progressionLatticeLegalEdges -eq 37184 -and [int]$matrix.integrationCoverage.exactEdgeStratumCount -eq 181 -and [int]$matrix.integrationCoverage.exactEdgeLogicalPairings -eq 362 -and [int]$matrix.integrationCoverage.boundedCombatScreenVariants -eq 724) 'Technology Matrix must retain accepted CP99 executable counts.'
$tl2=@($matrix.tiers|Where-Object technologyLevel -eq 2); Assert-True ($tl2.Count -eq 1) 'Technology Matrix TL2 tier missing.'
Assert-True ([string]$tl2[0].shield.status -eq 'cross_tl_validated_candidate' -and [string]$tl2[0].armor.status -eq 'cross_tl_validated_candidate') 'CP100 must carry CP99 Shield/Armor cross-TL candidate status.'
$tl3Matrix=@($matrix.tiers|Where-Object technologyLevel -eq 3); Assert-True ($tl3Matrix.Count -eq 1 -and [int]$tl3Matrix[0].powerReactor.installationSpace -eq 5 -and [int]$tl3Matrix[0].armor.armorProtection -eq 1) 'Technology Matrix TL3 tier mismatch.'

$catalog=Read-Json 'docs/archive/player_technology/pre-cp165-active/component_installation_space_catalog_v1.json'
Assert-True ([int]$catalog.globalRules.minimumMainWeaponCount -eq 1 -and [int]$catalog.globalRules.minimumReactorCount -eq 1 -and [int]$catalog.globalRules.minimumSensorCount -eq 1) 'Mandatory Weapon/Reactor/Sensor construction core drifted.'
$r3=@($catalog.components|Where-Object id -eq 'main_reactor_tl3'); $hard=@($catalog.components|Where-Object id -eq 'shield_hardener_tl3')
Assert-True ($r3.Count -eq 1 -and [int]$r3[0].installationSpace -eq 5 -and [string]$r3[0].status -eq 'conceptual_candidate') 'TL3 Main Reactor catalog entry mismatch.'
Assert-True ($hard.Count -eq 1 -and [int]$hard[0].installationSpace -eq 1 -and [int]$hard[0].maximumCount -eq 1 -and -not [bool]$hard[0].multiplicityAllowed -and [string]$hard[0].status -eq 'conceptual_candidate') 'TL3 Shield Hardener catalog entry mismatch.'
$aux=Read-Json 'docs/archive/player_technology/pre-cp165-active/auxiliary_component_catalog_v0_1.json'; $auxHard=@($aux.components|Where-Object id -eq 'aux_shield_hardener')
Assert-True ($auxHard.Count -eq 1 -and [int]$auxHard[0].candidateFirstStandardItemTl -eq 3 -and [int]$auxHard[0].minimumPrimaryResearchTl -eq 3 -and [int]$auxHard[0].minimumHullTl -eq 1 -and @($auxHard[0].supportFloors).Count -eq 0 -and [int]$auxHard[0].capacityCost -eq 1 -and [int]$auxHard[0].tacticalPowerBehavior.amount -eq 1 -and [string]$auxHard[0].availabilityStatus -eq 'tl3_conceptual_candidate') 'TL3 Auxiliary Shield Hardener catalog mismatch.'

$suite=Read-Json 'docs/design/testing/technology_integration_permutation_suite_v0_15.json'
Assert-True ([string]$suite.id -eq 'technology-integration-permutation-suite-v0_15' -and [string]$suite.tl3CandidateRegistration.status -eq 'registered_not_combat_consumer_enabled' -and -not [bool]$suite.tl3CandidateRegistration.completeTl3ShipPackage) 'Standing suite v0.15 TL3 registration status mismatch.'
Assert-True ([string]$suite.tl3CandidateRegistration.currentExecutableFoundation -eq 'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/cross-tl-build-permutation-foundation-v0_8.json' -and @($suite.tl3CandidateRegistration.registeredTransitions).Count -eq 7) 'Standing suite v0.15 executable-boundary/transition count mismatch.'
$ids=@($suite.tl3CandidateRegistration.registeredTransitions|ForEach-Object{[string]$_.id})
Assert-Sequence $ids @('computer-c2-to-c3','sensor-s2-to-s3','ecm-ecm2-to-ecm3','eccm-eccm2-to-eccm3','reactor-r2-to-r3','shield-sh2-to-tl3-hardener-unlock','armor-a2-to-a3') 'Standing suite v0.15 TL3 transition order drifted.'
$rr=@($suite.tl3CandidateRegistration.registeredTransitions|Where-Object id -eq 'reactor-r2-to-r3'); Assert-True ($rr.Count -eq 1 -and [string]$rr[0].kind -eq 'miniaturization' -and [int]$rr[0].installationSpaceDelta -eq -1) 'TL3 Reactor transition must be explicit -1 Space miniaturization.'
$sr=@($suite.tl3CandidateRegistration.registeredTransitions|Where-Object id -eq 'shield-sh2-to-tl3-hardener-unlock'); Assert-True ($sr.Count -eq 1 -and [string]$sr[0].kind -eq 'optional_component_unlock' -and [int]$sr[0].installationSpaceDelta -eq 1) 'TL3 Shield Hardener transition must remain an optional +1 Space unlock.'
Assert-True ([int]$suite.currentCoverage.legalBuildEnvelope.legalBuilds -eq 11776 -and [int]$suite.currentCoverage.progressionLattice.singleAxisLegalEdges -eq 37184 -and [int]$suite.currentCoverage.pairingSample.exactEdgeStrata -eq 181 -and [int]$suite.currentCoverage.currentStudy.variantCount -eq 724) 'Standing suite v0.15 must retain accepted CP99 executable coverage counts.'

$policy=Read-Json 'docs/design/testing/checkpoint_100_validation_suite_policy_v0_1.json'
Assert-True ([string]$policy.checkpoint -eq '100' -and -not [bool]$policy.mustAlwaysRun.cp99SubstantiveReplay -and -not [bool]$policy.mustAlwaysRun.newMonteCarloStudy -and [int]$policy.expected.xunitTests -eq 876 -and [int]$policy.expected.runnerStages -eq 10 -and [int]$policy.expected.scenarioRunnerSelfTests -eq 63 -and [long]$policy.expected.totalTrialExecutions -eq 0) 'CP100 validation policy mismatch.'
Assert-True (-not [bool]$policy.authorityBoundary.productionCombatDataChanged -and -not [bool]$policy.authorityBoundary.initiativeRuleChange -and -not [bool]$policy.authorityBoundary.tl3CombatMechanicsImplemented) 'CP100 policy must not claim runtime TL3 mechanics or initiative changes.'

Write-Host '       Validating current documentation authorities and no accidental TL3 runtime activation...'
Assert-ExactFileSet 'docs/design/testing' @('README.md','Checkpoint_100_Validation_Tiers.md','Technology_Integration_Permutation_Suite_Architecture_v0_15.md','checkpoint_100_validation_suite_policy_v0_1.json','technology_integration_permutation_suite_v0_15.json')
$activeConcept=@(Get-ChildItem -LiteralPath (RelPath 'docs') -File -Filter 'Star_Cluster_Game_Concept_v*.docx'); Assert-True ($activeConcept.Count -eq 1 -and $activeConcept[0].Name -eq 'Star_Cluster_Game_Concept_v0.7b.docx') 'Exactly one active Game Concept must remain and it must be v0.7b.'
$activeValidation=@(Get-ChildItem -LiteralPath (RelPath 'docs/validation') -File -Filter 'Checkpoint_*.md'); Assert-True ($activeValidation.Count -eq 1 -and $activeValidation[0].Name -eq 'Checkpoint_100_TL3_Core_Technology_Table_Foundation.md') 'Exactly one active validation runbook must remain and it must be CP100.'
$validationReadme=Read-Text 'docs/validation/README.md'; Require-Contains $validationReadme 'Checkpoint_100_TL3_Core_Technology_Table_Foundation.md' 'Validation README must point to CP100.'
$matrixMd=Read-Text 'docs/design/player_technology/Technology_Architecture_Matrix_v1.md'
foreach($needle in @('TL3','Mature Compact Fusion','6 TP','5 Space','Evasive Compensation','High Active','Shield Hardener','AP1','registered','not yet combat-consumer enabled','tl3CombatConsumerEnabled','remains false')){ Require-Contains $matrixMd $needle "Technology Matrix Markdown is missing TL3 authority text '$needle'." }
$suiteMd=Read-Text 'docs/design/testing/Technology_Integration_Permutation_Suite_Architecture_v0_15.md'
foreach($needle in @('registered','runtime activation','combat-consumer eligible','miniaturization','optional component unlock','CP99','executable baseline')){ Require-Contains $suiteMd $needle "Standing suite v0.15 architecture is missing semantic anchor '$needle'." }
$guidelines=Read-Text 'docs/development/Simulation_Development_Guidelines.md'
foreach($needle in @('same-Space','miniaturization','optional','registered transition','runtime activation','tiny')){ Require-Contains $guidelines $needle "Simulation Development Guidelines are missing progression-activation rule '$needle'." }
$runbook=Read-Text 'docs/validation/Checkpoint_100_TL3_Core_Technology_Table_Foundation.md'
foreach($needle in @('876','10 runner','63 ScenarioRunner','zero stochastic','v0.15','v0.8','TL3','tl3CombatConsumerEnabled')){ Require-Contains $runbook $needle "CP100 runbook is missing '$needle'." }
# CP100 does not modify any runtime C# source. The entire accepted CP99 src/ tree is already covered by the CP99 freeze above.
foreach($rel in $acceptedManifest.Entries.Keys){ if(([string]$rel).StartsWith('src/',[StringComparison]::Ordinal)){ Assert-True (-not $allowedCp100Changes.ContainsKey([string]$rel)) "CP100 may not whitelist runtime source '$rel'." } }

Write-Host '       Validating root manifest...'
$rootTxt=@(Get-ChildItem -LiteralPath $repositoryRoot -File -Filter '*.txt'); Assert-True ($rootTxt.Count -eq 1 -and $rootTxt[0].Name -eq 'CHECKPOINT_100_SHA256SUMS.txt') 'Repository root must contain only CHECKPOINT_100_SHA256SUMS.txt as .txt.'
$manifest=Read-Manifest 'CHECKPOINT_100_SHA256SUMS.txt'; Assert-True ($manifest.EntryCount -eq 1934 -and $manifest.PhysicalLineCount -eq 1934) 'CP100 manifest entry count mismatch.'; Assert-True (-not $manifest.Entries.ContainsKey('CHECKPOINT_100_SHA256SUMS.txt')) 'CP100 manifest must not contain itself.'
foreach($entry in $manifest.Entries.GetEnumerator()){
    Assert-True (Test-Path -LiteralPath (RelPath ([string]$entry.Key)) -PathType Leaf) "CP100 manifest entry '$($entry.Key)' is missing."
    Assert-True ((Hash-Rel ([string]$entry.Key)) -eq [string]$entry.Value) "CP100 manifest hash mismatch for '$($entry.Key)'."
}

Write-Host "Checkpoint 100 repository contracts passed ($frozen accepted CP99 files frozen; TL3 core candidate table and seven transition types registered; runtime TL3 activation remains disabled)."
