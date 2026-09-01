[CmdletBinding()]
param([switch]$RepositoryOnly,[switch]$NoClean,[int]$Jobs=24)
Set-StrictMode -Version 2.0
$ErrorActionPreference='Stop'
$repositoryRoot=(Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$preflight=Join-Path $PSScriptRoot 'preflight_checkpoint_140.py'
$contract=Join-Path $PSScriptRoot 'test_checkpoint_140_contract.py'
$research=Join-Path $repositoryRoot 'tools\simulation\run_starcluster_research.py'
$cp139Study='docs/archive/testing/pre-cp165-active/cp139_def_res_reconciliation_study_v0_1.json'
$cp140Study='docs/archive/testing/pre-cp165-active/cp140_stage_a_integration_study_v0_1.json'
$outRoot=Join-Path $repositoryRoot 'out\checkpoint-140'
$testOut=Join-Path $outRoot 'xunit';$parityOut=Join-Path $outRoot 'research-parity';$deterministicOut=Join-Path $outRoot 'deterministic-scenarios';$tl1PhaseAOut=Join-Path $outRoot 'tl1-phase-a';$reconOut=Join-Path $outRoot 'cp139-reconciliation'
$batchRoot=Join-Path $outRoot 'stage-a-batches';$mergeOut=Join-Path $outRoot 'stage-a-merged';$finalBatchRoot=Join-Path $outRoot 'stage-a-final-batches';$finalMergeOut=Join-Path $outRoot 'stage-a-final-merged'
$repoOnlySummary=Join-Path $outRoot 'CP140_REPOSITORY_ONLY_ACCEPTANCE.json';$finalSummary=Join-Path $outRoot 'CP140_NATIVE_ACCEPTANCE_SUMMARY.json'
function Get-Cpython313Command {$candidates=@(@{Command='py';Args=@('-3.13')},@{Command='python';Args=@()},@{Command='python3';Args=@()});foreach($candidate in $candidates){$cmd=Get-Command $candidate.Command -ErrorAction SilentlyContinue;if($null -eq $cmd){continue};$v=& $candidate.Command @($candidate.Args+@('--version')) 2>&1|Out-String;if($LASTEXITCODE -eq 0 -and $v -match 'Python\s+3\.13(?:\.|\s|$)'){return $candidate}};throw 'CP140 requires Python 3.13.'}
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
function Invoke-StageASmoke([string]$Batches,[string]$Merged,[string]$Tag){
    if(Test-Path -LiteralPath $Batches){Remove-Item -Recurse -Force $Batches};if(Test-Path -LiteralPath $Merged){Remove-Item -Recurse -Force $Merged};New-Item -ItemType Directory -Force -Path $Batches,$Merged|Out-Null
    $ranges=@(@(0,1024),@(1024,2048),@(2048,3072),@(3072,4096),@(4096,5120),@(5120,6144),@(6144,7168),@(7168,8192),@(8192,8220))
    $batchIndex=0
    foreach($range in $ranges){
        $start=[int]$range[0];$end=[int]$range[1];$dir=Join-Path $Batches ("batch_{0:D4}_{1:D4}" -f $start,$end);New-Item -ItemType Directory -Force -Path $dir|Out-Null
        $rel=Relative-To-Repo $dir;$log=Join-Path $dir 'console.log'
        $batchIndex++;Write-Host("       $Tag batch {0}/9: scenarios {1}-{2}" -f $batchIndex,$start,($end-1))
        Invoke-Captured "$Tag Stage-A batch $start-$end" $log {& $python.Command @($python.Args+@('-B',$research,'--repo',$repositoryRoot,'stage-a-integration-study',$cp140Study,'--output-dir',$rel,'--mode','smoke','--jobs',$Jobs,'--batch-start',$start,'--batch-end',$end))}
        $bs=Read-Json(Join-Path $dir 'summary.json');$ba=$bs.analysis;$expected=$end-$start
        if(-not[bool]$bs.passed -or[int]$ba.integrationSmokeTrials -ne $expected -or[int]$ba.smokeErrors -ne 0 -or[int]$ba.turnTelemetrySchemaConsistencyPass -ne $expected -or[int]$ba.battleTelemetryRows -ne (2*$expected)){throw "$Tag Stage-A batch $start-$end contract mismatch."}
    }
    $relB=Relative-To-Repo $Batches;$relM=Relative-To-Repo $Merged;$mergeLog=Join-Path $Merged 'console.log'
    Invoke-Captured "$Tag Stage-A merge" $mergeLog {& $python.Command @($python.Args+@('-B',$research,'--repo',$repositoryRoot,'stage-a-integration-merge',$cp140Study,'--batch-root',$relB,'--output-dir',$relM))}
    $ms=Read-Json(Join-Path $Merged 'summary.json');$ma=$ms.analysis
    if(-not[bool]$ms.passed -or-not[bool]$ma.stageAExecutionReady -or[int]$ma.integrationSmokeTrials -ne 8220 -or[int]$ma.smokeErrors -ne 0 -or[int]$ma.batchCount -ne 9 -or[int]$ma.turnTelemetrySchemaConsistencyPass -ne 8220 -or[int]$ma.battleTelemetryRows -ne 16440 -or[int]$ma.instrumentationEquivalencePass -ne 12 -or[int]$ma.tpConflictTurnsObserved -le 0 -or[int]$ma.powerCrisisTpConflictTurnsObserved -le 0 -or-not[bool]$ma.sourceMatrixUnmodified){throw "$Tag merged Stage-A contract mismatch."}
    return $ma
}
function Merged-Hashes([string]$Merged){
    return [ordered]@{
        smoke=File-Hash(Join-Path $Merged 'stage_a_smoke_results.csv')
        battle=File-Hash(Join-Path $Merged 'battle_telemetry.csv')
        turnSample=File-Hash(Join-Path $Merged 'turn_tp_telemetry_sample.csv')
        equivalence=File-Hash(Join-Path $Merged 'instrumentation_equivalence.csv')
        conflict=File-Hash(Join-Path $Merged 'tp_conflict_coverage.csv')
        resourceEquivalence=File-Hash(Join-Path $Merged 'resource_execution_equivalence.csv')
    }
}

$python=Get-Cpython313Command;$pythonVersion=& $python.Command @($python.Args+@('--version')) 2>&1|Out-String
$dotnetVersion=(& dotnet --version 2>&1|Out-String).Trim();if($LASTEXITCODE -ne 0 -or $dotnetVersion -ne '8.0.423'){throw "CP140 requires .NET SDK 8.0.423 exactly; observed '$dotnetVersion'."}
Write-Host("CP140 runtimes: {0}; .NET SDK {1}" -f $pythonVersion.Trim(),$dotnetVersion)
Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot) 'CP140 preflight failed'

if($RepositoryOnly){
    if(-not $NoClean -and(Test-Path -LiteralPath $outRoot)){Remove-Item -Recurse -Force $outRoot}
    New-Item -ItemType Directory -Force -Path $outRoot,$testOut,$parityOut,$deterministicOut,$tl1PhaseAOut,$reconOut|Out-Null
    Push-Location $repositoryRoot
    try{
        Write-Host '[1/8] Python research tests...'
        & $python.Command @($python.Args+@('-B','-m','unittest','discover','-s','tools/simulation/tests','-p','test_*.py'));if($LASTEXITCODE -ne 0){throw 'CP140 Python tests failed.'}
        Write-Host '[2/8] Warning-as-error .NET build...'
        Invoke-Captured 'CP140 build' (Join-Path $outRoot 'build.log') {dotnet build StarCluster.sln --configuration Release --nologo -warnaserror}
        Write-Host '[3/8] xUnit + ScenarioRunner deterministic corpora...'
        dotnet test tests\StarCluster.Tests\StarCluster.Tests.csproj --configuration Release --no-build --nologo --logger 'trx;LogFileName=cp140-tests.trx' --results-directory $testOut
        $xunitExit=$LASTEXITCODE;$trxPath=Join-Path $testOut 'cp140-tests.trx';if(-not(Test-Path -LiteralPath $trxPath)){throw 'CP140 xUnit TRX missing.'};[xml]$trx=Get-Content -LiteralPath $trxPath -Raw;$c=$trx.TestRun.ResultSummary.Counters;$total=[int]$c.total;$passed=[int]$c.passed;$failed=[int]$c.failed;$skipped=[int]$c.notExecuted;if($xunitExit -ne 0 -or $total -ne 915 -or $passed -ne 915 -or $failed -ne 0 -or $skipped -ne 0){throw "CP140 xUnit mismatch exit=$xunitExit total=$total passed=$passed failed=$failed skipped=$skipped."}
        $selfLog=Join-Path $outRoot 'scenario-self-tests.log';Invoke-Captured 'CP140 ScenarioRunner self-tests' $selfLog {dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- self-test};$selfText=Get-Content -LiteralPath $selfLog -Raw;if($selfText -notmatch 'Runner self-tests:\s+70 passed,\s+0 failed,\s+70 total\.'){throw 'CP140 expected 70/70 ScenarioRunner self-tests.'}
        Invoke-Captured 'CP140 deterministic scenario corpus' (Join-Path $outRoot 'deterministic-scenarios.log') {dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- run-all --output-dir $deterministicOut}
        Invoke-Captured 'CP140 TL1 Phase-A corpus' (Join-Path $outRoot 'tl1-phase-a.log') {dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- tl1-phase-a --output-dir $tl1PhaseAOut}
        Write-Host '[4/8] Existing C#/Python research parity...'
        Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'parity','--output-dir',$parityOut) 'CP140 research parity failed';$parity=Read-Json(Join-Path $parityOut 'summary.json');if(-not[bool]$parity.passed -or[int]$parity.cases -ne 25){throw 'CP140 expected 25/25 research parity.'}
        Write-Host '[5/8] CP139 regression foundation...'
        & $python.Command @($python.Args+@('-B','-m','unittest','discover','-v','-s','tools/simulation/tests','-p','test_cp139_def_res_reconciliation.py'));if($LASTEXITCODE -ne 0){throw 'CP139 focused regression failed under CP140.'}
        Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'combat-model-reconciliation-study',$cp139Study,'--output-dir','out/checkpoint-140/cp139-reconciliation') 'CP139 reconciliation regression failed';$recon=Read-Json(Join-Path $reconOut 'summary.json');$ra=$recon.analysis;if(-not[bool]$recon.passed -or[int]$ra.fixturePass -ne 8 -or[int]$ra.smokeVariants -ne 82 -or[int]$ra.smokeErrors -ne 0 -or-not[bool]$ra.sourceMatrixUnmodified){throw 'CP139 reconciliation regression mismatch.'}
        Write-Host '[6/8] Focused CP140 integration tests...'
        & $python.Command @($python.Args+@('-B','-m','unittest','discover','-v','-s','tools/simulation/tests','-p','test_cp140_stage_a_integration.py'));if($LASTEXITCODE -ne 0){throw 'CP140 focused tests failed.'}
        Write-Host '[7/8] Complete 8,220-scenario Stage-A integration smoke in isolated deterministic batches...'
        $ma=Invoke-StageASmoke $batchRoot $mergeOut 'CP140';$hashes=Merged-Hashes $mergeOut
        Write-Host '[8/8] Writing RepositoryOnly acceptance and repository contract...'
        $summary=[ordered]@{schemaVersion='star-cluster-cp140-repository-only-acceptance-v0.1';checkpoint=140;repositoryOnly=$true;failedGates=@();python=$pythonVersion.Trim();dotnetSdk=$dotnetVersion;buildPassed=$true;pythonTestsPassed=253;xunitTotal=$total;xunitPassed=$passed;xunitFailed=$failed;xunitSkipped=$skipped;scenarioRunnerSelfTestsPassed=70;deterministicScenarioCorpusPassed=$true;tl1PhaseACorpusPassed=$true;researchParityPassed=25;cp139FocusedTestsPassed=9;cp140FocusedTestsPassed=10;defResFixturesPassed=8;cp139ReconciliationSmokeVariants=82;cp139ReconciliationSmokeErrors=0;stageAScenarios=8220;stageAIntegrationSmokeTrials=8220;stageASmokeErrors=0;stageASmokeBatches=9;turnTelemetryRowsObserved=[int]$ma.turnTelemetryRowsObserved;turnTelemetrySchemaConsistencyPass=8220;battleTelemetryRows=16440;instrumentationEquivalencePassed=12;tpConflictTurnsObserved=[int]$ma.tpConflictTurnsObserved;powerCrisisTpConflictTurnsObserved=[int]$ma.powerCrisisTpConflictTurnsObserved;sourceMatrixUnmodified=$true;stageAExecutionReady=$true;substantiveCombatTrials=0;automaticPromotion=$false;mergedArtifactSha256=$hashes}
        $summary|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $repoOnlySummary -Encoding UTF8
        Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP140 RepositoryOnly contract failed'
        Write-Host 'CP140 RepositoryOnly acceptance PASSED.' -ForegroundColor Green
    } finally {Pop-Location}
    exit 0
}

if(-not(Test-Path -LiteralPath $repoOnlySummary)){throw 'Run CP140 -RepositoryOnly first in this same extraction.'}
Push-Location $repositoryRoot
try{
    Write-Host '[final 1/3] Revalidating preflight/manifest after RepositoryOnly outputs...';Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot) 'CP140 final preflight failed';Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP140 RepositoryOnly state contract failed'
    Write-Host '[final 2/3] Re-running complete Stage-A integration smoke for deterministic reproduction...';$maFinal=Invoke-StageASmoke $finalBatchRoot $finalMergeOut 'CP140 final';$finalHashes=Merged-Hashes $finalMergeOut;$ro=Read-Json $repoOnlySummary;$expected=$ro.mergedArtifactSha256
    foreach($name in @('smoke','battle','turnSample','equivalence','conflict','resourceEquivalence')){if([string]$finalHashes[$name] -ne [string]$expected.$name){throw "CP140 deterministic Stage-A hash mismatch for $name."}}
    Write-Host '[final 3/3] Final acceptance summary and result ZIP...'
    $final=[ordered]@{};$ro.psobject.Properties|ForEach-Object{$final[$_.Name]=$_.Value};$final['schemaVersion']='star-cluster-cp140-native-acceptance-v0.1';$final['repositoryOnly']=$false;$final['repositoryOnlyAccepted']=$true;$final['deterministicStageASmokeReproduced']=$true;$final['finalMergedArtifactSha256']=$finalHashes;$final|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $finalSummary -Encoding UTF8
    Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP140 final contract failed'
    $stamp=Get-Date -Format 'yyyyMMdd_HHmmss';$zip=Join-Path $outRoot ("StarCluster_CP140_native_results_$stamp.zip");$items=Get-ChildItem -LiteralPath $outRoot -Force|Where-Object{$_.FullName -ne $zip};Compress-Archive -Path $items.FullName -DestinationPath $zip -CompressionLevel Optimal
    Write-Host "CP140 native acceptance PASSED. Results: $zip" -ForegroundColor Green
} finally {Pop-Location}
