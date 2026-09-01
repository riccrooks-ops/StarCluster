[CmdletBinding()]
param([int]$Trials=0,[int]$Jobs=0,[switch]$RepositoryOnly,[switch]$NoClean)
Set-StrictMode -Version 2.0
$ErrorActionPreference='Stop'
$repositoryRoot=(Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$guard=Join-Path $repositoryRoot 'tools\checkpoints\Test-NativeAcceptanceDependencies.ps1'
$contract=Join-Path $PSScriptRoot 'test_checkpoint_107_contract.ps1'
if($Trials -ne 0 -or $Jobs -ne 0){ Write-Host '       CP107 is architecture-only; Trials/Jobs are ignored.' }
Write-Host '[1/4] Checking native-acceptance dependency contracts...'
& $guard -RepositoryRoot $repositoryRoot -PowerShellPaths @('tools/checkpoints/Test-NativeAcceptanceDependencies.ps1','tools/checkpoints/checkpoint-107/apply_checkpoint_107.ps1','tools/checkpoints/checkpoint-107/test_checkpoint_107_contract.ps1') -CheckpointDefinitionPaths @('tools/checkpoints/checkpoint-107/checkpoint_107_architecture_definition.json')
Write-Host '[2/4] Normalizing stale active checkpoint artifacts...'
Write-Host '[3/4] Verifying Checkpoint 107 architecture and table contracts...'
& $contract -RepositoryRoot $repositoryRoot
Write-Host '[4/4] Architecture-only checkpoint complete...'
if($RepositoryOnly){ Write-Host '       RepositoryOnly requested. Deterministic architecture validation completed successfully.' } else { Write-Host '       CP107 intentionally runs no .NET build, Python research engine, Monte Carlo, or calibration harness.' }
Write-Host ''
Write-Host 'Checkpoint 107 provisional technology-table validation completed successfully.'
