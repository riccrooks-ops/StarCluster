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
$contract = Join-Path $PSScriptRoot 'test_checkpoint_108_contract.py'

if ($Trials -ne 0 -or $Jobs -ne 0) {
    Write-Host '       CP108 is qualitative architecture-only; Trials/Jobs are ignored.'
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
        if ($versionText -match 'Python\s+3\.13(?:\.|\s|$)') {
            return $candidate
        }
    }
    throw 'CP108 requires CPython 3.13 for deterministic checkpoint validation. Install/enable CPython 3.13 or make it available through py -3.13, python, or python3.'
}

Write-Host '[1/4] Resolving deterministic Python validation runtime and production boundary...'
$python = Get-Cpython313Command
$versionArgs = @($python.Args) + @('--version')
$version = & $python.Command @versionArgs 2>&1 | Out-String
Write-Host ("       {0}" -f $version.Trim())
Write-Host '       Python is permitted for testing/checkpoint validation; shipped game/runtime remains C# / Godot.'

Write-Host '[2/4] Normalizing stale active checkpoint artifacts...'
Write-Host '[3/4] Verifying Checkpoint 108 qualitative technology-table contracts...'
$contractArgs = @($python.Args) + @('-B', $contract, '--repo', $repositoryRoot)
& $python.Command @contractArgs
if ($LASTEXITCODE -ne 0) { throw "Checkpoint 108 Python contract failed with exit code $LASTEXITCODE." }

Write-Host '[4/4] Qualitative architecture checkpoint complete...'
if ($RepositoryOnly) {
    Write-Host '       RepositoryOnly requested. Deterministic qualitative architecture validation completed successfully.'
}
else {
    Write-Host '       CP108 intentionally runs no .NET build, research simulation, Monte Carlo, or calibration harness.'
    Write-Host '       Python was used only for deterministic checkpoint validation; production game/runtime remains C# / Godot.'
}
Write-Host ''
Write-Host 'Checkpoint 108 qualitative technology-table validation completed successfully.'
