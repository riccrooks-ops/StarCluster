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
        throw "$Description file $Path was not found. Re-extract the Checkpoint 15 package."
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
        try {
            [xml]$documentXml = $reader.ReadToEnd()
        }
        finally {
            $reader.Dispose()
        }

        $wordNamespace = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
        $tables = $documentXml.GetElementsByTagName('tbl', $wordNamespace)
        foreach ($table in $tables) {
            $tableWidths = $table.GetElementsByTagName('tblW', $wordNamespace)
            if ($tableWidths.Count -gt 0) {
                $tableWidth = $tableWidths.Item(0)
                $widthType = $tableWidth.GetAttribute('type', $wordNamespace)
                $widthValueText = $tableWidth.GetAttribute('w', $wordNamespace)
                if ($widthType -eq 'dxa' -and $widthValueText) {
                    $widthValue = [int]$widthValueText
                    if ($widthValue -gt 10000) {
                        throw "Concept document contains a fixed-width table of $widthValue twips, wider than the printable text region."
                    }
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

        $sectionProperties = $documentXml.GetElementsByTagName('sectPr', $wordNamespace)
        foreach ($section in $sectionProperties) {
            $pageMargins = $section.GetElementsByTagName('pgMar', $wordNamespace)
            if ($pageMargins.Count -eq 0) {
                continue
            }

            $pageMargin = $pageMargins.Item(0)
            $leftMargin = [int]$pageMargin.GetAttribute('left', $wordNamespace)
            $rightMargin = [int]$pageMargin.GetAttribute('right', $wordNamespace)
            if ($leftMargin -lt 700 -or $rightMargin -lt 700) {
                throw "Concept document section margins are too narrow for normal printing: left=$leftMargin, right=$rightMargin twips."
            }
        }
    }
    finally {
        $archive.Dispose()
    }
}

try {
    Write-Host '[1/11] Verifying the Star Cluster repository and applied Checkpoint 14a...'

    if (-not (Test-Path '.\StarCluster.sln')) {
        throw "StarCluster.sln was not found at $repositoryRoot. Extract the package into the repository root."
    }

    foreach ($priorFile in @(
        '.\docs\checkpoints\Checkpoint_14a_Tactical_Presentation_And_Missile_Architecture_Documentation.md',
        '.\tools\checkpoints\checkpoint-14a\apply_checkpoint_14a.ps1',
        '.\src\StarCluster.Core\Combat\Tracking\SensorContactEvaluator.cs')) {
        if (-not (Test-Path $priorFile)) {
            throw "Required Checkpoint 14a file $priorFile was not found. Apply Checkpoint 14a before Checkpoint 15."
        }
    }

    $expectedV03lHash = '5caf6360b63104d61bd6212453d6e5efda61967eac5ec4b64a22916bf378da79'
    $priorRootConcept = '.\docs\Star_Cluster_Game_Concept_v0.3l.docx'
    $priorArchivedConcept = '.\docs\archive\Star_Cluster_Game_Concept_v0.3l.docx'
    if (Test-Path $priorRootConcept) {
        $priorConceptPath = $priorRootConcept
    }
    elseif (Test-Path $priorArchivedConcept) {
        # A previous Checkpoint 15 attempt may already have archived the keeper.
        # Accept that state so the applier remains safely rerunnable.
        $priorConceptPath = $priorArchivedConcept
    }
    else {
        throw "Required Checkpoint 14a Concept v0.3l was not found at $priorRootConcept or $priorArchivedConcept. Apply Checkpoint 14a before Checkpoint 15."
    }

    $priorV03lHash = (Get-FileHash $priorConceptPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($priorV03lHash -ne $expectedV03lHash) {
        throw "The prior Concept v0.3l hash at $priorConceptPath is $priorV03lHash, expected $expectedV03lHash."
    }

    Write-Host '[2/11] Confirming that Godot is closed...'
    $godotProcesses = Get-Process -ErrorAction SilentlyContinue |
        Where-Object { $_.ProcessName -like 'Godot*' }
    if ($godotProcesses) {
        $processNames = ($godotProcesses.ProcessName | Sort-Object -Unique) -join ', '
        throw "Close the Godot editor and debug window before applying Checkpoint 15. Running process(es): $processNames"
    }

    Write-Host '[3/11] Checking the pinned .NET SDK...'
    $sdkVersion = dotnet --version
    Write-Host "       SDK: $sdkVersion"
    if ($sdkVersion -ne '8.0.423') {
        throw "Expected .NET SDK 8.0.423 from global.json, but dotnet selected $sdkVersion."
    }

    Write-Host '[4/11] Verifying the engine-independent hybrid movement foundation...'
    foreach ($sourceFile in @(
        '.\src\StarCluster.Core\Movement\ShipMovementTurnState.cs',
        '.\src\StarCluster.Core\Movement\ShipMovementStepExecutionStatus.cs',
        '.\src\StarCluster.Core\Movement\ShipMovementStepExecutionResult.cs',
        '.\src\StarCluster.Core\Movement\ShipMovementTurnService.cs')) {
        if (-not (Test-Path $sourceFile)) {
            throw "Required Checkpoint 15 movement source $sourceFile was not found."
        }
    }
    Assert-FileContains '.\src\StarCluster.Core\Movement\ShipMovementTurnService.cs' @(
        'Begin(',
        'PlanDestination(',
        'FindLegalDestinations(',
        'ExecuteStep(',
        'EndMovement(',
        'map.Move(shipId, destination)') 'ShipMovementTurnService'
    Assert-FileContains '.\src\StarCluster.Core\Movement\ShipMovementTurnState.cs' @(
        'ExecutedPath',
        'DistanceSpent',
        'RemainingDistance',
        'Every committed movement step must enter an adjacent hex') 'ShipMovementTurnState'

    Write-Host '[5/11] Verifying per-entered-hex track semantics and diagnostics...'
    Assert-FileContains '.\src\StarCluster.Core\Combat\Tracking\TacticalTrackRepository.cs' @(
        'Losing visibility after a successful observation in the same epoch',
        'record.Quality = TacticalTrackQuality.Stale',
        'record.EstimatedCoordinate = record.LastObservedCoordinate') 'TacticalTrackRepository'
    Assert-FileContains '.\src\StarCluster.Core\Combat\Tracking\TrackUpdateTrigger.cs' @(
        'ShipMovementStepCommitted') 'TrackUpdateTrigger'
    Assert-FileContains '.\src\StarCluster.Core\Diagnostics\DiagnosticEventType.cs' @(
        'ShipMovementDestinationCommitted',
        'ShipMovementStepResolved') 'DiagnosticEventType'

    Write-Host '[6/11] Verifying the Godot hybrid movement interaction and observer-safe interruption...'
    Assert-FileContains '.\src\StarCluster.Game\Scripts\Main.cs' @(
        'checkpoint-15',
        'Star Cluster - Checkpoint 15',
        'Move to destination',
        'End movement',
        'ShipMovementTurnService.Begin',
        'ShipMovementTurnService.PlanDestination',
        'ShipMovementDestinationCommitted',
        'ShipMovementStepResolved',
        'ShipMovementStepCommitted',
        'Automatic route paused',
        'VisibleHostileMissileIds',
        'sameEpochVisibilityLoss',
        'the track became Stale at the most recently observed coordinate without advancing tactical age') 'Main.cs hybrid movement implementation'
    Assert-FileContains '.\src\StarCluster.Game\Scripts\DemoScenario.cs' @(
        'MovePlayerShipOneHex',
        'ShipMovementTurnService.ExecuteStep') 'DemoScenario hybrid movement bridge'
    Assert-FileContains '.\src\StarCluster.Game\Scripts\HexBoardView.cs' @(
        'bool immediateStep',
        'immediateStep ? 3.0f : 1.5f') 'HexBoardView movement emphasis'

    Write-Host '[7/11] Verifying Concept v0.3m, printable tables, and the refined missile contract...'
    foreach ($documentationFile in @(
        '.\docs\README.md',
        '.\docs\Star_Cluster_Game_Concept_v0.3m.docx',
        '.\docs\archive\Star_Cluster_Game_Concept_v0.3l.docx',
        '.\docs\Prototype_TODO.md',
        '.\docs\checkpoints\Checkpoint_15_Hybrid_Incremental_Tactical_Ship_Movement.md',
        '.\docs\design\Missile_Guidance_Datalink_Sensor_And_Seeker_Architecture.md',
        '.\docs\validation\Baseline_Tactical_Regression_Encounter.md',
        '.\src\StarCluster.Game\README.md')) {
        if (-not (Test-Path $documentationFile)) {
            throw "Required Checkpoint 15 documentation file $documentationFile was not found."
        }
    }

    $archivedV03lHash = (Get-FileHash '.\docs\archive\Star_Cluster_Game_Concept_v0.3l.docx' -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($archivedV03lHash -ne $expectedV03lHash) {
        throw "The archived Concept v0.3l hash is $archivedV03lHash, expected $expectedV03lHash."
    }
    Assert-ConceptPrintLayout '.\docs\Star_Cluster_Game_Concept_v0.3m.docx'

    Assert-FileContains '.\docs\README.md' @(
        'Star_Cluster_Game_Concept_v0.3m.docx',
        'Checkpoint_15_Hybrid_Incremental_Tactical_Ship_Movement.md') 'Documentation index'
    Assert-FileContains '.\docs\design\Missile_Guidance_Datalink_Sensor_And_Seeker_Architecture.md' @(
        'Command-guided; no onboard sensor or seeker',
        'Current Firm launcher track and live launcher-to-missile datalink',
        'Seeker-only',
        'Current Firm or Approximate launcher track',
        'Sensor-only',
        'data-defined usable Stale report',
        'most recent intermediate coordinate actually observed',
        'Target entry and departure are distinct movement-edge events') 'Missile architecture documentation'
    Assert-FileContains '.\docs\validation\Baseline_Tactical_Regression_Encounter.md' @(
        'Checkpoint 15 focused hybrid-movement check',
        'ShipMovementDestinationCommitted',
        'ShipMovementStepResolved',
        'last observed intermediate coordinate',
        'Automatic route paused') 'Checkpoint 15 validation runbook'

    Write-Host '[8/11] Verifying focused tests and expected suite growth...'
    $movementTestFile = '.\tests\StarCluster.Tests\Movement\HybridShipMovementTests.cs'
    if (-not (Test-Path $movementTestFile)) {
        throw "Checkpoint 15 movement test file $movementTestFile was not found."
    }
    $movementFactCount = (Select-String -Path $movementTestFile -Pattern '\[Fact\]' -AllMatches).Matches.Count
    if ($movementFactCount -ne 12) {
        throw "Expected 12 Checkpoint 15 hybrid movement [Fact] tests, but found $movementFactCount."
    }
    Assert-FileContains '.\tests\StarCluster.Tests\Combat\Tracking\TacticalTrackEpochTests.cs' @(
        'SameEpochVisibilityLossBecomesStaleWithoutAdvancingAge',
        'LaterSameEpochMissRetainsTheMostRecentObservedCoordinate') 'TacticalTrackEpochTests'

    Write-Host '[9/11] Refreshing generated Godot managed metadata and solution membership...'
    Remove-Item -Recurse -Force '.\src\StarCluster.Game\.godot\mono' -ErrorAction SilentlyContinue
    $solutionOutput = dotnet sln '.\StarCluster.sln' list
    if ($LASTEXITCODE -ne 0) {
        throw "dotnet sln list failed with exit code $LASTEXITCODE."
    }
    $solutionText = $solutionOutput | Out-String
    if ($solutionText -notmatch 'StarCluster.Game.csproj') {
        dotnet sln '.\StarCluster.sln' add '.\src\StarCluster.Game\StarCluster.Game.csproj'
        if ($LASTEXITCODE -ne 0) {
            throw "Could not add StarCluster.Game to the solution; exit code $LASTEXITCODE."
        }
    }

    Write-Host '[10/11] Building the complete solution with warnings treated as errors...'
    dotnet build '.\StarCluster.sln' --nologo -warnaserror
    if ($LASTEXITCODE -ne 0) {
        throw "dotnet build failed with exit code $LASTEXITCODE."
    }

    Write-Host '[11/11] Running tests and confirming the one-way architecture...'
    $testOutput = dotnet test '.\tests\StarCluster.Tests\StarCluster.Tests.csproj' --no-build --nologo
    $testOutput | Write-Host
    if ($LASTEXITCODE -ne 0) {
        throw "dotnet test failed with exit code $LASTEXITCODE."
    }
    $testText = $testOutput | Out-String
    if ($testText -notmatch 'Passed:\s+453') {
        throw 'The complete suite did not report the expected 453 passed tests.'
    }
    if (Select-String -Path '.\src\StarCluster.Core\StarCluster.Core.csproj' -Pattern 'Godot' -Quiet) {
        throw 'StarCluster.Core unexpectedly contains a Godot dependency.'
    }

    # Retire the prior root keeper only after all validation, build, tests, and
    # architecture checks have succeeded. Failed runs therefore remain rerunnable.
    Remove-Item '.\docs\Star_Cluster_Game_Concept_v0.3l.docx' -Force -ErrorAction SilentlyContinue

    Write-Host ''
    Write-Host 'Checkpoint 15 completed successfully.'
    Write-Host 'Expected engine-independent tests passed: 453.'
    Write-Host 'Reopen Godot and run the Checkpoint 15 focused hybrid-movement check in docs\validation\Baseline_Tactical_Regression_Encounter.md.'
    Write-Host 'Confirm one-step movement, a later distant destination using the remaining allowance, per-entered-hex Track Updates, the true last-observed intermediate coordinate, early End movement, and route interruption on a newly revealed hostile missile.'
    Write-Host 'Upload the matching checkpoint-15 .log and .jsonl files, numbered notes, and the requested movement screenshots.'
    Write-Host 'Next substantive checkpoint: launcher-to-missile datalink line of sight and retained copied reports.'
}
finally {
    Pop-Location
}
