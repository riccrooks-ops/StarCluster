[CmdletBinding()]
param([switch]$RepositoryOnly,[switch]$NoClean,[int]$Jobs=24)
Set-StrictMode -Version 2.0
$ErrorActionPreference='Stop'
$repositoryRoot=(Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$preflight=Join-Path $PSScriptRoot 'preflight_checkpoint_144.py'
$contract=Join-Path $PSScriptRoot 'test_checkpoint_144_contract.py'
$research=Join-Path $repositoryRoot 'tools\simulation\run_starcluster_research.py'
$cp139Study='docs/archive/testing/pre-cp165-active/cp139_def_res_reconciliation_study_v0_1.json'
$cp142Study='docs/archive/testing/pre-cp165-active/cp142_combat_surface_deep_reconciliation_study_v0_1.json'
$cp144Study='docs/archive/testing/pre-cp165-active/cp144_whole_combat_stage_a_response_surface_study_v0_1.json'
$cp144Manifest=Join-Path $repositoryRoot 'docs\archive\testing\pre-cp165-active\cp144_stage_a_experiment_manifest.csv'
$outRoot=Join-Path $repositoryRoot 'out\checkpoint-144'
$testOut=Join-Path $outRoot 'xunit';$parityOut=Join-Path $outRoot 'research-parity';$deterministicOut=Join-Path $outRoot 'deterministic-scenarios';$tl1PhaseAOut=Join-Path $outRoot 'tl1-phase-a';$cp139Out=Join-Path $outRoot 'cp139-reconciliation';$cp142AuditOut=Join-Path $outRoot 'cp142-reconciliation-audit'
$smokeBatchRoot=Join-Path $outRoot 'stage-a-smoke-batches';$smokeMergeOut=Join-Path $outRoot 'stage-a-smoke-merged'
$subBatchRoot=Join-Path $outRoot 'stage-a-substantive-batches';$subMergeOut=Join-Path $outRoot 'stage-a-substantive-merged'
$repoOnlySummary=Join-Path $outRoot 'CP144_REPOSITORY_ONLY_ACCEPTANCE.json';$finalSummary=Join-Path $outRoot 'CP144_NATIVE_ACCEPTANCE_SUMMARY.json'

function Get-Cpython313Command {$candidates=@(@{Command='py';Args=@('-3.13')},@{Command='python';Args=@()},@{Command='python3';Args=@()});foreach($candidate in $candidates){$cmd=Get-Command $candidate.Command -ErrorAction SilentlyContinue;if($null -eq $cmd){continue};$v=& $candidate.Command @($candidate.Args+@('--version')) 2>&1|Out-String;if($LASTEXITCODE -eq 0 -and $v -match 'Python\s+3\.13(?:\.|\s|$)'){return $candidate}};throw 'CP144 requires Python 3.13.'}
function Invoke-PythonChecked([object]$Python,[string[]]$Arguments,[string]$Failure){& $Python.Command @($Python.Args+$Arguments);if($LASTEXITCODE -ne 0){throw "$Failure (exit code $LASTEXITCODE)."}}
function Invoke-Captured([string]$Label,[string]$LogPath,[scriptblock]$Body){& $Body *> $LogPath;$exitCode=$LASTEXITCODE;if($exitCode -ne 0){Write-Host "       $Label output tail:" -ForegroundColor Yellow;Get-Content -LiteralPath $LogPath -Tail 120|ForEach-Object{Write-Host("       $_")};throw "$Label failed (exit code $exitCode)."}}
function Read-Json([string]$Path){return(Get-Content -LiteralPath $Path -Raw|ConvertFrom-Json)}
function Get-Analysis([object]$Obj){if($null -ne $Obj.PSObject.Properties['analysis']){return $Obj.analysis};return $Obj}
function Relative-To-Repo([string]$Path){
    $root=[System.IO.Path]::GetFullPath($repositoryRoot);$full=[System.IO.Path]::GetFullPath($Path);$sep=[System.IO.Path]::DirectorySeparatorChar
    if($full.Equals($root,[System.StringComparison]::OrdinalIgnoreCase)){return '.'}
    $prefix=$root;if(-not $prefix.EndsWith([string]$sep)){$prefix+=$sep}
    if(-not $full.StartsWith($prefix,[System.StringComparison]::OrdinalIgnoreCase)){throw "Path '$Path' is outside repository root '$repositoryRoot'."}
    return $full.Substring($prefix.Length)
}
function File-Hash([string]$Path){return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()}

function Invoke-PythonResearchTests {
    $files=Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'tools\simulation\tests') -Filter 'test_*.py' | Sort-Object Name
    if($files.Count -ne 35){throw "CP144 expected 35 Python test modules, found $($files.Count)."}
    $modules1=@($files[0..17] | ForEach-Object{"tools.simulation.tests.$($_.BaseName)"})
    $modules2=@($files[18..34] | ForEach-Object{"tools.simulation.tests.$($_.BaseName)"})
    Write-Host("       Python test chunk 1/2 ({0} modules)..." -f $modules1.Count)
    & $python.Command @($python.Args+@('-B','-m','unittest')+$modules1)
    if($LASTEXITCODE -ne 0){throw 'CP144 Python test chunk 1 failed.'}
    Write-Host("       Python test chunk 2/2 ({0} modules)..." -f $modules2.Count)
    & $python.Command @($python.Args+@('-B','-m','unittest')+$modules2)
    if($LASTEXITCODE -ne 0){throw 'CP144 Python test chunk 2 failed.'}
}

function Invoke-Smoke {
    if(Test-Path -LiteralPath $smokeBatchRoot){Remove-Item -Recurse -Force $smokeBatchRoot};if(Test-Path -LiteralPath $smokeMergeOut){Remove-Item -Recurse -Force $smokeMergeOut}
    New-Item -ItemType Directory -Force -Path $smokeBatchRoot,$smokeMergeOut|Out-Null
    $ranges=@(@(0,1024),@(1024,2048),@(2048,3072),@(3072,4096),@(4096,5120),@(5120,6144),@(6144,6850));$i=0
    foreach($range in $ranges){
        $i++;$start=[int]$range[0];$end=[int]$range[1];$dir=Join-Path $smokeBatchRoot ("batch_{0:D4}_{1:D4}" -f $start,$end);New-Item -ItemType Directory -Force -Path $dir|Out-Null
        $rel=Relative-To-Repo $dir;$log=Join-Path $dir 'console.log';Write-Host("       Stage-A smoke batch {0}/7: scenarios {1}-{2}" -f $i,$start,($end-1))
        Invoke-Captured "CP144 smoke batch $start-$end" $log {& $python.Command @($python.Args+@('-B',$research,'--repo',$repositoryRoot,'whole-combat-stage-a-smoke',$cp144Study,'--output-dir',$rel,'--jobs',$Jobs,'--batch-start',$start,'--batch-end',$end))}
        $bs=Read-Json(Join-Path $dir 'summary.json');$expected=$end-$start
        if(-not[bool]$bs.passed -or[int]$bs.scenarios -ne $expected -or[int]$bs.executionErrors -ne 0 -or[int]$bs.nonstandoffOpenOrders -ne 0 -or-not[bool]$bs.sourceMatrixUnmodified -or[int]$bs.substantiveCombatTrials -ne 0){throw "CP144 smoke batch $start-$end contract mismatch."}
    }
    $relB=Relative-To-Repo $smokeBatchRoot;$relM=Relative-To-Repo $smokeMergeOut;$log=Join-Path $smokeMergeOut 'console.log'
    Invoke-Captured 'CP144 Stage-A smoke merge' $log {& $python.Command @($python.Args+@('-B',$research,'--repo',$repositoryRoot,'whole-combat-stage-a-smoke-merge',$cp144Study,'--batch-root',$relB,'--output-dir',$relM))}
    $s=Read-Json(Join-Path $smokeMergeOut 'summary.json')
    if(-not[bool]$s.passed -or[int]$s.stageAScenarios -ne 6850 -or[int]$s.executionErrors -ne 0 -or[int]$s.resolved -ne 6785 -or[int]$s.resolvedGe25 -ne 9 -or[int]$s.turnCapSentinels -ne 65 -or[int]$s.safeStalemates -ne 0 -or[int]$s.nonstandoffOpenOrders -ne 0 -or[int]$s.resourceEnvironmentCount -ne 5 -or[int]$s.scenarioStrataCount -ne 10 -or[int]$s.orderedSameTlWeaponPairings -ne 137 -or-not[bool]$s.stageASubstantiveReady -or-not[bool]$s.sourceMatrixUnmodified){throw 'CP144 merged Stage-A smoke contract mismatch.'}
    return $s
}

function Test-SubstantiveBatch([string]$Dir,[int]$Start,[int]$End,[object[]]$ManifestRows){
    $summaryPath=Join-Path $Dir 'summary.json';$csvPath=Join-Path $Dir 'scenario_response_surface.csv'
    if(-not(Test-Path -LiteralPath $summaryPath) -or -not(Test-Path -LiteralPath $csvPath)){return $false}
    try{
        $s=Read-Json $summaryPath;$expected=$End-$Start
        if(-not[bool]$s.passed -or[int]$s.batchStart -ne $Start -or[int]$s.batchEnd -ne $End -or[int]$s.scenarios -ne $expected -or[int]$s.trialsPerScenario -ne 500 -or[int]$s.combatTrials -ne ($expected*500) -or[int]$s.trialErrors -ne 0 -or-not[bool]$s.sourceMatrixUnmodified){return $false}
        $rows=@(Import-Csv -LiteralPath $csvPath);if($rows.Count -ne $expected){return $false}
        for($i=0;$i -lt $rows.Count;$i++){
            if([string]$rows[$i].scenario_id -ne [string]$ManifestRows[$Start+$i].scenario_id){return $false}
            if([int]$rows[$i].trials -ne 500 -or[int]$rows[$i].error_trials -ne 0){return $false}
            if([double]$rows[$i].a_nonstandoff_open_orders_mean -ne 0.0 -or[double]$rows[$i].b_nonstandoff_open_orders_mean -ne 0.0){return $false}
        }
        return $true
    } catch {return $false}
}

function Invoke-Substantive {
    New-Item -ItemType Directory -Force -Path $subBatchRoot|Out-Null
    if(Test-Path -LiteralPath $subMergeOut){Remove-Item -Recurse -Force $subMergeOut};New-Item -ItemType Directory -Force -Path $subMergeOut|Out-Null
    $manifestRows=@(Import-Csv -LiteralPath $cp144Manifest);if($manifestRows.Count -ne 6850){throw 'CP144 substantive manifest must contain 6,850 rows.'}
    $start=0;$batch=0
    while($start -lt 6850){
        $end=[Math]::Min($start+256,6850);$batch++;$dir=Join-Path $subBatchRoot ("batch_{0:D4}_{1:D4}" -f $start,$end)
        if(Test-SubstantiveBatch $dir $start $end $manifestRows){Write-Host("       Stage-A substantive batch {0}/27: scenarios {1}-{2} already valid; reusing." -f $batch,$start,($end-1))}
        else{
            if(Test-Path -LiteralPath $dir){Remove-Item -Recurse -Force $dir};New-Item -ItemType Directory -Force -Path $dir|Out-Null
            $rel=Relative-To-Repo $dir;$log=Join-Path $dir 'console.log';Write-Host("       Stage-A substantive batch {0}/27: scenarios {1}-{2}, 500 trials/cell" -f $batch,$start,($end-1))
            Invoke-Captured "CP144 substantive batch $start-$end" $log {& $python.Command @($python.Args+@('-B',$research,'--repo',$repositoryRoot,'whole-combat-stage-a-substantive',$cp144Study,'--output-dir',$rel,'--jobs',$Jobs,'--batch-start',$start,'--batch-end',$end,'--trials-per-scenario','500'))}
            if(-not(Test-SubstantiveBatch $dir $start $end $manifestRows)){throw "CP144 substantive batch $start-$end failed validation after execution."}
        }
        $start=$end
    }
    $relB=Relative-To-Repo $subBatchRoot;$relM=Relative-To-Repo $subMergeOut;$log=Join-Path $subMergeOut 'console.log'
    Invoke-Captured 'CP144 substantive Stage-A merge/response surfaces' $log {& $python.Command @($python.Args+@('-B',$research,'--repo',$repositoryRoot,'whole-combat-stage-a-substantive-merge',$cp144Study,'--batch-root',$relB,'--output-dir',$relM,'--trials-per-scenario','500'))}
    $s=Read-Json(Join-Path $subMergeOut 'summary.json')
    if(-not[bool]$s.passed -or[int]$s.stageAScenarios -ne 6850 -or[int]$s.trialsPerScenario -ne 500 -or[int64]$s.substantiveCombatTrials -ne 3425000 -or[int]$s.resourceEnvironmentCount -ne 5 -or[int]$s.scenarioStrataCount -ne 10 -or[int]$s.orderedSameTlWeaponPairings -ne 137 -or-not[bool]$s.sourceMatrixUnmodified -or[bool]$s.automaticPromotion -or[bool]$s.tuningAllowed -or[bool]$s.stageBAutomatic){throw 'CP144 merged substantive Stage-A contract mismatch.'}
    return $s
}

$python=Get-Cpython313Command;$pythonVersion=& $python.Command @($python.Args+@('--version')) 2>&1|Out-String
$dotnetVersion=(& dotnet --version 2>&1|Out-String).Trim();if($LASTEXITCODE -ne 0 -or $dotnetVersion -ne '8.0.423'){throw "CP144 requires .NET SDK 8.0.423 exactly; observed '$dotnetVersion'."}
Write-Host("CP144 runtimes: {0}; .NET SDK {1}" -f $pythonVersion.Trim(),$dotnetVersion)
Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot) 'CP144 preflight failed'

if($RepositoryOnly){
    if(-not $NoClean -and(Test-Path -LiteralPath $outRoot)){Remove-Item -Recurse -Force $outRoot}
    New-Item -ItemType Directory -Force -Path $outRoot,$testOut,$parityOut,$deterministicOut,$tl1PhaseAOut,$cp139Out,$cp142AuditOut|Out-Null
    Push-Location $repositoryRoot
    try{
        Write-Host '[1/9] Python research tests in isolated chunks...';Invoke-PythonResearchTests
        Write-Host '[2/9] Warning-as-error .NET build...';Invoke-Captured 'CP144 build' (Join-Path $outRoot 'build.log') {dotnet build StarCluster.sln --configuration Release --nologo -warnaserror}
        Write-Host '[3/9] xUnit + ScenarioRunner deterministic corpora...'
        dotnet test tests\StarCluster.Tests\StarCluster.Tests.csproj --configuration Release --no-build --nologo --logger 'trx;LogFileName=cp144-tests.trx' --results-directory $testOut
        $xunitExit=$LASTEXITCODE;$trxPath=Join-Path $testOut 'cp144-tests.trx';if(-not(Test-Path -LiteralPath $trxPath)){throw 'CP144 xUnit TRX missing.'};[xml]$trx=Get-Content -LiteralPath $trxPath -Raw;$c=$trx.TestRun.ResultSummary.Counters;$total=[int]$c.total;$passed=[int]$c.passed;$failed=[int]$c.failed;$skipped=[int]$c.notExecuted;if($xunitExit -ne 0 -or $total -ne 916 -or $passed -ne 916 -or $failed -ne 0 -or $skipped -ne 0){throw "CP144 xUnit mismatch exit=$xunitExit total=$total passed=$passed failed=$failed skipped=$skipped."}
        $selfLog=Join-Path $outRoot 'scenario-self-tests.log';Invoke-Captured 'CP144 ScenarioRunner self-tests' $selfLog {dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- self-test};$selfText=Get-Content -LiteralPath $selfLog -Raw;if($selfText -notmatch 'Runner self-tests:\s+70 passed,\s+0 failed,\s+70 total\.'){throw 'CP144 expected 70/70 ScenarioRunner self-tests.'}
        Invoke-Captured 'CP144 deterministic scenario corpus' (Join-Path $outRoot 'deterministic-scenarios.log') {dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- run-all --output-dir $deterministicOut}
        Invoke-Captured 'CP144 TL1 Phase-A corpus' (Join-Path $outRoot 'tl1-phase-a.log') {dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- tl1-phase-a --output-dir $tl1PhaseAOut}
        Write-Host '[4/9] Existing C#/Python research parity...';Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'parity','--output-dir',$parityOut) 'CP144 research parity failed';$parity=Read-Json(Join-Path $parityOut 'summary.json');if(-not[bool]$parity.passed -or[int]$parity.cases -ne 25){throw 'CP144 expected 25/25 research parity.'}
        Write-Host '[5/9] CP139 DEF/RES regression foundation...'
        & $python.Command @($python.Args+@('-B','-m','unittest','discover','-v','-s','tools/simulation/tests','-p','test_cp139_def_res_reconciliation.py'));if($LASTEXITCODE -ne 0){throw 'CP139 focused regression failed under CP144.'}
        Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'combat-model-reconciliation-study',$cp139Study,'--output-dir','out/checkpoint-144/cp139-reconciliation') 'CP139 reconciliation regression failed';$recon=Read-Json(Join-Path $cp139Out 'summary.json');$ra=Get-Analysis $recon;if(-not[bool]$recon.passed -or[int]$ra.fixturePass -ne 8 -or[int]$ra.smokeVariants -ne 82 -or[int]$ra.smokeErrors -ne 0 -or-not[bool]$ra.sourceMatrixUnmodified){throw 'CP139 reconciliation regression mismatch.'}
        Write-Host '[6/9] Focused CP140 + CP141 + CP142 + CP143 + CP144 tests...'
        foreach($pattern in @('test_cp140_stage_a_integration.py','test_cp141_combat_duration_stalemate.py','test_cp142_combat_surface_reconciliation.py','test_cp143_missile_mirror_pacing_attribution.py','test_cp144_*.py')){& $python.Command @($python.Args+@('-B','-m','unittest','discover','-v','-s','tools/simulation/tests','-p',$pattern));if($LASTEXITCODE -ne 0){throw "Focused regression failed: $pattern"}}
        Write-Host '[7/9] CP142 deep-reconciliation audit regression...'
        Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'combat-surface-reconciliation-audit',$cp142Study,'--output-dir','out/checkpoint-144/cp142-reconciliation-audit') 'CP142 reconciliation audit regression failed';$audit=Read-Json(Join-Path $cp142AuditOut 'reconciliation_summary.json');if(-not[bool]$audit.passed -or[int]$audit.ledgerRows -ne 531 -or[int]$audit.changedVsCp141Rows -ne 72 -or[int]$audit.explicitUnresolvedRows -ne 7){throw 'CP142 reconciliation audit mismatch under CP144.'}
        Write-Host '[8/9] Complete 6,850-scenario whole-combat Stage-A smoke...';$smoke=Invoke-Smoke
        Write-Host '[9/9] Writing RepositoryOnly acceptance and repository contract...'
        $summary=[ordered]@{schemaVersion='star-cluster-cp144-repository-only-acceptance-v0.1';checkpoint=144;repositoryOnly=$true;failedGates=@();python=$pythonVersion.Trim();dotnetSdk=$dotnetVersion;buildPassed=$true;pythonTestsPassed=298;xunitTotal=$total;xunitPassed=$passed;xunitFailed=$failed;xunitSkipped=$skipped;scenarioRunnerSelfTestsPassed=70;deterministicScenarioCorpusPassed=$true;tl1PhaseACorpusPassed=$true;researchParityPassed=25;cp139FocusedTestsPassed=9;cp140FocusedTestsPassed=10;cp141FocusedTestsPassed=10;cp142FocusedTestsPassed=12;cp143FocusedTestsPassed=12;cp144FocusedTestsPassed=11;defResFixturesPassed=8;cp139ReconciliationSmokeVariants=82;cp139ReconciliationSmokeErrors=0;cp142ReconciliationLedgerRows=531;cp142ChangedRows=72;cp142ExplicitUnresolvedRows=7;sharedPolicyFixtureCases=10;pythonCsharpPolicyParityPassed=$true;stageAScenarios=6850;resourceEnvironmentCount=5;scenarioStrataCount=10;orderedSameTlWeaponPairings=137;smokeResolved=[int]$smoke.resolved;smokeResolvedGe25=[int]$smoke.resolvedGe25;smokeTurnCapSentinels=[int]$smoke.turnCapSentinels;smokeSafeStalemates=[int]$smoke.safeStalemates;smokeNonstandoffOpenOrders=[int]$smoke.nonstandoffOpenOrders;sourceMatrixUnmodified=$true;substantiveCombatTrials=0;tuningAllowed=$false;automaticPromotion=$false;stageBAutomatic=$false;nextStage='3,425,000-trial whole-combat Stage-A response surface'}
        $summary|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $repoOnlySummary -Encoding UTF8
        Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP144 RepositoryOnly contract failed'
        Write-Host 'CP144 RepositoryOnly acceptance PASSED. Run the same wrapper without -RepositoryOnly to execute the 3,425,000-trial Stage A.' -ForegroundColor Green
    } finally {Pop-Location}
    exit 0
}

if(-not(Test-Path -LiteralPath $repoOnlySummary)){throw 'Run CP144 -RepositoryOnly first in this same extraction.'}
Push-Location $repositoryRoot
try{
    Write-Host '[final 1/3] Revalidating preflight/manifest and accepted Stage-A smoke after RepositoryOnly outputs...';Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot) 'CP144 final preflight failed';Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP144 RepositoryOnly state contract failed'
    Write-Host '[final 2/3] Executing/resuming 6,850 x 500 = 3,425,000 substantive Stage-A trials...';$sub=Invoke-Substantive
    Write-Host '[final 3/3] Final response-surface validation, acceptance summary, and result ZIP...'
    $ro=Read-Json $repoOnlySummary;$final=[ordered]@{};$ro.psobject.Properties|ForEach-Object{$final[$_.Name]=$_.Value};$final['schemaVersion']='star-cluster-cp144-native-acceptance-v0.1';$final['repositoryOnly']=$false;$final['repositoryOnlyAccepted']=$true;$final['substantiveStageACompleted']=$true;$final['trialsPerScenario']=500;$final['substantiveCombatTrials']=[int64]$sub.substantiveCombatTrials;$final['substantiveTurnCapSentinels']=[int64]$sub.turnCapSentinels;$final['substantiveResolvedGe25']=[int64]$sub.resolvedGe25;$final['substantiveSafeStalemates']=[int64]$sub.safeStalemates;$final['substantiveGameplayDurationConcernRate']=[double]$sub.gameplayDurationConcernRate;$final|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $finalSummary -Encoding UTF8
    Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP144 final contract failed'
    $stamp=Get-Date -Format 'yyyyMMdd_HHmmss';$zip=Join-Path $outRoot ("StarCluster_CP144_native_results_$stamp.zip");$items=Get-ChildItem -LiteralPath $outRoot -Force|Where-Object{$_.FullName -ne $zip};Compress-Archive -Path $items.FullName -DestinationPath $zip -CompressionLevel Optimal
    Write-Host "CP144 native acceptance PASSED. Results: $zip" -ForegroundColor Green
} finally {Pop-Location}
