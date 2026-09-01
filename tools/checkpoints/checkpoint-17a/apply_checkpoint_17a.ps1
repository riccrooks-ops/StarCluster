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
        throw "$Description file $Path was not found. Re-extract the complete Checkpoint 17a package."
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
        if ($null -eq $entry) {
            throw "Concept document $Path has no word/document.xml entry."
        }
        $reader = New-Object System.IO.StreamReader($entry.Open())
        try { [xml]$documentXml = $reader.ReadToEnd() }
        finally { $reader.Dispose() }

        $wordNamespace = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
        $sectionProperties = $documentXml.GetElementsByTagName('sectPr', $wordNamespace)
        if ($sectionProperties.Count -eq 0) {
            throw "Concept document $Path contains no section properties."
        }

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
                throw "Concept document section margins are too narrow for normal printing: left=$leftMargin, right=$rightMargin twips."
            }
            $printableWidth = $pageWidth - $leftMargin - $rightMargin
            if ($printableWidth -le 0) {
                throw "Concept document section has a non-positive printable width."
            }
            if ($printableWidth -lt $minimumPrintableWidth) {
                $minimumPrintableWidth = $printableWidth
            }
        }

        $tables = $documentXml.GetElementsByTagName('tbl', $wordNamespace)
        foreach ($table in $tables) {
            $tableWidths = $table.GetElementsByTagName('tblW', $wordNamespace)
            if ($tableWidths.Count -gt 0) {
                $tableWidth = $tableWidths.Item(0)
                $widthType = $tableWidth.GetAttribute('type', $wordNamespace)
                $widthValueText = $tableWidth.GetAttribute('w', $wordNamespace)
                if ($widthType -eq 'dxa' -and $widthValueText) {
                    $widthValue = [int]$widthValueText
                    if ($widthValue -gt $minimumPrintableWidth) {
                        throw "Concept document contains a fixed-width table of $widthValue twips, wider than the printable text region of $minimumPrintableWidth twips."
                    }
                }
            }

            $tableGrids = $table.GetElementsByTagName('tblGrid', $wordNamespace)
            if ($tableGrids.Count -gt 0) {
                $gridColumns = $tableGrids.Item(0).GetElementsByTagName('gridCol', $wordNamespace)
                $gridWidth = 0
                foreach ($gridColumn in $gridColumns) {
                    $columnWidthText = $gridColumn.GetAttribute('w', $wordNamespace)
                    if ($columnWidthText) { $gridWidth += [int]$columnWidthText }
                }
                if ($gridWidth -gt $minimumPrintableWidth) {
                    throw "Concept document contains a table grid of $gridWidth twips, wider than the printable text region of $minimumPrintableWidth twips."
                }
            }

            $tableIndents = $table.GetElementsByTagName('tblInd', $wordNamespace)
            if ($tableIndents.Count -gt 0) {
                $indentText = $tableIndents.Item(0).GetAttribute('w', $wordNamespace)
                if ($indentText -and [int]$indentText -lt 0) {
                    throw "Concept document contains a table with a negative left indent ($indentText twips)."
                }
            }
        }
    }
    finally { $archive.Dispose() }
}

try {
    Write-Host '[1/11] Verifying the Star Cluster repository and applied Checkpoint 17...'
    if (-not (Test-Path '.\StarCluster.sln')) {
        throw "StarCluster.sln was not found at $repositoryRoot. Extract the package into the repository root."
    }
    foreach ($priorFile in @(
        '.\docs\checkpoints\Checkpoint_17_Missile_Local_Sensors_Report_Arbitration_And_Trail_Clarity.md',
        '.\tools\checkpoints\checkpoint-17\apply_checkpoint_17.ps1',
        '.\src\StarCluster.Core\Combat\Missiles\MissileAutonomousGuidanceService.cs',
        '.\tests\StarCluster.Tests\Combat\Missiles\MissileLocalSensorGuidanceTests.cs')) {
        if (-not (Test-Path $priorFile)) {
            throw "Required Checkpoint 17 file $priorFile was not found. Apply the complete corrected Checkpoint 17 archive before Checkpoint 17a."
        }
    }

    $expectedV03oHash = '8a3a5f07a358a968bce0a4fff9e9eb12bdc6aabaa953f0715cee2efb21662d6b'
    $priorRootConcept = '.\docs\Star_Cluster_Game_Concept_v0.3o.docx'
    $priorArchivedConcept = '.\docs\archive\Star_Cluster_Game_Concept_v0.3o.docx'
    if (Test-Path $priorRootConcept) { $priorConceptPath = $priorRootConcept }
    elseif (Test-Path $priorArchivedConcept) { $priorConceptPath = $priorArchivedConcept }
    else { throw "Required Checkpoint 17 Concept v0.3o was not found at $priorRootConcept or $priorArchivedConcept." }
    $priorHash = (Get-FileHash $priorConceptPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($priorHash -ne $expectedV03oHash) {
        throw "The prior Concept v0.3o hash at $priorConceptPath is $priorHash, expected $expectedV03oHash."
    }

    Write-Host '[2/11] Confirming that Godot is closed...'
    $godotProcesses = Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -like 'Godot*' }
    if ($godotProcesses) {
        $processNames = ($godotProcesses.ProcessName | Sort-Object -Unique) -join ', '
        throw "Close the Godot editor and debug window before applying Checkpoint 17a. Running process(es): $processNames"
    }

    Write-Host '[3/11] Checking the pinned .NET SDK...'
    $sdkVersion = dotnet --version
    Write-Host "       SDK: $sdkVersion"
    if ($sdkVersion -ne '8.0.423') {
        throw "Expected .NET SDK 8.0.423 from global.json, but dotnet selected $sdkVersion."
    }

    Write-Host '[4/11] Verifying exact local-observation coordinates and causal edge diagnostics...'
    Assert-FileContains '.\src\StarCluster.Core\Diagnostics\DiagnosticEventType.cs' @(
        'MissileMovementEdgeResolved') 'Diagnostic event categories'
    Assert-FileContains '.\src\StarCluster.Game\Scripts\Main.cs' @(
        'private const string CheckpointVersion = "checkpoint-17a";',
        'RecordAutonomousMissileAction(',
        'RecordMissileMovementEdge(',
        'DiagnosticEventType.MissileMovementEdgeResolved',
        '("missileCoordinate", Format(missileCoordinate))',
        'MissileGuidanceObservationOpportunity.AfterEnteredHex',
        'BuildPersistentMissilePhaseFeedback') 'Checkpoint 17a Godot integration'

    Write-Host '[5/11] Verifying observer trail lifecycle, selection, feedback, and opacity corrections...'
    Assert-FileContains '.\src\StarCluster.Game\Scripts\Main.cs' @(
        'LogObserverTrailLifecycleForTrackUpdate',
        'ObservedTrailSegmentStarted',
        'ObservedTrailSegmentClosed',
        'deselectSingleMissile',
        'Deselected the missile',
        '_persistentMissilePhaseFeedback',
        'Observation steps:') 'Checkpoint 17a presentation integration'
    Assert-FileContains '.\src\StarCluster.Game\Scripts\HexBoardView.cs' @(
        'Keep a readable minimum opacity',
        'TacticalTrackQuality.Stale => selectedTrail ? 0.52f : 0.28f',
        'TacticalTrackQuality.Approximate => selectedTrail ? 0.66f : 0.34f',
        '_ => selectedTrail ? 0.80f : 0.44f') 'Observed trail opacity floor'

    Write-Host '[6/11] Verifying synchronized documentation and exact validation procedure...'
    foreach ($documentationFile in @(
        '.\docs\README.md',
        '.\docs\Prototype_TODO.md',
        '.\docs\checkpoints\Checkpoint_17a_Causal_Missile_Diagnostics_And_Validation_Clarity.md',
        '.\docs\design\Missile_Guidance_Datalink_Sensor_And_Seeker_Architecture.md',
        '.\docs\validation\Baseline_Tactical_Regression_Encounter.md',
        '.\src\StarCluster.Game\README.md')) {
        if (-not (Test-Path $documentationFile)) { throw "Required Checkpoint 17a documentation file $documentationFile was not found." }
    }
    Assert-FileContains '.\docs\validation\Baseline_Tactical_Regression_Encounter.md' @(
        'Checkpoint 17a corrective validation - exact causal diagnostics and UI clarity',
        '(-2,-1) -> (-3,0)',
        'MissileMovementEdgeResolved',
        'ObservedTrailSegmentStarted',
        'Click the same singly selected missile again',
        'AUTHORITATIVE DEBUG',
        'Checkpoint 17a acceptance summary') 'Checkpoint 17a validation runbook'
    Assert-FileContains '.\docs\checkpoints\Checkpoint_17a_Causal_Missile_Diagnostics_And_Validation_Clarity.md' @(
        'Causal missile journal',
        'Exact local-sensor coordinates',
        'Observer trail lifecycle',
        'Expected complete suite: **490 tests**') 'Checkpoint 17a documentation'

    Write-Host '[7/11] Verifying Concept v0.3p, archive continuity, and printable tables...'
    foreach ($conceptFile in @(
        '.\docs\Star_Cluster_Game_Concept_v0.3p.docx',
        '.\docs\archive\Star_Cluster_Game_Concept_v0.3o.docx')) {
        if (-not (Test-Path $conceptFile)) { throw "Required Concept file $conceptFile was not found." }
    }
    $archivedHash = (Get-FileHash '.\docs\archive\Star_Cluster_Game_Concept_v0.3o.docx' -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($archivedHash -ne $expectedV03oHash) { throw "The archived Concept v0.3o hash is $archivedHash, expected $expectedV03oHash." }
    $expectedV03pHash = '77fbdf2c699300218f282f8dde84e46abee4fe372a251051d0533e75a9c7471b'
    $currentHash = (Get-FileHash '.\docs\Star_Cluster_Game_Concept_v0.3p.docx' -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($currentHash -ne $expectedV03pHash) { throw "Concept v0.3p hash is $currentHash, expected $expectedV03pHash. Re-extract the complete Checkpoint 17a package." }
    Assert-ConceptPrintLayout '.\docs\Star_Cluster_Game_Concept_v0.3p.docx'
    Assert-FileContains '.\docs\README.md' @(
        'Star_Cluster_Game_Concept_v0.3p.docx',
        'Checkpoint_17a_Causal_Missile_Diagnostics_And_Validation_Clarity.md') 'Documentation index'

    Write-Host '[8/11] Verifying the accepted test suite and diagnostic semantics fixture...'
    Assert-FileContains '.\tests\StarCluster.Tests\Diagnostics\DiagnosticEventSemanticsTests.cs' @(
        'DiagnosticEventType.MissileMovementEdgeResolved',
        'GuidanceLifecycleCanBeRecordedInCausalOrder') 'DiagnosticEventSemanticsTests'
    $arbitrationTests = '.\tests\StarCluster.Tests\Combat\Missiles\MissileGuidanceArbitrationTests.cs'
    $sensorTests = '.\tests\StarCluster.Tests\Combat\Missiles\MissileLocalSensorGuidanceTests.cs'
    foreach ($testFile in @($arbitrationTests, $sensorTests)) {
        if (-not (Test-Path $testFile)) { throw "Checkpoint 17 test file $testFile was not found." }
        $factCount = (Select-String -Path $testFile -Pattern '\[Fact\]' -AllMatches).Matches.Count
        if ($factCount -ne 10) { throw "Expected 10 Checkpoint 17 [Fact] tests in $testFile, but found $factCount." }
    }

    Write-Host '[9/11] Refreshing generated Godot managed metadata and solution membership...'
    Remove-Item -Recurse -Force '.\src\StarCluster.Game\.godot\mono' -ErrorAction SilentlyContinue
    $solutionOutput = dotnet sln '.\StarCluster.sln' list
    if ($LASTEXITCODE -ne 0) { throw "dotnet sln list failed with exit code $LASTEXITCODE." }
    $solutionText = $solutionOutput | Out-String
    if ($solutionText -notmatch 'StarCluster.Game.csproj') {
        dotnet sln '.\StarCluster.sln' add '.\src\StarCluster.Game\StarCluster.Game.csproj'
        if ($LASTEXITCODE -ne 0) { throw "Could not add StarCluster.Game to the solution; exit code $LASTEXITCODE." }
    }

    Write-Host '[10/11] Building the complete solution with warnings treated as errors...'
    dotnet build '.\StarCluster.sln' --nologo -warnaserror
    if ($LASTEXITCODE -ne 0) { throw "dotnet build failed with exit code $LASTEXITCODE." }

    Write-Host '[11/11] Running tests and confirming the one-way architecture...'
    $testOutput = dotnet test '.\tests\StarCluster.Tests\StarCluster.Tests.csproj' --no-build --nologo
    $testOutput | Write-Host
    if ($LASTEXITCODE -ne 0) { throw "dotnet test failed with exit code $LASTEXITCODE." }
    $testText = $testOutput | Out-String
    if ($testText -notmatch 'Passed:\s+490') { throw 'The complete suite did not report the expected 490 passed tests.' }
    if (Select-String -Path '.\src\StarCluster.Core\StarCluster.Core.csproj' -Pattern 'Godot' -Quiet) {
        throw 'StarCluster.Core unexpectedly contains a Godot dependency.'
    }

    Remove-Item '.\docs\Star_Cluster_Game_Concept_v0.3o.docx' -Force -ErrorAction SilentlyContinue

    Write-Host ''
    Write-Host 'Checkpoint 17a completed successfully.'
    Write-Host 'Expected engine-independent tests passed: 490.'
    Write-Host 'Reopen Godot and run the Checkpoint 17a corrective validation in docs\validation\Baseline_Tactical_Regression_Encounter.md.'
    Write-Host 'Use the embedded numbered notes fields to record exact causal event order, local-observation coordinates, trail lifecycle, click-again deselection, persistent interception feedback, opacity floor, and debug-panel agreement.'
    Write-Host 'Upload the matching checkpoint-17a .log and .jsonl files, completed notes, and requested screenshots.'
    Write-Host 'Next substantive checkpoint: terminal seeker acquisition, lock retention/loss, search behavior, and capability-specific terminal attack gates.'
}
finally {
    Pop-Location
}
