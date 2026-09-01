[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$repositoryRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
Push-Location $repositoryRoot

try {
    Write-Host '[1/9] Verifying the Star Cluster repository and Checkpoint 09...'

    if (-not (Test-Path '.\StarCluster.sln')) {
        throw "StarCluster.sln was not found at $repositoryRoot. Extract the package into the repository root."
    }

    $requiredFiles = @(
        '.\src\StarCluster.Core\Geometry\HexCoord.cs',
        '.\src\StarCluster.Core\Maps\SystemMap.cs',
        '.\src\StarCluster.Core\Combat\DirectFireLineOfSight.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileRoutePlanner.cs',
        '.\src\StarCluster.Game\StarCluster.Game.csproj',
        '.\src\StarCluster.Game\project.godot',
        '.\src\StarCluster.Game\Scenes\Main.tscn',
        '.\src\StarCluster.Game\Scripts\Main.cs',
        '.\src\StarCluster.Game\Scripts\HexBoardView.cs',
        '.\docs\checkpoints\Checkpoint_09_Godot_Presentation_Spike.md',
        '.\docs\Star_Cluster_Game_Concept_v0.3a.docx'
    )

    foreach ($requiredFile in $requiredFiles) {
        if (-not (Test-Path $requiredFile)) {
            throw "Required file $requiredFile was not found. Apply Checkpoint 09 first, then re-extract Checkpoint 09a."
        }
    }

    Write-Host '[2/9] Confirming that Godot is closed before generated metadata is refreshed...'
    $godotProcesses = Get-Process -ErrorAction SilentlyContinue |
        Where-Object { $_.ProcessName -like 'Godot*' }

    if ($godotProcesses) {
        $processNames = ($godotProcesses.ProcessName | Sort-Object -Unique) -join ', '
        throw "Close the Godot editor and debug window before applying this hotfix. Running process(es): $processNames"
    }

    Write-Host '[3/9] Checking the pinned .NET SDK...'
    $sdkVersion = dotnet --version
    Write-Host "       SDK: $sdkVersion"

    if ($sdkVersion -ne '8.0.423') {
        throw "Expected .NET SDK 8.0.423 from global.json, but dotnet selected $sdkVersion."
    }

    Write-Host '[4/9] Verifying the Checkpoint 09a Godot configuration and source files...'

    if (-not (Select-String -Path '.\src\StarCluster.Game\project.godot' -Pattern 'project/assembly_name="StarCluster.Game"' -Quiet)) {
        throw 'project.godot does not declare dotnet/project/assembly_name as StarCluster.Game.'
    }

    if (-not (Select-String -Path '.\src\StarCluster.Game\project.godot' -Pattern 'window/stretch/aspect="expand"' -Quiet)) {
        throw 'project.godot does not declare expand stretch behavior.'
    }

    if (-not (Select-String -Path '.\src\StarCluster.Game\Scripts\Main.cs' -Pattern 'new ScrollContainer' -Quiet)) {
        throw 'Main.cs does not contain the Checkpoint 09a scrollable side panel.'
    }

    if (-not (Select-String -Path '.\src\StarCluster.Game\Scripts\HexBoardView.cs' -Pattern 'DrawPointerStatusOverlay' -Quiet)) {
        throw 'HexBoardView.cs does not contain the always-visible pointer status overlay.'
    }

    if (-not (Select-String -Path '.\src\StarCluster.Game\Scripts\HexBoardView.cs' -Pattern 'topStatusArea' -Quiet)) {
        throw 'HexBoardView.cs does not contain the responsive board-fit layout.'
    }

    Write-Host '[5/9] Verifying solution membership and managed assembly identity...'
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

        $solutionText = (dotnet sln '.\StarCluster.sln' list) | Out-String
    }

    if ($solutionText -notmatch 'StarCluster.Game.csproj') {
        throw 'StarCluster.Game is missing from StarCluster.sln.'
    }

    $assemblyOutput = dotnet msbuild `
        '.\src\StarCluster.Game\StarCluster.Game.csproj' `
        -nologo `
        -getProperty:AssemblyName

    if ($LASTEXITCODE -ne 0) {
        throw "Could not query the StarCluster.Game AssemblyName; exit code $LASTEXITCODE."
    }

    $assemblyName = ($assemblyOutput |
        Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
        Select-Object -Last 1).Trim()

    Write-Host "       Managed assembly: $assemblyName"

    if ($assemblyName -ne 'StarCluster.Game') {
        throw "Expected AssemblyName StarCluster.Game, but MSBuild reported $assemblyName."
    }

    Write-Host '[6/9] Refreshing generated Godot managed metadata...'
    Remove-Item `
        -Recurse `
        -Force `
        '.\src\StarCluster.Game\.godot\mono' `
        -ErrorAction SilentlyContinue

    Write-Host '[7/9] Verifying synchronized project documentation...'

    $documentationFiles = @(
        '.\docs\README.md',
        '.\docs\Star_Cluster_Game_Concept_v0.3a.docx',
        '.\docs\checkpoints\Checkpoint_09_Godot_Presentation_Spike.md',
        '.\docs\checkpoints\Checkpoint_09a_Godot_Layout_Hotfix.md'
    )

    foreach ($documentationFile in $documentationFiles) {
        if (-not (Test-Path $documentationFile)) {
            throw "Required documentation file $documentationFile was not found."
        }
    }

    if (-not (Select-String -Path '.\docs\README.md' -Pattern 'Checkpoint_09a_Godot_Layout_Hotfix.md' -Quiet)) {
        throw 'The documentation index does not reference Checkpoint 09a.'
    }

    Write-Host '[8/9] Building the complete solution...'
    dotnet build '.\StarCluster.sln' --nologo

    if ($LASTEXITCODE -ne 0) {
        throw "dotnet build failed with exit code $LASTEXITCODE."
    }

    Write-Host '[9/9] Running tests and confirming the one-way architecture...'
    dotnet test '.\tests\StarCluster.Tests\StarCluster.Tests.csproj' --no-build --nologo

    if ($LASTEXITCODE -ne 0) {
        throw "dotnet test failed with exit code $LASTEXITCODE."
    }

    if (Select-String -Path '.\src\StarCluster.Core\StarCluster.Core.csproj' -Pattern 'Godot' -Quiet) {
        throw 'StarCluster.Core unexpectedly contains a Godot dependency.'
    }

    Write-Host ''
    Write-Host 'Checkpoint 09a completed successfully.' -ForegroundColor Green
    Write-Host 'Expected engine-independent tests passed: 208.'
    Write-Host 'Reopen the existing Godot project and press F5 to verify responsive layout, scrolling, hover status, and missile controls.'
}
finally {
    Pop-Location
}
