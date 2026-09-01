[CmdletBinding()]
param()

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$pt = Join-Path $repositoryRoot 'docs\design\player_technology'
$scenarioRoot = Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\Scenarios\ArchitectureTechnology'

function Assert-True([bool]$Condition, [string]$Message) {
    if (-not $Condition) { throw $Message }
}
function Read-Json([string]$Path) {
    Assert-True (Test-Path -LiteralPath $Path -PathType Leaf) "Missing JSON file: $Path"
    return (Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json)
}
function Find-ById($Items, [string]$Id) {
    foreach ($item in @($Items)) { if ([string]$item.id -eq $Id) { return $item } }
    return $null
}
function Get-OptionalProperty($Object, [string]$Name, $Default = $null) {
    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) { return $Default }
    return $property.Value
}

$architecture = Read-Json (Join-Path $pt 'player_technology_architecture_v0_7.json')
$schema = Read-Json (Join-Path $pt 'player_technology_architecture_schema_v0_7.json')
$capacityReview = Read-Json (Join-Path $pt 'cruiser_installation_capacity_review_v0_2.json')
$bridge = Read-Json (Join-Path $pt 'scenario_architecture_bridge_v0_7.json')
$standard = Read-Json (Join-Path $scenarioRoot 'tl1-tl3-standard-runtime-profiles-v0_2.json')
$aux = Read-Json (Join-Path $scenarioRoot 'tl3-auxiliary-capstone-profiles-v0_2.json')
$profileStudy = Read-Json (Join-Path $scenarioRoot 'tl3-itc03-low-tech-capstone-profile-screening.json')
$auxStudy = Read-Json (Join-Path $scenarioRoot 'tl3-aux02-low-tech-capstone-two-capacity-screening.json')
$isolationStudy = Read-Json (Join-Path $scenarioRoot 'tl3-aux03-component-isolation.json')
$powerStudy = Read-Json (Join-Path $scenarioRoot 'tl3-pwr02-single-main-power-envelope.json')
$profileCompanion = Read-Json (Join-Path $pt 'checkpoint_55_tl3_lowtech_profile_candidates_v0_1.json')
$auxInventory = Read-Json (Join-Path $pt 'checkpoint_55_tl3_auxiliary_loadout_inventory_v0_1.json')
$checkpoint = Read-Json (Join-Path $repositoryRoot 'tools\calibration\checkpoints\checkpoint-55.json')

Assert-True ([int]$architecture.checkpoint -eq 55) 'Architecture must identify Checkpoint 55.'
Assert-True ([string]$architecture.status -eq 'tl3_lowtech_capstone_candidate_screening') 'Architecture status mismatch.'
Assert-True ([int]$schema.properties.checkpoint.const -eq 55) 'Architecture schema must identify Checkpoint 55.'
Assert-True ([int]$bridge.checkpoint -eq 55) 'Scenario bridge must identify Checkpoint 55.'
Assert-True ([string]$bridge.status -eq 'tl1_tl2_frozen_tl3_lowtech_capstone_screening_bridge') 'Scenario bridge status mismatch.'

$expectedWeapons = @(1,1,1,2,2,2,3,3,3)
$expectedAux = @(1,1,2,2,2,3,3,3,4)
for ($tl = 1; $tl -le 9; $tl++) {
    $key = [string]$tl
    Assert-True ([int]$architecture.installationCapacityProposals.weaponBayCapacity.$key -eq $expectedWeapons[$tl-1]) "Weapon Bay capacity mismatch at TL$tl."
    Assert-True ([int]$architecture.installationCapacityProposals.auxiliaryCapacity.$key -eq $expectedAux[$tl-1]) "AUX capacity mismatch at TL$tl."
    Assert-True ([int]$capacityReview.capacityCurve.weaponBayCapacity.$key -eq $expectedWeapons[$tl-1]) "Capacity review Weapon Bay mismatch at TL$tl."
    Assert-True ([int]$capacityReview.capacityCurve.auxiliaryCapacity.$key -eq $expectedAux[$tl-1]) "Capacity review AUX mismatch at TL$tl."
}
Assert-True ([int]$bridge.matrixPolicy.normalTl3WeaponBays -eq 1) 'Normal TL3 must have one main weapon.'
Assert-True ([int]$bridge.matrixPolicy.normalTl3AuxCapacity -eq 2) 'Normal TL3 must have two AUX capacity.'
Assert-True ([int]$bridge.matrixPolicy.provisionalTl4WeaponBays -eq 2) 'Provisional TL4 must have two main weapons.'
Assert-True ([int]$bridge.matrixPolicy.provisionalTl7WeaponBays -eq 3) 'Provisional TL7 must have three main weapons.'
Assert-True ([string]$bridge.matrixPolicy.multiMainRestrictionPolicy -like 'none;*') 'Checkpoint 55 may not introduce an arbitrary multi-main firing restriction.'

Assert-True ([int]$architecture.generationModel.lowTech.foundationTl -eq 1 -and [int]$architecture.generationModel.lowTech.maturityTl -eq 3) 'Low-tech generation cadence mismatch.'
Assert-True ([int]$architecture.generationModel.midTech.foundationTl -eq 4 -and [int]$architecture.generationModel.midTech.maturityTl -eq 6) 'Mid-tech generation cadence mismatch.'
Assert-True ([int]$architecture.generationModel.highTech.foundationTl -eq 7 -and [int]$architecture.generationModel.highTech.maturityTl -eq 9) 'High-tech generation cadence mismatch.'

Assert-True (@($standard.profiles).Count -eq 6) 'TL1-TL3 standard catalog must contain six profiles.'
$tl2 = Find-ById $standard.profiles 'tl2-production'
$control = Find-ById $standard.profiles 'tl3-lowtech-control'
$offense = Find-ById $standard.profiles 'tl3-offense-refinement'
$defense = Find-ById $standard.profiles 'tl3-defense-refinement'
$mature = Find-ById $standard.profiles 'tl3-mature-lowtech-candidate'
Assert-True ($null -ne $tl2 -and $null -ne $control -and $null -ne $offense -and $null -ne $defense -and $null -ne $mature) 'Required Checkpoint 55 standard profiles missing.'
Assert-True ([int]$control.technologyLevel -eq 3 -and [int]$offense.technologyLevel -eq 3 -and [int]$defense.technologyLevel -eq 3 -and [int]$mature.technologyLevel -eq 3) 'All Checkpoint 55 candidate profiles must identify TL3.'
Assert-True ([int]$control.defense.hull -eq [int]$tl2.defense.hull -and [int]$control.powerAndControl.reactorOutput -eq [int]$tl2.powerAndControl.reactorOutput) 'Low-tech control must preserve TL2 numerical values.'
Assert-True ([int]$offense.defense.hull -eq [int]$tl2.defense.hull -and [int]$offense.weapons.kinetic.damage -eq [int]$tl2.weapons.kinetic.damage) 'Offense refinement may not smuggle in structure or raw-damage jumps.'
Assert-True ([int]$defense.powerAndControl.reactorOutput -eq [int]$tl2.powerAndControl.reactorOutput -and [int]$defense.weapons.energy.damage -eq [int]$tl2.weapons.energy.damage) 'Defense refinement may not smuggle in reactor or weapon-damage jumps.'
Assert-True ([int]$mature.weapons.kinetic.damage -eq [int]$tl2.weapons.kinetic.damage -and [int]$mature.weapons.energy.damage -eq [int]$tl2.weapons.energy.damage) 'Mature low-tech candidate must retain conservative direct-fire damage.'

Assert-True (@($aux.profiles).Count -eq 27) 'Checkpoint 55 TL3 AUX catalog must contain 28 profiles.'
$normalComposites = @($aux.profiles | Where-Object { [string]$_.id -like 'aux-r55-*' -and [int]$_.capacityCost -eq 2 -and -not [bool]$_.counterfactual })
Assert-True ($normalComposites.Count -eq 13) 'Checkpoint 55 must contain 13 capacity-2 TL3 loadouts.'
Assert-True ([int](Find-ById $aux.profiles 'aux-r55-amm').pdsAmmunition -eq 25) 'AMM isolated profile must preserve 25 rounds.'
Assert-True ([int](Find-ById $aux.profiles 'aux-r55-combat-battery').combatBatteryCharges -eq 3) 'Combat Battery must preserve three charges.'
Assert-True ([int](Find-ById $aux.profiles 'aux-r55-auxiliary-reactor').auxiliaryReactorOutput -eq 1) 'Auxiliary Reactor must remain +1 renewable TP.'

Assert-True (@($profileStudy.variants).Count -eq 102) 'TL3 low-tech profile study must contain 102 variants.'
Assert-True (@($auxStudy.variants).Count -eq 585) 'TL3 two-AUX study must contain 585 variants.'
Assert-True (@($isolationStudy.variants).Count -eq 78) 'TL3 AUX isolation study must contain 78 variants.'
Assert-True (@($powerStudy.variants).Count -eq 54) 'TL3 power-envelope study must contain 54 variants.'
foreach ($study in @($profileStudy,$auxStudy,$isolationStudy,$powerStudy)) {
    foreach ($v in @($study.variants)) {
        Assert-True ($null -eq (Get-OptionalProperty $v 'sideASecondaryFamily') -and $null -eq (Get-OptionalProperty $v 'sideBSecondaryFamily')) "Checkpoint 55 variant may not install a second main weapon: $($v.id)"
    }
}
Assert-True (@($profileStudy.variants | Where-Object { [string]$_.profileLabel -eq 'tl3-r55-standard-vs-tl2' }).Count -eq 72) 'TL3-vs-TL2 profile count mismatch.'
Assert-True (@($profileStudy.variants | Where-Object { [string]$_.profileLabel -eq 'tl3-r55-mature-cross-family' }).Count -eq 18) 'Mature cross-family count mismatch.'
Assert-True (@($profileStudy.variants | Where-Object { [string]$_.profileLabel -eq 'tl3-r55-maturity-attribution' }).Count -eq 12) 'Maturity-attribution count mismatch.'
Assert-True (@($auxStudy.variants | Where-Object { [string]$_.profileLabel -eq 'tl3-r55-aux-legal-matrix' }).Count -eq 507) 'TL3 legal two-AUX matrix count mismatch.'
Assert-True (@($auxStudy.variants | Where-Object { [string]$_.profileLabel -eq 'tl3-r55-aux-no-aux-diagnostic' }).Count -eq 78) 'TL3 two-AUX diagnostic count mismatch.'
Assert-True (@($isolationStudy.variants | Where-Object { [string]$_.profileLabel -eq 'tl3-r55-aux-component-isolation' }).Count -eq 78) 'TL3 component-isolation count mismatch.'
Assert-True (@($powerStudy.variants | Where-Object { [string]$_.profileLabel -eq 'tl3-r55-power-normal' }).Count -eq 18) 'TL3 normal power count mismatch.'
Assert-True (@($powerStudy.variants | Where-Object { [string]$_.profileLabel -eq 'tl3-r55-power-stress' }).Count -eq 18) 'TL3 stressed-vs-none power count mismatch.'
Assert-True (@($powerStudy.variants | Where-Object { [string]$_.profileLabel -eq 'tl3-r55-power-stress-pairwise' }).Count -eq 18) 'TL3 stressed pairwise power count mismatch.'

Assert-True (@($profileCompanion.candidates).Count -eq 4) 'TL3 low-tech profile companion must contain four candidates.'
Assert-True (@($auxInventory.isolatedComponents).Count -eq 13) 'TL3 AUX inventory must contain 13 isolated components.'
Assert-True (@($auxInventory.normalLoadouts).Count -eq 13) 'TL3 AUX inventory must contain 13 normal capacity-2 loadouts.'

Assert-True ([string]$checkpoint.checkpointId -eq '55') 'Checkpoint 55 definition ID mismatch.'
Assert-True (@($checkpoint.stages).Count -eq 39 -and [int]$checkpoint.checkpointMetrics.stageCount -eq 39) 'Checkpoint 55 must contain 39 stages.'
Assert-True ([int]$checkpoint.checkpointMetrics.monteCarloVariantCount -eq 10696 -and [int]$checkpoint.checkpointMetrics.trialsAtDefault -eq 106960000) 'Checkpoint 55 workload metrics mismatch.'
Assert-True ([string]$checkpoint.primaryStudy.id -eq 'tl3-itc03-low-tech-capstone-profile-screening' -and [int]$checkpoint.primaryStudy.variantCount -eq 102) 'Checkpoint 55 primary-study metadata mismatch.'

$hashPath = Join-Path $PSScriptRoot 'checkpoint_54a_scenario_hashes.txt'
Assert-True (Test-Path -LiteralPath $hashPath -PathType Leaf) 'Missing frozen Checkpoint 54a scenario hash list.'
$expected = New-Object 'System.Collections.Generic.Dictionary[string,string]' ([System.StringComparer]::OrdinalIgnoreCase)
foreach ($line in Get-Content -LiteralPath $hashPath) {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    if ($line -notmatch '^([0-9a-fA-F]{64})  (.+)$') { throw "Invalid scenario hash line: $line" }
    $expected.Add($Matches[2].Replace('/','\'), $Matches[1].ToLowerInvariant())
}
Assert-True ($expected.Count -eq 73) 'Checkpoint 54a frozen ScenarioRunner snapshot must contain 73 JSON files.'
foreach ($relative in $expected.Keys) {
    $path = Join-Path $repositoryRoot $relative
    Assert-True (Test-Path -LiteralPath $path -PathType Leaf) "Frozen Checkpoint 54a scenario file missing: $relative"
    $actual = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    Assert-True ($actual -eq $expected[$relative]) "Frozen Checkpoint 54a scenario file changed: $relative"
}

Write-Host '       Checkpoint 54a frozen runtime boundary: 73 ScenarioRunner JSON files SHA-256 verified unchanged.'
Write-Host '       Capacity cadence: main weapons 1/1/1, 2/2/2, 3/3/3; AUX 1/1/2, 2/2/3, 3/3/4.'
Write-Host '       TL3 low-tech capstone: one main weapon, two AUX capacity, no arbitrary firing restriction.'
Write-Host '       Checkpoint 55 evidence: 102 profile + 585 two-AUX + 78 isolation + 54 power-envelope variants.'
Write-Host '       Checkpoint 55 definition: 39 stages, 10,696 Monte Carlo variants, 106.96 million default trials.'
