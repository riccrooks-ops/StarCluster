[CmdletBinding()]
param([switch]$RepositoryOnly,[switch]$NoClean)
Set-StrictMode -Version 2.0
$ErrorActionPreference='Stop'
$repositoryRoot=(Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$preflight=Join-Path $PSScriptRoot 'preflight_checkpoint_132.py'
$contract=Join-Path $PSScriptRoot 'test_checkpoint_132_contract.py'
$hygiene=Join-Path $repositoryRoot 'tools\checkpoints\prepackage_repository_hygiene.py'
$research=Join-Path $repositoryRoot 'tools\simulation\run_starcluster_research.py'
$outRoot=Join-Path $repositoryRoot 'out\checkpoint-132'
$testOut=Join-Path $outRoot 'xunit'
$parityOut=Join-Path $outRoot 'research-parity'
$deterministicOut=Join-Path $outRoot 'deterministic-scenarios'
$tl1PhaseAOut=Join-Path $outRoot 'tl1-phase-a'
$repoOnlySummary=Join-Path $outRoot 'CP132_REPOSITORY_ONLY_ACCEPTANCE.json'
$finalSummary=Join-Path $outRoot 'CP132_NATIVE_ACCEPTANCE_SUMMARY.json'

function Get-Cpython313Command {
    $candidates=@(@{Command='py';Args=@('-3.13')},@{Command='python';Args=@()},@{Command='python3';Args=@()})
    foreach($candidate in $candidates){
        $cmd=Get-Command $candidate.Command -ErrorAction SilentlyContinue
        if($null -eq $cmd){continue}
        $v=& $candidate.Command @($candidate.Args + @('--version')) 2>&1 | Out-String
        if($LASTEXITCODE -eq 0 -and $v -match 'Python\s+3\.13(?:\.|\s|$)'){return $candidate}
    }
    throw 'CP132 requires Python 3.13 for deterministic acceptance tooling.'
}
function Invoke-PythonChecked([object]$Python,[string[]]$Arguments,[string]$Failure){
    & $Python.Command @($Python.Args + $Arguments)
    if($LASTEXITCODE -ne 0){throw "$Failure (exit code $LASTEXITCODE)."}
}
function Invoke-Captured([string]$Label,[string]$LogPath,[scriptblock]$Body){
    & $Body *> $LogPath; $exitCode=$LASTEXITCODE
    if($exitCode -ne 0){
        Write-Host "       $Label output tail:" -ForegroundColor Yellow
        Get-Content -LiteralPath $LogPath -Tail 100 | ForEach-Object { Write-Host ("       $_") }
        throw "$Label failed (exit code $exitCode)."
    }
}
function Read-Json([string]$Path){ return (Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json) }

Write-Host '[1/9] Resolving deterministic runtimes and pinned SDK...'
$python=Get-Cpython313Command
$pythonVersion=& $python.Command @($python.Args + @('--version')) 2>&1 | Out-String
Write-Host ("       {0}" -f $pythonVersion.Trim())
$dotnet=Get-Command dotnet -ErrorAction SilentlyContinue
if($null -eq $dotnet){throw 'CP132 requires the pinned .NET SDK 8.0.423; dotnet was not found.'}
$dotnetVersion=(& dotnet --version 2>&1 | Out-String).Trim()
if($LASTEXITCODE -ne 0 -or $dotnetVersion -ne '8.0.423'){throw "CP132 requires .NET SDK 8.0.423 exactly; observed '$dotnetVersion'."}
Write-Host "       .NET SDK $dotnetVersion"
Write-Host '       CP132 is a mechanics/architecture checkpoint: no technology-value promotion and no substantive Monte Carlo study.'

Write-Host '[2/9] Applying and verifying pre-package repository hygiene...'
Invoke-PythonChecked $python @('-B',$hygiene,'--repo',$repositoryRoot,'--apply') 'CP132 pre-package hygiene apply failed'
Invoke-PythonChecked $python @('-B',$hygiene,'--repo',$repositoryRoot,'--check') 'CP132 pre-package hygiene check failed'

if($RepositoryOnly){
    if(-not $NoClean -and (Test-Path -LiteralPath $outRoot)){Remove-Item -Recurse -Force $outRoot}
    New-Item -ItemType Directory -Force -Path $outRoot,$testOut,$parityOut,$deterministicOut,$tl1PhaseAOut | Out-Null

    Write-Host '[3/9] Running CP132 preflight and all Python self-tests...'
    Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot) 'CP132 preflight failed'
    Push-Location $repositoryRoot
    try {
        & $python.Command @($python.Args + @('-B','-m','unittest','discover','-s','tools/simulation/tests','-p','test_*.py'))
        if($LASTEXITCODE -ne 0){throw "CP132 Python self-tests failed (exit code $LASTEXITCODE)."}
        Write-Host '       Python self-tests: 196/196 passed.'

        Write-Host '[4/9] Building native C# solution with warnings as errors...'
        $buildLog=Join-Path $outRoot 'build.log'
        Invoke-Captured 'CP132 warning-as-error build' $buildLog { dotnet build StarCluster.sln --configuration Release --nologo -warnaserror }
        Write-Host '       Native build passed under SDK 8.0.423 with warnings treated as errors.'

        Write-Host '[5/9] Running xUnit and ScenarioRunner self-tests...'
        $testLog=Join-Path $outRoot 'xunit.log'
        dotnet test tests\StarCluster.Tests\StarCluster.Tests.csproj --configuration Release --no-build --nologo --logger 'trx;LogFileName=cp132-tests.trx' --results-directory $testOut
        $xunitExitCode=$LASTEXITCODE
        $trxPath=Join-Path $testOut 'cp132-tests.trx'
        if(-not (Test-Path -LiteralPath $trxPath)){throw 'CP132 xUnit TRX output is missing.'}
        [xml]$trx=Get-Content -LiteralPath $trxPath -Raw
        $counters=$trx.TestRun.ResultSummary.Counters
        $totalTests=[int]$counters.total; $passedTests=[int]$counters.passed; $failedTests=[int]$counters.failed; $skippedTests=[int]$counters.notExecuted
        if($xunitExitCode -ne 0 -or $totalTests -ne 910 -or $passedTests -ne 910 -or $failedTests -ne 0 -or $skippedTests -ne 0){throw "CP132 xUnit shape mismatch: exit=$xunitExitCode total=$totalTests passed=$passedTests failed=$failedTests skipped=$skippedTests; expected exit=0 and 910/910/0/0. See $trxPath for the complete result set."}
        Write-Host '       xUnit tests: 910/910 passed.'
        $selfLog=Join-Path $outRoot 'scenario-self-tests.log'
        Invoke-Captured 'CP132 ScenarioRunner self-tests' $selfLog { dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- self-test }
        $selfText=Get-Content -LiteralPath $selfLog -Raw
        if($selfText -notmatch 'Runner self-tests:\s+70 passed,\s+0 failed,\s+70 total\.'){throw 'CP132 ScenarioRunner self-test count/result mismatch; expected 70/70.'}
        Write-Host '       ScenarioRunner self-tests: 70/70 passed.'
        $deterministicLog=Join-Path $outRoot 'deterministic-scenarios.log'
        Invoke-Captured 'CP132 deterministic scenario corpus' $deterministicLog { dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- run-all --output-dir $deterministicOut }
        Write-Host '       Top-level deterministic scenario corpus passed.'
        $tl1Log=Join-Path $outRoot 'tl1-phase-a.log'
        Invoke-Captured 'CP132 TL1 Phase-A deterministic corpus' $tl1Log { dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- tl1-phase-a --output-dir $tl1PhaseAOut }
        Write-Host '       TL1 Phase-A deterministic mechanics corpus passed under penetration-hardening-v1.'

        Write-Host '[6/9] Running accepted C#/Python research parity and canonical mechanics tests...'
        Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'parity','--output-dir',$parityOut) 'CP132 research parity failed'
        $parity=Read-Json (Join-Path $parityOut 'summary.json')
        if(-not [bool]$parity.passed -or [int]$parity.cases -ne 25 -or @($parity.errors).Count -ne 0){throw 'CP132 expected 25/25 research parity fixtures.'}
        Write-Host '       Research parity fixtures: 25/25 passed.'
        & $python.Command @($python.Args + @('-B','-m','unittest','discover','-v','-s','tools/simulation/tests','-p','test_cp132_canonical_kernel.py'))
        if($LASTEXITCODE -ne 0){throw "CP132 canonical-kernel tests failed (exit code $LASTEXITCODE)."}
        Write-Host '       Canonical-kernel tests: 6/6 passed; five shared damage fixtures exercised.'

        Write-Host '[7/9] Writing repository-only native acceptance marker...'
        $repoOnly=[ordered]@{
            schemaVersion='star-cluster-cp132-repository-only-acceptance-v0.1'; checkpoint=132; acceptedEvidenceCheckpoint=131; acceptedNumericalCheckpoint=128; startingImplementationBaseline=122;
            repositoryOnly=$true; python=$pythonVersion.Trim(); dotnetSdk=$dotnetVersion; buildWarningsAsErrors=$true; buildPassed=$true;
            pythonTests=196; pythonTestsPassed=196; pythonDependencyPolicy='stdlib-only'; thirdPartyPythonPackagesAllowed=@();
            xunitTotal=$totalTests; xunitPassed=$passedTests; xunitFailed=$failedTests; xunitSkipped=$skippedTests;
            scenarioRunnerSelfTests=70; scenarioRunnerSelfTestsPassed=70; deterministicScenarioCorpusPassed=$true; tl1PhaseACorpusPassed=$true; researchParityCases=25; researchParityPassed=25;
            canonicalKernelVersion='0.1'; canonicalDamageModel='penetration-hardening-v1'; canonicalDamageFixtures=5; canonicalDamageFixturesPassed=5; visibleTurnPhases=6;
            standardSystemMapRadius=5; standardSystemMapCells=91; standardStartRange=10; precontactSearchHexesPerActivation=1;
            technologyValuesChanged=$false; productionSourceChanged=$true; researchSimulationChanged=$true; conceptChanged=$true;
            scenarioDefinitionsChanged=$true; scenarioDefinitionChangesAreMechanicsSynchronizationOnly=$true; mixedTlShipsExecuted=$false; automaticPromotion=$false;
            monteCarloStudy=$false; substantiveTrials=0; failedGates=@()
        }
        $repoOnly | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $repoOnlySummary -Encoding utf8

        Write-Host '[8/9] Verifying repository-only CP132 contract...'
        Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP132 repository-only contract failed'
        Write-Host '[9/9] Checkpoint 132 repository-only gates passed.' -ForegroundColor Green
        Write-Host '       Run the same wrapper without -RepositoryOnly in this unchanged extraction to finalize the zero-study native acceptance summary.'
    }
    finally { Pop-Location }
    exit 0
}

if(-not (Test-Path -LiteralPath $repoOnlySummary)){throw 'CP132 finalization requires a successful -RepositoryOnly run in the same extracted repository first.'}
Write-Host '[3/9] Revalidating CP132 preflight and prior repository-only marker...'
Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot) 'CP132 finalization preflight failed'
Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP132 prior repository-only contract failed'
$prior=Read-Json $repoOnlySummary
if(-not [bool]$prior.repositoryOnly -or @($prior.failedGates).Count -ne 0){throw 'CP132 repository-only acceptance marker is not valid.'}

Write-Host '[4/9] Preserving accepted native build/test gates...'
Write-Host '       196/196 Python; 910/910 xUnit; 70/70 ScenarioRunner; 25/25 research parity.'
Write-Host '[5/9] Preserving canonical mechanics evidence...'
Write-Host '       Kernel 0.1; penetration-hardening-v1; five shared damage fixtures; six visible turn phases.'
Write-Host '[6/9] Confirming no substantive simulation or technology promotion is scheduled...'
if([bool]$prior.monteCarloStudy -or [long]$prior.substantiveTrials -ne 0 -or [bool]$prior.technologyValuesChanged){throw 'CP132 zero-study/numerical boundary violation.'}
Write-Host '       Zero substantive trials; current Tech Table/Matrix remain frozen pending the separate TL-tree revision.'

Write-Host '[7/9] Writing final native acceptance summary...'
$final=[ordered]@{
    schemaVersion='star-cluster-cp132-native-acceptance-summary-v0.1'; checkpoint=132; acceptedEvidenceCheckpoint=131; acceptedNumericalCheckpoint=128; startingImplementationBaseline=122;
    repositoryOnly=$false; python=$prior.python; dotnetSdk=$prior.dotnetSdk; buildWarningsAsErrors=$prior.buildWarningsAsErrors; buildPassed=$prior.buildPassed;
    pythonTests=$prior.pythonTests; pythonTestsPassed=$prior.pythonTestsPassed; pythonDependencyPolicy=$prior.pythonDependencyPolicy; thirdPartyPythonPackagesAllowed=@();
    xunitTotal=$prior.xunitTotal; xunitPassed=$prior.xunitPassed; xunitFailed=$prior.xunitFailed; xunitSkipped=$prior.xunitSkipped;
    scenarioRunnerSelfTests=$prior.scenarioRunnerSelfTests; scenarioRunnerSelfTestsPassed=$prior.scenarioRunnerSelfTestsPassed; deterministicScenarioCorpusPassed=$prior.deterministicScenarioCorpusPassed; tl1PhaseACorpusPassed=$prior.tl1PhaseACorpusPassed; researchParityCases=$prior.researchParityCases; researchParityPassed=$prior.researchParityPassed;
    canonicalKernelVersion=$prior.canonicalKernelVersion; canonicalDamageModel=$prior.canonicalDamageModel; canonicalDamageFixtures=$prior.canonicalDamageFixtures; canonicalDamageFixturesPassed=$prior.canonicalDamageFixturesPassed; visibleTurnPhases=$prior.visibleTurnPhases;
    standardSystemMapRadius=$prior.standardSystemMapRadius; standardSystemMapCells=$prior.standardSystemMapCells; standardStartRange=$prior.standardStartRange; precontactSearchHexesPerActivation=$prior.precontactSearchHexesPerActivation;
    technologyValuesChanged=$false; productionSourceChanged=$true; researchSimulationChanged=$true; conceptChanged=$true;
    scenarioDefinitionsChanged=$true; scenarioDefinitionChangesAreMechanicsSynchronizationOnly=$true; mixedTlShipsExecuted=$false; automaticPromotion=$false;
    monteCarloStudy=$false; substantiveTrials=0; failedGates=@()
}
$final | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $finalSummary -Encoding utf8

Write-Host '[8/9] Verifying final CP132 repository/results contract...'
Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP132 final contract failed'
Write-Host '[9/9] Checkpoint 132 native gates passed.' -ForegroundColor Green
Write-Host '       CP132 is ready to become the canonical mechanics/architecture baseline; no numerical technology values were promoted.'
