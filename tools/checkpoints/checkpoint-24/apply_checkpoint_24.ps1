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
    $testRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("star-cluster-checkpoint-24-relative-path-test-{0}" -f ([guid]::NewGuid().ToString('N')))
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
        'out/checkpoint-24/example.txt',
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
        throw "Exactly the Checkpoint 24 concept document must remain active. Found: $activeNames"
    }
    Write-Host "       Active concept document: $ExpectedFileName"
}

function Test-ActiveConceptDocumentNormalization {
    $testRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("star-cluster-checkpoint-24-concept-test-{0}" -f ([guid]::NewGuid().ToString('N')))
    $docsDirectory = Join-Path $testRoot 'docs'
    $archiveDirectory = Join-Path $docsDirectory 'archive'
    $expectedName = 'Star_Cluster_Game_Concept_v0.3v.docx'
    $duplicateName = 'Star_Cluster_Game_Concept_v0.3u.docx'
    $importName = 'Star_Cluster_Game_Concept_v0.3t.docx'
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
        $imported = @(Get-ChildItem -LiteralPath $archiveDirectory -Filter 'Star_Cluster_Game_Concept_v0.3t_Imported_*.docx' -File)
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
        if ($relativePath -eq 'CHECKPOINT_24_SHA256SUMS.txt') {
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
    if ($verified -ne 485) { throw "Repository manifest verified $verified files; the Checkpoint 24 archive requires exactly 485 files." }

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
        throw "Exactly the Checkpoint 24 validation runbook must remain active. Found: $activeNames"
    }
    Write-Host "       Active validation runbook: $ExpectedFileName"
}

function Test-ActiveValidationRunbookNormalization {
    $testRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("star-cluster-checkpoint-24-runbook-test-{0}" -f ([guid]::NewGuid().ToString('N')))
    $validationDirectory = Join-Path $testRoot 'validation'
    $archiveDirectory = Join-Path $validationDirectory 'archive'
    $expectedName = 'Checkpoint_24_Unified_Tactical_Power_Component_State_And_TL1_Core_Combat_Test_Foundation.md'
    $staleName = 'Checkpoint_23a_Hull_Layered_Defense_And_Unified_Tactical_Power_Concept_Backup.md'
    try {
        [void](New-Item -ItemType Directory -Path $validationDirectory -Force)
        [void](New-Item -ItemType Directory -Path $archiveDirectory -Force)
        Set-Content -LiteralPath (Join-Path $validationDirectory $expectedName) -Value 'expected' -Encoding UTF8
        Set-Content -LiteralPath (Join-Path $validationDirectory $staleName) -Value 'stale-active-copy' -Encoding UTF8
        Set-Content -LiteralPath (Join-Path $archiveDirectory $staleName) -Value 'different-archived-copy' -Encoding UTF8
        Ensure-ActiveValidationRunbook -ValidationDirectory $validationDirectory -ExpectedFileName $expectedName -ArchiveDirectory $archiveDirectory
        $remaining = @(Get-ChildItem -LiteralPath $validationDirectory -Filter 'Checkpoint_*.md' -File)
        $imported = @(Get-ChildItem -LiteralPath $archiveDirectory -Filter 'Checkpoint_23a_Hull_Layered_Defense_And_Unified_Tactical_Power_Concept_Backup_Imported_*.md' -File)
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
    $reconPath = '.\docs\design\player_technology\player_tl_design_reconciliation_v0_2.csv'
    $baselinePath = '.\docs\archive\player_technology\pre-cp165-active\tl1_core_combat_numerical_baseline_v0_1.csv'
    $loadoutPath = '.\docs\design\player_technology\tl1_core_combat_loadouts_v0_1.csv'
    $scenarioPath = '.\docs\design\player_technology\tl1_core_combat_test_scenarios_v0_1.csv'

    $components = @(Import-Csv -LiteralPath $componentPath)
    if ($components.Count -ne 99) { throw "Expected 99 player components; found $($components.Count)." }
    $ids = @($components | ForEach-Object { $_.component_id })
    if (($ids | Sort-Object -Unique).Count -ne 99) { throw 'Component IDs are not unique.' }
    $families = @($components | Group-Object component_family_id)
    if ($families.Count -ne 11) { throw "Expected 11 component families; found $($families.Count)." }
    foreach ($family in $families) {
        if ($family.Count -ne 9) { throw "Family $($family.Name) does not contain exactly nine TL rows." }
        $levels = @($family.Group | ForEach-Object { [int]$_.tl } | Sort-Object)
        if (($levels -join ',') -ne '1,2,3,4,5,6,7,8,9') { throw "Family $($family.Name) does not cover TL 1-9 exactly once." }
    }
    $propulsionFamilies = @($components | Where-Object { $_.technology_id -eq 'propulsion' } | Select-Object -ExpandProperty component_family_id -Unique | Sort-Object)
    if (($propulsionFamilies -join ',') -ne 'ftl_drive,stl_drive') { throw 'Propulsion must contain exactly the FTL and STL component families.' }
    if (@($components | Where-Object { [string]::IsNullOrWhiteSpace($_.originality_guardrail) }).Count -ne 0) { throw 'Every component row must carry an originality guardrail.' }

    $profiles = @(Import-Csv -LiteralPath $profilePath)
    if ($profiles.Count -ne 11) { throw "Expected 11 compatibility profiles; found $($profiles.Count)." }
    foreach ($profile in $profiles) {
        $supportCount = 0
        if (-not [string]::IsNullOrWhiteSpace($profile.primary_support_category_id)) { $supportCount++ }
        if (-not [string]::IsNullOrWhiteSpace($profile.secondary_support_category_id)) { $supportCount++ }
        if ($supportCount -gt 2) { throw "Profile $($profile.compatibility_profile_id) exceeds two support categories." }
        if ($profile.maximum_engineer_tl_bridge -and [int]$profile.maximum_engineer_tl_bridge -gt 2) { throw "Profile $($profile.compatibility_profile_id) exceeds the two-TL engineer bridge." }
        if ([string]::IsNullOrWhiteSpace($profile.hard_blocker_policy)) { throw "Profile $($profile.compatibility_profile_id) lacks a hard-blocker policy." }
    }
    $profileIds = @($profiles | ForEach-Object { $_.compatibility_profile_id })
    foreach ($component in $components) {
        if ($profileIds -notcontains $component.compatibility_profile_id) { throw "Component $($component.component_id) references unknown compatibility profile $($component.compatibility_profile_id)." }
    }

    $library = @(Import-Csv -LiteralPath $libraryPath)
    if ($library.Count -ne 13) { throw "Expected 13 external reference records; found $($library.Count)." }
    if (@($library | Where-Object { $_.file_name -eq 'MOO2_GAME_MANUAL.PDF' }).Count -ne 1) { throw 'MOO2 reference inventory entry is missing.' }
    foreach ($source in $library) {
        if (-not (Test-Path -LiteralPath $source.project_path -PathType Leaf)) { throw "Reference inventory path $($source.project_path) was not found." }
        $actual = (Get-FileHash -LiteralPath $source.project_path -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actual -ne $source.sha256.ToLowerInvariant()) { throw "Reference inventory hash mismatch for $($source.file_name)." }
        if ([string]::IsNullOrWhiteSpace($source.originality_guardrail)) { throw "Reference $($source.source_id) lacks an originality guardrail." }
    }
    $insights = @(Import-Csv -LiteralPath $insightPath)
    if ($insights.Count -lt 40) { throw "Expected at least 40 reference insights; found $($insights.Count)." }
    $sourceIds = @($library | ForEach-Object { $_.source_id })
    foreach ($insight in $insights) {
        if ($sourceIds -notcontains $insight.source_id) { throw "Insight $($insight.insight_id) references unknown source $($insight.source_id)." }
        if ([string]::IsNullOrWhiteSpace($insight.originality_guardrail) -or [string]::IsNullOrWhiteSpace($insight.adoption_status)) { throw "Insight $($insight.insight_id) lacks guardrail or adoption status." }
    }

    $recon = @(Import-Csv -LiteralPath $reconPath)
    if ($recon.Count -ne 24) { throw "Expected 24 Checkpoint 24 reconciliation rows; found $($recon.Count)." }
    if (($recon[0].PSObject.Properties.Name -join ',') -ne 'topic,current_direction,reference_influence,checkpoint_24_decision,status,next_action') { throw 'Checkpoint 24 reconciliation header is invalid.' }

    $baseline = @(Import-Csv -LiteralPath $baselinePath)
    if ($baseline.Count -ne 117) { throw "Expected 117 TL1 baseline rows; found $($baseline.Count)." }
    if (($baseline[0].PSObject.Properties.Name -join ',') -ne 'section,parameter_id,display_name,value,unit,applies_to,status,rationale,test_signal') { throw 'TL1 baseline header is invalid.' }
    if (($baseline | Select-Object -ExpandProperty parameter_id -Unique).Count -ne 117) { throw 'TL1 baseline parameter IDs are not unique.' }
    $requiredValues = @{
        'hull_points'='12'; 'crew_pristine'='100'; 'marine_pristine'='10';
        'minimum_operating_crew'='10'; 'reactor_output'='5'; 'stl_move'='4';
        'armor_protection'='2'; 'armor_integrity'='6'; 'shield_capacity'='6'
    }
    foreach ($id in $requiredValues.Keys) {
        $row = @($baseline | Where-Object { $_.parameter_id -eq $id })
        if ($row.Count -ne 1 -or $row[0].value -ne $requiredValues[$id]) { throw "TL1 baseline value $id must equal $($requiredValues[$id])." }
    }

    $loadouts = @(Import-Csv -LiteralPath $loadoutPath)
    if ($loadouts.Count -ne 13) { throw "Expected 13 TL1 loadouts; found $($loadouts.Count)." }
    if (($loadouts[0].PSObject.Properties.Name -join ',') -ne 'loadout_id,name,base_chassis,weapon,optional_systems,weapon_mode,starting_ammo,starting_power,doctrine,purpose') { throw 'TL1 loadout header is invalid.' }
    if (($loadouts | Select-Object -ExpandProperty loadout_id -Unique).Count -ne 13) { throw 'TL1 loadout IDs are not unique.' }

    $scenarios = @(Import-Csv -LiteralPath $scenarioPath)
    if ($scenarios.Count -ne 60) { throw "Expected 60 TL1 scenarios; found $($scenarios.Count)." }
    if (($scenarios[0].PSObject.Properties.Name -join ',') -ne 'scenario_id,phase,name,baseline_version,side_a_fixture,side_b_fixture,starting_range_hexes,starting_tracks,doctrine,changed_variable,relevance_context,trial_mode,minimum_trials,primary_metrics,acceptance_question,implementation_status') { throw 'TL1 scenario header is invalid.' }
    if (($scenarios | Select-Object -ExpandProperty scenario_id -Unique).Count -ne 60) { throw 'TL1 scenario IDs are not unique.' }
    foreach ($phase in @('A Mechanics','B Core duels','C PDS','D EW','E Power','F Damage','G Movement')) {
        if (@($scenarios | Where-Object { $_.phase -eq $phase }).Count -eq 0) { throw "TL1 scenario phase $phase is missing." }
    }

    Write-Host "       Technology/test data: 99 components, 11 profiles, 13 references, $($insights.Count) insights, 24 reconciliations, 117 baseline values, 13 loadouts, 60 scenarios."
}

function Assert-WorkbookContract {
    $path = '.\docs\design\player_technology\StarCluster_Player_TL_Framework_Draft_v0_4.xlsx'
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw 'Technology workbook was not found.' }
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip = [System.IO.Compression.ZipFile]::OpenRead((Resolve-Path -LiteralPath $path).Path)
    try {
        $entryNames = @($zip.Entries | ForEach-Object { $_.FullName })
        if (@($entryNames | Where-Object { $_ -like 'xl/tables/*' }).Count -ne 0) { throw 'Workbook contains structured table parts; these are intentionally prohibited.' }
        $workbookEntry = $zip.GetEntry('xl/workbook.xml')
        if ($null -eq $workbookEntry) { throw 'Workbook XML is missing.' }
        $reader = New-Object System.IO.StreamReader($workbookEntry.Open())
        try { $workbookXml = $reader.ReadToEnd() } finally { $reader.Dispose() }
        foreach ($sheetName in @('Overview','TL1 Baseline','TL1 Loadouts','TL1 Test Matrix','Component Schema','Checkpoint 24 Plan','TL Matrix','Components','Compatibility Profiles','Adaptation Rules','Reference Library','Reference Insights','Design Reconciliation','Level Themes','Design Decisions','Sources Used')) {
            if (-not $workbookXml.Contains(('name="{0}"' -f $sheetName))) { throw "Workbook sheet $sheetName is missing." }
        }
        $allXml = ''
        foreach ($entry in @($zip.Entries | Where-Object { $_.FullName -like 'xl/*.xml' -or $_.FullName -like 'xl/worksheets/*.xml' })) {
            $entryReader = New-Object System.IO.StreamReader($entry.Open())
            try { $allXml += $entryReader.ReadToEnd() } finally { $entryReader.Dispose() }
        }
        if (-not $allXml.Contains('D-232')) { throw 'Workbook does not contain Decision D-232.' }
        if (-not $allXml.Contains('tl1_core_combat_numerical_baseline_v0_1.csv')) { throw 'Workbook does not identify the TL1 baseline source.' }
    }
    finally { $zip.Dispose() }
    Write-Host '       Workbook OOXML: Checkpoint 24 sheets and decision markers present; no structured table parts.'
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
    Write-Host '[1/7] Verifying complete Checkpoint 24 repository and parser contracts...'
    foreach ($requiredFile in @(
        '.\StarCluster.sln',
        '.\global.json',
        '.\CHECKPOINT_24_SHA256SUMS.txt',
        '.\src\StarCluster.Core\Geometry\HexCoord.cs',
        '.\src\StarCluster.Core\Maps\SystemMap.cs',
        '.\src\StarCluster.Core\Combat\DirectFireLineOfSight.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileRoutePlanner.cs',
        '.\tests\StarCluster.Tests\Geometry\HexCoordTests.cs',
        '.\tests\StarCluster.Tests\Maps\SystemMapTests.cs',
        '.\tools\checkpoints\checkpoint-02\apply_checkpoint_02.ps1',
        '.\docs\validation\archive\Checkpoint_20a_Calibration_Reporting_Guard_Hotfix.md',
        '.\docs\Star_Cluster_Game_Concept_v0.3v.docx',
        '.\docs\archive\Star_Cluster_Game_Concept_v0.3u.docx',
        '.\docs\references\MOO2_GAME_MANUAL.PDF',
        '.\docs\references\README.md',
        '.\docs\references\SHA256SUMS.txt',
        '.\docs\design\player_technology\StarCluster_Player_TL_Framework_Draft_v0_4.xlsx',
        '.\docs\design\player_technology\player_tl_components_draft_v0_3.csv',
        '.\docs\design\player_technology\player_tl_compatibility_profiles_draft_v0_3.csv',
        '.\docs\design\player_technology\player_reference_library_v0_1.csv',
        '.\docs\design\player_technology\player_reference_insights_v0_1.csv',
        '.\docs\design\player_technology\player_tl_design_reconciliation_v0_2.csv',
        '.\docs\archive\player_technology\pre-cp165-active\tl1_core_combat_numerical_baseline_v0_1.csv',
        '.\docs\design\player_technology\tl1_core_combat_loadouts_v0_1.csv',
        '.\docs\design\player_technology\tl1_core_combat_test_scenarios_v0_1.csv',
        '.\docs\design\player_technology\Component_State_And_Profile_Schema_v0_1.md',
        '.\docs\design\player_technology\TL1_Core_Combat_Test_Plan_v0_1.md',
        '.\docs\checkpoints\Checkpoint_24_Unified_Tactical_Power_Component_State_And_TL1_Core_Combat_Test_Foundation.md',
        '.\docs\validation\Checkpoint_24_Unified_Tactical_Power_Component_State_And_TL1_Core_Combat_Test_Foundation.md',
        '.\docs\validation\archive\Checkpoint_23a_Hull_Layered_Defense_And_Unified_Tactical_Power_Concept_Backup.md',
        '.\docs\design\player_technology\Hull_Armor_Shields_And_Tactical_Power_Foundation.md',
        '.\docs\design\player_technology\Online_Reference_Review_Queue.md')) {
        if (-not (Test-Path -LiteralPath $requiredFile -PathType Leaf)) { throw "Required Checkpoint 24 file $requiredFile was not found." }
    }
    Ensure-ActiveValidationRunbook -ValidationDirectory '.\docs\validation' -ExpectedFileName 'Checkpoint_24_Unified_Tactical_Power_Component_State_And_TL1_Core_Combat_Test_Foundation.md' -ArchiveDirectory '.\docs\validation\archive'
    Ensure-ActiveConceptDocument -DocsDirectory '.\docs' -ExpectedFileName 'Star_Cluster_Game_Concept_v0.3v.docx' -ArchiveDirectory '.\docs\archive'
    Test-NormalizedRelativePathCompatibility
    Test-RepositoryManifestLocalArtifactPolicy
    Assert-RepositoryManifest '.\CHECKPOINT_24_SHA256SUMS.txt'
    Assert-PowerShellScriptsParse '.\tools'
    Test-ActiveValidationRunbookNormalization
    Test-ActiveConceptDocumentNormalization

    Write-Host '[2/7] Verifying concept, reference library, technology data, schema, and workbook contracts...'
    Assert-FileContains '.\README.md' @('Checkpoint 24','Concept v0.3v','situational') 'Repository README'
    Assert-FileContains '.\docs\references\README.md' @('MOO2_GAME_MANUAL.PDF','Originality and copyright guardrail','Do not copy proprietary prose') 'Reference README'
    Assert-FileContains '.\docs\checkpoints\Checkpoint_24_Unified_Tactical_Power_Component_State_And_TL1_Core_Combat_Test_Foundation.md' @('SC24_POWER_STATES=AVAILABLE_POWERED_SPENT','SC24_REACTOR_ENVELOPE=POST_DAMAGE_CONTROL_TURN_SNAPSHOT','SC24_SHIELD_RESISTANCE=SHIELD_ARMOR_SA_AFTER_SPEN','SC24_RESET_MODEL=TURN_REFRESH_AND_FTL_ONLY','SC24_PERSONNEL=CREW_PLUS_MARINES_WITH_THREE_CREW_STAGES','SC24_TEST_BASELINE=EXACT_PROVISIONAL_TL1_CORE_COMBAT_V0_1') 'Checkpoint 24 documentation contract'
    Assert-FileContains '.\docs\design\player_technology\Hull_Armor_Shields_And_Tactical_Power_Foundation.md' @('Available','Powered','Spent','Turn Power Envelope','Shield Armor (SA)','Total Personnel = Crew + Marines','There is no universal combat-end reset') 'Checkpoint 24 foundation design record'
    Assert-FileNotContains '.\docs\design\player_technology\Hull_Armor_Shields_And_Tactical_Power_Foundation.md' @('Available/Committed/Consumed','Committed Tactical Power','Consumed Tactical Power','Shield Protection (SP)') 'Checkpoint 24 foundation design record'
    Assert-FileContains '.\docs\design\player_technology\Component_State_And_Profile_Schema_v0_1.md' @('Installed pristine data','Persistent current state','Derived values','Turn-local tactical state','Common component core','Optional profile blocks') 'Component schema'
    Assert-FileContains '.\docs\design\player_technology\TL1_Core_Combat_Test_Plan_v0_1.md' @('situational viability','irrelevant','relevant','heavy','paired side-swapped','Phase A','Phase G') 'TL1 test plan'
    Assert-FileContains '.\docs\Prototype_TODO.md' @('Checkpoint 24','one exact provisional TL1 numerical baseline','13 loadout fixtures','60 staged scenario specifications','Phase A deterministic mechanics') 'Prototype TODO'
    Assert-DocxContains '.\docs\Star_Cluster_Game_Concept_v0.3v.docx' @('Available, Powered, or Spent','Turn Power Envelope','Shield Armor (SA)','10.14 Overload, Strain, and energy-system modes','10.19 Tractors, Turn Refresh, and FTL transition','100 Crew, 10 Marines','D-232','END OF DRAFT v0.3v') 'Concept v0.3v'
    Assert-ReferenceHashes
    Assert-TechnologyCsvContracts
    Assert-WorkbookContract

    if ($RepositoryContractOnly) {
        Write-Host ''
        Write-Host 'Checkpoint 24 repository-contract preflight completed successfully.'
        Write-Host 'Manifest, native parsing, runbook/concept normalization, local-artifact policy, references, documentation, CSV, schema, and workbook contracts passed.'
        return
    }

    Write-Host '[3/7] Confirming Godot is closed and .NET SDK 8.0.423 is selected...'
    $godotProcesses = Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -like 'Godot*' }
    if ($godotProcesses) {
        $processNames = ($godotProcesses.ProcessName | Sort-Object -Unique) -join ', '
        throw "Close Godot before applying Checkpoint 24. Running process(es): $processNames"
    }
    $sdkVersion = dotnet --version
    Write-Host "       SDK: $sdkVersion"
    if ($sdkVersion -ne '8.0.423') { throw "Expected .NET SDK 8.0.423 from global.json, but dotnet selected $sdkVersion." }

    Write-Host '[4/7] Performing a clean compiler preflight with warnings as errors...'
    Get-ChildItem '.\src', '.\tests' -Directory -Recurse -Force -ErrorAction SilentlyContinue | Where-Object { $_.Name -eq 'bin' -or $_.Name -eq 'obj' } | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item '.\src\StarCluster.Game\.godot\mono\temp' -Recurse -Force -ErrorAction SilentlyContinue
    & dotnet build '.\StarCluster.sln' --nologo -warnaserror
    if ($LASTEXITCODE -ne 0) { throw "Clean dotnet build failed with exit code $LASTEXITCODE." }

    Write-Host '[5/7] Running 506 engine-independent tests...'
    $testOutput = & dotnet test '.\tests\StarCluster.Tests\StarCluster.Tests.csproj' --no-build --nologo 2>&1
    $testOutput | Write-Host
    if ($LASTEXITCODE -ne 0) { throw "dotnet test failed with exit code $LASTEXITCODE." }
    if (($testOutput | Out-String) -notmatch 'Passed:\s+506') { throw 'The complete suite did not report the expected 506 passed tests.' }

    Write-Host '[6/7] Running seven deterministic scenarios...'
    $deterministicOutput = '.\out\checkpoint-24-deterministic'
    Remove-Item $deterministicOutput -Recurse -Force -ErrorAction SilentlyContinue
    $scenarioText = Invoke-Runner -Arguments @('run-all','--scenario-dir','.\src\StarCluster.ScenarioRunner\Scenarios','--output-dir',$deterministicOutput) -Description 'Checkpoint 24 deterministic corpus'
    if ($scenarioText -notmatch 'Scenario preflight:\s+7 passed, 0 failed\.' -or $scenarioText -notmatch 'Scenarios:\s+7 passed, 0 failed, 7 total\.') { throw 'The deterministic corpus did not report seven passing scenarios.' }

    Write-Host '[7/7] Running forty-six ScenarioRunner self-tests...'
    $selfTestText = Invoke-Runner -Arguments @('self-test','--scenario-file','.\src\StarCluster.ScenarioRunner\Scenarios\terminal-two-window-hit.json') -Description 'Checkpoint 24 runner self-tests'
    if ($selfTestText -notmatch 'Runner self-tests:\s+46 passed, 0 failed, 46 total\.') { throw 'The runner self-tests did not report 46 passing tests.' }

    Write-Host ''
    Write-Host 'Checkpoint 24 completed successfully.'
    Write-Host 'Documentation, schema, and exact TL1 test data were updated; runtime mechanics remain unchanged.'
    Write-Host 'Engine-independent tests passed: 506.'
    Write-Host 'Deterministic headless scenarios passed: 7.'
    Write-Host 'Runner self-tests passed: 46.'
    Write-Host 'No mechanical Godot validation or Monte Carlo recalibration is required.'
}
finally { Pop-Location }
