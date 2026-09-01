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
$contractCheck = Join-Path $PSScriptRoot 'test_checkpoint_72_contract.ps1'
$harness = Join-Path $repositoryRoot 'tools\calibration\run_calibration_checkpoint.ps1'
$definitionName = if ($DeepCalibration) { 'checkpoint-72-deep-calibration.json' } else { 'checkpoint-72.json' }
$definition = Join-Path $repositoryRoot (Join-Path 'tools\calibration\checkpoints' $definitionName)
$normalDefinition = 'tools/calibration/checkpoints/checkpoint-72.json'
$deepDefinition = 'tools/calibration/checkpoints/checkpoint-72-deep-calibration.json'
$guardedPowerShellPaths = @(
    'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
    'tools/checkpoints/checkpoint-72/apply_checkpoint_72.ps1',
    'tools/checkpoints/checkpoint-72/test_checkpoint_72_contract.ps1',
    'tools/calibration/run_calibration_checkpoint.ps1'
)
$guardedDefinitionPaths = @($normalDefinition, $deepDefinition)
& $dependencyGuard -RepositoryRoot $repositoryRoot -PowerShellPaths $guardedPowerShellPaths -CheckpointDefinitionPaths $guardedDefinitionPaths

$staleRootPatterns = @('^CHECKPOINT_(?!72(?:_|$)).*_SHA256SUMS\.txt$','^Checkpoint_(?!72(?:_|$)).*_Readme\.txt$','^checkpoint-(?!72(?:-|$)).*-static-preflight\.txt$')
foreach ($file in @(Get-ChildItem -LiteralPath $repositoryRoot -File -Filter '*.txt')) {
    foreach ($pattern in $staleRootPatterns) { if ($file.Name -match $pattern) { Remove-Item -LiteralPath $file.FullName -Force; break } }
}
$validationRoot = Join-Path $repositoryRoot 'docs\validation'
if (Test-Path -LiteralPath $validationRoot -PathType Container) {
    $validationArchive = Join-Path $validationRoot 'archive'
    if (-not (Test-Path -LiteralPath $validationArchive -PathType Container)) { New-Item -ItemType Directory -Path $validationArchive | Out-Null }
    foreach ($file in @(Get-ChildItem -LiteralPath $validationRoot -File -Filter 'Checkpoint_*.md')) {
        if ($file.Name -ne 'Checkpoint_72_Reactive_PreCombat_EW_Subphase.md') { Move-Item -LiteralPath $file.FullName -Destination $validationArchive -Force }
    }
}
& $contractCheck
& $harness -CheckpointDefinition $definition -Trials $Trials -Jobs $Jobs -RepositoryOnly:$RepositoryOnly -NoClean:$NoClean
