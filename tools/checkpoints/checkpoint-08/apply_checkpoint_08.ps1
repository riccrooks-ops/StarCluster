[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$repositoryRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
Push-Location $repositoryRoot

try {
    Write-Host '[1/7] Verifying the Star Cluster repository and Checkpoint 07...'

    if (-not (Test-Path '.\StarCluster.sln')) {
        throw "StarCluster.sln was not found at $repositoryRoot. Extract the package into the repository root."
    }

    $priorFiles = @(
        '.\src\StarCluster.Core\Geometry\HexCoord.cs',
        '.\src\StarCluster.Core\Maps\HexMap.cs',
        '.\src\StarCluster.Core\Maps\SystemMap.cs',
        '.\src\StarCluster.Core\Combat\DirectFireLineOfSight.cs',
        '.\src\StarCluster.Core\Combat\LineOfSightGrazing.cs',
        '.\docs\checkpoints\Checkpoint_07_Grazing_Line_Of_Sight.md',
        '.\docs\Star_Cluster_Game_Concept_v0.3a.docx'
    )

    foreach ($priorFile in $priorFiles) {
        if (-not (Test-Path $priorFile)) {
            throw "Required Checkpoint 07 file $priorFile was not found. Apply Checkpoint 07 first."
        }
    }

    Write-Host '[2/7] Checking the pinned .NET SDK...'
    $sdkVersion = dotnet --version
    Write-Host "       SDK: $sdkVersion"

    if ($sdkVersion -ne '8.0.423') {
        throw "Expected .NET SDK 8.0.423 from global.json, but dotnet selected $sdkVersion."
    }

    Write-Host '[3/7] Verifying the Checkpoint 08 missile source files...'

    $requiredFiles = @(
        '.\src\StarCluster.Core\Maps\MapObject.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileRouteStatus.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileRoute.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileRouteResult.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileRoutePlanner.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileFlightProfile.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileAdvanceResult.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileSalvo.cs',
        '.\tests\StarCluster.Tests\Combat\Missiles\MissileRoutePlannerTests.cs',
        '.\tests\StarCluster.Tests\Combat\Missiles\MissileFlightProfileTests.cs',
        '.\tests\StarCluster.Tests\Combat\Missiles\MissileSalvoTests.cs',
        '.\tests\StarCluster.Tests\Maps\MapObjectMissileTests.cs'
    )

    foreach ($requiredFile in $requiredFiles) {
        if (-not (Test-Path $requiredFile)) {
            throw "$requiredFile was not found. Re-extract the Checkpoint 08 package into the repository root."
        }
    }

    Write-Host '[4/7] Verifying synchronized project documentation...'

    $documentationFiles = @(
        '.\docs\README.md',
        '.\docs\Star_Cluster_Game_Concept_v0.3a.docx',
        '.\docs\checkpoints\Checkpoint_08_Missile_Routing_Foundations.md'
    )

    foreach ($documentationFile in $documentationFiles) {
        if (-not (Test-Path $documentationFile)) {
            throw "Required documentation file $documentationFile was not found."
        }
    }

    Write-Host '[5/7] Building the solution...'
    dotnet build '.\StarCluster.sln' --nologo

    if ($LASTEXITCODE -ne 0) {
        throw "dotnet build failed with exit code $LASTEXITCODE."
    }

    Write-Host '[6/7] Running the automated tests...'
    dotnet test '.\StarCluster.sln' --no-build --nologo

    if ($LASTEXITCODE -ne 0) {
        throw "dotnet test failed with exit code $LASTEXITCODE."
    }

    Write-Host '[7/7] Confirming the Checkpoint 08 documentation state...'

    if (-not (Select-String -Path '.\docs\README.md' -Pattern 'Checkpoint_08_Missile_Routing_Foundations.md' -Quiet)) {
        throw 'The documentation index does not reference Checkpoint 08.'
    }

    Write-Host ''
    Write-Host 'Checkpoint 08 completed successfully.' -ForegroundColor Green
    Write-Host 'Current concept: .\docs\Star_Cluster_Game_Concept_v0.3a.docx'
}
finally {
    Pop-Location
}
