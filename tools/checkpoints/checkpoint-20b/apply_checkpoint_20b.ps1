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
        throw "$Description file $Path was not found. Re-extract the complete Checkpoint 20b package."
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
    Write-Host '[1/13] Verifying repository and accepted Checkpoint 20a overlay baseline...'
    if (-not (Test-Path '.\StarCluster.sln')) {
        throw "StarCluster.sln was not found at $repositoryRoot. Extract the package into the repository root."
    }

    foreach ($baselineFile in @(
        '.\docs\checkpoints\Checkpoint_18d_Scenario_Corpus_And_Preflight_Hotfix.md',
        '.\docs\checkpoints\Checkpoint_19_Reproducible_Monte_Carlo_And_Parameter_Sweep_Foundation.md',
        '.\docs\checkpoints\Checkpoint_19a_Validation_Runbook_Guard_Hotfix.md',
        '.\docs\checkpoints\Checkpoint_20_Representative_Missile_Profiles_And_TL_Calibration.md',
        '.\docs\checkpoints\Checkpoint_20a_Calibration_Reporting_Guard_Hotfix.md',
        '.\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj',
        '.\src\StarCluster.ScenarioRunner\Studies\checkpoint-19-reproducibility.sweep.json',
        '.\src\StarCluster.Core\Simulation\ScenarioInitializationService.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileInterceptionPhaseContext.cs')) {
        if (-not (Test-Path $baselineFile)) {
            throw "Required Checkpoint 20a overlay baseline file $baselineFile was not found."
        }
    }

    foreach ($obsoleteMissileFile in @(
        '.\src\StarCluster.Core\Combat\Missiles\MissileAdvanceResult.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileSalvo.cs',
        '.\tests\StarCluster.Tests\Combat\Missiles\MissileSalvoTests.cs')) {
        Remove-Item $obsoleteMissileFile -Force -ErrorAction SilentlyContinue
    }

    Write-Host '[2/13] Confirming that Godot is closed...'
    $godotProcesses = Get-Process -ErrorAction SilentlyContinue |
        Where-Object { $_.ProcessName -like 'Godot*' }
    if ($godotProcesses) {
        $processNames = ($godotProcesses.ProcessName | Sort-Object -Unique) -join ', '
        throw "Close Godot before applying Checkpoint 20b. Running process(es): $processNames"
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
        'MissileInterceptionOpportunity.PreTerminalAttack;') 'Checkpoint 20 interception policy'
    Assert-FileContains '.\src\StarCluster.Core\Simulation\ScenarioInitializationService.cs' @(
        'restoredGuidancePhaseCount = Math.Max(',
        'definition.RetainedDatalink.ReceivedGuidancePhase') 'Checkpoint 20 shared initialization'
    Assert-FileContains '.\src\StarCluster.Core\Combat\Missiles\MissileTerminalResolutionService.cs' @(
        'targetTerminalEcmStrength - seeker.TerminalEccmStrength',
        'MissileTerminalOutcome.Dud',
        'MissileTerminalOutcome.CriticalHit') 'Checkpoint 20 terminal contract'

    Write-Host '[5/13] Verifying calibration runner, compact provenance, and statistical seams...'
    foreach ($runnerFile in @(
        '.\src\StarCluster.ScenarioRunner\TechnologyCalibrationDocuments.cs',
        '.\src\StarCluster.ScenarioRunner\TechnologyCalibrationModel.cs',
        '.\src\StarCluster.ScenarioRunner\TechnologyCalibrationRunner.cs',
        '.\src\StarCluster.ScenarioRunner\PairedMarginalStatistics.cs',
        '.\src\StarCluster.ScenarioRunner\MonteCarloDocuments.cs',
        '.\src\StarCluster.ScenarioRunner\MonteCarloBatchRunner.cs',
        '.\src\StarCluster.ScenarioRunner\MonteCarloStatistics.cs',
        '.\src\StarCluster.ScenarioRunner\ScenarioDocumentSerialization.cs',
        '.\src\StarCluster.ScenarioRunner\ScenarioRunnerSelfTests.cs',
        '.\src\StarCluster.ScenarioRunner\Program.cs')) {
        if (-not (Test-Path $runnerFile)) {
            throw "Required Checkpoint 20 runner file $runnerFile was not found."
        }
    }
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\Program.cs' @(
        '"calibrate" => RunCalibration(args)',
        '--keep-trials',
        '--discard-trials') 'Checkpoint 20b runner modes'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\MonteCarloDocuments.cs' @(
        'RandomSeedNamespace') 'Checkpoint 20b random-seed namespace option'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\MonteCarloBatchRunner.cs' @(
        'RandomSeedNamespace',
        'randomSeedNamespace',
        'execution-history.jsonl',
        'Trials = Array.AsReadOnly(orderedTrials)') 'Checkpoint 20b paired batch provenance'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\PairedMarginalStatistics.cs' @(
        'PairedBinaryDifferenceSummary',
        'AdjustHolm',
        'CalculateMcNemarPValue',
        'minimumPracticalDelta',
        'familywiseAlpha') 'Checkpoint 20b paired statistical model'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\TechnologyCalibrationModel.cs' @(
        'CalculatePdsInterceptionChancePercent',
        'CalculateAcquisitionSuccessProbability',
        'MinimumPracticalMarginalDelta',
        'MarginalFamilywiseAlpha') 'Checkpoint 20b analytical model'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\TechnologyCalibrationRunner.cs' @(
        'common-random-numbers-v1',
        'CreateOutcomeVector',
        'PairedMarginalStatistics.AdjustHolm',
        'PairingFingerprintSha256',
        'calibration-marginals.csv') 'Checkpoint 20b paired calibration reporting'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\TechnologyCalibrationDocuments.cs' @(
        'SchemaVersion { get; init; } = 2',
        'HolmAdjustedPValue',
        'CommonRandomNumbersVerified',
        'ContradictoryMarginalCount') 'Checkpoint 20b calibration output schema'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\MonteCarloStatistics.cs' @(
        'effect.effectiveHit',
        'effect.intercepted') 'Checkpoint 20 aggregate metrics' 

    Write-Host '[6/13] Verifying representative profiles and the 108-variant study...'
    $scenarioDirectory = '.\src\StarCluster.ScenarioRunner\Scenarios'
    $scenarioFiles = @(Get-ChildItem $scenarioDirectory -File -Filter '*.json')
    if ($scenarioFiles.Count -ne 7) {
        throw "Expected 7 deterministic scenario files, found $($scenarioFiles.Count)."
    }
    foreach ($scenarioFile in $scenarioFiles) {
        try {
            $scenario = Get-Content $scenarioFile.FullName -Raw | ConvertFrom-Json
        }
        catch {
            throw "Scenario $($scenarioFile.Name) is not valid JSON: $($_.Exception.Message)"
        }
        if ($scenario.schemaVersion -ne 1 -or [string]::IsNullOrWhiteSpace($scenario.id)) {
            throw "Scenario $($scenarioFile.Name) must have schemaVersion 1 and a non-empty id."
        }
    }

    $studyDirectory = '.\src\StarCluster.ScenarioRunner\Studies'
    $catalogPath = Join-Path $studyDirectory 'checkpoint-20-representative-profiles.json'
    $calibrationPath = Join-Path $studyDirectory 'checkpoint-20-terminal-tl-calibration.calibration.json'
    foreach ($path in @($catalogPath, $calibrationPath)) {
        if (-not (Test-Path $path)) {
            throw "Required Checkpoint 20 study file $path was not found."
        }
    }
    try {
        $catalog = Get-Content $catalogPath -Raw | ConvertFrom-Json
        $calibration = Get-Content $calibrationPath -Raw | ConvertFrom-Json
    }
    catch {
        throw "Checkpoint 20 study JSON could not be read: $($_.Exception.Message)"
    }
    if ($catalog.schemaVersion -ne 1 -or $calibration.schemaVersion -ne 1) {
        throw 'Checkpoint 20 catalog and calibration study must use schemaVersion 1.'
    }
    $expectedProfiles = @('command-guided', 'seeker-only', 'sensor-only', 'sensor-plus-seeker')
    $actualProfiles = @($catalog.missileProfiles | ForEach-Object { $_.id } | Sort-Object)
    if (($actualProfiles -join '|') -ne (($expectedProfiles | Sort-Object) -join '|')) {
        throw "Expected the four representative missile profiles, found: $($actualProfiles -join ', ')."
    }
    $technologyLevels = @($catalog.technologyLevels | ForEach-Object { [int]$_.technologyLevel } | Sort-Object)
    if (($technologyLevels -join ',') -ne '1,2,3,4,5,6,7,8,9') {
        throw "Expected explicit TL 1 through TL 9 catalog entries, found: $($technologyLevels -join ',')."
    }
    foreach ($axisName in @('missileTechnologyLevels', 'pdsTechnologyLevels', 'targetEcmTechnologyLevels')) {
        $axis = @($calibration.$axisName | ForEach-Object { [int]$_ } | Sort-Object)
        if (($axis -join ',') -ne '2,4,6') {
            throw "Calibration axis $axisName must contain TL 2, 4, and 6."
        }
    }
    if (@($calibration.missileProfiles).Count -ne 4 -or
        $calibration.trialsPerVariant -ne 2000 -or
        [Math]::Abs([double]$calibration.maximumAbsoluteError - 0.04) -gt 0.0000001 -or
        [Math]::Abs([double]$calibration.minimumPracticalMarginalDelta - 0.01) -gt 0.0000001 -or
        [Math]::Abs([double]$calibration.marginalFamilywiseAlpha - 0.05) -gt 0.0000001) {
        throw 'Checkpoint 20b calibration requires four profiles, 2,000 trials, 0.04 variant error, 0.01 practical marginal delta, and 0.05 familywise alpha.'
    }
    $variantCount = (
        @($calibration.missileProfiles).Count *
        @($calibration.missileTechnologyLevels).Count *
        @($calibration.pdsTechnologyLevels).Count *
        @($calibration.targetEcmTechnologyLevels).Count)
    if ($variantCount -ne 108) {
        throw "Checkpoint 20 calibration matrix contains $variantCount variants, expected 108."
    }
    if ($catalog.pds.equalTechnologyInterceptionChancePercent -ne 35 -or
        $catalog.pds.interceptionChancePercentPerTechnologyDelta -ne 10 -or
        $catalog.pds.minimumInterceptionChancePercent -ne 5 -or
        $catalog.pds.maximumInterceptionChancePercent -ne 95) {
        throw 'Checkpoint 20 provisional PDS conversion must be 35% equal-TL, +/-10% per TL, bounded 5-95%.'
    }

    Write-Host '[7/13] Verifying synchronized Checkpoint 20b documentation...'
    foreach ($documentationFile in @(
        '.\docs\README.md',
        '.\docs\Prototype_TODO.md',
        '.\docs\checkpoints\Checkpoint_20_Representative_Missile_Profiles_And_TL_Calibration.md',
        '.\docs\checkpoints\Checkpoint_20b_Paired_Calibration_And_Statistical_Gate_Repair.md',
        '.\docs\validation\Checkpoint_20b_Paired_Calibration_And_Statistical_Gate_Repair.md',
        '.\docs\design\Technology_Calibration_And_Simulation_Architecture.md',
        '.\docs\design\Missile_Guidance_Datalink_Sensor_And_Seeker_Architecture.md',
        '.\src\StarCluster.ScenarioRunner\README.md',
        '.\src\StarCluster.Game\README.md')) {
        if (-not (Test-Path $documentationFile)) {
            throw "Required Checkpoint 20 documentation file $documentationFile was not found."
        }
    }
    Assert-FileContains '.\docs\validation\Checkpoint_20b_Paired_Calibration_And_Statistical_Gate_Repair.md' @(
        '506/506',
        'seven deterministic headless scenarios',
        'sixteen runner self-tests',
        '108 variants',
        '--jobs 24',
        'No Godot run') 'Checkpoint 20b active validation runbook'
    Assert-FileContains '.\docs\checkpoints\Checkpoint_20_Representative_Missile_Profiles_And_TL_Calibration.md' @(
        'Command-guided',
        'Seeker-only',
        'Sensor-only',
        'Sensor plus seeker',
        '216,000 total trials',
        'provisional') 'Checkpoint 20 implementation record'
    Assert-FileContains '.\docs\checkpoints\Checkpoint_20b_Paired_Calibration_And_Statistical_Gate_Repair.md' @(
        'Common random numbers',
        'Holm step-down',
        'Practical effect threshold',
        '`StarCluster.Core` combat mechanics',
        'changes the experiment and reporting layer only') 'Checkpoint 20b implementation record'

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

    Write-Host '[11/13] Running deterministic corpus and sixteen runner self-tests...'
    $deterministicOutputDirectory = '.\out\checkpoint-20b-deterministic'
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
    if ($selfTestText -notmatch 'Runner self-tests:\s+16 passed, 0 failed, 16 total\.') {
        throw 'The runner did not report the expected 16/16 self-test result.'
    }

    Write-Host '[12/13] Rechecking worker-independent stochastic results...'
    $reproStudy = Join-Path $studyDirectory 'checkpoint-19-reproducibility.sweep.json'
    $reproDirectories = @{
        1 = '.\out\checkpoint-20b-repro-j1'
        24 = '.\out\checkpoint-20b-repro-j24'
    }
    $reproHashes = @{}
    foreach ($jobs in @(1, 24)) {
        $outputDirectory = $reproDirectories[$jobs]
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
        throw "Worker-independent hashes differ: jobs1=$($reproHashes[1]), jobs24=$($reproHashes[24])."
    }

    Write-Host '[13/13] Running 108 representative-profile TL calibration variants and finalizing...'
    $calibrationOutputDirectory = '.\out\checkpoint-20b-terminal-tl-calibration'
    Remove-Item -Recurse -Force $calibrationOutputDirectory -ErrorAction SilentlyContinue
    $calibrationText = Invoke-Runner -Arguments @(
        'calibrate',
        $calibrationPath,
        '--jobs', '24',
        '--output-dir', $calibrationOutputDirectory) -Description 'Representative-profile TL calibration'
    if ($calibrationText -notmatch 'Calibration preflight:\s+108 variants across 4 missile profiles passed\.' -or
        $calibrationText -notmatch 'Calibration:\s+108 variants passed, 0 failed; 0 statistically contradictory marginals after Holm correction\.') {
        throw 'The calibration runner did not report 108 passing variants and zero contradictory marginals.'
    }

    $summaryPath = Join-Path $calibrationOutputDirectory 'calibration-summary.json'
    $summaryCsvPath = Join-Path $calibrationOutputDirectory 'calibration-summary.csv'
    $marginalCsvPath = Join-Path $calibrationOutputDirectory 'calibration-marginals.csv'
    $hashPath = Join-Path $calibrationOutputDirectory 'calibration-result.sha256'
    foreach ($outputFile in @($summaryPath, $summaryCsvPath, $marginalCsvPath, $hashPath)) {
        if (-not (Test-Path $outputFile)) {
            throw "Calibration output $outputFile was not produced."
        }
    }
    $summary = Get-Content $summaryPath -Raw | ConvertFrom-Json
    $flatMarginals = @($summary.marginals | Where-Object { $_.expectedDirection -eq 'flat' })
    if (-not $summary.passed -or
        $summary.schemaVersion -ne 2 -or
        $summary.variantCount -ne 108 -or
        @($summary.variants).Count -ne 108 -or
        @($summary.variants | Where-Object { -not $_.passed }).Count -ne 0 -or
        @($summary.marginals).Count -ne 216 -or
        $summary.contradictoryMarginalCount -ne 0 -or
        @($summary.marginals | Where-Object { -not $_.commonRandomNumbersVerified }).Count -ne 0 -or
        @($summary.marginals | Where-Object { $_.statisticallyContradictory }).Count -ne 0 -or
        $flatMarginals.Count -ne 63 -or
        @($flatMarginals | Where-Object { [Math]::Abs([double]$_.observedDelta) -gt 0.000000000001 }).Count -ne 0 -or
        [Math]::Abs([double]$summary.minimumPracticalMarginalDelta - 0.01) -gt 0.0000001 -or
        [Math]::Abs([double]$summary.marginalFamilywiseAlpha - 0.05) -gt 0.0000001 -or
        [string]::IsNullOrWhiteSpace([string]$summary.randomSeedNamespace)) {
        throw 'Calibration summary does not contain the required schema-v2 paired, common-random, Holm-corrected result.'
    }
    $variantDirectories = @(Get-ChildItem (Join-Path $calibrationOutputDirectory 'variants') -Directory)
    if ($variantDirectories.Count -ne 108) {
        throw "Calibration produced $($variantDirectories.Count) variant directories, expected 108."
    }
    $retainedTrialJournals = @(Get-ChildItem $calibrationOutputDirectory -Recurse -File -Filter 'trials.jsonl')
    if ($retainedTrialJournals.Count -ne 0) {
        throw 'The compact acceptance run unexpectedly retained per-trial journals.'
    }
    $executionHistories = @(Get-ChildItem $calibrationOutputDirectory -Recurse -File -Filter 'execution-history.jsonl')
    if ($executionHistories.Count -ne 108) {
        throw "Calibration produced $($executionHistories.Count) execution histories, expected 108."
    }
    $recordedHash = (Get-Content $hashPath -Raw).Trim().ToLowerInvariant()
    $actualHash = (Get-FileHash $summaryPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($recordedHash -ne $actualHash) {
        throw "Calibration result hash is $recordedHash, but the summary hash is $actualHash."
    }

    foreach ($supersededValidation in @(
        'Checkpoint_19_Reproducible_Monte_Carlo_And_Parameter_Sweep_Foundation.md',
        'Checkpoint_19a_Validation_Runbook_Guard_Hotfix.md',
        'Checkpoint_20_Representative_Missile_Profiles_And_TL_Calibration.md',
        'Checkpoint_20a_Calibration_Reporting_Guard_Hotfix.md')) {
        $activePath = Join-Path '.\docs\validation' $supersededValidation
        $archivePath = Join-Path '.\docs\validation\archive' $supersededValidation
        if (Test-Path $activePath) {
            Copy-Item $activePath $archivePath -Force
            Remove-Item $activePath -Force
        }
    }
    foreach ($oldActive in @(
        'Checkpoint_18_Unified_Missile_Terminal_Solutions_Search_And_Seeker_Assistance.md',
        'Checkpoint_17c_Presentation_Concept_And_Reference_Handoff.md')) {
        Remove-Item (Join-Path '.\docs\validation' $oldActive) -Force -ErrorAction SilentlyContinue
    }

    $activeValidationFiles = @(Get-ChildItem '.\docs\validation' -File -Filter '*.md')
    if ($activeValidationFiles.Count -ne 1 -or
        $activeValidationFiles[0].Name -ne 'Checkpoint_20b_Paired_Calibration_And_Statistical_Gate_Repair.md') {
        throw 'Checkpoint 20b must leave exactly one active validation runbook.'
    }

    Write-Host ''
    Write-Host 'Checkpoint 20b completed successfully.'
    Write-Host 'Engine-independent tests passed: 506.'
    Write-Host 'Deterministic headless scenarios passed: 7.'
    Write-Host 'Runner self-tests passed: 16.'
    Write-Host "Worker-independent reproducibility hash: $($reproHashes[1])."
    Write-Host 'Representative-profile calibration variants passed: 108.'
    Write-Host 'Paired adjacent-TL marginals verified: 216.'
    Write-Host 'Statistically contradictory adjacent-TL marginals after Holm correction: 0.'
    Write-Host "Calibration result hash: $actualHash."
    Write-Host 'No mechanical Godot validation is required.'
    Write-Host 'Checkpoint 20b uses common random numbers, paired marginals, Holm correction, and a practical-effect threshold.'
    Write-Host 'Preserve out\checkpoint-20b-terminal-tl-calibration for review.'
}
finally {
    Pop-Location
}
