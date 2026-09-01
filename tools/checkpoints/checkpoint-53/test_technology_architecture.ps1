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
function Find-Subfamily($Items, [string]$Id) {
    foreach ($item in @($Items)) { if ([string]$item.id -eq $Id) { return $item } }
    return $null
}

$architecture = Read-Json (Join-Path $pt 'player_technology_architecture_v0_5.json')
$schema = Read-Json (Join-Path $pt 'player_technology_architecture_schema_v0_5.json')
$bridge = Read-Json (Join-Path $pt 'scenario_architecture_bridge_v0_5.json')
$standard = Read-Json (Join-Path $scenarioRoot 'tl1-tl2-standard-runtime-profiles-v0_3.json')
$aux = Read-Json (Join-Path $scenarioRoot 'tl1-tl2-auxiliary-runtime-profiles-v0_3.json')
$refined = Read-Json (Join-Path $scenarioRoot 'aux-itc04-tl1-tl2-auxiliary-refinement.json')
$ablative = Read-Json (Join-Path $scenarioRoot 'aux-abl01-tl2-ablative-candidate-study.json')
$ablativeCatalogRelative = ([string]$ablative.auxiliaryProfileCatalog).Replace('/','\')
$ablativeCatalog = Read-Json (Join-Path $repositoryRoot $ablativeCatalogRelative)
$power = Read-Json (Join-Path $scenarioRoot 'aux-pwr01-tactical-power-stress.json')
$endurance = Read-Json (Join-Path $scenarioRoot 'aux-end02-resource-semantics-lock.json')
$pds = Read-Json (Join-Path $pt 'pds_tl1_tl2_characteristics_v0_3.json')
$lifecycle = Read-Json (Join-Path $pt 'auxiliary_resource_lifecycle_v0_2.json')
$inventory = Read-Json (Join-Path $pt 'checkpoint_53_early_auxiliary_matrix_inventory_v0_3.json')
$checkpoint = Read-Json (Join-Path $repositoryRoot 'tools\calibration\checkpoints\checkpoint-53.json')

Assert-True ([int]$architecture.checkpoint -eq 53) 'Architecture must identify Checkpoint 53.'
Assert-True ([int]$schema.properties.checkpoint.const -eq 53) 'Architecture schema must identify Checkpoint 53.'
Assert-True ([int]$bridge.checkpoint -eq 53) 'Scenario bridge must identify Checkpoint 53.'
Assert-True ([int]$bridge.matrixPolicy.normalTl1AuxCapacity -eq 1) 'Normal TL1 AUX Capacity must be one.'
Assert-True ([int]$bridge.matrixPolicy.normalTl2AuxCapacity -eq 1) 'Normal TL2 AUX Capacity must be one.'
Assert-True ([bool]$bridge.matrixPolicy.noAuxIsDiagnosticOnly) 'No-AUX must remain diagnostic only.'
Assert-True ([string]$bridge.matrixPolicy.tl3ThroughTl9RuntimeGeneration -eq 'deferred') 'TL3-TL9 runtime generation must remain deferred.'
Assert-True ([string]$bridge.resourcePolicy.combatBattery -match 'no encounter cap') 'Combat Battery bridge must state no encounter cap.'
Assert-True ([string]$bridge.resourcePolicy.amm -match '25 rounds at TL1 and TL2') 'AMM bridge must hold 25 rounds at both early TLs.'
Assert-True ([string]$bridge.resourcePolicy.ablativeArmor -match 'entry TL2') 'Ablative Armor bridge must begin at TL2.'

Assert-True (@($standard.profiles).Count -eq 2) 'Runtime standard catalog must contain TL1 and TL2 only.'
$tl1 = Find-ById $standard.profiles 'tl1-production'
$tl2 = Find-ById $standard.profiles 'tl2-production'
Assert-True ($null -ne $tl1 -and $null -ne $tl2) 'TL1/TL2 standard profiles missing.'
Assert-True ([int]$tl1.defense.hull -eq 12 -and [int]$tl1.powerAndControl.reactorOutput -eq 5 -and [int]$tl1.powerAndControl.targetingBonus -eq 10) 'TL1 table-backed standard changed unexpectedly.'
Assert-True ([int]$tl2.defense.armorIntegrity -eq 5 -and [int]$tl2.powerAndControl.reactorOutput -eq 6 -and [int]$tl2.weapons.kinetic.accuracyBonus -eq 23 -and [int]$tl2.weapons.energy.accuracyBonus -eq 28 -and [int]$tl2.weapons.missile.guidanceChance -eq 60) 'TL2 accepted standard changed unexpectedly.'

$normalAux = @($aux.profiles | Where-Object { -not [bool]$_.counterfactual })
$counterfactual = @($aux.profiles | Where-Object { [bool]$_.counterfactual })
$tl1Aux = @($normalAux | Where-Object { [int]$_.technologyLevel -eq 1 })
$tl2Aux = @($normalAux | Where-Object { [int]$_.technologyLevel -eq 2 })
Assert-True ($tl1Aux.Count -eq 7) 'Checkpoint 53 must contain seven legal TL1 combat AUX profiles.'
Assert-True ($tl2Aux.Count -eq 9) 'Checkpoint 53 must contain nine legal TL2 combat AUX profiles.'
Assert-True ($counterfactual.Count -eq 2) 'Checkpoint 53 must contain two no-AUX diagnostics.'
Assert-True (@($tl1Aux | Where-Object { [string]$_.familyId -eq 'aux_ablative_armor' }).Count -eq 0) 'Ablative Armor must not be legal at TL1.'
$tl2Abl = @($tl2Aux | Where-Object { [string]$_.familyId -eq 'aux_ablative_armor' })
Assert-True ($tl2Abl.Count -eq 1 -and [int]$tl2Abl[0].ablativeProtection -eq 0 -and [int]$tl2Abl[0].ablativeIntegrity -eq 2) 'TL2 leading Ablative profile must be AP0/AI2.'

$auxMap = @{}; foreach ($profile in @($aux.profiles)) { $auxMap[[string]$profile.id] = $profile }
foreach ($id in @('aux-r53-tl1-combat-battery','aux-r53-tl2-combat-battery')) {
    Assert-True ($auxMap.ContainsKey($id)) "Missing Combat Battery profile $id."
    Assert-True ([int]$auxMap[$id].combatBatteryGain -eq 1 -and [int]$auxMap[$id].combatBatteryCharges -eq 3) "$id must use +1 TP and three charges."
}
Assert-True ([int]$auxMap['aux-r53-tl2-power-capacitor'].capacitorCapacity -eq 1 -and [int]$auxMap['aux-r53-tl2-power-capacitor'].capacitorChargeRate -eq 1 -and [int]$auxMap['aux-r53-tl2-power-capacitor'].capacitorDischargeRate -eq 1) 'Power Capacitor must use 1/1/1 storage/recharge/discharge.'
foreach ($id in @('aux-r53-tl1-amm-pds','aux-r53-tl2-amm-pds')) {
    Assert-True ([int]$auxMap[$id].pdsPower -eq 1 -and [int]$auxMap[$id].pdsAmmunition -eq 25) "$id must use 1 TP and 25 AMM rounds."
}

Assert-True (@($pds.profiles).Count -eq 6) 'PDS companion must contain six TL1/TL2 rows.'
Assert-True (@($pds.profiles | Where-Object { [int]$_.reactionCapacity -ne 1 }).Count -eq 0) 'PDS Reaction Capacity must remain one.'
foreach ($row in @($pds.profiles | Where-Object { [string]$_.subfamilyId -eq 'aux_amm_pds' })) {
    Assert-True ([int]$row.tacticalPowerReadiness -eq 1 -and [int]$row.ammunition -eq 25) 'AMM companion must use 1 TP and 25 rounds at TL1/TL2.'
}
Assert-True (@($pds.ammunitionSensitivityCandidates.ammRounds).Count -eq 1 -and [int]$pds.ammunitionSensitivityCandidates.ammRounds[0] -eq 25) 'Checkpoint 53 AMM review must hold 25 rounds.'

Assert-True ([int]$lifecycle.checkpoint -eq 53) 'Resource lifecycle must identify Checkpoint 53.'
Assert-True ([int]$lifecycle.combatBattery.primaryCharges -eq 3 -and [int]$lifecycle.combatBattery.tacticalPowerPerCharge -eq 1 -and [int]$lifecycle.combatBattery.dischargeLimitPerTurn -eq 1) 'Combat Battery lifecycle mismatch.'
Assert-True ($null -eq $lifecycle.combatBattery.encounterDischargeCap) 'Combat Battery must have no encounter discharge cap.'
Assert-True ([int]$lifecycle.powerCapacitor.storedPower -eq 1 -and [int]$lifecycle.powerCapacitor.dischargePower -eq 1 -and [int]$lifecycle.powerCapacitor.rechargeCost -eq 1 -and -not [bool]$lifecycle.powerCapacitor.sameTurnChargeAndDischarge) 'Power Capacitor lifecycle mismatch.'
Assert-True ([int]$lifecycle.amm.tl1PrimaryRounds -eq 25 -and [int]$lifecycle.amm.tl2PrimaryRounds -eq 25) 'Lifecycle must hold 25 AMM rounds at TL1/TL2.'
Assert-True ([bool]$lifecycle.shieldRecharge.coreCapability) 'Tactical shield recharge must remain core capability.'
Assert-True ([int]$inventory.checkpoint -eq 53) 'Early AUX inventory must identify Checkpoint 53.'

$variants = @($refined.variants)
$legal = @($variants | Where-Object { [string]$_.profileLabel -eq 'aux-r53-refined-legal-matrix' })
$diagnostic = @($variants | Where-Object { [string]$_.profileLabel -eq 'aux-r53-no-aux-diagnostic' })
Assert-True ($variants.Count -eq 870 -and $legal.Count -eq 768 -and $diagnostic.Count -eq 102) 'Refined matrix must contain 870 = 768 legal + 102 diagnostic variants.'
$tl1v1 = @($legal | Where-Object { $_.sideAProfileId -eq 'tl1-production' -and $_.sideBProfileId -eq 'tl1-production' }).Count
$tl2v2 = @($legal | Where-Object { $_.sideAProfileId -eq 'tl2-production' -and $_.sideBProfileId -eq 'tl2-production' }).Count
$cross = @($legal | Where-Object { $_.sideAProfileId -ne $_.sideBProfileId }).Count
Assert-True ($tl1v1 -eq 147 -and $tl2v2 -eq 243 -and $cross -eq 378) 'Refined legal band counts must be 147/243/378.'
Assert-True (@($variants | Where-Object { [string]$_.sideAAuxiliaryProfileId -match 'ablative' -and $_.sideAProfileId -eq 'tl1-production' }).Count -eq 0) 'TL1 side A must never install Ablative Armor.'
Assert-True (@($variants | Where-Object { [string]$_.sideBAuxiliaryProfileId -match 'ablative' -and $_.sideBProfileId -eq 'tl1-production' }).Count -eq 0) 'TL1 side B must never install Ablative Armor.'

$ablVariants = @($ablative.variants)
Assert-True ($ablVariants.Count -eq 96) 'TL2 Ablative candidate study must contain 96 variants.'
Assert-True ([string]$ablative.auxiliaryProfileCatalog -eq 'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/tl2-ablative-candidate-profiles-v0_1.json') 'TL2 Ablative study must reference the expected candidate catalog.'
Assert-True (@($ablativeCatalog.profiles).Count -eq 6) 'TL2 Ablative candidate catalog must contain six profiles.'
foreach ($id in @('aux-r53-abl-ap0-ai2','aux-r53-abl-ap0-ai3','aux-r53-abl-ap1-ai1','aux-r53-abl-ap1-ai2-control','aux-r53-abl-none-tl2','aux-r53-abl-evasion-control')) {
    Assert-True (@($ablativeCatalog.profiles | Where-Object { [string]$_.id -eq $id }).Count -eq 1) "Missing Ablative study profile $id."
}

$powerVariants = @($power.variants)
$normalPower = @($powerVariants | Where-Object { [int]$_.sideABackgroundTacticalPowerCommitment -eq 0 -and [int]$_.sideBBackgroundTacticalPowerCommitment -eq 0 })
$stressPower = @($powerVariants | Where-Object { [int]$_.sideABackgroundTacticalPowerCommitment -gt 0 -or [int]$_.sideBBackgroundTacticalPowerCommitment -gt 0 })
Assert-True ($powerVariants.Count -eq 78 -and $normalPower.Count -eq 39 -and $stressPower.Count -eq 39) 'Power stress study must contain 39 control + 39 sustained-load variants.'
foreach ($v in $stressPower) {
    $expectedA = if ([string]$v.sideAProfileId -eq 'tl1-production') { 3 } else { 4 }
    $expectedB = if ([string]$v.sideBProfileId -eq 'tl1-production') { 3 } else { 4 }
    Assert-True ([int]$v.sideABackgroundTacticalPowerCommitment -eq $expectedA) "Unexpected side A stress load in $($v.id)."
    Assert-True ([int]$v.sideBBackgroundTacticalPowerCommitment -eq $expectedB) "Unexpected side B stress load in $($v.id)."
}

Assert-True ([int]$endurance.checkpoint -eq 53) 'Resource-semantics study must identify Checkpoint 53.'
Assert-True ([int]$endurance.combatBattery.powerPerCharge -eq 1 -and @($endurance.combatBattery.candidateCharges).Count -eq 1 -and [int]$endurance.combatBattery.candidateCharges[0] -eq 3) 'Resource-semantics Battery candidate must be 3 x +1 TP.'
Assert-True ([string]$endurance.policy -match 'one discharge per tactical turn') 'Resource-semantics policy must state one discharge per tactical turn.'
Assert-True ([string]$endurance.policy -match 'no encounter cap') 'Resource-semantics policy must state no encounter cap.'
Assert-True (@($endurance.amm.roundCandidates).Count -eq 1 -and [int]$endurance.amm.roundCandidates[0] -eq 25) 'Resource-semantics AMM reserve must be fixed at 25 rounds.'

Assert-True ([string]$checkpoint.checkpointId -eq '53') 'Checkpoint definition ID mismatch.'
Assert-True (@($checkpoint.stages).Count -eq 31 -and [int]$checkpoint.checkpointMetrics.stageCount -eq 31) 'Checkpoint 53 must contain 31 stages.'
Assert-True ([int]$checkpoint.checkpointMetrics.monteCarloVariantCount -eq 9007 -and [int]$checkpoint.checkpointMetrics.trialsAtDefault -eq 90070000) 'Checkpoint 53 workload metrics mismatch.'
Assert-True ([string]$checkpoint.primaryStudy.id -eq 'aux-itc04-tl1-tl2-auxiliary-refinement' -and [int]$checkpoint.primaryStudy.variantCount -eq 870) 'Checkpoint 53 primary-study metadata mismatch.'

$hashPath = Join-Path $PSScriptRoot 'checkpoint_52_scenario_hashes.txt'
Assert-True (Test-Path -LiteralPath $hashPath -PathType Leaf) 'Missing frozen Checkpoint 52 scenario hash list.'
$expected = New-Object 'System.Collections.Generic.Dictionary[string,string]' ([System.StringComparer]::OrdinalIgnoreCase)
foreach ($line in Get-Content -LiteralPath $hashPath) {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    if ($line -notmatch '^([0-9a-fA-F]{64})  (.+)$') { throw "Invalid scenario hash line: $line" }
    $expected.Add($Matches[2].Replace('/','\'), $Matches[1].ToLowerInvariant())
}
Assert-True ($expected.Count -eq 60) 'Checkpoint 52 frozen runtime snapshot must contain 60 scenario JSON files.'
foreach ($relative in $expected.Keys) {
    $path = Join-Path $repositoryRoot $relative
    Assert-True (Test-Path -LiteralPath $path -PathType Leaf) "Frozen Checkpoint 52 scenario file missing: $relative"
    $actual = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    Assert-True ($actual -eq $expected[$relative]) "Frozen Checkpoint 52 scenario file changed: $relative"
}

Write-Host '       Checkpoint 52 frozen runtime boundary: 60 scenario JSON files SHA-256 verified unchanged.'
Write-Host '       Early catalog: 7 legal TL1 AUX and 9 legal TL2 AUX; Ablative Armor begins at TL2.'
Write-Host '       AMM: 1 TP and 25 rounds at TL1/TL2; current PDS accuracy progression retained.'
Write-Host '       Combat Battery: +1 TP x3, one discharge per tactical turn, no encounter cap; charges persist.'
Write-Host '       Power Capacitor: 1/1/1 discharge-recharge cycle; tactical shield recharge remains core.'
Write-Host '       Checkpoint 53 evidence: 870 refined + 96 Ablative + 78 power-stress Monte Carlo variants.'
Write-Host '       Checkpoint 53 definition: 31 stages, 9,007 Monte Carlo variants, 90.07 million default trials.'
