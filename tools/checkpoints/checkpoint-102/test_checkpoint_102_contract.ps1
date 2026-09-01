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
function Assert-Sequence { param($Actual,[string[]]$Expected,[string]$Message) $a=@($Actual); Assert-True ($a.Count -eq $Expected.Count) $Message; for($i=0;$i -lt $Expected.Count;$i++){ Assert-True ([string]$a[$i] -eq $Expected[$i]) $Message } }
function Assert-ExactFileSet { param([string]$RelativeDirectory,[string[]]$Expected) $a=@(Get-ChildItem -LiteralPath (RelPath $RelativeDirectory) -File | ForEach-Object Name | Sort-Object); $w=@($Expected|Sort-Object); Assert-True ($a.Count -eq $w.Count) "Directory '$RelativeDirectory' active file count drifted."; for($i=0;$i -lt $w.Count;$i++){ Assert-True ($a[$i] -eq $w[$i]) "Directory '$RelativeDirectory' active file set drifted: expected '$($w[$i])', found '$($a[$i])'." } }
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
function Test-IsGeneratedOrLocalPath {
    param([string]$RelativePath)
    $path=$RelativePath.Replace('\','/')
    if($path -like '.git/*' -or $path -like '.vs/*' -or $path -like '.vscode/*' -or $path -like '.idea/*' -or $path -like 'out/*' -or $path -like 'src/StarCluster.Game/.godot/*' -or $path -match '(^|/)(bin|obj|TestResults)/'){ return $true }
    if($path -match '\.(user|userosscache|sln\.docstates|uid)$' -or $path -match '(^|/)\.suo$' -or $path -match '(^|/)(\.DS_Store|Thumbs\.db)$'){ return $true }
    return $false
}
function Get-Cp102RepositoryOwnedFileSet {
    $map=@{}
    foreach($file in @(Get-ChildItem -LiteralPath $repositoryRoot -Recurse -File -Force)){
        $rel=$file.FullName.Substring($repositoryRoot.Length).TrimStart('\','/').Replace('\','/')
        if($rel -eq 'CHECKPOINT_102_SHA256SUMS.txt'){ continue }
        if(Test-IsGeneratedOrLocalPath -RelativePath $rel){ continue }
        $map[$rel]=$true
    }
    return $map
}
function Assert-Cp102GeneratedArtifactSequencePreflight {
    param($Expected)
    $outputDir=RelPath 'out/checkpoint-102'
    $null=New-Item -ItemType Directory -Path $outputDir -Force
    $probePaths=@((Join-Path $outputDir 'acceptance-summary.json'),(Join-Path $outputDir 'acceptance-summary.txt'))
    $created=@()
    foreach($probe in $probePaths){ if(-not (Test-Path -LiteralPath $probe -PathType Leaf)){ 'CP102 RepositoryOnly sequence preflight generated artifact' | Set-Content -LiteralPath $probe -Encoding ASCII; $created += $probe } }
    try {
        foreach($rel in @('out/checkpoint-102/acceptance-summary.json','out/checkpoint-102/acceptance-summary.txt','src/StarCluster.Core/bin/Debug/net8.0/generated.dll','src/StarCluster.Core/obj/generated.tmp','TestResults/generated.trx')){ Assert-True (Test-IsGeneratedOrLocalPath -RelativePath $rel) "Generated/local artifact policy failed to ignore '$rel'." }
        foreach($rel in @('README.md','src/StarCluster.Core/StarCluster.Core.csproj','docs/README.md')){ Assert-True (-not (Test-IsGeneratedOrLocalPath -RelativePath $rel)) "Generated/local artifact policy incorrectly ignored repository-owned path '$rel'." }
        $probeActual=Get-Cp102RepositoryOwnedFileSet
        Assert-True ($probeActual.Count -eq $Expected.Count) "CP102 RepositoryOnly-to-full-run sequence preflight failed: generated acceptance summaries changed repository-owned file count from $($Expected.Count) to $($probeActual.Count)."
        foreach($rel in $Expected.Keys){ Assert-True ($probeActual.ContainsKey([string]$rel)) "CP102 sequence preflight lost expected repository-owned path '$rel'." }
        foreach($rel in $probeActual.Keys){ Assert-True ($Expected.ContainsKey([string]$rel)) "CP102 sequence preflight treated generated/local path '$rel' as repository-owned." }
    }
    finally { foreach($probe in $created){ Remove-Item -LiteralPath $probe -Force -ErrorAction SilentlyContinue } }
}

Write-Host '       Validating native dependencies, wrapper interface, and checkpoint definitions...'
$normalRel='tools/calibration/checkpoints/checkpoint-102.json'
$deepRel='tools/calibration/checkpoints/checkpoint-102-deep-calibration.json'
$guarded=@(
    'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
    'tools/checkpoints/checkpoint-102/apply_checkpoint_102.ps1',
    'tools/checkpoints/checkpoint-102/test_checkpoint_102_contract.ps1',
    'tools/calibration/run_calibration_checkpoint.ps1'
)
& (RelPath 'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1') -RepositoryRoot $repositoryRoot -PowerShellPaths $guarded -CheckpointDefinitionPaths @($normalRel,$deepRel)
$apply=Read-Text 'tools/checkpoints/checkpoint-102/apply_checkpoint_102.ps1'
$typeCall='Assert-Cp102PowerShell51TypeCompatibility -Paths @($MyInvocation.MyCommand.Path, $contract)'
Require-Contains $apply 'function Assert-Cp102PowerShell51TypeCompatibility' 'CP102 wrapper must define the Windows PowerShell 5.1 type-token compatibility precheck.'
Require-Contains $apply $typeCall 'CP102 wrapper must invoke the Windows PowerShell 5.1 type-token compatibility precheck.'
Assert-True ($apply.IndexOf($typeCall,[StringComparison]::Ordinal) -lt $apply.IndexOf('& $guard -RepositoryRoot',[StringComparison]::Ordinal)) 'CP102 PowerShell 5.1 type-token precheck must run before the native dependency guard.'
Require-Contains $apply '& $harness -CheckpointDefinition $definition -Trials $Trials -Jobs $Jobs -RepositoryOnly:$RepositoryOnly -NoClean:$NoClean' 'CP102 wrapper must use the proven direct named-parameter harness invocation.'
Assert-True ($apply.IndexOf('@harnessArgs',[StringComparison]::OrdinalIgnoreCase) -lt 0) 'CP102 wrapper must not regress to array splatting for harness invocation.'

$normal=Read-Json $normalRel; $deep=Read-Json $deepRel
foreach($def in @($normal,$deep)){
    Assert-True ([int]$def.schemaVersion -eq 1 -and [string]$def.checkpointId -eq '102') 'CP102 checkpoint-definition identity drifted.'
    Assert-True ([string]$def.sdkVersion -eq '8.0.423' -and [string]$def.configuration -eq 'Debug') 'CP102 pinned SDK/configuration drifted.'
    Assert-True ([string]$def.manifestFile -eq 'CHECKPOINT_102_SHA256SUMS.txt' -and [string]$def.outputRoot -eq 'out/checkpoint-102') 'CP102 manifest/output binding drifted.'
    Assert-True ([int]$def.defaultTrials -eq 1 -and [int]$def.defaultJobs -eq 24) 'CP102 bounded default workload drifted.'
    Assert-True (@($def.stages).Count -eq 15 -and [int]$def.checkpointMetrics.stageCount -eq 15) 'CP102 must contain exactly 15 runner stages.'
    Assert-True ([int]$def.checkpointMetrics.expectedXunitTests -eq 876 -and [int]$def.checkpointMetrics.expectedRunnerSelfTests -eq 70) 'CP102 expected test/self-test counts drifted.'
    Assert-True ([int]$def.checkpointMetrics.totalTrialExecutionsAtDefault -eq 32 -and [int]$def.checkpointMetrics.smokeTrialsAtDefault -eq 32 -and [int]$def.checkpointMetrics.monteCarloVariantCount -eq 0) 'CP102 must remain a 32-execution smoke-only checkpoint.'
    Assert-True ([bool]$def.checkpointMetrics.tl3CombatConsumerEnabled -and -not [bool]$def.checkpointMetrics.tl3BalanceCalibrated -and -not [bool]$def.checkpointMetrics.tl3Promoted -and -not [bool]$def.checkpointMetrics.technologyPromotionAutomatic) 'CP102 executable/calibration/promotion lifecycle drifted.'
    $expectedStageIds=@('deterministic','tl1-phase-a','tl1-phase-b','tl1-installation-space-envelope','tl1-sensor-ew-foundation','cross-tl-cp99-exact-edge-preflight','cross-tl-cp99-exact-edge-generation','cross-tl-cp102-construction-envelope-preflight','cross-tl-cp102-transition-preflight','cross-tl-cp102-transition-generation','cross-tl-cp102-generated-study-preflight','cross-tl-cp102-generated-study-smoke','auxiliary-resource-endurance','checkpoint-53-resource-semantics-lock','runner-self-tests')
    Assert-Sequence @($def.stages|ForEach-Object{$_.id}) $expectedStageIds 'CP102 stage sequence drifted.'
    $smoke=@($def.stages|Where-Object{[string]$_.id -eq 'cross-tl-cp102-generated-study-smoke'}); Assert-True ($smoke.Count -eq 1 -and [int]$smoke[0].metrics.variantCount -eq 32 -and [int]$smoke[0].metrics.trialsPerVariant -eq 1 -and [int]$smoke[0].metrics.totalTrials -eq 32 -and [bool]$smoke[0].metrics.smokeOnly) 'CP102 generated smoke stage drifted.'
    Assert-Sequence @($smoke[0].arguments) @('--study-file','{OutputRoot}/cross-tl-cp102-transition/generated-integrated-combat-study.json','--baseline-file','docs/archive/player_technology/pre-cp165-active/tl1_core_combat_numerical_baseline_v0_3.csv','--trials','1','--jobs','{Jobs}','--output-dir','{OutputRoot}/cross-tl-cp102-generated-study-smoke') 'CP102 smoke must consume the generated v7 study with exactly one trial per variant.'
    foreach($doc in @($def.documentation)){ Assert-True (Test-Path -LiteralPath (RelPath ([string]$doc)) -PathType Leaf) "CP102 definition references missing documentation '$doc'." }
}
Assert-Sequence @($deep.stages|ForEach-Object{$_.id}) @($normal.stages|ForEach-Object{$_.id}) 'CP102 deep alias must use the same bounded stage sequence as normal.'
Assert-True ([string]$deep.description -eq [string]$normal.description) 'CP102 deep alias must use the same bounded workload/description as normal.'

Write-Host '       Validating accepted CP101 provenance and frozen executable regression surface...'
Assert-True ((Hash-Rel 'docs/validation/evidence/checkpoint-101/CHECKPOINT_101_SHA256SUMS.txt') -eq '674912367de56d5dd3775f2535bc768b636dbd625c0583362c3df024ee5d1fab') 'Embedded accepted CP101 manifest hash drifted.'
Assert-True ((Hash-Rel 'docs/archive/player_technology/pre-cp165-active/tl3_base_technology_candidates_v0_2.json') -eq '06c7e00a52a749a8e540c7a1d1235f91d7ef6ed67f5a5382f13621c58b275aac') 'Accepted CP101 TL3 base registry bytes drifted.'
Assert-True ((Hash-Rel 'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/cross-tl-build-permutation-foundation-v0_8.json') -eq '148f4aadda8d65891a961a6e981c77c67e4e28a00359f0ad476e2e257f5be944') 'Accepted CP99 v6 exact-edge foundation bytes drifted.'
$accepted=Read-Json 'docs/validation/evidence/checkpoint-101/checkpoint-101-native-acceptance-summary.json'
Assert-True ([string]$accepted.status -eq 'Success' -and [string]$accepted.checkpointDefinitionSha256 -eq '31c6fe641a562005af325034c925d76f7339f97827d21cad5989052a4872cba3' -and [string]$accepted.checkpointManifestSha256 -eq '674912367de56d5dd3775f2535bc768b636dbd625c0583362c3df024ee5d1fab') 'Embedded CP101 native acceptance provenance drifted.'
Assert-True ([int]$accepted.tests.total -eq 876 -and [int]$accepted.tests.passed -eq 876 -and [int]$accepted.tests.failed -eq 0 -and [int]$accepted.aggregates.configuredRunnerStages -eq 10 -and [int]$accepted.aggregates.runnerStagesPassed -eq 10 -and [int]$accepted.aggregates.selfTests -eq 63 -and [int]$accepted.aggregates.failedGates -eq 0) 'Embedded CP101 native acceptance counters drifted.'
$evidence=Read-Json 'docs/validation/evidence/checkpoint-101/cp101-tl3-base-evidence.json'
Assert-True ([string]$evidence.nativeResultsZipSha256 -eq '6320c62576097aed1f7f3060011f174d880cda5ead28576cf19d5fa14408f5d7' -and [int]$evidence.acceptedCp99Regression.legalBuilds -eq 11776 -and [int]$evidence.acceptedCp99Regression.progressionEdges -eq 37184 -and [string]$evidence.acceptedCp99Regression.generatedStudySha256 -eq 'f41cd6473bbe5987c417038c881b35731456c82557194e0b656eab5a41469ec4') 'CP101 retained executable evidence drifted.'

Write-Host '       Validating CP102 v7 construction envelope and typed transition declarations...'
$construction=Read-Json 'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/cross-tl-build-permutation-foundation-v0_9.json'
$transition=Read-Json 'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/cross-tl-build-permutation-foundation-v1_0.json'
foreach($study in @($construction,$transition)){
    Assert-True ([string]$study.schemaVersion -eq 'star-cluster-cross-tl-build-permutation-v7' -and [string]$study.checkpoint -eq '102') 'CP102 v7 study identity drifted.'
    Assert-True ([int]$study.totalInstallationSpace -eq 36 -and [int]$study.fixedShellSpace -eq 0) 'CP102 v7 must expose Hull capacity and all construction Space explicitly.'
    Assert-True ([int]$study.constructionGuardrails.minimumMainWeaponCount -eq 1 -and [int]$study.constructionGuardrails.minimumReactorCount -eq 1 -and [int]$study.constructionGuardrails.minimumSensorCount -eq 1 -and -not [bool]$study.constructionGuardrails.powerSufficiencyIsConstructionLegalityFilter) 'CP102 construction guardrails drifted.'
    Assert-True (-not [bool]$study.constructionGuardrails.ecmSameTypeRatingsAdditive -and -not [bool]$study.constructionGuardrails.eccmSameTypeRatingsAdditive -and [string]$study.constructionGuardrails.ewDuplicateResolution -eq 'highest_applicable_functional_rating') 'CP102 EW redundancy rule drifted.'
    Assert-True (@($study.axes).Count -eq 13) 'CP102 v7 must expose exactly 13 independent construction axes.'
    Assert-Sequence @($study.axes|ForEach-Object{$_.id}) @('hull','weapon','reactor','computer','sensor','shield','shieldHardener','armor','ecm','eccm','stl','ftl','pds') 'CP102 v7 axis order/identity drifted.'
}
Assert-True ([string]$construction.coverageMode -eq 'construction_envelope' -and [int]$construction.expectedRawCombinationCount -eq 221184 -and [int]$construction.expectedLegalBuildCount -eq 51264 -and [int]$construction.expectedExactFillBuildCount -eq 10752 -and [int]$construction.expectedNearFillBuildCount -eq 25536 -and [int]$construction.expectedUnderfilledBuildCount -eq 14976 -and [int]$construction.expectedGeneratedVariantCount -eq 0 -and -not [bool]$construction.progressionLattice.enabled) 'CP102 construction-envelope declared counts/role drifted.'
Assert-True ([string]$transition.coverageMode -eq 'transition_smoke' -and [int]$transition.expectedRawCombinationCount -eq 43008 -and [int]$transition.expectedLegalBuildCount -eq 38400 -and [int]$transition.expectedExactFillBuildCount -eq 13824 -and [int]$transition.expectedNearFillBuildCount -eq 23808 -and [int]$transition.expectedUnderfilledBuildCount -eq 768 -and [int]$transition.expectedLogicalPairingCount -eq 16 -and [int]$transition.expectedGeometryCount -eq 2 -and [int]$transition.expectedGeneratedVariantCount -eq 32 -and [bool]$transition.progressionLattice.enabled -and [int]$transition.progressionLattice.expectedTotalLegalEdgeCount -eq 220416) 'CP102 transition-smoke declared counts/role drifted.'
Assert-True ([string]$transition.generatedStudyId -eq 'tl3-cp102-16-transition-integrated-smoke') 'CP102 transition-smoke generated integrated study ID drifted.'
$transitionExpected=@{
    'hull-h2-to-h3'='capacity_integration|0|1|16896'; 'computer-c2-to-c3'='capability_addition|0|0|19200'; 'sensor-s2-to-s3'='operating_mode_addition|0|0|19200';
    'ecm-ecm2-to-ecm3'='power_efficiency|0|0|19200'; 'eccm-eccm2-to-eccm3'='power_efficiency|0|0|19200'; 'reactor-r2-to-r3'='miniaturization|-1|0|16896';
    'stl-stl2-to-stl3'='primary_performance|0|0|19200'; 'ftl-ftl2-to-ftl3'='primary_performance|0|0|19200'; 'shield-sh2-to-tl3-hardener-unlock'='optional_component_unlock|1|0|16896';
    'armor-a2-to-a3'='protection_maturation|0|0|19200'; 'weapon-k2-to-k3'='power_efficiency|0|0|6400'; 'weapon-e2-to-e3'='safe_output_maturation|0|0|6400';
    'weapon-m2-to-m3'='autonomy_propulsion|0|0|6400'; 'pds-k2-to-k3'='explicit_hold|0|0|5376'; 'pds-e2-to-e3'='power_efficiency|0|0|5376'; 'pds-amm2-to-amm3'='readiness_mode_addition|0|0|5376'
}
$transitionMap=@{}; foreach($x in @($transition.progressionLattice.transitions)){ Assert-True (-not $transitionMap.ContainsKey([string]$x.id)) "Duplicate CP102 transition '$($x.id)'."; $transitionMap[[string]$x.id]=$x }
Assert-True ($transitionMap.Count -eq 16) 'CP102 transition study must contain exactly 16 typed transitions.'
$edgeSum=0
foreach($id in $transitionExpected.Keys){
    Assert-True ($transitionMap.ContainsKey([string]$id)) "CP102 transition study is missing '$id'."
    $parts=([string]$transitionExpected[[string]$id]).Split('|'); $x=$transitionMap[[string]$id]
    Assert-True ([string]$x.kind -eq $parts[0] -and [int]$x.expectedInstallationSpaceDelta -eq [int]$parts[1] -and [int]$x.expectedCapacityDelta -eq [int]$parts[2] -and [int]$x.expectedLegalEdgeCount -eq [int]$parts[3]) "CP102 typed transition '$id' semantics/count drifted."
    $edgeSum += [int]$x.expectedLegalEdgeCount
}
Assert-True ($edgeSum -eq 220416) 'CP102 transition edge counts do not sum to 220,416.'
$pairings=@($transition.pairingGroups); Assert-True ($pairings.Count -eq 16) 'CP102 transition smoke must declare exactly one named pairing per transition.'
foreach($p in $pairings){ Assert-True ($transitionMap.ContainsKey([string]$p.progressionTransitionId)) "CP102 pairing '$($p.id)' does not bind a registered transition." }
$weaponAxes=@($transition.axes|Where-Object{[string]$_.id -eq 'weapon'}); Assert-True ($weaponAxes.Count -eq 1) 'CP102 transition smoke must declare exactly one weapon axis.'
$k3Options=@($weaponAxes[0].options|Where-Object{[string]$_.id -eq 'k3'}); Assert-True ($k3Options.Count -eq 1 -and [string]$k3Options[0].family -eq 'Kinetic' -and [int]$k3Options[0].powerCost -eq 0) 'CP102 authoritative K3 transition fixture must remain a Kinetic ordinary-fire 0-TP maturation.'
Assert-True ([string]$pairings[10].progressionTransitionId -eq 'weapon-k2-to-k3') 'CP102 deterministic named-pair order must keep weapon-k2-to-k3 as pairing 11 so smoke variants 021/022 remain diagnosable.'

Write-Host '       Validating CP102 runtime profiles and executable field ownership...'
$profiles=Read-Json 'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/tl1-tl3-standard-runtime-profiles-v0_4.json'
$legacyProfiles=Read-Json 'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/tl1-tl2-standard-runtime-profiles-v0_3.json'
Assert-True ([string]$profiles.schemaVersion -eq 'star-cluster-architecture-runtime-profile-catalog-v1' -and [string]$profiles.checkpoint -eq '102') 'CP102 runtime-profile catalog identity drifted.'
$profileMap=@{}; foreach($p in @($profiles.profiles)){ $profileMap[[string]$p.id]=$p }
$legacyProfileMap=@{}; foreach($p in @($legacyProfiles.profiles)){ $legacyProfileMap[[string]$p.id]=$p }
foreach($legacyId in @('tl1-production','tl2-production')) {
    Assert-True ($legacyProfileMap.ContainsKey($legacyId) -and $profileMap.ContainsKey($legacyId)) "Runtime catalog is missing frozen legacy profile '$legacyId'."
    Assert-True ((ConvertTo-Json $legacyProfileMap[$legacyId] -Depth 20 -Compress) -eq (ConvertTo-Json $profileMap[$legacyId] -Depth 20 -Compress)) "CP102 runtime catalog drifted frozen legacy profile '$legacyId'."
}
foreach($id in @('tl1-production','tl2-production','tl2-cp102-integration-reference','tl3-cp102-executable-candidate')){ Assert-True ($profileMap.ContainsKey($id)) "CP102 runtime-profile catalog is missing '$id'." }
Assert-True ([int]$profileMap['tl3-cp102-executable-candidate'].powerAndControl.reactorOutput -eq 6) 'TL3 runtime reactor output must remain 6 TP.'

$implementation=Read-Json 'docs/archive/player_technology/pre-cp165-active/tl3_executable_implementation_profile_v0_1.json'
Assert-True ([int]$implementation.checkpoint -eq 102 -and [string]$implementation.status -eq 'implemented_executable_candidate_not_calibrated_not_promoted') 'CP102 implementation profile lifecycle drifted.'
Assert-True (-not [bool]$implementation.lifecycle.candidateValuesChanged -and [bool]$implementation.lifecycle.implemented -and -not [bool]$implementation.lifecycle.calibrated -and -not [bool]$implementation.lifecycle.promoted -and -not [bool]$implementation.lifecycle.balanceEvidence) 'CP102 must remain implementation-only, not calibration/promotion.'
Assert-True ([bool]$implementation.constructionConsumer.variableHullCapacity -and [bool]$implementation.constructionConsumer.spaceChangingProgressionSupported -and [bool]$implementation.constructionConsumer.capacityChangingProgressionSupported -and [bool]$implementation.constructionConsumer.optionalUnlockProgressionSupported) 'CP102 implementation profile must declare variable-capacity/typed progression support.'
Assert-True ([int]$implementation.transitionConsumer.declaredTransitionCount -eq 16 -and [int]$implementation.transitionConsumer.legalProgressionEdgeCount -eq 220416 -and [int]$implementation.transitionConsumer.tinySmokeVariants -eq 32 -and [int]$implementation.transitionConsumer.trialsPerVariant -eq 1) 'CP102 implementation-profile transition arithmetic drifted.'

$crossSource=Read-Text 'src/StarCluster.ScenarioRunner/CrossTlIntegration/CrossTlBuildPermutationRunner.cs'
foreach($needle in @('coverageMode','expectedInstallationSpaceDelta','expectedCapacityDelta','ShieldHardenerCompatibilityForSelfTest','EwFullStrengthNormalPowerCost','PdsFallbackPowerCost','tl3-cp102-executable-candidate')){ Require-Contains $crossSource $needle "CP102 cross-TL consumer is missing required runtime binding '$needle'." }
$edgeRecord=[regex]::Match($crossSource,'public sealed record CrossTlProgressionEdge\((?<Body>[\s\S]*?)\);')
Assert-True $edgeRecord.Success 'CP102 preflight could not locate the CrossTlProgressionEdge record declaration.'
$declaredEdgeMembers=@([regex]::Matches($edgeRecord.Groups['Body'].Value,'(?m)^\s*[A-Za-z_][A-Za-z0-9_<>,?]*\s+(?<Name>[A-Za-z_][A-Za-z0-9_]*)\s*,?\s*$') | ForEach-Object { $_.Groups['Name'].Value })
$usedEdgeMembers=@([regex]::Matches($crossSource,'\bedge\.(?<Name>[A-Za-z_][A-Za-z0-9_]*)') | ForEach-Object { $_.Groups['Name'].Value } | Sort-Object -Unique)
foreach($member in $usedEdgeMembers){ Assert-True ($declaredEdgeMembers -contains $member) "CP102 compile-surface preflight: CrossTlProgressionEdge consumer references undeclared member '$member'." }
foreach($needle in @('edge.LowerBuildId','edge.HigherBuildId')){ Require-Contains $crossSource $needle "CP102 named-pairing validation must bind CrossTlProgressionEdge endpoints through '$needle'." }
Assert-True ($crossSource.IndexOf('edge.LowerBuild.',[StringComparison]::Ordinal) -lt 0 -and $crossSource.IndexOf('edge.HigherBuild.',[StringComparison]::Ordinal) -lt 0) 'CP102 compile-surface preflight forbids treating CrossTlProgressionEdge endpoint IDs as embedded build objects.'
$docsSource=Read-Text 'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatDocuments.cs'
foreach($needle in @('pdsFallbackPowerCost','shieldHardenerArmor','tacticalComputerEvasiveCompensation','sideAEcmFullStrengthNormalPowerCostOverride','sideAEccmFullStrengthNormalPowerCostOverride')){ Require-Contains $docsSource $needle "CP102 integrated-combat document is missing '$needle'." }
$combatSource=Read-Text 'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs'
foreach($needle in @('BuildShieldHardenerFunctional','ApplyEvasiveCompensationForSelfTest','PdsFallbackPowerCost','fullStrengthNormalPowerCostOverride','TacticalComputerEvasiveCompensation','InitialBuildPdsAmmunitionForSelfTest','SpendAttackPowerForSelfTest')){ Require-Contains $combatSource $needle "CP102 integrated-combat runtime is missing '$needle'." }
Require-Contains $combatSource 'private static void SpendAttackPower(' 'CP102 integrated combat must centralize attack-power spending behind a zero-safe helper.'
Require-Contains $combatSource 'if (tacticalPowerCost > 0)' 'CP102 attack-power helper must treat zero Tactical Power as a valid no-op.'
Assert-True (([regex]::Matches($combatSource,'SpendAttackPower\(attacker\.Power, performance\.TacticalPowerCost\);')).Count -eq 2) 'CP102 direct-fire and missile-launch consumers must both route attack power through the zero-safe helper.'
Assert-True ($combatSource.IndexOf('attacker.Power.Spend(performance.TacticalPowerCost)',[StringComparison]::Ordinal) -lt 0) 'CP102 integrated combat must not pass a valid zero-cost weapon directly to TacticalPowerLedger.Spend().'
Require-Contains $combatSource 'SpendAttackPowerForSelfTest(6, 0)' 'CP102 generated-study actual-consumer preflight must execute the 0-TP attack-power path before smoke trials.'
Require-Contains $combatSource 'SpendAttackPowerForSelfTest(6, 1)' 'CP102 generated-study actual-consumer preflight must retain a positive-cost attack-power control.'
Require-Contains $combatSource 'TRIAL ERROR variant' 'CP102 trial-error handling must print the failing variant and trial context.'
Require-Contains $combatSource '{exception}' 'CP102 trial-error handling must retain the full exception and stack trace rather than only incrementing a counter.'
$powerLedgerSource=Read-Text 'src/StarCluster.Core/Combat/Power/TacticalPowerLedger.cs'
Require-Contains $powerLedgerSource 'if (amount <= 0)' 'CP102 must preserve TacticalPowerLedger.Spend as a positive-quantity API; zero-cost actions must bypass it rather than weakening the ledger contract.'
Require-Contains $powerLedgerSource 'Spent power must be positive.' 'CP102 must preserve the existing positive-spend ledger invariant.'
$generatedStudyId=[string]$transition.generatedStudyId
Require-Contains $combatSource ('"' + $generatedStudyId + '"') 'CP102 actual integrated-combat consumer must declare the generated v7 smoke study ID emitted by the producer.'
Require-Contains $combatSource 'private const int RequiredTl3Cp102TransitionSmokeVariantCount = 32;' 'CP102 actual consumer must declare the generated smoke required variant count.'
Assert-True ([regex]::IsMatch($combatSource,'Tl3Cp102TransitionSmokeStudyId\s*=>\s*RequiredTl3Cp102TransitionSmokeVariantCount')) 'CP102 actual consumer required-count dispatch must register the generated v7 smoke study.'
Require-Contains $combatSource 'studyId == Tl3Cp102TransitionSmokeStudyId;' 'CP102 generated smoke must enter the Adaptive Engage/operational Sensor-EW runtime classifier.'
Require-Contains $combatSource 'study.Id == Tl3Cp102TransitionSmokeStudyId;' 'CP102 generated smoke must enter the generalized multi-bay study legality classifier.'
Require-Contains $combatSource 'else if (study.Id == Tl3Cp102TransitionSmokeStudyId)' 'CP102 actual-consumer validation routing must recognize the generated v7 smoke study.'
Require-Contains $combatSource 'ValidateTl3Cp102TransitionSmokeCoverage(' 'CP102 actual consumer must provide dedicated generated-smoke coverage validation.'
Assert-True (([regex]::Matches($combatSource,'studyId == Tl3Cp102TransitionSmokeStudyId')).Count -ge 2) 'CP102 generated smoke must be registered in both Adaptive Engage and stateful build-level power/auxiliary classifiers.'
Require-Contains $combatSource 'if (study.Id == Tl3Cp102TransitionSmokeStudyId)' 'CP102 output routing must recognize the generated smoke without falling through to an unrelated legacy review writer.'
Assert-True (-not [regex]::IsMatch($combatSource,'IsTl3CandidateStudy\(study\.Id\)[\s\S]{0,180}study\.Id == Tl3Cp102TransitionSmokeStudyId\)')) 'CP102 generated smoke must not be routed through the legacy TL3 candidate review writer.'
$selfTests=Read-Text 'src/StarCluster.ScenarioRunner/ScenarioRunnerSelfTests.cs'
foreach($needle in @('CP102','ShieldHardenerCompatibilityForSelfTest','ApplyEvasiveCompensationForSelfTest','PdsReadinessModeForSelfTest','EffectiveRatedEwPowerCostForSelfTest','InitialBuildPdsAmmunitionForSelfTest','SpendAttackPowerForSelfTest')){ Require-Contains $selfTests $needle "CP102 ScenarioRunner self-test surface is missing '$needle'." }

Write-Host '       Validating standing suite, Matrix/catalog lifecycle, and active documentation authority...'
$suite=Read-Json 'docs/design/testing/technology_integration_permutation_suite_v0_17.json'
Assert-True ([int]$suite.checkpoint -eq 102 -and [bool]$suite.tl3BaseTableComplete -and [bool]$suite.tl3CombatConsumerEnabled -and [bool]$suite.cp102NoBalanceInference) 'Standing suite v0.17 executable/non-balance boundary drifted.'
Assert-True ([string]$suite.tl3CandidateRegistration.profile -eq 'docs/archive/player_technology/pre-cp165-active/tl3_base_technology_candidates_v0_2.json' -and [string]$suite.tl3ExecutableImplementationProfile -eq 'docs/archive/player_technology/pre-cp165-active/tl3_executable_implementation_profile_v0_1.json') 'Standing suite v0.17 TL3 bindings drifted.'
$registered=@($suite.tl3CandidateRegistration.registeredTransitions); Assert-True ($registered.Count -eq 16) 'Standing suite v0.17 must register exactly 16 TL3 transitions.'
$registeredMap=@{}; foreach($x in $registered){ $registeredMap[[string]$x.id]=$x }
foreach($id in $transitionExpected.Keys){ Assert-True ($registeredMap.ContainsKey([string]$id)) "Standing suite v0.17 is missing '$id'."; Assert-True ([string]$registeredMap[[string]$id].kind -eq [string]$transitionMap[[string]$id].kind) "Standing suite/runtime transition kind differs for '$id'." }
Assert-True (@($suite.reusableAxes.informationControlPackage) -contains 'tl3-base-executable-candidate') 'Standing suite v0.17 must expose TL3 information-control as an executable candidate rather than a registered-only placeholder.'
Assert-True (@($suite.reusableAxes.powerReactorPackage) -contains 'tl3-mature-compact-fusion-executable-candidate') 'Standing suite v0.17 must expose TL3 compact fusion as an executable candidate rather than a registered-only placeholder.'
Assert-True ((Read-Text 'docs/design/testing/technology_integration_permutation_suite_v0_17.json').IndexOf('registered-not-runtime',[StringComparison]::OrdinalIgnoreCase) -lt 0) 'Standing suite v0.17 must not retain stale registered-not-runtime TL3 labels after executable integration.'

$matrix=Read-Json 'docs/archive/player_technology/pre-cp165-active/technology_architecture_matrix_v1.json'
Assert-True ([int]$matrix.checkpoint -eq 102 -and [string]$matrix.authority.concept -eq 'docs/Star_Cluster_Game_Concept_v0.7d.docx' -and [string]$matrix.integrationArchitecture.standingPermutationSuite -eq 'docs/design/testing/technology_integration_permutation_suite_v0_17.json' -and [bool]$matrix.integrationArchitecture.tl3CombatConsumerEnabled) 'Technology Matrix CP102 authority/runtime binding drifted.'
$tier3=@($matrix.tiers|Where-Object{[int]$_.technologyLevel -eq 3}); Assert-True ($tier3.Count -eq 1 -and [bool]$tier3[0].combatConsumerEnabled) 'Technology Matrix TL3 executable status drifted.'
Assert-True ([int]$tier3[0].hull.installationSpaceCapacity -eq 36 -and [int]$tier3[0].powerReactor.operationalTacticalPower -eq 6 -and [int]$tier3[0].powerReactor.installationSpace -eq 5) 'Technology Matrix representative TL3 Hull/Reactor values drifted.'
$tier2=@($matrix.tiers|Where-Object{[int]$_.technologyLevel -eq 2}); Assert-True ($tier2.Count -eq 1) 'Technology Matrix TL2 authority row is missing.'
Require-Contains ([string]$tier2[0].armor.notes) 'CP102 implements AP1/AI5 as the distinct TL3 executable candidate' 'Technology Matrix TL2 Armor note must reflect the CP102 executable TL3 AP1 lifecycle.'
$auxCatalog=Read-Json 'docs/archive/player_technology/pre-cp165-active/auxiliary_component_catalog_v0_1.json'
$hardener=@($auxCatalog.components|Where-Object{[string]$_.id -eq 'aux_shield_hardener'}); Assert-True ($hardener.Count -eq 1) 'Auxiliary catalog Shield Hardener entry is missing.'
Assert-True ([string]$hardener[0].availabilityStatus -eq 'tl3_executable_candidate_not_calibrated_not_promoted' -and [string]$hardener[0].candidateProfile.status -eq 'implemented_executable_candidate_not_calibrated_not_promoted') 'Auxiliary catalog Shield Hardener lifecycle must match CP102 executable/not-calibrated/not-promoted status.'
$catalog=Read-Json 'docs/archive/player_technology/pre-cp165-active/component_installation_space_catalog_v1.json'
Assert-True ([int]$catalog.checkpoint -eq 102 -and [string]$catalog.authority.concept -eq 'docs/Star_Cluster_Game_Concept_v0.7d.docx') 'Component catalog CP102 authority binding drifted.'
Assert-True ([int]$catalog.globalRules.minimumMainWeaponCount -eq 1 -and [int]$catalog.globalRules.minimumReactorCount -eq 1 -and [int]$catalog.globalRules.minimumSensorCount -eq 1 -and -not [bool]$catalog.globalRules.simultaneousTacticalPowerSufficiencyRequiredForConstruction) 'Component catalog construction guardrails drifted.'

$policy=Read-Json 'docs/design/testing/checkpoint_102_validation_suite_policy_v0_1.json'
Assert-True ([int]$policy.checkpoint -eq 102 -and [int]$policy.acceptedBaseline.checkpoint -eq 101 -and [string]$policy.acceptedBaseline.checkpointDefinitionSha256 -eq '31c6fe641a562005af325034c925d76f7339f97827d21cad5989052a4872cba3' -and [string]$policy.acceptedBaseline.checkpointManifestSha256 -eq '674912367de56d5dd3775f2535bc768b636dbd625c0583362c3df024ee5d1fab') 'CP102 validation-policy baseline binding drifted.'
Assert-True ([int]$policy.cp102V7.constructionLegalBuilds -eq 51264 -and [int]$policy.cp102V7.transitionLegalBuilds -eq 38400 -and [int]$policy.cp102V7.progressionLegalEdges -eq 220416 -and [int]$policy.cp102V7.registeredTransitions -eq 16 -and [int]$policy.cp102V7.generatedSmokeVariants -eq 32 -and [int]$policy.cp102V7.totalSmokeTrials -eq 32) 'CP102 validation-policy v7 arithmetic drifted.'
Assert-True ([int]$policy.expected.xunitTests -eq 876 -and [int]$policy.expected.runnerStages -eq 15 -and [int]$policy.expected.scenarioRunnerSelfTests -eq 70 -and [int]$policy.expected.totalTrialExecutions -eq 32 -and -not [bool]$policy.deepCalibration.applicable) 'CP102 validation-policy acceptance workload drifted.'
Assert-True ([bool]$policy.preflight.crossTlProgressionEdgeMemberSurface) 'CP102 validation policy must require CrossTlProgressionEdge compile-surface member validation.'
Assert-True ([bool]$policy.preflight.integratedGeneratedStudyRegistrationSurface) 'CP102 validation policy must require generated integrated-study registration-surface validation.'
Assert-True ([bool]$policy.preflight.zeroCostWeaponSpendSemantics) 'CP102 validation policy must require zero-cost weapon spend semantics validation.'
Assert-True ([bool]$policy.preflight.trialExceptionStackTraceDiagnostics) 'CP102 validation policy must require full trial-exception diagnostics.'
Require-Contains (Read-Text 'docs/design/testing/Checkpoint_102_Validation_Tiers.md') 'compile-surface guard' 'CP102 validation tiers must document the RepositoryOnly CrossTlProgressionEdge compile-surface guard.'
Require-Contains (Read-Text 'docs/design/testing/Checkpoint_102_Validation_Tiers.md') 'generated-study producer/consumer registration surface' 'CP102 validation tiers must document the generated-study consumer-registration preflight.'
Require-Contains (Read-Text 'docs/validation/Checkpoint_102_TL3_Executable_Consumer_Integration.md') 'Corrected replacement 2' 'CP102 runbook must document the generated-study registration correction.'
Require-Contains (Read-Text 'docs/validation/Checkpoint_102_TL3_Executable_Consumer_Integration.md') 'Corrected replacement 3' 'CP102 runbook must document the zero-TP direct-fire execution correction.'
Require-Contains (Read-Text 'docs/design/testing/Checkpoint_102_Validation_Tiers.md') 'zero-cost weapon execution preflight' 'CP102 validation tiers must document the zero-cost weapon preflight.'
Require-Contains (Read-Text 'docs/development/Simulation_Development_Guidelines.md') 'producer''s emitted `generatedStudyId`' 'Durable simulation guidelines must require producer/consumer generated-study ID registration validation.'
Require-Contains (Read-Text 'docs/development/Simulation_Development_Guidelines.md') 'Zero-cost executable actions are first-class values' 'Durable simulation guidelines must require zero-cost resource actions to bypass positive-only spend APIs.'
Require-Contains (Read-Text 'docs/development/Simulation_Development_Guidelines.md') 'Counted trial errors must still preserve full diagnostics' 'Durable simulation guidelines must require full diagnostics for counted trial exceptions.'
Assert-ExactFileSet 'docs/design/testing' @('README.md','Checkpoint_102_Validation_Tiers.md','checkpoint_102_validation_suite_policy_v0_1.json','Technology_Integration_Permutation_Suite_Architecture_v0_17.md','technology_integration_permutation_suite_v0_17.json')
Assert-ExactFileSet 'docs/validation' @('README.md','Checkpoint_102_TL3_Executable_Consumer_Integration.md')
$activeConcepts=@(Get-ChildItem -LiteralPath (RelPath 'docs') -File -Filter 'Star_Cluster_Game_Concept*.docx' | ForEach-Object Name); Assert-True ($activeConcepts.Count -eq 1 -and $activeConcepts[0] -eq 'Star_Cluster_Game_Concept_v0.7d.docx') 'Exactly Concept v0.7d must be active.'
foreach($p in @('README.md','CHAT_README.md','docs/README.md','docs/design/README.md','docs/design/player_technology/README.md','docs/design/testing/README.md','docs/validation/README.md','docs/Prototype_TODO.md','docs/development/Simulation_Development_Guidelines.md','docs/design/player_technology/Technology_Architecture_Matrix_v1.md','docs/design/testing/Technology_Integration_Permutation_Suite_Architecture_v0_17.md','docs/validation/Checkpoint_102_TL3_Executable_Consumer_Integration.md')){
    $text=Read-Text $p
    Assert-True ($text.IndexOf('Concept v0.7c',[StringComparison]::OrdinalIgnoreCase) -lt 0) "Active document '$p' still describes Concept v0.7c as current."
    Assert-True ($text.IndexOf('suite v0.16',[StringComparison]::OrdinalIgnoreCase) -lt 0) "Active document '$p' still describes suite v0.16 as current."
}

Write-Host '       Validating final repository manifest and RepositoryOnly-to-full-run sequence safety...'
$manifest=Read-Manifest 'CHECKPOINT_102_SHA256SUMS.txt'
$actual=Get-Cp102RepositoryOwnedFileSet
Assert-True ($actual.Count -eq $manifest.EntryCount) "CP102 manifest entry count $($manifest.EntryCount) does not match repository-owned file count $($actual.Count)."
foreach($rel in $manifest.Entries.Keys){
    Assert-True ($actual.ContainsKey([string]$rel)) "CP102 manifest lists missing/unowned path '$rel'."
    Assert-True ((Hash-Rel ([string]$rel)) -eq [string]$manifest.Entries[[string]$rel]) "CP102 manifest hash mismatch for '$rel'."
}
foreach($rel in $actual.Keys){ Assert-True ($manifest.Entries.ContainsKey([string]$rel)) "Repository-owned path '$rel' is missing from CP102 manifest." }
Assert-True (-not $manifest.Entries.ContainsKey('CHECKPOINT_101_SHA256SUMS.txt')) 'Superseded CP101 root manifest must not remain repository-owned in CP102.'
Assert-Cp102GeneratedArtifactSequencePreflight -Expected $actual

Write-Host "       CP102 contract verified: $($manifest.EntryCount) repository-owned files; CP101 frozen authorities preserved; v7 construction 221,184 raw / 51,264 legal; typed transition smoke 43,008 raw / 38,400 legal / 220,416 edges / 32 one-trial variants."
