[CmdletBinding()]
param(
    [switch]$RepositoryOnly,
    [switch]$NoClean,
    [int]$Jobs = 24
)

$ErrorActionPreference = 'Stop'
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repo = (Resolve-Path (Join-Path $scriptRoot '..\..\..')).Path
$out = Join-Path $repo 'out\checkpoint-166'
$study = Join-Path $repo 'docs\validation\evidence\checkpoint-166\cp166_same_tl_whole_system_study_v0_1.json'
$preflight = Join-Path $scriptRoot 'preflight_checkpoint_166.py'
$contract = Join-Path $scriptRoot 'test_checkpoint_166_contract.py'
$research = Join-Path $repo 'tools\simulation\run_starcluster_research.py'
$repoOnlySummary = Join-Path $out 'CP166_REPOSITORY_ONLY_ACCEPTANCE.json'
$finalSummary = Join-Path $out 'CP166_NATIVE_ACCEPTANCE_SUMMARY.json'
$transcript = Join-Path $out 'CP166_console_output.txt'
$transcriptStarted = $false

function Get-Cpython313Command {
    foreach ($candidate in @(
        @{ Command = 'py'; Args = @('-3.13') },
        @{ Command = 'python'; Args = @() },
        @{ Command = 'python3'; Args = @() }
    )) {
        if (Get-Command $candidate.Command -ErrorAction SilentlyContinue) {
            $version = & $candidate.Command @($candidate.Args + @('--version')) 2>&1 | Out-String
            if ($LASTEXITCODE -eq 0 -and $version -match 'Python\s+3\.13(?:\.|\s|$)') {
                return $candidate
            }
        }
    }
    throw 'CP166 requires Python 3.13.'
}

function Invoke-PythonChecked([object]$Python, [string[]]$Arguments, [string]$Failure) {
    & $Python.Command @($Python.Args + $Arguments)
    if ($LASTEXITCODE -ne 0) { throw "$Failure (exit code $LASTEXITCODE)." }
}

function Invoke-Captured([string]$Label, [string]$LogPath, [scriptblock]$Body) {
    $old = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        & $Body *> $LogPath
        $code = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $old
    }
    if ($code -ne 0) {
        Write-Host "       $Label output tail:" -ForegroundColor Yellow
        Get-Content -LiteralPath $LogPath -Tail 120 | ForEach-Object { Write-Host "       $_" }
        throw "$Label failed (exit code $code)."
    }
}

function Read-Json([string]$Path) {
    return Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
}

function Invoke-Cp166([string[]]$Arguments, [string]$Failure) {
    $sim = Join-Path $repo 'tools\simulation'
    $oldPath = $env:PYTHONPATH
    try {
        if ([string]::IsNullOrWhiteSpace($oldPath)) { $env:PYTHONPATH = $sim }
        else { $env:PYTHONPATH = $sim + [IO.Path]::PathSeparator + $oldPath }
        & $python.Command @($python.Args + @('-B','-m','starcluster_research.same_tl_whole_system','--repo',$repo,'--study',$study) + $Arguments)
        if ($LASTEXITCODE -ne 0) { throw "$Failure (exit code $LASTEXITCODE)." }
    } finally {
        $env:PYTHONPATH = $oldPath
    }
}

function Invoke-PythonResearchTests {
    $files = @(Get-ChildItem -LiteralPath (Join-Path $repo 'tools\simulation\tests') -Filter 'test_*.py' | Sort-Object Name)
    if ($files.Count -ne 57) { throw "CP166 expected 57 Python test modules, found $($files.Count)." }
    $sim = Join-Path $repo 'tools\simulation'
    $oldPath = $env:PYTHONPATH
    try {
        if ([string]::IsNullOrWhiteSpace($oldPath)) { $env:PYTHONPATH = $sim }
        else { $env:PYTHONPATH = $sim + [IO.Path]::PathSeparator + $oldPath }
        $chunkSize = 8
        $chunks = [Math]::Ceiling($files.Count / [double]$chunkSize)
        for ($c = 0; $c -lt $chunks; $c++) {
            $start = $c * $chunkSize
            $end = [Math]::Min($files.Count - 1, $start + $chunkSize - 1)
            $mods = @($files[$start..$end] | ForEach-Object { "tools.simulation.tests.$($_.BaseName)" })
            Write-Host ("       Python test chunk {0}/{1} ({2} modules)..." -f ($c + 1), $chunks, $mods.Count)
            & $python.Command @($python.Args + @('-B','-m','unittest') + $mods)
            if ($LASTEXITCODE -ne 0) { throw "CP166 Python regression chunk $($c + 1) failed." }
        }
    } finally {
        $env:PYTHONPATH = $oldPath
    }
}

function Test-ValidBatch([int]$Tl) {
    $summaryPath = Join-Path $out ("combat-batches\tl{0}\summary.json" -f $Tl)
    if (-not (Test-Path $summaryPath)) { return $false }
    try {
        $s = Read-Json $summaryPath
        return ([bool]$s.passed -and [int]$s.tl -eq $Tl -and [int]$s.representatives -eq 28 -and
                [int]$s.combatVariants -eq 1624 -and [int]$s.trialsPerVariant -eq 200 -and
                [int64]$s.combatTrials -eq 324800 -and [int]$s.monotonicityVariants -eq 32 -and
                [int]$s.monotonicityTrialsPerVariant -eq 250 -and [int64]$s.monotonicityCombatTrials -eq 8000 -and
                [int64]$s.errors -eq 0 -and [int]$s.symmetryFailures -eq 0)
    } catch { return $false }
}

function Stop-TranscriptSafe {
    if ($script:transcriptStarted) {
        try { Stop-Transcript | Out-Null } catch {}
        $script:transcriptStarted = $false
    }
}

function New-ResultZip {
    $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $zip = Join-Path $repo ("StarCluster_CP166_native_results_{0}.zip" -f $stamp)
    if (Test-Path $zip) { Remove-Item -Force $zip }
    Compress-Archive -Path (Join-Path $out '*') -DestinationPath $zip -CompressionLevel Optimal
    return $zip
}

$python = Get-Cpython313Command
$pythonVersion = (& $python.Command @($python.Args + @('--version')) 2>&1 | Out-String).Trim()
$dotnetVersion = (& dotnet --version 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or $dotnetVersion -ne '8.0.423') {
    throw "CP166 requires .NET SDK 8.0.423 exactly; observed '$dotnetVersion'."
}
if ($Jobs -lt 1) { throw 'Jobs must be at least 1.' }

if ($RepositoryOnly -and -not $NoClean -and (Test-Path $out)) { Remove-Item -Recurse -Force $out }
New-Item -ItemType Directory -Force -Path $out | Out-Null
Start-Transcript -Path $transcript -Append | Out-Null
$transcriptStarted = $true

try {
    Write-Host ("CP166 runtimes: {0}; .NET SDK {1}; jobs {2}" -f $pythonVersion, $dotnetVersion, $Jobs)
    Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repo,'--out',(Join-Path $out 'preflight.json')) 'CP166 preflight failed'

    if ($RepositoryOnly) {
        $xunitOut = Join-Path $out 'xunit'
        $parityOut = Join-Path $out 'parity'
        $detOut = Join-Path $out 'deterministic-scenarios'
        $tl1Out = Join-Path $out 'tl1-phase-a'
        $planOut = Join-Path $out 'planning'
        $staticOut = Join-Path $out 'static-census'
        $smokeOut = Join-Path $out 'smoke'
        $snapshotOut = Join-Path $out 'authority-snapshot'
        New-Item -ItemType Directory -Force -Path $xunitOut,$parityOut,$detOut,$tl1Out,$snapshotOut | Out-Null
        Push-Location $repo
        try {
            Write-Host '[1/10] Python research regression (824 tests)...'
            Invoke-PythonResearchTests

            Write-Host '[2/10] Warning-as-error .NET build...'
            Invoke-Captured 'CP166 build' (Join-Path $out 'build.log') { dotnet build StarCluster.sln --configuration Release --nologo -warnaserror }

            Write-Host '[3/10] xUnit + ScenarioRunner regression...'
            dotnet test tests\StarCluster.Tests\StarCluster.Tests.csproj --configuration Release --no-build --nologo --logger 'trx;LogFileName=cp166-tests.trx' --results-directory $xunitOut
            $xunitExit = $LASTEXITCODE
            [xml]$trx = Get-Content -LiteralPath (Join-Path $xunitOut 'cp166-tests.trx') -Raw
            $c = $trx.TestRun.ResultSummary.Counters
            $total = [int]$c.total; $passed = [int]$c.passed; $failed = [int]$c.failed; $skipped = [int]$c.notExecuted
            if ($xunitExit -ne 0 -or $total -ne 934 -or $passed -ne 934 -or $failed -ne 0 -or $skipped -ne 0) { throw 'CP166 xUnit mismatch.' }
            $selfLog = Join-Path $out 'scenario-self-tests.log'
            Invoke-Captured 'CP166 ScenarioRunner self-tests' $selfLog { dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- self-test }
            if ((Get-Content $selfLog -Raw) -notmatch 'Runner self-tests:\s+70 passed,\s+0 failed,\s+70 total\.') { throw 'CP166 expected 70/70 self-tests.' }
            Invoke-Captured 'CP166 deterministic scenarios' (Join-Path $out 'deterministic-scenarios.log') { dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- run-all --output-dir $detOut }
            Invoke-Captured 'CP166 TL1 Phase-A' (Join-Path $out 'tl1-phase-a.log') { dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- tl1-phase-a --output-dir $tl1Out }

            Write-Host '[4/10] C#/Python research parity (25)...'
            Invoke-PythonChecked $python @('-B',$research,'--repo',$repo,'parity','--output-dir',$parityOut) 'CP166 parity failed'
            $parity = Read-Json (Join-Path $parityOut 'summary.json')
            if (-not [bool]$parity.passed -or [int]$parity.cases -ne 25) { throw 'CP166 parity mismatch.' }

            Write-Host '[5/10] CP166 focused whole-system tests (32)...'
            $sim = Join-Path $repo 'tools\simulation'
            $oldPath = $env:PYTHONPATH
            try {
                if ([string]::IsNullOrWhiteSpace($oldPath)) { $env:PYTHONPATH = $sim }
                else { $env:PYTHONPATH = $sim + [IO.Path]::PathSeparator + $oldPath }
                & $python.Command @($python.Args + @('-B','-m','unittest','-v','tools.simulation.tests.test_cp166_same_tl_whole_system'))
                if ($LASTEXITCODE -ne 0) { throw 'CP166 focused tests failed.' }
            } finally { $env:PYTHONPATH = $oldPath }

            Write-Host '[6/10] Exact same-TL whole-system plan...'
            if (Test-Path $planOut) { Remove-Item -Recurse -Force $planOut }
            Invoke-Cp166 @('plan','--out',$planOut) 'CP166 plan failed'
            $pl = Read-Json (Join-Path $planOut 'summary.json')
            if (-not [bool]$pl.passed -or [int]$pl.skeletons -ne 101207 -or [int]$pl.representatives -ne 252 -or [int]$pl.combatVariants -ne 14616 -or [int64]$pl.totalDiagnosticCombatTrials -ne 2995200) { throw 'CP166 plan mismatch.' }

            Write-Host '[7/10] Exhaustive legal architecture census + representative selection...'
            if (Test-Path $staticOut) { Remove-Item -Recurse -Force $staticOut }
            Invoke-Cp166 @('static','--out',$staticOut) 'CP166 static census failed'
            $st = Read-Json (Join-Path $staticOut 'summary.json')
            if (-not [bool]$st.passed -or [int]$st.skeletons -ne 101207 -or [int64]$st.effectDistinctStackCombinations -ne 635428 -or [int]$st.representatives -ne 252 -or [int]$st.coverageRows -ne 16) { throw 'CP166 static census mismatch.' }

            Write-Host '[8/10] Live current-working whole-system smoke + exact mirror probe...'
            if (Test-Path $smokeOut) { Remove-Item -Recurse -Force $smokeOut }
            Invoke-Cp166 @('smoke','--out',$smokeOut) 'CP166 smoke failed'
            $sm = Read-Json (Join-Path $smokeOut 'summary.json')
            if (-not [bool]$sm.passed -or [int]$sm.liveCombatTrials -ne 8 -or [int]$sm.errors -ne 0) { throw 'CP166 smoke mismatch.' }

            Write-Host '[9/10] Freezing accepted CP165 + current authority snapshot...'
            Copy-Item -LiteralPath (Join-Path $repo 'docs\validation\evidence\checkpoint-166\CP165_ACCEPTED_NATIVE_PROVENANCE.json') -Destination $snapshotOut
            Copy-Item -LiteralPath (Join-Path $repo 'docs\validation\evidence\checkpoint-166\CP166_CURRENT_AUTHORITY_SHA256.json') -Destination $snapshotOut
            Copy-Item -LiteralPath $study -Destination $snapshotOut
            Copy-Item -LiteralPath (Join-Path $staticOut 'execution_coverage.csv') -Destination $snapshotOut

            Write-Host '[10/10] Writing RepositoryOnly acceptance...'
            $summary = [ordered]@{
                schemaVersion = 'star-cluster-cp166-repository-only-acceptance-v0.1'
                checkpoint = 166
                repositoryOnly = $true
                failedGates = @()
                python = $pythonVersion
                dotnetSdk = $dotnetVersion
                buildPassed = $true
                pythonTestsPassed = 824
                xunitTotal = $total
                xunitPassed = $passed
                xunitFailed = $failed
                xunitSkipped = $skipped
                scenarioRunnerSelfTestsPassed = 70
                deterministicScenarioCorpusPassed = $true
                tl1PhaseACorpusPassed = $true
                researchParityPassed = 25
                cp166FocusedTestsPassed = 32
                acceptedBaseCheckpoint = 165
                acceptedBaseRevision = 'CP165-CR3'
                authorityHashesLocked = $true
                productionRuntimeMechanicsChanged = $false
                currentAuthorityChanged = $false
                sameTlOnly = $true
                differentTlCombatsExecuted = $false
                mixedTlShipsExecuted = $false
                architectureSkeletons = 101207
                effectDistinctStackCombinations = 635428
                representatives = 252
                pairGroups = 3654
                plannedCombatVariants = 14616
                plannedSubstantiveCombatTrials = 2923200
                plannedMonotonicityVariants = 288
                plannedMonotonicityCombatTrials = 72000
                plannedTotalDiagnosticCombatTrials = 2995200
                substantiveCombatTrials = 0
                componentStateIntegrationComplete = $false
                tuningAllowed = $false
                automaticPromotion = $false
            }
            $summary | ConvertTo-Json -Depth 8 | Set-Content $repoOnlySummary -Encoding UTF8
            Invoke-PythonChecked $python @('-B',$contract,'--repo',$repo,'--native-results',$out) 'CP166 RepositoryOnly contract failed'
            Write-Host 'CP166 RepositoryOnly PASSED. Run again without -RepositoryOnly in this same extraction to execute/resume 2,995,200 same-TL diagnostic combats.' -ForegroundColor Green
        } finally { Pop-Location }
        Stop-TranscriptSafe
        exit 0
    }

    if (-not (Test-Path $repoOnlySummary)) { throw 'Run CP166 -RepositoryOnly first in this same extraction.' }
    Push-Location $repo
    try {
        Write-Host '[final 1/4] Revalidating CP165 authority and RepositoryOnly state...'
        Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repo,'--out',(Join-Path $out 'preflight-final.json')) 'CP166 final preflight failed'
        Invoke-PythonChecked $python @('-B',$contract,'--repo',$repo,'--native-results',$out) 'CP166 RepositoryOnly state contract failed'

        Write-Host '[final 2/4] Executing/resuming TL1-TL9 same-TL whole-system batches...'
        $batchRoot = Join-Path $out 'combat-batches'
        New-Item -ItemType Directory -Force -Path $batchRoot | Out-Null
        foreach ($tl in 1..9) {
            $dir = Join-Path $batchRoot ("tl{0}" -f $tl)
            if (Test-ValidBatch $tl) {
                Write-Host ("       TL{0} batch valid; reusing." -f $tl)
            } else {
                if (Test-Path $dir) { Remove-Item -Recurse -Force $dir }
                Write-Host ("       TL{0}: 324,800 main + 8,000 monotonicity combats..." -f $tl)
                Invoke-Cp166 @('batch','--tl',[string]$tl,'--jobs',[string]$Jobs,'--out',$dir) "CP166 TL$tl batch failed"
                if (-not (Test-ValidBatch $tl)) { throw "CP166 TL$tl batch output contract failed." }
            }
        }

        Write-Host '[final 3/4] Merging whole-system response surface and tactical watches...'
        $merged = Join-Path $out 'combat-merged'
        if (Test-Path $merged) { Remove-Item -Recurse -Force $merged }
        Invoke-Cp166 @('merge','--batch-root',$batchRoot,'--out',$merged) 'CP166 merge failed'
        $m = Read-Json (Join-Path $merged 'summary.json')
        if (-not [bool]$m.passed -or [int]$m.representatives -ne 252 -or [int]$m.pairGroups -ne 3654 -or [int]$m.combatVariants -ne 14616 -or [int64]$m.substantiveCombatTrials -ne 2923200 -or [int]$m.monotonicityVariants -ne 288 -or [int64]$m.monotonicityCombatTrials -ne 72000 -or [int64]$m.totalDiagnosticCombatTrials -ne 2995200 -or [int64]$m.errors -ne 0 -or [int]$m.symmetryFailures -ne 0) { throw 'CP166 merged response contract mismatch.' }

        Write-Host '[final 4/4] Writing native diagnostic acceptance and packaging results...'
        $ro = Read-Json $repoOnlySummary
        $final = [ordered]@{}
        $ro.psobject.Properties | ForEach-Object { $final[$_.Name] = $_.Value }
        $final['schemaVersion'] = 'star-cluster-cp166-native-acceptance-v0.1'
        $final['repositoryOnly'] = $false
        $final['repositoryOnlyAccepted'] = $true
        $final['studyCompleted'] = $true
        $final['substantiveCombatTrials'] = [int64]$m.substantiveCombatTrials
        $final['monotonicityCombatTrials'] = [int64]$m.monotonicityCombatTrials
        $final['totalDiagnosticCombatTrials'] = [int64]$m.totalDiagnosticCombatTrials
        $final['combatErrorTrials'] = [int64]$m.errors
        $final['turnCapSentinels'] = [int64]$m.turnCapSentinels
        $final['symmetryFailures'] = [int]$m.symmetryFailures
        $final['dominanceWatchBuilds'] = [int]$m.dominanceWatchBuilds
        $final['weakWatchBuilds'] = [int]$m.weakWatchBuilds
        $final['allocatorRegressionWatches'] = [int]$m.allocatorRegressionWatches
        $final['tacticsWatchRows'] = [int]$m.tacticsWatchRows
        $final['tuningAllowed'] = $false
        $final['automaticPromotion'] = $false
        $final['sameTlDiagnosticComplete'] = $true
        $final['componentStateIntegrationComplete'] = $false
        $final | ConvertTo-Json -Depth 8 | Set-Content $finalSummary -Encoding UTF8
        Invoke-PythonChecked $python @('-B',$contract,'--repo',$repo,'--native-results',$out) 'CP166 final contract failed'
    } finally {
        Pop-Location
    }
    Stop-TranscriptSafe
    $zip = New-ResultZip
    Write-Host "CP166 native acceptance PASSED. Results: $zip" -ForegroundColor Green
} finally {
    Stop-TranscriptSafe
}
