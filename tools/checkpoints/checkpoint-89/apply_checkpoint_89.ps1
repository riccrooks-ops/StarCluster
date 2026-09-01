[CmdletBinding()]
param(
    [int]$Trials = 10000,
    [int]$Jobs = 24,
    [switch]$RepositoryOnly,
    [switch]$DeepCalibration,
    [switch]$NoClean
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$dependencyGuard = Join-Path $repositoryRoot 'tools\checkpoints\Test-NativeAcceptanceDependencies.ps1'
$contractCheck = Join-Path $repositoryRoot 'tools\checkpoints\checkpoint-89\test_checkpoint_89_contract.ps1'
$harness = Join-Path $repositoryRoot 'tools\calibration\run_calibration_checkpoint.ps1'
$definitionName = if ($DeepCalibration) { 'checkpoint-89-deep-calibration.json' } else { 'checkpoint-89.json' }
$definition = Join-Path $repositoryRoot ('tools\calibration\checkpoints\' + $definitionName)
$normalDefinition = 'tools/calibration/checkpoints/checkpoint-89.json'
$deepDefinition = 'tools/calibration/checkpoints/checkpoint-89-deep-calibration.json'
$guardedPowerShellPaths = @(
    'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
    'tools/checkpoints/checkpoint-89/apply_checkpoint_89.ps1',
    'tools/checkpoints/checkpoint-89/test_checkpoint_89_contract.ps1',
    'tools/calibration/run_calibration_checkpoint.ps1'
)
$guardedDefinitionPaths = @($normalDefinition, $deepDefinition)

Write-Host '[1/4] Checking native-acceptance dependency contracts...'
& $dependencyGuard -RepositoryRoot $repositoryRoot -PowerShellPaths $guardedPowerShellPaths -CheckpointDefinitionPaths $guardedDefinitionPaths

Write-Host '[2/4] Normalizing stale active checkpoint artifacts...'
foreach ($file in @(Get-ChildItem -LiteralPath $repositoryRoot -File -Filter '*.txt')) {
    if ($file.Name -match '^CHECKPOINT_(?!89(?:_|$)).*_SHA256SUMS\.txt$' -or
        $file.Name -match '^Checkpoint_(?!89(?:_|$)).*_Readme\.txt$' -or
        $file.Name -match '^checkpoint-(?!89(?:-|$)).*-static-preflight\.txt$') {
        Remove-Item -LiteralPath $file.FullName -Force
    }
}

$validationRoot = Join-Path $repositoryRoot 'docs\validation'
$validationArchive = Join-Path $validationRoot 'archive'
if (-not (Test-Path -LiteralPath $validationArchive -PathType Container)) { New-Item -ItemType Directory -Path $validationArchive | Out-Null }
foreach ($file in @(Get-ChildItem -LiteralPath $validationRoot -File -Filter 'Checkpoint_*.md')) {
    if ($file.Name -ne 'Checkpoint_89_Documentation_Repository_Consolidation_And_EW_Multiplicity.md') {
        Move-Item -LiteralPath $file.FullName -Destination (Join-Path $validationArchive $file.Name) -Force
    }
}

$docsRoot = Join-Path $repositoryRoot 'docs'
$conceptArchive = Join-Path $docsRoot 'archive\concepts'
if (-not (Test-Path -LiteralPath $conceptArchive -PathType Container)) { New-Item -ItemType Directory -Path $conceptArchive -Force | Out-Null }
foreach ($concept in @(Get-ChildItem -LiteralPath $docsRoot -File -Filter 'Star_Cluster_Game_Concept_v*.docx')) {
    if ($concept.Name -ne 'Star_Cluster_Game_Concept_v0.6z.docx') {
        Move-Item -LiteralPath $concept.FullName -Destination (Join-Path $conceptArchive $concept.Name) -Force
    }
}

Write-Host '[3/4] Verifying Checkpoint 89 documentation, authority, and EW multiplicity contracts...'
& $contractCheck

Write-Host '[4/4] Running checkpoint harness...'
& $harness -CheckpointDefinition $definition -Trials $Trials -Jobs $Jobs -RepositoryOnly:$RepositoryOnly -NoClean:$NoClean
