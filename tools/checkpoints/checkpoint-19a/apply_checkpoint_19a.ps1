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
        throw "$Description file $Path was not found. Re-extract the complete Checkpoint 19a package."
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
    Write-Host '[1/13] Verifying repository and Checkpoint 19 overlay baseline...'
    if (-not (Test-Path '.\StarCluster.sln')) {
        throw "StarCluster.sln was not found at $repositoryRoot. Extract the package into the repository root."
    }

    foreach ($baselineFile in @(
        '.\docs\checkpoints\Checkpoint_18d_Scenario_Corpus_And_Preflight_Hotfix.md',
        '.\docs\checkpoints\Checkpoint_19_Reproducible_Monte_Carlo_And_Parameter_Sweep_Foundation.md',
        '.\docs\checkpoints\Checkpoint_19a_Validation_Runbook_Guard_Hotfix.md',
        '.\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj',
        '.\src\StarCluster.ScenarioRunner\Scenarios\terminal-two-window-hit.json',
        '.\src\StarCluster.Core\Simulation\ScenarioInitializationService.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileInterceptionPhaseContext.cs')) {
        if (-not (Test-Path $baselineFile)) {
            throw "Required Checkpoint 19 baseline file $baselineFile was not found."
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
        throw "Close Godot before applying Checkpoint 19a. Running process(es): $processNames"
    }

    Write-Host '[3/13] Checking the pinned .NET SDK...'
    $sdkVersion = dotnet --version
    Write-Host "       SDK: $sdkVersion"
    if ($sdkVersion -ne '8.0.423') {
        throw "Expected .NET SDK 8.0.423 from global.json, but dotnet selected $sdkVersion."
    }

    Write-Host '[4/13] Verifying unchanged authoritative missile and initialization policy...'
    Assert-FileContains '.\src\StarCluster.Core\Combat\Missiles\MissileInterceptionPhaseContext.cs' @(
        'Held direct-fire weapons are deliberate long-range interceptors.',
        'MissileInterceptionOpportunity.Transit or',
        'MissileInterceptionOpportunity.Stationary;',
        'Standard PDS is terminal defense.',
        'MissileInterceptionOpportunity.TerminalEntry or',
        'MissileInterceptionOpportunity.PreTerminalAttack;') 'Checkpoint 19 interception policy'
    Assert-FileContains '.\src\StarCluster.Core\Simulation\ScenarioInitializationService.cs' @(
        'private const string CheckpointVersion = "checkpoint-19";',
        'restoredGuidancePhaseCount = Math.Max(',
        'definition.RetainedDatalink.ReceivedGuidancePhase') 'Checkpoint 19 shared initialization'

    Write-Host '[5/13] Verifying deterministic, batch, sweep, and resume runner seams...'
    foreach ($runnerFile in @(
        '.\src\StarCluster.ScenarioRunner\Program.cs',
        '.\src\StarCluster.ScenarioRunner\MonteCarloBatchRunner.cs',
        '.\src\StarCluster.ScenarioRunner\MonteCarloSweepRunner.cs',
        '.\src\StarCluster.ScenarioRunner\MonteCarloStatistics.cs',
        '.\src\StarCluster.ScenarioRunner\MonteCarloTrialResult.cs',
        '.\src\StarCluster.ScenarioRunner\TrialSeedDeriver.cs',
        '.\src\StarCluster.ScenarioRunner\DeterministicRandomStream.cs',
        '.\src\StarCluster.ScenarioRunner\ProbabilityMissileInterceptionResolver.cs',
        '.\src\StarCluster.ScenarioRunner\ScenarioOverrideApplier.cs',
        '.\src\StarCluster.ScenarioRunner\ScenarioRunnerSelfTests.cs')) {
        if (-not (Test-Path $runnerFile)) {
            throw "Required Checkpoint 19 runner file $runnerFile was not found."
        }
    }
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\Program.cs' @(
        '"batch" => RunBatch(args)',
        '"sweep" => RunSweep(args)',
        '"self-test" => RunSelfTests(args)') 'Checkpoint 19 runner modes'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\TrialSeedDeriver.cs' @(
        'masterSeed',
        'variantId',
        'trialIndex',
        'streamId') 'Checkpoint 19 trial seed derivation'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\MonteCarloBatchRunner.cs' @(
        'MaxDegreeOfParallelism = options.Jobs',
        'Checkpoint 19 Monte Carlo batches require exactly one primary',
        'result.sha256',
        'trials.jsonl',
        'Resume manifest does not match') 'Checkpoint 19 batch/restart contract'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\MonteCarloStatistics.cs' @(
        'Confidence95Low',
        'Confidence95High',
        'Z95') 'Checkpoint 19 statistical contract'

    Write-Host '[6/13] Verifying scenario corpus and packaged simulation studies...'
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

    $studyDirectory = '.\src\StarCluster.ScenarioRunner\Studies'
    $studyFiles = @(Get-ChildItem $studyDirectory -File -Filter '*.sweep.json')
    if ($studyFiles.Count -ne 2) {
        throw "Expected 2 Checkpoint 19 sweep files, found $($studyFiles.Count)."
    }
    foreach ($studyFile in $studyFiles) {
        try {
            $study = Get-Content $studyFile.FullName -Raw | ConvertFrom-Json
        }
        catch {
            throw "Study $($studyFile.Name) is not valid JSON: $($_.Exception.Message)"
        }
        if ($study.schemaVersion -ne 1 -or
            [string]::IsNullOrWhiteSpace($study.id) -or
            @($study.variants).Count -lt 1) {
            throw "Study $($studyFile.Name) must have schemaVersion 1, an id, and variants."
        }
    }
    $reproStudy = Join-Path $studyDirectory 'checkpoint-19-reproducibility.sweep.json'
    $probabilityStudy = Join-Path $studyDirectory 'checkpoint-19-terminal-probability-validation.sweep.json'
    $reproDocument = Get-Content $reproStudy -Raw | ConvertFrom-Json
    $probabilityDocument = Get-Content $probabilityStudy -Raw | ConvertFrom-Json
    if ($reproDocument.trialsPerVariant -ne 2000 -or @($reproDocument.variants).Count -ne 1) {
        throw 'The reproducibility study must contain one 2,000-trial variant.'
    }
    if ($probabilityDocument.trialsPerVariant -ne 5000 -or @($probabilityDocument.variants).Count -ne 3) {
        throw 'The probability-validation study must contain three 5,000-trial variants.'
    }

    Write-Host '[7/13] Verifying synchronized Checkpoint 19a documentation...'
    foreach ($documentationFile in @(
        '.\docs\README.md',
        '.\docs\Prototype_TODO.md',
        '.\docs\checkpoints\Checkpoint_19_Reproducible_Monte_Carlo_And_Parameter_Sweep_Foundation.md',
        '.\docs\checkpoints\Checkpoint_19a_Validation_Runbook_Guard_Hotfix.md',
        '.\docs\validation\Checkpoint_19a_Validation_Runbook_Guard_Hotfix.md',
        '.\docs\validation\archive\Checkpoint_19_Reproducible_Monte_Carlo_And_Parameter_Sweep_Foundation.md',
        '.\docs\validation\archive\Checkpoint_18d_Scenario_Corpus_And_Preflight_Hotfix.md',
        '.\docs\design\Missile_Guidance_Datalink_Sensor_And_Seeker_Architecture.md',
        '.\src\StarCluster.ScenarioRunner\README.md',
        '.\src\StarCluster.Game\README.md')) {
        if (-not (Test-Path $documentationFile)) {
            throw "Required Checkpoint 19a documentation file $documentationFile was not found."
        }
    }
    Assert-FileContains '.\docs\validation\Checkpoint_19a_Validation_Runbook_Guard_Hotfix.md' @(
        '506/506',
        'seven deterministic scenarios',
        'eight runner self-tests',
        '--jobs 1',
        '--jobs 12',
        '--jobs 24',
        'No Godot run') 'Checkpoint 19a active validation runbook'

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

    Write-Host '[11/13] Running deterministic corpus and runner self-tests...'
    $deterministicOutputDirectory = '.\out\checkpoint-19-deterministic'
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
    if ($selfTestText -notmatch 'Runner self-tests:\s+8 passed, 0 failed, 8 total\.') {
        throw 'The runner did not report the expected 8/8 self-test result.'
    }

    Write-Host '[12/13] Proving worker-independent Monte Carlo results and resume...'
    $reproDirectories = @{
        1 = '.\out\checkpoint-19-repro-j1'
        12 = '.\out\checkpoint-19-repro-j12'
        24 = '.\out\checkpoint-19-repro-j24'
    }
    $reproHashes = @{}
    foreach ($jobs in @(1, 12, 24)) {
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
    if ($reproHashes[1] -ne $reproHashes[12] -or
        $reproHashes[1] -ne $reproHashes[24]) {
        throw "Worker-independent hashes differ: jobs1=$($reproHashes[1]), jobs12=$($reproHashes[12]), jobs24=$($reproHashes[24])."
    }

    $resumeText = Invoke-Runner -Arguments @(
        'sweep',
        $reproStudy,
        '--jobs', '24',
        '--resume',
        '--checkpoint-every', '256',
        '--output-dir', $reproDirectories[24]) -Description 'Reproducibility resume'
    if ($resumeText -notmatch 'resumed 2000; executed 0') {
        throw 'The resumed reproducibility run did not reuse all 2,000 completed trials.'
    }
    $resumeHash = (Get-FileHash (Join-Path $reproDirectories[24] 'sweep-summary.json') -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($resumeHash -ne $reproHashes[24]) {
        throw "Resume changed the canonical sweep hash from $($reproHashes[24]) to $resumeHash."
    }

    Write-Host '[13/13] Running the terminal probability-validation sweep and finalizing...'
    $probabilityOutputDirectory = '.\out\checkpoint-19-terminal-probability-validation'
    Remove-Item -Recurse -Force $probabilityOutputDirectory -ErrorAction SilentlyContinue
    $probabilityText = Invoke-Runner -Arguments @(
        'sweep',
        $probabilityStudy,
        '--jobs', '24',
        '--checkpoint-every', '256',
        '--trace-samples', '2',
        '--output-dir', $probabilityOutputDirectory) -Description 'Terminal probability-validation sweep'
    if ($probabilityText -notmatch 'Sweep preflight:\s+3 variants passed, 0 failed\.' -or
        $probabilityText -notmatch 'Sweep:\s+3 passed, 0 failed, 3 total\.') {
        throw 'The terminal probability-validation sweep did not report 3/3 passing variants.'
    }

    foreach ($supersededValidation in @(
        'Checkpoint_18b_Headless_Scenario_Runner_And_Deterministic_Combat_Validation.md',
        'Checkpoint_18c_Headless_Runner_Policy_And_Initialization_Hotfix.md',
        'Checkpoint_18d_Scenario_Corpus_And_Preflight_Hotfix.md',
        'Checkpoint_19_Reproducible_Monte_Carlo_And_Parameter_Sweep_Foundation.md')) {
        $activePath = Join-Path '.\docs\validation' $supersededValidation
        $archivePath = Join-Path '.\docs\validation\archive' $supersededValidation
        if (Test-Path $activePath) {
            Copy-Item $activePath $archivePath -Force
            Remove-Item $activePath -Force
        }
    }
    Remove-Item '.\docs\validation\Checkpoint_18_Unified_Missile_Terminal_Solutions_Search_And_Seeker_Assistance.md' -Force -ErrorAction SilentlyContinue
    Remove-Item '.\docs\validation\Checkpoint_17c_Presentation_Concept_And_Reference_Handoff.md' -Force -ErrorAction SilentlyContinue

    $activeValidationFiles = @(Get-ChildItem '.\docs\validation' -File -Filter '*.md')
    if ($activeValidationFiles.Count -ne 1 -or
        $activeValidationFiles[0].Name -ne 'Checkpoint_19a_Validation_Runbook_Guard_Hotfix.md') {
        throw 'Checkpoint 19a must leave exactly one active validation runbook.'
    }

    Write-Host ''
    Write-Host 'Checkpoint 19a completed successfully.'
    Write-Host 'Engine-independent tests passed: 506.'
    Write-Host 'Deterministic headless scenarios passed: 7.'
    Write-Host 'Runner self-tests passed: 8.'
    Write-Host "Worker-independent reproducibility hash: $($reproHashes[1])."
    Write-Host 'Resume reused all 2,000 trials and preserved the canonical hash.'
    Write-Host 'Terminal probability-validation variants passed: 3.'
    Write-Host 'Checkpoint 19 Monte Carlo mechanics are unchanged; the validation guard is repaired.'
    Write-Host 'No mechanical Godot validation is required.'
}
finally {
    Pop-Location
}
