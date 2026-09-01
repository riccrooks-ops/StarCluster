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
$contractCheck = Join-Path $PSScriptRoot 'test_checkpoint_63a_contract.ps1'
$harness = Join-Path $repositoryRoot 'tools\calibration\run_calibration_checkpoint.ps1'
$definitionName = if ($DeepCalibration) { 'checkpoint-63-deep-calibration.json' } else { 'checkpoint-63.json' }
$definition = Join-Path $repositoryRoot (Join-Path 'tools\calibration\checkpoints' $definitionName)

# Checkpoint 63a deliberately stops shipping generated historical checkpoint text
# artifacts. Remove only known repository-generated stale files so extracting the
# full checkpoint over an older working tree does not leave manifest-breaking
# clutter behind. User-authored arbitrary .txt files are not touched.
$staleRootPatterns = @(
    '^CHECKPOINT_(?!63A(?:_|$)).*_SHA256SUMS\.txt$',
    '^Checkpoint_(?!63a(?:_|$)).*_Readme\.txt$',
    '^checkpoint-(?!63a(?:-|$)).*-static-preflight\.txt$'
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

# A full checkpoint may be extracted directly over an older repository. Retire
# only recognized historical active checkpoint runbooks so the sole-active-
# runbook contract remains true without deleting unrelated user documentation.
$validationRoot = Join-Path $repositoryRoot 'docs\validation'
if (Test-Path -LiteralPath $validationRoot -PathType Container) {
    foreach ($file in @(Get-ChildItem -LiteralPath $validationRoot -File -Filter 'Checkpoint_*.md')) {
        if ($file.Name -ne 'Checkpoint_63a_Passive_Core_Gate_Hotfix.md') {
            Remove-Item -LiteralPath $file.FullName -Force
        }
    }
}

& $contractCheck
& $harness -CheckpointDefinition $definition -Trials $Trials -Jobs $Jobs -RepositoryOnly:$RepositoryOnly -NoClean:$NoClean
