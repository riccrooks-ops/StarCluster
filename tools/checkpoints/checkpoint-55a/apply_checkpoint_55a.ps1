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
$architectureCheck = Join-Path $PSScriptRoot 'test_technology_architecture.ps1'
$staticPreflight = Join-Path $PSScriptRoot 'static_preflight_checkpoint_55a.py'
$harness = Join-Path $repositoryRoot 'tools\calibration\run_calibration_checkpoint.ps1'
$definition = Join-Path $repositoryRoot 'tools\calibration\checkpoints\checkpoint-55a.json'

& $architectureCheck
& python $staticPreflight --root $repositoryRoot
& $harness -CheckpointDefinition $definition -Trials $Trials -Jobs $Jobs -RepositoryOnly:$RepositoryOnly -NoClean:$NoClean
