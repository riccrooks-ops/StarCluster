[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$ArchivePath,
    [switch]$RepositoryContractOnly
)

. (Join-Path $PSScriptRoot 'checkpoint_runtime_registry.ps1')

$ErrorActionPreference = 'Stop'
$resolvedArchive = (Resolve-Path -LiteralPath $ArchivePath).Path
$stagingRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("star-cluster-checkpoint-32-release-{0}" -f ([guid]::NewGuid().ToString('N')))

Register-CheckpointOperation -Name 'StaticPreflight' -Operation {
    param([string]$ScriptPath,[string]$RootPath)
    return & $ScriptPath -RepositoryRoot $RootPath
}
Assert-CheckpointOperationRegistry -RequiredNames @('StaticPreflight')

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

        $manifestEntry = $zip.GetEntry('CHECKPOINT_32_SHA256SUMS.txt')
        if ($null -eq $manifestEntry) { throw 'Archive repository manifest is missing.' }
        $reader = New-Object System.IO.StreamReader($manifestEntry.Open())
        try { $manifestText = $reader.ReadToEnd() } finally { $reader.Dispose() }

        $manifest = @{}
        foreach ($line in ($manifestText -split '\r?\n')) {
            if ([string]::IsNullOrWhiteSpace($line) -or $line.StartsWith('#')) { continue }
            $match = [regex]::Match($line, '^([0-9a-fA-F]{64})  (.+)$')
            if (-not $match.Success) { throw "Malformed archive manifest line: $line" }
            $name = $match.Groups[2].Value.Replace('\','/')
            if ($name -eq 'CHECKPOINT_32_SHA256SUMS.txt') { throw 'Archive manifest must not contain itself.' }
            if ($manifest.ContainsKey($name)) { throw "Duplicate archive manifest path: $name" }
            $manifest[$name] = $match.Groups[1].Value.ToLowerInvariant()
        }
        if ($manifest.Count -ne 659) { throw "Checkpoint 32 archive manifest must contain exactly 659 files; found $($manifest.Count)." }

        $actualNames = @($entries | ForEach-Object { $_.FullName.Replace('\','/') } | Where-Object { $_ -ne 'CHECKPOINT_32_SHA256SUMS.txt' })
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
    $checkpointScript = Join-Path $stagingRoot 'tools\checkpoints\checkpoint-32\apply_checkpoint_32.ps1'
    $staticPreflight = Join-Path $stagingRoot 'tools\checkpoints\checkpoint-32\static_preflight_checkpoint_32.ps1'
    $runtimeRegistry = Join-Path $stagingRoot 'tools\checkpoints\checkpoint-32\checkpoint_runtime_registry.ps1'
    if (-not (Test-Path -LiteralPath $checkpointScript -PathType Leaf)) { throw "Checkpoint 32 application script was not found in $resolvedArchive." }
    if (-not (Test-Path -LiteralPath $staticPreflight -PathType Leaf)) { throw "Checkpoint 32 static preflight was not found in $resolvedArchive." }
    if (-not (Test-Path -LiteralPath $runtimeRegistry -PathType Leaf)) { throw "Checkpoint 32 runtime registry was not found in $resolvedArchive." }

    Write-Host '[2/5] Running clean-extraction environment-independent preflight...'
    Invoke-CheckpointOperation -Name 'StaticPreflight' -Arguments @($staticPreflight,$stagingRoot)

    Write-Host '[3/5] Running clean-extraction repository contracts...'
    & $checkpointScript -RepositoryContractOnly

    if (-not $RepositoryContractOnly) {
        Write-Host '[4/5] Running clean build, 668 tests, retained lanes, 504 power variants, and self-tests...'
        & $checkpointScript
    }
    else {
        Write-Host '[4/5] Full Windows acceptance intentionally skipped by -RepositoryContractOnly.'
    }

    Write-Host '[5/5] Proving clean-extraction repository contracts remain idempotent...'
    & $checkpointScript -RepositoryContractOnly

    Write-Host ''
    Write-Host 'Checkpoint 32 release validation completed successfully.'
    Write-Host 'Archive integrity, clean extraction, repository contracts, idempotence, and requested acceptance depth passed.'
}
finally { Remove-Item -LiteralPath $stagingRoot -Recurse -Force -ErrorAction SilentlyContinue }
