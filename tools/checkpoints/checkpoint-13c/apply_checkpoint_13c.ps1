[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$repositoryRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
Push-Location $repositoryRoot

try {
    Write-Host '[1/10] Verifying the Star Cluster repository and Checkpoint 13b...'

    if (-not (Test-Path '.\StarCluster.sln')) {
        throw "StarCluster.sln was not found at $repositoryRoot. Extract the package into the repository root."
    }

    $priorFiles = @(
        '.\src\StarCluster.Core\Combat\Tracking\TacticalMissileStackService.cs',
        '.\src\StarCluster.Core\Combat\Tracking\TacticalTrackRecord.cs',
        '.\src\StarCluster.Game\Scripts\AutomaticDiagnosticLog.cs',
        '.\docs\checkpoints\Checkpoint_13b_Track_Aging_Epochs_And_Tactical_Observability.md'
    )
    foreach ($priorFile in $priorFiles) {
        if (-not (Test-Path $priorFile)) {
            throw "Required prior-checkpoint file $priorFile was not found. Apply Checkpoint 13b first."
        }
    }

    Write-Host '[2/10] Confirming that Godot is closed...'
    $godotProcesses = Get-Process -ErrorAction SilentlyContinue |
        Where-Object { $_.ProcessName -like 'Godot*' }
    if ($godotProcesses) {
        $processNames = ($godotProcesses.ProcessName | Sort-Object -Unique) -join ', '
        throw "Close the Godot editor and debug window before applying Checkpoint 13c. Running process(es): $processNames"
    }

    Write-Host '[3/10] Checking the pinned .NET SDK...'
    $sdkVersion = dotnet --version
    Write-Host "       SDK: $sdkVersion"
    if ($sdkVersion -ne '8.0.423') {
        throw "Expected .NET SDK 8.0.423 from global.json, but dotnet selected $sdkVersion."
    }

    Write-Host '[4/10] Verifying observer-safe view, route disclosure, trail segmentation, and batch refresh sources...'
    $requiredSourceFiles = @(
        '.\src\StarCluster.Core\Combat\Tracking\ObservedTrackSample.cs',
        '.\src\StarCluster.Core\Combat\Tracking\ObservedTravelTrailService.cs',
        '.\src\StarCluster.Core\Combat\Tracking\ObserverSafeMissileViewSnapshot.cs',
        '.\src\StarCluster.Core\Combat\Tracking\ObserverSafeMissileViewService.cs',
        '.\src\StarCluster.Core\Combat\Tracking\TacticalMissileContact.cs',
        '.\src\StarCluster.Core\Combat\Tracking\TacticalMissileKnowledgeService.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileRouteProjectionStatus.cs',
        '.\src\StarCluster.Game\Scripts\TacticalResolutionCue.cs'
    )
    foreach ($sourceFile in $requiredSourceFiles) {
        if (-not (Test-Path $sourceFile)) {
            throw "Checkpoint 13c source $sourceFile was not found. Re-extract the package."
        }
    }

    $viewService = '.\src\StarCluster.Core\Combat\Tracking\ObserverSafeMissileViewService.cs'
    $trailService = '.\src\StarCluster.Core\Combat\Tracking\ObservedTravelTrailService.cs'
    $projectionStatus = '.\src\StarCluster.Core\Combat\Missiles\MissileRouteProjectionStatus.cs'
    $eventTypeFile = '.\src\StarCluster.Core\Diagnostics\DiagnosticEventType.cs'

    foreach ($pattern in @(
        'TacticalMissileKnowledgeService.Build',
        'WithheldByObserverUncertainty',
        'requestedSelectedSalvoId',
        'contact.TrackQuality != TacticalTrackQuality.Firm')) {
        if (-not (Select-String -Path $viewService -Pattern ([regex]::Escape($pattern)) -Quiet)) {
            throw "ObserverSafeMissileViewService is missing required behavior: $pattern"
        }
    }
    if (-not (Select-String -Path $trailService -Pattern 'ObservationEpoch' -Quiet) -or
        -not (Select-String -Path $trailService -Pattern 'segments.Add' -Quiet)) {
        throw 'ObservedTravelTrailService does not split observer-safe trail segments by observation epoch.'
    }
    if (-not (Select-String -Path $projectionStatus -Pattern 'WithheldByObserverUncertainty' -Quiet)) {
        throw 'The observer-safe projection-withheld status is missing.'
    }
    foreach ($pattern in @('MissileBatchResolved','TacticalViewRefreshed')) {
        if (-not (Select-String -Path $eventTypeFile -Pattern $pattern -Quiet)) {
            throw "The diagnostic event category $pattern is missing."
        }
    }

    Write-Host '[5/10] Verifying the 14 new observer-safety and trail tests...'
    $newTestFiles = @(
        '.\tests\StarCluster.Tests\Combat\Tracking\ObservedTravelTrailSegmentTests.cs',
        '.\tests\StarCluster.Tests\Combat\Tracking\ObserverSafeMissileViewTests.cs'
    )
    $newFactCount = 0
    foreach ($testFile in $newTestFiles) {
        if (-not (Test-Path $testFile)) {
            throw "Checkpoint 13c test file $testFile was not found."
        }
        $newFactCount += (Select-String -Path $testFile -Pattern '\[Fact\]' -AllMatches).Matches.Count
    }
    if ($newFactCount -ne 14) {
        throw "Expected 14 new [Fact] tests, but found $newFactCount."
    }

    $requiredTests = @(
        'UnknownHostileMissileCannotRenderOrRemainSelected',
        'StaleHostileContactIsVisibleButExactRouteIsWithheld',
        'HiddenHostileMissileCannotAffectVisibleStackCount',
        'ViewConstructionDoesNotMutateAuthoritativeSalvoState',
        'MissedEpochCreatesDisconnectedSegments',
        'ReacquisitionAfterGapNeverBridgesHiddenMovement'
    )
    foreach ($test in $requiredTests) {
        if (-not (Select-String -Path $newTestFiles -Pattern $test -Quiet)) {
            throw "Required Checkpoint 13c regression test $test is missing."
        }
    }

    Write-Host '[6/10] Verifying Godot observer filtering, impact cues, and post-batch refresh...'
    $mainFile = '.\src\StarCluster.Game\Scripts\Main.cs'
    $boardFile = '.\src\StarCluster.Game\Scripts\HexBoardView.cs'
    $trackFile = '.\src\StarCluster.Game\Scripts\DemoTrackState.cs'
    foreach ($gameFile in @($mainFile,$boardFile,$trackFile)) {
        if (-not (Test-Path $gameFile)) {
            throw "Required Checkpoint 13c Godot source $gameFile was not found."
        }
    }

    foreach ($pattern in @(
        'Star Cluster - Checkpoint 13c',
        'checkpoint-13c',
        'BuildPlayerMissileView',
        'Enemy launches never force-select',
        'BuildObserverSafeBatchSummary',
        'BuildResolutionCues',
        'MissileBatchResolved',
        'TacticalViewRefreshed',
        'No unresolved salvos remain')) {
        if (-not (Select-String -Path $mainFile -Pattern ([regex]::Escape($pattern)) -Quiet)) {
            throw "Main.cs is missing required Checkpoint 13c behavior: $pattern"
        }
    }
    foreach ($pattern in @(
        'VisibleTravelSegments',
        'DrawResolutionCues',
        'SetResolutionCues')) {
        if (-not (Select-String -Path $boardFile -Pattern ([regex]::Escape($pattern)) -Quiet)) {
            throw "HexBoardView.cs is missing required observer-safe presentation: $pattern"
        }
    }
    if (-not (Select-String -Path $trackFile -Pattern 'ObserverSafeMissileViewService.Build' -Quiet)) {
        throw 'DemoTrackState does not construct the player missile view through the engine-independent observer-safe service.'
    }

    Write-Host '[7/10] Verifying Concept v0.3h and synchronized validation documentation...'
    $documentationFiles = @(
        '.\docs\README.md',
        '.\docs\Star_Cluster_Game_Concept_v0.3h.docx',
        '.\docs\archive\Star_Cluster_Game_Concept_v0.3g.docx',
        '.\docs\Prototype_TODO.md',
        '.\docs\checkpoints\Checkpoint_13c_Observer_Safe_Tactical_View_And_Resolution_Feedback.md',
        '.\docs\validation\Baseline_Tactical_Regression_Encounter.md',
        '.\src\StarCluster.Game\README.md'
    )
    foreach ($documentationFile in $documentationFiles) {
        if (-not (Test-Path $documentationFile)) {
            throw "Required documentation file $documentationFile was not found."
        }
    }
    if (-not (Select-String -Path '.\docs\README.md' -Pattern 'Star_Cluster_Game_Concept_v0.3h.docx' -Quiet) -or
        -not (Select-String -Path '.\docs\README.md' -Pattern 'Checkpoint_13c_Observer_Safe_Tactical_View_And_Resolution_Feedback.md' -Quiet) -or
        -not (Select-String -Path '.\docs\README.md' -Pattern 'Baseline_Tactical_Regression_Encounter.md' -Quiet)) {
        throw 'The documentation index is not synchronized with Checkpoint 13c.'
    }
    if (-not (Select-String -Path '.\docs\Prototype_TODO.md' -Pattern 'observer-safe missile-view snapshot' -Quiet)) {
        throw 'The living TODO does not record the Checkpoint 13c observer-safety resolution.'
    }

    Remove-Item '.\docs\Star_Cluster_Game_Concept_v0.3g.docx' -Force -ErrorAction SilentlyContinue

    Write-Host '[8/10] Refreshing generated Godot managed metadata and solution membership...'
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

    Write-Host '[9/10] Building the complete solution with warnings treated as errors...'
    dotnet build '.\StarCluster.sln' --nologo -warnaserror
    if ($LASTEXITCODE -ne 0) {
        throw "dotnet build failed with exit code $LASTEXITCODE."
    }

    Write-Host '[10/10] Running tests and confirming the one-way architecture...'
    dotnet test '.\tests\StarCluster.Tests\StarCluster.Tests.csproj' --no-build --nologo
    if ($LASTEXITCODE -ne 0) {
        throw "dotnet test failed with exit code $LASTEXITCODE."
    }
    if (Select-String -Path '.\src\StarCluster.Core\StarCluster.Core.csproj' -Pattern 'Godot' -Quiet) {
        throw 'StarCluster.Core unexpectedly contains a Godot dependency.'
    }

    Write-Host ''
    Write-Host 'Checkpoint 13c completed successfully.' -ForegroundColor Green
    Write-Host 'Expected engine-independent tests passed: 399.'
    Write-Host 'Reopen Godot and run docs\validation\Baseline_Tactical_Regression_Encounter.md without changing the scripted actions unless necessary.'
    Write-Host 'Confirm Unknown missiles never render or remain selected, imperfect hostile tracks withhold exact routes, reacquired trails remain disconnected, and every missile batch produces clear impact/remaining-salvo feedback.'
    Write-Host 'Upload the matching checkpoint-13c .log and .jsonl files plus the three requested screenshots.'
    Write-Host 'Next candidate checkpoint: sensor signatures and electronic-warfare foundations, after reviewing the repeatable Checkpoint 13c run.'
}
finally {
    Pop-Location
}
