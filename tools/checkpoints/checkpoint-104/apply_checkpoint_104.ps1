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
$contract = Join-Path $PSScriptRoot 'test_checkpoint_104_contract.ps1'
$harness = Join-Path $repositoryRoot 'tools\calibration\run_calibration_checkpoint.ps1'
$definition = Join-Path $repositoryRoot 'tools\calibration\checkpoints\checkpoint-104.json'
$deepDefinition = Join-Path $repositoryRoot 'tools\calibration\checkpoints\checkpoint-104-deep-calibration.json'
$researchWrapper = Join-Path $repositoryRoot 'tools\simulation\Invoke-StarClusterResearch.ps1'

function Assert-Cp104DefinitionBindings {
    param([string[]]$DefinitionPaths)
    $expectedPowerShellPaths = @(
        'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
        'tools/checkpoints/checkpoint-104/apply_checkpoint_104.ps1',
        'tools/checkpoints/checkpoint-104/test_checkpoint_104_contract.ps1',
        'tools/simulation/Invoke-StarClusterResearch.ps1',
        'tools/calibration/run_calibration_checkpoint.ps1'
    )
    $expectedDefinitionPaths = @(
        'tools/calibration/checkpoints/checkpoint-104.json',
        'tools/calibration/checkpoints/checkpoint-104-deep-calibration.json'
    )
    foreach ($path in $DefinitionPaths) {
        $document = Get-Content -LiteralPath $path -Raw | ConvertFrom-Json
        $precheck = $document.nativeDependencyPrecheck
        if ($null -eq $precheck -or -not [bool]$precheck.required) { throw "CP104 definition '$path' must declare a required nativeDependencyPrecheck." }
        $actualPowerShellPaths = @($precheck.powerShellPaths | ForEach-Object { [string]$_ })
        $actualDefinitionPaths = @($precheck.checkpointDefinitionPaths | ForEach-Object { [string]$_ })
        $allowed = @($precheck.allowedInterpreters | ForEach-Object { [string]$_ })
        if ($actualPowerShellPaths.Count -ne $expectedPowerShellPaths.Count) { throw "CP104 definition '$path' has the wrong PowerShell-path count." }
        for ($i = 0; $i -lt $expectedPowerShellPaths.Count; $i++) {
            if ($actualPowerShellPaths[$i] -ne $expectedPowerShellPaths[$i]) { throw "CP104 definition '$path' must inspect '$($expectedPowerShellPaths[$i])'." }
        }
        if ($actualDefinitionPaths.Count -ne $expectedDefinitionPaths.Count) { throw "CP104 definition '$path' has the wrong checkpoint-definition count." }
        for ($i = 0; $i -lt $expectedDefinitionPaths.Count; $i++) {
            if ($actualDefinitionPaths[$i] -ne $expectedDefinitionPaths[$i]) { throw "CP104 definition '$path' must inspect '$($expectedDefinitionPaths[$i])'." }
        }
        if ($allowed.Count -ne 3 -or $allowed[0] -ne 'python' -or $allowed[1] -ne 'python3' -or $allowed[2] -ne 'py') {
            throw "CP104 definition '$path' must explicitly allow the Python research interpreter names."
        }
    }
}

Write-Host '[1/4] Checking native-acceptance dependency contracts...'
Assert-Cp104DefinitionBindings -DefinitionPaths @($definition, $deepDefinition)
& $guard -RepositoryRoot $repositoryRoot -PowerShellPaths @(
    'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
    'tools/checkpoints/checkpoint-104/apply_checkpoint_104.ps1',
    'tools/checkpoints/checkpoint-104/test_checkpoint_104_contract.ps1',
    'tools/simulation/Invoke-StarClusterResearch.ps1',
    'tools/calibration/run_calibration_checkpoint.ps1'
) -CheckpointDefinitionPaths @(
    'tools/calibration/checkpoints/checkpoint-104.json',
    'tools/calibration/checkpoints/checkpoint-104-deep-calibration.json'
) -AllowedInterpreters @('python','python3','py')

Write-Host '[2/4] Normalizing stale active checkpoint artifacts...'
$outputRoot = Join-Path $repositoryRoot 'out\checkpoint-104'
if (-not $NoClean) { Remove-Item -LiteralPath $outputRoot -Recurse -Force -ErrorAction SilentlyContinue }

Write-Host '[3/4] Verifying Checkpoint 104 bounded diagnostic-closure contracts...'
& $contract -RepositoryRoot $repositoryRoot

Write-Host '[4/4] Running checkpoint harness...'
& $harness -CheckpointDefinition $definition -Trials $Trials -Jobs $Jobs -RepositoryOnly:$RepositoryOnly -NoClean:$NoClean
