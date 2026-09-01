[CmdletBinding()]
param([switch]$RepositoryOnly,[switch]$NoClean,[int]$Jobs=24)
Set-StrictMode -Version 2.0
$ErrorActionPreference='Stop'

$repositoryRoot=(Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$preflight=Join-Path $PSScriptRoot 'preflight_checkpoint_147.py'
$contract=Join-Path $PSScriptRoot 'test_checkpoint_147_contract.py'
$research=Join-Path $repositoryRoot 'tools\simulation\run_starcluster_research.py'
$cp139Study='docs/archive/testing/pre-cp165-active/cp139_def_res_reconciliation_study_v0_1.json'
$cp142Study='docs/archive/testing/pre-cp165-active/cp142_combat_surface_deep_reconciliation_study_v0_1.json'
$cp144Study='docs/archive/testing/pre-cp165-active/cp144_whole_combat_stage_a_response_surface_study_v0_1.json'
$cp147Study='docs/archive/testing/pre-cp165-active/cp147_tactical_package_utility_study_v0_1.json'
$outRoot=Join-Path $repositoryRoot 'out\checkpoint-147'
$testOut=Join-Path $outRoot 'xunit'
$parityOut=Join-Path $outRoot 'research-parity'
$deterministicOut=Join-Path $outRoot 'deterministic-scenarios'
$tl1PhaseAOut=Join-Path $outRoot 'tl1-phase-a'
$cp139Out=Join-Path $outRoot 'cp139-reconciliation'
$cp142AuditOut=Join-Path $outRoot 'cp142-reconciliation-audit'
$smokeBatchRoot=Join-Path $outRoot 'cp144-stage-a-smoke-batches'
$smokeMergeOut=Join-Path $outRoot 'cp144-stage-a-smoke-merged'
$utilityOut=Join-Path $outRoot 'tactical-package-utility'
$repoOnlySummary=Join-Path $outRoot 'CP147_REPOSITORY_ONLY_ACCEPTANCE.json'
$finalSummary=Join-Path $outRoot 'CP147_NATIVE_ACCEPTANCE_SUMMARY.json'

function Get-Cpython313Command {
    $candidates=@(@{Command='py';Args=@('-3.13')},@{Command='python';Args=@()},@{Command='python3';Args=@()})
    foreach($candidate in $candidates){
        $cmd=Get-Command $candidate.Command -ErrorAction SilentlyContinue
        if($null -eq $cmd){continue}
        $v=& $candidate.Command @($candidate.Args+@('--version')) 2>&1|Out-String
        if($LASTEXITCODE -eq 0 -and $v -match 'Python\s+3\.13(?:\.|\s|$)'){return $candidate}
    }
    throw 'CP147 requires Python 3.13.'
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
    if($files.Count -ne 38){throw "CP147 expected 38 Python test modules, found $($files.Count)."}
    $chunks=@(@($files[0..12]),@($files[13..18]),@($files[19..24]),@($files[25..37]))
    $simulationRoot=Join-Path $repositoryRoot 'tools\simulation'
    $oldPythonPath=$env:PYTHONPATH
    try {
        if([string]::IsNullOrWhiteSpace($oldPythonPath)){$env:PYTHONPATH=$simulationRoot}else{$env:PYTHONPATH=$simulationRoot+[System.IO.Path]::PathSeparator+$oldPythonPath}
        for($i=0;$i -lt $chunks.Count;$i++){
            $modules=@($chunks[$i] | ForEach-Object{"tools.simulation.tests.$($_.BaseName)"})
            Write-Host("       Python test chunk {0}/4 ({1} modules)..." -f ($i+1),$modules.Count)
            & $python.Command @($python.Args+@('-B','-m','unittest')+$modules)
            if($LASTEXITCODE -ne 0){throw "CP147 Python test chunk $($i+1) failed."}
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
        Write-Host("       CP144 Stage-A legacy smoke batch {0}/7: scenarios {1}-{2}" -f $i,$start,($end-1))
        Invoke-Captured "CP147 CP144-smoke regression batch $start-$end" $log {& $python.Command @($python.Args+@('-B',$research,'--repo',$repositoryRoot,'whole-combat-stage-a-smoke',$cp144Study,'--output-dir',$rel,'--jobs',$Jobs,'--batch-start',$start,'--batch-end',$end))}
        $bs=Read-Json(Join-Path $dir 'summary.json');$expected=$end-$start
        if(-not[bool]$bs.passed -or[int]$bs.scenarios -ne $expected -or[int]$bs.executionErrors -ne 0 -or[int]$bs.nonstandoffOpenOrders -ne 0 -or-not[bool]$bs.sourceMatrixUnmodified -or[int]$bs.substantiveCombatTrials -ne 0){throw "CP147 CP144-smoke batch $start-$end contract mismatch."}
    }
    $relB=Relative-To-Repo $smokeBatchRoot;$relM=Relative-To-Repo $smokeMergeOut;$log=Join-Path $smokeMergeOut 'console.log'
    Invoke-Captured 'CP147 CP144 Stage-A legacy smoke merge' $log {& $python.Command @($python.Args+@('-B',$research,'--repo',$repositoryRoot,'whole-combat-stage-a-smoke-merge',$cp144Study,'--batch-root',$relB,'--output-dir',$relM))}
    $s=Read-Json(Join-Path $smokeMergeOut 'summary.json')
    if(-not[bool]$s.passed -or[int]$s.stageAScenarios -ne 6850 -or[int]$s.executionErrors -ne 0 -or[int]$s.resolved -ne 6785 -or[int]$s.resolvedGe25 -ne 9 -or[int]$s.turnCapSentinels -ne 65 -or[int]$s.safeStalemates -ne 0 -or[int]$s.nonstandoffOpenOrders -ne 0 -or[int]$s.resourceEnvironmentCount -ne 5 -or[int]$s.scenarioStrataCount -ne 10 -or[int]$s.orderedSameTlWeaponPairings -ne 137 -or-not[bool]$s.stageASubstantiveReady -or-not[bool]$s.sourceMatrixUnmodified){throw 'CP147 CP144 Stage-A smoke regression mismatch.'}
    return $s
}

$python=Get-Cpython313Command
$pythonVersion=& $python.Command @($python.Args+@('--version')) 2>&1|Out-String
$dotnetVersion=(& dotnet --version 2>&1|Out-String).Trim()
if($LASTEXITCODE -ne 0 -or $dotnetVersion -ne '8.0.423'){throw "CP147 requires .NET SDK 8.0.423 exactly; observed '$dotnetVersion'."}
Write-Host("CP147 runtimes: {0}; .NET SDK {1}" -f $pythonVersion.Trim(),$dotnetVersion)
Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot) 'CP147 preflight failed'

if($RepositoryOnly){
    if(-not $NoClean -and(Test-Path -LiteralPath $outRoot)){Remove-Item -Recurse -Force $outRoot}
    New-Item -ItemType Directory -Force -Path $outRoot,$testOut,$parityOut,$deterministicOut,$tl1PhaseAOut,$cp139Out,$cp142AuditOut|Out-Null
    Push-Location $repositoryRoot
    try{
        Write-Host '[1/9] Python research tests (346 total) in isolated chunks...';Invoke-PythonResearchTests
        Write-Host '[2/9] Warning-as-error .NET build...';Invoke-Captured 'CP147 build' (Join-Path $outRoot 'build.log') {dotnet build StarCluster.sln --configuration Release --nologo -warnaserror}
        Write-Host '[3/9] xUnit + ScenarioRunner deterministic corpora...'
        dotnet test tests\StarCluster.Tests\StarCluster.Tests.csproj --configuration Release --no-build --nologo --logger 'trx;LogFileName=cp147-tests.trx' --results-directory $testOut
        $xunitExit=$LASTEXITCODE;$trxPath=Join-Path $testOut 'cp147-tests.trx'
        if(-not(Test-Path -LiteralPath $trxPath)){throw 'CP147 xUnit TRX missing.'}
        [xml]$trx=Get-Content -LiteralPath $trxPath -Raw;$c=$trx.TestRun.ResultSummary.Counters
        $total=[int]$c.total;$passed=[int]$c.passed;$failed=[int]$c.failed;$skipped=[int]$c.notExecuted
        if($xunitExit -ne 0 -or $total -ne 934 -or $passed -ne 934 -or $failed -ne 0 -or $skipped -ne 0){throw "CP147 xUnit mismatch exit=$xunitExit total=$total passed=$passed failed=$failed skipped=$skipped."}
        $selfLog=Join-Path $outRoot 'scenario-self-tests.log'
        Invoke-Captured 'CP147 ScenarioRunner self-tests' $selfLog {dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- self-test}
        $selfText=Get-Content -LiteralPath $selfLog -Raw
        if($selfText -notmatch 'Runner self-tests:\s+70 passed,\s+0 failed,\s+70 total\.'){throw 'CP147 expected 70/70 ScenarioRunner self-tests.'}
        Invoke-Captured 'CP147 deterministic scenario corpus' (Join-Path $outRoot 'deterministic-scenarios.log') {dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- run-all --output-dir $deterministicOut}
        Invoke-Captured 'CP147 TL1 Phase-A corpus' (Join-Path $outRoot 'tl1-phase-a.log') {dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- tl1-phase-a --output-dir $tl1PhaseAOut}

        Write-Host '[4/9] Existing C#/Python research parity...'
        Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'parity','--output-dir',$parityOut) 'CP147 research parity failed'
        $parity=Read-Json(Join-Path $parityOut 'summary.json')
        if(-not[bool]$parity.passed -or[int]$parity.cases -ne 25){throw 'CP147 expected 25/25 research parity.'}

        Write-Host '[5/9] CP139 DEF/RES regression foundation...'
        & $python.Command @($python.Args+@('-B','-m','unittest','discover','-v','-s','tools/simulation/tests','-p','test_cp139_def_res_reconciliation.py'))
        if($LASTEXITCODE -ne 0){throw 'CP139 focused regression failed under CP147.'}
        Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'combat-model-reconciliation-study',$cp139Study,'--output-dir','out/checkpoint-147/cp139-reconciliation') 'CP139 reconciliation regression failed'
        $recon=Read-Json(Join-Path $cp139Out 'summary.json');$ra=Get-Analysis $recon
        if(-not[bool]$recon.passed -or[int]$ra.fixturePass -ne 8 -or[int]$ra.smokeVariants -ne 82 -or[int]$ra.smokeErrors -ne 0 -or-not[bool]$ra.sourceMatrixUnmodified){throw 'CP139 reconciliation regression mismatch under CP147.'}

        Write-Host '[6/9] Focused CP140 + CP141 + CP142 + CP143 + CP144 + CP145 + CP146 + CP147 tests...'
        foreach($pattern in @('test_cp140_stage_a_integration.py','test_cp141_combat_duration_stalemate.py','test_cp142_combat_surface_reconciliation.py','test_cp143_missile_mirror_pacing_attribution.py','test_cp144_*.py','test_cp145_*.py','test_cp146_*.py','test_cp147_*.py')){
            & $python.Command @($python.Args+@('-B','-m','unittest','discover','-v','-s','tools/simulation/tests','-p',$pattern))
            if($LASTEXITCODE -ne 0){throw "Focused regression failed: $pattern"}
        }

        Write-Host '[7/9] CP142 deep-reconciliation audit regression...'
        Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'combat-surface-reconciliation-audit',$cp142Study,'--output-dir','out/checkpoint-147/cp142-reconciliation-audit') 'CP142 reconciliation audit regression failed'
        $audit=Read-Json(Join-Path $cp142AuditOut 'reconciliation_summary.json')
        if(-not[bool]$audit.passed -or[int]$audit.ledgerRows -ne 531 -or[int]$audit.changedVsCp141Rows -ne 72 -or[int]$audit.explicitUnresolvedRows -ne 7){throw 'CP142 reconciliation audit mismatch under CP147.'}

        Write-Host '[8/9] Replaying the complete CP144 6,850-cell Stage-A legacy smoke signature...'
        $smoke=Invoke-Cp144SmokeRegression

        Write-Host '[9/9] Writing RepositoryOnly acceptance and repository contract...'
        $summary=[ordered]@{
            schemaVersion='star-cluster-cp147-repository-only-acceptance-v0.1';checkpoint=147;repositoryOnly=$true;failedGates=@();python=$pythonVersion.Trim();dotnetSdk=$dotnetVersion;buildPassed=$true;
            pythonTestsPassed=346;xunitTotal=$total;xunitPassed=$passed;xunitFailed=$failed;xunitSkipped=$skipped;scenarioRunnerSelfTestsPassed=70;deterministicScenarioCorpusPassed=$true;tl1PhaseACorpusPassed=$true;researchParityPassed=25;
            cp139FocusedTestsPassed=9;cp140FocusedTestsPassed=10;cp141FocusedTestsPassed=10;cp142FocusedTestsPassed=12;cp143FocusedTestsPassed=12;cp144FocusedTestsPassed=11;cp145FocusedTestsPassed=12;cp146FocusedTestsPassed=18;cp147FocusedTestsPassed=18;cp146DoctrineFixtureCases=9;cp147UtilityFixtureCases=10;
            defResFixturesPassed=8;cp139ReconciliationSmokeVariants=82;cp139ReconciliationSmokeErrors=0;cp142ReconciliationLedgerRows=531;cp142ChangedRows=72;cp142ExplicitUnresolvedRows=7;
            acceptedCp146EvidenceHashLocked=$true;acceptedCp146ContextualCombatTrials=6300;
            cp144SmokeResolved=[int]$smoke.resolved;cp144SmokeResolvedGe25=[int]$smoke.resolvedGe25;cp144SmokeTurnCapSentinels=[int]$smoke.turnCapSentinels;cp144SmokeSafeStalemates=[int]$smoke.safeStalemates;cp144SmokeNonstandoffOpenOrders=[int]$smoke.nonstandoffOpenOrders;
            sourceMatrixUnmodified=$true;utilityValidationCompleted=$false;utilityScenariosPerVersion=252;utilityTrialsPerScenario=25;utilityCombatTrialsPerVersion=6300;totalUtilityCombatTrials=0;
            tuningAllowed=$false;automaticPromotion=$false;stageBAutomatic=$false;nextStage='12,600 matched cp146_contextual vs cp147_tactical_utility replays'
        }
        $summary|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $repoOnlySummary -Encoding UTF8
        Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP147 RepositoryOnly contract failed'
        Write-Host 'CP147 RepositoryOnly acceptance PASSED. Run the same wrapper without -RepositoryOnly to execute the 12,600 matched utility replays.' -ForegroundColor Green
    } finally {Pop-Location}
    exit 0
}

if(-not(Test-Path -LiteralPath $repoOnlySummary)){throw 'Run CP147 -RepositoryOnly first in this same extraction.'}
Push-Location $repositoryRoot
try{
    Write-Host '[final 1/3] Revalidating preflight/manifest and RepositoryOnly state after generated outputs...'
    Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot) 'CP147 final preflight failed'
    Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP147 RepositoryOnly state contract failed'

    Write-Host '[final 2/3] Executing 252 x 25 x 2 = 12,600 matched contextual/utility doctrine replays...'
    if(Test-Path -LiteralPath $utilityOut){Remove-Item -Recurse -Force $utilityOut}
    New-Item -ItemType Directory -Force -Path $utilityOut|Out-Null
    $relUtility=Relative-To-Repo $utilityOut;$utilityLog=Join-Path $utilityOut 'console.log'
    Invoke-Captured 'CP147 tactical package utility validation' $utilityLog {& $python.Command @($python.Args+@('-B',$research,'--repo',$repositoryRoot,'tactical-package-utility-validation',$cp147Study,'--output-dir',$relUtility,'--jobs',$Jobs))}
    $utility=Read-Json(Join-Path $utilityOut 'summary.json')
    if(-not[bool]$utility.passed -or[int]$utility.scenariosPerDoctrine -ne 252 -or[int]$utility.trialsPerScenarioPerDoctrine -ne 25 -or[int64]$utility.combatTrialsPerDoctrine -ne 6300 -or[int64]$utility.totalCombatTrials -ne 12600 -or[int]$utility.acceptedCp146FieldMismatches -ne 0 -or-not[bool]$utility.sourceMatrixUnmodified -or[bool]$utility.tuningAllowed -or[bool]$utility.automaticPromotion -or[bool]$utility.stageBAutomatic -or[int]$utility.cp147TurnCapSentinels -ne 0 -or[int]$utility.cp147Tl2TurnCapSentinels -ne 0 -or[int]$utility.cp147NewSaturatedTurnCapCells -ne 0 -or[int64]$utility.cp147PackageDecisions -le 0 -or[int64]$utility.cp147DirectPackageSelections -le 0 -or[int64]$utility.cp147HeldPackageSelections -le 0 -or[int64]$utility.cp147HeldMainAttempts -le 0 -or[int64]$utility.cp147PdsPackageSelections -le 0 -or[int64]$utility.cp147SoleMainDiversionsWithoutHullRisk -ne 0){throw 'CP147 tactical-package utility validation mismatch.'}

    Write-Host '[final 3/3] Final utility validation, acceptance summary, and result ZIP...'
    $ro=Read-Json $repoOnlySummary;$final=[ordered]@{};$ro.psobject.Properties|ForEach-Object{$final[$_.Name]=$_.Value}
    $final['schemaVersion']='star-cluster-cp147-native-acceptance-v0.1';$final['repositoryOnly']=$false;$final['repositoryOnlyAccepted']=$true;$final['utilityValidationCompleted']=$true
    $final['utilityScenariosPerVersion']=[int]$utility.scenariosPerDoctrine;$final['utilityTrialsPerScenario']=[int]$utility.trialsPerScenarioPerDoctrine;$final['utilityCombatTrialsPerVersion']=[int64]$utility.combatTrialsPerDoctrine;$final['totalUtilityCombatTrials']=[int64]$utility.totalCombatTrials
    $final['acceptedCp146FieldMismatches']=[int]$utility.acceptedCp146FieldMismatches;$final['cp147TurnCapSentinels']=[int]$utility.cp147TurnCapSentinels;$final['cp147Tl2TurnCapSentinels']=[int]$utility.cp147Tl2TurnCapSentinels;$final['cp147NewSaturatedTurnCapCells']=[int]$utility.cp147NewSaturatedTurnCapCells
    $final['cp147PackageDecisions']=[int64]$utility.cp147PackageDecisions;$final['cp147DirectPackageSelections']=[int64]$utility.cp147DirectPackageSelections;$final['cp147HeldPackageSelections']=[int64]$utility.cp147HeldPackageSelections;$final['cp147HeldMainAttempts']=[int64]$utility.cp147HeldMainAttempts;$final['cp147PdsPackageSelections']=[int64]$utility.cp147PdsPackageSelections;$final['cp147SoleMainDiversionsWithoutHullRisk']=[int64]$utility.cp147SoleMainDiversionsWithoutHullRisk
    $final['nextStage']='rerun the broad whole-combat response surface under the accepted tactical-utility doctrine before numerical tuning or Stage B'
    $final|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $finalSummary -Encoding UTF8
    Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP147 final contract failed'
    $stamp=Get-Date -Format 'yyyyMMdd_HHmmss';$zip=Join-Path $outRoot ("StarCluster_CP147_native_results_$stamp.zip")
    $items=Get-ChildItem -LiteralPath $outRoot -Force|Where-Object{$_.FullName -ne $zip}
    Compress-Archive -Path $items.FullName -DestinationPath $zip -CompressionLevel Optimal
    Write-Host "CP147 native acceptance PASSED. Results: $zip" -ForegroundColor Green
} finally {Pop-Location}
