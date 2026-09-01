[CmdletBinding()]
param(
    [int]$Trials = 10000,
    [int]$Jobs = 24,
    [switch]$RepositoryOnly,
    [switch]$DeepCalibration,
    [switch]$NoClean
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$dependencyGuard = Join-Path $repositoryRoot 'tools\checkpoints\Test-NativeAcceptanceDependencies.ps1'
$contractCheck = Join-Path $repositoryRoot 'tools\checkpoints\checkpoint-91\test_checkpoint_91_contract.ps1'
$harness = Join-Path $repositoryRoot 'tools\calibration\run_calibration_checkpoint.ps1'
$definitionName = if ($DeepCalibration) { 'checkpoint-91-deep-calibration.json' } else { 'checkpoint-91.json' }
$definition = Join-Path $repositoryRoot ('tools\calibration\checkpoints\' + $definitionName)
$normalDefinition = 'tools/calibration/checkpoints/checkpoint-91.json'
$deepDefinition = 'tools/calibration/checkpoints/checkpoint-91-deep-calibration.json'
$guardedPowerShellPaths = @(
    'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
    'tools/checkpoints/checkpoint-91/apply_checkpoint_91.ps1',
    'tools/checkpoints/checkpoint-91/test_checkpoint_91_contract.ps1',
    'tools/calibration/run_calibration_checkpoint.ps1'
)
$guardedDefinitionPaths = @($normalDefinition, $deepDefinition)

Write-Host '[1/4] Checking native-acceptance dependency contracts...'
& $dependencyGuard -RepositoryRoot $repositoryRoot -PowerShellPaths $guardedPowerShellPaths -CheckpointDefinitionPaths $guardedDefinitionPaths

Write-Host '[2/4] Normalizing stale active checkpoint artifacts...'
foreach ($file in @(Get-ChildItem -LiteralPath $repositoryRoot -File -Filter '*.txt')) {
    if ($file.Name -match '^CHECKPOINT_(?!91(?:_|$)).*_SHA256SUMS\.txt$' -or
        $file.Name -match '^Checkpoint_(?!91(?:_|$)).*_Readme\.txt$' -or
        $file.Name -match '^checkpoint-(?!91(?:-|$)).*-static-preflight\.txt$') {
        Remove-Item -LiteralPath $file.FullName -Force
    }
}

$validationRoot = Join-Path $repositoryRoot 'docs\validation'
$validationArchive = Join-Path $validationRoot 'archive'
if (-not (Test-Path -LiteralPath $validationArchive -PathType Container)) { New-Item -ItemType Directory -Path $validationArchive | Out-Null }
foreach ($file in @(Get-ChildItem -LiteralPath $validationRoot -File -Filter 'Checkpoint_*.md')) {
    if ($file.Name -ne 'Checkpoint_91_External_Reference_Mining_Architecture_And_Initial_Spacedock_Design_Corpus.md') {
        Move-Item -LiteralPath $file.FullName -Destination (Join-Path $validationArchive $file.Name) -Force
    }
}

$testingRoot = Join-Path $repositoryRoot 'docs\design\testing'
$testingArchive = Join-Path $repositoryRoot 'docs\archive\testing'
if (-not (Test-Path -LiteralPath $testingArchive -PathType Container)) { New-Item -ItemType Directory -Path $testingArchive | Out-Null }
foreach ($file in @(Get-ChildItem -LiteralPath $testingRoot -File -Filter 'Checkpoint_*_Validation_Tiers.md')) {
    if ($file.Name -ne 'Checkpoint_91_Validation_Tiers.md') { Move-Item -LiteralPath $file.FullName -Destination (Join-Path $testingArchive $file.Name) -Force }
}
foreach ($file in @(Get-ChildItem -LiteralPath $testingRoot -File -Filter 'checkpoint_*_validation_suite_policy*.json')) {
    if ($file.Name -ne 'checkpoint_91_validation_suite_policy_v0_1.json') { Move-Item -LiteralPath $file.FullName -Destination (Join-Path $testingArchive $file.Name) -Force }
}

Write-Host '[3/4] Verifying Checkpoint 91 external reference-mining contracts...'
& $contractCheck -RepositoryRoot $repositoryRoot

Write-Host '[4/4] Running checkpoint harness...'
& $harness -CheckpointDefinition $definition -Trials $Trials -Jobs $Jobs -RepositoryOnly:$RepositoryOnly -NoClean:$NoClean
