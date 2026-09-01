[CmdletBinding()]
param()

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$architecturePath = Join-Path $repositoryRoot 'docs\design\player_technology\player_technology_architecture_v0_2.json'
$reviewPath = Join-Path $repositoryRoot 'docs\design\player_technology\cruiser_installation_capacity_review_v0_1.json'
$bridgePath = Join-Path $repositoryRoot 'docs\design\player_technology\scenario_architecture_bridge_v0_2.json'
$hashPath = Join-Path $PSScriptRoot 'checkpoint_49_scenario_hashes.txt'

function Assert-True {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) { throw $Message }
}

$architecture = Get-Content -LiteralPath $architecturePath -Raw | ConvertFrom-Json
$review = Get-Content -LiteralPath $reviewPath -Raw | ConvertFrom-Json
$bridge = Get-Content -LiteralPath $bridgePath -Raw | ConvertFrom-Json

Assert-True ([int]$architecture.schemaVersion -eq 1) 'Architecture schemaVersion must be 1.'
Assert-True ([int]$architecture.checkpoint -eq 50) 'Architecture checkpoint must be 50.'
Assert-True ([string]$architecture.status -eq 'provisional_architecture') 'Architecture remains provisional pending human acceptance.'
Assert-True (@($architecture.eras).Count -eq 9) 'Architecture must define exactly nine TL eras.'
Assert-True (@($architecture.standardFamilies).Count -eq 11) 'Architecture must retain eleven standard families.'
foreach ($family in @($architecture.standardFamilies)) {
    Assert-True (@($family.implementations).Count -eq 9) "Standard family $($family.familyId) must contain nine implementations."
}
$subfamilies = @($architecture.subfamilies)
Assert-True ($subfamilies.Count -eq 29) 'Architecture must define 29 sub-family lines.'

$expectedAux = @(1,1,2,2,3,3,3,4,4)
$expectedWeapon = @(1,1,2,2,2,3,3,3,4)
foreach ($tl in 1..9) {
    Assert-True ([int]$architecture.installationCapacityProposals.auxiliaryCapacity."$tl" -eq $expectedAux[$tl-1]) "Unexpected AUX Capacity at TL$tl."
    Assert-True ([int]$architecture.installationCapacityProposals.weaponBayCapacity."$tl" -eq $expectedWeapon[$tl-1]) "Unexpected Weapon Bay capacity at TL$tl."
}
Assert-True ([int]$review.historicalScreeningBoundary.checkpoint48Tl2AuxCapacity -eq 2) 'Historical TL2 screening capacity must remain recorded as 2.'
Assert-True ([int]$review.historicalScreeningBoundary.normalTl2CandidateAuxCapacity -eq 1) 'Normal TL2 candidate AUX Capacity must be 1.'

$disposition = @{}
foreach ($item in @($architecture.auxiliaryEntryDisposition)) { $disposition[[string]$item.id] = $item }
Assert-True (@($review.representativeProfiles).Count -eq 18) 'Capacity review must contain 18 representative profiles.'
foreach ($profile in @($review.representativeProfiles)) {
    $tl = [int]$profile.tl
    Assert-True ([int]$profile.weaponBaysUsed -le $expectedWeapon[$tl-1]) "Weapon Bay overfill in $($profile.id)."
    Assert-True ([int]$profile.auxiliaryCapacityUsed -le $expectedAux[$tl-1]) "AUX overfill in $($profile.id)."
    $sum = 0
    foreach ($module in @($profile.auxiliaryModules)) {
        Assert-True ($disposition.ContainsKey([string]$module.id)) "Unknown AUX module $($module.id)."
        Assert-True ($tl -ge [int]$disposition[[string]$module.id].proposedEntryTl) "AUX module $($module.id) is below its proposed entry TL in $($profile.id)."
        $sum += [int]$module.capacityCost
    }
    Assert-True ($sum -eq [int]$profile.auxiliaryCapacityUsed) "AUX capacity sum mismatch in $($profile.id)."
}
Assert-True (@($review.weaponBayStressCases).Count -eq 3) 'Capacity review must contain three multi-bay stress cases.'
foreach ($case in @($review.weaponBayStressCases)) {
    $sum = 0; foreach ($o in @($case.occupancies)) { $sum += [int]$o }
    Assert-True ($sum -eq [int]$case.weaponBaysAvailable) "Weapon occupancy stress case $($case.id) must exactly consume its available bays."
}

Assert-True ([string]$bridge.status -eq 'validation_bridge_only') 'Scenario bridge must remain validation-only.'
Assert-True (-not [bool]$bridge.tableDrivenScenarioGeneration) 'Table-driven scenario generation must remain disabled.'

$expected = New-Object 'System.Collections.Generic.Dictionary[string,string]' ([System.StringComparer]::OrdinalIgnoreCase)
foreach ($line in Get-Content -LiteralPath $hashPath) {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    if ($line -notmatch '^([0-9a-fA-F]{64})  (.+)$') { throw "Invalid scenario hash line: $line" }
    $expected.Add($Matches[2].Replace('/','\'), $Matches[1].ToLowerInvariant())
}
Assert-True ($expected.Count -eq 53) 'Checkpoint 49 runtime scenario snapshot must contain 53 files.'
foreach ($relative in $expected.Keys) {
    $path = Join-Path $repositoryRoot $relative
    Assert-True (Test-Path -LiteralPath $path -PathType Leaf) "Preserved scenario file is missing: $relative"
    $actual = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    Assert-True ($actual -eq $expected[$relative]) "Checkpoint 49 runtime scenario file changed: $relative"
}
Write-Host '       Capacity architecture: AUX 1/1/2/2/3/3/3/4/4 and Weapon Bays 1/1/2/2/2/3/3/3/4 validated.'
Write-Host '       Representative cruisers: 18 legal fixtures and 3 exact multi-bay stress cases validated.'
Write-Host '       Scenario preservation: 53 runtime scenario files hash-verified; table-driven generation remains deferred.'
