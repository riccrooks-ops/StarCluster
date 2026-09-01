[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$repositoryRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
Push-Location $repositoryRoot

try {
    Write-Host '[1/10] Verifying the Star Cluster repository and Checkpoint 13c...'

    if (-not (Test-Path '.\StarCluster.sln')) {
        throw "StarCluster.sln was not found at $repositoryRoot. Extract the package into the repository root."
    }

    $priorFiles = @(
        '.\src\StarCluster.Core\Combat\Tracking\ObserverSafeMissileViewService.cs',
        '.\src\StarCluster.Core\Combat\Tracking\ObservedTravelTrailService.cs',
        '.\docs\checkpoints\Checkpoint_13c_Observer_Safe_Tactical_View_And_Resolution_Feedback.md',
        '.\docs\validation\Baseline_Tactical_Regression_Encounter.md'
    )
    foreach ($priorFile in $priorFiles) {
        if (-not (Test-Path $priorFile)) {
            throw "Required prior-checkpoint file $priorFile was not found. Apply Checkpoint 13c first."
        }
    }

    Write-Host '[2/10] Confirming that Godot is closed...'
    $godotProcesses = Get-Process -ErrorAction SilentlyContinue |
        Where-Object { $_.ProcessName -like 'Godot*' }
    if ($godotProcesses) {
        $processNames = ($godotProcesses.ProcessName | Sort-Object -Unique) -join ', '
        throw "Close the Godot editor and debug window before applying Checkpoint 13d. Running process(es): $processNames"
    }

    Write-Host '[3/10] Checking the pinned .NET SDK...'
    $sdkVersion = dotnet --version
    Write-Host "       SDK: $sdkVersion"
    if ($sdkVersion -ne '8.0.423') {
        throw "Expected .NET SDK 8.0.423 from global.json, but dotnet selected $sdkVersion."
    }

    Write-Host '[4/10] Verifying observed-launch trails, per-hex detection, terminal filtering, and shared finalization...'
    $requiredSourceFiles = @(
        '.\src\StarCluster.Core\Combat\Tracking\MissileMovementObservationStep.cs',
        '.\src\StarCluster.Core\Combat\Tracking\MissileMovementObservationResult.cs',
        '.\src\StarCluster.Core\Combat\Tracking\MissileMovementObservationService.cs',
        '.\src\StarCluster.Core\Combat\Tracking\ObservedTrackSample.cs',
        '.\src\StarCluster.Core\Combat\Tracking\ObservedTravelTrailService.cs',
        '.\src\StarCluster.Core\Combat\Tracking\TacticalTrackRecord.cs',
        '.\src\StarCluster.Core\Combat\Tracking\TacticalMissileKnowledgeService.cs'
    )
    foreach ($sourceFile in $requiredSourceFiles) {
        if (-not (Test-Path $sourceFile)) {
            throw "Checkpoint 13d source $sourceFile was not found. Re-extract the package."
        }
    }

    $observationService = '.\src\StarCluster.Core\Combat\Tracking\MissileMovementObservationService.cs'
    $trackRecord = '.\src\StarCluster.Core\Combat\Tracking\TacticalTrackRecord.cs'
    $knowledgeService = '.\src\StarCluster.Core\Combat\Tracking\TacticalMissileKnowledgeService.cs'
    $sensorEvaluator = '.\src\StarCluster.Core\Combat\Tracking\SensorContactEvaluator.cs'
    foreach ($pattern in @(
        'launchObservedAtOrigin',
        'enteredCoordinates',
        'SensorContactEvaluator.Observe',
        'SegmentStarted',
        'segmentClosed')) {
        if (-not (Select-String -Path $observationService -Pattern ([regex]::Escape($pattern)) -Quiet)) {
            throw "MissileMovementObservationService is missing required behavior: $pattern"
        }
    }
    foreach ($pattern in @('SegmentId','CloseObservedSegment','HasOpenObservedSegment')) {
        if (-not (Select-String -Path $trackRecord -Pattern $pattern -Quiet)) {
            throw "TacticalTrackRecord is missing observed-segment behavior: $pattern"
        }
    }
    if (-not (Select-String -Path $knowledgeService -Pattern 'salvo.IsTerminal' -Quiet)) {
        throw 'Terminal salvos are not filtered from active tactical-map contacts.'
    }
    if (-not (Select-String -Path $sensorEvaluator -Pattern 'distance == 0' -Quiet)) {
        throw 'Same-coordinate sensor acquisition protection is missing.'
    }

    Write-Host '[5/10] Verifying the 12 new observed-trail and terminal-view tests...'
    $newTestFiles = @(
        '.\tests\StarCluster.Tests\Combat\Tracking\MissileMovementObservationTests.cs',
        '.\tests\StarCluster.Tests\Combat\Tracking\MissileTerminalViewTests.cs'
    )
    $newFactCount = 0
    foreach ($testFile in $newTestFiles) {
        if (-not (Test-Path $testFile)) {
            throw "Checkpoint 13d test file $testFile was not found."
        }
        $newFactCount += (Select-String -Path $testFile -Pattern '\[Fact\]' -AllMatches).Matches.Count
    }
    if ($newFactCount -ne 12) {
        throw "Expected 12 new [Fact] tests, but found $newFactCount."
    }

    $requiredTests = @(
        'FirmTrackedLauncherStartsTrailAtLaunchOrigin',
        'UndetectedLauncherStartsTrailAtFirstDetectedEnteredHex',
        'ReacquisitionSameEpochStartsDisconnectedSegment',
        'SameHexContactIsFirmWithoutZeroLengthLineOfSightRay',
        'MixedTerminalAndActiveSalvosKeepOnlyActiveContact',
        'SelectionOfTerminalSalvoNormalizesToNoneWhileActivePeerRemains'
    )
    foreach ($test in $requiredTests) {
        if (-not (Select-String -Path $newTestFiles -Pattern $test -Quiet)) {
            throw "Required Checkpoint 13d regression test $test is missing."
        }
    }

    Write-Host '[6/10] Verifying Godot trail observation, salvo-following selection, and mandatory batch finalization...'
    $mainFile = '.\src\StarCluster.Game\Scripts\Main.cs'
    $boardFile = '.\src\StarCluster.Game\Scripts\HexBoardView.cs'
    $trackFile = '.\src\StarCluster.Game\Scripts\DemoTrackState.cs'
    foreach ($gameFile in @($mainFile,$boardFile,$trackFile)) {
        if (-not (Test-Path $gameFile)) {
            throw "Required Checkpoint 13d Godot source $gameFile was not found."
        }
    }
    foreach ($pattern in @(
        'Star Cluster - Checkpoint 13d',
        'checkpoint-13d',
        'ObserveAndLogPlayerMissileAction',
        'launchObservedAtOrigin',
        'FinalizeMissileBatch',
        'MissileBatchFinalizationFailed',
        'SetInspectedCoordinate',
        'No unresolved salvos remain')) {
        if (-not (Select-String -Path $mainFile -Pattern ([regex]::Escape($pattern)) -Quiet)) {
            throw "Main.cs is missing required Checkpoint 13d behavior: $pattern"
        }
    }
    if (-not (Select-String -Path $boardFile -Pattern 'SetInspectedCoordinate' -Quiet)) {
        throw 'HexBoardView does not support salvo-following inspected-coordinate normalization.'
    }
    if (-not (Select-String -Path $trackFile -Pattern 'ObservePlayerMissileMovement' -Quiet)) {
        throw 'DemoTrackState does not apply per-hex player missile observations.'
    }

    Write-Host '[7/10] Verifying Concept v0.3i and synchronized validation documentation...'
    $documentationFiles = @(
        '.\docs\README.md',
        '.\docs\Star_Cluster_Game_Concept_v0.3i.docx',
        '.\docs\archive\Star_Cluster_Game_Concept_v0.3h.docx',
        '.\docs\Prototype_TODO.md',
        '.\docs\checkpoints\Checkpoint_13d_Observed_Launch_Trails_And_Batch_Finalization.md',
        '.\docs\validation\Baseline_Tactical_Regression_Encounter.md',
        '.\src\StarCluster.Game\README.md'
    )
    foreach ($documentationFile in $documentationFiles) {
        if (-not (Test-Path $documentationFile)) {
            throw "Required documentation file $documentationFile was not found."
        }
    }
    if (-not (Select-String -Path '.\docs\README.md' -Pattern 'Star_Cluster_Game_Concept_v0.3i.docx' -Quiet) -or
        -not (Select-String -Path '.\docs\README.md' -Pattern 'Checkpoint_13d_Observed_Launch_Trails_And_Batch_Finalization.md' -Quiet)) {
        throw 'The documentation index is not synchronized with Checkpoint 13d.'
    }
    foreach ($pattern in @(
        'first detected entered hex',
        'IMPACT x2',
        'MissileBatchFinalizationFailed')) {
        if (-not (Select-String -Path '.\docs\validation\Baseline_Tactical_Regression_Encounter.md' -Pattern ([regex]::Escape($pattern)) -Quiet)) {
            throw "The baseline regression runbook is missing: $pattern"
        }
    }

    Remove-Item '.\docs\Star_Cluster_Game_Concept_v0.3h.docx' -Force -ErrorAction SilentlyContinue

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
    $testOutput = dotnet test '.\tests\StarCluster.Tests\StarCluster.Tests.csproj' --no-build --nologo
    $testOutput | Write-Host
    if ($LASTEXITCODE -ne 0) {
        throw "dotnet test failed with exit code $LASTEXITCODE."
    }
    $testText = $testOutput | Out-String
    if ($testText -notmatch 'Passed:\s+411') {
        throw 'The complete suite did not report the expected 411 passed tests.'
    }
    if (Select-String -Path '.\src\StarCluster.Core\StarCluster.Core.csproj' -Pattern 'Godot' -Quiet) {
        throw 'StarCluster.Core unexpectedly contains a Godot dependency.'
    }

    Write-Host ''
    Write-Host 'Checkpoint 13d completed successfully.'
    Write-Host 'Expected engine-independent tests passed: 411.'
    Write-Host 'Reopen Godot and repeat docs\validation\Baseline_Tactical_Regression_Encounter.md exactly.'
    Write-Host 'Confirm observed launch/first-detection trails, salvo-following selection, IMPACT x2 mixed-batch feedback, and one finalization journal pair.'
    Write-Host 'Upload the matching checkpoint-13d .log and .jsonl files, updated numbered notes, and the three requested screenshots.'
    Write-Host 'Next candidate checkpoint: sensor signatures and electronic-warfare foundations, after reviewing the repeated Checkpoint 13d run.'
}
finally {
    Pop-Location
}
