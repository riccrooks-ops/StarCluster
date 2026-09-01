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
$contract = Join-Path $PSScriptRoot 'test_checkpoint_105_contract.ps1'
$definition = Join-Path $PSScriptRoot 'checkpoint_105_architecture_definition.json'

function Assert-Cp105ArchitectureDefinition {
    param([string]$DefinitionPath)
    $document = Get-Content -LiteralPath $DefinitionPath -Raw | ConvertFrom-Json
    if ([string]$document.checkpointId -ne '105') { throw 'CP105 architecture definition must identify checkpoint 105.' }
    if ([string]$document.scope -ne 'technology_architecture_only') { throw 'CP105 scope must remain technology_architecture_only.' }
    if ([bool]$document.numericalTlTableChanged) { throw 'CP105 must not change the numerical TL table.' }
    if ([bool]$document.simulationOrCalibrationRun) { throw 'CP105 must not run simulation or calibration.' }
    if ([int]$document.declaredTrials -ne 0) { throw 'CP105 must declare zero trials.' }
    if ([bool]$document.dotnetBuildRequired -or [bool]$document.pythonRequired) { throw 'CP105 must not require .NET or Python execution.' }
    if (@($document.stages).Count -ne 0) { throw 'CP105 architecture definition must contain zero runner stages.' }
    $precheck = $document.nativeDependencyPrecheck
    if ($null -eq $precheck -or -not [bool]$precheck.required) { throw 'CP105 must declare the native dependency precheck.' }
    $expectedPowerShell = @(
        'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
        'tools/checkpoints/checkpoint-105/apply_checkpoint_105.ps1',
        'tools/checkpoints/checkpoint-105/test_checkpoint_105_contract.ps1'
    )
    $actualPowerShell = @($precheck.powerShellPaths | ForEach-Object { [string]$_ })
    if ($actualPowerShell.Count -ne $expectedPowerShell.Count) { throw 'CP105 native dependency PowerShell-path count drifted.' }
    for ($i = 0; $i -lt $expectedPowerShell.Count; $i++) {
        if ($actualPowerShell[$i] -ne $expectedPowerShell[$i]) { throw "CP105 native dependency path drifted at index $i." }
    }
    $definitionPaths = @($precheck.checkpointDefinitionPaths | ForEach-Object { [string]$_ })
    if ($definitionPaths.Count -ne 1 -or $definitionPaths[0] -ne 'tools/checkpoints/checkpoint-105/checkpoint_105_architecture_definition.json') {
        throw 'CP105 native dependency definition path drifted.'
    }
    if (@($precheck.allowedInterpreters).Count -ne 0) { throw 'CP105 architecture acceptance must allow no external interpreter.' }
}

if ($Trials -ne 0 -or $Jobs -ne 0) {
    Write-Host '       CP105 is architecture-only; Trials/Jobs arguments are ignored because no simulation is run.'
}

Write-Host '[1/4] Checking native-acceptance dependency contracts...'
Assert-Cp105ArchitectureDefinition -DefinitionPath $definition
& $guard -RepositoryRoot $repositoryRoot -PowerShellPaths @(
    'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
    'tools/checkpoints/checkpoint-105/apply_checkpoint_105.ps1',
    'tools/checkpoints/checkpoint-105/test_checkpoint_105_contract.ps1'
) -CheckpointDefinitionPaths @(
    'tools/checkpoints/checkpoint-105/checkpoint_105_architecture_definition.json'
)

Write-Host '[2/4] Normalizing stale active checkpoint artifacts...'
if (-not $NoClean) {
    Remove-Item -LiteralPath (Join-Path $repositoryRoot 'out\checkpoint-105') -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host '[3/4] Verifying Checkpoint 105 technology-family architecture contracts...'
& $contract -RepositoryRoot $repositoryRoot

Write-Host '[4/4] Architecture-only checkpoint complete...'
if ($RepositoryOnly) {
    Write-Host '       RepositoryOnly requested. CP105 has no separate build/simulation path; deterministic architecture validation completed successfully.'
} else {
    Write-Host '       CP105 intentionally runs no .NET build, Python research engine, Monte Carlo study, or calibration harness.'
}
Write-Host ''
Write-Host 'Checkpoint 105 technology architecture validation completed successfully.'
