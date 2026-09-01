[CmdletBinding()]
param()

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$architecturePath = Join-Path $repositoryRoot 'docs\design\player_technology\player_technology_architecture_v0_1.json'
$bridgePath = Join-Path $repositoryRoot 'docs\design\player_technology\scenario_architecture_bridge_v0_1.json'
$hashPath = Join-Path $PSScriptRoot 'checkpoint_48_scenario_hashes.txt'

function Assert-True {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) { throw $Message }
}

$architecture = Get-Content -LiteralPath $architecturePath -Raw | ConvertFrom-Json
$bridge = Get-Content -LiteralPath $bridgePath -Raw | ConvertFrom-Json

Assert-True ([int]$architecture.schemaVersion -eq 1) 'Architecture schemaVersion must be 1.'
Assert-True ([int]$architecture.checkpoint -eq 49) 'Architecture checkpoint must be 49.'
Assert-True ([string]$architecture.status -eq 'provisional_architecture') 'Architecture status must remain provisional_architecture.'
Assert-True (@($architecture.eras).Count -eq 9) 'Architecture must define exactly nine TL eras.'
Assert-True ((@($architecture.eras | ForEach-Object { [int]$_.tl } | Sort-Object) -join ',') -eq '1,2,3,4,5,6,7,8,9') 'Architecture eras must cover TL1 through TL9 exactly.'
Assert-True (@($architecture.standardFamilies).Count -eq 11) 'Architecture must retain eleven standard families.'
foreach ($family in @($architecture.standardFamilies)) {
    Assert-True (@($family.implementations).Count -eq 9) "Standard family $($family.familyId) must contain nine implementations."
    Assert-True ((@($family.implementations | ForEach-Object { [int]$_.tl } | Sort-Object) -join ',') -eq '1,2,3,4,5,6,7,8,9') "Standard family $($family.familyId) must cover TL1-TL9."
}

$subfamilies = @($architecture.subfamilies)
Assert-True ($subfamilies.Count -eq 29) 'Architecture must define 29 sub-family lines.'
$ids = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
foreach ($subfamily in $subfamilies) {
    Assert-True ($ids.Add([string]$subfamily.id)) "Duplicate sub-family ID $($subfamily.id)."
    Assert-True ([int]$subfamily.entryTl -ge 1 -and [int]$subfamily.entryTl -le 9) "Invalid entry TL for $($subfamily.id)."
    $milestones = @($subfamily.milestones.PSObject.Properties.Name | Sort-Object {[int]$_})
    Assert-True (($milestones -join ',') -eq '1,2,3,4,5,6,7,8,9') "Sub-family $($subfamily.id) must define TL1-TL9 milestone cells."
}
function Get-Subfamily([string]$Id) { return @($subfamilies | Where-Object { [string]$_.id -eq $Id })[0] }
foreach ($pair in @(
    @('aux_kinetic_pds',1), @('aux_energy_pds',2), @('aux_amm_pds',3),
    @('aux_combat_battery',1), @('aux_shield_battery',3), @('aux_auxiliary_reactor',3),
    @('aux_shield_booster',3), @('aux_power_stabilizer',3), @('aux_shield_hardener',4),
    @('aux_evasive_maneuver_system',1), @('aux_ecm_suite',1), @('aux_eccm_suite',1),
    @('aux_repair_drone_bay',4), @('aux_tractor_projector',4)
)) {
    $sf = Get-Subfamily $pair[0]
    Assert-True ($null -ne $sf -and [int]$sf.entryTl -eq [int]$pair[1]) "Unexpected entry TL for $($pair[0])."
}
$battery = Get-Subfamily 'aux_combat_battery'
Assert-True ([int]$battery.initialEstimate.tacticalPowerPerUse -eq 1 -and [int]$battery.initialEstimate.uses -eq 3) 'TL1 Combat Battery estimate must be +1 Tactical Power for three uses.'
$pdsRules = @($architecture.familyRules.pds)
Assert-True (($pdsRules -join ' ').ToLowerInvariant().Contains('missile flights')) 'PDS rules must include missile flights.'
Assert-True (($pdsRules -join ' ').ToLowerInvariant().Contains('boarding craft')) 'PDS rules must include boarding craft.'
Assert-True (($pdsRules -join ' ').ToLowerInvariant().Contains('cannot attack enemy ships')) 'PDS rules must prohibit standard attacks against enemy ships.'

Assert-True ([string]$bridge.status -eq 'validation_bridge_only') 'Scenario bridge must remain validation-only.'
Assert-True (-not [bool]$bridge.tableDrivenScenarioGeneration) 'Table-driven scenario generation must remain deferred.'
$subfamilyIds = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
foreach ($sf in $subfamilies) { [void]$subfamilyIds.Add([string]$sf.id) }
foreach ($mapping in @($bridge.auxiliaryMappings)) {
    if (-not [bool]$mapping.counterfactual) {
        Assert-True (-not [string]::IsNullOrWhiteSpace([string]$mapping.architectureSubfamilyId)) "Legal mapping $($mapping.scenarioAuxiliaryProfileId) lacks an architecture sub-family."
        Assert-True ($subfamilyIds.Contains([string]$mapping.architectureSubfamilyId)) "Legal mapping $($mapping.scenarioAuxiliaryProfileId) references an unknown architecture sub-family."
    }
}

$expected = New-Object 'System.Collections.Generic.Dictionary[string,string]' ([System.StringComparer]::OrdinalIgnoreCase)
foreach ($line in Get-Content -LiteralPath $hashPath) {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    if ($line -notmatch '^([0-9a-fA-F]{64})  (.+)$') { throw "Invalid scenario hash line: $line" }
    $expected.Add($Matches[2].Replace('/','\'), $Matches[1].ToLowerInvariant())
}
Assert-True ($expected.Count -eq 53) 'Checkpoint 48 scenario hash snapshot must contain 53 files.'
foreach ($relative in $expected.Keys) {
    $path = Join-Path $repositoryRoot $relative
    Assert-True (Test-Path -LiteralPath $path -PathType Leaf) "Preserved scenario file is missing: $relative"
    $actual = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    Assert-True ($actual -eq $expected[$relative]) "Checkpoint 48 scenario file changed: $relative"
}
$scenarioRoot = Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\Scenarios'
$actualFiles = @(Get-ChildItem -LiteralPath $scenarioRoot -File -Recurse | ForEach-Object { $_.FullName.Substring($repositoryRoot.Length + 1) })
Assert-True ($actualFiles.Count -eq $expected.Count) 'Scenario file count differs from the Checkpoint 48 snapshot.'
foreach ($relative in $actualFiles) { Assert-True ($expected.ContainsKey($relative)) "Unexpected scenario file: $relative" }

Write-Host '       Technology architecture: 11 standard families, 29 sub-family lines, and 28 AUX entry dispositions validated.'
Write-Host '       Scenario preservation: 53 Checkpoint 48 scenario files hash-verified; table-driven generation remains deferred.'
