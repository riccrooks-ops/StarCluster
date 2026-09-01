# Shared Checkpoint 33 semantic operation registry.
# This file is dot-sourced by the apply, build, and release-validation scripts.
# Operations are registered under stable semantic keys so implementation helper
# names can change without leaving stale direct call sites throughout the harness.

if ($null -eq $script:CheckpointOperationRegistry) {
    $script:CheckpointOperationRegistry = [ordered]@{}
}

function Register-CheckpointOperation {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][scriptblock]$Operation
    )

    $script:CheckpointOperationRegistry[$Name] = $Operation
}

function Assert-CheckpointOperationRegistry {
    param([Parameter(Mandatory = $true)][string[]]$RequiredNames)

    foreach ($name in $RequiredNames) {
        if (-not $script:CheckpointOperationRegistry.Contains($name)) {
            throw "Checkpoint operation registry does not contain required key $name."
        }
        if ($script:CheckpointOperationRegistry[$name] -isnot [scriptblock]) {
            throw "Checkpoint operation registry key $name is not executable."
        }
    }
}

function Invoke-CheckpointOperation {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [object[]]$Arguments = @()
    )

    Assert-CheckpointOperationRegistry -RequiredNames @($Name)
    $operation = $script:CheckpointOperationRegistry[$Name]
    return & $operation @Arguments
}

function Test-CheckpointOperationRegistry {
    $smokeTestName = '__CheckpointRegistrySmokeTest'
    Register-CheckpointOperation -Name $smokeTestName -Operation {
        param([string]$Value)
        return "registry:$Value"
    }
    try {
        $result = Invoke-CheckpointOperation -Name $smokeTestName -Arguments @('ok')
        if ($result -ne 'registry:ok') {
            throw "Checkpoint operation registry smoke test returned $result."
        }
    }
    finally {
        [void]$script:CheckpointOperationRegistry.Remove($smokeTestName)
    }
    Write-Host '       Checkpoint operation registry self-test: passed.'
}
