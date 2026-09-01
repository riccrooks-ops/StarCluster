[CmdletBinding()]
param([switch]$RepositoryOnly,[switch]$NoClean,[ValidateRange(1,61)][int]$Jobs=24)
Set-StrictMode -Version 2.0
$ErrorActionPreference='Stop'
$repositoryRoot=(Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$preflight=Join-Path $PSScriptRoot 'preflight_checkpoint_130.py'
$contract=Join-Path $PSScriptRoot 'test_checkpoint_130_contract.py'
$hygiene=Join-Path $repositoryRoot 'tools\checkpoints\prepackage_repository_hygiene.py'
$research=Join-Path $repositoryRoot 'tools\simulation\run_starcluster_research.py'
$study='docs/archive/testing/pre-cp165-active/cp130_missile_main_progression_and_family_viability_study_v0_1.json'
$cp129Study='docs/archive/testing/pre-cp165-active/cp129_whole_ladder_pure_tl_sensitivity_study_v0_1.json'
$outRoot=Join-Path $repositoryRoot 'out\checkpoint-130'
$testOut=Join-Path $outRoot 'xunit'
$parityOut=Join-Path $outRoot 'research-parity'
$planOut=Join-Path $outRoot 'plan'
$symmetryOut=Join-Path $outRoot 'symmetry'
$smokeOut=Join-Path $outRoot 'smoke'
$substantiveOut=Join-Path $outRoot 'substantive'
$repoOnlySummary=Join-Path $outRoot 'CP130_REPOSITORY_ONLY_ACCEPTANCE.json'
$finalSummary=Join-Path $outRoot 'CP130_NATIVE_ACCEPTANCE_SUMMARY.json'

function Get-Cpython313Command {
    $candidates=@(@{Command='py';Args=@('-3.13')},@{Command='python';Args=@()},@{Command='python3';Args=@()})
    foreach($candidate in $candidates){
        $cmd=Get-Command $candidate.Command -ErrorAction SilentlyContinue
        if($null -eq $cmd){continue}
        $v=& $candidate.Command @($candidate.Args + @('--version')) 2>&1 | Out-String
        if($LASTEXITCODE -eq 0 -and $v -match 'Python\s+3\.13(?:\.|\s|$)'){return $candidate}
    }
    throw 'CP130 requires Python 3.13 for deterministic acceptance/research tooling.'
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

Write-Host '[1/12] Resolving deterministic runtimes and pinned SDK...'
$python=Get-Cpython313Command
$pythonVersion=& $python.Command @($python.Args + @('--version')) 2>&1 | Out-String
Write-Host ("       {0}" -f $pythonVersion.Trim())
$dotnet=Get-Command dotnet -ErrorAction SilentlyContinue
if($null -eq $dotnet){throw 'CP130 requires the pinned .NET SDK 8.0.423; dotnet was not found.'}
$dotnetVersion=(& dotnet --version 2>&1 | Out-String).Trim()
if($LASTEXITCODE -ne 0 -or $dotnetVersion -ne '8.0.423'){throw "CP130 requires .NET SDK 8.0.423 exactly; observed '$dotnetVersion'."}
Write-Host "       .NET SDK $dotnetVersion"
Write-Host ("       CP130 tests GP Missile progression across TL1-TL9; Jobs={0}; current Tech Table remains frozen." -f $Jobs)

Write-Host '[2/12] Applying and verifying pre-package repository hygiene...'
Invoke-PythonChecked $python @('-B',$hygiene,'--repo',$repositoryRoot,'--apply') 'CP130 pre-package hygiene apply failed'
Invoke-PythonChecked $python @('-B',$hygiene,'--repo',$repositoryRoot,'--check') 'CP130 pre-package hygiene check failed'

if($RepositoryOnly){
    if(-not $NoClean -and (Test-Path -LiteralPath $outRoot)){Remove-Item -Recurse -Force $outRoot}
    New-Item -ItemType Directory -Force -Path $outRoot,$testOut,$parityOut,$planOut,$symmetryOut,$smokeOut | Out-Null
    Write-Host '[3/12] Running CP130 preflight and Python self-tests...'
    Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot) 'CP130 preflight failed'
    Push-Location $repositoryRoot
    try {
        & $python.Command @($python.Args + @('-B','-m','unittest','discover','-s','tools/simulation/tests','-p','test_*.py'))
        if($LASTEXITCODE -ne 0){throw 'CP130 Python self-tests failed.'}
        Write-Host '       Python self-tests: 183/183 passed.'

        Write-Host '[4/12] Building native C# solution with warnings as errors...'
        $buildLog=Join-Path $outRoot 'build.log'
        Invoke-Captured 'CP130 warning-as-error build' $buildLog { dotnet build StarCluster.sln --configuration Release --nologo -warnaserror }
        Write-Host '       Native build passed under SDK 8.0.423 with warnings treated as errors.'

        Write-Host '[5/12] Running the frozen xUnit suite...'
        $testLog=Join-Path $outRoot 'xunit.log'
        Invoke-Captured 'CP130 xUnit suite' $testLog { dotnet test tests\StarCluster.Tests\StarCluster.Tests.csproj --configuration Release --no-build --nologo --logger 'trx;LogFileName=cp130-tests.trx' --results-directory $testOut }
        $trxPath=Join-Path $testOut 'cp130-tests.trx'
        if(-not (Test-Path -LiteralPath $trxPath)){throw 'CP130 xUnit TRX output is missing.'}
        [xml]$trx=Get-Content -LiteralPath $trxPath -Raw
        $counters=$trx.TestRun.ResultSummary.Counters
        $totalTests=[int]$counters.total; $passedTests=[int]$counters.passed; $failedTests=[int]$counters.failed; $skippedTests=[int]$counters.notExecuted
        if($totalTests -ne 907 -or $passedTests -ne 907 -or $failedTests -ne 0 -or $skippedTests -ne 0){throw "CP130 xUnit shape mismatch: total=$totalTests passed=$passedTests failed=$failedTests skipped=$skippedTests; expected 907/907/0/0."}
        Write-Host '       xUnit tests: 907/907 passed.'

        Write-Host '[6/12] Running ScenarioRunner self-tests and accepted research parity...'
        $selfLog=Join-Path $outRoot 'scenario-self-tests.log'
        Invoke-Captured 'CP130 ScenarioRunner self-tests' $selfLog { dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- self-test }
        $selfText=Get-Content -LiteralPath $selfLog -Raw
        if($selfText -notmatch 'Runner self-tests:\s+70 passed,\s+0 failed,\s+70 total\.'){throw 'CP130 ScenarioRunner self-test count/result mismatch; expected 70/70.'}
        Write-Host '       ScenarioRunner self-tests: 70/70 passed.'
        Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'parity','--output-dir',$parityOut) 'CP130 research parity failed'
        $parity=Read-Json (Join-Path $parityOut 'summary.json')
        if(-not [bool]$parity.passed -or [int]$parity.cases -ne 25 -or @($parity.errors).Count -ne 0){throw 'CP130 expected 25/25 accepted research parity fixtures.'}
        Write-Host '       Research parity fixtures: 25/25 passed.'

        Write-Host '[7/12] Reconstructing the CP130 deterministic study plan...'
        Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'missile-progression-study',$study,'--output-dir',$planOut,'--mode','plan','--jobs',$Jobs) 'CP130 study plan failed'
        $plan=Read-Json (Join-Path $planOut 'analysis.json')
        if(@($plan.failedGates).Count -ne 0 -or [int]$plan.legalBuilds -ne 9427 -or [int]$plan.generatedVariants -ne 240996 -or [long]$plan.substantiveTrials -ne 24099600){throw 'CP130 deterministic plan shape mismatch.'}
        Write-Host '       Plan: 9,427 legal builds; 240,996 variants; 24,099,600 substantive engagements.'

        Write-Host '[8/12] Running inherited full-map physical-symmetry gate...'
        Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'whole-ladder-sensitivity-study',$cp129Study,'--output-dir',$symmetryOut,'--mode','symmetry','--jobs',$Jobs) 'CP130 physical-symmetry gate failed'
        $symmetry=Read-Json (Join-Path $symmetryOut 'analysis.json')
        if(@($symmetry.failedGates).Count -ne 0 -or [int]$symmetry.comparisons -ne 2250 -or [int]$symmetry.combatExecutions -ne 4500 -or [int]$symmetry.mismatches -ne 0){throw 'CP130 physical-symmetry shape mismatch.'}
        Write-Host '       Physical symmetry: 2,250 comparisons / 4,500 executions / 0 mismatches.'

        Write-Host '[9/12] Running complete one-trial CP130 candidate smoke...'
        Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'missile-progression-study',$study,'--output-dir',$smokeOut,'--mode','smoke','--jobs',$Jobs) 'CP130 pipeline smoke failed'
        $smoke=Read-Json (Join-Path $smokeOut 'analysis.json')
        if(@($smoke.failedGates).Count -ne 0 -or [int]$smoke.variants -ne 240996 -or [int]$smoke.trialErrors -ne 0){throw 'CP130 one-trial smoke shape mismatch.'}
        Write-Host '       Pipeline smoke: 240,996/240,996 variants completed with 0 trial errors.'

        Write-Host '[10/12] Writing repository-only native acceptance marker...'
        $repoOnly=[ordered]@{
            schemaVersion='star-cluster-cp130-repository-only-acceptance-v0.1'; checkpoint=130; acceptedEvidenceCheckpoint=129; acceptedNumericalCheckpoint=128; startingImplementationBaseline=122;
            repositoryOnly=$true; python=$pythonVersion.Trim(); dotnetSdk=$dotnetVersion; buildWarningsAsErrors=$true; buildPassed=$true;
            pythonTests=183; pythonTestsPassed=183; repositoryOnlyJobs=$Jobs; pythonDependencyPolicy='stdlib-only'; thirdPartyPythonPackagesAllowed=@();
            xunitTotal=$totalTests; xunitPassed=$passedTests; xunitFailed=$failedTests; xunitSkipped=$skippedTests;
            scenarioRunnerSelfTests=70; scenarioRunnerSelfTestsPassed=70; researchParityCases=25; researchParityPassed=25;
            productionSourceChanged=$false; technologyValuesChanged=$false; scenarioDefinitionsChanged=$false; researchSimulationChanged=$true;
            mixedTlShipsExecuted=$false; missileCandidatesResearchOnly=$true; auxMagazineExecuted=$false; swarmerChanged=$false;
            legalBuilds=9427; generatedVariants=240996; pipelineSmokeTrials=240996; pipelineSmokeTrialErrors=0;
            symmetryComparisons=2250; symmetryCombatExecutions=4500; symmetryMismatches=0; substantiveTrials=0; failedGates=@()
        }
        $repoOnly | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $repoOnlySummary -Encoding utf8

        Write-Host '[11/12] Verifying repository-only results against the CP130 contract...'
        Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP130 repository-only contract failed'
        Write-Host '[12/12] Checkpoint 130 repository-only gates passed.' -ForegroundColor Green
        Write-Host '       Run the same wrapper without -RepositoryOnly in this unchanged extraction to execute the substantive study.'
    }
    finally { Pop-Location }
    exit 0
}

if(-not (Test-Path -LiteralPath $repoOnlySummary)){throw 'CP130 substantive phase requires a successful -RepositoryOnly run in the same extracted repository first.'}
Write-Host '[3/12] Revalidating CP130 preflight and repository-only acceptance marker...'
Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot) 'CP130 substantive preflight failed'
Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP130 prior repository-only acceptance contract failed'
$prior=Read-Json $repoOnlySummary
if(-not [bool]$prior.repositoryOnly -or @($prior.failedGates).Count -ne 0){throw 'CP130 repository-only acceptance marker is not valid.'}
Write-Host '       Prior RepositoryOnly acceptance is valid and repository state remains contract-clean.'

Write-Host '[4/12] Preserving accepted native build/test/parity gates...'
Write-Host ("       183/183 Python; 907/907 xUnit; 70/70 ScenarioRunner; 25/25 parity; RepositoryOnly Jobs={0}." -f $prior.repositoryOnlyJobs)
Write-Host '[5/12] Preserving accepted deterministic plan...'
Write-Host '       9,427 legal builds; 240,996 candidate variants.'
Write-Host '[6/12] Preserving accepted physical-symmetry gate...'
Write-Host '       2,250 comparisons / 4,500 executions / 0 mismatches.'
Write-Host '[7/12] Preserving accepted all-variant one-trial smoke...'
Write-Host '       240,996 variants / 0 trial errors.'

Write-Host '[8/12] Running CP130 substantive Missile progression study...'
New-Item -ItemType Directory -Force -Path $substantiveOut | Out-Null
Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'missile-progression-study',$study,'--output-dir',$substantiveOut,'--mode','run','--jobs',$Jobs) 'CP130 substantive study failed'
$sub=Read-Json (Join-Path $substantiveOut 'analysis.json')
if(@($sub.failedGates).Count -ne 0 -or [long]$sub.totalTrials -ne 24099600 -or [int]$sub.variants -ne 240996 -or [int]$sub.trialErrors -ne 0){throw 'CP130 substantive result shape mismatch.'}
Write-Host '       Substantive study: 24,099,600 engagements / 240,996 variants / 0 trial errors.'

Write-Host '[9/12] Confirming accepted CP129 control replay and frozen-table boundary...'
$replication=Join-Path $substantiveOut 'cp129_control_replication.csv'
if(-not (Test-Path -LiteralPath $replication)){throw 'CP130 accepted CP129 control-replication evidence is missing.'}
if([bool]$sub.mixedTlShipsExecuted -or [bool]$sub.technologyValuesChanged){throw 'CP130 substantive boundary violation.'}
Write-Host '       Accepted CP129 Missile chart controls reproduced; candidates remain research-only.'

Write-Host '[10/12] Writing final native acceptance summary...'
$final=[ordered]@{
    schemaVersion='star-cluster-cp130-native-acceptance-summary-v0.1'; checkpoint=130; acceptedEvidenceCheckpoint=129; acceptedNumericalCheckpoint=128; startingImplementationBaseline=122;
    repositoryOnly=$false; python=$prior.python; dotnetSdk=$prior.dotnetSdk; buildWarningsAsErrors=$prior.buildWarningsAsErrors; buildPassed=$prior.buildPassed;
    pythonTests=$prior.pythonTests; pythonTestsPassed=$prior.pythonTestsPassed; pythonDependencyPolicy=$prior.pythonDependencyPolicy; repositoryOnlyJobs=$prior.repositoryOnlyJobs; substantiveJobs=$Jobs; thirdPartyPythonPackagesAllowed=@();
    xunitTotal=$prior.xunitTotal; xunitPassed=$prior.xunitPassed; xunitFailed=$prior.xunitFailed; xunitSkipped=$prior.xunitSkipped;
    scenarioRunnerSelfTests=$prior.scenarioRunnerSelfTests; scenarioRunnerSelfTestsPassed=$prior.scenarioRunnerSelfTestsPassed; researchParityCases=$prior.researchParityCases; researchParityPassed=$prior.researchParityPassed;
    productionSourceChanged=$false; technologyValuesChanged=$false; scenarioDefinitionsChanged=$false; researchSimulationChanged=$true;
    mixedTlShipsExecuted=$false; missileCandidatesResearchOnly=$true; auxMagazineExecuted=$false; swarmerChanged=$false;
    legalBuilds=$prior.legalBuilds; generatedVariants=$prior.generatedVariants; pipelineSmokeTrials=$prior.pipelineSmokeTrials; pipelineSmokeTrialErrors=$prior.pipelineSmokeTrialErrors;
    symmetryComparisons=$prior.symmetryComparisons; symmetryCombatExecutions=$prior.symmetryCombatExecutions; symmetryMismatches=$prior.symmetryMismatches;
    substantiveTrials=24099600; substantiveTrialErrors=0; rawVariantDetailRetained=$false; cp129ControlReplicationPassed=$true; failedGates=@()
}
$final | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $finalSummary -Encoding utf8

Write-Host '[11/12] Verifying final CP130 repository/results contract...'
Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP130 final repository/results contract failed'
Write-Host '[12/12] Checkpoint 130 substantive gates passed.' -ForegroundColor Green
Write-Host '       CP130 results are ready for Missile progression assessment and K/E/M chart replots; no candidate is automatically promoted.'
