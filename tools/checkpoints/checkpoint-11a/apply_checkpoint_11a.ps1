[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$repositoryRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
Push-Location $repositoryRoot

try {
    Write-Host '[1/10] Verifying the Star Cluster repository and Checkpoint 11...'

    if (-not (Test-Path '.\StarCluster.sln')) {
        throw "StarCluster.sln was not found at $repositoryRoot. Extract the package into the repository root."
    }

    $priorFiles = @(
        '.\src\StarCluster.Core\Combat\Missiles\GuidedMissileSalvo.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileGuidanceService.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileTargetTrackSnapshot.cs',
        '.\src\StarCluster.Game\Scripts\Main.cs',
        '.\src\StarCluster.Game\project.godot',
        '.\docs\checkpoints\Checkpoint_11_Moving_Target_Missile_Guidance.md'
    )

    foreach ($priorFile in $priorFiles) {
        if (-not (Test-Path $priorFile)) {
            throw "Required prior-checkpoint file $priorFile was not found. Apply Checkpoint 11 first."
        }
    }

    Write-Host '[2/10] Confirming that Godot is closed...'
    $godotProcesses = Get-Process -ErrorAction SilentlyContinue |
        Where-Object { $_.ProcessName -like 'Godot*' }

    if ($godotProcesses) {
        $processNames = ($godotProcesses.ProcessName | Sort-Object -Unique) -join ', '
        throw "Close the Godot editor and debug window before applying Checkpoint 11a. Running process(es): $processNames"
    }

    Write-Host '[3/10] Checking the pinned .NET SDK...'
    $sdkVersion = dotnet --version
    Write-Host "       SDK: $sdkVersion"

    if ($sdkVersion -ne '8.0.423') {
        throw "Expected .NET SDK 8.0.423 from global.json, but dotnet selected $sdkVersion."
    }

    Write-Host '[4/10] Verifying the single-phase missile launch operation...'
    $launchFiles = @(
        '.\src\StarCluster.Core\Combat\Missiles\GuidedMissileLaunchResult.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileLaunchService.cs'
    )

    foreach ($launchFile in $launchFiles) {
        if (-not (Test-Path $launchFile)) {
            throw "Checkpoint 11a source file $launchFile was not found. Re-extract the package."
        }
    }

    if (-not (Select-String -Path '.\src\StarCluster.Core\Combat\Missiles\MissileLaunchService.cs' -Pattern 'LaunchAndAdvanceOnePhase' -Quiet)) {
        throw 'MissileLaunchService does not expose the atomic launch operation.'
    }

    if (-not (Select-String -Path '.\src\StarCluster.Core\Combat\Missiles\MissileLaunchService.cs' -Pattern 'MissileGuidanceService.AdvanceOnePhase' -Quiet)) {
        throw 'MissileLaunchService does not delegate to one guidance advance.'
    }

    if (Select-String -Path '.\src\StarCluster.Core\Combat\Missiles\MissileLaunchService.cs' -Pattern '\bwhile\b|\bfor\s*\(' -Quiet) {
        throw 'MissileLaunchService unexpectedly contains iteration and may fast-forward multiple phases.'
    }

    Write-Host '[5/10] Verifying the five new launch regression tests...'
    $launchTest = '.\tests\StarCluster.Tests\Combat\Missiles\MissileLaunchServiceTests.cs'

    if (-not (Test-Path $launchTest)) {
        throw "Checkpoint 11a test file $launchTest was not found."
    }

    $factCount = (Select-String -Path $launchTest -Pattern '\[Fact\]' -AllMatches).Matches.Count
    if ($factCount -ne 5) {
        throw "Expected 5 new [Fact] tests, but found $factCount."
    }

    if (-not (Select-String -Path $launchTest -Pattern 'LongRouteRemainsInFlightAfterOnlyOneLaunchAdvance' -Quiet)) {
        throw 'The long-route no-fast-forward regression test is missing.'
    }

    if (-not (Select-String -Path $launchTest -Pattern 'LaunchServiceNeverFastForwardsBeyondMissileSpeed' -Quiet)) {
        throw 'The one-phase launch speed-bound regression test is missing.'
    }

    Write-Host '[6/10] Verifying the Godot one-phase controls and phase guard...'
    $mainFile = '.\src\StarCluster.Game\Scripts\Main.cs'
    $boardFile = '.\src\StarCluster.Game\Scripts\HexBoardView.cs'

    if (-not (Select-String -Path $mainFile -Pattern 'Launch \+ advance once' -Quiet)) {
        throw 'Main.cs does not clearly label the one-phase launch action.'
    }

    if (-not (Select-String -Path $mainFile -Pattern 'MissileLaunchService.LaunchAndAdvanceOnePhase' -Quiet)) {
        throw 'Main.cs does not use the atomic launch-and-one-advance operation.'
    }

    if (-not (Select-String -Path $mainFile -Pattern 'later missile phases were not simulated' -Quiet)) {
        throw 'Main.cs does not explicitly report that no fast-forward occurred.'
    }

    if (-not (Select-String -Path $mainFile -Pattern 'unresolvedActiveMissile' -Quiet)) {
        throw 'Main.cs does not guard against skipping an active missile phase.'
    }

    if (-not (Select-String -Path $boardFile -Pattern 'GuidedMissileStatus.Arrived' -Quiet)) {
        throw 'HexBoardView does not distinguish an impact marker.'
    }

    Write-Host '[7/10] Verifying synchronized Checkpoint 11a documentation...'
    $documentationFiles = @(
        '.\docs\README.md',
        '.\docs\Star_Cluster_Game_Concept_v0.3b.docx',
        '.\docs\checkpoints\Checkpoint_11_Moving_Target_Missile_Guidance.md',
        '.\docs\checkpoints\Checkpoint_11a_Turn_By_Turn_Missile_Presentation_Hotfix.md',
        '.\src\StarCluster.Game\README.md'
    )

    foreach ($documentationFile in $documentationFiles) {
        if (-not (Test-Path $documentationFile)) {
            throw "Required documentation file $documentationFile was not found."
        }
    }

    if (-not (Select-String -Path '.\docs\README.md' -Pattern 'Checkpoint_11a_Turn_By_Turn_Missile_Presentation_Hotfix.md' -Quiet)) {
        throw 'The documentation index does not reference Checkpoint 11a.'
    }

    if (-not (Select-String -Path '.\docs\README.md' -Pattern 'Star_Cluster_Game_Concept_v0.3b.docx' -Quiet)) {
        throw 'The documentation index no longer identifies Concept v0.3b as current.'
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
    Write-Host 'Checkpoint 11a completed successfully.' -ForegroundColor Green
    Write-Host 'Expected engine-independent tests passed: 261.'
    Write-Host 'Reopen Godot and press F5. In the blocked-fire scenario, launch around the star and confirm exactly one two-hex advance occurs, the missile remains in flight, and later turns each require one Advance once command.'
    Write-Host 'After local acceptance, the next candidate checkpoint remains interception foundations or target-track quality.'
}
finally {
    Pop-Location
}
