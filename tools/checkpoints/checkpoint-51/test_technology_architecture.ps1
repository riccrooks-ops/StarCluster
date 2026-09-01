[CmdletBinding()]
param()

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$architecturePath = Join-Path $repositoryRoot 'docs\design\player_technology\player_technology_architecture_v0_3.json'
$bridgePath = Join-Path $repositoryRoot 'docs\design\player_technology\scenario_architecture_bridge_v0_3.json'
$standardPath = Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\Scenarios\ArchitectureTechnology\tl1-tl2-standard-runtime-profiles-v0_1.json'
$auxPath = Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\Scenarios\ArchitectureTechnology\tl1-tl2-auxiliary-runtime-profiles-v0_1.json'
$pdsPath = Join-Path $repositoryRoot 'docs\design\player_technology\pds_tl1_tl2_characteristics_v0_1.json'
$studyPath = Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\Scenarios\ArchitectureTechnology\aux-itc02-architecture-derived-tl1-tl2-pds.json'
$hashPath = Join-Path $PSScriptRoot 'checkpoint_50_scenario_hashes.txt'

function Assert-True {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) { throw $Message }
}

$architecture = Get-Content -LiteralPath $architecturePath -Raw | ConvertFrom-Json
$bridge = Get-Content -LiteralPath $bridgePath -Raw | ConvertFrom-Json
$standard = Get-Content -LiteralPath $standardPath -Raw | ConvertFrom-Json
$aux = Get-Content -LiteralPath $auxPath -Raw | ConvertFrom-Json
$pds = Get-Content -LiteralPath $pdsPath -Raw | ConvertFrom-Json
$study = Get-Content -LiteralPath $studyPath -Raw | ConvertFrom-Json

Assert-True ([int]$architecture.schemaVersion -eq 1) 'Architecture schemaVersion must be 1.'
Assert-True ([int]$architecture.checkpoint -eq 51) 'Architecture checkpoint must be 51.'
Assert-True ([string]$architecture.status -eq 'provisional_architecture_runtime_bridge') 'Architecture must be the Checkpoint 51 runtime-bridge candidate.'
Assert-True (@($architecture.eras).Count -eq 9) 'Architecture must define exactly nine TL eras.'
Assert-True (@($architecture.standardFamilies).Count -eq 11) 'Architecture must retain eleven standard families.'
foreach ($family in @($architecture.standardFamilies)) {
    Assert-True (@($family.implementations).Count -eq 9) "Standard family $($family.familyId) must contain nine implementations."
}
Assert-True (@($architecture.subfamilies).Count -eq 29) 'Architecture must define 29 sub-family lines.'

$expectedAuxCapacity = @(1,1,2,2,3,3,3,4,4)
$expectedWeapon = @(1,1,2,2,2,3,3,3,4)
foreach ($tl in 1..9) {
    Assert-True ([int]$architecture.installationCapacityProposals.auxiliaryCapacity."$tl" -eq $expectedAuxCapacity[$tl-1]) "Unexpected AUX Capacity at TL$tl."
    Assert-True ([int]$architecture.installationCapacityProposals.weaponBayCapacity."$tl" -eq $expectedWeapon[$tl-1]) "Unexpected Weapon Bay capacity at TL$tl."
}

$pdsIds = @('aux_kinetic_pds','aux_energy_pds','aux_amm_pds')
$subfamilyMap = @{}
foreach ($item in @($architecture.subfamilies)) { $subfamilyMap[[string]$item.id] = $item }
$dispositionMap = @{}
foreach ($item in @($architecture.auxiliaryEntryDisposition)) { $dispositionMap[[string]$item.id] = $item }
foreach ($id in $pdsIds) {
    Assert-True ($subfamilyMap.ContainsKey($id)) "Missing PDS sub-family $id."
    Assert-True ([int]$subfamilyMap[$id].entryTl -eq 1) "$id must enter at TL1."
    Assert-True ($dispositionMap.ContainsKey($id)) "Missing PDS disposition $id."
    Assert-True ([int]$dispositionMap[$id].proposedEntryTl -eq 1) "$id disposition must enter at TL1."
}

Assert-True ([string]$bridge.status -eq 'limited_tl1_tl2_runtime_bridge') 'Scenario bridge must be the limited TL1/TL2 runtime bridge.'
Assert-True ([bool]$bridge.tableDrivenScenarioGeneration) 'Table-driven TL1/TL2 scenario generation must be enabled.'
Assert-True ([int]$bridge.matrixPolicy.normalTl1AuxCapacity -eq 1) 'Normal TL1 AUX Capacity must be one.'
Assert-True ([int]$bridge.matrixPolicy.normalTl2AuxCapacity -eq 1) 'Normal TL2 AUX Capacity must be one.'
Assert-True ([bool]$bridge.matrixPolicy.noAuxIsDiagnosticOnly) 'No-AUX must remain diagnostic only.'
Assert-True ([string]$bridge.matrixPolicy.tl3ThroughTl9RuntimeGeneration -eq 'deferred') 'TL3-TL9 runtime generation must remain deferred.'

Assert-True ([string]$standard.schemaVersion -eq 'star-cluster-architecture-runtime-profile-catalog-v1') 'Unexpected architecture runtime profile schema.'
Assert-True (@($standard.profiles).Count -eq 2) 'Runtime profile catalog must contain exactly TL1 and TL2.'
$stdMap = @{}; foreach ($profile in @($standard.profiles)) { $stdMap[[string]$profile.id] = $profile }
Assert-True ($stdMap.ContainsKey('tl1-production') -and $stdMap.ContainsKey('tl2-production')) 'Runtime catalog must contain TL1 and TL2 production IDs.'
Assert-True ([int]$stdMap['tl1-production'].technologyLevel -eq 1) 'TL1 production runtime profile must be TL1.'
Assert-True ([int]$stdMap['tl2-production'].technologyLevel -eq 2) 'TL2 production runtime profile must be TL2.'
Assert-True ([int]$stdMap['tl1-production'].defense.hull -eq 12 -and [int]$stdMap['tl1-production'].powerAndControl.reactorOutput -eq 5 -and [int]$stdMap['tl1-production'].powerAndControl.targetingBonus -eq 10) 'TL1 table-backed profile no longer matches the frozen baseline envelope.'
Assert-True ([int]$stdMap['tl2-production'].defense.armorIntegrity -eq 5 -and [int]$stdMap['tl2-production'].powerAndControl.reactorOutput -eq 6 -and [int]$stdMap['tl2-production'].weapons.kinetic.accuracyBonus -eq 23 -and [int]$stdMap['tl2-production'].weapons.energy.accuracyBonus -eq 28 -and [int]$stdMap['tl2-production'].weapons.missile.guidanceChance -eq 60) 'TL2 table-backed profile no longer matches the accepted standard.'

$normalAux = @($aux.profiles | Where-Object { -not [bool]$_.counterfactual })
$counterfactual = @($aux.profiles | Where-Object { [bool]$_.counterfactual })
$tl1Aux = @($normalAux | Where-Object { [int]$_.technologyLevel -eq 1 })
$tl2Aux = @($normalAux | Where-Object { [int]$_.technologyLevel -eq 2 })
Assert-True ($tl1Aux.Count -eq 8) 'Architecture-derived runtime catalog must contain eight legal TL1 combat AUX profiles.'
Assert-True ($tl2Aux.Count -eq 9) 'Architecture-derived runtime catalog must contain nine legal TL2 combat AUX profiles.'
Assert-True ($counterfactual.Count -eq 2) 'Architecture-derived runtime catalog must contain two no-AUX diagnostics.'
Assert-True (@($normalAux | Where-Object { [int]$_.capacityCost -gt 1 }).Count -eq 0) 'Every normal early runtime AUX must fit the one-slot TL1/TL2 capacity.'

$expectedPds = @{
    'aux-r51-tl1-kinetic-pds' = @(1,10,1,50)
    'aux-r51-tl1-energy-pds' = @(1,12,2,-1)
    'aux-r51-tl1-amm-pds' = @(1,15,1,25)
    'aux-r51-tl2-kinetic-pds' = @(2,13,1,60)
    'aux-r51-tl2-energy-pds' = @(2,16,2,-1)
    'aux-r51-tl2-amm-pds' = @(2,20,1,30)
}
$auxMap = @{}; foreach ($profile in @($aux.profiles)) { $auxMap[[string]$profile.id] = $profile }
foreach ($id in $expectedPds.Keys) {
    Assert-True ($auxMap.ContainsKey($id)) "Missing PDS runtime profile $id."
    $expected = $expectedPds[$id]; $profile = $auxMap[$id]
    Assert-True ([int]$profile.technologyLevel -eq $expected[0]) "$id technology level mismatch."
    Assert-True ([int]$profile.pdsBaseChance -eq $expected[1]) "$id PDS base chance mismatch."
    Assert-True ([int]$profile.pdsPower -eq $expected[2]) "$id PDS power mismatch."
    if ($expected[3] -lt 0) {
        Assert-True ($null -eq $profile.pdsAmmunition) "$id must use unlimited/non-conventional ammunition."
    } else {
        Assert-True ([int]$profile.pdsAmmunition -eq $expected[3]) "$id PDS ammunition mismatch."
    }
}
Assert-True (@($pds.profiles).Count -eq 6) 'PDS characteristic companion must contain six TL1/TL2 rows.'
Assert-True (@($pds.profiles | Where-Object { [int]$_.reactionCapacity -ne 1 }).Count -eq 0) 'Checkpoint 51 must hold PDS Reaction Capacity at one.'

$variants = @($study.variants)
$legal = @($variants | Where-Object { [string]$_.profileLabel -eq 'aux-r51-architecture-legal-matrix' })
$diagnostic = @($variants | Where-Object { [string]$_.profileLabel -eq 'aux-r51-no-aux-diagnostic' })
Assert-True ($variants.Count -eq 975) 'Architecture-derived study must contain 975 variants.'
Assert-True ($legal.Count -eq 867) 'Architecture-derived legal matrix must contain 867 variants.'
Assert-True ($diagnostic.Count -eq 108) 'Architecture-derived no-AUX diagnostic must contain 108 variants.'
$tl1v1 = @($legal | Where-Object { $_.sideAProfileId -eq 'tl1-production' -and $_.sideBProfileId -eq 'tl1-production' }).Count
$tl2v2 = @($legal | Where-Object { $_.sideAProfileId -eq 'tl2-production' -and $_.sideBProfileId -eq 'tl2-production' }).Count
$cross = @($legal | Where-Object { $_.sideAProfileId -ne $_.sideBProfileId }).Count
Assert-True ($tl1v1 -eq 192 -and $tl2v2 -eq 243 -and $cross -eq 432) 'Architecture-derived band counts must be 192/243/432.'
foreach ($family in @('Kinetic','Energy','Missile')) {
    $count = @($legal | Where-Object { $_.sideAFamily -eq $family -and $_.sideBFamily -eq $family }).Count
    Assert-True ($count -eq 289) "$family architecture-derived matrix must contain 289 legal variants."
}

$expected = New-Object 'System.Collections.Generic.Dictionary[string,string]' ([System.StringComparer]::OrdinalIgnoreCase)
foreach ($line in Get-Content -LiteralPath $hashPath) {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    if ($line -notmatch '^([0-9a-fA-F]{64})  (.+)$') { throw "Invalid scenario hash line: $line" }
    $expected.Add($Matches[2].Replace('/','\'), $Matches[1].ToLowerInvariant())
}
Assert-True ($expected.Count -eq 53) 'Checkpoint 50 frozen runtime scenario snapshot must contain 53 files.'
foreach ($relative in $expected.Keys) {
    $path = Join-Path $repositoryRoot $relative
    Assert-True (Test-Path -LiteralPath $path -PathType Leaf) "Preserved scenario file is missing: $relative"
    $actual = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    Assert-True ($actual -eq $expected[$relative]) "Checkpoint 50 runtime scenario file changed: $relative"
}

Write-Host '       Checkpoint 50 capacity baseline: AUX 1/1/2/2/3/3/3/4/4 and Weapon Bays 1/1/2/2/2/3/3/3/4 retained.'
Write-Host '       PDS entry floors: Kinetic, Energy, and AMM all TL1; six provisional TL1/TL2 characteristic rows validated.'
Write-Host '       Runtime bridge: 2 standard profiles, 8 TL1 AUX, 9 TL2 AUX, and one-slot capacity validated.'
Write-Host '       Architecture-derived study: 975 variants = 867 legal + 108 diagnostic; bands 192/243/432 and 289 per weapon family.'
Write-Host '       Regression boundary: 53 Checkpoint 50 scenario files SHA-256 verified unchanged.'
