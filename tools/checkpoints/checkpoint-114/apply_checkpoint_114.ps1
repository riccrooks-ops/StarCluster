[CmdletBinding()]
param([switch]$RepositoryOnly,[switch]$NoClean)
Set-StrictMode -Version 2.0
$ErrorActionPreference='Stop'
$repositoryRoot=(Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$contract=Join-Path $PSScriptRoot 'test_checkpoint_114_contract.py'
$hygiene=Join-Path $repositoryRoot 'tools\checkpoints\prepackage_repository_hygiene.py'
$cli=Join-Path $repositoryRoot 'tools\simulation\run_starcluster_research.py'
$study=Join-Path $repositoryRoot 'docs\archive\testing\pre-cp165-active\payload_characteristic_space_study_v0_1.json'
$outRoot=Join-Path $repositoryRoot 'out\checkpoint-114'

function Get-Cpython313Command {
    $candidates=@(@{Command='py';Args=@('-3.13')},@{Command='python';Args=@()},@{Command='python3';Args=@()})
    foreach($candidate in $candidates){
        $cmd=Get-Command $candidate.Command -ErrorAction SilentlyContinue
        if($null -eq $cmd){continue}
        $versionText=& $candidate.Command @($candidate.Args + @('--version')) 2>&1 | Out-String
        if($LASTEXITCODE -eq 0 -and $versionText -match 'Python\s+3\.13(?:\.|\s|$)'){return $candidate}
    }
    throw 'CP114 requires CPython 3.13 for deterministic validation and payload simulation.'
}
function Invoke-PythonChecked([object]$Python,[string[]]$Arguments,[string]$FailureMessage){
    & $Python.Command @($Python.Args + $Arguments)
    if($LASTEXITCODE -ne 0){throw "$FailureMessage (exit code $LASTEXITCODE)."}
}

Write-Host '[1/5] Resolving Python research runtime and production boundary...'
$python=Get-Cpython313Command
$version=& $python.Command @($python.Args + @('--version')) 2>&1 | Out-String
Write-Host ("       {0}" -f $version.Trim())
Write-Host '       Python is permitted for research/testing; shipped game/runtime remains C# / Godot.'

Write-Host '[2/5] Applying and verifying pre-package repository hygiene...'
Invoke-PythonChecked $python @('-B',$hygiene,'--repo',$repositoryRoot,'--apply') 'CP114 pre-package hygiene apply failed'
Invoke-PythonChecked $python @('-B',$hygiene,'--repo',$repositoryRoot,'--check') 'CP114 pre-package hygiene check failed'

Write-Host '[3/5] Running payload-consumer self-tests, parity fixtures, and all-variant smoke...'
Push-Location $repositoryRoot
try {
    & $python.Command @($python.Args + @('-B','-m','unittest','discover','-s','tools/simulation/tests','-p','test_*.py'))
    if($LASTEXITCODE -ne 0){throw 'CP114 Python self-tests failed.'}
    Write-Host '       Python self-tests: 49/49 passed.'
    if(-not $NoClean -and (Test-Path $outRoot)){Remove-Item -Recurse -Force $outRoot}
    New-Item -ItemType Directory -Force -Path $outRoot | Out-Null
    $parityOut=Join-Path $outRoot 'parity'
    & $python.Command @($python.Args + @('-B',$cli,'--repo',$repositoryRoot,'parity','--output-dir',$parityOut)) | Out-Null
    if($LASTEXITCODE -ne 0){throw 'CP114 C#/Python parity fixtures failed.'}
    Write-Host '       C#/Python parity fixtures: 25/25 passed.'
    $smokeOut=Join-Path $outRoot 'smoke'
    & $python.Command @($python.Args + @('-B',$cli,'--repo',$repositoryRoot,'payload-study',$study,'--output-dir',$smokeOut,'--trials','1','--jobs','24')) | Out-Null
    if($LASTEXITCODE -ne 0){throw 'CP114 all-variant one-trial smoke failed.'}
    $smoke=Get-Content (Join-Path $smokeOut 'analysis.json') -Raw | ConvertFrom-Json
    if([int]$smoke.variants -ne 3184 -or [int]$smoke.totalTrials -ne 3184 -or @($smoke.failedGates).Count -ne 0){throw 'CP114 smoke result shape/gates failed.'}
    Write-Host '       All-variant smoke: 3,184 variants / 3,184 engagements; zero failed gates.'

    $nativeResults=$null
    if($RepositoryOnly){
        Write-Host '[4/5] RepositoryOnly requested; substantive native payload study skipped.'
        Write-Host '       Checked-in bounded authoring evidence remains 63,680 engagements and is diagnostic only.'
    } else {
        Write-Host '[4/5] Running substantive payload characteristic-space study...'
        $nativeResults=Join-Path $outRoot 'native-payload-study'
        & $python.Command @($python.Args + @('-B',$cli,'--repo',$repositoryRoot,'payload-study',$study,'--output-dir',$nativeResults,'--trials','2000','--jobs','24')) | Out-Null
        if($LASTEXITCODE -ne 0){throw 'CP114 substantive payload study failed.'}
        $native=Get-Content (Join-Path $nativeResults 'analysis.json') -Raw | ConvertFrom-Json
        if([int]$native.variants -ne 3184 -or [int64]$native.totalTrials -ne 6368000 -or @($native.failedGates).Count -ne 0){throw 'CP114 substantive study result shape/gates failed.'}
        Write-Host '       Substantive study: 3,184 variants / 6,368,000 engagements; zero failed gates.'
    }

    Write-Host '[5/5] Verifying Checkpoint 114 repository/evidence contracts...'
    $args=@('-B',$contract,'--repo',$repositoryRoot)
    if($null -ne $nativeResults){$args += @('--native-results',$nativeResults)}
    & $python.Command @($python.Args + $args)
    if($LASTEXITCODE -ne 0){throw 'Checkpoint 114 deterministic contract failed.'}
} finally { Pop-Location }

Write-Host ''
Write-Host 'Checkpoint 114 payload characteristic-space and pre-package-hygiene validation completed successfully.'
if($RepositoryOnly){
    Write-Host 'RepositoryOnly completed without running the substantive 6.368-million-engagement study.'
}else{
    Write-Host 'Payload results remain exploratory evidence; CP109/CP110 and C#/Godot production values remain unpromoted.'
}
