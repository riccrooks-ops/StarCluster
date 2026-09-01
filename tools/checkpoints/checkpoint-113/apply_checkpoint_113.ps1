[CmdletBinding()]
param([switch]$RepositoryOnly,[switch]$NoClean)
Set-StrictMode -Version 2.0
$ErrorActionPreference='Stop'
$repositoryRoot=(Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$contract=Join-Path $PSScriptRoot 'test_checkpoint_113_contract.py'
function Get-Cpython313Command {
    $candidates=@(@{Command='py';Args=@('-3.13')},@{Command='python';Args=@()},@{Command='python3';Args=@()})
    foreach($candidate in $candidates){
        $cmd=Get-Command $candidate.Command -ErrorAction SilentlyContinue
        if($null -eq $cmd){continue}
        $versionText=& $candidate.Command @($candidate.Args + @('--version')) 2>&1 | Out-String
        if($LASTEXITCODE -eq 0 -and $versionText -match 'Python\s+3\.13(?:\.|\s|$)'){return $candidate}
    }
    throw 'CP113 requires CPython 3.13 for deterministic checkpoint validation.'
}
Write-Host '[1/4] Resolving deterministic Python validation runtime and production boundary...'
$python=Get-Cpython313Command
$version=& $python.Command @($python.Args + @('--version')) 2>&1 | Out-String
Write-Host ("       {0}" -f $version.Trim())
Write-Host '       Python is permitted for testing/checkpoint validation; shipped game/runtime remains C# / Godot.'
Write-Host '[2/4] Normalizing stale active checkpoint artifacts...'
# CP113 has no generated substantive output. Keep this stage for wrapper consistency.
Write-Host '[3/4] Verifying Checkpoint 113 ammunition/warhead architecture and documentation-hygiene contracts...'
& $python.Command @($python.Args + @('-B',$contract,'--repo',$repositoryRoot))
if($LASTEXITCODE -ne 0){throw "Checkpoint 113 deterministic Python contract failed with exit code $LASTEXITCODE."}
Write-Host '[4/4] Architecture/documentation checkpoint complete...'
if($RepositoryOnly){
    Write-Host '       RepositoryOnly requested. Deterministic architecture/documentation validation completed successfully.'
}else{
    Write-Host '       CP113 intentionally runs no .NET build, research simulation, Monte Carlo, or calibration harness.'
    Write-Host '       CP109/CP110 numerical candidates and production C# / Godot runtime remain unpromoted and unchanged.'
}
Write-Host ''
Write-Host 'Checkpoint 113 weapon-ammunition/warhead architecture and docs-hygiene validation completed successfully.'
