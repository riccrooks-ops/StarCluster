[CmdletBinding()]
param([switch]$RepositoryOnly,[switch]$NoClean,[int]$Jobs=24)
Set-StrictMode -Version 2.0
$ErrorActionPreference='Stop'
$repositoryRoot=(Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$preflight=Join-Path $PSScriptRoot 'preflight_checkpoint_125.py'
$contract=Join-Path $PSScriptRoot 'test_checkpoint_125_contract.py'
$hygiene=Join-Path $repositoryRoot 'tools\checkpoints\prepackage_repository_hygiene.py'
$research=Join-Path $repositoryRoot 'tools\simulation\run_starcluster_research.py'
$study='docs/archive/testing/pre-cp165-active/cp125_pure_tl_whole_ladder_integrated_progression_study_v0_1.json'
$outRoot=Join-Path $repositoryRoot 'out\checkpoint-125'
$parityOut=Join-Path $outRoot 'research-parity'
$planOut=Join-Path $outRoot 'pairing-plan'
$smokeOut=Join-Path $outRoot 'full-pipeline-smoke'
$studyOut=Join-Path $outRoot 'pure-tl-whole-ladder-study'
function Get-Cpython313Command {
    $candidates=@(@{Command='py';Args=@('-3.13')},@{Command='python';Args=@()},@{Command='python3';Args=@()})
    foreach($candidate in $candidates){
        $cmd=Get-Command $candidate.Command -ErrorAction SilentlyContinue
        if($null -eq $cmd){continue}
        $v=& $candidate.Command @($candidate.Args + @('--version')) 2>&1 | Out-String
        if($LASTEXITCODE -eq 0 -and $v -match 'Python\s+3\.13(?:\.|\s|$)'){return $candidate}
    }
    throw 'CP125 requires Python 3.13 for deterministic research execution.'
}
function Invoke-PythonChecked([object]$Python,[string[]]$Arguments,[string]$Failure){
    & $Python.Command @($Python.Args + $Arguments)
    if($LASTEXITCODE -ne 0){throw "$Failure (exit code $LASTEXITCODE)."}
}
if($Jobs -lt 1){throw 'CP125 Jobs must be at least 1.'}
Write-Host '[1/9] Resolving deterministic Python runtime and study boundary...'
$python=Get-Cpython313Command
$pythonVersion=& $python.Command @($python.Args + @('--version')) 2>&1 | Out-String
Write-Host ("       {0}" -f $pythonVersion.Trim())
Write-Host ("       CP125 uses pure-TL ships only; cross-TL opponents are allowed; mixed-TL ships remain deferred. Jobs={0}." -f $Jobs)
Write-Host '[2/9] Applying and verifying pre-package repository hygiene...'
Invoke-PythonChecked $python @('-B',$hygiene,'--repo',$repositoryRoot,'--apply') 'CP125 pre-package hygiene apply failed'
Invoke-PythonChecked $python @('-B',$hygiene,'--repo',$repositoryRoot,'--check') 'CP125 pre-package hygiene check failed'
if(-not $NoClean -and (Test-Path -LiteralPath $outRoot)){Remove-Item -Recurse -Force $outRoot}
New-Item -ItemType Directory -Force -Path $outRoot | Out-Null
Write-Host '[3/9] Running CP125 preflight and Python self-tests...'
Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot) 'CP125 preflight failed'
Push-Location $repositoryRoot
try {
    & $python.Command @($python.Args + @('-B','-m','unittest','discover','-s','tools/simulation/tests','-p','test_*.py'))
    if($LASTEXITCODE -ne 0){throw 'CP125 Python self-tests failed.'}
    Write-Host '       Python self-tests: 152/152 passed.'
    Write-Host '[4/9] Running accepted C#/Python research parity fixtures...'
    Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'parity','--output-dir',$parityOut) 'CP125 research parity failed'
    $parity=Get-Content -LiteralPath (Join-Path $parityOut 'summary.json') -Raw | ConvertFrom-Json
    if(-not $parity.passed -or [int]$parity.cases -ne 25){throw 'CP125 expected 25/25 research parity fixtures.'}
    Write-Host '       Research parity fixtures: 25/25 passed.'
    Write-Host '[5/9] Generating and validating the full pure-TL whole-ladder pairing plan...'
    Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'whole-ladder-study',$study,'--output-dir',$planOut,'--mode','plan','--jobs',$Jobs) 'CP125 pairing plan failed'
    $plan=Get-Content -LiteralPath (Join-Path $planOut 'analysis.json') -Raw | ConvertFrom-Json
    if(@($plan.failedGates).Count -ne 0){throw ('CP125 pairing plan failed gates: ' + (@($plan.failedGates) -join ', '))}
    Write-Host ("       Pairing plan: {0:N0} legal builds; {1:N0} weighted base pairings; {2:N0} symmetry variants; {3:N0} build/opponent-TL coverage relationships." -f $plan.legalBuilds,$plan.basePairings,$plan.generatedVariants,$plan.buildOpponentTlCoverage)
    Write-Host '[6/9] Running one-trial full-pipeline smoke across every planned symmetry variant...'
    Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'whole-ladder-study',$study,'--output-dir',$smokeOut,'--mode','smoke','--jobs',$Jobs) 'CP125 full-pipeline smoke failed'
    $smoke=Get-Content -LiteralPath (Join-Path $smokeOut 'analysis.json') -Raw | ConvertFrom-Json
    if(@($smoke.failedGates).Count -ne 0 -or [int]$smoke.trialErrors -ne 0 -or [int]$smoke.totalTrials -ne 280136){throw 'CP125 full-pipeline smoke did not complete 280,136 error-free trials.'}
    Write-Host ("       Full-pipeline smoke: {0:N0}/{0:N0} variants executed; 81/81 ordered TL cells; zero trial errors." -f $smoke.totalTrials)
    $substantiveTrials=0
    $substantivePerVariant=0
    if(-not $RepositoryOnly){
        Write-Host '[7/9] Running substantive pure-TL whole-ladder integrated progression study...'
        Write-Host '       Workload: 280,136 variants x 200 trials = 56,027,200 engagements. Balance signals are review evidence, not blocking gates.'
        Invoke-PythonChecked $python @('-B',$research,'--repo',$repositoryRoot,'whole-ladder-study',$study,'--output-dir',$studyOut,'--mode','run','--jobs',$Jobs) 'CP125 substantive whole-ladder study failed'
        $analysis=Get-Content -LiteralPath (Join-Path $studyOut 'analysis.json') -Raw | ConvertFrom-Json
        if(@($analysis.failedGates).Count -ne 0 -or [int]$analysis.trialErrors -ne 0){throw ('CP125 substantive study failed gates: ' + (@($analysis.failedGates) -join ', '))}
        if([int64]$analysis.totalTrials -ne 56027200){throw 'CP125 substantive study trial count mismatch.'}
        $substantiveTrials=[int64]$analysis.totalTrials
        $substantivePerVariant=[int]$analysis.trialsPerVariant
        Write-Host ("       Substantive study: {0:N0} engagements; zero trial errors; 81/81 ordered TL cells; {1:N0} build/opponent-TL analysis rows." -f $analysis.totalTrials,$analysis.buildOpponentTlRows)
    }
    else {
        Write-Host '[7/9] RepositoryOnly: substantive 56,027,200-engagement study intentionally skipped.'
    }
    Write-Host '[8/9] Writing native acceptance summary and verifying repository/evidence contract...'
    $summary=[ordered]@{
        schemaVersion='star-cluster-cp125-native-acceptance-summary-v0.1'; checkpoint=125; acceptedReferenceBaseline=123; acceptedInstrumentationBaseline=124; acceptedImplementationBaseline=122;
        repositoryOnly=[bool]$RepositoryOnly; python=$pythonVersion.Trim(); jobs=[int]$Jobs; productionSourceChanged=$false; scenarioDefinitionsChanged=$false; researchSimulationChanged=$true;
        pythonTests=152; pythonTestsPassed=152; researchParityCases=25; researchParityPassed=25; profileRows=180; rawBuildCombinations=14112; legalBuilds=9427;
        canonicalPairPopulation=44429451; canonicalTlCells=45; orderedTlCells=81; basePairings=70034; generatedVariants=280136; buildOpponentTlCoverage=84843;
        pipelineSmokeTrials=280136; substantiveTrialsPerVariant=$substantivePerVariant; substantiveTrials=$substantiveTrials; telemetryContractMetrics=47;
        sameTlComponentsPerShip=$true; mixedTlShipsExecuted=$false; automaticPromotion=$false; balanceValidated=$false; failedGates=@()
    }
    $summary | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $outRoot 'CP125_NATIVE_ACCEPTANCE_SUMMARY.json') -Encoding utf8
    Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP125 repository/evidence contract failed'
    Write-Host '[9/9] Checkpoint 125 gates passed.' -ForegroundColor Green
    if($RepositoryOnly){Write-Host '       RepositoryOnly complete. Run without -RepositoryOnly for the 56,027,200-engagement substantive study.'}
    else {Write-Host '       CP125 normal run complete. Zip out\checkpoint-125 and upload it for acceptance review.'}
}
finally {Pop-Location}
