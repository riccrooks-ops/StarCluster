[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$repositoryRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
Push-Location $repositoryRoot

try {
    Write-Host '[1/10] Verifying the Star Cluster repository and Checkpoint 12a...'

    if (-not (Test-Path '.\StarCluster.sln')) {
        throw "StarCluster.sln was not found at $repositoryRoot. Extract the package into the repository root."
    }

    $priorFiles = @(
        '.\src\StarCluster.Core\Combat\DirectFire\DirectFireOrder.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileInterceptionPhaseContext.cs',
        '.\src\StarCluster.Game\Scripts\Main.cs',
        '.\docs\checkpoints\Checkpoint_12a_Direct_Fire_Commitment_And_Layered_Interception.md'
    )

    foreach ($priorFile in $priorFiles) {
        if (-not (Test-Path $priorFile)) {
            throw "Required prior-checkpoint file $priorFile was not found. Apply Checkpoint 12a first."
        }
    }

    Write-Host '[2/10] Confirming that Godot is closed...'
    $godotProcesses = Get-Process -ErrorAction SilentlyContinue |
        Where-Object { $_.ProcessName -like 'Godot*' }

    if ($godotProcesses) {
        $processNames = ($godotProcesses.ProcessName | Sort-Object -Unique) -join ', '
        throw "Close the Godot editor and debug window before applying Checkpoint 13. Running process(es): $processNames"
    }

    Write-Host '[3/10] Checking the pinned .NET SDK...'
    $sdkVersion = dotnet --version
    Write-Host "       SDK: $sdkVersion"

    if ($sdkVersion -ne '8.0.423') {
        throw "Expected .NET SDK 8.0.423 from global.json, but dotnet selected $sdkVersion."
    }

    Write-Host '[4/10] Verifying navigation knowledge, target tracks, and route projection sources...'
    $coreFiles = @(
        '.\src\StarCluster.Core\Combat\DirectFire\DirectFireOrder.cs',
        '.\src\StarCluster.Core\Combat\Missiles\FixedMissileDefenseTrackProvider.cs',
        '.\src\StarCluster.Core\Combat\Missiles\GuidedMissileSalvo.cs',
        '.\src\StarCluster.Core\Combat\Missiles\IMissileDefenseTrackProvider.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileDefenseSystem.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileInterceptionPhaseContext.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileRouteProjection.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileRouteProjectionService.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileRouteProjectionStatus.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileTargetTrackQuality.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileTargetTrackSnapshot.cs',
        '.\src\StarCluster.Core\Combat\Tracking\ComputingProfile.cs',
        '.\src\StarCluster.Core\Combat\Tracking\DirectFireTrackEligibility.cs',
        '.\src\StarCluster.Core\Combat\Tracking\KnownNavigationContact.cs',
        '.\src\StarCluster.Core\Combat\Tracking\NavigationKnowledge.cs',
        '.\src\StarCluster.Core\Combat\Tracking\SensorContactEvaluator.cs',
        '.\src\StarCluster.Core\Combat\Tracking\SensorProfile.cs',
        '.\src\StarCluster.Core\Combat\Tracking\SystemEntryTrackInitializer.cs',
        '.\src\StarCluster.Core\Combat\Tracking\TacticalMapContact.cs',
        '.\src\StarCluster.Core\Combat\Tracking\TacticalMapContactSource.cs',
        '.\src\StarCluster.Core\Combat\Tracking\TacticalMapKnowledgeService.cs',
        '.\src\StarCluster.Core\Combat\Tracking\TacticalMapKnowledgeSnapshot.cs',
        '.\src\StarCluster.Core\Combat\Tracking\TacticalMissileContact.cs',
        '.\src\StarCluster.Core\Combat\Tracking\TacticalMissileKnowledgeService.cs',
        '.\src\StarCluster.Core\Combat\Tracking\TacticalTrackObservation.cs',
        '.\src\StarCluster.Core\Combat\Tracking\TacticalTrackQuality.cs',
        '.\src\StarCluster.Core\Combat\Tracking\TacticalTrackRecord.cs',
        '.\src\StarCluster.Core\Combat\Tracking\TacticalTrackRepository.cs',
        '.\src\StarCluster.Core\Combat\Tracking\TacticalTrackSourceType.cs',
        '.\src\StarCluster.Core\Combat\Tracking\TacticalTrackUpdateResult.cs',
        '.\src\StarCluster.Core\Combat\Tracking\TacticalTrackUpdateService.cs',
        '.\src\StarCluster.Core\Combat\Tracking\TrackUpdateTrigger.cs'
    )
    foreach ($coreFile in $coreFiles) {
        if (-not (Test-Path $coreFile)) {
            throw "Checkpoint 13 source file $coreFile was not found. Re-extract the package."
        }
    }

    if (-not (Select-String -Path '.\src\StarCluster.Core\Combat\Tracking\NavigationKnowledge.cs' -Pattern 'MapObjectKind.Star' -Quiet)) {
        throw 'NavigationKnowledge does not automatically include every star.'
    }

    if (-not (Select-String -Path '.\src\StarCluster.Core\Combat\Tracking\TacticalTrackQuality.cs' -Pattern 'Firm' -Quiet) -or
        -not (Select-String -Path '.\src\StarCluster.Core\Combat\Tracking\TacticalTrackQuality.cs' -Pattern 'Approximate' -Quiet) -or
        -not (Select-String -Path '.\src\StarCluster.Core\Combat\Tracking\TacticalTrackQuality.cs' -Pattern 'Stale' -Quiet) -or
        -not (Select-String -Path '.\src\StarCluster.Core\Combat\Tracking\TacticalTrackQuality.cs' -Pattern 'Lost' -Quiet)) {
        throw 'The Firm / Approximate / Stale / Lost track-quality foundation is incomplete.'
    }

    if (-not (Select-String -Path '.\src\StarCluster.Core\Combat\Missiles\MissileRouteProjectionService.cs' -Pattern 'Project' -Quiet)) {
        throw 'The non-mutating missile route projection service is missing.'
    }

    if (-not (Select-String -Path '.\src\StarCluster.Core\Combat\Tracking\TacticalMissileKnowledgeService.cs' -Pattern 'visibleTravelHistory: Array.Empty' -Quiet)) {
        throw 'Hostile missile presentation is not suppressing authoritative travel history.'
    }

    Write-Host '[5/10] Verifying the 38 new tracking and tactical-knowledge tests...'
    $newTestFiles = @(
        '.\tests\StarCluster.Tests\Combat\Tracking\SensorAndComputingProfileTests.cs',
        '.\tests\StarCluster.Tests\Combat\Tracking\TacticalTrackUpdateServiceTests.cs',
        '.\tests\StarCluster.Tests\Combat\Tracking\NavigationAndSystemEntryTests.cs',
        '.\tests\StarCluster.Tests\Combat\Tracking\TacticalMapKnowledgeTests.cs',
        '.\tests\StarCluster.Tests\Combat\Tracking\MissileTrackIntegrationTests.cs',
        '.\tests\StarCluster.Tests\Combat\Tracking\InterceptionTrackGateTests.cs',
        '.\tests\StarCluster.Tests\Combat\Tracking\TacticalMissileKnowledgeTests.cs'
    )

    $newFactCount = 0
    foreach ($testFile in $newTestFiles) {
        if (-not (Test-Path $testFile)) {
            throw "Checkpoint 13 test file $testFile was not found."
        }

        $newFactCount += (Select-String -Path $testFile -Pattern '\[Fact\]' -AllMatches).Matches.Count
    }

    if ($newFactCount -ne 38) {
        throw "Expected 38 new [Fact] tests, but found $newFactCount."
    }

    $requiredTests = @(
        @{ File = '.\tests\StarCluster.Tests\Combat\Tracking\NavigationAndSystemEntryTests.cs'; Pattern = 'EveryStarIsAutomaticallyPreKnown' },
        @{ File = '.\tests\StarCluster.Tests\Combat\Tracking\NavigationAndSystemEntryTests.cs'; Pattern = 'InitialTrackUpdateCreatesContactBeforeSnapshotBuild' },
        @{ File = '.\tests\StarCluster.Tests\Combat\Tracking\TacticalMapKnowledgeTests.cs'; Pattern = 'UnknownShipDoesNotLeakIntoSnapshot' },
        @{ File = '.\tests\StarCluster.Tests\Combat\Tracking\MissileTrackIntegrationTests.cs'; Pattern = 'RouteProjectionDoesNotMutateSalvoLifetimeState' },
        @{ File = '.\tests\StarCluster.Tests\Combat\Tracking\InterceptionTrackGateTests.cs'; Pattern = 'PointDefenseUsesIndependentLocalAcquisition' },
        @{ File = '.\tests\StarCluster.Tests\Combat\Tracking\TacticalMissileKnowledgeTests.cs'; Pattern = 'HostileStaleMissileUsesTrackCoordinateWithoutTruthHistory' }
    )

    foreach ($requiredTest in $requiredTests) {
        if (-not (Select-String -Path $requiredTest.File -Pattern $requiredTest.Pattern -Quiet)) {
            throw "Required Checkpoint 13 regression test $($requiredTest.Pattern) is missing."
        }
    }

    Write-Host '[6/10] Verifying Godot initial tracking and presentation cleanup...'
    $mainFile = '.\src\StarCluster.Game\Scripts\Main.cs'
    $boardFile = '.\src\StarCluster.Game\Scripts\HexBoardView.cs'
    $trackFile = '.\src\StarCluster.Game\Scripts\DemoTrackState.cs'

    $mainPatterns = @(
        'Star Cluster - Checkpoint 13',
        'Track quality',
        'TrackUpdateTrigger.SystemEntry',
        'TrackUpdateTrigger.ScenarioReset',
        'TrackUpdateTrigger.ShipMovementCommitted',
        'DirectFireTrackEligibility',
        'known active salvos',
        'PlayerMissileContacts'
    )

    foreach ($pattern in $mainPatterns) {
        if (-not (Select-String -Path $mainFile -Pattern ([regex]::Escape($pattern)) -Quiet)) {
            throw "Main.cs is missing required Checkpoint 13 behavior: $pattern"
        }
    }

    $boardPatterns = @(
        'SetKnowledgeState',
        'DrawMissileOverlay',
        'DrawDashedRoutePath',
        'TacticalTrackQuality.Approximate',
        'TacticalTrackQuality.Stale',
        'TacticalMissileContact'
    )

    foreach ($pattern in $boardPatterns) {
        if (-not (Select-String -Path $boardFile -Pattern ([regex]::Escape($pattern)) -Quiet)) {
            throw "HexBoardView.cs is missing required Checkpoint 13 presentation: $pattern"
        }
    }

    if (-not (Select-String -Path $trackFile -Pattern 'Refresh\(initialTrigger' -Quiet)) {
        throw 'DemoTrackState does not complete its initial Track Update during construction.'
    }

    Write-Host '[7/10] Verifying Concept v0.3e and synchronized documentation...'
    $documentationFiles = @(
        '.\docs\README.md',
        '.\docs\Star_Cluster_Game_Concept_v0.3e.docx',
        '.\docs\archive\Star_Cluster_Game_Concept_v0.3d.docx',
        '.\docs\Prototype_TODO.md',
        '.\docs\checkpoints\Checkpoint_13_Target_Track_And_Tactical_Presentation_Foundations.md',
        '.\src\StarCluster.Game\README.md'
    )

    foreach ($documentationFile in $documentationFiles) {
        if (-not (Test-Path $documentationFile)) {
            throw "Required documentation file $documentationFile was not found."
        }
    }

    if (-not (Select-String -Path '.\docs\README.md' -Pattern 'Star_Cluster_Game_Concept_v0.3e.docx' -Quiet)) {
        throw 'The documentation index does not identify Concept v0.3e as current.'
    }

    if (-not (Select-String -Path '.\docs\README.md' -Pattern 'Checkpoint_13_Target_Track_And_Tactical_Presentation_Foundations.md' -Quiet)) {
        throw 'The documentation index does not reference Checkpoint 13.'
    }

    if (-not (Select-String -Path '.\docs\Prototype_TODO.md' -Pattern 'automatic phase advancement' -Quiet)) {
        throw 'The living TODO does not preserve the deferred automatic phase-advance item.'
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

    Write-Host '[9/10] Building the complete solution with warnings treated as errors...'
    dotnet build '.\StarCluster.sln' --nologo -warnaserror

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
    Write-Host 'Checkpoint 13 completed successfully.' -ForegroundColor Green
    Write-Host 'Expected engine-independent tests passed: 349.'
    Write-Host 'Reopen Godot and press F5. Confirm pre-known stars and initial Track Update, exercise Firm / Approximate / Stale / Lost visibility, verify precision-fire gating, keep tracked missiles visible across phases, compare executed and projected routes, and confirm movement overlays clear after commit.'
    Write-Host 'Next candidate checkpoint: sensor signatures and electronic-warfare foundations, after reviewing the local Checkpoint 13 results.'
}
finally {
    Pop-Location
}
