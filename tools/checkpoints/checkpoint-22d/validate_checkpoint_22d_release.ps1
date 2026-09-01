[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$ArchivePath
)

$ErrorActionPreference = 'Stop'
$resolvedArchive = (Resolve-Path -LiteralPath $ArchivePath).Path
$stagingRoot = Join-Path ([System.IO.Path]::GetTempPath()) `
    ("star-cluster-checkpoint-22d-release-{0}" -f `
        ([guid]::NewGuid().ToString('N')))

try {
    [void](New-Item -ItemType Directory -Path $stagingRoot -Force)
    Expand-Archive -LiteralPath $resolvedArchive -DestinationPath $stagingRoot -Force

    $checkpointScript = Join-Path $stagingRoot `
        'tools\checkpoints\checkpoint-22d\apply_checkpoint_22d.ps1'
    if (-not (Test-Path -LiteralPath $checkpointScript -PathType Leaf)) {
        throw "Checkpoint 22d application script was not found in $resolvedArchive."
    }

    Write-Host '[1/2] Running clean-extraction repository-contract preflight...'
    & $checkpointScript -RepositoryContractOnly

    Write-Host '[2/2] Testing extraction-over-existing runbook normalization...'
    $validationDirectory = Join-Path $stagingRoot 'docs\validation'
    $archivedRunbook = Join-Path $validationDirectory `
        'archive\Checkpoint_22c_Calibration_Map_Sizing_And_Allocation_Repair.md'
    $staleActiveRunbook = Join-Path $validationDirectory `
        'Checkpoint_22c_Calibration_Map_Sizing_And_Allocation_Repair.md'
    if (-not (Test-Path -LiteralPath $archivedRunbook -PathType Leaf)) {
        throw 'The packaged Checkpoint 22c archived validation runbook was not found.'
    }
    Copy-Item -LiteralPath $archivedRunbook -Destination $staleActiveRunbook -Force
    & $checkpointScript -RepositoryContractOnly

    $activeRunbooks = @(Get-ChildItem -LiteralPath $validationDirectory `
        -Filter 'Checkpoint_*.md' -File)
    if ($activeRunbooks.Count -ne 1 -or
        $activeRunbooks[0].Name -ne `
            'Checkpoint_22d_Accepted_Baseline_Closure_And_Checkpoint_23_Handoff.md') {
        throw 'Release validation left an invalid active-runbook set.'
    }

    Write-Host ''
    Write-Host 'Checkpoint 22d release validation completed successfully.'
    Write-Host 'Clean extraction and extraction-over-existing repository contracts passed.'
}
finally {
    Remove-Item -LiteralPath $stagingRoot -Recurse -Force `
        -ErrorAction SilentlyContinue
}
