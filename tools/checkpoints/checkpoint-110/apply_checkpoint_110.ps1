[CmdletBinding()]
param(
    [switch]$RepositoryOnly,
    [switch]$NoClean
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$contract = Join-Path $PSScriptRoot 'test_checkpoint_110_contract.py'
$research = Join-Path $repositoryRoot 'tools\simulation\run_starcluster_research.py'
$study = 'docs/archive/testing/pre-cp165-active/power_reactor_calibration_study_v0_1.json'
$outRoot = Join-Path $repositoryRoot 'out\checkpoint-110'

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
    throw 'CP110 requires CPython 3.13 for deterministic checkpoint validation and research simulation.'
}

Write-Host '[1/6] Resolving Python research/validation runtime and production boundary...'
$python = Get-Cpython313Command
$versionArgs = @($python.Args) + @('--version')
$version = & $python.Command @versionArgs 2>&1 | Out-String
Write-Host ("       {0}" -f $version.Trim())
Write-Host '       Python is permitted for research/simulation/testing; shipped game/runtime remains C# / Godot.'

Write-Host '[2/6] Normalizing local CP110 output artifacts...'
if (-not $NoClean -and (Test-Path $outRoot)) { Remove-Item -Recurse -Force $outRoot }
if (-not (Test-Path $outRoot)) { New-Item -ItemType Directory -Path $outRoot | Out-Null }

Write-Host '[3/6] Verifying Checkpoint 110 repository, provenance, and calibration contracts...'
$contractArgs = @($python.Args) + @('-B', $contract, '--repo', $repositoryRoot)
& $python.Command @contractArgs
if ($LASTEXITCODE -ne 0) { throw "Checkpoint 110 deterministic Python contract failed with exit code $LASTEXITCODE." }

if ($RepositoryOnly) {
    Write-Host '[4/6] RepositoryOnly requested; skipping Python research self-tests.'
    Write-Host '[5/6] RepositoryOnly requested; skipping parity fixtures.'
    Write-Host '[6/6] RepositoryOnly requested; skipping substantive Power/Reactor calibration rerun.'
    Write-Host ''
    Write-Host 'Checkpoint 110 deterministic repository/calibration-evidence validation completed successfully.'
    exit 0
}

Write-Host '[4/6] Running Python research self-tests...'
$selfArgs = @($python.Args) + @('-B', $research, '--repo', $repositoryRoot, 'self-test', '--output-dir', 'out/checkpoint-110/self-test')
& $python.Command @selfArgs
if ($LASTEXITCODE -ne 0) { throw "Checkpoint 110 Python self-tests failed with exit code $LASTEXITCODE." }

Write-Host '[5/6] Running deterministic C#/Python parity fixtures...'
$parityArgs = @($python.Args) + @('-B', $research, '--repo', $repositoryRoot, 'parity', '--output-dir', 'out/checkpoint-110/parity')
& $python.Command @parityArgs
if ($LASTEXITCODE -ne 0) { throw "Checkpoint 110 parity fixtures failed with exit code $LASTEXITCODE." }

Write-Host '[6/6] Running substantive Power/Reactor calibration study...'
$calibrationArgs = @($python.Args) + @('-B', $research, '--repo', $repositoryRoot, 'power-calibrate', $study, '--output-dir', 'out/checkpoint-110/power-calibration')
& $python.Command @calibrationArgs
if ($LASTEXITCODE -ne 0) { throw "Checkpoint 110 Power/Reactor calibration failed with exit code $LASTEXITCODE." }

$runtimeArgs = @($python.Args) + @('-B', $contract, '--repo', $repositoryRoot, '--runtime-output', 'out/checkpoint-110/power-calibration')
& $python.Command @runtimeArgs
if ($LASTEXITCODE -ne 0) { throw "Checkpoint 110 runtime-evidence verification failed with exit code $LASTEXITCODE." }

Write-Host ''
Write-Host 'Checkpoint 110 Power/Reactor first-pass calibration completed successfully.'
Write-Host '       Candidate Reactor values remain unpromoted; production game/runtime remains C# / Godot.'
