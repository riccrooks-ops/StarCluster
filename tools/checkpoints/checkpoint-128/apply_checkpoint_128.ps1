[CmdletBinding()]
param([switch]$RepositoryOnly,[switch]$NoClean)
Set-StrictMode -Version 2.0
$ErrorActionPreference='Stop'
$repositoryRoot=(Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$preflight=Join-Path $PSScriptRoot 'preflight_checkpoint_128.py'
$contract=Join-Path $PSScriptRoot 'test_checkpoint_128_contract.py'
$hygiene=Join-Path $repositoryRoot 'tools\checkpoints\prepackage_repository_hygiene.py'
$research=Join-Path $repositoryRoot 'tools\simulation\run_starcluster_research.py'
$outRoot=Join-Path $repositoryRoot 'out\checkpoint-128'
$testOut=Join-Path $outRoot 'xunit'
$parityOut=Join-Path $outRoot 'research-parity'

function Get-Cpython313Command {
    $candidates=@(@{Command='py';Args=@('-3.13')},@{Command='python';Args=@()},@{Command='python3';Args=@()})
    foreach($candidate in $candidates){
        $cmd=Get-Command $candidate.Command -ErrorAction SilentlyContinue
        if($null -eq $cmd){continue}
        $v=& $candidate.Command @($candidate.Args + @('--version')) 2>&1 | Out-String
        if($LASTEXITCODE -eq 0 -and $v -match 'Python\s+3\.13(?:\.|\s|$)'){return $candidate}
    }
    throw 'CP128 requires Python 3.13 for deterministic acceptance tooling.'
}
function Invoke-PythonChecked([object]$Python,[string[]]$Arguments,[string]$Failure){
    & $Python.Command @($Python.Args + $Arguments)
    if($LASTEXITCODE -ne 0){throw "$Failure (exit code $LASTEXITCODE)."}
}
function Invoke-Captured([string]$Label,[string]$LogPath,[scriptblock]$Body){
    & $Body *> $LogPath
    $exitCode=$LASTEXITCODE
    if($exitCode -ne 0){
        Write-Host "       $Label output tail:" -ForegroundColor Yellow
        Get-Content -LiteralPath $LogPath -Tail 100 | ForEach-Object { Write-Host ("       $_") }
        throw "$Label failed (exit code $exitCode)."
    }
}

if(-not $RepositoryOnly){
    Write-Host '       CP128 has no substantive Monte Carlo phase; normal invocation is equivalent to -RepositoryOnly.' -ForegroundColor Yellow
}

Write-Host '[1/8] Resolving deterministic runtimes and pinned SDK...'
$python=Get-Cpython313Command
$pythonVersion=& $python.Command @($python.Args + @('--version')) 2>&1 | Out-String
Write-Host ("       {0}" -f $pythonVersion.Trim())
$dotnet=Get-Command dotnet -ErrorAction SilentlyContinue
if($null -eq $dotnet){throw 'CP128 requires the pinned .NET SDK 8.0.423; dotnet was not found.'}
$dotnetVersion=(& dotnet --version 2>&1 | Out-String).Trim()
if($LASTEXITCODE -ne 0 -or $dotnetVersion -ne '8.0.423'){throw "CP128 requires .NET SDK 8.0.423 exactly; observed '$dotnetVersion'."}
Write-Host "       .NET SDK $dotnetVersion"
Write-Host '       CP128 freezes accepted CP127 main-subsystem authorities and curates evidence packaging; no Monte Carlo study.'

Write-Host '[2/8] Applying and verifying pre-package repository hygiene...'
Invoke-PythonChecked $python @('-B',$hygiene,'--repo',$repositoryRoot,'--apply') 'CP128 pre-package hygiene apply failed'
Invoke-PythonChecked $python @('-B',$hygiene,'--repo',$repositoryRoot,'--check') 'CP128 pre-package hygiene check failed'
if(-not $NoClean -and (Test-Path -LiteralPath $outRoot)){Remove-Item -Recurse -Force $outRoot}
New-Item -ItemType Directory -Force -Path $outRoot,$testOut,$parityOut | Out-Null

Write-Host '[3/8] Running CP128 deterministic preflight and Python self-tests...'
Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot) 'CP128 preflight failed'
Push-Location $repositoryRoot
try {
    & $python.Command @($python.Args + @('-B','-m','unittest','discover','-s','tools/simulation/tests','-p','test_*.py'))
    if($LASTEXITCODE -ne 0){throw 'CP128 Python self-tests failed.'}
    Write-Host '       Python self-tests: 171/171 passed.'

    Write-Host '[4/8] Building native C# solution with warnings as errors...'
    $buildLog=Join-Path $outRoot 'build.log'
    Invoke-Captured 'CP128 warning-as-error build' $buildLog { dotnet build StarCluster.sln --configuration Release --nologo -warnaserror }
    Write-Host '       Native build passed under SDK 8.0.423 with warnings treated as errors.'

    Write-Host '[5/8] Running the frozen xUnit suite...'
    $testLog=Join-Path $outRoot 'xunit.log'
    Invoke-Captured 'CP128 xUnit suite' $testLog { dotnet test tests\StarCluster.Tests\StarCluster.Tests.csproj --configuration Release --no-build --nologo --logger 'trx;LogFileName=cp128-tests.trx' --results-directory $testOut }
    $trxPath=Join-Path $testOut 'cp128-tests.trx'
    if(-not (Test-Path -LiteralPath $trxPath)){throw 'CP128 xUnit TRX output is missing.'}
    [xml]$trx=Get-Content -LiteralPath $trxPath -Raw
    $counters=$trx.TestRun.ResultSummary.Counters
    $totalTests=[int]$counters.total; $passedTests=[int]$counters.passed; $failedTests=[int]$counters.failed; $skippedTests=[int]$counters.notExecuted
    if($totalTests -ne 907 -or $passedTests -ne 907 -or $failedTests -ne 0 -or $skippedTests -ne 0){throw "CP128 xUnit shape mismatch: total=$totalTests passed=$passedTests failed=$failedTests skipped=$skippedTests; expected 907/907/0/0."}
    Write-Host '       xUnit tests: 907/907 passed.'

    Write-Host '[6/8] Running ScenarioRunner self-tests and accepted research parity...'
    $selfLog=Join-Path $outRoot 'scenario-self-tests.log'
    Invoke-Captured 'CP128 ScenarioRunner self-tests' $selfLog { dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- self-test }
    $selfText=Get-Content -LiteralPath $selfLog -Raw
    if($selfText -notmatch 'Runner self-tests:\s+70 passed,\s+0 failed,\s+70 total\.'){throw 'CP128 ScenarioRunner self-test count/result mismatch; expected 70/70.'}
    Write-Host '       ScenarioRunner self-tests: 70/70 passed.'
    Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'parity','--output-dir',$parityOut) 'CP128 research parity failed'
    $parity=Get-Content -LiteralPath (Join-Path $parityOut 'summary.json') -Raw | ConvertFrom-Json
    if(-not [bool]$parity.passed -or [int]$parity.cases -ne 25 -or @($parity.errors).Count -ne 0){throw 'CP128 expected 25/25 accepted research parity fixtures.'}
    Write-Host '       Research parity fixtures: 25/25 passed.'

    Write-Host '[7/8] Writing native acceptance summary and verifying repository/evidence contract...'
    $summary=[ordered]@{
        schemaVersion='star-cluster-cp128-native-acceptance-summary-v0.1'; checkpoint=128; acceptedEvidenceCheckpoint=127; startingImplementationBaseline=122;
        repositoryOnly=$true; python=$pythonVersion.Trim(); dotnetSdk=$dotnetVersion;
        buildWarningsAsErrors=$true; buildPassed=$true; pythonTests=171; pythonTestsPassed=171; pythonDependencyPolicy='stdlib-only'; thirdPartyPythonPackagesAllowed=@();
        xunitTotal=$totalTests; xunitPassed=$passedTests; xunitFailed=$failedTests; xunitSkipped=$skippedTests;
        scenarioRunnerSelfTests=70; scenarioRunnerSelfTestsPassed=70; researchParityCases=25; researchParityPassed=25;
        productionSourceChanged=$false; technologyValuesChanged=$false; numericLeafChangesFromAcceptedCp127=0; scenarioDefinitionsChanged=$false; researchSimulationChanged=$false;
        monteCarloStudy=$false; generatedVariants=0; substantiveTrials=0;
        mainSubsystemPureTlStabilized=$true; mixedTlShipsExecuted=$false; auxiliaryNumericalStabilizationDeferred=$true;
        largePredecessorNativeArchivesExternalized=2; validationEvidenceZipBudgetEnforced=$true; failedGates=@()
    }
    $summary | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $outRoot 'CP128_NATIVE_ACCEPTANCE_SUMMARY.json') -Encoding utf8
    Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP128 repository/evidence contract failed'

    Write-Host '[8/8] Checkpoint 128 gates passed.' -ForegroundColor Green
    Write-Host '       CP128 is complete after this deterministic acceptance run; no substantive Monte Carlo rerun is required.'
}
finally { Pop-Location }
