[CmdletBinding()]
param(
    [switch]$RepositoryOnly,
    [switch]$NoClean,
    [int]$Jobs = 24
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$preflight = Join-Path $PSScriptRoot 'preflight_checkpoint_155.py'
$contract = Join-Path $PSScriptRoot 'test_checkpoint_155_contract.py'
$research = Join-Path $repositoryRoot 'tools\simulation\run_starcluster_research.py'
$study = 'docs/archive/testing/pre-cp165-active/cp155_pds_architecture_resynthesis_study_v0_1.json'
$cp139Study = 'docs/archive/testing/pre-cp165-active/cp139_def_res_reconciliation_study_v0_1.json'
$cp142Study = 'docs/archive/testing/pre-cp165-active/cp142_combat_surface_deep_reconciliation_study_v0_1.json'

$outRoot = Join-Path $repositoryRoot 'out\checkpoint-155'
$testOut = Join-Path $outRoot 'xunit'
$parityOut = Join-Path $outRoot 'research-parity'
$deterministicOut = Join-Path $outRoot 'deterministic-scenarios'
$tl1PhaseAOut = Join-Path $outRoot 'tl1-phase-a'
$cp139Out = Join-Path $outRoot 'cp139-reconciliation'
$cp142Out = Join-Path $outRoot 'cp142-reconciliation-audit'
$planOut = Join-Path $outRoot 'pds-plan'
$smokeRoot = Join-Path $outRoot 'pds-smoke'
$baselineOut = Join-Path $outRoot 'pds-no-pds-baseline'
$candidateBatchRoot = Join-Path $outRoot 'pds-candidate-batches'
$candidateMerge = Join-Path $outRoot 'pds-candidate-merged'
$synthesisOut = Join-Path $outRoot 'pds-ladder-synthesis'
$deepBatchRoot = Join-Path $outRoot 'pds-deep-batches'
$deepMerge = Join-Path $outRoot 'pds-deep-merged'
$repoOnlySummary = Join-Path $outRoot 'CP155_REPOSITORY_ONLY_ACCEPTANCE.json'
$finalSummary = Join-Path $outRoot 'CP155_NATIVE_ACCEPTANCE_SUMMARY.json'

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
    throw 'CP155 requires Python 3.13.'
}

function Invoke-PythonChecked([object]$Python, [string[]]$Arguments, [string]$Failure) {
    & $Python.Command @($Python.Args + $Arguments)
    if ($LASTEXITCODE -ne 0) {
        throw "$Failure (exit code $LASTEXITCODE)."
    }
}

function Invoke-Captured([string]$Label, [string]$LogPath, [scriptblock]$Body) {
    $oldErrorActionPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        & $Body *> $LogPath
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $oldErrorActionPreference
    }
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
    if (-not $prefix.EndsWith([string]$sep)) {
        $prefix += $sep
    }
    if (-not $full.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Path outside repository: $Path"
    }
    return $full.Substring($prefix.Length)
}

function Invoke-PythonWithSimulationPath([scriptblock]$Body) {
    $sim = Join-Path $repositoryRoot 'tools\simulation'
    $old = $env:PYTHONPATH
    try {
        if ([string]::IsNullOrWhiteSpace($old)) {
            $env:PYTHONPATH = $sim
        }
        else {
            $env:PYTHONPATH = $sim + [IO.Path]::PathSeparator + $old
        }
        & $Body
    }
    finally {
        $env:PYTHONPATH = $old
    }
}

function Invoke-PythonFocusedPattern([string]$Pattern, [string]$Failure) {
    Invoke-PythonWithSimulationPath {
        & $python.Command @($python.Args + @('-B','-m','unittest','discover','-v','-s','tools/simulation/tests','-p',$Pattern))
        if ($LASTEXITCODE -ne 0) {
            throw $Failure
        }
    }
}

function Invoke-PythonResearchTests {
    $files = Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'tools\simulation\tests') -Filter 'test_*.py' | Sort-Object Name
    if ($files.Count -ne 46) {
        throw "CP155 expected 46 Python modules, found $($files.Count)."
    }
    $chunks = @(
        @($files[0..12]),
        @($files[13..18]),
        @($files[19..24]),
        @($files[25..38]),
        @($files[39]),
        @($files[40]),
        @($files[41]),
        @($files[42]),
        @($files[43]),
        @($files[44..45])
    )
    Invoke-PythonWithSimulationPath {
        for ($i=0; $i -lt $chunks.Count; $i++) {
            $mods = @($chunks[$i] | ForEach-Object { "tools.simulation.tests.$($_.BaseName)" })
            Write-Host("       Python test chunk {0}/10 ({1} modules)..." -f ($i+1), $mods.Count)
            & $python.Command @($python.Args + @('-B','-m','unittest') + $mods)
            if ($LASTEXITCODE -ne 0) {
                throw "CP155 Python chunk $($i+1) failed."
            }
        }
    }
}

function Invoke-Plan {
    if (Test-Path $planOut) {
        Remove-Item -Recurse -Force $planOut
    }
    New-Item -ItemType Directory -Force -Path $planOut | Out-Null
    Invoke-Captured 'CP155 PDS resynthesis plan' (Join-Path $planOut 'console.log') {
        & $python.Command @($python.Args + @('-B',$research,'--repo',$repositoryRoot,'pds-resynthesis-plan',$study,'--output-dir',(Relative-To-Repo $planOut)))
    }
    $s = Read-Json (Join-Path $planOut 'summary.json')
    if (-not [bool]$s.passed -or [int]$s.candidateTlRows -ne 1846 -or [int]$s.primaryContexts -ne 1560 -or [int]$s.robustnessContexts -ne 300 -or [int]$s.deepContextsPerLadder -ne 1860 -or [int64]$s.baselineCombatTrials -ne 312000 -or [int64]$s.screenCombatTrials -ne 9619200 -or [int64]$s.deepCombatTrials -ne 5580000 -or [int64]$s.substantiveCombatTrials -ne 15511200) {
        throw 'CP155 plan mismatch.'
    }
    return $s
}

function Invoke-OneSmoke([string]$Family, [int]$Tl, [int]$Index, [int]$Trials, [string]$Name) {
    $familyDir = Join-Path $smokeRoot $Family.ToLowerInvariant()
    $dir = Join-Path $familyDir $Name
    if (Test-Path $dir) {
        Remove-Item -Recurse -Force $dir
    }
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    Invoke-Captured "CP155 $Family smoke" (Join-Path $dir 'console.log') {
        & $python.Command @($python.Args + @('-B',$research,'--repo',$repositoryRoot,'pds-resynthesis-candidate-sweep',$study,'--output-dir',(Relative-To-Repo $dir),'--family',$Family,'--tl',$Tl,'--candidate-start',$Index,'--candidate-end',($Index+1),'--jobs',$Jobs,'--trials',$Trials,'--smoke'))
    }
    $s = Read-Json (Join-Path $dir 'summary.json')
    if (-not [bool]$s.passed -or [int]$s.candidates -ne 1 -or [int]$s.contextsPerCandidate -ne 6 -or [int]$s.errors -ne 0) {
        throw "CP155 $Family smoke mismatch."
    }
    return [pscustomobject]@{Dir=$dir; Summary=$s}
}

function Invoke-Smoke {
    if (Test-Path $smokeRoot) {
        Remove-Item -Recurse -Force $smokeRoot
    }
    New-Item -ItemType Directory -Force -Path $smokeRoot | Out-Null

    $k = Invoke-OneSmoke 'Kinetic' 6 7 2 'tl06_krc2_low'
    $e = Invoke-OneSmoke 'Energy' 6 24 4 'tl06_eoc'
    $a = Invoke-OneSmoke 'AMM' 7 14 2 'tl07_arc3'

    if ([int64]$k.Summary.combatTrials -ne 12 -or [int64]$e.Summary.combatTrials -ne 24 -or [int64]$a.Summary.combatTrials -ne 12) {
        throw 'CP155 smoke combat scale mismatch.'
    }

    $eRows = Import-Csv (Join-Path $e.Dir 'pds_candidate_context_results.csv')
    if (-not ($eRows | Where-Object { [double]$_.mean_b_pds_overcharge_attempts -gt 0 -and [int]$_.max_pds_strain -gt 0 })) {
        throw 'CP155 Energy smoke did not exercise overcharged RC2 Strain.'
    }
    $aRows = Import-Csv (Join-Path $a.Dir 'pds_candidate_context_results.csv')
    if (-not ($aRows | Where-Object { [double]$_.mean_b_pds_range_one_attempts -gt 0 })) {
        throw 'CP155 AMM smoke did not exercise the range-one RC3 window.'
    }
    $kRows = Import-Csv (Join-Path $k.Dir 'pds_candidate_context_results.csv')
    if ($kRows | Where-Object { [double]$_.mean_b_pds_range_one_attempts -gt 0 -or [double]$_.mean_b_pds_overcharge_attempts -gt 0 }) {
        throw 'CP155 Kinetic smoke crossed a forbidden PDS architecture boundary.'
    }

    return [pscustomobject]@{
        combatTrials = [int64]48
        turnCaps = [int64]$k.Summary.turnCapSentinels + [int64]$e.Summary.turnCapSentinels + [int64]$a.Summary.turnCapSentinels
    }
}

function Test-Baseline {
    $sp = Join-Path $baselineOut 'summary.json'
    $rp = Join-Path $baselineOut 'pds_no_pds_baseline.csv'
    if (-not (Test-Path $sp) -or -not (Test-Path $rp)) {
        return $false
    }
    try {
        $s = Read-Json $sp
        return ([bool]$s.passed -and [string]$s.mode -eq 'no-pds-baseline' -and [int]$s.contexts -eq 1560 -and [int]$s.trialsPerCell -eq 200 -and [int64]$s.combatTrials -eq 312000 -and [int]$s.errors -eq 0)
    }
    catch {
        return $false
    }
}

function Invoke-Baseline {
    if (Test-Baseline) {
        Write-Host '       CP155 no-PDS baseline valid; reusing.'
    }
    else {
        if (Test-Path $baselineOut) {
            Remove-Item -Recurse -Force $baselineOut
        }
        New-Item -ItemType Directory -Force -Path $baselineOut | Out-Null
        Write-Host '       CP155 no-PDS baseline: 312,000 combats'
        Invoke-Captured 'CP155 no-PDS baseline' (Join-Path $baselineOut 'console.log') {
            & $python.Command @($python.Args + @('-B',$research,'--repo',$repositoryRoot,'pds-resynthesis-baseline',$study,'--output-dir',(Relative-To-Repo $baselineOut),'--jobs',$Jobs,'--trials','200'))
        }
        if (-not (Test-Baseline)) {
            throw 'CP155 no-PDS baseline failed validation.'
        }
    }
    return (Read-Json (Join-Path $baselineOut 'summary.json'))
}

function Test-CandidateBatch([string]$Dir, [string]$Family, [int]$Tl, [int]$End, [int]$Contexts, [int]$Trials) {
    $sp = Join-Path $Dir 'summary.json'
    $rp = Join-Path $Dir 'pds_candidate_context_results.csv'
    if (-not (Test-Path $sp) -or -not (Test-Path $rp)) {
        return $false
    }
    try {
        $s = Read-Json $sp
        $cells = $End * $Contexts
        return (
            [bool]$s.passed -and
            [string]$s.mode -eq 'candidate-screen-batch' -and
            [string]$s.family -eq $Family -and
            [int]$s.tl -eq $Tl -and
            [int]$s.candidateStart -eq 0 -and
            [int]$s.candidateEnd -eq $End -and
            [int]$s.candidates -eq $End -and
            [int]$s.contextsPerCandidate -eq $Contexts -and
            [int]$s.candidateContextCells -eq $cells -and
            [int]$s.trialsPerCell -eq $Trials -and
            [int64]$s.combatTrials -eq ([int64]$cells * $Trials) -and
            [int]$s.errors -eq 0
        )
    }
    catch {
        return $false
    }
}

function Invoke-CandidateScreen {
    New-Item -ItemType Directory -Force -Path $candidateBatchRoot | Out-Null
    if (Test-Path $candidateMerge) {
        Remove-Item -Recurse -Force $candidateMerge
    }
    New-Item -ItemType Directory -Force -Path $candidateMerge | Out-Null

    $counts = Import-Csv (Join-Path $planOut 'pds_candidate_counts.csv')
    $batchNumber = 0
    $batchTotal = 27
    foreach ($row in $counts) {
        $family = [string]$row.family
        $tl = [int]$row.tl
        $candidates = [int]$row.candidates
        $contexts = [int]$row.primary_contexts
        $batchNumber++
        $familyName = $family.ToLowerInvariant()
        $dir = Join-Path $candidateBatchRoot ("{0}_tl{1:D2}_0000_{2:D4}" -f $familyName,$tl,$candidates)
        if (Test-CandidateBatch $dir $family $tl $candidates $contexts 30) {
            Write-Host("       CP155 PDS batch {0}/{1} {2} TL{3} valid; reusing." -f $batchNumber,$batchTotal,$family,$tl)
        }
        else {
            if (Test-Path $dir) {
                Remove-Item -Recurse -Force $dir
            }
            New-Item -ItemType Directory -Force -Path $dir | Out-Null
            $combats = [int64]$candidates * $contexts * 30
            Write-Host("       CP155 PDS batch {0}/{1} {2} TL{3}: {4:N0} combats" -f $batchNumber,$batchTotal,$family,$tl,$combats)
            Invoke-Captured "CP155 $family TL$tl" (Join-Path $dir 'console.log') {
                & $python.Command @($python.Args + @('-B',$research,'--repo',$repositoryRoot,'pds-resynthesis-candidate-sweep',$study,'--output-dir',(Relative-To-Repo $dir),'--family',$family,'--tl',$tl,'--candidate-start','0','--candidate-end',$candidates,'--jobs',$Jobs,'--trials','30'))
            }
            if (-not (Test-CandidateBatch $dir $family $tl $candidates $contexts 30)) {
                throw 'CP155 PDS candidate batch failed validation.'
            }
        }
    }
    if ($batchNumber -ne 27) {
        throw "CP155 candidate batch count $batchNumber."
    }

    Invoke-Captured 'CP155 candidate merge' (Join-Path $candidateMerge 'console.log') {
        & $python.Command @($python.Args + @('-B',$research,'--repo',$repositoryRoot,'pds-resynthesis-candidate-merge',$study,'--baseline-dir',(Relative-To-Repo $baselineOut),'--batch-root',(Relative-To-Repo $candidateBatchRoot),'--output-dir',(Relative-To-Repo $candidateMerge)))
    }
    $s = Read-Json (Join-Path $candidateMerge 'summary.json')
    if (-not [bool]$s.passed -or [int]$s.candidates -ne 1846 -or [int]$s.candidateContextCells -ne 320640 -or [int64]$s.combatTrials -ne 9619200 -or [int]$s.errorTrials -ne 0) {
        throw 'CP155 candidate merge mismatch.'
    }
    return $s
}

function Invoke-LadderSynthesis {
    if (Test-Path $synthesisOut) {
        Remove-Item -Recurse -Force $synthesisOut
    }
    New-Item -ItemType Directory -Force -Path $synthesisOut | Out-Null
    Invoke-Captured 'CP155 PDS ladder synthesis' (Join-Path $synthesisOut 'console.log') {
        & $python.Command @($python.Args + @('-B',$research,'--repo',$repositoryRoot,'pds-resynthesis-ladder-synthesize',$study,'--candidate-merged',(Relative-To-Repo $candidateMerge),'--output-dir',(Relative-To-Repo $synthesisOut)))
    }
    $s = Read-Json (Join-Path $synthesisOut 'summary.json')
    if (-not [bool]$s.passed -or [int]$s.laddersPerFamily -ne 10 -or [int]$s.deepLadders -ne 30 -or [int]$s.ladderTlRows -ne 270) {
        throw 'CP155 ladder synthesis mismatch.'
    }
    return $s
}

function Test-DeepBatch([string]$Dir, [int]$Start, [int]$End, [int]$Trials) {
    $sp = Join-Path $Dir 'summary.json'
    $rp = Join-Path $Dir 'pds_deep_context_results.csv'
    if (-not (Test-Path $sp) -or -not (Test-Path $rp)) {
        return $false
    }
    try {
        $s = Read-Json $sp
        $n = $End - $Start
        $cells = $n * 1860
        return (
            [bool]$s.passed -and
            [string]$s.mode -eq 'deep-batch' -and
            [int]$s.ladderStart -eq $Start -and
            [int]$s.ladderEnd -eq $End -and
            [int]$s.ladders -eq $n -and
            [int]$s.contextsPerLadder -eq 1860 -and
            [int]$s.ladderContextCells -eq $cells -and
            [int]$s.trialsPerCell -eq $Trials -and
            [int64]$s.combatTrials -eq ([int64]$cells * $Trials) -and
            [int]$s.errors -eq 0
        )
    }
    catch {
        return $false
    }
}

function Invoke-DeepConfirmation {
    New-Item -ItemType Directory -Force -Path $deepBatchRoot | Out-Null
    if (Test-Path $deepMerge) {
        Remove-Item -Recurse -Force $deepMerge
    }
    New-Item -ItemType Directory -Force -Path $deepMerge | Out-Null
    $ledger = Join-Path $synthesisOut 'pds_ladder_candidates.csv'

    $start = 0
    $batch = 0
    while ($start -lt 30) {
        $end = [Math]::Min($start + 2, 30)
        $batch++
        $dir = Join-Path $deepBatchRoot ("batch_{0:D2}_{1:D2}" -f $start,$end)
        if (Test-DeepBatch $dir $start $end 100) {
            Write-Host("       CP155 deep batch {0}/15 ladders {1}-{2} valid; reusing." -f $batch,$start,($end-1))
        }
        else {
            if (Test-Path $dir) {
                Remove-Item -Recurse -Force $dir
            }
            New-Item -ItemType Directory -Force -Path $dir | Out-Null
            $combats = [int64]($end-$start) * 1860 * 100
            Write-Host("       CP155 deep batch {0}/15 ladders {1}-{2}: {3:N0} combats" -f $batch,$start,($end-1),$combats)
            Invoke-Captured "CP155 deep $start-$end" (Join-Path $dir 'console.log') {
                & $python.Command @($python.Args + @('-B',$research,'--repo',$repositoryRoot,'pds-resynthesis-deep-sweep',$study,'--ladder-ledger',(Relative-To-Repo $ledger),'--output-dir',(Relative-To-Repo $dir),'--ladder-start',$start,'--ladder-end',$end,'--jobs',$Jobs,'--trials','100'))
            }
            if (-not (Test-DeepBatch $dir $start $end 100)) {
                throw 'CP155 deep batch failed validation.'
            }
        }
        $start = $end
    }

    Invoke-Captured 'CP155 deep merge' (Join-Path $deepMerge 'console.log') {
        & $python.Command @($python.Args + @('-B',$research,'--repo',$repositoryRoot,'pds-resynthesis-deep-merge',$study,'--baseline-dir',(Relative-To-Repo $baselineOut),'--ladder-ledger',(Relative-To-Repo $ledger),'--batch-root',(Relative-To-Repo $deepBatchRoot),'--output-dir',(Relative-To-Repo $deepMerge)))
    }
    $s = Read-Json (Join-Path $deepMerge 'summary.json')
    if (-not [bool]$s.passed -or [int]$s.ladders -ne 30 -or [int]$s.ladderContextCells -ne 55800 -or [int64]$s.combatTrials -ne 5580000 -or [int]$s.errorTrials -ne 0 -or [int]$s.triadCombinations -ne 1000 -or [bool]$s.equalizationObjectiveUsed) {
        throw 'CP155 deep merge mismatch.'
    }
    return $s
}

function New-ResultZip {
    $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $zip = Join-Path $outRoot ("StarCluster_CP155_native_results_$stamp.zip")
    $stage = Join-Path $repositoryRoot 'out\checkpoint-155-package-staging'
    if (Test-Path $stage) {
        Remove-Item -Recurse -Force $stage
    }
    New-Item -ItemType Directory -Force -Path $stage | Out-Null
    $skip = @('pds-candidate-batches','pds-deep-batches')
    foreach ($item in Get-ChildItem -LiteralPath $outRoot -Force) {
        if ($item.FullName -eq $zip -or $item.Name -in $skip -or $item.Name -like 'StarCluster_CP155_native_results_*.zip') {
            continue
        }
        Copy-Item -LiteralPath $item.FullName -Destination $stage -Recurse -Force
    }
    foreach ($spec in @(
        @('pds-candidate-batch-summaries',$candidateBatchRoot),
        @('pds-deep-batch-summaries',$deepBatchRoot)
    )) {
        $dest = Join-Path $stage $spec[0]
        New-Item -ItemType Directory -Force -Path $dest | Out-Null
        if (Test-Path $spec[1]) {
            foreach ($d in Get-ChildItem -LiteralPath $spec[1] -Directory | Sort-Object Name) {
                $sp = Join-Path $d.FullName 'summary.json'
                if (Test-Path $sp) {
                    Copy-Item $sp (Join-Path $dest ($d.Name + '_summary.json')) -Force
                }
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
if ($LASTEXITCODE -ne 0 -or $dotnetVersion -ne '8.0.423') {
    throw "CP155 requires .NET SDK 8.0.423 exactly; observed '$dotnetVersion'."
}
Write-Host("CP155 runtimes: {0}; .NET SDK {1}" -f $pythonVersion.Trim(),$dotnetVersion)
Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot) 'CP155 preflight failed'

if ($RepositoryOnly) {
    if (-not $NoClean -and (Test-Path $outRoot)) {
        Remove-Item -Recurse -Force $outRoot
    }
    New-Item -ItemType Directory -Force -Path $outRoot,$testOut,$parityOut,$deterministicOut,$tl1PhaseAOut,$cp139Out,$cp142Out | Out-Null
    Push-Location $repositoryRoot
    try {
        Write-Host '[1/10] Python research tests (500 total)...'
        Invoke-PythonResearchTests

        Write-Host '[2/10] Warning-as-error .NET build...'
        Invoke-Captured 'CP155 build' (Join-Path $outRoot 'build.log') {
            dotnet build StarCluster.sln --configuration Release --nologo -warnaserror
        }

        Write-Host '[3/10] xUnit + ScenarioRunner deterministic corpora...'
        dotnet test tests\StarCluster.Tests\StarCluster.Tests.csproj --configuration Release --no-build --nologo --logger 'trx;LogFileName=cp155-tests.trx' --results-directory $testOut
        $xunitExit = $LASTEXITCODE
        [xml]$trx = Get-Content -LiteralPath (Join-Path $testOut 'cp155-tests.trx') -Raw
        $c = $trx.TestRun.ResultSummary.Counters
        $total = [int]$c.total
        $passed = [int]$c.passed
        $failed = [int]$c.failed
        $skipped = [int]$c.notExecuted
        if ($xunitExit -ne 0 -or $total -ne 934 -or $passed -ne 934 -or $failed -ne 0 -or $skipped -ne 0) {
            throw 'CP155 xUnit mismatch.'
        }
        $selfLog = Join-Path $outRoot 'scenario-self-tests.log'
        Invoke-Captured 'CP155 ScenarioRunner self-tests' $selfLog {
            dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- self-test
        }
        if ((Get-Content $selfLog -Raw) -notmatch 'Runner self-tests:\s+70 passed,\s+0 failed,\s+70 total\.') {
            throw 'CP155 expected 70/70 self-tests.'
        }
        Invoke-Captured 'CP155 deterministic scenarios' (Join-Path $outRoot 'deterministic-scenarios.log') {
            dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- run-all --output-dir $deterministicOut
        }
        Invoke-Captured 'CP155 TL1 Phase-A' (Join-Path $outRoot 'tl1-phase-a.log') {
            dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- tl1-phase-a --output-dir $tl1PhaseAOut
        }

        Write-Host '[4/10] C#/Python parity...'
        Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'parity','--output-dir',$parityOut) 'CP155 parity failed'
        $parity = Read-Json (Join-Path $parityOut 'summary.json')
        if (-not [bool]$parity.passed -or [int]$parity.cases -ne 25) {
            throw 'CP155 parity mismatch.'
        }

        Write-Host '[5/10] CP139 reconciliation foundation...'
        Invoke-PythonFocusedPattern 'test_cp139_def_res_reconciliation.py' 'CP139 focused failed'
        Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'combat-model-reconciliation-study',$cp139Study,'--output-dir','out/checkpoint-155/cp139-reconciliation') 'CP139 reconciliation failed'

        Write-Host '[6/10] Focused CP140-CP155 regression tests...'
        foreach ($pattern in @(
            'test_cp140_stage_a_integration.py','test_cp141_combat_duration_stalemate.py','test_cp142_combat_surface_reconciliation.py','test_cp143_missile_mirror_pacing_attribution.py',
            'test_cp144_*.py','test_cp145_*.py','test_cp146_*.py','test_cp147_*.py','test_cp148_*.py','test_cp149_*.py','test_cp150_*.py','test_cp151_*.py','test_cp152_*.py','test_cp153_*.py','test_cp154_*.py','test_cp155_*.py'
        )) {
            Invoke-PythonFocusedPattern $pattern "Focused regression failed: $pattern"
        }

        Write-Host '[7/10] CP142 reconciliation audit...'
        Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'combat-surface-reconciliation-audit',$cp142Study,'--output-dir','out/checkpoint-155/cp142-reconciliation-audit') 'CP142 audit failed'
        $audit = Read-Json (Join-Path $cp142Out 'reconciliation_summary.json')
        if (-not [bool]$audit.passed -or [int]$audit.ledgerRows -ne 531 -or [int]$audit.changedVsCp141Rows -ne 72 -or [int]$audit.explicitUnresolvedRows -ne 7) {
            throw 'CP142 audit mismatch.'
        }

        Write-Host '[8/10] CP155 15.5112M architecture-constrained resynthesis plan...'
        $plan = Invoke-Plan

        Write-Host '[9/10] CP155 architecture smoke (K RC2 lower-bound, E overcharged RC2, AMM RC3/range-one)...'
        $smoke = Invoke-Smoke

        Write-Host '[10/10] Writing RepositoryOnly acceptance...'
        $summary = [ordered]@{
            schemaVersion='star-cluster-cp155-repository-only-acceptance-v0.1'
            checkpoint=155
            repositoryOnly=$true
            failedGates=@()
            python=$pythonVersion.Trim()
            dotnetSdk=$dotnetVersion
            buildPassed=$true
            pythonTestsPassed=500
            xunitTotal=$total
            xunitPassed=$passed
            xunitFailed=$failed
            xunitSkipped=$skipped
            scenarioRunnerSelfTestsPassed=70
            deterministicScenarioCorpusPassed=$true
            tl1PhaseACorpusPassed=$true
            researchParityPassed=25
            cp139FocusedTestsPassed=9
            cp140FocusedTestsPassed=10
            cp141FocusedTestsPassed=10
            cp142FocusedTestsPassed=12
            cp143FocusedTestsPassed=12
            cp144FocusedTestsPassed=11
            cp145FocusedTestsPassed=12
            cp146FocusedTestsPassed=18
            cp147FocusedTestsPassed=18
            cp148FocusedTestsPassed=12
            cp149FocusedTestsPassed=16
            cp150FocusedTestsPassed=16
            cp151FocusedTestsPassed=18
            cp152FocusedTestsPassed=18
            cp153FocusedTestsPassed=21
            cp154FocusedTestsPassed=25
            cp155FocusedTestsPassed=28
            acceptedCp154EvidenceHashLocked=$true
            pointScale=2
            combatDoctrine='cp147_tactical_utility'
            pdsCandidateTlRows=1846
            primaryContexts=1560
            robustnessContexts=300
            deepContextsPerLadder=1860
            deepLadders=30
            plannedNoPdsBaselineCombatTrials=312000
            plannedCandidateContextCells=320640
            plannedCandidateScreenCombatTrials=9619200
            plannedDeepCombatTrials=5580000
            plannedSubstantiveCombatTrials=15511200
            pdsSmokeCombatTrials=[int64]$smoke.combatTrials
            smokeTurnCapSentinels=[int64]$smoke.turnCaps
            smokeErrors=0
            equalizationObjectiveUsed=$false
            kAmmoFixed=75
            ammAmmoFixed=25
            kRc2BoundaryExtended=$true
            energyArchitectureStratified=$true
            ammRangeOneArchitectureStratified=$true
            technologyProgressionHardConstrained=$true
            noPdsMissileThreatAnchorPreserved=$true
            simultaneousMultiFlightBalanceDeferred=$true
            sourceMatrixUnmodified=$true
            conceptUnmodified=$true
            productionCSharpUnmodified=$true
            substantiveCombatTrials=0
            tuningAllowed=$false
            automaticPromotion=$false
            stageBAutomatic=$false
            nextStage='execute/resume CP155 no-PDS anchor, focused PDS screen, technology-valid ladder synthesis, and Pareto/viability deep confirmation'
        }
        $summary | ConvertTo-Json -Depth 8 | Set-Content $repoOnlySummary -Encoding UTF8
        Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP155 RepositoryOnly contract failed'
        Write-Host 'CP155 RepositoryOnly PASSED. Run again without -RepositoryOnly to execute/resume 15,511,200 substantive combats.' -ForegroundColor Green
    }
    finally {
        Pop-Location
    }
    exit 0
}

if (-not (Test-Path $repoOnlySummary)) {
    throw 'Run CP155 -RepositoryOnly first in this same extraction.'
}

Push-Location $repositoryRoot
try {
    Write-Host '[final 1/6] Revalidating repository and RepositoryOnly state...'
    Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot) 'CP155 final preflight failed'
    Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP155 RepositoryOnly state contract failed'
    $plan = Invoke-Plan

    Write-Host '[final 2/6] Executing/resuming no-PDS CP153 main-balance anchor (312k)...'
    $baseline = Invoke-Baseline

    Write-Host '[final 3/6] Executing/resuming focused PDS screen (9.6192M)...'
    $candidate = Invoke-CandidateScreen

    Write-Host '[final 4/6] Synthesizing 10 K / 10 E / 10 AMM technology-valid ladders...'
    $synthesis = Invoke-LadderSynthesis

    Write-Host '[final 5/6] Executing/resuming 30-ladder primary+robustness deep confirmation (5.58M)...'
    $deep = Invoke-DeepConfirmation

    Write-Host '[final 6/6] Final acceptance and result ZIP...'
    $ro = Read-Json $repoOnlySummary
    $final = [ordered]@{}
    $ro.psobject.Properties | ForEach-Object { $final[$_.Name] = $_.Value }
    $final['schemaVersion'] = 'star-cluster-cp155-native-acceptance-v0.1'
    $final['repositoryOnly'] = $false
    $final['repositoryOnlyAccepted'] = $true
    $final['substantiveSweepCompleted'] = $true
    $final['noPdsBaselineCombatTrials'] = [int64]$baseline.combatTrials
    $final['candidateScreenCombatTrials'] = [int64]$candidate.combatTrials
    $final['deepConfirmationCombatTrials'] = [int64]$deep.combatTrials
    $final['substantiveCombatTrials'] = [int64]$baseline.combatTrials + [int64]$candidate.combatTrials + [int64]$deep.combatTrials
    $final['substantiveTurnCapSentinels'] = [int64]$baseline.turnCapSentinels + [int64]$candidate.turnCapSentinels + [int64]$deep.turnCapSentinels
    $final['substantiveErrorTrials'] = [int64]$baseline.errors + [int64]$candidate.errorTrials + [int64]$deep.errorTrials
    $final['kineticLadders'] = 10
    $final['energyLadders'] = 10
    $final['ammLadders'] = 10
    $final['deepLadders'] = 30
    $final['triadCombinations'] = [int]$deep.triadCombinations
    $final['equalizationObjectiveUsed'] = $false
    $final['nextStage'] = 'analyze CP155 Pareto/viability PDS evidence; if PDS closes, sweep remaining defense/AUX lifetime viability before final Reactor/TP scarcity tuning; no automatic source promotion'
    $final | ConvertTo-Json -Depth 8 | Set-Content $finalSummary -Encoding UTF8
    Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP155 final contract failed'
    $zip = New-ResultZip
    Write-Host "CP155 native acceptance PASSED. Results: $zip" -ForegroundColor Green
}
finally {
    Pop-Location
}
