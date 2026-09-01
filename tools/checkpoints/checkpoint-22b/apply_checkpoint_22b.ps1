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
        throw "$Description file $Path was not found. Re-extract Checkpoint 22b into the repository root."
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
    $output = & dotnet @dotnetArguments 2>&1
    $output | Write-Host
    if ($LASTEXITCODE -ne 0) {
        throw "$Description failed with exit code $LASTEXITCODE."
    }
    return ($output | Out-String)
}

try {
    Write-Host '[1/9] Verifying the partially applied Checkpoint 22a repository state...'
    foreach ($requiredFile in @(
        '.\StarCluster.sln',
        '.\global.json',
        '.\docs\checkpoints\Checkpoint_21e_Global_Trial_Block_Scheduler_And_Scaling_Gate.md',
        '.\docs\checkpoints\Checkpoint_22_Monte_Carlo_Allocation_And_State_Preparation_Optimization.md',
        '.\docs\checkpoints\Checkpoint_22a_Source_Symbol_Resolution_Hotfix.md',
        '.\docs\checkpoints\Checkpoint_22b_Allocation_Attribution_And_Optimization_Triage.md',
        '.\src\StarCluster.ScenarioRunner\Studies\checkpoint-21-full-flight-pursuit.calibration.json',
        '.\src\StarCluster.ScenarioRunner\ScenarioAllocationProfile.cs',
        '.\src\StarCluster.ScenarioRunner\AllocationProfileRunner.cs')) {
        if (-not (Test-Path $requiredFile)) {
            throw "Required Checkpoint 22b file $requiredFile was not found."
        }
    }

    Write-Host '[2/9] Confirming that Godot is closed...'
    $godotProcesses = Get-Process -ErrorAction SilentlyContinue |
        Where-Object { $_.ProcessName -like 'Godot*' }
    if ($godotProcesses) {
        $processNames = ($godotProcesses.ProcessName | Sort-Object -Unique) -join ', '
        throw "Close Godot before applying Checkpoint 22b. Running process(es): $processNames"
    }

    Write-Host '[3/9] Checking the pinned .NET SDK...'
    $sdkVersion = dotnet --version
    Write-Host "       SDK: $sdkVersion"
    if ($sdkVersion -ne '8.0.423') {
        throw "Expected .NET SDK 8.0.423 from global.json, but dotnet selected $sdkVersion."
    }

    Write-Host '[4/9] Verifying source contracts and rejecting stale symbols before compilation...'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\ScenarioExecutionMetrics.cs' @(
        'StarCluster.Core.Combat.Tracking.SensorMode.Active') 'Checkpoint 22a SensorMode correction'
    Assert-FileNotContains '.\src\StarCluster.ScenarioRunner\ScenarioExecutionMetrics.cs' @(
        'StarCluster.Core.Combat.SensorMode.Active') 'Checkpoint 22a SensorMode correction'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\ScenarioRunnerSelfTests.cs' @(
        'ScenarioDocumentSerialization.CompactWriteOptions',
        'profiled trials preserve canonical outcomes',
        'allocation attribution records a bounded stage hierarchy') 'Checkpoint 22b self-tests'
    Assert-FileNotContains '.\src\StarCluster.ScenarioRunner\ScenarioRunnerSelfTests.cs' @(
        'ScenarioDocumentSerialization.WriteOptions') 'Checkpoint 22a serializer correction'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\ScenarioAllocationProfile.cs' @(
        'GC.GetAllocatedBytesForCurrentThread()',
        'TrialTotal,',
        'MissileGuidanceAdvance,') 'Checkpoint 22b allocation profiler'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\AllocationProfileRunner.cs' @(
        'PrepareSchedulerProofVariants',
        'TopLevelAttributionCoverage',
        'allocation-profile-summary.json',
        'allocation-stages.csv',
        'allocation-trials.csv',
        'DiagnosticJournal',
        'CompactMetrics') 'Checkpoint 22b profile corpus'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\MonteCarloTrialResult.cs' @(
        'ScenarioAllocationProfile? allocationProfile = null',
        'ScenarioAllocationStage.ResultProjection',
        'ScenarioAllocationStage.TrialTotal') 'Checkpoint 22b trial attribution'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\ScenarioExecutor.cs' @(
        'ScenarioAllocationStage.RuntimeInitialization',
        'ScenarioAllocationStage.ShipMovement',
        'ScenarioAllocationStage.MissileAdvancement',
        'ScenarioAllocationStage.PhaseAdvancement',
        'ScenarioAllocationStage.ScenarioFinalization') 'Checkpoint 22b executor attribution'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\Program.cs' @(
        '"allocation-profile" or "profile-allocations"',
        'RunAllocationProfile(args)') 'Checkpoint 22b command surface'

    Write-Host '[5/9] Performing a clean compiler preflight with warnings as errors...'
    Get-ChildItem '.\src', '.\tests' -Directory -Recurse -Force -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -eq 'bin' -or $_.Name -eq 'obj' } |
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item '.\src\StarCluster.Game\.godot\mono\temp' -Recurse -Force -ErrorAction SilentlyContinue
    & dotnet build '.\StarCluster.sln' --nologo -warnaserror
    if ($LASTEXITCODE -ne 0) {
        throw "Clean dotnet build failed with exit code $LASTEXITCODE."
    }

    Write-Host '[6/9] Running 506 engine-independent tests...'
    & dotnet test '.\tests\StarCluster.Tests\StarCluster.Tests.csproj' --no-build --nologo
    if ($LASTEXITCODE -ne 0) {
        throw "dotnet test failed with exit code $LASTEXITCODE."
    }

    Write-Host '[7/9] Running deterministic scenarios and forty-three runner self-tests...'
    $deterministicOutput = '.\out\checkpoint-22b-deterministic'
    Remove-Item $deterministicOutput -Recurse -Force -ErrorAction SilentlyContinue
    $scenarioText = Invoke-Runner -Arguments @(
        'run-all',
        '--scenario-dir', '.\src\StarCluster.ScenarioRunner\Scenarios',
        '--output-dir', $deterministicOutput) -Description 'Checkpoint 22b deterministic corpus'
    if ($scenarioText -notmatch 'Scenario preflight:\s+7 passed, 0 failed\.' -or
        $scenarioText -notmatch 'Scenarios:\s+7 passed, 0 failed, 7 total\.') {
        throw 'The deterministic corpus did not report seven passing scenarios.'
    }

    $selfTestText = Invoke-Runner -Arguments @(
        'self-test',
        '--scenario-file', '.\src\StarCluster.ScenarioRunner\Scenarios\terminal-two-window-hit.json') -Description 'Checkpoint 22b runner self-tests'
    if ($selfTestText -notmatch 'Runner self-tests:\s+43 passed, 0 failed, 43 total\.') {
        throw 'The runner self-tests did not report 43 passing tests.'
    }

    Write-Host '[8/9] Running the single-worker diagnostic and compact allocation corpus...'
    $profileOutput = '.\out\checkpoint-22b-allocation-profile'
    Remove-Item $profileOutput -Recurse -Force -ErrorAction SilentlyContinue
    $profileText = Invoke-Runner -Arguments @(
        'allocation-profile',
        '.\src\StarCluster.ScenarioRunner\Studies\checkpoint-21-full-flight-pursuit.calibration.json',
        '--trials', '4',
        '--warmup-trials', '1',
        '--output-dir', $profileOutput) -Description 'Checkpoint 22b allocation profile'
    if ($profileText -notmatch 'Allocation profile preflight:\s+24 scheduler-proof variants across 4 missile profiles passed\.' -or
        $profileText -notmatch 'Allocation profile parity:\s+96 matched, 0 failed\.' -or
        $profileText -notmatch 'Allocation profile:\s+PASS\.') {
        throw 'The allocation profile did not report its expected passing diagnostic contract.'
    }

    Write-Host '[9/9] Validating attribution artifacts and preserving the failed optimization gate...'
    $summaryPath = Join-Path $profileOutput 'allocation-profile-summary.json'
    $csvPath = Join-Path $profileOutput 'allocation-stages.csv'
    $trialCsvPath = Join-Path $profileOutput 'allocation-trials.csv'
    $reportPath = Join-Path $profileOutput 'allocation-profile-report.txt'
    foreach ($artifact in @($summaryPath, $csvPath, $trialCsvPath, $reportPath)) {
        if (-not (Test-Path $artifact)) {
            throw "Allocation profile artifact $artifact was not created."
        }
    }
    if (Test-Path (Join-Path $profileOutput 'parity-failures.txt')) {
        throw 'The allocation profile emitted parity failures.'
    }

    $summary = Get-Content $summaryPath -Raw | ConvertFrom-Json
    if ($summary.schemaVersion -ne 1 -or
        $summary.variantCount -ne 24 -or
        $summary.warmupTrialsPerVariant -ne 1 -or
        $summary.measuredTrialsPerVariant -ne 4 -or
        $summary.measuredTrialsPerMode -ne 96 -or
        $summary.parityFailureCount -ne 0 -or
        $summary.passed -ne $true -or
        $summary.modes.Count -ne 2) {
        throw 'The allocation profile summary failed its Checkpoint 22b contract.'
    }

    $trialRows = Import-Csv $trialCsvPath
    if ($trialRows.Count -ne 192) {
        throw "The per-trial allocation CSV contained $($trialRows.Count) rows instead of 192."
    }
    foreach ($requiredColumn in @(
        'mode',
        'variant_id',
        'profile_id',
        'trial_index',
        'global_allocated_bytes',
        'TrialTotal_bytes',
        'RuntimeInitialization_bytes',
        'ShipMovement_bytes',
        'MissileAdvancement_bytes',
        'ResultProjection_bytes')) {
        if ($requiredColumn -notin $trialRows[0].PSObject.Properties.Name) {
            throw "The per-trial allocation CSV is missing column $requiredColumn."
        }
    }
    if (($trialRows | Where-Object { $_.had_error -ne 'false' }).Count -ne 0) {
        throw 'The per-trial allocation CSV contains one or more trial errors.'
    }

    foreach ($modeName in @('DiagnosticJournal', 'CompactMetrics')) {
        $mode = $summary.modes | Where-Object { $_.mode -eq $modeName }
        if ($null -eq $mode -or
            $mode.trialCount -ne 96 -or
            $mode.errorCount -ne 0 -or
            $mode.hierarchyValid -ne $true -or
            [double]$mode.topLevelAttributionCoverage -lt 0.90 -or
            [double]$mode.globalBytesPerTrial -le 0 -or
            [double]$mode.profiledThreadBytesPerTrial -le 0 -or
            [double]$mode.profiledToGlobalAllocationRatio -lt 0.75 -or
            [double]$mode.profiledToGlobalAllocationRatio -gt 1.25) {
            throw "The $modeName allocation profile failed its measurement contract."
        }
        foreach ($stageName in @(
            'RuntimeInitialization',
            'ShipMovement',
            'MissileAdvancement',
            'PhaseAdvancement',
            'ScenarioFinalization',
            'ResultProjection')) {
            $stage = $mode.stages | Where-Object { $_.stage -eq $stageName -and $_.isDerived -eq $false }
            if ($null -eq $stage -or [long]$stage.invocationCount -le 0) {
                throw "The $modeName profile did not exercise stage $stageName."
            }
        }
    }

    $diagnostic = $summary.modes | Where-Object { $_.mode -eq 'DiagnosticJournal' }
    $compact = $summary.modes | Where-Object { $_.mode -eq 'CompactMetrics' }
    $diagnosticTotal = [double]$diagnostic.profiledThreadBytesPerTrial
    $compactTotal = [double]$compact.profiledThreadBytesPerTrial
    $compactRatio = $compactTotal / $diagnosticTotal
    $compactTop = $compact.stages |
        Where-Object { $_.level -eq 'TopLevel' } |
        Sort-Object -Property allocatedBytes -Descending |
        Select-Object -First 1
    $compactDetail = $compact.stages |
        Where-Object { $_.level -eq 'Detail' } |
        Sort-Object -Property allocatedBytes -Descending |
        Select-Object -First 1
    $compactResidual = $compact.stages |
        Where-Object { $_.level -eq 'Residual' } |
        Sort-Object -Property allocatedBytes -Descending |
        Select-Object -First 1

    Write-Host ''
    Write-Host 'Checkpoint 22b completed successfully as an allocation-attribution diagnostic.'
    Write-Host 'Engine-independent tests passed: 506.'
    Write-Host 'Deterministic headless scenarios passed: 7.'
    Write-Host 'Runner self-tests passed: 43.'
    Write-Host 'Profile corpus: 24 variants x 4 measured trials x 2 modes.'
    Write-Host 'Compact and diagnostic canonical parity: 96/96.'
    Write-Host ("Diagnostic allocation: {0:N0} profiled bytes/trial." -f $diagnosticTotal)
    Write-Host ("Compact allocation: {0:N0} profiled bytes/trial ({1:P1} of diagnostic)." -f $compactTotal, $compactRatio)
    Write-Host ("Largest compact top-level stage: {0} at {1:N0} bytes/trial ({2:P1})." -f $compactTop.stage, [double]$compactTop.bytesPerTrial, [double]$compactTop.percentOfTrialTotal)
    Write-Host ("Largest compact detail stage: {0} at {1:N0} bytes/trial ({2:P1})." -f $compactDetail.stage, [double]$compactDetail.bytesPerTrial, [double]$compactDetail.percentOfTrialTotal)
    Write-Host ("Largest compact residual stage: {0} at {1:N0} bytes/trial ({2:P1})." -f $compactResidual.stage, [double]$compactResidual.bytesPerTrial, [double]$compactResidual.percentOfTrialTotal)
    Write-Host 'Checkpoint 22 remains unaccepted; its 80 percent allocation-reduction gate was not relaxed.'
    Write-Host 'Checkpoint 21e remains the accepted behavioral baseline.'
    Write-Host "Preserve $profileOutput for assessment and the next targeted optimization pass."
}
finally {
    Pop-Location
}
