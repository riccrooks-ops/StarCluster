[CmdletBinding()]
param([switch]$RepositoryOnly,[switch]$NoClean)
Set-StrictMode -Version 2.0
$ErrorActionPreference='Stop'
$repositoryRoot=(Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$contract=Join-Path $PSScriptRoot 'test_checkpoint_117_contract.py'
$preflight=Join-Path $PSScriptRoot 'preflight_checkpoint_117.py'
$hygiene=Join-Path $repositoryRoot 'tools\checkpoints\prepackage_repository_hygiene.py'
$cli=Join-Path $repositoryRoot 'tools\simulation\run_starcluster_research.py'
$outRoot=Join-Path $repositoryRoot 'out\checkpoint-117'

function Get-Cpython313Command {
    $candidates=@(@{Command='py';Args=@('-3.13')},@{Command='python';Args=@()},@{Command='python3';Args=@()})
    foreach($candidate in $candidates){
        $cmd=Get-Command $candidate.Command -ErrorAction SilentlyContinue
        if($null -eq $cmd){continue}
        $versionText=& $candidate.Command @($candidate.Args + @('--version')) 2>&1 | Out-String
        if($LASTEXITCODE -eq 0 -and $versionText -match 'Python\s+3\.13(?:\.|\s|$)'){return $candidate}
    }
    throw 'CP117 requires CPython 3.13 for deterministic validation.'
}
function Invoke-PythonChecked([object]$Python,[string[]]$Arguments,[string]$FailureMessage){
    & $Python.Command @($Python.Args + $Arguments)
    if($LASTEXITCODE -ne 0){throw "$FailureMessage (exit code $LASTEXITCODE)."}
}
function Invoke-Captured([object]$Python,[string[]]$Arguments,[string]$LogPath,[string]$FailureMessage){
    & $Python.Command @($Python.Args + $Arguments) > $LogPath 2>&1
    $exitCode=$LASTEXITCODE
    if($exitCode -ne 0){
        if(Test-Path -LiteralPath $LogPath){
            Write-Host '       Output tail:' -ForegroundColor Yellow
            Get-Content -LiteralPath $LogPath -Tail 40 | ForEach-Object { Write-Host ("       $_") }
        }
        throw "$FailureMessage (exit code $exitCode)."
    }
}

Write-Host '[1/5] Resolving deterministic Python validation runtime and production boundary...'
$python=Get-Cpython313Command
$version=& $python.Command @($python.Args + @('--version')) 2>&1 | Out-String
Write-Host ("       {0}" -f $version.Trim())
Write-Host '       Python is permitted for research/testing; shipped game/runtime remains C# / Godot.'

Write-Host '[2/5] Applying and verifying pre-package repository hygiene...'
Invoke-PythonChecked $python @('-B',$hygiene,'--repo',$repositoryRoot,'--apply') 'CP117 pre-package hygiene apply failed'
Invoke-PythonChecked $python @('-B',$hygiene,'--repo',$repositoryRoot,'--check') 'CP117 pre-package hygiene check failed'

Write-Host '[3/5] Running CP117 KISS preflight, self-tests, and parity fixtures...'
Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot) 'CP117 weapon-family simplification preflight failed'
Push-Location $repositoryRoot
try {
    & $python.Command @($python.Args + @('-B','-m','unittest','discover','-s','tools/simulation/tests','-p','test_*.py'))
    if($LASTEXITCODE -ne 0){throw 'CP117 Python self-tests failed.'}
    Write-Host '       Python self-tests: 77/77 passed.'
    if(-not $NoClean -and (Test-Path $outRoot)){Remove-Item -Recurse -Force $outRoot}
    New-Item -ItemType Directory -Force -Path $outRoot | Out-Null
    $parityOut=Join-Path $outRoot 'parity'; New-Item -ItemType Directory -Force -Path $parityOut | Out-Null
    $parityLog=Join-Path $outRoot 'parity.log'
    Invoke-Captured $python @('-B',$cli,'--repo',$repositoryRoot,'parity','--output-dir',$parityOut) $parityLog 'CP117 C#/Python parity fixtures failed'
    $parity=Get-Content (Join-Path $parityOut 'summary.json') -Raw | ConvertFrom-Json
    if(-not $parity.passed -or [int]$parity.cases -ne 25 -or @($parity.errors).Count -ne 0){throw 'CP117 parity result shape failed.'}
    Write-Host '       C#/Python parity fixtures: 25/25 passed.'

    Write-Host '[4/5] Verifying Checkpoint 117 repository/design contracts...'
    Invoke-PythonChecked $python @('-B',$contract,'--repo',$repositoryRoot) 'Checkpoint 117 deterministic contract failed'

    Write-Host '[5/5] Weapon-family consolidation checkpoint complete...'
    Write-Host '       CP117 intentionally runs no substantive Monte Carlo or numerical calibration workload.'
    Write-Host '       CP109/CP110 numerical candidates and production C# / Godot runtime remain unpromoted and unchanged.'
} finally { Pop-Location }

Write-Host ''
Write-Host 'Checkpoint 117 weapon-family simplification and Swarmer architecture validation completed successfully.'
if($RepositoryOnly){
    Write-Host 'RepositoryOnly completed successfully; CP117 has no substantive study to skip.'
}else{
    Write-Host 'Normal validation completed successfully; CP117 intentionally contains zero new Monte Carlo trials.'
}
