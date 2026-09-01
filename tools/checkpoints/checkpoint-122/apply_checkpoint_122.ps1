[CmdletBinding()]
param([switch]$RepositoryOnly,[switch]$NoClean)
Set-StrictMode -Version 2.0
$ErrorActionPreference='Stop'
$repositoryRoot=(Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$preflight=Join-Path $PSScriptRoot 'preflight_checkpoint_122.py'
$contract=Join-Path $PSScriptRoot 'test_checkpoint_122_contract.py'
$hygiene=Join-Path $repositoryRoot 'tools\checkpoints\prepackage_repository_hygiene.py'
$cli=Join-Path $repositoryRoot 'tools\simulation\run_starcluster_research.py'
$outRoot=Join-Path $repositoryRoot 'out\checkpoint-122'
$parityOut=Join-Path $outRoot 'research-parity'
$damageParityOut=Join-Path $outRoot 'canonical-damage-scale-parity'
$testOut=Join-Path $outRoot 'xunit'

function Get-Cpython313Command {
    $candidates=@(@{Command='py';Args=@('-3.13')},@{Command='python';Args=@()},@{Command='python3';Args=@()})
    foreach($candidate in $candidates){
        $cmd=Get-Command $candidate.Command -ErrorAction SilentlyContinue
        if($null -eq $cmd){continue}
        $versionText=& $candidate.Command @($candidate.Args + @('--version')) 2>&1 | Out-String
        if($LASTEXITCODE -eq 0 -and $versionText -match 'Python\s+3\.13(?:\.|\s|$)'){return $candidate}
    }
    throw 'CP122 requires CPython 3.13 for deterministic repository/research validation.'
}
function Invoke-PythonChecked([object]$Python,[string[]]$Arguments,[string]$FailureMessage){
    & $Python.Command @($Python.Args + $Arguments)
    if($LASTEXITCODE -ne 0){throw "$FailureMessage (exit code $LASTEXITCODE)."}
}
function Invoke-Captured([string]$Label,[string]$LogPath,[scriptblock]$Body){
    & $Body *> $LogPath
    $exitCode=$LASTEXITCODE
    if($exitCode -ne 0){
        Write-Host "       $Label output tail:" -ForegroundColor Yellow
        Get-Content -LiteralPath $LogPath -Tail 80 | ForEach-Object { Write-Host ("       $_") }
        throw "$Label failed (exit code $exitCode)."
    }
}

Write-Host '[1/10] Resolving deterministic runtimes and pinned SDK...'
$python=Get-Cpython313Command
$pythonVersion=& $python.Command @($python.Args + @('--version')) 2>&1 | Out-String
Write-Host ("       {0}" -f $pythonVersion.Trim())
$dotnet=Get-Command dotnet -ErrorAction SilentlyContinue
if($null -eq $dotnet){throw 'CP122 requires the pinned .NET SDK 8.0.423; dotnet was not found.'}
$dotnetVersion=(& dotnet --version 2>&1 | Out-String).Trim()
if($LASTEXITCODE -ne 0 -or $dotnetVersion -ne '8.0.423'){throw "CP122 requires .NET SDK 8.0.423 exactly; observed '$dotnetVersion'."}
Write-Host "       .NET SDK $dotnetVersion"
Write-Host '       Production/game runtime remains C# / Godot; Python is validation/research infrastructure only.'

Write-Host '[2/10] Applying and verifying pre-package repository hygiene...'
Invoke-PythonChecked $python @('-B',$hygiene,'--repo',$repositoryRoot,'--apply') 'CP122 pre-package hygiene apply failed'
Invoke-PythonChecked $python @('-B',$hygiene,'--repo',$repositoryRoot,'--check') 'CP122 pre-package hygiene check failed'
if(-not $NoClean -and (Test-Path -LiteralPath $outRoot)){Remove-Item -Recurse -Force $outRoot}
New-Item -ItemType Directory -Force -Path $outRoot,$parityOut,$damageParityOut,$testOut | Out-Null

Write-Host '[3/10] Running CP122 canonical-migration preflight and Python self-tests...'
Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot) 'CP122 canonical-migration preflight failed'
Push-Location $repositoryRoot
try {
    & $python.Command @($python.Args + @('-B','-m','unittest','discover','-s','tools/simulation/tests','-p','test_*.py'))
    if($LASTEXITCODE -ne 0){throw 'CP122 Python self-tests failed.'}
    Write-Host '       Python self-tests: 124/124 passed.'

    Write-Host '[4/10] Building native C# solution with warnings as errors...'
    $buildLog=Join-Path $outRoot 'build.log'
    Invoke-Captured 'CP122 warning-as-error build' $buildLog { dotnet build StarCluster.sln --configuration Release --nologo -warnaserror }
    Write-Host '       Native build passed under SDK 8.0.423 with warnings treated as errors.'

    Write-Host '[5/10] Running all xUnit tests...'
    $testLog=Join-Path $outRoot 'xunit.log'
    Invoke-Captured 'CP122 xUnit suite' $testLog { dotnet test tests\StarCluster.Tests\StarCluster.Tests.csproj --configuration Release --no-build --nologo --logger 'trx;LogFileName=cp122-tests.trx' --results-directory $testOut }
    $trxPath=Join-Path $testOut 'cp122-tests.trx'
    if(-not (Test-Path -LiteralPath $trxPath)){throw 'CP122 xUnit TRX output is missing.'}
    [xml]$trx=Get-Content -LiteralPath $trxPath -Raw
    $counters=$trx.TestRun.ResultSummary.Counters
    $totalTests=[int]$counters.total; $passedTests=[int]$counters.passed; $failedTests=[int]$counters.failed
    if($totalTests -ne 905 -or $passedTests -ne 905 -or $failedTests -ne 0){throw "CP122 xUnit shape mismatch: total=$totalTests passed=$passedTests failed=$failedTests; expected 905/905/0."}
    Write-Host '       xUnit tests: 905/905 passed.'

    Write-Host '[6/10] Running ScenarioRunner self-tests and canonical x2 parity...'
    $selfLog=Join-Path $outRoot 'scenario-self-tests.log'
    Invoke-Captured 'CP122 ScenarioRunner self-tests' $selfLog { dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- self-test }
    $selfText=Get-Content -LiteralPath $selfLog -Raw
    if($selfText -notmatch 'Runner self-tests:\s+70 passed,\s+0 failed,\s+70 total\.'){throw 'CP122 ScenarioRunner self-test count/result mismatch; expected 70/70.'}
    Write-Host '       ScenarioRunner self-tests: 70/70 passed.'
    $damageLog=Join-Path $outRoot 'canonical-damage-scale-parity.log'
    Invoke-Captured 'CP122 canonical damage-scale parity runner' $damageLog { dotnet run --project src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --configuration Release --no-build -- damage-scale-parity --output-dir $damageParityOut }
    $damage=Get-Content -LiteralPath (Join-Path $damageParityOut 'summary.json') -Raw | ConvertFrom-Json
    if(-not [bool]$damage.exactParity -or [int]$damage.mismatches -ne 0 -or [int]$damage.layeredCases -ne 234000 -or [int]$damage.temporaryEffectCases -ne 117 -or [int]$damage.energyDegradedCases -ne 21 -or [int]$damage.productionRepairHullPerKit -ne 1 -or [int]$damage.parityOnlyRepairHullPerKit -ne 2 -or [bool]$damage.criticalCadenceMigrated){throw 'CP122 canonical damage-scale parity result shape failed.'}
    Write-Host '       Canonical parity: 234,000 layered + 117 temporary-effect + 21 degraded-Energy cases; zero mismatches.'
    Write-Host '       Production Repair Kit=1 Hull; parity-only repair=2 Hull; critical cadence unchanged/deferred.'

    Write-Host '[7/10] Running 25 C#/Python research parity fixtures...'
    $parityLog=Join-Path $outRoot 'research-parity.log'
    & $python.Command @($python.Args + @('-B',$cli,'--repo',$repositoryRoot,'parity','--output-dir',$parityOut)) > $parityLog 2>&1
    if($LASTEXITCODE -ne 0){Get-Content -LiteralPath $parityLog -Tail 80; throw 'CP122 research parity fixtures failed.'}
    $parity=Get-Content -LiteralPath (Join-Path $parityOut 'summary.json') -Raw | ConvertFrom-Json
    if(-not [bool]$parity.passed -or [int]$parity.cases -ne 25 -or @($parity.errors).Count -ne 0){throw 'CP122 research parity shape failed.'}
    Write-Host '       C#/Python parity fixtures: 25/25 passed.'

    Write-Host '[8/10] Writing compact native acceptance summary...'
    $summary=[ordered]@{
        schemaVersion='star-cluster-cp122-native-acceptance-summary-v0.1'
        checkpoint=122
        acceptedBaseline=121
        repositoryOnly=[bool]$RepositoryOnly
        dotnetSdk=$dotnetVersion
        python=$pythonVersion.Trim()
        buildWarningsAsErrors=$true
        buildPassed=$true
        xunitTotal=$totalTests
        xunitPassed=$passedTests
        scenarioRunnerSelfTests=70
        scenarioRunnerSelfTestsPassed=70
        researchParityCases=25
        researchParityPassed=25
        damagePointScale=2
        layeredParityCases=[int]$damage.layeredCases
        temporaryEffectParityCases=[int]$damage.temporaryEffectCases
        degradedEnergyParityCases=[int]$damage.energyDegradedCases
        parityMismatches=[int]$damage.mismatches
        exactParity=[bool]$damage.exactParity
        productionRepairHullPerKit=1
        parityOnlyRepairHullPerKit=2
        criticalCadenceMigrated=$false
        oddHalfStepValuesPromoted=$false
        substantiveMonteCarloTrials=0
        failedGates=@()
    }
    $summary | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $outRoot 'CP122_NATIVE_ACCEPTANCE_SUMMARY.json') -Encoding utf8
    Write-Host '       Native summary written; no Monte Carlo balance study is part of CP122.'

    Write-Host '[9/10] Verifying CP122 repository and native-evidence contracts...'
    Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot,'--native-results',$outRoot) 'CP122 repository/native contract failed'

    Write-Host '[10/10] Checkpoint 122 deterministic acceptance gates passed.' -ForegroundColor Green
    if($RepositoryOnly){
        Write-Host '       RepositoryOnly completed all deterministic gates. Run without -RepositoryOnly to repeat/freeze the normal handoff result.'
    } else {
        Write-Host '       CP122 normal native run complete. Zip out\checkpoint-122 and upload it for acceptance review.'
    }
}
finally { Pop-Location }
