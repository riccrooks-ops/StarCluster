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
 foreach($m in $matches){
  $name=$m.Groups['name'].Value; $indent=$m.Groups['indent'].Value.Replace("`t",'    ').Length
  if(-not $seen.ContainsKey($name)){ $seen[$name]=New-Object System.Collections.ArrayList }
  $null = $seen[$name].Add($indent)
 }
 foreach($name in $seen.Keys){
  $depths=@($seen[$name]|Sort-Object -Unique)
  Assert-True ($depths.Count -le 1) "$MessagePrefix local '$name' is redeclared at nested indentation depths ($($depths -join ', ')); this can trigger C# CS0136 shadowing."
 }
}

Write-Host '       Validating native dependencies, wrapper interface, and checkpoint definitions...'
$normalRel='tools/calibration/checkpoints/checkpoint-98.json'; $deepRel='tools/calibration/checkpoints/checkpoint-98-deep-calibration.json'
$guarded=@('tools/checkpoints/Test-NativeAcceptanceDependencies.ps1','tools/checkpoints/checkpoint-98/apply_checkpoint_98.ps1','tools/checkpoints/checkpoint-98/test_checkpoint_98_contract.ps1','tools/calibration/run_calibration_checkpoint.ps1')
& (RelPath 'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1') -RepositoryRoot $repositoryRoot -PowerShellPaths $guarded -CheckpointDefinitionPaths @($normalRel,$deepRel)
$apply=Read-Text 'tools/checkpoints/checkpoint-98/apply_checkpoint_98.ps1'
$typeCompatibilityCall='Assert-Cp98PowerShell51TypeCompatibility -Paths @($MyInvocation.MyCommand.Path, $contract)'
Require-Contains $apply 'function Assert-Cp98PowerShell51TypeCompatibility' 'CP98 wrapper must define the Windows PowerShell 5.1 type-token compatibility precheck.'
Require-Contains $apply $typeCompatibilityCall 'CP98 wrapper must invoke the Windows PowerShell 5.1 type-token compatibility precheck before repository contracts.'
Assert-True ($apply.IndexOf($typeCompatibilityCall,[StringComparison]::Ordinal) -lt $apply.IndexOf('& $guard -RepositoryRoot',[StringComparison]::Ordinal)) 'CP98 PowerShell 5.1 type-token compatibility precheck must run before the shared dependency guard.'
Require-Contains $apply 'unreviewed or unsupported type token' 'CP98 wrapper must reject unreviewed PowerShell type tokens explicitly.'
Require-Contains $apply '& $harness -CheckpointDefinition $definition -Trials $Trials -Jobs $Jobs -RepositoryOnly:$RepositoryOnly -NoClean:$NoClean' 'CP98 wrapper must use the proven direct named-parameter harness invocation.'
Assert-True (-not [regex]::IsMatch($apply,'&\s+\$harness\s+@[A-Za-z_]',[System.Text.RegularExpressions.RegexOptions]::IgnoreCase)) 'CP98 wrapper must not splat harness arguments.'
$stageIds=@('deterministic','tl1-phase-a','tl1-phase-b','tl1-installation-space-envelope','tl1-sensor-ew-foundation','cross-tl-build-permutation-preflight','cross-tl-build-permutation-generation','cross-tl-generated-study-preflight','cross-tl-generated-study-smoke','adaptive-engage-preflight','adaptive-engage-smoke','cross-tl-cp98-progression-preflight','cross-tl-cp98-progression-generation','cross-tl-cp98-generated-study-preflight','cross-tl-cp98-generated-study-smoke','cross-tl-cp98-progression-study','auxiliary-resource-endurance','checkpoint-53-resource-semantics-lock','runner-self-tests')
foreach($d in @((Read-Json $normalRel),(Read-Json $deepRel))){
 Assert-True ([string]$d.checkpointId -eq '98' -and [string]$d.manifestFile -eq 'CHECKPOINT_98_SHA256SUMS.txt') 'CP98 definition/manifest binding mismatch.'
 Assert-True ([int]$d.defaultTrials -eq 250 -and [int]$d.defaultJobs -eq 24) 'CP98 default trials/jobs mismatch.'
 Assert-True (@($d.stages).Count -eq 19 -and [int]$d.checkpointMetrics.stageCount -eq 19) 'CP98 must configure 19 runner stages.'
 Assert-Sequence @($d.stages|ForEach-Object{[string]$_.id}) $stageIds 'CP98 stage order drifted.'
 Assert-Sequence @($d.nativeDependencyPrecheck.powerShellPaths) $guarded 'CP98 guarded PowerShell path list drifted.'
 Assert-Sequence @($d.nativeDependencyPrecheck.checkpointDefinitionPaths) @($normalRel,$deepRel) 'CP98 guarded definition list drifted.'
 Assert-True ([long]$d.checkpointMetrics.totalTrialExecutionsAtDefault -eq 242436 -and [long]$d.checkpointMetrics.trialsAtDefault -eq 240000 -and [long]$d.checkpointMetrics.smokeTrialsAtDefault -eq 2436) 'CP98 trial accounting mismatch.'
 Assert-True ([int]$d.checkpointMetrics.legalBuildCount -eq 22592 -and [int]$d.checkpointMetrics.progressionLatticeTransitions -eq 12 -and [int]$d.checkpointMetrics.progressionLatticeLegalEdges -eq 65648 -and [int]$d.checkpointMetrics.adaptiveGeneratedVariantCount -eq 960) 'CP98 cross-progression metrics mismatch.'
 Assert-True (-not [bool]$d.checkpointMetrics.initiativeRuleChanged -and -not [bool]$d.checkpointMetrics.newTl3Values -and -not [bool]$d.checkpointMetrics.technologyPromotionAutomatic -and -not [bool]$d.checkpointMetrics.deepCalibrationApplicable) 'CP98 authority boundaries drifted.'
 Assert-True ([string]$d.primaryStudy.id -eq 'tl2-itc18-cross-tl-adaptive-engage-progression-screening' -and [int]$d.primaryStudy.variantCount -eq 960) 'CP98 primary-study binding mismatch.'
 $self=@($d.stages|Where-Object id -eq 'runner-self-tests'); Assert-True ($self.Count -eq 1 -and [int]$self[0].metrics.selfTestCount -eq 62) 'CP98 must expect 62 ScenarioRunner self-tests.'
}

Write-Host '       Validating native-accepted CP97 provenance and frozen repository surface...'
$acceptedManifestRel='docs/validation/evidence/checkpoint-97/CHECKPOINT_97_SHA256SUMS.txt'; $acceptedManifest=Read-Manifest $acceptedManifestRel
Assert-True ($acceptedManifest.EntryCount -eq 1890 -and $acceptedManifest.PhysicalLineCount -eq 1890) 'Embedded accepted CP97 manifest must contain 1,890 entries.'
Assert-True ((Hash-Rel $acceptedManifestRel) -eq '888e8c85f1fa3db5b95abc435d1bc51103ef7f7b99d5f79be5c8492bd6269ad4') 'Embedded accepted CP97 manifest SHA-256 mismatch.'
$acc=Read-Json 'docs/validation/evidence/checkpoint-97/checkpoint-97-native-acceptance-summary.json'
Assert-True ([string]$acc.checkpointId -eq '97' -and [string]$acc.status -eq 'Success' -and [string]$acc.checkpointDefinitionSha256 -eq 'd261eb01efde0919bb55f36e9fa58a5cf8885845af89310c12a92ebba0689055' -and [string]$acc.checkpointManifestSha256 -eq '888e8c85f1fa3db5b95abc435d1bc51103ef7f7b99d5f79be5c8492bd6269ad4') 'CP97 native acceptance provenance mismatch.'
Assert-True ([int]$acc.tests.passed -eq 875 -and [int]$acc.aggregates.runnerStagesPassed -eq 15 -and [int]$acc.aggregates.selfTests -eq 62 -and [int]$acc.aggregates.failedGates -eq 0) 'CP97 accepted metrics mismatch.'
$ev=Read-Json 'docs/validation/evidence/checkpoint-97/cp97-adaptive-engage-evidence.json'
Assert-True ([string]$ev.substantiveStudy.summarySha256 -eq '24b2d6745dc71995b12a5cc449da3a8dd4239d08ec9bfbcac04a2e38af7a6bbc' -and [string]$ev.nativeResultsZipSha256 -eq '4f73d0af4fb297d51af986412b0e5e058df774948ddd56f1ed97d742e8cc00c3') 'CP97 embedded evidence hashes mismatch.'
$mutable=@{}
foreach($r in @('CHECKPOINT_97_SHA256SUMS.txt','CHAT_README.md','README.md','docs/README.md','docs/Prototype_TODO.md','docs/design/README.md','docs/design/testing/README.md','docs/development/Simulation_Development_Guidelines.md','docs/design/player_technology/Technology_Architecture_Matrix_v1.md','docs/archive/player_technology/pre-cp165-active/technology_architecture_matrix_v1.json','docs/design/ai/AI_Doctrine_Registry_Architecture_v0_6.md','docs/design/ai/adaptive_engage_policy_v0_1.json','docs/design/testing/Technology_Integration_Permutation_Suite_Architecture_v0_12.md','docs/design/testing/technology_integration_permutation_suite_v0_12.json','docs/design/testing/Checkpoint_97_Validation_Tiers.md','docs/design/testing/checkpoint_97_validation_suite_policy_v0_1.json','docs/validation/Checkpoint_97_Encounter_And_Adaptive_Engage_AI_Foundation.md','src/StarCluster.Core/Combat/Tactics/TacticalCombatBlackboard.cs','tests/StarCluster.Tests/Combat/Tactics/TacticalCombatBlackboardTests.cs','src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs','src/StarCluster.ScenarioRunner/CrossTlIntegration/CrossTlBuildPermutationRunner.cs')){ $mutable[$r]=$true }
$frozen=0
foreach($entry in $acceptedManifest.Entries.GetEnumerator()){ $r=[string]$entry.Key; if($mutable.ContainsKey($r)){ continue }; Assert-True (Test-Path -LiteralPath (RelPath $r) -PathType Leaf) "Frozen CP97 file '$r' is missing."; Assert-True ((Hash-Rel $r) -eq [string]$entry.Value) "Frozen CP97 file '$r' changed unexpectedly."; $frozen++ }

Write-Host '       Reconstructing the 35-Space envelope and progression lattice independently...'
$foundation=Read-Json 'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/cross-tl-build-permutation-foundation-v0_7.json'
Assert-True ([string]$foundation.id -eq 'cross-tl-build-permutation-foundation-v0_7' -and [string]$foundation.generatedStudyId -eq 'tl2-itc18-cross-tl-adaptive-engage-progression-screening' -and [long]$foundation.masterSeed -eq 980100 -and [int]$foundation.trialsPerVariant -eq 250) 'CP98 foundation identity/seed/trials mismatch.'
Assert-True ([int]$foundation.expectedRawCombinationCount -eq 82944 -and [int]$foundation.expectedLegalBuildCount -eq 22592 -and [int]$foundation.expectedGeneratedVariantCount -eq 960 -and [int]$foundation.expectedGeometryCount -eq 2) 'CP98 declared envelope counts mismatch.'
$foundation96=Read-Json 'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/cross-tl-build-permutation-foundation-v0_6.json'
Assert-True (($foundation.axes | ConvertTo-Json -Depth 100 -Compress) -ceq ($foundation96.axes | ConvertTo-Json -Depth 100 -Compress)) 'CP98 foundation must preserve the accepted v0.6 construction-axis values exactly; CP98 introduces no new TL values.'
Assert-True (($foundation.fixedShell | ConvertTo-Json -Depth 20 -Compress) -ceq ($foundation96.fixedShell | ConvertTo-Json -Depth 20 -Compress) -and ($foundation.constructionGuardrails | ConvertTo-Json -Depth 20 -Compress) -ceq ($foundation96.constructionGuardrails | ConvertTo-Json -Depth 20 -Compress)) 'CP98 foundation must preserve the accepted v0.6 fixed shell and construction guardrails.'
Assert-True (($foundation.stratifiedPairingSelection | ConvertTo-Json -Depth 100 -Compress) -ceq ($foundation96.stratifiedPairingSelection | ConvertTo-Json -Depth 100 -Compress)) 'CP98 must preserve the accepted CP96/97 deterministic population-sampling configuration.'
$axes=@($foundation.axes); Assert-True ($axes.Count -eq 9) 'CP98 foundation must retain nine independent construction axes.'
$axisIndex=@{}; for($i=0;$i -lt $axes.Count;$i++){ $axisIndex[[string]$axes[$i].id]=$i }
$transitions=@($foundation.progressionLattice.transitions); Assert-True ([bool]$foundation.progressionLattice.enabled -and [bool]$foundation.progressionLattice.requireSameInstallationSpace -and $transitions.Count -eq 12 -and [int]$foundation.progressionLattice.expectedTotalLegalEdgeCount -eq 65648) 'CP98 progression lattice declaration mismatch.'
$edgeCount=@{}; $exactEdge=@{}; foreach($t in $transitions){ $edgeCount[[string]$t.id]=0; $exactEdge[[string]$t.id]=0; Assert-True ($axisIndex.ContainsKey([string]$t.axisId)) "Transition '$($t.id)' references missing axis."; $axis=$axes[$axisIndex[[string]$t.axisId]]; $from=@($axis.options|Where-Object id -eq ([string]$t.fromOptionId)); $to=@($axis.options|Where-Object id -eq ([string]$t.toOptionId)); Assert-True ($from.Count -eq 1 -and $to.Count -eq 1 -and [int]$from[0].space -eq [int]$to[0].space) "Transition '$($t.id)' must bind same-Space existing options." }
$optionCounts=@($axes|ForEach-Object{@($_.options).Count}); $raw=1; foreach($c in $optionCounts){ $raw*=$c }
$legal=0; $exact=0; $near=0; $under=0
for($n=0;$n -lt $raw;$n++){
 $x=$n; $used=[int]$foundation.fixedShellSpace; $selected=@{}
 for($i=0;$i -lt $axes.Count;$i++){ $opts=@($axes[$i].options); $idx=$x % $opts.Count; $x=[math]::Floor($x / $opts.Count); $o=$opts[$idx]; $selected[[string]$axes[$i].id]=[string]$o.id; $used += [int]$o.space }
 if($used -gt [int]$foundation.totalInstallationSpace){ continue }
 $legal++; if($used -eq 35){$exact++} elseif($used -ge 32){$near++} else {$under++}
 foreach($t in $transitions){ if($selected[[string]$t.axisId] -eq [string]$t.fromOptionId){ $edgeCount[[string]$t.id]++; if($used -eq 35){$exactEdge[[string]$t.id]++} } }
}
Assert-True ($raw -eq 82944 -and $legal -eq 22592 -and $exact -eq 4672 -and $near -eq 11328 -and $under -eq 6592) "Independent CP98 envelope reconstruction observed raw/legal/exact/near/under $raw/$legal/$exact/$near/$under."
$totalEdges=0; foreach($t in $transitions){ $id=[string]$t.id; Assert-True ($edgeCount[$id] -eq [int]$t.expectedLegalEdgeCount -and $exactEdge[$id] -eq [int]$t.expectedExactFillEdgeCount) "Independent progression count mismatch for '$id': $($edgeCount[$id])/$($exactEdge[$id])."; $totalEdges += $edgeCount[$id] }
Assert-True ($totalEdges -eq 65648) "Independent progression lattice observed $totalEdges edges; expected 65,648."
$geoms=@($foundation.geometries); Assert-True ($geoms.Count -eq 2 -and @($geoms|Where-Object movementMode -eq 'EngageAdaptive').Count -eq 2 -and @($geoms|Where-Object initialRangeHexes -eq 10).Count -eq 2 -and @($geoms|Where-Object movementOrder -eq 'SideAFirst').Count -eq 1 -and @($geoms|Where-Object movementOrder -eq 'SideBFirst').Count -eq 1) 'CP98 foundation Adaptive Encounter geometry drifted.'

Write-Host '       Validating actual-consumer, telemetry, safe-Strain, and report bindings...'
$runner=Read-Text 'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs'; $cross=Read-Text 'src/StarCluster.ScenarioRunner/CrossTlIntegration/CrossTlBuildPermutationRunner.cs'; $blackboard=Read-Text 'src/StarCluster.Core/Combat/Tactics/TacticalCombatBlackboard.cs'
foreach($needle in @('CrossTlAdaptiveEngageProgressionScreeningStudyId','RequiredCrossTlAdaptiveEngageProgressionScreeningVariantCount = 960','ValidateCrossTlAdaptiveEngageProgressionCoverage(','WriteCrossTlAdaptiveEngageProgressionReview(','cp98-safe-strain-exhaustion-suppresses-futile-requests','IsAdaptiveEncounterStudy(studyId)','IsSingleSourcePolicyTelemetryStudy')){ Require-Contains $runner $needle "CP98 integrated consumer is missing binding '$needle'." }
foreach($needle in @('BuildProgressionLattice(','progression-lattice-total-edge-count','progression-lattice-summary.json','progression-lattice-edges.csv','generated-geometry-binding')){ Require-Contains $cross $needle "CP98 generator is missing binding '$needle'." }
foreach($needle in @('RecordSafeStrainExhausted','IsSafeStrainExhausted','_safeStrainExhausted','if (IsSafeStrainExhausted(kind))')){ Require-Contains $blackboard $needle "Combat blackboard is missing safe-Strain capability binding '$needle'." }
$eccmStart=$runner.IndexOf('private static AdaptiveEccmOverloadResult TryAdaptiveEccmOverload',[StringComparison]::Ordinal); $eccmEnd=$runner.IndexOf('private static TacticalTrackQuality ToPlayerTrackQuality',$eccmStart,[StringComparison]::Ordinal); Assert-True ($eccmStart -ge 0 -and $eccmEnd -gt $eccmStart) 'Could not isolate Adaptive ECCM overload method.'; $eccm=$runner.Substring($eccmStart,$eccmEnd-$eccmStart); Assert-True ($eccm.IndexOf('RecordSafeStrainExhausted',[StringComparison]::Ordinal) -ge 0 -and $eccm.IndexOf('RecordSafeStrainExhausted',[StringComparison]::Ordinal) -lt $eccm.IndexOf('RecordEwOverloadRequest',[StringComparison]::Ordinal)) 'Adaptive ECCM must suppress safe-Strain-exhausted request before telemetry records another request.'
$sensorStart=$runner.IndexOf('private static Tl1IntegratedSensorOverloadPolicy AdaptiveSensorOverloadPolicy',[StringComparison]::Ordinal); $sensorEnd=$runner.IndexOf('private static AdaptiveEccmOverloadResult TryAdaptiveEccmOverload',$sensorStart,[StringComparison]::Ordinal); $sensor=$runner.Substring($sensorStart,$sensorEnd-$sensorStart); Assert-True ($sensor.IndexOf('RecordSafeStrainExhausted',[StringComparison]::Ordinal) -ge 0 -and $sensor.IndexOf('CanAttemptOverload',[StringComparison]::Ordinal) -gt $sensor.IndexOf('RecordSafeStrainExhausted',[StringComparison]::Ordinal)) 'Adaptive Active Sensor policy must mark safe-Strain exhaustion before retry eligibility.'
# Compiler-class preflight: detect nested local-name shadowing in all CP98-mutated progression-generator/gate methods before native build.
foreach($method in @(
 @('private static IReadOnlyList<CrossTlProgressionEdge> BuildProgressionLattice(','BuildProgressionLattice'),
 @('private static string CrossTlProfileLabelValue(','CrossTlProfileLabelValue'),
 @('private static IReadOnlyList<CrossTlFoundationGate> BuildFoundationGates(','BuildFoundationGates'),
 @('private static void WriteProgressionLatticeSummary(','WriteProgressionLatticeSummary'),
 @('private static void WriteProgressionLatticeEdges(','WriteProgressionLatticeEdges')
)){ Assert-NoNestedLocalShadowing $cross $method[0] $method[1] }
Require-Contains $cross 'int transitionExactFill = progressionEdges.Count' 'CP98 progression gate must use a transition-scoped exact-fill local distinct from the enclosing exactFill aggregate.'
# Known compiler-class patterns from CP97 authoring failures.
Require-NotContains $runner 'FinalTrack != TacticalTrackQuality' 'Changed runner contains a known cross-enum FinalTrack/TacticalTrackQuality comparison.'
Require-NotContains $runner 'FinalTrack == TacticalTrackQuality' 'Changed runner contains a known cross-enum FinalTrack/TacticalTrackQuality comparison.'
Assert-True (-not [regex]::IsMatch($blackboard,'TryGetValue\([^\r\n]+out\s+TacticalOverloadFailure\s+[A-Za-z_]')) 'Combat blackboard reintroduced a non-nullable TryGetValue out reference.'
Assert-True (-not [regex]::IsMatch($runner,'TryGetValue\([^\r\n]+out\s+SensorEwFoundationProfile\s+[A-Za-z_]')) 'Runner reintroduced a non-nullable SensorEwFoundationProfile TryGetValue out reference.'
$testText=Read-Text 'tests/StarCluster.Tests/Combat/Tactics/TacticalCombatBlackboardTests.cs'; Require-Contains $testText 'SafeStrainExhaustionSuppressesRetryEvenAfterClosingOrObservableChange' 'CP98 xUnit regression for safe-Strain exhaustion is missing.'

Write-Host '       Validating current authorities and checkpoint documentation...'
$aiPolicy=Read-Json 'docs/archive/ai/pre-cp165-active/adaptive_engage_policy_v0_2.json'; Assert-True ([string]$aiPolicy.id -eq 'adaptive-engage-policy-v0_2' -and [bool]$aiPolicy.combatBlackboard.safeStrainExhaustionRemembered -and [bool]$aiPolicy.escalation.safeStrainExhaustionSuppressesRetry -and [bool]$aiPolicy.escalation.closerRangeDoesNotRestoreSafeStrain) 'Adaptive Engage v0.2 machine policy mismatch.'
Assert-True ([bool]$aiPolicy.escalation.powerDeniedRetryMayReenterAfterOwnPowerStateChange) 'Adaptive Engage v0.2 must preserve retry after real power-state change.'
$suite=Read-Json 'docs/design/testing/technology_integration_permutation_suite_v0_13.json'; Assert-True ([string]$suite.id -eq 'technology-integration-permutation-suite-v0_13' -and [int]$suite.currentCoverage.progressionLattice.singleAxisLegalEdges -eq 65648 -and [int]$suite.currentCoverage.currentStudy.variantCount -eq 960) 'Standing permutation suite v0.13 mismatch.'
Assert-ExactFileSet 'docs/design/testing' @('README.md','Technology_Integration_Permutation_Suite_Architecture_v0_13.md','technology_integration_permutation_suite_v0_13.json','Checkpoint_98_Validation_Tiers.md','checkpoint_98_validation_suite_policy_v0_1.json')
Assert-True (Test-Path -LiteralPath (RelPath 'docs/archive/testing/Technology_Integration_Permutation_Suite_Architecture_v0_12.md')) 'Superseded suite v0.12 architecture must be archived.'
Assert-True (Test-Path -LiteralPath (RelPath 'docs/archive/ai/AI_Doctrine_Registry_Architecture_v0_6.md')) 'Superseded AI architecture v0.6 must be archived.'
$activeValidation=@(Get-ChildItem -LiteralPath (RelPath 'docs/validation') -File -Filter 'Checkpoint_*.md'); Assert-True ($activeValidation.Count -eq 1 -and $activeValidation[0].Name -eq 'Checkpoint_98_Cross_Progression_Adaptive_Engage_Integration_Foundation.md') 'Exactly one active CP98 validation runbook must remain.'
$policy=Read-Json 'docs/design/testing/checkpoint_98_validation_suite_policy_v0_1.json'; Assert-True ([string]$policy.checkpoint -eq '98' -and [long]$policy.study.totalTrialExecutionsAtDefault -eq 242436 -and [int]$policy.crossProgression.progressionLegalEdges -eq 65648 -and -not [bool]$policy.authorityBoundary.initiativeRuleChange -and -not [bool]$policy.deepCalibration.applicable) 'CP98 validation policy mismatch.'
$runbook=Read-Text 'docs/validation/Checkpoint_98_Cross_Progression_Adaptive_Engage_Integration_Foundation.md'; foreach($needle in @('d261eb01efde0919bb55f36e9fa58a5cf8885845af89310c12a92ebba0689055','888e8c85f1fa3db5b95abc435d1bc51103ef7f7b99d5f79be5c8492bd6269ad4','65,648','242,436','876 xUnit','62 ScenarioRunner')){ Require-Contains $runbook $needle "CP98 runbook is missing '$needle'." }

Write-Host '       Validating root manifest...'
$rootTxt=@(Get-ChildItem -LiteralPath $repositoryRoot -File -Filter '*.txt'); Assert-True ($rootTxt.Count -eq 1 -and $rootTxt[0].Name -eq 'CHECKPOINT_98_SHA256SUMS.txt') 'Repository root must contain only CHECKPOINT_98_SHA256SUMS.txt as .txt.'
$manifest=Read-Manifest 'CHECKPOINT_98_SHA256SUMS.txt'; Assert-True ($manifest.EntryCount -eq 1905 -and $manifest.PhysicalLineCount -eq 1905) 'CP98 manifest must contain exactly 1,905 repository-owned entries.'; Assert-True (-not $manifest.Entries.ContainsKey('CHECKPOINT_98_SHA256SUMS.txt')) 'CP98 manifest must not contain itself.'
foreach($entry in $manifest.Entries.GetEnumerator()){ Assert-True (Test-Path -LiteralPath (RelPath ([string]$entry.Key)) -PathType Leaf) "CP98 manifest entry '$($entry.Key)' is missing."; Assert-True ((Hash-Rel ([string]$entry.Key)) -eq [string]$entry.Value) "CP98 manifest hash mismatch for '$($entry.Key)'." }
Write-Host "Checkpoint 98 repository contracts passed ($frozen CP97 files frozen; independent 22,592-build / 65,648-edge progression reconstruction; Adaptive Engage consumer/preflight bindings locked)."
