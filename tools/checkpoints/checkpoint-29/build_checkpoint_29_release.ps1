[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$ArchivePath
)

$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$applyScript = Join-Path $PSScriptRoot 'apply_checkpoint_29.ps1'
$releaseValidator = Join-Path $PSScriptRoot 'validate_checkpoint_29_release.ps1'
$archiveFullPath = [System.IO.Path]::GetFullPath((Join-Path (Get-Location) $ArchivePath))
$archiveDirectory = [System.IO.Path]::GetDirectoryName($archiveFullPath)

function Assert-ReleaseMetadata {
    $readmePath = Join-Path $repositoryRoot 'README.md'
    if (-not (Test-Path -LiteralPath $readmePath -PathType Leaf)) {
        throw 'Repository README.md is missing.'
    }

    $requiredPatterns = @(
        'Checkpoint 29',
        'v0.4a',
        '48 complete weapon-matrix',
        '615 engine-independent tests',
        'Checkpoint 29e'
    )

    foreach ($pattern in $requiredPatterns) {
        if (-not (Select-String -LiteralPath $readmePath -SimpleMatch $pattern -Quiet)) {
            throw "Pre-archive release metadata is missing from README.md: $pattern"
        }
    }

    Write-Host '       Release metadata contract: passed.'
}


function Assert-WorkbookSheetContract {
    $workbookPath = Join-Path $repositoryRoot 'docs\design\player_technology\StarCluster_Player_TL_Framework_Draft_v0_9.xlsx'
    if (-not (Test-Path -LiteralPath $workbookPath -PathType Leaf)) {
        throw 'Checkpoint 29 workbook is missing.'
    }

    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $archive = [System.IO.Compression.ZipFile]::OpenRead($workbookPath)
    try {
        $entry = $archive.GetEntry('xl/workbook.xml')
        if ($null -eq $entry) { throw 'Workbook xl/workbook.xml is missing.' }
        $reader = New-Object System.IO.StreamReader($entry.Open())
        try { $workbookXml = $reader.ReadToEnd() } finally { $reader.Dispose() }
    } finally {
        $archive.Dispose()
    }

    foreach ($sheetName in @('Checkpoint 28 Energy','Checkpoint 29 Matrix')) {
        if (-not $workbookXml.Contains(('name="{0}"' -f $sheetName))) {
            throw "Pre-archive workbook sheet is missing: $sheetName"
        }
    }
    if ($workbookXml.Contains('name="Checkpoint 29 Energy"')) {
        throw 'Pre-archive workbook contains obsolete/non-authoritative sheet name: Checkpoint 29 Energy'
    }

    $allXml = ''
    $archive = [System.IO.Compression.ZipFile]::OpenRead($workbookPath)
    try {
        foreach ($xmlEntry in @($archive.Entries | Where-Object { $_.FullName -like 'xl/*.xml' -or $_.FullName -like 'xl/worksheets/*.xml' })) {
            $xmlReader = New-Object System.IO.StreamReader($xmlEntry.Open())
            try { $allXml += $xmlReader.ReadToEnd() } finally { $xmlReader.Dispose() }
        }
    } finally {
        $archive.Dispose()
    }
    foreach ($marker in @('D-257','Checkpoint 29 - Complete TL1 Weapon Matrix','48 variants x 10,000 trials','Accuracy / Guidance')) {
        if (-not $allXml.Contains($marker)) {
            throw "Pre-archive workbook marker is missing: $marker"
        }
    }

    Write-Host '       Workbook sheet-name and content-marker contract: passed.'
}


function Resolve-StaticDirectFireOutcome {
    param(
        [Parameter(Mandatory = $true)][int]$Roll,
        [Parameter(Mandatory = $true)][int]$Chance
    )

    if ($Roll -eq 1) { return 'CriticalMiss' }
    if ($Roll -eq 100) { return 'CriticalHit' }
    if ($Roll -gt (100 - $Chance)) { return 'Hit' }
    return 'Miss'
}

function Assert-PhaseBFixtureContract {
    $phaseBRoot = Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\Scenarios\TL1PhaseB'
    if (-not (Test-Path -LiteralPath $phaseBRoot -PathType Container)) {
        throw 'TL1 Phase B scenario directory is missing.'
    }

    $documents = @(Get-ChildItem -LiteralPath $phaseBRoot -Filter '*.json' -File | Sort-Object Name)
    if ($documents.Count -ne 7) {
        throw "Pre-archive Phase B document count mismatch: expected 7, actual $($documents.Count)."
    }

    $caseCount = 0
    foreach ($documentPath in $documents) {
        $document = Get-Content -LiteralPath $documentPath.FullName -Raw | ConvertFrom-Json
        foreach ($case in @($document.cases)) {
            $caseCount++
            $rangePenalty = 5 * [int]$case.rangeHexes
            $targetPenalty = if ([bool]$case.targetEvasive) { 10 } else { 0 }
            $shooterPenalty = if ([bool]$case.shooterEvasive) { 5 } else { 0 }
            $unbounded = 50 + [int]$case.weaponAccuracy + [int]$case.computerBonus - $rangePenalty - $targetPenalty - $shooterPenalty
            $calculatedChance = [Math]::Min(95, [Math]::Max(5, $unbounded))

            if ([int]$case.expectedChance -ne $calculatedChance) {
                throw "Phase B case $($case.id) expectedChance mismatch: fixture $($case.expectedChance), calculated $calculatedChance."
            }

            if ([string]$case.operation -eq 'Roll' -and -not [string]::IsNullOrWhiteSpace([string]$case.expectedOutcomeA)) {
                $calculatedOutcome = Resolve-StaticDirectFireOutcome -Roll ([int]$case.rollA) -Chance $calculatedChance
                if ([string]$case.expectedOutcomeA -ne $calculatedOutcome) {
                    throw "Phase B case $($case.id) roll outcome mismatch: fixture $($case.expectedOutcomeA), calculated $calculatedOutcome."
                }
            }

            if ([string]$case.operation -eq 'SimultaneousVolley') {
                $chanceA = $calculatedChance
                $unboundedB = 50 + [int]$case.weaponAccuracy + [int]$case.computerBonus - $rangePenalty - $(if ([bool]$case.shooterEvasive) { 10 } else { 0 }) - $(if ([bool]$case.targetEvasive) { 5 } else { 0 })
                $chanceB = [Math]::Min(95, [Math]::Max(5, $unboundedB))
                $outcomeA = Resolve-StaticDirectFireOutcome -Roll ([int]$case.rollA) -Chance $chanceA
                $outcomeB = Resolve-StaticDirectFireOutcome -Roll ([int]$case.rollB) -Chance $chanceB
                if (-not [string]::IsNullOrWhiteSpace([string]$case.expectedOutcomeA) -and [string]$case.expectedOutcomeA -ne $outcomeA) {
                    throw "Phase B case $($case.id) volley outcome A mismatch: fixture $($case.expectedOutcomeA), calculated $outcomeA."
                }
                if (-not [string]::IsNullOrWhiteSpace([string]$case.expectedOutcomeB) -and [string]$case.expectedOutcomeB -ne $outcomeB) {
                    throw "Phase B case $($case.id) volley outcome B mismatch: fixture $($case.expectedOutcomeB), calculated $outcomeB."
                }
                $aHit = $outcomeA -in @('Hit','CriticalHit')
                $bHit = $outcomeB -in @('Hit','CriticalHit')
                $calculatedHullA = [Math]::Max(0, [int]$case.hullA - $(if ($bHit) { [int]$case.damageB } else { 0 }))
                $calculatedHullB = [Math]::Max(0, [int]$case.hullB - $(if ($aHit) { [int]$case.damageA } else { 0 }))
                $calculatedMutual = ($calculatedHullA -eq 0 -and $calculatedHullB -eq 0)
                if ([int]$case.expectedHullA -ne $calculatedHullA -or [int]$case.expectedHullB -ne $calculatedHullB) {
                    throw "Phase B case $($case.id) volley hull mismatch: fixture $($case.expectedHullA)/$($case.expectedHullB), calculated $calculatedHullA/$calculatedHullB."
                }
                if ([bool]$case.expectedMutualDestruction -ne $calculatedMutual) {
                    throw "Phase B case $($case.id) mutual-destruction mismatch: fixture $($case.expectedMutualDestruction), calculated $calculatedMutual."
                }
            }
        }
    }

    if ($caseCount -ne 36) {
        throw "Pre-archive Phase B case count mismatch: expected 36, actual $caseCount."
    }

    Write-Host '       Phase B expected-chance and deterministic roll/volley fixture contract: passed.'
}

$stagingRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("star-cluster-checkpoint-29-prearchive-{0}" -f ([guid]::NewGuid().ToString('N')))

if (-not (Test-Path -LiteralPath $applyScript -PathType Leaf)) { throw 'Checkpoint 29 application script is missing.' }
if (-not (Test-Path -LiteralPath $releaseValidator -PathType Leaf)) { throw 'Checkpoint 29 release validator is missing.' }
if ([string]::IsNullOrWhiteSpace($archiveDirectory)) { throw 'Archive output directory could not be resolved.' }
[void](New-Item -ItemType Directory -Path $archiveDirectory -Force)

Push-Location $repositoryRoot
try {
    Write-Host '[1/8] Verifying release identity and required README metadata...'
    Assert-ReleaseMetadata
    Assert-WorkbookSheetContract
    Assert-PhaseBFixtureContract

    Write-Host '[2/8] Normalizing and validating the repository contract before packaging...'
    & $applyScript -RepositoryContractOnly

    Write-Host '[3/8] Running the complete warnings-as-errors acceptance suite before packaging...'
    & $applyScript

    Write-Host '[4/8] Proving the normalized repository remains idempotent...'
    & $applyScript -RepositoryContractOnly

    Write-Host '[5/8] Copying the manifest-locked repository into an isolated staging directory...'
    [void](New-Item -ItemType Directory -Path $stagingRoot -Force)
    foreach ($line in Get-Content -LiteralPath '.\CHECKPOINT_29_SHA256SUMS.txt') {
        if ([string]::IsNullOrWhiteSpace($line) -or $line.StartsWith('#')) { continue }
        $match = [regex]::Match($line, '^([0-9a-fA-F]{64})  (.+)$')
        if (-not $match.Success) { throw "Malformed manifest line: $line" }
        $relativePath = $match.Groups[2].Value.Replace('/','\')
        $sourcePath = Join-Path $repositoryRoot $relativePath
        $destinationPath = Join-Path $stagingRoot $relativePath
        [void](New-Item -ItemType Directory -Path ([System.IO.Path]::GetDirectoryName($destinationPath)) -Force)
        Copy-Item -LiteralPath $sourcePath -Destination $destinationPath -Force
    }
    Copy-Item -LiteralPath '.\CHECKPOINT_29_SHA256SUMS.txt' -Destination (Join-Path $stagingRoot 'CHECKPOINT_29_SHA256SUMS.txt') -Force

    Write-Host '[6/8] Creating the ZIP only after the pre-archive acceptance gate passes...'
    if (Test-Path -LiteralPath $archiveFullPath) { Remove-Item -LiteralPath $archiveFullPath -Force }
    Compress-Archive -Path (Join-Path $stagingRoot '*') -DestinationPath $archiveFullPath -CompressionLevel Optimal

    Write-Host '[7/8] Running the release validator against the newly created archive...'
    & $releaseValidator -ArchivePath $archiveFullPath

    Write-Host '[8/8] Writing the external SHA-256 checksum...'
    $hash = (Get-FileHash -LiteralPath $archiveFullPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $checksumPath = "$archiveFullPath.sha256.txt"
    [System.IO.File]::WriteAllText($checksumPath,"$hash  $([System.IO.Path]::GetFileName($archiveFullPath))`r`n",(New-Object System.Text.UTF8Encoding($false)))

    Write-Host ''
    Write-Host 'Checkpoint 29e pre-archive build and release validation completed successfully.'
    Write-Host "Archive: $archiveFullPath"
    Write-Host "SHA-256: $hash"
}
finally {
    Pop-Location
    Remove-Item -LiteralPath $stagingRoot -Recurse -Force -ErrorAction SilentlyContinue
}
