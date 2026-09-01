[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$repositoryRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
Push-Location $repositoryRoot

try {
    Write-Host '[1/8] Verifying the Star Cluster repository and Checkpoint 08...'

    if (-not (Test-Path '.\StarCluster.sln')) {
        throw "StarCluster.sln was not found at $repositoryRoot. Extract the package into the repository root."
    }

    $priorFiles = @(
        '.\src\StarCluster.Core\Geometry\HexCoord.cs',
        '.\src\StarCluster.Core\Maps\SystemMap.cs',
        '.\src\StarCluster.Core\Combat\DirectFireLineOfSight.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileRoutePlanner.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileSalvo.cs',
        '.\tests\StarCluster.Tests\Combat\Missiles\MissileSalvoTests.cs',
        '.\docs\checkpoints\Checkpoint_08_Missile_Routing_Foundations.md',
        '.\docs\Star_Cluster_Game_Concept_v0.3a.docx'
    )

    foreach ($priorFile in $priorFiles) {
        if (-not (Test-Path $priorFile)) {
            throw "Required Checkpoint 08 file $priorFile was not found. Apply Checkpoint 08 first."
        }
    }

    Write-Host '[2/8] Checking the pinned .NET SDK...'
    $sdkVersion = dotnet --version
    Write-Host "       SDK: $sdkVersion"

    if ($sdkVersion -ne '8.0.423') {
        throw "Expected .NET SDK 8.0.423 from global.json, but dotnet selected $sdkVersion."
    }

    Write-Host '[3/8] Verifying the Checkpoint 09 Godot project files...'

    $gameFiles = @(
        '.\src\StarCluster.Game\StarCluster.Game.csproj',
        '.\src\StarCluster.Game\project.godot',
        '.\src\StarCluster.Game\Scenes\Main.tscn',
        '.\src\StarCluster.Game\Scripts\Main.cs',
        '.\src\StarCluster.Game\Scripts\HexBoardView.cs',
        '.\src\StarCluster.Game\Scripts\DemoScenario.cs',
        '.\src\StarCluster.Game\Scripts\DemoScenarioFactory.cs',
        '.\src\StarCluster.Game\Scripts\TargetingMode.cs'
    )

    foreach ($gameFile in $gameFiles) {
        if (-not (Test-Path $gameFile)) {
            throw "$gameFile was not found. Re-extract the Checkpoint 09 package into the repository root."
        }
    }

    if (-not (Select-String -Path '.\src\StarCluster.Game\StarCluster.Game.csproj' -Pattern 'Godot.NET.Sdk/4.7.1' -Quiet)) {
        throw 'StarCluster.Game.csproj does not target Godot.NET.Sdk/4.7.1.'
    }

    if (-not (Select-String -Path '.\src\StarCluster.Game\StarCluster.Game.csproj' -Pattern 'StarCluster.Core.csproj' -Quiet)) {
        throw 'StarCluster.Game.csproj does not reference StarCluster.Core.'
    }

    Write-Host '[4/8] Adding StarCluster.Game to the solution when needed...'
    $solutionList = dotnet sln '.\StarCluster.sln' list

    if ($LASTEXITCODE -ne 0) {
        throw "dotnet sln list failed with exit code $LASTEXITCODE."
    }

    if ($solutionList -notmatch 'StarCluster.Game.csproj') {
        dotnet sln '.\StarCluster.sln' add '.\src\StarCluster.Game\StarCluster.Game.csproj'

        if ($LASTEXITCODE -ne 0) {
            throw "Could not add StarCluster.Game to the solution; exit code $LASTEXITCODE."
        }
    }
    else {
        Write-Host '       StarCluster.Game is already present in the solution.'
    }

    Write-Host '[5/8] Verifying synchronized project documentation...'

    $documentationFiles = @(
        '.\docs\README.md',
        '.\docs\Star_Cluster_Game_Concept_v0.3a.docx',
        '.\docs\checkpoints\Checkpoint_09_Godot_Presentation_Spike.md'
    )

    foreach ($documentationFile in $documentationFiles) {
        if (-not (Test-Path $documentationFile)) {
            throw "Required documentation file $documentationFile was not found."
        }
    }

    Write-Host '[6/8] Building the complete solution, including the Godot C# project...'
    Write-Host '       The first build may restore the Godot.NET.Sdk package and take longer than prior checkpoints.'
    dotnet build '.\StarCluster.sln' --nologo

    if ($LASTEXITCODE -ne 0) {
        throw "dotnet build failed with exit code $LASTEXITCODE."
    }

    Write-Host '[7/8] Running the engine-independent automated tests...'
    dotnet test '.\tests\StarCluster.Tests\StarCluster.Tests.csproj' --no-build --nologo

    if ($LASTEXITCODE -ne 0) {
        throw "dotnet test failed with exit code $LASTEXITCODE."
    }

    Write-Host '[8/8] Confirming architecture and documentation state...'

    if (-not (Select-String -Path '.\docs\README.md' -Pattern 'Checkpoint_09_Godot_Presentation_Spike.md' -Quiet)) {
        throw 'The documentation index does not reference Checkpoint 09.'
    }

    $coreProjectFile = '.\src\StarCluster.Core\StarCluster.Core.csproj'
    if (Select-String -Path $coreProjectFile -Pattern 'Godot' -Quiet) {
        throw 'StarCluster.Core unexpectedly contains a Godot dependency.'
    }

    $solutionList = dotnet sln '.\StarCluster.sln' list
    if ($solutionList -notmatch 'StarCluster.Game.csproj') {
        throw 'StarCluster.Game is still missing from StarCluster.sln.'
    }

    Write-Host ''
    Write-Host 'Checkpoint 09 completed successfully.' -ForegroundColor Green
    Write-Host 'Existing core tests passed: 208 expected.'
    Write-Host 'Next step: import .\src\StarCluster.Game\project.godot in Godot 4.7.1 .NET.'
}
finally {
    Pop-Location
}
