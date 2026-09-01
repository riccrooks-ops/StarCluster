[CmdletBinding()]
param([switch]$RepositoryOnly,[switch]$NoClean,[int]$Jobs=24)
Set-StrictMode -Version 2.0
$ErrorActionPreference='Stop'

$repositoryRoot=(Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$preflight=Join-Path $PSScriptRoot 'preflight_checkpoint_151.py'
$contract=Join-Path $PSScriptRoot 'test_checkpoint_151_contract.py'
$research=Join-Path $repositoryRoot 'tools\simulation\run_starcluster_research.py'
$cp139Study='docs/archive/testing/pre-cp165-active/cp139_def_res_reconciliation_study_v0_1.json'
$cp142Study='docs/archive/testing/pre-cp165-active/cp142_combat_surface_deep_reconciliation_study_v0_1.json'
$cp151Study='docs/archive/testing/pre-cp165-active/cp151_point_scale_multivariate_response_v0_1.json'
$outRoot=Join-Path $repositoryRoot 'out\checkpoint-151'
$testOut=Join-Path $outRoot 'xunit'
$parityOut=Join-Path $outRoot 'research-parity'
$deterministicOut=Join-Path $outRoot 'deterministic-scenarios'
$tl1PhaseAOut=Join-Path $outRoot 'tl1-phase-a'
$cp139Out=Join-Path $outRoot 'cp139-reconciliation'
$cp142AuditOut=Join-Path $outRoot 'cp142-reconciliation-audit'
$planOut=Join-Path $outRoot 'point-scale-plan'
$equivalenceOut=Join-Path $outRoot 'point-scale-equivalence'
$smokeRoot=Join-Path $outRoot 'point-scale-smoke'
$subBatchRoot=Join-Path $outRoot 'point-scale-substantive-batches'
$subMergeOut=Join-Path $outRoot 'point-scale-merged'
$repoOnlySummary=Join-Path $outRoot 'CP151_REPOSITORY_ONLY_ACCEPTANCE.json'
$finalSummary=Join-Path $outRoot 'CP151_NATIVE_ACCEPTANCE_SUMMARY.json'
$candidateCounts=@{1=261;2=263;3=263;4=263;5=263;6=265;7=265;8=265;9=265}
$contextCounts=@{1=450;2=800;3=800;4=800;5=800;6=800;7=800;8=800;9=800}

function Get-Cpython313Command {
    $candidates=@(@{Command='py';Args=@('-3.13')},@{Command='python';Args=@()},@{Command='python3';Args=@()})
    foreach($candidate in $candidates){
        $cmd=Get-Command $candidate.Command -ErrorAction SilentlyContinue
        if($null -eq $cmd){continue}
        $v=& $candidate.Command @($candidate.Args+@('--version')) 2>&1|Out-String
        if($LASTEXITCODE -eq 0 -and $v -match 'Python\s+3\.13(?:\.|\s|$)'){return $candidate}
    }
    throw 'CP151 requires Python 3.13.'
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
function Invoke-PythonWithSimulationPath([scriptblock]$Body){
    $simulationRoot=Join-Path $repositoryRoot 'tools\simulation';$oldPythonPath=$env:PYTHONPATH
    try{
        if([string]::IsNullOrWhiteSpace($oldPythonPath)){$env:PYTHONPATH=$simulationRoot}else{$env:PYTHONPATH=$simulationRoot+[System.IO.Path]::PathSeparator+$oldPythonPath}
        & $Body
    } finally {$env:PYTHONPATH=$oldPythonPath}
}
function Invoke-PythonFocusedPattern([string]$Pattern,[string]$Failure){
    Invoke-PythonWithSimulationPath {
        & $python.Command @($python.Args+@('-B','-m','unittest','discover','-v','-s','tools/simulation/tests','-p',$Pattern))
        if($LASTEXITCODE -ne 0){throw $Failure}
    }
}
function Invoke-PythonResearchTests {
    $files=Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'tools\simulation\tests') -Filter 'test_*.py' | Sort-Object Name
    if($files.Count -ne 42){throw "CP151 expected 42 Python test modules, found $($files.Count)."}
    $chunks=@(@($files[0..12]),@($files[13..18]),@($files[19..24]),@($files[25..38]),@($files[39]),@($files[40]),@($files[41]))
    Invoke-PythonWithSimulationPath {
        for($i=0;$i -lt $chunks.Count;$i++){
            $modules=@($chunks[$i] | ForEach-Object{"tools.simulation.tests.$($_.BaseName)"})
            Write-Host("       Python test chunk {0}/7 ({1} modules)..." -f ($i+1),$modules.Count)
            & $python.Command @($python.Args+@('-B','-m','unittest')+$modules)
            if($LASTEXITCODE -ne 0){throw "CP151 Python test chunk $($i+1) failed."}
        }
    }
}
function Invoke-Cp151Plan {
    if(Test-Path -LiteralPath $planOut){Remove-Item -Recurse -Force $planOut};New-Item -ItemType Directory -Force -Path $planOut|Out-Null
    $rel=Relative-To-Repo $planOut;$log=Join-Path $planOut 'console.log'
    Invoke-Captured 'CP151 point-scale plan' $log {& $python.Command @($python.Args+@('-B',$research,'--repo',$repositoryRoot,'point-scale-plan',$cp151Study,'--output-dir',$rel))}
    $s=Read-Json(Join-Path $planOut 'summary.json')
    if(-not[bool]$s.passed -or[int]$s.tlCandidateCount -ne 2373 -or[int]$s.candidateContextCells -ne 1807050 -or[int]$s.trialsPerCandidateContext -ne 25 -or[int64]$s.substantiveCombatTrials -ne 45176250 -or[int]$s.smokeCombatTrials -ne 118650 -or[int]$s.pointScale -ne 2){throw 'CP151 plan contract mismatch.'}
    return $s
}
function Invoke-Cp151Equivalence {
    if(Test-Path -LiteralPath $equivalenceOut){Remove-Item -Recurse -Force $equivalenceOut};New-Item -ItemType Directory -Force -Path $equivalenceOut|Out-Null
    $rel=Relative-To-Repo $equivalenceOut;$log=Join-Path $equivalenceOut 'console.log'
    Invoke-Captured 'CP151 full x2 equivalence audit' $log {& $python.Command @($python.Args+@('-B',$research,'--repo',$repositoryRoot,'point-scale-equivalence',$cp151Study,'--output-dir',$rel,'--jobs',$Jobs))}
    $s=Read-Json(Join-Path $equivalenceOut 'summary.json')
    if(-not[bool]$s.passed -or[int]$s.checkpoint -ne 151 -or[int]$s.pairedScenarioIdentities -ne 6850 -or[int]$s.legacyCombatExecutions -ne 6850 -or[int]$s.scaledCombatExecutions -ne 6850 -or[int]$s.mismatchedScenarioIdentities -ne 0){throw 'CP151 equivalence contract mismatch.'}
    return $s
}
function Invoke-Cp151Smoke {
    if(Test-Path -LiteralPath $smokeRoot){Remove-Item -Recurse -Force $smokeRoot};New-Item -ItemType Directory -Force -Path $smokeRoot|Out-Null
    $totalCombats=[int64]0;$totalCaps=[int64]0
    for($tl=1;$tl -le 9;$tl++){
        $n=[int]$candidateCounts[$tl];$dir=Join-Path $smokeRoot ("tl{0:D2}" -f $tl);New-Item -ItemType Directory -Force -Path $dir|Out-Null
        $rel=Relative-To-Repo $dir;$log=Join-Path $dir 'console.log';$expectedRows=$n*50
        Write-Host("       CP151 smoke TL{0}: {1} candidates x 50 contexts x 1 trial = {2:N0} combats" -f $tl,$n,$expectedRows)
        Invoke-Captured "CP151 smoke TL$tl" $log {& $python.Command @($python.Args+@('-B',$research,'--repo',$repositoryRoot,'point-scale-sweep',$cp151Study,'--output-dir',$rel,'--jobs',$Jobs,'--tl',$tl,'--candidate-start','0','--candidate-end',$n,'--trials','1','--smoke-panel'))}
        $s=Read-Json(Join-Path $dir 'summary.json')
        if(-not[bool]$s.passed -or[int]$s.checkpoint -ne 151 -or-not[bool]$s.smokePanel -or[int]$s.tl -ne $tl -or[int]$s.candidates -ne $n -or[int]$s.contextsPerCandidate -ne 50 -or[int]$s.candidateContextCells -ne $expectedRows -or[int]$s.trialsPerContext -ne 1 -or[int]$s.combatTrials -ne $expectedRows -or[int]$s.errors -ne 0){throw "CP151 smoke TL$tl contract mismatch."}
        $totalCombats += [int64]$s.combatTrials;$totalCaps += [int64]$s.turnCapSentinels
    }
    if($totalCombats -ne 118650){throw "CP151 smoke total mismatch: $totalCombats."}
    return [pscustomobject]@{combatTrials=$totalCombats;turnCapSentinels=$totalCaps;errors=0}
}
function Test-PointScaleBatch([string]$Dir,[int]$Tl,[int]$Start,[int]$End){
    $summaryPath=Join-Path $Dir 'summary.json';$csvPath=Join-Path $Dir 'point_scale_candidate_context_results.csv'
    if(-not(Test-Path -LiteralPath $summaryPath) -or -not(Test-Path -LiteralPath $csvPath)){return $false}
    try{
        $s=Read-Json $summaryPath;$contexts=[int]$contextCounts[$Tl];$candidates=$End-$Start;$expectedRows=$candidates*$contexts
        if(-not[bool]$s.passed -or[int]$s.checkpoint -ne 151 -or[bool]$s.smokePanel -or[int]$s.tl -ne $Tl -or[int]$s.candidateStart -ne $Start -or[int]$s.candidateEnd -ne $End -or[int]$s.candidates -ne $candidates -or[int]$s.contextsPerCandidate -ne $contexts -or[int]$s.candidateContextCells -ne $expectedRows -or[int]$s.trialsPerContext -ne 25 -or[int64]$s.combatTrials -ne ([int64]$expectedRows*25) -or[int]$s.errors -ne 0){return $false}
        $rows=@(Import-Csv -LiteralPath $csvPath);if($rows.Count -ne $expectedRows){return $false}
        $counts=@{}
        foreach($r in $rows){
            if([int]$r.tl -ne $Tl -or[int]$r.trials -ne 25 -or[int]$r.error_trials -ne 0){return $false}
            $cid=[string]$r.candidate_id;if(-not $counts.ContainsKey($cid)){$counts[$cid]=0};$counts[$cid]++
        }
        if($counts.Count -ne $candidates){return $false}
        for($i=$Start;$i -lt $End;$i++){$cid=("PS{0:D2}-{1:D3}" -f $Tl,$i);if(-not $counts.ContainsKey($cid) -or[int]$counts[$cid] -ne $contexts){return $false}}
        return $true
    } catch {return $false}
}
function Invoke-Substantive {
    New-Item -ItemType Directory -Force -Path $subBatchRoot|Out-Null
    if(Test-Path -LiteralPath $subMergeOut){Remove-Item -Recurse -Force $subMergeOut};New-Item -ItemType Directory -Force -Path $subMergeOut|Out-Null
    $batchNumber=0;$totalBatches=153
    for($tl=1;$tl -le 9;$tl++){
        $limit=[int]$candidateCounts[$tl];$start=0
        while($start -lt $limit){
            $end=[Math]::Min($start+16,$limit);$batchNumber++;$dir=Join-Path $subBatchRoot ("tl{0:D2}_{1:D3}_{2:D3}" -f $tl,$start,$end)
            if(Test-PointScaleBatch $dir $tl $start $end){Write-Host("       CP151 substantive batch {0}/{1}: TL{2} candidates {3}-{4} already valid; reusing." -f $batchNumber,$totalBatches,$tl,$start,($end-1))}
            else{
                if(Test-Path -LiteralPath $dir){Remove-Item -Recurse -Force $dir};New-Item -ItemType Directory -Force -Path $dir|Out-Null
                $rel=Relative-To-Repo $dir;$log=Join-Path $dir 'console.log';$contexts=[int]$contextCounts[$tl];$combats=[int64]($end-$start)*$contexts*25
                Write-Host("       CP151 substantive batch {0}/{1}: TL{2} candidates {3}-{4}, {5:N0} combats" -f $batchNumber,$totalBatches,$tl,$start,($end-1),$combats)
                Invoke-Captured "CP151 substantive TL$tl candidates $start-$end" $log {& $python.Command @($python.Args+@('-B',$research,'--repo',$repositoryRoot,'point-scale-sweep',$cp151Study,'--output-dir',$rel,'--jobs',$Jobs,'--tl',$tl,'--candidate-start',$start,'--candidate-end',$end,'--trials','25'))}
                if(-not(Test-PointScaleBatch $dir $tl $start $end)){throw "CP151 substantive TL$tl candidate batch $start-$end failed validation after execution."}
            }
            $start=$end
        }
    }
    if($batchNumber -ne 153){throw "CP151 substantive batch count mismatch: $batchNumber."}
    $relB=Relative-To-Repo $subBatchRoot;$relM=Relative-To-Repo $subMergeOut;$log=Join-Path $subMergeOut 'console.log'
    Invoke-Captured 'CP151 point-scale merge/response surfaces' $log {& $python.Command @($python.Args+@('-B',$research,'--repo',$repositoryRoot,'point-scale-merge',$cp151Study,'--batch-root',$relB,'--output-dir',$relM,'--trials','25'))}
    $s=Read-Json(Join-Path $subMergeOut 'summary.json')
    if(-not[bool]$s.passed -or[int]$s.checkpoint -ne 151 -or[int]$s.candidateContextCells -ne 1807050 -or[int]$s.tlCandidateCount -ne 2373 -or[int]$s.trialsPerCandidateContext -ne 25 -or[int64]$s.substantiveCombatTrials -ne 45176250 -or[int]$s.errorTrials -ne 0 -or[bool]$s.automaticPromotion -or[bool]$s.tuningAllowed -or[bool]$s.stageBAutomatic){throw 'CP151 merged substantive contract mismatch.'}
    foreach($name in @('batch_merge_audit.csv','point_scale_candidate_ledger.csv','point_scale_design_summary.csv','point_scale_aux_scaling_audit.csv','point_scale_candidate_summary.csv','point_scale_candidate_family_response.csv','point_scale_candidate_pair_response.csv','point_scale_candidate_resource_response.csv','point_scale_candidate_stratum_response.csv','point_scale_factor_family_marginals.csv','point_scale_pairwise_factor_family_response.csv','point_scale_axial_family_effects.csv','research_center_scenario_response.csv')){
        if(-not(Test-Path -LiteralPath (Join-Path $subMergeOut $name))){throw "CP151 merged substantive artifact missing: $name"}
    }
    return $s
}
function New-ResultZip {
    $stamp=Get-Date -Format 'yyyyMMdd_HHmmss';$zip=Join-Path $outRoot ("StarCluster_CP151_native_results_$stamp.zip")
    $stage=Join-Path $repositoryRoot 'out\checkpoint-151-package-staging'
    if(Test-Path -LiteralPath $stage){Remove-Item -Recurse -Force $stage};New-Item -ItemType Directory -Force -Path $stage|Out-Null
    foreach($item in Get-ChildItem -LiteralPath $outRoot -Force){
        if($item.FullName -eq $zip -or $item.Name -eq 'point-scale-substantive-batches'){continue}
        Copy-Item -LiteralPath $item.FullName -Destination $stage -Recurse -Force
    }
    $batchSummary=Join-Path $stage 'point-scale-substantive-batch-summaries';New-Item -ItemType Directory -Force -Path $batchSummary|Out-Null
    foreach($d in Get-ChildItem -LiteralPath $subBatchRoot -Directory | Sort-Object Name){$sp=Join-Path $d.FullName 'summary.json';if(Test-Path -LiteralPath $sp){Copy-Item -LiteralPath $sp -Destination (Join-Path $batchSummary ($d.Name+'_summary.json')) -Force}}
    Compress-Archive -Path (Join-Path $stage '*') -DestinationPath $zip -CompressionLevel Optimal
    Remove-Item -Recurse -Force $stage
    return $zip
}

$python=Get-Cpython313Command
$pythonVersion=& $python.Command @($python.Args+@('--version')) 2>&1|Out-String
$dotnetVersion=(& dotnet --version 2>&1|Out-String).Trim()
if($LASTEXITCODE -ne 0 -or $dotnetVersion -ne '8.0.423'){throw "CP151 requires .NET SDK 8.0.423 exactly; observed '$dotnetVersion'."}
Write-Host("CP151 runtimes: {0}; .NET SDK {1}" -f $pythonVersion.Trim(),$dotnetVersion)
Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot) 'CP151 preflight failed'

if($RepositoryOnly){
    if(-not $NoClean -and(Test-Path -LiteralPath $outRoot)){Remove-Item -Recurse -Force $outRoot}
    New-Item -ItemType Directory -Force -Path $outRoot,$testOut,$parityOut,$deterministicOut,$tl1PhaseAOut,$cp139Out,$cp142AuditOut|Out-Null
    Push-Location $repositoryRoot
    try{
        Write-Host '[1/11] Python research tests (408 total) in isolated chunks...';Invoke-PythonResearchTests
        Write-Host '[2/11] Warning-as-error .NET build...';Invoke-Captured 'CP151 build' (Join-Path $outRoot 'build.log') {dotnet build StarCluster.sln --configuration Release --nologo -warnaserror}
        Write-Host '[3/11] xUnit + ScenarioRunner deterministic corpora...'
        dotnet test tests\StarCluster.Tests\StarCluster.Tests.csproj --configuration Release --no-build --nologo --logger 'trx;LogFileName=cp151-tests.trx' --results-directory $testOut
        $xunitExit=$LASTEXITCODE;$trxPath=Join-Path $testOut 'cp151-tests.trx';if(-not(Test-Path -LiteralPath $trxPath)){throw 'CP151 xUnit TRX missing.'}
        [xml]$trx=Get-Content -LiteralPath $trxPath -Raw;$c=$trx.TestRun.ResultSummary.Counters;$total=[int]$c.total;$passed=[int]$c.passed;$failed=[int]$c.failed;$skipped=[int]$c.notExecuted
        if($xunitExit -ne 0 -or $total -ne 934 -or $passed -ne 934 -or $failed -ne 0 -or $skipped -ne 0){throw "CP151 xUnit mismatch exit=$xunitExit total=$total passed=$passed failed=$failed skipped=$skipped."}
        $selfLog=Join-Path $outRoot 'scenario-self-tests.log';Invoke-Captured 'CP151 ScenarioRunner self-tests' $selfLog {dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- self-test}
        $selfText=Get-Content -LiteralPath $selfLog -Raw;if($selfText -notmatch 'Runner self-tests:\s+70 passed,\s+0 failed,\s+70 total\.'){throw 'CP151 expected 70/70 ScenarioRunner self-tests.'}
        Invoke-Captured 'CP151 deterministic scenario corpus' (Join-Path $outRoot 'deterministic-scenarios.log') {dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- run-all --output-dir $deterministicOut}
        Invoke-Captured 'CP151 TL1 Phase-A corpus' (Join-Path $outRoot 'tl1-phase-a.log') {dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- tl1-phase-a --output-dir $tl1PhaseAOut}
        Write-Host '[4/11] Existing C#/Python research parity...';Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'parity','--output-dir',$parityOut) 'CP151 research parity failed'
        $parity=Read-Json(Join-Path $parityOut 'summary.json');if(-not[bool]$parity.passed -or[int]$parity.cases -ne 25){throw 'CP151 expected 25/25 research parity.'}
        Write-Host '[5/11] CP139 DEF/RES regression foundation...'
        Invoke-PythonFocusedPattern 'test_cp139_def_res_reconciliation.py' 'CP139 focused regression failed under CP151.'
        Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'combat-model-reconciliation-study',$cp139Study,'--output-dir','out/checkpoint-151/cp139-reconciliation') 'CP139 reconciliation regression failed'
        $recon=Read-Json(Join-Path $cp139Out 'summary.json');$ra=Get-Analysis $recon;if(-not[bool]$recon.passed -or[int]$ra.fixturePass -ne 8 -or[int]$ra.smokeVariants -ne 82 -or[int]$ra.smokeErrors -ne 0 -or-not[bool]$ra.sourceMatrixUnmodified){throw 'CP139 reconciliation mismatch under CP151.'}
        Write-Host '[6/11] Focused CP140 through CP151 tests...'
        foreach($pattern in @('test_cp140_stage_a_integration.py','test_cp141_combat_duration_stalemate.py','test_cp142_combat_surface_reconciliation.py','test_cp143_missile_mirror_pacing_attribution.py','test_cp144_*.py','test_cp145_*.py','test_cp146_*.py','test_cp147_*.py','test_cp148_*.py','test_cp149_*.py','test_cp150_*.py','test_cp151_*.py')){Invoke-PythonFocusedPattern $pattern "Focused regression failed: $pattern"}
        Write-Host '[7/11] CP142 deep-reconciliation audit regression...';Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'combat-surface-reconciliation-audit',$cp142Study,'--output-dir','out/checkpoint-151/cp142-reconciliation-audit') 'CP142 reconciliation audit regression failed'
        $audit=Read-Json(Join-Path $cp142AuditOut 'reconciliation_summary.json');if(-not[bool]$audit.passed -or[int]$audit.ledgerRows -ne 531 -or[int]$audit.changedVsCp141Rows -ne 72 -or[int]$audit.explicitUnresolvedRows -ne 7){throw 'CP142 reconciliation audit mismatch under CP151.'}
        Write-Host '[8/11] CP151 45.17625M-combat point-scale plan...';$plan=Invoke-Cp151Plan
        Write-Host '[9/11] CP151 strict x2 same-seed equivalence (6,850 paired identities)...';$eq=Invoke-Cp151Equivalence
        Write-Host '[10/11] CP151 all-candidate representative smoke (118,650 combats)...';$smoke=Invoke-Cp151Smoke
        Write-Host '[11/11] Writing RepositoryOnly acceptance and repository contract...'
        $summary=[ordered]@{
            schemaVersion='star-cluster-cp151-repository-only-acceptance-v0.1';checkpoint=151;repositoryOnly=$true;failedGates=@();python=$pythonVersion.Trim();dotnetSdk=$dotnetVersion;buildPassed=$true;
            pythonTestsPassed=408;xunitTotal=$total;xunitPassed=$passed;xunitFailed=$failed;xunitSkipped=$skipped;scenarioRunnerSelfTestsPassed=70;deterministicScenarioCorpusPassed=$true;tl1PhaseACorpusPassed=$true;researchParityPassed=25;
            cp139FocusedTestsPassed=9;cp140FocusedTestsPassed=10;cp141FocusedTestsPassed=10;cp142FocusedTestsPassed=12;cp143FocusedTestsPassed=12;cp144FocusedTestsPassed=11;cp145FocusedTestsPassed=12;cp146FocusedTestsPassed=18;cp147FocusedTestsPassed=18;cp148FocusedTestsPassed=12;cp149FocusedTestsPassed=16;cp150FocusedTestsPassed=16;cp151FocusedTestsPassed=18;cp146DoctrineFixtureCases=9;cp147UtilityFixtureCases=10;
            defResFixturesPassed=8;cp139ReconciliationSmokeVariants=82;cp139ReconciliationSmokeErrors=0;cp142ReconciliationLedgerRows=531;cp142ChangedRows=72;cp142ExplicitUnresolvedRows=7;
            acceptedCp150EvidenceHashLocked=$true;combatDoctrine='cp147_tactical_utility';pointScale=2;scaledFields=@('weapon DAM','Hull capacity','Shield capacity','Armor capacity');unchangedFields=@('ACC','DEF','RES','TP','range','Space');penetrationPolicy='K APEN and E SPEN +/-1 only; missile APEN/SPEN zero';
            equivalencePairedScenarioIdentities=[int]$eq.pairedScenarioIdentities;equivalenceMismatches=[int]$eq.mismatchedScenarioIdentities;tlCandidateCount=2373;candidateContextCells=1807050;smokeCombatTrials=[int64]$smoke.combatTrials;smokeTurnCapSentinels=[int64]$smoke.turnCapSentinels;smokeErrors=0;
            sourceMatrixUnmodified=$true;substantiveCombatTrials=0;tuningAllowed=$false;automaticPromotion=$false;stageBAutomatic=$false;nextStage='execute/resume 45,176,250-trial CP151 point-scale multivariate response surface'
        }
        $summary|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $repoOnlySummary -Encoding UTF8
        Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP151 RepositoryOnly contract failed'
        Write-Host 'CP151 RepositoryOnly acceptance PASSED. Run the same wrapper without -RepositoryOnly to execute/resume the 45.17625M-combat substantive sweep.' -ForegroundColor Green
    } finally {Pop-Location}
    exit 0
}

if(-not(Test-Path -LiteralPath $repoOnlySummary)){throw 'Run CP151 -RepositoryOnly first in this same extraction.'}
Push-Location $repositoryRoot
try{
    Write-Host '[final 1/3] Revalidating preflight/manifest and RepositoryOnly state after generated outputs...'
    Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot) 'CP151 final preflight failed'
    Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP151 RepositoryOnly state contract failed'
    Write-Host '[final 2/3] Executing/resuming 45,176,250 substantive point-scale combats...';$sub=Invoke-Substantive
    Write-Host '[final 3/3] Final response-surface validation, acceptance summary, and result ZIP...'
    $ro=Read-Json $repoOnlySummary;$final=[ordered]@{};$ro.psobject.Properties|ForEach-Object{$final[$_.Name]=$_.Value}
    $final['schemaVersion']='star-cluster-cp151-native-acceptance-v0.1';$final['repositoryOnly']=$false;$final['repositoryOnlyAccepted']=$true;$final['substantiveSweepCompleted']=$true;$final['trialsPerCandidateContext']=25;$final['substantiveCombatTrials']=[int64]$sub.substantiveCombatTrials;$final['substantiveTurnCapSentinels']=[int64]$sub.turnCapSentinels;$final['substantiveErrorTrials']=[int64]$sub.errorTrials
    $final['nextStage']='analyze CP151 x2 point-scale response surface; select coherent offensive/defensive centers and non-regressing technology ladders before any source numerical promotion'
    $final|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $finalSummary -Encoding UTF8
    Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP151 final contract failed'
    $zip=New-ResultZip
    Write-Host "CP151 native acceptance PASSED. Results: $zip" -ForegroundColor Green
} finally {Pop-Location}
