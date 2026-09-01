Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path

function Assert-True([bool]$Condition, [string]$Message) {
    if (-not $Condition) { throw $Message }
}

function Get-RequiredParameterRow($Rows, [string]$ParameterId) {
    $matches = @($Rows | Where-Object {
        $_.PSObject.Properties.Name -contains 'parameter_id' -and
        [string]$_.parameter_id -eq $ParameterId
    })
    Assert-True ($matches.Count -eq 1) "Numerical baseline requires exactly one '$ParameterId' row; found $($matches.Count)."
    return $matches[0]
}

function Get-Hash([string]$RelativePath) {
    $path = Join-Path $repositoryRoot $RelativePath
    Assert-True (Test-Path -LiteralPath $path -PathType Leaf) "Missing required file $RelativePath."
    return (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
}

$guard = Join-Path $repositoryRoot 'tools\checkpoints\Test-NativeAcceptanceDependencies.ps1'
$normalRel = 'tools/calibration/checkpoints/checkpoint-67a.json'
$deepRel = 'tools/calibration/checkpoints/checkpoint-67a-deep-calibration.json'
$powerShellPaths = @(
    'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
    'tools/checkpoints/checkpoint-67a/apply_checkpoint_67a.ps1',
    'tools/checkpoints/checkpoint-67a/test_checkpoint_67a_contract.ps1',
    'tools/calibration/run_calibration_checkpoint.ps1'
)
& $guard -RepositoryRoot $repositoryRoot -PowerShellPaths $powerShellPaths -CheckpointDefinitionPaths @($normalRel,$deepRel)

$normal = Get-Content -LiteralPath (Join-Path $repositoryRoot $normalRel) -Raw | ConvertFrom-Json
$deep = Get-Content -LiteralPath (Join-Path $repositoryRoot $deepRel) -Raw | ConvertFrom-Json
$policy = Get-Content -LiteralPath (Join-Path $repositoryRoot 'docs/design/testing/checkpoint_67_validation_suite_policy_v0_1.json') -Raw | ConvertFrom-Json
$study = Get-Content -LiteralPath (Join-Path $repositoryRoot 'src/StarCluster.ScenarioRunner/Scenarios/TL1Calibration/tl1-itc10-bilateral-overload-ew-counterplay.json') -Raw | ConvertFrom-Json
$schema = Get-Content -LiteralPath (Join-Path $repositoryRoot 'docs/design/player_technology/tl1_integrated_tactical_combat_schema_v0_13.json') -Raw | ConvertFrom-Json
$cruiserBaseline = Get-Content -LiteralPath (Join-Path $repositoryRoot 'docs/archive/player_technology/pre-cp165-active/tl1_35_space_player_cruiser_baseline_v0_9.json') -Raw | ConvertFrom-Json

# Checkpoint identity / workload / native dependency contract.
Assert-True ([string]$normal.checkpointId -eq '67a' -and [string]$deep.checkpointId -eq '67a') 'Checkpoint definitions must identify 67a.'
Assert-True ([string]$normal.manifestFile -eq 'CHECKPOINT_67A_SHA256SUMS.txt' -and [string]$deep.manifestFile -eq 'CHECKPOINT_67A_SHA256SUMS.txt') 'Checkpoint 67a manifest binding mismatch.'
Assert-True ([string]$normal.outputRoot -eq 'out/checkpoint-67a' -and [string]$deep.outputRoot -eq 'out/checkpoint-67a-deep-calibration') 'Checkpoint 67a output roots mismatch.'
Assert-True ([int]$normal.checkpointMetrics.stageCount -eq 8 -and [int]$normal.checkpointMetrics.monteCarloVariantCount -eq 60 -and [int]$normal.checkpointMetrics.trialsAtDefault -eq 600000) 'Checkpoint 67a normal workload mismatch.'
Assert-True ([int]$deep.checkpointMetrics.stageCount -eq 26 -and [int]$deep.checkpointMetrics.monteCarloVariantCount -eq 1544 -and [int]$deep.checkpointMetrics.trialsAtDefault -eq 15440000) 'Checkpoint 67a Deep workload mismatch.'
Assert-True ([string]$normal.primaryStudy.id -eq 'tl1-bilateral-overload-ew-counterplay' -and [int]$normal.primaryStudy.variantCount -eq 60) 'Checkpoint 67a normal primaryStudy metadata mismatch.'
Assert-True ([string]$deep.primaryStudy.id -eq 'tl1-bilateral-overload-ew-counterplay' -and [int]$deep.primaryStudy.variantCount -eq 60) 'Checkpoint 67a Deep primaryStudy metadata mismatch.'
Assert-True (@($policy.mustAlwaysRunStageIds).Count -eq 8 -and @($policy.deepCalibrationStageIds).Count -eq 18) 'Checkpoint 67a validation-tier policy count mismatch.'
$normalMcStages = @($normal.stages | Where-Object { $_.metrics.PSObject.Properties.Name -contains 'usesTrials' -and [bool]$_.metrics.usesTrials })
$deepMcStages = @($deep.stages | Where-Object { $_.metrics.PSObject.Properties.Name -contains 'usesTrials' -and [bool]$_.metrics.usesTrials })
Assert-True (($normalMcStages | ForEach-Object { [int]$_.metrics.variantCount } | Measure-Object -Sum).Sum -eq 60) 'Checkpoint 67a normal Monte Carlo stage total must recompute to 60 variants.'
Assert-True (($deepMcStages | ForEach-Object { [int]$_.metrics.variantCount } | Measure-Object -Sum).Sum -eq 1544) 'Checkpoint 67a Deep Monte Carlo stage total must recompute to 1,544 variants.'
$normalPrimaryStage = @($normal.stages | Where-Object { [string]$_.id -eq 'tl1-bilateral-overload-ew-counterplay' })
$deepPrimaryStage = @($deep.stages | Where-Object { [string]$_.id -eq 'tl1-bilateral-overload-ew-counterplay' })
Assert-True ($normalPrimaryStage.Count -eq 1 -and $deepPrimaryStage.Count -eq 1) 'Checkpoint 67a primary study stage must exist exactly once in normal and Deep definitions.'
$expectedStudyRel = 'src/StarCluster.ScenarioRunner/Scenarios/TL1Calibration/tl1-itc10-bilateral-overload-ew-counterplay.json'
$expectedBaselineRel = 'docs/archive/player_technology/pre-cp165-active/tl1_core_combat_numerical_baseline_v0_3.csv'
foreach ($stage in @($normalPrimaryStage[0],$deepPrimaryStage[0])) {
    $args = @($stage.arguments)
    $studyArg = [Array]::IndexOf($args, '--study-file')
    $baselineArg = [Array]::IndexOf($args, '--baseline-file')
    Assert-True ($studyArg -ge 0 -and $studyArg + 1 -lt $args.Count -and [string]$args[$studyArg + 1] -eq $expectedStudyRel) 'Checkpoint 67a stage must bind the exact CP67 study file.'
    Assert-True ($baselineArg -ge 0 -and $baselineArg + 1 -lt $args.Count -and [string]$args[$baselineArg + 1] -eq $expectedBaselineRel) 'Checkpoint 67a stage must bind the exact v0.3 numerical baseline.'
    Assert-True ([int]$stage.metrics.variantCount -eq 60 -and [int]$stage.metrics.startingFuel -eq 100) 'Checkpoint 67a stage metrics must retain 60 variants and the 100-fuel baseline.'
}
foreach ($definition in @($normal,$deep)) {
    $pre = $definition.nativeDependencyPrecheck
    Assert-True ([bool]$pre.required -and [string]$pre.script -eq 'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1') 'Checkpoint 67a must require the shared no-Python dependency precheck.'
    Assert-True (@($pre.powerShellPaths) -contains 'tools/checkpoints/checkpoint-67a/apply_checkpoint_67a.ps1' -and @($pre.powerShellPaths) -contains 'tools/checkpoints/checkpoint-67a/test_checkpoint_67a_contract.ps1' -and @($pre.powerShellPaths) -contains 'tools/calibration/run_calibration_checkpoint.ps1') 'Checkpoint 67a dependency precheck path coverage mismatch.'
}

# New authoritative numeric baseline: only fuel capacity changes from v0.2.
$numericPath = Join-Path $repositoryRoot 'docs/archive/player_technology/pre-cp165-active/tl1_core_combat_numerical_baseline_v0_3.csv'
$numericRows = @(Import-Csv -LiteralPath $numericPath)
Assert-True ($numericRows.Count -gt 0) 'Numerical baseline v0.3 must contain rows.'
$numericColumns = @($numericRows[0].PSObject.Properties.Name)
Assert-True ($numericColumns -contains 'parameter_id' -and $numericColumns -contains 'value') 'Numerical baseline v0.3 must expose parameter_id/value columns.'
Assert-True ([int](Get-RequiredParameterRow $numericRows 'fuel_capacity').value -eq 100) 'Authoritative Checkpoint 67a fuel capacity must be 100.'
Assert-True ([int](Get-RequiredParameterRow $numericRows 'stl_fuel_per_hex').value -eq 2) 'Movement fuel cost must remain 2 per traversed hex.'
Assert-True ([int](Get-RequiredParameterRow $numericRows 'evasive_flat_fuel_cost').value -eq 1) 'EvM fuel cost must remain flat +1.'
Assert-True ([int](Get-RequiredParameterRow $numericRows 'stl_overload_extra_fuel').value -eq 2) 'TL1 STL overload extra fuel must remain +2.'
Assert-True ((Get-Hash 'docs/archive/player_technology/pre-cp165-active/tl1_core_combat_numerical_baseline_v0_3.csv') -eq 'd3020245a1fe2d28f6795c96c3c331d905ed02ef5210f3ab661e3475f70cf5be') 'Numerical baseline v0.3 hash drifted after study binding.'
Assert-True ([string]$study.baselineSha256 -eq 'd3020245a1fe2d28f6795c96c3c331d905ed02ef5210f3ab661e3475f70cf5be') 'Checkpoint 67a study must bind numerical baseline v0.3 exactly.'

# Historical CP66d inputs remain frozen.
Assert-True ((Get-Hash 'docs/archive/Star_Cluster_Game_Concept_v0.6e.docx') -eq '5024b1cf65e176139496e4d05ded83963646f6c807155edf4ed83bba5bb1ca56') 'Archived Concept v0.6e drifted.'
Assert-True ((Get-Hash 'docs/design/player_technology/tl1_integrated_tactical_combat_schema_v0_12.json') -eq '16270a40c378f3f9315a88bfd65e5c0a0362081e70039ed5d2297f1c6a7fe1f1') 'Historical schema v0.12 drifted.'
Assert-True ((Get-Hash 'docs/archive/player_technology/pre-cp165-active/tl1_core_combat_numerical_baseline_v0_2.csv') -eq '44b167ddb4aca9737658f7bd8d5a0bc5d3506e8ac1129142241714ec59645eb5') 'Historical numerical baseline v0.2 drifted.'
Assert-True ((Get-Hash 'src/StarCluster.ScenarioRunner/Scenarios/TL1Calibration/tl1-itc09-scripted-overload-tactics.json') -eq '402687e896f261422a11a3214b0ba35e7bbb72221f78a86d5266dd257f0e10d8') 'Historical CP66d overload study drifted.'

# Study/schema/build matrix.
Assert-True ([string]$schema.'$id' -eq 'star-cluster-tl1-integrated-tactical-combat-schema-v0-13') 'Schema v0.13 identity mismatch.'
Assert-True ([string]$study.id -eq 'tl1-itc10-bilateral-overload-ew-counterplay' -and @($study.variants).Count -eq 60) 'Checkpoint 67a study identity/count mismatch.'
Assert-True (@($study.variants | Select-Object -ExpandProperty id -Unique).Count -eq 60) 'Checkpoint 67a variant IDs must be unique.'
Assert-True (@($study.builds).Count -eq 2) 'Checkpoint 67a requires exactly two construction fixtures.'
$baseBuild = @($study.builds | Where-Object { $_.id -eq 'balanced_generalist_major' })
$ewBuild = @($study.builds | Where-Object { $_.id -eq 'balanced_generalist_ew_major' })
Assert-True ($baseBuild.Count -eq 1 -and [int]$baseBuild[0].usedSpace -eq 33 -and [int]$baseBuild[0].freeSupportSpace -eq 2 -and -not [bool]$baseBuild[0].ecmSuite -and -not [bool]$baseBuild[0].eccmSuite) '33-Space balanced-generalist fixture mismatch.'
Assert-True ($ewBuild.Count -eq 1 -and [int]$ewBuild[0].usedSpace -eq 35 -and [int]$ewBuild[0].freeSupportSpace -eq 0 -and [bool]$ewBuild[0].ecmSuite -and [bool]$ewBuild[0].eccmSuite) '35-Space explicit EW fixture mismatch.'
Assert-True (@($study.variants | Where-Object { [int]$_.startingFuel -ne 100 -or [int]$_.movementFuelPerHex -ne 2 -or [int]$_.evasiveManeuverFuelCost -ne 1 }).Count -eq 0) 'Every CP67 variant must use 100/2/+1 fuel controls.'
Assert-True (@($study.variants | Where-Object { [string]$_.sideAProfileId -ne 'tl1-production' -or [string]$_.sideBProfileId -ne 'tl1-production' }).Count -eq 0) 'Checkpoint 67a must use tl1-production on both sides.'
Assert-True (-not ($study.PSObject.Properties.Name -contains 'technologyProfileCatalog')) 'Checkpoint 67a must not reintroduce the stale historical technology-profile catalog binding.'
$stlVariants = @($study.variants | Where-Object { [string]$_.sideABuildId -eq 'balanced_generalist_major' })
$ewVariants = @($study.variants | Where-Object { [string]$_.sideABuildId -eq 'balanced_generalist_ew_major' })
Assert-True ($stlVariants.Count -eq 48 -and $ewVariants.Count -eq 12) 'Checkpoint 67a 48+12 study split mismatch.'
Assert-True (@($stlVariants | Group-Object comparisonGroup).Count -eq 12 -and @($stlVariants | Group-Object comparisonGroup | Where-Object { $_.Count -ne 4 }).Count -eq 0) 'Bilateral STL lanes must be 12 paired groups of four.'
Assert-True (@($ewVariants | Group-Object comparisonGroup).Count -eq 2 -and @($ewVariants | Group-Object comparisonGroup | Where-Object { $_.Count -ne 6 }).Count -eq 0) 'Post-Movement EW lanes must be two paired groups of six.'
$auxCatalogRel = [string]$study.auxiliaryProfileCatalog
Assert-True (-not [string]::IsNullOrWhiteSpace($auxCatalogRel)) 'Checkpoint 67a study must name its auxiliary runtime-profile catalog.'
$auxCatalogPath = Join-Path $repositoryRoot $auxCatalogRel
Assert-True (Test-Path -LiteralPath $auxCatalogPath -PathType Leaf) 'Checkpoint 67a auxiliary runtime-profile catalog is missing.'
$auxCatalog = Get-Content -LiteralPath $auxCatalogPath -Raw | ConvertFrom-Json
$availableAuxIds = @($auxCatalog.profiles | Select-Object -ExpandProperty id -Unique)
$referencedAuxIds = @($study.variants | ForEach-Object { [string]$_.sideAAuxiliaryProfileId; [string]$_.sideBAuxiliaryProfileId } | Sort-Object -Unique)
Assert-True ($referencedAuxIds.Count -gt 0 -and @($referencedAuxIds | Where-Object { $availableAuxIds -notcontains $_ }).Count -eq 0) 'Every CP67 referenced AUX runtime profile must exist in the bound catalog.'

# Baseline/reference document records the new authoritative fuel and study.
Assert-True ([int]$cruiserBaseline.checkpoint -eq 67 -and [int]$cruiserBaseline.authoritativeTacticalFuel.startingFuel -eq 100) 'Player-cruiser baseline v0.9 must make 100 fuel authoritative.'
Assert-True ([int]$cruiserBaseline.bilateralOverloadEwCounterplayStudy.variantCount -eq 60 -and [bool]$cruiserBaseline.bilateralOverloadEwCounterplayStudy.fullTacticalAiDeferred) 'Player-cruiser baseline v0.9 CP67 study record mismatch.'

# Cross-study integration audit. Every material runner surface must recognize the new study.
$runner = Get-Content -LiteralPath (Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\TL1Calibration\Tl1IntegratedTacticalCombatRunner.cs') -Raw
$documents = Get-Content -LiteralPath (Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\TL1Calibration\Tl1IntegratedTacticalCombatDocuments.cs') -Raw
$requiredRunnerFragments = @(
    'Tl1BilateralOverloadCounterplayStudyId => RequiredTl1BilateralOverloadCounterplayVariantCount',
    'studyId == Tl1BilateralOverloadCounterplayStudyId',
    'ValidateTl1BilateralOverloadCounterplayCoverage(',
    'if (study.Id == Tl1BilateralOverloadCounterplayStudyId)',
    'WriteTl1BilateralOverloadCounterplayReview(study, results, outputDirectory);',
    '"tl1-c67-variant-coverage"',
    '"tl1-c67-post-movement-ew-exercised"',
    '"tl1-c67-denial-telemetry-accounting"',
    'AllocateOperationalEw(',
    'RecordSensorOverloadPlanningOpportunity(',
    'MeanOverloadDeniedPowerA'
)
foreach ($fragment in $requiredRunnerFragments) {
    Assert-True ($runner.Contains($fragment)) "Checkpoint 67a cross-study integration missing runner fragment: $fragment"
}
Assert-True ($documents.Contains('Tl1IntegratedEwPowerPolicy') -and $documents.Contains('EcmSuite') -and $documents.Contains('EccmSuite') -and $documents.Contains('SideAEcmPolicy') -and $documents.Contains('SideAEccmPolicy')) 'Integrated document model missing CP67 EW controls.'
$policyGateStart = $runner.IndexOf('"policy-telemetry"', [StringComparison]::Ordinal)
$policyGateEnd = $runner.IndexOf('"attack-layer-telemetry"', [StringComparison]::Ordinal)
Assert-True ($policyGateStart -ge 0 -and $policyGateEnd -gt $policyGateStart) 'Unable to isolate shared policy-telemetry gate.'
$policyGateText = $runner.Substring($policyGateStart, $policyGateEnd - $policyGateStart)
Assert-True (([regex]::Matches($policyGateText, 'Tl1BilateralOverloadCounterplayStudyId')).Count -ge 2) 'CP67 must be classified in both branches of the shared policy-telemetry gate.'
$validateStart = $runner.IndexOf('private static void Validate(', [StringComparison]::Ordinal)
$validateEnd = $runner.IndexOf('private static void ValidateTl2CandidateCoverage(', [StringComparison]::Ordinal)
$buildGatesStart = $runner.IndexOf('private static IReadOnlyList<Tl1IntegratedTacticalCombatGate> BuildGates(', [StringComparison]::Ordinal)
$buildGatesEnd = $runner.IndexOf('private static bool IsFixedRange(', [StringComparison]::Ordinal)
Assert-True ($validateStart -ge 0 -and $validateEnd -gt $validateStart -and $buildGatesStart -ge 0 -and $buildGatesEnd -gt $buildGatesStart) 'Unable to isolate runner Validate/BuildGates source spans.'
$validateText = $runner.Substring($validateStart, $validateEnd - $validateStart)
$buildGatesText = $runner.Substring($buildGatesStart, $buildGatesEnd - $buildGatesStart)
Assert-True ($validateText.Contains('ValidateTl1BilateralOverloadCounterplayCoverage(')) 'CP67 pre-run Validate path must dispatch the CP67 coverage validator.'
Assert-True (-not $validateText.Contains('"tl1-c67-variant-coverage"') -and -not $validateText.Contains('"tl1-c67-post-movement-ew-exercised"')) 'Result-dependent CP67 release gates must not be placed in the pre-run Validate scope.'
Assert-True ($buildGatesText.Contains('"tl1-c67-variant-coverage"') -and $buildGatesText.Contains('"tl1-c67-post-movement-ew-exercised"') -and $buildGatesText.Contains('"tl1-c67-denial-telemetry-accounting"')) 'CP67 result-dependent release gates must live inside BuildGates.'

# Guard startup order and StrictMode-safe contract behavior.
$applySource = Get-Content -LiteralPath (Join-Path $repositoryRoot 'tools\checkpoints\checkpoint-67a\apply_checkpoint_67a.ps1') -Raw
$guardCallIndex = $applySource.IndexOf('& $dependencyGuard')
$contractCallIndex = $applySource.LastIndexOf('& $contractCheck')
$harnessCallIndex = $applySource.LastIndexOf('& $harness')
Assert-True ($guardCallIndex -ge 0 -and $guardCallIndex -lt $contractCallIndex -and $contractCallIndex -lt $harnessCallIndex) 'Checkpoint 67a apply script must run dependency guard before contract and harness.'
Assert-True ($applySource -notmatch '\$LASTEXITCODE') 'Checkpoint 67a apply script must not read LASTEXITCODE.'
$harnessSource = Get-Content -LiteralPath (Join-Path $repositoryRoot 'tools\calibration\run_calibration_checkpoint.ps1') -Raw
Assert-True ($harnessSource -match 'Invoke-RequiredNativeDependencyPrecheck' -and $harnessSource -match '\$checkpointNumber -lt 66') 'Shared harness must continue enforcing the native dependency precheck for CP66+.'

# Active validation/archive hygiene.
$validationFiles = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs\validation') -File -Filter 'Checkpoint_*.md')
Assert-True ($validationFiles.Count -eq 1 -and $validationFiles[0].Name -eq 'Checkpoint_67a_EW_Strain_Ref_Compile_Hotfix.md') 'Exactly one Checkpoint 67a active validation runbook must remain.'
$rootTxt = @(Get-ChildItem -LiteralPath $repositoryRoot -File -Filter '*.txt')
Assert-True ($rootTxt.Count -eq 1 -and $rootTxt[0].Name -eq 'CHECKPOINT_67A_SHA256SUMS.txt') 'Repository root must contain only CHECKPOINT_67A_SHA256SUMS.txt as .txt.'
$archivedTxt = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs\archive') -Recurse -File -Filter '*.txt')
Assert-True ($archivedTxt.Count -eq 0) 'Generated historical checkpoint .txt artifacts must not remain under docs/archive.'

# CP67a compile regression: ordinary properties may not be passed by ref/out.
$runnerSource = Get-Content -LiteralPath (Join-Path $repositoryRoot 'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs') -Raw
Assert-True ($runnerSource -notmatch '\b(?:ref|out)\s+side\.(?:EcmStrain|EccmStrain)\b') 'CP67a compile regression: IntegratedSide EW Strain properties must not be passed by ref/out.'
Assert-True ($runnerSource.Contains('int ecmStrain = side.EcmStrain;') -and $runnerSource.Contains('ref ecmStrain') -and $runnerSource.Contains('side.EcmStrain = ecmStrain;')) 'CP67a compile regression: ECM Strain must be copied to a local ref variable and assigned back.'
Assert-True ($runnerSource.Contains('int eccmStrain = side.EccmStrain;') -and $runnerSource.Contains('ref eccmStrain') -and $runnerSource.Contains('side.EccmStrain = eccmStrain;')) 'CP67a compile regression: ECCM Strain must be copied to a local ref variable and assigned back.'

Write-Host '       Checkpoint 67a native dependency contract: PowerShell + pinned .NET only; active Python runtime dependencies are rejected before native work.'
Write-Host '       Fuel baseline: 100 start / 2 per traversed hex / EvM +1; existing overload fuel costs unchanged.'
Write-Host '       Bilateral STL precommit: 48 variants; post-Movement sensor/ECM/ECCM counterplay: 12 variants.'
Write-Host '       Existing TP windows and safe-only Strain policy remain authoritative; full tactical AI and overload-damage integration remain deferred.'
Write-Host '       Cross-study runner registration, policy telemetry, report routing, schema/baseline bindings, and historical CP66d hashes are preflighted.'
Write-Host '       Validation tiers: 8 normal stages / 60 MC variants; Deep Calibration 26 stages / 1,544 MC variants.'
Write-Host 'Checkpoint 67a compile-hotfix contract validation passed.'
