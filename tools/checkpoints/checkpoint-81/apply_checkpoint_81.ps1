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
$contractCheck = Join-Path $repositoryRoot 'tools\checkpoints\checkpoint-81\test_checkpoint_81_contract.ps1'
$harness = Join-Path $repositoryRoot 'tools\calibration\run_calibration_checkpoint.ps1'
$definitionName = if ($DeepCalibration) { 'checkpoint-81-deep-calibration.json' } else { 'checkpoint-81.json' }
$definition = Join-Path $repositoryRoot ('tools\calibration\checkpoints\' + $definitionName)
$normalDefinition = 'tools/calibration/checkpoints/checkpoint-81.json'
$deepDefinition = 'tools/calibration/checkpoints/checkpoint-81-deep-calibration.json'
$guardedPowerShellPaths = @(
    'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
    'tools/checkpoints/checkpoint-81/apply_checkpoint_81.ps1',
    'tools/checkpoints/checkpoint-81/test_checkpoint_81_contract.ps1',
    'tools/calibration/run_calibration_checkpoint.ps1'
)
$guardedDefinitionPaths = @($normalDefinition, $deepDefinition)

Write-Host '[1/4] Checking native-acceptance dependency contracts...'
& $dependencyGuard -RepositoryRoot $repositoryRoot -PowerShellPaths $guardedPowerShellPaths -CheckpointDefinitionPaths $guardedDefinitionPaths

Write-Host '[2/4] Normalizing stale active checkpoint artifacts...'
$staleRootPatterns = @(
    '^CHECKPOINT_(?!81(?:_|$)).*_SHA256SUMS\.txt$',
    '^Checkpoint_(?!81(?:_|$)).*_Readme\.txt$',
    '^checkpoint-(?!81(?:-|$)).*-static-preflight\.txt$'
)
foreach ($file in @(Get-ChildItem -LiteralPath $repositoryRoot -File -Filter '*.txt')) {
    foreach ($pattern in $staleRootPatterns) {
        if ($file.Name -match $pattern) {
            Remove-Item -LiteralPath $file.FullName -Force
            break
        }
    }
}

$validationRoot = Join-Path $repositoryRoot 'docs\validation'
if (Test-Path -LiteralPath $validationRoot -PathType Container) {
    $validationArchive = Join-Path $validationRoot 'archive'
    if (-not (Test-Path -LiteralPath $validationArchive -PathType Container)) {
        New-Item -ItemType Directory -Path $validationArchive | Out-Null
    }
    foreach ($file in @(Get-ChildItem -LiteralPath $validationRoot -File -Filter 'Checkpoint_*.md')) {
        if ($file.Name -ne 'Checkpoint_81_TL2_Tactical_Computer_EW_Integration_Permutation_Suite.md') {
            $archivedPath = Join-Path $validationArchive $file.Name
            if (Test-Path -LiteralPath $archivedPath -PathType Leaf) {
                Remove-Item -LiteralPath $archivedPath -Force
            }
            Move-Item -LiteralPath $file.FullName -Destination $archivedPath -Force
        }
    }
}

$docsRoot = Join-Path $repositoryRoot 'docs'
$conceptArchive = Join-Path $docsRoot 'archive'
if (-not (Test-Path -LiteralPath $conceptArchive -PathType Container)) {
    New-Item -ItemType Directory -Path $conceptArchive | Out-Null
}
foreach ($concept in @(Get-ChildItem -LiteralPath $docsRoot -File -Filter 'Star_Cluster_Game_Concept_v*.docx')) {
    if ($concept.Name -ne 'Star_Cluster_Game_Concept_v0.6s.docx') {
        $archivedConcept = Join-Path $conceptArchive $concept.Name
        if (Test-Path -LiteralPath $archivedConcept -PathType Leaf) {
            Remove-Item -LiteralPath $archivedConcept -Force
        }
        Move-Item -LiteralPath $concept.FullName -Destination $archivedConcept -Force
    }
}

Write-Host '[3/4] Verifying Checkpoint 81 Tactical Computer/EW integration permutation contracts...'
& $contractCheck

Write-Host '[4/4] Running checkpoint harness...'
& $harness -CheckpointDefinition $definition -Trials $Trials -Jobs $Jobs -RepositoryOnly:$RepositoryOnly -NoClean:$NoClean
