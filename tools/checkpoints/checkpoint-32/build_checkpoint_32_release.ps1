[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$ArchivePath
)

. (Join-Path $PSScriptRoot 'checkpoint_runtime_registry.ps1')

$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$applyScript = Join-Path $PSScriptRoot 'apply_checkpoint_32.ps1'
$staticPreflight = Join-Path $PSScriptRoot 'static_preflight_checkpoint_32.ps1'
$releaseValidator = Join-Path $PSScriptRoot 'validate_checkpoint_32_release.ps1'
$runtimeRegistry = Join-Path $PSScriptRoot 'checkpoint_runtime_registry.ps1'
$archiveFullPath = [System.IO.Path]::GetFullPath((Join-Path (Get-Location) $ArchivePath))
$archiveDirectory = [System.IO.Path]::GetDirectoryName($archiveFullPath)
$stagingRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("star-cluster-checkpoint-32-prearchive-{0}" -f ([guid]::NewGuid().ToString('N')))

Register-CheckpointOperation -Name 'StaticPreflight' -Operation {
    param([string]$ScriptPath,[string]$RootPath)
    return & $ScriptPath -RepositoryRoot $RootPath
}
Assert-CheckpointOperationRegistry -RequiredNames @('StaticPreflight')

function Assert-ReleaseMetadata {
    $contracts = @(
        @{ Path = 'README.md'; Patterns = @('Checkpoint 32','v0.4d','668 engine-independent tests','504 Tactical Power/reactor-envelope variants') },
        @{ Path = 'Checkpoint_32_Readme.txt'; Patterns = @('complete replacement repository','Capacitor','Held Interception','504 Tactical Power/reactor-envelope variants') },
        @{ Path = 'docs\checkpoints\Checkpoint_32_TL1_Tactical_Power_Completion_And_Reactor_Envelope_Calibration.md'; Patterns = @('504 variants','Held Interception','Auxiliary Reactor','Shield Battery') },
        @{ Path = 'docs\validation\Checkpoint_32_TL1_Tactical_Power_Completion_And_Reactor_Envelope_Calibration.md'; Patterns = @('668 engine-independent tests','504 Tactical Power/reactor-envelope variants','idempotent') }
    )
    foreach ($contract in $contracts) {
        $path = Join-Path $repositoryRoot $contract.Path
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Pre-archive metadata file is missing: $($contract.Path)" }
        foreach ($pattern in $contract.Patterns) {
            if (-not (Select-String -LiteralPath $path -SimpleMatch $pattern -Quiet)) { throw "Pre-archive metadata $($contract.Path) is missing: $pattern" }
        }
    }

    $workbookPath = Join-Path $repositoryRoot 'docs\design\player_technology\StarCluster_Player_TL_Framework_Draft_v0_12.xlsx'
    if (-not (Test-Path -LiteralPath $workbookPath -PathType Leaf)) { throw 'Checkpoint 32 workbook v0.12 is missing.' }
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip = [System.IO.Compression.ZipFile]::OpenRead($workbookPath)
    try {
        $workbookEntry = $zip.GetEntry('xl/workbook.xml')
        if ($null -eq $workbookEntry) { throw 'Workbook xl/workbook.xml is missing.' }
        $reader = New-Object System.IO.StreamReader($workbookEntry.Open())
        try { $workbookXml = $reader.ReadToEnd() } finally { $reader.Dispose() }
        foreach ($sheet in @('Checkpoint 29 Matrix','Checkpoint 30 PDS','Checkpoint 31 Defense','Checkpoint 32 Power')) {
            if (-not $workbookXml.Contains(('name="{0}"' -f $sheet))) { throw "Pre-archive workbook sheet is missing: $sheet" }
        }
        $allXml = ''
        foreach ($entry in @($zip.Entries | Where-Object { $_.FullName -like 'xl/*.xml' -or $_.FullName -like 'xl/worksheets/*.xml' })) {
            $xmlReader = New-Object System.IO.StreamReader($entry.Open())
            try { $allXml += $xmlReader.ReadToEnd() } finally { $xmlReader.Dispose() }
        }
        foreach ($marker in @('D-278','Checkpoint 32 - TL1 Tactical Power Completion and Reactor Envelope Calibration','504 variants x 10,000 trials','Capacity 3 / charge 1 / discharge 2','full after FTL')) {
            if (-not $allXml.Contains($marker)) { throw "Pre-archive workbook marker is missing: $marker" }
        }
        if (@($zip.Entries | Where-Object { $_.FullName -like 'xl/tables/*' }).Count -ne 0) { throw 'Pre-archive workbook contains prohibited structured table parts.' }
    }
    finally { $zip.Dispose() }
    Write-Host '       Release metadata and workbook contracts: passed.'
}

foreach ($path in @($applyScript,$staticPreflight,$releaseValidator,$runtimeRegistry)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Required release tool is missing: $path" }
}
if ([string]::IsNullOrWhiteSpace($archiveDirectory)) { throw 'Archive output directory could not be resolved.' }
[void](New-Item -ItemType Directory -Path $archiveDirectory -Force)

Push-Location $repositoryRoot
try {
    Write-Host '[1/9] Verifying release identity, documentation, and workbook metadata...'
    Assert-ReleaseMetadata

    Write-Host '[2/9] Running the environment-independent static preflight...'
    Invoke-CheckpointOperation -Name 'StaticPreflight' -Arguments @($staticPreflight,$repositoryRoot)

    Write-Host '[3/9] Running all repository/content/schema/source contracts...'
    & $applyScript -RepositoryContractOnly

    Write-Host '[4/9] Running the complete Windows warnings-as-errors acceptance suite...'
    & $applyScript

    Write-Host '[5/9] Proving the normalized repository remains idempotent...'
    & $applyScript -RepositoryContractOnly

    Write-Host '[6/9] Copying the manifest-locked repository into isolated staging...'
    [void](New-Item -ItemType Directory -Path $stagingRoot -Force)
    foreach ($line in Get-Content -LiteralPath '.\CHECKPOINT_32_SHA256SUMS.txt') {
        if ([string]::IsNullOrWhiteSpace($line) -or $line.StartsWith('#')) { continue }
        $match = [regex]::Match($line, '^([0-9a-fA-F]{64})  (.+)$')
        if (-not $match.Success) { throw "Malformed manifest line: $line" }
        $relativePath = $match.Groups[2].Value.Replace('/','\')
        $sourcePath = Join-Path $repositoryRoot $relativePath
        $destinationPath = Join-Path $stagingRoot $relativePath
        [void](New-Item -ItemType Directory -Path ([System.IO.Path]::GetDirectoryName($destinationPath)) -Force)
        Copy-Item -LiteralPath $sourcePath -Destination $destinationPath -Force
    }
    Copy-Item -LiteralPath '.\CHECKPOINT_32_SHA256SUMS.txt' -Destination (Join-Path $stagingRoot 'CHECKPOINT_32_SHA256SUMS.txt') -Force

    Write-Host '[7/9] Creating the complete replacement repository archive...'
    if (Test-Path -LiteralPath $archiveFullPath) { Remove-Item -LiteralPath $archiveFullPath -Force }
    Compress-Archive -Path (Join-Path $stagingRoot '*') -DestinationPath $archiveFullPath -CompressionLevel Optimal

    Write-Host '[8/9] Running the release validator against the newly created archive...'
    & $releaseValidator -ArchivePath $archiveFullPath

    Write-Host '[9/9] Writing the external SHA-256 checksum...'
    $hash = (Get-FileHash -LiteralPath $archiveFullPath -Algorithm SHA256).Hash.ToLowerInvariant()
    [System.IO.File]::WriteAllText("$archiveFullPath.sha256.txt","$hash  $([System.IO.Path]::GetFileName($archiveFullPath))`r`n",(New-Object System.Text.UTF8Encoding($false)))

    Write-Host ''
    Write-Host 'Checkpoint 32 full-repository build and release validation completed successfully.'
    Write-Host "Archive: $archiveFullPath"
    Write-Host "SHA-256: $hash"
}
finally {
    Pop-Location
    Remove-Item -LiteralPath $stagingRoot -Recurse -Force -ErrorAction SilentlyContinue
}
