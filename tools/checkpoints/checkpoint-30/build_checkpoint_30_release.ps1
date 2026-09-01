[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$ArchivePath
)

$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$applyScript = Join-Path $PSScriptRoot 'apply_checkpoint_30.ps1'
$releaseValidator = Join-Path $PSScriptRoot 'validate_checkpoint_30_release.ps1'
$archiveFullPath = [System.IO.Path]::GetFullPath((Join-Path (Get-Location) $ArchivePath))
$archiveDirectory = [System.IO.Path]::GetDirectoryName($archiveFullPath)
$stagingRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("star-cluster-checkpoint-30-prearchive-{0}" -f ([guid]::NewGuid().ToString('N')))

function Assert-ReleaseMetadata {
    $contracts = @(
        @{ Path = 'README.md'; Patterns = @('Checkpoint 30','v0.4b','59 PDS/interception variants','627 engine-independent tests') },
        @{ Path = 'Checkpoint_30_Readme.txt'; Patterns = @('Checkpoint 30','PDS','59') },
        @{ Path = 'docs\checkpoints\Checkpoint_30_TL1_PDS_And_Missile_Interception_Calibration.md'; Patterns = @('59-variant','Kinetic PDS','AMM PDS','Energy PDS') },
        @{ Path = 'docs\validation\Checkpoint_30_TL1_PDS_And_Missile_Interception_Calibration.md'; Patterns = @('627 engine-independent tests','59 PDS/interception variants','idempotent') }
    )
    foreach ($contract in $contracts) {
        $path = Join-Path $repositoryRoot $contract.Path
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Pre-archive metadata file is missing: $($contract.Path)" }
        foreach ($pattern in $contract.Patterns) {
            if (-not (Select-String -LiteralPath $path -SimpleMatch $pattern -Quiet)) { throw "Pre-archive metadata $($contract.Path) is missing: $pattern" }
        }
    }
    Write-Host '       Release metadata contract: passed.'
}

function Assert-WorkbookContract {
    $path = Join-Path $repositoryRoot 'docs\design\player_technology\StarCluster_Player_TL_Framework_Draft_v0_10.xlsx'
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw 'Checkpoint 30 workbook is missing.' }
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip = [System.IO.Compression.ZipFile]::OpenRead($path)
    try {
        $workbookEntry = $zip.GetEntry('xl/workbook.xml')
        if ($null -eq $workbookEntry) { throw 'Workbook xl/workbook.xml is missing.' }
        $reader = New-Object System.IO.StreamReader($workbookEntry.Open())
        try { $workbookXml = $reader.ReadToEnd() } finally { $reader.Dispose() }
        foreach ($sheet in @('Checkpoint 28 Energy','Checkpoint 29 Matrix','Checkpoint 30 PDS')) {
            if (-not $workbookXml.Contains(('name="{0}"' -f $sheet))) { throw "Pre-archive workbook sheet is missing: $sheet" }
        }
        $allXml = ''
        foreach ($entry in @($zip.Entries | Where-Object { $_.FullName -like 'xl/*.xml' -or $_.FullName -like 'xl/worksheets/*.xml' })) {
            $xmlReader = New-Object System.IO.StreamReader($entry.Open())
            try { $allXml += $xmlReader.ReadToEnd() } finally { $xmlReader.Dispose() }
        }
        foreach ($marker in @('D-261','Checkpoint 30 - TL1 PDS and Interception Calibration','59 variants x 10,000 trials','Reaction Capacity')) {
            if (-not $allXml.Contains($marker)) { throw "Pre-archive workbook marker is missing: $marker" }
        }
        if (@($zip.Entries | Where-Object { $_.FullName -like 'xl/tables/*' }).Count -ne 0) { throw 'Pre-archive workbook contains prohibited structured table parts.' }
    }
    finally { $zip.Dispose() }
    Write-Host '       Workbook sheet-name and content-marker contract: passed.'
}

if (-not (Test-Path -LiteralPath $applyScript -PathType Leaf)) { throw 'Checkpoint 30 application script is missing.' }
if (-not (Test-Path -LiteralPath $releaseValidator -PathType Leaf)) { throw 'Checkpoint 30 release validator is missing.' }
if ([string]::IsNullOrWhiteSpace($archiveDirectory)) { throw 'Archive output directory could not be resolved.' }
[void](New-Item -ItemType Directory -Path $archiveDirectory -Force)

Push-Location $repositoryRoot
try {
    Write-Host '[1/8] Verifying release identity, documentation, and workbook metadata...'
    Assert-ReleaseMetadata
    Assert-WorkbookContract

    Write-Host '[2/8] Running all static repository/content/schema/semantic contracts...'
    & $applyScript -RepositoryContractOnly

    Write-Host '[3/8] Running the complete Windows warnings-as-errors acceptance suite...'
    & $applyScript

    Write-Host '[4/8] Proving the normalized repository remains idempotent...'
    & $applyScript -RepositoryContractOnly

    Write-Host '[5/8] Copying the manifest-locked repository into isolated staging...'
    [void](New-Item -ItemType Directory -Path $stagingRoot -Force)
    foreach ($line in Get-Content -LiteralPath '.\CHECKPOINT_30_SHA256SUMS.txt') {
        if ([string]::IsNullOrWhiteSpace($line) -or $line.StartsWith('#')) { continue }
        $match = [regex]::Match($line, '^([0-9a-fA-F]{64})  (.+)$')
        if (-not $match.Success) { throw "Malformed manifest line: $line" }
        $relativePath = $match.Groups[2].Value.Replace('/','\')
        $sourcePath = Join-Path $repositoryRoot $relativePath
        $destinationPath = Join-Path $stagingRoot $relativePath
        [void](New-Item -ItemType Directory -Path ([System.IO.Path]::GetDirectoryName($destinationPath)) -Force)
        Copy-Item -LiteralPath $sourcePath -Destination $destinationPath -Force
    }
    Copy-Item -LiteralPath '.\CHECKPOINT_30_SHA256SUMS.txt' -Destination (Join-Path $stagingRoot 'CHECKPOINT_30_SHA256SUMS.txt') -Force

    Write-Host '[6/8] Creating the ZIP only after pre-archive acceptance passes...'
    if (Test-Path -LiteralPath $archiveFullPath) { Remove-Item -LiteralPath $archiveFullPath -Force }
    Compress-Archive -Path (Join-Path $stagingRoot '*') -DestinationPath $archiveFullPath -CompressionLevel Optimal

    Write-Host '[7/8] Running the release validator against the newly created archive...'
    & $releaseValidator -ArchivePath $archiveFullPath

    Write-Host '[8/8] Writing the external SHA-256 checksum...'
    $hash = (Get-FileHash -LiteralPath $archiveFullPath -Algorithm SHA256).Hash.ToLowerInvariant()
    [System.IO.File]::WriteAllText("$archiveFullPath.sha256.txt","$hash  $([System.IO.Path]::GetFileName($archiveFullPath))`r`n",(New-Object System.Text.UTF8Encoding($false)))

    Write-Host ''
    Write-Host 'Checkpoint 30 pre-archive build and release validation completed successfully.'
    Write-Host "Archive: $archiveFullPath"
    Write-Host "SHA-256: $hash"
}
finally {
    Pop-Location
    Remove-Item -LiteralPath $stagingRoot -Recurse -Force -ErrorAction SilentlyContinue
}
