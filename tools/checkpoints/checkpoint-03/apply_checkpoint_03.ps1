[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$repositoryRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
Push-Location $repositoryRoot

try {
    Write-Host '[1/5] Verifying the Star Cluster repository and Checkpoint 02...'

    if (-not (Test-Path '.\StarCluster.sln')) {
        throw "StarCluster.sln was not found at $repositoryRoot. Extract the package into the repository root."
    }

    if (-not (Test-Path '.\src\StarCluster.Core\Geometry\HexCoord.cs')) {
        throw 'Checkpoint 02 HexCoord.cs was not found. Apply Checkpoint 02 first.'
    }

    if (-not (Test-Path '.\tests\StarCluster.Tests\Geometry\HexCoordTests.cs')) {
        throw 'Checkpoint 02 HexCoordTests.cs was not found. Apply Checkpoint 02 first.'
    }

    Write-Host '[2/5] Checking the pinned .NET SDK...'
    $sdkVersion = dotnet --version
    Write-Host "       SDK: $sdkVersion"

    if ($sdkVersion -ne '8.0.423') {
        throw "Expected .NET SDK 8.0.423 from global.json, but dotnet selected $sdkVersion."
    }

    Write-Host '[3/5] Verifying the new Checkpoint 03 source files...'

    if (-not (Test-Path '.\src\StarCluster.Core\Geometry\HexGeometry.cs')) {
        throw 'HexGeometry.cs was not found. Re-extract the Checkpoint 03 package into the repository root.'
    }

    if (-not (Test-Path '.\tests\StarCluster.Tests\Geometry\HexGeometryTests.cs')) {
        throw 'HexGeometryTests.cs was not found. Re-extract the Checkpoint 03 package into the repository root.'
    }

    Write-Host '[4/5] Building the solution...'
    dotnet build '.\StarCluster.sln' --nologo

    if ($LASTEXITCODE -ne 0) {
        throw "dotnet build failed with exit code $LASTEXITCODE."
    }

    Write-Host '[5/5] Running the automated tests...'
    dotnet test '.\StarCluster.sln' --no-build --nologo

    if ($LASTEXITCODE -ne 0) {
        throw "dotnet test failed with exit code $LASTEXITCODE."
    }

    Write-Host ''
    Write-Host 'Checkpoint 03 completed successfully.' -ForegroundColor Green
}
finally {
    Pop-Location
}
