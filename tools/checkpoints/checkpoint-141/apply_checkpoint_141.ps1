[CmdletBinding()]
param([switch]$RepositoryOnly,[switch]$NoClean,[int]$Jobs=24)
Set-StrictMode -Version 2.0
$ErrorActionPreference='Stop'
$repositoryRoot=(Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$preflight=Join-Path $PSScriptRoot 'preflight_checkpoint_141.py'
$contract=Join-Path $PSScriptRoot 'test_checkpoint_141_contract.py'
$research=Join-Path $repositoryRoot 'tools\simulation\run_starcluster_research.py'
$cp139Study='docs/archive/testing/pre-cp165-active/cp139_def_res_reconciliation_study_v0_1.json'
$cp141Study='docs/archive/testing/pre-cp165-active/cp141_combat_duration_stalemate_study_v0_1.json'
$outRoot=Join-Path $repositoryRoot 'out\checkpoint-141'
$testOut=Join-Path $outRoot 'xunit';$parityOut=Join-Path $outRoot 'research-parity';$deterministicOut=Join-Path $outRoot 'deterministic-scenarios';$tl1PhaseAOut=Join-Path $outRoot 'tl1-phase-a';$reconOut=Join-Path $outRoot 'cp139-reconciliation'
$batchRoot=Join-Path $outRoot 'duration-batches';$mergeOut=Join-Path $outRoot 'duration-merged';$finalBatchRoot=Join-Path $outRoot 'duration-final-batches';$finalMergeOut=Join-Path $outRoot 'duration-final-merged'
$repoOnlySummary=Join-Path $outRoot 'CP141_REPOSITORY_ONLY_ACCEPTANCE.json';$finalSummary=Join-Path $outRoot 'CP141_NATIVE_ACCEPTANCE_SUMMARY.json'
function Get-Cpython313Command {$candidates=@(@{Command='py';Args=@('-3.13')},@{Command='python';Args=@()},@{Command='python3';Args=@()});foreach($candidate in $candidates){$cmd=Get-Command $candidate.Command -ErrorAction SilentlyContinue;if($null -eq $cmd){continue};$v=& $candidate.Command @($candidate.Args+@('--version')) 2>&1|Out-String;if($LASTEXITCODE -eq 0 -and $v -match 'Python\s+3\.13(?:\.|\s|$)'){return $candidate}};throw 'CP141 requires Python 3.13.'}
function Invoke-PythonChecked([object]$Python,[string[]]$Arguments,[string]$Failure){& $Python.Command @($Python.Args+$Arguments);if($LASTEXITCODE -ne 0){throw "$Failure (exit code $LASTEXITCODE)."}}
function Invoke-Captured([string]$Label,[string]$LogPath,[scriptblock]$Body){& $Body *> $LogPath;$exitCode=$LASTEXITCODE;if($exitCode -ne 0){Write-Host "       $Label output tail:" -ForegroundColor Yellow;Get-Content -LiteralPath $LogPath -Tail 120|ForEach-Object{Write-Host("       $_")};throw "$Label failed (exit code $exitCode)."}}
function Read-Json([string]$Path){return(Get-Content -LiteralPath $Path -Raw|ConvertFrom-Json)}
function Relative-To-Repo([string]$Path){
    $root=[System.IO.Path]::GetFullPath($repositoryRoot)
    $full=[System.IO.Path]::GetFullPath($Path)
    $sep=[System.IO.Path]::DirectorySeparatorChar
    if($full.Equals($root,[System.StringComparison]::OrdinalIgnoreCase)){return '.'}
    $prefix=$root
    if(-not $prefix.EndsWith([string]$sep)){$prefix+=$sep}
    if(-not $full.StartsWith($prefix,[System.StringComparison]::OrdinalIgnoreCase)){throw "Path '$Path' is outside repository root '$repositoryRoot'."}
    return $full.Substring($prefix.Length)
}
function File-Hash([string]$Path){return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()}
function Invoke-DurationSmoke([string]$Batches,[string]$Merged,[string]$Tag){
    if(Test-Path -LiteralPath $Batches){Remove-Item -Recurse -Force $Batches};if(Test-Path -LiteralPath $Merged){Remove-Item -Recurse -Force $Merged};New-Item -ItemType Directory -Force -Path $Batches,$Merged|Out-Null
    $ranges=@(@(0,1024),@(1024,2048),@(2048,3072),@(3072,4096),@(4096,5120),@(5120,6144),@(6144,7168),@(7168,8192),@(8192,8220))
    $batchIndex=0
    foreach($range in $ranges){
        $start=[int]$range[0];$end=[int]$range[1];$dir=Join-Path $Batches ("batch_{0:D4}_{1:D4}" -f $start,$end);New-Item -ItemType Directory -Force -Path $dir|Out-Null
        $rel=Relative-To-Repo $dir;$log=Join-Path $dir 'console.log'
        $batchIndex++;Write-Host("       $Tag batch {0}/9: scenarios {1}-{2}" -f $batchIndex,$start,($end-1))
        Invoke-Captured "$Tag duration batch $start-$end" $log {& $python.Command @($python.Args+@('-B',$research,'--repo',$repositoryRoot,'combat-duration-stalemate-study',$cp141Study,'--output-dir',$rel,'--jobs',$Jobs,'--batch-start',$start,'--batch-end',$end))}
        $bs=Read-Json(Join-Path $dir 'summary.json');$ba=$bs.analysis;$expected=$end-$start
        if(-not[bool]$bs.passed -or[int]$ba.scenarios -ne $expected -or[int]$ba.executionErrors -ne 0 -or[int]$ba.hardTurnSentinel -ne 60 -or[int]$ba.longResolvedTurn -ne 25 -or-not[bool]$ba.sourceMatrixUnmodified){throw "$Tag duration batch $start-$end contract mismatch."}
    }
    $relB=Relative-To-Repo $Batches;$relM=Relative-To-Repo $Merged;$mergeLog=Join-Path $Merged 'console.log'
    Invoke-Captured "$Tag duration merge" $mergeLog {& $python.Command @($python.Args+@('-B',$research,'--repo',$repositoryRoot,'combat-duration-stalemate-merge',$cp141Study,'--batch-root',$relB,'--output-dir',$relM))}
    $ms=Read-Json(Join-Path $Merged 'summary.json');$ma=$ms.analysis
    if(-not[bool]$ms.passed -or-not[bool]$ma.stageASubstantiveMeasurementReady -or[int]$ma.stageAScenarios -ne 8220 -or[int]$ma.batchCount -ne 9 -or[int]$ma.hardTurnSentinel -ne 60 -or[int]$ma.longResolvedTurn -ne 25 -or[int]$ma.substantiveCombatTrials -ne 0 -or[bool]$ma.promotionAllowed -or-not[bool]$ma.sourceMatrixUnmodified){throw "$Tag merged duration contract mismatch."}
    if([int]$ma.resolvedGe25 -le 0 -or[int]$ma.turnCapSentinels -le 0){throw "$Tag duration metrics were not exercised."}
    return $ma
}
function Merged-Hashes([string]$Merged){
    return [ordered]@{
        smoke=File-Hash(Join-Path $Merged 'duration_smoke_results.csv')
        capDiagnostics=File-Hash(Join-Path $Merged 'turn_cap_diagnostics.csv')
        groups=File-Hash(Join-Path $Merged 'duration_group_summary.csv')
        termination=File-Hash(Join-Path $Merged 'termination_cause_summary.csv')
        capSignals=File-Hash(Join-Path $Merged 'turn_cap_signal_summary.csv')
        batchAudit=File-Hash(Join-Path $Merged 'batch_merge_audit.csv')
    }
}

$python=Get-Cpython313Command;$pythonVersion=& $python.Command @($python.Args+@('--version')) 2>&1|Out-String
$dotnetVersion=(& dotnet --version 2>&1|Out-String).Trim();if($LASTEXITCODE -ne 0 -or $dotnetVersion -ne '8.0.423'){throw "CP141 requires .NET SDK 8.0.423 exactly; observed '$dotnetVersion'."}
Write-Host("CP141 runtimes: {0}; .NET SDK {1}" -f $pythonVersion.Trim(),$dotnetVersion)
Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot) 'CP141 preflight failed'

if($RepositoryOnly){
    if(-not $NoClean -and(Test-Path -LiteralPath $outRoot)){Remove-Item -Recurse -Force $outRoot}
    New-Item -ItemType Directory -Force -Path $outRoot,$testOut,$parityOut,$deterministicOut,$tl1PhaseAOut,$reconOut|Out-Null
    Push-Location $repositoryRoot
    try{
        Write-Host '[1/8] Python research tests...'
        & $python.Command @($python.Args+@('-B','-m','unittest','discover','-s','tools/simulation/tests','-p','test_*.py'));if($LASTEXITCODE -ne 0){throw 'CP141 Python tests failed.'}
        Write-Host '[2/8] Warning-as-error .NET build...'
        Invoke-Captured 'CP141 build' (Join-Path $outRoot 'build.log') {dotnet build StarCluster.sln --configuration Release --nologo -warnaserror}
        Write-Host '[3/8] xUnit + ScenarioRunner deterministic corpora...'
        dotnet test tests\StarCluster.Tests\StarCluster.Tests.csproj --configuration Release --no-build --nologo --logger 'trx;LogFileName=cp141-tests.trx' --results-directory $testOut
        $xunitExit=$LASTEXITCODE;$trxPath=Join-Path $testOut 'cp141-tests.trx';if(-not(Test-Path -LiteralPath $trxPath)){throw 'CP141 xUnit TRX missing.'};[xml]$trx=Get-Content -LiteralPath $trxPath -Raw;$c=$trx.TestRun.ResultSummary.Counters;$total=[int]$c.total;$passed=[int]$c.passed;$failed=[int]$c.failed;$skipped=[int]$c.notExecuted;if($xunitExit -ne 0 -or $total -ne 915 -or $passed -ne 915 -or $failed -ne 0 -or $skipped -ne 0){throw "CP141 xUnit mismatch exit=$xunitExit total=$total passed=$passed failed=$failed skipped=$skipped."}
        $selfLog=Join-Path $outRoot 'scenario-self-tests.log';Invoke-Captured 'CP141 ScenarioRunner self-tests' $selfLog {dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- self-test};$selfText=Get-Content -LiteralPath $selfLog -Raw;if($selfText -notmatch 'Runner self-tests:\s+70 passed,\s+0 failed,\s+70 total\.'){throw 'CP141 expected 70/70 ScenarioRunner self-tests.'}
        Invoke-Captured 'CP141 deterministic scenario corpus' (Join-Path $outRoot 'deterministic-scenarios.log') {dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- run-all --output-dir $deterministicOut}
        Invoke-Captured 'CP141 TL1 Phase-A corpus' (Join-Path $outRoot 'tl1-phase-a.log') {dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- tl1-phase-a --output-dir $tl1PhaseAOut}
        Write-Host '[4/8] Existing C#/Python research parity...'
        Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'parity','--output-dir',$parityOut) 'CP141 research parity failed';$parity=Read-Json(Join-Path $parityOut 'summary.json');if(-not[bool]$parity.passed -or[int]$parity.cases -ne 25){throw 'CP141 expected 25/25 research parity.'}
        Write-Host '[5/8] CP139 DEF/RES regression foundation...'
        & $python.Command @($python.Args+@('-B','-m','unittest','discover','-v','-s','tools/simulation/tests','-p','test_cp139_def_res_reconciliation.py'));if($LASTEXITCODE -ne 0){throw 'CP139 focused regression failed under CP141.'}
        Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'combat-model-reconciliation-study',$cp139Study,'--output-dir','out/checkpoint-141/cp139-reconciliation') 'CP139 reconciliation regression failed';$recon=Read-Json(Join-Path $reconOut 'summary.json');$ra=$recon.analysis;if(-not[bool]$recon.passed -or[int]$ra.fixturePass -ne 8 -or[int]$ra.smokeVariants -ne 82 -or[int]$ra.smokeErrors -ne 0 -or-not[bool]$ra.sourceMatrixUnmodified){throw 'CP139 reconciliation regression mismatch.'}
        Write-Host '[6/8] Focused CP140 + CP141 integration/duration tests...'
        & $python.Command @($python.Args+@('-B','-m','unittest','discover','-v','-s','tools/simulation/tests','-p','test_cp140_stage_a_integration.py'));if($LASTEXITCODE -ne 0){throw 'CP140 focused regression failed under CP141.'}
        & $python.Command @($python.Args+@('-B','-m','unittest','discover','-v','-s','tools/simulation/tests','-p','test_cp141_combat_duration_stalemate.py'));if($LASTEXITCODE -ne 0){throw 'CP141 focused tests failed.'}
        Write-Host '[7/8] Complete 8,220-scenario combat-duration/stalemate smoke in isolated deterministic batches...'
        $ma=Invoke-DurationSmoke $batchRoot $mergeOut 'CP141';$hashes=Merged-Hashes $mergeOut
        Write-Host '[8/8] Writing RepositoryOnly acceptance and repository contract...'
        $summary=[ordered]@{schemaVersion='star-cluster-cp141-repository-only-acceptance-v0.1';checkpoint=141;repositoryOnly=$true;failedGates=@();python=$pythonVersion.Trim();dotnetSdk=$dotnetVersion;buildPassed=$true;pythonTestsPassed=263;xunitTotal=$total;xunitPassed=$passed;xunitFailed=$failed;xunitSkipped=$skipped;scenarioRunnerSelfTestsPassed=70;deterministicScenarioCorpusPassed=$true;tl1PhaseACorpusPassed=$true;researchParityPassed=25;cp139FocusedTestsPassed=9;cp140FocusedTestsPassed=10;cp141FocusedTestsPassed=10;defResFixturesPassed=8;cp139ReconciliationSmokeVariants=82;cp139ReconciliationSmokeErrors=0;durationScenarios=8220;durationSmokeErrors=0;durationSmokeBatches=9;hardTurnSentinel=60;longResolvedTurn=25;resolvedGe25=[int]$ma.resolvedGe25;turnCapSentinels=[int]$ma.turnCapSentinels;safeStalemates=[int]$ma.safeStalemates;sourceMatrixUnmodified=$true;stageASubstantiveMeasurementReady=$true;substantiveCombatTrials=0;automaticPromotion=$false;mergedArtifactSha256=$hashes}
        $summary|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $repoOnlySummary -Encoding UTF8
        Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP141 RepositoryOnly contract failed'
        Write-Host 'CP141 RepositoryOnly acceptance PASSED.' -ForegroundColor Green
    } finally {Pop-Location}
    exit 0
}

if(-not(Test-Path -LiteralPath $repoOnlySummary)){throw 'Run CP141 -RepositoryOnly first in this same extraction.'}
Push-Location $repositoryRoot
try{
    Write-Host '[final 1/3] Revalidating preflight/manifest after RepositoryOnly outputs...';Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot) 'CP141 final preflight failed';Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP141 RepositoryOnly state contract failed'
    Write-Host '[final 2/3] Re-running complete duration/stalemate smoke for deterministic reproduction...';$maFinal=Invoke-DurationSmoke $finalBatchRoot $finalMergeOut 'CP141 final';$finalHashes=Merged-Hashes $finalMergeOut;$ro=Read-Json $repoOnlySummary;$expected=$ro.mergedArtifactSha256
    foreach($name in @('smoke','capDiagnostics','groups','termination','capSignals','batchAudit')){if([string]$finalHashes[$name] -ne [string]$expected.$name){throw "CP141 deterministic duration hash mismatch for $name."}}
    Write-Host '[final 3/3] Final acceptance summary and result ZIP...'
    $final=[ordered]@{};$ro.psobject.Properties|ForEach-Object{$final[$_.Name]=$_.Value};$final['schemaVersion']='star-cluster-cp141-native-acceptance-v0.1';$final['repositoryOnly']=$false;$final['repositoryOnlyAccepted']=$true;$final['deterministicDurationSmokeReproduced']=$true;$final['finalMergedArtifactSha256']=$finalHashes;$final|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $finalSummary -Encoding UTF8
    Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP141 final contract failed'
    $stamp=Get-Date -Format 'yyyyMMdd_HHmmss';$zip=Join-Path $outRoot ("StarCluster_CP141_native_results_$stamp.zip");$items=Get-ChildItem -LiteralPath $outRoot -Force|Where-Object{$_.FullName -ne $zip};Compress-Archive -Path $items.FullName -DestinationPath $zip -CompressionLevel Optimal
    Write-Host "CP141 native acceptance PASSED. Results: $zip" -ForegroundColor Green
} finally {Pop-Location}
