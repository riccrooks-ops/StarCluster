[CmdletBinding()]
param(
    [int]$Trials = 0,
    [int]$Jobs = 0,
    [switch]$RepositoryOnly,
    [switch]$NoClean,
    [switch]$DeepCalibration
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$dependencyGuard = Join-Path $repositoryRoot 'tools\checkpoints\Test-NativeAcceptanceDependencies.ps1'
$contractCheck = Join-Path $PSScriptRoot 'test_checkpoint_71_contract.ps1'
$harness = Join-Path $repositoryRoot 'tools\calibration\run_calibration_checkpoint.ps1'
$definitionName = if ($DeepCalibration) { 'checkpoint-71-deep-calibration.json' } else { 'checkpoint-71.json' }
$definition = Join-Path $repositoryRoot (Join-Path 'tools\calibration\checkpoints' $definitionName)
$normalDefinition = 'tools/calibration/checkpoints/checkpoint-71.json'
$deepDefinition = 'tools/calibration/checkpoints/checkpoint-71-deep-calibration.json'
$guardedPowerShellPaths = @(
    'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
    'tools/checkpoints/checkpoint-71/apply_checkpoint_71.ps1',
    'tools/checkpoints/checkpoint-71/test_checkpoint_71_contract.ps1',
    'tools/calibration/run_calibration_checkpoint.ps1'
)
$guardedDefinitionPaths = @($normalDefinition, $deepDefinition)

& $dependencyGuard -RepositoryRoot $repositoryRoot -PowerShellPaths $guardedPowerShellPaths -CheckpointDefinitionPaths $guardedDefinitionPaths

$staleRootPatterns = @(
    '^CHECKPOINT_(?!71(?:_|$)).*_SHA256SUMS\.txt$',
    '^Checkpoint_(?!71(?:_|$)).*_Readme\.txt$',
    '^checkpoint-(?!71(?:-|$)).*-static-preflight\.txt$'
)
foreach ($file in @(Get-ChildItem -LiteralPath $repositoryRoot -File -Filter '*.txt')) {
    foreach ($pattern in $staleRootPatterns) {
        if ($file.Name -match $pattern) {
            Remove-Item -LiteralPath $file.FullName -Force
            break
        }
    }
}

$archiveRoot = Join-Path $repositoryRoot 'docs\archive'
$staleArchivePatterns = @(
    '^CHECKPOINT_.*_SHA256SUMS\.txt$',
    '^Checkpoint_.*_Readme\.txt$',
    '^checkpoint-.*-static-preflight\.txt$'
)
if (Test-Path -LiteralPath $archiveRoot -PathType Container) {
    foreach ($file in @(Get-ChildItem -LiteralPath $archiveRoot -Recurse -File -Filter '*.txt')) {
        foreach ($pattern in $staleArchivePatterns) {
            if ($file.Name -match $pattern) {
                Remove-Item -LiteralPath $file.FullName -Force
                break
            }
        }
    }
}

$validationRoot = Join-Path $repositoryRoot 'docs\validation'
if (Test-Path -LiteralPath $validationRoot -PathType Container) {
    $validationArchive = Join-Path $validationRoot 'archive'
    if (-not (Test-Path -LiteralPath $validationArchive -PathType Container)) {
        New-Item -ItemType Directory -Path $validationArchive | Out-Null
    }
    foreach ($file in @(Get-ChildItem -LiteralPath $validationRoot -File -Filter 'Checkpoint_*.md')) {
        if ($file.Name -ne 'Checkpoint_71_Sensor_Discrimination_Resistance_And_Burnthrough.md') {
            Move-Item -LiteralPath $file.FullName -Destination $validationArchive -Force
        }
    }
}

& $contractCheck
& $harness -CheckpointDefinition $definition -Trials $Trials -Jobs $Jobs -RepositoryOnly:$RepositoryOnly -NoClean:$NoClean
