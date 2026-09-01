[CmdletBinding()]
param()

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path

function Assert-True([bool]$Condition, [string]$Message) { if (-not $Condition) { throw $Message } }
function Read-Json([string]$Path) { Assert-True (Test-Path -LiteralPath $Path -PathType Leaf) "Missing JSON file: $Path"; return (Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json) }
function Find-ById($Items, [string]$Id) { foreach ($item in @($Items)) { if ([string]$item.id -eq $Id) { return $item } }; return $null }

$baseline = Read-Json (Join-Path $repositoryRoot 'docs\design\player_technology\tl1_35_space_player_cruiser_baseline_v0_1.json')
$policy = Read-Json (Join-Path $repositoryRoot 'docs\design\testing\checkpoint_59_validation_suite_policy_v0_1.json')
$active = Read-Json (Join-Path $repositoryRoot 'tools\calibration\checkpoints\checkpoint-59.json')
$deep = Read-Json (Join-Path $repositoryRoot 'tools\calibration\checkpoints\checkpoint-59-deep-calibration.json')
$legacy = Read-Json (Join-Path $repositoryRoot 'tools\calibration\checkpoints\checkpoint-58e.json')

Assert-True ([int]$baseline.checkpoint -eq 59) 'TL1 baseline must identify Checkpoint 59.'
Assert-True ([int]$baseline.installationSpace.playerCruiserTotal -eq 35) 'TL1 player cruiser must use the working 35-Space baseline.'
Assert-True ([int]$baseline.installationSpace.mandatoryCoreTotal -eq 25) 'TL1 mandatory core must total 25 Space.'
Assert-True ([int]$baseline.installationSpace.basePrimaryArmorSpace -eq 0) 'Base primary armor must consume zero Installation Space.'

$components = @($baseline.installationSpace.components)
$weapon = Find-ById $components 'main_weapon'
$reactor = Find-ById $components 'main_reactor'
$stl = Find-ById $components 'stl_drive'
$ftl = Find-ById $components 'ftl_drive'
$computer = Find-ById $components 'tactical_computer'
$activeSensor = Find-ById $components 'active_sensor'
$shield = Find-ById $components 'shield_generator'
$pds = Find-ById $components 'kinetic_pds'
$pdsAmmo = Find-ById $components 'pds_ammunition_support'
$aux = Find-ById $components 'small_aux'
Assert-True ($null -ne $weapon -and [int]$weapon.space -eq 6 -and [bool]$weapon.duplicable) 'TL1 main weapon footprint/duplication mismatch.'
Assert-True ($null -ne $reactor -and [int]$reactor.space -eq 6 -and [bool]$reactor.duplicable) 'TL1 main reactor footprint/duplication mismatch.'
Assert-True ($null -ne $stl -and [int]$stl.space -eq 5 -and (-not [bool]$stl.duplicable) -and [int]$stl.ordinaryMiniaturizationFloor -eq 4) 'TL1 STL primary architecture mismatch.'
Assert-True ($null -ne $ftl -and [int]$ftl.space -eq 5 -and (-not [bool]$ftl.duplicable) -and [int]$ftl.ordinaryMiniaturizationFloor -eq 4 -and [bool]$ftl.playerMandatory) 'TL1 FTL primary architecture mismatch.'
Assert-True ($null -ne $computer -and [int]$computer.space -eq 3 -and (-not [bool]$computer.duplicable)) 'TL1 tactical-computer primary architecture mismatch.'
Assert-True ([int]$activeSensor.space -eq 3 -and [int]$shield.space -eq 3 -and [int]$pds.space -eq 2 -and [int]$pdsAmmo.space -eq 1 -and [int]$aux.space -eq 1) 'TL1 optional footprint mismatch.'

$mandatory = [int]$weapon.space + [int]$reactor.space + [int]$stl.space + [int]$ftl.space + [int]$computer.space
Assert-True ($mandatory -eq 25) 'Calculated TL1 mandatory core must equal 25.'
$balanced = Find-ById @($baseline.referenceBuilds) 'balanced_generalist'
$striker = Find-ById @($baseline.referenceBuilds) 'dual_main_striker'
$over = Find-ById @($baseline.referenceBuilds) 'dual_main_dual_reactor_core'
Assert-True ([int]$balanced.space -eq 35 -and [bool]$balanced.legal) 'Balanced reference build must be legal at 35 Space.'
Assert-True ([int]$striker.space -eq 35 -and [bool]$striker.legal) 'Dual-main striker reference build must be legal at 35 Space.'
Assert-True ([int]$over.space -eq 37 -and (-not [bool]$over.legal)) 'Dual-main/dual-reactor core must remain a 37-Space illegal TL1 stress case.'

$primaryIds = @($baseline.installationSpace.primaryArchitectureIds)
Assert-True ($primaryIds.Count -eq 3 -and $primaryIds -contains 'stl_drive' -and $primaryIds -contains 'ftl_drive' -and $primaryIds -contains 'tactical_computer') 'Primary architecture IDs mismatch.'
$backupIds = @($baseline.installationSpace.limitedAuxiliaryBackupEligibleIds)
Assert-True ($backupIds.Count -eq 2 -and $backupIds -contains 'stl_drive' -and $backupIds -contains 'tactical_computer' -and (-not ($backupIds -contains 'ftl_drive'))) 'Only STL and tactical computer may receive limited AUX backup.'
Assert-True (-not ([bool]$baseline.installationSpace.fullBackupFtlAllowed)) 'Full backup FTL must remain disallowed.'
Assert-True ([int]$baseline.retainedTl1MechanicalSeed.mainReactorTacticalPowerByCondition.operational -eq 5 -and [int]$baseline.retainedTl1MechanicalSeed.mainReactorTacticalPowerByCondition.degraded -eq 3 -and [int]$baseline.retainedTl1MechanicalSeed.mainReactorTacticalPowerByCondition.disabled -eq 1 -and [int]$baseline.retainedTl1MechanicalSeed.mainReactorTacticalPowerByCondition.destroyed -eq 0) 'Retained TL1 reactor 5/3/1/0 seed mismatch.'

$must = @($policy.mustAlwaysRunStageIds)
$deepOnly = @($policy.deepCalibrationStageIds)
$archived = @($policy.archivedHistoricalStageIds)
Assert-True ($must.Count -eq 6) 'Checkpoint 59 must-always-run stage count must be 6.'
Assert-True ($deepOnly.Count -eq 12) 'Checkpoint 59 Deep Calibration addition count must be 12.'
Assert-True ($archived.Count -eq 38) 'Checkpoint 59 historical-only stage count must be 38.'
$allClassified = @($must + $deepOnly + $archived)
Assert-True ($allClassified.Count -eq 56) 'Checkpoint 59 suite policy must classify all 56 Checkpoint 58e runner stages.'
Assert-True (($allClassified | Select-Object -Unique).Count -eq 56) 'Checkpoint 59 stage classifications must be mutually exclusive.'
$legacyIds = @($legacy.stages | ForEach-Object { [string]$_.id })
foreach ($id in $legacyIds) { Assert-True ($allClassified -contains $id) "Legacy stage is not classified by Checkpoint 59: $id" }

$activeIds = @($active.stages | ForEach-Object { [string]$_.id })
$expectedActive = @($legacyIds | Where-Object { $must -contains $_ })
Assert-True (($activeIds -join '|') -eq ($expectedActive -join '|')) 'Active checkpoint stage order/content does not match must-always-run policy.'
foreach ($stage in @($active.stages)) {
    $usesTrials = $false
    $metricsProp = $stage.PSObject.Properties['metrics']
    if ($null -ne $metricsProp) {
        $usesProp = $stage.metrics.PSObject.Properties['usesTrials']
        if ($null -ne $usesProp) { $usesTrials = [bool]$usesProp.Value }
    }
    Assert-True (-not $usesTrials) "Default active suite may not contain Monte Carlo stage $($stage.id)."
}
Assert-True ([int]$active.checkpointMetrics.stageCount -eq 6 -and [int]$active.checkpointMetrics.monteCarloVariantCount -eq 0) 'Active checkpoint workload metrics mismatch.'

$deepIds = @($deep.stages | ForEach-Object { [string]$_.id })
$expectedDeep = @($legacyIds | Where-Object { $must -contains $_ -or $deepOnly -contains $_ })
Assert-True (($deepIds -join '|') -eq ($expectedDeep -join '|')) 'Deep checkpoint stage order/content does not match policy.'
Assert-True ([int]$deep.checkpointMetrics.stageCount -eq 18 -and [int]$deep.checkpointMetrics.monteCarloVariantCount -eq 1026 -and [int]$deep.checkpointMetrics.trialsAtDefault -eq 10260000) 'Deep Calibration workload metrics mismatch.'

$validationFiles = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs\validation') -File -Filter '*.md')
Assert-True ($validationFiles.Count -eq 1 -and $validationFiles[0].Name -eq 'Checkpoint_59_Active_Test_Suite_Scrub_And_TL1_35_Space_Baseline.md') 'Exactly one active validation runbook must remain.'
Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot 'docs\Star_Cluster_Game_Concept_v0.6b.docx') -PathType Leaf) 'Concept v0.6b must be active.'
Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot 'docs\archive\Star_Cluster_Game_Concept_v0.6a.docx') -PathType Leaf) 'Concept v0.6a must be archived.'

Write-Host '       Checkpoint 59 design contract: 35-Space TL1 player cruiser; 25-Space mandatory core; 10-Space discretionary envelope.'
Write-Host '       Primary architectures: one STL, one FTL, one tactical computer; AUX backup may later cover STL/computer only.'
Write-Host '       Validation scrub: 6 must-always-run runner stages; 12 optional TL1 deep-calibration studies; 38 historical-only stages.'
Write-Host '       Default active suite has zero Monte Carlo variants; Deep Calibration has 1,026 variants / 10.26 million default trials.'
