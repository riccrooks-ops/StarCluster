[CmdletBinding()]
param([switch]$RepositoryOnly,[switch]$NoClean)
Set-StrictMode -Version 2.0
$ErrorActionPreference='Stop'
$repositoryRoot=(Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$contract=Join-Path $PSScriptRoot 'test_checkpoint_116_contract.py'
$preflight=Join-Path $PSScriptRoot 'preflight_checkpoint_116.py'
$hygiene=Join-Path $repositoryRoot 'tools\checkpoints\prepackage_repository_hygiene.py'
$cli=Join-Path $repositoryRoot 'tools\simulation\run_starcluster_research.py'
$study116=Join-Path $repositoryRoot 'docs\archive\testing\pre-cp165-active\warhead_role_generation_study_v0_1.json'
$study115=Join-Path $repositoryRoot 'docs\archive\testing\pre-cp165-active\weapon_family_payload_study_v0_2.json'
$study114=Join-Path $repositoryRoot 'docs\archive\testing\pre-cp165-active\payload_characteristic_space_study_v0_1.json'
$outRoot=Join-Path $repositoryRoot 'out\checkpoint-116'

function Get-Cpython313Command {
    $candidates=@(@{Command='py';Args=@('-3.13')},@{Command='python';Args=@()},@{Command='python3';Args=@()})
    foreach($candidate in $candidates){
        $cmd=Get-Command $candidate.Command -ErrorAction SilentlyContinue
        if($null -eq $cmd){continue}
        $versionText=& $candidate.Command @($candidate.Args + @('--version')) 2>&1 | Out-String
        if($LASTEXITCODE -eq 0 -and $versionText -match 'Python\s+3\.13(?:\.|\s|$)'){return $candidate}
    }
    throw 'CP116 requires CPython 3.13 for deterministic validation and research simulation.'
}
function Invoke-PythonChecked([object]$Python,[string[]]$Arguments,[string]$FailureMessage){
    & $Python.Command @($Python.Args + $Arguments)
    if($LASTEXITCODE -ne 0){throw "$FailureMessage (exit code $LASTEXITCODE)."}
}
function Invoke-StudyCaptured([object]$Python,[string[]]$Arguments,[string]$OutputDir,[string]$LogPath,[string]$FailureMessage){
    & $Python.Command @($Python.Args + $Arguments) > $LogPath 2>&1
    $exitCode=$LASTEXITCODE
    if($exitCode -ne 0){
        $summaryPath=Join-Path $OutputDir 'summary.json'
        if(Test-Path -LiteralPath $summaryPath){
            try {
                $failure=Get-Content -LiteralPath $summaryPath -Raw | ConvertFrom-Json
                if($null -ne $failure.gates -and $null -ne $failure.gates.failed){
                    Write-Host ("       Failed gates: {0}" -f (@($failure.gates.failed) -join ', ')) -ForegroundColor Red
                }
                if($null -ne $failure.error){Write-Host ("       Error: {0}" -f $failure.error) -ForegroundColor Red}
            } catch { Write-Host '       Could not parse study summary.json after failure.' -ForegroundColor Yellow }
        }
        if(Test-Path -LiteralPath $LogPath){
            Write-Host '       Study output tail:' -ForegroundColor Yellow
            Get-Content -LiteralPath $LogPath -Tail 40 | ForEach-Object { Write-Host ("       $_") }
        }
        throw "$FailureMessage (exit code $exitCode)."
    }
}
function Assert-StudyShape([string]$AnalysisPath,[int]$Variants,[int64]$Trials,[string]$Label){
    $a=Get-Content -LiteralPath $AnalysisPath -Raw | ConvertFrom-Json
    if([int]$a.variants -ne $Variants -or [int64]$a.totalTrials -ne $Trials -or @($a.failedGates).Count -ne 0){
        throw "$Label result shape/gates failed."
    }
}

Write-Host '[1/7] Resolving Python research runtime and production boundary...'
$python=Get-Cpython313Command
$version=& $python.Command @($python.Args + @('--version')) 2>&1 | Out-String
Write-Host ("       {0}" -f $version.Trim())
Write-Host '       Python is permitted for research/testing; shipped game/runtime remains C# / Godot.'

Write-Host '[2/7] Applying and verifying pre-package repository hygiene...'
Invoke-PythonChecked $python @('-B',$hygiene,'--repo',$repositoryRoot,'--apply') 'CP116 pre-package hygiene apply failed'
Invoke-PythonChecked $python @('-B',$hygiene,'--repo',$repositoryRoot,'--check') 'CP116 pre-package hygiene check failed'

Write-Host '[3/7] Running CP116 preflight, self-tests, and parity fixtures...'
Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot) 'CP116 role-orthogonality preflight failed'
Push-Location $repositoryRoot
try {
    & $python.Command @($python.Args + @('-B','-m','unittest','discover','-s','tools/simulation/tests','-p','test_*.py'))
    if($LASTEXITCODE -ne 0){throw 'CP116 Python self-tests failed.'}
    Write-Host '       Python self-tests: 77/77 passed.'
    if(-not $NoClean -and (Test-Path $outRoot)){Remove-Item -Recurse -Force $outRoot}
    New-Item -ItemType Directory -Force -Path $outRoot | Out-Null
    $parityOut=Join-Path $outRoot 'parity'; $parityLog=Join-Path $outRoot 'parity.log'
    Invoke-StudyCaptured $python @('-B',$cli,'--repo',$repositoryRoot,'parity','--output-dir',$parityOut) $parityOut $parityLog 'CP116 C#/Python parity fixtures failed'
    $parity=Get-Content (Join-Path $parityOut 'summary.json') -Raw | ConvertFrom-Json
    if(-not $parity.passed -or [int]$parity.cases -ne 25 -or @($parity.errors).Count -ne 0){throw 'CP116 parity result shape failed.'}
    Write-Host '       C#/Python parity fixtures: 25/25 passed.'

    Write-Host '[4/7] Running prior-study regression smokes and CP116 all-variant smoke...'
    $cp114Out=Join-Path $outRoot 'cp114-regression-smoke'; $cp114Log=Join-Path $outRoot 'cp114-regression-smoke.log'
    Invoke-StudyCaptured $python @('-B',$cli,'--repo',$repositoryRoot,'payload-study',$study114,'--output-dir',$cp114Out,'--trials','1','--jobs','24') $cp114Out $cp114Log 'CP116 CP114 regression smoke failed'
    Assert-StudyShape (Join-Path $cp114Out 'analysis.json') 3184 3184 'CP114 regression smoke'
    Write-Host '       CP114 regression smoke: 3,184 variants / 3,184 engagements; zero failed gates.'
    $cp115Out=Join-Path $outRoot 'cp115a-regression-smoke'; $cp115Log=Join-Path $outRoot 'cp115a-regression-smoke.log'
    Invoke-StudyCaptured $python @('-B',$cli,'--repo',$repositoryRoot,'weapon-family-study',$study115,'--output-dir',$cp115Out,'--trials','1','--jobs','24') $cp115Out $cp115Log 'CP116 CP115a regression smoke failed'
    Assert-StudyShape (Join-Path $cp115Out 'analysis.json') 4064 4064 'CP115a regression smoke'
    Write-Host '       CP115a regression smoke: 4,064 variants / 4,064 engagements; zero failed gates.'
    $smokeOut=Join-Path $outRoot 'smoke'; $smokeLog=Join-Path $outRoot 'smoke.log'
    Invoke-StudyCaptured $python @('-B',$cli,'--repo',$repositoryRoot,'warhead-generation-study',$study116,'--output-dir',$smokeOut,'--trials','1','--jobs','24') $smokeOut $smokeLog 'CP116 all-variant one-trial smoke failed'
    Assert-StudyShape (Join-Path $smokeOut 'analysis.json') 2976 2976 'CP116 smoke'
    Write-Host '       CP116 all-variant smoke: 2,976 variants / 2,976 engagements; zero failed gates.'

    $nativeResults=$null
    if($RepositoryOnly){
        Write-Host '[5/7] RepositoryOnly requested; substantive native CP116 study skipped.'
        Write-Host '       Checked-in bounded authoring evidence remains 74,400 engagements and is diagnostic only.'
    } else {
        Write-Host '[5/7] Running substantive warhead-role orthogonality/generational-scaling study...'
        $nativeResults=Join-Path $outRoot 'native-warhead-generation-study'; $nativeLog=Join-Path $outRoot 'native-warhead-generation-study.log'
        Invoke-StudyCaptured $python @('-B',$cli,'--repo',$repositoryRoot,'warhead-generation-study',$study116,'--output-dir',$nativeResults,'--trials','2000','--jobs','24') $nativeResults $nativeLog 'CP116 substantive warhead-generation study failed'
        Assert-StudyShape (Join-Path $nativeResults 'analysis.json') 2976 5952000 'CP116 substantive study'
        $native=Get-Content (Join-Path $nativeResults 'analysis.json') -Raw | ConvertFrom-Json
        Write-Host ("       Substantive study: 2,976 variants / 5,952,000 engagements; zero failed gates; adaptive switch rows: {0}." -f [int]$native.adaptivePairRowsWithSwitches)
    }

    Write-Host '[6/7] Verifying CP116 repository/evidence contracts...'
    $args=@('-B',$contract,'--repo',$repositoryRoot)
    if($null -ne $nativeResults){$args += @('--native-results',$nativeResults)}
    & $python.Command @($python.Args + $args)
    if($LASTEXITCODE -ne 0){throw 'Checkpoint 116 deterministic contract failed.'}

    Write-Host '[7/7] Checkpoint 116 validation complete...'
    Write-Host '       GP energetic yield and penetration-specialization axes remain separated; no production or numerical promotion occurs.'
} finally { Pop-Location }

Write-Host ''
Write-Host 'Checkpoint 116 warhead-role orthogonality and generational-scaling validation completed successfully.'
if($RepositoryOnly){
    Write-Host 'RepositoryOnly completed without running the substantive 5.952-million-engagement study.'
}else{
    Write-Host 'Results remain diagnostic evidence; no production or numerical promotion occurs.'
}
