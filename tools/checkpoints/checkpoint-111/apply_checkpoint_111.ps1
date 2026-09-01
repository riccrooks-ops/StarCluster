[CmdletBinding()]
param(
    [switch]$RepositoryOnly,
    [switch]$NoClean
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$contract = Join-Path $PSScriptRoot 'test_checkpoint_111_contract.py'
$research = Join-Path $repositoryRoot 'tools\simulation\run_starcluster_research.py'
$study = 'docs/archive/testing/pre-cp165-active/same_tl_build_ecology_instrumentation_study_v0_1.json'
$outRoot = Join-Path $repositoryRoot 'out\checkpoint-111'

function Get-Cpython313Command {
    $candidates = @(
        @{ Command = 'py'; Args = @('-3.13') },
        @{ Command = 'python'; Args = @() },
        @{ Command = 'python3'; Args = @() }
    )
    foreach ($candidate in $candidates) {
        $cmd = Get-Command $candidate.Command -ErrorAction SilentlyContinue
        if ($null -eq $cmd) { continue }
        $probeArgs = @($candidate.Args) + @('--version')
        $versionText = & $candidate.Command @probeArgs 2>&1 | Out-String
        if ($LASTEXITCODE -ne 0) { continue }
        if ($versionText -match 'Python\s+3\.13(?:\.|\s|$)') { return $candidate }
    }
    throw 'CP111 requires CPython 3.13 for deterministic checkpoint validation and research simulation.'
}

Write-Host '[1/7] Resolving Python research/validation runtime and production boundary...'
$python = Get-Cpython313Command
$versionArgs = @($python.Args) + @('--version')
$version = & $python.Command @versionArgs 2>&1 | Out-String
Write-Host ("       {0}" -f $version.Trim())
Write-Host '       Python is permitted for research/simulation/testing; shipped game/runtime remains C# / Godot.'

Write-Host '[2/7] Normalizing local CP111 output artifacts...'
if (-not $NoClean -and (Test-Path $outRoot)) { Remove-Item -Recurse -Force $outRoot }
if (-not (Test-Path $outRoot)) { New-Item -ItemType Directory -Path $outRoot | Out-Null }

Write-Host '[3/7] Verifying Checkpoint 111 repository, provenance, ecology, and instrumentation contracts...'
$contractArgs = @($python.Args) + @('-B', $contract, '--repo', $repositoryRoot)
& $python.Command @contractArgs
if ($LASTEXITCODE -ne 0) { throw "Checkpoint 111 deterministic Python contract failed with exit code $LASTEXITCODE." }

if ($RepositoryOnly) {
    Write-Host '[4/7] RepositoryOnly requested; skipping Python research self-tests.'
    Write-Host '[5/7] RepositoryOnly requested; skipping parity fixtures.'
    Write-Host '[6/7] RepositoryOnly requested; skipping one-trial full ecology smoke.'
    Write-Host '[7/7] RepositoryOnly requested; skipping substantive same-TL ecology rerun.'
    Write-Host ''
    Write-Host 'Checkpoint 111 deterministic repository/instrumentation-evidence validation completed successfully.'
    exit 0
}

Write-Host '[4/7] Running Python research self-tests...'
$selfArgs = @($python.Args) + @('-B', $research, '--repo', $repositoryRoot, 'self-test', '--output-dir', 'out/checkpoint-111/self-test')
& $python.Command @selfArgs
if ($LASTEXITCODE -ne 0) { throw "Checkpoint 111 Python self-tests failed with exit code $LASTEXITCODE." }

Write-Host '[5/7] Running deterministic C#/Python parity fixtures...'
$parityArgs = @($python.Args) + @('-B', $research, '--repo', $repositoryRoot, 'parity', '--output-dir', 'out/checkpoint-111/parity')
& $python.Command @parityArgs
if ($LASTEXITCODE -ne 0) { throw "Checkpoint 111 parity fixtures failed with exit code $LASTEXITCODE." }

Write-Host '[6/7] Running one-trial full-variant ecology smoke...'
$smokeArgs = @($python.Args) + @('-B', $research, '--repo', $repositoryRoot, 'ecology', $study, '--output-dir', 'out/checkpoint-111/smoke', '--trials', '1', '--jobs', '1')
& $python.Command @smokeArgs
if ($LASTEXITCODE -ne 0) { throw "Checkpoint 111 one-trial ecology smoke failed with exit code $LASTEXITCODE." }

Write-Host '[7/7] Running substantive same-TL build ecology (1,188 variants x 1,000 trials)...'
$jobs = [Math]::Max(1, [Environment]::ProcessorCount)
Write-Host ("       Worker processes: {0}" -f $jobs)
$ecologyArgs = @($python.Args) + @('-B', $research, '--repo', $repositoryRoot, 'ecology', $study, '--output-dir', 'out/checkpoint-111/same-tl-ecology', '--trials', '1000', '--jobs', $jobs)
& $python.Command @ecologyArgs
if ($LASTEXITCODE -ne 0) { throw "Checkpoint 111 substantive same-TL ecology failed with exit code $LASTEXITCODE." }

$runtimeArgs = @($python.Args) + @('-B', $contract, '--repo', $repositoryRoot, '--runtime-output', 'out/checkpoint-111/same-tl-ecology')
& $python.Command @runtimeArgs
if ($LASTEXITCODE -ne 0) { throw "Checkpoint 111 runtime-evidence verification failed with exit code $LASTEXITCODE." }

Write-Host ''
Write-Host 'Checkpoint 111 same-TL build ecology instrumentation validation completed successfully.'
Write-Host '       Same-TL outcomes remain diagnostic; no CP109/CP110 candidate value is promoted.'
Write-Host '       Production game/runtime remains C# / Godot; CP111 Python damage scope is layered defense plus Hull only.'
