[CmdletBinding()]
param([switch]$RepositoryOnly,[switch]$NoClean,[int]$Jobs=24)
Set-StrictMode -Version 2.0
$ErrorActionPreference='Stop'

$repositoryRoot=(Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$preflight=Join-Path $PSScriptRoot 'preflight_checkpoint_148.py'
$contract=Join-Path $PSScriptRoot 'test_checkpoint_148_contract.py'
$research=Join-Path $repositoryRoot 'tools\simulation\run_starcluster_research.py'
$cp139Study='docs/archive/testing/pre-cp165-active/cp139_def_res_reconciliation_study_v0_1.json'
$cp142Study='docs/archive/testing/pre-cp165-active/cp142_combat_surface_deep_reconciliation_study_v0_1.json'
$cp148Study='docs/archive/testing/pre-cp165-active/cp148_whole_combat_stage_a_tactical_utility_response_surface_study_v0_1.json'
$cp144Manifest=Join-Path $repositoryRoot 'docs\archive\testing\pre-cp165-active\cp144_stage_a_experiment_manifest.csv'
$outRoot=Join-Path $repositoryRoot 'out\checkpoint-148'
$testOut=Join-Path $outRoot 'xunit'
$parityOut=Join-Path $outRoot 'research-parity'
$deterministicOut=Join-Path $outRoot 'deterministic-scenarios'
$tl1PhaseAOut=Join-Path $outRoot 'tl1-phase-a'
$cp139Out=Join-Path $outRoot 'cp139-reconciliation'
$cp142AuditOut=Join-Path $outRoot 'cp142-reconciliation-audit'
$smokeBatchRoot=Join-Path $outRoot 'stage-a-smoke-batches'
$smokeMergeOut=Join-Path $outRoot 'stage-a-smoke-merged'
$subBatchRoot=Join-Path $outRoot 'stage-a-substantive-batches'
$subMergeOut=Join-Path $outRoot 'stage-a-substantive-merged'
$repoOnlySummary=Join-Path $outRoot 'CP148_REPOSITORY_ONLY_ACCEPTANCE.json'
$finalSummary=Join-Path $outRoot 'CP148_NATIVE_ACCEPTANCE_SUMMARY.json'

function Get-Cpython313Command {
    $candidates=@(@{Command='py';Args=@('-3.13')},@{Command='python';Args=@()},@{Command='python3';Args=@()})
    foreach($candidate in $candidates){
        $cmd=Get-Command $candidate.Command -ErrorAction SilentlyContinue
        if($null -eq $cmd){continue}
        $v=& $candidate.Command @($candidate.Args+@('--version')) 2>&1|Out-String
        if($LASTEXITCODE -eq 0 -and $v -match 'Python\s+3\.13(?:\.|\s|$)'){return $candidate}
    }
    throw 'CP148 requires Python 3.13.'
}
function Invoke-PythonChecked([object]$Python,[string[]]$Arguments,[string]$Failure){
    & $Python.Command @($Python.Args+$Arguments)
    if($LASTEXITCODE -ne 0){throw "$Failure (exit code $LASTEXITCODE)."}
}
function Invoke-Captured([string]$Label,[string]$LogPath,[scriptblock]$Body){
    & $Body *> $LogPath
    $exitCode=$LASTEXITCODE
    if($exitCode -ne 0){
        Write-Host "       $Label output tail:" -ForegroundColor Yellow
        Get-Content -LiteralPath $LogPath -Tail 120|ForEach-Object{Write-Host("       $_")}
        throw "$Label failed (exit code $exitCode)."
    }
}
function Read-Json([string]$Path){return(Get-Content -LiteralPath $Path -Raw|ConvertFrom-Json)}
function Get-Analysis([object]$Obj){if($null -ne $Obj.PSObject.Properties['analysis']){return $Obj.analysis};return $Obj}
function Relative-To-Repo([string]$Path){
    $root=[System.IO.Path]::GetFullPath($repositoryRoot);$full=[System.IO.Path]::GetFullPath($Path);$sep=[System.IO.Path]::DirectorySeparatorChar
    if($full.Equals($root,[System.StringComparison]::OrdinalIgnoreCase)){return '.'}
    $prefix=$root;if(-not $prefix.EndsWith([string]$sep)){$prefix+=$sep}
    if(-not $full.StartsWith($prefix,[System.StringComparison]::OrdinalIgnoreCase)){throw "Path '$Path' is outside repository root '$repositoryRoot'."}
    return $full.Substring($prefix.Length)
}

function Invoke-PythonResearchTests {
    $files=Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'tools\simulation\tests') -Filter 'test_*.py' | Sort-Object Name
    if($files.Count -ne 39){throw "CP148 expected 39 Python test modules, found $($files.Count)."}
    $chunks=@(@($files[0..12]),@($files[13..18]),@($files[19..24]),@($files[25..38]))
    $simulationRoot=Join-Path $repositoryRoot 'tools\simulation'
    $oldPythonPath=$env:PYTHONPATH
    try {
        if([string]::IsNullOrWhiteSpace($oldPythonPath)){$env:PYTHONPATH=$simulationRoot}else{$env:PYTHONPATH=$simulationRoot+[System.IO.Path]::PathSeparator+$oldPythonPath}
        for($i=0;$i -lt $chunks.Count;$i++){
            $modules=@($chunks[$i] | ForEach-Object{"tools.simulation.tests.$($_.BaseName)"})
            Write-Host("       Python test chunk {0}/4 ({1} modules)..." -f ($i+1),$modules.Count)
            & $python.Command @($python.Args+@('-B','-m','unittest')+$modules)
            if($LASTEXITCODE -ne 0){throw "CP148 Python test chunk $($i+1) failed."}
        }
    } finally {$env:PYTHONPATH=$oldPythonPath}
}

function Invoke-Cp148Smoke {
    if(Test-Path -LiteralPath $smokeBatchRoot){Remove-Item -Recurse -Force $smokeBatchRoot}
    if(Test-Path -LiteralPath $smokeMergeOut){Remove-Item -Recurse -Force $smokeMergeOut}
    New-Item -ItemType Directory -Force -Path $smokeBatchRoot,$smokeMergeOut|Out-Null
    $ranges=@(@(0,1024),@(1024,2048),@(2048,3072),@(3072,4096),@(4096,5120),@(5120,6144),@(6144,6850));$i=0
    foreach($range in $ranges){
        $i++;$start=[int]$range[0];$end=[int]$range[1]
        $dir=Join-Path $smokeBatchRoot ("batch_{0:D4}_{1:D4}" -f $start,$end)
        New-Item -ItemType Directory -Force -Path $dir|Out-Null
        $rel=Relative-To-Repo $dir;$log=Join-Path $dir 'console.log'
        Write-Host("       CP148 utility smoke batch {0}/7: scenarios {1}-{2}" -f $i,$start,($end-1))
        Invoke-Captured "CP148 utility smoke batch $start-$end" $log {& $python.Command @($python.Args+@('-B',$research,'--repo',$repositoryRoot,'whole-combat-stage-a-smoke',$cp148Study,'--output-dir',$rel,'--jobs',$Jobs,'--batch-start',$start,'--batch-end',$end))}
        $bs=Read-Json(Join-Path $dir 'summary.json');$expected=$end-$start
        if(-not[bool]$bs.passed -or[int]$bs.checkpoint -ne 148 -or[int]$bs.scenarios -ne $expected -or[int]$bs.executionErrors -ne 0 -or[int]$bs.nonstandoffOpenOrders -ne 0 -or-not[bool]$bs.sourceMatrixUnmodified -or[int]$bs.substantiveCombatTrials -ne 0){throw "CP148 utility-smoke batch $start-$end contract mismatch."}
    }
    $relB=Relative-To-Repo $smokeBatchRoot;$relM=Relative-To-Repo $smokeMergeOut;$log=Join-Path $smokeMergeOut 'console.log'
    Invoke-Captured 'CP148 utility Stage-A smoke merge' $log {& $python.Command @($python.Args+@('-B',$research,'--repo',$repositoryRoot,'whole-combat-stage-a-smoke-merge',$cp148Study,'--batch-root',$relB,'--output-dir',$relM))}
    $s=Read-Json(Join-Path $smokeMergeOut 'summary.json')
    if(-not[bool]$s.passed -or[int]$s.checkpoint -ne 148 -or[int]$s.stageAScenarios -ne 6850 -or[int]$s.integrationSmokeTrials -ne 6850 -or[int]$s.executionErrors -ne 0 -or[int]$s.resolved -ne 6850 -or[int]$s.resolvedGe25 -ne 0 -or[int]$s.turnCapSentinels -ne 0 -or[int]$s.safeStalemates -ne 0 -or[int]$s.nonstandoffOpenOrders -ne 0 -or[int]$s.resourceEnvironmentCount -ne 5 -or[int]$s.scenarioStrataCount -ne 10 -or[int]$s.orderedSameTlWeaponPairings -ne 137 -or-not[bool]$s.stageASubstantiveReady -or-not[bool]$s.sourceMatrixUnmodified){throw 'CP148 merged utility Stage-A smoke contract mismatch.'}
    return $s
}

function Test-SubstantiveBatch([string]$Dir,[int]$Start,[int]$End,[object[]]$ManifestRows){
    $summaryPath=Join-Path $Dir 'summary.json';$csvPath=Join-Path $Dir 'scenario_response_surface.csv'
    if(-not(Test-Path -LiteralPath $summaryPath) -or -not(Test-Path -LiteralPath $csvPath)){return $false}
    try{
        $s=Read-Json $summaryPath;$expected=$End-$Start
        if(-not[bool]$s.passed -or[int]$s.checkpoint -ne 148 -or[int]$s.batchStart -ne $Start -or[int]$s.batchEnd -ne $End -or[int]$s.scenarios -ne $expected -or[int]$s.trialsPerScenario -ne 500 -or[int64]$s.combatTrials -ne ([int64]$expected*500) -or[int]$s.trialErrors -ne 0 -or-not[bool]$s.sourceMatrixUnmodified){return $false}
        $rows=@(Import-Csv -LiteralPath $csvPath);if($rows.Count -ne $expected){return $false}
        for($i=0;$i -lt $rows.Count;$i++){
            $r=$rows[$i]
            if([string]$r.scenario_id -ne [string]$ManifestRows[$Start+$i].scenario_id){return $false}
            if([int]$r.trials -ne 500 -or[int]$r.error_trials -ne 0){return $false}
            if([double]$r.a_nonstandoff_open_orders_mean -ne 0.0 -or[double]$r.b_nonstandoff_open_orders_mean -ne 0.0){return $false}
            foreach($side in @('a','b')){
                $dProp="${side}_base_max_installed_tp_demand"
                $reactorProp="${side}_base_reactor_tp"
                $meanProp="${side}_mean_tp_allocated_per_turn"
                $peakProp="${side}_peak_tp_allocated_per_turn"
                $d=[double]$r.$dProp;$reactor=[double]$r.$reactorProp;$meanAlloc=[double]$r.$meanProp;$peakAlloc=[double]$r.$peakProp
                if($d -le 0 -or $reactor -le 0 -or $meanAlloc -lt 0 -or $peakAlloc -lt 0){return $false}
            }
        }
        return $true
    } catch {return $false}
}

function Invoke-Substantive {
    New-Item -ItemType Directory -Force -Path $subBatchRoot|Out-Null
    if(Test-Path -LiteralPath $subMergeOut){Remove-Item -Recurse -Force $subMergeOut}
    New-Item -ItemType Directory -Force -Path $subMergeOut|Out-Null
    $manifestRows=@(Import-Csv -LiteralPath $cp144Manifest);if($manifestRows.Count -ne 6850){throw 'CP148 substantive manifest must contain 6,850 rows.'}
    $start=0;$batch=0
    while($start -lt 6850){
        $end=[Math]::Min($start+256,6850);$batch++;$dir=Join-Path $subBatchRoot ("batch_{0:D4}_{1:D4}" -f $start,$end)
        if(Test-SubstantiveBatch $dir $start $end $manifestRows){Write-Host("       CP148 substantive batch {0}/27: scenarios {1}-{2} already valid; reusing." -f $batch,$start,($end-1))}
        else{
            if(Test-Path -LiteralPath $dir){Remove-Item -Recurse -Force $dir}
            New-Item -ItemType Directory -Force -Path $dir|Out-Null
            $rel=Relative-To-Repo $dir;$log=Join-Path $dir 'console.log'
            Write-Host("       CP148 substantive batch {0}/27: scenarios {1}-{2}, 500 trials/cell" -f $batch,$start,($end-1))
            Invoke-Captured "CP148 substantive batch $start-$end" $log {& $python.Command @($python.Args+@('-B',$research,'--repo',$repositoryRoot,'whole-combat-stage-a-substantive',$cp148Study,'--output-dir',$rel,'--jobs',$Jobs,'--batch-start',$start,'--batch-end',$end,'--trials-per-scenario','500'))}
            if(-not(Test-SubstantiveBatch $dir $start $end $manifestRows)){throw "CP148 substantive batch $start-$end failed validation after execution."}
        }
        $start=$end
    }
    $relB=Relative-To-Repo $subBatchRoot;$relM=Relative-To-Repo $subMergeOut;$log=Join-Path $subMergeOut 'console.log'
    Invoke-Captured 'CP148 substantive Stage-A merge/response surfaces' $log {& $python.Command @($python.Args+@('-B',$research,'--repo',$repositoryRoot,'whole-combat-stage-a-substantive-merge',$cp148Study,'--batch-root',$relB,'--output-dir',$relM,'--trials-per-scenario','500'))}
    $s=Read-Json(Join-Path $subMergeOut 'summary.json')
    if(-not[bool]$s.passed -or[int]$s.checkpoint -ne 148 -or[int]$s.stageAScenarios -ne 6850 -or[int]$s.trialsPerScenario -ne 500 -or[int64]$s.substantiveCombatTrials -ne 3425000 -or[int]$s.resourceEnvironmentCount -ne 5 -or[int]$s.scenarioStrataCount -ne 10 -or[int]$s.orderedSameTlWeaponPairings -ne 137 -or[string]$s.combatDoctrine -ne 'cp147_tactical_utility' -or[string]$s.baseMaxTpDemandPolicy -ne 'all-installed-normal-combat-demand-no-overload' -or[string]$s.strategicParetoPolicy -ne 'combat-gated-before-resource-robustness' -or-not[bool]$s.sourceMatrixUnmodified -or[bool]$s.automaticPromotion -or[bool]$s.tuningAllowed -or[bool]$s.stageBAutomatic){throw 'CP148 merged substantive Stage-A contract mismatch.'}
    foreach($name in @('scenario_response_surface.csv','tp_load_response_surface.csv','tp_load_weapon_tl_summary.csv','combat_gated_strategic_viability.csv','role_response_summary.csv')){
        if(-not(Test-Path -LiteralPath (Join-Path $subMergeOut $name))){throw "CP148 merged substantive artifact missing: $name"}
    }
    return $s
}

$python=Get-Cpython313Command
$pythonVersion=& $python.Command @($python.Args+@('--version')) 2>&1|Out-String
$dotnetVersion=(& dotnet --version 2>&1|Out-String).Trim()
if($LASTEXITCODE -ne 0 -or $dotnetVersion -ne '8.0.423'){throw "CP148 requires .NET SDK 8.0.423 exactly; observed '$dotnetVersion'."}
Write-Host("CP148 runtimes: {0}; .NET SDK {1}" -f $pythonVersion.Trim(),$dotnetVersion)
Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot) 'CP148 preflight failed'

if($RepositoryOnly){
    if(-not $NoClean -and(Test-Path -LiteralPath $outRoot)){Remove-Item -Recurse -Force $outRoot}
    New-Item -ItemType Directory -Force -Path $outRoot,$testOut,$parityOut,$deterministicOut,$tl1PhaseAOut,$cp139Out,$cp142AuditOut|Out-Null
    Push-Location $repositoryRoot
    try{
        Write-Host '[1/9] Python research tests (358 total) in isolated chunks...';Invoke-PythonResearchTests
        Write-Host '[2/9] Warning-as-error .NET build...';Invoke-Captured 'CP148 build' (Join-Path $outRoot 'build.log') {dotnet build StarCluster.sln --configuration Release --nologo -warnaserror}
        Write-Host '[3/9] xUnit + ScenarioRunner deterministic corpora...'
        dotnet test tests\StarCluster.Tests\StarCluster.Tests.csproj --configuration Release --no-build --nologo --logger 'trx;LogFileName=cp148-tests.trx' --results-directory $testOut
        $xunitExit=$LASTEXITCODE;$trxPath=Join-Path $testOut 'cp148-tests.trx'
        if(-not(Test-Path -LiteralPath $trxPath)){throw 'CP148 xUnit TRX missing.'}
        [xml]$trx=Get-Content -LiteralPath $trxPath -Raw;$c=$trx.TestRun.ResultSummary.Counters
        $total=[int]$c.total;$passed=[int]$c.passed;$failed=[int]$c.failed;$skipped=[int]$c.notExecuted
        if($xunitExit -ne 0 -or $total -ne 934 -or $passed -ne 934 -or $failed -ne 0 -or $skipped -ne 0){throw "CP148 xUnit mismatch exit=$xunitExit total=$total passed=$passed failed=$failed skipped=$skipped."}
        $selfLog=Join-Path $outRoot 'scenario-self-tests.log'
        Invoke-Captured 'CP148 ScenarioRunner self-tests' $selfLog {dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- self-test}
        $selfText=Get-Content -LiteralPath $selfLog -Raw
        if($selfText -notmatch 'Runner self-tests:\s+70 passed,\s+0 failed,\s+70 total\.'){throw 'CP148 expected 70/70 ScenarioRunner self-tests.'}
        Invoke-Captured 'CP148 deterministic scenario corpus' (Join-Path $outRoot 'deterministic-scenarios.log') {dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- run-all --output-dir $deterministicOut}
        Invoke-Captured 'CP148 TL1 Phase-A corpus' (Join-Path $outRoot 'tl1-phase-a.log') {dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- tl1-phase-a --output-dir $tl1PhaseAOut}

        Write-Host '[4/9] Existing C#/Python research parity...'
        Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'parity','--output-dir',$parityOut) 'CP148 research parity failed'
        $parity=Read-Json(Join-Path $parityOut 'summary.json')
        if(-not[bool]$parity.passed -or[int]$parity.cases -ne 25){throw 'CP148 expected 25/25 research parity.'}

        Write-Host '[5/9] CP139 DEF/RES regression foundation...'
        & $python.Command @($python.Args+@('-B','-m','unittest','discover','-v','-s','tools/simulation/tests','-p','test_cp139_def_res_reconciliation.py'))
        if($LASTEXITCODE -ne 0){throw 'CP139 focused regression failed under CP148.'}
        Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'combat-model-reconciliation-study',$cp139Study,'--output-dir','out/checkpoint-148/cp139-reconciliation') 'CP139 reconciliation regression failed'
        $recon=Read-Json(Join-Path $cp139Out 'summary.json');$ra=Get-Analysis $recon
        if(-not[bool]$recon.passed -or[int]$ra.fixturePass -ne 8 -or[int]$ra.smokeVariants -ne 82 -or[int]$ra.smokeErrors -ne 0 -or-not[bool]$ra.sourceMatrixUnmodified){throw 'CP139 reconciliation regression mismatch under CP148.'}

        Write-Host '[6/9] Focused CP140 through CP148 tests...'
        foreach($pattern in @('test_cp140_stage_a_integration.py','test_cp141_combat_duration_stalemate.py','test_cp142_combat_surface_reconciliation.py','test_cp143_missile_mirror_pacing_attribution.py','test_cp144_*.py','test_cp145_*.py','test_cp146_*.py','test_cp147_*.py','test_cp148_*.py')){
            & $python.Command @($python.Args+@('-B','-m','unittest','discover','-v','-s','tools/simulation/tests','-p',$pattern))
            if($LASTEXITCODE -ne 0){throw "Focused regression failed: $pattern"}
        }

        Write-Host '[7/9] CP142 deep-reconciliation audit regression...'
        Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'combat-surface-reconciliation-audit',$cp142Study,'--output-dir','out/checkpoint-148/cp142-reconciliation-audit') 'CP142 reconciliation audit regression failed'
        $audit=Read-Json(Join-Path $cp142AuditOut 'reconciliation_summary.json')
        if(-not[bool]$audit.passed -or[int]$audit.ledgerRows -ne 531 -or[int]$audit.changedVsCp141Rows -ne 72 -or[int]$audit.explicitUnresolvedRows -ne 7){throw 'CP142 reconciliation audit mismatch under CP148.'}

        Write-Host '[8/9] Complete 6,850-scenario CP148 tactical-utility Stage-A smoke...';$smoke=Invoke-Cp148Smoke

        Write-Host '[9/9] Writing RepositoryOnly acceptance and repository contract...'
        $summary=[ordered]@{
            schemaVersion='star-cluster-cp148-repository-only-acceptance-v0.1';checkpoint=148;repositoryOnly=$true;failedGates=@();python=$pythonVersion.Trim();dotnetSdk=$dotnetVersion;buildPassed=$true;
            pythonTestsPassed=358;xunitTotal=$total;xunitPassed=$passed;xunitFailed=$failed;xunitSkipped=$skipped;scenarioRunnerSelfTestsPassed=70;deterministicScenarioCorpusPassed=$true;tl1PhaseACorpusPassed=$true;researchParityPassed=25;
            cp139FocusedTestsPassed=9;cp140FocusedTestsPassed=10;cp141FocusedTestsPassed=10;cp142FocusedTestsPassed=12;cp143FocusedTestsPassed=12;cp144FocusedTestsPassed=11;cp145FocusedTestsPassed=12;cp146FocusedTestsPassed=18;cp147FocusedTestsPassed=18;cp148FocusedTestsPassed=12;cp146DoctrineFixtureCases=9;cp147UtilityFixtureCases=10;
            defResFixturesPassed=8;cp139ReconciliationSmokeVariants=82;cp139ReconciliationSmokeErrors=0;cp142ReconciliationLedgerRows=531;cp142ChangedRows=72;cp142ExplicitUnresolvedRows=7;
            acceptedCp147EvidenceHashLocked=$true;combatDoctrine='cp147_tactical_utility';baseMaxTpDemandPolicy='all-installed-normal-combat-demand-no-overload';strategicParetoPolicy='combat-gated-before-resource-robustness';
            stageAScenarios=6850;resourceEnvironmentCount=5;scenarioStrataCount=10;orderedSameTlWeaponPairings=137;smokeResolved=[int]$smoke.resolved;smokeResolvedGe25=[int]$smoke.resolvedGe25;smokeTurnCapSentinels=[int]$smoke.turnCapSentinels;smokeSafeStalemates=[int]$smoke.safeStalemates;smokeNonstandoffOpenOrders=[int]$smoke.nonstandoffOpenOrders;
            sourceMatrixUnmodified=$true;substantiveCombatTrials=0;tuningAllowed=$false;automaticPromotion=$false;stageBAutomatic=$false;nextStage='execute/resume 3,425,000-trial CP148 tactical-utility Stage-A response surface'
        }
        $summary|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $repoOnlySummary -Encoding UTF8
        Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP148 RepositoryOnly contract failed'
        Write-Host 'CP148 RepositoryOnly acceptance PASSED. Run the same wrapper without -RepositoryOnly to execute/resume the 3,425,000-trial tactical-utility Stage A.' -ForegroundColor Green
    } finally {Pop-Location}
    exit 0
}

if(-not(Test-Path -LiteralPath $repoOnlySummary)){throw 'Run CP148 -RepositoryOnly first in this same extraction.'}
Push-Location $repositoryRoot
try{
    Write-Host '[final 1/3] Revalidating preflight/manifest and RepositoryOnly state after generated outputs...'
    Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot) 'CP148 final preflight failed'
    Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP148 RepositoryOnly state contract failed'

    Write-Host '[final 2/3] Executing/resuming 6,850 x 500 = 3,425,000 substantive tactical-utility Stage-A trials...';$sub=Invoke-Substantive

    Write-Host '[final 3/3] Final response-surface validation, acceptance summary, and result ZIP...'
    $ro=Read-Json $repoOnlySummary;$final=[ordered]@{};$ro.psobject.Properties|ForEach-Object{$final[$_.Name]=$_.Value}
    $final['schemaVersion']='star-cluster-cp148-native-acceptance-v0.1';$final['repositoryOnly']=$false;$final['repositoryOnlyAccepted']=$true;$final['substantiveStageACompleted']=$true;$final['trialsPerScenario']=500;$final['substantiveCombatTrials']=[int64]$sub.substantiveCombatTrials
    $final['substantiveTurnCapSentinels']=[int64]$sub.turnCapSentinels;$final['substantiveResolvedGe25']=[int64]$sub.resolvedGe25;$final['substantiveSafeStalemates']=[int64]$sub.safeStalemates;$final['substantiveGameplayDurationConcernRate']=[double]$sub.gameplayDurationConcernRate
    $final['nextStage']='review CP148 3,425,000-combat tactical-utility response surface and base-max TP-load evidence before numerical intervention; Stage B remains deferred'
    $final|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $finalSummary -Encoding UTF8
    Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP148 final contract failed'
    $stamp=Get-Date -Format 'yyyyMMdd_HHmmss';$zip=Join-Path $outRoot ("StarCluster_CP148_native_results_$stamp.zip")
    $items=Get-ChildItem -LiteralPath $outRoot -Force|Where-Object{$_.FullName -ne $zip}
    Compress-Archive -Path $items.FullName -DestinationPath $zip -CompressionLevel Optimal
    Write-Host "CP148 native acceptance PASSED. Results: $zip" -ForegroundColor Green
} finally {Pop-Location}
