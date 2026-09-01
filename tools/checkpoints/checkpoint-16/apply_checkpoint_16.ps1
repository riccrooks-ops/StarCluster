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
        throw "$Description file $Path was not found. Re-extract the complete Checkpoint 16 package."
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
                    if ($columnWidthText) {
                        $gridWidth += [int]$columnWidthText
                    }
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
    finally {
        $archive.Dispose()
    }
}

try {
    Write-Host '[1/11] Verifying the Star Cluster repository and applied Checkpoint 15...'

    if (-not (Test-Path '.\StarCluster.sln')) {
        throw "StarCluster.sln was not found at $repositoryRoot. Extract the package into the repository root."
    }

    foreach ($priorFile in @(
        '.\docs\checkpoints\Checkpoint_15_Hybrid_Incremental_Tactical_Ship_Movement.md',
        '.\tools\checkpoints\checkpoint-15\apply_checkpoint_15.ps1',
        '.\src\StarCluster.Core\Movement\ShipMovementTurnService.cs',
        '.\tests\StarCluster.Tests\Movement\HybridShipMovementTests.cs')) {
        if (-not (Test-Path $priorFile)) {
            throw "Required Checkpoint 15 file $priorFile was not found. Apply the complete Checkpoint 15 archive before Checkpoint 16."
        }
    }

    $expectedV03mHash = 'c0771de6152a55ce9bd8f518556f16113b08fd51c8984d4f8cddfe7babf3fa79'
    $priorRootConcept = '.\docs\Star_Cluster_Game_Concept_v0.3m.docx'
    $priorArchivedConcept = '.\docs\archive\Star_Cluster_Game_Concept_v0.3m.docx'
    if (Test-Path $priorRootConcept) {
        $priorConceptPath = $priorRootConcept
    }
    elseif (Test-Path $priorArchivedConcept) {
        # A previous Checkpoint 16 attempt may already have archived the keeper.
        # Accept that state so the applier remains safely rerunnable.
        $priorConceptPath = $priorArchivedConcept
    }
    else {
        throw "Required Checkpoint 15 Concept v0.3m was not found at $priorRootConcept or $priorArchivedConcept. Apply Checkpoint 15 before Checkpoint 16."
    }

    $priorV03mHash = (Get-FileHash $priorConceptPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($priorV03mHash -ne $expectedV03mHash) {
        throw "The prior Concept v0.3m hash at $priorConceptPath is $priorV03mHash, expected $expectedV03mHash."
    }

    Write-Host '[2/11] Confirming that Godot is closed...'
    $godotProcesses = Get-Process -ErrorAction SilentlyContinue |
        Where-Object { $_.ProcessName -like 'Godot*' }
    if ($godotProcesses) {
        $processNames = ($godotProcesses.ProcessName | Sort-Object -Unique) -join ', '
        throw "Close the Godot editor and debug window before applying Checkpoint 16. Running process(es): $processNames"
    }

    Write-Host '[3/11] Checking the pinned .NET SDK...'
    $sdkVersion = dotnet --version
    Write-Host "       SDK: $sdkVersion"
    if ($sdkVersion -ne '8.0.423') {
        throw "Expected .NET SDK 8.0.423 from global.json, but dotnet selected $sdkVersion."
    }

    Write-Host '[4/11] Verifying the engine-independent datalink foundation...'
    foreach ($sourceFile in @(
        '.\src\StarCluster.Core\Combat\Missiles\MissileDatalinkState.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileGuidanceReportSource.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileDatalinkProfile.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileDatalinkReport.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileDatalinkLinkEvaluation.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileDatalinkUpdateResult.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileDatalinkService.cs')) {
        if (-not (Test-Path $sourceFile)) {
            throw "Required Checkpoint 16 datalink source $sourceFile was not found."
        }
    }
    Assert-FileContains '.\src\StarCluster.Core\Combat\Missiles\MissileDatalinkService.cs' @(
        'DirectFireLineOfSight.Evaluate',
        'MissileDatalinkState.Unavailable',
        'MissileDatalinkState.Blocked',
        'UpdateForGuidancePhase(',
        'RefreshLinkState(') 'MissileDatalinkService'
    Assert-FileContains '.\src\StarCluster.Core\Combat\Missiles\GuidedMissileSalvo.cs' @(
        'DatalinkState',
        'RetainedDatalinkReport',
        'LastDatalinkEvaluationGuidancePhase',
        'ApplyDatalinkEvaluation(') 'GuidedMissileSalvo datalink state'
    Assert-FileContains '.\src\StarCluster.Core\Combat\Missiles\MissileLaunchService.cs' @(
        'MissileDatalinkProfile datalinkProfile',
        'MissileDatalinkService.UpdateForGuidancePhase',
        'datalinkUpdateResult.GuidanceSnapshot') 'MissileLaunchService datalink integration'

    Write-Host '[5/11] Verifying copied-report retention, provenance, and observer boundaries...'
    Assert-FileContains '.\src\StarCluster.Core\Combat\Missiles\MissileDatalinkReport.cs' @(
        'ReceivedQuality',
        'GuidanceCoordinate',
        'SourceObservationEpoch',
        'ReceivedGuidancePhase',
        'AgePhases',
        'AgeOnePhase()',
        'MissileTargetTrackQuality.Stale',
        'MissileTargetTrackQuality.Lost') 'MissileDatalinkReport'
    Assert-FileContains '.\src\StarCluster.Core\Combat\Missiles\MissileDatalinkService.cs' @(
        'duplicateSamePhase',
        'salvo.LastDatalinkEvaluationGuidancePhase == guidancePhaseNumber',
        'retainedReport = retainedReport.AgeOnePhase()',
        'MissileGuidanceReportSource.FreshDatalink',
        'MissileGuidanceReportSource.RetainedDatalink') 'Datalink once-per-phase semantics'
    Assert-FileContains '.\src\StarCluster.Core\Combat\Tracking\ObserverSafeMissileViewService.cs' @(
        'if (contact.OwnerSide == observerSide)',
        'salvo.LastTrackQuality',
        'salvo.CurrentTrackedTargetCoordinate',
        'salvo.LastKnownTargetCoordinate',
        'WithheldByObserverUncertainty') 'Observer-safe missile projection'
    Assert-FileContains '.\src\StarCluster.Core\Diagnostics\DiagnosticEventType.cs' @(
        'MissileDatalinkUpdated') 'DiagnosticEventType'

    Write-Host '[6/11] Verifying Godot action-start/action-end integration and batch diagnostics...'
    Assert-FileContains '.\src\StarCluster.Game\Scripts\Main.cs' @(
        'private const string CheckpointVersion = "checkpoint-16";',
        'Star Cluster - Checkpoint 16',
        '_missileDatalinkProfile',
        'MissileDatalinkService.UpdateForGuidancePhase',
        'RecordMissileDatalinkUpdate(',
        'RefreshAndLogDatalinkStateAfterMovement(',
        '("evaluationStage", "ActionStart")',
        '("evaluationStage", "ActionEnd")',
        '("reportDelivered", "False")',
        '("retainedReportAged", "False")',
        'launchesResolved',
        'existingSalvosAdvanced',
        'totalMissileActionsResolved') 'Main.cs datalink implementation'
    Assert-FileContains '.\src\StarCluster.Game\Scripts\Main.cs' @(
        'Enemy datalink state is not added to normal player-visible contact summaries') 'Main.cs observer-safe datalink comment'

    Write-Host '[7/11] Verifying Concept v0.3n, printable tables, and synchronized documentation...'
    foreach ($documentationFile in @(
        '.\docs\README.md',
        '.\docs\Star_Cluster_Game_Concept_v0.3n.docx',
        '.\docs\archive\Star_Cluster_Game_Concept_v0.3m.docx',
        '.\docs\Prototype_TODO.md',
        '.\docs\checkpoints\Checkpoint_16_Launcher_To_Missile_Datalink_And_Retained_Reports.md',
        '.\docs\design\Missile_Guidance_Datalink_Sensor_And_Seeker_Architecture.md',
        '.\docs\validation\Baseline_Tactical_Regression_Encounter.md',
        '.\src\StarCluster.Game\README.md')) {
        if (-not (Test-Path $documentationFile)) {
            throw "Required Checkpoint 16 documentation file $documentationFile was not found."
        }
    }

    $archivedV03mHash = (Get-FileHash '.\docs\archive\Star_Cluster_Game_Concept_v0.3m.docx' -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($archivedV03mHash -ne $expectedV03mHash) {
        throw "The archived Concept v0.3m hash is $archivedV03mHash, expected $expectedV03mHash."
    }
    $expectedV03nHash = 'd3c7839a8463a0e2133e48cb08cf47842355c4d9750e00f48613f7779074c3ab'
    $currentV03nHash = (Get-FileHash '.\docs\Star_Cluster_Game_Concept_v0.3n.docx' -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($currentV03nHash -ne $expectedV03nHash) {
        throw "Concept v0.3n hash is $currentV03nHash, expected $expectedV03nHash. Re-extract the complete Checkpoint 16 package."
    }
    Assert-ConceptPrintLayout '.\docs\Star_Cluster_Game_Concept_v0.3n.docx'

    Assert-FileContains '.\docs\README.md' @(
        'Star_Cluster_Game_Concept_v0.3n.docx',
        'Checkpoint_16_Launcher_To_Missile_Datalink_And_Retained_Reports.md') 'Documentation index'
    Assert-FileContains '.\docs\checkpoints\Checkpoint_16_Launcher_To_Missile_Datalink_And_Retained_Reports.md' @(
        'Independent line-of-sight relationships',
        'Copied missile-owned reports',
        'Bounded retention and expiration',
        'Action-start delivery and action-end state',
        'Expected complete engine-independent suite after application: **470 tests**') 'Checkpoint 16 documentation'
    Assert-FileContains '.\docs\design\Missile_Guidance_Datalink_Sensor_And_Seeker_Architecture.md' @(
        'Checkpoint 16 implements launcher-to-missile datalink line of sight',
        'Checkpoint 16 performs delivery at the start of one missile action',
        'refreshes link state after movement',
        'Retained age advances at most once per missile guidance phase',
        'Friendly route projections use the missile''s own last guidance report') 'Missile architecture documentation'
    Assert-FileContains '.\docs\validation\Baseline_Tactical_Regression_Encounter.md' @(
        'Checkpoint 16 focused datalink check',
        'evaluationStage=ActionEnd',
        'retainedReportAged=True',
        'launchesResolved',
        'totalMissileActionsResolved') 'Checkpoint 16 validation runbook'

    Write-Host '[8/11] Verifying focused tests and expected suite growth...'
    $datalinkTestFile = '.\tests\StarCluster.Tests\Combat\Missiles\MissileDatalinkServiceTests.cs'
    if (-not (Test-Path $datalinkTestFile)) {
        throw "Checkpoint 16 datalink test file $datalinkTestFile was not found."
    }
    $datalinkFactCount = (Select-String -Path $datalinkTestFile -Pattern '\[Fact\]' -AllMatches).Matches.Count
    if ($datalinkFactCount -ne 16) {
        throw "Expected 16 Checkpoint 16 datalink [Fact] tests, but found $datalinkFactCount."
    }
    Assert-FileContains $datalinkTestFile @(
        'CentralStarBlocksTheDatalink',
        'BlockedLinkRetainsAndAgesTheLastCopyToStale',
        'RetainedCopyDoesNotFollowANewerBlockedLauncherSnapshot',
        'RepeatedEvaluationInOneGuidancePhaseDoesNotAgeTwice',
        'RestoredLinkReplacesTheRetainedCopyAndResetsAge',
        'RetainedReportExpiresAfterTheConfiguredAgeLimit',
        'ActionEndLinkRefreshDoesNotAgeTheRetainedReport',
        'LaunchServiceExposesTheCopiedDatalinkUpdate') 'MissileDatalinkServiceTests'

    Assert-FileContains '.\tests\StarCluster.Tests\Combat\Tracking\ObserverSafeMissileViewTests.cs' @(
        'FriendlyProjectionUsesTheMissilesConsumedDatalinkReport',
        'copiedGuidanceCoordinate',
        'newerObserverCoordinate') 'ObserverSafeMissileViewTests'

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
    if ($testText -notmatch 'Passed:\s+470') {
        throw 'The complete suite did not report the expected 470 passed tests.'
    }
    if (Select-String -Path '.\src\StarCluster.Core\StarCluster.Core.csproj' -Pattern 'Godot' -Quiet) {
        throw 'StarCluster.Core unexpectedly contains a Godot dependency.'
    }

    # Retire the prior root keeper only after all validation, build, tests, and
    # architecture checks have succeeded. Failed runs therefore remain rerunnable.
    Remove-Item '.\docs\Star_Cluster_Game_Concept_v0.3m.docx' -Force -ErrorAction SilentlyContinue

    Write-Host ''
    Write-Host 'Checkpoint 16 completed successfully.'
    Write-Host 'Expected engine-independent tests passed: 470.'
    Write-Host 'Reopen Godot and run the Checkpoint 16 focused datalink check in docs\validation\Baseline_Tactical_Regression_Encounter.md.'
    Write-Host 'Confirm action-start delivery, action-end state-only refresh, blocked-link retention, one age step per guidance phase, copied-coordinate independence, restored-link replacement, friendly report-based projection, and clarified batch counts.'
    Write-Host 'Upload the matching checkpoint-16 .log and .jsonl files, numbered notes, and the requested datalink screenshots.'
    Write-Host 'Next substantive checkpoint: missile-local onboard sensor tracks, deterministic launcher/local arbitration, and per-movement-edge reacquisition.'
}
finally {
    Pop-Location
}
