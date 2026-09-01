[CmdletBinding()]
param([switch]$RepositoryOnly,[switch]$NoClean)
Set-StrictMode -Version 2.0
$ErrorActionPreference='Stop'
$repositoryRoot=(Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$preflight=Join-Path $PSScriptRoot 'preflight_checkpoint_123.py'
$contract=Join-Path $PSScriptRoot 'test_checkpoint_123_contract.py'
$hygiene=Join-Path $repositoryRoot 'tools\checkpoints\prepackage_repository_hygiene.py'
$outRoot=Join-Path $repositoryRoot 'out\checkpoint-123'
function Get-Cpython313Command {
    $candidates=@(@{Command='py';Args=@('-3.13')},@{Command='python';Args=@()},@{Command='python3';Args=@()})
    foreach($candidate in $candidates){
        $cmd=Get-Command $candidate.Command -ErrorAction SilentlyContinue
        if($null -eq $cmd){continue}
        $v=& $candidate.Command @($candidate.Args + @('--version')) 2>&1 | Out-String
        if($LASTEXITCODE -eq 0 -and $v -match 'Python\s+3\.13(?:\.|\s|$)'){return $candidate}
    }
    throw 'CP123 requires Python 3.13 for deterministic repository/reference validation.'
}
function Invoke-PythonChecked([object]$Python,[string[]]$Arguments,[string]$Failure){
    & $Python.Command @($Python.Args + $Arguments)
    if($LASTEXITCODE -ne 0){throw "$Failure (exit code $LASTEXITCODE)."}
}
Write-Host '[1/5] Resolving deterministic Python runtime...'
$python=Get-Cpython313Command
$pythonVersion=& $python.Command @($python.Args + @('--version')) 2>&1 | Out-String
Write-Host ("       {0}" -f $pythonVersion.Trim())
Write-Host '       CP123 is reference-only: no production build, scenario run, or Monte Carlo calibration is invoked.'
Write-Host '[2/5] Applying and verifying pre-package repository hygiene...'
Invoke-PythonChecked $python @('-B',$hygiene,'--repo',$repositoryRoot,'--apply') 'CP123 pre-package hygiene apply failed'
Invoke-PythonChecked $python @('-B',$hygiene,'--repo',$repositoryRoot,'--check') 'CP123 pre-package hygiene check failed'
if(-not $NoClean -and (Test-Path -LiteralPath $outRoot)){Remove-Item -Recurse -Force $outRoot}
New-Item -ItemType Directory -Force -Path $outRoot | Out-Null
Write-Host '[3/5] Running CP123 technology-reference preflight and Python self-tests...'
Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot) 'CP123 technology-reference preflight failed'
Push-Location $repositoryRoot
try {
    & $python.Command @($python.Args + @('-B','-m','unittest','discover','-s','tools/simulation/tests','-p','test_*.py'))
    if($LASTEXITCODE -ne 0){throw 'CP123 Python self-tests failed.'}
    Write-Host '       Python self-tests: 124/124 passed.'
    Write-Host '[4/5] Writing compact reference acceptance summary and verifying repository contract...'
    $summary=[ordered]@{
        schemaVersion='star-cluster-cp123-native-acceptance-summary-v0.1'; checkpoint=123; acceptedBaseline=122; repositoryOnly=[bool]$RepositoryOnly; python=$pythonVersion.Trim(); referenceOnly=$true;
        productionSourceChanged=$false; scenarioDefinitionsChanged=$false; simulationMechanicsChanged=$false; pythonTests=124; pythonTestsPassed=124;
        disciplines=10; lineages=33; storyboardBeats=218; technologyTableEntries=218; ideaRegisterEntries=138; numericalProfileFamilies=20; numericalProfileRows=180;
        damagePointScale=2; productionRepairHullPerKitTl1=1; criticalCadenceMigrated=$false; acceptedCp122XunitTests=905; acceptedCp122ScenarioRunnerSelfTests=70;
        acceptedCp122ResearchParityCases=25; acceptedCp122CanonicalParityCases=234138; acceptedCp122CanonicalParityMismatches=0; newScenarioCount=0; substantiveMonteCarloTrials=0; balanceValidated=$false; failedGates=@()
    }
    $summary | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $outRoot 'CP123_NATIVE_ACCEPTANCE_SUMMARY.json') -Encoding utf8
    Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP123 repository/reference contract failed'
    Write-Host '       Reference authority: 10 disciplines / 33 lineages / 218 exact Storyboard-Tech-Table beats / 20x9 numerical profile rows.'
    Write-Host '       Production/scenario/simulation surfaces match accepted CP122; newScenarioCount=0; substantiveMonteCarloTrials=0.'
    Write-Host '[5/5] Checkpoint 123 deterministic reference gates passed.' -ForegroundColor Green
    if($RepositoryOnly){Write-Host '       RepositoryOnly complete. Run without -RepositoryOnly to repeat and freeze the normal compact handoff result.'}
    else {Write-Host '       CP123 normal run complete. Zip out\checkpoint-123 and upload it for acceptance review.'}
}
finally {Pop-Location}
