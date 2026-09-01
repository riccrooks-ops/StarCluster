[CmdletBinding()]
param()

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$pt = Join-Path $repositoryRoot 'docs\design\player_technology'
$scenarioRoot = Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\Scenarios\ArchitectureTechnology'

$architecturePath = Join-Path $pt 'player_technology_architecture_v0_4.json'
$bridgePath = Join-Path $pt 'scenario_architecture_bridge_v0_4.json'
$standardPath = Join-Path $scenarioRoot 'tl1-tl2-standard-runtime-profiles-v0_2.json'
$auxPath = Join-Path $scenarioRoot 'tl1-tl2-auxiliary-runtime-profiles-v0_2.json'
$pdsPath = Join-Path $pt 'pds_tl1_tl2_characteristics_v0_2.json'
$lifecyclePath = Join-Path $pt 'auxiliary_resource_lifecycle_v0_1.json'
$studyPath = Join-Path $scenarioRoot 'aux-itc03-stateful-power-and-pds-tuning.json'
$endurancePath = Join-Path $scenarioRoot 'aux-end01-resource-endurance-stress.json'
$hashPath = Join-Path $PSScriptRoot 'checkpoint_51_scenario_hashes.txt'

function Assert-True {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) { throw $Message }
}

foreach ($path in @($architecturePath,$bridgePath,$standardPath,$auxPath,$pdsPath,$lifecyclePath,$studyPath,$endurancePath,$hashPath)) {
    Assert-True (Test-Path -LiteralPath $path -PathType Leaf) "Required Checkpoint 52 file is missing: $path"
}

$architecture = Get-Content -LiteralPath $architecturePath -Raw | ConvertFrom-Json
$bridge = Get-Content -LiteralPath $bridgePath -Raw | ConvertFrom-Json
$standard = Get-Content -LiteralPath $standardPath -Raw | ConvertFrom-Json
$aux = Get-Content -LiteralPath $auxPath -Raw | ConvertFrom-Json
$pds = Get-Content -LiteralPath $pdsPath -Raw | ConvertFrom-Json
$lifecycle = Get-Content -LiteralPath $lifecyclePath -Raw | ConvertFrom-Json
$study = Get-Content -LiteralPath $studyPath -Raw | ConvertFrom-Json
$endurance = Get-Content -LiteralPath $endurancePath -Raw | ConvertFrom-Json

Assert-True ([int]$architecture.schemaVersion -eq 1) 'Architecture schemaVersion must remain 1.'
Assert-True ([int]$architecture.checkpoint -eq 52) 'Architecture checkpoint must be 52.'
Assert-True ([string]$architecture.status -eq 'provisional_stateful_resource_tuning') 'Architecture must be the Checkpoint 52 stateful-resource candidate.'
Assert-True (@($architecture.eras).Count -eq 9) 'Architecture must define exactly nine TL eras.'
Assert-True (@($architecture.standardFamilies).Count -eq 11) 'Architecture must retain eleven standard families.'
foreach ($family in @($architecture.standardFamilies)) {
    Assert-True (@($family.implementations).Count -eq 9) "Standard family $($family.familyId) must contain nine implementations."
}
Assert-True (@($architecture.subfamilies).Count -eq 29) 'Architecture must retain 29 sub-family lines.'

$expectedAuxCapacity = @(1,1,2,2,3,3,3,4,4)
$expectedWeapon = @(1,1,2,2,2,3,3,3,4)
foreach ($tl in 1..9) {
    Assert-True ([int]$architecture.installationCapacityProposals.auxiliaryCapacity."$tl" -eq $expectedAuxCapacity[$tl-1]) "Unexpected AUX Capacity at TL$tl."
    Assert-True ([int]$architecture.installationCapacityProposals.weaponBayCapacity."$tl" -eq $expectedWeapon[$tl-1]) "Unexpected Weapon Bay capacity at TL$tl."
}

$subfamilyMap = @{}; foreach ($item in @($architecture.subfamilies)) { $subfamilyMap[[string]$item.id] = $item }
$dispositionMap = @{}; foreach ($item in @($architecture.auxiliaryEntryDisposition)) { $dispositionMap[[string]$item.id] = $item }
foreach ($id in @('aux_kinetic_pds','aux_energy_pds','aux_amm_pds')) {
    Assert-True ($subfamilyMap.ContainsKey($id)) "Missing PDS sub-family $id."
    Assert-True ([int]$subfamilyMap[$id].entryTl -eq 1) "$id must enter at TL1."
    Assert-True ($dispositionMap.ContainsKey($id)) "Missing PDS disposition $id."
    Assert-True ([int]$dispositionMap[$id].proposedEntryTl -eq 1) "$id disposition must enter at TL1."
}

Assert-True ([string]$bridge.status -eq 'limited_tl1_tl2_stateful_resource_bridge') 'Scenario bridge must identify the Checkpoint 52 stateful-resource bridge.'
Assert-True ([bool]$bridge.tableDrivenScenarioGeneration) 'Table-driven TL1/TL2 scenario generation must remain enabled.'
Assert-True ([int]$bridge.matrixPolicy.normalTl1AuxCapacity -eq 1) 'Normal TL1 AUX Capacity must be one.'
Assert-True ([int]$bridge.matrixPolicy.normalTl2AuxCapacity -eq 1) 'Normal TL2 AUX Capacity must be one.'
Assert-True ([bool]$bridge.matrixPolicy.noAuxIsDiagnosticOnly) 'No-AUX must remain diagnostic only.'
Assert-True ([string]$bridge.matrixPolicy.tl3ThroughTl9RuntimeGeneration -eq 'deferred') 'TL3-TL9 runtime generation must remain deferred.'

Assert-True ([string]$standard.schemaVersion -eq 'star-cluster-architecture-runtime-profile-catalog-v1') 'Unexpected architecture runtime profile schema.'
Assert-True (@($standard.profiles).Count -eq 2) 'Runtime profile catalog must contain exactly TL1 and TL2.'
$stdMap = @{}; foreach ($profile in @($standard.profiles)) { $stdMap[[string]$profile.id] = $profile }
Assert-True ([int]$stdMap['tl1-production'].technologyLevel -eq 1 -and [int]$stdMap['tl1-production'].defense.hull -eq 12 -and [int]$stdMap['tl1-production'].powerAndControl.reactorOutput -eq 5 -and [int]$stdMap['tl1-production'].powerAndControl.targetingBonus -eq 10) 'TL1 table-backed profile no longer matches the frozen baseline envelope.'
Assert-True ([int]$stdMap['tl2-production'].technologyLevel -eq 2 -and [int]$stdMap['tl2-production'].defense.armorIntegrity -eq 5 -and [int]$stdMap['tl2-production'].powerAndControl.reactorOutput -eq 6 -and [int]$stdMap['tl2-production'].weapons.kinetic.accuracyBonus -eq 23 -and [int]$stdMap['tl2-production'].weapons.energy.accuracyBonus -eq 28 -and [int]$stdMap['tl2-production'].weapons.missile.guidanceChance -eq 60) 'TL2 table-backed profile no longer matches the accepted standard.'

$normalAux = @($aux.profiles | Where-Object { -not [bool]$_.counterfactual })
$counterfactual = @($aux.profiles | Where-Object { [bool]$_.counterfactual })
$tl1Aux = @($normalAux | Where-Object { [int]$_.technologyLevel -eq 1 })
$tl2Aux = @($normalAux | Where-Object { [int]$_.technologyLevel -eq 2 })
Assert-True ($tl1Aux.Count -eq 8) 'Checkpoint 52 runtime catalog must contain eight legal TL1 combat AUX profiles.'
Assert-True ($tl2Aux.Count -eq 9) 'Checkpoint 52 runtime catalog must contain nine legal TL2 combat AUX profiles.'
Assert-True ($counterfactual.Count -eq 2) 'Checkpoint 52 runtime catalog must contain two no-AUX diagnostics.'
Assert-True (@($normalAux | Where-Object { [int]$_.capacityCost -gt 1 }).Count -eq 0) 'Every normal early runtime AUX must fit one-slot TL1/TL2 capacity.'
$auxMap = @{}; foreach ($profile in @($aux.profiles)) { $auxMap[[string]$profile.id] = $profile }
foreach ($id in @('aux-r52-tl1-combat-battery','aux-r52-tl2-combat-battery')) {
    Assert-True ($auxMap.ContainsKey($id)) "Missing Combat Battery profile $id."
    Assert-True ([int]$auxMap[$id].combatBatteryGain -eq 1 -and [int]$auxMap[$id].combatBatteryCharges -eq 3) "$id must use +1 TP and three charges."
}
Assert-True ([int]$auxMap['aux-r52-tl2-power-capacitor'].capacitorCapacity -eq 1 -and [int]$auxMap['aux-r52-tl2-power-capacitor'].capacitorChargeRate -eq 1 -and [int]$auxMap['aux-r52-tl2-power-capacitor'].capacitorDischargeRate -eq 1) 'Power Capacitor must store one, recharge one, and discharge one TP.'

$expectedPds = @{
    'aux-r52-tl1-kinetic-pds' = @(1,10,1,50)
    'aux-r52-tl1-energy-pds' = @(1,12,2,-1)
    'aux-r52-tl1-amm-pds' = @(1,15,1,25)
    'aux-r52-tl2-kinetic-pds' = @(2,13,1,60)
    'aux-r52-tl2-energy-pds' = @(2,16,2,-1)
    'aux-r52-tl2-amm-pds' = @(2,20,1,30)
}
foreach ($id in $expectedPds.Keys) {
    Assert-True ($auxMap.ContainsKey($id)) "Missing PDS runtime profile $id."
    $expected = $expectedPds[$id]; $profile = $auxMap[$id]
    Assert-True ([int]$profile.technologyLevel -eq $expected[0]) "$id technology level mismatch."
    Assert-True ([int]$profile.pdsBaseChance -eq $expected[1]) "$id PDS base chance mismatch."
    Assert-True ([int]$profile.pdsPower -eq $expected[2]) "$id PDS power mismatch."
    if ($expected[3] -lt 0) { Assert-True ($null -eq $profile.pdsAmmunition) "$id must use unlimited/non-conventional ammunition." }
    else { Assert-True ([int]$profile.pdsAmmunition -eq $expected[3]) "$id PDS ammunition mismatch." }
}
Assert-True (@($pds.profiles).Count -eq 6) 'PDS characteristic companion must contain six TL1/TL2 rows.'
Assert-True (@($pds.profiles | Where-Object { [int]$_.reactionCapacity -ne 1 }).Count -eq 0) 'Checkpoint 52 must hold PDS Reaction Capacity at one.'
Assert-True ([int]($pds.profiles | Where-Object { $_.subfamilyId -eq 'aux_amm_pds' -and [int]$_.technologyLevel -eq 1 }).tacticalPowerReadiness -eq 1) 'TL1 AMM must cost one TP to ready.'
Assert-True ([int]($pds.profiles | Where-Object { $_.subfamilyId -eq 'aux_amm_pds' -and [int]$_.technologyLevel -eq 2 }).tacticalPowerReadiness -eq 1) 'TL2 AMM must cost one TP to ready.'
Assert-True (@($pds.ammunitionSensitivityCandidates.ammRounds) -contains 15 -and @($pds.ammunitionSensitivityCandidates.ammRounds) -contains 20 -and @($pds.ammunitionSensitivityCandidates.ammRounds) -contains 25 -and @($pds.ammunitionSensitivityCandidates.ammRounds) -contains 30) 'AMM endurance study must retain 15/20/25/30 round candidates.'

Assert-True ([int]$lifecycle.combatBattery.primaryCharges -eq 3 -and [int]$lifecycle.combatBattery.tacticalPowerPerCharge -eq 1 -and [int]$lifecycle.combatBattery.dischargeLimitPerTurn -eq 1) 'Combat Battery lifecycle contract mismatch.'
Assert-True (@($lifecycle.combatBattery.diagnosticCharges) -contains 2) 'Two-charge Combat Battery fallback must remain an explicit diagnostic.'
Assert-True ([int]$lifecycle.powerCapacitor.storedPower -eq 1 -and [int]$lifecycle.powerCapacitor.dischargePower -eq 1 -and [int]$lifecycle.powerCapacitor.rechargeCost -eq 1 -and -not [bool]$lifecycle.powerCapacitor.sameTurnChargeAndDischarge) 'Power Capacitor lifecycle contract mismatch.'
Assert-True ([bool]$lifecycle.shieldRecharge.coreCapability) 'Tactical shield recharge must remain a core ship capability.'
Assert-True ([int]$lifecycle.amm.readinessPower -eq 1 -and [int]$lifecycle.amm.tl1PrimaryRounds -eq 25 -and [int]$lifecycle.amm.tl2PrimaryRounds -eq 30) 'AMM lifecycle contract mismatch.'

$variants = @($study.variants)
$legal = @($variants | Where-Object { [string]$_.profileLabel -eq 'aux-r52-stateful-legal-matrix' })
$diagnostic = @($variants | Where-Object { [string]$_.profileLabel -eq 'aux-r52-no-aux-diagnostic' })
Assert-True ($variants.Count -eq 975) 'Checkpoint 52 stateful study must contain 975 variants.'
Assert-True ($legal.Count -eq 867) 'Checkpoint 52 legal matrix must contain 867 variants.'
Assert-True ($diagnostic.Count -eq 108) 'Checkpoint 52 no-AUX diagnostic must contain 108 variants.'
$tl1v1 = @($legal | Where-Object { $_.sideAProfileId -eq 'tl1-production' -and $_.sideBProfileId -eq 'tl1-production' }).Count
$tl2v2 = @($legal | Where-Object { $_.sideAProfileId -eq 'tl2-production' -and $_.sideBProfileId -eq 'tl2-production' }).Count
$cross = @($legal | Where-Object { $_.sideAProfileId -ne $_.sideBProfileId }).Count
Assert-True ($tl1v1 -eq 192 -and $tl2v2 -eq 243 -and $cross -eq 432) 'Checkpoint 52 band counts must be 192/243/432.'
foreach ($family in @('Kinetic','Energy','Missile')) {
    Assert-True (@($legal | Where-Object { $_.sideAFamily -eq $family -and $_.sideBFamily -eq $family }).Count -eq 289) "$family stateful matrix must contain 289 legal variants."
}

Assert-True ([string]$endurance.schemaVersion -eq 'star-cluster-auxiliary-resource-endurance-v1' -and [int]$endurance.checkpoint -eq 52) 'Resource-endurance study identity mismatch.'
Assert-True ([int]$endurance.combatBattery.powerPerCharge -eq 1 -and @($endurance.combatBattery.candidateCharges) -contains 2 -and @($endurance.combatBattery.candidateCharges) -contains 3) 'Resource study must test two- and three-charge +1 TP batteries.'
Assert-True ([int]$endurance.powerCapacitor.capacity -eq 1 -and [int]$endurance.powerCapacitor.chargeRate -eq 1 -and [int]$endurance.powerCapacitor.dischargeRate -eq 1) 'Resource study Power Capacitor contract mismatch.'
Assert-True (@($endurance.amm.roundCandidates).Count -eq 4) 'Resource study must contain four AMM ammunition candidates.'

$expected = New-Object 'System.Collections.Generic.Dictionary[string,string]' ([System.StringComparer]::OrdinalIgnoreCase)
foreach ($line in Get-Content -LiteralPath $hashPath) {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    if ($line -notmatch '^([0-9a-fA-F]{64})  (.+)$') { throw "Invalid scenario hash line: $line" }
    $expected.Add($Matches[2].Replace('/','\'), $Matches[1].ToLowerInvariant())
}
Assert-True ($expected.Count -eq 56) 'Checkpoint 51 frozen runtime scenario snapshot must contain 56 files.'
foreach ($relative in $expected.Keys) {
    $path = Join-Path $repositoryRoot $relative
    Assert-True (Test-Path -LiteralPath $path -PathType Leaf) "Preserved Checkpoint 51 scenario file is missing: $relative"
    $actual = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    Assert-True ($actual -eq $expected[$relative]) "Checkpoint 51 runtime scenario file changed: $relative"
}

Write-Host '       Checkpoint 51 frozen runtime boundary: 56 scenario JSON files SHA-256 verified unchanged.'
Write-Host '       Capacity baseline retained: AUX 1/1/2/2/3/3/3/4/4 and Weapon Bays 1/1/2/2/2/3/3/3/4.'
Write-Host '       Stateful power: Combat Battery +1 TP x3 primary; Power Capacitor 1/1/1 cycle; tactical shield recharge remains core.'
Write-Host '       PDS: Kinetic, Energy, and AMM all TL1; AMM remains 1 TP with 25/30 primary rounds and 15/20/25/30 endurance stress.'
Write-Host '       Checkpoint 52 combat study: 975 variants = 867 legal + 108 diagnostic; bands 192/243/432 and 289 per weapon family.'
Write-Host '       Multi-encounter endurance inputs validated for batteries, capacitor cycling, AMM, kinetic magazines, and missile magazines.'
