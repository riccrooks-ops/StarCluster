[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$repositoryRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
Push-Location $repositoryRoot

try {
    Write-Host '[1/10] Verifying the Star Cluster repository and Checkpoint 11a...'

    if (-not (Test-Path '.\StarCluster.sln')) {
        throw "StarCluster.sln was not found at $repositoryRoot. Extract the package into the repository root."
    }

    $priorFiles = @(
        '.\src\StarCluster.Core\Combat\Missiles\GuidedMissileSalvo.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileGuidanceService.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileLaunchService.cs',
        '.\src\StarCluster.Game\Scripts\Main.cs',
        '.\src\StarCluster.Game\Scripts\HexBoardView.cs',
        '.\docs\checkpoints\Checkpoint_11a_Turn_By_Turn_Missile_Presentation_Hotfix.md'
    )

    foreach ($priorFile in $priorFiles) {
        if (-not (Test-Path $priorFile)) {
            throw "Required prior-checkpoint file $priorFile was not found. Apply Checkpoint 11a first."
        }
    }

    Write-Host '[2/10] Confirming that Godot is closed...'
    $godotProcesses = Get-Process -ErrorAction SilentlyContinue |
        Where-Object { $_.ProcessName -like 'Godot*' }

    if ($godotProcesses) {
        $processNames = ($godotProcesses.ProcessName | Sort-Object -Unique) -join ', '
        throw "Close the Godot editor and debug window before applying Checkpoint 12. Running process(es): $processNames"
    }

    Write-Host '[3/10] Checking the pinned .NET SDK...'
    $sdkVersion = dotnet --version
    Write-Host "       SDK: $sdkVersion"

    if ($sdkVersion -ne '8.0.423') {
        throw "Expected .NET SDK 8.0.423 from global.json, but dotnet selected $sdkVersion."
    }

    Write-Host '[4/10] Verifying ownership, multi-salvo, and interception sources...'
    $coreFiles = @(
        '.\src\StarCluster.Core\Combat\TacticalSide.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileEngagementState.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileDefenseProfile.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileDefenseSystem.cs',
        '.\src\StarCluster.Core\Combat\Missiles\IMissileInterceptionResolver.cs',
        '.\src\StarCluster.Core\Combat\Missiles\FixedMissileInterceptionResolver.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileInterceptionAttempt.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileInterceptionAttemptResult.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileInterceptionOutcome.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileInterceptionPhaseContext.cs'
    )

    foreach ($coreFile in $coreFiles) {
        if (-not (Test-Path $coreFile)) {
            throw "Checkpoint 12 source file $coreFile was not found. Re-extract the package."
        }
    }

    if (-not (Select-String -Path '.\src\StarCluster.Core\Combat\Missiles\GuidedMissileSalvo.cs' -Pattern 'OwnerSide' -Quiet)) {
        throw 'GuidedMissileSalvo does not record explicit ownership.'
    }

    if (-not (Select-String -Path '.\src\StarCluster.Core\Combat\Missiles\GuidedMissileSalvo.cs' -Pattern 'TravelHistory' -Quiet)) {
        throw 'GuidedMissileSalvo does not preserve cumulative travel history.'
    }

    if (-not (Select-String -Path '.\src\StarCluster.Core\Combat\Missiles\MissileGuidanceService.cs' -Pattern 'interceptionContext.ResolveAt' -Quiet)) {
        throw 'MissileGuidanceService does not perform stepwise interception checks.'
    }

    if (-not (Select-String -Path '.\src\StarCluster.Core\Combat\Missiles\MissileGuidanceService.cs' -Pattern 'finalApproach' -Quiet)) {
        throw 'MissileGuidanceService does not preserve a final interception opportunity before impact.'
    }

    Write-Host '[5/10] Verifying the 32 new ownership and interception tests...'
    $newTestFiles = @(
        '.\tests\StarCluster.Tests\Combat\Missiles\GuidedMissileOwnershipTests.cs',
        '.\tests\StarCluster.Tests\Combat\Missiles\MissileDefenseProfileTests.cs',
        '.\tests\StarCluster.Tests\Combat\Missiles\MissileEngagementStateTests.cs',
        '.\tests\StarCluster.Tests\Combat\Missiles\MissileInterceptionPhaseContextTests.cs',
        '.\tests\StarCluster.Tests\Combat\Missiles\MissileGuidanceInterceptionTests.cs'
    )

    foreach ($testFile in $newTestFiles) {
        if (-not (Test-Path $testFile)) {
            throw "Checkpoint 12 test file $testFile was not found."
        }
    }

    $newFactCount = 0
    foreach ($testFile in $newTestFiles) {
        $newFactCount += (Select-String -Path $testFile -Pattern '\[Fact\]' -AllMatches).Matches.Count
    }

    if ($newFactCount -ne 32) {
        throw "Expected 32 new [Fact] tests, but found $newFactCount."
    }

    if (-not (Select-String -Path '.\tests\StarCluster.Tests\Combat\Missiles\MissileGuidanceInterceptionTests.cs' -Pattern 'FastMissileCannotSkipShortDefenseEnvelope' -Quiet)) {
        throw 'The fast-missile short-envelope regression test is missing.'
    }

    if (-not (Select-String -Path '.\tests\StarCluster.Tests\Combat\Missiles\MissileGuidanceInterceptionTests.cs' -Pattern 'FinalInterceptionOccursBeforeImpact' -Quiet)) {
        throw 'The final-opportunity-before-impact regression test is missing.'
    }

    Write-Host '[6/10] Verifying Godot ownership, target selection, and multi-salvo controls...'
    $mainFile = '.\src\StarCluster.Game\Scripts\Main.cs'
    $boardFile = '.\src\StarCluster.Game\Scripts\HexBoardView.cs'

    $mainPatterns = @(
        'Launch player missile',
        'Launch enemy at player',
        'Advance unresolved salvos once',
        'Demonstration interception succeeds',
        'MissileEngagementState',
        'TacticalSide.Player',
        'TacticalSide.Enemy'
    )

    foreach ($pattern in $mainPatterns) {
        if (-not (Select-String -Path $mainFile -Pattern ([regex]::Escape($pattern)) -Quiet)) {
            throw "Main.cs is missing required Checkpoint 12 presentation text or state: $pattern"
        }
    }

    if (-not (Select-String -Path $boardFile -Pattern 'TacticalSide.Player => "F"' -Quiet)) {
        throw 'HexBoardView does not provide the non-color friendly F marker.'
    }

    if (-not (Select-String -Path $boardFile -Pattern 'TacticalSide.Enemy => "E"' -Quiet)) {
        throw 'HexBoardView does not provide the non-color enemy E marker.'
    }

    if (-not (Select-String -Path $boardFile -Pattern 'TravelHistory' -Quiet)) {
        throw 'HexBoardView does not draw the cumulative traveled trail.'
    }

    Write-Host '[7/10] Verifying Concept v0.3c and synchronized documentation...'
    $documentationFiles = @(
        '.\docs\README.md',
        '.\docs\Star_Cluster_Game_Concept_v0.3c.docx',
        '.\docs\archive\Star_Cluster_Game_Concept_v0.3b.docx',
        '.\docs\checkpoints\Checkpoint_12_Missile_Ownership_And_Interception_Foundations.md',
        '.\src\StarCluster.Game\README.md'
    )

    foreach ($documentationFile in $documentationFiles) {
        if (-not (Test-Path $documentationFile)) {
            throw "Required documentation file $documentationFile was not found."
        }
    }

    if (-not (Select-String -Path '.\docs\README.md' -Pattern 'Star_Cluster_Game_Concept_v0.3c.docx' -Quiet)) {
        throw 'The documentation index does not identify Concept v0.3c as current.'
    }

    if (-not (Select-String -Path '.\docs\README.md' -Pattern 'Checkpoint_12_Missile_Ownership_And_Interception_Foundations.md' -Quiet)) {
        throw 'The documentation index does not reference Checkpoint 12.'
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

    Write-Host '[9/10] Building the complete solution...'
    dotnet build '.\StarCluster.sln' --nologo

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
    Write-Host 'Checkpoint 12 completed successfully.' -ForegroundColor Green
    Write-Host 'Expected engine-independent tests passed: 293.'
    Write-Host 'Reopen Godot and press F5. Select the red ship as the player missile target, launch green and red salvos, advance unresolved salvos once per phase, exercise both deterministic interception outcomes, and reset from several phases.'
    Write-Host 'Next candidate checkpoint: target-track quality and sensor/electronic-warfare foundations, after reviewing the local Checkpoint 12 results.'
}
finally {
    Pop-Location
}
