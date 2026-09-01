[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repositoryRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
Push-Location $repositoryRoot

function Assert-FileContains {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string[]]$Patterns,
        [Parameter(Mandatory = $true)][string]$Description
    )

    if (-not (Test-Path $Path)) {
        throw "$Description file $Path was not found. Extract the complete Checkpoint 22a package into the repository root."
    }

    foreach ($pattern in $Patterns) {
        if (-not (Select-String -Path $Path -SimpleMatch $pattern -Quiet)) {
            throw "$Description is missing required content: $pattern"
        }
    }
}

function Assert-FileNotContains {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string[]]$Patterns,
        [Parameter(Mandatory = $true)][string]$Description
    )

    if (-not (Test-Path $Path)) {
        throw "$Description file $Path was not found."
    }

    foreach ($pattern in $Patterns) {
        if (Select-String -Path $Path -SimpleMatch $pattern -Quiet) {
            throw "$Description still contains forbidden content: $pattern"
        }
    }
}

try {
    Write-Host '[1/4] Verifying the partially applied Checkpoint 22 baseline...'
    foreach ($requiredFile in @(
        '.\StarCluster.sln',
        '.\src\StarCluster.ScenarioRunner\ScenarioExecutionMetrics.cs',
        '.\src\StarCluster.ScenarioRunner\ScenarioRunnerSelfTests.cs',
        '.\src\StarCluster.ScenarioRunner\ScenarioDocumentSerialization.cs',
        '.\src\StarCluster.Core\Combat\Tracking\SensorMode.cs',
        '.\tools\checkpoints\checkpoint-22\apply_checkpoint_22.ps1',
        '.\docs\checkpoints\Checkpoint_22a_Source_Symbol_Resolution_Hotfix.md')) {
        if (-not (Test-Path $requiredFile)) {
            throw "Required Checkpoint 22a file $requiredFile was not found."
        }
    }

    Write-Host '[2/4] Verifying corrected namespace and serializer symbols...'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\ScenarioExecutionMetrics.cs' @(
        'StarCluster.Core.Combat.Tracking.SensorMode.Active') 'Checkpoint 22a SensorMode namespace repair'
    Assert-FileNotContains '.\src\StarCluster.ScenarioRunner\ScenarioExecutionMetrics.cs' @(
        'StarCluster.Core.Combat.SensorMode.Active') 'Checkpoint 22a stale SensorMode namespace guard'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\ScenarioRunnerSelfTests.cs' @(
        'ScenarioDocumentSerialization.CompactWriteOptions') 'Checkpoint 22a compact serializer repair'
    Assert-FileNotContains '.\src\StarCluster.ScenarioRunner\ScenarioRunnerSelfTests.cs' @(
        'ScenarioDocumentSerialization.WriteOptions') 'Checkpoint 22a stale serializer option guard'
    Assert-FileContains '.\src\StarCluster.ScenarioRunner\ScenarioDocumentSerialization.cs' @(
        'CompactWriteOptions',
        'IndentedWriteOptions') 'Checkpoint 22a serializer declarations'
    Assert-FileContains '.\src\StarCluster.Core\Combat\Tracking\SensorMode.cs' @(
        'namespace StarCluster.Core.Combat.Tracking;',
        'public enum SensorMode') 'Checkpoint 22a SensorMode declaration'

    Write-Host '[3/4] Running the complete corrected Checkpoint 22 acceptance sequence...'
    & '.\tools\checkpoints\checkpoint-22\apply_checkpoint_22.ps1'

    Write-Host '[4/4] Checkpoint 22a source-symbol hotfix completed successfully.'
}
finally {
    Pop-Location
}
