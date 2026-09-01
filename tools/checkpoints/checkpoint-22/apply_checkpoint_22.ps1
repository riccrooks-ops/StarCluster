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
        throw "$Description file $Path was not found. Re-extract the complete Checkpoint 22 package."
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
    Write-Host '[1/13] Verifying repository and accepted Checkpoint 21e baseline...'
    if (-not (Test-Path '.\StarCluster.sln')) {
        throw "StarCluster.sln was not found at $repositoryRoot. Extract the package into the repository root."
    }
    foreach ($baselineFile in @(
        '.\docs\checkpoints\Checkpoint_18d_Scenario_Corpus_And_Preflight_Hotfix.md',
        '.\docs\checkpoints\Checkpoint_19a_Validation_Runbook_Guard_Hotfix.md',
        '.\docs\checkpoints\Checkpoint_20b_Paired_Calibration_And_Statistical_Gate_Repair.md',
        '.\docs\checkpoints\Checkpoint_21d_Nullable_Dequeue_Build_Hotfix.md',
        '.\docs\checkpoints\Checkpoint_21e_Global_Trial_Block_Scheduler_And_Scaling_Gate.md',
        '.\docs\checkpoints\Checkpoint_22_Monte_Carlo_Allocation_And_State_Preparation_Optimization.md',
        '.\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj',
        '.\src\StarCluster.ScenarioRunner\Studies\checkpoint-20-representative-profiles.json',
        '.\src\StarCluster.ScenarioRunner\Studies\checkpoint-21-full-flight-pursuit.calibration.json',
        '.\src\StarCluster.Core\Simulation\ScenarioInitializationService.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileInterceptionPhaseContext.cs')) {
        if (-not (Test-Path $baselineFile)) {
            throw "Required Checkpoint 22 baseline file $baselineFile was not found."
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
        Where-Object { $_.Name -ne 'Checkpoint_22_Monte_Carlo_Allocation_And_State_Preparation_Optimization.md' } |
        Remove-Item -Force

    Write-Host '[2/13] Confirming that Godot is closed...'
    $godotProcesses = Get-Process -ErrorAction SilentlyContinue |
        Where-Object { $_.ProcessName -like 'Godot*' }
    if ($godotProcesses) {
        $processNames = ($godotProcesses.ProcessName | Sort-Object -Unique) -join ', '
        throw "Close Godot before applying Checkpoint 22. Running process(es): $processNames"
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
        'MissileInterceptionOpportunity.PreTerminalAttack;') 'Checkpoint 22 interception policy'
    Assert-FileContains '.\src\StarCluster.Core\Simulation\ScenarioInitializationService.cs' @(
        'restoredGuidancePhaseCount = Math.Max(',
        'definition.RetainedDatalink.ReceivedGuidancePhase') 'Checkpoint 22 shared initialization'
    Assert-FileContains '.\src\StarCluster.Core\Combat\Missiles\MissileAutonomousGuidanceService.cs' @(
        'MissileGuidanceArbitrator.Select(',
        'MissileLocalSensorService.Observe(',
        'MissileRoutePlanner.FindRoute(') 'Checkpoint 22 authoritative guidance path'
    Assert-FileContains '.\src\StarCluster.Core\Combat\Missiles\MissileTerminalResolutionService.cs' @(
        'MissileTerminalOutcome.Dud',
        'MissileTerminalOutcome.CriticalHit') 'Checkpoint 22 terminal contract'

    Write-Host '[5/13] Verifying compact metrics, reusable preparation, allocation telemetry, parity seams, and source symbols...'
    foreach ($runnerFile in @(
        '.\src\StarCluster.ScenarioRunner\FullFlightCalibrationDocuments.cs',
        '.\src\StarCluster.ScenarioRunner\FullFlightCalibrationModel.cs',
        '.\src\StarCluster.ScenarioRunner\FullFlightCalibrationRunner.cs',
        '.\src\StarCluster.ScenarioRunner\MonteCarloTrialResult.cs',
        '.\src\StarCluster.ScenarioRunner\ScenarioExecutionMetrics.cs',
        '.\src\StarCluster.ScenarioRunner\ScenarioExecutionPlan.cs',
        '.\src\StarCluster.ScenarioRunner\ScenarioExecutor.cs',
        '.\src\StarCluster.ScenarioRunner\ScenarioRunnerSelfTests.cs',
        '.\src\StarCluster.ScenarioRunner\Program.cs')) {
        if (-not (Test-Path $runnerFile)) {
            throw "Required Checkpoint 22 runner file $runnerFile was not found."
        }
    }
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj' @(
        '<ServerGarbageCollection>true</ServerGarbageCollection>',
        '<ConcurrentGarbageCollection>true</ConcurrentGarbageCollection>') 'Checkpoint 22 GC configuration'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\FullFlightCalibrationRunner.cs' @(
        'public readonly record struct TrialBlock(',
        'CreateTrialBlocks(',
        'ExecuteWithGlobalTrialBlocks(',
        'global-trial-block-workers',
        'GC.GetTotalAllocatedBytes(precise: false)',
        'GCSettings.IsServerGC',
        'Full-flight progress:',
        'ComputeTrialsPerSecond',
        'ProcessAffinityProcessorCount',
        'TrialExecutionMode = trialExecutionMode.ToString()',
        'AllocatedBytesPerTrial') 'Checkpoint 22 global trial scheduler'
    Assert-FileNotContains '.\src\StarCluster.ScenarioRunner\FullFlightCalibrationRunner.cs' @(
        'ExecuteWithDedicatedVariantWorkers(',
        'dedicated-variant-workers',
        'MonteCarloBatchRunner.Run(') 'Checkpoint 22 rejected coarse scheduler'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\ScenarioExecutionPlan.cs' @(
        'ScenarioInitializationRequest InitializationRequest',
        'ProbabilityMissileInterceptionProfile InterceptionProfile',
        'CreateDefenses(',
        'ParseActionKind(') 'Checkpoint 22 reusable execution plan'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\ScenarioExecutionOptions.cs' @(
        'RecordDiagnostics',
        'CaptureExecutionMetrics') 'Checkpoint 22 execution options'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\MonteCarloTrialResult.cs' @(
        'MonteCarloTrialExecutionMode',
        'DiagnosticJournal',
        'CompactMetrics',
        'ScenarioExecutionPlan executionPlan') 'Checkpoint 22 compact trial path'
    Assert-FileContains '.\src\StarCluster.Core\Simulation\ScenarioInitializationService.cs' @(
        'bool recordDiagnostics = true',
        'RefreshAllTracksWithoutResults(') 'Checkpoint 22 compact initialization and tracking'
    Assert-FileContains '.\src\StarCluster.Core\Combat\Tracking\TacticalTrackUpdateService.cs' @(
        'ApplyWithoutResult(',
        'ApplyCore(') 'Checkpoint 22 allocation-conscious track mutation'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\FullFlightCalibrationDocuments.cs' @(
        'public int SchemaVersion { get; init; } = 3;',
        'public int SchemaVersion { get; init; } = 4;',
        'SchedulingStrategy { get; init; } = "global-trial-block-workers";',
        'TrialBlockCount',
        'ComputeTrialsPerSecond',
        'EffectiveProcessorCores',
        'ServerGarbageCollection',
        'TrialExecutionMode',
        'AllocatedBytesPerTrial') 'Checkpoint 22 execution telemetry'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\ScenarioRunnerSelfTests.cs' @(
        'trial-block sizing preserves bounded granularity',
        'trial blocks cover every variant trial exactly once',
        'scenario runner uses server garbage collection',
        'scenario execution plans reuse immutable preparation',
        'compact and diagnostic trials preserve identical outcomes',
        'compact trials suppress diagnostic journal materialization',
        'compact track refresh preserves authoritative final state') 'Checkpoint 22 scheduler and compact-mode tests'

    Assert-FileContains '.\src\StarCluster.ScenarioRunner\ScenarioExecutionMetrics.cs' @(
        'StarCluster.Core.Combat.Tracking.SensorMode.Active') 'Checkpoint 22 SensorMode namespace contract'
    Assert-FileNotContains '.\src\StarCluster.ScenarioRunner\ScenarioExecutionMetrics.cs' @(
        'StarCluster.Core.Combat.SensorMode.Active') 'Checkpoint 22 stale SensorMode namespace guard'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\ScenarioRunnerSelfTests.cs' @(
        'ScenarioDocumentSerialization.CompactWriteOptions') 'Checkpoint 22 compact serializer option contract'
    Assert-FileNotContains '.\src\StarCluster.ScenarioRunner\ScenarioRunnerSelfTests.cs' @(
        'ScenarioDocumentSerialization.WriteOptions') 'Checkpoint 22 stale serializer option guard'

    Write-Host '[6/13] Verifying the unchanged 288-variant pursuit study and relative-motion corpus...'
    $scenarioDirectory = '.\src\StarCluster.ScenarioRunner\Scenarios'
    $studyDirectory = '.\src\StarCluster.ScenarioRunner\Studies'
    $catalogPath = Join-Path $studyDirectory 'checkpoint-20-representative-profiles.json'
    $pursuitPath = Join-Path $studyDirectory 'checkpoint-21-full-flight-pursuit.calibration.json'
    foreach ($path in @($catalogPath, $pursuitPath)) {
        if (-not (Test-Path $path)) { throw "Required study file $path was not found." }
        Get-Content $path -Raw | ConvertFrom-Json | Out-Null
    }
    $catalog = Get-Content $catalogPath -Raw | ConvertFrom-Json
    $pursuit = Get-Content $pursuitPath -Raw | ConvertFrom-Json
    if ($pursuit.id -ne 'checkpoint-21c-full-flight-pursuit-calibration' -or
        $pursuit.trialsPerVariant -ne 1000 -or
        @($pursuit.missileProfiles).Count -ne 4 -or
        @($pursuit.missileTechnologyLevels).Count -ne 3 -or
        @($pursuit.targetPropulsionTechnologyLevels).Count -ne 3 -or
        @($pursuit.targetMovementPolicies).Count -ne 4 -or
        @($pursuit.datalinkConditions).Count -ne 2) {
        throw 'Checkpoint 22 requires the unchanged Checkpoint 21c pursuit study metadata and cardinality.'
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
        throw 'Checkpoint 22 requires the four accepted relative-motion trajectories.'
    }
    if ((@($catalog.technologyLevels | Where-Object { [int]$_.shipMovementHexesPerTurn -le 0 })).Count -ne 0) {
        throw 'Every technology level requires a positive shipMovementHexesPerTurn value.'
    }

    Write-Host '[7/13] Verifying synchronized Checkpoint 22 documentation...'
    foreach ($documentationFile in @(
        '.\docs\README.md',
        '.\docs\Prototype_TODO.md',
        '.\docs\checkpoints\Checkpoint_22_Monte_Carlo_Allocation_And_State_Preparation_Optimization.md',
        '.\docs\validation\Checkpoint_22_Monte_Carlo_Allocation_And_State_Preparation_Optimization.md',
        '.\docs\validation\archive\Checkpoint_21e_Global_Trial_Block_Scheduler_And_Scaling_Gate.md',
        '.\docs\design\Technology_Calibration_And_Simulation_Architecture.md',
        '.\src\StarCluster.ScenarioRunner\README.md',
        '.\src\StarCluster.Game\README.md')) {
        if (-not (Test-Path $documentationFile)) {
            throw "Required Checkpoint 22 documentation file $documentationFile was not found."
        }
    }
    Assert-FileContains '.\docs\validation\Checkpoint_22_Monte_Carlo_Allocation_And_State_Preparation_Optimization.md' @(
        '506/506',
        'forty-one runner self-tests',
        '--jobs 1',
        '--jobs 24',
        '32 trials per variant',
        'no more than 20 percent',
        'at least 80 percent lower',
        'at least 90 percent lower',
        'No mechanical Godot validation is required') 'Checkpoint 22 active validation runbook'
    Assert-FileContains '.\docs\checkpoints\Checkpoint_22_Monte_Carlo_Allocation_And_State_Preparation_Optimization.md' @(
        'Reusable execution preparation',
        'Compact Monte Carlo execution',
        'Behavioral equivalence and performance gates',
        'DiagnosticJournal',
        'CompactMetrics') 'Checkpoint 22 implementation record'
    $activeValidationFiles = @(Get-ChildItem '.\docs\validation' -File)
    if ($activeValidationFiles.Count -ne 1 -or
        $activeValidationFiles[0].Name -ne 'Checkpoint_22_Monte_Carlo_Allocation_And_State_Preparation_Optimization.md') {
        throw 'Exactly the Checkpoint 22 validation runbook must remain active.'
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

    Write-Host '[11/13] Running deterministic corpus and forty-one runner self-tests...'
    $deterministicOutputDirectory = '.\out\checkpoint-22-deterministic'
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
    if ($selfTestText -notmatch 'Runner self-tests:\s+41 passed, 0 failed, 41 total\.') {
        throw 'The runner did not report the expected 41/41 self-test result.'
    }

    Write-Host '[12/13] Proving ordinary worker independence, compact parity, and allocation reduction...'
    $reproStudy = Join-Path $studyDirectory 'checkpoint-19-reproducibility.sweep.json'
    $reproHashes = @{}
    foreach ($jobs in @(1, 24)) {
        $outputDirectory = ".\out\checkpoint-22-repro-j$jobs"
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

    $proofRuns = @(
        @{ Name = 'diagnostic-j24'; Jobs = 24; Mode = 'diagnostic'; Directory = '.\out\checkpoint-22-diagnostic-proof-j24' },
        @{ Name = 'compact-j1'; Jobs = 1; Mode = 'compact'; Directory = '.\out\checkpoint-22-compact-proof-j1' },
        @{ Name = 'compact-j24'; Jobs = 24; Mode = 'compact'; Directory = '.\out\checkpoint-22-compact-proof-j24' }
    )
    $proofHashes = @{}
    $proofExecutions = @{}
    foreach ($proof in $proofRuns) {
        Remove-Item -Recurse -Force $proof.Directory -ErrorAction SilentlyContinue
        $proofText = Invoke-Runner -Arguments @(
            'pursuit-calibrate',
            $pursuitPath,
            '--scheduler-proof',
            '--jobs', $proof.Jobs.ToString(),
            '--trials', '32',
            '--trial-execution', $proof.Mode,
            '--output-dir', $proof.Directory) -Description "Checkpoint 22 $($proof.Name) proof"
        if ($proofText -notmatch 'Full-flight scheduler proof preflight:\s+24 variants across 4 missile profiles passed\.' -or
            $proofText -notmatch 'Full-flight scheduler proof:\s+24 variants passed, 0 failed; common random numbers verified; statistical gates skipped\.') {
            throw "The $($proof.Name) proof did not report 24/24 passing variants."
        }
        if ($proofText -notmatch 'Full-flight failure categories:\s+trial errors 0; datalink contract failures 0; terminal-opportunity invariant failures 0; unexplained unresolved outcomes 0\.') {
            throw "The $($proof.Name) proof reported a mechanical failure category."
        }
        $summary = Get-Content (Join-Path $proof.Directory 'full-flight-summary.json') -Raw | ConvertFrom-Json
        $execution = Get-Content (Join-Path $proof.Directory 'full-flight-execution.json') -Raw | ConvertFrom-Json
        $expectedMode = if ($proof.Mode -eq 'compact') { 'CompactMetrics' } else { 'DiagnosticJournal' }
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
            throw "The $($proof.Name) proof summary failed its semantic checks."
        }
        if ($execution.schemaVersion -ne 4 -or
            $execution.runMode -ne 'scheduler-proof' -or
            $execution.schedulingStrategy -ne 'global-trial-block-workers' -or
            $execution.trialExecutionMode -ne $expectedMode -or
            $execution.requestedWorkers -ne $proof.Jobs -or
            $execution.workerLimit -ne $proof.Jobs -or
            $execution.peakActiveWorkers -ne $proof.Jobs -or
            $execution.variantCount -ne 24 -or
            $execution.trialsPerVariant -ne 32 -or
            $execution.totalTrials -ne 768 -or
            $execution.trialBlockSize -ne 4 -or
            $execution.trialBlockCount -ne 192 -or
            $execution.completedTrialBlockCount -ne 192 -or
            $execution.serverGarbageCollection -ne $true -or
            [double]$execution.computeTrialsPerSecond -le 0 -or
            [double]$execution.allocatedBytesPerTrial -le 0) {
            throw "The $($proof.Name) proof telemetry failed its contract."
        }
        $proofHashes[$proof.Name] = (Get-Content (Join-Path $proof.Directory 'full-flight-result.sha256') -Raw).Trim()
        $proofExecutions[$proof.Name] = $execution
    }

    if ($proofHashes['diagnostic-j24'] -ne $proofHashes['compact-j1'] -or
        $proofHashes['diagnostic-j24'] -ne $proofHashes['compact-j24']) {
        throw "Diagnostic and compact proof hashes differ: diagnostic=$($proofHashes['diagnostic-j24']), compact-j1=$($proofHashes['compact-j1']), compact-j24=$($proofHashes['compact-j24'])."
    }

    $singleRate = [double]$proofExecutions['compact-j1'].computeTrialsPerSecond
    $parallelRate = [double]$proofExecutions['compact-j24'].computeTrialsPerSecond
    $speedup = $parallelRate / $singleRate
    $diagnosticAllocation = [double]$proofExecutions['diagnostic-j24'].allocatedBytesPerTrial
    $compactAllocation = [double]$proofExecutions['compact-j24'].allocatedBytesPerTrial
    $allocationRatio = $compactAllocation / $diagnosticAllocation
    $projectedSeconds = 288000.0 / $parallelRate
    Write-Host ("       Compact proof: {0:N2} trials/s at jobs=1; {1:N2} trials/s at jobs=24; {2:N2}x speedup." -f $singleRate, $parallelRate, $speedup)
    Write-Host ("       Allocation proof: diagnostic {0:N0} bytes/trial; compact {1:N0} bytes/trial; compact ratio {2:P1}." -f $diagnosticAllocation, $compactAllocation, $allocationRatio)
    Write-Host ("       Projected 288,000-trial compact compute time: {0:N1} minutes." -f ($projectedSeconds / 60.0))
    if ($speedup -lt 2.0) {
        throw ("Compact 24-worker execution achieved only {0:N2}x speedup. The full calibration was not started." -f $speedup)
    }
    if ($allocationRatio -gt 0.20) {
        throw ("Compact execution retained {0:P1} of diagnostic allocation, above the 20 percent limit. The full calibration was not started." -f $allocationRatio)
    }
    if ($projectedSeconds -gt 1800.0) {
        throw ("The compact proof projects {0:N1} minutes for the full study, above the 30-minute safety limit." -f ($projectedSeconds / 60.0))
    }

    Write-Host '[13/13] Running the unchanged 288-variant calibration through compact metrics and finalizing...'
    $fullOutputDirectory = '.\out\checkpoint-22-full-flight-pursuit-calibration'
    Remove-Item -Recurse -Force $fullOutputDirectory -ErrorAction SilentlyContinue
    $fullText = Invoke-Runner -Arguments @(
        'pursuit-calibrate',
        $pursuitPath,
        '--jobs', '24',
        '--trial-execution', 'compact',
        '--output-dir', $fullOutputDirectory) -Description 'Checkpoint 22 compact full-flight calibration'
    if ($fullText -notmatch 'Full-flight preflight:\s+288 variants across 4 missile profiles passed\.' -or
        $fullText -notmatch 'Full-flight calibration:\s+288 variants passed, 0 failed; 0 statistically contradictory inferential paired marginals after Holm correction; 144 descriptive relative-motion marginals\.') {
        throw 'The compact full-flight calibration did not report its expected passing result.'
    }
    if ($fullText -notmatch 'Full-flight failure categories:\s+trial errors 0; datalink contract failures 0; terminal-opportunity invariant failures 0; unexplained unresolved outcomes 0\.') {
        throw 'The compact full-flight calibration reported a mechanical failure category.'
    }

    $fullSummary = Get-Content (Join-Path $fullOutputDirectory 'full-flight-summary.json') -Raw | ConvertFrom-Json
    $fullExecution = Get-Content (Join-Path $fullOutputDirectory 'full-flight-execution.json') -Raw | ConvertFrom-Json
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
        throw 'The compact full-flight summary failed its Checkpoint 22 acceptance contract.'
    }
    if ($fullExecution.schemaVersion -ne 4 -or
        $fullExecution.runMode -ne 'calibration' -or
        $fullExecution.schedulingStrategy -ne 'global-trial-block-workers' -or
        $fullExecution.trialExecutionMode -ne 'CompactMetrics' -or
        $fullExecution.requestedWorkers -ne 24 -or
        $fullExecution.workerLimit -ne 24 -or
        $fullExecution.peakActiveWorkers -ne 24 -or
        $fullExecution.variantCount -ne 288 -or
        $fullExecution.trialsPerVariant -ne 1000 -or
        $fullExecution.totalTrials -ne 288000 -or
        $fullExecution.trialBlockSize -ne 16 -or
        $fullExecution.trialBlockCount -ne 18144 -or
        $fullExecution.completedTrialBlockCount -ne 18144 -or
        $fullExecution.serverGarbageCollection -ne $true) {
        throw 'The compact full-flight execution telemetry failed its 24-worker contract.'
    }

    $acceptedSummaryPath = '.\tools\checkpoints\checkpoint-22\reference\checkpoint-21e-full-flight-summary.csv'
    $acceptedMarginalsPath = '.\tools\checkpoints\checkpoint-22\reference\checkpoint-21e-full-flight-marginals.csv'
    $acceptedSummaryHash = (Get-FileHash $acceptedSummaryPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $acceptedMarginalsHash = (Get-FileHash $acceptedMarginalsPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($acceptedSummaryHash -ne '1632e624c6500dd09c5b68250b58622e8e6c24ad1f1b1369989b2e1d2baee0e9' -or
        $acceptedMarginalsHash -ne 'd54f916954db8051f50f698fc0f641f82ab22d1b82448aeebab3cbe4986856cc') {
        throw 'The packaged Checkpoint 21e behavioral reference files failed their locked hashes.'
    }
    $newSummaryHash = (Get-FileHash (Join-Path $fullOutputDirectory 'full-flight-summary.csv') -Algorithm SHA256).Hash.ToLowerInvariant()
    $newMarginalsHash = (Get-FileHash (Join-Path $fullOutputDirectory 'full-flight-marginals.csv') -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($newSummaryHash -ne $acceptedSummaryHash -or $newMarginalsHash -ne $acceptedMarginalsHash) {
        throw "Compact execution changed accepted behavior: summary=$newSummaryHash expected=$acceptedSummaryHash; marginals=$newMarginalsHash expected=$acceptedMarginalsHash."
    }

    $checkpoint21eAllocatedBytes = 6037761090128.0
    $checkpoint21eGen2Collections = 4117
    $allocationReduction = 1.0 - ([double]$fullExecution.allocatedBytes / $checkpoint21eAllocatedBytes)
    $gen2Reduction = 1.0 - ([double]$fullExecution.gen2Collections / $checkpoint21eGen2Collections)
    Write-Host ("       Full allocation reduction versus Checkpoint 21e: {0:P2} ({1:N0} bytes; {2:N0} bytes/trial)." -f $allocationReduction, [double]$fullExecution.allocatedBytes, [double]$fullExecution.allocatedBytesPerTrial)
    Write-Host ("       Full Gen 2 collection reduction versus Checkpoint 21e: {0:P2} ({1} collections)." -f $gen2Reduction, [int]$fullExecution.gen2Collections)
    if ($allocationReduction -lt 0.80) {
        throw ("Full-run allocation reduction was only {0:P2}; Checkpoint 22 requires at least 80 percent." -f $allocationReduction)
    }
    if ($gen2Reduction -lt 0.90) {
        throw ("Full-run Gen 2 reduction was only {0:P2}; Checkpoint 22 requires at least 90 percent." -f $gen2Reduction)
    }

    $canonicalHash = (Get-Content (Join-Path $fullOutputDirectory 'full-flight-result.sha256') -Raw).Trim()
    Write-Host ''
    Write-Host 'Checkpoint 22 completed successfully.'
    Write-Host 'Engine-independent tests passed: 506.'
    Write-Host 'Deterministic headless scenarios passed: 7.'
    Write-Host 'Runner self-tests passed: 41.'
    Write-Host "Ordinary worker-independent reproducibility hash: $($reproHashes[24])."
    Write-Host "Diagnostic and compact proof hash: $($proofHashes['compact-j24'])."
    Write-Host ("Compact 24-worker speedup: {0:N2}x." -f $speedup)
    Write-Host ("Compact proof allocation ratio: {0:P1}." -f $allocationRatio)
    Write-Host ("Full allocation reduction: {0:P2}." -f $allocationReduction)
    Write-Host ("Full Gen 2 collection reduction: {0:P2}." -f $gen2Reduction)
    Write-Host 'Accepted Checkpoint 21e summary and marginal CSV behavior reproduced exactly.'
    Write-Host 'Representative full-flight variants passed: 288.'
    Write-Host 'Inferential paired marginals verified: 720.'
    Write-Host 'Descriptive relative-motion marginals reported: 144.'
    Write-Host 'Mechanical failure categories: all zero.'
    Write-Host "Full-flight calibration result hash: $canonicalHash."
    Write-Host ("Full-flight compact compute throughput: {0:N2} trials/second over {1} ms." -f [double]$fullExecution.computeTrialsPerSecond, [long]$fullExecution.computeElapsedMilliseconds)
    Write-Host 'No mechanical Godot validation is required.'
    Write-Host 'Preserve out\checkpoint-22-full-flight-pursuit-calibration and the three proof directories for review.'
}
finally {
    Pop-Location
}
