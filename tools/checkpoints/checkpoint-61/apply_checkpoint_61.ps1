[CmdletBinding()]
param(
    [int]$Trials = 0,
    [int]$Jobs = 0,
    [switch]$RepositoryOnly,
    [switch]$NoClean,
    [switch]$DeepCalibration
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$contractCheck = Join-Path $PSScriptRoot 'test_checkpoint_61_contract.ps1'
$harness = Join-Path $repositoryRoot 'tools\calibration\run_calibration_checkpoint.ps1'
$definitionName = if ($DeepCalibration) { 'checkpoint-61-deep-calibration.json' } else { 'checkpoint-61.json' }
$definition = Join-Path $repositoryRoot (Join-Path 'tools\calibration\checkpoints' $definitionName)

& $contractCheck
& $harness -CheckpointDefinition $definition -Trials $Trials -Jobs $Jobs -RepositoryOnly:$RepositoryOnly -NoClean:$NoClean
