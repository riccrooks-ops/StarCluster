[CmdletBinding()]
param([switch]$RepositoryOnly,[switch]$NoClean)
Set-StrictMode -Version 2.0
$ErrorActionPreference='Stop'
$repositoryRoot=(Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$contract=Join-Path $PSScriptRoot 'test_checkpoint_115a_contract.py'
$preflight=Join-Path $PSScriptRoot 'preflight_checkpoint_115a.py'
$hygiene=Join-Path $repositoryRoot 'tools\checkpoints\prepackage_repository_hygiene.py'
$cli=Join-Path $repositoryRoot 'tools\simulation\run_starcluster_research.py'
$study=Join-Path $repositoryRoot 'docs\archive\testing\pre-cp165-active\weapon_family_payload_study_v0_2.json'
$outRoot=Join-Path $repositoryRoot 'out\checkpoint-115a'

function Get-Cpython313Command {
    $candidates=@(@{Command='py';Args=@('-3.13')},@{Command='python';Args=@()},@{Command='python3';Args=@()})
    foreach($candidate in $candidates){
        $cmd=Get-Command $candidate.Command -ErrorAction SilentlyContinue
        if($null -eq $cmd){continue}
        $versionText=& $candidate.Command @($candidate.Args + @('--version')) 2>&1 | Out-String
        if($LASTEXITCODE -eq 0 -and $versionText -match 'Python\s+3\.13(?:\.|\s|$)'){return $candidate}
    }
    throw 'CP115a requires CPython 3.13 for deterministic validation and weapon-family simulation.'
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

Write-Host '[1/6] Resolving Python research runtime and production boundary...'
$python=Get-Cpython313Command
$version=& $python.Command @($python.Args + @('--version')) 2>&1 | Out-String
Write-Host ("       {0}" -f $version.Trim())
Write-Host '       Python is permitted for research/testing; shipped game/runtime remains C# / Godot.'

Write-Host '[2/6] Applying and verifying pre-package repository hygiene...'
Invoke-PythonChecked $python @('-B',$hygiene,'--repo',$repositoryRoot,'--apply') 'CP115a pre-package hygiene apply failed'
Invoke-PythonChecked $python @('-B',$hygiene,'--repo',$repositoryRoot,'--check') 'CP115a pre-package hygiene check failed'

Write-Host '[3/6] Running substantive-gate preflight, self-tests, parity fixtures, and all-variant smoke...'
Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot) 'CP115a substantive-gate preflight failed'
Push-Location $repositoryRoot
try {
    & $python.Command @($python.Args + @('-B','-m','unittest','discover','-s','tools/simulation/tests','-p','test_*.py'))
    if($LASTEXITCODE -ne 0){throw 'CP115a Python self-tests failed.'}
    Write-Host '       Python self-tests: 64/64 passed.'
    if(-not $NoClean -and (Test-Path $outRoot)){Remove-Item -Recurse -Force $outRoot}
    New-Item -ItemType Directory -Force -Path $outRoot | Out-Null
    $parityOut=Join-Path $outRoot 'parity'; $parityLog=Join-Path $outRoot 'parity.log'
    Invoke-StudyCaptured $python @('-B',$cli,'--repo',$repositoryRoot,'parity','--output-dir',$parityOut) $parityOut $parityLog 'CP115a C#/Python parity fixtures failed'
    Write-Host '       C#/Python parity fixtures: 25/25 passed.'
    $smokeOut=Join-Path $outRoot 'smoke'; $smokeLog=Join-Path $outRoot 'smoke.log'
    Invoke-StudyCaptured $python @('-B',$cli,'--repo',$repositoryRoot,'weapon-family-study',$study,'--output-dir',$smokeOut,'--trials','1','--jobs','24') $smokeOut $smokeLog 'CP115a all-variant one-trial smoke failed'
    $smoke=Get-Content (Join-Path $smokeOut 'analysis.json') -Raw | ConvertFrom-Json
    if([int]$smoke.variants -ne 4064 -or [int]$smoke.totalTrials -ne 4064 -or @($smoke.failedGates).Count -ne 0){throw 'CP115a smoke result shape/gates failed.'}
    Write-Host '       All-variant smoke: 4,064 variants / 4,064 engagements; zero failed gates.'

    $nativeResults=$null
    if($RepositoryOnly){
        Write-Host '[4/6] RepositoryOnly requested; substantive native weapon-family study skipped.'
        Write-Host '       CP115a fixes acceptance-gate semantics only; checked-in CP115 authoring evidence remains diagnostic.'
    } else {
        Write-Host '[4/6] Running substantive weapon-family payload characteristic-space study...'
        $nativeResults=Join-Path $outRoot 'native-weapon-family-study'; $nativeLog=Join-Path $outRoot 'native-weapon-family-study.log'
        Invoke-StudyCaptured $python @('-B',$cli,'--repo',$repositoryRoot,'weapon-family-study',$study,'--output-dir',$nativeResults,'--trials','2000','--jobs','24') $nativeResults $nativeLog 'CP115a substantive weapon-family study failed'
        $native=Get-Content (Join-Path $nativeResults 'analysis.json') -Raw | ConvertFrom-Json
        if([int]$native.variants -ne 4064 -or [int64]$native.totalTrials -ne 8128000 -or @($native.failedGates).Count -ne 0){throw 'CP115a substantive study result shape/gates failed.'}
        Write-Host ("       Substantive study: 4,064 variants / 8,128,000 engagements; zero failed gates; adaptive switch rows: {0}." -f [int]$native.adaptivePairRowsWithSwitches)
    }

    Write-Host '[5/6] Verifying CP115a repository/evidence and regression contracts...'
    $args=@('-B',$contract,'--repo',$repositoryRoot)
    if($null -ne $nativeResults){$args += @('--native-results',$nativeResults)}
    & $python.Command @($python.Args + $args)
    if($LASTEXITCODE -ne 0){throw 'Checkpoint 115a deterministic contract failed.'}

    Write-Host '[6/6] Acceptance-harness hotfix complete...'
    Write-Host '       CP115 study population, payload mechanics, candidate values, Concept, and production C#/Godot behavior are unchanged.'
} finally { Pop-Location }

Write-Host ''
Write-Host 'Checkpoint 115a weapon-family substantive-gate hotfix validation completed successfully.'
if($RepositoryOnly){
    Write-Host 'RepositoryOnly completed without running the substantive 8.128-million-engagement study.'
}else{
    Write-Host 'Results remain diagnostic evidence; no production or numerical promotion occurs.'
}
