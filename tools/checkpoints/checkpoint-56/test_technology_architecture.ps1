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

$architecture = Read-Json (Join-Path $pt 'player_technology_architecture_v0_8.json')
$schema = Read-Json (Join-Path $pt 'player_technology_architecture_schema_v0_8.json')
$bridge = Read-Json (Join-Path $pt 'scenario_architecture_bridge_v0_8.json')
$capacityReview = Read-Json (Join-Path $pt 'cruiser_installation_capacity_review_v0_2.json')
$standard = Read-Json (Join-Path $scenarioRoot 'tl1-tl3-standard-runtime-profiles-v0_3.json')
$tl3Aux = Read-Json (Join-Path $scenarioRoot 'tl3-auxiliary-capstone-profiles-v0_2.json')
$powerAux = Read-Json (Join-Path $scenarioRoot 'tl3-power-component-sweep-profiles-v0_1.json')
$crossAux = Read-Json (Join-Path $scenarioRoot 'tl2-tl3-production-auxiliary-profiles-v0_1.json')
$checkpoint = Read-Json (Join-Path $repositoryRoot 'tools\calibration\checkpoints\checkpoint-56.json')

Assert-True ([int]$architecture.checkpoint -eq 56) 'Architecture must identify Checkpoint 56.'
Assert-True ([string]$architecture.status -eq 'tl3_defensive_microstep_and_independent_power_aux_screening') 'Architecture status mismatch.'
Assert-True ([int]$schema.properties.checkpoint.const -eq 56) 'Architecture schema must identify Checkpoint 56.'
Assert-True ([int]$bridge.checkpoint -eq 56) 'Scenario bridge must identify Checkpoint 56.'
Assert-True ([string]$bridge.standardProfileCatalog -like '*tl1-tl3-standard-runtime-profiles-v0_3.json') 'Bridge must point to the Checkpoint 56 standard profile catalog.'

$expectedWeapons = @(1,1,1,2,2,2,3,3,3)
$expectedAux = @(1,1,2,2,2,3,3,3,4)
for ($tl = 1; $tl -le 9; $tl++) {
    $key = [string]$tl
    Assert-True ([int]$architecture.installationCapacityProposals.weaponBayCapacity.$key -eq $expectedWeapons[$tl-1]) "Weapon capacity mismatch at TL$tl."
    Assert-True ([int]$architecture.installationCapacityProposals.auxiliaryCapacity.$key -eq $expectedAux[$tl-1]) "AUX capacity mismatch at TL$tl."
    Assert-True ([int]$capacityReview.capacityCurve.weaponBayCapacity.$key -eq $expectedWeapons[$tl-1]) "Capacity review Weapon Bay mismatch at TL$tl."
    Assert-True ([int]$capacityReview.capacityCurve.auxiliaryCapacity.$key -eq $expectedAux[$tl-1]) "Capacity review AUX mismatch at TL$tl."
}
Assert-True ([int]$bridge.matrixPolicy.normalTl3WeaponBays -eq 1) 'TL3 must remain single-main.'
Assert-True ([int]$bridge.matrixPolicy.normalTl3AuxCapacity -eq 2) 'TL3 must have two AUX capacity.'

# Standard profiles: accepted offense-only base plus exactly three one-point defense microsteps.
Assert-True (@($standard.profiles).Count -eq 7) 'Checkpoint 56 standard catalog must contain seven profiles.'
$offense = Find-ById $standard.profiles 'tl3-offense-refinement'
$hull = Find-ById $standard.profiles 'tl3-offense-plus-hull1'
$ai = Find-ById $standard.profiles 'tl3-offense-plus-ai1'
$shield = Find-ById $standard.profiles 'tl3-offense-plus-shield1'
Assert-True ($null -ne $offense -and $null -ne $hull -and $null -ne $ai -and $null -ne $shield) 'Required TL3 microstep profiles are missing.'
Assert-True ([int]$hull.defense.hull -eq ([int]$offense.defense.hull + 1) -and [int]$hull.defense.armorIntegrity -eq [int]$offense.defense.armorIntegrity -and [int]$hull.defense.shieldCapacity -eq [int]$offense.defense.shieldCapacity) 'Hull microstep must change Hull only.'
Assert-True ([int]$ai.defense.armorIntegrity -eq ([int]$offense.defense.armorIntegrity + 1) -and [int]$ai.defense.hull -eq [int]$offense.defense.hull -and [int]$ai.defense.shieldCapacity -eq [int]$offense.defense.shieldCapacity) 'Armor Integrity microstep must change Armor Integrity only.'
Assert-True ([int]$shield.defense.shieldCapacity -eq ([int]$offense.defense.shieldCapacity + 1) -and [int]$shield.defense.hull -eq [int]$offense.defense.hull -and [int]$shield.defense.armorIntegrity -eq [int]$offense.defense.armorIntegrity) 'Shield microstep must change Shield Capacity only.'

# Power profile structure.
$powerProfiles = @($powerAux.profiles)
Assert-True ($powerProfiles.Count -eq 34) 'Checkpoint 56 power catalog must contain 34 profiles including no-AUX diagnostic.'
$ids = @($powerProfiles | ForEach-Object { [string]$_.id })
Assert-True (@($ids | Select-Object -Unique).Count -eq $ids.Count) 'Checkpoint 56 power profile IDs must be unique.'
$atomicIds = @('aux-r56-b3g1','aux-r56-b4g1','aux-r56-b3g2','aux-r56-b4g2','aux-r56-c2d1','aux-r56-c3d1','aux-r56-c2d2','aux-r56-c3d2')
foreach ($id in $atomicIds) {
    $profile = Find-ById $powerProfiles $id
    Assert-True ($null -ne $profile) "Missing atomic power candidate: $id"
    Assert-True ([int]$profile.capacityCost -eq 1 -and @((Get-OptionalProperty $profile 'powerComponents' @())).Count -eq 1) "Atomic power candidate must contain exactly one independent one-slot component: $id"
}
$reactor = Find-ById $powerProfiles 'aux-r56-auxiliary-reactor'
Assert-True ($null -ne $reactor -and [int]$reactor.capacityCost -eq 2 -and [int]$reactor.auxiliaryReactorOutput -eq 1) 'Auxiliary Reactor must remain capacity 2 and +1 sustained TP.'
$capacityTwo = @($powerProfiles | Where-Object { -not [bool]$_.counterfactual -and [int]$_.capacityCost -eq 2 })
Assert-True ($capacityTwo.Count -eq 25) 'Equal-capacity power catalog must contain 25 normal capacity-2 profiles.'
$twoComponent = @($capacityTwo | Where-Object { [string]$_.id -ne 'aux-r56-auxiliary-reactor' })
Assert-True ($twoComponent.Count -eq 24) 'Equal-capacity power catalog must contain 24 two-component alternatives to the Reactor.'
foreach ($profile in $twoComponent) {
    $components = @((Get-OptionalProperty $profile 'powerComponents' @()))
    Assert-True ($components.Count -eq 2) "Two-slot power profile must contain exactly two independent components: $($profile.id)"
    $componentIds = @($components | ForEach-Object { [string]$_.id })
    Assert-True (@($componentIds | Select-Object -Unique).Count -eq 2) "Independent power component IDs must be unique within profile: $($profile.id)"
}
# Explicit characteristic controls.
$b3g1 = (Find-ById $powerProfiles 'aux-r56-b3g1').powerComponents[0]
$b4g1 = (Find-ById $powerProfiles 'aux-r56-b4g1').powerComponents[0]
$b3g2 = (Find-ById $powerProfiles 'aux-r56-b3g2').powerComponents[0]
$b4g2 = (Find-ById $powerProfiles 'aux-r56-b4g2').powerComponents[0]
Assert-True ([int]$b3g1.combatBatteryCharges -eq 3 -and [int]$b3g1.combatBatteryGain -eq 1) 'B3G1 control mismatch.'
Assert-True ([int]$b4g1.combatBatteryCharges -eq 4 -and [int]$b4g1.combatBatteryGain -eq 1) 'B4G1 charge-count candidate mismatch.'
Assert-True ([int]$b3g2.combatBatteryCharges -eq 3 -and [int]$b3g2.combatBatteryGain -eq 2) 'B3G2 magnitude candidate mismatch.'
Assert-True ([int]$b4g2.combatBatteryCharges -eq 4 -and [int]$b4g2.combatBatteryGain -eq 2) 'B4G2 combined candidate mismatch.'
$c2d1 = (Find-ById $powerProfiles 'aux-r56-c2d1').powerComponents[0]
$c3d1 = (Find-ById $powerProfiles 'aux-r56-c3d1').powerComponents[0]
$c2d2 = (Find-ById $powerProfiles 'aux-r56-c2d2').powerComponents[0]
$c3d2 = (Find-ById $powerProfiles 'aux-r56-c3d2').powerComponents[0]
foreach ($c in @($c2d1,$c3d1,$c2d2,$c3d2)) { Assert-True ([int]$c.capacitorChargeRate -eq 1) 'Checkpoint 56 capacitor charge rate must remain 1 for attribution.' }
Assert-True ([int]$c2d1.capacitorCapacity -eq 2 -and [int]$c2d1.capacitorDischargeRate -eq 1) 'C2D1 control mismatch.'
Assert-True ([int]$c3d1.capacitorCapacity -eq 3 -and [int]$c3d1.capacitorDischargeRate -eq 1) 'C3D1 capacity candidate mismatch.'
Assert-True ([int]$c2d2.capacitorCapacity -eq 2 -and [int]$c2d2.capacitorDischargeRate -eq 2) 'C2D2 magnitude candidate mismatch.'
Assert-True ([int]$c3d2.capacitorCapacity -eq 3 -and [int]$c3d2.capacitorDischargeRate -eq 2) 'C3D2 combined candidate mismatch.'

# Complete integrated-combat study envelopes -- fail before ScenarioRunner if anything is omitted.
$baselinePath = Join-Path $pt 'tl1_core_combat_numerical_baseline_v0_1.csv'
$canonicalBaselineHash = (Get-FileHash -LiteralPath $baselinePath -Algorithm SHA256).Hash.ToLowerInvariant()
$canonicalSchema = 'star-cluster-tl1-integrated-tactical-combat-v2'
$entries = @(
    @{ File='tl3-itc04-defensive-microstep-screening.json'; Id='tl3-itc04-defensive-microstep-screening'; Seed=560100; Count=108; Tech='src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/tl1-tl3-standard-runtime-profiles-v0_3.json'; Aux='src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/tl3-auxiliary-capstone-profiles-v0_2.json' },
    @{ File='tl3-aux04-offense-base-two-capacity-screening.json'; Id='tl3-aux04-offense-base-two-capacity-screening'; Seed=560200; Count=585; Tech='src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/tl1-tl3-standard-runtime-profiles-v0_3.json'; Aux='src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/tl3-auxiliary-capstone-profiles-v0_2.json' },
    @{ File='tl3-aux05-shield-breakpoint-screening.json'; Id='tl3-aux05-shield-breakpoint-screening'; Seed=560300; Count=72; Tech='src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/tl1-tl3-standard-runtime-profiles-v0_3.json'; Aux='src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/tl3-auxiliary-capstone-profiles-v0_2.json' },
    @{ File='tl3-aux06-tl2-tl3-production-progression.json'; Id='tl3-aux06-tl2-tl3-production-progression'; Seed=560400; Count=702; Tech='src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/tl1-tl3-standard-runtime-profiles-v0_3.json'; Aux='src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/tl2-tl3-production-auxiliary-profiles-v0_1.json' },
    @{ File='tl3-pwr03-component-characteristic-sweep.json'; Id='tl3-pwr03-component-characteristic-sweep'; Seed=560500; Count=168; Tech='src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/tl1-tl3-standard-runtime-profiles-v0_3.json'; Aux='src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/tl3-power-component-sweep-profiles-v0_1.json' },
    @{ File='tl3-pwr04-equal-capacity-power-loadouts.json'; Id='tl3-pwr04-equal-capacity-power-loadouts'; Seed=560600; Count=360; Tech='src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/tl1-tl3-standard-runtime-profiles-v0_3.json'; Aux='src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/tl3-power-component-sweep-profiles-v0_1.json' }
)
foreach ($entry in $entries) {
    $study = Read-Json (Join-Path $scenarioRoot $entry.File)
    Assert-True ([string](Get-OptionalProperty $study 'schemaVersion' '') -eq $canonicalSchema) "Study schema mismatch: $($entry.Id)"
    Assert-True ([string](Get-OptionalProperty $study 'id' '') -eq [string]$entry.Id) "Study ID mismatch: $($entry.Id)"
    Assert-True ([string](Get-OptionalProperty $study 'baselineSha256' '') -eq $canonicalBaselineHash) "Study baseline hash mismatch: $($entry.Id)"
    Assert-True ([uint64](Get-OptionalProperty $study 'masterSeed' 0) -eq [uint64]$entry.Seed) "Study seed mismatch: $($entry.Id)"
    Assert-True ([int](Get-OptionalProperty $study 'trialsPerVariant' 0) -eq 10000) "Study default trials mismatch: $($entry.Id)"
    Assert-True ([string](Get-OptionalProperty $study 'technologyProfileCatalog' '') -eq [string]$entry.Tech) "Study technology catalog mismatch: $($entry.Id)"
    Assert-True ([string](Get-OptionalProperty $study 'auxiliaryProfileCatalog' '') -eq [string]$entry.Aux) "Study auxiliary catalog mismatch: $($entry.Id)"
    $variants = @((Get-OptionalProperty $study 'variants' @()))
    Assert-True ($variants.Count -eq [int]$entry.Count) "Study variant count mismatch: $($entry.Id)"
    foreach ($v in $variants) {
        Assert-True ($null -eq (Get-OptionalProperty $v 'sideASecondaryFamily') -and $null -eq (Get-OptionalProperty $v 'sideBSecondaryFamily')) "Checkpoint 56 variant may not install a second main weapon: $($v.id)"
    }
}

Assert-True (@($crossAux.profiles | Where-Object { [int]$_.technologyLevel -eq 2 -and -not [bool]$_.counterfactual }).Count -eq 9) 'Cross-TL catalog must expose nine legal TL2 one-AUX profiles.'
Assert-True (@($crossAux.profiles | Where-Object { [int]$_.technologyLevel -eq 3 -and -not [bool]$_.counterfactual -and [int]$_.capacityCost -eq 2 }).Count -eq 13) 'Cross-TL catalog must expose thirteen legal TL3 two-AUX profiles.'

Assert-True ([string]$checkpoint.checkpointId -eq '56') 'Checkpoint definition ID mismatch.'
Assert-True (@($checkpoint.stages).Count -eq 45 -and [int]$checkpoint.checkpointMetrics.stageCount -eq 45) 'Checkpoint 56 must contain 45 stages.'
Assert-True ([int]$checkpoint.checkpointMetrics.monteCarloVariantCount -eq 12691 -and [int]$checkpoint.checkpointMetrics.trialsAtDefault -eq 126910000) 'Checkpoint 56 workload metrics mismatch.'
Assert-True ([string]$checkpoint.primaryStudy.id -eq 'tl3-itc04-defensive-microstep-screening' -and [int]$checkpoint.primaryStudy.variantCount -eq 108) 'Checkpoint 56 primary study metadata mismatch.'

# Frozen accepted Checkpoint 55b ScenarioRunner JSON boundary.
$hashPath = Join-Path $PSScriptRoot 'checkpoint_55b_scenario_hashes.txt'
Assert-True (Test-Path -LiteralPath $hashPath -PathType Leaf) 'Missing frozen Checkpoint 55b scenario hash list.'
$expected = New-Object 'System.Collections.Generic.Dictionary[string,string]' ([System.StringComparer]::OrdinalIgnoreCase)
foreach ($line in Get-Content -LiteralPath $hashPath) {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    if ($line -notmatch '^([0-9a-fA-F]{64})  (.+)$') { throw "Invalid scenario hash line: $line" }
    $expected.Add($Matches[2].Replace('/','\'), $Matches[1].ToLowerInvariant())
}
Assert-True ($expected.Count -eq 79) 'Checkpoint 55b frozen ScenarioRunner snapshot must contain 79 JSON files.'
foreach ($relative in $expected.Keys) {
    $path = Join-Path $repositoryRoot $relative
    Assert-True (Test-Path -LiteralPath $path -PathType Leaf) "Frozen Checkpoint 55b scenario file missing: $relative"
    $actual = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    Assert-True ($actual -eq $expected[$relative]) "Frozen Checkpoint 55b scenario file changed: $relative"
}

Write-Host '       Checkpoint 55b frozen runtime boundary: 79 ScenarioRunner JSON files SHA-256 verified unchanged.'
Write-Host '       TL3 working base: offense-only refinement; Hull/Armor Integrity/Shield microsteps screened independently.'
Write-Host '       Power AUX: per-installation independent state; 8 atomic candidates; 24 independent two-component capacity-2 alternatives plus Auxiliary Reactor.'
Write-Host '       Checkpoint 56: 45 stages; 12,691 Monte Carlo variants; 126.91 million default trials.'
