[CmdletBinding()]
param()

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$pt = Join-Path $repositoryRoot 'docs\design\player_technology'
$scenarioRoot = Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\Scenarios\ArchitectureTechnology'

function Assert-True([bool]$Condition, [string]$Message) { if (-not $Condition) { throw $Message } }
function Read-Json([string]$Path) { Assert-True (Test-Path -LiteralPath $Path -PathType Leaf) "Missing JSON file: $Path"; return (Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json) }
function Find-ById($Items, [string]$Id) { foreach ($item in @($Items)) { if ([string]$item.id -eq $Id) { return $item } }; return $null }
function Get-OptionalProperty($Object, [string]$Name, $Default = $null) { $property = $Object.PSObject.Properties[$Name]; if ($null -eq $property) { return $Default }; return $property.Value }

$architecture = Read-Json (Join-Path $pt 'player_technology_architecture_v0_10.json')
$schema = Read-Json (Join-Path $pt 'player_technology_architecture_schema_v0_10.json')
$bridge = Read-Json (Join-Path $pt 'scenario_architecture_bridge_v0_10.json')
$standard = Read-Json (Join-Path $scenarioRoot 'tl1-tl4-standard-runtime-profiles-v0_2.json')
$aux = Read-Json (Join-Path $scenarioRoot 'tl3-tl4-production-auxiliary-profiles-v0_2.json')
$checkpoint = Read-Json (Join-Path $repositoryRoot 'tools\calibration\checkpoints\checkpoint-58.json')

Assert-True ([int]$architecture.checkpoint -eq 58) 'Architecture must identify Checkpoint 58.'
Assert-True ([string]$architecture.status -eq 'tl1_tl3_frozen_single_main_tl4_subsystem_foundation_screening') 'Architecture status mismatch.'
Assert-True ([int]$schema.properties.checkpoint.const -eq 58) 'Architecture schema must identify Checkpoint 58.'
Assert-True ([int]$bridge.checkpoint -eq 58) 'Scenario bridge must identify Checkpoint 58.'
Assert-True ([int]$bridge.matrixPolicy.standardPlayerWeaponBaysAllTl -eq 1) 'Standard player cruiser must remain one-main at every TL.'
Assert-True ([int]$bridge.matrixPolicy.normalTl4WeaponBays -eq 1 -and [int]$bridge.matrixPolicy.normalTl4AuxiliaryCapacity -eq 2) 'TL4 foundation must be one main / two AUX.'
Assert-True (-not [bool]$bridge.matrixPolicy.syntheticBackgroundTacticalPower) 'Checkpoint 58 may not add synthetic background Tactical Power.'

$expectedWeapons = @(1,1,1,1,1,1,1,1,1)
$expectedAux = @(1,1,2,2,2,3,3,3,4)
for ($tl = 1; $tl -le 9; $tl++) {
    $key = [string]$tl
    Assert-True ([int]$architecture.installationCapacityProposals.weaponBayCapacity.$key -eq $expectedWeapons[$tl-1]) "Weapon capacity mismatch at TL$tl."
    Assert-True ([int]$architecture.installationCapacityProposals.auxiliaryCapacity.$key -eq $expectedAux[$tl-1]) "AUX capacity mismatch at TL$tl."
}

$tl3 = Find-ById $standard.profiles 'tl3-production'
$control = Find-ById $standard.profiles 'tl4-single-control'
Assert-True ($null -ne $tl3 -and $null -ne $control) 'Frozen TL3 or TL4 control profile missing.'
foreach ($section in @('defense','powerAndControl','movement','weapons')) {
    Assert-True (($tl3.$section | ConvertTo-Json -Depth 20 -Compress) -eq ($control.$section | ConvertTo-Json -Depth 20 -Compress)) "TL4 control must copy TL3 $section statistics exactly."
}
$axisIds = @('tl4-single-control','tl4-fire-control-foundation','tl4-output-power-foundation','tl4-reactor-foundation','tl4-structure-foundation','tl4-armor-protection-foundation','tl4-shield-foundation','tl4-mobility-foundation')
$packageIds = @('tl4-package-firecontrol-reactor','tl4-package-firepower-reactor','tl4-package-structure-reactor','tl4-package-firepower-structure-reactor','tl4-package-firepower-ap-reactor','tl4-package-firepower-mobility-reactor')
foreach ($id in @($axisIds + $packageIds)) { Assert-True ($null -ne (Find-ById $standard.profiles $id)) "Missing Checkpoint 58 technology profile: $id" }

# Higher-output weapons pay +1 Tactical Power for the +1 damage candidate.
$output = Find-ById $standard.profiles 'tl4-output-power-foundation'
Assert-True ([int]$output.weapons.kinetic.damage -eq 5 -and [int]$output.weapons.kinetic.power -eq 2) 'TL4 Kinetic output/power candidate mismatch.'
Assert-True ([int]$output.weapons.energy.damage -eq 4 -and [int]$output.weapons.energy.power -eq 3) 'TL4 Energy output/power candidate mismatch.'
Assert-True ([int]$output.weapons.missile.damage -eq 6 -and [int]$output.weapons.missile.power -eq 1) 'TL4 Missile output/power candidate mismatch.'

$hardenerIds = @('aux-r58-shield-hardener-s1-p1','aux-r58-shield-hardener-s1-p2','aux-r58-shield-hardener-s2-p2')
$energizedIds = @('aux-r58-energized-armor-a1-p1','aux-r58-energized-armor-a1-p2','aux-r58-energized-armor-a2-p2')
$mixedIds = @('aux-r58-shield-hardener-battery','aux-r58-shield-hardener-capacitor','aux-r58-energized-armor-battery','aux-r58-energized-armor-capacitor')
foreach ($id in @($hardenerIds + $energizedIds + $mixedIds)) {
    $p = Find-ById $aux.profiles $id
    Assert-True ($null -ne $p) "Missing Checkpoint 58 powered-defense AUX: $id"
    Assert-True ([int]$p.capacityCost -ge 1 -and [int]$p.capacityCost -le 2) "Invalid Checkpoint 58 AUX capacity: $id"
}
foreach ($id in $hardenerIds) {
    $p = Find-ById $aux.profiles $id
    Assert-True ([int](Get-OptionalProperty $p 'shieldHardenerStrength' 0) -gt 0 -and [int](Get-OptionalProperty $p 'shieldHardenerPower' 0) -gt 0) "Shield Hardener effect/power missing: $id"
}
foreach ($id in $energizedIds) {
    $p = Find-ById $aux.profiles $id
    Assert-True ([int](Get-OptionalProperty $p 'energizedArmorProtectionBonus' 0) -gt 0 -and [int](Get-OptionalProperty $p 'energizedArmorPower' 0) -gt 0) "Energized Armor effect/power missing: $id"
}
foreach ($id in $mixedIds) {
    $p = Find-ById $aux.profiles $id
    $pcs = @((Get-OptionalProperty $p 'powerComponents' @()))
    Assert-True ($pcs.Count -eq 1) "Mixed powered-defense AUX must contain exactly one independent compact power component: $id"
    Assert-True ([int]$p.capacityCost -eq 2) "Mixed powered-defense AUX must use the full two-AUX budget: $id"
}

$baselinePath = Join-Path $pt 'tl1_core_combat_numerical_baseline_v0_1.csv'
$canonicalBaselineHash = (Get-FileHash -LiteralPath $baselinePath -Algorithm SHA256).Hash.ToLowerInvariant()
$canonicalSchema = 'star-cluster-tl1-integrated-tactical-combat-v2'
$entries = @(
    @{ File='tl4-itc04-single-main-axis-screening.json'; Id='tl4-itc04-single-main-axis-screening'; Seed=580100; Count=144 },
    @{ File='tl4-itc05-foundation-package-screening.json'; Id='tl4-itc05-foundation-package-screening'; Seed=580200; Count=108 },
    @{ File='tl4-itc06-tl3-specialization-resistance.json'; Id='tl4-itc06-tl3-specialization-resistance'; Seed=580300; Count=468 },
    @{ File='tl4-aux01-powered-defense-isolation.json'; Id='tl4-aux01-powered-defense-isolation'; Seed=580400; Count=36 },
    @{ File='tl4-pwr03-powered-defense-power-pairing.json'; Id='tl4-pwr03-powered-defense-power-pairing'; Seed=580500; Count=60 },
    @{ File='tl4-pwr04-single-main-natural-power.json'; Id='tl4-pwr04-single-main-natural-power'; Seed=580600; Count=84 }
)
foreach ($entry in $entries) {
    $study = Read-Json (Join-Path $scenarioRoot $entry.File)
    Assert-True ([string](Get-OptionalProperty $study 'schemaVersion' '') -eq $canonicalSchema) "Study schema mismatch: $($entry.Id)"
    Assert-True ([string](Get-OptionalProperty $study 'id' '') -eq [string]$entry.Id) "Study ID mismatch: $($entry.Id)"
    Assert-True ([int](Get-OptionalProperty $study 'checkpoint' 0) -eq 58) "Study checkpoint mismatch: $($entry.Id)"
    Assert-True ([string](Get-OptionalProperty $study 'baselineSha256' '') -eq $canonicalBaselineHash) "Study baseline hash mismatch: $($entry.Id)"
    Assert-True ([uint64](Get-OptionalProperty $study 'masterSeed' 0) -eq [uint64]$entry.Seed) "Study seed mismatch: $($entry.Id)"
    Assert-True ([int](Get-OptionalProperty $study 'trialsPerVariant' 0) -eq 10000) "Study default trials mismatch: $($entry.Id)"
    Assert-True ([string](Get-OptionalProperty $study 'technologyProfileCatalog' '') -like '*tl1-tl4-standard-runtime-profiles-v0_2.json') "Study technology catalog mismatch: $($entry.Id)"
    Assert-True ([string](Get-OptionalProperty $study 'auxiliaryProfileCatalog' '') -like '*tl3-tl4-production-auxiliary-profiles-v0_2.json') "Study AUX catalog mismatch: $($entry.Id)"
    $variants = @((Get-OptionalProperty $study 'variants' @()))
    Assert-True ($variants.Count -eq [int]$entry.Count) "Study variant count mismatch: $($entry.Id)"
    foreach ($v in $variants) {
        Assert-True ($null -eq (Get-OptionalProperty $v 'sideASecondaryFamily') -and $null -eq (Get-OptionalProperty $v 'sideBSecondaryFamily')) "Checkpoint 58 second main found: $($v.id)"
        Assert-True ([int](Get-OptionalProperty $v 'sideABackgroundTacticalPowerCommitment' 0) -eq 0 -and [int](Get-OptionalProperty $v 'sideBBackgroundTacticalPowerCommitment' 0) -eq 0) "Synthetic background TP found: $($v.id)"
    }
}

Assert-True ([string]$checkpoint.checkpointId -eq '58') 'Checkpoint 58 definition ID mismatch.'
Assert-True (@($checkpoint.stages).Count -eq 56 -and [int]$checkpoint.checkpointMetrics.stageCount -eq 56) 'Checkpoint 58 must contain 56 stages.'
Assert-True ([int]$checkpoint.checkpointMetrics.monteCarloVariantCount -eq 14746 -and [int]$checkpoint.checkpointMetrics.trialsAtDefault -eq 147460000) 'Checkpoint 58 workload metrics mismatch.'
Assert-True ([string]$checkpoint.primaryStudy.id -eq 'tl4-itc04-single-main-axis-screening' -and [int]$checkpoint.primaryStudy.variantCount -eq 144) 'Checkpoint 58 primary study metadata mismatch.'

# Frozen Checkpoint 57a ScenarioRunner JSON boundary.
$hashPath = Join-Path $PSScriptRoot 'checkpoint_57a_scenario_hashes.txt'
$expected = New-Object 'System.Collections.Generic.Dictionary[string,string]' ([System.StringComparer]::OrdinalIgnoreCase)
foreach ($line in Get-Content -LiteralPath $hashPath) {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    if ($line -notmatch '^([0-9a-fA-F]{64})  (.+)$') { throw "Invalid scenario hash line: $line" }
    $expected.Add($Matches[2].Replace('/','\'), $Matches[1].ToLowerInvariant())
}
Assert-True ($expected.Count -eq 95) 'Checkpoint 57a frozen ScenarioRunner snapshot must contain 95 JSON files.'
foreach ($relative in $expected.Keys) {
    $path = Join-Path $repositoryRoot $relative
    Assert-True (Test-Path -LiteralPath $path -PathType Leaf) "Frozen Checkpoint 57a scenario file missing: $relative"
    $actual = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    Assert-True ($actual -eq $expected[$relative]) "Frozen Checkpoint 57a scenario file changed: $relative"
}

$applySource = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'apply_checkpoint_58.ps1') -Raw
Assert-True (-not ($applySource -match '(?im)^\s*&\s*(python|python3|py)(\.exe)?\b')) 'Checkpoint 58 launcher must not require Python.'
Assert-True ($applySource.Contains('checkpoint-58.json')) 'Checkpoint 58 launcher must use the Checkpoint 58 definition.'

Write-Host '       Checkpoint 57a runtime boundary: 95 ScenarioRunner JSON files SHA-256 verified unchanged.'
Write-Host '       TL1-TL3 frozen; standard player cruiser: one main weapon at every TL; AUX 1/1/2, 2/2/3, 3/3/4.'
Write-Host '       TL4 foundation screen: subsystem capability, natural Tactical Power demand, Shield Hardener, and Energized Armor.'
Write-Host '       Checkpoint 58: 56 stages; 14,746 Monte Carlo variants; 147.46 million default trials.'
