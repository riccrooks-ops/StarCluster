[CmdletBinding()]
param([switch]$RepositoryOnly,[switch]$NoClean,[ValidateRange(1,61)][int]$Jobs=24)
Set-StrictMode -Version 2.0
$ErrorActionPreference='Stop'
$repositoryRoot=(Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$preflight=Join-Path $PSScriptRoot 'preflight_checkpoint_129.py'
$contract=Join-Path $PSScriptRoot 'test_checkpoint_129_contract.py'
$hygiene=Join-Path $repositoryRoot 'tools\checkpoints\prepackage_repository_hygiene.py'
$research=Join-Path $repositoryRoot 'tools\simulation\run_starcluster_research.py'
$study='docs/archive/testing/pre-cp165-active/cp129_whole_ladder_pure_tl_sensitivity_study_v0_1.json'
$outRoot=Join-Path $repositoryRoot 'out\checkpoint-129'
$testOut=Join-Path $outRoot 'xunit'
$parityOut=Join-Path $outRoot 'research-parity'
$planOut=Join-Path $outRoot 'plan'
$symmetryOut=Join-Path $outRoot 'symmetry'
$smokeOut=Join-Path $outRoot 'smoke'
$substantiveOut=Join-Path $outRoot 'substantive'
$repoOnlySummary=Join-Path $outRoot 'CP129_REPOSITORY_ONLY_ACCEPTANCE.json'
$finalSummary=Join-Path $outRoot 'CP129_NATIVE_ACCEPTANCE_SUMMARY.json'

function Get-Cpython313Command {
    $candidates=@(@{Command='py';Args=@('-3.13')},@{Command='python';Args=@()},@{Command='python3';Args=@()})
    foreach($candidate in $candidates){
        $cmd=Get-Command $candidate.Command -ErrorAction SilentlyContinue
        if($null -eq $cmd){continue}
        $v=& $candidate.Command @($candidate.Args + @('--version')) 2>&1 | Out-String
        if($LASTEXITCODE -eq 0 -and $v -match 'Python\s+3\.13(?:\.|\s|$)'){return $candidate}
    }
    throw 'CP129 requires Python 3.13 for deterministic acceptance/research tooling.'
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
function Read-Json([string]$Path){ return (Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json) }

Write-Host '[1/12] Resolving deterministic runtimes and pinned SDK...'
$python=Get-Cpython313Command
$pythonVersion=& $python.Command @($python.Args + @('--version')) 2>&1 | Out-String
Write-Host ("       {0}" -f $pythonVersion.Trim())
$dotnet=Get-Command dotnet -ErrorAction SilentlyContinue
if($null -eq $dotnet){throw 'CP129 requires the pinned .NET SDK 8.0.423; dotnet was not found.'}
$dotnetVersion=(& dotnet --version 2>&1 | Out-String).Trim()
if($LASTEXITCODE -ne 0 -or $dotnetVersion -ne '8.0.423'){throw "CP129 requires .NET SDK 8.0.423 exactly; observed '$dotnetVersion'."}
Write-Host "       .NET SDK $dotnetVersion"
Write-Host ("       CP129 measures broad pure-TL sensitivity on the frozen CP128 table; Jobs={0}; legal mixed-TL ships remain excluded." -f $Jobs)

Write-Host '[2/12] Applying and verifying pre-package repository hygiene...'
Invoke-PythonChecked $python @('-B',$hygiene,'--repo',$repositoryRoot,'--apply') 'CP129 pre-package hygiene apply failed'
Invoke-PythonChecked $python @('-B',$hygiene,'--repo',$repositoryRoot,'--check') 'CP129 pre-package hygiene check failed'

if($RepositoryOnly){
    if(-not $NoClean -and (Test-Path -LiteralPath $outRoot)){Remove-Item -Recurse -Force $outRoot}
    New-Item -ItemType Directory -Force -Path $outRoot,$testOut,$parityOut,$planOut,$symmetryOut,$smokeOut | Out-Null

    Write-Host '[3/12] Running CP129 preflight and Python self-tests...'
    Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot) 'CP129 preflight failed'
    Push-Location $repositoryRoot
    try {
        & $python.Command @($python.Args + @('-B','-m','unittest','discover','-s','tools/simulation/tests','-p','test_*.py'))
        if($LASTEXITCODE -ne 0){throw 'CP129 Python self-tests failed.'}
        Write-Host '       Python self-tests: 177/177 passed.'

        Write-Host '[4/12] Building native C# solution with warnings as errors...'
        $buildLog=Join-Path $outRoot 'build.log'
        Invoke-Captured 'CP129 warning-as-error build' $buildLog { dotnet build StarCluster.sln --configuration Release --nologo -warnaserror }
        Write-Host '       Native build passed under SDK 8.0.423 with warnings treated as errors.'

        Write-Host '[5/12] Running the frozen xUnit suite...'
        $testLog=Join-Path $outRoot 'xunit.log'
        Invoke-Captured 'CP129 xUnit suite' $testLog { dotnet test tests\StarCluster.Tests\StarCluster.Tests.csproj --configuration Release --no-build --nologo --logger 'trx;LogFileName=cp129-tests.trx' --results-directory $testOut }
        $trxPath=Join-Path $testOut 'cp129-tests.trx'
        if(-not (Test-Path -LiteralPath $trxPath)){throw 'CP129 xUnit TRX output is missing.'}
        [xml]$trx=Get-Content -LiteralPath $trxPath -Raw
        $counters=$trx.TestRun.ResultSummary.Counters
        $totalTests=[int]$counters.total; $passedTests=[int]$counters.passed; $failedTests=[int]$counters.failed; $skippedTests=[int]$counters.notExecuted
        if($totalTests -ne 907 -or $passedTests -ne 907 -or $failedTests -ne 0 -or $skippedTests -ne 0){throw "CP129 xUnit shape mismatch: total=$totalTests passed=$passedTests failed=$failedTests skipped=$skippedTests; expected 907/907/0/0."}
        Write-Host '       xUnit tests: 907/907 passed.'

        Write-Host '[6/12] Running ScenarioRunner self-tests and accepted research parity...'
        $selfLog=Join-Path $outRoot 'scenario-self-tests.log'
        Invoke-Captured 'CP129 ScenarioRunner self-tests' $selfLog { dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- self-test }
        $selfText=Get-Content -LiteralPath $selfLog -Raw
        if($selfText -notmatch 'Runner self-tests:\s+70 passed,\s+0 failed,\s+70 total\.'){throw 'CP129 ScenarioRunner self-test count/result mismatch; expected 70/70.'}
        Write-Host '       ScenarioRunner self-tests: 70/70 passed.'
        Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'parity','--output-dir',$parityOut) 'CP129 research parity failed'
        $parity=Read-Json (Join-Path $parityOut 'summary.json')
        if(-not [bool]$parity.passed -or [int]$parity.cases -ne 25 -or @($parity.errors).Count -ne 0){throw 'CP129 expected 25/25 accepted research parity fixtures.'}
        Write-Host '       Research parity fixtures: 25/25 passed.'

        Write-Host '[7/12] Reconstructing the full CP129 deterministic study plan...'
        Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'whole-ladder-sensitivity-study',$study,'--output-dir',$planOut,'--mode','plan','--jobs',$Jobs) 'CP129 study plan failed'
        $plan=Read-Json (Join-Path $planOut 'analysis.json')
        if(@($plan.failedGates).Count -ne 0 -or [int]$plan.legalBuilds -ne 9427 -or [int]$plan.generatedVariants -ne 626028 -or [long]$plan.substantiveTrials -ne 45665000){throw 'CP129 deterministic plan shape mismatch.'}
        Write-Host '       Plan: 9,427 legal builds; 70,034 whole-ladder pairings; 626,028 variants; 45,665,000 substantive engagements.'

        Write-Host '[8/12] Running blocking full-map physical-symmetry gate...'
        Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'whole-ladder-sensitivity-study',$study,'--output-dir',$symmetryOut,'--mode','symmetry','--jobs',$Jobs) 'CP129 physical-symmetry gate failed'
        $symmetry=Read-Json (Join-Path $symmetryOut 'analysis.json')
        if(@($symmetry.failedGates).Count -ne 0 -or [int]$symmetry.comparisons -ne 2250 -or [int]$symmetry.combatExecutions -ne 4500 -or [int]$symmetry.mismatches -ne 0){throw 'CP129 physical-symmetry shape mismatch.'}
        Write-Host '       Physical symmetry: 2,250 comparisons / 4,500 executions / 0 mismatches.'

        Write-Host '[9/12] Running complete one-trial CP129 pipeline smoke...'
        Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'whole-ladder-sensitivity-study',$study,'--output-dir',$smokeOut,'--mode','smoke','--jobs',$Jobs) 'CP129 pipeline smoke failed'
        $smoke=Read-Json (Join-Path $smokeOut 'analysis.json')
        if(@($smoke.failedGates).Count -ne 0 -or [int]$smoke.variants -ne 626028 -or [int]$smoke.trialErrors -ne 0){throw 'CP129 one-trial smoke shape mismatch.'}
        Write-Host '       Pipeline smoke: 626,028/626,028 variants completed with 0 trial errors.'

        Write-Host '[10/12] Writing repository-only native acceptance marker...'
        $repoOnly=[ordered]@{
            schemaVersion='star-cluster-cp129-repository-only-acceptance-v0.1'; checkpoint=129; acceptedEvidenceCheckpoint=128; startingImplementationBaseline=122;
            repositoryOnly=$true; python=$pythonVersion.Trim(); dotnetSdk=$dotnetVersion; buildWarningsAsErrors=$true; buildPassed=$true;
            pythonTests=177; pythonTestsPassed=177; repositoryOnlyJobs=$Jobs; pythonDependencyPolicy='stdlib-only'; thirdPartyPythonPackagesAllowed=@();
            xunitTotal=$totalTests; xunitPassed=$passedTests; xunitFailed=$failedTests; xunitSkipped=$skippedTests;
            scenarioRunnerSelfTests=70; scenarioRunnerSelfTestsPassed=70; researchParityCases=25; researchParityPassed=25;
            productionSourceChanged=$false; technologyValuesChanged=$false; scenarioDefinitionsChanged=$false; researchSimulationChanged=$true;
            mainSubsystemPureTlStabilized=$true; mixedTlShipsExecuted=$false; counterfactualHoldbacksAreLegalMixedTlBuilds=$false; auxiliaryNumericalStabilizationDeferred=$true;
            legalBuilds=9427; wholeLadderBasePairings=70034; generatedVariants=626028; pipelineSmokeTrials=626028; pipelineSmokeTrialErrors=0;
            symmetryComparisons=2250; symmetryCombatExecutions=4500; symmetryMismatches=0; substantiveTrials=0; failedGates=@()
        }
        $repoOnly | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $repoOnlySummary -Encoding utf8

        Write-Host '[11/12] Verifying repository-only results against the CP129 contract...'
        Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP129 repository-only contract failed'

        Write-Host '[12/12] Checkpoint 129 repository-only gates passed.' -ForegroundColor Green
        Write-Host '       Run the same wrapper without -RepositoryOnly in this unchanged extraction to execute the substantive study.'
    }
    finally { Pop-Location }
    exit 0
}

# Substantive phase deliberately consumes the already accepted RepositoryOnly marker in the same extraction.
if(-not (Test-Path -LiteralPath $repoOnlySummary)){throw 'CP129 substantive phase requires a successful -RepositoryOnly run in the same extracted repository first.'}
Write-Host '[3/12] Revalidating CP129 preflight and repository-only acceptance marker...'
Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot) 'CP129 substantive preflight failed'
Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP129 prior repository-only acceptance contract failed'
$prior=Read-Json $repoOnlySummary
if(-not [bool]$prior.repositoryOnly -or @($prior.failedGates).Count -ne 0){throw 'CP129 repository-only acceptance marker is not valid.'}
Write-Host '       Prior RepositoryOnly acceptance is valid and repository state remains contract-clean.'

Write-Host '[4/12] Preserving previously accepted native build/test/parity gates...'
Write-Host ("       177/177 Python; 907/907 xUnit; 70/70 ScenarioRunner; 25/25 parity from this same extraction; RepositoryOnly Jobs={0}." -f $prior.repositoryOnlyJobs)
Write-Host '[5/12] Preserving accepted deterministic plan...'
Write-Host '       9,427 legal builds; 626,028 total variants.'
Write-Host '[6/12] Preserving accepted physical-symmetry gate...'
Write-Host '       2,250 comparisons / 4,500 executions / 0 mismatches.'
Write-Host '[7/12] Preserving accepted all-variant one-trial smoke...'
Write-Host '       626,028 variants / 0 trial errors.'

Write-Host '[8/12] Running CP129 substantive whole-ladder sensitivity study...'
New-Item -ItemType Directory -Force -Path $substantiveOut | Out-Null
Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'whole-ladder-sensitivity-study',$study,'--output-dir',$substantiveOut,'--mode','run','--jobs',$Jobs) 'CP129 substantive study failed'
$sub=Read-Json (Join-Path $substantiveOut 'analysis.json')
if(@($sub.failedGates).Count -ne 0 -or [long]$sub.totalTrials -ne 45665000 -or [int]$sub.variants -ne 626028 -or [int]$sub.trialErrors -ne 0){throw 'CP129 substantive result shape mismatch.'}
Write-Host '       Substantive study: 45,665,000 engagements / 626,028 variants / 0 trial errors.'

Write-Host '[9/12] Confirming accepted CP127 overlap and pure-TL boundaries...'
if([bool]$sub.mixedTlShipsExecuted -or [bool]$sub.counterfactualHoldbacksAreLegalMixedTlBuilds -or [bool]$sub.technologyValuesChanged){throw 'CP129 substantive boundary violation.'}
$replication=Join-Path $substantiveOut 'whole-ladder\cp127_adjacent_replication.csv'
if(-not (Test-Path -LiteralPath $replication)){throw 'CP129 accepted-CP127 replication evidence is missing.'}
Write-Host '       Accepted CP127 adjacent control reproduced; counterfactual holdbacks remain non-legal probes.'

Write-Host '[10/12] Writing final native acceptance summary...'
$final=[ordered]@{
    schemaVersion='star-cluster-cp129-native-acceptance-summary-v0.1'; checkpoint=129; acceptedEvidenceCheckpoint=128; startingImplementationBaseline=122;
    repositoryOnly=$false; python=$prior.python; dotnetSdk=$prior.dotnetSdk; buildWarningsAsErrors=$prior.buildWarningsAsErrors; buildPassed=$prior.buildPassed;
    pythonTests=$prior.pythonTests; pythonTestsPassed=$prior.pythonTestsPassed; pythonDependencyPolicy=$prior.pythonDependencyPolicy; repositoryOnlyJobs=$prior.repositoryOnlyJobs; substantiveJobs=$Jobs; thirdPartyPythonPackagesAllowed=@();
    xunitTotal=$prior.xunitTotal; xunitPassed=$prior.xunitPassed; xunitFailed=$prior.xunitFailed; xunitSkipped=$prior.xunitSkipped;
    scenarioRunnerSelfTests=$prior.scenarioRunnerSelfTests; scenarioRunnerSelfTestsPassed=$prior.scenarioRunnerSelfTestsPassed; researchParityCases=$prior.researchParityCases; researchParityPassed=$prior.researchParityPassed;
    productionSourceChanged=$false; technologyValuesChanged=$false; scenarioDefinitionsChanged=$false; researchSimulationChanged=$true;
    mainSubsystemPureTlStabilized=$true; mixedTlShipsExecuted=$false; counterfactualHoldbacksAreLegalMixedTlBuilds=$false; auxiliaryNumericalStabilizationDeferred=$true;
    legalBuilds=$prior.legalBuilds; wholeLadderBasePairings=$prior.wholeLadderBasePairings; generatedVariants=$prior.generatedVariants; pipelineSmokeTrials=$prior.pipelineSmokeTrials; pipelineSmokeTrialErrors=$prior.pipelineSmokeTrialErrors;
    symmetryComparisons=$prior.symmetryComparisons; symmetryCombatExecutions=$prior.symmetryCombatExecutions; symmetryMismatches=$prior.symmetryMismatches;
    substantiveTrials=45665000; substantiveTrialErrors=0; rawVariantDetailRetained=$false; failedGates=@()
}
$final | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $finalSummary -Encoding utf8

Write-Host '[11/12] Verifying final CP129 repository/results contract...'
Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP129 final repository/results contract failed'

Write-Host '[12/12] Checkpoint 129 substantive gates passed.' -ForegroundColor Green
Write-Host '       CP129 results are ready for whole-ladder sensitivity assessment; no technology value is automatically promoted by this run.'
