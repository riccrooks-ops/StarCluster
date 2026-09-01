[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$ArchivePath
)

$ErrorActionPreference = 'Stop'
$resolvedArchive = (Resolve-Path -LiteralPath $ArchivePath).Path
$stagingRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("star-cluster-checkpoint-29-release-{0}" -f ([guid]::NewGuid().ToString('N')))

function Assert-ArchiveContract {
    param([Parameter(Mandatory = $true)][string]$Path)
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip = [System.IO.Compression.ZipFile]::OpenRead($Path)
    try {
        $entries = @($zip.Entries | Where-Object { -not [string]::IsNullOrEmpty($_.Name) })
        $names = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
        foreach ($entry in $entries) {
            $name = $entry.FullName.Replace('\','/')
            if ([System.IO.Path]::IsPathRooted($name) -or $name.Split('/') -contains '..') { throw "Unsafe archive entry: $name" }
            if (-not $names.Add($name)) { throw "Duplicate archive entry: $name" }
        }
        $manifestEntry = $zip.GetEntry('CHECKPOINT_29_SHA256SUMS.txt')
        if ($null -eq $manifestEntry) { throw 'Archive repository manifest is missing.' }
        $reader = New-Object System.IO.StreamReader($manifestEntry.Open())
        try { $manifestText = $reader.ReadToEnd() } finally { $reader.Dispose() }
        $manifest = @{}
        foreach ($line in ($manifestText -split '\r?\n')) {
            if ([string]::IsNullOrWhiteSpace($line) -or $line.StartsWith('#')) { continue }
            $m = [regex]::Match($line, '^([0-9a-fA-F]{64})  (.+)$')
            if (-not $m.Success) { throw "Malformed archive manifest line: $line" }
            $name = $m.Groups[2].Value.Replace('\','/')
            if ($name -eq 'CHECKPOINT_29_SHA256SUMS.txt') { throw 'Archive manifest must not contain itself.' }
            if ($manifest.ContainsKey($name)) { throw "Duplicate archive manifest path: $name" }
            $manifest[$name] = $m.Groups[1].Value.ToLowerInvariant()
        }
        if ($manifest.Count -ne 611) { throw "Checkpoint 29 archive manifest must contain exactly 611 files; found $($manifest.Count)." }
        $actualNames = @($entries | ForEach-Object { $_.FullName.Replace('\','/') } | Where-Object {
            $_ -ne 'CHECKPOINT_29_SHA256SUMS.txt'
        })
        $missing = @($manifest.Keys | Where-Object { -not $names.Contains($_) } | Sort-Object)
        $extra = @($actualNames | Where-Object { -not $manifest.ContainsKey($_) } | Sort-Object)
        if ($missing.Count -gt 0) { throw ("Archive is missing manifest files:`n{0}" -f ($missing -join "`n")) }
        if ($extra.Count -gt 0) { throw ("Archive contains files not locked by the manifest:`n{0}" -f ($extra -join "`n")) }
        foreach ($name in $manifest.Keys) {
            $entry = $zip.GetEntry($name)
            if ($null -eq $entry) { throw "Archive entry $name was not found." }
            $stream = $entry.Open()
            $sha = [System.Security.Cryptography.SHA256]::Create()
            try { $actualHash = [System.BitConverter]::ToString($sha.ComputeHash($stream)).Replace('-','').ToLowerInvariant() }
            finally { $sha.Dispose(); $stream.Dispose() }
            if ($actualHash -ne $manifest[$name]) { throw "Archive hash mismatch for $name." }
        }
        Write-Host "       Archive manifest: $($manifest.Count) files verified; no extra entries."
    }
    finally { $zip.Dispose() }
}

try {
    Write-Host '[1/5] Verifying archive entries and internal repository manifest...'
    Assert-ArchiveContract -Path $resolvedArchive

    [void](New-Item -ItemType Directory -Path $stagingRoot -Force)
    Expand-Archive -LiteralPath $resolvedArchive -DestinationPath $stagingRoot -Force
    $checkpointScript = Join-Path $stagingRoot 'tools\checkpoints\checkpoint-29\apply_checkpoint_29.ps1'
    if (-not (Test-Path -LiteralPath $checkpointScript -PathType Leaf)) { throw "Checkpoint 29 application script was not found in $resolvedArchive." }

    Write-Host '[2/5] Running clean-extraction repository-contract preflight...'
    & $checkpointScript -RepositoryContractOnly

    Write-Host '[3/5] Running clean warning-as-error build, tests, legacy scenarios, Phase A/B corpora, kinetic and energy calibration, and runner self-tests...'
    & $checkpointScript

    Write-Host '[4/5] Testing extraction-over-existing normalization and local-artifact tolerance...'
    $validationDirectory = Join-Path $stagingRoot 'docs\validation'
    $archivedRunbook = Join-Path $validationDirectory 'archive\Checkpoint_27_Revised_TL1_Defensive_Envelope_And_Kinetic_Interaction_Calibration.md'
    $staleActiveRunbook = Join-Path $validationDirectory 'Checkpoint_27_Revised_TL1_Defensive_Envelope_And_Kinetic_Interaction_Calibration.md'
    if (-not (Test-Path -LiteralPath $archivedRunbook -PathType Leaf)) { throw 'The packaged Checkpoint 27 archived validation runbook was not found.' }
    Copy-Item -LiteralPath $archivedRunbook -Destination $staleActiveRunbook -Force

    $archivedConcept = Join-Path $stagingRoot 'docs\archive\Star_Cluster_Game_Concept_v0.3y.docx'
    $staleActiveConcept = Join-Path $stagingRoot 'docs\Star_Cluster_Game_Concept_v0.3y.docx'
    if (-not (Test-Path -LiteralPath $archivedConcept -PathType Leaf)) { throw 'The packaged Concept v0.3y archive copy was not found.' }
    Copy-Item -LiteralPath $archivedConcept -Destination $staleActiveConcept -Force

    $localArtifacts = @{
        '.vs\StarCluster\v17\.suo' = 'local visual studio state'
        'src\StarCluster.Game\.godot\editor\project_metadata.cfg' = 'local Godot state'
        'src\StarCluster.Game\Scripts\Main.cs.uid' = 'generated Godot UID'
        'out\checkpoint-29-release-test\result.txt' = 'local output'
        'Checkpoint_27_Readme.txt' = 'stale checkpoint identity'
        'CHECKPOINT_27_SHA256SUMS.txt' = 'stale checkpoint identity'
        'StarCluster_Checkpoint_27_Local_Copy.zip' = 'local package copy'
    }
    foreach ($relativePath in $localArtifacts.Keys) {
        $fullPath = Join-Path $stagingRoot $relativePath
        [void](New-Item -ItemType Directory -Path ([System.IO.Path]::GetDirectoryName($fullPath)) -Force)
        Set-Content -LiteralPath $fullPath -Value $localArtifacts[$relativePath] -Encoding UTF8
    }

    & $checkpointScript -RepositoryContractOnly
    $activeRunbooks = @(Get-ChildItem -LiteralPath $validationDirectory -Filter 'Checkpoint_*.md' -File)
    if ($activeRunbooks.Count -ne 1 -or $activeRunbooks[0].Name -ne 'Checkpoint_29_Revised_Evasive_Maneuvering_And_Complete_TL1_Weapon_Matrix.md') { throw 'Release validation left an invalid active-runbook set.' }
    if (Test-Path -LiteralPath $staleActiveConcept -PathType Leaf) { throw 'Release validation did not normalize the duplicate stale active concept.' }

    Write-Host '[5/5] Confirming unknown repository-owned files are rejected...'
    $unexpectedSource = Join-Path $stagingRoot 'src\StarCluster.Core\UnexpectedRepositoryOwnedSource.cs'
    Set-Content -LiteralPath $unexpectedSource -Value 'namespace StarCluster.Core; internal static class UnexpectedRepositoryOwnedSource { }' -Encoding UTF8
    $rejected = $false
    try {
        & $checkpointScript -RepositoryContractOnly
    }
    catch {
        $message = $_.Exception.Message
        if ($message -like '*repository-owned files not locked by the manifest*UnexpectedRepositoryOwnedSource.cs*') {
            $rejected = $true
        }
        else {
            throw
        }
    }
    finally {
        Remove-Item -LiteralPath $unexpectedSource -Force -ErrorAction SilentlyContinue
    }
    if (-not $rejected) { throw 'Repository contract failed to reject an unknown source file.' }

    Write-Host ''
    Write-Host 'Checkpoint 29 release validation completed successfully.'
    Write-Host 'Archive integrity, clean extraction, full acceptance, energy calibration, dirty-tree normalization, local-artifact tolerance, and unknown-source rejection passed.'
}
finally { Remove-Item -LiteralPath $stagingRoot -Recurse -Force -ErrorAction SilentlyContinue }
