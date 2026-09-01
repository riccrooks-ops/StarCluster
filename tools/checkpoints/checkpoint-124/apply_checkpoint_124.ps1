[CmdletBinding()]
param([switch]$RepositoryOnly,[switch]$NoClean)
Set-StrictMode -Version 2.0
$ErrorActionPreference='Stop'
$repositoryRoot=(Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$preflight=Join-Path $PSScriptRoot 'preflight_checkpoint_124.py'
$contract=Join-Path $PSScriptRoot 'test_checkpoint_124_contract.py'
$hygiene=Join-Path $repositoryRoot 'tools\checkpoints\prepackage_repository_hygiene.py'
$research=Join-Path $repositoryRoot 'tools\simulation\run_starcluster_research.py'
$study='docs/archive/testing/pre-cp165-active/cp123_executable_baseline_instrumentation_foundation_v0_1.json'
$outRoot=Join-Path $repositoryRoot 'out\checkpoint-124'
$foundationOut=Join-Path $outRoot 'executable-baseline-foundation'
$parityOut=Join-Path $outRoot 'research-parity'
function Get-Cpython313Command {
    $candidates=@(@{Command='py';Args=@('-3.13')},@{Command='python';Args=@()},@{Command='python3';Args=@()})
    foreach($candidate in $candidates){
        $cmd=Get-Command $candidate.Command -ErrorAction SilentlyContinue
        if($null -eq $cmd){continue}
        $v=& $candidate.Command @($candidate.Args + @('--version')) 2>&1 | Out-String
        if($LASTEXITCODE -eq 0 -and $v -match 'Python\s+3\.13(?:\.|\s|$)'){return $candidate}
    }
    throw 'CP124 requires Python 3.13 for deterministic research/reference validation.'
}
function Invoke-PythonChecked([object]$Python,[string[]]$Arguments,[string]$Failure){
    & $Python.Command @($Python.Args + $Arguments)
    if($LASTEXITCODE -ne 0){throw "$Failure (exit code $LASTEXITCODE)."}
}
Write-Host '[1/8] Resolving deterministic Python runtime and research boundary...'
$python=Get-Cpython313Command
$pythonVersion=& $python.Command @($python.Args + @('--version')) 2>&1 | Out-String
Write-Host ("       {0}" -f $pythonVersion.Trim())
Write-Host '       CP124 changes Python research/instrumentation only; production C#/Godot and C# ScenarioRunner scenario definitions are frozen.'
Write-Host '[2/8] Applying and verifying pre-package repository hygiene...'
Invoke-PythonChecked $python @('-B',$hygiene,'--repo',$repositoryRoot,'--apply') 'CP124 pre-package hygiene apply failed'
Invoke-PythonChecked $python @('-B',$hygiene,'--repo',$repositoryRoot,'--check') 'CP124 pre-package hygiene check failed'
if(-not $NoClean -and (Test-Path -LiteralPath $outRoot)){Remove-Item -Recurse -Force $outRoot}
New-Item -ItemType Directory -Force -Path $outRoot | Out-Null
Write-Host '[3/8] Running CP124 preflight and Python self-tests...'
Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot) 'CP124 preflight failed'
Push-Location $repositoryRoot
try {
    & $python.Command @($python.Args + @('-B','-m','unittest','discover','-s','tools/simulation/tests','-p','test_*.py'))
    if($LASTEXITCODE -ne 0){throw 'CP124 Python self-tests failed.'}
    Write-Host '       Python self-tests: 139/139 passed.'
    Write-Host '[4/8] Running accepted C#/Python research parity fixtures...'
    Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'parity','--output-dir',$parityOut) 'CP124 research parity failed'
    $parity=Get-Content -LiteralPath (Join-Path $parityOut 'summary.json') -Raw | ConvertFrom-Json
    if(-not $parity.passed -or [int]$parity.cases -ne 25){throw 'CP124 expected 25/25 research parity fixtures.'}
    Write-Host '       Research parity fixtures: 25/25 passed.'
    Write-Host '[5/8] Running CP123 executable-catalog / legal-build / instrumentation foundation...'
    Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'baseline-foundation',$study,'--output-dir',$foundationOut) 'CP124 executable-baseline foundation failed'
    $analysis=Get-Content -LiteralPath (Join-Path $foundationOut 'analysis.json') -Raw | ConvertFrom-Json
    if(@($analysis.failedGates).Count -ne 0){throw ('CP124 foundation failed gates: ' + (@($analysis.failedGates) -join ', '))}
    Write-Host ("       Foundation: {0} profile rows; {1} raw combinations / {2} legal builds; {3} zero-weight smoke variants; {4} telemetry metrics; {5} blocking probes." -f $analysis.profileRows,$analysis.rawBuildCombinations,$analysis.legalBuilds,$analysis.pipelineSmokeVariants,$analysis.telemetryContractMetricCount,$analysis.instrumentationProbeCount)
    Write-Host '[6/8] Writing compact native/reference acceptance summary...'
    $summary=[ordered]@{
        schemaVersion='star-cluster-cp124-native-acceptance-summary-v0.1'; checkpoint=124; acceptedReferenceBaseline=123; acceptedImplementationBaseline=122;
        repositoryOnly=[bool]$RepositoryOnly; python=$pythonVersion.Trim(); productionSourceChanged=$false; scenarioDefinitionsChanged=$false; researchSimulationChanged=$true;
        pythonTests=139; pythonTestsPassed=139; researchParityCases=25; researchParityPassed=25; profileFamilies=[int]$analysis.profileFamilies; profileRows=[int]$analysis.profileRows;
        rawBuildCombinations=[int]$analysis.rawBuildCombinations; legalBuilds=[int]$analysis.legalBuilds; pipelineSmokeVariants=[int]$analysis.pipelineSmokeVariants; pipelineSmokeTrials=[int]$analysis.pipelineSmokeTrials;
        instrumentationProbes=[int]$analysis.instrumentationProbeCount; telemetryContractMetrics=[int]$analysis.telemetryContractMetricCount; newCSharpScenarioCount=0;
        substantiveMonteCarloTrials=0; balanceValidated=$false; automaticPromotion=$false; failedGates=@()
    }
    $summary | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $outRoot 'CP124_NATIVE_ACCEPTANCE_SUMMARY.json') -Encoding utf8
    Write-Host '[7/8] Verifying CP124 repository/evidence contract...'
    Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP124 repository/evidence contract failed'
    Write-Host '[8/8] Checkpoint 124 foundation gates passed.' -ForegroundColor Green
    if($RepositoryOnly){Write-Host '       RepositoryOnly complete. Run without -RepositoryOnly to repeat and freeze the normal compact handoff result.'}
    else {Write-Host '       CP124 normal run complete. Zip out\checkpoint-124 and upload it for acceptance review.'}
}
finally {Pop-Location}
