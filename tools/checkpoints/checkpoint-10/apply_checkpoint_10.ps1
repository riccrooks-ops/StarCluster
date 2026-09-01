[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$repositoryRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
Push-Location $repositoryRoot

try {
    Write-Host '[1/10] Verifying the Star Cluster repository and Checkpoint 09a...'

    if (-not (Test-Path '.\StarCluster.sln')) {
        throw "StarCluster.sln was not found at $repositoryRoot. Extract the package into the repository root."
    }

    $priorFiles = @(
        '.\src\StarCluster.Core\Geometry\HexCoord.cs',
        '.\src\StarCluster.Core\Maps\SystemMap.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileRoutePlanner.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileSalvo.cs',
        '.\src\StarCluster.Game\project.godot',
        '.\src\StarCluster.Game\Scripts\HexBoardView.cs',
        '.\docs\checkpoints\Checkpoint_09a_Godot_Layout_Hotfix.md'
    )

    foreach ($priorFile in $priorFiles) {
        if (-not (Test-Path $priorFile)) {
            throw "Required prior-checkpoint file $priorFile was not found. Apply Checkpoint 09a first."
        }
    }

    Write-Host '[2/10] Confirming that Godot is closed...'
    $godotProcesses = Get-Process -ErrorAction SilentlyContinue |
        Where-Object { $_.ProcessName -like 'Godot*' }

    if ($godotProcesses) {
        $processNames = ($godotProcesses.ProcessName | Sort-Object -Unique) -join ', '
        throw "Close the Godot editor and debug window before applying Checkpoint 10. Running process(es): $processNames"
    }

    Write-Host '[3/10] Checking the pinned .NET SDK...'
    $sdkVersion = dotnet --version
    Write-Host "       SDK: $sdkVersion"

    if ($sdkVersion -ne '8.0.423') {
        throw "Expected .NET SDK 8.0.423 from global.json, but dotnet selected $sdkVersion."
    }

    Write-Host '[4/10] Verifying the engine-independent movement and turn sources...'
    $coreFiles = @(
        '.\src\StarCluster.Core\Movement\SublightMovementProfile.cs',
        '.\src\StarCluster.Core\Movement\ShipMovementStatus.cs',
        '.\src\StarCluster.Core\Movement\ShipMovementRoute.cs',
        '.\src\StarCluster.Core\Movement\ShipMovementResult.cs',
        '.\src\StarCluster.Core\Movement\ShipMovementPlanner.cs',
        '.\src\StarCluster.Core\Movement\ShipMovementExecutionStatus.cs',
        '.\src\StarCluster.Core\Movement\ShipMovementExecutionResult.cs',
        '.\src\StarCluster.Core\Movement\ShipMovementService.cs',
        '.\src\StarCluster.Core\Combat\TacticalTurnPhase.cs',
        '.\src\StarCluster.Core\Combat\TacticalTurnState.cs'
    )

    foreach ($coreFile in $coreFiles) {
        if (-not (Test-Path $coreFile)) {
            throw "Checkpoint 10 source file $coreFile was not found. Re-extract the package."
        }
    }

    if (-not (Select-String -Path '.\src\StarCluster.Core\Movement\ShipMovementPlanner.cs' -Pattern 'FindLegalDestinations' -Quiet)) {
        throw 'ShipMovementPlanner does not contain legal-destination enumeration.'
    }

    if (-not (Select-String -Path '.\src\StarCluster.Core\Movement\ShipMovementService.cs' -Pattern 'map.Move' -Quiet)) {
        throw 'ShipMovementService does not commit through SystemMap.Move.'
    }

    if (-not (Select-String -Path '.\src\StarCluster.Core\Combat\TacticalTurnPhase.cs' -Pattern 'MissileAndInterception' -Quiet)) {
        throw 'The tactical phase sequence is incomplete.'
    }

    Write-Host '[5/10] Verifying the 24 new movement and phase tests...'
    $testFiles = @(
        '.\tests\StarCluster.Tests\Movement\SublightMovementProfileTests.cs',
        '.\tests\StarCluster.Tests\Movement\ShipMovementPlannerTests.cs',
        '.\tests\StarCluster.Tests\Combat\TacticalTurnStateTests.cs'
    )

    foreach ($testFile in $testFiles) {
        if (-not (Test-Path $testFile)) {
            throw "Checkpoint 10 test file $testFile was not found."
        }
    }

    $factCount = (Select-String -Path $testFiles -Pattern '\[Fact\]' -AllMatches).Matches.Count
    if ($factCount -ne 24) {
        throw "Expected 24 new [Fact] tests, but found $factCount."
    }

    Write-Host '[6/10] Verifying the Godot movement presentation...'
    $gameFiles = @(
        '.\src\StarCluster.Game\Scripts\DemoScenario.cs',
        '.\src\StarCluster.Game\Scripts\HexBoardView.cs',
        '.\src\StarCluster.Game\Scripts\Main.cs',
        '.\src\StarCluster.Game\Scripts\TargetingMode.cs'
    )

    foreach ($gameFile in $gameFiles) {
        if (-not (Test-Path $gameFile)) {
            throw "Checkpoint 10 Godot file $gameFile was not found."
        }
    }

    if (-not (Select-String -Path '.\src\StarCluster.Game\Scripts\HexBoardView.cs' -Pattern 'DrawMovementOverlay' -Quiet)) {
        throw 'HexBoardView does not contain the movement overlay.'
    }

    if (-not (Select-String -Path '.\src\StarCluster.Game\Scripts\Main.cs' -Pattern 'CommitPlayerMovement' -Quiet)) {
        throw 'Main.cs does not contain the committed movement workflow.'
    }

    if (-not (Select-String -Path '.\src\StarCluster.Game\Scripts\Main.cs' -Pattern 'AdvanceTacticalPhase' -Quiet)) {
        throw 'Main.cs does not expose tactical phase advancement.'
    }

    Write-Host '[7/10] Verifying Concept v0.3b and synchronized documentation...'
    $documentationFiles = @(
        '.\docs\README.md',
        '.\docs\Star_Cluster_Game_Concept_v0.3b.docx',
        '.\docs\archive\Star_Cluster_Game_Concept_v0.3a.docx',
        '.\docs\checkpoints\Checkpoint_10_Tactical_Ship_Movement.md'
    )

    foreach ($documentationFile in $documentationFiles) {
        if (-not (Test-Path $documentationFile)) {
            throw "Required documentation file $documentationFile was not found."
        }
    }

    if (-not (Select-String -Path '.\docs\README.md' -Pattern 'Star_Cluster_Game_Concept_v0.3b.docx' -Quiet)) {
        throw 'The documentation index does not identify Concept v0.3b as current.'
    }

    if (-not (Select-String -Path '.\docs\README.md' -Pattern 'Checkpoint_10_Tactical_Ship_Movement.md' -Quiet)) {
        throw 'The documentation index does not reference Checkpoint 10.'
    }

    Remove-Item '.\docs\Star_Cluster_Game_Concept_v0.3a.docx' -Force -ErrorAction SilentlyContinue

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
    Write-Host 'Checkpoint 10 completed successfully.' -ForegroundColor Green
    Write-Host 'Expected engine-independent tests passed: 232.'
    Write-Host 'Reopen the Godot project and press F5. Select Ship movement, preview and commit routes, hold position, and advance the tactical phase cursor.'
    Write-Host 'Next checkpoint: moving-target missile guidance with cumulative range and no-route waiting.'
}
finally {
    Pop-Location
}
