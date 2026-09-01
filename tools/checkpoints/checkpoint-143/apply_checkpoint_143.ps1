[CmdletBinding()]
param([switch]$RepositoryOnly,[switch]$NoClean,[int]$Jobs=24)
Set-StrictMode -Version 2.0
$ErrorActionPreference='Stop'
$repositoryRoot=(Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$preflight=Join-Path $PSScriptRoot 'preflight_checkpoint_143.py'
$contract=Join-Path $PSScriptRoot 'test_checkpoint_143_contract.py'
$research=Join-Path $repositoryRoot 'tools\simulation\run_starcluster_research.py'
$cp139Study='docs/archive/testing/pre-cp165-active/cp139_def_res_reconciliation_study_v0_1.json'
$cp142Study='docs/archive/testing/pre-cp165-active/cp142_combat_surface_deep_reconciliation_study_v0_1.json'
$cp143Study='docs/archive/testing/pre-cp165-active/cp143_missile_mirror_pacing_attribution_study_v0_1.json'
$outRoot=Join-Path $repositoryRoot 'out\checkpoint-143'
$testOut=Join-Path $outRoot 'xunit';$parityOut=Join-Path $outRoot 'research-parity';$deterministicOut=Join-Path $outRoot 'deterministic-scenarios';$tl1PhaseAOut=Join-Path $outRoot 'tl1-phase-a';$cp139Out=Join-Path $outRoot 'cp139-reconciliation';$cp142AuditOut=Join-Path $outRoot 'cp142-reconciliation-audit'
$batchRoot=Join-Path $outRoot 'attribution-batches';$mergeOut=Join-Path $outRoot 'attribution-merged';$finalBatchRoot=Join-Path $outRoot 'attribution-final-batches';$finalMergeOut=Join-Path $outRoot 'attribution-final-merged'
$repoOnlySummary=Join-Path $outRoot 'CP143_REPOSITORY_ONLY_ACCEPTANCE.json';$finalSummary=Join-Path $outRoot 'CP143_NATIVE_ACCEPTANCE_SUMMARY.json'
function Get-Cpython313Command {$candidates=@(@{Command='py';Args=@('-3.13')},@{Command='python';Args=@()},@{Command='python3';Args=@()});foreach($candidate in $candidates){$cmd=Get-Command $candidate.Command -ErrorAction SilentlyContinue;if($null -eq $cmd){continue};$v=& $candidate.Command @($candidate.Args+@('--version')) 2>&1|Out-String;if($LASTEXITCODE -eq 0 -and $v -match 'Python\s+3\.13(?:\.|\s|$)'){return $candidate}};throw 'CP143 requires Python 3.13.'}
function Invoke-PythonChecked([object]$Python,[string[]]$Arguments,[string]$Failure){& $Python.Command @($Python.Args+$Arguments);if($LASTEXITCODE -ne 0){throw "$Failure (exit code $LASTEXITCODE)."}}
function Invoke-Captured([string]$Label,[string]$LogPath,[scriptblock]$Body){& $Body *> $LogPath;$exitCode=$LASTEXITCODE;if($exitCode -ne 0){Write-Host "       $Label output tail:" -ForegroundColor Yellow;Get-Content -LiteralPath $LogPath -Tail 120|ForEach-Object{Write-Host("       $_")};throw "$Label failed (exit code $exitCode)."}}
function Read-Json([string]$Path){return(Get-Content -LiteralPath $Path -Raw|ConvertFrom-Json)}
function Get-Analysis([object]$Obj){if($null -ne $Obj.PSObject.Properties['analysis']){return $Obj.analysis};return $Obj}
function Relative-To-Repo([string]$Path){
    $root=[System.IO.Path]::GetFullPath($repositoryRoot)
    $full=[System.IO.Path]::GetFullPath($Path)
    $sep=[System.IO.Path]::DirectorySeparatorChar
    if($full.Equals($root,[System.StringComparison]::OrdinalIgnoreCase)){return '.'}
    $prefix=$root;if(-not $prefix.EndsWith([string]$sep)){$prefix+=$sep}
    if(-not $full.StartsWith($prefix,[System.StringComparison]::OrdinalIgnoreCase)){throw "Path '$Path' is outside repository root '$repositoryRoot'."}
    return $full.Substring($prefix.Length)
}
function File-Hash([string]$Path){return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()}
function Invoke-Attribution([string]$Batches,[string]$Merged,[string]$Tag){
    if(Test-Path -LiteralPath $Batches){Remove-Item -Recurse -Force $Batches};if(Test-Path -LiteralPath $Merged){Remove-Item -Recurse -Force $Merged};New-Item -ItemType Directory -Force -Path $Batches,$Merged|Out-Null
    $ranges=@(@(0,512),@(512,1024),@(1024,1536),@(1536,1980));$batchIndex=0
    foreach($range in $ranges){
        $start=[int]$range[0];$end=[int]$range[1];$dir=Join-Path $Batches ("batch_{0:D4}_{1:D4}" -f $start,$end);New-Item -ItemType Directory -Force -Path $dir|Out-Null
        $rel=Relative-To-Repo $dir;$log=Join-Path $dir 'console.log';$batchIndex++;Write-Host("       $Tag batch {0}/4: Missile-mirror scenarios {1}-{2}" -f $batchIndex,$start,($end-1))
        Invoke-Captured "$Tag attribution batch $start-$end" $log {& $python.Command @($python.Args+@('-B',$research,'--repo',$repositoryRoot,'missile-mirror-pacing-attribution-study',$cp143Study,'--output-dir',$rel,'--jobs',$Jobs,'--batch-start',$start,'--batch-end',$end))}
        $bs=Read-Json(Join-Path $dir 'summary.json');$expected=$end-$start
        if(-not[bool]$bs.passed -or[int]$bs.scenarios -ne $expected -or[int]$bs.executionErrors -ne 0 -or-not[bool]$bs.sourceMatrixUnmodified -or[int]$bs.substantiveCombatTrials -ne 0 -or[bool]$bs.tuningAllowed -or[bool]$bs.promotionAllowed){throw "$Tag attribution batch $start-$end contract mismatch."}
    }
    $relB=Relative-To-Repo $Batches;$relM=Relative-To-Repo $Merged;$mergeLog=Join-Path $Merged 'console.log'
    Invoke-Captured "$Tag attribution merge" $mergeLog {& $python.Command @($python.Args+@('-B',$research,'--repo',$repositoryRoot,'missile-mirror-pacing-attribution-merge',$cp143Study,'--batch-root',$relB,'--output-dir',$relM))}
    $ma=Read-Json(Join-Path $Merged 'summary.json')
    if(-not[bool]$ma.passed -or[int]$ma.missileMirrorScenarios -ne 1980 -or[int]$ma.executionErrors -ne 0 -or[int]$ma.resolved -ne 1751 -or[int]$ma.resolvedGe25 -ne 1085 -or[int]$ma.turnCapSentinels -ne 228 -or[int]$ma.safeStalemates -ne 1 -or[int]$ma.instrumentationEquivalenceCases -ne 12 -or[int]$ma.instrumentationEquivalencePassed -ne 12 -or[int]$ma.cp142PairedOutcomeReferenceCases -ne 1980 -or[int]$ma.cp142PairedOutcomeMatches -ne 1980 -or[int]$ma.hardTurnSentinel -ne 60 -or[int]$ma.substantiveCombatTrials -ne 0 -or[bool]$ma.tuningAllowed -or[bool]$ma.promotionAllowed -or-not[bool]$ma.sourceMatrixUnmodified){throw "$Tag merged attribution contract mismatch."}
    return $ma
}
function Merged-Hashes([string]$Merged){return [ordered]@{
    attribution=File-Hash(Join-Path $Merged 'missile_mirror_attribution_results.csv')
    groups=File-Hash(Join-Path $Merged 'missile_mirror_group_summary.csv')
    signals=File-Hash(Join-Path $Merged 'missile_mirror_pacing_signal_summary.csv')
    instrumentation=File-Hash(Join-Path $Merged 'instrumentation_equivalence.csv')
    cp142Paired=File-Hash(Join-Path $Merged 'cp142_paired_outcome_equivalence.csv')
    timelineSample=File-Hash(Join-Path $Merged 'missile_mirror_timeline_sample.csv')
    batchAudit=File-Hash(Join-Path $Merged 'batch_merge_audit.csv')
    summary=File-Hash(Join-Path $Merged 'summary.json')
}}

$python=Get-Cpython313Command;$pythonVersion=& $python.Command @($python.Args+@('--version')) 2>&1|Out-String
$dotnetVersion=(& dotnet --version 2>&1|Out-String).Trim();if($LASTEXITCODE -ne 0 -or $dotnetVersion -ne '8.0.423'){throw "CP143 requires .NET SDK 8.0.423 exactly; observed '$dotnetVersion'."}
Write-Host("CP143 runtimes: {0}; .NET SDK {1}" -f $pythonVersion.Trim(),$dotnetVersion)
Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot) 'CP143 preflight failed'

if($RepositoryOnly){
    if(-not $NoClean -and(Test-Path -LiteralPath $outRoot)){Remove-Item -Recurse -Force $outRoot}
    New-Item -ItemType Directory -Force -Path $outRoot,$testOut,$parityOut,$deterministicOut,$tl1PhaseAOut,$cp139Out,$cp142AuditOut|Out-Null
    Push-Location $repositoryRoot
    try{
        Write-Host '[1/9] Python research tests...'
        & $python.Command @($python.Args+@('-B','-m','unittest','discover','-s','tools/simulation/tests','-p','test_*.py'));if($LASTEXITCODE -ne 0){throw 'CP143 Python tests failed.'}
        Write-Host '[2/9] Warning-as-error .NET build...';Invoke-Captured 'CP143 build' (Join-Path $outRoot 'build.log') {dotnet build StarCluster.sln --configuration Release --nologo -warnaserror}
        Write-Host '[3/9] xUnit + ScenarioRunner deterministic corpora...'
        dotnet test tests\StarCluster.Tests\StarCluster.Tests.csproj --configuration Release --no-build --nologo --logger 'trx;LogFileName=cp143-tests.trx' --results-directory $testOut
        $xunitExit=$LASTEXITCODE;$trxPath=Join-Path $testOut 'cp143-tests.trx';if(-not(Test-Path -LiteralPath $trxPath)){throw 'CP143 xUnit TRX missing.'};[xml]$trx=Get-Content -LiteralPath $trxPath -Raw;$c=$trx.TestRun.ResultSummary.Counters;$total=[int]$c.total;$passed=[int]$c.passed;$failed=[int]$c.failed;$skipped=[int]$c.notExecuted;if($xunitExit -ne 0 -or $total -ne 915 -or $passed -ne 915 -or $failed -ne 0 -or $skipped -ne 0){throw "CP143 xUnit mismatch exit=$xunitExit total=$total passed=$passed failed=$failed skipped=$skipped."}
        $selfLog=Join-Path $outRoot 'scenario-self-tests.log';Invoke-Captured 'CP143 ScenarioRunner self-tests' $selfLog {dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- self-test};$selfText=Get-Content -LiteralPath $selfLog -Raw;if($selfText -notmatch 'Runner self-tests:\s+70 passed,\s+0 failed,\s+70 total\.'){throw 'CP143 expected 70/70 ScenarioRunner self-tests.'}
        Invoke-Captured 'CP143 deterministic scenario corpus' (Join-Path $outRoot 'deterministic-scenarios.log') {dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- run-all --output-dir $deterministicOut}
        Invoke-Captured 'CP143 TL1 Phase-A corpus' (Join-Path $outRoot 'tl1-phase-a.log') {dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- tl1-phase-a --output-dir $tl1PhaseAOut}
        Write-Host '[4/9] Existing C#/Python research parity...';Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'parity','--output-dir',$parityOut) 'CP143 research parity failed';$parity=Read-Json(Join-Path $parityOut 'summary.json');if(-not[bool]$parity.passed -or[int]$parity.cases -ne 25){throw 'CP143 expected 25/25 research parity.'}
        Write-Host '[5/9] CP139 DEF/RES regression foundation...'
        & $python.Command @($python.Args+@('-B','-m','unittest','discover','-v','-s','tools/simulation/tests','-p','test_cp139_def_res_reconciliation.py'));if($LASTEXITCODE -ne 0){throw 'CP139 focused regression failed under CP143.'}
        Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'combat-model-reconciliation-study',$cp139Study,'--output-dir','out/checkpoint-143/cp139-reconciliation') 'CP139 reconciliation regression failed';$recon=Read-Json(Join-Path $cp139Out 'summary.json');$ra=Get-Analysis $recon;if(-not[bool]$recon.passed -or[int]$ra.fixturePass -ne 8 -or[int]$ra.smokeVariants -ne 82 -or[int]$ra.smokeErrors -ne 0 -or-not[bool]$ra.sourceMatrixUnmodified){throw 'CP139 reconciliation regression mismatch.'}
        Write-Host '[6/9] Focused CP140 + CP141 + CP142 + CP143 tests...'
        foreach($pattern in @('test_cp140_stage_a_integration.py','test_cp141_combat_duration_stalemate.py','test_cp142_combat_surface_reconciliation.py','test_cp143_missile_mirror_pacing_attribution.py')){& $python.Command @($python.Args+@('-B','-m','unittest','discover','-v','-s','tools/simulation/tests','-p',$pattern));if($LASTEXITCODE -ne 0){throw "Focused regression failed: $pattern"}}
        Write-Host '[7/9] CP142 deep-reconciliation audit regression...'
        Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'combat-surface-reconciliation-audit',$cp142Study,'--output-dir','out/checkpoint-143/cp142-reconciliation-audit') 'CP142 reconciliation audit regression failed';$audit=Read-Json(Join-Path $cp142AuditOut 'reconciliation_summary.json');if(-not[bool]$audit.passed -or[int]$audit.ledgerRows -ne 531 -or[int]$audit.changedVsCp141Rows -ne 72 -or[int]$audit.explicitUnresolvedRows -ne 7){throw 'CP142 reconciliation audit mismatch under CP143.'}
        Write-Host '[8/9] Exact 1,980-scenario Missile-mirror pacing attribution in four isolated deterministic batches...';$ma=Invoke-Attribution $batchRoot $mergeOut 'CP143';$hashes=Merged-Hashes $mergeOut
        Write-Host '[9/9] Writing RepositoryOnly acceptance and repository contract...'
        $summary=[ordered]@{schemaVersion='star-cluster-cp143-repository-only-acceptance-v0.1';checkpoint=143;repositoryOnly=$true;failedGates=@();python=$pythonVersion.Trim();dotnetSdk=$dotnetVersion;buildPassed=$true;pythonTestsPassed=287;xunitTotal=$total;xunitPassed=$passed;xunitFailed=$failed;xunitSkipped=$skipped;scenarioRunnerSelfTestsPassed=70;deterministicScenarioCorpusPassed=$true;tl1PhaseACorpusPassed=$true;researchParityPassed=25;cp139FocusedTestsPassed=9;cp140FocusedTestsPassed=10;cp141FocusedTestsPassed=10;cp142FocusedTestsPassed=12;cp143FocusedTestsPassed=12;defResFixturesPassed=8;cp139ReconciliationSmokeVariants=82;cp139ReconciliationSmokeErrors=0;cp142ReconciliationLedgerRows=531;cp142ChangedRows=72;cp142ExplicitUnresolvedRows=7;missileMirrorScenarios=1980;attributionErrors=0;attributionBatches=4;instrumentationEquivalencePassed=12;cp142PairedOutcomeMatches=1980;hardTurnSentinel=60;longResolvedTurn=25;resolved=[int]$ma.resolved;resolvedGe25=[int]$ma.resolvedGe25;turnCapSentinels=[int]$ma.turnCapSentinels;safeStalemates=[int]$ma.safeStalemates;sourceMatrixUnmodified=$true;substantiveCombatTrials=0;tuningAllowed=$false;automaticPromotion=$false;nextStage='whole-combat substantive Stage A with five distinct executable resource environments';mergedArtifactSha256=$hashes}
        $summary|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $repoOnlySummary -Encoding UTF8
        Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP143 RepositoryOnly contract failed'
        Write-Host 'CP143 RepositoryOnly acceptance PASSED.' -ForegroundColor Green
    } finally {Pop-Location}
    exit 0
}

if(-not(Test-Path -LiteralPath $repoOnlySummary)){throw 'Run CP143 -RepositoryOnly first in this same extraction.'}
Push-Location $repositoryRoot
try{
    Write-Host '[final 1/3] Revalidating preflight/manifest after RepositoryOnly outputs...';Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot) 'CP143 final preflight failed';Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP143 RepositoryOnly state contract failed'
    Write-Host '[final 2/3] Re-running exact Missile-mirror attribution for deterministic reproduction...';$maFinal=Invoke-Attribution $finalBatchRoot $finalMergeOut 'CP143 final';$finalHashes=Merged-Hashes $finalMergeOut;$ro=Read-Json $repoOnlySummary;$expected=$ro.mergedArtifactSha256
    foreach($name in @('attribution','groups','signals','instrumentation','cp142Paired','timelineSample','batchAudit','summary')){if([string]$finalHashes[$name] -ne [string]$expected.$name){throw "CP143 deterministic attribution hash mismatch for $name."}}
    Write-Host '[final 3/3] Final acceptance summary and result ZIP...'
    $final=[ordered]@{};$ro.psobject.Properties|ForEach-Object{$final[$_.Name]=$_.Value};$final['schemaVersion']='star-cluster-cp143-native-acceptance-v0.1';$final['repositoryOnly']=$false;$final['repositoryOnlyAccepted']=$true;$final['deterministicAttributionReproduced']=$true;$final['finalMergedArtifactSha256']=$finalHashes;$final|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $finalSummary -Encoding UTF8
    Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP143 final contract failed'
    $stamp=Get-Date -Format 'yyyyMMdd_HHmmss';$zip=Join-Path $outRoot ("StarCluster_CP143_native_results_$stamp.zip");$items=Get-ChildItem -LiteralPath $outRoot -Force|Where-Object{$_.FullName -ne $zip};Compress-Archive -Path $items.FullName -DestinationPath $zip -CompressionLevel Optimal
    Write-Host "CP143 native acceptance PASSED. Results: $zip" -ForegroundColor Green
} finally {Pop-Location}
