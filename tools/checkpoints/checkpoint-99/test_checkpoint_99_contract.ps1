[CmdletBinding()]
param([string]$RepositoryRoot)

Set-StrictMode -Version 2.0
$ErrorActionPreference='Stop'
if([string]::IsNullOrWhiteSpace($RepositoryRoot)){ $repositoryRoot=(Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path } else { $repositoryRoot=(Resolve-Path $RepositoryRoot).Path }
function Assert-True { param([bool]$Condition,[string]$Message) if(-not $Condition){ throw $Message } }
function RelPath { param([string]$RelativePath) Join-Path $repositoryRoot ($RelativePath.Replace('/','\')) }
function Read-Text { param([string]$RelativePath) $p=RelPath $RelativePath; Assert-True (Test-Path -LiteralPath $p -PathType Leaf) "Required file '$RelativePath' is missing."; [IO.File]::ReadAllText($p) }
function Read-Json { param([string]$RelativePath) (Read-Text $RelativePath) | ConvertFrom-Json }
function Hash-Rel { param([string]$RelativePath) (Get-FileHash -LiteralPath (RelPath $RelativePath) -Algorithm SHA256).Hash.ToLowerInvariant() }
function Require-Contains { param([string]$Text,[string]$Needle,[string]$Message) Assert-True ($Text.IndexOf($Needle,[StringComparison]::Ordinal) -ge 0) $Message }
function Require-NotContains { param([string]$Text,[string]$Needle,[string]$Message) Assert-True ($Text.IndexOf($Needle,[StringComparison]::Ordinal) -lt 0) $Message }
function Read-Manifest {
 param([string]$RelativePath)
 $map=@{}; $lines=@(Get-Content -LiteralPath (RelPath $RelativePath)); $n=0
 foreach($line in $lines){ $n++; $m=[regex]::Match([string]$line,'^([0-9a-fA-F]{64})  (.+)$'); Assert-True $m.Success "Manifest '$RelativePath' malformed at line $n."; $r=$m.Groups[2].Value.Replace('\','/'); Assert-True (-not $map.ContainsKey($r)) "Manifest '$RelativePath' duplicates '$r'."; $map[$r]=$m.Groups[1].Value.ToLowerInvariant() }
 [pscustomobject]@{ EntryCount=$map.Count; PhysicalLineCount=$lines.Count; Entries=$map }
}
function Assert-Sequence { param([object[]]$Actual,[string[]]$Expected,[string]$Message) Assert-True ($Actual.Count -eq $Expected.Count) $Message; for($i=0;$i -lt $Expected.Count;$i++){ Assert-True ([string]$Actual[$i] -eq $Expected[$i]) $Message } }
function Assert-ExactFileSet { param([string]$RelativeDirectory,[string[]]$Expected) $a=@(Get-ChildItem -LiteralPath (RelPath $RelativeDirectory) -File | ForEach-Object Name | Sort-Object); $w=@($Expected|Sort-Object); Assert-True ($a.Count -eq $w.Count) "Directory '$RelativeDirectory' active file count drifted."; for($i=0;$i -lt $w.Count;$i++){ Assert-True ($a[$i] -eq $w[$i]) "Directory '$RelativeDirectory' active file set drifted: expected '$($w[$i])', found '$($a[$i])'." } }
function Assert-NoNestedLocalShadowing {
 param([string]$Text,[string]$MethodMarker,[string]$MessagePrefix)
 $start=$Text.IndexOf($MethodMarker,[StringComparison]::Ordinal); Assert-True ($start -ge 0) "$MessagePrefix method marker was not found."
 $next=$Text.IndexOf("`n    private static ",$start+$MethodMarker.Length,[StringComparison]::Ordinal); if($next -lt 0){$next=$Text.Length}
 $method=$Text.Substring($start,$next-$start)
 $matches=[regex]::Matches($method,'(?m)^(?<indent>[ \t]+)(?:(?:const\s+)?(?:bool|byte|sbyte|short|ushort|int|uint|long|float|double|decimal|string|var|[A-Z][A-Za-z0-9_<>?,.\[\]]*))\s+(?<name>[A-Za-z_][A-Za-z0-9_]*)\s*=')
 $seen=@{}
 foreach($m in $matches){ $name=$m.Groups['name'].Value; $indent=$m.Groups['indent'].Value.Replace("`t",'    ').Length; if(-not $seen.ContainsKey($name)){ $seen[$name]=New-Object System.Collections.ArrayList }; $null=$seen[$name].Add($indent) }
 foreach($name in $seen.Keys){ $depths=@($seen[$name]|Sort-Object -Unique); Assert-True ($depths.Count -le 1) "$MessagePrefix local '$name' is redeclared at nested indentation depths ($($depths -join ', ')); this can trigger C# CS0136 shadowing." }
}
function Get-OptionById { param($Axis,[string]$Id) $m=@($Axis.options|Where-Object id -eq $Id); Assert-True ($m.Count -eq 1) "Axis '$($Axis.id)' option '$Id' was not unique."; $m[0] }
function Count-AdvancedComponents {
 param($Selected)
 $count=0; $weapon=$Selected['weapon']; $reactor=$Selected['reactor']
 if([int]$weapon.technologyLevel -ge 2){$count += [int]$weapon.mainWeaponCount}
 if([int]$reactor.technologyLevel -ge 2){$count += [int]$reactor.reactorCount}
 foreach($axisId in @('computer','sensor','shield','armor')){ $o=$Selected[$axisId]; $installed=$true; if($o.PSObject.Properties.Name -contains 'installed'){$installed=[bool]$o.installed}; if($installed -and [int]$o.technologyLevel -ge 2){$count++} }
 foreach($axisId in @('ecm','eccm')){ foreach($rating in @($Selected[$axisId].ewRatings)){ if([int]$rating -ge 2){$count++} } }
 $count
}
function Get-OptionAdvancedContribution {
 param([string]$AxisId,$Option)
 if([int]$Option.technologyLevel -lt 2){ return 0 }
 switch($AxisId){
  'weapon' { if($Option.PSObject.Properties.Name -contains 'mainWeaponCount'){ return [int]$Option.mainWeaponCount }; return 1 }
  'reactor' { if($Option.PSObject.Properties.Name -contains 'reactorCount'){ return [int]$Option.reactorCount }; return 1 }
  'computer' { return 1 }
  'sensor' { if($Option.PSObject.Properties.Name -contains 'installed' -and -not [bool]$Option.installed){ return 0 }; return 1 }
  'shield' { if($Option.PSObject.Properties.Name -contains 'installed' -and -not [bool]$Option.installed){ return 0 }; return 1 }
  'armor' { if($Option.PSObject.Properties.Name -contains 'installed' -and -not [bool]$Option.installed){ return 0 }; return 1 }
  'ecm' { $n=0; foreach($rating in @($Option.ewRatings)){ if([int]$rating -ge 2){$n++} }; return $n }
  'eccm' { $n=0; foreach($rating in @($Option.ewRatings)){ if([int]$rating -ge 2){$n++} }; return $n }
  default { return 0 }
 }
}

Write-Host '       Validating native dependencies, wrapper interface, and checkpoint definitions...'
$normalRel='tools/calibration/checkpoints/checkpoint-99.json'; $deepRel='tools/calibration/checkpoints/checkpoint-99-deep-calibration.json'
$guarded=@('tools/checkpoints/Test-NativeAcceptanceDependencies.ps1','tools/checkpoints/checkpoint-99/apply_checkpoint_99.ps1','tools/checkpoints/checkpoint-99/test_checkpoint_99_contract.ps1','tools/calibration/run_calibration_checkpoint.ps1')
& (RelPath 'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1') -RepositoryRoot $repositoryRoot -PowerShellPaths $guarded -CheckpointDefinitionPaths @($normalRel,$deepRel)
$apply=Read-Text 'tools/checkpoints/checkpoint-99/apply_checkpoint_99.ps1'
$typeCompatibilityCall='Assert-Cp99PowerShell51TypeCompatibility -Paths @($MyInvocation.MyCommand.Path, $contract)'
Require-Contains $apply 'function Assert-Cp99PowerShell51TypeCompatibility' 'CP99 wrapper must define the Windows PowerShell 5.1 type-token compatibility precheck.'
Require-Contains $apply $typeCompatibilityCall 'CP99 wrapper must invoke the Windows PowerShell 5.1 type-token compatibility precheck.'
Assert-True ($apply.IndexOf($typeCompatibilityCall,[StringComparison]::Ordinal) -lt $apply.IndexOf('& $guard -RepositoryRoot',[StringComparison]::Ordinal)) 'CP99 PowerShell 5.1 type-token precheck must run before the shared dependency guard.'
Require-Contains $apply 'unreviewed or unsupported type token' 'CP99 wrapper must explicitly reject unreviewed PowerShell type tokens.'
Require-Contains $apply '& $harness -CheckpointDefinition $definition -Trials $Trials -Jobs $Jobs -RepositoryOnly:$RepositoryOnly -NoClean:$NoClean' 'CP99 wrapper must preserve direct named-parameter harness invocation.'
Assert-True (-not [regex]::IsMatch($apply,'&\s+\$harness\s+@[A-Za-z_]',[System.Text.RegularExpressions.RegexOptions]::IgnoreCase)) 'CP99 wrapper must not splat harness arguments.'
$stageIds=@('deterministic','tl1-phase-a','tl1-phase-b','tl1-installation-space-envelope','tl1-sensor-ew-foundation','cross-tl-build-permutation-preflight','cross-tl-build-permutation-generation','cross-tl-generated-study-preflight','cross-tl-generated-study-smoke','adaptive-engage-preflight','adaptive-engage-smoke','cross-tl-cp98-progression-preflight','cross-tl-cp98-progression-generation','cross-tl-cp98-generated-study-preflight','cross-tl-cp98-generated-study-smoke','cross-tl-cp99-exact-edge-preflight','cross-tl-cp99-exact-edge-generation','cross-tl-cp99-generated-study-preflight','cross-tl-cp99-generated-study-smoke','cross-tl-cp99-exact-edge-study','auxiliary-resource-endurance','checkpoint-53-resource-semantics-lock','runner-self-tests')
foreach($d in @((Read-Json $normalRel),(Read-Json $deepRel))){
 Assert-True ([string]$d.checkpointId -eq '99' -and [string]$d.manifestFile -eq 'CHECKPOINT_99_SHA256SUMS.txt') 'CP99 definition/manifest binding mismatch.'
 Assert-True ([string]$d.outputRoot -eq 'out/checkpoint-99') 'CP99 outputRoot must be out/checkpoint-99; inherited predecessor output roots are forbidden.'
 Assert-True ([int]$d.defaultTrials -eq 250 -and [int]$d.defaultJobs -eq 24) 'CP99 default trials/jobs mismatch.'
 Assert-True (@($d.stages).Count -eq 23 -and [int]$d.checkpointMetrics.stageCount -eq 23) 'CP99 must configure exactly 23 runner stages.'
 Assert-Sequence @($d.stages|ForEach-Object{[string]$_.id}) $stageIds 'CP99 stage order drifted.'
 Assert-Sequence @($d.nativeDependencyPrecheck.powerShellPaths) $guarded 'CP99 guarded PowerShell path list drifted.'
 Assert-Sequence @($d.nativeDependencyPrecheck.checkpointDefinitionPaths) @($normalRel,$deepRel) 'CP99 guarded definition list drifted.'
 Assert-True ([long]$d.checkpointMetrics.trialsAtDefault -eq 181000 -and [long]$d.checkpointMetrics.smokeTrialsAtDefault -eq 3160 -and [long]$d.checkpointMetrics.totalTrialExecutionsAtDefault -eq 184160) 'CP99 stochastic execution accounting mismatch.'
 Assert-True ([int]$d.checkpointMetrics.monteCarloVariantCount -eq 724 -and [int]$d.checkpointMetrics.legalBuildCount -eq 11776 -and [int]$d.checkpointMetrics.progressionLatticeLegalEdges -eq 37184 -and [int]$d.checkpointMetrics.exactEdgeStratumCount -eq 181 -and [int]$d.checkpointMetrics.logicalPairingCount -eq 362) 'CP99 exact-edge metrics mismatch.'
 Assert-True ([bool]$d.checkpointMetrics.mandatorySensorConstructionCore -and [bool]$d.checkpointMetrics.exactEdgeProgressionScreening -and -not [bool]$d.checkpointMetrics.initiativeRuleChanged -and -not [bool]$d.checkpointMetrics.newTl3Values -and -not [bool]$d.checkpointMetrics.technologyPromotionAutomatic -and -not [bool]$d.checkpointMetrics.deepCalibrationApplicable) 'CP99 authority boundaries drifted.'
 Assert-True ([string]$d.primaryStudy.id -eq 'tl2-itc19-exact-edge-progression-screening' -and [int]$d.primaryStudy.variantCount -eq 724) 'CP99 primary-study binding mismatch.'
 $self=@($d.stages|Where-Object id -eq 'runner-self-tests'); Assert-True ($self.Count -eq 1 -and [int]$self[0].metrics.selfTestCount -eq 63) 'CP99 must expect 63 ScenarioRunner self-tests.'
 Assert-True (@($d.documentation).Count -eq 30 -and @($d.documentation|Where-Object {$_ -eq 'docs/Star_Cluster_Game_Concept_v0.7a.docx'}).Count -eq 1 -and @($d.documentation|Where-Object {$_ -eq 'docs/validation/evidence/checkpoint-98/CHECKPOINT_98_SHA256SUMS.txt'}).Count -eq 1) 'CP99 documentation declaration drifted.'
}

Write-Host '       Validating native-accepted CP98 provenance and frozen repository surface...'
$acceptedManifestRel='docs/validation/evidence/checkpoint-98/CHECKPOINT_98_SHA256SUMS.txt'; $acceptedManifest=Read-Manifest $acceptedManifestRel
Assert-True ($acceptedManifest.EntryCount -eq 1905 -and $acceptedManifest.PhysicalLineCount -eq 1905) 'Embedded accepted CP98 manifest must contain 1,905 entries.'
Assert-True ((Hash-Rel $acceptedManifestRel) -eq 'f6a1b8c04bc5b237d3e80d02ee2874bb5290c5369ff367459b43c2e21b2bc126') 'Embedded accepted CP98 manifest SHA-256 mismatch.'
$acc=Read-Json 'docs/validation/evidence/checkpoint-98/checkpoint-98-native-acceptance-summary.json'
Assert-True ([string]$acc.checkpointId -eq '98' -and [string]$acc.status -eq 'Success' -and [string]$acc.checkpointDefinitionSha256 -eq 'c57f4912ccf2fa79b3085f64ec1887c599946c02712fcb48173ba9580f8ab2c5' -and [string]$acc.checkpointManifestSha256 -eq 'f6a1b8c04bc5b237d3e80d02ee2874bb5290c5369ff367459b43c2e21b2bc126') 'CP98 native acceptance provenance mismatch.'
Assert-True ([int]$acc.tests.passed -eq 876 -and [int]$acc.aggregates.runnerStagesPassed -eq 19 -and [int]$acc.aggregates.selfTests -eq 62 -and [int]$acc.aggregates.failedGates -eq 0 -and [long]$acc.aggregates.trials -eq 242436) 'CP98 accepted metrics mismatch.'
$ev=Read-Json 'docs/validation/evidence/checkpoint-98/cp98-cross-progression-evidence.json'
Assert-True ([string]$ev.nativeResultsZipSha256 -eq '1ee459063d8bd24a0228c8410c6912aeaabe3daa21b888b1dd7b68c348de4014' -and [string]$ev.substantiveStudy.summarySha256 -eq '37be9c45ba62f020a2ccdcdc9d0988288a76ff90b6deace3763b3ffec899eea5') 'CP98 embedded evidence hashes mismatch.'
$mutable=@{}
foreach($r in @('CHAT_README.md','README.md','docs/Prototype_TODO.md','docs/README.md','docs/Star_Cluster_Game_Concept_v0.6z.docx','docs/design/README.md','docs/design/player_technology/README.md','docs/design/player_technology/StarCluster_Technology_Architecture_Matrix_v1.xlsx','docs/design/player_technology/Technology_Architecture_Matrix_v1.md','docs/archive/player_technology/pre-cp165-active/component_installation_space_catalog_v1.json','docs/archive/player_technology/pre-cp165-active/technology_architecture_matrix_v1.json','docs/design/testing/README.md','docs/design/testing/Checkpoint_98_Validation_Tiers.md','docs/design/testing/Technology_Integration_Permutation_Suite_Architecture_v0_13.md','docs/design/testing/checkpoint_98_validation_suite_policy_v0_1.json','docs/design/testing/technology_integration_permutation_suite_v0_13.json','docs/development/Simulation_Development_Guidelines.md','docs/validation/Checkpoint_98_Cross_Progression_Adaptive_Engage_Integration_Foundation.md','src/StarCluster.ScenarioRunner/CrossTlIntegration/CrossTlBuildPermutationRunner.cs','src/StarCluster.ScenarioRunner/ScenarioRunnerSelfTests.cs','src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs')){ $mutable[$r]=$true }
$frozen=0
foreach($entry in $acceptedManifest.Entries.GetEnumerator()){ $r=[string]$entry.Key; if($mutable.ContainsKey($r)){ continue }; Assert-True (Test-Path -LiteralPath (RelPath $r) -PathType Leaf) "Frozen CP98 file '$r' is missing."; Assert-True ((Hash-Rel $r) -eq [string]$entry.Value) "Frozen CP98 file '$r' changed unexpectedly."; $frozen++ }
Assert-True ($frozen -eq 1884) "Expected 1,884 frozen CP98 files; observed $frozen."
$archiveMap=@{
 'docs/Star_Cluster_Game_Concept_v0.6z.docx'='docs/archive/concepts/Star_Cluster_Game_Concept_v0.6z.docx';
 'docs/design/testing/Checkpoint_98_Validation_Tiers.md'='docs/archive/testing/Checkpoint_98_Validation_Tiers.md';
 'docs/design/testing/Technology_Integration_Permutation_Suite_Architecture_v0_13.md'='docs/archive/testing/Technology_Integration_Permutation_Suite_Architecture_v0_13.md';
 'docs/design/testing/checkpoint_98_validation_suite_policy_v0_1.json'='docs/archive/testing/checkpoint_98_validation_suite_policy_v0_1.json';
 'docs/design/testing/technology_integration_permutation_suite_v0_13.json'='docs/archive/testing/technology_integration_permutation_suite_v0_13.json';
 'docs/validation/Checkpoint_98_Cross_Progression_Adaptive_Engage_Integration_Foundation.md'='docs/validation/archive/Checkpoint_98_Cross_Progression_Adaptive_Engage_Integration_Foundation.md'
}
foreach($old in $archiveMap.Keys){ $new=[string]$archiveMap[$old]; Assert-True (Test-Path -LiteralPath (RelPath $new) -PathType Leaf) "Archived CP98 authority '$new' is missing."; Assert-True ((Hash-Rel $new) -eq [string]$acceptedManifest.Entries[$old]) "Archived CP98 authority '$new' is not byte-identical to accepted '$old'." }

Write-Host '       Reconstructing mandatory-Sensor envelope, exact progression lattice, and strata independently...'
$foundation=Read-Json 'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/cross-tl-build-permutation-foundation-v0_8.json'
$foundation98=Read-Json 'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/cross-tl-build-permutation-foundation-v0_7.json'
$legacyAxes=@{}; foreach($axis in @($foundation98.axes)){ $legacyAxes[[string]$axis.id]=$axis }
$legacyTransitions=@($foundation98.progressionLattice.transitions)
Assert-True ($legacyTransitions.Count -eq 12) 'Frozen CP98 v0.7 progression lattice must retain 12 transitions.'
foreach($t in $legacyTransitions){
 $id=[string]$t.id
 Assert-True (-not ($t.PSObject.Properties.Name -contains 'expectedAdvancedComponentDelta')) "Frozen CP98 transition '$id' unexpectedly gained the CP99 delta declaration field; accepted CP98 evidence must remain byte-frozen."
 $axis=$legacyAxes[[string]$t.axisId]; Assert-True ($null -ne $axis) "Frozen CP98 transition '$id' references unknown axis '$($t.axisId)'."
 $from=@($axis.options|Where-Object id -eq ([string]$t.fromOptionId)); $to=@($axis.options|Where-Object id -eq ([string]$t.toOptionId))
 Assert-True ($from.Count -eq 1 -and $to.Count -eq 1) "Frozen CP98 transition '$id' option binding is not unique."
 $legacyDelta=(Get-OptionAdvancedContribution ([string]$t.axisId) $to[0])-(Get-OptionAdvancedContribution ([string]$t.axisId) $from[0])
 Assert-True ($legacyDelta -in @(1,2)) "Frozen CP98 transition '$id' must infer advanced-component delta 1 or 2; inferred $legacyDelta."
 if($id -like '*-double-*'){ Assert-True ($legacyDelta -eq 2) "Frozen CP98 double-installation transition '$id' must infer advanced-component delta 2." } else { Assert-True ($legacyDelta -eq 1) "Frozen CP98 single-installation transition '$id' must infer advanced-component delta 1." }
}
Assert-True ([string]$foundation.schemaVersion -eq 'star-cluster-cross-tl-build-permutation-v6' -and [string]$foundation.id -eq 'cross-tl-build-permutation-foundation-v0_8' -and [string]$foundation.generatedStudyId -eq 'tl2-itc19-exact-edge-progression-screening' -and [long]$foundation.masterSeed -eq 990100 -and [int]$foundation.trialsPerVariant -eq 250) 'CP99 foundation identity/seed/trials mismatch.'
Assert-True (($foundation.axes|ConvertTo-Json -Depth 100 -Compress) -ceq ($foundation98.axes|ConvertTo-Json -Depth 100 -Compress) -and ($foundation.fixedShell|ConvertTo-Json -Depth 50 -Compress) -ceq ($foundation98.fixedShell|ConvertTo-Json -Depth 50 -Compress) -and [int]$foundation.fixedShellSpace -eq [int]$foundation98.fixedShellSpace -and [int]$foundation.totalInstallationSpace -eq [int]$foundation98.totalInstallationSpace) 'CP99 must preserve CP98 construction axes, values, fixed shell, and 35-Space budget exactly.'
foreach($name in @('minimumMainWeaponCount','minimumReactorCount','additionalMainWeaponsOptional','additionalReactorsOptional','duplicationMustBeExplicit','redundantEwInstallationsAllowed','ecmSameTypeRatingsAdditive','eccmSameTypeRatingsAdditive','ewDuplicateResolution','powerSufficiencyIsConstructionLegalityFilter')){ Assert-True (($foundation.constructionGuardrails.$name|ConvertTo-Json -Compress) -ceq ($foundation98.constructionGuardrails.$name|ConvertTo-Json -Compress)) "CP99 construction guardrail '$name' drifted from CP98." }
Assert-True ([int]$foundation.constructionGuardrails.minimumSensorCount -eq 1 -and [bool]$foundation.constructionGuardrails.sensorlessDiagnosticsAllowedOutsideLegalPopulation) 'CP99 must add mandatory Sensor normal-construction guardrail while preserving explicit sensorless diagnostics.'
Assert-True ([int]$foundation.expectedRawCombinationCount -eq 82944 -and [int]$foundation.expectedLegalBuildCount -eq 11776 -and [int]$foundation.expectedExactFillBuildCount -eq 2944 -and [int]$foundation.expectedNearFillBuildCount -eq 6656 -and [int]$foundation.expectedUnderfilledBuildCount -eq 2176 -and [int]$foundation.expectedLogicalPairingCount -eq 362 -and [int]$foundation.expectedGeneratedVariantCount -eq 724) 'CP99 declared envelope/sample counts mismatch.'
Assert-True ([bool]$foundation.exactEdgePairingSelection.enabled -and [int]$foundation.exactEdgePairingSelection.representativesPerStratum -eq 2 -and [int]$foundation.exactEdgePairingSelection.expectedStratumCount -eq 181 -and [int]$foundation.exactEdgePairingSelection.expectedLogicalPairingCount -eq 362 -and -not [bool]$foundation.stratifiedPairingSelection.enabled) 'CP99 exact-edge selection isolation mismatch.'
Assert-True (-not [bool]$foundation.stratifiedPairingSelection.enabled -and [int]$foundation.stratifiedPairingSelection.nearDistanceMaximum -eq 2 -and [int]$foundation.stratifiedPairingSelection.equalLowAdvancedMaximum -eq 3 -and [int]$foundation.stratifiedPairingSelection.nearFillMinimumUsedSpace -eq 32 -and [int]$foundation.stratifiedPairingSelection.informationControlNearDistanceMaximum -eq 2) 'CP99 exact-edge mode must retain explicit CP98 classification thresholds even while broad population sampling is disabled.'
Assert-Sequence @($foundation.exactEdgePairingSelection.strata) @('transition','weaponFamily','compositionClass','spaceUtilizationClass') 'CP99 exact-edge stratum definition drifted.'
$axes=@($foundation.axes); Assert-True ($axes.Count -eq 9) 'CP99 foundation must retain nine construction axes.'
$axisIndex=@{}; for($i=0;$i -lt $axes.Count;$i++){ $axisIndex[[string]$axes[$i].id]=$i }
$transitions=@($foundation.progressionLattice.transitions); Assert-True ([bool]$foundation.progressionLattice.enabled -and [bool]$foundation.progressionLattice.requireSameInstallationSpace -and $transitions.Count -eq 12 -and [int]$foundation.progressionLattice.expectedTotalLegalEdgeCount -eq 37184) 'CP99 progression-lattice declaration mismatch.'
$edgeCount=@{}; $exactEdge=@{}; $strata=@{}
foreach($t in $transitions){ $id=[string]$t.id; $edgeCount[$id]=0; $exactEdge[$id]=0; Assert-True ([int]$t.expectedAdvancedComponentDelta -in @(1,2)) "Transition '$id' must declare advanced-component delta 1 or 2."; $axis=$axes[$axisIndex[[string]$t.axisId]]; $from=@($axis.options|Where-Object id -eq ([string]$t.fromOptionId)); $to=@($axis.options|Where-Object id -eq ([string]$t.toOptionId)); Assert-True ($from.Count -eq 1 -and $to.Count -eq 1 -and [int]$from[0].space -eq [int]$to[0].space) "Transition '$id' must bind existing same-Space options." }
$raw=1; foreach($a in $axes){ $raw *= @($a.options).Count }
$legal=0; $exact=0; $near=0; $under=0
for($n=0;$n -lt $raw;$n++){
 $x=$n; $used=[int]$foundation.fixedShellSpace; $selectedId=@{}; $selectedObj=@{}
 for($i=0;$i -lt $axes.Count;$i++){ $opts=@($axes[$i].options); $idx=$x % $opts.Count; $x=[math]::Floor($x / $opts.Count); $o=$opts[$idx]; $aid=[string]$axes[$i].id; $selectedId[$aid]=[string]$o.id; $selectedObj[$aid]=$o; $used += [int]$o.space }
 if($used -gt [int]$foundation.totalInstallationSpace){ continue }
 $weaponCount=[int]$selectedObj['weapon'].mainWeaponCount; $reactorCount=[int]$selectedObj['reactor'].reactorCount; $sensorInstalled=$true; if($selectedObj['sensor'].PSObject.Properties.Name -contains 'installed'){$sensorInstalled=[bool]$selectedObj['sensor'].installed}
 if($weaponCount -lt 1 -or $reactorCount -lt 1 -or -not $sensorInstalled){ continue }
 $nearFillMinimum=[int]$foundation.stratifiedPairingSelection.nearFillMinimumUsedSpace
 $legal++; $spaceClass='underfilled'; if($used -eq [int]$foundation.totalInstallationSpace){$exact++;$spaceClass='exact_fill'} elseif($used -ge $nearFillMinimum){$near++;$spaceClass='near_fill'} else {$under++}
 $ewRedundancy=@($selectedObj['ecm'].ewRatings).Count -gt 1 -or @($selectedObj['eccm'].ewRatings).Count -gt 1; $dup=$weaponCount -gt 1 -or $reactorCount -gt 1
 $composition='single-no-ew-redundancy'; if($dup -and $ewRedundancy){$composition='combined-duplication'} elseif($dup){$composition='weapon-reactor-duplication'} elseif($ewRedundancy){$composition='ew-redundancy'}
 foreach($t in $transitions){
  $tid=[string]$t.id; $axisId=[string]$t.axisId; if($selectedId[$axisId] -ne [string]$t.fromOptionId){continue}
  $before=Count-AdvancedComponents $selectedObj; $oldObj=$selectedObj[$axisId]; $axis=$axes[$axisIndex[$axisId]]; $selectedObj[$axisId]=Get-OptionById $axis ([string]$t.toOptionId); $after=Count-AdvancedComponents $selectedObj; $selectedObj[$axisId]=$oldObj
  Assert-True (($after-$before) -eq [int]$t.expectedAdvancedComponentDelta) "Independent advanced-component delta mismatch for '$tid'."
  $edgeCount[$tid]++; if($used -eq 35){$exactEdge[$tid]++}
  $key=$tid+'|'+[string]$selectedObj['weapon'].family+'|'+$composition+'|'+$spaceClass; if(-not $strata.ContainsKey($key)){$strata[$key]=0}; $strata[$key]++
 }
}
Assert-True ($raw -eq 82944 -and $legal -eq 11776 -and $exact -eq 2944 -and $near -eq 6656 -and $under -eq 2176) "Independent CP99 envelope observed raw/legal/exact/near/under $raw/$legal/$exact/$near/$under."
$totalEdges=0; foreach($t in $transitions){ $id=[string]$t.id; Assert-True ($edgeCount[$id] -eq [int]$t.expectedLegalEdgeCount -and $exactEdge[$id] -eq [int]$t.expectedExactFillEdgeCount) "Independent progression count mismatch for '$id': $($edgeCount[$id])/$($exactEdge[$id])."; $totalEdges += $edgeCount[$id] }
Assert-True ($totalEdges -eq 37184) "Independent CP99 progression lattice observed $totalEdges edges; expected 37,184."
$minStratum=($strata.Values|Measure-Object -Minimum).Minimum; Assert-True ($strata.Count -eq 181 -and [int]$minStratum -ge 2 -and $strata.Count*[int]$foundation.exactEdgePairingSelection.representativesPerStratum -eq 362) "Independent exact-edge strata observed $($strata.Count) strata with minimum size $minStratum."
Assert-True ([int]$foundation.stratifiedPairingSelection.nearDistanceMaximum -ge 2) 'CP99 exact-edge deltas 1/2 must remain classified as near by shared progression metadata.'
$geoms=@($foundation.geometries); Assert-True ($geoms.Count -eq 2 -and @($geoms|Where-Object movementMode -eq 'EngageAdaptive').Count -eq 2 -and @($geoms|Where-Object initialRangeHexes -eq 10).Count -eq 2 -and @($geoms|Where-Object movementOrder -eq 'SideAFirst').Count -eq 1 -and @($geoms|Where-Object movementOrder -eq 'SideBFirst').Count -eq 1) 'CP99 Adaptive Encounter geometry drifted.'

Write-Host '       Validating actual-consumer, exact-edge isolation, telemetry, reports, and compiler-risk bindings...'
$runner=Read-Text 'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs'; $cross=Read-Text 'src/StarCluster.ScenarioRunner/CrossTlIntegration/CrossTlBuildPermutationRunner.cs'; $selfTests=Read-Text 'src/StarCluster.ScenarioRunner/ScenarioRunnerSelfTests.cs'
foreach($needle in @('CrossTlExactEdgeProgressionScreeningStudyId','RequiredCrossTlExactEdgeProgressionScreeningVariantCount = 724','ValidateCrossTlExactEdgeProgressionCoverage(','WriteCrossTlExactEdgeProgressionReview(','cp99-mandatory-sensor-runtime-binding','cp99-twelve-transition-classes-carried','cross-tl-cp99-exact-edge-review.csv','cross-tl-cp99-exact-edge-mover-neutral-review.csv','IsAdaptiveEncounterStudy(studyId)','IsSingleSourcePolicyTelemetryStudy(study.Id)')){ Require-Contains $runner $needle "CP99 integrated consumer is missing binding '$needle'." }
foreach($needle in @('SchemaVersionV6','ExactEdgePairingSelection','SelectExactProgressionEdgePairings(','minimumSensorCount','ExpectedAdvancedComponentDelta','HasExplicitExpectedAdvancedComponentDelta','ResolveLegacyExpectedAdvancedComponentDelta(','ResolveExpectedAdvancedComponentDelta(','int expectedAdvancedComponentDelta = ResolveExpectedAdvancedComponentDelta(transition, from, to);','transition.ResolveLegacyExpectedAdvancedComponentDelta(inferred);','AdvancedComponentContribution(','selection?.NearFillMinimumUsedSpace ?? Math.Max(0, totalSpace - 3)','selection?.NearDistanceMaximum ?? 2','WriteExactEdgePairingPlan(','exact-edge-sample-count','exact-edge-stratum-coverage','exact-edge-one-axis-and-space-preserved','!exactEdgeSelection')){ Require-Contains $cross $needle "CP99 generator is missing binding '$needle'." }
Require-Contains $selfTests 'TestCp99MandatorySensorCombatCore' 'CP99 mandatory-Sensor ScenarioRunner self-test is missing.'
Require-Contains $selfTests 'minimumSensorCount: 1' 'CP99 sensor-core self-test must exercise the explicit Sensor minimum.'
# Exact-edge v0.8 must bypass the broad population-cell construction/output path while retaining it for older matched-readiness studies.
Require-Contains $cross 'IsMatchedReadinessSchema(study.SchemaVersion) && !exactEdgeSelection' 'CP99 generator must bypass broad population-cell construction for exact-edge selection.'
Require-Contains $cross 'if (IsMatchedReadinessSchema(study.SchemaVersion) && !exactEdgeSelection)' 'CP99 generator must bypass broad population coverage writers for exact-edge selection.'
# Known compiler-class preflight across all CP99-mutated private methods.
foreach($method in @(
 @('private static CrossTlEnumerationResult ValidateAndEnumerate(','ValidateAndEnumerate'),
 @('private static bool MeetsMinimumCombatCore(','MeetsMinimumCombatCore'),
 @('private static CrossTlResolvedBuild ResolveBuild(','ResolveBuild'),
 @('private static IReadOnlyList<CrossTlLogicalPairing> ExpandPairings(','ExpandPairings'),
 @('private static IReadOnlyList<CrossTlLogicalPairing> SelectExactProgressionEdgePairings(','SelectExactProgressionEdgePairings'),
 @('private static int ResolveExpectedAdvancedComponentDelta(','ResolveExpectedAdvancedComponentDelta'),
 @('private static int AdvancedComponentContribution(','AdvancedComponentContribution'),
 @('private static IReadOnlyList<CrossTlProgressionEdge> BuildProgressionLattice(','BuildProgressionLattice'),
 @('private static IReadOnlyList<CrossTlFoundationGate> BuildFoundationGates(','BuildFoundationGates'),
 @('private static void WriteExactEdgePairingPlan(','WriteExactEdgePairingPlan'),
 @('private static void ValidateCrossTlExactEdgeProgressionCoverage(','ValidateCrossTlExactEdgeProgressionCoverage'),
 @('private static void WriteCrossTlExactEdgeProgressionReview(','WriteCrossTlExactEdgeProgressionReview')
)){ $text=$cross; if($method[1] -in @('ValidateCrossTlExactEdgeProgressionCoverage','WriteCrossTlExactEdgeProgressionReview')){$text=$runner}; Assert-NoNestedLocalShadowing $text $method[0] $method[1] }
Require-NotContains $runner 'FinalTrack != TacticalTrackQuality' 'Runner contains a known cross-enum FinalTrack/TacticalTrackQuality comparison.'
Require-NotContains $runner 'FinalTrack == TacticalTrackQuality' 'Runner contains a known cross-enum FinalTrack/TacticalTrackQuality comparison.'
Assert-True (-not [regex]::IsMatch($runner,'TryGetValue\([^\r\n]+out\s+SensorEwFoundationProfile\s+[A-Za-z_]')) 'Runner reintroduced a non-nullable SensorEwFoundationProfile TryGetValue out reference.'
Assert-True (-not [regex]::IsMatch($cross,'TryGetValue\([^\r\n]+out\s+CrossTlTechnologyOptionDocument\s+[A-Za-z_]')) 'Cross-TL generator reintroduced a non-nullable CrossTlTechnologyOptionDocument TryGetValue out reference.'
Require-NotContains $cross 'CrossTlExactEdgePairingSelectionDocument exactSelection = study.ExactEdgePairingSelection;' 'CP99 gate construction must not assign nullable ExactEdgePairingSelection directly to a non-nullable local.'

Write-Host '       Validating current gameplay/technology/testing authorities...'
$designReadme=Read-Text 'docs/design/README.md'; Require-Contains $designReadme 'Technology_Integration_Permutation_Suite_Architecture_v0_14.md' 'Design README must point to standing permutation architecture v0.14.'
$playerTechReadme=Read-Text 'docs/design/player_technology/README.md'; Require-Contains $playerTechReadme 'historical optional-active-sensor construction language is superseded' 'Player-technology README must distinguish the retained v0.9 footprint seed from current mandatory-Sensor construction legality.'
$matrix=Read-Json 'docs/archive/player_technology/pre-cp165-active/technology_architecture_matrix_v1.json'; Assert-True ([string]$matrix.authority.concept -eq 'docs/Star_Cluster_Game_Concept_v0.7a.docx' -and [int]$matrix.integrationArchitecture.currentLegalBuildEnvelope -eq 11776 -and [int]$matrix.integrationArchitecture.constructionGuardrails.minimumSensorCount -eq 1 -and [string]$matrix.integrationCoverage.standingPermutationSuite -eq 'v0.14' -and [int]$matrix.integrationCoverage.progressionLatticeLegalEdges -eq 37184) 'Technology Matrix CP99 construction/integration authority mismatch.'
$catalog=Read-Json 'docs/archive/player_technology/pre-cp165-active/component_installation_space_catalog_v1.json'; Assert-True ([int]$catalog.globalRules.minimumMainWeaponCount -eq 1 -and [int]$catalog.globalRules.minimumReactorCount -eq 1 -and [int]$catalog.globalRules.minimumSensorCount -eq 1 -and [bool]$catalog.globalRules.sensorlessDiagnosticsAllowedOutsideNormalCombatConstruction -and [string]$catalog.authority.tl1ConstructionSeedSemantics -like '*current ordinary-combat construction legality*require an installed Sensor*') 'Component Installation Space catalog must require Weapon/Reactor/Sensor normal combat core and distinguish the retained v0.9 footprint seed from current legality.'
$sensorComponent=@($catalog.components|Where-Object id -eq 'active_sensor'); Assert-True ($sensorComponent.Count -eq 1 -and [int]$sensorComponent[0].minimumCount -eq 1) 'Component catalog Sensor suite must have minimum count 1.'
$suite=Read-Json 'docs/design/testing/technology_integration_permutation_suite_v0_14.json'; Assert-True ([string]$suite.id -eq 'technology-integration-permutation-suite-v0_14' -and [int]$suite.currentCoverage.legalBuildEnvelope.legalBuilds -eq 11776 -and [int]$suite.currentCoverage.progressionLattice.singleAxisLegalEdges -eq 37184 -and [int]$suite.currentCoverage.pairingSample.exactEdgeStrata -eq 181 -and [int]$suite.currentCoverage.currentStudy.variantCount -eq 724) 'Standing permutation suite v0.14 mismatch.'
$policy=Read-Json 'docs/design/testing/checkpoint_99_validation_suite_policy_v0_1.json'; Assert-True ([string]$policy.checkpoint -eq '99' -and [int]$policy.constructionCore.minimumSensorCount -eq 1 -and [long]$policy.study.totalTrialExecutionsAtDefault -eq 184160 -and [int]$policy.crossProgression.progressionLegalEdges -eq 37184 -and -not [bool]$policy.authorityBoundary.initiativeRuleChange -and -not [bool]$policy.deepCalibration.applicable) 'CP99 validation policy mismatch.'
Assert-ExactFileSet 'docs/design/testing' @('README.md','Technology_Integration_Permutation_Suite_Architecture_v0_14.md','technology_integration_permutation_suite_v0_14.json','Checkpoint_99_Validation_Tiers.md','checkpoint_99_validation_suite_policy_v0_1.json')
$activeConcept=@(Get-ChildItem -LiteralPath (RelPath 'docs') -File -Filter 'Star_Cluster_Game_Concept_v*.docx'); Assert-True ($activeConcept.Count -eq 1 -and $activeConcept[0].Name -eq 'Star_Cluster_Game_Concept_v0.7a.docx') 'Exactly one active Game Concept must remain and it must be v0.7a.'
$activeValidation=@(Get-ChildItem -LiteralPath (RelPath 'docs/validation') -File -Filter 'Checkpoint_*.md'); Assert-True ($activeValidation.Count -eq 1 -and $activeValidation[0].Name -eq 'Checkpoint_99_Mandatory_Sensor_And_Exact_Edge_Progression_Screening.md') 'Exactly one active CP99 validation runbook must remain.'
$conceptArchiveHash=[string]$acceptedManifest.Entries['docs/Star_Cluster_Game_Concept_v0.6z.docx']; Assert-True ((Hash-Rel 'docs/archive/concepts/Star_Cluster_Game_Concept_v0.6z.docx') -eq $conceptArchiveHash) 'Archived CP98 Game Concept v0.6z changed.'
$runbook=Read-Text 'docs/validation/Checkpoint_99_Mandatory_Sensor_And_Exact_Edge_Progression_Screening.md'; foreach($needle in @('11,776','37,184','181 populated strata','362 logical','724 variants','181,000','184,160','876 xUnit','63 ScenarioRunner','Sensor')){ Require-Contains $runbook $needle "CP99 runbook is missing '$needle'." }

Write-Host '       Validating root manifest...'
$rootTxt=@(Get-ChildItem -LiteralPath $repositoryRoot -File -Filter '*.txt'); Assert-True ($rootTxt.Count -eq 1 -and $rootTxt[0].Name -eq 'CHECKPOINT_99_SHA256SUMS.txt') 'Repository root must contain only CHECKPOINT_99_SHA256SUMS.txt as .txt.'
$manifest=Read-Manifest 'CHECKPOINT_99_SHA256SUMS.txt'; Assert-True ($manifest.EntryCount -eq 1920 -and $manifest.PhysicalLineCount -eq 1920) 'CP99 manifest entry count mismatch.'; Assert-True (-not $manifest.Entries.ContainsKey('CHECKPOINT_99_SHA256SUMS.txt')) 'CP99 manifest must not contain itself.'
foreach($entry in $manifest.Entries.GetEnumerator()){ Assert-True (Test-Path -LiteralPath (RelPath ([string]$entry.Key)) -PathType Leaf) "CP99 manifest entry '$($entry.Key)' is missing."; Assert-True ((Hash-Rel ([string]$entry.Key)) -eq [string]$entry.Value) "CP99 manifest hash mismatch for '$($entry.Key)'." }
Write-Host "Checkpoint 99 repository contracts passed ($frozen CP98 files frozen; independent 11,776-build / 37,184-edge / 181-stratum reconstruction; 362 exact-edge pairs / 724 Adaptive Engage variants locked)."
