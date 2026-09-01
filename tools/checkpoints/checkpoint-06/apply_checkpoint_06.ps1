[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$repositoryRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
Push-Location $repositoryRoot

try {
    Write-Host '[1/6] Verifying the Star Cluster repository and prior checkpoints...'

    if (-not (Test-Path '.\StarCluster.sln')) {
        throw "StarCluster.sln was not found at $repositoryRoot. Extract the package into the repository root."
    }

    $priorFiles = @(
        '.\src\StarCluster.Core\Geometry\HexCoord.cs',
        '.\src\StarCluster.Core\Maps\HexMap.cs',
        '.\src\StarCluster.Core\Maps\MapDefaults.cs',
        '.\src\StarCluster.Core\Maps\MapCell.cs',
        '.\src\StarCluster.Core\Maps\MapObjectKind.cs',
        '.\src\StarCluster.Core\Maps\MapTerrain.cs',
        '.\src\StarCluster.Core\Maps\SystemMap.cs'
    )

    foreach ($priorFile in $priorFiles) {
        if (-not (Test-Path $priorFile)) {
            throw "Required prior-checkpoint file $priorFile was not found. Apply Checkpoints 02 through 05 first."
        }
    }

    Write-Host '[2/6] Checking the pinned .NET SDK...'
    $sdkVersion = dotnet --version
    Write-Host "       SDK: $sdkVersion"

    if ($sdkVersion -ne '8.0.423') {
        throw "Expected .NET SDK 8.0.423 from global.json, but dotnet selected $sdkVersion."
    }

    Write-Host '[3/6] Verifying the Checkpoint 06 line-of-sight source files...'

    $requiredFiles = @(
        '.\src\StarCluster.Core\Geometry\HexGeometry.cs',
        '.\src\StarCluster.Core\Maps\MapObject.cs',
        '.\src\StarCluster.Core\Combat\LineOfSightBlocker.cs',
        '.\src\StarCluster.Core\Combat\DirectFireLineOfSightResult.cs',
        '.\src\StarCluster.Core\Combat\DirectFireLineOfSight.cs',
        '.\tests\StarCluster.Tests\Geometry\HexSupercoverLineTests.cs',
        '.\tests\StarCluster.Tests\Maps\MapObjectDirectFireTests.cs',
        '.\tests\StarCluster.Tests\Combat\DirectFireLineOfSightTests.cs'
    )

    foreach ($requiredFile in $requiredFiles) {
        if (-not (Test-Path $requiredFile)) {
            throw "$requiredFile was not found. Re-extract the Checkpoint 06 package into the repository root."
        }
    }

    Write-Host '[4/6] Verifying synchronized project documentation...'

    if (-not (Test-Path '.\docs\Star_Cluster_Game_Concept_v0.3.docx')) {
        throw 'The current v0.3 concept document was not found in the docs folder.'
    }

    if (-not (Test-Path '.\docs\checkpoints\Checkpoint_06_Direct_Fire_Line_Of_Sight.md')) {
        throw 'The Checkpoint 06 documentation file was not found.'
    }

    Write-Host '[5/6] Building the solution...'
    dotnet build '.\StarCluster.sln' --nologo

    if ($LASTEXITCODE -ne 0) {
        throw "dotnet build failed with exit code $LASTEXITCODE."
    }

    Write-Host '[6/6] Running the automated tests...'
    dotnet test '.\StarCluster.sln' --no-build --nologo

    if ($LASTEXITCODE -ne 0) {
        throw "dotnet test failed with exit code $LASTEXITCODE."
    }

    Write-Host ''
    Write-Host 'Checkpoint 06 completed successfully.' -ForegroundColor Green
}
finally {
    Pop-Location
}
