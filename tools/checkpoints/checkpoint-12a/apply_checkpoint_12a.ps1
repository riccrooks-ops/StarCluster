[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$repositoryRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
Push-Location $repositoryRoot

try {
    Write-Host '[1/10] Verifying the Star Cluster repository and Checkpoint 12...'

    if (-not (Test-Path '.\StarCluster.sln')) {
        throw "StarCluster.sln was not found at $repositoryRoot. Extract the package into the repository root."
    }

    $priorFiles = @(
        '.\src\StarCluster.Core\Combat\Missiles\MissileEngagementState.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileInterceptionPhaseContext.cs',
        '.\src\StarCluster.Game\Scripts\Main.cs',
        '.\docs\checkpoints\Checkpoint_12_Missile_Ownership_And_Interception_Foundations.md'
    )

    foreach ($priorFile in $priorFiles) {
        if (-not (Test-Path $priorFile)) {
            throw "Required prior-checkpoint file $priorFile was not found. Apply Checkpoint 12 first."
        }
    }

    Write-Host '[2/10] Confirming that Godot is closed...'
    $godotProcesses = Get-Process -ErrorAction SilentlyContinue |
        Where-Object { $_.ProcessName -like 'Godot*' }

    if ($godotProcesses) {
        $processNames = ($godotProcesses.ProcessName | Sort-Object -Unique) -join ', '
        throw "Close the Godot editor and debug window before applying Checkpoint 12a. Running process(es): $processNames"
    }

    Write-Host '[3/10] Checking the pinned .NET SDK...'
    $sdkVersion = dotnet --version
    Write-Host "       SDK: $sdkVersion"

    if ($sdkVersion -ne '8.0.423') {
        throw "Expected .NET SDK 8.0.423 from global.json, but dotnet selected $sdkVersion."
    }

    Write-Host '[4/10] Verifying phase order and direct-fire commitment sources...'
    $coreFiles = @(
        '.\src\StarCluster.Core\Combat\TacticalTurnPhase.cs',
        '.\src\StarCluster.Core\Combat\TacticalTurnState.cs',
        '.\src\StarCluster.Core\Combat\DirectFire\DirectFireOrderType.cs',
        '.\src\StarCluster.Core\Combat\DirectFire\DirectFireWeaponProfile.cs',
        '.\src\StarCluster.Core\Combat\DirectFire\DirectFireOrder.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileDefenseSourceType.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileDefenseSystem.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileInterceptionPhaseContext.cs'
    )

    foreach ($coreFile in $coreFiles) {
        if (-not (Test-Path $coreFile)) {
            throw "Checkpoint 12a source file $coreFile was not found. Re-extract the package."
        }
    }

    $turnState = '.\src\StarCluster.Core\Combat\TacticalTurnState.cs'
    if (-not (Select-String -Path $turnState -Pattern 'case TacticalTurnPhase.Movement:' -Quiet) -or
        -not (Select-String -Path $turnState -Pattern 'Phase = TacticalTurnPhase.DirectFire;' -Quiet)) {
        throw 'Movement does not advance to Direct Fire.'
    }

    if (-not (Select-String -Path $turnState -Pattern 'case TacticalTurnPhase.DirectFire:' -Quiet) -or
        -not (Select-String -Path $turnState -Pattern 'Phase = TacticalTurnPhase.MissileAndInterception;' -Quiet)) {
        throw 'Direct Fire does not advance to Missile / Interception.'
    }

    if (-not (Select-String -Path '.\src\StarCluster.Core\Combat\DirectFire\DirectFireOrder.cs' -Pattern 'HoldForAnyMissile' -Quiet)) {
        throw 'The hold-for-any defensive order is missing.'
    }

    if (-not (Select-String -Path '.\src\StarCluster.Core\Combat\DirectFire\DirectFireOrder.cs' -Pattern 'InterceptSpecificMissile' -Quiet)) {
        throw 'The selected-missile defensive order is missing.'
    }

    Write-Host '[5/10] Verifying the 18 new direct-fire and layered-defense tests...'
    $newTestFiles = @(
        '.\tests\StarCluster.Tests\Combat\DirectFire\DirectFireOrderTests.cs',
        '.\tests\StarCluster.Tests\Combat\DirectFire\LayeredInterceptionTests.cs'
    )

    $newFactCount = 0
    foreach ($testFile in $newTestFiles) {
        if (-not (Test-Path $testFile)) {
            throw "Checkpoint 12a test file $testFile was not found."
        }

        $newFactCount += (Select-String -Path $testFile -Pattern '\[Fact\]' -AllMatches).Matches.Count
    }

    if ($newFactCount -ne 18) {
        throw "Expected 18 new [Fact] tests, but found $newFactCount."
    }

    if (-not (Select-String -Path '.\tests\StarCluster.Tests\Combat\DirectFire\LayeredInterceptionTests.cs' -Pattern 'MissedHeldWeaponAllowsPointDefenseSecondOpportunity' -Quiet)) {
        throw 'The held-main-weapon plus PDS layered-defense regression test is missing.'
    }

    if (-not (Select-String -Path '.\tests\StarCluster.Tests\Combat\DirectFire\LayeredInterceptionTests.cs' -Pattern 'StarBlocksHeldWeaponButNotIndependentPointDefense' -Quiet)) {
        throw 'The held-weapon LOS versus independent PDS regression test is missing.'
    }

    Write-Host '[6/10] Verifying Godot commitments, phase restoration, and warning cleanup...'
    $mainFile = '.\src\StarCluster.Game\Scripts\Main.cs'
    $boardFile = '.\src\StarCluster.Game\Scripts\HexBoardView.cs'

    $mainPatterns = @(
        'Fire main weapon at selected ship',
        'Intercept selected missile',
        'Hold main weapon for any missile',
        'Hold main weapon fire',
        'EnterPhase',
        'held-main-weapon-player',
        'Advance to Direct Fire when ready'
    )

    foreach ($pattern in $mainPatterns) {
        if (-not (Select-String -Path $mainFile -Pattern ([regex]::Escape($pattern)) -Quiet)) {
            throw "Main.cs is missing required Checkpoint 12a presentation or state: $pattern"
        }
    }

    if (-not (Select-String -Path $boardFile -Pattern 'DisplayMode == TargetingMode.Movement' -Quiet)) {
        throw 'HexBoardView does not preserve missile markers for Direct Fire selection.'
    }

    if (Select-String -Path $mainFile -Pattern 'out GuidedMissileAdvanceResult lastAdvance' -Quiet) {
        throw 'The Checkpoint 12 nullable warning pattern is still present.'
    }

    Write-Host '[7/10] Verifying Concept v0.3d and synchronized documentation...'
    $documentationFiles = @(
        '.\docs\README.md',
        '.\docs\Star_Cluster_Game_Concept_v0.3d.docx',
        '.\docs\archive\Star_Cluster_Game_Concept_v0.3c.docx',
        '.\docs\checkpoints\Checkpoint_12a_Direct_Fire_Commitment_And_Layered_Interception.md',
        '.\src\StarCluster.Game\README.md'
    )

    foreach ($documentationFile in $documentationFiles) {
        if (-not (Test-Path $documentationFile)) {
            throw "Required documentation file $documentationFile was not found."
        }
    }

    if (-not (Select-String -Path '.\docs\README.md' -Pattern 'Star_Cluster_Game_Concept_v0.3d.docx' -Quiet)) {
        throw 'The documentation index does not identify Concept v0.3d as current.'
    }

    if (-not (Select-String -Path '.\docs\README.md' -Pattern 'Checkpoint_12a_Direct_Fire_Commitment_And_Layered_Interception.md' -Quiet)) {
        throw 'The documentation index does not reference Checkpoint 12a.'
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
    dotnet test '.\tests\StarCluster.Tests\StarCluster.Tests.csproj' --no-build --nologo

    if ($LASTEXITCODE -ne 0) {
        throw "dotnet test failed with exit code $LASTEXITCODE."
    }

    if (Select-String -Path '.\src\StarCluster.Core\StarCluster.Core.csproj' -Pattern 'Godot' -Quiet) {
        throw 'StarCluster.Core unexpectedly contains a Godot dependency.'
    }

    Write-Host ''
    Write-Host 'Checkpoint 12a completed successfully.' -ForegroundColor Green
    Write-Host 'Expected engine-independent tests passed: 311.'
    Write-Host 'Reopen Godot and press F5. Confirm Movement -> Direct Fire -> Missile / Interception, test all four main-weapon commitments, exercise held-main-weapon plus PDS layering, complete several turns without losing Movement selection, and reset from multiple phases.'
    Write-Host 'Next candidate checkpoint: target-track quality and sensor/electronic-warfare foundations, after reviewing the local Checkpoint 12a results.'
}
finally {
    Pop-Location
}
