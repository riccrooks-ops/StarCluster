[CmdletBinding()]
param([switch]$RepositoryOnly,[switch]$NoClean)
Set-StrictMode -Version 2.0
$ErrorActionPreference='Stop'
$repositoryRoot=(Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$preflight=Join-Path $PSScriptRoot 'preflight_checkpoint_133.py'
$contract=Join-Path $PSScriptRoot 'test_checkpoint_133_contract.py'
$hygiene=Join-Path $repositoryRoot 'tools\checkpoints\prepackage_repository_hygiene.py'
$research=Join-Path $repositoryRoot 'tools\simulation\run_starcluster_research.py'
$outRoot=Join-Path $repositoryRoot 'out\checkpoint-133'
$testOut=Join-Path $outRoot 'xunit'
$parityOut=Join-Path $outRoot 'research-parity'
$repoOnlySummary=Join-Path $outRoot 'CP133_REPOSITORY_ONLY_ACCEPTANCE.json'
$finalSummary=Join-Path $outRoot 'CP133_NATIVE_ACCEPTANCE_SUMMARY.json'
function Get-Cpython313Command {
    $candidates=@(@{Command='py';Args=@('-3.13')},@{Command='python';Args=@()},@{Command='python3';Args=@()})
    foreach($candidate in $candidates){$cmd=Get-Command $candidate.Command -ErrorAction SilentlyContinue;if($null -eq $cmd){continue};$v=& $candidate.Command @($candidate.Args+@('--version')) 2>&1|Out-String;if($LASTEXITCODE -eq 0 -and $v -match 'Python\s+3\.13(?:\.|\s|$)'){return $candidate}}
    throw 'CP133 requires Python 3.13.'
}
function Invoke-PythonChecked([object]$Python,[string[]]$Arguments,[string]$Failure){& $Python.Command @($Python.Args+$Arguments);if($LASTEXITCODE -ne 0){throw "$Failure (exit code $LASTEXITCODE)."}}
function Invoke-Captured([string]$Label,[string]$LogPath,[scriptblock]$Body){& $Body *> $LogPath;$exitCode=$LASTEXITCODE;if($exitCode -ne 0){Write-Host "       $Label output tail:" -ForegroundColor Yellow;Get-Content -LiteralPath $LogPath -Tail 100|ForEach-Object{Write-Host("       $_")};throw "$Label failed (exit code $exitCode)."}}
function Read-Json([string]$Path){return(Get-Content -LiteralPath $Path -Raw|ConvertFrom-Json)}

Write-Host '[1/8] Resolving deterministic runtimes and accepted CP132 baseline...'
$python=Get-Cpython313Command;$pythonVersion=& $python.Command @($python.Args+@('--version')) 2>&1|Out-String;Write-Host("       {0}" -f $pythonVersion.Trim())
$dotnetVersion=(& dotnet --version 2>&1|Out-String).Trim();if($LASTEXITCODE -ne 0 -or $dotnetVersion -ne '8.0.423'){throw "CP133 requires .NET SDK 8.0.423 exactly; observed '$dotnetVersion'."};Write-Host "       .NET SDK $dotnetVersion"
Write-Host '       CP133 changes candidate reference tables only; no production/simulation/Concept/Storyboard changes and no Monte Carlo study.'

Write-Host '[2/8] Applying and verifying repository hygiene...'
Invoke-PythonChecked $python @('-B',$hygiene,'--repo',$repositoryRoot,'--apply') 'CP133 hygiene apply failed'
Invoke-PythonChecked $python @('-B',$hygiene,'--repo',$repositoryRoot,'--check') 'CP133 hygiene check failed'

if($RepositoryOnly){
    if(-not $NoClean -and(Test-Path -LiteralPath $outRoot)){Remove-Item -Recurse -Force $outRoot}
    New-Item -ItemType Directory -Force -Path $outRoot,$testOut,$parityOut|Out-Null
    Write-Host '[3/8] Validating revised tables and running Python standing suite...'
    Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot) 'CP133 preflight failed'
    Push-Location $repositoryRoot
    try{
        & $python.Command @($python.Args+@('-B','-m','unittest','discover','-s','tools/simulation/tests','-p','test_*.py'));if($LASTEXITCODE -ne 0){throw "CP133 Python self-tests failed (exit code $LASTEXITCODE)."};Write-Host '       Python self-tests: 196/196 passed.'
        Write-Host '[4/8] Revalidating frozen native C# surface...'
        $buildLog=Join-Path $outRoot 'build.log';Invoke-Captured 'CP133 warning-as-error build' $buildLog {dotnet build StarCluster.sln --configuration Release --nologo -warnaserror};Write-Host '       Native build passed.'
        dotnet test tests\StarCluster.Tests\StarCluster.Tests.csproj --configuration Release --no-build --nologo --logger 'trx;LogFileName=cp133-tests.trx' --results-directory $testOut
        $xunitExit=$LASTEXITCODE;$trxPath=Join-Path $testOut 'cp133-tests.trx';if(-not(Test-Path -LiteralPath $trxPath)){throw 'CP133 xUnit TRX missing.'};[xml]$trx=Get-Content -LiteralPath $trxPath -Raw;$c=$trx.TestRun.ResultSummary.Counters;$total=[int]$c.total;$passed=[int]$c.passed;$failed=[int]$c.failed;$skipped=[int]$c.notExecuted;if($xunitExit -ne 0 -or $total -ne 910 -or $passed -ne 910 -or $failed -ne 0 -or $skipped -ne 0){throw "CP133 xUnit mismatch exit=$xunitExit total=$total passed=$passed failed=$failed skipped=$skipped."};Write-Host '       xUnit tests: 910/910 passed.'
        $selfLog=Join-Path $outRoot 'scenario-self-tests.log';Invoke-Captured 'CP133 ScenarioRunner self-tests' $selfLog {dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- self-test};$selfText=Get-Content -LiteralPath $selfLog -Raw;if($selfText -notmatch 'Runner self-tests:\s+70 passed,\s+0 failed,\s+70 total\.'){throw 'CP133 expected 70/70 ScenarioRunner self-tests.'};Write-Host '       ScenarioRunner self-tests: 70/70 passed.'
        Write-Host '[5/8] Revalidating accepted parity/canonical kernel while candidate data remains non-executable...'
        Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'parity','--output-dir',$parityOut) 'CP133 research parity failed';$parity=Read-Json(Join-Path $parityOut 'summary.json');if(-not[bool]$parity.passed -or[int]$parity.cases -ne 25){throw 'CP133 expected 25/25 research parity.'};Write-Host '       Research parity: 25/25 passed.'
        & $python.Command @($python.Args+@('-B','-m','unittest','discover','-v','-s','tools/simulation/tests','-p','test_cp132_canonical_kernel.py'));if($LASTEXITCODE -ne 0){throw 'CP133 canonical-kernel regression failed.'};Write-Host '       Canonical-kernel regression: 6/6 passed.'
        Write-Host '[6/8] Writing repository-only acceptance marker...'
        $summary=[ordered]@{schemaVersion='star-cluster-cp133-repository-only-acceptance-v0.1';checkpoint=133;repositoryOnly=$true;acceptedMechanicsBaseline=132;previousAcceptedNumericalReference=128;python=$pythonVersion.Trim();dotnetSdk=$dotnetVersion;pythonTestsPassed=196;xunitTotal=$total;xunitPassed=$passed;xunitFailed=$failed;xunitSkipped=$skipped;scenarioRunnerSelfTestsPassed=70;researchParityPassed=25;canonicalKernelTestsPassed=6;technologyValuesChanged=$true;productionSourceChanged=$false;researchSimulationChanged=$false;scenarioDefinitionsChanged=$false;conceptChanged=$false;storyboardChanged=$false;balanceCalibrationRun=$false;monteCarloStudy=$false;substantiveTrials=0;mixedTlShipsExecuted=$false;automaticPromotion=$false;candidateMatrix='technology_numerical_matrix_v0_6.json';candidateTable='technology_component_table_v0_8.json';approximateTrackPenaltyPp=-25;extendedRangePenaltyPp=-10;mandatorySameTlDefenses=@('shield','armor');failedGates=@()}
        $summary|ConvertTo-Json -Depth 6|Set-Content -LiteralPath $repoOnlySummary -Encoding utf8
        Write-Host '[7/8] Verifying CP133 repository/results contract...';Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP133 repository-only contract failed'
        Write-Host '[8/8] Checkpoint 133 repository-only gates passed.' -ForegroundColor Green;Write-Host '       Run the same wrapper without -RepositoryOnly in this unchanged extraction to finalize the zero-study candidate-baseline acceptance summary.'
    }finally{Pop-Location};exit 0
}
if(-not(Test-Path -LiteralPath $repoOnlySummary)){throw 'CP133 finalization requires a successful -RepositoryOnly run in the same extraction first.'}
Write-Host '[3/8] Revalidating table preflight and repository-only marker...';Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot) 'CP133 final preflight failed';Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP133 prior contract failed';$prior=Read-Json $repoOnlySummary
Write-Host '[4/8] Preserving frozen implementation standing gates...';Write-Host '       196/196 Python; 910/910 xUnit; 70/70 ScenarioRunner; 25/25 parity; 6/6 canonical kernel.'
Write-Host '[5/8] Confirming candidate-only numerical boundary...';if([bool]$prior.productionSourceChanged -or[bool]$prior.researchSimulationChanged -or[bool]$prior.conceptChanged -or[bool]$prior.storyboardChanged -or[long]$prior.substantiveTrials -ne 0){throw 'CP133 change boundary violation.'};Write-Host '       Selected combat tables changed; production/kernel/Concept/Storyboard frozen; zero substantive trials.'
Write-Host '[6/8] Writing final native acceptance summary...';$final=[ordered]@{};foreach($p in $prior.PSObject.Properties){$final[$p.Name]=$p.Value};$final['schemaVersion']='star-cluster-cp133-native-acceptance-summary-v0.1';$final['repositoryOnly']=$false;$final|ConvertTo-Json -Depth 6|Set-Content -LiteralPath $finalSummary -Encoding utf8
Write-Host '[7/8] Verifying final CP133 contract...';Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP133 final contract failed'
Write-Host '[8/8] Checkpoint 133 native gates passed.' -ForegroundColor Green;Write-Host '       CP133 is accepted as the revised candidate numerical baseline for post-CP132 same-TL calibration; it is not a balance or production promotion.'
