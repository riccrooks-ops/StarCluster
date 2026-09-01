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
$contract = Join-Path $PSScriptRoot 'test_checkpoint_102_contract.ps1'
$harness = Join-Path $repositoryRoot 'tools\calibration\run_calibration_checkpoint.ps1'
$definition = Join-Path $repositoryRoot 'tools\calibration\checkpoints\checkpoint-102.json'

function Assert-Cp102PowerShell51TypeCompatibility {
    param([string[]]$Paths)
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
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "CP102 PowerShell 5.1 type precheck cannot find '$path'." }
        $text = [IO.File]::ReadAllText($path)
        foreach ($match in [regex]::Matches($text, '\[(?<type>[A-Za-z_][A-Za-z0-9_.+]*)\]')) {
            $typeName = [string]$match.Groups['type'].Value
            if (-not $allowedTypes.ContainsKey($typeName)) { throw "CP102 PowerShell 5.1 type precheck found unreviewed token '[$typeName]' in '$path'." }
        }
    }
}

Write-Host '[1/4] Checking native-acceptance dependency contracts...'
Assert-Cp102PowerShell51TypeCompatibility -Paths @($MyInvocation.MyCommand.Path, $contract)
& $guard -RepositoryRoot $repositoryRoot -PowerShellPaths @(
    'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
    'tools/checkpoints/checkpoint-102/apply_checkpoint_102.ps1',
    'tools/checkpoints/checkpoint-102/test_checkpoint_102_contract.ps1',
    'tools/calibration/run_calibration_checkpoint.ps1'
) -CheckpointDefinitionPaths @(
    'tools/calibration/checkpoints/checkpoint-102.json',
    'tools/calibration/checkpoints/checkpoint-102-deep-calibration.json'
)

Write-Host '[2/4] Normalizing stale active checkpoint artifacts...'
$outputRoot = Join-Path $repositoryRoot 'out\checkpoint-102'
if (-not $NoClean) { Remove-Item -LiteralPath $outputRoot -Recurse -Force -ErrorAction SilentlyContinue }
# RepositoryOnly writes acceptance summaries under out/checkpoint-102. The repository contract explicitly classifies out/* as generated so a subsequent full run in the same extraction remains valid.

Write-Host '[3/4] Verifying Checkpoint 102 TL3 executable-consumer contracts...'
& $contract -RepositoryRoot $repositoryRoot

Write-Host '[4/4] Running checkpoint harness...'
& $harness -CheckpointDefinition $definition -Trials $Trials -Jobs $Jobs -RepositoryOnly:$RepositoryOnly -NoClean:$NoClean
