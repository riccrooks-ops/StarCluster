[CmdletBinding()]
param()

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
function Assert-True {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) { throw $Message }
}

$guard = Join-Path $repositoryRoot 'tools\checkpoints\Test-NativeAcceptanceDependencies.ps1'
$normalRel = 'tools/calibration/checkpoints/checkpoint-69c.json'
$deepRel = 'tools/calibration/checkpoints/checkpoint-69c-deep-calibration.json'
$guardedPs = @(
    'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
    'tools/checkpoints/checkpoint-69c/apply_checkpoint_69c.ps1',
    'tools/checkpoints/checkpoint-69c/test_checkpoint_69c_contract.ps1',
    'tools/calibration/run_calibration_checkpoint.ps1'
)
& $guard -RepositoryRoot $repositoryRoot -PowerShellPaths $guardedPs -CheckpointDefinitionPaths @($normalRel, $deepRel)

$normal = Get-Content -LiteralPath (Join-Path $repositoryRoot $normalRel) -Raw | ConvertFrom-Json
$deep = Get-Content -LiteralPath (Join-Path $repositoryRoot $deepRel) -Raw | ConvertFrom-Json
Assert-True ([string]$normal.checkpointId -eq '69c') 'Checkpoint 69c normal definition ID mismatch.'
Assert-True ([string]$deep.checkpointId -eq '69c') 'Checkpoint 69c deep definition ID mismatch.'
Assert-True ([string]$normal.manifestFile -eq 'CHECKPOINT_69C_SHA256SUMS.txt') 'Checkpoint 69c normal manifest binding mismatch.'
Assert-True ([string]$deep.manifestFile -eq 'CHECKPOINT_69C_SHA256SUMS.txt') 'Checkpoint 69c deep manifest binding mismatch.'
Assert-True ([string]$normal.outputRoot -eq 'out/checkpoint-69c') 'Checkpoint 69c normal output root mismatch.'
Assert-True ([string]$deep.outputRoot -eq 'out/checkpoint-69c-deep-calibration') 'Checkpoint 69c deep output root mismatch.'
$expectedGuardedPs = @(
    'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
    'tools/checkpoints/checkpoint-69c/apply_checkpoint_69c.ps1',
    'tools/checkpoints/checkpoint-69c/test_checkpoint_69c_contract.ps1',
    'tools/calibration/run_calibration_checkpoint.ps1'
)
$expectedGuardedDefs = @($normalRel, $deepRel)
foreach ($definitionDocument in @($normal, $deep)) {
    Assert-True ([bool]$definitionDocument.nativeDependencyPrecheck.required) 'Checkpoint 69c definitions must require the native dependency precheck.'
    Assert-True ((@($definitionDocument.nativeDependencyPrecheck.powerShellPaths) -join '|') -eq ($expectedGuardedPs -join '|')) 'Checkpoint 69c native dependency PowerShell path binding mismatch.'
    Assert-True ((@($definitionDocument.nativeDependencyPrecheck.checkpointDefinitionPaths) -join '|') -eq ($expectedGuardedDefs -join '|')) 'Checkpoint 69c native dependency definition binding mismatch.'
}
Assert-True (@($normal.stages).Count -eq 11) 'Checkpoint 69c normal suite must contain 11 stages.'
Assert-True (@($deep.stages).Count -eq 30) 'Checkpoint 69c Deep Calibration must contain 30 stages.'
Assert-True ([int]$normal.checkpointMetrics.monteCarloVariantCount -eq 72 -and [int]$normal.checkpointMetrics.trialsAtDefault -eq 720000 -and [int]$normal.checkpointMetrics.smokeTrialsAtDefault -eq 72 -and [int]$normal.checkpointMetrics.totalTrialExecutionsAtDefault -eq 720072) 'Checkpoint 69c normal Monte Carlo/smoke workload mismatch.'
Assert-True ([int]$deep.checkpointMetrics.monteCarloVariantCount -eq 1616 -and [int]$deep.checkpointMetrics.trialsAtDefault -eq 16160000 -and [int]$deep.checkpointMetrics.smokeTrialsAtDefault -eq 72 -and [int]$deep.checkpointMetrics.totalTrialExecutionsAtDefault -eq 16160072) 'Checkpoint 69c Deep Calibration workload mismatch.'

$policyPath = Join-Path $repositoryRoot 'docs\design\testing\checkpoint_69_validation_suite_policy_v0_1.json'
$policy = Get-Content -LiteralPath $policyPath -Raw | ConvertFrom-Json
Assert-True ([int]$policy.normal.stageCount -eq 11 -and [int]$policy.normal.smokeTrials -eq 72 -and [int]$policy.normal.totalTrialExecutions -eq 720072) 'Checkpoint 69c validation policy normal-stage/smoke metadata mismatch.'
Assert-True ([int]$policy.deepCalibration.stageCount -eq 30 -and [int]$policy.deepCalibration.smokeTrials -eq 72 -and [int]$policy.deepCalibration.totalTrialExecutions -eq 16160072) 'Checkpoint 69c validation policy Deep Calibration metadata mismatch.'
$mustAlways = @($policy.mustAlwaysRunStageIds)
Assert-True ($mustAlways -contains 'tl1-sensor-ew-candidate-operational-preflight' -and $mustAlways -contains 'tl1-sensor-ew-candidate-operational-smoke' -and $mustAlways -contains 'tl1-sensor-ew-candidate-operational-combat') 'Checkpoint 69c validation policy must require candidate preflight, smoke, and substantive combat stages.'

$normalSensorStage = @($normal.stages | Where-Object { [string]$_.id -eq 'tl1-sensor-ew-foundation' })
$normalCombatStage = @($normal.stages | Where-Object { [string]$_.id -eq 'tl1-sensor-ew-candidate-operational-combat' })
Assert-True ($normalSensorStage.Count -eq 1 -and $normalCombatStage.Count -eq 1) 'Checkpoint 69 normal suite must contain one deterministic Sensor/EW stage and one operational candidate combat stage.'
Assert-True ([int]$normalSensorStage[0].metrics.profileCount -eq 7 -and [int]$normalSensorStage[0].metrics.deterministicRowCount -eq 924) 'Checkpoint 69 deterministic Sensor/EW matrix mismatch.'
Assert-True ([bool]$normalSensorStage[0].metrics.sameHexLosUnoccludable -and [bool]$normalSensorStage[0].metrics.sameHexEwStillResolves) 'Checkpoint 69 same-hex Sensor/EW metrics are not bound.'
Assert-True ([int]$normalCombatStage[0].metrics.variantCount -eq 72 -and [int]$normalCombatStage[0].metrics.candidateCount -eq 3) 'Checkpoint 69 operational candidate stage matrix mismatch.'
Assert-True (-not [bool]$normalCombatStage[0].metrics.balanceTargetsBlocking) 'Checkpoint 69 candidate combat outcomes must remain diagnostic rather than target-win release gates.'

$studyPath = Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\Scenarios\SensorEw\tl1-sew02-sensor-ew-foundation-range-sweep.json'
$study = Get-Content -LiteralPath $studyPath -Raw | ConvertFrom-Json
Assert-True ([string]$study.schemaVersion -eq 'star-cluster-tl1-sensor-ew-foundation-v1') 'Checkpoint 69 Sensor/EW schema version mismatch.'
Assert-True ([string]$study.id -eq 'tl1-sew02-sensor-ew-foundation-range-sweep') 'Checkpoint 69 Sensor/EW study ID mismatch.'
Assert-True ([int]$study.checkpoint -eq 69 -and [int]$study.maxTacticalSeparationHexes -eq 10) 'Checkpoint 69 Sensor/EW map/range identity mismatch.'
Assert-True (@($study.candidates).Count -eq 7) 'Checkpoint 69 Sensor/EW study must contain one historical control and six forward candidates.'
$forward = @($study.candidates | Where-Object { -not [bool]$_.isHistoricalControl })
Assert-True ($forward.Count -eq 6) 'Checkpoint 69 must contain six forward TL1 sensor candidates.'
Assert-True (@($forward | Where-Object { [int]$_.activePowerCost -ne 1 -or [int]$_.activeOverloadAdditionalPowerCost -ne 1 }).Count -eq 0) 'Forward TL1 candidates must use one 1-TP normal Active mode plus one +1-TP overload.'
$balanced0 = @($study.candidates | Where-Object { [string]$_.id -eq 'balanced-0' })
Assert-True ($balanced0.Count -eq 1) 'Checkpoint 69 must contain exactly one balanced-0 candidate.'
Assert-True ([int]$balanced0[0].passiveFirmRange -eq 1 -and [int]$balanced0[0].passiveApproximateRange -eq 3 -and [int]$balanced0[0].activeFirmRange -eq 3 -and [int]$balanced0[0].activeApproximateRange -eq 4 -and [int]$balanced0[0].activeOverloadFirmBonus -eq 1 -and [int]$balanced0[0].activeOverloadApproximateBonus -eq 1) 'Balanced-0 must remain Passive 1/3, Active 3/4, Overload 4/5.'

$historicalStudyPath = Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\Scenarios\SensorEw\tl1-sew01-sensor-ew-foundation-range-sweep.json'
$historicalHash = (Get-FileHash -LiteralPath $historicalStudyPath -Algorithm SHA256).Hash.ToLowerInvariant()
Assert-True ($historicalHash -eq '986b07d7408883aae7d41c8405a212499023a578b897d4408b9b544af8054b53') 'Checkpoint 68 Sensor/EW study must remain byte-for-byte frozen historical evidence.'

$combatPath = Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\Scenarios\TL1Calibration\tl1-itc11-sensor-ew-candidate-operational-combat.json'
$combat = Get-Content -LiteralPath $combatPath -Raw | ConvertFrom-Json
Assert-True ([string]$combat.id -eq 'tl1-itc11-sensor-ew-candidate-operational-combat') 'Checkpoint 69 operational Sensor/EW study ID mismatch.'
Assert-True ([int]$combat.trialsPerVariant -eq 10000 -and @($combat.variants).Count -eq 72) 'Checkpoint 69 operational Sensor/EW study must define 72 variants at 10,000 trials each by default.'
Assert-True ([string]$combat.sensorEwProfileCatalog -eq 'src/StarCluster.ScenarioRunner/Scenarios/SensorEw/tl1-sew02-sensor-ew-foundation-range-sweep.json') 'Checkpoint 69 operational study must bind the CP69 Sensor/EW profile catalog.'
Assert-True (@($combat.builds).Count -eq 1 -and [string]$combat.builds[0].id -eq 'balanced_generalist_ew_major' -and [int]$combat.builds[0].usedSpace -eq 35) 'Checkpoint 69 operational study must hold the accepted 35-Space EW-capable build fixed.'
foreach ($profileId in @('balanced-0','balanced-1','balanced-2')) {
    Assert-True (@($combat.variants | Where-Object { [string]$_.sensorEwProfileId -eq $profileId }).Count -eq 24) "Checkpoint 69 profile $profileId must have exactly 24 variants."
}
Assert-True (@($combat.variants | Where-Object { [int]$_.startingFuel -ne 100 -or [int]$_.sideAReactorOutputOverride -ne 5 -or [int]$_.sideBReactorOutputOverride -ne 5 }).Count -eq 0) 'Checkpoint 69 operational study must preserve 100 fuel and 5-TP reactor controls.'
Assert-True (@($combat.variants | Where-Object { [int]$_.sideANetEwRangePenalty -ne 0 -or [int]$_.sideBNetEwRangePenalty -ne 0 }).Count -eq 0) 'Checkpoint 69 must not reintroduce static net-EW range penalties.'
$clearNormal = @($combat.variants | Where-Object {
    [string]$_.sideASensorOverloadPolicy -eq 'None' -and
    [string]$_.sideBSensorOverloadPolicy -eq 'None' -and
    [string]$_.sideBEcmPolicy -eq 'None' -and
    [string]$_.sideAEccmPolicy -eq 'None'
})
$clearOverload = @($combat.variants | Where-Object {
    [string]$_.sideASensorOverloadPolicy -eq 'SafeWhenNeeded' -and
    [string]$_.sideBSensorOverloadPolicy -eq 'SafeWhenNeeded' -and
    [string]$_.sideBEcmPolicy -eq 'None' -and
    [string]$_.sideAEccmPolicy -eq 'None'
})
$jammedNoCounter = @($combat.variants | Where-Object {
    [string]$_.sideASensorOverloadPolicy -eq 'SafeWhenNeeded' -and
    [string]$_.sideBSensorOverloadPolicy -eq 'SafeWhenNeeded' -and
    [string]$_.sideBEcmPolicy -eq 'Normal' -and
    [string]$_.sideAEccmPolicy -eq 'None'
})
$jammedEccm = @($combat.variants | Where-Object {
    [string]$_.sideASensorOverloadPolicy -eq 'SafeWhenNeeded' -and
    [string]$_.sideBSensorOverloadPolicy -eq 'SafeWhenNeeded' -and
    [string]$_.sideBEcmPolicy -eq 'Normal' -and
    [string]$_.sideAEccmPolicy -eq 'Normal'
})
Assert-True ($clearNormal.Count -eq 18 -and $clearOverload.Count -eq 18 -and $jammedNoCounter.Count -eq 18 -and $jammedEccm.Count -eq 18) 'Checkpoint 69 operational Sensor/EW package matrix must contain exactly 18 clear-normal, clear-overload, jammed-no-counter, and jammed-ECCM variants.'

$coreSource = Get-Content -LiteralPath (Join-Path $repositoryRoot 'src\StarCluster.Core\Combat\Tracking\SensorEwFoundationResolver.cs') -Raw
Assert-True ($coreSource.Contains('bool hasLineOfSight = distanceHexes == 0 || context.HasLineOfSight;')) 'Same-hex LOS must be explicitly unoccludable.'
Assert-True (-not $coreSource.Contains('if (distanceHexes == 0)')) 'Range zero must not use an early Firm-track return.'
Assert-True ($coreSource.Contains('context.TargetEcmRating - context.ObserverEccmRating')) 'Sensor/EW resolver must compute net ECM from target ECM minus observer ECCM.'
Assert-True ($coreSource.Contains('emissionAssisted == SensorEwFoundationTrackState.Firm')) 'ECM must degrade Firm discrimination rather than subtract physical sensor range.'

$runnerSource = Get-Content -LiteralPath (Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\TL1Calibration\Tl1IntegratedTacticalCombatRunner.cs') -Raw
Assert-True ($runnerSource.Contains('tl1-itc11-sensor-ew-candidate-operational-combat')) 'Integrated runner must register the Checkpoint 69 operational Sensor/EW study.'
Assert-True ($runnerSource.Contains('ValidateTl1SensorEwCandidateCombatCoverage')) 'Integrated runner must bind Checkpoint 69 pre-run matrix validation.'
Assert-True ($runnerSource.Contains('ResolveFoundationTrackQuality')) 'Integrated combat must call the causal Sensor/EW resolver for CP69 candidate profiles.'
Assert-True ($runnerSource.Contains('WriteTl1SensorEwCandidateCombatReview')) 'Integrated runner must write the CP69 candidate review output.'
Assert-True ($runnerSource.Contains('study.Id == Tl1SensorEwCandidateCombatStudyId')) 'Integrated runner must classify the CP69 study in shared release-gate logic.'
Assert-True ($runnerSource -match 'if\s*\(variant\.SideAEcmPolicy\s*!=\s*Tl1IntegratedEwPowerPolicy\.None\s*\|\|\s*variant\.SideBEccmPolicy\s*!=\s*Tl1IntegratedEwPowerPolicy\.None\)') 'Checkpoint 69 package classifier guard must allow Side A ECCM so jammed-ECCM variants are not rejected before classification.'

# CP69c runtime-binding regression learned from the native CP69b Stage 11 failure.
$preflightStage = @($normal.stages | Where-Object { [string]$_.id -eq 'tl1-sensor-ew-candidate-operational-preflight' })
Assert-True ($preflightStage.Count -eq 1) 'Checkpoint 69c normal suite must contain exactly one executable Sensor/EW candidate preflight stage.'
Assert-True ([string]$preflightStage[0].command -eq 'tl1-integrated-tactical-combat-preflight') 'Checkpoint 69c candidate preflight must invoke the actual integrated tactical-combat consumer in preflight mode.'
Assert-True (-not [bool]$preflightStage[0].metrics.usesTrials -and [bool]$preflightStage[0].metrics.actualConsumerDeserializer -and [bool]$preflightStage[0].metrics.catalogBindingRequired) 'Checkpoint 69c candidate preflight metrics must bind actual consumer deserialization without Monte Carlo trials.'
$deepPreflightStage = @($deep.stages | Where-Object { [string]$_.id -eq 'tl1-sensor-ew-candidate-operational-preflight' })
Assert-True ($deepPreflightStage.Count -eq 1) 'Checkpoint 69c Deep Calibration must also contain the executable Sensor/EW candidate preflight stage.'
$smokeStage = @($normal.stages | Where-Object { [string]$_.id -eq 'tl1-sensor-ew-candidate-operational-smoke' })
Assert-True ($smokeStage.Count -eq 1) 'Checkpoint 69c normal suite must contain exactly one 72-variant execution smoke stage.'
Assert-True ([string]$smokeStage[0].command -eq 'tl1-integrated-tactical-combat') 'Checkpoint 69c smoke stage must invoke the full integrated tactical-combat runner.'
Assert-True ((@($smokeStage[0].arguments) -join '|').Contains('--trials|1')) 'Checkpoint 69c smoke stage must execute exactly one trial per variant.'
Assert-True ([int]$smokeStage[0].metrics.variantCount -eq 72 -and [int]$smokeStage[0].metrics.totalSmokeTrials -eq 72 -and [bool]$smokeStage[0].metrics.fullPipelineExecution) 'Checkpoint 69c smoke stage must execute the full 72-variant pipeline for 72 total smoke trials.'
$deepSmokeStage = @($deep.stages | Where-Object { [string]$_.id -eq 'tl1-sensor-ew-candidate-operational-smoke' })
Assert-True ($deepSmokeStage.Count -eq 1) 'Checkpoint 69c Deep Calibration must also contain the 72-variant execution smoke stage.'

$loadSensorStart = $runnerSource.IndexOf('private static IReadOnlyDictionary<string, SensorEwFoundationProfile>', [StringComparison]::Ordinal)
$loadSensorEnd = $runnerSource.IndexOf('private static Tl1SensorEnvelope ResolveSensorEnvelope(', [StringComparison]::Ordinal)
Assert-True ($loadSensorStart -ge 0 -and $loadSensorEnd -gt $loadSensorStart) 'Checkpoint 69c catalog-binding regression: unable to isolate LoadSensorEwProfiles.'
$loadSensorText = $runnerSource.Substring($loadSensorStart, $loadSensorEnd - $loadSensorStart)
Assert-True ($loadSensorText.Contains('PropertyNameCaseInsensitive = true')) 'Checkpoint 69c catalog-binding regression: integrated Sensor/EW catalog deserialization must accept the authoritative camelCase catalog.'
Assert-True ($loadSensorText.Contains('if (catalog.Candidates is null)')) 'Checkpoint 69c catalog-binding regression: integrated Sensor/EW catalog loader must reject an unbound Candidates collection explicitly.'
Assert-True ($loadSensorText.Contains('catalog.Candidates.ToDictionary(')) 'Checkpoint 69c catalog-binding regression: candidate dictionary construction must occur only after the binding guard.'

$programSource = Get-Content -LiteralPath (Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\Program.cs') -Raw
Assert-True ($programSource.Contains('tl1-sew02-sensor-ew-foundation-range-sweep.json')) 'ScenarioRunner default Sensor/EW foundation command must point at the CP69 successor study.'
Assert-True ($programSource.Contains('Console.Error.WriteLine($"ERROR: {exception}");')) 'Checkpoint 69c diagnostics must print the full top-level exception so native-only failures retain stack traces.'

$concept = Join-Path $repositoryRoot 'docs\Star_Cluster_Game_Concept_v0.6h.docx'
$archivedConcept = Join-Path $repositoryRoot 'docs\archive\Star_Cluster_Game_Concept_v0.6g.docx'
Assert-True (Test-Path -LiteralPath $concept -PathType Leaf) 'Concept v0.6h must be active.'
Assert-True (Test-Path -LiteralPath $archivedConcept -PathType Leaf) 'Concept v0.6g must be archived.'

# Compile-adjacent regression checks learned from prior checkpoint failures.
$changedCs = @(
    'src/StarCluster.Core/Combat/Tracking/SensorEwFoundationResolver.cs',
    'src/StarCluster.ScenarioRunner/TL1SensorEw/Tl1SensorEwFoundationRunner.cs',
    'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatDocuments.cs',
    'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs',
    'src/StarCluster.ScenarioRunner/Program.cs',
    'tests/StarCluster.Tests/Combat/Tracking/SensorEwFoundationResolverTests.cs'
)
foreach ($rel in $changedCs) {
    $source = Get-Content -LiteralPath (Join-Path $repositoryRoot $rel) -Raw
    Assert-True ($source -notmatch '\b(?:ref|out)\s+[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*\b') "Compile-adjacent regression: ordinary properties must not be passed directly by ref/out in $rel."
}


# Retain CP69b compile regressions learned from the failed native CP69/CP69a builds.
Assert-True (-not $runnerSource.Contains('v.ProtectedCompartmentation || !v.BaseShieldRechargeEnabled ||')) 'CP69c compile regression: nullable BaseShieldRechargeEnabled may not be negated directly inside a non-nullable || chain.'
Assert-True ($runnerSource.Contains('v.ProtectedCompartmentation || !(v.BaseShieldRechargeEnabled ?? true) ||')) 'CP69c compile regression: fixed-control shield check must coalesce nullable BaseShieldRechargeEnabled to its existing default true value before negation.'
Assert-True (-not $runnerSource.Contains('v.EvasiveManeuversEnabled || !v.PdsEnabled || v.EscapeDisengagementEnabled ||')) 'CP69c compile regression: nullable Evasive/PDS/Escape controls may not be used directly inside a non-nullable || chain.'
Assert-True ($runnerSource.Contains('v.EvasiveManeuversEnabled != false || v.PdsEnabled != true ||')) 'CP69c compile regression: fixed-control validation must require explicit Evasive=false and PDS=true values.'
Assert-True ($runnerSource.Contains('v.EscapeDisengagementEnabled != false ||')) 'CP69c compile regression: fixed-control validation must require explicit EscapeDisengagement=false.'
$reviewStart = $runnerSource.IndexOf('private static void WriteTl1SensorEwCandidateCombatReview(', [StringComparison]::Ordinal)
$reviewEnd = $runnerSource.IndexOf('private static void WriteMinimalTacticsReviewGrid(', [StringComparison]::Ordinal)
Assert-True ($reviewStart -ge 0 -and $reviewEnd -gt $reviewStart) 'CP69c compile regression: unable to isolate Sensor/EW candidate review writer.'
$reviewText = $runnerSource.Substring($reviewStart, $reviewEnd - $reviewStart)
Assert-True ($reviewText.Contains('static double Conditional(Tl1IntegratedTacticalCombatVariantSummary result)')) 'CP69c compile regression: Sensor/EW candidate review writer must define its own method-local Conditional helper.'
Assert-True ($reviewText.Contains('F(Conditional(result))')) 'CP69c compile regression: candidate review output must continue using the local conditional-win helper.'

# CP69c is a runtime-binding-only hotfix: pin all non-runner Sensor/EW authority and study inputs to the original CP69 package.
$cp69FrozenHashes = @{
    'docs/Star_Cluster_Game_Concept_v0.6h.docx' = '39d8e9ec81c2dfe10a8eb7e1ef3e6cd1692e184988d5efbb2d7daaa4b338cb9e'
    'docs/design/player_technology/tl1_integrated_tactical_combat_schema_v0_14.json' = '0ccbcec2fb34169f12d3914f02fefe0caec03907e91ff4803a17f7812e17b97c'
    'src/StarCluster.Core/Combat/Tracking/SensorEwFoundationResolver.cs' = '2bb38d44bf50774210deaa4f0fc9ba5815f24fab392b8c2f7e9674901e9e25dd'
    'src/StarCluster.ScenarioRunner/Scenarios/SensorEw/tl1-sew02-sensor-ew-foundation-range-sweep.json' = '1639d45cedf941925d25cdff91b77c2636ef82a15f389f05916f1efef3d13875'
    'src/StarCluster.ScenarioRunner/Scenarios/TL1Calibration/tl1-itc11-sensor-ew-candidate-operational-combat.json' = '8da880a9da997d019d3a98bd1c0ea89aebecbbb7e41b0057799cb572827daf58'
}
foreach ($entry in $cp69FrozenHashes.GetEnumerator()) {
    $actual = (Get-FileHash -LiteralPath (Join-Path $repositoryRoot $entry.Key) -Algorithm SHA256).Hash.ToLowerInvariant()
    Assert-True ($actual -eq [string]$entry.Value) "CP69c runtime-binding hotfix changed frozen CP69 authority/input: $($entry.Key)."
}

$validationFiles = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs\validation') -File -Filter 'Checkpoint_*.md')
Assert-True ($validationFiles.Count -eq 1 -and $validationFiles[0].Name -eq 'Checkpoint_69c_Sensor_EW_Candidate_Catalog_Binding_Hotfix.md') 'Exactly one Checkpoint 69c active validation runbook must remain.'
$rootTxt = @(Get-ChildItem -LiteralPath $repositoryRoot -File -Filter '*.txt')
Assert-True ($rootTxt.Count -eq 1 -and $rootTxt[0].Name -eq 'CHECKPOINT_69C_SHA256SUMS.txt') 'Repository root must contain only CHECKPOINT_69C_SHA256SUMS.txt as .txt.'
$archivedTxt = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs\archive') -Recurse -File -Filter '*.txt')
Assert-True ($archivedTxt.Count -eq 0) 'Generated historical checkpoint .txt artifacts must not remain under docs/archive.'

Write-Host '       Checkpoint 69c native dependency contract: PowerShell + pinned .NET only; active Python runtime dependencies are rejected before native work.'
Write-Host '       Sensor/EW foundation: 7 profiles x 12 contexts x 11 ranges = 924 deterministic rows; Balanced-0 adds Passive Approximate range without extending Passive Firm range.'
Write-Host '       Same-hex guardrail: LOS cannot be occluded, but emissions and ECM/ECCM discrimination still resolve normally at range zero.'
Write-Host '       Operational candidate study: Balanced-0/1/2 x 3 weapon pairings x 2 movement orders x 4 Sensor/EW packages = 72 variants / 720,000 default trials.'
Write-Host '       Validation tiers: 11 normal stages / 72 substantive MC variants + 72 smoke trials; Deep Calibration 30 stages / 1,616 substantive MC variants + 72 smoke trials.'
Write-Host 'Checkpoint 69c catalog-binding hotfix contract validation passed.'
