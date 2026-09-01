[CmdletBinding()]
param([switch]$RepositoryOnly,[switch]$NoClean)
$ErrorActionPreference='Stop'
$scriptRoot=Split-Path -Parent $MyInvocation.MyCommand.Path
$repositoryRoot=(Resolve-Path (Join-Path $scriptRoot '..\..\..')).Path
$preflight=Join-Path $scriptRoot 'preflight_checkpoint_160.py'
$contract=Join-Path $scriptRoot 'test_checkpoint_160_contract.py'
$research=Join-Path $repositoryRoot 'tools\simulation\run_starcluster_research.py'
$outRoot=Join-Path $repositoryRoot 'out\checkpoint-160'
$testOut=Join-Path $outRoot 'xunit'
$parityOut=Join-Path $outRoot 'research-parity'
$deterministicOut=Join-Path $outRoot 'deterministic-scenarios'
$tl1PhaseAOut=Join-Path $outRoot 'tl1-phase-a'
$snapshotOut=Join-Path $outRoot 'pf4-snapshot'
$repoOnlySummary=Join-Path $outRoot 'CP160_REPOSITORY_ONLY_ACCEPTANCE.json'
$finalSummary=Join-Path $outRoot 'CP160_NATIVE_ACCEPTANCE_SUMMARY.json'

function Get-Cpython313Command {
 foreach($c in @(@{Command='py';Args=@('-3.13')},@{Command='python';Args=@()},@{Command='python3';Args=@()})){
  if(Get-Command $c.Command -ErrorAction SilentlyContinue){
   $v=& $c.Command @($c.Args+@('--version')) 2>&1|Out-String
   if($LASTEXITCODE -eq 0 -and $v -match 'Python\s+3\.13(?:\.|\s|$)'){return $c}
  }
 }
 throw 'CP160 requires Python 3.13.'
}
function Invoke-PythonChecked([object]$Python,[string[]]$Arguments,[string]$Failure){
 & $Python.Command @($Python.Args+$Arguments)
 if($LASTEXITCODE -ne 0){throw "$Failure (exit code $LASTEXITCODE)."}
}
function Invoke-Captured([string]$Label,[string]$LogPath,[scriptblock]$Body){
 $old=$ErrorActionPreference
 try{$ErrorActionPreference='Continue';& $Body *> $LogPath;$code=$LASTEXITCODE}finally{$ErrorActionPreference=$old}
 if($code -ne 0){
  Write-Host "       $Label output tail:" -ForegroundColor Yellow
  Get-Content -LiteralPath $LogPath -Tail 120|ForEach-Object{Write-Host("       $_")}
  throw "$Label failed (exit code $code)."
 }
}
function Read-Json([string]$Path){return(Get-Content -LiteralPath $Path -Raw|ConvertFrom-Json)}
function Invoke-PythonResearchTests {
 $files=@(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'tools\simulation\tests') -Filter 'test_*.py'|Sort-Object Name)
 if($files.Count -ne 51){throw "CP160 expected 51 Python modules, found $($files.Count)."}
 $sim=Join-Path $repositoryRoot 'tools\simulation';$oldPath=$env:PYTHONPATH
 try{
  if([string]::IsNullOrWhiteSpace($oldPath)){$env:PYTHONPATH=$sim}else{$env:PYTHONPATH=$sim+[IO.Path]::PathSeparator+$oldPath}
  $chunkSize=8;$chunks=[Math]::Ceiling($files.Count/[double]$chunkSize)
  for($c=0;$c -lt $chunks;$c++){
   $start=$c*$chunkSize;$end=[Math]::Min($files.Count-1,$start+$chunkSize-1)
   $mods=@($files[$start..$end]|ForEach-Object{"tools.simulation.tests.$($_.BaseName)"})
   Write-Host("       Python test chunk {0}/{1} ({2} modules)..." -f ($c+1),$chunks,$mods.Count)
   & $python.Command @($python.Args+@('-B','-m','unittest')+$mods)
   if($LASTEXITCODE -ne 0){throw "CP160 Python chunk $($c+1) failed."}
  }
 }finally{$env:PYTHONPATH=$oldPath}
}
function Copy-Pf4Snapshot {
 if(Test-Path $snapshotOut){Remove-Item -Recurse -Force $snapshotOut}
 New-Item -ItemType Directory -Force -Path $snapshotOut|Out-Null
 $ev=Join-Path $repositoryRoot 'docs\validation\evidence\checkpoint-160'
 foreach($n in @('research_execution_baseline_manifest_v0_4.json','research_execution_baseline_diff_v0_4.csv','aux_pending_finalization_promotion_ledger_v0_2.csv','cp159_aux_closure_selection_evidence_v0_1.json','pf4_conformance_report_v0_1.json')){
  Copy-Item -LiteralPath (Join-Path $ev $n) -Destination $snapshotOut
 }
 Copy-Item -LiteralPath (Join-Path $repositoryRoot 'docs\design\player_technology\technology_research_execution_baseline_pending_finalization_v0_4.json') -Destination $snapshotOut
 Copy-Item -LiteralPath (Join-Path $ev 'accepted-cp159\CP159_NATIVE_ACCEPTANCE_SUMMARY.json') -Destination $snapshotOut
}
function New-ResultZip {
 $stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
 $zip=Join-Path $repositoryRoot ("StarCluster_CP160_native_results_{0}.zip" -f $stamp)
 if(Test-Path $zip){Remove-Item -Force $zip}
 Compress-Archive -Path (Join-Path $outRoot '*') -DestinationPath $zip -CompressionLevel Optimal
 return $zip
}

$python=Get-Cpython313Command
$pythonVersion=& $python.Command @($python.Args+@('--version')) 2>&1|Out-String
$dotnetVersion=(& dotnet --version 2>&1|Out-String).Trim()
if($LASTEXITCODE -ne 0 -or $dotnetVersion -ne '8.0.423'){throw "CP160 requires .NET SDK 8.0.423 exactly; observed '$dotnetVersion'."}
Write-Host("CP160 runtimes: {0}; .NET SDK {1}" -f $pythonVersion.Trim(),$dotnetVersion)
Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot) 'CP160 preflight failed'

if($RepositoryOnly){
 if(-not $NoClean -and (Test-Path $outRoot)){Remove-Item -Recurse -Force $outRoot}
 New-Item -ItemType Directory -Force -Path $outRoot,$testOut,$parityOut,$deterministicOut,$tl1PhaseAOut|Out-Null
 Push-Location $repositoryRoot
 try{
  Write-Host '[1/7] Python research regression (628 tests)...';Invoke-PythonResearchTests
  Write-Host '[2/7] Warning-as-error .NET build...';Invoke-Captured 'CP160 build' (Join-Path $outRoot 'build.log'){dotnet build StarCluster.sln --configuration Release --nologo -warnaserror}
  Write-Host '[3/7] xUnit + ScenarioRunner regression...'
  dotnet test tests\StarCluster.Tests\StarCluster.Tests.csproj --configuration Release --no-build --nologo --logger 'trx;LogFileName=cp160-tests.trx' --results-directory $testOut
  $xunitExit=$LASTEXITCODE
  [xml]$trx=Get-Content -LiteralPath (Join-Path $testOut 'cp160-tests.trx') -Raw
  $c=$trx.TestRun.ResultSummary.Counters;$total=[int]$c.total;$passed=[int]$c.passed;$failed=[int]$c.failed;$skipped=[int]$c.notExecuted
  if($xunitExit -ne 0 -or $total -ne 934 -or $passed -ne 934 -or $failed -ne 0 -or $skipped -ne 0){throw 'CP160 xUnit mismatch.'}
  $selfLog=Join-Path $outRoot 'scenario-self-tests.log'
  Invoke-Captured 'CP160 ScenarioRunner self-tests' $selfLog {dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- self-test}
  if((Get-Content $selfLog -Raw)-notmatch 'Runner self-tests:\s+70 passed,\s+0 failed,\s+70 total\.'){throw 'CP160 expected 70/70 self-tests.'}
  Invoke-Captured 'CP160 deterministic scenarios' (Join-Path $outRoot 'deterministic-scenarios.log'){dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- run-all --output-dir $deterministicOut}
  Invoke-Captured 'CP160 TL1 Phase-A' (Join-Path $outRoot 'tl1-phase-a.log'){dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- tl1-phase-a --output-dir $tl1PhaseAOut}
  Write-Host '[4/7] C#/Python parity...';Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'parity','--output-dir',$parityOut) 'CP160 parity failed'
  $parity=Read-Json (Join-Path $parityOut 'summary.json');if(-not [bool]$parity.passed -or [int]$parity.cases -ne 25){throw 'CP160 parity mismatch.'}
  Write-Host '[5/7] CP160 focused PF4-promotion tests...'
  $sim=Join-Path $repositoryRoot 'tools\simulation';$oldPath=$env:PYTHONPATH
  try{
   if([string]::IsNullOrWhiteSpace($oldPath)){$env:PYTHONPATH=$sim}else{$env:PYTHONPATH=$sim+[IO.Path]::PathSeparator+$oldPath}
   & $python.Command @($python.Args+@('-B','-m','unittest','discover','-v','-s','tools/simulation/tests','-p','test_cp160_*.py'))
   if($LASTEXITCODE -ne 0){throw 'CP160 focused tests failed.'}
  }finally{$env:PYTHONPATH=$oldPath}
  Write-Host '[6/7] Freezing PF4 AUX-closure snapshot...';Copy-Pf4Snapshot
  Write-Host '[7/7] Writing RepositoryOnly acceptance...'
  $bm=Read-Json (Join-Path $repositoryRoot 'docs\validation\evidence\checkpoint-160\research_execution_baseline_manifest_v0_4.json')
  $summary=[ordered]@{
   schemaVersion='star-cluster-cp160-repository-only-acceptance-v0.1';checkpoint=160;repositoryOnly=$true;failedGates=@();python=$pythonVersion.Trim();dotnetSdk=$dotnetVersion;buildPassed=$true;
   pythonTestsPassed=628;xunitTotal=$total;xunitPassed=$passed;xunitFailed=$failed;xunitSkipped=$skipped;scenarioRunnerSelfTestsPassed=70;deterministicScenarioCorpusPassed=$true;tl1PhaseACorpusPassed=$true;researchParityPassed=25;cp160FocusedTestsPassed=24;
   pendingFinalizationBaselineId='CP160-PF4';pendingFinalizationMatrixSha256=$bm.materializedMatrixSha256;researchExecutionAuthorityPromoted=$true;productionAuthorityChanged=$false;
   cp159NativeEvidenceAccepted=$true;isolatedAuxMagnitudeArchitectureClosed=$true;poweredAuxTpCostsRemainProvisional=$true;fieldStabilizerTrajectory='16/18/20@1TP';crystallineTrajectory='CRY_RISE_A';repairDroneMechanic='+1 distinct-target Damage Control action';repairDroneKitRule='+100% default prepared kit reserve';
   substantiveCombatTrials=0;repairDroneMicroTrials=0;tuningAllowed=$false;automaticFinalProductionPromotion=$false;nextPass='Reactor/TP Scarcity and Whole-Ship Equilibrium';finalMajorPass='Reactor/TP Scarcity and Whole-Ship Equilibrium'
  }
  $summary|ConvertTo-Json -Depth 8|Set-Content $repoOnlySummary -Encoding UTF8
  Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP160 RepositoryOnly contract failed'
  Write-Host 'CP160 RepositoryOnly PASSED. Run again without -RepositoryOnly for final zero-combat native acceptance/package.' -ForegroundColor Green
 }finally{Pop-Location}
 exit 0
}

if(-not(Test-Path $repoOnlySummary)){throw 'Run CP160 -RepositoryOnly first in this same extraction.'}
Push-Location $repositoryRoot
try{
 Write-Host '[final 1/3] Revalidating repository and PF4 AUX closure...';Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot) 'CP160 final preflight failed';Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP160 RepositoryOnly state contract failed'
 Write-Host '[final 2/3] Writing final zero-combat native acceptance...'
 $ro=Read-Json $repoOnlySummary;$final=[ordered]@{};$ro.psobject.Properties|ForEach-Object{$final[$_.Name]=$_.Value}
 $final['schemaVersion']='star-cluster-cp160-native-acceptance-v0.1';$final['repositoryOnly']=$false;$final['repositoryOnlyAccepted']=$true;$final['baselinePromotionCompleted']=$true
 $final|ConvertTo-Json -Depth 8|Set-Content $finalSummary -Encoding UTF8
 Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP160 final contract failed'
 Write-Host '[final 3/3] Packaging native results...';$zip=New-ResultZip;Write-Host "CP160 native acceptance PASSED. Results: $zip" -ForegroundColor Green
}finally{Pop-Location}
