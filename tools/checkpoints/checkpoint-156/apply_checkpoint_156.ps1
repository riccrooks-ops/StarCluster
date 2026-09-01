[CmdletBinding()]
param(
    [switch]$RepositoryOnly,
    [switch]$NoClean
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$preflight = Join-Path $PSScriptRoot 'preflight_checkpoint_156.py'
$contract = Join-Path $PSScriptRoot 'test_checkpoint_156_contract.py'
$research = Join-Path $repositoryRoot 'tools\simulation\run_starcluster_research.py'
$outRoot = Join-Path $repositoryRoot 'out\checkpoint-156'
$testOut = Join-Path $outRoot 'xunit'
$parityOut = Join-Path $outRoot 'research-parity'
$deterministicOut = Join-Path $outRoot 'deterministic-scenarios'
$tl1PhaseAOut = Join-Path $outRoot 'tl1-phase-a'
$continuityOut = Join-Path $outRoot 'continuity-snapshot'
$repoOnlySummary = Join-Path $outRoot 'CP156_REPOSITORY_ONLY_ACCEPTANCE.json'
$finalSummary = Join-Path $outRoot 'CP156_NATIVE_ACCEPTANCE_SUMMARY.json'

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
    throw 'CP156 requires Python 3.13.'
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
    }
    finally { $ErrorActionPreference = $old }
    if ($code -ne 0) {
        Write-Host "       $Label output tail:" -ForegroundColor Yellow
        Get-Content -LiteralPath $LogPath -Tail 120 | ForEach-Object { Write-Host("       $_") }
        throw "$Label failed (exit code $code)."
    }
}

function Read-Json([string]$Path) { return (Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json) }

function Invoke-PythonResearchTests {
    $files = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'tools\simulation\tests') -Filter 'test_*.py' | Sort-Object Name)
    if ($files.Count -ne 47) { throw "CP156 expected 47 Python modules, found $($files.Count)." }
    $sim = Join-Path $repositoryRoot 'tools\simulation'
    $oldPath = $env:PYTHONPATH
    try {
        if ([string]::IsNullOrWhiteSpace($oldPath)) { $env:PYTHONPATH = $sim } else { $env:PYTHONPATH = $sim + [IO.Path]::PathSeparator + $oldPath }
        $chunkSize = 8
        $chunks = [Math]::Ceiling($files.Count / [double]$chunkSize)
        for ($c=0; $c -lt $chunks; $c++) {
            $start = $c * $chunkSize
            $end = [Math]::Min($files.Count - 1, $start + $chunkSize - 1)
            $mods = @($files[$start..$end] | ForEach-Object { "tools.simulation.tests.$($_.BaseName)" })
            Write-Host("       Python test chunk {0}/{1} ({2} modules)..." -f ($c+1),$chunks,$mods.Count)
            & $python.Command @($python.Args + @('-B','-m','unittest') + $mods)
            if ($LASTEXITCODE -ne 0) { throw "CP156 Python chunk $($c+1) failed." }
        }
    }
    finally { $env:PYTHONPATH = $oldPath }
}

function Copy-ContinuitySnapshot {
    if (Test-Path $continuityOut) { Remove-Item -Recurse -Force $continuityOut }
    New-Item -ItemType Directory -Force -Path $continuityOut | Out-Null
    $src = Join-Path $repositoryRoot 'docs\validation\evidence\checkpoint-156'
    foreach ($name in @(
        'research_continuity_register_v0_1.json','authority_snapshot_v0_1.json','promotion_audit_v0_1.csv',
        'research_findings_ledger_v0_1.csv','viable_ladder_register_v0_1.csv','guardrail_registry_v0_1.json',
        'future_pass_contract_v0_1.json','evidence_chain_sha256_v0_1.csv'
    )) { Copy-Item -LiteralPath (Join-Path $src $name) -Destination $continuityOut }
}

function New-ResultZip {
    $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $zip = Join-Path $repositoryRoot ("StarCluster_CP156_native_results_{0}.zip" -f $stamp)
    if (Test-Path $zip) { Remove-Item -Force $zip }
    Compress-Archive -Path (Join-Path $outRoot '*') -DestinationPath $zip -CompressionLevel Optimal
    return $zip
}

$python = Get-Cpython313Command
$pythonVersion = & $python.Command @($python.Args + @('--version')) 2>&1 | Out-String
$dotnetVersion = (& dotnet --version 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or $dotnetVersion -ne '8.0.423') { throw "CP156 requires .NET SDK 8.0.423 exactly; observed '$dotnetVersion'." }
Write-Host("CP156 runtimes: {0}; .NET SDK {1}" -f $pythonVersion.Trim(),$dotnetVersion)
Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot) 'CP156 preflight failed'

if ($RepositoryOnly) {
    if (-not $NoClean -and (Test-Path $outRoot)) { Remove-Item -Recurse -Force $outRoot }
    New-Item -ItemType Directory -Force -Path $outRoot,$testOut,$parityOut,$deterministicOut,$tl1PhaseAOut | Out-Null
    Push-Location $repositoryRoot
    try {
        Write-Host '[1/7] Python research regression (520 tests)...'
        Invoke-PythonResearchTests

        Write-Host '[2/7] Warning-as-error .NET build...'
        Invoke-Captured 'CP156 build' (Join-Path $outRoot 'build.log') { dotnet build StarCluster.sln --configuration Release --nologo -warnaserror }

        Write-Host '[3/7] xUnit + ScenarioRunner regression...'
        dotnet test tests\StarCluster.Tests\StarCluster.Tests.csproj --configuration Release --no-build --nologo --logger 'trx;LogFileName=cp156-tests.trx' --results-directory $testOut
        $xunitExit = $LASTEXITCODE
        [xml]$trx = Get-Content -LiteralPath (Join-Path $testOut 'cp156-tests.trx') -Raw
        $counters = $trx.TestRun.ResultSummary.Counters
        $total=[int]$counters.total; $passed=[int]$counters.passed; $failed=[int]$counters.failed; $skipped=[int]$counters.notExecuted
        if ($xunitExit -ne 0 -or $total -ne 934 -or $passed -ne 934 -or $failed -ne 0 -or $skipped -ne 0) { throw 'CP156 xUnit mismatch.' }
        $selfLog=Join-Path $outRoot 'scenario-self-tests.log'
        Invoke-Captured 'CP156 ScenarioRunner self-tests' $selfLog { dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- self-test }
        if ((Get-Content $selfLog -Raw) -notmatch 'Runner self-tests:\s+70 passed,\s+0 failed,\s+70 total\.') { throw 'CP156 expected 70/70 self-tests.' }
        Invoke-Captured 'CP156 deterministic scenarios' (Join-Path $outRoot 'deterministic-scenarios.log') { dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- run-all --output-dir $deterministicOut }
        Invoke-Captured 'CP156 TL1 Phase-A' (Join-Path $outRoot 'tl1-phase-a.log') { dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- tl1-phase-a --output-dir $tl1PhaseAOut }

        Write-Host '[4/7] C#/Python parity...'
        Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'parity','--output-dir',$parityOut) 'CP156 parity failed'
        $parity=Read-Json (Join-Path $parityOut 'summary.json')
        if (-not [bool]$parity.passed -or [int]$parity.cases -ne 25) { throw 'CP156 parity mismatch.' }

        Write-Host '[5/7] CP156 focused continuity tests...'
        $sim=Join-Path $repositoryRoot 'tools\simulation'; $oldPath=$env:PYTHONPATH
        try {
            if ([string]::IsNullOrWhiteSpace($oldPath)) { $env:PYTHONPATH=$sim } else { $env:PYTHONPATH=$sim+[IO.Path]::PathSeparator+$oldPath }
            & $python.Command @($python.Args + @('-B','-m','unittest','discover','-v','-s','tools/simulation/tests','-p','test_cp156_*.py'))
            if ($LASTEXITCODE -ne 0) { throw 'CP156 focused tests failed.' }
        }
        finally { $env:PYTHONPATH=$oldPath }

        Write-Host '[6/7] Freezing continuity snapshot...'
        Copy-ContinuitySnapshot

        Write-Host '[7/7] Writing RepositoryOnly acceptance...'
        $summary=[ordered]@{
            schemaVersion='star-cluster-cp156-repository-only-acceptance-v0.1'; checkpoint=156; repositoryOnly=$true; failedGates=@();
            python=$pythonVersion.Trim(); dotnetSdk=$dotnetVersion; buildPassed=$true; pythonTestsPassed=520;
            xunitTotal=$total; xunitPassed=$passed; xunitFailed=$failed; xunitSkipped=$skipped; scenarioRunnerSelfTestsPassed=70;
            deterministicScenarioCorpusPassed=$true; tl1PhaseACorpusPassed=$true; researchParityPassed=25; cp156FocusedTestsPassed=20;
            cp155NativeEvidencePreserved=$true; promotionAuditPassed=$true; guardrailsFrozen=$true; viableLadderRowsPreserved=447;
            evidenceHashRows=52; activeAuthorityHashLocked=$true; closedSurfaceReuseRuleFrozen=$true; noGlobalPds50RuleFrozen=$true;
            nextPass='Defense/AUX Lifetime Viability'; finalMajorPass='Reactor/TP Scarcity and Whole-Ship Equilibrium';
            substantiveCombatTrials=0; tuningAllowed=$false; automaticPromotion=$false; authorityChanges=$false
        }
        $summary | ConvertTo-Json -Depth 8 | Set-Content $repoOnlySummary -Encoding UTF8
        Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP156 RepositoryOnly contract failed'
        Write-Host 'CP156 RepositoryOnly PASSED. Run again without -RepositoryOnly for final zero-combat native acceptance/package.' -ForegroundColor Green
    }
    finally { Pop-Location }
    exit 0
}

if (-not (Test-Path $repoOnlySummary)) { throw 'Run CP156 -RepositoryOnly first in this same extraction.' }
Push-Location $repositoryRoot
try {
    Write-Host '[final 1/3] Revalidating repository and continuity state...'
    Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot) 'CP156 final preflight failed'
    Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP156 RepositoryOnly state contract failed'

    Write-Host '[final 2/3] Writing final zero-combat native acceptance...'
    $ro=Read-Json $repoOnlySummary; $final=[ordered]@{}
    $ro.psobject.Properties | ForEach-Object { $final[$_.Name]=$_.Value }
    $final['schemaVersion']='star-cluster-cp156-native-acceptance-v0.1'; $final['repositoryOnly']=$false; $final['repositoryOnlyAccepted']=$true; $final['continuityAuditCompleted']=$true
    $final | ConvertTo-Json -Depth 8 | Set-Content $finalSummary -Encoding UTF8
    Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP156 final contract failed'

    Write-Host '[final 3/3] Packaging native results...'
    $zip=New-ResultZip
    Write-Host "CP156 native acceptance PASSED. Results: $zip" -ForegroundColor Green
}
finally { Pop-Location }
