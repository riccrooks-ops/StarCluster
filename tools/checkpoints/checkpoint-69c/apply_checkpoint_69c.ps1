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
$contractCheck = Join-Path $PSScriptRoot 'test_checkpoint_69c_contract.ps1'
$harness = Join-Path $repositoryRoot 'tools\calibration\run_calibration_checkpoint.ps1'
$definitionName = if ($DeepCalibration) { 'checkpoint-69c-deep-calibration.json' } else { 'checkpoint-69c.json' }
$definition = Join-Path $repositoryRoot (Join-Path 'tools\calibration\checkpoints' $definitionName)
$normalDefinition = 'tools/calibration/checkpoints/checkpoint-69c.json'
$deepDefinition = 'tools/calibration/checkpoints/checkpoint-69c-deep-calibration.json'
$guardedPowerShellPaths = @(
    'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
    'tools/checkpoints/checkpoint-69c/apply_checkpoint_69c.ps1',
    'tools/checkpoints/checkpoint-69c/test_checkpoint_69c_contract.ps1',
    'tools/calibration/run_calibration_checkpoint.ps1'
)
$guardedDefinitionPaths = @($normalDefinition, $deepDefinition)

# FIRST validation action: reject accidental Python/runtime dependencies before
# cleanup, contract execution, manifest validation, or native build work.
& $dependencyGuard -RepositoryRoot $repositoryRoot -PowerShellPaths $guardedPowerShellPaths -CheckpointDefinitionPaths $guardedDefinitionPaths

# Preserve clean checkpoint packaging when extracting over an older worktree.
$staleRootPatterns = @(
    '^CHECKPOINT_(?!69C(?:_|$)).*_SHA256SUMS\.txt$',
    '^Checkpoint_(?!69c(?:_|$)).*_Readme\.txt$',
    '^checkpoint-(?!69c(?:-|$)).*-static-preflight\.txt$'
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
    foreach ($directory in @(Get-ChildItem -LiteralPath $archiveRoot -Recurse -Directory | Sort-Object FullName -Descending)) {
        if (-not @(Get-ChildItem -LiteralPath $directory.FullName -Force).Count) {
            Remove-Item -LiteralPath $directory.FullName -Force
        }
    }
}

$validationRoot = Join-Path $repositoryRoot 'docs\validation'
if (Test-Path -LiteralPath $validationRoot -PathType Container) {
    foreach ($file in @(Get-ChildItem -LiteralPath $validationRoot -File -Filter 'Checkpoint_*.md')) {
        if ($file.Name -ne 'Checkpoint_69c_Sensor_EW_Candidate_Catalog_Binding_Hotfix.md') {
            Move-Item -LiteralPath $file.FullName -Destination (Join-Path $validationRoot 'archive') -Force
        }
    }
}

& $contractCheck
& $harness -CheckpointDefinition $definition -Trials $Trials -Jobs $Jobs -RepositoryOnly:$RepositoryOnly -NoClean:$NoClean
