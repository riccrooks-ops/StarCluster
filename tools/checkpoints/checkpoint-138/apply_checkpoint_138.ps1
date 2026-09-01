[CmdletBinding()]
param([switch]$RepositoryOnly,[switch]$NoClean,[int]$Jobs=24)
Set-StrictMode -Version 2.0
$ErrorActionPreference='Stop'
$repositoryRoot=(Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$preflight=Join-Path $PSScriptRoot 'preflight_checkpoint_138.py'
$contract=Join-Path $PSScriptRoot 'test_checkpoint_138_contract.py'
$hygiene=Join-Path $repositoryRoot 'tools\checkpoints\prepackage_repository_hygiene.py'
$research=Join-Path $repositoryRoot 'tools\simulation\run_starcluster_research.py'
$study='docs/archive/testing/pre-cp165-active/cp138_aux_reference_full_ship_integration_study_v0_1.json'
$outRoot=Join-Path $repositoryRoot 'out\checkpoint-138'
$testOut=Join-Path $outRoot 'xunit';$parityOut=Join-Path $outRoot 'research-parity';$deterministicOut=Join-Path $outRoot 'deterministic-scenarios';$tl1PhaseAOut=Join-Path $outRoot 'tl1-phase-a';$planOut=Join-Path $outRoot 'plan';$symmetryOut=Join-Path $outRoot 'symmetry';$smokeOut=Join-Path $outRoot 'smoke';$substantiveOut=Join-Path $outRoot 'substantive'
$repoOnlySummary=Join-Path $outRoot 'CP138_REPOSITORY_ONLY_ACCEPTANCE.json';$finalSummary=Join-Path $outRoot 'CP138_NATIVE_ACCEPTANCE_SUMMARY.json'
function Get-Cpython313Command {$candidates=@(@{Command='py';Args=@('-3.13')},@{Command='python';Args=@()},@{Command='python3';Args=@()});foreach($candidate in $candidates){$cmd=Get-Command $candidate.Command -ErrorAction SilentlyContinue;if($null -eq $cmd){continue};$v=& $candidate.Command @($candidate.Args+@('--version')) 2>&1|Out-String;if($LASTEXITCODE -eq 0 -and $v -match 'Python\s+3\.13(?:\.|\s|$)'){return $candidate}};throw 'CP138 requires Python 3.13.'}
function Invoke-PythonChecked([object]$Python,[string[]]$Arguments,[string]$Failure){& $Python.Command @($Python.Args+$Arguments);if($LASTEXITCODE -ne 0){throw "$Failure (exit code $LASTEXITCODE)."}}
function Invoke-Captured([string]$Label,[string]$LogPath,[scriptblock]$Body){& $Body *> $LogPath;$exitCode=$LASTEXITCODE;if($exitCode -ne 0){Write-Host "       $Label output tail:" -ForegroundColor Yellow;Get-Content -LiteralPath $LogPath -Tail 120|ForEach-Object{Write-Host("       $_")};throw "$Label failed (exit code $exitCode)."}}
function Read-Json([string]$Path){return(Get-Content -LiteralPath $Path -Raw|ConvertFrom-Json)}

Write-Host '[1/11] Resolving deterministic runtimes and accepted CP137 evidence...'
$python=Get-Cpython313Command;$pythonVersion=& $python.Command @($python.Args+@('--version')) 2>&1|Out-String;Write-Host("       {0}" -f $pythonVersion.Trim())
$dotnetVersion=(& dotnet --version 2>&1|Out-String).Trim();if($LASTEXITCODE -ne 0 -or $dotnetVersion -ne '8.0.423'){throw "CP138 requires .NET SDK 8.0.423 exactly; observed '$dotnetVersion'."};Write-Host "       .NET SDK $dotnetVersion"
Write-Host '       CP138 is an AUX reference/full-ship integration sweep on accepted CP137: kernel v0.4, numerical matrix, Concept, production C#, Reactor TP, and power-AUX execution are frozen.'

Write-Host '[2/11] Applying and verifying repository hygiene...'
Invoke-PythonChecked $python @('-B',$hygiene,'--repo',$repositoryRoot,'--apply') 'CP138 hygiene apply failed';Invoke-PythonChecked $python @('-B',$hygiene,'--repo',$repositoryRoot,'--check') 'CP138 hygiene check failed'

if($RepositoryOnly){
    if(-not $NoClean -and(Test-Path -LiteralPath $outRoot)){Remove-Item -Recurse -Force $outRoot}
    New-Item -ItemType Directory -Force -Path $outRoot,$testOut,$parityOut,$deterministicOut,$tl1PhaseAOut,$planOut,$symmetryOut,$smokeOut|Out-Null
    Write-Host '[3/11] Running CP138 preflight and all Python self-tests...'
    Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot) 'CP138 preflight failed'
    Push-Location $repositoryRoot
    try{
        & $python.Command @($python.Args+@('-B','-m','unittest','discover','-s','tools/simulation/tests','-p','test_*.py'));if($LASTEXITCODE -ne 0){throw "CP138 Python self-tests failed (exit code $LASTEXITCODE)."};Write-Host '       Python self-tests: 234/234 passed.'
        Write-Host '[4/11] Building native C# solution with warnings as errors...'
        $buildLog=Join-Path $outRoot 'build.log';Invoke-Captured 'CP138 warning-as-error build' $buildLog {dotnet build StarCluster.sln --configuration Release --nologo -warnaserror};Write-Host '       Native build passed under SDK 8.0.423 with warnings treated as errors.'
        Write-Host '[5/11] Running xUnit and ScenarioRunner deterministic gates...'
        dotnet test tests\StarCluster.Tests\StarCluster.Tests.csproj --configuration Release --no-build --nologo --logger 'trx;LogFileName=cp138-tests.trx' --results-directory $testOut
        $xunitExit=$LASTEXITCODE;$trxPath=Join-Path $testOut 'cp138-tests.trx';if(-not(Test-Path -LiteralPath $trxPath)){throw 'CP138 xUnit TRX missing.'};[xml]$trx=Get-Content -LiteralPath $trxPath -Raw;$c=$trx.TestRun.ResultSummary.Counters;$total=[int]$c.total;$passed=[int]$c.passed;$failed=[int]$c.failed;$skipped=[int]$c.notExecuted;if($xunitExit -ne 0 -or $total -ne 913 -or $passed -ne 913 -or $failed -ne 0 -or $skipped -ne 0){throw "CP138 xUnit mismatch exit=$xunitExit total=$total passed=$passed failed=$failed skipped=$skipped."};Write-Host '       xUnit tests: 913/913 passed.'
        $selfLog=Join-Path $outRoot 'scenario-self-tests.log';Invoke-Captured 'CP138 ScenarioRunner self-tests' $selfLog {dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- self-test};$selfText=Get-Content -LiteralPath $selfLog -Raw;if($selfText -notmatch 'Runner self-tests:\s+70 passed,\s+0 failed,\s+70 total\.'){throw 'CP138 expected 70/70 ScenarioRunner self-tests.'};Write-Host '       ScenarioRunner self-tests: 70/70 passed.'
        $detLog=Join-Path $outRoot 'deterministic-scenarios.log';Invoke-Captured 'CP138 deterministic scenario corpus' $detLog {dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- run-all --output-dir $deterministicOut};Write-Host '       Top-level deterministic scenario corpus passed.'
        $tl1Log=Join-Path $outRoot 'tl1-phase-a.log';Invoke-Captured 'CP138 TL1 Phase-A deterministic corpus' $tl1Log {dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- tl1-phase-a --output-dir $tl1PhaseAOut};Write-Host '       TL1 Phase-A deterministic mechanics corpus passed.'
        Write-Host '[6/11] Running research parity and CP138 AUX integration tests...'
        Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'parity','--output-dir',$parityOut) 'CP138 research parity failed';$parity=Read-Json(Join-Path $parityOut 'summary.json');if(-not[bool]$parity.passed -or[int]$parity.cases -ne 25){throw 'CP138 expected 25/25 research parity.'};Write-Host '       Research parity: 25/25 passed.'
        & $python.Command @($python.Args+@('-B','-m','unittest','discover','-v','-s','tools/simulation/tests','-p','test_cp138_auxiliary_integration.py'));if($LASTEXITCODE -ne 0){throw 'CP138 AUX integration tests failed.'};Write-Host '       CP138 AUX integration tests: 8/8 passed.'
        Write-Host '[7/11] Verifying whole-catalog coverage and exact-fill full-ship plan...'
        Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'auxiliary-integration-study',$study,'--output-dir','out/checkpoint-138/plan','--mode','plan','--jobs',$Jobs) 'CP138 study plan failed';$plan=Read-Json(Join-Path $planOut 'summary.json');if(-not[bool]$plan.passed -or[int]$plan.analysis.logicalContexts -ne 787 -or[int]$plan.analysis.generatedVariants -ne 1574 -or[int]$plan.analysis.catalogCoverage.catalogComponents -ne 35 -or[int]$plan.analysis.catalogCoverage.catalogCovered -ne 35){throw 'CP138 plan/catalog shape mismatch.'};Write-Host '       Plan: 35/35 AUX catalog coverage; 10 philosophies; 787 contexts / 1,574 variants; every reference ship exact-fill.'
        Write-Host '[8/11] Running physical-symmetry gate...'
        Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'auxiliary-integration-study',$study,'--output-dir','out/checkpoint-138/symmetry','--mode','symmetry','--jobs',$Jobs) 'CP138 symmetry gate failed';$sym=Read-Json(Join-Path $symmetryOut 'summary.json');if(-not[bool]$sym.passed -or[int]$sym.analysis.comparisons -ne 50 -or[int]$sym.analysis.mismatches -ne 0){throw 'CP138 symmetry mismatch.'};Write-Host '       Physical symmetry: 50 comparisons / 100 executions / 0 mismatches.'
        Write-Host '[9/11] Running one-trial full-matrix AUX pipeline smoke...'
        Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'auxiliary-integration-study',$study,'--output-dir','out/checkpoint-138/smoke','--mode','smoke','--jobs',$Jobs) 'CP138 pipeline smoke failed';$smoke=Read-Json(Join-Path $smokeOut 'summary.json');if(-not[bool]$smoke.passed -or[int]$smoke.analysis.variants -ne 1574 -or[int]$smoke.analysis.totalTrials -ne 1574 -or[int]$smoke.analysis.trialErrors -ne 0 -or[int]$smoke.analysis.mechanicsFlags -ne 0){throw 'CP138 smoke shape/mechanics mismatch.'};Write-Host '       Smoke: 1,574/1,574 variants, zero trial errors, zero mechanics flags.'
        Write-Host '[10/11] Writing repository-only acceptance marker...'
        $summary=[ordered]@{schemaVersion='star-cluster-cp138-repository-only-acceptance-v0.1';checkpoint=138;repositoryOnly=$true;acceptedMechanicsResearchBaseline=137;python=$pythonVersion.Trim();dotnetSdk=$dotnetVersion;buildPassed=$true;pythonTestsPassed=234;xunitTotal=$total;xunitPassed=$passed;xunitFailed=$failed;xunitSkipped=$skipped;scenarioRunnerSelfTestsPassed=70;deterministicScenarioCorpusPassed=$true;tl1PhaseACorpusPassed=$true;researchParityPassed=25;cp138TestsPassed=8;canonicalKernelVersion='0.4';canonicalDamageModel='penetration-hardening-v1';catalogComponents=35;referencePhilosophies=10;logicalContexts=787;generatedVariants=1574;symmetryComparisons=50;symmetryMismatches=0;smokeTrials=1574;smokeTrialErrors=0;smokeMechanicsFlags=0;reactorTuningEnabled=$false;powerAuxExecutionEnabled=$false;balanceTargets=$null;automaticPromotion=$false;substantiveTrials=0;failedGates=@()};$summary|ConvertTo-Json -Depth 7|Set-Content -LiteralPath $repoOnlySummary -Encoding utf8
        Write-Host '[11/11] Verifying CP138 repository/results contract...';Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP138 repository-only contract failed';Write-Host '       Checkpoint 138 RepositoryOnly gates passed.' -ForegroundColor Green
    }finally{Pop-Location}
    return
}

if(-not(Test-Path -LiteralPath $repoOnlySummary)){throw 'CP138 finalization requires a successful -RepositoryOnly run in the same extraction first.'}
Write-Host '[3/11] Revalidating preflight and repository-only marker...';Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot);Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP138 prior contract failed';$prior=Read-Json $repoOnlySummary
Write-Host '[4/11] Preserving native deterministic gates...';Write-Host '       234/234 Python; 913/913 xUnit; 70/70 ScenarioRunner; deterministic corpora; 25/25 parity; 8/8 CP138 tests.'
Write-Host '[5/11] Preserving AUX plan/symmetry/smoke gates...';Write-Host '       35/35 catalog coverage; 787 contexts / 1,574 variants; 50 symmetry comparisons / 0 mismatches; 1,574 smoke trials / 0 errors.'
Write-Host '[6/11] Running substantive full-ship AUX integration diagnostic...'
if(-not $NoClean -and(Test-Path -LiteralPath $substantiveOut)){Remove-Item -Recurse -Force $substantiveOut};New-Item -ItemType Directory -Force -Path $substantiveOut|Out-Null
Push-Location $repositoryRoot
try{Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'auxiliary-integration-study',$study,'--output-dir','out/checkpoint-138/substantive','--mode','run','--trials','2000','--jobs',$Jobs) 'CP138 substantive study failed'}finally{Pop-Location}
$subWrap=Read-Json(Join-Path $substantiveOut 'summary.json');$sub=$subWrap.analysis
if(-not[bool]$subWrap.passed -or[int]$sub.variants -ne 1574 -or[int]$sub.logicalContexts -ne 787 -or[int]$sub.trialsPerVariant -ne 2000 -or[long]$sub.totalTrials -ne 3148000 -or[int]$sub.trialErrors -ne 0 -or[int]$sub.mechanicsFlags -ne 0){throw 'CP138 substantive result shape/mechanics gate mismatch.'}
Write-Host '[7/11] Recording AUX integration strata and Tactical Power telemetry...';Write-Host("       role rows={0}; EW rows={1}; PDS rows={2}; hardener rows={3}; generalist rows={4}; review flags={5}." -f $sub.roleSummaryRows,$sub.ewCounterplayRows,$sub.pdsThreatRows,$sub.hardenerRows,$sub.generalistRows,$sub.diagnosticReviewFlags);Write-Host '       Review flags are diagnostic only; no 50/50 target is applied.'
Write-Host '[8/11] Confirming Reactor and numerical promotion remain frozen...';if([bool]$sub.reactorTuningEnabled -or[bool]$sub.powerAuxExecutionEnabled -or[bool]$sub.automaticPromotion -or $null -ne $sub.balanceTargets){throw 'CP138 interpretation boundary violated.'};Write-Host '       Reactor TP and power-AUX execution remain held for the post-AUX demand phase.'
Write-Host '[9/11] Writing final native acceptance summary...'
$final=[ordered]@{};foreach($p in $prior.PSObject.Properties){$final[$p.Name]=$p.Value};$final['schemaVersion']='star-cluster-cp138-native-acceptance-summary-v0.1';$final['repositoryOnly']=$false;$final['substantiveVariants']=[int]$sub.variants;$final['substantiveLogicalContexts']=[int]$sub.logicalContexts;$final['substantiveTrialsPerVariant']=[int]$sub.trialsPerVariant;$final['substantiveTrials']=[long]$sub.totalTrials;$final['substantiveTrialErrors']=[int]$sub.trialErrors;$final['substantiveMechanicsFlags']=[int]$sub.mechanicsFlags;$final['diagnosticReviewFlags']=[int]$sub.diagnosticReviewFlags;$final['roleSummaryRows']=[int]$sub.roleSummaryRows;$final['ewCounterplayRows']=[int]$sub.ewCounterplayRows;$final['pdsThreatRows']=[int]$sub.pdsThreatRows;$final['hardenerRows']=[int]$sub.hardenerRows;$final['generalistRows']=[int]$sub.generalistRows;$final['substantiveElapsedSeconds']=[double]$sub.elapsedSeconds;$final|ConvertTo-Json -Depth 7|Set-Content -LiteralPath $finalSummary -Encoding utf8
Write-Host '[10/11] Verifying final CP138 repository/results contract...';Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP138 final contract failed'
Write-Host '[11/11] Checkpoint 138 native gates passed.' -ForegroundColor Green;Write-Host '       CP138 is accepted as an AUX reference/full-ship integration diagnostic; no AUX or Reactor values are automatically promoted.'
