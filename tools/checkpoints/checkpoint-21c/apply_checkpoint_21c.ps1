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
        throw "$Description file $Path was not found. Re-extract the complete Checkpoint 21c package."
    }
    foreach ($pattern in $Patterns) {
        if (-not (Select-String -Path $Path -SimpleMatch $pattern -Quiet)) {
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
        throw "$Description file $Path was not found."
    }
    foreach ($pattern in $Patterns) {
        if (Select-String -Path $Path -SimpleMatch $pattern -Quiet) {
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
    Write-Host '[1/13] Verifying repository and partially applied Checkpoint 21b baseline...'
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
        '.\docs\checkpoints\Checkpoint_21c_Full_Flight_Diagnostics_Semantic_Contracts_And_Dedicated_24_Worker_Repair.md',
        '.\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj',
        '.\src\StarCluster.ScenarioRunner\Studies\checkpoint-20-representative-profiles.json',
        '.\src\StarCluster.ScenarioRunner\Studies\checkpoint-21-full-flight-pursuit.calibration.json',
        '.\src\StarCluster.Core\Simulation\ScenarioInitializationService.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileInterceptionPhaseContext.cs')) {
        if (-not (Test-Path $baselineFile)) {
            throw "Required Checkpoint 21c baseline file $baselineFile was not found."
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
        Where-Object { $_.Name -ne 'Checkpoint_21c_Full_Flight_Diagnostics_Semantic_Contracts_And_Dedicated_24_Worker_Repair.md' } |
        Remove-Item -Force

    Write-Host '[2/13] Confirming that Godot is closed...'
    $godotProcesses = Get-Process -ErrorAction SilentlyContinue |
        Where-Object { $_.ProcessName -like 'Godot*' }
    if ($godotProcesses) {
        $processNames = ($godotProcesses.ProcessName | Sort-Object -Unique) -join ', '
        throw "Close Godot before applying Checkpoint 21c. Running process(es): $processNames"
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
        'MissileInterceptionOpportunity.PreTerminalAttack;') 'Checkpoint 21c interception policy'
    Assert-FileContains '.\src\StarCluster.Core\Simulation\ScenarioInitializationService.cs' @(
        'restoredGuidancePhaseCount = Math.Max(',
        'definition.RetainedDatalink.ReceivedGuidancePhase') 'Checkpoint 21c shared initialization'
    Assert-FileContains '.\src\StarCluster.Core\Combat\Missiles\MissileAutonomousGuidanceService.cs' @(
        'MissileGuidanceArbitrator.Select(',
        'MissileLocalSensorService.Observe(',
        'MissileRoutePlanner.FindRoute(') 'Checkpoint 21c authoritative guidance path'
    Assert-FileContains '.\src\StarCluster.Core\Combat\Missiles\MissileTerminalResolutionService.cs' @(
        'MissileTerminalOutcome.Dud',
        'MissileTerminalOutcome.CriticalHit') 'Checkpoint 21c terminal contract'

    Write-Host '[5/13] Verifying Search/Wait diagnostics, semantic datalinks, error evidence, and dedicated scheduling...'
    foreach ($runnerFile in @(
        '.\src\StarCluster.ScenarioRunner\FullFlightCalibrationDocuments.cs',
        '.\src\StarCluster.ScenarioRunner\FullFlightCalibrationModel.cs',
        '.\src\StarCluster.ScenarioRunner\FullFlightCalibrationRunner.cs',
        '.\src\StarCluster.ScenarioRunner\MonteCarloTrialResult.cs',
        '.\src\StarCluster.ScenarioRunner\MonteCarloBatchRunner.cs',
        '.\src\StarCluster.ScenarioRunner\PairedMarginalStatistics.cs',
        '.\src\StarCluster.ScenarioRunner\RunnerHashUtility.cs',
        '.\src\StarCluster.ScenarioRunner\ScenarioExecutor.cs',
        '.\src\StarCluster.ScenarioRunner\ScenarioRunnerSelfTests.cs',
        '.\src\StarCluster.ScenarioRunner\Program.cs')) {
        if (-not (Test-Path $runnerFile)) {
            throw "Required Checkpoint 21c runner file $runnerFile was not found."
        }
    }
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\ScenarioExecutor.cs' @(
        'RecordSearchWaitDiagnostic(',
        '"CandidateCoordinateReached"',
        'if (terminal.TargetCoLocated &&',
        'DiagnosticEventType.MissileSearchActivated',
        'DiagnosticEventType.MissileTerminalAcquisitionResolved') 'Checkpoint 21c Search/Wait diagnostic separation'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\MonteCarloTrialResult.cs' @(
        'DatalinkUpdateAttempted',
        'DatalinkLiveObserved',
        'TerminalOpportunityInvariantPassed',
        'result.TerminalOpportunities.Count') 'Checkpoint 21c trial semantics'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\MonteCarloBatchRunner.cs' @(
        'WriteErrorJournal(',
        '"errors.jsonl"',
        'if (options.Jobs == 1)',
        'if (options.KeepTrialJournal || options.Resume)') 'Checkpoint 21c compact error evidence'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\FullFlightCalibrationModel.cs' @(
        'PrepareSchedulerProofVariants(',
        'CrossingWeavePolicy => ((turn - 1) % 4) switch',
        'The scheduler proof corpus did not produce its expected unique variants.') 'Checkpoint 21c scheduler-proof corpus'
    Assert-FileNotContains '.\src\StarCluster.ScenarioRunner\FullFlightCalibrationModel.cs' @(
        'CrossingWeavePolicy => (turn - 1) % 4 switch') 'Checkpoint 21c crossing-weave parser guard'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\FullFlightCalibrationRunner.cs' @(
        'public const int MaximumVariantWorkers = 24;',
        'TaskCreationOptions.LongRunning',
        'ExecuteWithDedicatedVariantWorkers(',
        'Jobs = 1,',
        'full-flight-common-random-numbers-v3',
        'DatalinkSemanticContractPassed(',
        'expectedDirection != "descriptive"',
        'Full-flight failure categories:') 'Checkpoint 21c dedicated scheduler and reporting'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\PairedMarginalStatistics.cs' @(
        'expectedDirection != "descriptive"',
        'if (expectedDirection == "descriptive")',
        '"descriptive" => 1.0') 'Checkpoint 21c descriptive marginal support'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\RunnerHashUtility.cs' @(
        'Lazy<string> RunnerAssemblyHash',
        'LazyThreadSafetyMode.ExecutionAndPublication',
        'RunnerAssemblyHash.Value',
        'CoreAssemblyHash.Value') 'Checkpoint 21c thread-safe assembly-hash caching'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\Program.cs' @(
        'HasFlag(args, "--scheduler-proof")',
        '[--scheduler-proof]') 'Checkpoint 21c scheduler-proof CLI'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\ScenarioRunnerSelfTests.cs' @(
        'candidate-coordinate Search/Wait is not terminal acquisition',
        'discarded trial journals retain error details',
        'scheduler proof corpus has twenty-four stable variants',
        'relative-motion datalink comparisons can be descriptive',
        'semantic occlusion permits resolution before a guidance update') 'Checkpoint 21c self-test coverage'

    Write-Host '[6/13] Verifying the repaired deterministic corpus and 288-variant study...'
    $scenarioDirectory = '.\src\StarCluster.ScenarioRunner\Scenarios'
    $scenarioFiles = @(Get-ChildItem $scenarioDirectory -File -Filter '*.json')
    if ($scenarioFiles.Count -ne 7) {
        throw "Expected 7 deterministic scenarios, found $($scenarioFiles.Count)."
    }
    foreach ($scenarioFile in $scenarioFiles) {
        Get-Content $scenarioFile.FullName -Raw | ConvertFrom-Json | Out-Null
    }
    Assert-FileContains (Join-Path $scenarioDirectory 'blocked-retained-report-search.json') @(
        '"MissileDatalinkUpdated"',
        '"MissileTerminalAcquisitionResolved"',
        '"MissileGuidanceResolved"') 'Checkpoint 21c co-located blocked retained-report scenario'

    $studyDirectory = '.\src\StarCluster.ScenarioRunner\Studies'
    $catalogPath = Join-Path $studyDirectory 'checkpoint-20-representative-profiles.json'
    $pursuitPath = Join-Path $studyDirectory 'checkpoint-21-full-flight-pursuit.calibration.json'
    $catalog = Get-Content $catalogPath -Raw | ConvertFrom-Json
    $pursuit = Get-Content $pursuitPath -Raw | ConvertFrom-Json
    if ($pursuit.id -ne 'checkpoint-21c-full-flight-pursuit-calibration' -or
        $pursuit.trialsPerVariant -ne 1000 -or
        @($pursuit.missileProfiles).Count -ne 4 -or
        @($pursuit.missileTechnologyLevels).Count -ne 3 -or
        @($pursuit.targetPropulsionTechnologyLevels).Count -ne 3 -or
        @($pursuit.targetMovementPolicies).Count -ne 4 -or
        @($pursuit.datalinkConditions).Count -ne 2) {
        throw 'Checkpoint 21c pursuit study metadata or cardinality is incorrect.'
    }
    $variantCount = @($pursuit.missileProfiles).Count *
        @($pursuit.missileTechnologyLevels).Count *
        @($pursuit.targetPropulsionTechnologyLevels).Count *
        @($pursuit.targetMovementPolicies).Count *
        @($pursuit.datalinkConditions).Count
    if ($variantCount -ne 288) {
        throw "Expected 288 full-flight variants, calculated $variantCount."
    }
    $policyNames = @($pursuit.targetMovementPolicies | Sort-Object -Unique)
    if ($policyNames.Count -ne 4 -or
        $policyNames -notcontains 'stationary' -or
        $policyNames -notcontains 'straight-retreat' -or
        $policyNames -notcontains 'crossing-weave' -or
        $policyNames -notcontains 'turnback') {
        throw 'Checkpoint 21c requires the four accepted relative-motion trajectories.'
    }
    if ((@($catalog.technologyLevels | Where-Object { [int]$_.shipMovementHexesPerTurn -le 0 })).Count -ne 0) {
        throw 'Every technology level requires a positive shipMovementHexesPerTurn value.'
    }

    Write-Host '[7/13] Verifying synchronized Checkpoint 21c documentation...'
    foreach ($documentationFile in @(
        '.\docs\README.md',
        '.\docs\Prototype_TODO.md',
        '.\docs\checkpoints\Checkpoint_21c_Full_Flight_Diagnostics_Semantic_Contracts_And_Dedicated_24_Worker_Repair.md',
        '.\docs\validation\Checkpoint_21c_Full_Flight_Diagnostics_Semantic_Contracts_And_Dedicated_24_Worker_Repair.md',
        '.\docs\validation\archive\Checkpoint_21b_CSharp_Switch_Expression_Build_Hotfix.md',
        '.\docs\design\Technology_Calibration_And_Simulation_Architecture.md',
        '.\docs\design\Missile_Guidance_Datalink_Sensor_And_Seeker_Architecture.md',
        '.\src\StarCluster.ScenarioRunner\README.md',
        '.\src\StarCluster.Game\README.md')) {
        if (-not (Test-Path $documentationFile)) {
            throw "Required Checkpoint 21c documentation file $documentationFile was not found."
        }
    }
    Assert-FileContains '.\docs\validation\Checkpoint_21c_Full_Flight_Diagnostics_Semantic_Contracts_And_Dedicated_24_Worker_Repair.md' @(
        '506/506',
        'thirty-four runner self-tests',
        '--jobs 1',
        '--jobs 24',
        '24-variant scheduler corpus',
        '288 variants x 1,000 trials = 288,000 trials',
        '720 inferential and 144 descriptive marginals',
        'No mechanical Godot validation is required') 'Checkpoint 21c active validation runbook'
    Assert-FileContains '.\docs\checkpoints\Checkpoint_21c_Full_Flight_Diagnostics_Semantic_Contracts_And_Dedicated_24_Worker_Repair.md' @(
        'CandidateCoordinateReached',
        'semantic datalink contract',
        'dedicated long-running variant workers',
        '720 inferential rows',
        '144 crossing-weave/turnback datalink rows',
        'No mechanical Godot validation is required') 'Checkpoint 21c implementation record'
    $activeValidationFiles = @(Get-ChildItem '.\docs\validation' -File)
    if ($activeValidationFiles.Count -ne 1 -or
        $activeValidationFiles[0].Name -ne 'Checkpoint_21c_Full_Flight_Diagnostics_Semantic_Contracts_And_Dedicated_24_Worker_Repair.md') {
        throw 'Exactly the Checkpoint 21c validation runbook must remain active.'
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
    if (($solutionOutput | Out-String) -notmatch 'StarCluster.ScenarioRunner.csproj') {
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
    if (($testOutput | Out-String) -notmatch 'Passed:\s+506') {
        throw 'The complete suite did not report the expected 506 passed tests.'
    }
    if (Select-String -Path '.\src\StarCluster.Core\StarCluster.Core.csproj' -Pattern 'Godot' -Quiet) {
        throw 'StarCluster.Core unexpectedly contains a Godot dependency.'
    }

    Write-Host '[11/13] Running deterministic corpus and thirty-four runner self-tests...'
    $deterministicOutputDirectory = '.\out\checkpoint-21c-deterministic'
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
    if ($selfTestText -notmatch 'Runner self-tests:\s+34 passed, 0 failed, 34 total\.') {
        throw 'The runner did not report the expected 34/34 self-test result.'
    }

    Write-Host '[12/13] Proving ordinary stochastic and dedicated scheduler worker independence...'
    $reproStudy = Join-Path $studyDirectory 'checkpoint-19-reproducibility.sweep.json'
    $reproHashes = @{}
    foreach ($jobs in @(1, 24)) {
        $outputDirectory = ".\out\checkpoint-21c-repro-j$jobs"
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
        $reproHashes[$jobs] = (Get-FileHash (Join-Path $outputDirectory 'sweep-summary.json') -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    if ($reproHashes[1] -ne $reproHashes[24]) {
        throw "Ordinary worker-independent hashes differ: jobs1=$($reproHashes[1]), jobs24=$($reproHashes[24])."
    }

    $schedulerHashes = @{}
    foreach ($jobs in @(1, 24)) {
        $outputDirectory = ".\out\checkpoint-21c-scheduler-proof-j$jobs"
        Remove-Item -Recurse -Force $outputDirectory -ErrorAction SilentlyContinue
        $schedulerText = Invoke-Runner -Arguments @(
            'pursuit-calibrate',
            $pursuitPath,
            '--scheduler-proof',
            '--jobs', $jobs.ToString(),
            '--trials', '8',
            '--output-dir', $outputDirectory) -Description "Dedicated scheduler proof at jobs=$jobs"
        if ($schedulerText -notmatch 'Full-flight scheduler proof preflight:\s+24 variants across 4 missile profiles passed\.' -or
            $schedulerText -notmatch 'Full-flight scheduler proof:\s+24 variants passed, 0 failed; common random numbers verified; statistical gates skipped\.') {
            throw "The jobs=$jobs scheduler proof did not report 24/24 passing variants."
        }
        if ($schedulerText -notmatch 'Full-flight failure categories:\s+trial errors 0; datalink contract failures 0; terminal-opportunity invariant failures 0; unexplained unresolved outcomes 0\.') {
            throw "The jobs=$jobs scheduler proof reported a mechanical failure category."
        }
        $summary = Get-Content (Join-Path $outputDirectory 'full-flight-summary.json') -Raw | ConvertFrom-Json
        $execution = Get-Content (Join-Path $outputDirectory 'full-flight-execution.json') -Raw | ConvertFrom-Json
        if ($summary.schemaVersion -ne 3 -or
            $summary.runMode -ne 'scheduler-proof' -or
            $summary.statisticalGatesApplied -ne $false -or
            $summary.commonRandomNumbersVerified -ne $true -or
            $summary.variantCount -ne 24 -or
            $summary.marginalCount -ne 0 -or
            $summary.failedVariantCount -ne 0 -or
            $summary.trialErrorCount -ne 0 -or
            $summary.datalinkContractFailureCount -ne 0 -or
            $summary.terminalOpportunityInvariantFailureCount -ne 0 -or
            $summary.unexplainedUnresolvedCount -ne 0 -or
            $summary.passed -ne $true) {
            throw "The jobs=$jobs scheduler-proof summary failed its semantic checks."
        }
        $expectedPeak = $jobs
        if ($execution.schemaVersion -ne 2 -or
            $execution.runMode -ne 'scheduler-proof' -or
            $execution.schedulingStrategy -ne 'dedicated-variant-workers' -or
            $execution.requestedWorkers -ne $jobs -or
            $execution.workerLimit -ne $jobs -or
            $execution.peakActiveWorkers -ne $expectedPeak -or
            $execution.innerTrialWorkersPerVariant -ne 1 -or
            $execution.variantCount -ne 24 -or
            $execution.trialsPerVariant -ne 8 -or
            $execution.totalTrials -ne 192) {
            throw "The jobs=$jobs scheduler telemetry did not preserve the dedicated-worker contract."
        }
        $schedulerHashes[$jobs] = (Get-Content (Join-Path $outputDirectory 'full-flight-result.sha256') -Raw).Trim()
    }
    if ($schedulerHashes[1] -ne $schedulerHashes[24]) {
        throw "Scheduler-proof hashes differ: jobs1=$($schedulerHashes[1]), jobs24=$($schedulerHashes[24])."
    }

    Write-Host '[13/13] Running the 288-variant full-flight calibration at 24 workers and finalizing...'
    $fullOutputDirectory = '.\out\checkpoint-21c-full-flight-pursuit-calibration'
    Remove-Item -Recurse -Force $fullOutputDirectory -ErrorAction SilentlyContinue
    $fullText = Invoke-Runner -Arguments @(
        'pursuit-calibrate',
        $pursuitPath,
        '--jobs', '24',
        '--output-dir', $fullOutputDirectory) -Description 'Checkpoint 21c full-flight calibration'
    if ($fullText -notmatch 'Full-flight preflight:\s+288 variants across 4 missile profiles passed\.' -or
        $fullText -notmatch 'Full-flight calibration:\s+288 variants passed, 0 failed; 0 statistically contradictory inferential paired marginals after Holm correction; 144 descriptive relative-motion marginals\.') {
        throw 'The full-flight calibration did not report its expected passing result.'
    }
    if ($fullText -notmatch 'Full-flight failure categories:\s+trial errors 0; datalink contract failures 0; terminal-opportunity invariant failures 0; unexplained unresolved outcomes 0\.') {
        throw 'The full-flight calibration reported a mechanical failure category.'
    }

    $fullSummaryPath = Join-Path $fullOutputDirectory 'full-flight-summary.json'
    $fullExecutionPath = Join-Path $fullOutputDirectory 'full-flight-execution.json'
    $fullSummary = Get-Content $fullSummaryPath -Raw | ConvertFrom-Json
    $fullExecution = Get-Content $fullExecutionPath -Raw | ConvertFrom-Json
    if ($fullSummary.schemaVersion -ne 3 -or
        $fullSummary.runMode -ne 'calibration' -or
        $fullSummary.statisticalGatesApplied -ne $true -or
        $fullSummary.commonRandomNumbersVerified -ne $true -or
        $fullSummary.trialsPerVariant -ne 1000 -or
        $fullSummary.variantCount -ne 288 -or
        $fullSummary.marginalCount -ne 864 -or
        $fullSummary.inferentialMarginalCount -ne 720 -or
        $fullSummary.descriptiveMarginalCount -ne 144 -or
        $fullSummary.contradictoryMarginalCount -ne 0 -or
        $fullSummary.failedVariantCount -ne 0 -or
        $fullSummary.trialErrorCount -ne 0 -or
        $fullSummary.datalinkContractFailureCount -ne 0 -or
        $fullSummary.terminalOpportunityInvariantFailureCount -ne 0 -or
        $fullSummary.unexplainedUnresolvedCount -ne 0 -or
        $fullSummary.passed -ne $true) {
        throw 'The full-flight summary failed its Checkpoint 21c acceptance contract.'
    }
    if (@($fullSummary.variants | Where-Object { $_.passed -ne $true -or @($_.failureReasons).Count -ne 0 }).Count -ne 0) {
        throw 'At least one full-flight variant retained a failure reason.'
    }
    if (@($fullSummary.marginals | Where-Object { $_.statisticalGateApplied -eq $true }).Count -ne 720 -or
        @($fullSummary.marginals | Where-Object { $_.statisticalGateApplied -eq $false }).Count -ne 144 -or
        @($fullSummary.marginals | Where-Object { $_.statisticallyContradictory -eq $true }).Count -ne 0) {
        throw 'The full-flight marginal family did not contain 720 inferential and 144 descriptive passing rows.'
    }
    if ($fullExecution.schemaVersion -ne 2 -or
        $fullExecution.runMode -ne 'calibration' -or
        $fullExecution.schedulingStrategy -ne 'dedicated-variant-workers' -or
        $fullExecution.requestedWorkers -ne 24 -or
        $fullExecution.workerLimit -ne 24 -or
        $fullExecution.peakActiveWorkers -ne 24 -or
        $fullExecution.innerTrialWorkersPerVariant -ne 1 -or
        $fullExecution.variantCount -ne 288 -or
        $fullExecution.trialsPerVariant -ne 1000 -or
        $fullExecution.totalTrials -ne 288000) {
        throw 'The full-flight execution telemetry did not preserve the 24-worker contract.'
    }
    foreach ($requiredOutput in @(
        'full-flight-summary.json',
        'full-flight-summary.csv',
        'full-flight-marginals.csv',
        'full-flight-result.sha256',
        'full-flight-execution.json',
        'full-flight-variant-execution.csv')) {
        if (-not (Test-Path (Join-Path $fullOutputDirectory $requiredOutput))) {
            throw "The full-flight output is missing $requiredOutput."
        }
    }

    $canonicalHash = (Get-Content (Join-Path $fullOutputDirectory 'full-flight-result.sha256') -Raw).Trim()
    Write-Host ''
    Write-Host 'Checkpoint 21c completed successfully.'
    Write-Host 'Engine-independent tests passed: 506.'
    Write-Host 'Deterministic headless scenarios passed: 7.'
    Write-Host 'Runner self-tests passed: 34.'
    Write-Host "Ordinary worker-independent reproducibility hash: $($reproHashes[24])."
    Write-Host "Dedicated scheduler-proof hash: $($schedulerHashes[24])."
    Write-Host 'Scheduler proof variants passed: 24 at jobs 1 and jobs 24.'
    Write-Host 'Peak active variant workers at jobs 24: 24.'
    Write-Host 'Representative full-flight variants passed: 288.'
    Write-Host 'Inferential paired marginals verified: 720.'
    Write-Host 'Descriptive relative-motion marginals reported: 144.'
    Write-Host 'Mechanical failure categories: all zero.'
    Write-Host "Full-flight calibration result hash: $canonicalHash."
    Write-Host "Full-flight throughput: $([math]::Round([double]$fullExecution.trialsPerSecond, 2)) trials/second over $($fullExecution.elapsedMilliseconds) ms."
    Write-Host 'No mechanical Godot validation is required.'
    Write-Host 'Preserve out\checkpoint-21c-full-flight-pursuit-calibration for review.'
}
finally {
    Pop-Location
}
