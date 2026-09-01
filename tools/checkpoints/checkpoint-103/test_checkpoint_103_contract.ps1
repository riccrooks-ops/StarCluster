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
function Product-Options { param($Axes) [long]$p=1; foreach($axis in @($Axes)){ $p=[long]($p * @($axis.options).Count) }; return $p }
function Option-Ids { param($Study,[string]$AxisId) $axis=@($Study.axes|Where-Object{[string]$_.id -eq $AxisId}); Assert-True ($axis.Count -eq 1) "Study is missing axis '$AxisId'."; return @($axis[0].options|ForEach-Object{[string]$_.id}) }
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
    [pscustomobject]@{ EntryCount=$map.Count; Entries=$map }
}
function Test-IsGeneratedOrLocalPath {
    param([string]$RelativePath)
    $path=$RelativePath.Replace('\','/')
    if($path -like '.git/*' -or $path -like '.vs/*' -or $path -like '.vscode/*' -or $path -like '.idea/*' -or $path -like 'out/*' -or $path -like 'src/StarCluster.Game/.godot/*' -or $path -match '(^|/)(bin|obj|TestResults)/'){ return $true }
    if($path -match '(^|/)__pycache__/' -or $path -match '\.pyc$'){ return $true }
    if($path -match '\.(user|userosscache|sln\.docstates|uid)$' -or $path -match '(^|/)\.suo$' -or $path -match '(^|/)(\.DS_Store|Thumbs\.db)$'){ return $true }
    return $false
}
function Get-Cp103RepositoryOwnedFileSet {
    $map=@{}
    foreach($file in @(Get-ChildItem -LiteralPath $repositoryRoot -Recurse -File -Force)){
        $rel=$file.FullName.Substring($repositoryRoot.Length).TrimStart('\','/').Replace('\','/')
        if($rel -eq 'CHECKPOINT_103_SHA256SUMS.txt'){ continue }
        if(Test-IsGeneratedOrLocalPath -RelativePath $rel){ continue }
        $map[$rel]=$true
    }
    return $map
}
function Assert-Cp103GeneratedArtifactSequencePreflight {
    param($Expected)
    $outputDir=RelPath 'out/checkpoint-103'; $null=New-Item -ItemType Directory -Path $outputDir -Force
    $probePaths=@((Join-Path $outputDir 'acceptance-summary.json'),(Join-Path $outputDir 'acceptance-summary.txt')); $created=@()
    foreach($probe in $probePaths){ if(-not (Test-Path -LiteralPath $probe -PathType Leaf)){ 'CP103 RepositoryOnly sequence preflight generated artifact' | Set-Content -LiteralPath $probe -Encoding ASCII; $created += $probe } }
    try {
        foreach($rel in @('out/checkpoint-103/acceptance-summary.json','out/checkpoint-103/acceptance-summary.txt','src/StarCluster.Core/bin/Debug/net8.0/generated.dll','src/StarCluster.Core/obj/generated.tmp','TestResults/generated.trx','tools/simulation/starcluster_research/__pycache__/model.cpython-313.pyc','tools/simulation/tests/test_cp103_research.pyc')){ Assert-True (Test-IsGeneratedOrLocalPath -RelativePath $rel) "Generated/local artifact policy failed to ignore '$rel'." }
        $actual=Get-Cp103RepositoryOwnedFileSet; Assert-True ($actual.Count -eq $Expected.Count) 'CP103 RepositoryOnly-to-full-run generated artifacts changed the repository-owned file count.'
        foreach($rel in $Expected.Keys){ Assert-True ($actual.ContainsKey([string]$rel)) "CP103 sequence preflight lost repository-owned path '$rel'." }
        foreach($rel in $actual.Keys){ Assert-True ($Expected.ContainsKey([string]$rel)) "CP103 sequence preflight treated generated/local path '$rel' as repository-owned." }
    }
    finally { foreach($probe in $created){ Remove-Item -LiteralPath $probe -Force -ErrorAction SilentlyContinue } }
}

Write-Host '       Validating native dependencies, wrapper interface, and checkpoint definitions...'
$normalRel='tools/calibration/checkpoints/checkpoint-103.json'; $deepRel='tools/calibration/checkpoints/checkpoint-103-deep-calibration.json'
$guarded=@('tools/checkpoints/Test-NativeAcceptanceDependencies.ps1','tools/checkpoints/checkpoint-103/apply_checkpoint_103.ps1','tools/checkpoints/checkpoint-103/test_checkpoint_103_contract.ps1','tools/simulation/Invoke-StarClusterResearch.ps1','tools/calibration/run_calibration_checkpoint.ps1')
& (RelPath 'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1') -RepositoryRoot $repositoryRoot -PowerShellPaths $guarded -CheckpointDefinitionPaths @($normalRel,$deepRel) -AllowedInterpreters @('python','python3','py')
$apply=Read-Text 'tools/checkpoints/checkpoint-103/apply_checkpoint_103.ps1'
Require-Contains $apply 'function Assert-Cp103PowerShell51ArrayCompatibility' 'CP103 wrapper must define the Windows PowerShell 5.1 array-shape compatibility precheck.'
Require-Contains $apply 'function Assert-Cp103DefinitionBindings' 'CP103 wrapper must preflight its checkpoint-definition dependency bindings before the contract/harness.'
Require-Contains $apply 'Assert-Cp103DefinitionBindings -DefinitionPaths' 'CP103 wrapper must invoke its checkpoint-definition dependency-binding precheck.'
Require-Contains $apply '& $harness -CheckpointDefinition $definition -Trials $Trials -Jobs $Jobs -RepositoryOnly:$RepositoryOnly -NoClean:$NoClean' 'CP103 wrapper must use direct named-parameter harness invocation.'
Assert-True ($apply.IndexOf('@harnessArgs',[StringComparison]::OrdinalIgnoreCase) -lt 0) 'CP103 wrapper must not use fragile harness array splatting.'
$normal=Read-Json $normalRel; $deep=Read-Json $deepRel
$expectedStageIds=@('deterministic','tl1-phase-a','tl1-phase-b','tl1-installation-space-envelope','tl1-sensor-ew-foundation','cross-tl-cp99-exact-edge-preflight','cross-tl-cp99-exact-edge-generation','cross-tl-cp102-construction-envelope-preflight','cross-tl-cp102-transition-preflight','cross-tl-cp102-transition-generation','cross-tl-cp102-generated-study-preflight','cross-tl-cp102-generated-study-smoke','cp103-python-environment','cp103-python-self-tests','cp103-python-parity','cross-tl-cp103-primary-validation','cross-tl-cp103-overlay-validation','cross-tl-cp103-primary-smoke','cross-tl-cp103-overlay-smoke','cross-tl-cp103-primary-substantive','cross-tl-cp103-overlay-substantive','cross-tl-cp103-analysis','auxiliary-resource-endurance','checkpoint-53-resource-semantics-lock','runner-self-tests')
foreach($def in @($normal,$deep)){
    Assert-True ([int]$def.schemaVersion -eq 1 -and [string]$def.checkpointId -eq '103') 'CP103 checkpoint-definition identity drifted.'
    Assert-True ([string]$def.sdkVersion -eq '8.0.423' -and [string]$def.configuration -eq 'Debug') 'CP103 pinned SDK/configuration drifted.'
    Assert-True ([string]$def.manifestFile -eq 'CHECKPOINT_103_SHA256SUMS.txt' -and [string]$def.outputRoot -eq 'out/checkpoint-103') 'CP103 manifest/output binding drifted.'
    $nativePrecheck=$def.nativeDependencyPrecheck
    Assert-True ($null -ne $nativePrecheck -and [bool]$nativePrecheck.required -and [string]$nativePrecheck.script -eq 'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1') 'CP103 checkpoint definition native-dependency precheck declaration drifted.'
    Assert-Sequence @($nativePrecheck.powerShellPaths|ForEach-Object{[string]$_}) $guarded 'CP103 checkpoint definition native-dependency PowerShell inspection surface drifted.'
    Assert-Sequence @($nativePrecheck.checkpointDefinitionPaths|ForEach-Object{[string]$_}) @($normalRel,$deepRel) 'CP103 checkpoint definition native-dependency definition inspection surface drifted.'
    Assert-Sequence @($nativePrecheck.allowedInterpreters|ForEach-Object{[string]$_}) @('python','python3','py') 'CP103 checkpoint definition explicitly allowed research interpreters drifted.'
    Assert-True ([string]$def.description -like 'Measure the native-accepted TL1/TL2/TL3 executable technology architecture with the CP103 Python research simulator*' -and [string]$def.description -like '*no automatic technology promotion*') 'CP103 checkpoint-definition description drifted or was copied from an older checkpoint.'
    Assert-True ([int]$def.defaultTrials -eq 250 -and [int]$def.defaultJobs -eq 24) 'CP103 substantive default workload drifted.'
    Assert-True (@($def.stages).Count -eq 25 -and [int]$def.checkpointMetrics.stageCount -eq 25) 'CP103 must contain exactly 25 runner stages.'
    Assert-True ([int]$def.checkpointMetrics.expectedXunitTests -eq 876 -and [int]$def.checkpointMetrics.expectedRunnerSelfTests -eq 70 -and [int]$def.checkpointMetrics.cp103PythonUnitTests -eq 6 -and [int]$def.checkpointMetrics.cp103PythonParityCases -eq 25) 'CP103 C#/Python expected test counts drifted.'
    Assert-True ([int]$def.checkpointMetrics.monteCarloVariantCount -eq 1252 -and [int]$def.checkpointMetrics.trialsAtDefault -eq 313000 -and [int]$def.checkpointMetrics.smokeTrialsAtDefault -eq 1284 -and [int]$def.checkpointMetrics.totalTrialExecutionsAtDefault -eq 314284) 'CP103 aggregate workload accounting drifted.'
    Assert-True ([string]$def.primaryStudy.id -eq 'cross-tl-cp103-primary-substantive' -and [int]$def.primaryStudy.variantCount -eq 1152) 'CP103 acceptance-summary primary-study binding drifted.'
    Assert-True ([string]$def.checkpointMetrics.acceptedBaselineCheckpoint -eq '102' -and [bool]$def.checkpointMetrics.cp102NativeAccepted -and -not [bool]$def.checkpointMetrics.technologyPromotionAutomatic -and -not [bool]$def.checkpointMetrics.deepCalibrationApplicable) 'CP103 baseline/promotion/deep-calibration lifecycle drifted.'
    Assert-True ([string]$def.checkpointMetrics.pythonResearchEngine -eq 'starcluster-python-research-v1' -and [string]$def.checkpointMetrics.pythonMajorMinor -eq '3.13' -and [bool]$def.checkpointMetrics.pythonStdlibOnly -and -not [bool]$def.checkpointMetrics.cp103CSharpSimulationExtension -and [bool]$def.checkpointMetrics.cp103LocalExecutableResearchRequired) 'CP103 research-engine lifecycle metadata drifted.'
    foreach($stage in @($def.stages | Where-Object { [string]$_.id -like 'cp103-python-*' -or [string]$_.id -like 'cross-tl-cp103-*' })){ Assert-True ([string]$stage.executor -eq 'powershell-script' -and [string]$stage.script -eq 'tools/simulation/Invoke-StarClusterResearch.ps1') "CP103 research stage '$($stage.id)' must execute through the Python research wrapper." }
    Assert-Sequence @($def.stages|ForEach-Object{$_.id}) $expectedStageIds 'CP103 stage sequence drifted.'
    foreach($doc in @($def.documentation)){ Assert-True (Test-Path -LiteralPath (RelPath ([string]$doc)) -PathType Leaf) "CP103 definition references missing documentation '$doc'." }
}
Assert-Sequence @($deep.stages|ForEach-Object{$_.id}) @($normal.stages|ForEach-Object{$_.id}) 'CP103 deep alias must use the exact normal stage sequence.'

Write-Host '       Validating accepted CP102 provenance and frozen regression surfaces...'
Assert-True ((Hash-Rel 'docs/validation/evidence/checkpoint-102/CHECKPOINT_102_SHA256SUMS.txt') -eq '02582d2def97fd3060dc66128ab11d6744b1d8f48ff58cfbe44865524604ed89') 'Embedded accepted CP102 manifest hash drifted.'
Assert-True ((Hash-Rel 'tools/calibration/checkpoints/checkpoint-102.json') -eq 'b996ca4517d114a701faf4665c9440032f597354b0c91070e3b058e8eaa64f1f') 'Accepted CP102 checkpoint definition bytes drifted.'
$cp102Evidence=Read-Json 'docs/validation/evidence/checkpoint-102/cp102-accepted-evidence.json'
Assert-True ([string]$cp102Evidence.status -eq 'native-accepted' -and [string]$cp102Evidence.nativeResultsZipSha256 -eq '5becb0ce44e76d6be8c5515e3956dece9f7ed025d6836fa105ad3f03ada4ca23') 'Embedded CP102 native-results provenance drifted.'
Assert-True ([int]$cp102Evidence.xunitPassed -eq 876 -and [int]$cp102Evidence.runnerStagesPassed -eq 15 -and [int]$cp102Evidence.scenarioRunnerSelfTestsPassed -eq 70 -and [int]$cp102Evidence.failedGates -eq 0) 'Embedded CP102 native-acceptance counters drifted.'
Assert-True ((Hash-Rel 'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/cross-tl-build-permutation-foundation-v0_8.json') -eq '148f4aadda8d65891a961a6e981c77c67e4e28a00359f0ad476e2e257f5be944') 'Frozen CP99 v0.8 regression foundation bytes drifted.'
$cp102Construction=Read-Json 'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/cross-tl-build-permutation-foundation-v0_9.json'
$cp102Transition=Read-Json 'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/cross-tl-build-permutation-foundation-v1_0.json'
Assert-True ([int]$cp102Construction.expectedLegalBuildCount -eq 51264 -and [int]$cp102Transition.expectedLegalBuildCount -eq 38400 -and [int]$cp102Transition.progressionLattice.expectedTotalLegalEdgeCount -eq 220416 -and [int]$cp102Transition.expectedGeneratedVariantCount -eq 32) 'Accepted CP102 v7 regression counts drifted.'

Write-Host '       Validating CP103 v8 primary population and diagnostic-overlay declarations...'
$primary=Read-Json 'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/cross-tl-build-permutation-foundation-v1_1.json'
$overlay=Read-Json 'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/cross-tl-build-permutation-foundation-v1_2.json'
foreach($study in @($primary,$overlay)){
    Assert-True ($study.checkpoint -is [string]) 'CP103 v8 checkpoint must be encoded as a JSON string; numeric checkpoint values are rejected by the executable consumer contract.'
    Assert-True ([string]$study.schemaVersion -eq 'star-cluster-cross-tl-build-permutation-v8' -and [string]$study.checkpoint -eq '103') 'CP103 v8 study identity drifted.'
    Assert-True ([string]$study.researchSimulationEngine -eq 'starcluster-python-research-v1' -and [string]$study.researchSimulationAuthority -eq 'screening_not_gameplay_authority' -and [string]$study.pythonRuntimeMajorMinor -eq '3.13') 'CP103 v8 research-simulation ownership/runtime declaration drifted.'
    Assert-Sequence @($study.axes|ForEach-Object{$_.id}) @('hull','weapon','reactor','computer','sensor','shield','shieldHardener','armor','ecm','eccm','stl','ftl','pds') 'CP103 v8 axis order/identity drifted.'
    Assert-True ([int]$study.constructionGuardrails.minimumMainWeaponCount -eq 1 -and [int]$study.constructionGuardrails.minimumReactorCount -eq 1 -and [int]$study.constructionGuardrails.minimumSensorCount -eq 1 -and -not [bool]$study.constructionGuardrails.powerSufficiencyIsConstructionLegalityFilter) 'CP103 construction-core/TP-legality guardrail drifted.'
    Assert-True (-not [bool]$study.constructionGuardrails.ecmSameTypeRatingsAdditive -and -not [bool]$study.constructionGuardrails.eccmSameTypeRatingsAdditive -and [string]$study.constructionGuardrails.ewDuplicateResolution -eq 'highest_applicable_functional_rating') 'CP103 non-additive EW redundancy rule drifted.'
    Assert-True ((Product-Options $study.axes) -eq [long]$study.expectedRawCombinationCount) 'CP103 declared raw Cartesian product does not match axis option counts.'
}
Assert-True ([string]$primary.coverageMode -eq 'integration_screening' -and [string]$primary.generatedStudyId -eq 'tl3-cp103-frontier-population-screening') 'CP103 primary coverage/study ID drifted.'
Assert-True ([int]$primary.expectedRawCombinationCount -eq 921600 -and [int]$primary.expectedLegalBuildCount -eq 164160 -and [int]$primary.expectedExactFillBuildCount -eq 43584 -and [int]$primary.expectedNearFillBuildCount -eq 82848 -and [int]$primary.expectedUnderfilledBuildCount -eq 37728) 'CP103 primary legal/Space envelope drifted.'
Assert-True ([long]$primary.expectedUnorderedDistinctPairingEnvelope -eq 13474170720 -and [long]$primary.expectedOrientedDistinctPairingEnvelope -eq 26948341440) 'CP103 primary distinct pairing envelope drifted.'
$selection=$primary.stratifiedPairingSelection
Assert-True ([bool]$selection.enabled -and [bool]$selection.adaptiveAllocationEnabled -and [bool]$selection.matchedBidirectional -and [int]$selection.nearFillHeadroomMaximum -eq 3 -and [int]$selection.equalLowAdvancedMaximum -eq 5 -and [int]$selection.targetBasePairBudget -eq 240 -and [int]$selection.minimumPerPopulationCell -eq 1 -and [int]$selection.maximumPerPopulationCell -eq 6 -and [double]$selection.allocationExponent -eq 0.5) 'CP103 adaptive/capacity-relative/frontier selection settings drifted.'
Assert-True (@($selection.compositionClasses).Count -eq 4 -and @($selection.progressionMagnitudeStrata).Count -eq 4 -and @($selection.spacePairStrata).Count -eq 6) 'CP103 primary must define exactly 96 population cells.'
Assert-True ([int]$selection.expectedBasePairCount -eq 240 -and [int]$selection.expectedSampleCount -eq 480 -and [int]$selection.expectedDiversityBasePairCount -eq 32 -and [int]$selection.expectedDiversitySampleCount -eq 64) 'CP103 adaptive sample/overlay counts drifted.'
Assert-True ([int]$primary.expectedNamedRecipeCount -eq 32 -and [int]$primary.expectedNamedLogicalPairingCount -eq 32 -and [int]$primary.expectedLogicalPairingCount -eq 576 -and [int]$primary.expectedGeneratedVariantCount -eq 1152 -and [int]$primary.trialsPerVariant -eq 250) 'CP103 primary recipe/pairing/variant workload drifted.'
$primaryFtl=@(Option-Ids $primary 'ftl'); Assert-True ($primaryFtl.Count -eq 1 -and $primaryFtl[0] -eq 'ftl2') 'CP103 weighted population must collapse tactically isomorphic FTL2/FTL3 labels.'
$primaryPds=@(Option-Ids $primary 'pds'); Assert-True (($primaryPds -contains 'kpds2') -and -not ($primaryPds -contains 'kpds3')) 'CP103 weighted population must collapse the held Kinetic-PDS3 label while retaining Kinetic PDS2.'
Assert-True ([string]$overlay.coverageMode -eq 'diagnostic_overlay' -and [string]$overlay.generatedStudyId -eq 'tl3-cp103-legacy-stack-diagnostic-screening') 'CP103 diagnostic overlay coverage/study ID drifted.'
Assert-True ([int]$overlay.expectedRawCombinationCount -eq 1417176 -and [int]$overlay.expectedLegalBuildCount -eq 28 -and [int]$overlay.expectedNamedRecipeCount -eq 33 -and [int]$overlay.expectedLogicalPairingCount -eq 50 -and [int]$overlay.expectedGeneratedVariantCount -eq 100 -and [int]$overlay.trialsPerVariant -eq 250) 'CP103 diagnostic-overlay bounds/workload drifted.'
Assert-True (-not [bool]$overlay.stratifiedPairingSelection.enabled -and [int]$overlay.expectedStratifiedLogicalPairingCount -eq 0) 'CP103 diagnostic overlay must remain named-only with stratified population sampling disabled.'
$overlayFtl=@(Option-Ids $overlay 'ftl'); Assert-True (($overlayFtl -contains 'ftl1') -and ($overlayFtl -contains 'ftl2') -and ($overlayFtl -contains 'ftl3')) 'CP103 legacy overlay must retain TL1/TL2/TL3 FTL labels as explicit diagnostics.'
$overlayPds=@(Option-Ids $overlay 'pds'); Assert-True (($overlayPds -contains 'kpds2') -and ($overlayPds -contains 'kpds3')) 'CP103 legacy overlay must retain the held Kinetic-PDS2/PDS3 negative control.'

Write-Host '       Validating CP103 Python research-engine ownership and frozen C# mechanics surface...'
$runtime=Read-Json 'tools/simulation/PYTHON_RUNTIME.json'
Assert-True ([string]$runtime.implementation -eq 'CPython' -and [string]$runtime.majorMinor -eq '3.13' -and [bool]$runtime.stdlibOnly -and [string]$runtime.deterministicRng -eq 'repository-owned-xorshift64') 'CP103 Python runtime policy drifted.'
$pythonReadme=Read-Text 'tools/simulation/README.md'
foreach($needle in @('C#/Godot is authoritative for game mechanics','Python is authoritative for research-study construction and statistical execution','CPython 3.13.x','standard-library-only','Research Monte Carlo output is screening evidence')){ Require-Contains $pythonReadme $needle "CP103 Python research README is missing '$needle'." }
$pythonWrapper=Read-Text 'tools/simulation/Invoke-StarClusterResearch.ps1'
foreach($needle in @('PYTHON_RUNTIME.json','Resolve-Cp103Python','py','python','python3','No pip packages are required','run_starcluster_research.py','[void]$invokeArgs.Add(''-B'')','--version','Windows PowerShell 5.1','[regex]::Match')){ Require-Contains $pythonWrapper $needle "CP103 Python wrapper is missing '$needle'." }
Assert-True (-not [regex]::IsMatch($pythonWrapper, '(?m)^\s*\$probe\s*=.*-c')) 'CP103 Python wrapper must not use Python -c for the Windows PowerShell 5.1 bootstrap probe.'
$harnessText=Read-Text 'tools/calibration/run_calibration_checkpoint.ps1'
foreach($needle in @('__pycache__','\.pyc$','powershell-script','allowedInterpreters','failedGates')){ Require-Contains $harnessText $needle "Shared checkpoint harness is missing CP103 Python executor/hygiene/gate support '$needle'." }
$pythonCli=Read-Text 'tools/simulation/starcluster_research/cli.py'
$pythonStudy=Read-Text 'tools/simulation/starcluster_research/study.py'
$pythonCombat=Read-Text 'tools/simulation/starcluster_research/combat.py'
$pythonRunner=Read-Text 'tools/simulation/starcluster_research/runner.py'
$pythonParity=Read-Text 'tools/simulation/starcluster_research/parity.py'
foreach($needle in @("require_type(doc,'checkpoint',str)",'CP103 v8 checkpoint must be the string "103"','expectedRawCombinationCount','expectedLegalBuildCount','configured CP103 population cell is empty','adaptive sampler stopped')){ Require-Contains $pythonStudy $needle "CP103 executable study validator is missing '$needle'." }
foreach($needle in @('environment','validate','self-test','parity','run','analyze')){ Require-Contains $pythonCli $needle "CP103 Python CLI is missing command '$needle'." }
foreach($needle in @('direct_hit_chance','apply_damage','sensor_track','run_trial')){ Require-Contains $pythonCombat $needle "CP103 research combat model is missing '$needle'." }
foreach($needle in @('EXPECTED_PRIMARY_ROWS=1152',"EXPECTED_SOURCE_COUNTS={'statistical':960,'diversity':128,'named':64}",'EXPECTED_STATISTICAL_BUNDLES=240','EXPECTED_POPULATION_CELLS=96','EXPECTED_POPULATION_WEIGHT=13_474_170_720.0','EXPECTED_OVERLAY_ROWS=100','EXPECTED_OVERLAY_DIAGNOSTICS=25','analysis_space_breakpoints.csv','analysis_dominance_screen.csv','analysis_legacy_overlay.csv','failed_gates')){ Require-Contains $pythonRunner $needle "CP103 Python analysis/gating surface is missing '$needle'." }
foreach($needle in @('PARITY_CASE_COUNT = 25','direct-fire chance expected 67','layered hardener damage mismatch','DR1 versus ECM2 without ECCM','TL2 ECCM2 must restore Firm','TL3 high sensor expected Firm/high/2','duplicate TL3 ECM must remain Rating2/non-additive','K3 parity fixture must retain 0-TP ordinary fire','TL3 AMM PDS expected base20','Energy PDS readiness must improve')){ Require-Contains $pythonParity $needle "CP103 C#/Python parity corpus is missing '$needle'." }
Assert-True (Test-Path -LiteralPath (RelPath 'tools/simulation/schemas/cross_tl_v8.schema.json') -PathType Leaf) 'CP103 v8 JSON Schema file is missing.'
$schema=Read-Json 'tools/simulation/schemas/cross_tl_v8.schema.json'
Assert-True ([string]$schema.properties.checkpoint.type -eq 'string' -and [string]$schema.properties.checkpoint.const -eq '103') 'CP103 v8 schema must reject numeric checkpoint values.'
$tests=Read-Text 'tools/simulation/tests/test_cp103_research.py'
foreach($needle in @('test_numeric_checkpoint_is_rejected','test_primary_exact_population_contract','97848','test_overlay_exact_contract','test_parity_corpus')){ Require-Contains $tests $needle "CP103 Python unit corpus is missing '$needle'." }
Assert-True ((Hash-Rel 'src/StarCluster.ScenarioRunner/CrossTlIntegration/CrossTlBuildPermutationRunner.cs') -eq '6cebb3efa11e1fea63cab88377b9de0960b3d5e2a9029385a72556c87afe2984') 'CP103 must preserve the native-accepted CP102 CrossTlBuildPermutationRunner rather than extending C# for the research study.'
Assert-True ((Hash-Rel 'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs') -eq '8c46eb15814737a1dae80c3320be385361b054c6f8c3cce96afd4dd3a4cc525e') 'CP103 must preserve the native-accepted CP102 integrated tactical-combat C# runner.'
Assert-True ((Hash-Rel 'src/StarCluster.ScenarioRunner/ScenarioRunnerSelfTests.cs') -eq 'af3bb02e64f371f20a4ed6051c7f90fbec960ed6fc614960893d17e28ee858ce') 'CP103 must preserve the native-accepted CP102 ScenarioRunner self-test surface.'

Write-Host '       Validating CP103 standing suite, Matrix, lifecycle, and durable methodology...'
$suite=Read-Json 'docs/design/testing/technology_integration_permutation_suite_v0_18.json'
Assert-True ([int]$suite.checkpoint -eq 103 -and [bool]$suite.cp102NativeAccepted -and [bool]$suite.cp102NoBalanceInference -and [bool]$suite.cp103NoAutomaticPromotion) 'Standing suite v0.18 lifecycle drifted.'
$suitePrimary=$suite.currentCoverage.cp103PrimaryPopulationScreen
Assert-True ([long]$suitePrimary.conceptualUnorderedDistinctPairingEnvelope -eq 13474170720 -and [string]$suitePrimary.populationAccounting -eq 'bucket_combinatorial_no_full_pair_materialization' -and [int]$suitePrimary.equalLowAdvancedMaximum -eq 5 -and [int]$suitePrimary.equalHighAdvancedMinimum -eq 6 -and [bool]$suitePrimary.tacticalFrontierExcludesStrategicFtl) 'Standing suite v0.18 CP103 population/frontier accounting drifted.'
Assert-Sequence @($suitePrimary.tacticalFrontierAdditionalAxes) @('hull','shieldHardener','stl','pds') 'Standing suite v0.18 CP103 tactical frontier axes drifted.'
Assert-True ([int]$suite.currentCoverage.cp103PrimaryPopulationScreen.legalBuildCount -eq 164160 -and [int]$suite.currentCoverage.cp103PrimaryPopulationScreen.generatedVariants -eq 1152 -and [int]$suite.currentCoverage.cp103LegacyDiagnosticOverlay.generatedVariants -eq 100 -and [int]$suite.currentCoverage.cp103LegacyDiagnosticOverlay.populationInferenceWeight -eq 0) 'Standing suite v0.18 CP103 coverage drifted.'
$matrix=Read-Json 'docs/archive/player_technology/pre-cp165-active/technology_architecture_matrix_v1.json'
Assert-True ([int]$matrix.checkpoint -eq 103 -and [string]$matrix.authority.concept -eq 'docs/Star_Cluster_Game_Concept_v0.7d.docx' -and [string]$matrix.integrationArchitecture.standingPermutationSuite -eq 'docs/design/testing/technology_integration_permutation_suite_v0_18.json' -and [bool]$matrix.integrationArchitecture.cp102NativeAccepted -and -not [bool]$matrix.integrationArchitecture.cp103AutomaticPromotion) 'Technology Matrix CP103 integration lifecycle drifted.'
$guidelines=Read-Text 'docs/development/Simulation_Development_Guidelines.md'
foreach($needle in @('Classify Space utilization relative to the selected Hull capacity','Do not overweight tactically isomorphic labels','Separate population inference from legacy/all-tier diagnostic overlays','Frontier counts are stratifiers, not scores','Adaptive cell budgets must be independently feasible before release','Absent catalog placeholders do not raise a build''s executable Technology Level')){ Require-Contains $guidelines $needle "Durable CP103 methodology is missing '$needle'." }
$validationPolicy=Read-Json 'docs/design/testing/checkpoint_103_validation_suite_policy_v0_1.json'
Assert-True ([string]$validationPolicy.researchSimulation.windowsPowerShellBootstrapProbe -eq '--version' -and -not [bool]$validationPolicy.researchSimulation.inlinePythonBootstrapAllowed) 'CP103 validation policy must preserve the Windows PowerShell 5.1-safe Python bootstrap rule.'
Assert-ExactFileSet 'docs/design/testing' @('README.md','Checkpoint_103_Validation_Tiers.md','checkpoint_103_validation_suite_policy_v0_1.json','Technology_Integration_Permutation_Suite_Architecture_v0_18.md','technology_integration_permutation_suite_v0_18.json')
Assert-ExactFileSet 'docs/validation' @('README.md','Checkpoint_103_TL1_TL2_TL3_Integration_Permutation_Analysis.md')
$activeConcepts=@(Get-ChildItem -LiteralPath (RelPath 'docs') -File -Filter 'Star_Cluster_Game_Concept*.docx'|ForEach-Object Name); Assert-True ($activeConcepts.Count -eq 1 -and $activeConcepts[0] -eq 'Star_Cluster_Game_Concept_v0.7d.docx') 'Exactly Concept v0.7d must remain active; CP103 changes no Concept rule/value.'
foreach($p in @('README.md','CHAT_README.md','docs/README.md','docs/design/README.md','docs/design/player_technology/README.md','docs/design/testing/README.md','docs/validation/README.md','docs/Prototype_TODO.md','docs/design/player_technology/Technology_Architecture_Matrix_v1.md','docs/design/testing/Technology_Integration_Permutation_Suite_Architecture_v0_18.md','docs/validation/Checkpoint_103_TL1_TL2_TL3_Integration_Permutation_Analysis.md')){
    $text=Read-Text $p; Assert-True ($text.IndexOf('CP101 is the latest native-accepted',[StringComparison]::OrdinalIgnoreCase) -lt 0) "Active document '$p' retains stale CP101 acceptance authority."
}

Write-Host '       Validating final repository manifest and RepositoryOnly-to-full-run sequence safety...'
$manifest=Read-Manifest 'CHECKPOINT_103_SHA256SUMS.txt'; $actual=Get-Cp103RepositoryOwnedFileSet
Assert-True ($actual.Count -eq $manifest.EntryCount) "CP103 manifest entry count $($manifest.EntryCount) does not match repository-owned file count $($actual.Count)."
foreach($rel in $manifest.Entries.Keys){ Assert-True ($actual.ContainsKey([string]$rel)) "CP103 manifest lists missing/unowned path '$rel'."; Assert-True ((Hash-Rel ([string]$rel)) -eq [string]$manifest.Entries[[string]$rel]) "CP103 manifest hash mismatch for '$rel'." }
foreach($rel in $actual.Keys){ Assert-True ($manifest.Entries.ContainsKey([string]$rel)) "Repository-owned path '$rel' is missing from CP103 manifest." }
Assert-True (-not $manifest.Entries.ContainsKey('CHECKPOINT_102_SHA256SUMS.txt')) 'Superseded CP102 root manifest must not remain repository-owned in CP103.'
Assert-Cp103GeneratedArtifactSequencePreflight -Expected $actual

Write-Host "       CP103 contract verified: $($manifest.EntryCount) repository-owned files; accepted CP102 provenance preserved; v8 primary 921,600 raw / 164,160 legal / 96 population cells / 1,152 variants; legacy overlay 33 recipes / 28 unique builds / 100 variants; 313,000 substantive trials; zero automatic promotion."
