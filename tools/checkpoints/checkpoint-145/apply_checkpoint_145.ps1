[CmdletBinding()]
param([switch]$RepositoryOnly,[switch]$NoClean,[int]$Jobs=24)
Set-StrictMode -Version 2.0
$ErrorActionPreference='Stop'

$repositoryRoot=(Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$preflight=Join-Path $PSScriptRoot 'preflight_checkpoint_145.py'
$contract=Join-Path $PSScriptRoot 'test_checkpoint_145_contract.py'
$research=Join-Path $repositoryRoot 'tools\simulation\run_starcluster_research.py'
$cp139Study='docs/archive/testing/pre-cp165-active/cp139_def_res_reconciliation_study_v0_1.json'
$cp142Study='docs/archive/testing/pre-cp165-active/cp142_combat_surface_deep_reconciliation_study_v0_1.json'
$cp144Study='docs/archive/testing/pre-cp165-active/cp144_whole_combat_stage_a_response_surface_study_v0_1.json'
$cp145Study='docs/archive/testing/pre-cp165-active/cp145_stage_a_diagnostic_attribution_study_v0_1.json'
$outRoot=Join-Path $repositoryRoot 'out\checkpoint-145'
$testOut=Join-Path $outRoot 'xunit'
$parityOut=Join-Path $outRoot 'research-parity'
$deterministicOut=Join-Path $outRoot 'deterministic-scenarios'
$tl1PhaseAOut=Join-Path $outRoot 'tl1-phase-a'
$cp139Out=Join-Path $outRoot 'cp139-reconciliation'
$cp142AuditOut=Join-Path $outRoot 'cp142-reconciliation-audit'
$smokeBatchRoot=Join-Path $outRoot 'cp144-stage-a-smoke-batches'
$smokeMergeOut=Join-Path $outRoot 'cp144-stage-a-smoke-merged'
$diagOut=Join-Path $outRoot 'stage-a-diagnostic-attribution'
$repoOnlySummary=Join-Path $outRoot 'CP145_REPOSITORY_ONLY_ACCEPTANCE.json'
$finalSummary=Join-Path $outRoot 'CP145_NATIVE_ACCEPTANCE_SUMMARY.json'

function Get-Cpython313Command {
    $candidates=@(@{Command='py';Args=@('-3.13')},@{Command='python';Args=@()},@{Command='python3';Args=@()})
    foreach($candidate in $candidates){
        $cmd=Get-Command $candidate.Command -ErrorAction SilentlyContinue
        if($null -eq $cmd){continue}
        $v=& $candidate.Command @($candidate.Args+@('--version')) 2>&1|Out-String
        if($LASTEXITCODE -eq 0 -and $v -match 'Python\s+3\.13(?:\.|\s|$)'){return $candidate}
    }
    throw 'CP145 requires Python 3.13.'
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
    if($files.Count -ne 36){throw "CP145 expected 36 Python test modules, found $($files.Count)."}
    $chunks=@(@($files[0..11]),@($files[12..23]),@($files[24..35]))
    $simulationRoot=Join-Path $repositoryRoot 'tools\simulation'
    $oldPythonPath=$env:PYTHONPATH
    try {
        if([string]::IsNullOrWhiteSpace($oldPythonPath)){$env:PYTHONPATH=$simulationRoot}else{$env:PYTHONPATH=$simulationRoot+[System.IO.Path]::PathSeparator+$oldPythonPath}
        for($i=0;$i -lt $chunks.Count;$i++){
            $modules=@($chunks[$i] | ForEach-Object{"tools.simulation.tests.$($_.BaseName)"})
            Write-Host("       Python test chunk {0}/3 ({1} modules)..." -f ($i+1),$modules.Count)
            & $python.Command @($python.Args+@('-B','-m','unittest')+$modules)
            if($LASTEXITCODE -ne 0){throw "CP145 Python test chunk $($i+1) failed."}
        }
    } finally {
        $env:PYTHONPATH=$oldPythonPath
    }
}

function Invoke-Cp144SmokeRegression {
    if(Test-Path -LiteralPath $smokeBatchRoot){Remove-Item -Recurse -Force $smokeBatchRoot}
    if(Test-Path -LiteralPath $smokeMergeOut){Remove-Item -Recurse -Force $smokeMergeOut}
    New-Item -ItemType Directory -Force -Path $smokeBatchRoot,$smokeMergeOut|Out-Null
    $ranges=@(@(0,1024),@(1024,2048),@(2048,3072),@(3072,4096),@(4096,5120),@(5120,6144),@(6144,6850));$i=0
    foreach($range in $ranges){
        $i++;$start=[int]$range[0];$end=[int]$range[1]
        $dir=Join-Path $smokeBatchRoot ("batch_{0:D4}_{1:D4}" -f $start,$end)
        New-Item -ItemType Directory -Force -Path $dir|Out-Null
        $rel=Relative-To-Repo $dir;$log=Join-Path $dir 'console.log'
        Write-Host("       CP144 Stage-A smoke regression batch {0}/7: scenarios {1}-{2}" -f $i,$start,($end-1))
        Invoke-Captured "CP145 CP144-smoke regression batch $start-$end" $log {& $python.Command @($python.Args+@('-B',$research,'--repo',$repositoryRoot,'whole-combat-stage-a-smoke',$cp144Study,'--output-dir',$rel,'--jobs',$Jobs,'--batch-start',$start,'--batch-end',$end))}
        $bs=Read-Json(Join-Path $dir 'summary.json');$expected=$end-$start
        if(-not[bool]$bs.passed -or[int]$bs.scenarios -ne $expected -or[int]$bs.executionErrors -ne 0 -or[int]$bs.nonstandoffOpenOrders -ne 0 -or-not[bool]$bs.sourceMatrixUnmodified -or[int]$bs.substantiveCombatTrials -ne 0){throw "CP145 CP144-smoke batch $start-$end contract mismatch."}
    }
    $relB=Relative-To-Repo $smokeBatchRoot;$relM=Relative-To-Repo $smokeMergeOut;$log=Join-Path $smokeMergeOut 'console.log'
    Invoke-Captured 'CP145 CP144 Stage-A smoke merge' $log {& $python.Command @($python.Args+@('-B',$research,'--repo',$repositoryRoot,'whole-combat-stage-a-smoke-merge',$cp144Study,'--batch-root',$relB,'--output-dir',$relM))}
    $s=Read-Json(Join-Path $smokeMergeOut 'summary.json')
    if(-not[bool]$s.passed -or[int]$s.stageAScenarios -ne 6850 -or[int]$s.executionErrors -ne 0 -or[int]$s.resolved -ne 6785 -or[int]$s.resolvedGe25 -ne 9 -or[int]$s.turnCapSentinels -ne 65 -or[int]$s.safeStalemates -ne 0 -or[int]$s.nonstandoffOpenOrders -ne 0 -or[int]$s.resourceEnvironmentCount -ne 5 -or[int]$s.scenarioStrataCount -ne 10 -or[int]$s.orderedSameTlWeaponPairings -ne 137 -or-not[bool]$s.stageASubstantiveReady -or-not[bool]$s.sourceMatrixUnmodified){throw 'CP145 CP144 Stage-A smoke regression mismatch.'}
    return $s
}

$python=Get-Cpython313Command
$pythonVersion=& $python.Command @($python.Args+@('--version')) 2>&1|Out-String
$dotnetVersion=(& dotnet --version 2>&1|Out-String).Trim()
if($LASTEXITCODE -ne 0 -or $dotnetVersion -ne '8.0.423'){throw "CP145 requires .NET SDK 8.0.423 exactly; observed '$dotnetVersion'."}
Write-Host("CP145 runtimes: {0}; .NET SDK {1}" -f $pythonVersion.Trim(),$dotnetVersion)
Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot) 'CP145 preflight failed'

if($RepositoryOnly){
    if(-not $NoClean -and(Test-Path -LiteralPath $outRoot)){Remove-Item -Recurse -Force $outRoot}
    New-Item -ItemType Directory -Force -Path $outRoot,$testOut,$parityOut,$deterministicOut,$tl1PhaseAOut,$cp139Out,$cp142AuditOut|Out-Null
    Push-Location $repositoryRoot
    try{
        Write-Host '[1/9] Python research tests (310 total) in isolated chunks...';Invoke-PythonResearchTests
        Write-Host '[2/9] Warning-as-error .NET build...';Invoke-Captured 'CP145 build' (Join-Path $outRoot 'build.log') {dotnet build StarCluster.sln --configuration Release --nologo -warnaserror}
        Write-Host '[3/9] xUnit + ScenarioRunner deterministic corpora...'
        dotnet test tests\StarCluster.Tests\StarCluster.Tests.csproj --configuration Release --no-build --nologo --logger 'trx;LogFileName=cp145-tests.trx' --results-directory $testOut
        $xunitExit=$LASTEXITCODE;$trxPath=Join-Path $testOut 'cp145-tests.trx'
        if(-not(Test-Path -LiteralPath $trxPath)){throw 'CP145 xUnit TRX missing.'}
        [xml]$trx=Get-Content -LiteralPath $trxPath -Raw;$c=$trx.TestRun.ResultSummary.Counters
        $total=[int]$c.total;$passed=[int]$c.passed;$failed=[int]$c.failed;$skipped=[int]$c.notExecuted
        if($xunitExit -ne 0 -or $total -ne 916 -or $passed -ne 916 -or $failed -ne 0 -or $skipped -ne 0){throw "CP145 xUnit mismatch exit=$xunitExit total=$total passed=$passed failed=$failed skipped=$skipped."}
        $selfLog=Join-Path $outRoot 'scenario-self-tests.log'
        Invoke-Captured 'CP145 ScenarioRunner self-tests' $selfLog {dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- self-test}
        $selfText=Get-Content -LiteralPath $selfLog -Raw
        if($selfText -notmatch 'Runner self-tests:\s+70 passed,\s+0 failed,\s+70 total\.'){throw 'CP145 expected 70/70 ScenarioRunner self-tests.'}
        Invoke-Captured 'CP145 deterministic scenario corpus' (Join-Path $outRoot 'deterministic-scenarios.log') {dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- run-all --output-dir $deterministicOut}
        Invoke-Captured 'CP145 TL1 Phase-A corpus' (Join-Path $outRoot 'tl1-phase-a.log') {dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- tl1-phase-a --output-dir $tl1PhaseAOut}

        Write-Host '[4/9] Existing C#/Python research parity...'
        Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'parity','--output-dir',$parityOut) 'CP145 research parity failed'
        $parity=Read-Json(Join-Path $parityOut 'summary.json')
        if(-not[bool]$parity.passed -or[int]$parity.cases -ne 25){throw 'CP145 expected 25/25 research parity.'}

        Write-Host '[5/9] CP139 DEF/RES regression foundation...'
        & $python.Command @($python.Args+@('-B','-m','unittest','discover','-v','-s','tools/simulation/tests','-p','test_cp139_def_res_reconciliation.py'))
        if($LASTEXITCODE -ne 0){throw 'CP139 focused regression failed under CP145.'}
        Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'combat-model-reconciliation-study',$cp139Study,'--output-dir','out/checkpoint-145/cp139-reconciliation') 'CP139 reconciliation regression failed'
        $recon=Read-Json(Join-Path $cp139Out 'summary.json');$ra=Get-Analysis $recon
        if(-not[bool]$recon.passed -or[int]$ra.fixturePass -ne 8 -or[int]$ra.smokeVariants -ne 82 -or[int]$ra.smokeErrors -ne 0 -or-not[bool]$ra.sourceMatrixUnmodified){throw 'CP139 reconciliation regression mismatch under CP145.'}

        Write-Host '[6/9] Focused CP140 + CP141 + CP142 + CP143 + CP144 + CP145 tests...'
        foreach($pattern in @('test_cp140_stage_a_integration.py','test_cp141_combat_duration_stalemate.py','test_cp142_combat_surface_reconciliation.py','test_cp143_missile_mirror_pacing_attribution.py','test_cp144_*.py','test_cp145_*.py')){
            & $python.Command @($python.Args+@('-B','-m','unittest','discover','-v','-s','tools/simulation/tests','-p',$pattern))
            if($LASTEXITCODE -ne 0){throw "Focused regression failed: $pattern"}
        }

        Write-Host '[7/9] CP142 deep-reconciliation audit regression...'
        Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'combat-surface-reconciliation-audit',$cp142Study,'--output-dir','out/checkpoint-145/cp142-reconciliation-audit') 'CP142 reconciliation audit regression failed'
        $audit=Read-Json(Join-Path $cp142AuditOut 'reconciliation_summary.json')
        if(-not[bool]$audit.passed -or[int]$audit.ledgerRows -ne 531 -or[int]$audit.changedVsCp141Rows -ne 72 -or[int]$audit.explicitUnresolvedRows -ne 7){throw 'CP142 reconciliation audit mismatch under CP145.'}

        Write-Host '[8/9] Replaying the complete CP144 6,850-cell Stage-A smoke signature under observation-only telemetry...'
        $smoke=Invoke-Cp144SmokeRegression

        Write-Host '[9/9] Writing RepositoryOnly acceptance and repository contract...'
        $summary=[ordered]@{
            schemaVersion='star-cluster-cp145-repository-only-acceptance-v0.1';checkpoint=145;repositoryOnly=$true;failedGates=@();python=$pythonVersion.Trim();dotnetSdk=$dotnetVersion;buildPassed=$true;
            pythonTestsPassed=310;xunitTotal=$total;xunitPassed=$passed;xunitFailed=$failed;xunitSkipped=$skipped;scenarioRunnerSelfTestsPassed=70;deterministicScenarioCorpusPassed=$true;tl1PhaseACorpusPassed=$true;researchParityPassed=25;
            cp139FocusedTestsPassed=9;cp140FocusedTestsPassed=10;cp141FocusedTestsPassed=10;cp142FocusedTestsPassed=12;cp143FocusedTestsPassed=12;cp144FocusedTestsPassed=11;cp145FocusedTestsPassed=12;
            defResFixturesPassed=8;cp139ReconciliationSmokeVariants=82;cp139ReconciliationSmokeErrors=0;cp142ReconciliationLedgerRows=531;cp142ChangedRows=72;cp142ExplicitUnresolvedRows=7;
            acceptedCp144StageAScenarios=6850;acceptedCp144SubstantiveCombatTrials=3425000;acceptedCp144EvidenceHashLocked=$true;
            cp144SmokeResolved=[int]$smoke.resolved;cp144SmokeResolvedGe25=[int]$smoke.resolvedGe25;cp144SmokeTurnCapSentinels=[int]$smoke.turnCapSentinels;cp144SmokeSafeStalemates=[int]$smoke.safeStalemates;cp144SmokeNonstandoffOpenOrders=[int]$smoke.nonstandoffOpenOrders;
            sourceMatrixUnmodified=$true;diagnosticAttributionCompleted=$false;diagnosticScenarios=252;diagnosticTrialsPerScenario=25;diagnosticCombatTrials=0;pdsOpportunityScenarios=204;tpStarvationScenarios=48;
            tuningAllowed=$false;automaticPromotion=$false;stageBAutomatic=$false;nextStage='6,300 exact-seed CP145 diagnostic replays plus accepted Stage-A attribution'
        }
        $summary|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $repoOnlySummary -Encoding UTF8
        Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP145 RepositoryOnly contract failed'
        Write-Host 'CP145 RepositoryOnly acceptance PASSED. Run the same wrapper without -RepositoryOnly to execute the 6,300 diagnostic replays.' -ForegroundColor Green
    } finally {Pop-Location}
    exit 0
}

if(-not(Test-Path -LiteralPath $repoOnlySummary)){throw 'Run CP145 -RepositoryOnly first in this same extraction.'}
Push-Location $repositoryRoot
try{
    Write-Host '[final 1/3] Revalidating preflight/manifest and RepositoryOnly state after generated outputs...'
    Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot) 'CP145 final preflight failed'
    Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP145 RepositoryOnly state contract failed'

    Write-Host '[final 2/3] Executing 252 x 25 = 6,300 exact-seed observation-only diagnostic replays and accepted Stage-A attribution...'
    if(Test-Path -LiteralPath $diagOut){Remove-Item -Recurse -Force $diagOut}
    New-Item -ItemType Directory -Force -Path $diagOut|Out-Null
    $relDiag=Relative-To-Repo $diagOut;$diagLog=Join-Path $diagOut 'console.log'
    Invoke-Captured 'CP145 Stage-A diagnostic attribution' $diagLog {& $python.Command @($python.Args+@('-B',$research,'--repo',$repositoryRoot,'stage-a-diagnostic-attribution',$cp145Study,'--output-dir',$relDiag,'--jobs',$Jobs))}
    $diag=Read-Json(Join-Path $diagOut 'summary.json')
    if(-not[bool]$diag.passed -or[int]$diag.diagnosticScenarios -ne 252 -or[int]$diag.diagnosticTrialsPerScenario -ne 25 -or[int64]$diag.diagnosticCombatTrials -ne 6300 -or[int]$diag.pdsOpportunityScenarios -ne 204 -or[int]$diag.tpStarvationScenarios -ne 48 -or-not[bool]$diag.sourceMatrixUnmodified -or[bool]$diag.tuningAllowed -or[bool]$diag.automaticPromotion -or[bool]$diag.stageBAutomatic){throw 'CP145 diagnostic attribution contract mismatch.'}

    Write-Host '[final 3/3] Final diagnostic validation, acceptance summary, and result ZIP...'
    $ro=Read-Json $repoOnlySummary;$final=[ordered]@{};$ro.psobject.Properties|ForEach-Object{$final[$_.Name]=$_.Value}
    $final['schemaVersion']='star-cluster-cp145-native-acceptance-v0.1';$final['repositoryOnly']=$false;$final['repositoryOnlyAccepted']=$true;$final['diagnosticAttributionCompleted']=$true
    $final['diagnosticScenarios']=[int]$diag.diagnosticScenarios;$final['diagnosticTrialsPerScenario']=[int]$diag.diagnosticTrialsPerScenario;$final['diagnosticCombatTrials']=[int64]$diag.diagnosticCombatTrials
    $final['pdsOpportunityScenarios']=[int]$diag.pdsOpportunityScenarios;$final['tpStarvationScenarios']=[int]$diag.tpStarvationScenarios;$final['originalParetoWinFastCorrelation']=[double]$diag.originalParetoWinFastCorrelation;$final['originalParetoSingleSurvivorContexts']=[int]$diag.originalParetoSingleSurvivorContexts
    $final['strategicParetoRows']=[int]$diag.strategicParetoRows;$final['kineticAttributionRows']=[int]$diag.kineticAttributionRows;$final['kineticVsEnergyAttributionRows']=[int]$diag.kineticVsEnergyAttributionRows;$final['energyResourceRows']=[int]$diag.energyResourceRows;$final['pdsBaselineRows']=[int]$diag.pdsBaselineRows
    $final['nextStage']='review CP145 causal attribution; only then decide whether a bounded candidate sweep is justified before Stage B'
    $final|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $finalSummary -Encoding UTF8
    Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP145 final contract failed'
    $stamp=Get-Date -Format 'yyyyMMdd_HHmmss';$zip=Join-Path $outRoot ("StarCluster_CP145_native_results_$stamp.zip")
    $items=Get-ChildItem -LiteralPath $outRoot -Force|Where-Object{$_.FullName -ne $zip}
    Compress-Archive -Path $items.FullName -DestinationPath $zip -CompressionLevel Optimal
    Write-Host "CP145 native acceptance PASSED. Results: $zip" -ForegroundColor Green
} finally {Pop-Location}
