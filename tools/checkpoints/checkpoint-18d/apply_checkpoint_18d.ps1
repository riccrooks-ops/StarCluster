[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repositoryRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
Push-Location $repositoryRoot

function Assert-FileContains {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string[]]$Patterns,
        [Parameter(Mandatory = $true)][string]$Description
    )

    if (-not (Test-Path $Path)) {
        throw "$Description file $Path was not found. Re-extract the complete Checkpoint 18d package."
    }

    foreach ($pattern in $Patterns) {
        if (-not (Select-String -Path $Path -Pattern ([regex]::Escape($pattern)) -Quiet)) {
            throw "$Description is missing required content: $pattern"
        }
    }
}

function Assert-FileNotContains {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string[]]$Patterns,
        [Parameter(Mandatory = $true)][string]$Description
    )

    if (-not (Test-Path $Path)) {
        throw "$Description file $Path was not found. Re-extract the complete Checkpoint 18d package."
    }

    foreach ($pattern in $Patterns) {
        if (Select-String -Path $Path -Pattern ([regex]::Escape($pattern)) -Quiet) {
            throw "$Description still contains forbidden content: $pattern"
        }
    }
}

function Assert-ReferenceManifest {
    param(
        [Parameter(Mandatory = $true)][string]$Directory,
        [Parameter(Mandatory = $true)][string]$ManifestPath
    )

    if (-not (Test-Path $ManifestPath)) {
        throw "Reference manifest $ManifestPath was not found."
    }

    foreach ($line in Get-Content $ManifestPath) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        if ($line -notmatch '^([0-9a-fA-F]{64})\s+(.+)$') {
            throw "Malformed reference manifest line: $line"
        }

        $expectedHash = $Matches[1].ToLowerInvariant()
        $relativeName = $Matches[2]
        $referencePath = Join-Path $Directory $relativeName
        if (-not (Test-Path $referencePath)) {
            throw "Reference file $relativeName is missing from $Directory."
        }

        $actualHash = (Get-FileHash $referencePath -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actualHash -ne $expectedHash) {
            throw "Reference file $relativeName hash is $actualHash, expected $expectedHash."
        }
    }
}

try {
    Write-Host '[1/12] Verifying repository and accepted Checkpoint 18c baseline...'
    if (-not (Test-Path '.\StarCluster.sln')) {
        throw "StarCluster.sln was not found at $repositoryRoot. Extract the package into the repository root."
    }

    foreach ($baselineFile in @(
        '.\docs\checkpoints\Checkpoint_18c_Headless_Runner_Policy_And_Initialization_Hotfix.md',
        '.\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj',
        '.\src\StarCluster.Core\Simulation\ScenarioInitializationService.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileInterceptionPhaseContext.cs',
        '.\tests\StarCluster.Tests\Combat\Missiles\TerminalPointDefensePolicyTests.cs')) {
        if (-not (Test-Path $baselineFile)) {
            throw "Required Checkpoint 18c baseline file $baselineFile was not found."
        }
    }

    foreach ($obsoleteMissileFile in @(
        '.\src\StarCluster.Core\Combat\Missiles\MissileAdvanceResult.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileSalvo.cs',
        '.\tests\StarCluster.Tests\Combat\Missiles\MissileSalvoTests.cs')) {
        Remove-Item $obsoleteMissileFile -Force -ErrorAction SilentlyContinue
    }

    Write-Host '[2/12] Confirming that Godot is closed...'
    $godotProcesses = Get-Process -ErrorAction SilentlyContinue |
        Where-Object { $_.ProcessName -like 'Godot*' }
    if ($godotProcesses) {
        $processNames = ($godotProcesses.ProcessName | Sort-Object -Unique) -join ', '
        throw "Close Godot before applying Checkpoint 18d. Running process(es): $processNames"
    }

    Write-Host '[3/12] Checking the pinned .NET SDK...'
    $sdkVersion = dotnet --version
    Write-Host "       SDK: $sdkVersion"
    if ($sdkVersion -ne '8.0.423') {
        throw "Expected .NET SDK 8.0.423 from global.json, but dotnet selected $sdkVersion."
    }

    Write-Host '[4/12] Verifying unchanged Checkpoint 18c Core policy...'
    $interceptionContext = '.\src\StarCluster.Core\Combat\Missiles\MissileInterceptionPhaseContext.cs'
    Assert-FileContains $interceptionContext @(
        'Held direct-fire weapons are deliberate long-range interceptors.',
        'MissileInterceptionOpportunity.Transit or',
        'MissileInterceptionOpportunity.Stationary;',
        'Standard PDS is terminal defense.',
        'MissileInterceptionOpportunity.TerminalEntry or',
        'MissileInterceptionOpportunity.PreTerminalAttack;') 'Checkpoint 18d retained interception policy'
    Assert-FileNotContains $interceptionContext @(
        'return opportunity !=') 'Checkpoint 18d held-weapon opportunity filter'
    Assert-FileContains '.\src\StarCluster.Core\Simulation\ScenarioInitializationService.cs' @(
        'restoredGuidancePhaseCount = Math.Max(',
        'definition.RetainedDatalink.ReceivedGuidancePhase') 'Checkpoint 18d retained-report chronology'

    Write-Host '[5/12] Verifying corrected deterministic scenario corpus...'
    $scenarioDirectory = '.\src\StarCluster.ScenarioRunner\Scenarios'
    $scenarioFiles = @(Get-ChildItem $scenarioDirectory -File -Filter '*.json')
    if ($scenarioFiles.Count -ne 7) {
        throw "Expected 7 deterministic scenario files, found $($scenarioFiles.Count)."
    }
    foreach ($scenarioFile in $scenarioFiles) {
        try {
            $document = Get-Content $scenarioFile.FullName -Raw | ConvertFrom-Json
        }
        catch {
            throw "Scenario $($scenarioFile.Name) is not valid JSON: $($_.Exception.Message)"
        }
        if ($document.schemaVersion -ne 1 -or [string]::IsNullOrWhiteSpace($document.id)) {
            throw "Scenario $($scenarioFile.Name) must have schemaVersion 1 and a non-empty id."
        }
    }

    $blockedScenario = Get-Content (Join-Path $scenarioDirectory 'blocked-retained-report-search.json') -Raw | ConvertFrom-Json
    $blockedHistory = @($blockedScenario.missiles[0].enteredCoordinates)
    if ($blockedHistory.Count -ne 4 -or
        $blockedHistory[2].q -ne 0 -or $blockedHistory[2].r -ne 3 -or
        $blockedHistory[3].q -ne 0 -or $blockedHistory[3].r -ne 2) {
        throw 'The blocked-retained-report-search scenario does not contain the corrected adjacent four-edge history.'
    }
    $blockedExpected = $blockedScenario.expect.missiles[0]
    if ($blockedExpected.distanceTraveled -ne 4 -or $blockedExpected.totalFuelSpent -ne 4) {
        throw 'The blocked-retained-report-search scenario must expect distance and fuel of 4.'
    }

    $commandScenario = Get-Content (Join-Path $scenarioDirectory 'command-guided-live-datalink.json') -Raw | ConvertFrom-Json
    $requiredEvents = @($commandScenario.expect.requiredEventsInOrder)
    $trackIndex = [array]::IndexOf($requiredEvents, 'TrackUpdated')
    $movementIndex = [array]::IndexOf($requiredEvents, 'ShipMovementResolved')
    $datalinkIndex = [array]::IndexOf($requiredEvents, 'MissileDatalinkUpdated')
    if ($trackIndex -lt 0 -or $movementIndex -lt 0 -or $datalinkIndex -lt 0 -or
        -not ($trackIndex -lt $movementIndex -and $movementIndex -lt $datalinkIndex)) {
        throw 'The command-guided scenario must expect TrackUpdated before ShipMovementResolved before MissileDatalinkUpdated.'
    }

    Write-Host '[6/12] Verifying whole-batch preflight and event-order diagnostics...'
    foreach ($runnerFile in @(
        '.\src\StarCluster.ScenarioRunner\Program.cs',
        '.\src\StarCluster.ScenarioRunner\ScenarioPreflightValidator.cs',
        '.\src\StarCluster.ScenarioRunner\ScenarioAssertionEvaluator.cs',
        '.\src\StarCluster.ScenarioRunner\README.md')) {
        if (-not (Test-Path $runnerFile)) {
            throw "Required Checkpoint 18d runner file $runnerFile was not found."
        }
    }
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\Program.cs' @(
        'ReadAndPreflightScenarios(',
        'Scenario preflight:',
        'No scenarios were executed.',
        'checkpoint-18d-scenarios') 'Checkpoint 18d batch preflight host'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\ScenarioPreflightValidator.cs' @(
        'ScenarioDocumentMapper.ToInitializationRequest(document)',
        'enteredCoordinates[',
        'every pre-simulation travel-history step must be adjacent') 'Checkpoint 18d scenario preflight'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\ScenarioAssertionEvaluator.cs' @(
        'Matched required events:',
        "All '{eventType}' event indexes:",
        'matched.Add((eventType, found));') 'Checkpoint 18d event-order diagnostics'

    Write-Host '[7/12] Verifying unchanged focused tests and runner support seams...'
    foreach ($testFile in @(
        '.\tests\StarCluster.Tests\Simulation\ScenarioInitializationTests.cs',
        '.\tests\StarCluster.Tests\Combat\Missiles\TerminalPointDefensePolicyTests.cs',
        '.\src\StarCluster.Core\Combat\Missiles\QueuedMissileInterceptionResolver.cs')) {
        if (-not (Test-Path $testFile)) {
            throw "Required Checkpoint 18d test/support file $testFile was not found."
        }
    }
    $initializationFacts = (Select-String -Path '.\tests\StarCluster.Tests\Simulation\ScenarioInitializationTests.cs' -Pattern '^\s*\[Fact\]\s*$').Count
    $pdsFacts = (Select-String -Path '.\tests\StarCluster.Tests\Combat\Missiles\TerminalPointDefensePolicyTests.cs' -Pattern '^\s*\[Fact\]\s*$').Count
    if ($initializationFacts -ne 10 -or $pdsFacts -ne 3) {
        throw "Expected 10 initialization facts and 3 PDS-policy facts; found $initializationFacts and $pdsFacts."
    }

    Write-Host '[8/12] Verifying synchronized documentation and validation handoff...'
    foreach ($documentationFile in @(
        '.\docs\README.md',
        '.\docs\Prototype_TODO.md',
        '.\docs\checkpoints\Checkpoint_18d_Scenario_Corpus_And_Preflight_Hotfix.md',
        '.\docs\validation\Checkpoint_18d_Scenario_Corpus_And_Preflight_Hotfix.md',
        '.\docs\validation\archive\Checkpoint_18c_Headless_Runner_Policy_And_Initialization_Hotfix.md',
        '.\docs\design\Missile_Guidance_Datalink_Sensor_And_Seeker_Architecture.md',
        '.\src\StarCluster.Game\README.md')) {
        if (-not (Test-Path $documentationFile)) {
            throw "Required Checkpoint 18d documentation file $documentationFile was not found."
        }
    }
    Assert-FileContains '.\docs\validation\Checkpoint_18d_Scenario_Corpus_And_Preflight_Hotfix.md' @(
        '506/506',
        'Scenario preflight',
        '7/7',
        'No separate mechanical Godot test is required.') 'Checkpoint 18d active validation runbook'

    Write-Host '[9/12] Verifying unchanged Concept v0.3s and reference library...'
    $expectedV03sHash = '2cf4b68eff1d2ac1a1d532de5e216e3432cc64f6494f2435230b4f86b1c86ea4'
    $conceptHash = (Get-FileHash '.\docs\Star_Cluster_Game_Concept_v0.3s.docx' -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($conceptHash -ne $expectedV03sHash) {
        throw "Concept v0.3s hash is $conceptHash, expected $expectedV03sHash."
    }
    $expectedV03rHash = '633e0f90e31183158f1ec156965ea9beed339948f4b089c393312a9722033dc8'
    $archivedHash = (Get-FileHash '.\docs\archive\Star_Cluster_Game_Concept_v0.3r.docx' -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($archivedHash -ne $expectedV03rHash) {
        throw "Archived Concept v0.3r hash is $archivedHash, expected $expectedV03rHash."
    }
    $expectedReferenceManifestHash = '070ced666ad12a448d6767769ac4ff6e38379ecb5d182dae7ce83f9bad786db4'
    $referenceManifestHash = (Get-FileHash '.\docs\references\SHA256SUMS.txt' -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($referenceManifestHash -ne $expectedReferenceManifestHash) {
        throw "Reference manifest hash is $referenceManifestHash, expected $expectedReferenceManifestHash."
    }
    Assert-ReferenceManifest '.\docs\references' '.\docs\references\SHA256SUMS.txt'

    Write-Host '[10/12] Refreshing Godot metadata and building...'
    Remove-Item -Recurse -Force '.\src\StarCluster.Game\.godot\mono' -ErrorAction SilentlyContinue
    $solutionOutput = dotnet sln '.\StarCluster.sln' list
    if ($LASTEXITCODE -ne 0) {
        throw "dotnet sln list failed with exit code $LASTEXITCODE."
    }
    $solutionText = $solutionOutput | Out-String
    if ($solutionText -notmatch 'StarCluster.ScenarioRunner.csproj') {
        dotnet sln '.\StarCluster.sln' add '.\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj'
        if ($LASTEXITCODE -ne 0) {
            throw "Could not add StarCluster.ScenarioRunner to the solution; exit code $LASTEXITCODE."
        }
    }

    dotnet build '.\StarCluster.sln' --nologo -warnaserror
    if ($LASTEXITCODE -ne 0) {
        throw "dotnet build failed with exit code $LASTEXITCODE."
    }

    Write-Host '[11/12] Running 506 engine-independent tests...'
    $testOutput = dotnet test '.\tests\StarCluster.Tests\StarCluster.Tests.csproj' --no-build --nologo
    $testOutput | Write-Host
    if ($LASTEXITCODE -ne 0) {
        throw "dotnet test failed with exit code $LASTEXITCODE."
    }
    $testText = $testOutput | Out-String
    if ($testText -notmatch 'Passed:\s+506') {
        throw 'The complete suite did not report the expected 506 passed tests.'
    }
    if (Select-String -Path '.\src\StarCluster.Core\StarCluster.Core.csproj' -Pattern 'Godot' -Quiet) {
        throw 'StarCluster.Core unexpectedly contains a Godot dependency.'
    }

    Write-Host '[12/12] Preflighting and running seven deterministic headless scenarios...'
    $scenarioOutputDirectory = '.\out\checkpoint-18d-scenarios'
    Remove-Item -Recurse -Force $scenarioOutputDirectory -ErrorAction SilentlyContinue
    $runnerOutput = dotnet run `
        --project '.\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj' `
        --no-build `
        -- `
        run-all `
        --scenario-dir $scenarioDirectory `
        --output-dir $scenarioOutputDirectory
    $runnerOutput | Write-Host
    if ($LASTEXITCODE -ne 0) {
        throw "The deterministic scenario runner failed with exit code $LASTEXITCODE."
    }
    $runnerText = $runnerOutput | Out-String
    if ($runnerText -notmatch 'Scenario preflight:\s+7 passed, 0 failed\.') {
        throw 'The runner did not report the expected 7/7 scenario preflight result.'
    }
    if ($runnerText -notmatch 'Scenarios:\s+7 passed, 0 failed, 7 total\.') {
        throw 'The runner did not report the expected 7/7 passing scenarios.'
    }

    Remove-Item '.\docs\validation\Checkpoint_18_Unified_Missile_Terminal_Solutions_Search_And_Seeker_Assistance.md' -Force -ErrorAction SilentlyContinue
    Remove-Item '.\docs\validation\Checkpoint_17c_Presentation_Concept_And_Reference_Handoff.md' -Force -ErrorAction SilentlyContinue
    foreach ($supersededValidation in @(
        'Checkpoint_18b_Headless_Scenario_Runner_And_Deterministic_Combat_Validation.md',
        'Checkpoint_18c_Headless_Runner_Policy_And_Initialization_Hotfix.md')) {
        $activePath = Join-Path '.\docs\validation' $supersededValidation
        $archivePath = Join-Path '.\docs\validation\archive' $supersededValidation
        if (Test-Path $activePath) {
            Copy-Item $activePath $archivePath -Force
            Remove-Item $activePath -Force
        }
    }

    $activeValidationFiles = @(Get-ChildItem '.\docs\validation' -File -Filter '*.md')
    if ($activeValidationFiles.Count -ne 1 -or
        $activeValidationFiles[0].Name -ne 'Checkpoint_18d_Scenario_Corpus_And_Preflight_Hotfix.md') {
        throw 'Checkpoint 18d must leave exactly one active validation runbook.'
    }

    Write-Host ''
    Write-Host 'Checkpoint 18d completed successfully.'
    Write-Host 'Engine-independent tests passed: 506.'
    Write-Host 'Scenario preflight passed: 7.'
    Write-Host 'Deterministic headless scenarios passed: 7.'
    Write-Host 'No mechanical Godot validation is required.'
}
finally {
    Pop-Location
}
