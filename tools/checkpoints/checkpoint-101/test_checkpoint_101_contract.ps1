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
function Require-Contains { param([string]$Text,[string]$Needle,[string]$Message) Assert-True ($Text.IndexOf($Needle,[StringComparison]::OrdinalIgnoreCase) -ge 0) $Message }
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
function Test-IsGeneratedOrLocalPath {
    param([string]$RelativePath)
    $path=$RelativePath.Replace('\','/')
    if($path -like '.git/*' -or $path -like '.vs/*' -or $path -like '.vscode/*' -or $path -like '.idea/*' -or $path -like 'out/*' -or $path -like 'src/StarCluster.Game/.godot/*' -or $path -match '(^|/)(bin|obj|TestResults)/'){ return $true }
    if($path -match '\.(user|userosscache|sln\.docstates|uid)$' -or $path -match '(^|/)\.suo$' -or $path -match '(^|/)(\.DS_Store|Thumbs\.db)$'){ return $true }
    return $false
}
function Get-Cp101RepositoryOwnedFileSet {
    $map=@{}
    foreach($file in @(Get-ChildItem -LiteralPath $repositoryRoot -Recurse -File -Force)){
        $rel=$file.FullName.Substring($repositoryRoot.Length).TrimStart('\','/').Replace('\','/')
        if($rel -eq 'CHECKPOINT_101_SHA256SUMS.txt'){ continue }
        if(Test-IsGeneratedOrLocalPath -RelativePath $rel){ continue }
        $map[$rel]=$true
    }
    return $map
}
function Assert-Cp101GeneratedArtifactSequencePreflight {
    param($Expected)
    $outputDir=RelPath 'out/checkpoint-101'
    $null=New-Item -ItemType Directory -Path $outputDir -Force
    $probePaths=@((Join-Path $outputDir 'acceptance-summary.json'),(Join-Path $outputDir 'acceptance-summary.txt'))
    $created=@()
    foreach($probe in $probePaths){
        if(-not (Test-Path -LiteralPath $probe -PathType Leaf)){
            'CP101 RepositoryOnly sequence preflight generated artifact' | Set-Content -LiteralPath $probe -Encoding ASCII
            $created += $probe
        }
    }
    try {
        foreach($rel in @('out/checkpoint-101/acceptance-summary.json','out/checkpoint-101/acceptance-summary.txt','src/StarCluster.Core/bin/Debug/net8.0/generated.dll','src/StarCluster.Core/obj/generated.tmp','TestResults/generated.trx')){
            Assert-True (Test-IsGeneratedOrLocalPath -RelativePath $rel) "Generated/local artifact policy failed to ignore '$rel'."
        }
        foreach($rel in @('README.md','src/StarCluster.Core/StarCluster.Core.csproj','docs/README.md')){
            Assert-True (-not (Test-IsGeneratedOrLocalPath -RelativePath $rel)) "Generated/local artifact policy incorrectly ignored repository-owned path '$rel'."
        }
        $probeActual=Get-Cp101RepositoryOwnedFileSet
        Assert-True ($probeActual.Count -eq $Expected.Count) "CP101 RepositoryOnly-to-full-run sequence preflight failed: generated acceptance summaries changed repository-owned file count from $($Expected.Count) to $($probeActual.Count)."
        foreach($rel in $Expected.Keys){ Assert-True ($probeActual.ContainsKey([string]$rel)) "CP101 sequence preflight lost expected repository-owned path '$rel'." }
        foreach($rel in $probeActual.Keys){ Assert-True ($Expected.ContainsKey([string]$rel)) "CP101 sequence preflight treated generated/local path '$rel' as repository-owned." }
    }
    finally {
        foreach($probe in $created){ Remove-Item -LiteralPath $probe -Force -ErrorAction SilentlyContinue }
    }
}


Write-Host '       Validating native dependencies, wrapper interface, and checkpoint definitions...'
$normalRel='tools/calibration/checkpoints/checkpoint-101.json'
$deepRel='tools/calibration/checkpoints/checkpoint-101-deep-calibration.json'
$guarded=@(
    'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
    'tools/checkpoints/checkpoint-101/apply_checkpoint_101.ps1',
    'tools/checkpoints/checkpoint-101/test_checkpoint_101_contract.ps1',
    'tools/calibration/run_calibration_checkpoint.ps1'
)
& (RelPath 'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1') -RepositoryRoot $repositoryRoot -PowerShellPaths $guarded -CheckpointDefinitionPaths @($normalRel,$deepRel)
$apply=Read-Text 'tools/checkpoints/checkpoint-101/apply_checkpoint_101.ps1'
$typeCall='Assert-Cp101PowerShell51TypeCompatibility -Paths @($MyInvocation.MyCommand.Path, $contract)'
Require-Contains $apply 'function Assert-Cp101PowerShell51TypeCompatibility' 'CP101 wrapper must define the Windows PowerShell 5.1 type-token compatibility precheck.'
Require-Contains $apply $typeCall 'CP101 wrapper must invoke the Windows PowerShell 5.1 type-token compatibility precheck.'
Assert-True ($apply.IndexOf($typeCall,[StringComparison]::Ordinal) -lt $apply.IndexOf('& $guard -RepositoryRoot',[StringComparison]::Ordinal)) 'CP101 PowerShell 5.1 type-token precheck must run before the shared dependency guard.'
Assert-True ($apply.IndexOf('& $guard -RepositoryRoot',[StringComparison]::Ordinal) -lt $apply.IndexOf('& $contract -RepositoryRoot',[StringComparison]::Ordinal)) 'CP101 dependency guard must run before the repository contract.'
Assert-True ($apply.IndexOf('& $contract -RepositoryRoot',[StringComparison]::Ordinal) -lt $apply.IndexOf('& $harness -CheckpointDefinition',[StringComparison]::Ordinal)) 'CP101 repository contract must run before the checkpoint harness.'
Require-Contains $apply 'unreviewed token' 'CP101 wrapper must explicitly reject unreviewed PowerShell type tokens.'
Require-Contains $apply '& $harness -CheckpointDefinition $definition -Trials $Trials -Jobs $Jobs -RepositoryOnly:$RepositoryOnly -NoClean:$NoClean' 'CP101 wrapper must preserve direct named-parameter harness invocation.'
Require-Contains $apply '$outputRoot = Join-Path $repositoryRoot ''out\checkpoint-101''' 'CP101 wrapper must bind the generated output root before repository-contract execution.'
Require-Contains $apply 'Remove-Item -LiteralPath $outputRoot -Recurse -Force -ErrorAction SilentlyContinue' 'CP101 wrapper must normalize stale checkpoint output before repository-contract execution when cleaning is enabled.'
Assert-True ($apply.IndexOf('Remove-Item -LiteralPath $outputRoot',[StringComparison]::Ordinal) -lt $apply.IndexOf('& $contract -RepositoryRoot',[StringComparison]::Ordinal)) 'CP101 stale generated-output normalization must occur before the repository contract.'
Require-Contains (Read-Text 'tools/calibration/run_calibration_checkpoint.ps1') '$path -like ''out/*''' 'Shared harness generated/local policy must continue to ignore out/* artifacts.'
Assert-True (-not [regex]::IsMatch($apply,'&\s+\$harness\s+@[A-Za-z_]',[System.Text.RegularExpressions.RegexOptions]::IgnoreCase)) 'CP101 wrapper must not splat harness arguments.'

$stageIds=@(
    'deterministic','tl1-phase-a','tl1-phase-b','tl1-installation-space-envelope','tl1-sensor-ew-foundation',
    'cross-tl-cp99-exact-edge-preflight','cross-tl-cp99-exact-edge-generation','auxiliary-resource-endurance',
    'checkpoint-53-resource-semantics-lock','runner-self-tests'
)
$documentation=@(
    'CHAT_README.md','README.md','docs/README.md','docs/Star_Cluster_Game_Concept_v0.7c.docx','docs/Prototype_TODO.md','docs/design/README.md',
    'docs/design/player_technology/README.md','docs/design/player_technology/Technology_Architecture_Matrix_v1.md','docs/archive/player_technology/pre-cp165-active/technology_architecture_matrix_v1.json',
    'docs/design/player_technology/StarCluster_Technology_Architecture_Matrix_v1.xlsx','docs/archive/player_technology/pre-cp165-active/tl3_base_technology_candidates_v0_2.json',
    'docs/archive/player_technology/pre-cp165-active/tl3_base_build_sanity_v0_1.json','docs/archive/player_technology/pre-cp165-active/component_installation_space_catalog_v1.json',
    'docs/archive/player_technology/pre-cp165-active/auxiliary_component_catalog_v0_1.json','docs/design/testing/README.md','docs/design/testing/Checkpoint_101_Validation_Tiers.md',
    'docs/design/testing/checkpoint_101_validation_suite_policy_v0_1.json','docs/design/testing/Technology_Integration_Permutation_Suite_Architecture_v0_16.md',
    'docs/design/testing/technology_integration_permutation_suite_v0_16.json','docs/development/Simulation_Development_Guidelines.md',
    'docs/validation/Checkpoint_101_TL3_Base_Technology_Table_Completion.md','docs/validation/evidence/checkpoint-100/CHECKPOINT_100_SHA256SUMS.txt',
    'docs/validation/evidence/checkpoint-100/checkpoint-100-native-acceptance-summary.json','docs/validation/evidence/checkpoint-100/cp100-tl3-foundation-evidence.json'
)
foreach($d in @((Read-Json $normalRel),(Read-Json $deepRel))){
    Assert-True ([string]$d.checkpointId -eq '101' -and [string]$d.manifestFile -eq 'CHECKPOINT_101_SHA256SUMS.txt') 'CP101 definition/manifest binding mismatch.'
    Assert-True ([string]$d.sdkVersion -eq '8.0.423' -and [string]$d.outputRoot -eq 'out/checkpoint-101') 'CP101 SDK/outputRoot mismatch.'
    Assert-True ([int]$d.defaultTrials -eq 250 -and [int]$d.defaultJobs -eq 24) 'CP101 default trials/jobs mismatch.'
    Assert-True (@($d.stages).Count -eq 10 -and [int]$d.checkpointMetrics.stageCount -eq 10) 'CP101 must configure exactly 10 runner stages.'
    Assert-Sequence @($d.stages|ForEach-Object{[string]$_.id}) $stageIds 'CP101 stage order drifted.'
    Assert-Sequence @($d.documentation) $documentation 'CP101 documentation authority list drifted.'
    Assert-Sequence @($d.nativeDependencyPrecheck.powerShellPaths) $guarded 'CP101 guarded PowerShell path list drifted.'
    Assert-Sequence @($d.nativeDependencyPrecheck.checkpointDefinitionPaths) @($normalRel,$deepRel) 'CP101 guarded definition list drifted.'
    Assert-True ([long]$d.checkpointMetrics.trialsAtDefault -eq 0 -and [long]$d.checkpointMetrics.smokeTrialsAtDefault -eq 0 -and [long]$d.checkpointMetrics.totalTrialExecutionsAtDefault -eq 0) 'CP101 must run no stochastic trials.'
    Assert-True ([int]$d.checkpointMetrics.monteCarloVariantCount -eq 0 -and [int]$d.checkpointMetrics.expectedXunitTests -eq 876 -and [int]$d.checkpointMetrics.expectedRunnerSelfTests -eq 63) 'CP101 deterministic acceptance metrics mismatch.'
    Assert-True ([string]$d.checkpointMetrics.acceptedBaselineCheckpoint -eq '100') 'CP101 must name CP100 as the accepted repository baseline.'
    Assert-True ([string]$d.checkpointMetrics.acceptedExecutableFoundation -eq 'cross-tl-build-permutation-foundation-v0_8' -and [int]$d.checkpointMetrics.acceptedLegalBuildCount -eq 11776 -and [int]$d.checkpointMetrics.acceptedProgressionLegalEdges -eq 37184) 'CP101 must retain the accepted CP99 executable cross-progression foundation.'
    Assert-True ([bool]$d.checkpointMetrics.tl3BaseTableCompleted -and [bool]$d.checkpointMetrics.tl3BaseCandidateRegistered -and -not [bool]$d.checkpointMetrics.tl3CombatConsumerEnabled) 'CP101 must complete/register the TL3 base table without runtime activation.'
    Assert-True ([int]$d.checkpointMetrics.tl3CruiserInstallationSpace -eq 36 -and [int]$d.checkpointMetrics.tl3SingleMainSingleReactorUsedSpace -eq 27 -and [int]$d.checkpointMetrics.tl3DualMainSingleReactorUsedSpace -eq 33 -and [int]$d.checkpointMetrics.tl3SingleMainDualReactorUsedSpace -eq 32 -and [int]$d.checkpointMetrics.tl3DualMainDualReactorUsedSpace -eq 38 -and -not [bool]$d.checkpointMetrics.tl3DualMainDualReactorLegal) 'CP101 TL3 Space sanity metrics drifted.'
    Assert-True ([int]$d.checkpointMetrics.tl3SingleReactorOperationalTp -eq 6 -and -not [bool]$d.checkpointMetrics.initiativeRuleChanged -and -not [bool]$d.checkpointMetrics.deepCalibrationApplicable -and -not [bool]$d.checkpointMetrics.technologyPromotionAutomatic) 'CP101 authority-boundary metrics drifted.'
}

Write-Host '       Validating native-accepted CP100 provenance and frozen executable surface...'
$acceptedManifestRel='docs/validation/evidence/checkpoint-100/CHECKPOINT_100_SHA256SUMS.txt'
Assert-True ((Hash-Rel $acceptedManifestRel) -eq 'e8104cc761e0807414ccf278a7bd9813cdd3ea99cfd5f58dab9ae7cce16faaf6') 'Archived accepted CP100 manifest hash mismatch.'
$accepted=Read-Json 'docs/validation/evidence/checkpoint-100/checkpoint-100-native-acceptance-summary.json'
Assert-True ([string]$accepted.status -eq 'Success' -and [string]$accepted.sdk.actual -eq '8.0.423') 'Accepted CP100 native status/SDK evidence mismatch.'
Assert-True ([string]$accepted.checkpointDefinitionSha256 -eq '4d9420008706b2970151159d4041a2b3ad81bad145b8985a1583416f82d54c13' -and [string]$accepted.checkpointManifestSha256 -eq 'e8104cc761e0807414ccf278a7bd9813cdd3ea99cfd5f58dab9ae7cce16faaf6') 'Accepted CP100 definition/manifest provenance mismatch.'
Assert-True ([int]$accepted.tests.passed -eq 876 -and [int]$accepted.tests.failed -eq 0 -and [int]$accepted.aggregates.runnerStagesPassed -eq 10 -and [int]$accepted.aggregates.selfTests -eq 63 -and [int]$accepted.aggregates.failedGates -eq 0 -and [long]$accepted.aggregates.trials -eq 0) 'Accepted CP100 native metric evidence mismatch.'
$cp100Evidence=Read-Json 'docs/validation/evidence/checkpoint-100/cp100-tl3-foundation-evidence.json'
Assert-True ([string]$cp100Evidence.status -eq 'native_accepted' -and [int]$cp100Evidence.retainedCp99Foundation.legalBuildCount -eq 11776 -and [int]$cp100Evidence.retainedCp99Foundation.logicalPairingCount -eq 362 -and [int]$cp100Evidence.retainedCp99Foundation.generatedVariantCount -eq 724 -and [int]$cp100Evidence.retainedCp99Foundation.failedGateCount -eq 0) 'CP100 retained executable-foundation evidence mismatch.'
$cp100Def=Read-Json 'tools/calibration/checkpoints/checkpoint-100.json'; Assert-True ([int]$cp100Def.checkpointMetrics.acceptedProgressionLegalEdges -eq 37184 -and [int]$cp100Def.checkpointMetrics.acceptedLegalBuildCount -eq 11776) 'Frozen CP100 definition lost the accepted CP99 progression counts.'

$acceptedManifest=Read-Manifest $acceptedManifestRel
Assert-True ($acceptedManifest.EntryCount -eq 1934) 'Accepted CP100 manifest must contain 1,934 entries.'
$allowedChanges=@{
    'CHAT_README.md'=$true; 'README.md'=$true; 'docs/README.md'=$true; 'docs/design/README.md'=$true;
    'docs/design/player_technology/README.md'=$true; 'docs/design/player_technology/StarCluster_Technology_Architecture_Matrix_v1.xlsx'=$true;
    'docs/design/player_technology/Technology_Architecture_Matrix_v1.md'=$true; 'docs/archive/player_technology/pre-cp165-active/component_installation_space_catalog_v1.json'=$true;
    'docs/archive/player_technology/pre-cp165-active/technology_architecture_matrix_v1.json'=$true; 'docs/design/testing/README.md'=$true;
    'docs/development/Simulation_Development_Guidelines.md'=$true; 'docs/validation/README.md'=$true
}
$moved=@{
    'docs/Star_Cluster_Game_Concept_v0.7b.docx'='docs/archive/concepts/Star_Cluster_Game_Concept_v0.7b.docx';
    'docs/design/player_technology/tl3_core_technology_candidates_v0_1.json'='docs/archive/player_technology/architecture-history/tl3_core_technology_candidates_v0_1.json';
    'docs/design/testing/Checkpoint_100_Validation_Tiers.md'='docs/archive/testing/Checkpoint_100_Validation_Tiers.md';
    'docs/design/testing/Technology_Integration_Permutation_Suite_Architecture_v0_15.md'='docs/archive/testing/Technology_Integration_Permutation_Suite_Architecture_v0_15.md';
    'docs/design/testing/checkpoint_100_validation_suite_policy_v0_1.json'='docs/archive/testing/checkpoint_100_validation_suite_policy_v0_1.json';
    'docs/design/testing/technology_integration_permutation_suite_v0_15.json'='docs/archive/testing/technology_integration_permutation_suite_v0_15.json';
    'docs/validation/Checkpoint_100_TL3_Core_Technology_Table_Foundation.md'='docs/validation/archive/Checkpoint_100_TL3_Core_Technology_Table_Foundation.md'
}
$newFiles=@(
    'docs/Star_Cluster_Game_Concept_v0.7c.docx','docs/archive/player_technology/pre-cp165-active/tl3_base_build_sanity_v0_1.json','docs/archive/player_technology/pre-cp165-active/tl3_base_technology_candidates_v0_2.json',
    'docs/design/testing/Checkpoint_101_Validation_Tiers.md','docs/design/testing/Technology_Integration_Permutation_Suite_Architecture_v0_16.md',
    'docs/design/testing/checkpoint_101_validation_suite_policy_v0_1.json','docs/design/testing/technology_integration_permutation_suite_v0_16.json',
    'docs/validation/Checkpoint_101_TL3_Base_Technology_Table_Completion.md','docs/validation/evidence/checkpoint-100/CHECKPOINT_100_SHA256SUMS.txt',
    'docs/validation/evidence/checkpoint-100/checkpoint-100-native-acceptance-summary.json','docs/validation/evidence/checkpoint-100/cp100-tl3-foundation-evidence.json',
    'tools/calibration/checkpoints/checkpoint-101.json','tools/calibration/checkpoints/checkpoint-101-deep-calibration.json',
    'tools/checkpoints/checkpoint-101/apply_checkpoint_101.ps1','tools/checkpoints/checkpoint-101/test_checkpoint_101_contract.ps1'
)
$frozen=0
foreach($rel in $acceptedManifest.Entries.Keys){
    if($moved.ContainsKey([string]$rel)){
        $dest=[string]$moved[[string]$rel]
        Assert-True (-not (Test-Path -LiteralPath (RelPath ([string]$rel)))) "Superseded CP100 authority '$rel' must not remain active."
        Assert-True (Test-Path -LiteralPath (RelPath $dest) -PathType Leaf) "Archived CP100 authority '$dest' is missing."
        Assert-True ((Hash-Rel $dest) -eq [string]$acceptedManifest.Entries[[string]$rel]) "Archived CP100 authority '$dest' is not byte-identical."
    } elseif($allowedChanges.ContainsKey([string]$rel)) {
        Assert-True (Test-Path -LiteralPath (RelPath ([string]$rel)) -PathType Leaf) "Allowed CP101 authority '$rel' is missing."
    } else {
        Assert-True (Test-Path -LiteralPath (RelPath ([string]$rel)) -PathType Leaf) "Frozen CP100 file '$rel' is missing."
        Assert-True ((Hash-Rel ([string]$rel)) -eq [string]$acceptedManifest.Entries[[string]$rel]) "Frozen CP100 file '$rel' changed unexpectedly."
        $frozen++
    }
}
foreach($rel in $newFiles){ Assert-True (Test-Path -LiteralPath (RelPath $rel) -PathType Leaf) "Expected new CP101 file '$rel' is missing." }
foreach($rel in $acceptedManifest.Entries.Keys){ if(([string]$rel).StartsWith('src/',[StringComparison]::Ordinal)){ Assert-True (-not $allowedChanges.ContainsKey([string]$rel) -and -not $moved.ContainsKey([string]$rel)) "CP101 may not alter runtime source '$rel'." } }

Write-Host '       Validating complete TL3 base candidate values and subsystem identity...'
$base=Read-Json 'docs/archive/player_technology/pre-cp165-active/tl3_base_technology_candidates_v0_2.json'
Assert-True ([int]$base.checkpoint -eq 101 -and [string]$base.status -eq 'complete_base_conceptual_candidate_table') 'TL3 base candidate profile identity/status mismatch.'
Assert-True (-not [bool]$base.candidateLifecycle.registeredCandidateIsImplemented -and -not [bool]$base.candidateLifecycle.registeredCandidateIsCalibrated -and -not [bool]$base.candidateLifecycle.registeredCandidateIsPromoted -and -not [bool]$base.candidateLifecycle.combatConsumerEnabled -and -not [bool]$base.candidateLifecycle.automaticPromotion) 'TL3 candidate lifecycle boundary drifted.'
Assert-True (@($base.tl3Candidates.psobject.Properties).Count -eq 16) 'TL3 base profile must define exactly 16 base streams.'
$t=$base.tl3Candidates
Assert-True ([int]$t.hull.installationSpaceCapacity -eq 36 -and [int]$t.hull.hullPointsHeld -eq 12 -and [int]$t.hull.shuttleCapacityHeld -eq 1) 'TL3 Hull candidate drifted.'
Assert-True ([int]$t.armor.armorProtection -eq 1 -and [int]$t.armor.armorIntegrity -eq 5) 'TL3 Armor candidate drifted.'
Assert-True ([int]$t.powerReactor.installationSpace -eq 5 -and [int]$t.powerReactor.operationalTacticalPower -eq 6 -and [int]$t.powerReactor.degradedTacticalPowerHeld -eq 3 -and [int]$t.powerReactor.disabledEmergencyTacticalPowerHeld -eq 1) 'TL3 Reactor candidate drifted.'
Assert-True ([int]$t.stlDrive.installationSpace -eq 5 -and [int]$t.stlDrive.normalMove -eq 3 -and [int]$t.stlDrive.overloadI.moveBonus -eq 1 -and [int]$t.stlDrive.overloadI.tacticalPower -eq 1 -and [int]$t.stlDrive.overloadI.extraFuel -eq 2 -and [int]$t.stlDrive.overloadI.strain -eq 1) 'TL3 STL candidate drifted.'
Assert-True ([int]$t.ftlDrive.installationSpace -eq 5 -and [int]$t.ftlDrive.strategicMove -eq 3 -and [bool]$t.ftlDrive.unknownSectorConsumesRemainingMove) 'TL3 FTL candidate drifted.'
Assert-True ([int]$t.tacticalComputer.ordinaryTargetingAssistanceOperationalPp -eq 12 -and [int]$t.tacticalComputer.approximateTrackPenaltyPp -eq -25 -and [int]$t.tacticalComputer.evasiveCompensationPp -eq 5) 'TL3 Tactical Computer candidate drifted.'
Assert-True ([int]$t.sensor.discriminationResistance -eq 1 -and [int]$t.sensor.normalActiveModes[0].firm -eq 3 -and [int]$t.sensor.normalActiveModes[0].approximate -eq 4 -and [int]$t.sensor.normalActiveModes[0].tacticalPower -eq 1 -and [int]$t.sensor.normalActiveModes[1].firm -eq 4 -and [int]$t.sensor.normalActiveModes[1].approximate -eq 5 -and [int]$t.sensor.normalActiveModes[1].tacticalPower -eq 2 -and [int]$t.sensor.normalActiveModes[1].strain -eq 0) 'TL3 Sensor candidate drifted.'
foreach($ew in @($t.ecm,$t.eccm)){ Assert-True ([int]$ew.normalRatingCeiling -eq 2 -and [int]$ew.fullStrengthNormalTp -eq 1 -and [int]$ew.installationSpace -eq 1 -and -not [bool]$ew.sameTypeRatingsAdditive) 'TL3 ECM/ECCM efficiency candidate drifted.' }
Assert-True ([int]$t.shield.primaryShield.shieldCapacity -eq 3 -and [int]$t.shield.primaryShield.installationSpace -eq 3 -and [int]$t.shield.shieldHardener.installationSpace -eq 1 -and [int]$t.shield.shieldHardener.normalShieldArmor -eq 1 -and [int]$t.shield.shieldHardener.sustainedTacticalPower -eq 1) 'TL3 Shield/Hardener candidate drifted.'
Assert-True ([int]$t.kineticMainWeapon.installationSpace -eq 6 -and [int]$t.kineticMainWeapon.accuracyPp -eq 20 -and [int]$t.kineticMainWeapon.damage -eq 4 -and [int]$t.kineticMainWeapon.shieldPenetration -eq 1 -and [int]$t.kineticMainWeapon.armorPenetration -eq 1 -and [int]$t.kineticMainWeapon.maximumRange -eq 4 -and [int]$t.kineticMainWeapon.ordinaryFiringTacticalPower -eq 0 -and [int]$t.kineticMainWeapon.ammunitionPackagesHeld -eq 100) 'TL3 Kinetic Main candidate drifted.'
Assert-True ([int]$t.energyMainWeapon.installationSpace -eq 6 -and [int]$t.energyMainWeapon.maximumRange -eq 5 -and @($t.energyMainWeapon.modes).Count -eq 3) 'TL3 Energy Main base identity drifted.'
Assert-True ([int]$t.energyMainWeapon.modes[0].tacticalPower -eq 1 -and [int]$t.energyMainWeapon.modes[0].damage -eq 2 -and [int]$t.energyMainWeapon.modes[1].tacticalPower -eq 2 -and [int]$t.energyMainWeapon.modes[1].damage -eq 3 -and [int]$t.energyMainWeapon.modes[2].tacticalPower -eq 3 -and [int]$t.energyMainWeapon.modes[2].damage -eq 4 -and [int]$t.energyMainWeapon.modes[2].strain -eq 0) 'TL3 Energy safe-output modes drifted.'
Assert-True ([int]$t.missileMainWeapon.launcherInstallationSpace -eq 6 -and [int]$t.missileMainWeapon.launchTacticalPower -eq 0 -and [int]$t.missileMainWeapon.warheadDamage -eq 5 -and [int]$t.missileMainWeapon.shieldPenetration -eq 1 -and [int]$t.missileMainWeapon.armorPenetration -eq 2 -and [int]$t.missileMainWeapon.maximumRangeHeld -eq 6 -and [int]$t.missileMainWeapon.missileFlightsHeld -eq 25 -and [int]$t.missileMainWeapon.missileMove -eq 4 -and [bool]$t.missileMainWeapon.standardOnboardNavigationSensor -and -not [bool]$t.missileMainWeapon.terminalSeekerStandard -and [bool]$t.missileMainWeapon.ordinaryTerminalFirmRequired -and -not [bool]$t.missileMainWeapon.approximateTerminalAttack) 'TL3 Missile Main candidate drifted.'
Assert-True ([int]$t.kineticPds.installationSpace -eq 2 -and [int]$t.kineticPds.pdsBaseChanceHeld -eq 13 -and [int]$t.kineticPds.reactionCapacity -eq 1 -and [int]$t.kineticPds.tacticalPowerReadiness -eq 1 -and [int]$t.kineticPds.ammunitionHeld -eq 60) 'TL3 Kinetic PDS hold drifted.'
Assert-True ([int]$t.energyPds.installationSpace -eq 2 -and [int]$t.energyPds.pdsBaseChanceHeld -eq 16 -and [int]$t.energyPds.reactionCapacity -eq 1 -and [int]$t.energyPds.tacticalPowerReadiness -eq 1) 'TL3 Energy PDS efficiency candidate drifted.'
Assert-True ([int]$t.ammPds.installationSpace -eq 2 -and [int]$t.ammPds.pdsBaseChanceHeld -eq 20 -and [int]$t.ammPds.ammunitionHeld -eq 25 -and @($t.ammPds.readinessModes).Count -eq 2 -and [int]$t.ammPds.readinessModes[0].tacticalPower -eq 1 -and [int]$t.ammPds.readinessModes[0].reactionCapacity -eq 1 -and [int]$t.ammPds.readinessModes[1].tacticalPower -eq 2 -and [int]$t.ammPds.readinessModes[1].reactionCapacity -eq 2 -and [int]$t.ammPds.perFlightAttemptCapHeld -eq 2) 'TL3 AMM PDS readiness candidate drifted.'

Write-Host '       Recomputing TL3 build-space and Tactical-Power sanity independently...'
$sanity=Read-Json 'docs/archive/player_technology/pre-cp165-active/tl3_base_build_sanity_v0_1.json'
Assert-True ([int]$sanity.checkpoint -eq 101 -and [string]$sanity.status -eq 'conceptual_arithmetic_sanity_not_combat_calibration') 'TL3 build-sanity profile identity/status mismatch.'
$fixed=[int]$sanity.space.fixedPrimaryShell.stlDrive+[int]$sanity.space.fixedPrimaryShell.ftlDrive+[int]$sanity.space.fixedPrimaryShell.tacticalComputer+[int]$sanity.space.fixedPrimaryShell.sensor
Assert-True ($fixed -eq 16) 'TL3 fixed primary shell must recompute to 16 Space.'
$tl12Single=$fixed+[int]$sanity.space.mainWeaponSpace+[int]$sanity.space.tl1Tl2ReactorSpace
$tl3Single=$fixed+[int]$sanity.space.mainWeaponSpace+[int]$sanity.space.tl3ReactorSpace
$tl3DualMain=$fixed+(2*[int]$sanity.space.mainWeaponSpace)+[int]$sanity.space.tl3ReactorSpace
$tl3DualReactor=$fixed+[int]$sanity.space.mainWeaponSpace+(2*[int]$sanity.space.tl3ReactorSpace)
$tl3DualBoth=$fixed+(2*[int]$sanity.space.mainWeaponSpace)+(2*[int]$sanity.space.tl3ReactorSpace)
Assert-True ($tl12Single -eq 28 -and $tl3Single -eq 27 -and $tl3DualMain -eq 33 -and $tl3DualReactor -eq 32 -and $tl3DualBoth -eq 38) 'Independent TL3 build-space reconstruction failed.'
$arch=@{}; foreach($a in @($sanity.space.architectures)){ $arch[[string]$a.id]=$a }
Assert-True ([int]$arch['single-main-single-reactor'].tl3Used -eq $tl3Single -and [int]$arch['dual-main-single-reactor'].tl3Used -eq $tl3DualMain -and [int]$arch['single-main-dual-reactor'].tl3Used -eq $tl3DualReactor -and [int]$arch['dual-main-dual-reactor'].tl3Used -eq $tl3DualBoth) 'Declared TL3 architecture used-Space values do not match independent reconstruction.'
Assert-True ([int]$sanity.space.tl3BaseCandidateCruiserCapacity -eq 36 -and -not [bool]$arch['dual-main-dual-reactor'].tl3Legal -and [int]$sanity.space.futureMilestones.firstLegalDualMainDualReactorEffectiveSpace -eq 38 -and [int]$sanity.space.futureMilestones.dualMainDualReactorPlusMeaningfulThreeSpacePackage -eq 41) 'TL3 dual-heavy legality/milestone guardrails drifted.'
Assert-True ([int]$sanity.power.singleTl3ReactorOperationalTp -eq 6 -and [int]$sanity.power.dualTl3ReactorOperationalTp -eq 12) 'TL3 reactor power sanity drifted.'
foreach($pkg in @($sanity.power.dualEnergySingleReactor)){ $sum=[int]$pkg.weaponTp+[int]$pkg.sensorTp+[int]$pkg.otherTp; Assert-True ($sum -eq [int]$pkg.totalTp) "Power package '$($pkg.package)' total does not recompute."; Assert-True ((6-$sum) -eq [int]$pkg.margin) "Power package '$($pkg.package)' margin does not recompute." }
Assert-True ([int]$sanity.power.dualEnergySingleReactor[0].totalTp -eq 6 -and [int]$sanity.power.dualEnergySingleReactor[0].margin -eq 0 -and [int]$sanity.power.dualEnergySingleReactor[2].totalTp -eq 8 -and [int]$sanity.power.dualEnergySingleReactor[2].margin -eq -2) 'Dual-Energy power breakpoints drifted.'
$gp=$sanity.power.generalistSupportPackage; $support=[int]$gp.highActiveSensor+[int]$gp.pdsReadiness+[int]$gp.ecm+[int]$gp.eccm+[int]$gp.shieldHardener
Assert-True ($support -eq 6 -and [int]$gp.totalBeforeWeaponEvasionOrTacticalRecharge -eq 6 -and [int]$gp.marginBeforeWeaponEvasionOrTacticalRecharge -eq 0) 'Generalist support power package must consume the full 6-TP reactor before weapon/EvM/recharge costs.'
Assert-True ([int]$sanity.power.dualReactorDamageResilience.operationalPlusOperational -eq 12 -and [int]$sanity.power.dualReactorDamageResilience.operationalPlusDegraded -eq 9 -and [int]$sanity.power.dualReactorDamageResilience.operationalPlusDisabled -eq 7 -and [int]$sanity.power.dualReactorDamageResilience.operationalPlusDestroyed -eq 6) 'Dual-reactor damage-resilience arithmetic drifted.'
Assert-True ([bool]$base.buildSanity.constructionPowerSeparation -and [bool]$base.buildSanity.noSpecialAntiStackingRuleAdded) 'CP101 must preserve construction/power separation and avoid an artificial anti-stacking rule.'

Write-Host '       Validating standing suite, current matrix/catalog, and authority boundaries...'
$suite=Read-Json 'docs/design/testing/technology_integration_permutation_suite_v0_16.json'
Assert-True ([int]$suite.checkpoint -eq 101 -and [bool]$suite.tl3BaseTableComplete -and -not [bool]$suite.tl3CombatConsumerEnabled) 'Suite v0.16 TL3 registration boundary mismatch.'
Assert-True ([string]$suite.tl3CandidateRegistration.profile -eq 'docs/archive/player_technology/pre-cp165-active/tl3_base_technology_candidates_v0_2.json' -and [string]$suite.tl3CandidateRegistration.buildSanityProfile -eq 'docs/archive/player_technology/pre-cp165-active/tl3_base_build_sanity_v0_1.json') 'Suite v0.16 TL3 profile bindings drifted.'
$trans=@($suite.tl3CandidateRegistration.registeredTransitions); Assert-True ($trans.Count -eq 16) 'Suite v0.16 must register exactly 16 TL3 base transitions.'
$transitionMap=@{}; foreach($x in $trans){ Assert-True (-not $transitionMap.ContainsKey([string]$x.id)) "Duplicate TL3 transition '$($x.id)'."; $transitionMap[[string]$x.id]=$x }
$transitionExpect=@{
    'hull-h2-to-h3'='capacity_integration|1'; 'computer-c2-to-c3'='capability_addition|0'; 'sensor-s2-to-s3'='operating_mode_addition|0';
    'ecm-ecm2-to-ecm3'='power_efficiency|0'; 'eccm-eccm2-to-eccm3'='power_efficiency|0'; 'reactor-r2-to-r3'='miniaturization|-1';
    'stl-stl2-to-stl3'='primary_performance|0'; 'ftl-ftl2-to-ftl3'='primary_performance|0'; 'shield-sh2-to-tl3-hardener-unlock'='optional_component_unlock|1';
    'armor-a2-to-a3'='protection_maturation|0'; 'weapon-k2-to-k3'='power_efficiency|0'; 'weapon-e2-to-e3'='safe_output_maturation|0';
    'weapon-m2-to-m3'='autonomy_propulsion|0'; 'pds-k2-to-k3'='explicit_hold|0'; 'pds-e2-to-e3'='power_efficiency|0'; 'pds-amm2-to-amm3'='readiness_mode_addition|0'
}
foreach($id in $transitionExpect.Keys){ Assert-True ($transitionMap.ContainsKey([string]$id)) "Suite v0.16 is missing transition '$id'."; $parts=([string]$transitionExpect[[string]$id]).Split('|'); Assert-True ([string]$transitionMap[[string]$id].kind -eq $parts[0] -and [int]$transitionMap[[string]$id].installationSpaceDelta -eq [int]$parts[1]) "Suite v0.16 transition '$id' kind/Space delta drifted." }

$matrix=Read-Json 'docs/archive/player_technology/pre-cp165-active/technology_architecture_matrix_v1.json'
Assert-True ([int]$matrix.checkpoint -eq 101 -and [string]$matrix.authority.concept -eq 'docs/Star_Cluster_Game_Concept_v0.7c.docx' -and [string]$matrix.integrationArchitecture.standingPermutationSuite -eq 'docs/design/testing/technology_integration_permutation_suite_v0_16.json' -and [string]$matrix.integrationArchitecture.tl3CandidateRegistry -eq 'docs/archive/player_technology/pre-cp165-active/tl3_base_technology_candidates_v0_2.json' -and -not [bool]$matrix.integrationArchitecture.tl3CombatConsumerEnabled) 'Technology Matrix current-authority bindings drifted.'
$tier3=@($matrix.tiers|Where-Object{[int]$_.technologyLevel -eq 3}); Assert-True ($tier3.Count -eq 1 -and [string]$tier3[0].baseTableStatus -eq 'complete_base_conceptual_candidate_table' -and -not [bool]$tier3[0].combatConsumerEnabled) 'Technology Matrix TL3 base status drifted.'
Assert-True ([int]$tier3[0].hull.installationSpaceCapacity -eq 36 -and [int]$tier3[0].powerReactor.operationalTacticalPower -eq 6 -and [int]$tier3[0].powerReactor.installationSpace -eq 5 -and [int]$tier3[0].kineticMainWeapon.ordinaryFiringTacticalPower -eq 0 -and [int]$tier3[0].missileMainWeapon.missileMove -eq 4) 'Technology Matrix representative TL3 values drifted.'
$catalog=Read-Json 'docs/archive/player_technology/pre-cp165-active/component_installation_space_catalog_v1.json'
Assert-True ([int]$catalog.checkpoint -eq 101 -and [string]$catalog.authority.concept -eq 'docs/Star_Cluster_Game_Concept_v0.7c.docx' -and [int]$catalog.globalRules.playerCruiserInstallationSpace -eq 35 -and [int]$catalog.globalRules.playerCruiserInstallationSpaceByTechnologyStatus.tl3_conceptual_candidate -eq 36) 'Component catalog TL1/TL2 current vs TL3 conceptual hull-capacity boundary drifted.'
Assert-True ([int]$catalog.globalRules.minimumMainWeaponCount -eq 1 -and [int]$catalog.globalRules.minimumReactorCount -eq 1 -and [int]$catalog.globalRules.minimumSensorCount -eq 1 -and [bool]$catalog.globalRules.additionalMainWeaponsOptional -and [bool]$catalog.globalRules.additionalReactorsOptional -and -not [bool]$catalog.globalRules.simultaneousTacticalPowerSufficiencyRequiredForConstruction) 'Component catalog construction guardrails drifted.'

$policy=Read-Json 'docs/design/testing/checkpoint_101_validation_suite_policy_v0_1.json'
Assert-True ([int]$policy.checkpoint -eq 101 -and [int]$policy.acceptedBaseline.checkpoint -eq 100 -and [string]$policy.acceptedBaseline.checkpointManifestSha256 -eq 'e8104cc761e0807414ccf278a7bd9813cdd3ea99cfd5f58dab9ae7cce16faaf6') 'CP101 validation policy accepted-baseline binding drifted.'
Assert-True ([string]$policy.tl3BaseRegistration.profile -eq 'docs/archive/player_technology/pre-cp165-active/tl3_base_technology_candidates_v0_2.json' -and [int]$policy.tl3BaseRegistration.registeredTransitionCount -eq 16 -and [bool]$policy.tl3BaseRegistration.baseTableComplete -and -not [bool]$policy.tl3BaseRegistration.combatConsumerEnabled -and -not [bool]$policy.tl3BaseRegistration.dualMainDualReactorLegal) 'CP101 validation policy TL3 base registration drifted.'
Assert-True (-not [bool]$policy.authorityBoundary.technologyPromotionAutomatic -and -not [bool]$policy.authorityBoundary.productionCombatDataChanged -and -not [bool]$policy.authorityBoundary.initiativeRuleChange -and -not [bool]$policy.authorityBoundary.tl3CombatMechanicsImplemented) 'CP101 validation policy authority boundary drifted.'

Write-Host '       Validating current human-readable authority set and semantic anchors...'
Assert-ExactFileSet 'docs/design/testing' @('README.md','Checkpoint_101_Validation_Tiers.md','Technology_Integration_Permutation_Suite_Architecture_v0_16.md','checkpoint_101_validation_suite_policy_v0_1.json','technology_integration_permutation_suite_v0_16.json')
$activeConcept=@(Get-ChildItem -LiteralPath (RelPath 'docs') -File -Filter 'Star_Cluster_Game_Concept_v*.docx'); Assert-True ($activeConcept.Count -eq 1 -and $activeConcept[0].Name -eq 'Star_Cluster_Game_Concept_v0.7c.docx') 'Exactly one active Game Concept must remain and it must be v0.7c.'
$activeValidation=@(Get-ChildItem -LiteralPath (RelPath 'docs/validation') -File -Filter 'Checkpoint_*.md'); Assert-True ($activeValidation.Count -eq 1 -and $activeValidation[0].Name -eq 'Checkpoint_101_TL3_Base_Technology_Table_Completion.md') 'Exactly one active validation runbook must remain and it must be CP101.'
$validationReadme=Read-Text 'docs/validation/README.md'; foreach($needle in @('Checkpoint_101_TL3_Base_Technology_Table_Completion.md','Checkpoint 100','accepted')){ Require-Contains $validationReadme $needle "Validation README is missing semantic anchor '$needle'." }
$matrixMd=Read-Text 'docs/design/player_technology/Technology_Architecture_Matrix_v1.md'; foreach($needle in @('complete TL3 base','Move3','Mature Compact Fusion','Kinetic','Energy','Missile','PDS','dual-main','runtime activation')){ Require-Contains $matrixMd $needle "Technology Matrix Markdown is missing semantic anchor '$needle'." }
$suiteMd=Read-Text 'docs/design/testing/Technology_Integration_Permutation_Suite_Architecture_v0_16.md'; foreach($needle in @('complete TL3 base','Hull','miniaturization','optional component unlock','PDS','runtime activation')){ Require-Contains $suiteMd $needle "Standing suite v0.16 is missing semantic anchor '$needle'." }
$guidelines=Read-Text 'docs/development/Simulation_Development_Guidelines.md'; foreach($needle in @('candidate','calibration','promotion','same-Space','miniaturization','optional','power','construction','runtime activation')){ Require-Contains $guidelines $needle "Simulation Development Guidelines are missing semantic anchor '$needle'." }
$runbook=Read-Text 'docs/validation/Checkpoint_101_TL3_Base_Technology_Table_Completion.md'; foreach($needle in @('CP100','876','10 runner','63 self-tests','zero stochastic','36','33/36','32/36','38/36','6-TP','v0.16','v0.8','tl3CombatConsumerEnabled')){ Require-Contains $runbook $needle "CP101 runbook is missing semantic anchor '$needle'." }

Write-Host '       Validating exact repository file set and root manifest...'
$expected=@{}
foreach($rel in $acceptedManifest.Entries.Keys){ if($moved.ContainsKey([string]$rel)){ $expected[[string]$moved[[string]$rel]]=$true } else { $expected[[string]$rel]=$true } }
foreach($rel in $newFiles){ $expected[[string]$rel]=$true }
Assert-Cp101GeneratedArtifactSequencePreflight -Expected $expected
$actual=Get-Cp101RepositoryOwnedFileSet
Assert-True ($actual.Count -eq $expected.Count) "CP101 repository-owned file count drifted after generated/local filtering: expected $($expected.Count), found $($actual.Count)."
foreach($rel in $expected.Keys){ Assert-True ($actual.ContainsKey([string]$rel)) "CP101 repository is missing expected path '$rel'." }
foreach($rel in $actual.Keys){ Assert-True ($expected.ContainsKey([string]$rel)) "CP101 repository contains unexpected path '$rel'." }
$rootTxt=@(Get-ChildItem -LiteralPath $repositoryRoot -File -Filter '*.txt'); Assert-True ($rootTxt.Count -eq 1 -and $rootTxt[0].Name -eq 'CHECKPOINT_101_SHA256SUMS.txt') 'Repository root must contain only CHECKPOINT_101_SHA256SUMS.txt as .txt.'
$manifest=Read-Manifest 'CHECKPOINT_101_SHA256SUMS.txt'; Assert-True ($manifest.EntryCount -eq $expected.Count -and $manifest.PhysicalLineCount -eq $expected.Count) 'CP101 manifest entry count must match the exact expected repository file set.'; Assert-True (-not $manifest.Entries.ContainsKey('CHECKPOINT_101_SHA256SUMS.txt')) 'CP101 manifest must not contain itself.'
foreach($entry in $manifest.Entries.GetEnumerator()){
    Assert-True (Test-Path -LiteralPath (RelPath ([string]$entry.Key)) -PathType Leaf) "CP101 manifest entry '$($entry.Key)' is missing."
    Assert-True ((Hash-Rel ([string]$entry.Key)) -eq [string]$entry.Value) "CP101 manifest hash mismatch for '$($entry.Key)'."
}

Write-Host "Checkpoint 101 repository contracts passed ($frozen CP100 files frozen; complete 16-stream TL3 base table registered; 38/36 dual-main/dual-reactor remains illegal; runtime TL3 activation remains disabled)."
