[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$ArchivePath
)

. (Join-Path $PSScriptRoot 'checkpoint_runtime_registry.ps1')

$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$applyScript = Join-Path $PSScriptRoot 'apply_checkpoint_33.ps1'
$staticPreflight = Join-Path $PSScriptRoot 'static_preflight_checkpoint_33.ps1'
$releaseValidator = Join-Path $PSScriptRoot 'validate_checkpoint_33_release.ps1'
$runtimeRegistry = Join-Path $PSScriptRoot 'checkpoint_runtime_registry.ps1'
$archiveFullPath = [System.IO.Path]::GetFullPath((Join-Path (Get-Location) $ArchivePath))
$archiveDirectory = [System.IO.Path]::GetDirectoryName($archiveFullPath)
$stagingRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("star-cluster-checkpoint-33-prearchive-{0}" -f ([guid]::NewGuid().ToString('N')))

Register-CheckpointOperation -Name 'StaticPreflight' -Operation {
    param([string]$ScriptPath,[string]$RootPath)
    return & $ScriptPath -RepositoryRoot $RootPath
}
Assert-CheckpointOperationRegistry -RequiredNames @('StaticPreflight')

function Assert-ReleaseMetadata {
    $contracts = @(
        @{ Path = 'README.md'; Patterns = @('Checkpoint 33','v0.4e','674 engine-independent tests','294 main-power/interception correction variants') },
        @{ Path = 'Checkpoint_33_Readme.txt'; Patterns = @('complete replacement repository','Kinetic Cannon','Held Main','294 main-power/interception correction variants') },
        @{ Path = 'docs\checkpoints\Checkpoint_33_TL1_Main_Weapon_Power_And_Interception_Order_Correction.md'; Patterns = @('294 variants','Kinetic Cannon fire spends 1 TP','Held Main resolves before PDS','Shield overcapacity') },
        @{ Path = 'docs\validation\Checkpoint_33_TL1_Main_Weapon_Power_And_Interception_Order_Correction.md'; Patterns = @('674 engine-independent tests','294 main-power/interception correction variants','idempotent') }
    )
    foreach ($contract in $contracts) {
        $path = Join-Path $repositoryRoot $contract.Path
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Pre-archive metadata file is missing: $($contract.Path)" }
        foreach ($pattern in $contract.Patterns) {
            if (-not (Select-String -LiteralPath $path -SimpleMatch $pattern -Quiet)) { throw "Pre-archive metadata $($contract.Path) is missing: $pattern" }
        }
    }

    $preflightPath = Join-Path $repositoryRoot 'tools\checkpoints\checkpoint-33\static_preflight_checkpoint_33.ps1'
    if (-not (Test-Path -LiteralPath $preflightPath -PathType Leaf)) { throw 'Checkpoint 33 static preflight is missing.' }
    $preflightText = Get-Content -LiteralPath $preflightPath -Raw
    foreach ($marker in @('Get-RegisteredPhaseACase','UnusedKineticHold','a06-c02','TriggeredKineticHold','a07-c02','KineticWeaponPacket','a11-c01')) {
        if (-not $preflightText.Contains($marker)) { throw "Checkpoint 33 static preflight exact-case registry is missing: $marker" }
    }
    if ($preflightText.Contains("[string]`$_.id -match 'kinetic'")) { throw 'Checkpoint 33 static preflight retains the obsolete heuristic Kinetic case selector.' }

    $workbookPath = Join-Path $repositoryRoot 'docs\design\player_technology\StarCluster_Player_TL_Framework_Draft_v0_13.xlsx'
    if (-not (Test-Path -LiteralPath $workbookPath -PathType Leaf)) { throw 'Checkpoint 33 workbook v0.13 is missing.' }
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip = [System.IO.Compression.ZipFile]::OpenRead($workbookPath)
    try {
        $workbookEntry = $zip.GetEntry('xl/workbook.xml')
        if ($null -eq $workbookEntry) { throw 'Workbook xl/workbook.xml is missing.' }
        $reader = New-Object System.IO.StreamReader($workbookEntry.Open())
        try { $workbookXml = $reader.ReadToEnd() } finally { $reader.Dispose() }
        foreach ($sheet in @('Checkpoint 29 Matrix','Checkpoint 30 PDS','Checkpoint 31 Defense','Checkpoint 33 Correction')) {
            if (-not $workbookXml.Contains(('name="{0}"' -f $sheet))) { throw "Pre-archive workbook sheet is missing: $sheet" }
        }
        $allXml = ''
        foreach ($entry in @($zip.Entries | Where-Object { $_.FullName -like 'xl/*.xml' -or $_.FullName -like 'xl/worksheets/*.xml' })) {
            $xmlReader = New-Object System.IO.StreamReader($entry.Open())
            try { $allXml += $xmlReader.ReadToEnd() } finally { $xmlReader.Dispose() }
        }
        foreach ($marker in @('D-285','Checkpoint 33 - TL1 Main-Weapon Power and Interception-Order Correction','294 variants x 10,000 trials','Held Main then PDS','Operational +1 / Degraded +0')) {
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
    foreach ($line in Get-Content -LiteralPath '.\CHECKPOINT_33_SHA256SUMS.txt') {
        if ([string]::IsNullOrWhiteSpace($line) -or $line.StartsWith('#')) { continue }
        $match = [regex]::Match($line, '^([0-9a-fA-F]{64})  (.+)$')
        if (-not $match.Success) { throw "Malformed manifest line: $line" }
        $relativePath = $match.Groups[2].Value.Replace('/','\')
        $sourcePath = Join-Path $repositoryRoot $relativePath
        $destinationPath = Join-Path $stagingRoot $relativePath
        [void](New-Item -ItemType Directory -Path ([System.IO.Path]::GetDirectoryName($destinationPath)) -Force)
        Copy-Item -LiteralPath $sourcePath -Destination $destinationPath -Force
    }
    Copy-Item -LiteralPath '.\CHECKPOINT_33_SHA256SUMS.txt' -Destination (Join-Path $stagingRoot 'CHECKPOINT_33_SHA256SUMS.txt') -Force

    Write-Host '[7/9] Creating the complete replacement repository archive...'
    if (Test-Path -LiteralPath $archiveFullPath) { Remove-Item -LiteralPath $archiveFullPath -Force }
    Compress-Archive -Path (Join-Path $stagingRoot '*') -DestinationPath $archiveFullPath -CompressionLevel Optimal

    Write-Host '[8/9] Running the release validator against the newly created archive...'
    & $releaseValidator -ArchivePath $archiveFullPath

    Write-Host '[9/9] Writing the external SHA-256 checksum...'
    $hash = (Get-FileHash -LiteralPath $archiveFullPath -Algorithm SHA256).Hash.ToLowerInvariant()
    [System.IO.File]::WriteAllText("$archiveFullPath.sha256.txt","$hash  $([System.IO.Path]::GetFileName($archiveFullPath))`r`n",(New-Object System.Text.UTF8Encoding($false)))

    Write-Host ''
    Write-Host 'Checkpoint 33 full-repository build and release validation completed successfully.'
    Write-Host "Archive: $archiveFullPath"
    Write-Host "SHA-256: $hash"
}
finally {
    Pop-Location
    Remove-Item -LiteralPath $stagingRoot -Recurse -Force -ErrorAction SilentlyContinue
}
