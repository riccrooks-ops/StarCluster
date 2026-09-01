$ErrorActionPreference = "Stop"

Write-Host "[1/4] Verifying the Star Cluster repository..."
if (-not (Test-Path ".\StarCluster.sln")) {
    throw "StarCluster.sln was not found. Run this script from E:\dev\star-cluster."
}

Write-Host "[2/4] Verifying the current concept document..."
$current = ".\docs\Star_Cluster_Game_Concept_v0.3.docx"
if (-not (Test-Path $current)) {
    throw "The v0.3 concept document is missing. Extract the documentation archive into the repository root first."
}

Write-Host "[3/4] Verifying archived concept versions..."
$archiveFiles = @(
    ".\docs\archive\Star_Cluster_Roguelike_Game_Concept_v0.1.docx",
    ".\docs\archive\Star_Cluster_Roguelike_Game_Concept_v0.2.docx"
)
foreach ($file in $archiveFiles) {
    if (-not (Test-Path $file)) {
        throw "Archived concept document missing: $file"
    }
}

Write-Host "[4/4] Confirming documentation policy..."
if (-not (Test-Path ".\docs\README.md")) {
    throw "docs\README.md is missing."
}

Write-Host "Documentation update v0.3 completed successfully."
Write-Host "Current concept: $current"
