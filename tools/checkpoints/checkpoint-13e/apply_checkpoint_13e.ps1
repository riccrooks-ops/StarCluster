[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$repositoryRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
Push-Location $repositoryRoot

try {
    Write-Host '[1/10] Verifying the Star Cluster repository and Checkpoint 13d...'

    if (-not (Test-Path '.\StarCluster.sln')) {
        throw "StarCluster.sln was not found at $repositoryRoot. Extract the package into the repository root."
    }

    $priorFiles = @(
        '.\src\StarCluster.Core\Combat\Tracking\MissileMovementObservationService.cs',
        '.\docs\checkpoints\Checkpoint_13d_Observed_Launch_Trails_And_Batch_Finalization.md',
        '.\docs\validation\Baseline_Tactical_Regression_Encounter.md'
    )
    foreach ($priorFile in $priorFiles) {
        if (-not (Test-Path $priorFile)) {
            throw "Required prior-checkpoint file $priorFile was not found. Apply Checkpoint 13d first."
        }
    }

    Write-Host '[2/10] Confirming that Godot is closed...'
    $godotProcesses = Get-Process -ErrorAction SilentlyContinue |
        Where-Object { $_.ProcessName -like 'Godot*' }
    if ($godotProcesses) {
        $processNames = ($godotProcesses.ProcessName | Sort-Object -Unique) -join ', '
        throw "Close the Godot editor and debug window before applying Checkpoint 13e. Running process(es): $processNames"
    }

    Write-Host '[3/10] Checking the pinned .NET SDK...'
    $sdkVersion = dotnet --version
    Write-Host "       SDK: $sdkVersion"
    if ($sdkVersion -ne '8.0.423') {
        throw "Expected .NET SDK 8.0.423 from global.json, but dotnet selected $sdkVersion."
    }

    Write-Host '[4/10] Verifying direct-fire eligibility, current-LOS gating, cue persistence, and viewport isolation...'
    $eligibilityFiles = @(
        '.\src\StarCluster.Core\Combat\DirectFire\DirectFireTargetEligibility.cs',
        '.\src\StarCluster.Core\Combat\DirectFire\DirectFireTargetEligibilityResult.cs',
        '.\src\StarCluster.Core\Combat\DirectFire\DirectFireTargetEligibilityStatus.cs'
    )
    foreach ($sourceFile in $eligibilityFiles) {
        if (-not (Test-Path $sourceFile)) {
            throw "Checkpoint 13e source $sourceFile was not found. Re-extract the package."
        }
    }

    $eligibilityService = '.\src\StarCluster.Core\Combat\DirectFire\DirectFireTargetEligibility.cs'
    foreach ($pattern in @(
        'EvaluateShipAttack',
        'EvaluateSpecificMissileOrder',
        'BlockedLineOfSight',
        'EligibleForSpecificMissileReserve',
        'WeaponCannotInterceptMissiles')) {
        if (-not (Select-String -Path $eligibilityService -Pattern ([regex]::Escape($pattern)) -Quiet)) {
            throw "DirectFireTargetEligibility is missing required behavior: $pattern"
        }
    }

    Write-Host '[5/10] Verifying the 10 new target-eligibility tests...'
    $testFile = '.\tests\StarCluster.Tests\Combat\DirectFire\DirectFireTargetEligibilityTests.cs'
    if (-not (Test-Path $testFile)) {
        throw "Checkpoint 13e test file $testFile was not found."
    }
    $newFactCount = (Select-String -Path $testFile -Pattern '\[Fact\]' -AllMatches).Matches.Count
    if ($newFactCount -ne 10) {
        throw "Expected 10 new [Fact] tests, but found $newFactCount."
    }
    foreach ($test in @(
        'ShipAttackRequiresCurrentLineOfSight',
        'ShipAttackRequiresCurrentRange',
        'SpecificMissileOrderRequiresFirmTrack',
        'SpecificMissileOrderRequiresCurrentLineOfSight',
        'SpecificMissileOrderMayReserveOnlyForCurrentRangeShortfall')) {
        if (-not (Select-String -Path $testFile -Pattern $test -Quiet)) {
            throw "Required Checkpoint 13e regression test $test is missing."
        }
    }

    Write-Host '[6/10] Verifying Godot command gating, muted inspection, stable layout, and Damage-phase cues...'
    $mainFile = '.\src\StarCluster.Game\Scripts\Main.cs'
    $boardFile = '.\src\StarCluster.Game\Scripts\HexBoardView.cs'
    foreach ($gameFile in @($mainFile,$boardFile)) {
        if (-not (Test-Path $gameFile)) {
            throw "Required Checkpoint 13e Godot source $gameFile was not found."
        }
    }
    foreach ($pattern in @(
        'Star Cluster - Checkpoint 13e',
        'checkpoint-13e',
        'EvaluateEnemyShipDirectFireEligibility',
        'EvaluateSpecificMissileDirectFireEligibility',
        'Use Hold main weapon for any missile instead',
        'preserveMissileResolutionCues',
        'fixed-width host')) {
        if (-not (Select-String -Path $mainFile -Pattern ([regex]::Escape($pattern)) -Quiet)) {
            throw "Main.cs is missing required Checkpoint 13e behavior: $pattern"
        }
    }
    foreach ($pattern in @(
        'selectedAsWeaponTarget',
        '_selectedMissileIsWeaponTarget',
        'selectionColor')) {
        if (-not (Select-String -Path $boardFile -Pattern ([regex]::Escape($pattern)) -Quiet)) {
            throw "HexBoardView is missing required Checkpoint 13e presentation behavior: $pattern"
        }
    }

    Write-Host '[7/10] Verifying Concept v0.3j and synchronized validation documentation...'
    $documentationFiles = @(
        '.\docs\README.md',
        '.\docs\Star_Cluster_Game_Concept_v0.3j.docx',
        '.\docs\archive\Star_Cluster_Game_Concept_v0.3i.docx',
        '.\docs\Prototype_TODO.md',
        '.\docs\checkpoints\Checkpoint_13e_Target_Eligibility_And_Viewport_Stability.md',
        '.\docs\validation\Baseline_Tactical_Regression_Encounter.md',
        '.\src\StarCluster.Game\README.md'
    )
    foreach ($documentationFile in $documentationFiles) {
        if (-not (Test-Path $documentationFile)) {
            throw "Required documentation file $documentationFile was not found."
        }
    }
    if (-not (Select-String -Path '.\docs\README.md' -Pattern 'Star_Cluster_Game_Concept_v0.3j.docx' -Quiet) -or
        -not (Select-String -Path '.\docs\README.md' -Pattern 'Checkpoint_13e_Target_Eligibility_And_Viewport_Stability.md' -Quiet)) {
        throw 'The documentation index is not synchronized with Checkpoint 13e.'
    }
    foreach ($pattern in @(
        'specific interception order',
        'Hold main weapon for any missile',
        'do not shift',
        'Damage Control')) {
        if (-not (Select-String -Path '.\docs\validation\Baseline_Tactical_Regression_Encounter.md' -Pattern ([regex]::Escape($pattern)) -Quiet)) {
            throw "The baseline regression runbook is missing: $pattern"
        }
    }

    Remove-Item '.\docs\Star_Cluster_Game_Concept_v0.3i.docx' -Force -ErrorAction SilentlyContinue

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
    if ($testText -notmatch 'Passed:\s+421') {
        throw 'The complete suite did not report the expected 421 passed tests.'
    }
    if (Select-String -Path '.\src\StarCluster.Core\StarCluster.Core.csproj' -Pattern 'Godot' -Quiet) {
        throw 'StarCluster.Core unexpectedly contains a Godot dependency.'
    }

    Write-Host ''
    Write-Host 'Checkpoint 13e completed successfully.'
    Write-Host 'Expected engine-independent tests passed: 421.'
    Write-Host 'Reopen Godot and repeat docs\validation\Baseline_Tactical_Regression_Encounter.md exactly.'
    Write-Host 'Confirm blocked or stale contacts are inspection-only, hold-for-any remains available, the tactical map never shifts, and IMPACT x2 persists through Damage.'
    Write-Host 'Upload the matching checkpoint-13e .log and .jsonl files, updated numbered notes, and the three requested screenshots.'
    Write-Host 'Next candidate checkpoint: sensor signatures and electronic-warfare foundations, after reviewing the repeated Checkpoint 13e run.'
}
finally {
    Pop-Location
}
