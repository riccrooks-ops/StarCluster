[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$repositoryRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
Push-Location $repositoryRoot

try {
    Write-Host '[1/7] Verifying the Star Cluster repository and Checkpoint 06...'

    if (-not (Test-Path '.\StarCluster.sln')) {
        throw "StarCluster.sln was not found at $repositoryRoot. Extract the package into the repository root."
    }

    $priorFiles = @(
        '.\src\StarCluster.Core\Geometry\HexCoord.cs',
        '.\src\StarCluster.Core\Geometry\HexGeometry.cs',
        '.\src\StarCluster.Core\Maps\HexMap.cs',
        '.\src\StarCluster.Core\Maps\SystemMap.cs',
        '.\src\StarCluster.Core\Combat\LineOfSightBlocker.cs',
        '.\src\StarCluster.Core\Combat\DirectFireLineOfSightResult.cs',
        '.\src\StarCluster.Core\Combat\DirectFireLineOfSight.cs',
        '.\docs\checkpoints\Checkpoint_06_Direct_Fire_Line_Of_Sight.md'
    )

    foreach ($priorFile in $priorFiles) {
        if (-not (Test-Path $priorFile)) {
            throw "Required Checkpoint 06 file $priorFile was not found. Apply Checkpoint 06 first."
        }
    }

    Write-Host '[2/7] Checking the pinned .NET SDK...'
    $sdkVersion = dotnet --version
    Write-Host "       SDK: $sdkVersion"

    if ($sdkVersion -ne '8.0.423') {
        throw "Expected .NET SDK 8.0.423 from global.json, but dotnet selected $sdkVersion."
    }

    Write-Host '[3/7] Verifying the Checkpoint 07 grazing source files...'

    $requiredFiles = @(
        '.\src\StarCluster.Core\Geometry\HexLineStep.cs',
        '.\src\StarCluster.Core\Geometry\HexGeometry.cs',
        '.\src\StarCluster.Core\Combat\LineOfSightQuality.cs',
        '.\src\StarCluster.Core\Combat\LineOfSightGrazing.cs',
        '.\src\StarCluster.Core\Combat\LineOfSightBlockage.cs',
        '.\src\StarCluster.Core\Combat\DirectFireLineOfSightResult.cs',
        '.\src\StarCluster.Core\Combat\DirectFireLineOfSight.cs',
        '.\tests\StarCluster.Tests\Geometry\HexSupercoverStepTests.cs',
        '.\tests\StarCluster.Tests\Combat\DirectFireLineOfSightTests.cs'
    )

    foreach ($requiredFile in $requiredFiles) {
        if (-not (Test-Path $requiredFile)) {
            throw "$requiredFile was not found. Re-extract the Checkpoint 07 package into the repository root."
        }
    }

    Write-Host '[4/7] Updating and verifying synchronized project documentation...'

    if (-not (Test-Path '.\docs\Star_Cluster_Game_Concept_v0.3a.docx')) {
        throw 'The current Concept v0.3a document was not found in the docs folder.'
    }

    if (-not (Test-Path '.\docs\archive\Star_Cluster_Game_Concept_v0.3.docx')) {
        throw 'The archived Concept v0.3 document was not found.'
    }

    if (-not (Test-Path '.\docs\checkpoints\Checkpoint_07_Grazing_Line_Of_Sight.md')) {
        throw 'The Checkpoint 07 documentation file was not found.'
    }

    if (Test-Path '.\docs\Star_Cluster_Game_Concept_v0.3.docx') {
        Remove-Item '.\docs\Star_Cluster_Game_Concept_v0.3.docx' -Force
        Write-Host '       Removed superseded active Concept v0.3; archived copy retained.'
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

    Write-Host '[7/7] Confirming the Checkpoint 07 documentation state...'

    if (Test-Path '.\docs\Star_Cluster_Game_Concept_v0.3.docx') {
        throw 'The superseded Concept v0.3 remains active instead of archived.'
    }

    Write-Host ''
    Write-Host 'Checkpoint 07 completed successfully.' -ForegroundColor Green
    Write-Host 'Current concept: .\docs\Star_Cluster_Game_Concept_v0.3a.docx'
}
finally {
    Pop-Location
}
