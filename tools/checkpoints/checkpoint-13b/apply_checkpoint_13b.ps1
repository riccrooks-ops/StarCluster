[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$repositoryRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
Push-Location $repositoryRoot

try {
    Write-Host '[1/10] Verifying the Star Cluster repository and Checkpoint 13a...'

    if (-not (Test-Path '.\StarCluster.sln')) {
        throw "StarCluster.sln was not found at $repositoryRoot. Extract the package into the repository root."
    }

    $priorFiles = @(
        '.\src\StarCluster.Core\Diagnostics\DiagnosticEventJournal.cs',
        '.\src\StarCluster.Core\Combat\Tracking\TacticalTrackRecord.cs',
        '.\src\StarCluster.Game\Scripts\AutomaticDiagnosticLog.cs',
        '.\docs\checkpoints\Checkpoint_13a_Automatic_Event_Journal_And_Track_Diagnostics.md'
    )

    foreach ($priorFile in $priorFiles) {
        if (-not (Test-Path $priorFile)) {
            throw "Required prior-checkpoint file $priorFile was not found. Apply Checkpoint 13a first."
        }
    }

    Write-Host '[2/10] Confirming that Godot is closed...'
    $godotProcesses = Get-Process -ErrorAction SilentlyContinue |
        Where-Object { $_.ProcessName -like 'Godot*' }

    if ($godotProcesses) {
        $processNames = ($godotProcesses.ProcessName | Sort-Object -Unique) -join ', '
        throw "Close the Godot editor and debug window before applying Checkpoint 13b. Running process(es): $processNames"
    }

    Write-Host '[3/10] Checking the pinned .NET SDK...'
    $sdkVersion = dotnet --version
    Write-Host "       SDK: $sdkVersion"

    if ($sdkVersion -ne '8.0.423') {
        throw "Expected .NET SDK 8.0.423 from global.json, but dotnet selected $sdkVersion."
    }

    Write-Host '[4/10] Verifying track-aging epochs, missile stacks, and causal diagnostics...'
    $requiredSourceFiles = @(
        '.\src\StarCluster.Core\Combat\Tracking\TacticalTrackRecord.cs',
        '.\src\StarCluster.Core\Combat\Tracking\TacticalTrackUpdateResult.cs',
        '.\src\StarCluster.Core\Combat\Tracking\TacticalTrackRepository.cs',
        '.\src\StarCluster.Core\Combat\Tracking\TacticalTrackUpdateService.cs',
        '.\src\StarCluster.Core\Combat\Tracking\TacticalMissileContactStack.cs',
        '.\src\StarCluster.Core\Combat\Tracking\TacticalMissileStackService.cs',
        '.\src\StarCluster.Core\Diagnostics\DiagnosticEventType.cs'
    )

    foreach ($sourceFile in $requiredSourceFiles) {
        if (-not (Test-Path $sourceFile)) {
            throw "Checkpoint 13b source $sourceFile was not found. Re-extract the package."
        }
    }

    $trackRecordFile = '.\src\StarCluster.Core\Combat\Tracking\TacticalTrackRecord.cs'
    $trackServiceFile = '.\src\StarCluster.Core\Combat\Tracking\TacticalTrackUpdateService.cs'
    $repositoryFile = '.\src\StarCluster.Core\Combat\Tracking\TacticalTrackRepository.cs'
    $stackServiceFile = '.\src\StarCluster.Core\Combat\Tracking\TacticalMissileStackService.cs'
    $eventTypeFile = '.\src\StarCluster.Core\Diagnostics\DiagnosticEventType.cs'

    $trackPatterns = @(
        'LastObservedEpoch',
        'LastAgedEpoch',
        'ObservationEpoch',
        'AgeAdvanced'
    )
    foreach ($pattern in $trackPatterns) {
        $matched = (Select-String -Path $trackRecordFile,$trackServiceFile,'.\src\StarCluster.Core\Combat\Tracking\TacticalTrackUpdateResult.cs' -Pattern $pattern -Quiet)
        if (-not $matched) {
            throw "Track-aging epoch behavior is missing required symbol: $pattern"
        }
    }

    if (-not (Select-String -Path $repositoryFile -Pattern 'record.LastObservedEpoch == observationEpoch' -Quiet) -or
        -not (Select-String -Path $repositoryFile -Pattern 'record.LastAgedEpoch == observationEpoch' -Quiet)) {
        throw 'The repository does not enforce one missed-age step per observation epoch.'
    }

    if (-not (Select-String -Path $stackServiceFile -Pattern 'GroupBy' -Quiet) -or
        -not (Select-String -Path $stackServiceFile -Pattern 'OwnerSide' -Quiet)) {
        throw 'Missile stack grouping is not separated by coordinate and ownership.'
    }

    $eventPatterns = @(
        'MissileGuidanceStarted',
        'MissileMoved',
        'InterceptionTargetAcquired',
        'MissileGuidanceCompleted',
        'MissileStackChanged',
        'TacticalFeedback'
    )
    foreach ($pattern in $eventPatterns) {
        if (-not (Select-String -Path $eventTypeFile -Pattern $pattern -Quiet)) {
            throw "The causal diagnostic event category $pattern is missing."
        }
    }

    Write-Host '[5/10] Verifying the 20 new epoch, stack, and diagnostic tests...'
    $newTestFiles = @(
        '.\tests\StarCluster.Tests\Combat\Tracking\TacticalTrackEpochTests.cs',
        '.\tests\StarCluster.Tests\Combat\Tracking\TacticalMissileStackTests.cs',
        '.\tests\StarCluster.Tests\Diagnostics\DiagnosticEventSemanticsTests.cs'
    )

    $newFactCount = 0
    foreach ($testFile in $newTestFiles) {
        if (-not (Test-Path $testFile)) {
            throw "Checkpoint 13b test file $testFile was not found."
        }
        $newFactCount += (Select-String -Path $testFile -Pattern '\[Fact\]' -AllMatches).Matches.Count
    }

    if ($newFactCount -ne 20) {
        throw "Expected 20 new [Fact] tests, but found $newFactCount."
    }

    $requiredTests = @(
        @{ File = $newTestFiles[0]; Pattern = 'RepeatedMissesInOneEpochAdvanceAgeOnlyOnce' },
        @{ File = $newTestFiles[0]; Pattern = 'ExtraEventsCannotAccelerateLossWithinOneTurn' },
        @{ File = $newTestFiles[0]; Pattern = 'SuccessfulObservationProtectsTrackFromLaterMissInSameEpoch' },
        @{ File = $newTestFiles[1]; Pattern = 'CollocatedFriendlyMissilesProduceOneCountedStack' },
        @{ File = $newTestFiles[1]; Pattern = 'FriendlyAndEnemyMissilesAtSameCoordinateRemainSeparateStacks' },
        @{ File = $newTestFiles[2]; Pattern = 'GuidanceLifecycleCanBeRecordedInCausalOrder' },
        @{ File = $newTestFiles[2]; Pattern = 'MovementEventCanPreservePlannedAndActualPaths' }
    )

    foreach ($requiredTest in $requiredTests) {
        if (-not (Select-String -Path $requiredTest.File -Pattern $requiredTest.Pattern -Quiet)) {
            throw "Required Checkpoint 13b regression test $($requiredTest.Pattern) is missing."
        }
    }

    Write-Host '[6/10] Verifying Godot stacks, layered-defense feedback, and fixed controls...'
    $mainFile = '.\src\StarCluster.Game\Scripts\Main.cs'
    $boardFile = '.\src\StarCluster.Game\Scripts\HexBoardView.cs'
    $trackFile = '.\src\StarCluster.Game\Scripts\DemoTrackState.cs'

    foreach ($gameFile in @($mainFile, $boardFile, $trackFile)) {
        if (-not (Test-Path $gameFile)) {
            throw "Required Checkpoint 13b Godot source $gameFile was not found."
        }
    }

    $mainPatterns = @(
        'Star Cluster - Checkpoint 13b',
        'checkpoint-13b',
        'detailScroll',
        '_movementCommandPanel',
        '_directFireCommandPanel',
        '_missileCommandPanel',
        'Installed PDS auxiliary',
        'MAIN WEAPON',
        'PDS',
        'MissileGuidanceStarted',
        'MissileMoved',
        'InterceptionTargetAcquired',
        'MissileGuidanceCompleted',
        'plannedRoute',
        'actualMovementPath',
        'waitReason',
        'observationEpoch',
        'ageAdvanced'
    )

    foreach ($pattern in $mainPatterns) {
        if (-not (Select-String -Path $mainFile -Pattern ([regex]::Escape($pattern)) -Quiet)) {
            throw "Main.cs is missing required Checkpoint 13b behavior: $pattern"
        }
    }

    $boardPatterns = @(
        'TacticalMissileStackService.Build',
        'stack.DisplaySymbol',
        'stack.Count',
        'stack.IsStacked'
    )
    foreach ($pattern in $boardPatterns) {
        if (-not (Select-String -Path $boardFile -Pattern ([regex]::Escape($pattern)) -Quiet)) {
            throw "HexBoardView.cs is missing required stacked-missile presentation: $pattern"
        }
    }

    if (-not (Select-String -Path $trackFile -Pattern 'observationEpoch' -Quiet) -or
        -not (Select-String -Path $trackFile -Pattern '_observationEpoch' -Quiet)) {
        throw 'DemoTrackState does not preserve an explicit observation epoch.'
    }

    if (-not (Select-String -Path $mainFile -Pattern '_turnState.TurnNumber' -Quiet)) {
        throw 'Main.cs does not supply the tactical turn number as the observation epoch.'
    }

    Write-Host '[7/10] Verifying Concept v0.3g and synchronized documentation...'
    $documentationFiles = @(
        '.\docs\README.md',
        '.\docs\Star_Cluster_Game_Concept_v0.3g.docx',
        '.\docs\archive\Star_Cluster_Game_Concept_v0.3f.docx',
        '.\docs\Prototype_TODO.md',
        '.\docs\checkpoints\Checkpoint_13b_Track_Aging_Epochs_And_Tactical_Observability.md',
        '.\src\StarCluster.Game\README.md'
    )

    foreach ($documentationFile in $documentationFiles) {
        if (-not (Test-Path $documentationFile)) {
            throw "Required documentation file $documentationFile was not found."
        }
    }

    if (-not (Select-String -Path '.\docs\README.md' -Pattern 'Star_Cluster_Game_Concept_v0.3g.docx' -Quiet)) {
        throw 'The documentation index does not identify Concept v0.3g as current.'
    }

    if (-not (Select-String -Path '.\docs\README.md' -Pattern 'Checkpoint_13b_Track_Aging_Epochs_And_Tactical_Observability.md' -Quiet)) {
        throw 'The documentation index does not reference Checkpoint 13b.'
    }

    if (-not (Select-String -Path '.\docs\Prototype_TODO.md' -Pattern 'observation epochs' -Quiet) -or
        -not (Select-String -Path '.\docs\Prototype_TODO.md' -Pattern 'Collocated missiles' -Quiet)) {
        throw 'The living TODO does not record the Checkpoint 13b resolved work.'
    }

    Remove-Item '.\docs\Star_Cluster_Game_Concept_v0.3f.docx' -Force -ErrorAction SilentlyContinue

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
    Write-Host 'Checkpoint 13b completed successfully.' -ForegroundColor Green
    Write-Host 'Expected engine-independent tests passed: 385.'
    Write-Host 'Reopen Godot and press F5. Confirm once-per-turn track aging, counted collocated missile markers with salvo cycling, visible PDS readiness, distinct held-main-weapon and PDS feedback, fixed command controls, and causal checkpoint-13b journals.'
    Write-Host 'Upload the matching .log and .jsonl files with any screenshots for review.'
    Write-Host 'Next candidate checkpoint: sensor signatures and electronic-warfare foundations, after reviewing the local Checkpoint 13b results.'
}
finally {
    Pop-Location
}
