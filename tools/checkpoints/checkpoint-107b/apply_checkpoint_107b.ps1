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
$guard = Join-Path $repositoryRoot 'tools\checkpoints\Test-NativeAcceptanceDependencies.ps1'
$contract = Join-Path $PSScriptRoot 'test_checkpoint_107b_contract.ps1'

if ($Trials -ne 0 -or $Jobs -ne 0) {
    Write-Host '       CP107b is architecture-only; Trials/Jobs are ignored.'
}

Write-Host '[1/4] Checking native-acceptance dependency contracts...'
& $guard -RepositoryRoot $repositoryRoot -PowerShellPaths @(
    'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
    'tools/checkpoints/checkpoint-107b/apply_checkpoint_107b.ps1',
    'tools/checkpoints/checkpoint-107b/test_checkpoint_107b_contract.ps1'
) -CheckpointDefinitionPaths @(
    'tools/checkpoints/checkpoint-107b/checkpoint_107b_architecture_definition.json'
)

Write-Host '[2/4] Normalizing stale active checkpoint artifacts...'
Write-Host '[3/4] Verifying Checkpoint 107b architecture, hotfix, and table contracts...'
& $contract -RepositoryRoot $repositoryRoot

Write-Host '[4/4] Architecture-only hotfix checkpoint complete...'
if ($RepositoryOnly) {
    Write-Host '       RepositoryOnly requested. Deterministic architecture and acceptance-hotfix validation completed successfully.'
}
else {
    Write-Host '       CP107b intentionally runs no .NET build, Python research engine, Monte Carlo, or calibration harness.'
}
Write-Host ''
Write-Host 'Checkpoint 107b provisional technology-table acceptance-hotfix validation completed successfully.'
