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
        throw "$Description file $Path was not found. Re-extract the complete Checkpoint 21b package."
    }

    foreach ($pattern in $Patterns) {
        if (-not (Select-String -Path $Path -Pattern ([regex]::Escape($pattern)) -Quiet)) {
            throw "$Description is missing required content: $pattern"
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

function Invoke-Runner {
    param(
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][string]$Description
    )

    $dotnetArguments = @(
        'run',
        '--project', '.\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj',
        '--no-build',
        '--'
    ) + $Arguments
    $output = & dotnet @dotnetArguments
    $output | Write-Host
    if ($LASTEXITCODE -ne 0) {
        throw "$Description failed with exit code $LASTEXITCODE."
    }
    return ($output | Out-String)
}

try {
    Write-Host '[1/13] Verifying repository and partially applied Checkpoint 21a baseline...'
    if (-not (Test-Path '.\StarCluster.sln')) {
        throw "StarCluster.sln was not found at $repositoryRoot. Extract the package into the repository root."
    }

    foreach ($baselineFile in @(
        '.\docs\checkpoints\Checkpoint_18d_Scenario_Corpus_And_Preflight_Hotfix.md',
        '.\docs\checkpoints\Checkpoint_19a_Validation_Runbook_Guard_Hotfix.md',
        '.\docs\checkpoints\Checkpoint_20b_Paired_Calibration_And_Statistical_Gate_Repair.md',
        '.\docs\checkpoints\Checkpoint_21_Full_Flight_Missile_Pursuit_And_Guidance_Calibration.md',
        '.\docs\checkpoints\Checkpoint_21a_Full_Flight_Opportunity_Movement_Horizon_And_24_Worker_Scheduler_Repair.md',
        '.\docs\checkpoints\Checkpoint_21b_CSharp_Switch_Expression_Build_Hotfix.md',
        '.\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj',
        '.\src\StarCluster.ScenarioRunner\Studies\checkpoint-20-representative-profiles.json',
        '.\src\StarCluster.ScenarioRunner\Studies\checkpoint-21-full-flight-pursuit.calibration.json',
        '.\src\StarCluster.Core\Simulation\ScenarioInitializationService.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileInterceptionPhaseContext.cs')) {
        if (-not (Test-Path $baselineFile)) {
            throw "Required Checkpoint 21 overlay baseline file $baselineFile was not found."
        }
    }

    foreach ($obsoleteMissileFile in @(
        '.\src\StarCluster.Core\Combat\Missiles\MissileAdvanceResult.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileSalvo.cs',
        '.\tests\StarCluster.Tests\Combat\Missiles\MissileSalvoTests.cs')) {
        Remove-Item $obsoleteMissileFile -Force -ErrorAction SilentlyContinue
    }

    Remove-Item '.\docs\Star_Cluster_Game_Concept_v0.3r.docx' -Force -ErrorAction SilentlyContinue
    Get-ChildItem '.\docs\validation' -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -ne 'Checkpoint_21b_CSharp_Switch_Expression_Build_Hotfix.md' } |
        Remove-Item -Force

    Write-Host '[2/13] Confirming that Godot is closed...'
    $godotProcesses = Get-Process -ErrorAction SilentlyContinue |
        Where-Object { $_.ProcessName -like 'Godot*' }
    if ($godotProcesses) {
        $processNames = ($godotProcesses.ProcessName | Sort-Object -Unique) -join ', '
        throw "Close Godot before applying Checkpoint 21b. Running process(es): $processNames"
    }

    Write-Host '[3/13] Checking the pinned .NET SDK...'
    $sdkVersion = dotnet --version
    Write-Host "       SDK: $sdkVersion"
    if ($sdkVersion -ne '8.0.423') {
        throw "Expected .NET SDK 8.0.423 from global.json, but dotnet selected $sdkVersion."
    }

    Write-Host '[4/13] Verifying unchanged authoritative terminal and initialization policy...'
    Assert-FileContains '.\src\StarCluster.Core\Combat\Missiles\MissileInterceptionPhaseContext.cs' @(
        'Held direct-fire weapons are deliberate long-range interceptors.',
        'MissileInterceptionOpportunity.Transit or',
        'MissileInterceptionOpportunity.Stationary;',
        'Standard PDS is terminal defense.',
        'MissileInterceptionOpportunity.TerminalEntry or',
        'MissileInterceptionOpportunity.PreTerminalAttack;') 'Checkpoint 21b interception policy'
    Assert-FileContains '.\src\StarCluster.Core\Simulation\ScenarioInitializationService.cs' @(
        'restoredGuidancePhaseCount = Math.Max(',
        'definition.RetainedDatalink.ReceivedGuidancePhase') 'Checkpoint 21b shared initialization'
    Assert-FileContains '.\src\StarCluster.Core\Combat\Missiles\MissileAutonomousGuidanceService.cs' @(
        'MissileGuidanceArbitrator.Select(',
        'MissileLocalSensorService.Observe(',
        'MissileRoutePlanner.FindRoute(') 'Checkpoint 21b authoritative guidance path'
    Assert-FileContains '.\src\StarCluster.Core\Combat\Missiles\MissileTerminalResolutionService.cs' @(
        'MissileTerminalOutcome.Dud',
        'MissileTerminalOutcome.CriticalHit') 'Checkpoint 21b terminal contract'

    Write-Host '[5/13] Verifying opportunity authority, operational caps, and the 24-worker scheduler...'
    foreach ($runnerFile in @(
        '.\src\StarCluster.ScenarioRunner\FullFlightCalibrationDocuments.cs',
        '.\src\StarCluster.ScenarioRunner\FullFlightCalibrationModel.cs',
        '.\src\StarCluster.ScenarioRunner\FullFlightCalibrationRunner.cs',
        '.\src\StarCluster.ScenarioRunner\MonteCarloTrialResult.cs',
        '.\src\StarCluster.ScenarioRunner\MonteCarloBatchRunner.cs',
        '.\src\StarCluster.ScenarioRunner\ScenarioDocument.cs',
        '.\src\StarCluster.ScenarioRunner\ScenarioExecutor.cs',
        '.\src\StarCluster.ScenarioRunner\ScenarioOutputWriter.cs',
        '.\src\StarCluster.ScenarioRunner\ScenarioPreflightValidator.cs',
        '.\src\StarCluster.ScenarioRunner\ScenarioRunResult.cs',
        '.\src\StarCluster.ScenarioRunner\ScenarioRunnerSelfTests.cs',
        '.\src\StarCluster.ScenarioRunner\ScenarioTerminalOpportunity.cs',
        '.\src\StarCluster.ScenarioRunner\Program.cs')) {
        if (-not (Test-Path $runnerFile)) {
            throw "Required Checkpoint 21b runner file $runnerFile was not found."
        }
    }
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\ScenarioTerminalOpportunity.cs' @(
        'MissileEnteredTargetHex',
        'TargetEnteredMissileHex',
        'ActionBeganColocated',
        'StationarySearchRetry') 'Checkpoint 21b opportunity source model'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\ScenarioExecutor.cs' @(
        'RecordTerminalOpportunityIfPresent',
        'ScenarioTerminalOpportunitySource.TargetEnteredMissileHex',
        'DiagnosticEventType.MissileTerminalOpportunity',
        'data: Data(("source", source.ToString()))') 'Checkpoint 21b opportunity authority'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\MonteCarloTrialResult.cs' @(
        'TerminalOpportunityInvariantPassed',
        'OperationalTimeoutReached',
        'UnexplainedUnresolved',
        'result.TerminalOpportunities.Count') 'Checkpoint 21b trial classifications'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\MonteCarloBatchRunner.cs' @(
        'if (options.KeepTrialJournal || options.Resume)',
        'AppendTrials(trialsPath, ordered);') 'Checkpoint 21b discarded-journal optimization'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\FullFlightCalibrationModel.cs' @(
        'CrossingWeavePolicy = "crossing-weave"',
        'TurnbackPolicy = "turnback"',
        'CalculateSafetyTurnCap(',
        'OperationalTurnLimit = safetyTurnCap',
        'ScenarioPreflightValidator.Validate') 'Checkpoint 21b full-flight materialization'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\FullFlightCalibrationModel.cs' @(
        'CrossingWeavePolicy => ((turn - 1) % 4) switch') 'Checkpoint 21b corrected crossing-weave switch expression'
    if (Select-String -Path '.\src\StarCluster.ScenarioRunner\FullFlightCalibrationModel.cs' -SimpleMatch 'CrossingWeavePolicy => (turn - 1) % 4 switch' -Quiet) {
        throw 'The malformed unparenthesized crossing-weave switch expression is still present.'
    }
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\FullFlightCalibrationRunner.cs' @(
        'public const int MaximumVariantWorkers = 24;',
        'MaxDegreeOfParallelism = workerLimit',
        'Jobs = 1,',
        'full-flight-common-random-numbers-v2',
        'full-flight-execution.json',
        'full-flight-variant-execution.csv',
        'PeakActiveWorkers') 'Checkpoint 21b bounded scheduler and reporting'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\ScenarioRunnerSelfTests.cs' @(
        'full-flight safety caps scale with missile endurance',
        'crossing-weave is distinct and deterministic',
        'target-entered missile hex creates an authoritative opportunity',
        'terminal opportunity diagnostics match authoritative records',
        'operational safety caps classify stalled missiles',
        'variant scheduler honors the 24-worker ceiling') 'Checkpoint 21b runner self-tests'

    Write-Host '[6/13] Verifying the repaired 288-variant pursuit study...'
    $scenarioDirectory = '.\src\StarCluster.ScenarioRunner\Scenarios'
    $scenarioFiles = @(Get-ChildItem $scenarioDirectory -File -Filter '*.json')
    if ($scenarioFiles.Count -ne 7) {
        throw "Expected 7 deterministic scenario files, found $($scenarioFiles.Count)."
    }

    $studyDirectory = '.\src\StarCluster.ScenarioRunner\Studies'
    $catalogPath = Join-Path $studyDirectory 'checkpoint-20-representative-profiles.json'
    $pursuitPath = Join-Path $studyDirectory 'checkpoint-21-full-flight-pursuit.calibration.json'
    foreach ($path in @($catalogPath, $pursuitPath)) {
        if (-not (Test-Path $path)) {
            throw "Required Checkpoint 21b study file $path was not found."
        }
    }
    try {
        $catalog = Get-Content $catalogPath -Raw | ConvertFrom-Json
        $pursuit = Get-Content $pursuitPath -Raw | ConvertFrom-Json
    }
    catch {
        throw "Checkpoint 21b study JSON could not be parsed: $($_.Exception.Message)"
    }
    if ($pursuit.schemaVersion -ne 2 -or
        $pursuit.trialsPerVariant -ne 1000 -or
        $pursuit.minimumSafetyTurns -ne 8 -or
        $pursuit.safetyTurnBuffer -ne 4 -or
        $pursuit.fixedPdsTechnologyLevel -ne 4 -or
        $pursuit.fixedTargetEcmTechnologyLevel -ne 4) {
        throw 'Checkpoint 21b study requires schema 2, 1,000 trials, minimum 8 turns, safety buffer 4, PDS TL 4, and target ECM TL 4.'
    }
    $variantCount = (
        @($pursuit.missileProfiles).Count *
        @($pursuit.missileTechnologyLevels).Count *
        @($pursuit.targetPropulsionTechnologyLevels).Count *
        @($pursuit.targetMovementPolicies).Count *
        @($pursuit.datalinkConditions).Count)
    if ($variantCount -ne 288) {
        throw "Checkpoint 21b pursuit matrix contains $variantCount variants, expected 288."
    }
    if ((@($catalog.technologyLevels | Where-Object { [int]$_.shipMovementHexesPerTurn -le 0 })).Count -ne 0) {
        throw 'Every technology level requires a positive shipMovementHexesPerTurn value.'
    }
    $policyNames = @($pursuit.targetMovementPolicies | Sort-Object -Unique)
    if ($policyNames.Count -ne 4 -or
        $policyNames -notcontains 'stationary' -or
        $policyNames -notcontains 'straight-retreat' -or
        $policyNames -notcontains 'crossing-weave' -or
        $policyNames -notcontains 'turnback' -or
        $policyNames -contains 'lateral' -or
        $policyNames -contains 'reversal') {
        throw 'Checkpoint 21b movement policies must be stationary, straight-retreat, crossing-weave, and turnback.'
    }

    Write-Host '[7/13] Verifying synchronized Checkpoint 21b documentation...'
    foreach ($documentationFile in @(
        '.\docs\README.md',
        '.\docs\Prototype_TODO.md',
        '.\docs\checkpoints\Checkpoint_21b_CSharp_Switch_Expression_Build_Hotfix.md',
        '.\docs\validation\Checkpoint_21b_CSharp_Switch_Expression_Build_Hotfix.md',
        '.\docs\validation\archive\Checkpoint_21_Full_Flight_Missile_Pursuit_And_Guidance_Calibration.md',
        '.\docs\validation\archive\Checkpoint_21a_Full_Flight_Opportunity_Movement_Horizon_And_24_Worker_Scheduler_Repair.md',
        '.\docs\design\Technology_Calibration_And_Simulation_Architecture.md',
        '.\docs\design\Missile_Guidance_Datalink_Sensor_And_Seeker_Architecture.md',
        '.\src\StarCluster.ScenarioRunner\README.md',
        '.\src\StarCluster.Game\README.md')) {
        if (-not (Test-Path $documentationFile)) {
            throw "Required Checkpoint 21b documentation file $documentationFile was not found."
        }
    }
    Assert-FileContains '.\docs\validation\Checkpoint_21b_CSharp_Switch_Expression_Build_Hotfix.md' @(
        '506/506',
        'twenty-nine runner self-tests',
        '288 variants',
        '1,000 trials each',
        '--jobs 24',
        '864 paired marginals',
        'CrossingWeavePolicy => ((turn - 1) % 4) switch',
        'No mechanical Godot validation is required') 'Checkpoint 21b active validation runbook'
    Assert-FileContains '.\docs\checkpoints\Checkpoint_21b_CSharp_Switch_Expression_Build_Hotfix.md' @(
        'CS0019',
        'CrossingWeavePolicy => ((turn - 1) % 4) switch',
        'changes no Core mechanics',
        '288 repaired full-flight variants',
        'No mechanical Godot validation is required') 'Checkpoint 21b implementation record'
    $activeValidationFiles = @(Get-ChildItem '.\docs\validation' -File)
    if ($activeValidationFiles.Count -ne 1 -or
        $activeValidationFiles[0].Name -ne 'Checkpoint_21b_CSharp_Switch_Expression_Build_Hotfix.md') {
        throw 'Exactly the Checkpoint 21b validation runbook must remain active.'
    }

    Write-Host '[8/13] Verifying unchanged Concept v0.3s and reference library...'
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

    Write-Host '[9/13] Refreshing Godot metadata and building...'
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

    Write-Host '[10/13] Running 506 engine-independent tests...'
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

    Write-Host '[11/13] Running deterministic corpus and twenty-nine runner self-tests...'
    $deterministicOutputDirectory = '.\out\checkpoint-21b-deterministic'
    Remove-Item -Recurse -Force $deterministicOutputDirectory -ErrorAction SilentlyContinue
    $deterministicText = Invoke-Runner -Arguments @(
        'run-all',
        '--scenario-dir', $scenarioDirectory,
        '--output-dir', $deterministicOutputDirectory) -Description 'Deterministic scenario corpus'
    if ($deterministicText -notmatch 'Scenario preflight:\s+7 passed, 0 failed\.' -or
        $deterministicText -notmatch 'Scenarios:\s+7 passed, 0 failed, 7 total\.') {
        throw 'The deterministic runner did not report the expected 7/7 result.'
    }
    $selfTestText = Invoke-Runner -Arguments @(
        'self-test',
        '--scenario-file', (Join-Path $scenarioDirectory 'terminal-two-window-hit.json')) -Description 'Runner self-tests'
    if ($selfTestText -notmatch 'Runner self-tests:\s+29 passed, 0 failed, 29 total\.') {
        throw 'The runner did not report the expected 29/29 self-test result.'
    }

    Write-Host '[12/13] Proving worker-independent stochastic and variant-scheduler results...'
    $reproStudy = Join-Path $studyDirectory 'checkpoint-19-reproducibility.sweep.json'
    $reproHashes = @{}
    foreach ($jobs in @(1, 24)) {
        $outputDirectory = ".\out\checkpoint-21b-repro-j$jobs"
        Remove-Item -Recurse -Force $outputDirectory -ErrorAction SilentlyContinue
        $reproText = Invoke-Runner -Arguments @(
            'sweep',
            $reproStudy,
            '--jobs', $jobs.ToString(),
            '--checkpoint-every', '256',
            '--output-dir', $outputDirectory) -Description "Reproducibility sweep at jobs=$jobs"
        if ($reproText -notmatch 'Sweep preflight:\s+1 variants passed, 0 failed\.' -or
            $reproText -notmatch 'Sweep:\s+1 passed, 0 failed, 1 total\.') {
            throw "The jobs=$jobs reproducibility sweep did not report 1/1 passing variant."
        }
        $summaryPath = Join-Path $outputDirectory 'sweep-summary.json'
        $reproHashes[$jobs] = (Get-FileHash $summaryPath -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    if ($reproHashes[1] -ne $reproHashes[24]) {
        throw "Ordinary worker-independent hashes differ: jobs1=$($reproHashes[1]), jobs24=$($reproHashes[24])."
    }

    $schedulerHashes = @{}
    foreach ($jobs in @(1, 24)) {
        $outputDirectory = ".\out\checkpoint-21b-scheduler-repro-j$jobs"
        Remove-Item -Recurse -Force $outputDirectory -ErrorAction SilentlyContinue
        $schedulerText = Invoke-Runner -Arguments @(
            'pursuit-calibrate',
            $pursuitPath,
            '--jobs', $jobs.ToString(),
            '--trials', '32',
            '--output-dir', $outputDirectory) -Description "Full-flight scheduler reproducibility at jobs=$jobs"
        if ($schedulerText -notmatch 'Full-flight preflight:\s+288 variants across 4 missile profiles passed\.' -or
            $schedulerText -notmatch 'Full-flight calibration:\s+288 variants passed, 0 failed; 0 statistically contradictory paired marginals after Holm correction\.') {
            throw "The jobs=$jobs scheduler reproducibility run did not report 288 passing variants."
        }
        $schedulerHashes[$jobs] = (Get-Content (Join-Path $outputDirectory 'full-flight-result.sha256') -Raw).Trim()
        $execution = Get-Content (Join-Path $outputDirectory 'full-flight-execution.json') -Raw | ConvertFrom-Json
        if ($execution.schedulingStrategy -ne 'variant-level-bounded' -or
            $execution.requestedWorkers -ne $jobs -or
            $execution.workerLimit -ne $jobs -or
            $execution.innerTrialWorkersPerVariant -ne 1 -or
            $execution.peakActiveWorkers -lt 1 -or
            $execution.peakActiveWorkers -gt $jobs) {
            throw "The jobs=$jobs scheduler telemetry did not preserve the bounded one-inner-worker contract."
        }
        if ($jobs -eq 24 -and $execution.peakActiveWorkers -lt 2) {
            throw 'The 24-worker scheduler proof did not execute at least two variants concurrently.'
        }
    }
    if ($schedulerHashes[1] -ne $schedulerHashes[24]) {
        throw "Full-flight scheduler hashes differ: jobs1=$($schedulerHashes[1]), jobs24=$($schedulerHashes[24])."
    }

    Write-Host '[13/13] Running 288 repaired full-flight variants with 24 workers and finalizing...'
    $pursuitOutputDirectory = '.\out\checkpoint-21b-full-flight-pursuit-calibration'
    Remove-Item -Recurse -Force $pursuitOutputDirectory -ErrorAction SilentlyContinue
    $pursuitText = Invoke-Runner -Arguments @(
        'pursuit-calibrate',
        $pursuitPath,
        '--jobs', '24',
        '--output-dir', $pursuitOutputDirectory) -Description 'Repaired full-flight pursuit calibration'
    if ($pursuitText -notmatch 'Full-flight preflight:\s+288 variants across 4 missile profiles passed\.' -or
        $pursuitText -notmatch 'Full-flight execution:\s+peak\s+[0-9]+/24 active variant workers;' -or
        $pursuitText -notmatch 'Full-flight calibration:\s+288 variants passed, 0 failed; 0 statistically contradictory paired marginals after Holm correction\.') {
        throw 'The full-flight runner did not report 288 passing variants, 24-worker telemetry, and zero contradictory marginals.'
    }

    $summaryPath = Join-Path $pursuitOutputDirectory 'full-flight-summary.json'
    $summaryCsvPath = Join-Path $pursuitOutputDirectory 'full-flight-summary.csv'
    $marginalCsvPath = Join-Path $pursuitOutputDirectory 'full-flight-marginals.csv'
    $hashPath = Join-Path $pursuitOutputDirectory 'full-flight-result.sha256'
    $executionPath = Join-Path $pursuitOutputDirectory 'full-flight-execution.json'
    $executionCsvPath = Join-Path $pursuitOutputDirectory 'full-flight-variant-execution.csv'
    foreach ($outputFile in @(
        $summaryPath,
        $summaryCsvPath,
        $marginalCsvPath,
        $hashPath,
        $executionPath,
        $executionCsvPath)) {
        if (-not (Test-Path $outputFile)) {
            throw "Full-flight output $outputFile was not produced."
        }
    }

    $summary = Get-Content $summaryPath -Raw | ConvertFrom-Json
    $unpairedMarginals = @(
        $summary.marginals | Where-Object { -not $_.commonRandomNumbersVerified })
    $opportunityInvariantFailures = @(
        $summary.variants | Where-Object { [double]$_.terminalOpportunityInvariantFailureProbability -ne 0.0 })
    $unexplainedUnresolved = @(
        $summary.variants | Where-Object { [double]$_.unexplainedUnresolvedProbability -ne 0.0 })
    if (-not $summary.passed -or
        $summary.schemaVersion -ne 2 -or
        $summary.variantCount -ne 288 -or
        $summary.trialsPerVariant -ne 1000 -or
        $summary.marginalCount -ne 864 -or
        $summary.contradictoryMarginalCount -ne 0 -or
        $unpairedMarginals.Count -ne 0 -or
        $opportunityInvariantFailures.Count -ne 0 -or
        $unexplainedUnresolved.Count -ne 0) {
        throw 'Full-flight summary did not preserve the passing 288-variant, 864-paired-marginal, opportunity-invariant, and explained-resolution contract.'
    }

    $execution = Get-Content $executionPath -Raw | ConvertFrom-Json
    if ($execution.schedulingStrategy -ne 'variant-level-bounded' -or
        $execution.requestedWorkers -ne 24 -or
        $execution.workerLimit -ne 24 -or
        $execution.innerTrialWorkersPerVariant -ne 1 -or
        $execution.peakActiveWorkers -lt 2 -or
        $execution.peakActiveWorkers -gt 24 -or
        $execution.variantCount -ne 288 -or
        $execution.trialsPerVariant -ne 1000 -or
        [long]$execution.totalTrials -ne 288000 -or
        @($execution.variants).Count -ne 288) {
        throw 'Full-flight execution telemetry did not preserve the requested 24-worker bounded scheduler contract.'
    }

    Write-Host ''
    Write-Host 'Checkpoint 21b completed successfully.'
    Write-Host 'The crossing-weave C# switch-expression build defect is repaired; Checkpoint 21a mechanics are unchanged.'
    Write-Host 'Engine-independent tests passed: 506.'
    Write-Host 'Deterministic headless scenarios passed: 7.'
    Write-Host 'Runner self-tests passed: 29.'
    Write-Host "Ordinary worker-independent reproducibility hash: $($reproHashes[1])."
    Write-Host "Full-flight scheduler reproducibility hash: $($schedulerHashes[1])."
    Write-Host "Peak active full-flight variant workers: $($execution.peakActiveWorkers)/24."
    Write-Host 'Full-flight pursuit variants passed: 288.'
    Write-Host "Paired full-flight marginals verified: $($summary.marginalCount)."
    Write-Host 'Terminal-opportunity invariant failures: 0.'
    Write-Host 'Unexplained unresolved outcomes: 0.'
    Write-Host 'Statistically contradictory paired marginals after Holm correction: 0.'
    Write-Host "Full-flight result hash: $((Get-Content $hashPath -Raw).Trim())."
    Write-Host 'No mechanical Godot validation is required.'
    Write-Host 'Preserve out\checkpoint-21b-full-flight-pursuit-calibration for review.'
}
finally {
    Pop-Location
}
