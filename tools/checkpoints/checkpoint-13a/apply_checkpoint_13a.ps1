[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$repositoryRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
Push-Location $repositoryRoot

try {
    Write-Host '[1/10] Verifying the Star Cluster repository and Checkpoint 13...'

    if (-not (Test-Path '.\StarCluster.sln')) {
        throw "StarCluster.sln was not found at $repositoryRoot. Extract the package into the repository root."
    }

    $priorFiles = @(
        '.\src\StarCluster.Core\Combat\Tracking\TacticalTrackRecord.cs',
        '.\src\StarCluster.Core\Combat\Tracking\TacticalMissileKnowledgeService.cs',
        '.\src\StarCluster.Game\Scripts\Main.cs',
        '.\docs\checkpoints\Checkpoint_13_Target_Track_And_Tactical_Presentation_Foundations.md'
    )

    foreach ($priorFile in $priorFiles) {
        if (-not (Test-Path $priorFile)) {
            throw "Required prior-checkpoint file $priorFile was not found. Apply Checkpoint 13 first."
        }
    }

    Write-Host '[2/10] Confirming that Godot is closed...'
    $godotProcesses = Get-Process -ErrorAction SilentlyContinue |
        Where-Object { $_.ProcessName -like 'Godot*' }

    if ($godotProcesses) {
        $processNames = ($godotProcesses.ProcessName | Sort-Object -Unique) -join ', '
        throw "Close the Godot editor and debug window before applying Checkpoint 13a. Running process(es): $processNames"
    }

    Write-Host '[3/10] Checking the pinned .NET SDK...'
    $sdkVersion = dotnet --version
    Write-Host "       SDK: $sdkVersion"

    if ($sdkVersion -ne '8.0.423') {
        throw "Expected .NET SDK 8.0.423 from global.json, but dotnet selected $sdkVersion."
    }

    Write-Host '[4/10] Verifying the engine-independent diagnostic journal...'
    $diagnosticFiles = @(
        '.\src\StarCluster.Core\Diagnostics\DiagnosticEventType.cs',
        '.\src\StarCluster.Core\Diagnostics\DiagnosticEvent.cs',
        '.\src\StarCluster.Core\Diagnostics\DiagnosticEventJournal.cs',
        '.\src\StarCluster.Core\Diagnostics\DiagnosticEventJsonlFormatter.cs',
        '.\src\StarCluster.Core\Diagnostics\DiagnosticEventTextFormatter.cs'
    )

    foreach ($diagnosticFile in $diagnosticFiles) {
        if (-not (Test-Path $diagnosticFile)) {
            throw "Checkpoint 13a diagnostic source $diagnosticFile was not found. Re-extract the package."
        }
    }

    if (-not (Select-String -Path '.\src\StarCluster.Core\Diagnostics\DiagnosticEventJournal.cs' -Pattern '_nextSequence' -Quiet)) {
        throw 'The diagnostic journal does not preserve a monotonic event sequence.'
    }

    if (-not (Select-String -Path '.\src\StarCluster.Core\Diagnostics\DiagnosticEventJsonlFormatter.cs' -Pattern 'JsonSerializer.Serialize' -Quiet)) {
        throw 'The JSON Lines formatter is missing.'
    }

    if (-not (Select-String -Path '.\src\StarCluster.Core\Combat\Tracking\TacticalTrackRecord.cs' -Pattern 'ObservedCoordinateHistory' -Quiet)) {
        throw 'Observer-safe observed-coordinate history is missing.'
    }

    if (-not (Select-String -Path '.\src\StarCluster.Core\Combat\Tracking\TacticalMissileKnowledgeService.cs' -Pattern 'track.ObservedCoordinateHistory' -Quiet)) {
        throw 'Hostile missile presentation is not using observer-derived travel history.'
    }

    Write-Host '[5/10] Verifying the 16 new journal and observed-trail tests...'
    $newTestFiles = @(
        '.\tests\StarCluster.Tests\Diagnostics\DiagnosticEventJournalTests.cs',
        '.\tests\StarCluster.Tests\Combat\Tracking\ObservedTrackHistoryTests.cs'
    )

    $newFactCount = 0
    foreach ($testFile in $newTestFiles) {
        if (-not (Test-Path $testFile)) {
            throw "Checkpoint 13a test file $testFile was not found."
        }

        $newFactCount += (Select-String -Path $testFile -Pattern '\[Fact\]' -AllMatches).Matches.Count
    }

    if ($newFactCount -ne 16) {
        throw "Expected 16 new [Fact] tests, but found $newFactCount."
    }

    $requiredTests = @(
        @{ File = '.\tests\StarCluster.Tests\Diagnostics\DiagnosticEventJournalTests.cs'; Pattern = 'RecordAssignsMonotonicSequenceNumbers' },
        @{ File = '.\tests\StarCluster.Tests\Diagnostics\DiagnosticEventJournalTests.cs'; Pattern = 'JsonlFormatterUsesCamelCaseAndStringEnums' },
        @{ File = '.\tests\StarCluster.Tests\Diagnostics\DiagnosticEventJournalTests.cs'; Pattern = 'FormattersPreserveBeforeAndAfterCoordinates' },
        @{ File = '.\tests\StarCluster.Tests\Combat\Tracking\ObservedTrackHistoryTests.cs'; Pattern = 'ChangedDetectedCoordinateExtendsObservedHistory' },
        @{ File = '.\tests\StarCluster.Tests\Combat\Tracking\ObservedTrackHistoryTests.cs'; Pattern = 'HostileMissileContactExposesObservedTrailWithoutAuthoritativeRoute' }
    )

    foreach ($requiredTest in $requiredTests) {
        if (-not (Select-String -Path $requiredTest.File -Pattern $requiredTest.Pattern -Quiet)) {
            throw "Required Checkpoint 13a regression test $($requiredTest.Pattern) is missing."
        }
    }

    Write-Host '[6/10] Verifying automatic Godot logging and track diagnostics...'
    $mainFile = '.\src\StarCluster.Game\Scripts\Main.cs'
    $boardFile = '.\src\StarCluster.Game\Scripts\HexBoardView.cs'
    $trackFile = '.\src\StarCluster.Game\Scripts\DemoTrackState.cs'
    $automaticLogFile = '.\src\StarCluster.Game\Scripts\AutomaticDiagnosticLog.cs'

    $gameFiles = @($mainFile, $boardFile, $trackFile, $automaticLogFile)
    foreach ($gameFile in $gameFiles) {
        if (-not (Test-Path $gameFile)) {
            throw "Required Checkpoint 13a Godot source $gameFile was not found."
        }
    }

    $mainPatterns = @(
        'Star Cluster - Checkpoint 13a',
        'ProjectSettings.GlobalizePath("user://logs")',
        'BeginDiagnosticLog',
        'EndCurrentDiagnosticLog',
        'LogTrackUpdates',
        'MissileGuidanceResolved',
        'MissileInterceptionAttempted'
    )

    foreach ($pattern in $mainPatterns) {
        if (-not (Select-String -Path $mainFile -Pattern ([regex]::Escape($pattern)) -Quiet)) {
            throw "Main.cs is missing required Checkpoint 13a behavior: $pattern"
        }
    }

    $logPatterns = @(
        'checkpointVersion',
        "yyyyMMdd'T'HHmmssfff'Z'",
        'encounter-{encounterNumber:D3}',
        '.jsonl',
        '.log',
        'Flush()'
    )

    foreach ($pattern in $logPatterns) {
        if (-not (Select-String -Path $automaticLogFile -Pattern ([regex]::Escape($pattern)) -Quiet)) {
            throw "AutomaticDiagnosticLog.cs is missing required behavior: $pattern"
        }
    }

    if (Select-String -Path $mainFile -Pattern 'Open log folder' -Quiet) {
        throw 'Checkpoint 13a should not add an Open log folder button.'
    }

    if (-not (Select-String -Path $boardFile -Pattern 'known contacts:' -Quiet) -or
        -not (Select-String -Path $boardFile -Pattern 'TacticalMissileContact' -Quiet)) {
        throw 'Pointer inspection does not include track-aware missile contacts.'
    }

    if (-not (Select-String -Path $boardFile -Pattern '_hexSize \* 0.27f' -Quiet)) {
        throw 'The projected-route first-segment visibility correction is missing.'
    }

    if (-not (Select-String -Path $trackFile -Pattern 'InitialUpdateResults' -Quiet)) {
        throw 'Initial Track Update results are not available to the automatic journal.'
    }

    Write-Host '[7/10] Verifying Concept v0.3f and synchronized documentation...'
    $documentationFiles = @(
        '.\docs\README.md',
        '.\docs\Star_Cluster_Game_Concept_v0.3f.docx',
        '.\docs\archive\Star_Cluster_Game_Concept_v0.3e.docx',
        '.\docs\Prototype_TODO.md',
        '.\docs\checkpoints\Checkpoint_13a_Automatic_Event_Journal_And_Track_Diagnostics.md',
        '.\src\StarCluster.Game\README.md'
    )

    foreach ($documentationFile in $documentationFiles) {
        if (-not (Test-Path $documentationFile)) {
            throw "Required documentation file $documentationFile was not found."
        }
    }

    if (-not (Select-String -Path '.\docs\README.md' -Pattern 'Star_Cluster_Game_Concept_v0.3f.docx' -Quiet)) {
        throw 'The documentation index does not identify Concept v0.3f as current.'
    }

    if (-not (Select-String -Path '.\docs\README.md' -Pattern 'Checkpoint_13a_Automatic_Event_Journal_And_Track_Diagnostics.md' -Quiet)) {
        throw 'The documentation index does not reference Checkpoint 13a.'
    }

    if (-not (Select-String -Path '.\docs\Prototype_TODO.md' -Pattern 'player-visible combat log' -Quiet)) {
        throw 'The living TODO does not preserve the separate player-visible combat-log work.'
    }

    # The overlay archives v0.3e and installs v0.3f. Remove the former
    # current-copy path so docs/ retains one unambiguous current concept file.
    Remove-Item '.\docs\Star_Cluster_Game_Concept_v0.3e.docx' -Force -ErrorAction SilentlyContinue

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
    Write-Host 'Checkpoint 13a completed successfully.' -ForegroundColor Green
    Write-Host 'Expected engine-independent tests passed: 365.'
    Write-Host 'Reopen Godot and press F5. Confirm that timestamped checkpoint-13a JSONL and text logs are created automatically, reset begins a new encounter pair, pointer inspection reports missile track state, observed hostile trails remain observer-safe, and Lost-track waiting is explicit in the log.'
    Write-Host 'Upload the matching .log and .jsonl files with any screenshots for review.'
    Write-Host 'Next candidate checkpoint: sensor signatures and electronic-warfare foundations, after reviewing the generated Checkpoint 13a journal.'
}
finally {
    Pop-Location
}
