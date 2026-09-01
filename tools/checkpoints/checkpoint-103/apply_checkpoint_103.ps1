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
$contract = Join-Path $PSScriptRoot 'test_checkpoint_103_contract.ps1'
$harness = Join-Path $repositoryRoot 'tools\calibration\run_calibration_checkpoint.ps1'
$definition = Join-Path $repositoryRoot 'tools\calibration\checkpoints\checkpoint-103.json'
$deepDefinition = Join-Path $repositoryRoot 'tools\calibration\checkpoints\checkpoint-103-deep-calibration.json'
$researchWrapper = Join-Path $repositoryRoot 'tools\simulation\Invoke-StarClusterResearch.ps1'

function Assert-Cp103PowerShell51ArrayCompatibility {
    param([string[]]$Paths)
    foreach ($path in $Paths) {
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "CP103 PowerShell precheck cannot find '$path'." }
        $text = [IO.File]::ReadAllText($path)
        foreach ($match in [regex]::Matches($text, '(?m)^\s*\$[A-Za-z_][A-Za-z0-9_]*\s*=\s*Option-Ids\b')) {
            throw "CP103 PowerShell 5.1 array-shape precheck found an unmaterialized Option-Ids assignment in '$path'. Wrap helper output in @(...)."
        }
    }
}


function Assert-Cp103PythonWrapperNativeCompatibility {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "CP103 Python-wrapper precheck cannot find '$Path'." }
    $text = [IO.File]::ReadAllText($Path)
    if (-not $text.Contains('--version')) {
        throw 'CP103 Python wrapper must probe interpreter versions with --version.'
    }
    if ([regex]::IsMatch($text, '(?m)^\s*\$probe\s*=.*-c')) {
        throw 'CP103 Python wrapper must not use Python -c for the Windows PowerShell 5.1 bootstrap probe.'
    }
    if (-not $text.Contains('Windows PowerShell 5.1') -or -not $text.Contains('[regex]::Match')) {
        throw 'CP103 Python wrapper must retain the reviewed Windows PowerShell 5.1-safe version parser.'
    }
}

function Assert-Cp103DefinitionBindings {
    param([string[]]$DefinitionPaths)
    $expectedPowerShellPaths = @(
        'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
        'tools/checkpoints/checkpoint-103/apply_checkpoint_103.ps1',
        'tools/checkpoints/checkpoint-103/test_checkpoint_103_contract.ps1',
        'tools/simulation/Invoke-StarClusterResearch.ps1',
        'tools/calibration/run_calibration_checkpoint.ps1'
    )
    $expectedDefinitionPaths = @(
        'tools/calibration/checkpoints/checkpoint-103.json',
        'tools/calibration/checkpoints/checkpoint-103-deep-calibration.json'
    )
    foreach ($path in $DefinitionPaths) {
        $document = Get-Content -LiteralPath $path -Raw | ConvertFrom-Json
        $precheck = $document.nativeDependencyPrecheck
        if ($null -eq $precheck -or -not [bool]$precheck.required) { throw "CP103 definition '$path' must declare a required nativeDependencyPrecheck." }
        $actualPowerShellPaths = @($precheck.powerShellPaths | ForEach-Object { [string]$_ })
        $actualDefinitionPaths = @($precheck.checkpointDefinitionPaths | ForEach-Object { [string]$_ })
        $allowed = @($precheck.allowedInterpreters | ForEach-Object { [string]$_ })
        if ($actualPowerShellPaths.Count -ne $expectedPowerShellPaths.Count) { throw "CP103 definition '$path' nativeDependencyPrecheck has the wrong PowerShell-path count." }
        for ($i=0; $i -lt $expectedPowerShellPaths.Count; $i++) { if ($actualPowerShellPaths[$i] -ne $expectedPowerShellPaths[$i]) { throw "CP103 definition '$path' must inspect '$($expectedPowerShellPaths[$i])'." } }
        if ($actualDefinitionPaths.Count -ne $expectedDefinitionPaths.Count) { throw "CP103 definition '$path' nativeDependencyPrecheck has the wrong checkpoint-definition count." }
        for ($i=0; $i -lt $expectedDefinitionPaths.Count; $i++) { if ($actualDefinitionPaths[$i] -ne $expectedDefinitionPaths[$i]) { throw "CP103 definition '$path' must inspect '$($expectedDefinitionPaths[$i])'." } }
        if ($allowed.Count -ne 3 -or $allowed[0] -ne 'python' -or $allowed[1] -ne 'python3' -or $allowed[2] -ne 'py') { throw "CP103 definition '$path' must explicitly allow the Python research interpreter names." }
    }
}

Write-Host '[1/4] Checking native-acceptance dependency contracts...'
Assert-Cp103PowerShell51ArrayCompatibility -Paths @($MyInvocation.MyCommand.Path, $contract)
Assert-Cp103PythonWrapperNativeCompatibility -Path $researchWrapper
Assert-Cp103DefinitionBindings -DefinitionPaths @($definition, $deepDefinition)
& $guard -RepositoryRoot $repositoryRoot -PowerShellPaths @(
    'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
    'tools/checkpoints/checkpoint-103/apply_checkpoint_103.ps1',
    'tools/checkpoints/checkpoint-103/test_checkpoint_103_contract.ps1',
    'tools/simulation/Invoke-StarClusterResearch.ps1',
    'tools/calibration/run_calibration_checkpoint.ps1'
) -CheckpointDefinitionPaths @(
    'tools/calibration/checkpoints/checkpoint-103.json',
    'tools/calibration/checkpoints/checkpoint-103-deep-calibration.json'
) -AllowedInterpreters @('python','python3','py')

Write-Host '[2/4] Normalizing stale active checkpoint artifacts...'
$outputRoot = Join-Path $repositoryRoot 'out\checkpoint-103'
if (-not $NoClean) { Remove-Item -LiteralPath $outputRoot -Recurse -Force -ErrorAction SilentlyContinue }

Write-Host '[3/4] Verifying Checkpoint 103 Python-research integration/permutation contracts...'
& $contract -RepositoryRoot $repositoryRoot

Write-Host '[4/4] Running checkpoint harness...'
& $harness -CheckpointDefinition $definition -Trials $Trials -Jobs $Jobs -RepositoryOnly:$RepositoryOnly -NoClean:$NoClean
