[CmdletBinding()]
param(
    [switch]$KeepTemplateFiles
)

$ErrorActionPreference = 'Stop'

$repositoryRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
Push-Location $repositoryRoot

try {
    Write-Host '[1/5] Verifying the Star Cluster repository...'

    if (-not (Test-Path '.\StarCluster.sln')) {
        throw "StarCluster.sln was not found at $repositoryRoot. Extract the package into the repository root."
    }

    if (-not (Test-Path '.\src\StarCluster.Core\StarCluster.Core.csproj')) {
        throw 'The StarCluster.Core project was not found.'
    }

    if (-not (Test-Path '.\tests\StarCluster.Tests\StarCluster.Tests.csproj')) {
        throw 'The StarCluster.Tests project was not found.'
    }

    Write-Host '[2/5] Checking the pinned .NET SDK...'
    $sdkVersion = dotnet --version
    Write-Host "       SDK: $sdkVersion"

    if ($sdkVersion -ne '8.0.423') {
        throw "Expected .NET SDK 8.0.423 from global.json, but dotnet selected $sdkVersion."
    }

    Write-Host '[3/5] Removing generated template source files...'

    if (-not $KeepTemplateFiles) {
        Remove-Item '.\src\StarCluster.Core\Class1.cs' -Force -ErrorAction SilentlyContinue
        Remove-Item '.\tests\StarCluster.Tests\UnitTest1.cs' -Force -ErrorAction SilentlyContinue
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
    Write-Host 'Checkpoint 02 completed successfully.' -ForegroundColor Green
}
finally {
    Pop-Location
}
