[CmdletBinding()]
param()

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path

function Assert-True([bool]$Condition, [string]$Message) { if (-not $Condition) { throw $Message } }
function Read-Json([string]$Path) { Assert-True (Test-Path -LiteralPath $Path -PathType Leaf) "Missing JSON file: $Path"; return (Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json) }
function Find-ById($Items, [string]$Id) { foreach ($item in @($Items)) { if ([string]$item.id -eq $Id) { return $item } }; return $null }

$baseline = Read-Json (Join-Path $repositoryRoot 'docs\design\player_technology\tl1_35_space_player_cruiser_baseline_v0_7.json')
$study = Read-Json (Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\Scenarios\TL1Calibration\tl1-itc08-bilateral-tactical-geometry-fuel-movement-order.json')
$profiles = Read-Json (Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\Scenarios\ArchitectureTechnology\tl1-tl2-standard-runtime-profiles-v0_3.json')
$schema = Read-Json (Join-Path $repositoryRoot 'docs\design\player_technology\tl1_integrated_tactical_combat_schema_v0_11.json')
$policy = Read-Json (Join-Path $repositoryRoot 'docs\design\testing\checkpoint_65_validation_suite_policy_v0_1.json')
$active = Read-Json (Join-Path $repositoryRoot 'tools\calibration\checkpoints\checkpoint-65a.json')
$deep = Read-Json (Join-Path $repositoryRoot 'tools\calibration\checkpoints\checkpoint-65a-deep-calibration.json')

Assert-True ([string]$active.checkpointId -eq '65a' -and [string]$deep.checkpointId -eq '65a') 'Checkpoint 65a definitions must identify checkpoint 65a.'
Assert-True ([string]$active.manifestFile -eq 'CHECKPOINT_65A_SHA256SUMS.txt' -and [string]$deep.manifestFile -eq 'CHECKPOINT_65A_SHA256SUMS.txt') 'Checkpoint 65a definitions must bind CHECKPOINT_65A_SHA256SUMS.txt.'
Assert-True ([string]$active.outputRoot -eq 'out/checkpoint-65a' -and [string]$deep.outputRoot -eq 'out/checkpoint-65a-deep-calibration') 'Checkpoint 65a output roots must be checkpoint-specific.'
Assert-True (@($active.documentation) -contains 'docs/validation/Checkpoint_65a_TL1_Bilateral_Tactical_Geometry_Fuel_And_Movement_Order_Hotfix.md') 'Checkpoint 65a definition must reference the active runbook.'

Assert-True ([int]$baseline.checkpoint -eq 65) 'TL1 baseline must identify Checkpoint 65.'
Assert-True ([int]$baseline.installationSpace.playerCruiserTotal -eq 35 -and [int]$baseline.installationSpace.mandatoryCoreTotal -eq 25) 'TL1 construction baseline changed unexpectedly.'
Assert-True ([int]$baseline.bilateralTacticalGeometryFuelMovementOrderStudy.variantCount -eq 54) 'Checkpoint 65 baseline must define 54 variants.'
Assert-True ([int]$baseline.bilateralTacticalGeometryFuelMovementOrderStudy.productionReactorOutput -eq 5) 'Production TL1 reactor must remain 5 TP.'
Assert-True ([int]$baseline.bilateralTacticalGeometryFuelMovementOrderStudy.map.radius -eq 5 -and [int]$baseline.bilateralTacticalGeometryFuelMovementOrderStudy.map.cellCount -eq 91) 'Checkpoint 65 baseline must use the radius-5 / 91-cell tactical map.'
Assert-True ([int]$baseline.bilateralTacticalGeometryFuelMovementOrderStudy.fuel.startingFuel -eq 200 -and [int]$baseline.bilateralTacticalGeometryFuelMovementOrderStudy.fuel.fuelPerTraversedHex -eq 2 -and [int]$baseline.bilateralTacticalGeometryFuelMovementOrderStudy.fuel.evasiveManeuverFlatFuelPerTurn -eq 1) 'Checkpoint 65 fuel baseline mismatch.'
Assert-True (-not [bool]$baseline.bilateralTacticalGeometryFuelMovementOrderStudy.balanceTargetsBlocking) 'Checkpoint 65 outcomes must remain diagnostic.'

$production = Find-ById $profiles.profiles 'tl1-production'
Assert-True ($null -ne $production -and [int]$production.powerAndControl.reactorOutput -eq 5) 'TL1 production runtime profile must remain 5 TP.'

Assert-True ([string]$study.id -eq 'tl1-itc08-bilateral-tactical-geometry-fuel-movement-order') 'Unexpected Checkpoint 65 study ID.'
Assert-True (@($study.builds).Count -eq 1 -and [string]$study.builds[0].id -eq 'balanced_generalist_major') 'Checkpoint 65 study must isolate the balanced-generalist build.'
Assert-True (@($study.variants).Count -eq 54) 'Checkpoint 65 study must define exactly 54 variants.'
$families = @('Kinetic','Energy','Missile')
$regimes = @(
    @{ Move='OpponentAwareRange'; Track='EstablishedFirm'; Ew=0 },
    @{ Move='TrackAwareOpponentRange'; Track='AcquisitionFirstAutoActive'; Ew=0 },
    @{ Move='TrackAwareOpponentRange'; Track='AcquisitionFirstAutoActive'; Ew=1 }
)
$orders = @('SideAFirst','SideBFirst')
foreach ($familyA in $families) {
    foreach ($familyB in $families) {
        foreach ($regime in $regimes) {
            $lane = @($study.variants | Where-Object { [string]$_.sideAFamily -eq $familyA -and [string]$_.sideBFamily -eq $familyB -and [string]$_.movementMode -eq $regime.Move -and [string]$_.sideATrackPolicy -eq $regime.Track -and [string]$_.sideBTrackPolicy -eq $regime.Track -and [int]$_.sideANetEwRangePenalty -eq $regime.Ew -and [int]$_.sideBNetEwRangePenalty -eq $regime.Ew })
            Assert-True ($lane.Count -eq 2) "Expected mirrored movement-order pair for $familyA/$familyB/$($regime.Move)/EW$($regime.Ew)."
            Assert-True (@($lane | ForEach-Object { [string]$_.comparisonGroup } | Select-Object -Unique).Count -eq 1) 'Mirrored movement-order variants must share a comparisonGroup/seed lane.'
            foreach ($order in $orders) {
                $matches = @($lane | Where-Object { [string]$_.movementOrder -eq $order })
                Assert-True ($matches.Count -eq 1) "Missing movement order $order."
                $v = $matches[0]
                Assert-True ([int]$v.tacticalMapRadius -eq 5 -and [int]$v.initialRangeHexes -eq 4) "Variant $($v.id) finite-map contract mismatch."
                Assert-True ([int]$v.startingFuel -eq 200 -and [int]$v.movementFuelPerHex -eq 2 -and [int]$v.evasiveManeuverFuelCost -eq 1) "Variant $($v.id) fuel contract mismatch."
                Assert-True ([string]$v.sideABuildId -eq 'balanced_generalist_major' -and [string]$v.sideBBuildId -eq 'balanced_generalist_major') "Variant $($v.id) build mismatch."
                Assert-True ([string]$v.sideATacticalPowerDoctrine -eq 'FullVolleyFirst' -and [string]$v.sideBTacticalPowerDoctrine -eq 'FullVolleyFirst') "Variant $($v.id) doctrine mismatch."
                Assert-True ([int]$v.sideAReactorOutputOverride -eq 5 -and [int]$v.sideBReactorOutputOverride -eq 5) "Variant $($v.id) reactor mismatch."
                Assert-True (-not [bool]$v.evasiveManeuversEnabled -and -not [bool]$v.escapeDisengagementEnabled) "Variant $($v.id) must keep EvM and disengagement off."
            }
        }
    }
}

$variantProps = $schema.'$defs'.variant.properties
Assert-True (@($variantProps.movementOrder.enum) -contains 'SideAFirst' -and @($variantProps.movementOrder.enum) -contains 'SideBFirst') 'Schema v0.11 is missing movement-order bounds.'
Assert-True ($null -ne $variantProps.tacticalMapRadius -and $null -ne $variantProps.startingFuel -and $null -ne $variantProps.movementFuelPerHex -and $null -ne $variantProps.evasiveManeuverFuelCost) 'Schema v0.11 is missing finite-map/fuel controls.'

$must = @($policy.mustAlwaysRunStageIds)
$deepOnly = @($policy.deepCalibrationStageIds)
Assert-True ($must.Count -eq 8 -and $must -contains 'tl1-bilateral-tactical-geometry' -and -not ($must -contains 'tl1-track-aware-movement-acquisition')) 'Checkpoint 65 normal suite must contain only the current stochastic study.'
Assert-True ($deepOnly.Count -eq 16 -and $deepOnly[0] -eq 'tl1-track-aware-movement-acquisition') 'Checkpoint 65 Deep Calibration historical stage policy mismatch.'
Assert-True ([int]$active.checkpointMetrics.stageCount -eq 8 -and [int]$active.checkpointMetrics.monteCarloVariantCount -eq 54 -and [int]$active.checkpointMetrics.trialsAtDefault -eq 540000) 'Checkpoint 65 active workload metrics mismatch.'
Assert-True ([int]$deep.checkpointMetrics.stageCount -eq 24 -and [int]$deep.checkpointMetrics.monteCarloVariantCount -eq 1404 -and [int]$deep.checkpointMetrics.trialsAtDefault -eq 14040000) 'Checkpoint 65 Deep workload metrics mismatch.'

$runner = Get-Content -LiteralPath (Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\TL1Calibration\Tl1IntegratedTacticalCombatRunner.cs') -Raw
$docs = Get-Content -LiteralPath (Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\TL1Calibration\Tl1IntegratedTacticalCombatDocuments.cs') -Raw
Assert-True ($docs -match 'Tl1IntegratedMovementOrder' -and $docs -match 'tacticalMapRadius' -and $docs -match 'movementFuelPerHex') 'Integrated combat document model is missing Checkpoint 65 fields.'
Assert-True ($runner -match 'tl1-itc08-bilateral-tactical-geometry-fuel-movement-order' -and $runner -match 'FiniteTacticalMovementResolver' -and $runner -match 'AdvanceMissilesFiniteMap') 'Integrated runner is missing finite-map Checkpoint 65 behavior.'
Assert-True ($runner -match 'tl1-c65-fuel-accounting' -and $runner -match 'bilateral-geometry-movement-order-paired-review.csv') 'Integrated runner is missing Checkpoint 65 gates/reporting.'

$validationFiles = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs\validation') -File -Filter '*.md')
Assert-True ($validationFiles.Count -eq 1 -and $validationFiles[0].Name -eq 'Checkpoint_65a_TL1_Bilateral_Tactical_Geometry_Fuel_And_Movement_Order_Hotfix.md') 'Exactly one Checkpoint 65a active validation runbook must remain.'
$rootTxt = @(Get-ChildItem -LiteralPath $repositoryRoot -File -Filter '*.txt')
Assert-True ($rootTxt.Count -eq 1 -and $rootTxt[0].Name -eq 'CHECKPOINT_65A_SHA256SUMS.txt') 'Repository root must contain only CHECKPOINT_65A_SHA256SUMS.txt as a .txt file.'
$archivedTxt = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs\archive') -Recurse -File -Filter '*.txt')
Assert-True ($archivedTxt.Count -eq 0) 'Generated historical checkpoint .txt artifacts must not remain under docs/archive.'

Write-Host '       Checkpoint 65a design contract: balanced TL1 cruisers on the radius-5 map, 3x3 weapon families, 3 bilateral regimes, 2 movement orders = 54 variants.'
Write-Host '       Fuel: 200 start / 2 per traversed hex / EvM +1; EvM remains off in the current Monte Carlo isolation.'
Write-Host '       Final positions drive ordinary post-Movement combat; closest approach remains Movement-phase/diagnostic evidence.'
Write-Host '       Existing Tactical Power windows and overload/Strain rules remain authoritative; no full tactical-response AI is added.'
Write-Host '       No target win rate is a release gate; contextual capabilities such as Energy APEN remain preserved.'
Write-Host '       Validation tiers: 8 normal stages / 54 MC variants; Deep Calibration 24 stages / 1,404 MC variants.'
