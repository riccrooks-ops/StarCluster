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
    $testRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("star-cluster-checkpoint-27-relative-path-test-{0}" -f ([guid]::NewGuid().ToString('N')))
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
        throw "Exactly the Checkpoint 28 concept document must remain active. Found: $activeNames"
    }
    Write-Host "       Active concept document: $ExpectedFileName"
}

function Test-ActiveConceptDocumentNormalization {
    $testRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("star-cluster-checkpoint-27-concept-test-{0}" -f ([guid]::NewGuid().ToString('N')))
    $docsDirectory = Join-Path $testRoot 'docs'
    $archiveDirectory = Join-Path $docsDirectory 'archive'
    $expectedName = 'Star_Cluster_Game_Concept_v0.3z.docx'
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
        if ($relativePath -eq 'CHECKPOINT_28_SHA256SUMS.txt') {
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
    if ($verified -ne 597) { throw "Repository manifest verified $verified files; the Checkpoint 28 archive requires exactly 597 files." }

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
        throw "Exactly the Checkpoint 28 validation runbook must remain active. Found: $activeNames"
    }
    Write-Host "       Active validation runbook: $ExpectedFileName"
}

function Test-ActiveValidationRunbookNormalization {
    $testRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("star-cluster-checkpoint-27-runbook-test-{0}" -f ([guid]::NewGuid().ToString('N')))
    $validationDirectory = Join-Path $testRoot 'validation'
    $archiveDirectory = Join-Path $validationDirectory 'archive'
    $expectedName = 'Checkpoint_28_TL1_Energy_Weapon_And_Tactical_Power_Calibration.md'
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
    if ($recon.Count -ne 32) { throw "Expected 32 Checkpoint 28 reconciliation rows; found $($recon.Count)." }
    if (($recon[0].PSObject.Properties.Name -join ',') -ne 'topic,current_direction,reference_influence,checkpoint_25_decision,status,next_action') { throw 'Checkpoint 28 reconciliation header is invalid.' }

    $baseline = @(Import-Csv -LiteralPath $baselinePath)
    if ($baseline.Count -ne 126) { throw "Expected 126 TL1 baseline rows; found $($baseline.Count)." }
    if (($baseline[0].PSObject.Properties.Name -join ',') -ne 'section,parameter_id,display_name,value,unit,applies_to,status,rationale,test_signal') { throw 'TL1 baseline header is invalid.' }
    if (($baseline | Select-Object -ExpandProperty parameter_id -Unique).Count -ne 126) { throw 'TL1 baseline parameter IDs are not unique.' }
    $baselineHash = (Get-FileHash -LiteralPath $baselinePath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($baselineHash -ne 'd49fdffb60f3c7ee41c5e587daaabcdabf95ffd230e3aa947be5de5a291c6a1e') { throw "TL1 baseline SHA-256 is $baselineHash, not the accepted Checkpoint 28 hash." }
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
    $expectedHash = 'd49fdffb60f3c7ee41c5e587daaabcdabf95ffd230e3aa947be5de5a291c6a1e'
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
    if ($implemented.Count -ne 12) { throw "Expected 12 implemented Checkpoint 28 matrix rows; found $($implemented.Count)." }
    foreach ($row in $implemented) {
        if (-not $documentsByMatrixId.ContainsKey($row.scenario_id)) { throw "Matrix row $($row.scenario_id) has no runtime scenario document." }
        $contract = $documentsByMatrixId[$row.scenario_id]
        if ($row.runtime_scenario_file.Replace('\','/') -ne $contract.RelativePath) { throw "Matrix row $($row.scenario_id) runtime path does not match $($contract.RelativePath)." }
        if ([int]$row.runtime_case_count -ne [int]$contract.CaseCount) { throw "Matrix row $($row.scenario_id) case count does not match its runtime document." }
    }

    Write-Host "       TL1 Phase A corpus: 12 documents, 54 unique mechanics cases, exact baseline hash, matrix links, and supported operations verified."
}

function Assert-WorkbookContract {
    $path = '.\docs\design\player_technology\StarCluster_Player_TL_Framework_Draft_v0_8.xlsx'
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw 'Technology workbook v0.8 was not found.' }
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip = [System.IO.Compression.ZipFile]::OpenRead((Resolve-Path -LiteralPath $path).Path)
    try {
        $entryNames = @($zip.Entries | ForEach-Object { $_.FullName })
        if (@($entryNames | Where-Object { $_ -like 'xl/tables/*' }).Count -ne 0) { throw 'Workbook contains structured table parts; these are intentionally prohibited.' }
        $workbookEntry = $zip.GetEntry('xl/workbook.xml')
        if ($null -eq $workbookEntry) { throw 'Workbook XML is missing.' }
        $reader = New-Object System.IO.StreamReader($workbookEntry.Open())
        try { $workbookXml = $reader.ReadToEnd() } finally { $reader.Dispose() }
        foreach ($sheetName in @('Overview','TL1 Baseline','TL1 Loadouts','TL1 Test Matrix','Phase A Runtime','TL1 Phase B','TL1 Calibration','Checkpoint 28 Energy','Component Schema','Checkpoint 25 Plan','TL Matrix','Components','Compatibility Profiles','Adaptation Rules','Reference Library','Reference Insights','Design Reconciliation','Level Themes','Design Decisions','Sources Used')) {
            if (-not $workbookXml.Contains(('name="{0}"' -f $sheetName))) { throw "Workbook sheet $sheetName is missing." }
        }
        $allXml = ''
        foreach ($entry in @($zip.Entries | Where-Object { $_.FullName -like 'xl/*.xml' -or $_.FullName -like 'xl/worksheets/*.xml' })) {
            $entryReader = New-Object System.IO.StreamReader($entry.Open())
            try { $allXml += $entryReader.ReadToEnd() } finally { $entryReader.Dispose() }
        }
        foreach ($marker in @('D-253','Checkpoint 28 - TL1 Energy Weapon Calibration','31 variants x 10,000 trials','Safe overload burst')) {
            if (-not $allXml.Contains($marker)) { throw "Workbook does not contain required Checkpoint 28 marker $marker." }
        }
    }
    finally { $zip.Dispose() }
    Write-Host '       Workbook OOXML: Checkpoint 28 Energy sheet and Decision D-253 present; no structured table parts.'
}

function Assert-NewUnitTestContracts {
    $path = '.\tests\StarCluster.Tests\Combat\DirectFire\Tl1DirectFireAccuracyTests.cs'
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Checkpoint 28 direct-fire unit-test file was not found." }
    $facts = @(Select-String -LiteralPath $path -SimpleMatch '[Fact]').Count
    $theories = @(Select-String -LiteralPath $path -SimpleMatch '[Theory]').Count
    if ($facts -ne 10 -or $theories -ne 3) { throw "Expected 10 Fact methods and 3 Theory methods in the Checkpoint 28 direct-fire test file; found $facts and $theories." }
    Assert-FileContains $path @('CalculatorMatchesAcceptedTl1Examples','SimultaneousWindowAllowsMutualDestruction','KineticMirrorAllHitsMutuallyDestroysOnTurnNine') 'Checkpoint 28 direct-fire tests'
    $calibrationPath = '.\tests\StarCluster.Tests\Combat\DirectFire\Tl1KineticDuelCalibrationTests.cs'
    if (-not (Test-Path -LiteralPath $calibrationPath -PathType Leaf)) { throw 'Checkpoint 28 calibration test file was not found.' }
    $calibrationFacts = @(Select-String -LiteralPath $calibrationPath -SimpleMatch '[Fact]').Count
    if ($calibrationFacts -ne 8) { throw "Expected 8 calibration Fact methods; found $calibrationFacts." }
    Assert-FileContains $calibrationPath @('RevisedBaselineAllHitsMutuallyDestroysOnTurnNine','ArmorProtectionTwoWithoutApenCanStallDamageThree','ApenTwoRestoresProgressAgainstArmorProtectionTwo') 'Checkpoint 28 calibration tests'
    Write-Host '       Checkpoint 28 unit-test source: 10 direct-fire facts, 3 theories, and 8 calibration facts present.'
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
    Write-Host '[1/11] Verifying complete Checkpoint 28 repository and parser contracts...'
    foreach ($requiredFile in @(
        '.\StarCluster.sln',
        '.\global.json',
        '.\CHECKPOINT_28_SHA256SUMS.txt',
        '.\src\StarCluster.Core\Combat\Damage\LayeredDamageResolver.cs',
        '.\src\StarCluster.Core\Combat\Damage\ShieldRechargeService.cs',
        '.\src\StarCluster.Core\Combat\Power\TacticalPowerLedger.cs',
        '.\src\StarCluster.Core\Combat\Power\ReactorState.cs',
        '.\src\StarCluster.Core\Combat\Weapons\WeaponState.cs',
        '.\src\StarCluster.Core\Combat\Weapons\ChargedWeaponState.cs',
        '.\src\StarCluster.ScenarioRunner\TL1\Tl1ScenarioCorpusRunner.cs',
        '.\src\StarCluster.ScenarioRunner\TL1\Tl1MechanicsOperationExecutor.cs',
        '.\src\StarCluster.ScenarioRunner\Scenarios\TL1PhaseA\tl1-a01-shield-bypass-capacity.json',
        '.\src\StarCluster.ScenarioRunner\Scenarios\TL1PhaseA\tl1-a12-charging-retention-ftl.json',
        '.\tests\StarCluster.Tests\Combat\Damage\LayeredDamageResolverTests.cs',
        '.\tests\StarCluster.Tests\Combat\Power\TacticalPowerLedgerTests.cs',
        '.\tests\StarCluster.Tests\Combat\Weapons\WeaponStateTests.cs',
        '.\docs\Star_Cluster_Game_Concept_v0.3z.docx',
        '.\docs\design\player_technology\TL1_Core_Combat_Test_Plan_v0_3.md',
        '.\docs\design\player_technology\StarCluster_Player_TL_Framework_Draft_v0_8.xlsx',
        '.\docs\checkpoints\Checkpoint_28_TL1_Energy_Weapon_And_Tactical_Power_Calibration.md',
        '.\docs\validation\Checkpoint_28_TL1_Energy_Weapon_And_Tactical_Power_Calibration.md',
        '.\docs\design\player_technology\TL1_Kinetic_Interaction_Calibration_Plan_v0_1.md',
        '.\src\StarCluster.ScenarioRunner\Scenarios\TL1Calibration\tl1-kc01-kinetic-interaction-study.json',
        '.\src\StarCluster.ScenarioRunner\TL1Calibration\Tl1KineticCalibrationRunner.cs',
        '.\tests\StarCluster.Tests\Combat\DirectFire\Tl1KineticDuelCalibrationTests.cs',
        '.\docs\design\player_technology\TL1_Energy_Interaction_Calibration_Plan_v0_1.md',
        '.\docs\design\player_technology\tl1_energy_calibration_schema_v0_1.json',
        '.\src\StarCluster.ScenarioRunner\Scenarios\TL1Calibration\tl1-ec01-energy-interaction-study.json',
        '.\src\StarCluster.ScenarioRunner\TL1Calibration\Tl1EnergyCalibrationRunner.cs',
        '.\src\StarCluster.Core\Combat\DirectFire\Tl1EnergyDuelSimulator.cs',
        '.\tests\StarCluster.Tests\Combat\DirectFire\Tl1EnergyDuelCalibrationTests.cs',
        '.\docs\checkpoints\Checkpoint_26_TL1_Direct_Fire_Accuracy_Simultaneous_Volley_And_Kinetic_Mirror_Duel_Foundation.md',
        '.\docs\validation\archive\Checkpoint_26_TL1_Direct_Fire_Accuracy_Simultaneous_Volley_And_Kinetic_Mirror_Duel_Foundation.md',
        '.\docs\archive\Star_Cluster_Game_Concept_v0.3v.docx',
        '.\docs\archive\Star_Cluster_Game_Concept_v0.3y.docx',
        '.\docs\validation\archive\Checkpoint_27_Revised_TL1_Defensive_Envelope_And_Kinetic_Interaction_Calibration.md',
        '.\docs\references\SHA256SUMS.txt',
        '.\docs\design\player_technology\StarCluster_Player_TL_Framework_Draft_v0_5.xlsx',
        '.\docs\design\player_technology\player_tl_design_reconciliation_v0_3.csv',
        '.\docs\design\player_technology\tl1_core_combat_test_scenarios_v0_2.csv',
        '.\docs\design\player_technology\tl1_phase_a_scenario_schema_v0_1.json',
        '.\docs\design\player_technology\Component_State_And_Profile_Schema_v0_2.md',
        '.\docs\design\player_technology\TL1_Core_Combat_Test_Plan_v0_2.md',
        '.\docs\checkpoints\Checkpoint_26_TL1_Direct_Fire_Accuracy_Simultaneous_Volley_And_Kinetic_Mirror_Duel_Foundation.md',
        '.\docs\validation\archive\Checkpoint_26_TL1_Direct_Fire_Accuracy_Simultaneous_Volley_And_Kinetic_Mirror_Duel_Foundation.md',
        '.\docs\validation\archive\Checkpoint_24_Unified_Tactical_Power_Component_State_And_TL1_Core_Combat_Test_Foundation.md')) {
        if (-not (Test-Path -LiteralPath $requiredFile -PathType Leaf)) { throw "Required Checkpoint 28 file $requiredFile was not found." }
    }
    Ensure-ActiveValidationRunbook -ValidationDirectory '.\docs\validation' -ExpectedFileName 'Checkpoint_28_TL1_Energy_Weapon_And_Tactical_Power_Calibration.md' -ArchiveDirectory '.\docs\validation\archive'
    Ensure-ActiveConceptDocument -DocsDirectory '.\docs' -ExpectedFileName 'Star_Cluster_Game_Concept_v0.3z.docx' -ArchiveDirectory '.\docs\archive'
    Test-NormalizedRelativePathCompatibility
    Test-RepositoryManifestLocalArtifactPolicy
    Assert-RepositoryManifest '.\CHECKPOINT_28_SHA256SUMS.txt'
    Assert-PowerShellScriptsParse '.\tools'
    Test-ActiveValidationRunbookNormalization
    Test-ActiveConceptDocumentNormalization

    Write-Host '[2/11] Verifying Concept, reference library, exact data, schema, corpus, tests, and workbook contracts...'
    Assert-FileContains '.\README.md' @('Checkpoint 28','v0.3z','31 energy','607 engine-independent tests') 'Repository README'
    Assert-FileContains '.\docs\checkpoints\Checkpoint_28_TL1_Energy_Weapon_And_Tactical_Power_Calibration.md' @('31-variant TL1 energy study','Tactical Power','side swaps','No accepted Checkpoint 27c kinetic or defensive value is changed') 'Checkpoint 28 documentation contract'
    Assert-FileContains '.\docs\design\player_technology\Component_State_And_Profile_Schema_v0_2.md' @('Persistent current state','Derived values','Turn-local state','pristine','field-repair ceiling') 'Component schema v0.2'
    Assert-FileContains '.\docs\design\player_technology\TL1_Core_Combat_Test_Plan_v0_2.md' @('Phase A','12 baseline-driven scenario documents','54 deterministic cases','Expected subsets','Phase B entry gate') 'TL1 test plan v0.2'
    Assert-FileContains '.\docs\Prototype_TODO.md' @('Checkpoint 28 status','31 variants','10,000 trials','forced overload') 'Prototype TODO'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\README.md' @('tl1-phase-b-preflight','tl1-phase-b','36 deterministic cases','does not establish weapon balance') 'ScenarioRunner README'
    Assert-FileContains '.\docs\design\player_technology\TL1_Kinetic_Interaction_Calibration_Plan_v0_1.md' @('29 variants','10,000 trials per variant','common random numbers','balance conclusions') 'Phase B kinetic calibration plan'
    Assert-DocxContains '.\docs\Star_Cluster_Game_Concept_v0.3z.docx' @('Checkpoint 28 - TL1 Energy Weapon Calibration','D-250','D-253','31 variants','END OF DRAFT v0.3z') 'Concept v0.3z'
    Assert-FileContains '.\src\StarCluster.Core\Combat\DirectFire\DirectFireAccuracyCalculator.cs' @('RangePenaltyPerHex','Math.Clamp','ShooterEvasivePenalty') 'Direct-fire accuracy calculator'
    Assert-FileContains '.\src\StarCluster.Core\Combat\DirectFire\SimultaneousDirectFire.cs' @('cannot commit direct fire','MutualDestruction','A weapon cannot be committed') 'Simultaneous direct-fire resolver'
    Assert-FileContains '.\src\StarCluster.Core\Combat\DirectFire\Tl1KineticMirrorDuel.cs' @('Tl1DuelOutcome','RestoreShields(1)','MutualDestruction') 'TL1 kinetic mirror duel'
    $phaseBFiles = @(Get-ChildItem -LiteralPath '.\src\StarCluster.ScenarioRunner\Scenarios\TL1PhaseB' -Filter '*.json' -File)
    if ($phaseBFiles.Count -ne 7) { throw "Expected 7 TL1 Phase B scenario documents, found $($phaseBFiles.Count)." }
    $phaseBCases = 0
    foreach ($file in $phaseBFiles) {
        $document = Get-Content -LiteralPath $file.FullName -Raw | ConvertFrom-Json
        if ($document.schemaVersion -ne 'star-cluster-tl1-phase-b-v1') { throw "Unexpected Phase B schema in $($file.Name)." }
        $phaseBCases += @($document.cases).Count
    }
    if ($phaseBCases -ne 36) { throw "Expected 36 TL1 Phase B cases, found $phaseBCases." }
    $phaseCPath = '.\src\StarCluster.ScenarioRunner\Scenarios\TL1Calibration\tl1-kc01-kinetic-interaction-study.json'
    $phaseC = Get-Content -LiteralPath $phaseCPath -Raw | ConvertFrom-Json
    if ($phaseC.schemaVersion -ne 'star-cluster-tl1-kinetic-calibration-v1') { throw 'Unexpected kinetic calibration schema.' }
    if ($phaseC.baselineSha256.ToLowerInvariant() -ne 'd49fdffb60f3c7ee41c5e587daaabcdabf95ffd230e3aa947be5de5a291c6a1e') { throw 'Kinetic calibration baseline hash is invalid.' }
    if (@($phaseC.variants).Count -ne 29) { throw "Expected 29 kinetic calibration variants; found $(@($phaseC.variants).Count)." }
    if ($phaseC.trialsPerVariant -ne 10000) { throw 'Kinetic calibration default must be 10,000 trials per variant.' }

    Assert-FileContains '.\docs\design\player_technology\tl1_energy_calibration_schema_v0_1.json' @('star-cluster-tl1-energy-calibration-v1','safe-burst','reactorOutput','tacticalShieldRecharge') 'TL1 energy calibration schema'
    Assert-FileContains '.\docs\design\player_technology\TL1_Energy_Interaction_Calibration_Plan_v0_1.md' @('31 variants','10,000 trials per variant','Safe overload','Forced overload') 'TL1 energy calibration plan'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\TL1Calibration\Tl1EnergyCalibrationRunner.cs' @('TL1 Energy Calibration preflight','mirror-side-bias','side-swap','variants.csv') 'TL1 energy calibration runner'
    Assert-FileContains '.\src\StarCluster.Core\Combat\DirectFire\Tl1EnergyDuelSimulator.cs' @('safe-burst','TacticalShieldRecharge','WeaponCostForTurn','TacticalPowerSpentA') 'TL1 energy duel simulator'
    $energyStudy = Get-Content -LiteralPath '.\src\StarCluster.ScenarioRunner\Scenarios\TL1Calibration\tl1-ec01-energy-interaction-study.json' -Raw | ConvertFrom-Json
    if ($energyStudy.schemaVersion -ne 'star-cluster-tl1-energy-calibration-v1') { throw 'Unexpected energy calibration schema.' }
    if ($energyStudy.baselineSha256.ToLowerInvariant() -ne 'd49fdffb60f3c7ee41c5e587daaabcdabf95ffd230e3aa947be5de5a291c6a1e') { throw 'Energy calibration baseline hash is invalid.' }
    if (@($energyStudy.variants).Count -ne 31) { throw "Expected 31 energy calibration variants; found $(@($energyStudy.variants).Count)." }
    if ($energyStudy.trialsPerVariant -ne 10000) { throw 'Energy calibration default must be 10,000 trials per variant.' }
    $energyTestPath = '.\tests\StarCluster.Tests\Combat\DirectFire\Tl1EnergyDuelCalibrationTests.cs'
    $energyFacts = @(Select-String -LiteralPath $energyTestPath -SimpleMatch '[Fact]').Count
    if ($energyFacts -ne 10) { throw "Expected 10 energy calibration Fact methods; found $energyFacts." }

    Assert-ReferenceHashes
    Assert-TechnologyCsvContracts
    Assert-Tl1ScenarioCorpusContracts
    Assert-NewUnitTestContracts
    Assert-WorkbookContract

    if ($RepositoryContractOnly) {
        Write-Host ''
        Write-Host 'Checkpoint 28 repository-contract preflight completed successfully.'
        Write-Host 'Manifest, parser, normalization, reference, documentation, CSV, Phase A/B/kinetic/energy calibration corpus, schema, test-source, and workbook contracts passed.'
        return
    }

    Write-Host '[3/11] Confirming Godot is closed and .NET SDK 8.0.423 is selected...'
    $godotProcesses = Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -like 'Godot*' }
    if ($godotProcesses) {
        $processNames = ($godotProcesses.ProcessName | Sort-Object -Unique) -join ', '
        throw "Close Godot before applying Checkpoint 28. Running process(es): $processNames"
    }
    $sdkVersion = dotnet --version
    Write-Host "       SDK: $sdkVersion"
    if ($sdkVersion -ne '8.0.423') { throw "Expected .NET SDK 8.0.423 from global.json, but dotnet selected $sdkVersion." }

    Write-Host '[4/11] Performing a clean compiler preflight with warnings as errors...'
    Get-ChildItem '.\src', '.\tests' -Directory -Recurse -Force -ErrorAction SilentlyContinue | Where-Object { $_.Name -eq 'bin' -or $_.Name -eq 'obj' } | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item '.\src\StarCluster.Game\.godot\mono\temp' -Recurse -Force -ErrorAction SilentlyContinue
    & dotnet build '.\StarCluster.sln' --nologo -warnaserror
    if ($LASTEXITCODE -ne 0) { throw "Clean dotnet build failed with exit code $LASTEXITCODE." }

    Write-Host '[5/11] Running 607 engine-independent tests...'
    $testOutput = & dotnet test '.\tests\StarCluster.Tests\StarCluster.Tests.csproj' --no-build --nologo 2>&1
    $testOutput | Write-Host
    if ($LASTEXITCODE -ne 0) { throw "dotnet test failed with exit code $LASTEXITCODE." }
    if (($testOutput | Out-String) -notmatch 'Passed:\s+607') { throw 'The complete suite did not report the expected 607 passed tests.' }

    Write-Host '[6/11] Running seven accepted deterministic moving-missile scenarios...'
    $legacyOutput = '.\out\checkpoint-28-deterministic'
    Remove-Item $legacyOutput -Recurse -Force -ErrorAction SilentlyContinue
    $legacyText = Invoke-Runner -Arguments @('run-all','--scenario-dir','.\src\StarCluster.ScenarioRunner\Scenarios','--output-dir',$legacyOutput) -Description 'Checkpoint 28 legacy deterministic corpus'
    if ($legacyText -notmatch 'Scenario preflight:\s+7 passed, 0 failed\.' -or $legacyText -notmatch 'Scenarios:\s+7 passed, 0 failed, 7 total\.') { throw 'The legacy deterministic corpus did not report seven passing scenarios.' }

    Write-Host '[7/11] Running 12 TL1 Phase A documents and 54 mechanics cases...'
    $phaseAOutput = '.\out\checkpoint-28-tl1-phase-a'
    Remove-Item $phaseAOutput -Recurse -Force -ErrorAction SilentlyContinue
    $phaseAText = Invoke-Runner -Arguments @('tl1-phase-a','--scenario-dir','.\src\StarCluster.ScenarioRunner\Scenarios\TL1PhaseA','--baseline-file','.\docs\archive\player_technology\pre-cp165-active\tl1_core_combat_numerical_baseline_v0_1.csv','--output-dir',$phaseAOutput) -Description 'Checkpoint 28 TL1 Phase A corpus'
    if ($phaseAText -notmatch 'TL1 Phase A preflight:\s+12 scenario documents, 54 mechanics cases, baseline 126 values; passed\.' -or $phaseAText -notmatch 'TL1 Phase A:\s+12 passed, 0 failed, 12 scenarios; 54 passed, 0 failed, 54 cases\.') { throw 'The TL1 Phase A corpus did not report 12 documents and 54 passing cases.' }

    Write-Host '[8/11] Running seven TL1 Phase B documents and 36 direct-fire cases...'
    $phaseBOutput = '.\out\checkpoint-28-tl1-phase-b'
    if (Test-Path -LiteralPath $phaseBOutput) { Remove-Item -LiteralPath $phaseBOutput -Recurse -Force }
    $phaseBText = (& dotnet run --project .\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --no-build -- tl1-phase-b --output-dir $phaseBOutput 2>&1 | Out-String)
    Write-Host $phaseBText.TrimEnd()
    if ($LASTEXITCODE -ne 0) { throw 'The TL1 Phase B corpus failed.' }
    if ($phaseBText -notmatch 'TL1 Phase B preflight:\s+7 scenario documents, 36 cases, baseline hash verified; passed\.' -or $phaseBText -notmatch 'TL1 Phase B:\s+36 passed, 0 failed, 36 cases\.') { throw 'The TL1 Phase B corpus did not report seven documents and 36 passing cases.' }

    Write-Host '[9/11] Running 29 TL1 kinetic-interaction calibration variants at 10,000 trials each...'
    $phaseCOutput = '.\out\checkpoint-28-tl1-kinetic-calibration'
    Remove-Item $phaseCOutput -Recurse -Force -ErrorAction SilentlyContinue
    $phaseCText = Invoke-Runner -Arguments @('tl1-kinetic-calibration','--study-file','.\src\StarCluster.ScenarioRunner\Scenarios\TL1Calibration\tl1-kc01-kinetic-interaction-study.json','--baseline-file','.\docs\archive\player_technology\pre-cp165-active\tl1_core_combat_numerical_baseline_v0_1.csv','--trials','10000','--jobs','24','--output-dir',$phaseCOutput) -Description 'Checkpoint 28 TL1 kinetic calibration study'
    if ($phaseCText -notmatch 'TL1 Kinetic Calibration preflight:\s+29 variants, baseline hash verified; passed\.' -or $phaseCText -notmatch 'TL1 Kinetic Calibration:\s+29 variants, 10000 trials each, 0 failed gates\.') { throw 'The TL1 kinetic calibration study did not report 29 variants and zero failed gates.' }

    Write-Host '[10/11] Running 31 TL1 energy-interaction calibration variants at 10,000 trials each...'
    $phaseDOutput = '.\out\checkpoint-28-tl1-energy-calibration'
    Remove-Item $phaseDOutput -Recurse -Force -ErrorAction SilentlyContinue
    $phaseDText = Invoke-Runner -Arguments @('tl1-energy-calibration','--study-file','.\src\StarCluster.ScenarioRunner\Scenarios\TL1Calibration\tl1-ec01-energy-interaction-study.json','--baseline-file','.\docs\archive\player_technology\pre-cp165-active\tl1_core_combat_numerical_baseline_v0_1.csv','--trials','10000','--jobs','24','--output-dir',$phaseDOutput) -Description 'Checkpoint 28 TL1 energy calibration study'
    if ($phaseDText -notmatch 'TL1 Energy Calibration preflight:\s+31 variants, baseline hash verified; passed\.' -or $phaseDText -notmatch 'TL1 Energy Calibration:\s+31 variants, 10000 trials each, 0 failed gates\.') { throw 'The TL1 energy calibration study did not report 31 variants and zero failed gates.' }

    Write-Host '[11/11] Running forty-six ScenarioRunner self-tests...'
    $selfTestText = Invoke-Runner -Arguments @('self-test','--scenario-file','.\src\StarCluster.ScenarioRunner\Scenarios\terminal-two-window-hit.json') -Description 'Checkpoint 28 runner self-tests'
    if ($selfTestText -notmatch 'Runner self-tests:\s+46 passed, 0 failed, 46 total\.') { throw 'The runner self-tests did not report 46 passing tests.' }

    Write-Host ''
    Write-Host 'Checkpoint 28 completed successfully.'
    Write-Host 'Engine-independent tests passed: 607.'
    Write-Host 'Legacy deterministic scenarios passed: 7.'
    Write-Host 'TL1 Phase A scenarios passed: 12 documents / 54 cases.'
    Write-Host 'TL1 Phase B scenarios passed: 7 documents / 36 cases.'
    Write-Host 'TL1 kinetic calibration passed: 29 variants / 10,000 trials each / 0 failed gates.'
    Write-Host 'TL1 energy calibration passed: 31 variants / 10,000 trials each / 0 failed gates.'
    Write-Host 'Runner self-tests passed: 46.'
    Write-Host 'Energy Monte Carlo calibration completed; no mechanical Godot validation is required.'
}
finally { Pop-Location }
