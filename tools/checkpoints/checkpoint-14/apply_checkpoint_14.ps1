[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$repositoryRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
Push-Location $repositoryRoot

try {
    Write-Host '[1/10] Verifying the Star Cluster repository and Checkpoint 13e...'

    if (-not (Test-Path '.\StarCluster.sln')) {
        throw "StarCluster.sln was not found at $repositoryRoot. Extract the package into the repository root."
    }

    $priorFiles = @(
        '.\src\StarCluster.Core\Combat\DirectFire\DirectFireTargetEligibility.cs',
        '.\docs\checkpoints\Checkpoint_13e_Target_Eligibility_And_Viewport_Stability.md',
        '.\tools\checkpoints\checkpoint-13e\apply_checkpoint_13e.ps1'
    )
    foreach ($priorFile in $priorFiles) {
        if (-not (Test-Path $priorFile)) {
            throw "Required prior-checkpoint file $priorFile was not found. Apply Checkpoint 13e first."
        }
    }

    Write-Host '[2/10] Confirming that Godot is closed...'
    $godotProcesses = Get-Process -ErrorAction SilentlyContinue |
        Where-Object { $_.ProcessName -like 'Godot*' }
    if ($godotProcesses) {
        $processNames = ($godotProcesses.ProcessName | Sort-Object -Unique) -join ', '
        throw "Close the Godot editor and debug window before applying Checkpoint 14. Running process(es): $processNames"
    }

    Write-Host '[3/10] Checking the pinned .NET SDK...'
    $sdkVersion = dotnet --version
    Write-Host "       SDK: $sdkVersion"
    if ($sdkVersion -ne '8.0.423') {
        throw "Expected .NET SDK 8.0.423 from global.json, but dotnet selected $sdkVersion."
    }

    Write-Host '[4/10] Verifying sensor signatures, effective envelopes, electronic warfare, and the policy seam...'
    $sensorFiles = @(
        '.\src\StarCluster.Core\Combat\Tracking\SensorMode.cs',
        '.\src\StarCluster.Core\Combat\Tracking\SensorSignatureProfile.cs',
        '.\src\StarCluster.Core\Combat\Tracking\ElectronicWarfareProfile.cs',
        '.\src\StarCluster.Core\Combat\Tracking\SensorEnvironmentProfile.cs',
        '.\src\StarCluster.Core\Combat\Tracking\SensorContactEvaluationContext.cs',
        '.\src\StarCluster.Core\Combat\Tracking\SensorContactEvaluationResult.cs',
        '.\src\StarCluster.Core\Combat\Tracking\SensorContactResolutionContext.cs',
        '.\src\StarCluster.Core\Combat\Tracking\ISensorContactResolutionPolicy.cs',
        '.\src\StarCluster.Core\Combat\Tracking\DeterministicSensorContactResolutionPolicy.cs'
    )
    foreach ($sourceFile in $sensorFiles) {
        if (-not (Test-Path $sourceFile)) {
            throw "Checkpoint 14 source $sourceFile was not found. Re-extract the package."
        }
    }

    $evaluatorFile = '.\src\StarCluster.Core\Combat\Tracking\SensorContactEvaluator.cs'
    foreach ($pattern in @(
        'ActiveModeRangeBonusHexes',
        'TargetSignature',
        'Environment.RangePenaltyHexes',
        'rawJammingPenalty - counterJamming',
        'MissedOccluded',
        'ISensorContactResolutionPolicy',
        'DeterministicSensorContactResolutionPolicy.Instance')) {
        if (-not (Select-String -Path $evaluatorFile -Pattern ([regex]::Escape($pattern)) -Quiet)) {
            throw "SensorContactEvaluator is missing required Checkpoint 14 behavior: $pattern"
        }
    }
    if (-not (Select-String -Path '.\src\StarCluster.Core\Combat\Tracking\MissileMovementObservationService.cs' -Pattern 'SensorContactEvaluationContext' -Quiet)) {
        throw 'Missile movement observation is not wired to the Checkpoint 14 sensor context.'
    }

    Write-Host '[5/10] Verifying the 19 new sensor and electronic-warfare tests...'
    $testFile = '.\tests\StarCluster.Tests\Combat\Tracking\SensorSignatureAndElectronicWarfareTests.cs'
    if (-not (Test-Path $testFile)) {
        throw "Checkpoint 14 test file $testFile was not found."
    }
    $newFactCount = (Select-String -Path $testFile -Pattern '\[Fact\]' -AllMatches).Matches.Count
    if ($newFactCount -ne 19) {
        throw "Expected 19 new [Fact] tests, but found $newFactCount."
    }
    foreach ($test in @(
        'NeutralContextMatchesLegacyObservation',
        'ActiveSensorsExtendFirmEnvelope',
        'TargetActiveEmissionsIncreaseItsSignature',
        'TargetJammingShrinksBothEffectiveEnvelopes',
        'OcclusionRemainsAbsoluteUnderActiveSensors',
        'SameHexContactIsFirmDespiteRangePenalties',
        'ReplaceablePolicyMayForceAMissWithinTheEnvelope',
        'RepeatedSensorStateMissesDoNotAgeTwiceInOneEpoch')) {
        if (-not (Select-String -Path $testFile -Pattern $test -Quiet)) {
            throw "Required Checkpoint 14 regression test $test is missing."
        }
    }

    Write-Host '[6/10] Verifying the Godot range gate, state controls, dynamic interception context, and diagnostics...'
    $mainFile = '.\src\StarCluster.Game\Scripts\Main.cs'
    $trackStateFile = '.\src\StarCluster.Game\Scripts\DemoTrackState.cs'
    $trackProviderFile = '.\src\StarCluster.Game\Scripts\DemoMissileDefenseTrackProvider.cs'
    $scenarioFile = '.\src\StarCluster.Game\Scripts\DemoScenarioFactory.cs'
    foreach ($gameFile in @($mainFile,$trackStateFile,$trackProviderFile,$scenarioFile)) {
        if (-not (Test-Path $gameFile)) {
            throw "Required Checkpoint 14 Godot source $gameFile was not found."
        }
    }
    foreach ($pattern in @(
        'Star Cluster - Checkpoint 14',
        'checkpoint-14',
        'Player active sensors (+2 range)',
        'Enemy active emissions (+2 signature)',
        'OnSensorStateToggled',
        'SensorStateChanged',
        'baseFirmRange',
        'baseApproximateRange',
        'effectiveFirmRange',
        'environmentProfile',
        'netJammingPenalty')) {
        if (-not (Select-String -Path $mainFile -Pattern ([regex]::Escape($pattern)) -Quiet)) {
            throw "Main.cs is missing required Checkpoint 14 behavior: $pattern"
        }
    }
    foreach ($pattern in @(
        'CreatePlayerMissileEvaluationContext',
        'SetSensorState',
        'CreateShipEvaluationContext',
        'GetLastSensorEvaluation')) {
        if (-not (Select-String -Path $trackStateFile -Pattern $pattern -Quiet)) {
            throw "DemoTrackState is missing required Checkpoint 14 behavior: $pattern"
        }
    }
    if (-not (Select-String -Path $trackProviderFile -Pattern 'Func<SensorContactEvaluationContext>' -Quiet)) {
        throw 'Held-main-weapon interception does not use the dynamic Checkpoint 14 sensor context.'
    }
    if (-not (Select-String -Path $scenarioFile -Pattern 'Sensor and jamming range gate' -Quiet)) {
        throw 'The focused Sensor / EW range-gate scenario is missing.'
    }

    Write-Host '[7/10] Verifying Concept v0.3k and synchronized checkpoint documentation...'
    $documentationFiles = @(
        '.\docs\README.md',
        '.\docs\Star_Cluster_Game_Concept_v0.3k.docx',
        '.\docs\archive\Star_Cluster_Game_Concept_v0.3j.docx',
        '.\docs\Prototype_TODO.md',
        '.\docs\checkpoints\Checkpoint_14_Sensor_Signatures_And_Electronic_Warfare_Foundations.md',
        '.\docs\validation\Baseline_Tactical_Regression_Encounter.md',
        '.\src\StarCluster.Game\README.md'
    )
    foreach ($documentationFile in $documentationFiles) {
        if (-not (Test-Path $documentationFile)) {
            throw "Required documentation file $documentationFile was not found."
        }
    }
    if (-not (Select-String -Path '.\docs\README.md' -Pattern 'Star_Cluster_Game_Concept_v0.3k.docx' -Quiet) -or
        -not (Select-String -Path '.\docs\README.md' -Pattern 'Checkpoint_14_Sensor_Signatures_And_Electronic_Warfare_Foundations.md' -Quiet)) {
        throw 'The documentation index is not synchronized with Checkpoint 14.'
    }
    foreach ($pattern in @(
        'Sensor and jamming range gate',
        'effective Firm 6 and Approximate 10',
        'SensorStateChanged',
        'missile-trail presentation-policy opinion')) {
        if (-not (Select-String -Path '.\docs\validation\Baseline_Tactical_Regression_Encounter.md' -Pattern ([regex]::Escape($pattern)) -Quiet)) {
            throw "The Checkpoint 14 validation runbook is missing: $pattern"
        }
    }

    Remove-Item '.\docs\Star_Cluster_Game_Concept_v0.3j.docx' -Force -ErrorAction SilentlyContinue

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
    Write-Host 'Checkpoint 14 completed successfully.'
    Write-Host 'Expected engine-independent tests passed: 440.'
    Write-Host 'Reopen Godot and run docs\validation\Baseline_Tactical_Regression_Encounter.md exactly.'
    Write-Host 'First repeat the four-turn baseline with every Sensor / EW control passive or off; then perform the focused Sensor and jamming range-gate check.'
    Write-Host 'Confirm the tactical viewport and observer-safe behavior remain stable, and record your preferred selected-versus-unselected missile-trail policy.'
    Write-Host 'Upload the matching checkpoint-14 .log and .jsonl files, updated numbered notes, the Sensor / EW summary, trail-policy opinion, and the four requested screenshots.'
    Write-Host 'Next candidate checkpoint: missile seeker acquisition and reacquisition foundations, after reviewing the repeated Checkpoint 14 run.'
}
finally {
    Pop-Location
}
