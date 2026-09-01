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

    if (-not (Test-Path '.\src\StarCluster.Core\Geometry\HexCoord.cs')) {
        throw 'Checkpoint 02 HexCoord.cs was not found. Apply Checkpoint 02 first.'
    }

    if (-not (Test-Path '.\src\StarCluster.Core\Geometry\HexGeometry.cs')) {
        throw 'Checkpoint 03 HexGeometry.cs was not found. Apply Checkpoint 03 first.'
    }

    Write-Host '[2/6] Checking the pinned .NET SDK...'
    $sdkVersion = dotnet --version
    Write-Host "       SDK: $sdkVersion"

    if ($sdkVersion -ne '8.0.423') {
        throw "Expected .NET SDK 8.0.423 from global.json, but dotnet selected $sdkVersion."
    }

    Write-Host '[3/6] Verifying the Checkpoint 04 map source files...'

    $requiredFiles = @(
        '.\src\StarCluster.Core\Maps\HexMap.cs',
        '.\src\StarCluster.Core\Maps\MapDefaults.cs',
        '.\tests\StarCluster.Tests\Maps\HexMapTests.cs'
    )

    foreach ($requiredFile in $requiredFiles) {
        if (-not (Test-Path $requiredFile)) {
            throw "$requiredFile was not found. Re-extract the Checkpoint 04 package into the repository root."
        }
    }

    Write-Host '[4/6] Verifying synchronized project documentation...'

    if (-not (Test-Path '.\docs\Star_Cluster_Game_Concept_v0.3.docx')) {
        throw 'The current v0.3 concept document was not found in the docs folder.'
    }

    if (-not (Test-Path '.\docs\checkpoints\Checkpoint_04_Finite_Hex_Maps.md')) {
        throw 'The Checkpoint 04 documentation file was not found.'
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
    Write-Host 'Checkpoint 04 completed successfully.' -ForegroundColor Green
}
finally {
    Pop-Location
}
