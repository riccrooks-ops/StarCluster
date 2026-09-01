[CmdletBinding()]
param([switch]$RepositoryOnly,[switch]$NoClean,[int]$Jobs=24)
$ErrorActionPreference='Stop'
$scriptRoot=Split-Path -Parent $MyInvocation.MyCommand.Path
$repositoryRoot=(Resolve-Path (Join-Path $scriptRoot '..\..\..')).Path
$preflight=Join-Path $scriptRoot 'preflight_checkpoint_161.py'
$contract=Join-Path $scriptRoot 'test_checkpoint_161_contract.py'
$research=Join-Path $repositoryRoot 'tools\simulation\run_starcluster_research.py'
$study=Join-Path $repositoryRoot 'docs\archive\testing\pre-cp165-active\cp161_reactor_tp_equilibrium_study_v0_1.json'
$outRoot=Join-Path $repositoryRoot 'out\checkpoint-161'
$testOut=Join-Path $outRoot 'xunit'
$parityOut=Join-Path $outRoot 'research-parity'
$deterministicOut=Join-Path $outRoot 'deterministic-scenarios'
$tl1PhaseAOut=Join-Path $outRoot 'tl1-phase-a'
$planOut=Join-Path $outRoot 'reactor-tp-plan'
$smokeOut=Join-Path $outRoot 'reactor-tp-smoke'
$staticOut=Join-Path $outRoot 'static-demand'
$stochasticOut=Join-Path $outRoot 'stochastic-demand'
$combatRoot=Join-Path $outRoot 'combat-batches'
$combatMerged=Join-Path $outRoot 'combat-merged'
$snapshotOut=Join-Path $outRoot 'pf4-snapshot'
$repoOnlySummary=Join-Path $outRoot 'CP161_REPOSITORY_ONLY_ACCEPTANCE.json'
$finalSummary=Join-Path $outRoot 'CP161_NATIVE_ACCEPTANCE_SUMMARY.json'
$transcriptPath=Join-Path $outRoot 'CP161_console_output.txt'
$transcriptStarted=$false

function Get-Cpython313Command {
 foreach($c in @(@{Command='py';Args=@('-3.13')},@{Command='python';Args=@()},@{Command='python3';Args=@()})){
  if(Get-Command $c.Command -ErrorAction SilentlyContinue){
   $v=& $c.Command @($c.Args+@('--version')) 2>&1|Out-String
   if($LASTEXITCODE -eq 0 -and $v -match 'Python\s+3\.13(?:\.|\s|$)'){return $c}
  }
 }
 throw 'CP161 requires Python 3.13.'
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
function Invoke-ReactorChecked([string[]]$Arguments,[string]$Failure){
 $sim=Join-Path $repositoryRoot 'tools\simulation';$oldPath=$env:PYTHONPATH
 try{
  if([string]::IsNullOrWhiteSpace($oldPath)){$env:PYTHONPATH=$sim}else{$env:PYTHONPATH=$sim+[IO.Path]::PathSeparator+$oldPath}
  & $python.Command @($python.Args+@('-B','-m','starcluster_research.reactor_tp_equilibrium','--repo',$repositoryRoot,'--study',$study)+$Arguments)
  if($LASTEXITCODE -ne 0){throw "$Failure (exit code $LASTEXITCODE)."}
 }finally{$env:PYTHONPATH=$oldPath}
}
function Invoke-PythonResearchTests {
 $files=@(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'tools\simulation\tests') -Filter 'test_*.py'|Sort-Object Name)
 if($files.Count -ne 52){throw "CP161 expected 52 Python modules, found $($files.Count)."}
 $sim=Join-Path $repositoryRoot 'tools\simulation';$oldPath=$env:PYTHONPATH
 try{
  if([string]::IsNullOrWhiteSpace($oldPath)){$env:PYTHONPATH=$sim}else{$env:PYTHONPATH=$sim+[IO.Path]::PathSeparator+$oldPath}
  $chunkSize=8;$chunks=[Math]::Ceiling($files.Count/[double]$chunkSize)
  for($c=0;$c -lt $chunks;$c++){
   $start=$c*$chunkSize;$end=[Math]::Min($files.Count-1,$start+$chunkSize-1)
   $mods=@($files[$start..$end]|ForEach-Object{"tools.simulation.tests.$($_.BaseName)"})
   Write-Host("       Python test chunk {0}/{1} ({2} modules)..." -f ($c+1),$chunks,$mods.Count)
   & $python.Command @($python.Args+@('-B','-m','unittest')+$mods)
   if($LASTEXITCODE -ne 0){throw "CP161 Python chunk $($c+1) failed."}
  }
 }finally{$env:PYTHONPATH=$oldPath}
}
function Valid-Summary([string]$Path,[string]$Mode,[int64]$Expected=-1,[string]$Field='combatTrials'){
 if(-not(Test-Path $Path)){return $false}
 try{
  $s=Read-Json $Path
  if(-not[bool]$s.passed -or [string]$s.mode -ne $Mode){return $false}
  if($Expected -ge 0 -and [int64]$s.$Field -ne $Expected){return $false}
  if($s.PSObject.Properties.Name -contains 'errorTrials' -and [int64]$s.errorTrials -ne 0){return $false}
  return $true
 }catch{return $false}
}
function Copy-Pf4Snapshot {
 if(Test-Path $snapshotOut){Remove-Item -Recurse -Force $snapshotOut}
 New-Item -ItemType Directory -Force -Path $snapshotOut|Out-Null
 Copy-Item -LiteralPath (Join-Path $repositoryRoot 'docs\design\player_technology\technology_research_execution_baseline_pending_finalization_v0_4.json') -Destination $snapshotOut
 Copy-Item -LiteralPath (Join-Path $repositoryRoot 'docs\validation\evidence\checkpoint-160\research_execution_baseline_manifest_v0_4.json') -Destination $snapshotOut
 Copy-Item -LiteralPath (Join-Path $repositoryRoot 'docs\validation\evidence\checkpoint-160\pf4_conformance_report_v0_1.json') -Destination $snapshotOut
 Copy-Item -LiteralPath (Join-Path $repositoryRoot 'docs\validation\evidence\checkpoint-161\accepted-cp160\CP160_NATIVE_ACCEPTANCE_SUMMARY.json') -Destination $snapshotOut
 Copy-Item -LiteralPath (Join-Path $repositoryRoot 'docs\validation\evidence\checkpoint-161\accepted-cp160\CP160_NATIVE_RESULTS_ARCHIVE_SHA256.txt') -Destination $snapshotOut
 Copy-Item -LiteralPath (Join-Path $repositoryRoot 'docs\validation\evidence\checkpoint-161\cp161_reactor_tp_study_contract_v0_1.json') -Destination $snapshotOut
}
function Stop-TranscriptSafe {
 if($script:transcriptStarted){try{Stop-Transcript|Out-Null}catch{};$script:transcriptStarted=$false}
}
function New-ResultZip {
 $stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
 $zip=Join-Path $repositoryRoot ("StarCluster_CP161_native_results_{0}.zip" -f $stamp)
 if(Test-Path $zip){Remove-Item -Force $zip}
 Compress-Archive -Path (Join-Path $outRoot '*') -DestinationPath $zip -CompressionLevel Optimal
 return $zip
}

$python=Get-Cpython313Command
$pythonVersion=& $python.Command @($python.Args+@('--version')) 2>&1|Out-String
$dotnetVersion=(& dotnet --version 2>&1|Out-String).Trim()
if($LASTEXITCODE -ne 0 -or $dotnetVersion -ne '8.0.423'){throw "CP161 requires .NET SDK 8.0.423 exactly; observed '$dotnetVersion'."}
if($RepositoryOnly -and -not $NoClean -and (Test-Path $outRoot)){Remove-Item -Recurse -Force $outRoot}
New-Item -ItemType Directory -Force -Path $outRoot|Out-Null
Start-Transcript -Path $transcriptPath -Append|Out-Null;$transcriptStarted=$true

try{
 Write-Host("CP161 runtimes: {0}; .NET SDK {1}; jobs {2}" -f $pythonVersion.Trim(),$dotnetVersion,$Jobs)
 Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot) 'CP161 preflight failed'

 if($RepositoryOnly){
  New-Item -ItemType Directory -Force -Path $testOut,$parityOut,$deterministicOut,$tl1PhaseAOut|Out-Null
  Push-Location $repositoryRoot
  try{
   Write-Host '[1/10] Python research regression (660 tests)...';Invoke-PythonResearchTests
   Write-Host '[2/10] Warning-as-error .NET build...';Invoke-Captured 'CP161 build' (Join-Path $outRoot 'build.log'){dotnet build StarCluster.sln --configuration Release --nologo -warnaserror}
   Write-Host '[3/10] xUnit + ScenarioRunner regression...'
   dotnet test tests\StarCluster.Tests\StarCluster.Tests.csproj --configuration Release --no-build --nologo --logger 'trx;LogFileName=cp161-tests.trx' --results-directory $testOut
   $xunitExit=$LASTEXITCODE;[xml]$trx=Get-Content -LiteralPath (Join-Path $testOut 'cp161-tests.trx') -Raw;$c=$trx.TestRun.ResultSummary.Counters
   $total=[int]$c.total;$passed=[int]$c.passed;$failed=[int]$c.failed;$skipped=[int]$c.notExecuted
   if($xunitExit -ne 0 -or $total -ne 934 -or $passed -ne 934 -or $failed -ne 0 -or $skipped -ne 0){throw 'CP161 xUnit mismatch.'}
   $selfLog=Join-Path $outRoot 'scenario-self-tests.log';Invoke-Captured 'CP161 ScenarioRunner self-tests' $selfLog {dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- self-test}
   if((Get-Content $selfLog -Raw)-notmatch 'Runner self-tests:\s+70 passed,\s+0 failed,\s+70 total\.'){throw 'CP161 expected 70/70 self-tests.'}
   Invoke-Captured 'CP161 deterministic scenarios' (Join-Path $outRoot 'deterministic-scenarios.log'){dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- run-all --output-dir $deterministicOut}
   Invoke-Captured 'CP161 TL1 Phase-A' (Join-Path $outRoot 'tl1-phase-a.log'){dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- tl1-phase-a --output-dir $tl1PhaseAOut}
   Write-Host '[4/10] C#/Python parity...';Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'parity','--output-dir',$parityOut) 'CP161 parity failed';$parity=Read-Json (Join-Path $parityOut 'summary.json');if(-not[bool]$parity.passed -or [int]$parity.cases -ne 25){throw 'CP161 parity mismatch.'}
   Write-Host '[5/10] CP161 focused Reactor/TP tests (32)...';$sim=Join-Path $repositoryRoot 'tools\simulation';$oldPath=$env:PYTHONPATH
   try{if([string]::IsNullOrWhiteSpace($oldPath)){$env:PYTHONPATH=$sim}else{$env:PYTHONPATH=$sim+[IO.Path]::PathSeparator+$oldPath};& $python.Command @($python.Args+@('-B','-m','unittest','discover','-v','-s','tools/simulation/tests','-p','test_cp161_*.py'));if($LASTEXITCODE -ne 0){throw 'CP161 focused tests failed.'}}finally{$env:PYTHONPATH=$oldPath}
   Write-Host '[6/10] Reactor/TP exact study plan...';if(Test-Path $planOut){Remove-Item -Recurse -Force $planOut};Invoke-ReactorChecked @('plan','--out',$planOut) 'CP161 plan failed';$pl=Read-Json (Join-Path $planOut 'summary.json');if([int]$pl.legalPoweredArchitectures -ne 22482 -or [int64]$pl.stochasticTurnSamples -ne 7776000 -or [int64]$pl.combatTrials -ne 4536000){throw 'CP161 plan mismatch.'}
   Write-Host '[7/10] Live PF4 Reactor/TP integration smoke...';if(Test-Path $smokeOut){Remove-Item -Recurse -Force $smokeOut};Invoke-ReactorChecked @('smoke','--out',$smokeOut) 'CP161 smoke failed';$sm=Read-Json (Join-Path $smokeOut 'summary.json');if(-not[bool]$sm.passed -or [int]$sm.probes -ne 5 -or [int]$sm.combatTrials -ne 3){throw 'CP161 smoke mismatch.'}
   Write-Host '[8/10] Exact architecture/supply/Space/TP sensitivity surfaces...';if(Test-Path $staticOut){Remove-Item -Recurse -Force $staticOut};Invoke-ReactorChecked @('static','--out',$staticOut) 'CP161 static analysis failed';$st=Read-Json (Join-Path $staticOut 'summary.json');if([int]$st.legalPoweredArchitectures -ne 22482 -or [int]$st.staticSupplyRows -ne 3132 -or [int]$st.reactorSpaceRows -ne 45 -or [int]$st.costSensitivityRows -ne 1368){throw 'CP161 static analysis scale mismatch.'}
   Write-Host '[9/10] Freezing accepted PF4/CP160 provenance snapshot...';Copy-Pf4Snapshot
   Write-Host '[10/10] Writing RepositoryOnly acceptance...'
   $summary=[ordered]@{schemaVersion='star-cluster-cp161-repository-only-acceptance-v0.1';checkpoint=161;repositoryOnly=$true;failedGates=@();python=$pythonVersion.Trim();dotnetSdk=$dotnetVersion;buildPassed=$true;pythonTestsPassed=660;xunitTotal=$total;xunitPassed=$passed;xunitFailed=$failed;xunitSkipped=$skipped;scenarioRunnerSelfTestsPassed=70;deterministicScenarioCorpusPassed=$true;tl1PhaseACorpusPassed=$true;researchParityPassed=25;cp161FocusedTestsPassed=32;acceptedBaseCheckpoint=160;pendingFinalizationBaselineId='CP160-PF4';pendingFinalizationMatrixSha256='7fd4dfbbe375586de2605361006db84b68f89767c76ba4b76da6cf5f48253155';productionAuthorityChanged=$false;conceptChanged=$false;tuningAllowed=$false;automaticPromotion=$false;legalPoweredArchitectures=22482;oneReactorArchitectures=16741;twoReactorArchitectures=5741;representativeLoadouts=108;stochasticVariants=648;plannedStochasticTurnSamples=7776000;combatContexts=324;combatCells=2268;plannedSubstantiveCombatTrials=4536000;architectureSmokeCombats=3;substantiveCombatTrials=0;stochasticTurnSamples=0;operationalSupplySweep='2-30 TP per Reactor';reactorSpaceSweep='4-8 Space';combatSupplyOffsets='-4,-2,0,+2,+4,+6,+8 from PF4';optionalSecondReactorIncluded=$true;isolatedAuxMagnitudeArchitectureRemainClosed=$true;poweredAuxTpCostsRemainProvisional=$true;repairDroneIntegratedComponentDamageExecutionDeferred=$true;selectionDeferredToNextCheckpoint=$true}
   $summary|ConvertTo-Json -Depth 8|Set-Content $repoOnlySummary -Encoding UTF8
   Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP161 RepositoryOnly contract failed'
   Write-Host 'CP161 RepositoryOnly PASSED. Run again without -RepositoryOnly to execute/resume 7,776,000 tactical-demand samples and 4,536,000 full-map combat trials.' -ForegroundColor Green
  }finally{Pop-Location}
  Stop-TranscriptSafe
  exit 0
 }

 if(-not(Test-Path $repoOnlySummary)){throw 'Run CP161 -RepositoryOnly first in this same extraction.'}
 Push-Location $repositoryRoot
 try{
  Write-Host '[final 1/5] Revalidating repository, PF4, and RepositoryOnly state...';Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot) 'CP161 final preflight failed';Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP161 RepositoryOnly state contract failed'
  Write-Host '[final 2/5] Executing/resuming stochastic whole-ship demand/allocation surface (7,776,000 turn samples)...';$sum=Join-Path $stochasticOut 'summary.json';if(Valid-Summary $sum 'stochastic' 7776000 'turnSamples'){Write-Host '       CP161 stochastic surface valid; reusing.'}else{if(Test-Path $stochasticOut){Remove-Item -Recurse -Force $stochasticOut};Invoke-ReactorChecked @('stochastic','--static-dir',$staticOut,'--out',$stochasticOut,'--jobs',[string]$Jobs) 'CP161 stochastic demand surface failed'}
  Write-Host '[final 3/5] Executing/resuming full-map Reactor-output combat batches (9 x 504,000 = 4,536,000)...';New-Item -ItemType Directory -Force -Path $combatRoot|Out-Null
  foreach($tl in 1..9){$dir=Join-Path $combatRoot ("TL{0}" -f $tl);$sum=Join-Path $dir 'summary.json';if(Valid-Summary $sum 'combat-batch' 504000){Write-Host("       Combat TL{0} valid; reusing." -f $tl)}else{if(Test-Path $dir){Remove-Item -Recurse -Force $dir};Invoke-ReactorChecked @('combat-batch','--tl',[string]$tl,'--out',$dir,'--jobs',[string]$Jobs) "CP161 combat TL$tl failed"}}
  Write-Host '[final 4/5] Merging Reactor/TP combat response surface...';if(Test-Path $combatMerged){Remove-Item -Recurse -Force $combatMerged};Invoke-ReactorChecked @('merge-combat','--batches',$combatRoot,'--out',$combatMerged) 'CP161 combat merge failed';$cm=Read-Json (Join-Path $combatMerged 'summary.json');if(-not[bool]$cm.passed -or [int]$cm.batches -ne 9 -or [int]$cm.cells -ne 2268 -or [int64]$cm.combatTrials -ne 4536000 -or [int64]$cm.errorTrials -ne 0){throw 'CP161 merged combat contract mismatch.'}
  Write-Host '[final 5/5] Writing final diagnostic acceptance and packaging results...';$sd=Read-Json (Join-Path $stochasticOut 'summary.json');$ro=Read-Json $repoOnlySummary;$final=[ordered]@{};$ro.psobject.Properties|ForEach-Object{$final[$_.Name]=$_.Value};$final['schemaVersion']='star-cluster-cp161-native-acceptance-v0.1';$final['repositoryOnly']=$false;$final['repositoryOnlyAccepted']=$true;$final['stochasticTurnSamples']=[int64]$sd.turnSamples;$final['stochasticVariantsCompleted']=[int]$sd.variants;$final['substantiveCombatTrials']=[int64]$cm.combatTrials;$final['combatCellsCompleted']=[int]$cm.cells;$final['combatTurnCapSentinels']=[int64]$cm.turnCapSentinels;$final['combatErrorTrials']=[int64]$cm.errorTrials;$final['studyCompleted']=$true;$final['tuningAllowed']=$false;$final['automaticPromotion']=$false;$final['productionAuthorityChanged']=$false;$final['selectionDeferredToNextCheckpoint']=$true
  if([int64]$final['stochasticTurnSamples'] -ne 7776000 -or [int64]$final['substantiveCombatTrials'] -ne 4536000 -or [int64]$final['combatErrorTrials'] -ne 0){throw 'CP161 final substantive scale/error mismatch.'}
  $final|ConvertTo-Json -Depth 8|Set-Content $finalSummary -Encoding UTF8
  Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP161 final contract failed'
 }finally{Pop-Location}
 Stop-TranscriptSafe
 $zip=New-ResultZip
 Write-Host "CP161 native acceptance PASSED. Results: $zip" -ForegroundColor Green
}finally{Stop-TranscriptSafe}
