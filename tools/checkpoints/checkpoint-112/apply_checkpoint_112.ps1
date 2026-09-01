[CmdletBinding()]
param([switch]$RepositoryOnly,[switch]$NoClean)
Set-StrictMode -Version 2.0
$ErrorActionPreference='Stop'
$repositoryRoot=(Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$contract=Join-Path $PSScriptRoot 'test_checkpoint_112_contract.py'
$research=Join-Path $repositoryRoot 'tools\simulation\run_starcluster_research.py'
$study='docs/archive/testing/pre-cp165-active/build_neighbor_ablation_study_v0_1.json'
$outRoot=Join-Path $repositoryRoot 'out\checkpoint-112'
function Get-Cpython313Command {
    $candidates=@(@{Command='py';Args=@('-3.13')},@{Command='python';Args=@()},@{Command='python3';Args=@()})
    foreach($candidate in $candidates){
        $cmd=Get-Command $candidate.Command -ErrorAction SilentlyContinue
        if($null -eq $cmd){continue}
        $versionText=& $candidate.Command @($candidate.Args + @('--version')) 2>&1 | Out-String
        if($LASTEXITCODE -eq 0 -and $versionText -match 'Python\s+3\.13(?:\.|\s|$)'){return $candidate}
    }
    throw 'CP112 requires CPython 3.13 for research simulation and checkpoint validation.'
}
Write-Host '[1/8] Resolving Python research/validation runtime and production boundary...'
$python=Get-Cpython313Command
$version=& $python.Command @($python.Args + @('--version')) 2>&1 | Out-String
Write-Host ("       {0}" -f $version.Trim())
Write-Host '       Python is permitted for research/simulation/testing; shipped game/runtime remains C# / Godot.'
Write-Host '[2/8] Normalizing local CP112 output artifacts...'
if(-not $NoClean -and (Test-Path $outRoot)){Remove-Item -Recurse -Force $outRoot}
if(-not (Test-Path $outRoot)){New-Item -ItemType Directory -Path $outRoot | Out-Null}
Write-Host '[3/8] Verifying Checkpoint 112 repository, provenance, and causal-study contracts...'
& $python.Command @($python.Args + @('-B',$contract,'--repo',$repositoryRoot))
if($LASTEXITCODE -ne 0){throw "Checkpoint 112 deterministic Python contract failed with exit code $LASTEXITCODE."}
if($RepositoryOnly){
    Write-Host '[4/8] RepositoryOnly requested; skipping Python research self-tests.'
    Write-Host '[5/8] RepositoryOnly requested; skipping parity fixtures.'
    Write-Host '[6/8] RepositoryOnly requested; skipping all-variant smoke.'
    Write-Host '[7/8] RepositoryOnly requested; skipping substantive 2.4M diagnostic workload.'
    Write-Host '[8/8] RepositoryOnly requested; native runtime evidence validation not required.'
    Write-Host ''; Write-Host 'Checkpoint 112 deterministic repository/causal-evidence validation completed successfully.'; exit 0
}
Write-Host '[4/8] Running Python research self-tests...'
& $python.Command @($python.Args + @('-B',$research,'--repo',$repositoryRoot,'self-test','--output-dir','out/checkpoint-112/self-test'))
if($LASTEXITCODE -ne 0){throw "Checkpoint 112 Python self-tests failed with exit code $LASTEXITCODE."}
Write-Host '[5/8] Running deterministic C#/Python parity fixtures...'
& $python.Command @($python.Args + @('-B',$research,'--repo',$repositoryRoot,'parity','--output-dir','out/checkpoint-112/parity'))
if($LASTEXITCODE -ne 0){throw "Checkpoint 112 parity failed with exit code $LASTEXITCODE."}
Write-Host '[6/8] Running one-trial all-variant causal-study smoke...'
& $python.Command @($python.Args + @('-B',$research,'--repo',$repositoryRoot,'neighbor-study',$study,'--output-dir','out/checkpoint-112/smoke','--trials','1','--jobs','1'))
if($LASTEXITCODE -ne 0){throw "Checkpoint 112 smoke failed with exit code $LASTEXITCODE."}
Write-Host '[7/8] Running substantive build-neighbor/ablation diagnostics (1,200 variants x 2,000 trials)...'
$jobs=[Math]::Max(1,[Environment]::ProcessorCount); Write-Host ("       Worker processes: {0}" -f $jobs)
& $python.Command @($python.Args + @('-B',$research,'--repo',$repositoryRoot,'neighbor-study',$study,'--output-dir','out/checkpoint-112/neighbor-study','--trials','2000','--jobs',$jobs))
if($LASTEXITCODE -ne 0){throw "Checkpoint 112 substantive diagnostic study failed with exit code $LASTEXITCODE."}
Write-Host '[8/8] Verifying native substantive output against CP112 contracts...'
& $python.Command @($python.Args + @('-B',$contract,'--repo',$repositoryRoot,'--runtime-output','out/checkpoint-112/neighbor-study'))
if($LASTEXITCODE -ne 0){throw "Checkpoint 112 native evidence verification failed with exit code $LASTEXITCODE."}
Write-Host ''; Write-Host 'Checkpoint 112 build-neighbor / ablation diagnostic validation completed successfully.'
Write-Host '       Outcomes remain diagnostic; no CP109/CP110 candidate value is automatically changed or promoted.'
Write-Host '       Production game/runtime remains C# / Godot; internal critical/subsystem damage remains outside this Python consumer.'
