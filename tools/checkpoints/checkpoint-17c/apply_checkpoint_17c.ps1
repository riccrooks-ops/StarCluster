[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repositoryRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
Push-Location $repositoryRoot

function Assert-FileContains {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string[]]$Patterns,
        [Parameter(Mandatory = $true)][string]$Description
    )
    if (-not (Test-Path $Path)) {
        throw "$Description file $Path was not found. Re-extract the complete Checkpoint 17c package."
    }
    foreach ($pattern in $Patterns) {
        if (-not (Select-String -Path $Path -Pattern ([regex]::Escape($pattern)) -Quiet)) {
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
    if (-not (Test-Path $Path)) {
        throw "$Description file $Path was not found. Re-extract the complete Checkpoint 17c package."
    }
    foreach ($pattern in $Patterns) {
        if (Select-String -Path $Path -Pattern ([regex]::Escape($pattern)) -Quiet) {
            throw "$Description still contains forbidden content: $pattern"
        }
    }
}

function Assert-ConceptPrintLayout {
    param([Parameter(Mandatory = $true)][string]$Path)

    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $archive = [System.IO.Compression.ZipFile]::OpenRead((Resolve-Path $Path).Path)
    try {
        $entry = $archive.GetEntry('word/document.xml')
        if ($null -eq $entry) { throw "Concept document $Path has no word/document.xml entry." }
        $reader = New-Object System.IO.StreamReader($entry.Open())
        try { [xml]$documentXml = $reader.ReadToEnd() }
        finally { $reader.Dispose() }

        $wordNamespace = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
        $sectionProperties = $documentXml.GetElementsByTagName('sectPr', $wordNamespace)
        if ($sectionProperties.Count -eq 0) { throw "Concept document $Path contains no section properties." }
        $minimumPrintableWidth = [int]::MaxValue
        foreach ($section in $sectionProperties) {
            $pageSizes = $section.GetElementsByTagName('pgSz', $wordNamespace)
            $pageMargins = $section.GetElementsByTagName('pgMar', $wordNamespace)
            if ($pageSizes.Count -eq 0 -or $pageMargins.Count -eq 0) {
                throw "Concept document $Path contains a section without explicit page size and margins."
            }
            $pageSize = $pageSizes.Item(0)
            $pageMargin = $pageMargins.Item(0)
            $pageWidth = [int]$pageSize.GetAttribute('w', $wordNamespace)
            $leftMargin = [int]$pageMargin.GetAttribute('left', $wordNamespace)
            $rightMargin = [int]$pageMargin.GetAttribute('right', $wordNamespace)
            if ($leftMargin -lt 700 -or $rightMargin -lt 700) {
                throw "Concept section margins are too narrow: left=$leftMargin, right=$rightMargin twips."
            }
            $printableWidth = $pageWidth - $leftMargin - $rightMargin
            if ($printableWidth -le 0) { throw 'Concept section has a non-positive printable width.' }
            if ($printableWidth -lt $minimumPrintableWidth) { $minimumPrintableWidth = $printableWidth }
        }

        $tables = $documentXml.GetElementsByTagName('tbl', $wordNamespace)
        foreach ($table in $tables) {
            $tableGrids = $table.GetElementsByTagName('tblGrid', $wordNamespace)
            if ($tableGrids.Count -gt 0) {
                $gridColumns = $tableGrids.Item(0).GetElementsByTagName('gridCol', $wordNamespace)
                $gridWidth = 0
                foreach ($gridColumn in $gridColumns) {
                    $columnWidthText = $gridColumn.GetAttribute('w', $wordNamespace)
                    if ($columnWidthText) { $gridWidth += [int]$columnWidthText }
                }
                if ($gridWidth -gt $minimumPrintableWidth) {
                    throw "Concept contains a table grid of $gridWidth twips, wider than printable width $minimumPrintableWidth."
                }
            }
            $tableIndents = $table.GetElementsByTagName('tblInd', $wordNamespace)
            if ($tableIndents.Count -gt 0) {
                $indentText = $tableIndents.Item(0).GetAttribute('w', $wordNamespace)
                if ($indentText -and [int]$indentText -lt 0) {
                    throw "Concept contains a table with negative left indent $indentText twips."
                }
            }
        }
    }
    finally { $archive.Dispose() }
}

function Assert-ReferenceManifest {
    param(
        [Parameter(Mandatory = $true)][string]$Directory,
        [Parameter(Mandatory = $true)][string]$ManifestPath
    )
    if (-not (Test-Path $ManifestPath)) { throw "Reference manifest $ManifestPath was not found." }
    foreach ($line in Get-Content $ManifestPath) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        if ($line -notmatch '^([0-9a-fA-F]{64})\s+(.+)$') {
            throw "Malformed reference manifest line: $line"
        }
        $expectedHash = $Matches[1].ToLowerInvariant()
        $relativeName = $Matches[2]
        $referencePath = Join-Path $Directory $relativeName
        if (-not (Test-Path $referencePath)) {
            throw "Reference file $relativeName is missing from $Directory."
        }
        $actualHash = (Get-FileHash $referencePath -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actualHash -ne $expectedHash) {
            throw "Reference file $relativeName hash is $actualHash, expected $expectedHash."
        }
    }
}

try {
    Write-Host '[1/12] Verifying repository and accepted Checkpoint 17b baseline...'
    if (-not (Test-Path '.\StarCluster.sln')) {
        throw "StarCluster.sln was not found at $repositoryRoot. Extract the package into the repository root."
    }
    foreach ($priorFile in @(
        '.\docs\checkpoints\Checkpoint_17b_Combat_Concept_Consolidation_And_Validation_UX_Hotfixes.md',
        '.\tools\checkpoints\checkpoint-17b\apply_checkpoint_17b.ps1',
        '.\src\StarCluster.Game\Scripts\Main.cs',
        '.\src\StarCluster.Game\Scripts\HexBoardView.cs',
        '.\src\StarCluster.Game\Scripts\DemoScenarioFactory.cs',
        '.\tests\StarCluster.Tests\Combat\Missiles\MissileLocalSensorGuidanceTests.cs')) {
        if (-not (Test-Path $priorFile)) {
            throw "Required Checkpoint 17b baseline file $priorFile was not found."
        }
    }

    $expectedV03qHash = '4a7dfa6c3180f913811b15cfa0f47e4b1ee242d4bdebbad7bfc0ffd23ffb3a99'
    $priorRootConcept = '.\docs\Star_Cluster_Game_Concept_v0.3q.docx'
    $priorArchivedConcept = '.\docs\archive\Star_Cluster_Game_Concept_v0.3q.docx'
    if (Test-Path $priorRootConcept) { $priorConceptPath = $priorRootConcept }
    elseif (Test-Path $priorArchivedConcept) { $priorConceptPath = $priorArchivedConcept }
    else { throw 'Required accepted Concept v0.3q was not found in docs or docs\archive.' }
    $priorHash = (Get-FileHash $priorConceptPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($priorHash -ne $expectedV03qHash) {
        throw "Accepted Concept v0.3q hash is $priorHash, expected $expectedV03qHash."
    }

    Write-Host '[2/12] Confirming that Godot is closed...'
    $godotProcesses = Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -like 'Godot*' }
    if ($godotProcesses) {
        $processNames = ($godotProcesses.ProcessName | Sort-Object -Unique) -join ', '
        throw "Close the Godot editor and debug window before applying Checkpoint 17c. Running process(es): $processNames"
    }

    Write-Host '[3/12] Checking the pinned .NET SDK...'
    $sdkVersion = dotnet --version
    Write-Host "       SDK: $sdkVersion"
    if ($sdkVersion -ne '8.0.423') {
        throw "Expected .NET SDK 8.0.423 from global.json, but dotnet selected $sdkVersion."
    }

    Write-Host '[4/12] Verifying the expanded AUTHORITATIVE DEBUG presentation...'
    Assert-FileContains '.\src\StarCluster.Game\Scripts\Main.cs' @(
        'private const string CheckpointVersion = "checkpoint-17c";',
        'commandControls.AddChild(CreateSectionLabel("Development diagnostics"));',
        'CustomMinimumSize = new Vector2(0.0f, 280.0f)',
        'CallDeferred(nameof(ScrollAuthoritativeMissileDebugIntoView))',
        'Filenames include checkpoint-17c') 'Checkpoint 17c debug-panel integration'
    Assert-FileContains '.\src\StarCluster.Game\project.godot' @(
        'window/size/viewport_width=1440',
        'window/size/viewport_height=900',
        'window/size/window_width_override=1440',
        'window/size/window_height_override=900') 'Checkpoint 17c default viewport'

    Write-Host '[5/12] Verifying selected-only friendly missile planning and trails...'
    Assert-FileContains '.\src\StarCluster.Game\Scripts\HexBoardView.cs' @(
        'Historical travel is selected-only to keep the normal tactical map uncluttered.',
        'if (contact.OwnerSide == TacticalSide.Player)',
        'return selected;',
        'target {contact.TargetId}; range {contact.RemainingRange}/{contact.MaximumRange}') 'Checkpoint 17c friendly missile presentation'
    Assert-FileNotContains '.\src\StarCluster.Game\Scripts\HexBoardView.cs' @(
        'executedPlan =',
        'selection only emphasizes it') 'Checkpoint 17c removal of persistent/future solid route rendering'

    Write-Host '[6/12] Verifying synchronized Checkpoint 17c documentation...'
    foreach ($documentationFile in @(
        '.\docs\README.md',
        '.\docs\Prototype_TODO.md',
        '.\docs\checkpoints\Checkpoint_17c_Presentation_Concept_Power_Repair_And_Reference_Handoff.md',
        '.\docs\validation\Checkpoint_17c_Presentation_Concept_And_Reference_Handoff.md',
        '.\docs\validation\archive\Checkpoint_17b_Partial_Validation_Results.md',
        '.\docs\validation\archive\Tested_Tactical_Regression_Checkpoints_09_Through_17a.md',
        '.\docs\validation\evidence\checkpoint-17b-partial\README.md',
        '.\docs\validation\evidence\checkpoint-17b-partial\SHA256SUMS.txt',
        '.\src\StarCluster.Game\README.md')) {
        if (-not (Test-Path $documentationFile)) {
            throw "Required Checkpoint 17c documentation file $documentationFile was not found."
        }
    }
    Assert-FileContains '.\docs\validation\Checkpoint_17c_Presentation_Concept_And_Reference_Handoff.md' @(
        'AUTHORITATIVE DEBUG correction',
        'Friendly Missile Flight decluttering',
        'Observer-safe boundary checks carried from 17b',
        '490/490 engine-independent tests pass') 'Checkpoint 17c active validation runbook'

    Write-Host '[7/12] Verifying Concept v0.3r and archive continuity...'
    foreach ($conceptFile in @(
        '.\docs\Star_Cluster_Game_Concept_v0.3r.docx',
        '.\docs\archive\Star_Cluster_Game_Concept_v0.3q.docx')) {
        if (-not (Test-Path $conceptFile)) { throw "Required Concept file $conceptFile was not found." }
    }
    $archivedHash = (Get-FileHash '.\docs\archive\Star_Cluster_Game_Concept_v0.3q.docx' -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($archivedHash -ne $expectedV03qHash) {
        throw "Archived Concept v0.3q hash is $archivedHash, expected $expectedV03qHash."
    }
    $expectedV03rHash = '633e0f90e31183158f1ec156965ea9beed339948f4b089c393312a9722033dc8'
    $currentHash = (Get-FileHash '.\docs\Star_Cluster_Game_Concept_v0.3r.docx' -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($currentHash -ne $expectedV03rHash) {
        throw "Concept v0.3r hash is $currentHash, expected $expectedV03rHash. Re-extract the complete Checkpoint 17c package."
    }
    Assert-ConceptPrintLayout '.\docs\Star_Cluster_Game_Concept_v0.3r.docx'
    Assert-FileContains '.\docs\README.md' @(
        'Star_Cluster_Game_Concept_v0.3r.docx',
        'Checkpoint_17c_Presentation_Concept_Power_Repair_And_Reference_Handoff.md') 'Documentation index'

    Write-Host '[8/12] Verifying the complete packaged reference library...'
    $expectedReferenceManifestHash = '070ced666ad12a448d6767769ac4ff6e38379ecb5d182dae7ce83f9bad786db4'
    $referenceManifestHash = (Get-FileHash '.\docs\references\SHA256SUMS.txt' -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($referenceManifestHash -ne $expectedReferenceManifestHash) {
        throw "Reference manifest hash is $referenceManifestHash, expected $expectedReferenceManifestHash."
    }
    Assert-ReferenceManifest '.\docs\references' '.\docs\references\SHA256SUMS.txt'
    $referenceCount = (Get-ChildItem '.\docs\references' -File | Where-Object { $_.Name -notin @('README.md', 'SHA256SUMS.txt') }).Count
    if ($referenceCount -ne 12) {
        throw "Expected 12 packaged external reference files, found $referenceCount."
    }

    Write-Host '[9/12] Refreshing generated Godot managed metadata and solution membership...'
    Remove-Item -Recurse -Force '.\src\StarCluster.Game\.godot\mono' -ErrorAction SilentlyContinue
    $solutionOutput = dotnet sln '.\StarCluster.sln' list
    if ($LASTEXITCODE -ne 0) { throw "dotnet sln list failed with exit code $LASTEXITCODE." }
    $solutionText = $solutionOutput | Out-String
    if ($solutionText -notmatch 'StarCluster.Game.csproj') {
        dotnet sln '.\StarCluster.sln' add '.\src\StarCluster.Game\StarCluster.Game.csproj'
        if ($LASTEXITCODE -ne 0) { throw "Could not add StarCluster.Game to the solution; exit code $LASTEXITCODE." }
    }

    Write-Host '[10/12] Building the complete solution with warnings treated as errors...'
    dotnet build '.\StarCluster.sln' --nologo -warnaserror
    if ($LASTEXITCODE -ne 0) { throw "dotnet build failed with exit code $LASTEXITCODE." }

    Write-Host '[11/12] Running the accepted test suite and checking one-way architecture...'
    $testOutput = dotnet test '.\tests\StarCluster.Tests\StarCluster.Tests.csproj' --no-build --nologo
    $testOutput | Write-Host
    if ($LASTEXITCODE -ne 0) { throw "dotnet test failed with exit code $LASTEXITCODE." }
    $testText = $testOutput | Out-String
    if ($testText -notmatch 'Passed:\s+490') { throw 'The complete suite did not report the expected 490 passed tests.' }
    if (Select-String -Path '.\src\StarCluster.Core\StarCluster.Core.csproj' -Pattern 'Godot' -Quiet) {
        throw 'StarCluster.Core unexpectedly contains a Godot dependency.'
    }

    Write-Host '[12/12] Removing superseded current-root and active-validation artifacts...'
    foreach ($obsoleteFile in @(
        '.\docs\Star_Cluster_Game_Concept_v0.3p.docx',
        '.\docs\Star_Cluster_Game_Concept_v0.3q.docx',
        '.\docs\validation\Checkpoint_17b_Combat_Concept_And_Validation_UX_Hotfixes.md',
        '.\docs\validation\Baseline_Tactical_Regression_Encounter.md')) {
        Remove-Item $obsoleteFile -Force -ErrorAction SilentlyContinue
    }

    Write-Host ''
    Write-Host 'Checkpoint 17c completed successfully.'
    Write-Host 'Expected engine-independent tests passed: 490.'
    Write-Host 'The complete indexed reference library is present under docs\references.'
    Write-Host 'Reopen Godot and run docs\validation\Checkpoint_17c_Presentation_Concept_And_Reference_Handoff.md.'
    Write-Host 'Preserve the matching checkpoint-17c logs and requested screenshots.'
    Write-Host 'Next substantive checkpoint: unified Firm terminal solutions and seeker-assisted acquisition.'
}
finally {
    Pop-Location
}
