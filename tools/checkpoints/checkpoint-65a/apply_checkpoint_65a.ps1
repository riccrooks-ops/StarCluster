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
$contractCheck = Join-Path $PSScriptRoot 'test_checkpoint_65a_contract.ps1'
$staticPreflight = Join-Path $PSScriptRoot 'static_preflight_checkpoint_65a.py'
$harness = Join-Path $repositoryRoot 'tools\calibration\run_calibration_checkpoint.ps1'
$definitionName = if ($DeepCalibration) { 'checkpoint-65a-deep-calibration.json' } else { 'checkpoint-65a.json' }
$definition = Join-Path $repositoryRoot (Join-Path 'tools\calibration\checkpoints' $definitionName)

# Preserve the Checkpoint 62+ clean packaging policy when a full repository is
# extracted over an older working tree. Remove only recognized generated
# checkpoint text artifacts; arbitrary user-authored .txt files are untouched.
$staleRootPatterns = @(
    '^CHECKPOINT_(?!65A(?:_|$)).*_SHA256SUMS\.txt$',
    '^Checkpoint_(?!65A(?:_|$)).*_Readme\.txt$',
    '^checkpoint-(?!65a(?:-|$)).*-static-preflight\.txt$'
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
    foreach ($file in @(Get-ChildItem -LiteralPath $validationRoot -File -Filter 'Checkpoint_*.md')) {
        if ($file.Name -ne 'Checkpoint_65a_TL1_Bilateral_Tactical_Geometry_Fuel_And_Movement_Order_Hotfix.md') {
            Remove-Item -LiteralPath $file.FullName -Force
        }
    }
}

# The contract is a PowerShell child script. Under StrictMode it reports failure by
# throwing; invoking it does not initialize the native-process $LASTEXITCODE variable.
& $contractCheck
python $staticPreflight --repository-root $repositoryRoot
if ($LASTEXITCODE -ne 0) { throw "Checkpoint 65a static preflight failed with exit code $LASTEXITCODE." }
& $harness -CheckpointDefinition $definition -Trials $Trials -Jobs $Jobs -RepositoryOnly:$RepositoryOnly -NoClean:$NoClean
