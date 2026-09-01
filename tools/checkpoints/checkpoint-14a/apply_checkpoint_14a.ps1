[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$repositoryRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
Push-Location $repositoryRoot

try {
    Write-Host '[1/10] Verifying the Star Cluster repository and Checkpoint 14...'

    if (-not (Test-Path '.\StarCluster.sln')) {
        throw "StarCluster.sln was not found at $repositoryRoot. Extract the package into the repository root."
    }

    $priorFiles = @(
        '.\src\StarCluster.Core\Combat\Tracking\SensorContactEvaluator.cs',
        '.\docs\checkpoints\Checkpoint_14_Sensor_Signatures_And_Electronic_Warfare_Foundations.md',
        '.\tools\checkpoints\checkpoint-14\apply_checkpoint_14.ps1'
    )
    foreach ($priorFile in $priorFiles) {
        if (-not (Test-Path $priorFile)) {
            throw "Required prior-checkpoint file $priorFile was not found. Apply Checkpoint 14 first."
        }
    }

    Write-Host '[2/10] Confirming that Godot is closed...'
    $godotProcesses = Get-Process -ErrorAction SilentlyContinue |
        Where-Object { $_.ProcessName -like 'Godot*' }
    if ($godotProcesses) {
        $processNames = ($godotProcesses.ProcessName | Sort-Object -Unique) -join ', '
        throw "Close the Godot editor and debug window before applying Checkpoint 14a. Running process(es): $processNames"
    }

    Write-Host '[3/10] Checking the pinned .NET SDK...'
    $sdkVersion = dotnet --version
    Write-Host "       SDK: $sdkVersion"
    if ($sdkVersion -ne '8.0.423') {
        throw "Expected .NET SDK 8.0.423 from global.json, but dotnet selected $sdkVersion."
    }

    Write-Host '[4/10] Verifying the responsive side panel and directional Sensor / EW summary...'
    $mainFile = '.\src\StarCluster.Game\Scripts\Main.cs'
    if (-not (Test-Path $mainFile)) {
        throw "Checkpoint 14a Godot source $mainFile was not found. Re-extract the package."
    }
    foreach ($pattern in @(
        'checkpoint-14a',
        'Star Cluster - Checkpoint 14a',
        'CustomMinimumSize = new Vector2(420.0f, 0.0f)',
        'CustomMinimumSize = Vector2.Zero',
        'FitToLongestItem = false',
        'CreateWrappedCheckButton',
        'Sensor / EW status',
        'PLAYER -> ENEMY',
        'ENEMY -> PLAYER',
        'Player active sensors improve player detection',
        'Player jamming impairs enemy detection of the player')) {
        if (-not (Select-String -Path $mainFile -Pattern ([regex]::Escape($pattern)) -Quiet)) {
            throw "Main.cs is missing required Checkpoint 14a responsive or directional behavior: $pattern"
        }
    }

    Write-Host '[5/10] Verifying Approximate cues, selected-only trails, and track-quality-specific guidance wording...'
    $boardFile = '.\src\StarCluster.Game\Scripts\HexBoardView.cs'
    if (-not (Test-Path $boardFile)) {
        throw "Checkpoint 14a Godot source $boardFile was not found."
    }
    foreach ($pattern in @(
        'ShouldDrawObservedTrail',
        'ShouldDrawMissileProjection',
        'DrawSegmentedRing',
        'DrawApproximateTag',
        '"APPROX"',
        'TacticalTrackQuality.Stale => 0.20f')) {
        if (-not (Select-String -Path $boardFile -Pattern ([regex]::Escape($pattern)) -Quiet)) {
            throw "HexBoardView.cs is missing required Checkpoint 14a presentation behavior: $pattern"
        }
    }
    foreach ($pattern in @(
        'MovedToApproximateCoordinate',
        'Reached the Approximate guidance coordinate without a current Firm terminal solution.',
        'MovedToLastKnownCoordinate',
        'Reached the Stale last-known coordinate without reacquisition.')) {
        if (-not (Select-String -Path $mainFile -Pattern ([regex]::Escape($pattern)) -Quiet)) {
            throw "Main.cs is missing required Checkpoint 14a guidance diagnostic wording: $pattern"
        }
    }

    Write-Host '[6/10] Verifying Concept v0.3l and the detailed missile-architecture documentation...'
    $documentationFiles = @(
        '.\docs\README.md',
        '.\docs\Star_Cluster_Game_Concept_v0.3l.docx',
        '.\docs\archive\Star_Cluster_Game_Concept_v0.3k.docx',
        '.\docs\Prototype_TODO.md',
        '.\docs\checkpoints\Checkpoint_14a_Tactical_Presentation_And_Missile_Architecture_Documentation.md',
        '.\docs\design\Missile_Guidance_Datalink_Sensor_And_Seeker_Architecture.md',
        '.\docs\validation\Baseline_Tactical_Regression_Encounter.md',
        '.\src\StarCluster.Game\README.md'
    )
    foreach ($documentationFile in $documentationFiles) {
        if (-not (Test-Path $documentationFile)) {
            throw "Required Checkpoint 14a documentation file $documentationFile was not found."
        }
    }

    $expectedV03kHash = '7b72ea9085ee3a506b6d11ca1b44ccf8a7b0e0db747091b3032bb170288e549f'
    $actualV03kHash = (Get-FileHash '.\docs\archive\Star_Cluster_Game_Concept_v0.3k.docx' -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actualV03kHash -ne $expectedV03kHash) {
        throw "The archived Concept v0.3k hash is $actualV03kHash, expected $expectedV03kHash."
    }

    foreach ($pattern in @(
        'Star_Cluster_Game_Concept_v0.3l.docx',
        'Checkpoint_14a_Tactical_Presentation_And_Missile_Architecture_Documentation.md',
        'Missile_Guidance_Datalink_Sensor_And_Seeker_Architecture.md')) {
        if (-not (Select-String -Path '.\docs\README.md' -Pattern ([regex]::Escape($pattern)) -Quiet)) {
            throw "The documentation index is missing: $pattern"
        }
    }
    foreach ($pattern in @(
        'Command-guided missile',
        'Seeker-only missile',
        'Sensor-only missile',
        'Sensor-plus-seeker missile',
        'launcher-to-missile datalink line of sight',
        'Target entry and departure are distinct movement-edge events',
        'overshoot-and-reacquisition tactic',
        'Hybrid ship-movement interface dependency')) {
        if (-not (Select-String -Path '.\docs\design\Missile_Guidance_Datalink_Sensor_And_Seeker_Architecture.md' -Pattern ([regex]::Escape($pattern)) -Quiet)) {
            throw "The detailed missile architecture is missing: $pattern"
        }
    }
    foreach ($pattern in @(
        'Checkpoint 14a focused presentation check',
        'segmented uncertainty ring',
        'MovedToApproximateCoordinate',
        'unselected historical trails remain hidden')) {
        if (-not (Select-String -Path '.\docs\validation\Baseline_Tactical_Regression_Encounter.md' -Pattern ([regex]::Escape($pattern)) -Quiet)) {
            throw "The Checkpoint 14a validation runbook is missing: $pattern"
        }
    }

    Remove-Item '.\docs\Star_Cluster_Game_Concept_v0.3k.docx' -Force -ErrorAction SilentlyContinue

    Write-Host '[7/10] Confirming Checkpoint 14 simulation foundations remain present...'
    foreach ($sourceFile in @(
        '.\src\StarCluster.Core\Combat\Tracking\SensorMode.cs',
        '.\src\StarCluster.Core\Combat\Tracking\SensorSignatureProfile.cs',
        '.\src\StarCluster.Core\Combat\Tracking\ElectronicWarfareProfile.cs',
        '.\src\StarCluster.Core\Combat\Tracking\ISensorContactResolutionPolicy.cs',
        '.\tests\StarCluster.Tests\Combat\Tracking\SensorSignatureAndElectronicWarfareTests.cs')) {
        if (-not (Test-Path $sourceFile)) {
            throw "Checkpoint 14 foundation file $sourceFile was not found."
        }
    }
    $newFactCount = (Select-String -Path '.\tests\StarCluster.Tests\Combat\Tracking\SensorSignatureAndElectronicWarfareTests.cs' -Pattern '\[Fact\]' -AllMatches).Matches.Count
    if ($newFactCount -ne 19) {
        throw "Expected the unchanged 19 Checkpoint 14 sensor/EW [Fact] tests, but found $newFactCount."
    }

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
    if ($testText -notmatch 'Passed:\s+440') {
        throw 'The complete suite did not report the expected 440 passed tests.'
    }
    if (Select-String -Path '.\src\StarCluster.Core\StarCluster.Core.csproj' -Pattern 'Godot' -Quiet) {
        throw 'StarCluster.Core unexpectedly contains a Godot dependency.'
    }

    Write-Host ''
    Write-Host 'Checkpoint 14a completed successfully.'
    Write-Host 'Expected engine-independent tests passed: 440.'
    Write-Host 'Reopen Godot and run the Checkpoint 14a focused presentation check in docs\validation\Baseline_Tactical_Regression_Encounter.md.'
    Write-Host 'Confirm no right-edge clipping, a stable tactical board, directional Sensor / EW calculations, segmented APPROX cues, selected-only historical trails, and corrected Approximate/Stale diagnostics.'
    Write-Host 'Upload the matching checkpoint-14a .log and .jsonl files, numbered notes, and the requested presentation screenshots.'
    Write-Host 'Next substantive checkpoint: hybrid one-hex-or-destination tactical ship movement with authoritative intermediate updates.'
}
finally {
    Pop-Location
}
