[CmdletBinding()]
param(
    [ValidateSet('Debug','Release')][string]$Configuration = 'Debug',
    [switch]$NoClean
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

function Invoke-NativeCommand {
    param(
        [Parameter(Mandatory = $true)][string]$Executable,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][string]$Description
    )

    $exitCode = -1
    $previousPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        & $Executable @Arguments
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousPreference
    }
    if ($exitCode -ne 0) { throw "$Description failed with exit code $exitCode." }
}

function Get-DotNetSdkVersion {
    $exitCode = -1
    $output = @()
    $previousPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $output = @(& dotnet --version 2>&1)
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousPreference
    }
    if ($exitCode -ne 0) { throw "dotnet --version failed with exit code $exitCode." }
    return (($output | ForEach-Object { [string]$_ }) -join "`n").Trim()
}

$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Push-Location $repositoryRoot
try {
    $sdkVersion = Get-DotNetSdkVersion
    Write-Host "       SDK: $sdkVersion"
    if ($sdkVersion -ne '8.0.423') { throw "Expected .NET SDK 8.0.423, found $sdkVersion." }

    if (-not $NoClean) {
        Invoke-NativeCommand -Executable 'dotnet' -Arguments @('clean', '.\StarCluster.sln', '--configuration', $Configuration, '--nologo') -Description 'Full-solution clean'
    }

    Invoke-NativeCommand -Executable 'dotnet' -Arguments @('build', '.\StarCluster.sln', '--configuration', $Configuration, '--nologo', '-warnaserror') -Description 'Full-solution build'
    Invoke-NativeCommand -Executable 'dotnet' -Arguments @('test', '.\tests\StarCluster.Tests\StarCluster.Tests.csproj', '--configuration', $Configuration, '--no-build', '--nologo') -Description 'Full-solution test run'

    Write-Host 'Full Godot/C# integration validation completed successfully.'
}
finally {
    Pop-Location
}
