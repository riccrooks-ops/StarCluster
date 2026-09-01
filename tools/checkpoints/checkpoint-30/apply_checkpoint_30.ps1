[CmdletBinding()]
param(
    [switch]$RepositoryContractOnly
)

$ErrorActionPreference = 'Stop'
$repositoryRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
Push-Location $repositoryRoot

function Assert-FileContains {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string[]]$Patterns,
        [Parameter(Mandatory = $true)][string]$Description
    )
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "$Description file $Path was not found."
    }
    foreach ($pattern in $Patterns) {
        if (-not (Select-String -LiteralPath $Path -SimpleMatch $pattern -Quiet)) {
            throw "$Description is missing required content: $pattern"
        }
    }
}

function Assert-FileNotContains {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string[]]$Patterns,
        [Parameter(Mandatory = $true)][string]$Description
    )
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "$Description file $Path was not found." }
    foreach ($pattern in $Patterns) {
        if (Select-String -LiteralPath $Path -SimpleMatch $pattern -Quiet) {
            throw "$Description contains prohibited legacy content: $pattern"
        }
    }
}

function Assert-DocxContains {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string[]]$Patterns,
        [Parameter(Mandatory = $true)][string]$Description
    )
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "$Description file $Path was not found." }
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip = [System.IO.Compression.ZipFile]::OpenRead((Resolve-Path -LiteralPath $Path).Path)
    try {
        $entry = $zip.GetEntry('word/document.xml')
        if ($null -eq $entry) { throw "$Description has no word/document.xml." }
        $reader = New-Object System.IO.StreamReader($entry.Open())
        try { $xmlText = $reader.ReadToEnd() } finally { $reader.Dispose() }
        $xml = New-Object System.Xml.XmlDocument
        $xml.PreserveWhitespace = $false
        $xml.LoadXml($xmlText)
        $ns = New-Object System.Xml.XmlNamespaceManager($xml.NameTable)
        $ns.AddNamespace('w','http://schemas.openxmlformats.org/wordprocessingml/2006/main')
        $plainText = (($xml.SelectNodes('//w:t',$ns) | ForEach-Object { $_.InnerText }) -join ' ') -replace '\s+',' '
        foreach ($pattern in $Patterns) {
            if (-not $plainText.Contains($pattern)) { throw "$Description is missing required content: $pattern" }
        }
    }
    finally { $zip.Dispose() }
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

function Assert-PhaseBStaticSemanticContracts {
    param(
        [Parameter(Mandatory = $true)][string]$ScenarioDirectory
    )

    $documents = @(Get-ChildItem -LiteralPath $ScenarioDirectory -Filter '*.json' -File | Sort-Object Name)
    if ($documents.Count -ne 7) {
        throw "Expected 7 TL1 Phase B scenario documents, found $($documents.Count)."
    }

    $caseCount = 0
    foreach ($documentPath in $documents) {
        $document = Get-Content -LiteralPath $documentPath.FullName -Raw | ConvertFrom-Json
        foreach ($case in @($document.cases)) {
            $caseCount++
            $rangePenalty = 5 * [int]$case.rangeHexes
            $targetPenaltyA = if ([bool]$case.targetEvasive) { 10 } else { 0 }
            $shooterPenaltyA = if ([bool]$case.shooterEvasive) { 5 } else { 0 }
            $unboundedA = 50 + [int]$case.weaponAccuracy + [int]$case.computerBonus - $rangePenalty - $targetPenaltyA - $shooterPenaltyA
            $chanceA = [Math]::Min(95, [Math]::Max(5, $unboundedA))

            if ([int]$case.expectedChance -ne $chanceA) {
                throw "Phase B case $($case.id) expectedChance mismatch: fixture $($case.expectedChance), calculated $chanceA."
            }

            if ([string]$case.operation -eq 'Roll' -and -not [string]::IsNullOrWhiteSpace([string]$case.expectedOutcomeA)) {
                $outcomeA = Resolve-StaticDirectFireOutcome -Roll ([int]$case.rollA) -Chance $chanceA
                if ([string]$case.expectedOutcomeA -ne $outcomeA) {
                    throw "Phase B case $($case.id) roll outcome mismatch: fixture $($case.expectedOutcomeA), calculated $outcomeA."
                }
            }

            if ([string]$case.operation -eq 'SimultaneousVolley') {
                $targetPenaltyB = if ([bool]$case.shooterEvasive) { 10 } else { 0 }
                $shooterPenaltyB = if ([bool]$case.targetEvasive) { 5 } else { 0 }
                $unboundedB = 50 + [int]$case.weaponAccuracy + [int]$case.computerBonus - $rangePenalty - $targetPenaltyB - $shooterPenaltyB
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
                $damageToA = if ($bHit) { [int]$case.damageB } else { 0 }
                $damageToB = if ($aHit) { [int]$case.damageA } else { 0 }
                $calculatedHullA = [Math]::Max(0, [int]$case.hullA - $damageToA)
                $calculatedHullB = [Math]::Max(0, [int]$case.hullB - $damageToB)
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
        throw "Expected 36 TL1 Phase B cases, found $caseCount."
    }

    Write-Host '       TL1 Phase B static semantics: 36 expected chances and deterministic roll/volley contracts verified.'
}

function Get-NormalizedRelativePath {
    param(
        [Parameter(Mandatory = $true)][string]$BasePath,
        [Parameter(Mandatory = $true)][string]$FullPath
    )

    # Windows PowerShell 5.1 runs on .NET Framework, which does not provide
    # System.IO.Path.GetRelativePath. Normalize both paths with APIs available
    # on .NET Framework and remove the verified repository prefix directly.
    $baseFullPath = [System.IO.Path]::GetFullPath($BasePath)
    $directorySeparator = [System.IO.Path]::DirectorySeparatorChar.ToString()
    $alternateSeparator = [System.IO.Path]::AltDirectorySeparatorChar.ToString()
    if (-not $baseFullPath.EndsWith($directorySeparator) -and -not $baseFullPath.EndsWith($alternateSeparator)) {
        $baseFullPath += $directorySeparator
    }

    $targetFullPath = [System.IO.Path]::GetFullPath($FullPath)
    if (-not $targetFullPath.StartsWith($baseFullPath,[System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Path $targetFullPath is outside repository root $baseFullPath."
    }

    $relativePath = $targetFullPath.Substring($baseFullPath.Length).Replace('\','/')
    if ([string]::IsNullOrWhiteSpace($relativePath) -or $relativePath.StartsWith('../')) {
        throw "Could not derive a safe repository-relative path for $targetFullPath."
    }
    return $relativePath
}

function Test-NormalizedRelativePathCompatibility {
    $testRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("star-cluster-checkpoint-30-relative-path-test-{0}" -f ([guid]::NewGuid().ToString('N')))
    $nestedPath = Join-Path (Join-Path $testRoot 'nested') 'example.txt'
    $relativePath = Get-NormalizedRelativePath -BasePath $testRoot -FullPath $nestedPath
    if ($relativePath -ne 'nested/example.txt') {
        throw "Windows PowerShell-compatible relative-path self-test returned $relativePath."
    }
    Write-Host '       Windows PowerShell relative-path compatibility self-test: passed.'
}


function Test-IsAllowedUnmanifestedPath {
    param([Parameter(Mandatory = $true)][string]$RelativePath)

    $path = $RelativePath.Replace('\','/')
    if ($path -like '.git/*' -or
        $path -like '.vs/*' -or
        $path -like '.vscode/*' -or
        $path -like '.idea/*' -or
        $path -like 'out/*' -or
        $path -like 'src/StarCluster.Game/.godot/*' -or
        $path -match '(^|/)(bin|obj|TestResults)/') {
        return $true
    }

    if ($path -match '\.(user|userosscache|sln\.docstates|uid)$' -or
        $path -match '(^|/)\.suo$' -or
        $path -match '(^|/)(\.DS_Store|Thumbs\.db)$') {
        return $true
    }

    if ($path -notmatch '/') {
        if ($path -match '^Checkpoint_.*Readme\.txt$' -or
            $path -match '^CHECKPOINT_.*SHA256SUMS\.txt$' -or
            $path -match '\.zip(\.sha256\.txt)?$' -or
            $path -eq 'collect_checkpoint_23_missing_baseline_files.ps1' -or
            $path -eq 'collect_checkpoint_23a_missing_baseline_files.ps1' -or
            $path -eq 'Checkpoint_23_Missing_Baseline_Capture_Instructions.txt' -or
            $path -eq 'Checkpoint_23a_Missing_Baseline_Capture_Instructions.txt') {
            return $true
        }
    }

    return $false
}

function Test-RepositoryManifestLocalArtifactPolicy {
    $allowed = @(
        '.vs/StarCluster/v17/.suo',
        'src/StarCluster.Game/.godot/editor/project_metadata.cfg',
        'src/StarCluster.Game/Scripts/Main.cs.uid',
        'src/StarCluster.Core/bin/Debug/example.dll',
        'tests/StarCluster.Tests/obj/project.assets.json',
        'out/checkpoint-27/example.txt',
        'Checkpoint_22a_Hotfix_Readme.txt',
        'Checkpoint_22d_Readme.txt',
        'CHECKPOINT_22D_SHA256SUMS.txt',
        'StarCluster_Checkpoint_22d_Local_Copy.zip',
        'collect_checkpoint_23_missing_baseline_files.ps1'
    )
    foreach ($path in $allowed) {
        if (-not (Test-IsAllowedUnmanifestedPath -RelativePath $path)) {
            throw "Local-artifact policy rejected allowed path $path."
        }
    }

    $rejected = @(
        'src/StarCluster.Core/Geometry/UnexpectedSource.cs',
        'tests/StarCluster.Tests/UnexpectedTests.cs',
        'tools/checkpoints/unexpected.ps1',
        'docs/unexpected-design-file.md'
    )
    foreach ($path in $rejected) {
        if (Test-IsAllowedUnmanifestedPath -RelativePath $path) {
            throw "Local-artifact policy incorrectly allowed repository-owned path $path."
        }
    }
    Write-Host '       Repository local-artifact policy self-test: passed.'
}

function Ensure-ActiveConceptDocument {
    param(
        [Parameter(Mandatory = $true)][string]$DocsDirectory,
        [Parameter(Mandatory = $true)][string]$ExpectedFileName,
        [Parameter(Mandatory = $true)][string]$ArchiveDirectory
    )

    $expectedPath = Join-Path $DocsDirectory $ExpectedFileName
    if (-not (Test-Path -LiteralPath $expectedPath -PathType Leaf)) {
        throw "Expected active concept document $expectedPath was not found."
    }

    $staleConcepts = @(Get-ChildItem -LiteralPath $DocsDirectory -Filter 'Star_Cluster_Game_Concept_v*.docx' -File |
        Where-Object { $_.Name -ne $ExpectedFileName })
    if ($staleConcepts.Count -gt 0) {
        [void](New-Item -ItemType Directory -Path $ArchiveDirectory -Force)
        foreach ($staleConcept in $staleConcepts) {
            $archivePath = Join-Path $ArchiveDirectory $staleConcept.Name
            if (Test-Path -LiteralPath $archivePath -PathType Leaf) {
                $sourceHash = (Get-FileHash -LiteralPath $staleConcept.FullName -Algorithm SHA256).Hash
                $archiveHash = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash
                if ($sourceHash -eq $archiveHash) {
                    Remove-Item -LiteralPath $staleConcept.FullName -Force
                    Write-Host ("       Removed duplicate stale active concept: {0}" -f $staleConcept.Name)
                    continue
                }
                $baseName = [System.IO.Path]::GetFileNameWithoutExtension($staleConcept.Name)
                $extension = [System.IO.Path]::GetExtension($staleConcept.Name)
                $archiveName = "{0}_Imported_{1}{2}" -f $baseName,([guid]::NewGuid().ToString('N')),$extension
                $archivePath = Join-Path $ArchiveDirectory $archiveName
            }
            Move-Item -LiteralPath $staleConcept.FullName -Destination $archivePath -Force
            Write-Host ("       Archived stale active concept: {0}" -f $staleConcept.Name)
        }
    }

    $activeConcepts = @(Get-ChildItem -LiteralPath $DocsDirectory -Filter 'Star_Cluster_Game_Concept_v*.docx' -File)
    if ($activeConcepts.Count -ne 1 -or $activeConcepts[0].Name -ne $ExpectedFileName) {
        $activeNames = @($activeConcepts | ForEach-Object { $_.Name }) -join ', '
        throw "Exactly the Checkpoint 30 concept document must remain active. Found: $activeNames"
    }
    Write-Host "       Active concept document: $ExpectedFileName"
}

function Test-ActiveConceptDocumentNormalization {
    $testRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("star-cluster-checkpoint-30-concept-test-{0}" -f ([guid]::NewGuid().ToString('N')))
    $docsDirectory = Join-Path $testRoot 'docs'
    $archiveDirectory = Join-Path $docsDirectory 'archive'
    $expectedName = 'Star_Cluster_Game_Concept_v0.4b.docx'
    $duplicateName = 'Star_Cluster_Game_Concept_v0.3v.docx'
    $importName = 'Star_Cluster_Game_Concept_v0.3u.docx'
    try {
        [void](New-Item -ItemType Directory -Path $docsDirectory -Force)
        [void](New-Item -ItemType Directory -Path $archiveDirectory -Force)
        Set-Content -LiteralPath (Join-Path $docsDirectory $expectedName) -Value 'expected' -Encoding UTF8
        Set-Content -LiteralPath (Join-Path $docsDirectory $duplicateName) -Value 'duplicate' -Encoding UTF8
        Set-Content -LiteralPath (Join-Path $archiveDirectory $duplicateName) -Value 'duplicate' -Encoding UTF8
        Set-Content -LiteralPath (Join-Path $docsDirectory $importName) -Value 'stale-active-copy' -Encoding UTF8
        Set-Content -LiteralPath (Join-Path $archiveDirectory $importName) -Value 'different-archived-copy' -Encoding UTF8

        Ensure-ActiveConceptDocument -DocsDirectory $docsDirectory -ExpectedFileName $expectedName -ArchiveDirectory $archiveDirectory
        $remaining = @(Get-ChildItem -LiteralPath $docsDirectory -Filter 'Star_Cluster_Game_Concept_v*.docx' -File)
        $imported = @(Get-ChildItem -LiteralPath $archiveDirectory -Filter 'Star_Cluster_Game_Concept_v0.3u_Imported_*.docx' -File)
        if ($remaining.Count -ne 1 -or $remaining[0].Name -ne $expectedName -or $imported.Count -ne 1) {
            throw 'Concept-document normalization self-test failed.'
        }
        Write-Host '       Concept-document normalization self-test: passed.'
    }
    finally { Remove-Item -LiteralPath $testRoot -Recurse -Force -ErrorAction SilentlyContinue }
}

function Assert-RepositoryManifest {
    param([Parameter(Mandatory = $true)][string]$ManifestPath)
    if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) {
        throw "Repository manifest $ManifestPath was not found."
    }
    $manifestEntries = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
    $verified = 0
    foreach ($line in Get-Content -LiteralPath $ManifestPath) {
        if ([string]::IsNullOrWhiteSpace($line) -or $line.StartsWith('#')) { continue }
        $manifestMatch = [regex]::Match($line, '^([0-9a-fA-F]{64})  (.+)$')
        if (-not $manifestMatch.Success) { throw "Malformed repository manifest line: $line" }
        $expectedHash = $manifestMatch.Groups[1].Value.ToLowerInvariant()
        $relativePath = $manifestMatch.Groups[2].Value.Replace('\','/')
        if ([System.IO.Path]::IsPathRooted($relativePath) -or $relativePath.Split('/') -contains '..') {
            throw "Unsafe repository manifest path: $relativePath"
        }
        if ($relativePath -eq 'CHECKPOINT_30_SHA256SUMS.txt') {
            throw 'The repository manifest must not contain its own checksum file.'
        }
        if (-not $manifestEntries.Add($relativePath)) { throw "Duplicate repository manifest path: $relativePath" }
        if (-not (Test-Path -LiteralPath $relativePath -PathType Leaf)) {
            throw "Manifest file $relativePath was not found."
        }
        $actualHash = (Get-FileHash -LiteralPath $relativePath -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actualHash -ne $expectedHash) {
            throw "Manifest hash mismatch for ${relativePath}: $actualHash expected $expectedHash."
        }
        $verified++
    }
    if ($verified -ne 625) { throw "Repository manifest verified $verified files; the Checkpoint 30 archive requires exactly 625 files." }

    $manifestFullPath = (Resolve-Path -LiteralPath $ManifestPath).Path
    $unexpectedFiles = @()
    $ignoredLocalFiles = @()
    foreach ($file in Get-ChildItem -LiteralPath $repositoryRoot.Path -File -Recurse -Force) {
        if ($file.FullName -eq $manifestFullPath) { continue }
        $relative = Get-NormalizedRelativePath -BasePath $repositoryRoot.Path -FullPath $file.FullName
        if ($manifestEntries.Contains($relative)) { continue }
        if (Test-IsAllowedUnmanifestedPath -RelativePath $relative) {
            $ignoredLocalFiles += $relative
            continue
        }
        $unexpectedFiles += $relative
    }
    if ($unexpectedFiles.Count -gt 0) {
        throw ("Repository contains repository-owned files not locked by the manifest:`n{0}" -f (($unexpectedFiles | Sort-Object) -join "`n"))
    }
    if ($manifestEntries.Count -ne $verified) { throw 'Repository manifest entry accounting failed.' }
    Write-Host "       Repository manifest: $verified files verified; no unexpected repository-owned files."
    if ($ignoredLocalFiles.Count -gt 0) {
        Write-Host ("       Ignored local/generated artifacts: {0}." -f $ignoredLocalFiles.Count)
    }
}

function Assert-PowerShellScriptsParse {
    param([Parameter(Mandatory = $true)][string]$RootPath)
    $parseFailures = @()
    $scriptCount = 0
    foreach ($scriptFile in Get-ChildItem -LiteralPath $RootPath -Filter '*.ps1' -File -Recurse) {
        $tokens = $null
        $parseErrors = $null
        [void][System.Management.Automation.Language.Parser]::ParseFile($scriptFile.FullName,[ref]$tokens,[ref]$parseErrors)
        $scriptCount++
        foreach ($parseError in @($parseErrors | Where-Object { $null -ne $_ })) {
            $relativeScriptPath = Resolve-Path -LiteralPath $scriptFile.FullName -Relative
            $parseFailures += ("{0}:{1}:{2}: {3}" -f $relativeScriptPath,$parseError.Extent.StartLineNumber,$parseError.Extent.StartColumnNumber,$parseError.Message)
        }
    }
    if ($parseFailures.Count -gt 0) { throw ("PowerShell parser rejected the repository scripts:`n{0}" -f ($parseFailures -join "`n")) }
    Write-Host "       PowerShell parser: $scriptCount scripts parsed successfully."
}

function Ensure-ActiveValidationRunbook {
    param(
        [Parameter(Mandatory = $true)][string]$ValidationDirectory,
        [Parameter(Mandatory = $true)][string]$ExpectedFileName,
        [Parameter(Mandatory = $true)][string]$ArchiveDirectory
    )
    $expectedPath = Join-Path $ValidationDirectory $ExpectedFileName
    if (-not (Test-Path -LiteralPath $expectedPath -PathType Leaf)) { throw "Expected active validation runbook $expectedPath was not found." }
    $staleRunbooks = @(Get-ChildItem -LiteralPath $ValidationDirectory -Filter 'Checkpoint_*.md' -File | Where-Object { $_.Name -ne $ExpectedFileName })
    if ($staleRunbooks.Count -gt 0) {
        [void](New-Item -ItemType Directory -Path $ArchiveDirectory -Force)
        foreach ($staleRunbook in $staleRunbooks) {
            $archivePath = Join-Path $ArchiveDirectory $staleRunbook.Name
            if (Test-Path -LiteralPath $archivePath -PathType Leaf) {
                $sourceHash = (Get-FileHash -LiteralPath $staleRunbook.FullName -Algorithm SHA256).Hash
                $archiveHash = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash
                if ($sourceHash -eq $archiveHash) {
                    Remove-Item -LiteralPath $staleRunbook.FullName -Force
                    Write-Host ("       Removed duplicate stale active runbook: {0}" -f $staleRunbook.Name)
                    continue
                }
                $baseName = [System.IO.Path]::GetFileNameWithoutExtension($staleRunbook.Name)
                $extension = [System.IO.Path]::GetExtension($staleRunbook.Name)
                $archiveName = "{0}_Imported_{1}{2}" -f $baseName,([guid]::NewGuid().ToString('N')),$extension
                $archivePath = Join-Path $ArchiveDirectory $archiveName
            }
            Move-Item -LiteralPath $staleRunbook.FullName -Destination $archivePath -Force
            Write-Host ("       Archived stale active runbook: {0}" -f $staleRunbook.Name)
        }
    }
    $activeRunbooks = @(Get-ChildItem -LiteralPath $ValidationDirectory -Filter 'Checkpoint_*.md' -File)
    if ($activeRunbooks.Count -ne 1 -or $activeRunbooks[0].Name -ne $ExpectedFileName) {
        $activeNames = @($activeRunbooks | ForEach-Object { $_.Name }) -join ', '
        throw "Exactly the Checkpoint 30 validation runbook must remain active. Found: $activeNames"
    }
    Write-Host "       Active validation runbook: $ExpectedFileName"
}

function Test-ActiveValidationRunbookNormalization {
    $testRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("star-cluster-checkpoint-30-runbook-test-{0}" -f ([guid]::NewGuid().ToString('N')))
    $validationDirectory = Join-Path $testRoot 'validation'
    $archiveDirectory = Join-Path $validationDirectory 'archive'
    $expectedName = 'Checkpoint_30_TL1_PDS_And_Missile_Interception_Calibration.md'
    $staleName = 'Checkpoint_24_Unified_Tactical_Power_Component_State_And_TL1_Core_Combat_Test_Foundation.md'
    try {
        [void](New-Item -ItemType Directory -Path $validationDirectory -Force)
        [void](New-Item -ItemType Directory -Path $archiveDirectory -Force)
        Set-Content -LiteralPath (Join-Path $validationDirectory $expectedName) -Value 'expected' -Encoding UTF8
        Set-Content -LiteralPath (Join-Path $validationDirectory $staleName) -Value 'stale-active-copy' -Encoding UTF8
        Set-Content -LiteralPath (Join-Path $archiveDirectory $staleName) -Value 'different-archived-copy' -Encoding UTF8
        Ensure-ActiveValidationRunbook -ValidationDirectory $validationDirectory -ExpectedFileName $expectedName -ArchiveDirectory $archiveDirectory
        $remaining = @(Get-ChildItem -LiteralPath $validationDirectory -Filter 'Checkpoint_*.md' -File)
        $imported = @(Get-ChildItem -LiteralPath $archiveDirectory -Filter 'Checkpoint_24_Unified_Tactical_Power_Component_State_And_TL1_Core_Combat_Test_Foundation_Imported_*.md' -File)
        if ($remaining.Count -ne 1 -or $remaining[0].Name -ne $expectedName -or $imported.Count -ne 1) { throw 'Validation-runbook normalization self-test failed.' }
        Write-Host '       Validation-runbook normalization self-test: passed.'
    }
    finally { Remove-Item -LiteralPath $testRoot -Recurse -Force -ErrorAction SilentlyContinue }
}

function Assert-ReferenceHashes {
    $hashPath = '.\docs\references\SHA256SUMS.txt'
    $verified = 0
    foreach ($line in Get-Content -LiteralPath $hashPath) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        $m = [regex]::Match($line, '^([0-9a-fA-F]{64})  (.+)$')
        if (-not $m.Success) { throw "Malformed reference hash line: $line" }
        $file = Join-Path '.\docs\references' $m.Groups[2].Value
        if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw "Reference file $file was not found." }
        $actual = (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actual -ne $m.Groups[1].Value.ToLowerInvariant()) { throw "Reference hash mismatch for $file." }
        $verified++
    }
    if ($verified -ne 14) { throw "Expected 14 hashed reference files including README.md; found $verified." }
    Write-Host "       Reference library: $verified files hash-verified."
}


function Assert-TechnologyCsvContracts {
    $componentPath = '.\docs\design\player_technology\player_tl_components_draft_v0_3.csv'
    $profilePath = '.\docs\design\player_technology\player_tl_compatibility_profiles_draft_v0_3.csv'
    $libraryPath = '.\docs\design\player_technology\player_reference_library_v0_1.csv'
    $insightPath = '.\docs\design\player_technology\player_reference_insights_v0_1.csv'
    $reconPath = '.\docs\design\player_technology\player_tl_design_reconciliation_v0_3.csv'
    $baselinePath = '.\docs\archive\player_technology\pre-cp165-active\tl1_core_combat_numerical_baseline_v0_1.csv'
    $loadoutPath = '.\docs\design\player_technology\tl1_core_combat_loadouts_v0_1.csv'
    $scenarioPath = '.\docs\design\player_technology\tl1_core_combat_test_scenarios_v0_2.csv'

    $components = @(Import-Csv -LiteralPath $componentPath)
    if ($components.Count -ne 99) { throw "Expected 99 player components; found $($components.Count)." }
    if (($components | Select-Object -ExpandProperty component_id -Unique).Count -ne 99) { throw 'Component IDs are not unique.' }
    $families = @($components | Group-Object component_family_id)
    if ($families.Count -ne 11) { throw "Expected 11 component families; found $($families.Count)." }
    foreach ($family in $families) {
        if ($family.Count -ne 9) { throw "Family $($family.Name) does not contain exactly nine TL rows." }
        $levels = @($family.Group | ForEach-Object { [int]$_.tl } | Sort-Object)
        if (($levels -join ',') -ne '1,2,3,4,5,6,7,8,9') { throw "Family $($family.Name) does not cover TL 1-9 exactly once." }
    }
    if (@($components | Where-Object { [string]::IsNullOrWhiteSpace($_.originality_guardrail) }).Count -ne 0) { throw 'Every component row must carry an originality guardrail.' }

    $profiles = @(Import-Csv -LiteralPath $profilePath)
    if ($profiles.Count -ne 11) { throw "Expected 11 compatibility profiles; found $($profiles.Count)." }
    $profileIds = @($profiles | ForEach-Object { $_.compatibility_profile_id })
    foreach ($component in $components) {
        if ($profileIds -notcontains $component.compatibility_profile_id) { throw "Component $($component.component_id) references unknown compatibility profile $($component.compatibility_profile_id)." }
    }

    $library = @(Import-Csv -LiteralPath $libraryPath)
    if ($library.Count -ne 13) { throw "Expected 13 external reference records; found $($library.Count)." }
    foreach ($source in $library) {
        if (-not (Test-Path -LiteralPath $source.project_path -PathType Leaf)) { throw "Reference inventory path $($source.project_path) was not found." }
        $actual = (Get-FileHash -LiteralPath $source.project_path -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actual -ne $source.sha256.ToLowerInvariant()) { throw "Reference inventory hash mismatch for $($source.file_name)." }
    }

    $insights = @(Import-Csv -LiteralPath $insightPath)
    if ($insights.Count -ne 40) { throw "Expected 40 reference insights; found $($insights.Count)." }
    $sourceIds = @($library | ForEach-Object { $_.source_id })
    foreach ($insight in $insights) {
        if ($sourceIds -notcontains $insight.source_id) { throw "Insight $($insight.insight_id) references unknown source $($insight.source_id)." }
    }

    $recon = @(Import-Csv -LiteralPath $reconPath)
    if ($recon.Count -ne 32) { throw "Expected 32 player-technology reconciliation rows; found $($recon.Count)." }
    if (($recon[0].PSObject.Properties.Name -join ',') -ne 'topic,current_direction,reference_influence,checkpoint_25_decision,status,next_action') { throw 'Player-technology reconciliation header is invalid.' }

    $baseline = @(Import-Csv -LiteralPath $baselinePath)
    if ($baseline.Count -ne 126) { throw "Expected 126 TL1 baseline rows; found $($baseline.Count)." }
    if (($baseline[0].PSObject.Properties.Name -join ',') -ne 'section,parameter_id,display_name,value,unit,applies_to,status,rationale,test_signal') { throw 'TL1 baseline header is invalid.' }
    if (($baseline | Select-Object -ExpandProperty parameter_id -Unique).Count -ne 126) { throw 'TL1 baseline parameter IDs are not unique.' }
    $baselineHash = (Get-FileHash -LiteralPath $baselinePath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($baselineHash -ne '11913725247f43c7a11c4d5fd06a2182586ca0d91d49abd9236af5b398088dcb') { throw "TL1 baseline SHA-256 is $baselineHash, not the accepted TL1 baseline hash." }
    $requiredValues = @{
        'hull_points'='12'; 'crew_pristine'='100'; 'marine_pristine'='10';
        'minimum_operating_crew'='10'; 'reactor_output'='5'; 'stl_move'='4';
        'armor_protection'='0'; 'armor_integrity'='4'; 'shield_capacity'='2';
        'kinetic_damage'='3'; 'kinetic_spen'='1'; 'kinetic_apen'='0';
        'kinetic_ammo'='100'; 'missile_ammo'='24'
    }
    foreach ($id in $requiredValues.Keys) {
        $row = @($baseline | Where-Object { $_.parameter_id -eq $id })
        if ($row.Count -ne 1 -or $row[0].value -ne $requiredValues[$id]) { throw "TL1 baseline value $id must equal $($requiredValues[$id])." }
    }

    $loadouts = @(Import-Csv -LiteralPath $loadoutPath)
    if ($loadouts.Count -ne 13) { throw "Expected 13 TL1 loadouts; found $($loadouts.Count)." }
    if (($loadouts | Select-Object -ExpandProperty loadout_id -Unique).Count -ne 13) { throw 'TL1 loadout IDs are not unique.' }

    $scenarios = @(Import-Csv -LiteralPath $scenarioPath)
    if ($scenarios.Count -ne 62) { throw "Expected 62 TL1 scenarios; found $($scenarios.Count)." }
    $expectedHeader = 'scenario_id,phase,name,baseline_version,side_a_fixture,side_b_fixture,starting_range_hexes,starting_tracks,doctrine,changed_variable,relevance_context,trial_mode,minimum_trials,primary_metrics,acceptance_question,implementation_status,runtime_scenario_file,runtime_case_count'
    if (($scenarios[0].PSObject.Properties.Name -join ',') -ne $expectedHeader) { throw 'TL1 scenario matrix v0.2 header is invalid.' }
    if (($scenarios | Select-Object -ExpandProperty scenario_id -Unique).Count -ne 62) { throw 'TL1 scenario IDs are not unique.' }
    foreach ($phase in @('A Mechanics','B Core duels','C PDS','D EW','E Power','F Damage','G Movement')) {
        if (@($scenarios | Where-Object { $_.phase -eq $phase }).Count -eq 0) { throw "TL1 scenario phase $phase is missing." }
    }

    Write-Host "       Technology/test data: 99 components, 11 profiles, 13 references, 40 insights, 32 reconciliations, 126 baseline values, 13 loadouts, 62 scenarios."
}

function Assert-Tl1ScenarioCorpusContracts {
    $scenarioDirectory = '.\src\StarCluster.ScenarioRunner\Scenarios\TL1PhaseA'
    $matrixPath = '.\docs\design\player_technology\tl1_core_combat_test_scenarios_v0_2.csv'
    $schemaPath = '.\docs\design\player_technology\tl1_phase_a_scenario_schema_v0_1.json'
    $expectedHash = '11913725247f43c7a11c4d5fd06a2182586ca0d91d49abd9236af5b398088dcb'
    $supportedOperations = @('resolveDamage','turnStartRecharge','powerScript','heldInterception','reactorEnvelope','reactorOverload','resetState','weaponFire','chargedWeaponScript')

    $schemaText = Get-Content -LiteralPath $schemaPath -Raw
    foreach ($marker in @('star-cluster-tl1-phase-a-v1','baselineSha256','matrixScenarioId','resolveDamage','chargedWeaponScript')) {
        if (-not $schemaText.Contains($marker)) { throw "TL1 scenario schema is missing $marker." }
    }
    $schema = $schemaText | ConvertFrom-Json
    if ($schema.type -ne 'object') { throw 'TL1 scenario schema root type must be object.' }

    $files = @(Get-ChildItem -LiteralPath $scenarioDirectory -Filter '*.json' -File | Sort-Object Name)
    if ($files.Count -ne 12) { throw "Expected 12 TL1 Phase A scenario documents; found $($files.Count)." }
    $ids = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
    $caseIds = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
    $matrixIds = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
    $documentsByMatrixId = @{}
    $caseTotal = 0
    foreach ($file in $files) {
        $document = Get-Content -LiteralPath $file.FullName -Raw | ConvertFrom-Json
        if ($document.schemaVersion -ne 'star-cluster-tl1-phase-a-v1') { throw "$($file.Name) has an invalid schemaVersion." }
        if (-not $ids.Add([string]$document.id)) { throw "Duplicate TL1 Phase A document ID $($document.id)." }
        if (-not $matrixIds.Add([string]$document.matrixScenarioId)) { throw "Duplicate matrixScenarioId $($document.matrixScenarioId)." }
        if ($document.baselineVersion -ne 'tl1-core-combat-v0.1') { throw "$($file.Name) has an invalid baselineVersion." }
        if ($document.baselineSha256.ToLowerInvariant() -ne $expectedHash) { throw "$($file.Name) has an invalid baselineSha256." }
        $cases = @($document.cases)
        if ($cases.Count -lt 1) { throw "$($file.Name) has no mechanics cases." }
        foreach ($case in $cases) {
            if (-not $caseIds.Add([string]$case.id)) { throw "Duplicate TL1 Phase A case ID $($case.id)." }
            if ($supportedOperations -notcontains [string]$case.operation) { throw "Case $($case.id) uses unsupported operation $($case.operation)." }
            if ($null -eq $case.input -or $null -eq $case.expected) { throw "Case $($case.id) lacks input or expected data." }
        }
        $caseTotal += $cases.Count
        $documentsByMatrixId[[string]$document.matrixScenarioId] = @{
            RelativePath = Get-NormalizedRelativePath -BasePath $repositoryRoot.Path -FullPath $file.FullName
            CaseCount = $cases.Count
        }
    }
    if ($caseTotal -ne 54) { throw "Expected 54 TL1 Phase A mechanics cases; found $caseTotal." }

    $matrix = @(Import-Csv -LiteralPath $matrixPath)
    $implemented = @($matrix | Where-Object { $_.implementation_status -eq 'implemented_checkpoint_25' })
    if ($implemented.Count -ne 12) { throw "Expected 12 implemented Phase A matrix rows; found $($implemented.Count)." }
    foreach ($row in $implemented) {
        if (-not $documentsByMatrixId.ContainsKey($row.scenario_id)) { throw "Matrix row $($row.scenario_id) has no runtime scenario document." }
        $contract = $documentsByMatrixId[$row.scenario_id]
        if ($row.runtime_scenario_file.Replace('\','/') -ne $contract.RelativePath) { throw "Matrix row $($row.scenario_id) runtime path does not match $($contract.RelativePath)." }
        if ([int]$row.runtime_case_count -ne [int]$contract.CaseCount) { throw "Matrix row $($row.scenario_id) case count does not match its runtime document." }
    }

    Write-Host "       TL1 Phase A corpus: 12 documents, 54 unique mechanics cases, exact baseline hash, matrix links, and supported operations verified."
}

function Assert-PdsStudyContracts {
    $studyPath = '.\src\StarCluster.ScenarioRunner\Scenarios\TL1Calibration\tl1-pds01-interception-study.json'
    $schemaPath = '.\docs\design\player_technology\tl1_pds_calibration_schema_v0_1.json'
    $baselinePath = '.\docs\archive\player_technology\pre-cp165-active\tl1_core_combat_numerical_baseline_v0_1.csv'
    $expectedBaselineHash = '11913725247f43c7a11c4d5fd06a2182586ca0d91d49abd9236af5b398088dcb'

    $study = Get-Content -LiteralPath $studyPath -Raw | ConvertFrom-Json
    $schema = Get-Content -LiteralPath $schemaPath -Raw | ConvertFrom-Json
    if ($study.schemaVersion -ne 'star-cluster-tl1-pds-calibration-v1') { throw 'PDS study schemaVersion is invalid.' }
    if ($schema.'$id' -ne 'star-cluster-tl1-pds-calibration-v1') { throw 'PDS JSON schema ID is invalid.' }
    if ([int]$schema.properties.variants.minItems -ne 59 -or [int]$schema.properties.variants.maxItems -ne 59) { throw 'PDS JSON schema must require exactly 59 variants.' }
    if ($study.baselineSha256.ToLowerInvariant() -ne $expectedBaselineHash) { throw 'PDS study baselineSha256 is invalid.' }
    $actualBaselineHash = (Get-FileHash -LiteralPath $baselinePath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actualBaselineHash -ne $expectedBaselineHash) { throw 'PDS study does not reference the packaged accepted baseline.' }
    if ([int]$study.trialsPerVariant -ne 10000) { throw 'PDS study must default to 10,000 trials per variant.' }

    $variants = @($study.variants)
    if ($variants.Count -ne 59) { throw "Expected 59 PDS variants; found $($variants.Count)." }
    $byId = @{}
    foreach ($variant in $variants) {
        $id = [string]$variant.id
        if ([string]::IsNullOrWhiteSpace($id)) { throw 'PDS variant has an empty ID.' }
        if ($byId.ContainsKey($id)) { throw "Duplicate PDS variant ID $id." }
        $byId[$id] = $variant
    }
    foreach ($variant in $variants) {
        $pairId = [string]$variant.pairId
        if ([string]::IsNullOrWhiteSpace($pairId)) { continue }
        if (-not $byId.ContainsKey($pairId)) { throw "PDS variant $($variant.id) references missing pair $pairId." }
        if ([string]$byId[$pairId].pairId -ne [string]$variant.id) { throw "PDS pair $($variant.id)/$pairId is not reciprocal." }
    }

    foreach ($requiredId in @(
        'pds-k-no-threat','pds-e-no-threat',
        'pds-kpds-v-m-r0','pds-kpds-v-m-r2','pds-kpds-v-m-r4',
        'pds-ammpds-v-m-r0','pds-ammpds-v-m-r2','pds-ammpds-v-m-r4',
        'pds-epds-v-m-r0','pds-epds-v-m-r2','pds-epds-v-m-r4',
        'pds-e-v-m-control-r2','pds-e-kpds-v-m-r2','pds-e-ammpds-v-m-r2','pds-e-epds-v-m-r2',
        'pds-k-v-saturation-r2','pds-kpds-v-saturation-r2','pds-ammpds-v-saturation-r2','pds-epds-v-saturation-r2',
        'pds-kpds-chance20-r2','pds-kpds-chance50-r2','pds-kpds-reaction2-r2','pds-kpds-ammo2-r2',
        'pds-kpds-unpowered-r2','pds-kpds-evm-v-m-r2',
        'pds-mm-both-kpds-r2','pds-mm-both-ammpds-r2','pds-mm-both-epds-r2',
        'pds-mm-one-kpds-r2','pds-mm-one-ammpds-r2','pds-mm-one-epds-r2')) {
        if (-not $byId.ContainsKey($requiredId)) { throw "Required PDS variant $requiredId is missing." }
    }

    function Assert-PdsSideValue {
        param([object]$Side,[string]$Family,[int]$Power,[int]$Reaction,[int]$Chance,[int]$Ammo,[bool]$Unlimited,[string]$Context)
        if ([string]$Side.pdsFamily -ne $Family -or [int]$Side.pdsPowerCost -ne $Power -or
            [int]$Side.pdsReactionCapacity -ne $Reaction -or [int]$Side.pdsInterceptionChance -ne $Chance -or
            [int]$Side.pdsAmmunition -ne $Ammo -or [bool]$Side.pdsUnlimitedAmmunition -ne $Unlimited) {
            throw "$Context does not match its canonical PDS profile."
        }
    }

    Assert-PdsSideValue $byId['pds-kpds-v-m-r2'].sideA 'kinetic' 1 1 35 12 $false 'Kinetic PDS'
    Assert-PdsSideValue $byId['pds-ammpds-v-m-r2'].sideA 'amm' 1 1 50 6 $false 'AMM PDS'
    Assert-PdsSideValue $byId['pds-epds-v-m-r2'].sideA 'energy' 2 1 40 0 $true 'Energy PDS'

    $saturation = $byId['pds-kpds-v-saturation-r2']
    if ([int]$saturation.sideB.missileLaunchesPerTurn -ne 2 -or [int]$saturation.sideA.pdsReactionCapacity -ne 1) { throw 'Saturation control must launch two missiles per turn against Reaction Capacity 1.' }
    if ([int]$byId['pds-kpds-reaction2-r2'].sideA.pdsReactionCapacity -ne 2) { throw 'Reaction Capacity 2 control is invalid.' }
    if ([int]$byId['pds-kpds-ammo2-r2'].sideA.pdsAmmunition -ne 2) { throw 'Finite PDS ammunition control is invalid.' }
    if ([int]$byId['pds-kpds-unpowered-r2'].sideA.reactorOutput -ge [int]$byId['pds-kpds-unpowered-r2'].sideA.pdsPowerCost) { throw 'Unpowered PDS control does not actually starve PDS power.' }

    Write-Host '       TL1 PDS study: 59 variants, reciprocal pairs, baseline hash, canonical PDS profiles, and boundary controls verified.'
}

function Assert-WorkbookContract {
    $path = '.\docs\design\player_technology\StarCluster_Player_TL_Framework_Draft_v0_10.xlsx'
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw 'Technology workbook v0.10 was not found.' }
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip = [System.IO.Compression.ZipFile]::OpenRead((Resolve-Path -LiteralPath $path).Path)
    try {
        $entryNames = @($zip.Entries | ForEach-Object { $_.FullName })
        if (@($entryNames | Where-Object { $_ -like 'xl/tables/*' }).Count -ne 0) { throw 'Workbook contains structured table parts; these are intentionally prohibited.' }
        $workbookEntry = $zip.GetEntry('xl/workbook.xml')
        if ($null -eq $workbookEntry) { throw 'Workbook XML is missing.' }
        $reader = New-Object System.IO.StreamReader($workbookEntry.Open())
        try { $workbookXml = $reader.ReadToEnd() } finally { $reader.Dispose() }
        $requiredSheets = @('Overview','TL1 Baseline','TL1 Loadouts','TL1 Test Matrix','Phase A Runtime','TL1 Phase B','TL1 Calibration','Checkpoint 28 Energy','Checkpoint 29 Matrix','Checkpoint 30 PDS','Component Schema','Checkpoint 25 Plan','TL Matrix','Components','Compatibility Profiles','Adaptation Rules','Reference Library','Reference Insights','Design Reconciliation','Level Themes','Design Decisions','Sources Used')
        foreach ($sheetName in $requiredSheets) {
            if (-not $workbookXml.Contains(('name="{0}"' -f $sheetName))) { throw "Workbook sheet $sheetName is missing." }
        }
        $allXml = ''
        foreach ($entry in @($zip.Entries | Where-Object { $_.FullName -like 'xl/*.xml' -or $_.FullName -like 'xl/worksheets/*.xml' })) {
            $entryReader = New-Object System.IO.StreamReader($entry.Open())
            try { $allXml += $entryReader.ReadToEnd() } finally { $entryReader.Dispose() }
        }
        foreach ($marker in @('D-257','Checkpoint 29 - Complete TL1 Weapon Matrix','48 variants x 10,000 trials','Accuracy / Guidance','D-261','Checkpoint 30 - TL1 PDS and Interception Calibration','59 variants x 10,000 trials','Reaction Capacity')) {
            if (-not $allXml.Contains($marker)) { throw "Workbook does not contain required marker $marker." }
        }
    }
    finally { $zip.Dispose() }
    Write-Host '       Workbook OOXML: retained Checkpoint 29 Matrix and new Checkpoint 30 PDS sheets, Decisions D-257/D-261, and no structured table parts verified.'
}

function Assert-NewUnitTestContracts {
    $directPath = '.\tests\StarCluster.Tests\Combat\DirectFire\Tl1DirectFireAccuracyTests.cs'
    $kineticPath = '.\tests\StarCluster.Tests\Combat\DirectFire\Tl1KineticDuelCalibrationTests.cs'
    $energyPath = '.\tests\StarCluster.Tests\Combat\DirectFire\Tl1EnergyDuelCalibrationTests.cs'
    $matrixPath = '.\tests\StarCluster.Tests\Combat\DirectFire\Tl1WeaponMatrixTests.cs'
    $pdsPath = '.\tests\StarCluster.Tests\Combat\DirectFire\Tl1PdsCalibrationTests.cs'
    foreach ($path in @($directPath,$kineticPath,$energyPath,$matrixPath,$pdsPath)) {
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Required unit-test source $path was not found." }
    }
    $directFacts = @(Select-String -LiteralPath $directPath -SimpleMatch '[Fact]').Count
    $directTheories = @(Select-String -LiteralPath $directPath -SimpleMatch '[Theory]').Count
    $kineticFacts = @(Select-String -LiteralPath $kineticPath -SimpleMatch '[Fact]').Count
    $energyFacts = @(Select-String -LiteralPath $energyPath -SimpleMatch '[Fact]').Count
    $matrixFacts = @(Select-String -LiteralPath $matrixPath -SimpleMatch '[Fact]').Count
    $pdsFacts = @(Select-String -LiteralPath $pdsPath -SimpleMatch '[Fact]').Count
    if ($directFacts -ne 10 -or $directTheories -ne 3 -or $kineticFacts -ne 8 -or $energyFacts -ne 10 -or $matrixFacts -ne 8 -or $pdsFacts -ne 12) {
        throw "Unit-test source counts differ from the Checkpoint 30 contract: direct $directFacts/$directTheories, kinetic $kineticFacts, energy $energyFacts, matrix $matrixFacts, PDS $pdsFacts."
    }
    Assert-FileContains $pdsPath @('Pds_readiness_locks_power_before_weapon_commitment','Kinetic_pds_consumes_ammunition_on_a_miss','Reaction_capacity_one_allows_one_attempt_against_saturation','Unpowered_pds_does_not_attempt_interception','Own_evm_reduces_pds_chance_by_five_points') 'Checkpoint 30 PDS tests'
    Write-Host '       Checkpoint 30 unit-test source: 10 direct-fire facts, 3 theories, 8 kinetic, 10 energy, 8 matrix, and 12 PDS facts present.'
}

function Invoke-Runner {
    param([Parameter(Mandatory = $true)][string[]]$Arguments,[Parameter(Mandatory = $true)][string]$Description)
    $dotnetArguments = @('run','--project','.\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj','--no-build','--') + $Arguments
    $output = & dotnet @dotnetArguments 2>&1
    $output | Write-Host
    if ($LASTEXITCODE -ne 0) { throw "$Description failed with exit code $LASTEXITCODE." }
    return ($output | Out-String)
}


try {
    Write-Host '[1/13] Verifying complete Checkpoint 30 repository and parser contracts...'
    foreach ($requiredFile in @(
        '.\StarCluster.sln',
        '.\global.json',
        '.\CHECKPOINT_30_SHA256SUMS.txt',
        '.\Checkpoint_30_Readme.txt',
        '.\README.md',
        '.\docs\Star_Cluster_Game_Concept_v0.4b.docx',
        '.\docs\archive\Star_Cluster_Game_Concept_v0.4a.docx',
        '.\docs\checkpoints\Checkpoint_30_TL1_PDS_And_Missile_Interception_Calibration.md',
        '.\docs\validation\Checkpoint_30_TL1_PDS_And_Missile_Interception_Calibration.md',
        '.\docs\validation\archive\Checkpoint_29_Revised_Evasive_Maneuvering_And_Complete_TL1_Weapon_Matrix.md',
        '.\docs\design\player_technology\StarCluster_Player_TL_Framework_Draft_v0_10.xlsx',
        '.\docs\design\player_technology\TL1_PDS_And_Interception_Calibration_Plan_v0_1.md',
        '.\docs\design\player_technology\tl1_pds_calibration_schema_v0_1.json',
        '.\docs\archive\player_technology\pre-cp165-active\tl1_core_combat_numerical_baseline_v0_1.csv',
        '.\docs\design\player_technology\tl1_core_combat_test_scenarios_v0_2.csv',
        '.\src\StarCluster.Core\Combat\DirectFire\Tl1WeaponMatrixSimulator.cs',
        '.\src\StarCluster.ScenarioRunner\Program.cs',
        '.\src\StarCluster.ScenarioRunner\TL1Calibration\Tl1PdsCalibrationDocuments.cs',
        '.\src\StarCluster.ScenarioRunner\TL1Calibration\Tl1PdsCalibrationRunner.cs',
        '.\src\StarCluster.ScenarioRunner\Scenarios\TL1Calibration\tl1-pds01-interception-study.json',
        '.\tests\StarCluster.Tests\Combat\DirectFire\Tl1PdsCalibrationTests.cs',
        '.\tools\checkpoints\checkpoint-30\static_preflight_checkpoint_30.py',
        '.\tools\checkpoints\checkpoint-30\build_checkpoint_30_release.ps1',
        '.\tools\checkpoints\checkpoint-30\validate_checkpoint_30_release.ps1',
        '.\src\StarCluster.ScenarioRunner\Scenarios\TL1Calibration\tl1-kc01-kinetic-interaction-study.json',
        '.\src\StarCluster.ScenarioRunner\Scenarios\TL1Calibration\tl1-ec01-energy-interaction-study.json',
        '.\src\StarCluster.ScenarioRunner\Scenarios\TL1Calibration\tl1-wm01-complete-weapon-matrix.json',
        '.\docs\references\SHA256SUMS.txt')) {
        if (-not (Test-Path -LiteralPath $requiredFile -PathType Leaf)) { throw "Required Checkpoint 30 file $requiredFile was not found." }
    }

    Ensure-ActiveValidationRunbook -ValidationDirectory '.\docs\validation' -ExpectedFileName 'Checkpoint_30_TL1_PDS_And_Missile_Interception_Calibration.md' -ArchiveDirectory '.\docs\validation\archive'
    Ensure-ActiveConceptDocument -DocsDirectory '.\docs' -ExpectedFileName 'Star_Cluster_Game_Concept_v0.4b.docx' -ArchiveDirectory '.\docs\archive'
    Test-NormalizedRelativePathCompatibility
    Test-RepositoryManifestLocalArtifactPolicy
    Assert-RepositoryManifest '.\CHECKPOINT_30_SHA256SUMS.txt'
    Assert-PowerShellScriptsParse '.\tools'
    Test-ActiveValidationRunbookNormalization
    Test-ActiveConceptDocumentNormalization

    Write-Host '[2/13] Verifying Concept, reference library, exact data, schemas, corpora, tests, and workbook contracts...'
    Assert-FileContains '.\README.md' @('Checkpoint 30','v0.4b','59 PDS/interception variants','627 engine-independent tests') 'Repository README'
    Assert-FileContains '.\docs\checkpoints\Checkpoint_30_TL1_PDS_And_Missile_Interception_Calibration.md' @('59-variant','Kinetic PDS','AMM PDS','Energy PDS','ECM') 'Checkpoint 30 documentation'
    Assert-FileContains '.\docs\validation\Checkpoint_30_TL1_PDS_And_Missile_Interception_Calibration.md' @('627 engine-independent tests','59 PDS/interception variants','zero failed gates','idempotent') 'Checkpoint 30 validation runbook'
    Assert-FileContains '.\docs\Prototype_TODO.md' @('Checkpoint 30 status','59 paired PDS/interception variants','ECM/ECCM') 'Prototype TODO'
    Assert-FileContains '.\docs\design\player_technology\README.md' @('TL1_PDS_And_Interception_Calibration_Plan_v0_1.md','tl1_pds_calibration_schema_v0_1.json','StarCluster_Player_TL_Framework_Draft_v0_10.xlsx') 'Player-technology README'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\README.md' @('tl1-pds-calibration-preflight','tl1-pds-calibration','checkpoint-30-tl1-pds-calibration') 'ScenarioRunner README'
    Assert-DocxContains '.\docs\Star_Cluster_Game_Concept_v0.4b.docx' @(
        'Checkpoint 30 - TL1 PDS and Missile-Interception Calibration',
        'Kinetic PDS requires 1 Powered Tactical Power',
        'Anti-Missile Missile (AMM) PDS requires 1 Powered Tactical Power',
        'Energy PDS requires 2 Powered Tactical Power',
        'D-258','D-261','END OF DRAFT v0.4b') 'Concept v0.4b'
    Assert-FileContains '.\src\StarCluster.Core\Combat\DirectFire\Tl1WeaponMatrixSimulator.cs' @('PdsReactionCapacity','PdsInterceptionChance','PdsPowerCommittedA','ResolvePdsAgainstMissile','MissilesReachedGuidanceA') 'TL1 PDS simulator'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\TL1Calibration\Tl1PdsCalibrationRunner.cs' @('TL1 PDS Calibration preflight','tl1-pds-common-interception','mirror-side-bias','side-swap-intercepts','variants.csv') 'TL1 PDS runner'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\Program.cs' @('tl1-pds-calibration','tl1-pds-calibration-preflight','checkpoint-30-tl1-pds-calibration') 'ScenarioRunner PDS command routing'

    $kineticStudy = Get-Content -LiteralPath '.\src\StarCluster.ScenarioRunner\Scenarios\TL1Calibration\tl1-kc01-kinetic-interaction-study.json' -Raw | ConvertFrom-Json
    if (@($kineticStudy.variants).Count -ne 29) { throw "Expected 29 kinetic variants; found $(@($kineticStudy.variants).Count)." }
    $energyStudy = Get-Content -LiteralPath '.\src\StarCluster.ScenarioRunner\Scenarios\TL1Calibration\tl1-ec01-energy-interaction-study.json' -Raw | ConvertFrom-Json
    if (@($energyStudy.variants).Count -ne 31) { throw "Expected 31 energy variants; found $(@($energyStudy.variants).Count)." }
    $weaponStudy = Get-Content -LiteralPath '.\src\StarCluster.ScenarioRunner\Scenarios\TL1Calibration\tl1-wm01-complete-weapon-matrix.json' -Raw | ConvertFrom-Json
    if (@($weaponStudy.variants).Count -ne 48) { throw "Expected 48 no-counter weapon-matrix variants; found $(@($weaponStudy.variants).Count)." }

    Assert-PhaseBStaticSemanticContracts -ScenarioDirectory '.\src\StarCluster.ScenarioRunner\Scenarios\TL1PhaseB'
    Assert-ReferenceHashes
    Assert-TechnologyCsvContracts
    Assert-Tl1ScenarioCorpusContracts
    Assert-PdsStudyContracts
    Assert-NewUnitTestContracts
    Assert-WorkbookContract

    if ($RepositoryContractOnly) {
        Write-Host ''
        Write-Host 'Checkpoint 30 repository-contract preflight completed successfully.'
        Write-Host 'Manifest, parser, normalization, reference, documentation, CSV, Phase A/B/kinetic/energy/no-counter/PDS corpus, schema, test-source, semantic, and workbook contracts passed.'
        return
    }

    Write-Host '[3/13] Confirming Godot is closed and .NET SDK 8.0.423 is selected...'
    $godotProcesses = Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -like 'Godot*' }
    if ($godotProcesses) {
        $processNames = ($godotProcesses.ProcessName | Sort-Object -Unique) -join ', '
        throw "Close Godot before applying Checkpoint 30. Running process(es): $processNames"
    }
    $sdkVersion = dotnet --version
    Write-Host "       SDK: $sdkVersion"
    if ($sdkVersion -ne '8.0.423') { throw "Expected .NET SDK 8.0.423 from global.json, but dotnet selected $sdkVersion." }

    Write-Host '[4/13] Performing a clean compiler preflight with warnings as errors...'
    Get-ChildItem '.\src', '.\tests' -Directory -Recurse -Force -ErrorAction SilentlyContinue | Where-Object { $_.Name -eq 'bin' -or $_.Name -eq 'obj' } | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item '.\src\StarCluster.Game\.godot\mono\temp' -Recurse -Force -ErrorAction SilentlyContinue
    & dotnet build '.\StarCluster.sln' --nologo -warnaserror
    if ($LASTEXITCODE -ne 0) { throw "Clean dotnet build failed with exit code $LASTEXITCODE." }

    Write-Host '[5/13] Running 627 engine-independent tests...'
    $testOutput = & dotnet test '.\tests\StarCluster.Tests\StarCluster.Tests.csproj' --no-build --nologo 2>&1
    $testOutput | Write-Host
    if ($LASTEXITCODE -ne 0) { throw "dotnet test failed with exit code $LASTEXITCODE." }
    if (($testOutput | Out-String) -notmatch 'Passed:\s+627') { throw 'The complete suite did not report the expected 627 passed tests.' }

    Write-Host '[6/13] Running seven accepted deterministic moving-missile scenarios...'
    $legacyOutput = '.\out\checkpoint-30-deterministic'
    Remove-Item $legacyOutput -Recurse -Force -ErrorAction SilentlyContinue
    $legacyText = Invoke-Runner -Arguments @('run-all','--scenario-dir','.\src\StarCluster.ScenarioRunner\Scenarios','--output-dir',$legacyOutput) -Description 'Checkpoint 30 legacy deterministic corpus'
    if ($legacyText -notmatch 'Scenario preflight:\s+7 passed, 0 failed\.' -or $legacyText -notmatch 'Scenarios:\s+7 passed, 0 failed, 7 total\.') { throw 'The legacy deterministic corpus did not report seven passing scenarios.' }

    Write-Host '[7/13] Running 12 TL1 Phase A documents and 54 mechanics cases...'
    $phaseAOutput = '.\out\checkpoint-30-tl1-phase-a'
    Remove-Item $phaseAOutput -Recurse -Force -ErrorAction SilentlyContinue
    $phaseAText = Invoke-Runner -Arguments @('tl1-phase-a','--scenario-dir','.\src\StarCluster.ScenarioRunner\Scenarios\TL1PhaseA','--baseline-file','.\docs\archive\player_technology\pre-cp165-active\tl1_core_combat_numerical_baseline_v0_1.csv','--output-dir',$phaseAOutput) -Description 'Checkpoint 30 TL1 Phase A corpus'
    if ($phaseAText -notmatch 'TL1 Phase A preflight:\s+12 scenario documents, 54 mechanics cases, baseline 126 values; passed\.' -or $phaseAText -notmatch 'TL1 Phase A:\s+12 passed, 0 failed, 12 scenarios; 54 passed, 0 failed, 54 cases\.') { throw 'The TL1 Phase A corpus did not report 12 documents and 54 passing cases.' }

    Write-Host '[8/13] Running seven TL1 Phase B documents and 36 direct-fire cases...'
    $phaseBOutput = '.\out\checkpoint-30-tl1-phase-b'
    Remove-Item $phaseBOutput -Recurse -Force -ErrorAction SilentlyContinue
    $phaseBText = Invoke-Runner -Arguments @('tl1-phase-b','--output-dir',$phaseBOutput) -Description 'Checkpoint 30 TL1 Phase B corpus'
    if ($phaseBText -notmatch 'TL1 Phase B preflight:\s+7 scenario documents, 36 cases, baseline hash verified; passed\.' -or $phaseBText -notmatch 'TL1 Phase B:\s+36 passed, 0 failed, 36 cases\.') { throw 'The TL1 Phase B corpus did not report seven documents and 36 passing cases.' }

    Write-Host '[9/13] Running 29 TL1 kinetic-interaction calibration variants at 10,000 trials each...'
    $phaseCOutput = '.\out\checkpoint-30-tl1-kinetic-calibration'
    Remove-Item $phaseCOutput -Recurse -Force -ErrorAction SilentlyContinue
    $phaseCText = Invoke-Runner -Arguments @('tl1-kinetic-calibration','--study-file','.\src\StarCluster.ScenarioRunner\Scenarios\TL1Calibration\tl1-kc01-kinetic-interaction-study.json','--baseline-file','.\docs\archive\player_technology\pre-cp165-active\tl1_core_combat_numerical_baseline_v0_1.csv','--trials','10000','--jobs','24','--output-dir',$phaseCOutput) -Description 'Checkpoint 30 TL1 kinetic calibration study'
    if ($phaseCText -notmatch 'TL1 Kinetic Calibration preflight:\s+29 variants, baseline hash verified; passed\.' -or $phaseCText -notmatch 'TL1 Kinetic Calibration:\s+29 variants, 10000 trials each, 0 failed gates\.') { throw 'The TL1 kinetic calibration study did not report 29 variants and zero failed gates.' }

    Write-Host '[10/13] Running 31 TL1 energy-interaction calibration variants at 10,000 trials each...'
    $phaseDOutput = '.\out\checkpoint-30-tl1-energy-calibration'
    Remove-Item $phaseDOutput -Recurse -Force -ErrorAction SilentlyContinue
    $phaseDText = Invoke-Runner -Arguments @('tl1-energy-calibration','--study-file','.\src\StarCluster.ScenarioRunner\Scenarios\TL1Calibration\tl1-ec01-energy-interaction-study.json','--baseline-file','.\docs\archive\player_technology\pre-cp165-active\tl1_core_combat_numerical_baseline_v0_1.csv','--trials','10000','--jobs','24','--output-dir',$phaseDOutput) -Description 'Checkpoint 30 TL1 energy calibration study'
    if ($phaseDText -notmatch 'TL1 Energy Calibration preflight:\s+31 variants, baseline hash verified; passed\.' -or $phaseDText -notmatch 'TL1 Energy Calibration:\s+31 variants, 10000 trials each, 0 failed gates\.') { throw 'The TL1 energy calibration study did not report 31 variants and zero failed gates.' }

    Write-Host '[11/13] Running 48 complete TL1 no-counter weapon-matrix variants at 10,000 trials each...'
    $phaseEOutput = '.\out\checkpoint-30-tl1-weapon-matrix'
    Remove-Item $phaseEOutput -Recurse -Force -ErrorAction SilentlyContinue
    $phaseEText = Invoke-Runner -Arguments @('tl1-weapon-matrix','--study-file','.\src\StarCluster.ScenarioRunner\Scenarios\TL1Calibration\tl1-wm01-complete-weapon-matrix.json','--baseline-file','.\docs\archive\player_technology\pre-cp165-active\tl1_core_combat_numerical_baseline_v0_1.csv','--trials','10000','--jobs','24','--output-dir',$phaseEOutput) -Description 'Checkpoint 30 no-counter TL1 weapon matrix'
    if ($phaseEText -notmatch 'TL1 Weapon Matrix preflight:\s+48 variants, baseline hash verified; passed\.' -or $phaseEText -notmatch 'TL1 Weapon Matrix:\s+48 variants, 10000 trials each, 0 failed gates\.') { throw 'The TL1 weapon matrix did not report 48 variants and zero failed gates.' }

    Write-Host '[12/13] Running 59 TL1 PDS/interception variants at 10,000 trials each...'
    $phaseFOutput = '.\out\checkpoint-30-tl1-pds-calibration'
    Remove-Item $phaseFOutput -Recurse -Force -ErrorAction SilentlyContinue
    $phaseFText = Invoke-Runner -Arguments @('tl1-pds-calibration','--study-file','.\src\StarCluster.ScenarioRunner\Scenarios\TL1Calibration\tl1-pds01-interception-study.json','--baseline-file','.\docs\archive\player_technology\pre-cp165-active\tl1_core_combat_numerical_baseline_v0_1.csv','--trials','10000','--jobs','24','--output-dir',$phaseFOutput) -Description 'Checkpoint 30 TL1 PDS calibration study'
    if ($phaseFText -notmatch 'TL1 PDS Calibration preflight:\s+59 variants, baseline hash and PDS contracts verified; passed\.' -or $phaseFText -notmatch 'TL1 PDS Calibration:\s+59 variants, 10000 trials each, 0 failed gates\.') { throw 'The TL1 PDS calibration study did not report 59 variants and zero failed gates.' }

    Write-Host '[13/13] Running forty-six ScenarioRunner self-tests...'
    $selfTestText = Invoke-Runner -Arguments @('self-test','--scenario-file','.\src\StarCluster.ScenarioRunner\Scenarios\terminal-two-window-hit.json') -Description 'Checkpoint 30 runner self-tests'
    if ($selfTestText -notmatch 'Runner self-tests:\s+46 passed, 0 failed, 46 total\.') { throw 'The runner self-tests did not report 46 passing tests.' }

    Write-Host ''
    Write-Host 'Checkpoint 30 completed successfully.'
    Write-Host 'Engine-independent tests passed: 627.'
    Write-Host 'Legacy deterministic scenarios passed: 7.'
    Write-Host 'TL1 Phase A scenarios passed: 12 documents / 54 cases.'
    Write-Host 'TL1 Phase B scenarios passed: 7 documents / 36 cases.'
    Write-Host 'TL1 kinetic calibration passed: 29 variants / 10,000 trials each / 0 failed gates.'
    Write-Host 'TL1 energy calibration passed: 31 variants / 10,000 trials each / 0 failed gates.'
    Write-Host 'TL1 no-counter weapon matrix passed: 48 variants / 10,000 trials each / 0 failed gates.'
    Write-Host 'TL1 PDS/interception calibration passed: 59 variants / 10,000 trials each / 0 failed gates.'
    Write-Host 'Runner self-tests passed: 46.'
    Write-Host 'TL1 PDS and missile-interception calibration completed; no mechanical Godot validation is required.'
}
finally { Pop-Location }
