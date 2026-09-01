[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$repositoryRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
Push-Location $repositoryRoot

try {
    Write-Host '[1/10] Verifying the Star Cluster repository and Checkpoint 10...'

    if (-not (Test-Path '.\StarCluster.sln')) {
        throw "StarCluster.sln was not found at $repositoryRoot. Extract the package into the repository root."
    }

    $priorFiles = @(
        '.\src\StarCluster.Core\Geometry\HexCoord.cs',
        '.\src\StarCluster.Core\Maps\SystemMap.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileRoutePlanner.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileSalvo.cs',
        '.\src\StarCluster.Core\Movement\ShipMovementPlanner.cs',
        '.\src\StarCluster.Core\Combat\TacticalTurnState.cs',
        '.\src\StarCluster.Game\project.godot',
        '.\docs\checkpoints\Checkpoint_10_Tactical_Ship_Movement.md'
    )

    foreach ($priorFile in $priorFiles) {
        if (-not (Test-Path $priorFile)) {
            throw "Required prior-checkpoint file $priorFile was not found. Apply Checkpoint 10 first."
        }
    }

    Write-Host '[2/10] Confirming that Godot is closed...'
    $godotProcesses = Get-Process -ErrorAction SilentlyContinue |
        Where-Object { $_.ProcessName -like 'Godot*' }

    if ($godotProcesses) {
        $processNames = ($godotProcesses.ProcessName | Sort-Object -Unique) -join ', '
        throw "Close the Godot editor and debug window before applying Checkpoint 11. Running process(es): $processNames"
    }

    Write-Host '[3/10] Checking the pinned .NET SDK...'
    $sdkVersion = dotnet --version
    Write-Host "       SDK: $sdkVersion"

    if ($sdkVersion -ne '8.0.423') {
        throw "Expected .NET SDK 8.0.423 from global.json, but dotnet selected $sdkVersion."
    }

    Write-Host '[4/10] Verifying moving-target guidance and lifetime sources...'
    $coreFiles = @(
        '.\src\StarCluster.Core\Combat\Missiles\MissileTargetTrackQuality.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileTargetTrackSnapshot.cs',
        '.\src\StarCluster.Core\Combat\Missiles\GuidedMissileStatus.cs',
        '.\src\StarCluster.Core\Combat\Missiles\GuidedMissileAdvanceResult.cs',
        '.\src\StarCluster.Core\Combat\Missiles\GuidedMissileSalvo.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileGuidanceService.cs'
    )

    foreach ($coreFile in $coreFiles) {
        if (-not (Test-Path $coreFile)) {
            throw "Checkpoint 11 source file $coreFile was not found. Re-extract the package."
        }
    }

    if (-not (Select-String -Path '.\src\StarCluster.Core\Combat\Missiles\MissileGuidanceService.cs' -Pattern 'salvo.RemainingRange' -Quiet)) {
        throw 'MissileGuidanceService does not plan against remaining lifetime range.'
    }

    if (-not (Select-String -Path '.\src\StarCluster.Core\Combat\Missiles\MissileGuidanceService.cs' -Pattern 'WaitingForRoute' -Quiet)) {
        throw 'MissileGuidanceService does not preserve no-route waiting.'
    }

    if (-not (Select-String -Path '.\src\StarCluster.Core\Combat\Missiles\GuidedMissileSalvo.cs' -Pattern 'Profile.MaximumRange - DistanceTraveled' -Quiet)) {
        throw 'GuidedMissileSalvo does not derive remaining range from cumulative travel.'
    }

    Write-Host '[5/10] Verifying the 24 new guidance tests...'
    $testFiles = @(
        '.\tests\StarCluster.Tests\Combat\Missiles\MissileTargetTrackSnapshotTests.cs',
        '.\tests\StarCluster.Tests\Combat\Missiles\GuidedMissileSalvoTests.cs',
        '.\tests\StarCluster.Tests\Combat\Missiles\MissileGuidanceServiceTests.cs'
    )

    foreach ($testFile in $testFiles) {
        if (-not (Test-Path $testFile)) {
            throw "Checkpoint 11 test file $testFile was not found."
        }
    }

    $factCount = (Select-String -Path $testFiles -Pattern '\[Fact\]' -AllMatches).Matches.Count
    if ($factCount -ne 24) {
        throw "Expected 24 new [Fact] tests, but found $factCount."
    }

    if (-not (Select-String -Path '.\tests\StarCluster.Tests\Combat\Missiles\MissileGuidanceServiceTests.cs' -Pattern 'FasterTargetCanOutrun' -Quiet)) {
        throw 'The faster-target pursuit regression test is missing.'
    }

    Write-Host '[6/10] Verifying the Godot guidance, reset, and movement guard...'
    $gameFiles = @(
        '.\src\StarCluster.Game\Scripts\DemoScenario.cs',
        '.\src\StarCluster.Game\Scripts\HexBoardView.cs',
        '.\src\StarCluster.Game\Scripts\Main.cs',
        '.\src\StarCluster.Game\Scripts\TargetingMode.cs'
    )

    foreach ($gameFile in $gameFiles) {
        if (-not (Test-Path $gameFile)) {
            throw "Checkpoint 11 Godot file $gameFile was not found."
        }
    }

    if (-not (Select-String -Path '.\src\StarCluster.Game\Scripts\Main.cs' -Pattern 'ResetCurrentScenario' -Quiet)) {
        throw 'Main.cs does not contain the complete scenario reset workflow.'
    }

    if (-not (Select-String -Path '.\src\StarCluster.Game\Scripts\Main.cs' -Pattern '_advancePhaseButton.Disabled = unresolvedMovement' -Quiet)) {
        throw 'Main.cs does not prevent accidental advancement from unresolved Movement.'
    }

    if (-not (Select-String -Path '.\src\StarCluster.Game\Scripts\Main.cs' -Pattern 'MissileGuidanceService.AdvanceOnePhase' -Quiet)) {
        throw 'Main.cs does not invoke engine-independent moving-target guidance.'
    }

    if (-not (Select-String -Path '.\src\StarCluster.Game\Scripts\HexBoardView.cs' -Pattern 'GuidedMissileSalvo' -Quiet)) {
        throw 'HexBoardView does not display the guided salvo state.'
    }

    Write-Host '[7/10] Verifying synchronized Checkpoint 11 documentation...'
    $documentationFiles = @(
        '.\docs\README.md',
        '.\docs\Star_Cluster_Game_Concept_v0.3b.docx',
        '.\docs\archive\Star_Cluster_Game_Concept_v0.3a.docx',
        '.\docs\checkpoints\Checkpoint_11_Moving_Target_Missile_Guidance.md',
        '.\src\StarCluster.Game\README.md'
    )

    foreach ($documentationFile in $documentationFiles) {
        if (-not (Test-Path $documentationFile)) {
            throw "Required documentation file $documentationFile was not found."
        }
    }

    if (-not (Select-String -Path '.\docs\README.md' -Pattern 'Star_Cluster_Game_Concept_v0.3b.docx' -Quiet)) {
        throw 'The documentation index does not identify Concept v0.3b as current.'
    }

    if (-not (Select-String -Path '.\docs\README.md' -Pattern 'Checkpoint_11_Moving_Target_Missile_Guidance.md' -Quiet)) {
        throw 'The documentation index does not reference Checkpoint 11.'
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
    Write-Host 'Checkpoint 11 completed successfully.' -ForegroundColor Green
    Write-Host 'Expected engine-independent tests passed: 256.'
    Write-Host 'Reopen Godot and press F5. Confirm movement must be resolved before phase advance, launch an incoming missile, move the player on later turns, advance guidance, and test Reset map / scenario from multiple phases.'
    Write-Host 'Next candidate checkpoint: interception foundations or target-track quality, after reviewing the Checkpoint 11 local results.'
}
finally {
    Pop-Location
}
