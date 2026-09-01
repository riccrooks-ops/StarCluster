[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Command,
    [string[]]$Arguments = @()
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$runtimePath = Join-Path $PSScriptRoot 'PYTHON_RUNTIME.json'
if (-not (Test-Path -LiteralPath $runtimePath -PathType Leaf)) { throw 'Python runtime policy is missing.' }
$runtime = Get-Content -LiteralPath $runtimePath -Raw | ConvertFrom-Json
$requiredMajorMinor = [string]$runtime.majorMinor

function Resolve-Cp103Python {
    $candidates = @(
        @{ Name = 'py'; Prefix = @("-$requiredMajorMinor") },
        @{ Name = 'python'; Prefix = @() },
        @{ Name = 'python3'; Prefix = @() }
    )
    foreach ($candidate in $candidates) {
        $cmd = Get-Command -Name $candidate.Name -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($null -eq $cmd) { continue }
        # Use --version rather than Python -c for the bootstrap probe. Windows PowerShell 5.1
        # can mangle embedded quotes when marshalling native-command arguments, which can turn
        # otherwise valid Python source into a SyntaxError before the research engine starts.
        $probe = @($candidate.Prefix + @('--version'))
        $savedErrorActionPreference = $ErrorActionPreference
        try {
            # A fallback interpreter may be a broken shim that writes to stderr. Do not let that
            # abort discovery; parse its output only when the native process exits successfully.
            $ErrorActionPreference = 'Continue'
            $versionOutput = @(& $cmd.Path @probe 2>&1)
            $exitCode = $LASTEXITCODE
        } finally {
            $ErrorActionPreference = $savedErrorActionPreference
        }
        if ($exitCode -ne 0 -or $versionOutput.Count -eq 0) { continue }

        $versionText = (($versionOutput | ForEach-Object { [string]$_ }) -join ' ').Trim()
        $versionMatch = [regex]::Match($versionText, '^Python\s+(?<major>\d+)\.(?<minor>\d+)(?:\.|\s|$)')
        if ($versionMatch.Success) {
            $actualMajorMinor = '{0}.{1}' -f $versionMatch.Groups['major'].Value, $versionMatch.Groups['minor'].Value
            if ($actualMajorMinor -eq $requiredMajorMinor) {
                return @{ Path = [string]$cmd.Path; Prefix = @($candidate.Prefix); Display = $candidate.Name }
            }
        }
    }
    throw "Star Cluster CP103 research simulation requires CPython $requiredMajorMinor.x. Install Python $requiredMajorMinor and ensure either 'py -$requiredMajorMinor', 'python', or 'python3' resolves to it. No pip packages are required."
}

$python = Resolve-Cp103Python
$entry = Join-Path $PSScriptRoot 'run_starcluster_research.py'
if (-not (Test-Path -LiteralPath $entry -PathType Leaf)) { throw 'Star Cluster research Python entry point is missing.' }

$invokeArgs = New-Object System.Collections.Generic.List[string]
foreach ($p in @($python.Prefix)) { [void]$invokeArgs.Add([string]$p) }

[void]$invokeArgs.Add('-B')
[void]$invokeArgs.Add($entry)
[void]$invokeArgs.Add('--repo')
[void]$invokeArgs.Add($repositoryRoot)
[void]$invokeArgs.Add($Command)
foreach ($argument in @($Arguments)) { [void]$invokeArgs.Add([string]$argument) }

& $python.Path @invokeArgs
$exitCode = $LASTEXITCODE
if ($exitCode -ne 0) { throw "Star Cluster research command '$Command' failed with exit code $exitCode." }
