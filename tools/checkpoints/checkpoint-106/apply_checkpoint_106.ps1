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
$contract = Join-Path $PSScriptRoot 'test_checkpoint_106_contract.ps1'
$definition = Join-Path $PSScriptRoot 'checkpoint_106_architecture_definition.json'

function Assert-Cp106ArchitectureDefinition {
    param([string]$DefinitionPath)
    $document = Get-Content -LiteralPath $DefinitionPath -Raw | ConvertFrom-Json
    if ([string]$document.checkpointId -ne '106') { throw 'CP106 architecture definition must identify checkpoint 106.' }
    if ([string]$document.acceptedBaseline -ne '105') { throw 'CP106 must identify accepted CP105 as its baseline.' }
    if ([string]$document.scope -ne 'technology_foundation_completeness_audit_only') { throw 'CP106 scope drifted.' }
    if ([bool]$document.numericalTlTableChanged -or [bool]$document.simulationOrCalibrationRun) { throw 'CP106 must remain non-numerical and non-simulation.' }
    if ([int]$document.declaredTrials -ne 0 -or @($document.stages).Count -ne 0) { throw 'CP106 must declare zero trials and stages.' }
    if ([bool]$document.dotnetBuildRequired -or [bool]$document.pythonRequired) { throw 'CP106 validation must not require .NET or Python.' }
    $precheck = $document.nativeDependencyPrecheck
    if ($null -eq $precheck -or -not [bool]$precheck.required) { throw 'CP106 must declare the native dependency precheck.' }
    $expectedPowerShell = @(
        'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
        'tools/checkpoints/checkpoint-106/apply_checkpoint_106.ps1',
        'tools/checkpoints/checkpoint-106/test_checkpoint_106_contract.ps1'
    )
    $actualPowerShell = @($precheck.powerShellPaths | ForEach-Object { [string]$_ })
    if ($actualPowerShell.Count -ne $expectedPowerShell.Count) { throw 'CP106 dependency path count drifted.' }
    for ($i = 0; $i -lt $expectedPowerShell.Count; $i++) {
        if ($actualPowerShell[$i] -ne $expectedPowerShell[$i]) { throw "CP106 dependency path drifted at index $i." }
    }
    if (@($precheck.allowedInterpreters).Count -ne 0) { throw 'CP106 acceptance must allow no external interpreter.' }
}

if ($Trials -ne 0 -or $Jobs -ne 0) {
    Write-Host '       CP106 is architecture-only; Trials/Jobs are ignored.'
}

Write-Host '[1/4] Checking native-acceptance dependency contracts...'
Assert-Cp106ArchitectureDefinition -DefinitionPath $definition
& $guard -RepositoryRoot $repositoryRoot -PowerShellPaths @(
    'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
    'tools/checkpoints/checkpoint-106/apply_checkpoint_106.ps1',
    'tools/checkpoints/checkpoint-106/test_checkpoint_106_contract.ps1'
) -CheckpointDefinitionPaths @(
    'tools/checkpoints/checkpoint-106/checkpoint_106_architecture_definition.json'
)

Write-Host '[2/4] Normalizing stale active checkpoint artifacts...'
if (-not $NoClean) {
    Remove-Item -LiteralPath (Join-Path $repositoryRoot 'out\checkpoint-106') -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host '[3/4] Verifying Checkpoint 106 architecture and coverage contracts...'
& $contract -RepositoryRoot $repositoryRoot

Write-Host '[4/4] Architecture-only checkpoint complete...'
if ($RepositoryOnly) {
    Write-Host '       RepositoryOnly requested. Deterministic architecture validation completed successfully.'
} else {
    Write-Host '       CP106 intentionally runs no .NET build, Python research engine, Monte Carlo, or calibration harness.'
}
Write-Host ''
Write-Host 'Checkpoint 106 technology-foundation validation completed successfully.'
