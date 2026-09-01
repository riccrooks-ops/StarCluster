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

$architecture = Read-Json (Join-Path $pt 'player_technology_architecture_v0_9.json')
$schema = Read-Json (Join-Path $pt 'player_technology_architecture_schema_v0_9.json')
$bridge = Read-Json (Join-Path $pt 'scenario_architecture_bridge_v0_9.json')
$standard = Read-Json (Join-Path $scenarioRoot 'tl1-tl4-standard-runtime-profiles-v0_1.json')
$aux = Read-Json (Join-Path $scenarioRoot 'tl3-tl4-production-auxiliary-profiles-v0_1.json')
$checkpoint = Read-Json (Join-Path $repositoryRoot 'tools\calibration\checkpoints\checkpoint-57a.json')

Assert-True ([int]$architecture.checkpoint -eq 57) 'Architecture must identify Checkpoint 57.'
Assert-True ([string]$architecture.status -eq 'tl1_tl3_frozen_tl4_dual_main_foundation_screening') 'Architecture status mismatch.'
Assert-True ([int]$schema.properties.checkpoint.const -eq 57) 'Architecture schema must identify Checkpoint 57.'
Assert-True ([string]$schema.properties.status.const -eq 'tl1_tl3_frozen_tl4_dual_main_foundation_screening') 'Architecture schema status mismatch.'
Assert-True ([int]$bridge.checkpoint -eq 57) 'Scenario bridge must identify Checkpoint 57.'
Assert-True ([int]$bridge.matrixPolicy.normalTl3WeaponBays -eq 1) 'TL3 must remain single-main.'
Assert-True ([int]$bridge.matrixPolicy.normalTl4WeaponBays -eq 2) 'TL4 must screen two unrestricted main weapons.'
Assert-True ([int]$bridge.matrixPolicy.normalTl4AuxiliaryCapacity -eq 2) 'TL4 must retain two AUX Capacity.'
Assert-True (-not [bool]$bridge.matrixPolicy.syntheticBackgroundTacticalPower) 'Checkpoint 57 TL4 studies may not add synthetic background Tactical Power.'

$expectedWeapons = @(1,1,1,2,2,2,3,3,3)
$expectedAux = @(1,1,2,2,2,3,3,3,4)
for ($tl = 1; $tl -le 9; $tl++) {
    $key = [string]$tl
    Assert-True ([int]$architecture.installationCapacityProposals.weaponBayCapacity.$key -eq $expectedWeapons[$tl-1]) "Weapon capacity mismatch at TL$tl."
    Assert-True ([int]$architecture.installationCapacityProposals.auxiliaryCapacity.$key -eq $expectedAux[$tl-1]) "AUX capacity mismatch at TL$tl."
}

$tl3 = Find-ById $standard.profiles 'tl3-production'
$tl4 = Find-ById $standard.profiles 'tl4-foundation-control'
Assert-True ($null -ne $tl3 -and [int]$tl3.technologyLevel -eq 3) 'Accepted TL3 production profile is missing.'
Assert-True ($null -ne $tl4 -and [int]$tl4.technologyLevel -eq 4) 'TL4 foundation profile is missing.'
foreach ($section in @('defense','powerAndControl','movement','weapons')) {
    $a = ($tl3.$section | ConvertTo-Json -Depth 20 -Compress)
    $b = ($tl4.$section | ConvertTo-Json -Depth 20 -Compress)
    Assert-True ($a -eq $b) "TL4 foundation must copy TL3 $section statistics exactly."
}
Assert-True ([int]$tl3.powerAndControl.targetingBonus -eq 13) 'Accepted TL3 targeting bonus must be 13.'
Assert-True ([int]$tl3.weapons.kinetic.accuracyBonus -eq 24) 'Accepted TL3 Kinetic accuracy must be 24.'
Assert-True ([int]$tl3.weapons.energy.accuracyBonus -eq 29) 'Accepted TL3 Energy accuracy must be 29.'
Assert-True ([int]$tl3.weapons.missile.guidanceChance -eq 62) 'Accepted TL3 Missile guidance must be 62.'
Assert-True ([int]$tl3.defense.hull -eq 12 -and [int]$tl3.defense.armorIntegrity -eq 5 -and [int]$tl3.defense.shieldCapacity -eq 2) 'Accepted TL3 must include no defensive integer microstep.'

$battery = Find-ById $aux.profiles 'aux-r57-battery'
$capacitor = Find-ById $aux.profiles 'aux-r57-capacitor'
$reactor = Find-ById $aux.profiles 'aux-r57-reactor'
Assert-True ($null -ne $battery -and [int]$battery.capacityCost -eq 1) 'TL3 production Battery missing.'
Assert-True (@((Get-OptionalProperty $battery 'powerComponents' @())).Count -eq 1) 'TL3 Battery must be one independent component.'
Assert-True ([int]$battery.powerComponents[0].combatBatteryCharges -eq 4 -and [int]$battery.powerComponents[0].combatBatteryGain -eq 1) 'TL3 Battery must be B4G1.'
Assert-True ($null -ne $capacitor -and [int]$capacitor.capacityCost -eq 1) 'TL3 production Capacitor missing.'
Assert-True ([int]$capacitor.powerComponents[0].capacitorCapacity -eq 2 -and [int]$capacitor.powerComponents[0].capacitorChargeRate -eq 1 -and [int]$capacitor.powerComponents[0].capacitorDischargeRate -eq 1) 'TL3 Capacitor must be C2D1.'
Assert-True ($null -ne $reactor -and [int]$reactor.capacityCost -eq 2 -and [int]$reactor.auxiliaryReactorOutput -eq 1) 'TL3 Auxiliary Reactor must remain capacity 2 and +1 sustained TP.'
foreach ($id in @('aux-r57-bb','aux-r57-cc','aux-r57-bc')) {
    $p = Find-ById $aux.profiles $id
    Assert-True ($null -ne $p -and [int]$p.capacityCost -eq 2) "Missing full two-AUX power build: $id"
    $pcs = @((Get-OptionalProperty $p 'powerComponents' @()))
    Assert-True ($pcs.Count -eq 2) "Full power build must contain two independent components: $id"
    Assert-True (@($pcs | ForEach-Object { [string]$_.id } | Select-Object -Unique).Count -eq 2) "Independent component IDs must be unique: $id"
}

$baselinePath = Join-Path $pt 'tl1_core_combat_numerical_baseline_v0_1.csv'
$canonicalBaselineHash = (Get-FileHash -LiteralPath $baselinePath -Algorithm SHA256).Hash.ToLowerInvariant()
$canonicalSchema = 'star-cluster-tl1-integrated-tactical-combat-v2'
$entries = @(
    @{ File='tl4-itc01-foundation-transition.json'; Id='tl4-itc01-foundation-transition'; Seed=570100; Count=180 },
    @{ File='tl4-itc02-two-bay-loadout-screening.json'; Id='tl4-itc02-two-bay-loadout-screening'; Seed=570200; Count=243 },
    @{ File='tl4-itc03-tl3-specialization-resistance.json'; Id='tl4-itc03-tl3-specialization-resistance'; Seed=570300; Count=468 },
    @{ File='tl4-pwr01-natural-two-bay-power.json'; Id='tl4-pwr01-natural-two-bay-power'; Seed=570400; Count=120 },
    @{ File='tl4-pwr02-mixed-power-flexibility.json'; Id='tl4-pwr02-mixed-power-flexibility'; Seed=570500; Count=144 }
)
foreach ($entry in $entries) {
    $study = Read-Json (Join-Path $scenarioRoot $entry.File)
    Assert-True ([string](Get-OptionalProperty $study 'schemaVersion' '') -eq $canonicalSchema) "Study schema mismatch: $($entry.Id)"
    Assert-True ([string](Get-OptionalProperty $study 'id' '') -eq [string]$entry.Id) "Study ID mismatch: $($entry.Id)"
    Assert-True ([int](Get-OptionalProperty $study 'checkpoint' 0) -eq 57) "Study checkpoint mismatch: $($entry.Id)"
    Assert-True ([string](Get-OptionalProperty $study 'baselineSha256' '') -eq $canonicalBaselineHash) "Study baseline hash mismatch: $($entry.Id)"
    Assert-True ([uint64](Get-OptionalProperty $study 'masterSeed' 0) -eq [uint64]$entry.Seed) "Study seed mismatch: $($entry.Id)"
    Assert-True ([int](Get-OptionalProperty $study 'trialsPerVariant' 0) -eq 10000) "Study default trials mismatch: $($entry.Id)"
    Assert-True ([string](Get-OptionalProperty $study 'technologyProfileCatalog' '') -like '*tl1-tl4-standard-runtime-profiles-v0_1.json') "Study technology catalog mismatch: $($entry.Id)"
    Assert-True ([string](Get-OptionalProperty $study 'auxiliaryProfileCatalog' '') -like '*tl3-tl4-production-auxiliary-profiles-v0_1.json') "Study AUX catalog mismatch: $($entry.Id)"
    $variants = @((Get-OptionalProperty $study 'variants' @()))
    Assert-True ($variants.Count -eq [int]$entry.Count) "Study variant count mismatch: $($entry.Id)"
    foreach ($v in $variants) {
        Assert-True ([int](Get-OptionalProperty $v 'sideABackgroundTacticalPowerCommitment' 0) -eq 0 -and [int](Get-OptionalProperty $v 'sideBBackgroundTacticalPowerCommitment' 0) -eq 0) "Synthetic background TP found in: $($v.id)"
        if ($null -ne (Get-OptionalProperty $v 'sideASecondaryFamily')) { Assert-True ([string]$v.sideAProfileId -eq 'tl4-foundation-control') "Non-TL4 second main on Side A: $($v.id)" }
        if ($null -ne (Get-OptionalProperty $v 'sideBSecondaryFamily')) { Assert-True ([string]$v.sideBProfileId -eq 'tl4-foundation-control') "Non-TL4 second main on Side B: $($v.id)" }
    }
}

Assert-True ([string]$checkpoint.checkpointId -eq '57a') 'Checkpoint 57a definition ID mismatch.'
Assert-True (@($checkpoint.stages).Count -eq 50 -and [int]$checkpoint.checkpointMetrics.stageCount -eq 50) 'Checkpoint 57a must contain 50 stages.'
Assert-True ([int]$checkpoint.checkpointMetrics.monteCarloVariantCount -eq 13846 -and [int]$checkpoint.checkpointMetrics.trialsAtDefault -eq 138460000) 'Checkpoint 57a workload metrics mismatch.'
Assert-True ([string]$checkpoint.primaryStudy.id -eq 'tl4-itc01-foundation-transition' -and [int]$checkpoint.primaryStudy.variantCount -eq 180) 'Checkpoint 57a primary study metadata mismatch.'

# Frozen Checkpoint 56 ScenarioRunner JSON boundary.
$hashPath = Join-Path $PSScriptRoot 'checkpoint_56_scenario_hashes.txt'
Assert-True (Test-Path -LiteralPath $hashPath -PathType Leaf) 'Missing frozen Checkpoint 56 scenario hash list.'
$expected = New-Object 'System.Collections.Generic.Dictionary[string,string]' ([System.StringComparer]::OrdinalIgnoreCase)
foreach ($line in Get-Content -LiteralPath $hashPath) {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    if ($line -notmatch '^([0-9a-fA-F]{64})  (.+)$') { throw "Invalid scenario hash line: $line" }
    $expected.Add($Matches[2].Replace('/','\'), $Matches[1].ToLowerInvariant())
}
Assert-True ($expected.Count -eq 88) 'Checkpoint 56 frozen ScenarioRunner snapshot must contain 88 JSON files.'
foreach ($relative in $expected.Keys) {
    $path = Join-Path $repositoryRoot $relative
    Assert-True (Test-Path -LiteralPath $path -PathType Leaf) "Frozen Checkpoint 56 scenario file missing: $relative"
    $actual = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    Assert-True ($actual -eq $expected[$relative]) "Frozen Checkpoint 56 scenario file changed: $relative"
}

# Checkpoint 57a compile/launcher hotfix contract.
$runnerPath = Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\TL1Calibration\Tl1IntegratedTacticalCombatRunner.cs'
$runnerSource = Get-Content -LiteralPath $runnerPath -Raw
$validateStart = $runnerSource.IndexOf('    private static void Validate(')
$validateEnd = $runnerSource.IndexOf('    private static void ValidateTl2CandidateCoverage(', $validateStart)
$buildGatesStart = $runnerSource.IndexOf('    private static IReadOnlyList<Tl1IntegratedTacticalCombatGate> BuildGates(')
$buildGatesEnd = $runnerSource.IndexOf('    private static ', $buildGatesStart + 20)
Assert-True ($validateStart -ge 0 -and $validateEnd -gt $validateStart) 'Unable to locate integrated-combat Validate method.'
Assert-True ($buildGatesStart -ge 0 -and $buildGatesEnd -gt $buildGatesStart) 'Unable to locate integrated-combat BuildGates method.'
$validateBody = $runnerSource.Substring($validateStart, $validateEnd - $validateStart)
$buildGatesBody = $runnerSource.Substring($buildGatesStart, $buildGatesEnd - $buildGatesStart)
Assert-True (-not $validateBody.Contains('tl4-foundation-two-main-telemetry')) 'TL4 result telemetry gate must not execute inside pre-result Validate().' 
Assert-True ($buildGatesBody.Contains('tl4-foundation-two-main-telemetry')) 'TL4 result telemetry gate must execute inside BuildGates().' 
Assert-True ($runnerSource.Contains('v.InitialRangeHexes.HasValue ? v.InitialRangeHexes.Value.ToString(CultureInfo.InvariantCulture) : string.Empty')) 'Nullable InitialRangeHexes formatting hotfix is missing.'
Assert-True (-not $runnerSource.Contains('v.InitialRangeHexes.ToString(CultureInfo.InvariantCulture)')) 'Invalid nullable InitialRangeHexes ToString overload remains.'
$applyPath = Join-Path $PSScriptRoot 'apply_checkpoint_57a.ps1'
$applySource = Get-Content -LiteralPath $applyPath -Raw
Assert-True (-not ($applySource -match '(?im)^\s*&\s*(python|python3|py)(\.exe)?\b')) 'Checkpoint 57a launcher must not require Python.'
Assert-True ($applySource.Contains('checkpoint-57a.json')) 'Checkpoint 57a launcher must use the 57a checkpoint definition.'

Write-Host '       Checkpoint 56 frozen runtime boundary: 88 ScenarioRunner JSON files SHA-256 verified unchanged.'
Write-Host '       TL3 frozen: one main / two AUX; offense-only production; Battery B4G1; Capacitor C2D1.'
Write-Host '       TL4 foundation: two unrestricted main weapons / two AUX; TL3-equivalent component statistics.'
Write-Host '       Checkpoint 57a hotfix: 50 stages; 13,846 Monte Carlo variants; 138.46 million default trials.'
Write-Host '       Compile hotfix: TL4 telemetry gate moved to BuildGates; nullable range formatting corrected; Python launcher dependency removed.'
