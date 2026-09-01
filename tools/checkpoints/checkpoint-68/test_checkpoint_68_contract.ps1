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
$normalRel = 'tools/calibration/checkpoints/checkpoint-68.json'
$deepRel = 'tools/calibration/checkpoints/checkpoint-68-deep-calibration.json'
$guardedPs = @(
    'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
    'tools/checkpoints/checkpoint-68/apply_checkpoint_68.ps1',
    'tools/checkpoints/checkpoint-68/test_checkpoint_68_contract.ps1',
    'tools/calibration/run_calibration_checkpoint.ps1'
)
& $guard -RepositoryRoot $repositoryRoot -PowerShellPaths $guardedPs -CheckpointDefinitionPaths @($normalRel, $deepRel)

$normal = Get-Content -LiteralPath (Join-Path $repositoryRoot $normalRel) -Raw | ConvertFrom-Json
$deep = Get-Content -LiteralPath (Join-Path $repositoryRoot $deepRel) -Raw | ConvertFrom-Json
Assert-True ([string]$normal.checkpointId -eq '68') 'Checkpoint 68 normal definition ID mismatch.'
Assert-True ([string]$deep.checkpointId -eq '68') 'Checkpoint 68 deep definition ID mismatch.'
Assert-True ([string]$normal.manifestFile -eq 'CHECKPOINT_68_SHA256SUMS.txt') 'Checkpoint 68 normal manifest binding mismatch.'
Assert-True ([string]$deep.manifestFile -eq 'CHECKPOINT_68_SHA256SUMS.txt') 'Checkpoint 68 deep manifest binding mismatch.'
Assert-True ([string]$normal.outputRoot -eq 'out/checkpoint-68') 'Checkpoint 68 normal output root mismatch.'
Assert-True ([string]$deep.outputRoot -eq 'out/checkpoint-68-deep-calibration') 'Checkpoint 68 deep output root mismatch.'
Assert-True (@($normal.stages).Count -eq 8) 'Checkpoint 68 normal suite must contain 8 stages.'
Assert-True (@($deep.stages).Count -eq 27) 'Checkpoint 68 Deep Calibration must contain 27 stages.'
Assert-True ([int]$normal.checkpointMetrics.monteCarloVariantCount -eq 0 -and [int]$normal.checkpointMetrics.trialsAtDefault -eq 0) 'Checkpoint 68 normal suite must contain no Monte Carlo workload.'
Assert-True ([int]$deep.checkpointMetrics.monteCarloVariantCount -eq 1544 -and [int]$deep.checkpointMetrics.trialsAtDefault -eq 15440000) 'Checkpoint 68 Deep Calibration workload mismatch.'

$normalSensorStage = @($normal.stages | Where-Object { [string]$_.id -eq 'tl1-sensor-ew-foundation' })
$deepSensorStage = @($deep.stages | Where-Object { [string]$_.id -eq 'tl1-sensor-ew-foundation' })
Assert-True ($normalSensorStage.Count -eq 1 -and $deepSensorStage.Count -eq 1) 'Checkpoint 68 Sensor/EW foundation stage must exist exactly once in both suites.'
Assert-True ([string]$normalSensorStage[0].command -eq 'tl1-sensor-ew-foundation') 'Checkpoint 68 Sensor/EW command mismatch.'
Assert-True ([int]$normalSensorStage[0].metrics.deterministicRowCount -eq 792) 'Checkpoint 68 deterministic row count mismatch.'

$studyPath = Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\Scenarios\SensorEw\tl1-sew01-sensor-ew-foundation-range-sweep.json'
$study = Get-Content -LiteralPath $studyPath -Raw | ConvertFrom-Json
Assert-True ([string]$study.schemaVersion -eq 'star-cluster-tl1-sensor-ew-foundation-v1') 'Checkpoint 68 Sensor/EW schema version mismatch.'
Assert-True ([string]$study.id -eq 'tl1-sew01-sensor-ew-foundation-range-sweep') 'Checkpoint 68 Sensor/EW study ID mismatch.'
Assert-True ([int]$study.checkpoint -eq 68 -and [int]$study.maxTacticalSeparationHexes -eq 10) 'Checkpoint 68 Sensor/EW map/range identity mismatch.'
Assert-True (@($study.candidates).Count -eq 6) 'Checkpoint 68 Sensor/EW study must contain one historical control and five forward candidates.'
$forward = @($study.candidates | Where-Object { -not [bool]$_.isHistoricalControl })
Assert-True ($forward.Count -eq 5) 'Checkpoint 68 must contain five forward TL1 sensor candidates.'
Assert-True (@($forward | Where-Object { [int]$_.activePowerCost -ne 1 -or [int]$_.activeOverloadAdditionalPowerCost -ne 1 }).Count -eq 0) 'Forward TL1 candidates must use one 1-TP normal Active mode plus one +1-TP overload.'
Assert-True (@($forward | Where-Object { [int]$_.activeFirmRange -gt 3 -or [int]$_.activeApproximateRange -gt 4 }).Count -eq 0) 'Forward TL1 normal Active candidates must retain the reduced-range sweep envelope.'

$concept = Join-Path $repositoryRoot 'docs\Star_Cluster_Game_Concept_v0.6g.docx'
$archivedConcept = Join-Path $repositoryRoot 'docs\archive\Star_Cluster_Game_Concept_v0.6f.docx'
Assert-True (Test-Path -LiteralPath $concept -PathType Leaf) 'Concept v0.6g must be active.'
Assert-True (Test-Path -LiteralPath $archivedConcept -PathType Leaf) 'Concept v0.6f must be archived.'

$coreSource = Get-Content -LiteralPath (Join-Path $repositoryRoot 'src\StarCluster.Core\Combat\Tracking\SensorEwFoundationResolver.cs') -Raw
Assert-True ($coreSource.Contains('ECM is intentionally conspicuous') -and $coreSource.Contains('SensorEwFoundationTrackState.Approximate')) 'Sensor/EW resolver must preserve emission-assisted Approximate semantics.'
Assert-True ($coreSource.Contains('context.TargetEcmRating - context.ObserverEccmRating')) 'Sensor/EW resolver must compute net ECM from target ECM minus observer ECCM.'
Assert-True ($coreSource.Contains('emissionAssisted == SensorEwFoundationTrackState.Firm')) 'ECM must degrade Firm discrimination rather than subtract sensor range.'

$stlSource = Get-Content -LiteralPath (Join-Path $repositoryRoot 'src\StarCluster.Core\Combat\Tactics\StlDriveOverloadCommitmentService.cs') -Raw
Assert-True ($stlSource.Contains('StrainRemoved: 0') -and $stlSource.Contains('OverloadFuelSpent: 0')) 'Standing down a prepared STL overload must not heal Strain or spend overload fuel.'
Assert-True ($stlSource.Contains('TacticalPowerCommitted: commitment.TacticalPowerCommitted')) 'Standing down must retain the committed Tactical Power cost.'

$programSource = Get-Content -LiteralPath (Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\Program.cs') -Raw
Assert-True ($programSource.Contains('"tl1-sensor-ew-foundation" => RunTl1SensorEwFoundation')) 'ScenarioRunner must register the Checkpoint 68 Sensor/EW command.'
Assert-True ($programSource.Contains('Tl1SensorEwFoundationRunner.Run')) 'ScenarioRunner must dispatch the Checkpoint 68 Sensor/EW runner.'

# Compile-adjacent regression checks learned from CP66/67.
$changedCs = @(
    'src/StarCluster.Core/Combat/Tracking/SensorEwFoundationResolver.cs',
    'src/StarCluster.Core/Combat/Tactics/StlDriveOverloadCommitmentService.cs',
    'src/StarCluster.ScenarioRunner/TL1SensorEw/Tl1SensorEwFoundationRunner.cs',
    'src/StarCluster.ScenarioRunner/Program.cs'
)
foreach ($rel in $changedCs) {
    $source = Get-Content -LiteralPath (Join-Path $repositoryRoot $rel) -Raw
    Assert-True ($source -notmatch '\b(?:ref|out)\s+[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*\b') "Compile-adjacent regression: ordinary properties must not be passed directly by ref/out in $rel."
}

$validationFiles = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs\validation') -File -Filter 'Checkpoint_*.md')
Assert-True ($validationFiles.Count -eq 1 -and $validationFiles[0].Name -eq 'Checkpoint_68_TL1_Sensor_EW_Foundation_And_Range_Sweep.md') 'Exactly one Checkpoint 68 active validation runbook must remain.'
$rootTxt = @(Get-ChildItem -LiteralPath $repositoryRoot -File -Filter '*.txt')
Assert-True ($rootTxt.Count -eq 1 -and $rootTxt[0].Name -eq 'CHECKPOINT_68_SHA256SUMS.txt') 'Repository root must contain only CHECKPOINT_68_SHA256SUMS.txt as .txt.'
$archivedTxt = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs\archive') -Recurse -File -Filter '*.txt')
Assert-True ($archivedTxt.Count -eq 0) 'Generated historical checkpoint .txt artifacts must not remain under docs/archive.'

Write-Host '       Checkpoint 68 native dependency contract: PowerShell + pinned .NET only; active Python runtime dependencies are rejected before native work.'
Write-Host '       Sensor/EW foundation: 6 profiles x 12 contexts x 11 ranges = 792 deterministic rows; no sensor candidate is promoted to production.'
Write-Host '       Forward TL1 architecture: one normal Active mode plus one bounded overload; emissions assist detection while ECM/ECCM resolve discrimination.'
Write-Host '       Prepared STL overload may be stood down without refund, overload fuel, added Strain, or Strain healing.'
Write-Host '       Validation tiers: 8 normal stages / 0 MC variants; Deep Calibration 27 stages / 1,544 MC variants.'
Write-Host 'Checkpoint 68 contract validation passed.'
