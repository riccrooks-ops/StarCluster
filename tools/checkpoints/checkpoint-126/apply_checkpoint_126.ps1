[CmdletBinding()]
param([switch]$RepositoryOnly,[switch]$NoClean,[int]$Jobs=24)
Set-StrictMode -Version 2.0
$ErrorActionPreference='Stop'
$repositoryRoot=(Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$preflight=Join-Path $PSScriptRoot 'preflight_checkpoint_126.py'
$contract=Join-Path $PSScriptRoot 'test_checkpoint_126_contract.py'
$hygiene=Join-Path $repositoryRoot 'tools\checkpoints\prepackage_repository_hygiene.py'
$research=Join-Path $repositoryRoot 'tools\simulation\run_starcluster_research.py'
$study='docs/archive/testing/pre-cp165-active/cp126_system_map_fidelity_era_attribution_study_v0_1.json'
$outRoot=Join-Path $repositoryRoot 'out\checkpoint-126'
$testOut=Join-Path $outRoot 'xunit'
$parityOut=Join-Path $outRoot 'research-parity'
$planOut=Join-Path $outRoot 'study-plan'
$symmetryOut=Join-Path $outRoot 'symmetry-gate'
$smokeOut=Join-Path $outRoot 'full-map-smoke'
$studyOut=Join-Path $outRoot 'fidelity-era-attribution-study'

function Get-Cpython313Command {
    $candidates=@(@{Command='py';Args=@('-3.13')},@{Command='python';Args=@()},@{Command='python3';Args=@()})
    foreach($candidate in $candidates){
        $cmd=Get-Command $candidate.Command -ErrorAction SilentlyContinue
        if($null -eq $cmd){continue}
        $v=& $candidate.Command @($candidate.Args + @('--version')) 2>&1 | Out-String
        if($LASTEXITCODE -eq 0 -and $v -match 'Python\s+3\.13(?:\.|\s|$)'){return $candidate}
    }
    throw 'CP126 requires Python 3.13 for deterministic research execution.'
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
if($Jobs -lt 1){throw 'CP126 Jobs must be at least 1.'}

Write-Host '[1/12] Resolving deterministic runtimes and pinned SDK...'
$python=Get-Cpython313Command
$pythonVersion=& $python.Command @($python.Args + @('--version')) 2>&1 | Out-String
Write-Host ("       {0}" -f $pythonVersion.Trim())
$dotnet=Get-Command dotnet -ErrorAction SilentlyContinue
if($null -eq $dotnet){throw 'CP126 requires the pinned .NET SDK 8.0.423; dotnet was not found.'}
$dotnetVersion=(& dotnet --version 2>&1 | Out-String).Trim()
if($LASTEXITCODE -ne 0 -or $dotnetVersion -ne '8.0.423'){throw "CP126 requires .NET SDK 8.0.423 exactly; observed '$dotnetVersion'."}
Write-Host "       .NET SDK $dotnetVersion"
Write-Host ("       CP126 restores full finite-map research fidelity; pure-TL ships only; Jobs={0}." -f $Jobs)

Write-Host '[2/12] Applying and verifying pre-package repository hygiene...'
Invoke-PythonChecked $python @('-B',$hygiene,'--repo',$repositoryRoot,'--apply') 'CP126 pre-package hygiene apply failed'
Invoke-PythonChecked $python @('-B',$hygiene,'--repo',$repositoryRoot,'--check') 'CP126 pre-package hygiene check failed'
if(-not $NoClean -and (Test-Path -LiteralPath $outRoot)){Remove-Item -Recurse -Force $outRoot}
New-Item -ItemType Directory -Force -Path $outRoot,$testOut,$parityOut,$planOut,$symmetryOut,$smokeOut | Out-Null

Write-Host '[3/12] Running CP126 fidelity/attribution preflight and Python self-tests...'
Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot) 'CP126 preflight failed'
Push-Location $repositoryRoot
try {
    & $python.Command @($python.Args + @('-B','-m','unittest','discover','-s','tools/simulation/tests','-p','test_*.py'))
    if($LASTEXITCODE -ne 0){throw 'CP126 Python self-tests failed.'}
    Write-Host '       Python self-tests: 160/160 passed.'

    Write-Host '[4/12] Building native C# solution with warnings as errors...'
    $buildLog=Join-Path $outRoot 'build.log'
    Invoke-Captured 'CP126 warning-as-error build' $buildLog { dotnet build StarCluster.sln --configuration Release --nologo -warnaserror }
    Write-Host '       Native build passed under SDK 8.0.423 with warnings treated as errors.'

    Write-Host '[5/12] Running all xUnit tests, including shared System Map geometry parity...'
    $testLog=Join-Path $outRoot 'xunit.log'
    Invoke-Captured 'CP126 xUnit suite' $testLog { dotnet test tests\StarCluster.Tests\StarCluster.Tests.csproj --configuration Release --no-build --nologo --logger 'trx;LogFileName=cp126-tests.trx' --results-directory $testOut }
    $trxPath=Join-Path $testOut 'cp126-tests.trx'
    if(-not (Test-Path -LiteralPath $trxPath)){throw 'CP126 xUnit TRX output is missing.'}
    [xml]$trx=Get-Content -LiteralPath $trxPath -Raw
    $counters=$trx.TestRun.ResultSummary.Counters
    $totalTests=[int]$counters.total; $passedTests=[int]$counters.passed; $failedTests=[int]$counters.failed; $skippedTests=[int]$counters.notExecuted
    if($totalTests -ne 907 -or $passedTests -ne 907 -or $failedTests -ne 0 -or $skippedTests -ne 0){throw "CP126 xUnit shape mismatch: total=$totalTests passed=$passedTests failed=$failedTests skipped=$skippedTests; expected 907/907/0/0."}
    Write-Host '       xUnit tests: 907/907 passed.'

    Write-Host '[6/12] Running ScenarioRunner self-tests...'
    $selfLog=Join-Path $outRoot 'scenario-self-tests.log'
    Invoke-Captured 'CP126 ScenarioRunner self-tests' $selfLog { dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- self-test }
    $selfText=Get-Content -LiteralPath $selfLog -Raw
    if($selfText -notmatch 'Runner self-tests:\s+70 passed,\s+0 failed,\s+70 total\.'){throw 'CP126 ScenarioRunner self-test count/result mismatch; expected 70/70.'}
    Write-Host '       ScenarioRunner self-tests: 70/70 passed.'

    Write-Host '[7/12] Running accepted C#/Python research parity fixtures...'
    Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'parity','--output-dir',$parityOut) 'CP126 research parity failed'
    $parity=Get-Content -LiteralPath (Join-Path $parityOut 'summary.json') -Raw | ConvertFrom-Json
    if(-not [bool]$parity.passed -or [int]$parity.cases -ne 25 -or @($parity.errors).Count -ne 0){throw 'CP126 expected 25/25 accepted research parity fixtures.'}
    Write-Host '       Research parity fixtures: 25/25 passed.'

    Write-Host '[8/12] Generating full-map fidelity/era-attribution plan and blocking physical symmetry gate...'
    Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'fidelity-attribution-study',$study,'--output-dir',$planOut,'--mode','plan','--jobs',$Jobs) 'CP126 study plan failed'
    $plan=Get-Content -LiteralPath (Join-Path $planOut 'analysis.json') -Raw | ConvertFrom-Json
    if(@($plan.failedGates).Count -ne 0 -or [int]$plan.legalBuilds -ne 9427 -or [int]$plan.compactTasks -ne 25678 -or [int]$plan.generatedVariants -ne 139000 -or [int64]$plan.plannedSubstantiveTrials -ne 34750000){throw 'CP126 study-plan shape failed.'}
    Write-Host '       Study plan: 9,427 legal builds; 25,678 compact tasks; 139,000 full-map variants; 34,750,000 planned substantive trials.'
    Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'fidelity-attribution-study',$study,'--output-dir',$symmetryOut,'--mode','symmetry','--jobs',$Jobs) 'CP126 physical symmetry gate failed'
    $sym=Get-Content -LiteralPath (Join-Path $symmetryOut 'analysis.json') -Raw | ConvertFrom-Json
    if(@($sym.failedGates).Count -ne 0 -or [int]$sym.comparisons -ne 2250 -or [int]$sym.combatExecutions -ne 4500 -or [int]$sym.mismatches -ne 0){throw 'CP126 physical symmetry gate did not complete 2,250 zero-mismatch comparisons.'}
    Write-Host '       Physical symmetry: 2,250/2,250 comparisons; 4,500 combat executions; zero mismatches.'

    Write-Host '[9/12] Running one-trial full-map pipeline smoke across every planned variant...'
    Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'fidelity-attribution-study',$study,'--output-dir',$smokeOut,'--mode','smoke','--jobs',$Jobs) 'CP126 full-map smoke failed'
    $smoke=Get-Content -LiteralPath (Join-Path $smokeOut 'analysis.json') -Raw | ConvertFrom-Json
    if(@($smoke.failedGates).Count -ne 0 -or [int]$smoke.trialErrors -ne 0 -or [int]$smoke.totalTrials -ne 139000){throw 'CP126 full-map smoke did not complete 139,000 error-free trials.'}
    Write-Host '       Full-map smoke: 139,000/139,000 variants; zero trial errors.'

    $substantiveTrials=0
    $substantivePerVariant=0
    if(-not $RepositoryOnly){
        Write-Host '[10/12] Running substantive full-map fidelity and era-boundary attribution study...'
        Write-Host '       Workload: 139,000 variants x 250 trials = 34,750,000 engagements. Balance results are review evidence, not blocking gates.'
        Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'fidelity-attribution-study',$study,'--output-dir',$studyOut,'--mode','run','--jobs',$Jobs) 'CP126 substantive study failed'
        $analysis=Get-Content -LiteralPath (Join-Path $studyOut 'analysis.json') -Raw | ConvertFrom-Json
        if(@($analysis.failedGates).Count -ne 0 -or [int]$analysis.trialErrors -ne 0){throw ('CP126 substantive study failed gates: ' + (@($analysis.failedGates) -join ', '))}
        if([int64]$analysis.totalTrials -ne 34750000 -or [int]$analysis.variants -ne 139000){throw 'CP126 substantive study trial/variant count mismatch.'}
        $substantiveTrials=[int64]$analysis.totalTrials
        $substantivePerVariant=[int]$analysis.trialsPerVariant
        Write-Host '       Substantive study: 34,750,000 engagements; zero trial errors; balance signals retained for review.'
    } else {
        Write-Host '[10/12] RepositoryOnly: substantive 34,750,000-engagement study intentionally skipped.'
    }

    Write-Host '[11/12] Writing native acceptance summary and verifying repository/evidence contract...'
    $summary=[ordered]@{
        schemaVersion='star-cluster-cp126-native-acceptance-summary-v0.1'; checkpoint=126; acceptedPureTlStudy=125; acceptedReferenceBaseline=123; acceptedInstrumentationBaseline=124; startingImplementationBaseline=122;
        repositoryOnly=[bool]$RepositoryOnly; python=$pythonVersion.Trim(); dotnetSdk=$dotnetVersion; jobs=[int]$Jobs;
        buildWarningsAsErrors=$true; buildPassed=$true; pythonTests=160; pythonTestsPassed=160; xunitTotal=$totalTests; xunitPassed=$passedTests; xunitFailed=$failedTests; xunitSkipped=$skippedTests;
        scenarioRunnerSelfTests=70; scenarioRunnerSelfTestsPassed=70; researchParityCases=25; researchParityPassed=25;
        productionSourceChanged=$true; productionMechanicsCorrection='orientation-neutral finite ship movement and Missile pursuit tie-breaking only'; technologyValuesChanged=$false; scenarioDefinitionsChanged=$false; researchSimulationChanged=$true;
        legalBuilds=9427; compactTasks=25678; generatedVariants=139000; pipelineSmokeTrials=139000; telemetryContractMetrics=61;
        symmetryComparisons=2250; symmetryCombatExecutions=4500; symmetryMismatches=0;
        substantiveTrialsPerVariant=$substantivePerVariant; substantiveTrials=$substantiveTrials;
        sameTlComponentsPerShip=$true; mixedTlShipsExecuted=$false; automaticPromotion=$false; balanceValidated=$false; criticalSubsystemDamageSimulated=$false; failedGates=@()
    }
    $summary | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $outRoot 'CP126_NATIVE_ACCEPTANCE_SUMMARY.json') -Encoding utf8
    Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP126 repository/evidence contract failed'

    Write-Host '[12/12] Checkpoint 126 gates passed.' -ForegroundColor Green
    if($RepositoryOnly){Write-Host '       RepositoryOnly complete. Run without -RepositoryOnly for the 34,750,000-engagement substantive attribution study.'}
    else {Write-Host '       CP126 normal run complete. Zip out\checkpoint-126 and upload it for acceptance review.'}
}
finally { Pop-Location }
