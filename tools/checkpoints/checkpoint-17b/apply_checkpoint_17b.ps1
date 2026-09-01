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
        throw "$Description file $Path was not found. Re-extract the complete Checkpoint 17b package."
    }
    foreach ($pattern in $Patterns) {
        if (-not (Select-String -Path $Path -Pattern ([regex]::Escape($pattern)) -Quiet)) {
            throw "$Description is missing required content: $pattern"
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

try {
    Write-Host '[1/10] Verifying repository and accepted Checkpoint 17a baseline...'
    if (-not (Test-Path '.\StarCluster.sln')) {
        throw "StarCluster.sln was not found at $repositoryRoot. Extract the package into the repository root."
    }
    foreach ($priorFile in @(
        '.\docs\checkpoints\Checkpoint_17a_Causal_Missile_Diagnostics_And_Validation_Clarity.md',
        '.\tools\checkpoints\checkpoint-17a\apply_checkpoint_17a.ps1',
        '.\src\StarCluster.Game\Scripts\Main.cs',
        '.\src\StarCluster.Game\Scripts\DemoScenarioFactory.cs',
        '.\tests\StarCluster.Tests\Combat\Missiles\MissileLocalSensorGuidanceTests.cs')) {
        if (-not (Test-Path $priorFile)) {
            throw "Required Checkpoint 17a baseline file $priorFile was not found."
        }
    }

    $expectedV03pHash = '77fbdf2c699300218f282f8dde84e46abee4fe372a251051d0533e75a9c7471b'
    $priorRootConcept = '.\docs\Star_Cluster_Game_Concept_v0.3p.docx'
    $priorArchivedConcept = '.\docs\archive\Star_Cluster_Game_Concept_v0.3p.docx'
    if (Test-Path $priorRootConcept) { $priorConceptPath = $priorRootConcept }
    elseif (Test-Path $priorArchivedConcept) { $priorConceptPath = $priorArchivedConcept }
    else { throw 'Required accepted Concept v0.3p was not found in docs or docs\archive.' }
    $priorHash = (Get-FileHash $priorConceptPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($priorHash -ne $expectedV03pHash) {
        throw "Accepted Concept v0.3p hash is $priorHash, expected $expectedV03pHash."
    }

    Write-Host '[2/10] Confirming that Godot is closed...'
    $godotProcesses = Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -like 'Godot*' }
    if ($godotProcesses) {
        $processNames = ($godotProcesses.ProcessName | Sort-Object -Unique) -join ', '
        throw "Close the Godot editor and debug window before applying Checkpoint 17b. Running process(es): $processNames"
    }

    Write-Host '[3/10] Checking the pinned .NET SDK...'
    $sdkVersion = dotnet --version
    Write-Host "       SDK: $sdkVersion"
    if ($sdkVersion -ne '8.0.423') {
        throw "Expected .NET SDK 8.0.423 from global.json, but dotnet selected $sdkVersion."
    }

    Write-Host '[4/10] Verifying the AUTHORITATIVE DEBUG usability hotfix...'
    Assert-FileContains '.\src\StarCluster.Game\Scripts\Main.cs' @(
        'private const string CheckpointVersion = "checkpoint-17b";',
        'private ScrollContainer _detailScroll = null!;',
        'CustomMinimumSize = new Vector2(0.0f, 190.0f)',
        'ScrollAuthoritativeMissileDebugIntoView',
        'CallDeferred(nameof(ScrollAuthoritativeMissileDebugIntoView))') 'Checkpoint 17b debug-panel integration'

    Write-Host '[5/10] Verifying the dedicated friendly Missile Flight fixture...'
    Assert-FileContains '.\src\StarCluster.Game\Scripts\DemoScenarioFactory.cs' @(
        'Friendly missile route validation',
        'CreateFriendlyMissileRouteScenario()',
        'A dedicated clear, Firm-track fixture') 'Checkpoint 17b scenario fixture'

    Write-Host '[6/10] Verifying synchronized documentation and validation archive policy...'
    foreach ($documentationFile in @(
        '.\docs\README.md',
        '.\docs\Prototype_TODO.md',
        '.\docs\checkpoints\Checkpoint_17b_Combat_Concept_Consolidation_And_Validation_UX_Hotfixes.md',
        '.\docs\design\Missile_Guidance_Datalink_Sensor_And_Seeker_Architecture.md',
        '.\docs\validation\Checkpoint_17b_Combat_Concept_And_Validation_UX_Hotfixes.md',
        '.\docs\validation\archive\Tested_Tactical_Regression_Checkpoints_09_Through_17a.md',
        '.\src\StarCluster.Game\README.md')) {
        if (-not (Test-Path $documentationFile)) {
            throw "Required Checkpoint 17b documentation file $documentationFile was not found."
        }
    }
    Assert-FileContains '.\docs\validation\Checkpoint_17b_Combat_Concept_And_Validation_UX_Hotfixes.md' @(
        'AUTHORITATIVE DEBUG usability hotfix',
        'Dedicated friendly Missile Flight route fixture',
        '490/490 engine-independent tests pass',
        'only active manual validation procedure') 'Checkpoint 17b active validation runbook'
    Assert-FileContains '.\docs\checkpoints\Checkpoint_17b_Combat_Concept_Consolidation_And_Validation_UX_Hotfixes.md' @(
        'Usable AUTHORITATIVE DEBUG region',
        'Dedicated friendly Missile Flight route fixture',
        'Concept v0.3q consolidation',
        'Expected complete suite: **490 tests**') 'Checkpoint 17b checkpoint documentation'

    Write-Host '[7/10] Verifying Concept v0.3q and archive continuity...'
    foreach ($conceptFile in @(
        '.\docs\Star_Cluster_Game_Concept_v0.3q.docx',
        '.\docs\archive\Star_Cluster_Game_Concept_v0.3p.docx')) {
        if (-not (Test-Path $conceptFile)) { throw "Required Concept file $conceptFile was not found." }
    }
    $archivedHash = (Get-FileHash '.\docs\archive\Star_Cluster_Game_Concept_v0.3p.docx' -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($archivedHash -ne $expectedV03pHash) {
        throw "Archived Concept v0.3p hash is $archivedHash, expected $expectedV03pHash."
    }
    $expectedV03qHash = '4a7dfa6c3180f913811b15cfa0f47e4b1ee242d4bdebbad7bfc0ffd23ffb3a99'
    $currentHash = (Get-FileHash '.\docs\Star_Cluster_Game_Concept_v0.3q.docx' -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($currentHash -ne $expectedV03qHash) {
        throw "Concept v0.3q hash is $currentHash, expected $expectedV03qHash. Re-extract the complete Checkpoint 17b package."
    }
    Assert-ConceptPrintLayout '.\docs\Star_Cluster_Game_Concept_v0.3q.docx'
    Assert-FileContains '.\docs\README.md' @(
        'Star_Cluster_Game_Concept_v0.3q.docx',
        'Checkpoint_17b_Combat_Concept_Consolidation_And_Validation_UX_Hotfixes.md') 'Documentation index'

    Write-Host '[8/10] Refreshing generated Godot managed metadata and solution membership...'
    Remove-Item -Recurse -Force '.\src\StarCluster.Game\.godot\mono' -ErrorAction SilentlyContinue
    $solutionOutput = dotnet sln '.\StarCluster.sln' list
    if ($LASTEXITCODE -ne 0) { throw "dotnet sln list failed with exit code $LASTEXITCODE." }
    $solutionText = $solutionOutput | Out-String
    if ($solutionText -notmatch 'StarCluster.Game.csproj') {
        dotnet sln '.\StarCluster.sln' add '.\src\StarCluster.Game\StarCluster.Game.csproj'
        if ($LASTEXITCODE -ne 0) { throw "Could not add StarCluster.Game to the solution; exit code $LASTEXITCODE." }
    }

    Write-Host '[9/10] Building the complete solution with warnings treated as errors...'
    dotnet build '.\StarCluster.sln' --nologo -warnaserror
    if ($LASTEXITCODE -ne 0) { throw "dotnet build failed with exit code $LASTEXITCODE." }

    Write-Host '[10/10] Running the accepted test suite and checking one-way architecture...'
    $testOutput = dotnet test '.\tests\StarCluster.Tests\StarCluster.Tests.csproj' --no-build --nologo
    $testOutput | Write-Host
    if ($LASTEXITCODE -ne 0) { throw "dotnet test failed with exit code $LASTEXITCODE." }
    $testText = $testOutput | Out-String
    if ($testText -notmatch 'Passed:\s+490') { throw 'The complete suite did not report the expected 490 passed tests.' }
    if (Select-String -Path '.\src\StarCluster.Core\StarCluster.Core.csproj' -Pattern 'Godot' -Quiet) {
        throw 'StarCluster.Core unexpectedly contains a Godot dependency.'
    }

    Remove-Item '.\docs\Star_Cluster_Game_Concept_v0.3o.docx' -Force -ErrorAction SilentlyContinue
    Remove-Item '.\docs\Star_Cluster_Game_Concept_v0.3p.docx' -Force -ErrorAction SilentlyContinue
    Remove-Item '.\docs\validation\Baseline_Tactical_Regression_Encounter.md' -Force -ErrorAction SilentlyContinue

    Write-Host ''
    Write-Host 'Checkpoint 17b completed successfully.'
    Write-Host 'Expected engine-independent tests passed: 490.'
    Write-Host 'Reopen Godot and run docs\validation\Checkpoint_17b_Combat_Concept_And_Validation_UX_Hotfixes.md.'
    Write-Host 'Preserve the matching checkpoint-17b logs and the requested debug-panel and route screenshots.'
    Write-Host 'Next substantive checkpoint: unified Firm terminal solutions and seeker-assisted acquisition.'
}
finally {
    Pop-Location
}
