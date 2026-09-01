[CmdletBinding()]
param(
    [switch]$RepositoryContractOnly
)

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
        throw "$Description file $Path was not found. Re-extract Checkpoint 22d into the repository root."
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

function Assert-RepositoryManifest {
    param(
        [Parameter(Mandatory = $true)][string]$ManifestPath
    )

    if (-not (Test-Path $ManifestPath)) {
        throw "Repository manifest $ManifestPath was not found."
    }

    $verified = 0
    foreach ($line in Get-Content $ManifestPath) {
        if ([string]::IsNullOrWhiteSpace($line) -or $line.StartsWith('#')) {
            continue
        }
        $manifestMatch = [regex]::Match($line, '^([0-9a-fA-F]{64})  (.+)$')
        if (-not $manifestMatch.Success) {
            throw "Malformed repository manifest line: $line"
        }
        $expectedHash = $manifestMatch.Groups[1].Value.ToLowerInvariant()
        $relativePath = $manifestMatch.Groups[2].Value
        if (-not (Test-Path -LiteralPath $relativePath -PathType Leaf)) {
            throw "Manifest file $relativePath was not found."
        }
        $actualHash = (Get-FileHash -LiteralPath $relativePath -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actualHash -ne $expectedHash) {
            throw "Manifest hash mismatch for ${relativePath}: $actualHash expected $expectedHash."
        }
        $verified++
    }

    if ($verified -lt 400) {
        throw "Repository manifest verified only $verified files; a complete Checkpoint 22d archive is required."
    }
    Write-Host "       Repository manifest: $verified files verified."
}

function Assert-PowerShellScriptsParse {
    param(
        [Parameter(Mandatory = $true)][string]$RootPath
    )

    $parseFailures = @()
    $scriptCount = 0
    foreach ($scriptFile in Get-ChildItem -LiteralPath $RootPath -Filter '*.ps1' -File -Recurse) {
        $tokens = $null
        $parseErrors = $null
        [void][System.Management.Automation.Language.Parser]::ParseFile(
            $scriptFile.FullName,
            [ref]$tokens,
            [ref]$parseErrors)
        $scriptCount++
        foreach ($parseError in @($parseErrors | Where-Object { $null -ne $_ })) {
            $relativeScriptPath = Resolve-Path -LiteralPath $scriptFile.FullName -Relative
            $parseFailures += ("{0}:{1}:{2}: {3}" -f
                $relativeScriptPath,
                $parseError.Extent.StartLineNumber,
                $parseError.Extent.StartColumnNumber,
                $parseError.Message)
        }
    }

    if ($parseFailures.Count -gt 0) {
        throw ("PowerShell parser rejected the repository scripts:`n{0}" -f
            ($parseFailures -join "`n"))
    }
    Write-Host "       PowerShell parser: $scriptCount scripts parsed successfully."
}

function Ensure-ActiveValidationRunbook {
    param(
        [Parameter(Mandatory = $true)][string]$ValidationDirectory,
        [Parameter(Mandatory = $true)][string]$ExpectedFileName,
        [Parameter(Mandatory = $true)][string]$ArchiveDirectory
    )

    $expectedPath = Join-Path $ValidationDirectory $ExpectedFileName
    if (-not (Test-Path -LiteralPath $expectedPath -PathType Leaf)) {
        throw "Expected active validation runbook $expectedPath was not found."
    }

    $staleRunbooks = @(Get-ChildItem -LiteralPath $ValidationDirectory `
        -Filter 'Checkpoint_*.md' -File |
        Where-Object { $_.Name -ne $ExpectedFileName })

    if ($staleRunbooks.Count -gt 0) {
        [void](New-Item -ItemType Directory -Path $ArchiveDirectory -Force)
        foreach ($staleRunbook in $staleRunbooks) {
            $archivePath = Join-Path $ArchiveDirectory $staleRunbook.Name
            if (Test-Path -LiteralPath $archivePath -PathType Leaf) {
                $sourceHash = (Get-FileHash -LiteralPath $staleRunbook.FullName `
                    -Algorithm SHA256).Hash
                $archiveHash = (Get-FileHash -LiteralPath $archivePath `
                    -Algorithm SHA256).Hash
                if ($sourceHash -eq $archiveHash) {
                    Remove-Item -LiteralPath $staleRunbook.FullName -Force
                    Write-Host ("       Removed duplicate stale active runbook: {0}" -f `
                        $staleRunbook.Name)
                    continue
                }

                $baseName = [System.IO.Path]::GetFileNameWithoutExtension(
                    $staleRunbook.Name)
                $extension = [System.IO.Path]::GetExtension($staleRunbook.Name)
                $archiveName = "{0}_Imported_{1}{2}" -f `
                    $baseName,
                    ([guid]::NewGuid().ToString('N')),
                    $extension
                $archivePath = Join-Path $ArchiveDirectory $archiveName
            }

            Move-Item -LiteralPath $staleRunbook.FullName `
                -Destination $archivePath -Force
            Write-Host ("       Archived stale active runbook: {0}" -f `
                $staleRunbook.Name)
        }
    }

    $activeRunbooks = @(Get-ChildItem -LiteralPath $ValidationDirectory `
        -Filter 'Checkpoint_*.md' -File)
    if ($activeRunbooks.Count -ne 1 -or
        $activeRunbooks[0].Name -ne $ExpectedFileName) {
        $activeNames = @($activeRunbooks | ForEach-Object { $_.Name }) -join ', '
        throw ("Exactly the Checkpoint 22d validation runbook must remain active. " +
            "Found: $activeNames")
    }

    Write-Host "       Active validation runbook: $ExpectedFileName"
}

function Test-ActiveValidationRunbookNormalization {
    $testRoot = Join-Path ([System.IO.Path]::GetTempPath()) `
        ("star-cluster-checkpoint-22d-runbook-test-{0}" -f `
            ([guid]::NewGuid().ToString('N')))
    $validationDirectory = Join-Path $testRoot 'validation'
    $archiveDirectory = Join-Path $validationDirectory 'archive'
    $expectedName = `
        'Checkpoint_22d_Accepted_Baseline_Closure_And_Checkpoint_23_Handoff.md'
    $staleName = 'Checkpoint_22c_Calibration_Map_Sizing_And_Allocation_Repair.md'

    try {
        [void](New-Item -ItemType Directory -Path $validationDirectory -Force)
        [void](New-Item -ItemType Directory -Path $archiveDirectory -Force)
        Set-Content -LiteralPath (Join-Path $validationDirectory $expectedName) `
            -Value 'expected' -Encoding UTF8
        Set-Content -LiteralPath (Join-Path $validationDirectory $staleName) `
            -Value 'stale-active-copy' -Encoding UTF8
        Set-Content -LiteralPath (Join-Path $archiveDirectory $staleName) `
            -Value 'different-archived-copy' -Encoding UTF8

        Ensure-ActiveValidationRunbook `
            -ValidationDirectory $validationDirectory `
            -ExpectedFileName $expectedName `
            -ArchiveDirectory $archiveDirectory

        $remaining = @(Get-ChildItem -LiteralPath $validationDirectory `
            -Filter 'Checkpoint_*.md' -File)
        $imported = @(Get-ChildItem -LiteralPath $archiveDirectory `
            -Filter 'Checkpoint_22c_Calibration_Map_Sizing_And_Allocation_Repair_Imported_*.md' `
            -File)
        if ($remaining.Count -ne 1 -or
            $remaining[0].Name -ne $expectedName -or
            $imported.Count -ne 1) {
            throw 'Validation-runbook normalization self-test failed.'
        }

        Write-Host '       Validation-runbook normalization self-test: passed.'
    }
    finally {
        Remove-Item -LiteralPath $testRoot -Recurse -Force `
            -ErrorAction SilentlyContinue
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
    Write-Host '[1/12] Verifying the complete Checkpoint 22d repository archive and accepted baseline...'
    foreach ($requiredFile in @(
        '.\StarCluster.sln',
        '.\global.json',
        '.\tools\checkpoints\checkpoint-22b\apply_checkpoint_22b.ps1',
        '.\docs\checkpoints\Checkpoint_21e_Global_Trial_Block_Scheduler_And_Scaling_Gate.md',
        '.\docs\checkpoints\Checkpoint_22b_Allocation_Attribution_And_Optimization_Triage.md',
        '.\docs\checkpoints\Checkpoint_22c_Calibration_Map_Sizing_And_Allocation_Repair.md',
        '.\docs\checkpoints\Checkpoint_22d_Accepted_Baseline_Closure_And_Checkpoint_23_Handoff.md',
        '.\docs\validation\Checkpoint_22d_Accepted_Baseline_Closure_And_Checkpoint_23_Handoff.md',
        '.\CHECKPOINT_22D_SHA256SUMS.txt',
        '.\README.md',
        '.\src\StarCluster.Core\StarCluster.Core.csproj',
        '.\src\StarCluster.Game\StarCluster.Game.csproj',
        '.\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj',
        '.\tests\StarCluster.Tests\StarCluster.Tests.csproj',
        '.\src\StarCluster.ScenarioRunner\Studies\checkpoint-21-full-flight-pursuit.calibration.json',
        '.\src\StarCluster.ScenarioRunner\AllocationProfileRunner.cs',
        '.\src\StarCluster.ScenarioRunner\MapOptimizationRunner.cs',
        '.\src\StarCluster.Core\Simulation\ScenarioInitializationStageRecorder.cs',
        '.\tools\checkpoints\checkpoint-22\reference\checkpoint-21e-full-flight-summary.csv',
        '.\tools\checkpoints\checkpoint-22\reference\checkpoint-21e-full-flight-marginals.csv')) {
        if (-not (Test-Path $requiredFile)) {
            throw "Required Checkpoint 22d file $requiredFile was not found."
        }
    }
    Assert-RepositoryManifest '.\CHECKPOINT_22D_SHA256SUMS.txt'
    Assert-PowerShellScriptsParse '.\tools'
    Test-ActiveValidationRunbookNormalization

    if ($RepositoryContractOnly) {
        Write-Host '[2/12] Godot process check skipped for repository-contract-only preflight.'
        Write-Host '[3/12] .NET SDK check skipped for repository-contract-only preflight.'
    }
    else {
        Write-Host '[2/12] Confirming that Godot is closed...'
        $godotProcesses = Get-Process -ErrorAction SilentlyContinue |
            Where-Object { $_.ProcessName -like 'Godot*' }
        if ($godotProcesses) {
            $processNames = ($godotProcesses.ProcessName | Sort-Object -Unique) -join ', '
            throw "Close Godot before applying Checkpoint 22d. Running process(es): $processNames"
        }

        Write-Host '[3/12] Checking the pinned .NET SDK...'
        $sdkVersion = dotnet --version
        Write-Host "       SDK: $sdkVersion"
        if ($sdkVersion -ne '8.0.423') {
            throw "Expected .NET SDK 8.0.423 from global.json, but dotnet selected $sdkVersion."
        }
    }

    Write-Host '[4/12] Verifying map-sizing, initialization-attribution, and symbol contracts...'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\FullFlightCalibrationModel.cs' @(
        'ReferenceMapRadius = 192',
        'OptimizedMapSafetyMargin = 2',
        'FullFlightMapSizingMode.OptimizedVariant',
        'CalculateOptimizedMapRadius',
        'CalculateHexCellCount') 'Checkpoint 22d map sizing'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\MapOptimizationRunner.cs' @(
        'map-optimization-summary.json',
        'map-allocation-sweep.csv',
        'map-radius-variants.csv',
        'checkpoint-22c-map-parity-v1',
        'AverageCellRetentionRatio') 'Checkpoint 22d map proof'
    Assert-FileContains '.\src\StarCluster.Core\Simulation\ScenarioInitializationService.cs' @(
        'ScenarioInitializationStage.MapCreation',
        'ScenarioInitializationStage.InitialTrackRefresh',
        'IScenarioInitializationStageRecorder? stageRecorder') 'Checkpoint 22d initialization instrumentation'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\ScenarioAllocationProfile.cs' @(
        'IScenarioInitializationStageRecorder',
        'InitializationMapCreation',
        'InitializationResultConstruction') 'Checkpoint 22d allocation attribution'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\ScenarioRunnerSelfTests.cs' @(
        'optimized calibration maps are bounded and deterministic',
        'optimized and reference maps preserve canonical trial outcomes',
        'initialization attribution isolates map creation',
        'ScenarioDocumentSerialization.CompactWriteOptions') 'Checkpoint 22d self-tests'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\Program.cs' @(
        '"map-optimization-proof" or "prove-map-optimization"',
        'RunMapOptimizationProof(args)') 'Checkpoint 22d command surface'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\ScenarioExecutionMetrics.cs' @(
        'StarCluster.Core.Combat.Tracking.SensorMode.Active') 'Checkpoint 22a SensorMode correction'
    Assert-FileNotContains '.\src\StarCluster.ScenarioRunner\ScenarioExecutionMetrics.cs' @(
        'StarCluster.Core.Combat.SensorMode.Active') 'Checkpoint 22a SensorMode correction'
    Assert-FileNotContains '.\src\StarCluster.ScenarioRunner\ScenarioRunnerSelfTests.cs' @(
        'ScenarioDocumentSerialization.WriteOptions') 'Checkpoint 22a serializer correction'
    Assert-FileNotContains '.\src\StarCluster.ScenarioRunner\FullFlightCalibrationModel.cs' @(
        'Radius = 192,') 'Checkpoint 22d fixed-radius removal'
    Assert-FileContains '.\docs\checkpoints\Checkpoint_22d_Accepted_Baseline_Closure_And_Checkpoint_23_Handoff.md' @(
        'Accepted repository baseline',
        'Complete-archive release contract',
        'Checkpoint 23 handoff',
        '226677d3b9d2fded9e529ab5b897f6ec0e5251eb27937208f571cbb9b184ee28') 'Checkpoint 22d closure documentation'
    Assert-FileContains '.\docs\Prototype_TODO.md' @(
        'Checkpoint 22d accepted-baseline closure',
        'Checkpoint 23 independent Missile Flight subsystem-TL decomposition',
        'complete repository archive') 'Checkpoint 22d TODO handoff'
    Assert-FileContains '.\README.md' @(
        'Checkpoint 22d is the accepted repository baseline',
        'complete repository archives') 'Checkpoint 22d repository readme'

    Ensure-ActiveValidationRunbook `
        -ValidationDirectory '.\docs\validation' `
        -ExpectedFileName 'Checkpoint_22d_Accepted_Baseline_Closure_And_Checkpoint_23_Handoff.md' `
        -ArchiveDirectory '.\docs\validation\archive'

    if ($RepositoryContractOnly) {
        Write-Host ''
        Write-Host 'Checkpoint 22d repository-contract preflight completed successfully.'
        Write-Host 'Manifest, native parsing, runbook normalization, and source contracts passed.'
        return
    }

    Write-Host '[5/12] Performing a clean compiler preflight with warnings as errors...'
    Get-ChildItem '.\src', '.\tests' -Directory -Recurse -Force -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -eq 'bin' -or $_.Name -eq 'obj' } |
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item '.\src\StarCluster.Game\.godot\mono\temp' -Recurse -Force -ErrorAction SilentlyContinue
    & dotnet build '.\StarCluster.sln' --nologo -warnaserror
    if ($LASTEXITCODE -ne 0) {
        throw "Clean dotnet build failed with exit code $LASTEXITCODE."
    }

    Write-Host '[6/12] Running 506 engine-independent tests...'
    $testOutput = & dotnet test '.\tests\StarCluster.Tests\StarCluster.Tests.csproj' --no-build --nologo 2>&1
    $testOutput | Write-Host
    if ($LASTEXITCODE -ne 0) {
        throw "dotnet test failed with exit code $LASTEXITCODE."
    }
    if (($testOutput | Out-String) -notmatch 'Passed:\s+506') {
        throw 'The complete suite did not report the expected 506 passed tests.'
    }

    Write-Host '[7/12] Running deterministic scenarios and forty-six runner self-tests...'
    $deterministicOutput = '.\out\checkpoint-22d-deterministic'
    Remove-Item $deterministicOutput -Recurse -Force -ErrorAction SilentlyContinue
    $scenarioText = Invoke-Runner -Arguments @(
        'run-all',
        '--scenario-dir', '.\src\StarCluster.ScenarioRunner\Scenarios',
        '--output-dir', $deterministicOutput) -Description 'Checkpoint 22d deterministic corpus'
    if ($scenarioText -notmatch 'Scenario preflight:\s+7 passed, 0 failed\.' -or
        $scenarioText -notmatch 'Scenarios:\s+7 passed, 0 failed, 7 total\.') {
        throw 'The deterministic corpus did not report seven passing scenarios.'
    }
    $selfTestText = Invoke-Runner -Arguments @(
        'self-test',
        '--scenario-file', '.\src\StarCluster.ScenarioRunner\Scenarios\terminal-two-window-hit.json') -Description 'Checkpoint 22d runner self-tests'
    if ($selfTestText -notmatch 'Runner self-tests:\s+46 passed, 0 failed, 46 total\.') {
        throw 'The runner self-tests did not report 46 passing tests.'
    }

    Write-Host '[8/12] Proving radius-scaled map allocation and all-variant radius-192 parity...'
    $pursuitPath = '.\src\StarCluster.ScenarioRunner\Studies\checkpoint-21-full-flight-pursuit.calibration.json'
    $mapProofOutput = '.\out\checkpoint-22d-map-optimization-proof'
    Remove-Item $mapProofOutput -Recurse -Force -ErrorAction SilentlyContinue
    $mapProofText = Invoke-Runner -Arguments @(
        'map-optimization-proof',
        $pursuitPath,
        '--parity-trials', '4',
        '--map-measurements', '3',
        '--output-dir', $mapProofOutput) -Description 'Checkpoint 22d map optimization proof'
    if ($mapProofText -notmatch 'Map optimization preflight:\s+288 optimized variants and 288 radius-192 reference variants passed\.' -or
        $mapProofText -notmatch 'Map canonical parity:\s+288 matched, 0 failed; explicit-coordinate failures 0\.' -or
        $mapProofText -notmatch 'Map optimization proof:\s+PASS\.') {
        throw 'The map optimization proof did not report its expected passing contract.'
    }

    $mapSummaryPath = Join-Path $mapProofOutput 'map-optimization-summary.json'
    $mapSweepPath = Join-Path $mapProofOutput 'map-allocation-sweep.csv'
    $mapVariantsPath = Join-Path $mapProofOutput 'map-radius-variants.csv'
    $mapReportPath = Join-Path $mapProofOutput 'map-optimization-report.txt'
    foreach ($artifact in @($mapSummaryPath, $mapSweepPath, $mapVariantsPath, $mapReportPath)) {
        if (-not (Test-Path $artifact)) {
            throw "Map optimization artifact $artifact was not created."
        }
    }
    if (Test-Path (Join-Path $mapProofOutput 'map-parity-failures.txt')) {
        throw 'The map optimization proof emitted parity failures.'
    }
    $mapSummary = Get-Content $mapSummaryPath -Raw | ConvertFrom-Json
    if ($mapSummary.schemaVersion -ne 1 -or
        $mapSummary.variantCount -ne 288 -or
        $mapSummary.referenceRadius -ne 192 -or
        $mapSummary.parityTrialsPerVariant -ne 4 -or
        $mapSummary.minimumOptimizedRadius -ne 30 -or
        $mapSummary.maximumOptimizedRadius -ne 102 -or
        [math]::Abs([double]$mapSummary.averageOptimizedRadius - 38.25) -gt 0.001 -or
        [double]$mapSummary.averageCellRetentionRatio -gt 0.05 -or
        $mapSummary.explicitCoordinateFailureCount -ne 0 -or
        $mapSummary.canonicalParityFailureCount -ne 0 -or
        $mapSummary.allocationSweepMonotonic -ne $true -or
        $mapSummary.passed -ne $true) {
        throw 'The map optimization summary failed its Checkpoint 22d contract.'
    }
    $mapRows = Import-Csv $mapVariantsPath
    $sweepRows = Import-Csv $mapSweepPath
    if ($mapRows.Count -ne 288 -or $sweepRows.Count -ne 5) {
        throw "Map proof row counts were variants=$($mapRows.Count), sweep=$($sweepRows.Count); expected 288 and 5."
    }
    if (($mapRows | Where-Object {
            $_.explicit_coordinates_fit -ne 'true' -or
            $_.canonical_parity_matched -ne 'true'
        }).Count -ne 0) {
        throw 'One or more map-optimization variant rows failed coordinates or parity.'
    }

    Write-Host '[9/12] Reprofiling optimized initialization against the frozen Checkpoint 22b gate...'
    $profileOutput = '.\out\checkpoint-22d-allocation-profile'
    Remove-Item $profileOutput -Recurse -Force -ErrorAction SilentlyContinue
    $profileText = Invoke-Runner -Arguments @(
        'allocation-profile',
        $pursuitPath,
        '--trials', '4',
        '--warmup-trials', '1',
        '--output-dir', $profileOutput) -Description 'Checkpoint 22d allocation profile'
    if ($profileText -notmatch 'Allocation profile preflight:\s+24 scheduler-proof variants across 4 missile profiles passed\.' -or
        $profileText -notmatch 'Allocation profile parity:\s+96 matched, 0 failed\.' -or
        $profileText -notmatch 'Allocation profile:\s+PASS\.') {
        throw 'The optimized allocation profile did not report its expected passing contract.'
    }

    $allocationSummaryPath = Join-Path $profileOutput 'allocation-profile-summary.json'
    $allocationStagesPath = Join-Path $profileOutput 'allocation-stages.csv'
    $allocationTrialsPath = Join-Path $profileOutput 'allocation-trials.csv'
    $allocationReportPath = Join-Path $profileOutput 'allocation-profile-report.txt'
    foreach ($artifact in @(
        $allocationSummaryPath,
        $allocationStagesPath,
        $allocationTrialsPath,
        $allocationReportPath)) {
        if (-not (Test-Path $artifact)) {
            throw "Allocation profile artifact $artifact was not created."
        }
    }
    if (Test-Path (Join-Path $profileOutput 'parity-failures.txt')) {
        throw 'The optimized allocation profile emitted parity failures.'
    }
    $allocationSummary = Get-Content $allocationSummaryPath -Raw | ConvertFrom-Json
    if ($allocationSummary.schemaVersion -ne 2 -or
        $allocationSummary.variantCount -ne 24 -or
        $allocationSummary.warmupTrialsPerVariant -ne 1 -or
        $allocationSummary.measuredTrialsPerVariant -ne 4 -or
        $allocationSummary.measuredTrialsPerMode -ne 96 -or
        $allocationSummary.parityFailureCount -ne 0 -or
        $allocationSummary.passed -ne $true -or
        $allocationSummary.modes.Count -ne 2) {
        throw 'The optimized allocation profile summary failed its Checkpoint 22d contract.'
    }
    foreach ($modeName in @('DiagnosticJournal', 'CompactMetrics')) {
        $mode = $allocationSummary.modes | Where-Object { $_.mode -eq $modeName }
        if ($null -eq $mode -or
            $mode.trialCount -ne 96 -or
            $mode.errorCount -ne 0 -or
            $mode.hierarchyValid -ne $true -or
            [double]$mode.topLevelAttributionCoverage -lt 0.90 -or
            [double]$mode.profiledToGlobalAllocationRatio -lt 0.75 -or
            [double]$mode.profiledToGlobalAllocationRatio -gt 1.25) {
            throw "The $modeName optimized allocation profile failed its measurement contract."
        }
        foreach ($stageName in @(
            'RuntimeInitialization',
            'InitializationMapCreation',
            'InitializationShipStateCreation',
            'InitializationInitialTrackRefresh',
            'ShipMovement',
            'MissileAdvancement',
            'ResultProjection')) {
            $stage = $mode.stages | Where-Object {
                $_.stage -eq $stageName -and $_.isDerived -eq $false
            }
            if ($null -eq $stage -or [long]$stage.invocationCount -le 0) {
                throw "The $modeName optimized profile did not exercise stage $stageName."
            }
        }
        $runtimeResidual = $mode.stages | Where-Object {
            $_.stage -eq 'RuntimeInitializationResidual' -and $_.isDerived -eq $true
        }
        if ($null -eq $runtimeResidual) {
            throw "The $modeName profile did not report RuntimeInitializationResidual."
        }
    }

    $compactProfile = $allocationSummary.modes |
        Where-Object { $_.mode -eq 'CompactMetrics' }
    $frozenCheckpoint22bCompactBytesPerTrial = 20863918.0
    $maximumCompactBytesPerTrial = $frozenCheckpoint22bCompactBytesPerTrial * 0.20
    $optimizedCompactBytesPerTrial = [double]$compactProfile.profiledThreadBytesPerTrial
    $profileReduction = 1.0 - (
        $optimizedCompactBytesPerTrial / $frozenCheckpoint22bCompactBytesPerTrial)
    $mapCreationStage = $compactProfile.stages | Where-Object {
        $_.stage -eq 'InitializationMapCreation' -and $_.isDerived -eq $false
    }
    Write-Host ("       Frozen Checkpoint 22b compact allocation: {0:N0} bytes/trial." -f $frozenCheckpoint22bCompactBytesPerTrial)
    Write-Host ("       Optimized compact allocation: {0:N0} bytes/trial; reduction {1:P2}." -f $optimizedCompactBytesPerTrial, $profileReduction)
    Write-Host ("       Optimized map creation: {0:N0} bytes/trial ({1:P1} of total)." -f [double]$mapCreationStage.bytesPerTrial, [double]$mapCreationStage.percentOfTrialTotal)
    if ($optimizedCompactBytesPerTrial -gt $maximumCompactBytesPerTrial) {
        throw ("Optimized compact execution still allocates {0:N0} bytes/trial, above the frozen 4,172,784-byte gate." -f $optimizedCompactBytesPerTrial)
    }
    if ($profileReduction -lt 0.80) {
        throw ("Optimized compact allocation reduction was only {0:P2}; at least 80 percent is required." -f $profileReduction)
    }

    Write-Host '[10/12] Proving worker independence, execution-mode parity, and scaling...'
    $reproStudy = '.\src\StarCluster.ScenarioRunner\Studies\checkpoint-19-reproducibility.sweep.json'
    $reproHashes = @{}
    foreach ($jobs in @(1, 24)) {
        $outputDirectory = ".\out\checkpoint-22d-repro-j$jobs"
        Remove-Item $outputDirectory -Recurse -Force -ErrorAction SilentlyContinue
        $reproText = Invoke-Runner -Arguments @(
            'sweep',
            $reproStudy,
            '--jobs', $jobs.ToString(),
            '--checkpoint-every', '256',
            '--output-dir', $outputDirectory) -Description "Checkpoint 22d reproducibility sweep at jobs=$jobs"
        if ($reproText -notmatch 'Sweep preflight:\s+1 variants passed, 0 failed\.' -or
            $reproText -notmatch 'Sweep:\s+1 passed, 0 failed, 1 total\.') {
            throw "The jobs=$jobs reproducibility sweep did not report 1/1 passing variant."
        }
        $reproHashes[$jobs] = (Get-FileHash (
            Join-Path $outputDirectory 'sweep-summary.json') -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    if ($reproHashes[1] -ne $reproHashes[24]) {
        throw "Worker-independent hashes differ: jobs1=$($reproHashes[1]), jobs24=$($reproHashes[24])."
    }

    $proofTrials = 128
    $proofRuns = @(
        @{ Name = 'diagnostic-j24'; Jobs = 24; Mode = 'diagnostic'; Directory = '.\out\checkpoint-22d-diagnostic-proof-j24' },
        @{ Name = 'compact-j1'; Jobs = 1; Mode = 'compact'; Directory = '.\out\checkpoint-22d-compact-proof-j1' },
        @{ Name = 'compact-j24'; Jobs = 24; Mode = 'compact'; Directory = '.\out\checkpoint-22d-compact-proof-j24' }
    )
    $proofHashes = @{}
    $proofExecutions = @{}
    foreach ($proof in $proofRuns) {
        Remove-Item $proof.Directory -Recurse -Force -ErrorAction SilentlyContinue
        $proofText = Invoke-Runner -Arguments @(
            'pursuit-calibrate',
            $pursuitPath,
            '--scheduler-proof',
            '--jobs', $proof.Jobs.ToString(),
            '--trials', $proofTrials.ToString(),
            '--trial-execution', $proof.Mode,
            '--output-dir', $proof.Directory) -Description "Checkpoint 22d $($proof.Name) proof"
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
        if ($summary.runMode -ne 'scheduler-proof' -or
            $summary.commonRandomNumbersVerified -ne $true -or
            $summary.variantCount -ne 24 -or
            $summary.failedVariantCount -ne 0 -or
            $summary.passed -ne $true -or
            $execution.runMode -ne 'scheduler-proof' -or
            $execution.trialExecutionMode -ne $expectedMode -or
            $execution.requestedWorkers -ne $proof.Jobs -or
            $execution.workerLimit -ne $proof.Jobs -or
            $execution.peakActiveWorkers -ne $proof.Jobs -or
            $execution.variantCount -ne 24 -or
            $execution.trialsPerVariant -ne $proofTrials -or
            $execution.totalTrials -ne 3072 -or
            $execution.trialBlockSize -ne 8 -or
            $execution.trialBlockCount -ne 384 -or
            $execution.completedTrialBlockCount -ne 384 -or
            $execution.serverGarbageCollection -ne $true) {
            throw "The $($proof.Name) proof telemetry failed its contract."
        }
        $proofHashes[$proof.Name] = (Get-Content (
            Join-Path $proof.Directory 'full-flight-result.sha256') -Raw).Trim()
        $proofExecutions[$proof.Name] = $execution
    }
    if ($proofHashes['diagnostic-j24'] -ne $proofHashes['compact-j1'] -or
        $proofHashes['diagnostic-j24'] -ne $proofHashes['compact-j24']) {
        throw 'Diagnostic and compact scheduler-proof hashes differ.'
    }

    $singleRate = [double]$proofExecutions['compact-j1'].computeTrialsPerSecond
    $parallelRate = [double]$proofExecutions['compact-j24'].computeTrialsPerSecond
    $speedup = $parallelRate / $singleRate
    $proofCompactAllocation = [double]$proofExecutions['compact-j24'].allocatedBytesPerTrial
    $projectedSeconds = 288000.0 / $parallelRate
    Write-Host ("       Compact proof: {0:N2} trials/s at jobs=1; {1:N2} trials/s at jobs=24; {2:N2}x speedup." -f $singleRate, $parallelRate, $speedup)
    Write-Host ("       Compact proof allocation: {0:N0} bytes/trial." -f $proofCompactAllocation)
    Write-Host ("       Projected 288,000-trial compute time: {0:N1} minutes." -f ($projectedSeconds / 60.0))
    if ($speedup -lt 2.0) {
        throw ("Optimized 24-worker execution achieved only {0:N2}x speedup." -f $speedup)
    }
    if ($proofCompactAllocation -gt $maximumCompactBytesPerTrial) {
        throw ("Optimized 24-worker proof allocates {0:N0} bytes/trial, above the frozen gate." -f $proofCompactAllocation)
    }
    if ($projectedSeconds -gt 1800.0) {
        throw ("The optimized proof projects {0:N1} minutes for the full study, above the 30-minute safety limit." -f ($projectedSeconds / 60.0))
    }

    Write-Host '[11/12] Running the 288-variant compact calibration and reproducing accepted behavior...'
    $fullOutputDirectory = '.\out\checkpoint-22d-full-flight-pursuit-calibration'
    Remove-Item $fullOutputDirectory -Recurse -Force -ErrorAction SilentlyContinue
    $fullText = Invoke-Runner -Arguments @(
        'pursuit-calibrate',
        $pursuitPath,
        '--jobs', '24',
        '--trial-execution', 'compact',
        '--output-dir', $fullOutputDirectory) -Description 'Checkpoint 22d compact full-flight calibration'
    if ($fullText -notmatch 'Full-flight preflight:\s+288 variants across 4 missile profiles passed\.' -or
        $fullText -notmatch 'Full-flight calibration:\s+288 variants passed, 0 failed; 0 statistically contradictory inferential paired marginals after Holm correction; 144 descriptive relative-motion marginals\.') {
        throw 'The optimized full-flight calibration did not report its expected passing result.'
    }
    if ($fullText -notmatch 'Full-flight failure categories:\s+trial errors 0; datalink contract failures 0; terminal-opportunity invariant failures 0; unexplained unresolved outcomes 0\.') {
        throw 'The optimized full-flight calibration reported a mechanical failure category.'
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
        throw 'The optimized full-flight summary failed its Checkpoint 22d contract.'
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
        throw 'The optimized full-flight execution telemetry failed its 24-worker contract.'
    }

    $acceptedSummaryPath = '.\tools\checkpoints\checkpoint-22\reference\checkpoint-21e-full-flight-summary.csv'
    $acceptedMarginalsPath = '.\tools\checkpoints\checkpoint-22\reference\checkpoint-21e-full-flight-marginals.csv'
    $acceptedSummaryHash = (Get-FileHash $acceptedSummaryPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $acceptedMarginalsHash = (Get-FileHash $acceptedMarginalsPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($acceptedSummaryHash -ne '1632e624c6500dd09c5b68250b58622e8e6c24ad1f1b1369989b2e1d2baee0e9' -or
        $acceptedMarginalsHash -ne 'd54f916954db8051f50f698fc0f641f82ab22d1b82448aeebab3cbe4986856cc') {
        throw 'The packaged Checkpoint 21e behavioral reference files failed their locked hashes.'
    }
    $newSummaryHash = (Get-FileHash (
        Join-Path $fullOutputDirectory 'full-flight-summary.csv') -Algorithm SHA256).Hash.ToLowerInvariant()
    $newMarginalsHash = (Get-FileHash (
        Join-Path $fullOutputDirectory 'full-flight-marginals.csv') -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($newSummaryHash -ne $acceptedSummaryHash -or
        $newMarginalsHash -ne $acceptedMarginalsHash) {
        throw "Optimized map sizing changed accepted behavior: summary=$newSummaryHash expected=$acceptedSummaryHash; marginals=$newMarginalsHash expected=$acceptedMarginalsHash."
    }

    $checkpoint21eAllocatedBytes = 6037761090128.0
    $checkpoint21eGen2Collections = 4117
    $allocationReduction = 1.0 - (
        [double]$fullExecution.allocatedBytes / $checkpoint21eAllocatedBytes)
    $gen2Reduction = 1.0 - (
        [double]$fullExecution.gen2Collections / $checkpoint21eGen2Collections)
    if ($allocationReduction -lt 0.80) {
        throw ("Full-run allocation reduction was only {0:P2}; Checkpoint 22d requires at least 80 percent." -f $allocationReduction)
    }
    if ($gen2Reduction -lt 0.90) {
        throw ("Full-run Gen 2 reduction was only {0:P2}; Checkpoint 22d requires at least 90 percent." -f $gen2Reduction)
    }

    Write-Host '[12/12] Finalizing Checkpoint 22d evidence...'
    $canonicalHash = (Get-Content (
        Join-Path $fullOutputDirectory 'full-flight-result.sha256') -Raw).Trim()
    $acceptedCanonicalHash = '226677d3b9d2fded9e529ab5b897f6ec0e5251eb27937208f571cbb9b184ee28'
    if ($canonicalHash -ne $acceptedCanonicalHash) {
        throw "Checkpoint 22d canonical hash $canonicalHash did not match accepted hash $acceptedCanonicalHash."
    }
    Write-Host ''
    Write-Host 'Checkpoint 22d completed successfully and is the accepted repository baseline.'
    Write-Host 'Engine-independent tests passed: 506.'
    Write-Host 'Deterministic headless scenarios passed: 7.'
    Write-Host 'Runner self-tests passed: 46.'
    Write-Host 'Map optimization parity: 288/288 variants against radius 192.'
    Write-Host ("Average map-cell retention: {0:P2}." -f [double]$mapSummary.averageCellRetentionRatio)
    Write-Host ("Profiled compact allocation reduction versus Checkpoint 22b: {0:P2}." -f $profileReduction)
    Write-Host ("Compact 24-worker speedup: {0:N2}x." -f $speedup)
    Write-Host ("Full allocation reduction versus Checkpoint 21e: {0:P2}." -f $allocationReduction)
    Write-Host ("Full Gen 2 collection reduction versus Checkpoint 21e: {0:P2}." -f $gen2Reduction)
    Write-Host 'Accepted Checkpoint 21e summary and marginal CSV behavior reproduced exactly.'
    Write-Host 'Representative full-flight variants passed: 288.'
    Write-Host 'Inferential paired marginals verified: 720.'
    Write-Host 'Descriptive relative-motion marginals reported: 144.'
    Write-Host 'Mechanical failure categories: all zero.'
    Write-Host "Full-flight calibration result hash: $canonicalHash."
    Write-Host ("Full-flight compact throughput: {0:N2} trials/second over {1} ms." -f [double]$fullExecution.computeTrialsPerSecond, [long]$fullExecution.computeElapsedMilliseconds)
    Write-Host 'No mechanical Godot validation is required.'
    Write-Host 'Checkpoint 22 is closed. Preserve the Checkpoint 22d evidence directories; Checkpoint 23 may now begin.'
}
finally {
    Pop-Location
}
