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
$contract = Join-Path $PSScriptRoot 'test_checkpoint_98_contract.ps1'
$harness = Join-Path $repositoryRoot 'tools\calibration\run_calibration_checkpoint.ps1'
$definition = Join-Path $repositoryRoot 'tools\calibration\checkpoints\checkpoint-98.json'

function Assert-Cp98PowerShell51TypeCompatibility {
    param([string[]]$Paths)

    # Windows PowerShell 5.1 resolves a narrower set of type accelerators than modern C# aliases.
    # Keep this allow-list intentionally explicit for the CP98-authored PowerShell surface so an
    # unreviewed bracketed type token fails before the checkpoint contract or long native stages run.
    $allowedTypes = @{
        'bool' = $true
        'int' = $true
        'long' = $true
        'string' = $true
        'switch' = $true
        'IO.File' = $true
        'StringComparison' = $true
        'System.Text.RegularExpressions.RegexOptions' = $true
        'math' = $true
        'pscustomobject' = $true
        'regex' = $true
    }

    foreach ($path in $Paths) {
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            throw "CP98 PowerShell 5.1 type-compatibility precheck cannot find '$path'."
        }

        $text = [IO.File]::ReadAllText($path)
        foreach ($match in [regex]::Matches($text, '\[(?<type>[A-Za-z_][A-Za-z0-9_.+]*)\]')) {
            $typeName = [string]$match.Groups['type'].Value
            if (-not $allowedTypes.ContainsKey($typeName)) {
                throw "CP98 PowerShell 5.1 type-compatibility precheck found unreviewed or unsupported type token '[$typeName]' in '$path'. Use a Windows PowerShell 5.1-compatible type name and add it to the reviewed allow-list only after verification."
            }
        }
    }
}

Write-Host '[1/4] Checking native-acceptance dependency contracts...'
Assert-Cp98PowerShell51TypeCompatibility -Paths @($MyInvocation.MyCommand.Path, $contract)
& $guard -RepositoryRoot $repositoryRoot -PowerShellPaths @(
    'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
    'tools/checkpoints/checkpoint-98/apply_checkpoint_98.ps1',
    'tools/checkpoints/checkpoint-98/test_checkpoint_98_contract.ps1',
    'tools/calibration/run_calibration_checkpoint.ps1'
) -CheckpointDefinitionPaths @(
    'tools/calibration/checkpoints/checkpoint-98.json',
    'tools/calibration/checkpoints/checkpoint-98-deep-calibration.json'
)

Write-Host '[2/4] Normalizing stale active checkpoint artifacts...'
# Current checkpoint archives historical authorities explicitly; no generated output is repository-owned.

Write-Host '[3/4] Verifying Checkpoint 98 Cross-Progression Adaptive Engage contracts...'
& $contract -RepositoryRoot $repositoryRoot

Write-Host '[4/4] Running checkpoint harness...'
& $harness -CheckpointDefinition $definition -Trials $Trials -Jobs $Jobs -RepositoryOnly:$RepositoryOnly -NoClean:$NoClean
