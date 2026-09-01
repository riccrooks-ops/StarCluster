[CmdletBinding()]
param(
    [int]$Trials = 0,
    [int]$Jobs = 0,
    [switch]$RepositoryOnly,
    [switch]$NoClean
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$contract = Join-Path $PSScriptRoot 'test_checkpoint_109_contract.py'

if ($Trials -ne 0 -or $Jobs -ne 0) {
    Write-Host '       CP109 builds candidate numerical design data only; Trials/Jobs are ignored.'
}

function Get-Cpython313Command {
    $candidates = @(
        @{ Command = 'py'; Args = @('-3.13') },
        @{ Command = 'python'; Args = @() },
        @{ Command = 'python3'; Args = @() }
    )
    foreach ($candidate in $candidates) {
        $cmd = Get-Command $candidate.Command -ErrorAction SilentlyContinue
        if ($null -eq $cmd) { continue }
        $probeArgs = @($candidate.Args) + @('--version')
        $versionText = & $candidate.Command @probeArgs 2>&1 | Out-String
        if ($LASTEXITCODE -ne 0) { continue }
        if ($versionText -match 'Python\s+3\.13(?:\.|\s|$)') { return $candidate }
    }
    throw 'CP109 requires CPython 3.13 for deterministic checkpoint validation.'
}

Write-Host '[1/4] Resolving deterministic Python validation runtime and production boundary...'
$python = Get-Cpython313Command
$versionArgs = @($python.Args) + @('--version')
$version = & $python.Command @versionArgs 2>&1 | Out-String
Write-Host ("       {0}" -f $version.Trim())
Write-Host '       Python is permitted for testing/checkpoint validation; shipped game/runtime remains C# / Godot.'

Write-Host '[2/4] Normalizing stale active checkpoint artifacts...'
Write-Host '[3/4] Verifying Checkpoint 109 whole-ladder numerical-design contracts...'
$contractArgs = @($python.Args) + @('-B', $contract, '--repo', $repositoryRoot)
& $python.Command @contractArgs
if ($LASTEXITCODE -ne 0) { throw "Checkpoint 109 Python contract failed with exit code $LASTEXITCODE." }

Write-Host '[4/4] Numerical-design checkpoint complete...'
if ($RepositoryOnly) {
    Write-Host '       RepositoryOnly requested. Deterministic whole-ladder matrix validation completed successfully.'
} else {
    Write-Host '       CP109 intentionally runs no .NET build, research simulation, Monte Carlo, or calibration harness.'
    Write-Host '       Candidate values are not promoted into the C# / Godot production runtime.'
}
Write-Host ''
Write-Host 'Checkpoint 109 whole-ladder candidate numerical technology matrix validation completed successfully.'
