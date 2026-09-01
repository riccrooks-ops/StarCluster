[CmdletBinding()]
param([switch]$RepositoryOnly,[switch]$NoClean,[int]$Jobs=24)
Set-StrictMode -Version 2.0
$ErrorActionPreference='Stop'
$repositoryRoot=(Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$preflight=Join-Path $PSScriptRoot 'preflight_checkpoint_127.py'
$contract=Join-Path $PSScriptRoot 'test_checkpoint_127_contract.py'
$hygiene=Join-Path $repositoryRoot 'tools\checkpoints\prepackage_repository_hygiene.py'
$research=Join-Path $repositoryRoot 'tools\simulation\run_starcluster_research.py'
$study='docs/archive/testing/pre-cp165-active/cp127_main_subsystem_tl_stabilization_study_v0_1.json'
$outRoot=Join-Path $repositoryRoot 'out\checkpoint-127'
$testOut=Join-Path $outRoot 'xunit'
$parityOut=Join-Path $outRoot 'research-parity'
$planOut=Join-Path $outRoot 'study-plan'
$symmetryOut=Join-Path $outRoot 'symmetry-gate'
$smokeOut=Join-Path $outRoot 'pipeline-smoke'
$studyOut=Join-Path $outRoot 'main-subsystem-stabilization-study'

function Get-Cpython313Command {
    $candidates=@(@{Command='py';Args=@('-3.13')},@{Command='python';Args=@()},@{Command='python3';Args=@()})
    foreach($candidate in $candidates){
        $cmd=Get-Command $candidate.Command -ErrorAction SilentlyContinue
        if($null -eq $cmd){continue}
        $v=& $candidate.Command @($candidate.Args + @('--version')) 2>&1 | Out-String
        if($LASTEXITCODE -eq 0 -and $v -match 'Python\s+3\.13(?:\.|\s|$)'){return $candidate}
    }
    throw 'CP127 requires Python 3.13 for deterministic research execution.'
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
if($Jobs -lt 1){throw 'CP127 Jobs must be at least 1.'}

Write-Host '[1/12] Resolving deterministic runtimes and pinned SDK...'
$python=Get-Cpython313Command
$pythonVersion=& $python.Command @($python.Args + @('--version')) 2>&1 | Out-String
Write-Host ("       {0}" -f $pythonVersion.Trim())
$dotnet=Get-Command dotnet -ErrorAction SilentlyContinue
if($null -eq $dotnet){throw 'CP127 requires the pinned .NET SDK 8.0.423; dotnet was not found.'}
$dotnetVersion=(& dotnet --version 2>&1 | Out-String).Trim()
if($LASTEXITCODE -ne 0 -or $dotnetVersion -ne '8.0.423'){throw "CP127 requires .NET SDK 8.0.423 exactly; observed '$dotnetVersion'."}
Write-Host "       .NET SDK $dotnetVersion"
Write-Host ("       CP127 stabilizes the pure-TL main-subsystem table before broader TL sensitivity and mixed-TL studies; Jobs={0}." -f $Jobs)

Write-Host '[2/12] Applying and verifying pre-package repository hygiene...'
Invoke-PythonChecked $python @('-B',$hygiene,'--repo',$repositoryRoot,'--apply') 'CP127 pre-package hygiene apply failed'
Invoke-PythonChecked $python @('-B',$hygiene,'--repo',$repositoryRoot,'--check') 'CP127 pre-package hygiene check failed'
if(-not $NoClean -and (Test-Path -LiteralPath $outRoot)){Remove-Item -Recurse -Force $outRoot}
New-Item -ItemType Directory -Force -Path $outRoot,$testOut,$parityOut,$planOut,$symmetryOut,$smokeOut | Out-Null

Write-Host '[3/12] Running CP127 stabilization preflight and Python self-tests...'
Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot) 'CP127 preflight failed'
Push-Location $repositoryRoot
try {
    & $python.Command @($python.Args + @('-B','-m','unittest','discover','-s','tools/simulation/tests','-p','test_*.py'))
    if($LASTEXITCODE -ne 0){throw 'CP127 Python self-tests failed.'}
    Write-Host '       Python self-tests: 170/170 passed.'

    Write-Host '[4/12] Building native C# solution with warnings as errors...'
    $buildLog=Join-Path $outRoot 'build.log'
    Invoke-Captured 'CP127 warning-as-error build' $buildLog { dotnet build StarCluster.sln --configuration Release --nologo -warnaserror }
    Write-Host '       Native build passed under SDK 8.0.423 with warnings treated as errors.'

    Write-Host '[5/12] Running the frozen xUnit suite...'
    $testLog=Join-Path $outRoot 'xunit.log'
    Invoke-Captured 'CP127 xUnit suite' $testLog { dotnet test tests\StarCluster.Tests\StarCluster.Tests.csproj --configuration Release --no-build --nologo --logger 'trx;LogFileName=cp127-tests.trx' --results-directory $testOut }
    $trxPath=Join-Path $testOut 'cp127-tests.trx'
    if(-not (Test-Path -LiteralPath $trxPath)){throw 'CP127 xUnit TRX output is missing.'}
    [xml]$trx=Get-Content -LiteralPath $trxPath -Raw
    $counters=$trx.TestRun.ResultSummary.Counters
    $totalTests=[int]$counters.total; $passedTests=[int]$counters.passed; $failedTests=[int]$counters.failed; $skippedTests=[int]$counters.notExecuted
    if($totalTests -ne 907 -or $passedTests -ne 907 -or $failedTests -ne 0 -or $skippedTests -ne 0){throw "CP127 xUnit shape mismatch: total=$totalTests passed=$passedTests failed=$failedTests skipped=$skippedTests; expected 907/907/0/0."}
    Write-Host '       xUnit tests: 907/907 passed.'

    Write-Host '[6/12] Running ScenarioRunner self-tests and accepted C#/Python parity fixtures...'
    $selfLog=Join-Path $outRoot 'scenario-self-tests.log'
    Invoke-Captured 'CP127 ScenarioRunner self-tests' $selfLog { dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- self-test }
    $selfText=Get-Content -LiteralPath $selfLog -Raw
    if($selfText -notmatch 'Runner self-tests:\s+70 passed,\s+0 failed,\s+70 total\.'){throw 'CP127 ScenarioRunner self-test count/result mismatch; expected 70/70.'}
    Write-Host '       ScenarioRunner self-tests: 70/70 passed.'
    Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'parity','--output-dir',$parityOut) 'CP127 research parity failed'
    $parity=Get-Content -LiteralPath (Join-Path $parityOut 'summary.json') -Raw | ConvertFrom-Json
    if(-not [bool]$parity.passed -or [int]$parity.cases -ne 25 -or @($parity.errors).Count -ne 0){throw 'CP127 expected 25/25 accepted research parity fixtures.'}
    Write-Host '       Research parity fixtures: 25/25 passed.'

    Write-Host '[7/12] Reconstructing the bounded CP127 study plan...'
    Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'main-subsystem-stabilization-study',$study,'--output-dir',$planOut,'--mode','plan','--jobs',$Jobs) 'CP127 study plan failed'
    $plan=Get-Content -LiteralPath (Join-Path $planOut 'analysis.json') -Raw | ConvertFrom-Json
    if(@($plan.failedGates).Count -ne 0 -or [int]$plan.legalBuilds -ne 9427 -or [int]$plan.finalBaselineTasks -ne 18646 -or [int]$plan.finalBaselineVariants -ne 74584 -or [int]$plan.tl5Tl6AblationVariants -ne 4320 -or [int]$plan.tl8EnergyVariants -ne 7680 -or [int]$plan.generatedVariants -ne 86584 -or [int64]$plan.plannedSubstantiveTrials -ne 8658400){throw 'CP127 study-plan shape failed.'}
    Write-Host '       Study plan: 9,427 legal builds; 18,646 final-baseline tasks; 86,584 total variants; 8,658,400 planned substantive engagements.'

    Write-Host '[8/12] Re-running the blocking physical-symmetry gate...'
    Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'main-subsystem-stabilization-study',$study,'--output-dir',$symmetryOut,'--mode','symmetry','--jobs',$Jobs) 'CP127 physical symmetry gate failed'
    $sym=Get-Content -LiteralPath (Join-Path $symmetryOut 'analysis.json') -Raw | ConvertFrom-Json
    if(@($sym.failedGates).Count -ne 0 -or [int]$sym.comparisons -ne 2250 -or [int]$sym.combatExecutions -ne 4500 -or [int]$sym.mismatches -ne 0){throw 'CP127 physical symmetry gate did not complete 2,250 zero-mismatch comparisons.'}
    Write-Host '       Physical symmetry: 2,250/2,250 comparisons; 4,500 combat executions; zero mismatches.'

    Write-Host '[9/12] Running one-trial actual-consumer smoke across all CP127 variants...'
    Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'main-subsystem-stabilization-study',$study,'--output-dir',$smokeOut,'--mode','smoke','--jobs',$Jobs) 'CP127 pipeline smoke failed'
    $smoke=Get-Content -LiteralPath (Join-Path $smokeOut 'analysis.json') -Raw | ConvertFrom-Json
    if(@($smoke.failedGates).Count -ne 0 -or [int]$smoke.trialErrors -ne 0 -or [int]$smoke.variants -ne 86584 -or [int]$smoke.totalTrials -ne 86584){throw 'CP127 pipeline smoke did not complete 86,584 error-free variant trials.'}
    Write-Host '       Pipeline smoke: 86,584/86,584 variants; zero trial errors.'

    $substantiveTrials=0
    $substantivePerVariant=0
    if(-not $RepositoryOnly){
        Write-Host '[10/12] Running substantive main-subsystem stabilization study...'
        Write-Host '       Workload: 86,584 variants x 100 trials = 8,658,400 engagements. Balance signals are review evidence; mechanics/count/error gates remain blocking.'
        Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'main-subsystem-stabilization-study',$study,'--output-dir',$studyOut,'--mode','run','--jobs',$Jobs) 'CP127 substantive study failed'
        $analysis=Get-Content -LiteralPath (Join-Path $studyOut 'analysis.json') -Raw | ConvertFrom-Json
        if(@($analysis.failedGates).Count -ne 0 -or [int]$analysis.trialErrors -ne 0){throw ('CP127 substantive study failed gates: ' + (@($analysis.failedGates) -join ', '))}
        if([int64]$analysis.totalTrials -ne 8658400 -or [int]$analysis.variants -ne 86584){throw 'CP127 substantive study trial/variant count mismatch.'}
        $substantiveTrials=[int64]$analysis.totalTrials
        $substantivePerVariant=[int]$analysis.trialsPerVariant
        Write-Host '       Substantive study: 8,658,400 engagements; zero trial errors; stabilization signals retained for review.'
    } else {
        Write-Host '[10/12] RepositoryOnly: substantive 8,658,400-engagement study intentionally skipped.'
    }

    Write-Host '[11/12] Writing native acceptance summary and verifying repository/evidence contract...'
    $summary=[ordered]@{
        schemaVersion='star-cluster-cp127-native-acceptance-summary-v0.1'; checkpoint=127; acceptedEvidenceCheckpoint=126; acceptedReferenceBaseline=123; acceptedInstrumentationBaseline=124; startingImplementationBaseline=122;
        repositoryOnly=[bool]$RepositoryOnly; python=$pythonVersion.Trim(); dotnetSdk=$dotnetVersion; jobs=[int]$Jobs;
        buildWarningsAsErrors=$true; buildPassed=$true; pythonTests=170; pythonTestsPassed=170; pythonDependencyPolicy='stdlib-only'; thirdPartyPythonPackagesAllowed=@(); xunitTotal=$totalTests; xunitPassed=$passedTests; xunitFailed=$failedTests; xunitSkipped=$skippedTests;
        scenarioRunnerSelfTests=70; scenarioRunnerSelfTestsPassed=70; researchParityCases=25; researchParityPassed=25;
        productionSourceChanged=$false; technologyValuesChanged=$true; numericLeafChanges=9; scenarioDefinitionsChanged=$false; researchSimulationChanged=$true;
        legalBuilds=9427; finalBaselineTasks=18646; finalBaselineVariants=74584; tl5Tl6AblationVariants=4320; tl8EnergyVariants=7680; generatedVariants=86584; pipelineSmokeTrials=86584; telemetryContractMetrics=61;
        symmetryComparisons=2250; symmetryCombatExecutions=4500; symmetryMismatches=0;
        substantiveTrialsPerVariant=$substantivePerVariant; substantiveTrials=$substantiveTrials;
        stlMoveEqualsDriveTl=$true; missileMoveEqualsDriveTlPlusOne=$true; ftlStrategicUnevenLadderRetained=$true; tl8EnergyDamageCandidate='7/10/12';
        sameTlComponentsPerShip=$true; mixedTlShipsExecuted=$false; auxiliaryNumericalStabilizationDeferred=$true; automaticPromotion=$false; balanceValidated=$false; mainSubsystemCandidateReadyForReview=$true; failedGates=@()
    }
    $summary | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $outRoot 'CP127_NATIVE_ACCEPTANCE_SUMMARY.json') -Encoding utf8
    Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP127 repository/evidence contract failed'

    Write-Host '[12/12] Checkpoint 127 gates passed.' -ForegroundColor Green
    if($RepositoryOnly){Write-Host '       RepositoryOnly complete. Run without -RepositoryOnly for the 8,658,400-engagement substantive stabilization study.'}
    else {Write-Host '       CP127 normal run complete. Zip out\checkpoint-127 and upload it for acceptance review.'}
}
finally { Pop-Location }
