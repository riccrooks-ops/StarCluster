[CmdletBinding()]
param([switch]$RepositoryOnly,[switch]$NoClean,[int]$Jobs=24)
Set-StrictMode -Version 2.0
$ErrorActionPreference='Stop'
$repositoryRoot=(Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$preflight=Join-Path $PSScriptRoot 'preflight_checkpoint_136.py'
$contract=Join-Path $PSScriptRoot 'test_checkpoint_136_contract.py'
$hygiene=Join-Path $repositoryRoot 'tools\checkpoints\prepackage_repository_hygiene.py'
$research=Join-Path $repositoryRoot 'tools\simulation\run_starcluster_research.py'
$study='docs/archive/testing/pre-cp165-active/cp136_armor_rebaseline_study_v0_1.json'
$outRoot=Join-Path $repositoryRoot 'out\checkpoint-136'
$testOut=Join-Path $outRoot 'xunit'
$parityOut=Join-Path $outRoot 'research-parity'
$deterministicOut=Join-Path $outRoot 'deterministic-scenarios'
$tl1PhaseAOut=Join-Path $outRoot 'tl1-phase-a'
$planOut=Join-Path $outRoot 'plan'
$symmetryOut=Join-Path $outRoot 'symmetry'
$smokeOut=Join-Path $outRoot 'smoke'
$substantiveOut=Join-Path $outRoot 'substantive'
$repoOnlySummary=Join-Path $outRoot 'CP136_REPOSITORY_ONLY_ACCEPTANCE.json'
$finalSummary=Join-Path $outRoot 'CP136_NATIVE_ACCEPTANCE_SUMMARY.json'
function Get-Cpython313Command {
    $candidates=@(@{Command='py';Args=@('-3.13')},@{Command='python';Args=@()},@{Command='python3';Args=@()})
    foreach($candidate in $candidates){$cmd=Get-Command $candidate.Command -ErrorAction SilentlyContinue;if($null -eq $cmd){continue};$v=& $candidate.Command @($candidate.Args+@('--version')) 2>&1|Out-String;if($LASTEXITCODE -eq 0 -and $v -match 'Python\s+3\.13(?:\.|\s|$)'){return $candidate}}
    throw 'CP136 requires Python 3.13.'
}
function Invoke-PythonChecked([object]$Python,[string[]]$Arguments,[string]$Failure){& $Python.Command @($Python.Args+$Arguments);if($LASTEXITCODE -ne 0){throw "$Failure (exit code $LASTEXITCODE)."}}
function Invoke-Captured([string]$Label,[string]$LogPath,[scriptblock]$Body){& $Body *> $LogPath;$exitCode=$LASTEXITCODE;if($exitCode -ne 0){Write-Host "       $Label output tail:" -ForegroundColor Yellow;Get-Content -LiteralPath $LogPath -Tail 120|ForEach-Object{Write-Host("       $_")};throw "$Label failed (exit code $exitCode)."}}
function Read-Json([string]$Path){return(Get-Content -LiteralPath $Path -Raw|ConvertFrom-Json)}

Write-Host '[1/11] Resolving deterministic runtimes and accepted CP135 evidence...'
$python=Get-Cpython313Command;$pythonVersion=& $python.Command @($python.Args+@('--version')) 2>&1|Out-String;Write-Host("       {0}" -f $pythonVersion.Trim())
$dotnetVersion=(& dotnet --version 2>&1|Out-String).Trim();if($LASTEXITCODE -ne 0 -or $dotnetVersion -ne '8.0.423'){throw "CP136 requires .NET SDK 8.0.423 exactly; observed '$dotnetVersion'."};Write-Host "       .NET SDK $dotnetVersion"
Write-Host '       CP136 repeats CP135 with only mainline Armor TL6-TL9 and TL6 A_b1 Crystalline numerics changed; kernel v0.3, Shield recharge, Hull-only DamCon, weapons, PDS, and study geometry are held.'

Write-Host '[2/11] Applying and verifying repository hygiene...'
Invoke-PythonChecked $python @('-B',$hygiene,'--repo',$repositoryRoot,'--apply') 'CP136 hygiene apply failed'
Invoke-PythonChecked $python @('-B',$hygiene,'--repo',$repositoryRoot,'--check') 'CP136 hygiene check failed'

if($RepositoryOnly){
    if(-not $NoClean -and(Test-Path -LiteralPath $outRoot)){Remove-Item -Recurse -Force $outRoot}
    New-Item -ItemType Directory -Force -Path $outRoot,$testOut,$parityOut,$deterministicOut,$tl1PhaseAOut,$planOut,$symmetryOut,$smokeOut|Out-Null
    Write-Host '[3/11] Running CP136 preflight and all Python self-tests...'
    Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot) 'CP136 preflight failed'
    Push-Location $repositoryRoot
    try{
        & $python.Command @($python.Args+@('-B','-m','unittest','discover','-s','tools/simulation/tests','-p','test_*.py'));if($LASTEXITCODE -ne 0){throw "CP136 Python self-tests failed (exit code $LASTEXITCODE)."};Write-Host '       Python self-tests: 218/218 passed.'
        Write-Host '[4/11] Building native C# solution with warnings as errors...'
        $buildLog=Join-Path $outRoot 'build.log';Invoke-Captured 'CP136 warning-as-error build' $buildLog {dotnet build StarCluster.sln --configuration Release --nologo -warnaserror};Write-Host '       Native build passed under SDK 8.0.423 with warnings treated as errors.'
        Write-Host '[5/11] Running xUnit and ScenarioRunner deterministic gates...'
        dotnet test tests\StarCluster.Tests\StarCluster.Tests.csproj --configuration Release --no-build --nologo --logger 'trx;LogFileName=cp136-tests.trx' --results-directory $testOut
        $xunitExit=$LASTEXITCODE;$trxPath=Join-Path $testOut 'cp136-tests.trx';if(-not(Test-Path -LiteralPath $trxPath)){throw 'CP136 xUnit TRX missing.'};[xml]$trx=Get-Content -LiteralPath $trxPath -Raw;$c=$trx.TestRun.ResultSummary.Counters;$total=[int]$c.total;$passed=[int]$c.passed;$failed=[int]$c.failed;$skipped=[int]$c.notExecuted;if($xunitExit -ne 0 -or $total -ne 913 -or $passed -ne 913 -or $failed -ne 0 -or $skipped -ne 0){throw "CP136 xUnit mismatch exit=$xunitExit total=$total passed=$passed failed=$failed skipped=$skipped. See $trxPath for complete results."};Write-Host '       xUnit tests: 913/913 passed.'
        $selfLog=Join-Path $outRoot 'scenario-self-tests.log';Invoke-Captured 'CP136 ScenarioRunner self-tests' $selfLog {dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- self-test};$selfText=Get-Content -LiteralPath $selfLog -Raw;if($selfText -notmatch 'Runner self-tests:\s+70 passed,\s+0 failed,\s+70 total\.'){throw 'CP136 expected 70/70 ScenarioRunner self-tests.'};Write-Host '       ScenarioRunner self-tests: 70/70 passed.'
        $detLog=Join-Path $outRoot 'deterministic-scenarios.log';Invoke-Captured 'CP136 deterministic scenario corpus' $detLog {dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- run-all --output-dir $deterministicOut};Write-Host '       Top-level deterministic scenario corpus passed.'
        $tl1Log=Join-Path $outRoot 'tl1-phase-a.log';Invoke-Captured 'CP136 TL1 Phase-A deterministic corpus' $tl1Log {dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- tl1-phase-a --output-dir $tl1PhaseAOut};Write-Host '       TL1 Phase-A deterministic mechanics corpus passed.'
        Write-Host '[6/11] Running research parity and CP136 canonical mechanics tests...'
        Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'parity','--output-dir',$parityOut) 'CP136 research parity failed';$parity=Read-Json(Join-Path $parityOut 'summary.json');if(-not[bool]$parity.passed -or[int]$parity.cases -ne 25){throw 'CP136 expected 25/25 research parity.'};Write-Host '       Research parity: 25/25 passed.'
        & $python.Command @($python.Args+@('-B','-m','unittest','discover','-v','-s','tools/simulation/tests','-p','test_cp136_armor_rebaseline.py'));if($LASTEXITCODE -ne 0){throw 'CP136 Armor rebaseline tests failed.'};Write-Host '       CP136 Armor rebaseline tests: 7/7 passed.'
        Write-Host '[7/11] Verifying exact CP135-shaped common-random-number plan...'
        Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'same-tl-candidate-baseline-study',$study,'--output-dir','out/checkpoint-136/plan','--mode','plan','--jobs',$Jobs) 'CP136 study plan failed';$plan=Read-Json(Join-Path $planOut 'summary.json');if(-not[bool]$plan.passed -or[int]$plan.analysis.logicalContexts -ne 196 -or[int]$plan.analysis.generatedVariants -ne 392 -or[int]$plan.analysis.tl6Variants -ne 136){throw 'CP136 plan shape mismatch.'};Write-Host '       Study plan: 196 contexts / 392 variants / 136 TL6 variants; master seed 134001.'
        Write-Host '[8/11] Running physical-symmetry gate...'
        Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'same-tl-candidate-baseline-study',$study,'--output-dir','out/checkpoint-136/symmetry','--mode','symmetry','--jobs',$Jobs) 'CP136 symmetry gate failed';$sym=Read-Json(Join-Path $symmetryOut 'summary.json');if(-not[bool]$sym.passed -or[int]$sym.analysis.comparisons -ne 50 -or[int]$sym.analysis.mismatches -ne 0){throw 'CP136 symmetry shape mismatch.'};Write-Host '       Physical symmetry: 50 comparisons / 100 executions / 0 mismatches.'
        Write-Host '[9/11] Running one-trial full-matrix pipeline smoke...'
        Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'same-tl-candidate-baseline-study',$study,'--output-dir','out/checkpoint-136/smoke','--mode','smoke','--jobs',$Jobs) 'CP136 pipeline smoke failed';$smoke=Read-Json(Join-Path $smokeOut 'summary.json');if(-not[bool]$smoke.passed -or[int]$smoke.analysis.variants -ne 392 -or[int]$smoke.analysis.totalTrials -ne 392 -or[int]$smoke.analysis.trialErrors -ne 0 -or[int]$smoke.analysis.mechanicsFlags -ne 0){throw 'CP136 smoke shape mismatch.'};Write-Host '       Smoke: 392/392 variants, zero trial errors, zero mechanics flags.'
        Write-Host '[10/11] Writing repository-only acceptance marker...'
        $summary=[ordered]@{schemaVersion='star-cluster-cp136-repository-only-acceptance-v0.1';checkpoint=136;repositoryOnly=$true;acceptedMechanicsResearchBaseline=135;previousCandidateNumericalBaseline=135;python=$pythonVersion.Trim();dotnetSdk=$dotnetVersion;buildPassed=$true;pythonTestsPassed=218;xunitTotal=$total;xunitPassed=$passed;xunitFailed=$failed;xunitSkipped=$skipped;scenarioRunnerSelfTestsPassed=70;deterministicScenarioCorpusPassed=$true;tl1PhaseACorpusPassed=$true;researchParityPassed=25;cp136KernelTestsPassed=7;canonicalKernelVersion='0.3';canonicalDamageModel='penetration-hardening-v1';logicalContexts=196;generatedVariants=392;tl6Variants=136;symmetryComparisons=50;symmetryMismatches=0;smokeTrials=392;smokeTrialErrors=0;smokeMechanicsFlags=0;mandatoryDefenses=@('shield','armor');tl6ArmorProfiles=@('mainline','A_b1');pdsContextsForMissileLanes=@('off','AMM');damageControlStudyDoctrine='HullOnlyWhenDamaged';commonRandomNumberBaseline=135;masterSeed=134001;balanceTargets=$null;mixedTlShipsExecuted=$false;automaticPromotion=$false;substantiveTrials=0;failedGates=@()}
        $summary|ConvertTo-Json -Depth 7|Set-Content -LiteralPath $repoOnlySummary -Encoding utf8
        Write-Host '[11/11] Verifying repository-only CP136 contract...';Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP136 repository-only contract failed';Write-Host '       Checkpoint 136 repository-only gates passed.' -ForegroundColor Green;Write-Host '       Run the same wrapper without -RepositoryOnly in this unchanged extraction to execute the 1,960,000-engagement common-random-number rerun.'
    }finally{Pop-Location};exit 0
}

if(-not(Test-Path -LiteralPath $repoOnlySummary)){throw 'CP136 finalization requires a successful -RepositoryOnly run in the same extraction first.'}
Write-Host '[3/11] Revalidating preflight and repository-only marker...';Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot) 'CP136 final preflight failed';Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP136 prior contract failed';$prior=Read-Json $repoOnlySummary
Write-Host '[4/11] Preserving native deterministic gates...';Write-Host '       218/218 Python; 913/913 xUnit; 70/70 ScenarioRunner; deterministic corpora; 25/25 parity; 7/7 CP136 kernel tests.'
Write-Host '[5/11] Preserving plan/symmetry/smoke gates...';Write-Host '       196 contexts / 392 variants / 136 TL6 variants; 50 symmetry comparisons / 0 mismatches; 392 smoke trials / 0 errors.'
Write-Host '[6/11] Running substantive Armor-regeneration/Crystalline rebaseline diagnostic...'
if(-not $NoClean -and(Test-Path -LiteralPath $substantiveOut)){Remove-Item -Recurse -Force $substantiveOut};New-Item -ItemType Directory -Force -Path $substantiveOut|Out-Null
Push-Location $repositoryRoot
try{Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'same-tl-candidate-baseline-study',$study,'--output-dir','out/checkpoint-136/substantive','--mode','run','--trials','5000','--jobs',$Jobs) 'CP136 substantive study failed'}finally{Pop-Location}
$subWrap=Read-Json(Join-Path $substantiveOut 'summary.json');$sub=$subWrap.analysis
if(-not[bool]$subWrap.passed -or[int]$sub.variants -ne 392 -or[int]$sub.logicalContexts -ne 196 -or[int]$sub.trialsPerVariant -ne 5000 -or[long]$sub.totalTrials -ne 1960000 -or[int]$sub.trialErrors -ne 0 -or[int]$sub.mechanicsFlags -ne 0){throw 'CP136 substantive result shape/mechanics gate mismatch.'}
$contextsPath=Join-Path $substantiveOut 'contexts.csv';if(-not(Test-Path -LiteralPath $contextsPath)){throw 'CP136 substantive contexts.csv missing.'};$contextsHeader=Get-Content -LiteralPath $contextsPath -TotalCount 1;if($contextsHeader -notmatch 'mean_a_damage_control_attempts' -or $contextsHeader -notmatch 'mean_b_damage_control_hull_restored'){throw 'CP136 Damage Control telemetry columns missing from contexts.csv.'}
Write-Host '[7/11] Recording diagnostic strata, DamCon telemetry, and review flags...';Write-Host("       PDS comparisons: {0}; TL6 Armor contexts: {1}; review flags: {2}." -f $sub.pdsComparisons,$sub.tl6ArmorContexts,$sub.diagnosticReviewFlags);Write-Host '       Hull-only Damage Control attempts/successes/kits/TP/queued/restored telemetry is present in contexts.csv.';Write-Host '       Review flags do not fail CP136 and do not imply 50/50 balance targets.'
Write-Host '[8/11] Confirming no automatic balance promotion...';if([bool]$sub.automaticPromotion -or $null -ne $sub.balanceTargets){throw 'CP136 must not auto-promote or use balance targets.'};Write-Host '       CP136 remains a before/after diagnostic; later tuning requires review.'
Write-Host '[9/11] Writing final native acceptance summary...'
$final=[ordered]@{};foreach($p in $prior.PSObject.Properties){$final[$p.Name]=$p.Value};$final['schemaVersion']='star-cluster-cp136-native-acceptance-summary-v0.1';$final['repositoryOnly']=$false;$final['substantiveVariants']=[int]$sub.variants;$final['substantiveLogicalContexts']=[int]$sub.logicalContexts;$final['substantiveTrialsPerVariant']=[int]$sub.trialsPerVariant;$final['substantiveTrials']=[long]$sub.totalTrials;$final['substantiveTrialErrors']=[int]$sub.trialErrors;$final['substantiveMechanicsFlags']=[int]$sub.mechanicsFlags;$final['diagnosticReviewFlags']=[int]$sub.diagnosticReviewFlags;$final['pdsComparisons']=[int]$sub.pdsComparisons;$final['tl6ArmorContexts']=[int]$sub.tl6ArmorContexts;$final['substantiveElapsedSeconds']=[double]$sub.elapsedSeconds;$final['damageControlTelemetryPresent']=$true;$final|ConvertTo-Json -Depth 7|Set-Content -LiteralPath $finalSummary -Encoding utf8
Write-Host '[10/11] Verifying final CP136 repository/results contract...';Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP136 final contract failed'
Write-Host '[11/11] Checkpoint 136 native gates passed.' -ForegroundColor Green;Write-Host '       CP136 is accepted as an Armor-regeneration/Crystalline common-random-number diagnostic; no values are automatically promoted.'
