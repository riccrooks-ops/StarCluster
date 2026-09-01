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
function Resolve-RepositoryJson([string]$RelativePath) {
    $normalized = $RelativePath.Replace('/','\')
    return Read-Json (Join-Path $repositoryRoot $normalized)
}
function Get-OptionalProperty($Object, [string]$Name, $Default = $null) {
    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) { return $Default }
    return $property.Value
}

$architecture = Read-Json (Join-Path $pt 'player_technology_architecture_v0_6.json')
$schema = Read-Json (Join-Path $pt 'player_technology_architecture_schema_v0_6.json')
$bridge = Read-Json (Join-Path $pt 'scenario_architecture_bridge_v0_6.json')
$standard = Read-Json (Join-Path $scenarioRoot 'tl1-tl3-standard-runtime-profiles-v0_1.json')
$aux = Read-Json (Join-Path $scenarioRoot 'tl3-auxiliary-capacity2-loadouts-v0_1.json')
$profileStudy = Read-Json (Join-Path $scenarioRoot 'tl3-itc01-standard-profile-screening.json')
$twoBayStudy = Read-Json (Join-Path $scenarioRoot 'tl3-itc02-two-bay-loadout-screening.json')
$auxStudy = Read-Json (Join-Path $scenarioRoot 'tl3-aux01-two-capacity-loadout-screening.json')
$powerStudy = Read-Json (Join-Path $scenarioRoot 'tl3-pwr01-two-bay-power-envelope.json')
$weaponInventory = Read-Json (Join-Path $pt 'checkpoint_54_tl3_weapon_loadouts_v0_1.json')
$auxInventory = Read-Json (Join-Path $pt 'checkpoint_54_tl3_auxiliary_loadout_inventory_v0_1.json')
$profileCompanion = Read-Json (Join-Path $pt 'checkpoint_54_tl3_runtime_profile_candidates_v0_1.json')
$checkpoint = Read-Json (Join-Path $repositoryRoot 'tools\calibration\checkpoints\checkpoint-54a.json')

Assert-True ([int]$architecture.checkpoint -eq 54) 'Architecture must identify Checkpoint 54.'
Assert-True ([string]$architecture.status -eq 'provisional_tl3_candidate_screening') 'Architecture status mismatch.'
Assert-True ([int]$schema.properties.checkpoint.const -eq 54) 'Architecture schema must identify Checkpoint 54.'
Assert-True ([int]$bridge.checkpoint -eq 54) 'Scenario bridge must identify Checkpoint 54.'
Assert-True ([string]$bridge.status -eq 'tl1_tl2_frozen_tl3_candidate_screening_bridge') 'Scenario bridge status mismatch.'
Assert-True ([int]$bridge.matrixPolicy.normalTl3AuxCapacity -eq 2) 'Normal TL3 AUX Capacity must be two.'
Assert-True ([int]$bridge.matrixPolicy.normalTl3WeaponBays -eq 2) 'Normal TL3 Weapon Bay Capacity must be two.'
Assert-True ([string]$bridge.matrixPolicy.tl3RuntimeGeneration -eq 'candidate_screening_enabled') 'TL3 candidate screening must be enabled.'
Assert-True ([string]$bridge.matrixPolicy.tl4ThroughTl9RuntimeGeneration -eq 'deferred') 'TL4-TL9 runtime generation must remain deferred.'

$capacity = $architecture.installationCapacityProposals
Assert-True ([int]$capacity.weaponBayCapacity.'3' -eq 2) 'Architecture TL3 Weapon Bay Capacity must be two.'
Assert-True ([int]$capacity.auxiliaryCapacity.'3' -eq 2) 'Architecture TL3 AUX Capacity must be two.'

Assert-True (@($standard.profiles).Count -eq 5) 'TL1-TL3 standard catalog must contain five profiles.'
$tl1 = Find-ById $standard.profiles 'tl1-production'
$tl2 = Find-ById $standard.profiles 'tl2-production'
$control = Find-ById $standard.profiles 'tl3-capacity-control'
$balanced = Find-ById $standard.profiles 'tl3-balanced-candidate'
$output = Find-ById $standard.profiles 'tl3-output-forward-control'
Assert-True ($null -ne $tl1 -and $null -ne $tl2 -and $null -ne $control -and $null -ne $balanced -and $null -ne $output) 'Required standard profiles missing.'
Assert-True ([int]$tl1.technologyLevel -eq 1 -and [int]$tl2.technologyLevel -eq 2) 'Frozen TL1/TL2 profile levels changed.'
Assert-True ([int]$control.technologyLevel -eq 3 -and [int]$balanced.technologyLevel -eq 3 -and [int]$output.technologyLevel -eq 3) 'All TL3 candidates must identify TL3.'
Assert-True ([int]$control.defense.hull -eq [int]$tl2.defense.hull -and [int]$control.powerAndControl.reactorOutput -eq [int]$tl2.powerAndControl.reactorOutput) 'Capacity-control profile must retain TL2 standard values.'
Assert-True ([int]$balanced.powerAndControl.reactorOutput -eq 8 -and [int]$balanced.powerAndControl.targetingBonus -eq 14) 'Balanced TL3 candidate control values mismatch.'
Assert-True ([int]$output.powerAndControl.reactorOutput -eq 9 -and [int]$output.weapons.energy.damage -eq 4) 'Output-forward TL3 sensitivity vector mismatch.'

$normalAux = @($aux.profiles | Where-Object { -not [bool]$_.counterfactual })
$counterfactualAux = @($aux.profiles | Where-Object { [bool]$_.counterfactual })
Assert-True ($normalAux.Count -eq 13) 'TL3 AUX screening catalog must contain 13 normal loadouts.'
Assert-True ($counterfactualAux.Count -eq 2) 'TL3 AUX screening catalog must contain two no-AUX controls.'
foreach ($p in $normalAux) {
    Assert-True ([int]$p.technologyLevel -eq 3) "Normal TL3 AUX profile has wrong TL: $($p.id)"
    Assert-True ([int]$p.capacityCost -eq 2) "Normal TL3 AUX profile must consume exactly two capacity: $($p.id)"
}
Assert-True ($null -ne (Find-ById $normalAux 'aux-r54-auxiliary-reactor')) 'TL3 Auxiliary Reactor candidate missing.'
Assert-True ([int](Find-ById $normalAux 'aux-r54-auxiliary-reactor').auxiliaryReactorOutput -eq 1) 'Auxiliary Reactor must provide +1 renewable TP.'
Assert-True ([int](Find-ById $normalAux 'aux-r54-battery-evasion').combatBatteryCharges -eq 3) 'Combat Battery composite must preserve three charges.'
Assert-True ([int](Find-ById $normalAux 'aux-r54-missile-mag-amm').pdsAmmunition -eq 25) 'AMM composite must preserve 25-round reserve.'

Assert-True (@($profileStudy.variants).Count -eq 72) 'TL3 standard-profile study must contain 72 variants.'
Assert-True (@($twoBayStudy.variants).Count -eq 141) 'TL3 two-bay study must contain 141 variants.'
Assert-True (@($auxStudy.variants).Count -eq 585) 'TL3 two-AUX study must contain 585 variants.'
Assert-True (@($powerStudy.variants).Count -eq 72) 'TL3 power-envelope study must contain 72 variants.'

foreach ($v in @($profileStudy.variants)) {
    Assert-True ($null -eq (Get-OptionalProperty $v 'sideASecondaryFamily') -and $null -eq (Get-OptionalProperty $v 'sideBSecondaryFamily')) "Standard-profile isolation may not use a second bay: $($v.id)"
}
foreach ($v in @($twoBayStudy.variants)) {
    if ([string]$v.sideAProfileId -like 'tl3-*') { Assert-True ($null -ne (Get-OptionalProperty $v 'sideASecondaryFamily')) "TL3 side A must use second bay: $($v.id)" }
    if ([string]$v.sideBProfileId -like 'tl3-*') { Assert-True ($null -ne (Get-OptionalProperty $v 'sideBSecondaryFamily')) "TL3 side B must use second bay: $($v.id)" }
    if ([string]$v.sideAProfileId -eq 'tl2-production') { Assert-True ($null -eq (Get-OptionalProperty $v 'sideASecondaryFamily')) "TL2 side A may not use second bay: $($v.id)" }
    if ([string]$v.sideBProfileId -eq 'tl2-production') { Assert-True ($null -eq (Get-OptionalProperty $v 'sideBSecondaryFamily')) "TL2 side B may not use second bay: $($v.id)" }
}
foreach ($v in @($auxStudy.variants)) {
    Assert-True ([string]$v.sideAProfileId -eq 'tl3-balanced-candidate' -and [string]$v.sideBProfileId -eq 'tl3-balanced-candidate') "TL3 AUX study must use balanced standard candidate: $($v.id)"
    Assert-True ($null -ne (Get-OptionalProperty $v 'sideASecondaryFamily') -and $null -ne (Get-OptionalProperty $v 'sideBSecondaryFamily')) "TL3 AUX study must exercise both Weapon Bays: $($v.id)"
}
foreach ($v in @($powerStudy.variants)) {
    Assert-True ($null -ne (Get-OptionalProperty $v 'sideASecondaryFamily') -and $null -ne (Get-OptionalProperty $v 'sideBSecondaryFamily')) "TL3 power study must exercise both Weapon Bays: $($v.id)"
    Assert-True ([int]$v.sideABackgroundTacticalPowerCommitment -in @(0,3)) "Unexpected side A background TP in $($v.id)"
    Assert-True ([int]$v.sideBBackgroundTacticalPowerCommitment -in @(0,3)) "Unexpected side B background TP in $($v.id)"
}

Assert-True (@($weaponInventory.loadouts).Count -eq 9) 'Weapon-loadout companion must contain all nine ordered combinations.'
Assert-True (@($auxInventory.normalLoadouts).Count -eq 13) 'AUX companion must contain 13 curated capacity-2 loadouts.'
Assert-True (@($profileCompanion.candidates).Count -eq 3) 'TL3 runtime profile companion must contain three candidates.'

Assert-True ([string]$checkpoint.checkpointId -eq '54a') 'Checkpoint 54a definition ID mismatch.'
Assert-True (@($checkpoint.stages).Count -eq 35 -and [int]$checkpoint.checkpointMetrics.stageCount -eq 35) 'Checkpoint 54 must contain 35 stages.'
Assert-True ([int]$checkpoint.checkpointMetrics.monteCarloVariantCount -eq 9877 -and [int]$checkpoint.checkpointMetrics.trialsAtDefault -eq 98770000) 'Checkpoint 54 workload metrics mismatch.'
Assert-True ([string]$checkpoint.primaryStudy.id -eq 'tl3-itc02-two-bay-loadout-screening' -and [int]$checkpoint.primaryStudy.variantCount -eq 141) 'Checkpoint 54 primary-study metadata mismatch.'

$hashPath = Join-Path $PSScriptRoot 'checkpoint_53a_scenario_hashes.txt'
Assert-True (Test-Path -LiteralPath $hashPath -PathType Leaf) 'Missing frozen Checkpoint 53a scenario hash list.'
$expected = New-Object 'System.Collections.Generic.Dictionary[string,string]' ([System.StringComparer]::OrdinalIgnoreCase)
foreach ($line in Get-Content -LiteralPath $hashPath) {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    if ($line -notmatch '^([0-9a-fA-F]{64})  (.+)$') { throw "Invalid scenario hash line: $line" }
    $expected.Add($Matches[2].Replace('/','\'), $Matches[1].ToLowerInvariant())
}
Assert-True ($expected.Count -eq 67) 'Checkpoint 53a frozen ScenarioRunner snapshot must contain 67 JSON files.'
foreach ($relative in $expected.Keys) {
    $path = Join-Path $repositoryRoot $relative
    Assert-True (Test-Path -LiteralPath $path -PathType Leaf) "Frozen Checkpoint 53a scenario file missing: $relative"
    $actual = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    Assert-True ($actual -eq $expected[$relative]) "Frozen Checkpoint 53a scenario file changed: $relative"
}

Write-Host '       Checkpoint 53a frozen runtime boundary: 67 ScenarioRunner JSON files SHA-256 verified unchanged.'
Write-Host '       TL3 structural capacity: 2 Weapon Bays and 2 AUX Capacity.'
Write-Host '       TL3 standard screen: 3 candidate vectors; none auto-promoted.'
Write-Host '       TL3 loadouts: all 9 ordered two-bay combinations and 13 curated capacity-2 AUX packages.'
Write-Host '       Checkpoint 54 evidence: 72 profile + 141 two-bay + 585 two-AUX + 72 power-envelope variants.'
Write-Host '       Checkpoint 54a hotfix definition: unchanged 35 stages, 9,877 Monte Carlo variants, 98.77 million default trials.'
