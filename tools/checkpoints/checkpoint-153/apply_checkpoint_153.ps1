[CmdletBinding()]
param(
    [switch]$RepositoryOnly,
    [switch]$NoClean,
    [int]$Jobs = 24
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$preflight = Join-Path $PSScriptRoot 'preflight_checkpoint_153.py'
$contract = Join-Path $PSScriptRoot 'test_checkpoint_153_contract.py'
$research = Join-Path $repositoryRoot 'tools\simulation\run_starcluster_research.py'
$study = 'docs/archive/testing/pre-cp165-active/cp153_four_main_ladder_synthesis_study_v0_1.json'
$cp139Study = 'docs/archive/testing/pre-cp165-active/cp139_def_res_reconciliation_study_v0_1.json'
$cp142Study = 'docs/archive/testing/pre-cp165-active/cp142_combat_surface_deep_reconciliation_study_v0_1.json'

$outRoot = Join-Path $repositoryRoot 'out\checkpoint-153'
$testOut = Join-Path $outRoot 'xunit'
$parityOut = Join-Path $outRoot 'research-parity'
$deterministicOut = Join-Path $outRoot 'deterministic-scenarios'
$tl1PhaseAOut = Join-Path $outRoot 'tl1-phase-a'
$cp139Out = Join-Path $outRoot 'cp139-reconciliation'
$cp142Out = Join-Path $outRoot 'cp142-reconciliation-audit'
$planOut = Join-Path $outRoot 'four-main-plan'
$energySmokeRoot = Join-Path $outRoot 'energy-closure-smoke'
$energyBatchRoot = Join-Path $outRoot 'energy-closure-batches'
$energyMerge = Join-Path $outRoot 'energy-closure-merged'
$synthesisOut = Join-Path $outRoot 'four-main-ladder-synthesis'
$screenBatchRoot = Join-Path $outRoot 'four-main-screen-batches'
$screenMerge = Join-Path $outRoot 'four-main-screen-merged'
$deepSelect = Join-Path $outRoot 'four-main-deep-select'
$deepBatchRoot = Join-Path $outRoot 'four-main-deep-batches'
$deepMerge = Join-Path $outRoot 'four-main-deep-merged'
$repoOnlySummary = Join-Path $outRoot 'CP153_REPOSITORY_ONLY_ACCEPTANCE.json'
$finalSummary = Join-Path $outRoot 'CP153_NATIVE_ACCEPTANCE_SUMMARY.json'
$contextCounts = @{1=200;2=300;3=300;4=300;5=300;6=300;7=300;8=300;9=300}

function Get-Cpython313Command {
    $candidates = @(
        @{Command='py'; Args=@('-3.13')},
        @{Command='python'; Args=@()},
        @{Command='python3'; Args=@()}
    )
    foreach ($candidate in $candidates) {
        if (Get-Command $candidate.Command -ErrorAction SilentlyContinue) {
            $version = & $candidate.Command @($candidate.Args + @('--version')) 2>&1 | Out-String
            if ($LASTEXITCODE -eq 0 -and $version -match 'Python\s+3\.13(?:\.|\s|$)') {
                return $candidate
            }
        }
    }
    throw 'CP153 requires Python 3.13.'
}

function Invoke-PythonChecked([object]$Python, [string[]]$Arguments, [string]$Failure) {
    & $Python.Command @($Python.Args + $Arguments)
    if ($LASTEXITCODE -ne 0) {
        throw "$Failure (exit code $LASTEXITCODE)."
    }
}

function Invoke-Captured([string]$Label, [string]$LogPath, [scriptblock]$Body) {
    & $Body *> $LogPath
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        Write-Host "       $Label output tail:" -ForegroundColor Yellow
        Get-Content -LiteralPath $LogPath -Tail 120 | ForEach-Object { Write-Host("       $_") }
        throw "$Label failed (exit code $exitCode)."
    }
}

function Read-Json([string]$Path) {
    return (Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json)
}

function Relative-To-Repo([string]$Path) {
    $root = [IO.Path]::GetFullPath($repositoryRoot)
    $full = [IO.Path]::GetFullPath($Path)
    $sep = [IO.Path]::DirectorySeparatorChar
    $prefix = $root
    if (-not $prefix.EndsWith([string]$sep)) { $prefix += $sep }
    if (-not $full.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Path outside repository: $Path"
    }
    return $full.Substring($prefix.Length)
}

function Invoke-PythonWithSimulationPath([scriptblock]$Body) {
    $sim = Join-Path $repositoryRoot 'tools\simulation'
    $old = $env:PYTHONPATH
    try {
        if ([string]::IsNullOrWhiteSpace($old)) { $env:PYTHONPATH = $sim }
        else { $env:PYTHONPATH = $sim + [IO.Path]::PathSeparator + $old }
        & $Body
    }
    finally { $env:PYTHONPATH = $old }
}

function Invoke-PythonFocusedPattern([string]$Pattern, [string]$Failure) {
    Invoke-PythonWithSimulationPath {
        & $python.Command @($python.Args + @('-B','-m','unittest','discover','-v','-s','tools/simulation/tests','-p',$Pattern))
        if ($LASTEXITCODE -ne 0) { throw $Failure }
    }
}

function Invoke-PythonResearchTests {
    $files = Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'tools\simulation\tests') -Filter 'test_*.py' | Sort-Object Name
    if ($files.Count -ne 44) { throw "CP153 expected 44 Python modules, found $($files.Count)." }
    $chunks = @(
        @($files[0..12]),
        @($files[13..18]),
        @($files[19..24]),
        @($files[25..38]),
        @($files[39]),
        @($files[40]),
        @($files[41]),
        @($files[42]),
        @($files[43])
    )
    Invoke-PythonWithSimulationPath {
        for ($i=0; $i -lt $chunks.Count; $i++) {
            $mods = @($chunks[$i] | ForEach-Object { "tools.simulation.tests.$($_.BaseName)" })
            Write-Host("       Python test chunk {0}/9 ({1} modules)..." -f ($i+1), $mods.Count)
            & $python.Command @($python.Args + @('-B','-m','unittest') + $mods)
            if ($LASTEXITCODE -ne 0) { throw "CP153 Python chunk $($i+1) failed." }
        }
    }
}

function Invoke-Plan {
    if (Test-Path $planOut) { Remove-Item -Recurse -Force $planOut }
    New-Item -ItemType Directory -Force -Path $planOut | Out-Null
    Invoke-Captured 'CP153 plan' (Join-Path $planOut 'console.log') {
        & $python.Command @($python.Args + @('-B',$research,'--repo',$repositoryRoot,'four-main-ladder-plan',$study,'--output-dir',(Relative-To-Repo $planOut)))
    }
    $s = Read-Json (Join-Path $planOut 'summary.json')
    if (-not [bool]$s.passed -or [int]$s.energyTlCandidates -ne 3798 -or [int]$s.wholeLadderPackages -ne 432 -or [int64]$s.totalCombatTrials -ne 102346800 -or [int64]$s.energySmokeCombatTrials -ne 189900) {
        throw 'CP153 plan mismatch.'
    }
    return $s
}

function Invoke-EnergySmoke {
    $total = [int64]0
    $caps = [int64]0
    for ($tl=1; $tl -le 9; $tl++) {
        $dir = Join-Path $energySmokeRoot ("tl{0:D2}" -f $tl)
        if (Test-Path $dir) { Remove-Item -Recurse -Force $dir }
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
        Write-Host("       CP153 E smoke TL{0}: 422 x 50 = 21,100 combats" -f $tl)
        Invoke-Captured "CP153 E smoke TL$tl" (Join-Path $dir 'console.log') {
            & $python.Command @($python.Args + @('-B',$research,'--repo',$repositoryRoot,'four-main-energy-closure',$study,'--output-dir',(Relative-To-Repo $dir),'--jobs',$Jobs,'--tl',$tl,'--candidate-start','0','--candidate-end','422','--trials','1','--smoke-panel'))
        }
        $s = Read-Json (Join-Path $dir 'summary.json')
        if (-not [bool]$s.passed -or [int]$s.candidates -ne 422 -or [int]$s.contextsPerCandidate -ne 50 -or [int]$s.combatTrials -ne 21100 -or [int]$s.errors -ne 0) {
            throw "CP153 E smoke TL$tl mismatch."
        }
        $total += [int64]$s.combatTrials
        $caps += [int64]$s.turnCapSentinels
    }
    if ($total -ne 189900) { throw "CP153 smoke total $total." }
    return [pscustomobject]@{combatTrials=$total; turnCaps=$caps}
}

function Test-EnergyBatch([string]$Dir, [int]$Tl, [int]$Start, [int]$End, [int]$Trials) {
    $sp = Join-Path $Dir 'summary.json'
    $rp = Join-Path $Dir 'energy_closure_candidate_context_results.csv'
    if (-not (Test-Path $sp) -or -not (Test-Path $rp)) { return $false }
    try {
        $s = Read-Json $sp
        $contexts = [int]$contextCounts[$Tl]
        $n = $End - $Start
        $cells = $n * $contexts
        return (
            [bool]$s.passed -and
            [string]$s.lane -eq 'E' -and
            [int]$s.tl -eq $Tl -and
            [int]$s.candidateStart -eq $Start -and
            [int]$s.candidateEnd -eq $End -and
            [int]$s.candidateContextCells -eq $cells -and
            [int]$s.trialsPerContext -eq $Trials -and
            [int64]$s.combatTrials -eq ([int64]$cells * $Trials) -and
            [int]$s.errors -eq 0 -and
            -not [bool]$s.smokePanel
        )
    }
    catch { return $false }
}

function Invoke-EnergyClosure {
    New-Item -ItemType Directory -Force -Path $energyBatchRoot | Out-Null
    if (Test-Path $energyMerge) { Remove-Item -Recurse -Force $energyMerge }
    New-Item -ItemType Directory -Force -Path $energyMerge | Out-Null
    $batch = 0
    for ($tl=1; $tl -le 9; $tl++) {
        $start = 0
        while ($start -lt 422) {
            $end = [Math]::Min($start + 16, 422)
            $batch++
            $dir = Join-Path $energyBatchRoot ("tl{0:D2}_{1:D3}_{2:D3}" -f $tl,$start,$end)
            if (Test-EnergyBatch $dir $tl $start $end 75) {
                Write-Host("       CP153 E batch {0}/243 TL{1} {2}-{3} valid; reusing." -f $batch,$tl,$start,($end-1))
            }
            else {
                if (Test-Path $dir) { Remove-Item -Recurse -Force $dir }
                New-Item -ItemType Directory -Force -Path $dir | Out-Null
                $combats = [int64]($end-$start) * [int]$contextCounts[$tl] * 75
                Write-Host("       CP153 E batch {0}/243 TL{1} {2}-{3}: {4:N0} combats" -f $batch,$tl,$start,($end-1),$combats)
                Invoke-Captured "CP153 E TL$tl $start-$end" (Join-Path $dir 'console.log') {
                    & $python.Command @($python.Args + @('-B',$research,'--repo',$repositoryRoot,'four-main-energy-closure',$study,'--output-dir',(Relative-To-Repo $dir),'--jobs',$Jobs,'--tl',$tl,'--candidate-start',$start,'--candidate-end',$end,'--trials','75'))
                }
                if (-not (Test-EnergyBatch $dir $tl $start $end 75)) { throw 'CP153 Energy batch failed validation.' }
            }
            $start = $end
        }
    }
    if ($batch -ne 243) { throw "CP153 Energy batch count $batch." }
    Invoke-Captured 'CP153 Energy closure merge' (Join-Path $energyMerge 'console.log') {
        & $python.Command @($python.Args + @('-B',$research,'--repo',$repositoryRoot,'four-main-energy-merge',$study,'--batch-root',(Relative-To-Repo $energyBatchRoot),'--output-dir',(Relative-To-Repo $energyMerge)))
    }
    $s = Read-Json (Join-Path $energyMerge 'summary.json')
    if (-not [bool]$s.passed -or [int64]$s.combatTrials -ne 82290000 -or [int]$s.errorTrials -ne 0) { throw 'CP153 Energy merge mismatch.' }
    return $s
}

function Invoke-LadderSynthesis {
    if (Test-Path $synthesisOut) { Remove-Item -Recurse -Force $synthesisOut }
    New-Item -ItemType Directory -Force -Path $synthesisOut | Out-Null
    Invoke-Captured 'CP153 four-main ladder synthesis' (Join-Path $synthesisOut 'console.log') {
        & $python.Command @($python.Args + @('-B',$research,'--repo',$repositoryRoot,'four-main-ladder-synthesize',$study,'--energy-merged',(Relative-To-Repo $energyMerge),'--output-dir',(Relative-To-Repo $synthesisOut)))
    }
    $s = Read-Json (Join-Path $synthesisOut 'summary.json')
    if (-not [bool]$s.passed -or [int]$s.kLadders -ne 6 -or [int]$s.eLadders -ne 8 -or [int]$s.gpLadders -ne 3 -or [int]$s.swLadders -ne 3 -or [int]$s.packages -ne 432) { throw 'CP153 ladder synthesis mismatch.' }
    return $s
}

function Test-PackageBatch([string]$Dir, [string]$Mode, [int]$Start, [int]$End, [int]$Contexts, [int]$Trials) {
    $sp = Join-Path $Dir 'summary.json'
    $rp = Join-Path $Dir 'four_main_package_context_results.csv'
    if (-not (Test-Path $sp) -or -not (Test-Path $rp)) { return $false }
    try {
        $s = Read-Json $sp
        $n = $End - $Start
        $cells = $n * $Contexts
        return (
            [bool]$s.passed -and
            [string]$s.mode -eq "package-$Mode-batch" -and
            [int]$s.packageStart -eq $Start -and
            [int]$s.packageEnd -eq $End -and
            [int]$s.packages -eq $n -and
            [int]$s.contextsPerPackage -eq $Contexts -and
            [int]$s.packageContextCells -eq $cells -and
            [int]$s.trialsPerContext -eq $Trials -and
            [int64]$s.combatTrials -eq ([int64]$cells * $Trials) -and
            [int]$s.errors -eq 0
        )
    }
    catch { return $false }
}

function Invoke-PackagePhase([string]$Mode, [string]$Ledger, [string]$BatchRoot, [string]$MergeRoot, [int]$TotalPackages, [int]$BatchSize, [int]$Contexts, [int]$Trials, [int64]$ExpectedCombats) {
    New-Item -ItemType Directory -Force -Path $BatchRoot | Out-Null
    if (Test-Path $MergeRoot) { Remove-Item -Recurse -Force $MergeRoot }
    New-Item -ItemType Directory -Force -Path $MergeRoot | Out-Null
    $start = 0
    $batch = 0
    $batchTotal = [int][Math]::Ceiling($TotalPackages / [double]$BatchSize)
    while ($start -lt $TotalPackages) {
        $end = [Math]::Min($start + $BatchSize, $TotalPackages)
        $batch++
        $dir = Join-Path $BatchRoot ("batch_{0:D3}_{1:D3}" -f $start,$end)
        if (Test-PackageBatch $dir $Mode $start $end $Contexts $Trials) {
            Write-Host("       CP153 {0} batch {1}/{2} packages {3}-{4} valid; reusing." -f $Mode,$batch,$batchTotal,$start,($end-1))
        }
        else {
            if (Test-Path $dir) { Remove-Item -Recurse -Force $dir }
            New-Item -ItemType Directory -Force -Path $dir | Out-Null
            $combats = [int64]($end-$start) * $Contexts * $Trials
            Write-Host("       CP153 {0} batch {1}/{2} packages {3}-{4}: {5:N0} combats" -f $Mode,$batch,$batchTotal,$start,($end-1),$combats)
            Invoke-Captured "CP153 $Mode $start-$end" (Join-Path $dir 'console.log') {
                & $python.Command @($python.Args + @('-B',$research,'--repo',$repositoryRoot,'four-main-package-sweep',$study,'--package-ledger',(Relative-To-Repo $Ledger),'--mode',$Mode,'--output-dir',(Relative-To-Repo $dir),'--jobs',$Jobs,'--package-start',$start,'--package-end',$end,'--trials',$Trials))
            }
            if (-not (Test-PackageBatch $dir $Mode $start $end $Contexts $Trials)) { throw "CP153 $Mode package batch failed validation." }
        }
        $start = $end
    }
    Invoke-Captured "CP153 $Mode package merge" (Join-Path $MergeRoot 'console.log') {
        & $python.Command @($python.Args + @('-B',$research,'--repo',$repositoryRoot,'four-main-package-merge',$study,'--package-ledger',(Relative-To-Repo $Ledger),'--mode',$Mode,'--batch-root',(Relative-To-Repo $BatchRoot),'--output-dir',(Relative-To-Repo $MergeRoot)))
    }
    $s = Read-Json (Join-Path $MergeRoot 'summary.json')
    if (-not [bool]$s.passed -or [int]$s.packages -ne $TotalPackages -or [int64]$s.combatTrials -ne $ExpectedCombats -or [int]$s.errorTrials -ne 0) { throw "CP153 $Mode package merge mismatch." }
    return $s
}

function Invoke-DeepSelection {
    if (Test-Path $deepSelect) { Remove-Item -Recurse -Force $deepSelect }
    New-Item -ItemType Directory -Force -Path $deepSelect | Out-Null
    $ledger = Join-Path $synthesisOut 'four_main_package_tl_ledger.csv'
    Invoke-Captured 'CP153 deep package selection' (Join-Path $deepSelect 'console.log') {
        & $python.Command @($python.Args + @('-B',$research,'--repo',$repositoryRoot,'four-main-deep-select',$study,'--package-ledger',(Relative-To-Repo $ledger),'--screen-merged',(Relative-To-Repo $screenMerge),'--output-dir',(Relative-To-Repo $deepSelect)))
    }
    $s = Read-Json (Join-Path $deepSelect 'summary.json')
    if (-not [bool]$s.passed -or [int]$s.deepPackages -ne 12 -or [int]$s.packageTlRows -ne 108 -or [int]$s.energyLaddersRepresented -ne 8) { throw 'CP153 deep selection mismatch.' }
    return $s
}

function New-ResultZip {
    $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $zip = Join-Path $outRoot ("StarCluster_CP153_native_results_$stamp.zip")
    $stage = Join-Path $repositoryRoot 'out\checkpoint-153-package-staging'
    if (Test-Path $stage) { Remove-Item -Recurse -Force $stage }
    New-Item -ItemType Directory -Force -Path $stage | Out-Null
    $skip = @('energy-closure-batches','four-main-screen-batches','four-main-deep-batches')
    foreach ($item in Get-ChildItem -LiteralPath $outRoot -Force) {
        if ($item.FullName -eq $zip -or $item.Name -in $skip) { continue }
        Copy-Item -LiteralPath $item.FullName -Destination $stage -Recurse -Force
    }
    foreach ($spec in @(
        @('energy-closure-batch-summaries',$energyBatchRoot),
        @('four-main-screen-batch-summaries',$screenBatchRoot),
        @('four-main-deep-batch-summaries',$deepBatchRoot)
    )) {
        $dest = Join-Path $stage $spec[0]
        New-Item -ItemType Directory -Force -Path $dest | Out-Null
        if (Test-Path $spec[1]) {
            foreach ($d in Get-ChildItem -LiteralPath $spec[1] -Directory | Sort-Object Name) {
                $sp = Join-Path $d.FullName 'summary.json'
                if (Test-Path $sp) { Copy-Item $sp (Join-Path $dest ($d.Name + '_summary.json')) -Force }
            }
        }
    }
    Compress-Archive -Path (Join-Path $stage '*') -DestinationPath $zip -CompressionLevel Optimal
    Remove-Item -Recurse -Force $stage
    return $zip
}

$python = Get-Cpython313Command
$pythonVersion = & $python.Command @($python.Args + @('--version')) 2>&1 | Out-String
$dotnetVersion = (& dotnet --version 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or $dotnetVersion -ne '8.0.423') { throw "CP153 requires .NET SDK 8.0.423 exactly; observed '$dotnetVersion'." }
Write-Host("CP153 runtimes: {0}; .NET SDK {1}" -f $pythonVersion.Trim(),$dotnetVersion)
Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot) 'CP153 preflight failed'

if ($RepositoryOnly) {
    if (-not $NoClean -and (Test-Path $outRoot)) { Remove-Item -Recurse -Force $outRoot }
    New-Item -ItemType Directory -Force -Path $outRoot,$testOut,$parityOut,$deterministicOut,$tl1PhaseAOut,$cp139Out,$cp142Out | Out-Null
    Push-Location $repositoryRoot
    try {
        Write-Host '[1/10] Python research tests (447 total)...'
        Invoke-PythonResearchTests

        Write-Host '[2/10] Warning-as-error .NET build...'
        Invoke-Captured 'CP153 build' (Join-Path $outRoot 'build.log') { dotnet build StarCluster.sln --configuration Release --nologo -warnaserror }

        Write-Host '[3/10] xUnit + ScenarioRunner deterministic corpora...'
        dotnet test tests\StarCluster.Tests\StarCluster.Tests.csproj --configuration Release --no-build --nologo --logger 'trx;LogFileName=cp153-tests.trx' --results-directory $testOut
        $xunitExit = $LASTEXITCODE
        [xml]$trx = Get-Content -LiteralPath (Join-Path $testOut 'cp153-tests.trx') -Raw
        $c = $trx.TestRun.ResultSummary.Counters
        $total = [int]$c.total; $passed = [int]$c.passed; $failed = [int]$c.failed; $skipped = [int]$c.notExecuted
        if ($xunitExit -ne 0 -or $total -ne 934 -or $passed -ne 934 -or $failed -ne 0 -or $skipped -ne 0) { throw 'CP153 xUnit mismatch.' }
        $selfLog = Join-Path $outRoot 'scenario-self-tests.log'
        Invoke-Captured 'CP153 ScenarioRunner self-tests' $selfLog { dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- self-test }
        if ((Get-Content $selfLog -Raw) -notmatch 'Runner self-tests:\s+70 passed,\s+0 failed,\s+70 total\.') { throw 'CP153 expected 70/70 self-tests.' }
        Invoke-Captured 'CP153 deterministic scenarios' (Join-Path $outRoot 'deterministic-scenarios.log') { dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- run-all --output-dir $deterministicOut }
        Invoke-Captured 'CP153 TL1 Phase-A' (Join-Path $outRoot 'tl1-phase-a.log') { dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- tl1-phase-a --output-dir $tl1PhaseAOut }

        Write-Host '[4/10] C#/Python parity...'
        Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'parity','--output-dir',$parityOut) 'CP153 parity failed'
        $parity = Read-Json (Join-Path $parityOut 'summary.json')
        if (-not [bool]$parity.passed -or [int]$parity.cases -ne 25) { throw 'CP153 parity mismatch.' }

        Write-Host '[5/10] CP139 reconciliation foundation...'
        Invoke-PythonFocusedPattern 'test_cp139_def_res_reconciliation.py' 'CP139 focused failed'
        Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'combat-model-reconciliation-study',$cp139Study,'--output-dir','out/checkpoint-153/cp139-reconciliation') 'CP139 reconciliation failed'

        Write-Host '[6/10] Focused CP140-CP153 regression tests...'
        foreach ($pattern in @(
            'test_cp140_stage_a_integration.py','test_cp141_combat_duration_stalemate.py','test_cp142_combat_surface_reconciliation.py','test_cp143_missile_mirror_pacing_attribution.py',
            'test_cp144_*.py','test_cp145_*.py','test_cp146_*.py','test_cp147_*.py','test_cp148_*.py','test_cp149_*.py','test_cp150_*.py','test_cp151_*.py','test_cp152_*.py','test_cp153_*.py'
        )) { Invoke-PythonFocusedPattern $pattern "Focused regression failed: $pattern" }

        Write-Host '[7/10] CP142 reconciliation audit...'
        Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'combat-surface-reconciliation-audit',$cp142Study,'--output-dir','out/checkpoint-153/cp142-reconciliation-audit') 'CP142 audit failed'
        $audit = Read-Json (Join-Path $cp142Out 'reconciliation_summary.json')
        if (-not [bool]$audit.passed -or [int]$audit.ledgerRows -ne 531 -or [int]$audit.changedVsCp141Rows -ne 72 -or [int]$audit.explicitUnresolvedRows -ne 7) { throw 'CP142 audit mismatch.' }

        Write-Host '[8/10] CP153 102.347M four-main plan...'
        $plan = Invoke-Plan

        Write-Host '[9/10] CP153 all-candidate Energy smoke (189,900 combats)...'
        $smoke = Invoke-EnergySmoke

        Write-Host '[10/10] Writing RepositoryOnly acceptance...'
        $summary = [ordered]@{
            schemaVersion='star-cluster-cp153-repository-only-acceptance-v0.1'; checkpoint=153; repositoryOnly=$true; failedGates=@();
            python=$pythonVersion.Trim(); dotnetSdk=$dotnetVersion; buildPassed=$true; pythonTestsPassed=447;
            xunitTotal=$total; xunitPassed=$passed; xunitFailed=$failed; xunitSkipped=$skipped;
            scenarioRunnerSelfTestsPassed=70; deterministicScenarioCorpusPassed=$true; tl1PhaseACorpusPassed=$true; researchParityPassed=25;
            cp139FocusedTestsPassed=9; cp140FocusedTestsPassed=10; cp141FocusedTestsPassed=10; cp142FocusedTestsPassed=12; cp143FocusedTestsPassed=12;
            cp144FocusedTestsPassed=11; cp145FocusedTestsPassed=12; cp146FocusedTestsPassed=18; cp147FocusedTestsPassed=18; cp148FocusedTestsPassed=12;
            cp149FocusedTestsPassed=16; cp150FocusedTestsPassed=16; cp151FocusedTestsPassed=18; cp152FocusedTestsPassed=18; cp153FocusedTestsPassed=21;
            acceptedCp152EvidenceHashLocked=$true; pointScale=2; combatDoctrine='cp147_tactical_utility'; energyTlCandidates=3798; energyCandidatesPerTl=422;
            energyPairwiseCandidatesPerTl=264; wholeLadderPackages=432; plannedEnergyCombatTrials=82290000; plannedScreenCombatTrials=11836800;
            plannedDeepCombatTrials=8220000; plannedSubstantiveCombatTrials=102346800; energySmokeCombatTrials=[int64]$smoke.combatTrials;
            smokeTurnCapSentinels=[int64]$smoke.turnCaps; smokeErrors=0; sourceMatrixUnmodified=$true; conceptUnmodified=$true; productionCSharpUnmodified=$true;
            substantiveCombatTrials=0; tuningAllowed=$false; automaticPromotion=$false; stageBAutomatic=$false;
            nextStage='execute/resume CP153 Energy closure, synthesize K/E/GP/Swarmer whole ladders, screen 432 packages, and deep-confirm 12 diverse packages'
        }
        $summary | ConvertTo-Json -Depth 8 | Set-Content $repoOnlySummary -Encoding UTF8
        Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP153 RepositoryOnly contract failed'
        Write-Host 'CP153 RepositoryOnly PASSED. Run again without -RepositoryOnly to execute/resume 102,346,800 substantive combats.' -ForegroundColor Green
    }
    finally { Pop-Location }
    exit 0
}

if (-not (Test-Path $repoOnlySummary)) { throw 'Run CP153 -RepositoryOnly first in this same extraction.' }

Push-Location $repositoryRoot
try {
    Write-Host '[final 1/7] Revalidating repository and RepositoryOnly state...'
    Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot) 'CP153 final preflight failed'
    Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP153 RepositoryOnly state contract failed'

    Write-Host '[final 2/7] Executing/resuming Energy closure (82.290M)...'
    $energy = Invoke-EnergyClosure

    Write-Host '[final 3/7] Synthesizing coherent K/E/GP/Swarmer TL1-TL9 ladders...'
    $synthesis = Invoke-LadderSynthesis
    $packageLedger = Join-Path $synthesisOut 'four_main_package_tl_ledger.csv'

    Write-Host '[final 4/7] Executing/resuming 432-package screen (11.837M)...'
    $screen = Invoke-PackagePhase 'screen' $packageLedger $screenBatchRoot $screenMerge 432 8 1370 20 11836800

    Write-Host '[final 5/7] Selecting 12 diverse deep-confirmation packages...'
    $selection = Invoke-DeepSelection
    $deepLedger = Join-Path $deepSelect 'four_main_deep_package_tl_ledger.csv'

    Write-Host '[final 6/7] Executing/resuming full Stage-A deep confirmation (8.220M)...'
    $deep = Invoke-PackagePhase 'deep' $deepLedger $deepBatchRoot $deepMerge 12 2 6850 100 8220000

    Write-Host '[final 7/7] Final acceptance and result ZIP...'
    $ro = Read-Json $repoOnlySummary
    $final = [ordered]@{}
    $ro.psobject.Properties | ForEach-Object { $final[$_.Name] = $_.Value }
    $final['schemaVersion'] = 'star-cluster-cp153-native-acceptance-v0.1'
    $final['repositoryOnly'] = $false
    $final['repositoryOnlyAccepted'] = $true
    $final['substantiveSweepCompleted'] = $true
    $final['energySubstantiveCombatTrials'] = [int64]$energy.combatTrials
    $final['screenSubstantiveCombatTrials'] = [int64]$screen.combatTrials
    $final['deepSubstantiveCombatTrials'] = [int64]$deep.combatTrials
    $final['substantiveCombatTrials'] = [int64]$energy.combatTrials + [int64]$screen.combatTrials + [int64]$deep.combatTrials
    $final['substantiveTurnCapSentinels'] = [int64]$energy.turnCapSentinels + [int64]$screen.turnCapSentinels + [int64]$deep.turnCapSentinels
    $final['substantiveErrorTrials'] = [int64]$energy.errorTrials + [int64]$screen.errorTrials + [int64]$deep.errorTrials
    $final['kLadders'] = 6; $final['eLadders'] = 8; $final['gpLadders'] = 3; $final['swLadders'] = 3
    $final['wholeLadderPackages'] = 432; $final['deepPackages'] = 12; $final['energyLaddersRepresentedDeep'] = [int]$selection.energyLaddersRepresented
    $final['nextStage'] = 'analyze CP153 four-main Pareto/response evidence; if mains close, sweep defense/AUX lifetime viability before final Reactor/TP supply tuning; no automatic source promotion'
    $final | ConvertTo-Json -Depth 8 | Set-Content $finalSummary -Encoding UTF8
    Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP153 final contract failed'
    $zip = New-ResultZip
    Write-Host "CP153 native acceptance PASSED. Results: $zip" -ForegroundColor Green
}
finally { Pop-Location }
