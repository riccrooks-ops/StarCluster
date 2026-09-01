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
$harness = Join-Path $repositoryRoot 'tools\calibration\run_calibration_checkpoint.ps1'
$definition = Join-Path $repositoryRoot 'tools\calibration\checkpoints\checkpoint-45.json'
$preflight = Join-Path $PSScriptRoot 'static_preflight_checkpoint_45.py'

$python = Get-Command -Name 'python' -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
if ($null -eq $python) {
    $python = Get-Command -Name 'py' -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
}
if ($null -eq $python) {
    throw 'Python is required for the Checkpoint 45 repository preflight.'
}

& $python.Path $preflight --root $repositoryRoot
if ($LASTEXITCODE -ne 0) {
    throw "Checkpoint 45 repository preflight failed with exit code $LASTEXITCODE."
}

& $harness -CheckpointDefinition $definition -Trials $Trials -Jobs $Jobs -RepositoryOnly:$RepositoryOnly -NoClean:$NoClean
