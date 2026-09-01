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
$contractCheck = Join-Path $PSScriptRoot 'test_checkpoint_74d_contract.ps1'
$harness = Join-Path $repositoryRoot 'tools\calibration\run_calibration_checkpoint.ps1'
$definitionName = if ($DeepCalibration) { 'checkpoint-74d-deep-calibration.json' } else { 'checkpoint-74d.json' }
$definition = Join-Path $repositoryRoot (Join-Path 'tools\calibration\checkpoints' $definitionName)
$normalDefinition = 'tools/calibration/checkpoints/checkpoint-74d.json'
$deepDefinition = 'tools/calibration/checkpoints/checkpoint-74d-deep-calibration.json'
$guardedPowerShellPaths = @(
    'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
    'tools/checkpoints/checkpoint-74d/apply_checkpoint_74d.ps1',
    'tools/checkpoints/checkpoint-74d/test_checkpoint_74d_contract.ps1',
    'tools/calibration/run_calibration_checkpoint.ps1'
)
$guardedDefinitionPaths = @($normalDefinition, $deepDefinition)

# FIRST validation action: reject accidental Python/runtime dependencies before
# cleanup, contract execution, manifest validation, or native build work.
& $dependencyGuard -RepositoryRoot $repositoryRoot -PowerShellPaths $guardedPowerShellPaths -CheckpointDefinitionPaths $guardedDefinitionPaths

# Preserve clean full-repository checkpoint packaging when extracting over an older CP74 hotfix or another worktree.
$staleRootPatterns = @(
    '^CHECKPOINT_(?!74D(?:_|$)).*_SHA256SUMS\.txt$',
    '^Checkpoint_(?!74d(?:_|$)).*_Readme\.txt$',
    '^checkpoint-(?!74d(?:-|$)).*-static-preflight\.txt$'
)
foreach ($file in @(Get-ChildItem -LiteralPath $repositoryRoot -File -Filter '*.txt')) {
    foreach ($pattern in $staleRootPatterns) {
        if ($file.Name -match $pattern) {
            Remove-Item -LiteralPath $file.FullName -Force
            break
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
        if ($file.Name -ne 'Checkpoint_74d_Degraded_Fire_Firm_Reference_Gate_Semantics_Hotfix.md') {
            $archivedPath = Join-Path $validationArchive $file.Name
            if (Test-Path -LiteralPath $archivedPath -PathType Leaf) {
                Remove-Item -LiteralPath $archivedPath -Force
            }
            Move-Item -LiteralPath $file.FullName -Destination $archivedPath -Force
        }
    }
}

& $contractCheck
& $harness -CheckpointDefinition $definition -Trials $Trials -Jobs $Jobs -RepositoryOnly:$RepositoryOnly -NoClean:$NoClean
