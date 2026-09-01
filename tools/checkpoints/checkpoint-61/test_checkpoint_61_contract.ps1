[CmdletBinding()]
param()

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path

function Assert-True([bool]$Condition, [string]$Message) { if (-not $Condition) { throw $Message } }
function Read-Json([string]$Path) { Assert-True (Test-Path -LiteralPath $Path -PathType Leaf) "Missing JSON file: $Path"; return (Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json) }
function Find-ById($Items, [string]$Id) { foreach ($item in @($Items)) { if ([string]$item.id -eq $Id) { return $item } }; return $null }

$baseline = Read-Json (Join-Path $repositoryRoot 'docs\design\player_technology\tl1_35_space_player_cruiser_baseline_v0_3.json')
$envelope = Read-Json (Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\Scenarios\ArchitectureTechnology\tl1-space01-35-space-construction-envelope.json')
$combat = Read-Json (Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\Scenarios\TL1Calibration\tl1-itc04-35-space-composed-ship-odd-build-matrix.json')
$policy = Read-Json (Join-Path $repositoryRoot 'docs\design\testing\checkpoint_61_validation_suite_policy_v0_1.json')
$active = Read-Json (Join-Path $repositoryRoot 'tools\calibration\checkpoints\checkpoint-61.json')
$deep = Read-Json (Join-Path $repositoryRoot 'tools\calibration\checkpoints\checkpoint-61-deep-calibration.json')

Assert-True ([int]$baseline.checkpoint -eq 61) 'TL1 baseline must identify Checkpoint 61.'
Assert-True ([int]$baseline.installationSpace.playerCruiserTotal -eq 35) 'TL1 player cruiser must remain 35 Space.'
Assert-True ([int]$baseline.installationSpace.mandatoryCoreTotal -eq 25) 'TL1 mandatory core must remain 25 Space.'
Assert-True ([int]$baseline.deterministicArchitectureEnvelope.macroLoadoutCount -eq 27) 'Deterministic envelope must retain 27 macro loadouts.'
Assert-True ([int]$baseline.deterministicArchitectureEnvelope.weaponPowerVariantCount -eq 96) 'Deterministic envelope must retain 96 weapon/power variants.'
Assert-True (-not [bool]$baseline.composedShipCombatStudy.balanceTargetsBlocking) 'Checkpoint 61 combat outcomes must remain diagnostic rather than target-gated.'
Assert-True ([int]$baseline.composedShipCombatStudy.legalBuildCount -eq 6 -and [int]$baseline.composedShipCombatStudy.variantCount -eq 54) 'Baseline composed-study cardinality mismatch.'

Assert-True ([string]$envelope.id -eq 'tl1-space01-35-space-construction-envelope' -and [int]$envelope.checkpoint -eq 60) 'Checkpoint 60 deterministic envelope must remain frozen as the construction source.'
Assert-True (@($envelope.referenceBuilds).Count -eq 7) 'Envelope must retain six legal builds plus the 37-Space illegal control.'

Assert-True ([string]$combat.id -eq 'tl1-itc04-35-space-composed-ship-odd-build-matrix') 'Unexpected Checkpoint 61 combat study ID.'
Assert-True (@($combat.builds).Count -eq 6) 'Composed combat study must define exactly six legal builds.'
Assert-True (@($combat.variants).Count -eq 54) 'Composed combat study must define exactly 54 variants.'
$buildIds = @($combat.builds | ForEach-Object { [string]$_.id })
Assert-True (($buildIds | Select-Object -Unique).Count -eq 6) 'Composed build IDs must be unique.'
$expectedBuildIds = @('balanced_generalist_major','dual_main_striker_major','dual_reactor_power_core','pds_saturator','dual_main_dual_pds','shielded_pds_fortress')
foreach ($id in $expectedBuildIds) { Assert-True ($buildIds -contains $id) "Missing composed build: $id" }
foreach ($v in @($combat.variants)) {
    Assert-True ([string]$v.sideBBuildId -eq 'balanced_generalist_major') "Variant $($v.id) must use balanced Side B."
    Assert-True ([string]$v.sideAProfileId -eq 'tl1-production' -and [string]$v.sideBProfileId -eq 'tl1-production') "Variant $($v.id) must use TL1 production profiles."
    Assert-True ([string]$v.sideAAuxiliaryProfileId -eq 'aux-r53-none-tl1' -and [string]$v.sideBAuxiliaryProfileId -eq 'aux-r53-none-tl1') "Variant $($v.id) must use the zero-effect AUX profile."
    Assert-True ([string]$v.movementMode -eq 'OpponentAwareRange' -and [int]$v.initialRangeHexes -eq 4) "Variant $($v.id) must use the Range-4 opponent-aware control."
    Assert-True ([string]$v.damageControl -eq 'ComponentFirstReserveOne') "Variant $($v.id) must use normal Damage Control."
    Assert-True (-not [bool]$v.evasiveManeuversEnabled -and -not [bool]$v.escapeDisengagementEnabled) "Variant $($v.id) has an unexpected evasion/disengagement control."
}
$dualBuildIds = @('dual_main_striker_major','dual_main_dual_pds')
foreach ($v in @($combat.variants)) {
    if ($dualBuildIds -contains [string]$v.sideABuildId) {
        Assert-True ($null -ne $v.PSObject.Properties['sideASecondaryFamily'] -and [string]$v.sideASecondaryFamily -eq [string]$v.sideAFamily) "Dual-main variant $($v.id) must duplicate the Side-A family."
    } else {
        Assert-True ($null -eq $v.PSObject.Properties['sideASecondaryFamily']) "Single-main variant $($v.id) may not install a secondary family."
    }
}

$must = @($policy.mustAlwaysRunStageIds)
$deepOnly = @($policy.deepCalibrationStageIds)
Assert-True ($must.Count -eq 8 -and $must -contains 'tl1-composed-ship-odd-build-combat') 'Checkpoint 61 must-always-run policy must contain 8 stages including the composed study.'
Assert-True ($deepOnly.Count -eq 12) 'Checkpoint 61 Deep Calibration addition count must remain 12.'
Assert-True ([int]$active.checkpointMetrics.stageCount -eq 8 -and [int]$active.checkpointMetrics.monteCarloVariantCount -eq 54 -and [int]$active.checkpointMetrics.trialsAtDefault -eq 540000) 'Checkpoint 61 active workload metrics mismatch.'
Assert-True ([int]$deep.checkpointMetrics.stageCount -eq 20 -and [int]$deep.checkpointMetrics.monteCarloVariantCount -eq 1080 -and [int]$deep.checkpointMetrics.trialsAtDefault -eq 10800000) 'Checkpoint 61 Deep workload metrics mismatch.'
$activeIds = @($active.stages | ForEach-Object { [string]$_.id })
Assert-True ($activeIds[3] -eq 'tl1-installation-space-envelope' -and $activeIds[4] -eq 'tl1-composed-ship-odd-build-combat') 'Checkpoint 61 architecture/combat stages are out of order.'

$runnerPath = Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\TL1Calibration\Tl1IntegratedTacticalCombatRunner.cs'
$docPath = Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\TL1Calibration\Tl1IntegratedTacticalCombatDocuments.cs'
$runner = Get-Content -LiteralPath $runnerPath -Raw
$docs = Get-Content -LiteralPath $docPath -Raw
Assert-True ($docs -match 'Tl1IntegratedShipBuildDocument' -and $docs -match 'sideABuildId') 'Integrated combat document model is missing explicit build records.'
Assert-True ($runner -match 'tl1-itc04-35-space-composed-ship-odd-build-matrix') 'Integrated runner is missing the Checkpoint 61 study ID.'
Assert-True ($runner -match 'ApplyComposedShipPds' -and $runner -match 'ShuffleDeterministically') 'Integrated runner is missing pooled composed-build PDS allocation.'
Assert-True ($runner -match 'composed-build-rollup.csv' -and $runner -match 'tl1-c61-outcomes-review-only') 'Integrated runner is missing Checkpoint 61 review outputs/nonblocking outcome gate.'

$validationFiles = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs\validation') -File -Filter '*.md')
Assert-True ($validationFiles.Count -eq 1 -and $validationFiles[0].Name -eq 'Checkpoint_61_TL1_35_Space_Composed_Ship_And_Odd_Build_Combat_Study.md') 'Exactly one Checkpoint 61 active validation runbook must remain.'
Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot 'docs\validation\archive\Checkpoint_60_TL1_35_Space_Construction_Envelope_And_Odd_Build_Foundation.md') -PathType Leaf) 'Checkpoint 60 runbook must be archived.'

Write-Host '       Checkpoint 61 design contract: six explicit legal TL1 35-Space build packages across 54 family matchups.'
Write-Host '       Composed path: explicit reactor/shield/sensor/PDS counts, independent second-main support, zero-effect AUX fixture.'
Write-Host '       Validation tiers: 8 normal stages / 54 MC variants; Deep Calibration 20 stages / 1,080 MC variants.'
Write-Host '       Balance outcomes remain review evidence; no target win percentage is a release gate.'
