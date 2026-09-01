[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$RepositoryRoot
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$BaselineSha256 = '93bff5c75d81cbf738107a22393e05f5b072446f4ff519d773dfa6dd94ed1a75'
$ExpectedManifestCount = 659
$root = (Resolve-Path -LiteralPath $RepositoryRoot).Path

function Assert-Contract {
    param(
        [Parameter(Mandatory = $true)][bool]$Condition,
        [Parameter(Mandatory = $true)][string]$Message
    )
    if (-not $Condition) { throw $Message }
}

function Get-RepositoryPath {
    param([Parameter(Mandatory = $true)][string]$RelativePath)
    return Join-Path $root ($RelativePath.Replace('/','\'))
}

function Get-TextFile {
    param([Parameter(Mandatory = $true)][string]$RelativePath)
    $path = Get-RepositoryPath $RelativePath
    Assert-Contract (Test-Path -LiteralPath $path -PathType Leaf) "Missing required file: $RelativePath"
    return [System.IO.File]::ReadAllText($path)
}

function Get-FileSha256 {
    param([Parameter(Mandatory = $true)][string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Read-JsonFile {
    param([Parameter(Mandatory = $true)][string]$RelativePath)
    try { return (Get-TextFile $RelativePath | ConvertFrom-Json) }
    catch { throw "Invalid JSON $RelativePath`: $($_.Exception.Message)" }
}

function ConvertTo-CanonicalJson {
    param($Value)
    if ($null -eq $Value) { return 'null' }
    return ($Value | ConvertTo-Json -Depth 100 -Compress)
}


function Get-TextAfterMarker {
    param(
        [Parameter(Mandatory = $true)][string]$Text,
        [Parameter(Mandatory = $true)][string]$Marker
    )
    $index = $Text.IndexOf($Marker,[System.StringComparison]::Ordinal)
    Assert-Contract ($index -ge 0) "Required source marker was not found: $Marker"
    return $Text.Substring($index + $Marker.Length)
}

function Get-TextBeforeMarker {
    param(
        [Parameter(Mandatory = $true)][string]$Text,
        [Parameter(Mandatory = $true)][string]$Marker
    )
    $index = $Text.IndexOf($Marker,[System.StringComparison]::Ordinal)
    Assert-Contract ($index -ge 0) "Required source marker was not found: $Marker"
    return $Text.Substring(0,$index)
}

function Get-PropertyNames {
    param(
        [Parameter(Mandatory = $true)][string]$Text,
        [Parameter(Mandatory = $true)][string]$Pattern
    )
    $set = New-Object 'System.Collections.Generic.HashSet[string]'
    foreach ($match in [regex]::Matches($Text,$Pattern,[System.Text.RegularExpressions.RegexOptions]::Multiline)) {
        [void]$set.Add($match.Groups[1].Value)
    }
    return ,$set
}

function Assert-SameStringSet {
    param(
        [Parameter(Mandatory = $true)]$Left,
        [Parameter(Mandatory = $true)]$Right,
        [Parameter(Mandatory = $true)][string]$Message
    )
    if ($Left.Count -ne $Right.Count) { throw $Message }
    foreach ($item in $Left) {
        if (-not $Right.Contains($item)) { throw $Message }
    }
}

function Get-ZipEntryText {
    param(
        [Parameter(Mandatory = $true)]$Zip,
        [Parameter(Mandatory = $true)][string]$EntryName,
        [switch]$Required
    )
    $entry = $Zip.GetEntry($EntryName)
    if ($null -eq $entry) {
        if ($Required) { throw "ZIP entry is missing: $EntryName" }
        return $null
    }
    $reader = New-Object System.IO.StreamReader($entry.Open())
    try { return $reader.ReadToEnd() }
    finally { $reader.Dispose() }
}

function Assert-ManifestContract {
    $manifestPath = Get-RepositoryPath 'CHECKPOINT_32_SHA256SUMS.txt'
    Assert-Contract (Test-Path -LiteralPath $manifestPath -PathType Leaf) 'CHECKPOINT_32_SHA256SUMS.txt missing'
    $entries = @{}
    foreach ($raw in Get-Content -LiteralPath $manifestPath) {
        if ([string]::IsNullOrWhiteSpace($raw) -or $raw.StartsWith('#')) { continue }
        $match = [regex]::Match($raw,'^([0-9a-fA-F]{64})  (.+)$')
        Assert-Contract ($match.Success) "Malformed manifest line: $raw"
        $digest = $match.Groups[1].Value.ToLowerInvariant()
        $relative = $match.Groups[2].Value.Replace('\','/')
        Assert-Contract ($relative -ne 'CHECKPOINT_32_SHA256SUMS.txt') 'Manifest contains itself'
        Assert-Contract (-not $entries.ContainsKey($relative)) "Duplicate manifest path: $relative"
        Assert-Contract (-not [System.IO.Path]::IsPathRooted($relative)) "Unsafe manifest path: $relative"
        Assert-Contract (-not ($relative.Split('/') -contains '..')) "Unsafe manifest path: $relative"
        $entries[$relative] = $digest
    }
    Assert-Contract ($entries.Count -eq $ExpectedManifestCount) "Manifest count $($entries.Count) != $ExpectedManifestCount"
    foreach ($relative in $entries.Keys) {
        $path = Get-RepositoryPath $relative
        Assert-Contract (Test-Path -LiteralPath $path -PathType Leaf) "Manifest file missing: $relative"
        Assert-Contract ((Get-FileSha256 $path) -eq $entries[$relative]) "Manifest hash mismatch: $relative"
    }
    Write-Host "       Static manifest contract: $($entries.Count) files hash-verified."
}

function Assert-ActiveDocumentsContract {
    $concepts = @(Get-ChildItem -LiteralPath (Get-RepositoryPath 'docs') -Filter 'Star_Cluster_Game_Concept_v*.docx' -File | Sort-Object Name | ForEach-Object { $_.Name })
    Assert-Contract (($concepts.Count -eq 1) -and ($concepts[0] -eq 'Star_Cluster_Game_Concept_v0.4d.docx')) "Active Concept set invalid: $($concepts -join ', ')"
    $runbooks = @(Get-ChildItem -LiteralPath (Get-RepositoryPath 'docs/validation') -Filter 'Checkpoint_*.md' -File | Sort-Object Name | ForEach-Object { $_.Name })
    Assert-Contract (($runbooks.Count -eq 1) -and ($runbooks[0] -eq 'Checkpoint_32_TL1_Tactical_Power_Completion_And_Reactor_Envelope_Calibration.md')) "Active validation set invalid: $($runbooks -join ', ')"
    Assert-Contract (Test-Path -LiteralPath (Get-RepositoryPath 'docs/archive/Star_Cluster_Game_Concept_v0.4c.docx') -PathType Leaf) 'Archived Concept v0.4c missing'
    Assert-Contract (Test-Path -LiteralPath (Get-RepositoryPath 'docs/validation/archive/Checkpoint_31_TL1_Layered_Defensive_Systems_Calibration.md') -PathType Leaf) 'Archived Checkpoint 31 runbook missing'
}

function Assert-BaselineContract {
    $relative = 'docs/archive/player_technology/pre-cp165-active/tl1_core_combat_numerical_baseline_v0_1.csv'
    $path = Get-RepositoryPath $relative
    Assert-Contract ((Get-FileSha256 $path) -eq $BaselineSha256) 'Baseline hash mismatch'
    $rows = @(Import-Csv -LiteralPath $path)
    $ids = New-Object 'System.Collections.Generic.HashSet[string]'
    foreach ($row in $rows) { [void]$ids.Add([string]$row.parameter_id) }
    Assert-Contract (($rows.Count -eq 127) -and ($ids.Count -eq 127)) 'Baseline must have 127 unique rows'
    $byId = @{}
    foreach ($row in $rows) { $byId[[string]$row.parameter_id] = $row }
    $expected = [ordered]@{
        reactor_output = '5'; reactor_degraded_output = '3'; reactor_emergency_output = '1'
        aux_reactor_output = '2'; aux_reactor_degraded_output = '1'
        combat_battery_gain = '2'; combat_battery_charges = '3'
        capacitor_capacity = '3'; capacitor_charge_rate = '1'; capacitor_discharge_rate = '2'
        missile_ammo = '25'; kinetic_pds_ammo = '50'; amm_pds_ammo = '25'
    }
    foreach ($key in $expected.Keys) {
        Assert-Contract ($byId.ContainsKey($key) -and ([string]$byId[$key].value -eq $expected[$key])) "Baseline $key mismatch"
    }
    $capRationale = [string]$byId['capacitor_capacity'].rationale
    Assert-Contract (($capRationale.Contains('full after FTL')) -or ($capRationale.Contains('full capacity'))) 'Capacitor FTL-full rationale missing'
    Assert-Contract ([string]$byId['ftl_transition'].test_signal -like '*Refills the Capacitor Bank only*') 'FTL exception contract missing'
    $linkedCount = 0
    foreach ($jsonPath in Get-ChildItem -LiteralPath (Get-RepositoryPath 'src/StarCluster.ScenarioRunner/Scenarios') -Filter '*.json' -File -Recurse) {
        try { $document = ([System.IO.File]::ReadAllText($jsonPath.FullName) | ConvertFrom-Json) }
        catch { throw "Invalid JSON $($jsonPath.FullName): $($_.Exception.Message)" }
        if ($document.PSObject.Properties.Name -contains 'baselineSha256') {
            $linkedCount++
            Assert-Contract ([string]$document.baselineSha256 -eq $BaselineSha256) "Baseline hash mismatch in $($jsonPath.FullName)"
        }
    }
    Write-Host "       Technology/test data: 127 baseline values and $linkedCount baseline-linked scenario documents verified."
}

function Assert-PhaseACapacitorFtlContract {
    $relative = 'src/StarCluster.ScenarioRunner/Scenarios/TL1PhaseA/tl1-a10-turn-and-ftl-resets.json'
    $document = Read-JsonFile $relative
    $case = @($document.cases | Where-Object { [string]$_.id -eq 'a10-c02' })
    Assert-Contract ($case.Count -eq 1) 'Phase A case a10-c02 is missing or duplicated'
    Assert-Contract ([string]$case[0].input.reset -eq 'ftlTransition') 'Phase A case a10-c02 is not an FTL transition'
    Assert-Contract ([int]$case[0].input.capacitorCharge -eq 2) 'Phase A case a10-c02 no longer begins with a partially charged Capacitor Bank'
    Assert-Contract ([int]$case[0].expected.persistent.capacitorCharge -eq 3) 'Phase A case a10-c02 must expect the installed Capacitor Bank to refill to Capacity 3 after FTL travel'
    Assert-Contract ([int]$case[0].expected.persistent.reactorStrain -eq 2) 'Phase A case a10-c02 must retain post-overload Reactor Strain through FTL travel'
    Write-Host '       Phase A FTL reset contract: Capacitor refills to 3/3 while Reactor Strain and other persistent resources remain unchanged.'
}

function Get-VariantIndexAndAssertReciprocal {
    param(
        [Parameter(Mandatory = $true)][object[]]$Variants,
        [Parameter(Mandatory = $true)][string]$Label
    )
    $index = @{}
    foreach ($variant in $Variants) {
        $id = [string]$variant.id
        Assert-Contract (-not [string]::IsNullOrWhiteSpace($id)) "$Label IDs contain an empty value"
        Assert-Contract (-not $index.ContainsKey($id)) "$Label IDs duplicated: $id"
        $index[$id] = $variant
    }
    $shared = @('category','shieldCapacity','shieldArmor','baseShieldRecharge','armorProtection','armorIntegrity','hull','rangeHexes','rangePenaltyPerHex','turnCap')
    foreach ($variant in $Variants) {
        $id = [string]$variant.id
        $sideA = ConvertTo-CanonicalJson $variant.sideA
        $sideB = ConvertTo-CanonicalJson $variant.sideB
        $pairId = if ($variant.PSObject.Properties.Name -contains 'pairId') { [string]$variant.pairId } else { '' }
        $asymmetric = $sideA -ne $sideB
        Assert-Contract ((-not $asymmetric) -or (-not [string]::IsNullOrWhiteSpace($pairId))) "Asymmetric $Label $id lacks pair"
        if ([string]::IsNullOrWhiteSpace($pairId)) { continue }
        Assert-Contract ($index.ContainsKey($pairId)) "$Label $id pair is missing"
        $pair = $index[$pairId]
        Assert-Contract ([string]$pair.pairId -eq $id) "$Label $id pair is not reciprocal"
        Assert-Contract ((ConvertTo-CanonicalJson $variant.sideA) -eq (ConvertTo-CanonicalJson $pair.sideB)) "$Label $id is not an exact side swap"
        Assert-Contract ((ConvertTo-CanonicalJson $variant.sideB) -eq (ConvertTo-CanonicalJson $pair.sideA)) "$Label $id is not an exact side swap"
        foreach ($field in $shared) {
            $leftProperty = $variant.PSObject.Properties[$field]
            $rightProperty = $pair.PSObject.Properties[$field]
            $leftValue = if ($null -eq $leftProperty) { $null } else { $leftProperty.Value }
            $rightValue = if ($null -eq $rightProperty) { $null } else { $rightProperty.Value }
            Assert-Contract ((ConvertTo-CanonicalJson $leftValue) -eq (ConvertTo-CanonicalJson $rightValue)) "$Label $id pair differs in $field"
        }
    }
    return $index
}

function Assert-CategoryCounts {
    param(
        [Parameter(Mandatory = $true)][object[]]$Variants,
        [Parameter(Mandatory = $true)]$Expected,
        [Parameter(Mandatory = $true)][string]$Label
    )
    $actual = @{}
    foreach ($group in ($Variants | Group-Object category)) { $actual[[string]$group.Name] = [int]$group.Count }
    Assert-Contract ($actual.Count -eq $Expected.Count) "$Label category count set drifted"
    foreach ($key in $Expected.Keys) {
        Assert-Contract ($actual.ContainsKey($key) -and $actual[$key] -eq $Expected[$key]) "$Label category $key mismatch"
    }
}

function Assert-RetainedStudiesContract {
    $specs = @(
        [pscustomobject]@{ Name='tl1-kc01-kinetic-interaction-study.json'; Count=29; Categories=$null },
        [pscustomobject]@{ Name='tl1-ec01-energy-interaction-study.json'; Count=31; Categories=$null },
        [pscustomobject]@{ Name='tl1-wm01-complete-weapon-matrix.json'; Count=48; Categories=$null },
        [pscustomobject]@{ Name='tl1-pds01-interception-study.json'; Count=59; Categories=$null },
        [pscustomobject]@{ Name='tl1-ds01-layered-defensive-systems-study.json'; Count=171; Categories=[ordered]@{'accepted-control'=6;'pds-rule-correction'=36;'sensor-ew-boundary'=57;'shield-defense'=36;'layered-defense'=36} }
    )
    foreach ($spec in $specs) {
        $relative = "src/StarCluster.ScenarioRunner/Scenarios/TL1Calibration/$($spec.Name)"
        $document = Read-JsonFile $relative
        Assert-Contract (([string]$document.baselineSha256 -eq $BaselineSha256) -and ([int]$document.trialsPerVariant -eq 10000)) "$($spec.Name) baseline/trials mismatch"
        $variants = @($document.variants)
        Assert-Contract ($variants.Count -eq $spec.Count) "$($spec.Name) has $($variants.Count), expected $($spec.Count)"
        if ($spec.Count -eq 59 -or $spec.Count -eq 171) { [void](Get-VariantIndexAndAssertReciprocal -Variants $variants -Label $spec.Name) }
        if ($null -ne $spec.Categories) { Assert-CategoryCounts -Variants $variants -Expected $spec.Categories -Label $spec.Name }
    }
}

function Assert-PowerStudyContract {
    $document = Read-JsonFile 'src/StarCluster.ScenarioRunner/Scenarios/TL1Calibration/tl1-pe01-tactical-power-and-reactor-envelope-study.json'
    $schema = Read-JsonFile 'docs/design/player_technology/tl1_power_envelope_calibration_schema_v0_1.json'
    Assert-Contract ([string]$document.schemaVersion -eq 'star-cluster-tl1-power-envelope-calibration-v1') 'Power schemaVersion mismatch'
    Assert-Contract ([string]$schema.'$id' -eq 'star-cluster-tl1-power-envelope-calibration-v1') 'Power schema ID mismatch'
    Assert-Contract (([int]$schema.properties.variants.minItems -eq 504) -and ([int]$schema.properties.variants.maxItems -eq 504)) 'Power schema must require 504 variants'
    Assert-Contract (([string]$document.baselineSha256 -eq $BaselineSha256) -and ([int]$document.trialsPerVariant -eq 10000)) 'Power study baseline/trials mismatch'
    $variants = @($document.variants)
    Assert-Contract ($variants.Count -eq 504) "Power study has $($variants.Count) variants"
    $expected = [ordered]@{'accepted-control'=6;'reactor-sweep'=90;'single-consumer'=144;'layered-sweep'=144;'power-source-overlay'=60;'overload-boundary'=30;'held-interception'=30}
    Assert-CategoryCounts -Variants $variants -Expected $expected -Label 'Power study'
    $index = Get-VariantIndexAndAssertReciprocal -Variants $variants -Label 'power variant'
    $outputSet = @{}
    foreach ($variant in $variants | Where-Object { $_.category -eq 'reactor-sweep' }) {
        $outputSet[[int]$variant.sideA.reactorOutput] = $true
        $outputSet[[int]$variant.sideB.reactorOutput] = $true
    }
    $outputs = @($outputSet.Keys | Sort-Object)
    Assert-Contract (($outputs.Count -eq 9) -and (($outputs -join ',') -eq '0,1,2,3,4,5,6,7,8')) "Reactor sweep outputs $($outputs -join ',') != 0-8"
    foreach ($id in @('pe-reactor-energy-standard-r2-p0','pe-single-energy-epds-r2-p5','pe-layer-energy-full-defense-r2-p5','pe-overlay-cap-full-a-r2-p3','pe-overload-sensor-r6-p4','pe-held-energy-standard-r2-p2','pe-held-pds-saturation-r2-p5')) {
        Assert-Contract ($index.ContainsKey($id)) "Missing required power variant $id"
    }
    $cap = $index['pe-overlay-cap-full-a-r2-p3'].sideA
    Assert-Contract (([int]$cap.capacitorCapacity -eq 3) -and ([int]$cap.capacitorStartingCharge -eq 3) -and ([int]$cap.capacitorChargeRate -eq 1) -and ([int]$cap.capacitorDischargeRate -eq 2)) 'Full capacitor overlay mismatch'
    Assert-Contract ([int]$index['pe-held-pds-saturation-r2-p5'].sideB.missileLaunchesPerTurn -eq 2) 'Held saturation boundary missing'
    foreach ($variant in $variants) {
        if ([string]$variant.id -like '*saturation*') { continue }
        foreach ($side in @($variant.sideA,$variant.sideB)) {
            if ([string]$side.family -eq 'missile') {
                Assert-Contract ([int]$side.missileLaunchesPerTurn -eq 1) 'Normal launcher exceeds one Flight per turn'
            }
        }
    }
    Write-Host '       TL1 power-envelope study: 504 variants, exact category counts, reactor outputs 0-8, reciprocal pairs, full-after-FTL Capacitors, overlays, overloads, and Held Interception verified.'
}

function Assert-TestContract {
    $facts = 0; $theories = 0; $inline = 0
    foreach ($path in Get-ChildItem -LiteralPath (Get-RepositoryPath 'tests') -Filter '*.cs' -File -Recurse) {
        $source = [System.IO.File]::ReadAllText($path.FullName)
        $facts += ([regex]::Matches($source,'\[Fact\]')).Count
        $theories += ([regex]::Matches($source,'\[Theory\]')).Count
        $inline += ([regex]::Matches($source,'\[InlineData\(')).Count
    }
    Assert-Contract (($facts -eq 588) -and ($theories -eq 20) -and ($inline -eq 80) -and (($facts + $inline) -eq 668)) "Test cardinality $facts/$theories/$inline/$($facts + $inline), expected 588/20/80/668"
    $source = Get-TextFile 'tests/StarCluster.Tests/Combat/Power/Tl1TacticalPowerCompletionTests.cs'
    Assert-Contract (([regex]::Matches($source,'\[Fact\]')).Count -eq 26) 'Checkpoint 32 power test source must contain 26 facts'
    foreach ($marker in @('Ftl_transition_refills_a_depleted_capacitor','Combat_battery_injects_two_available_power','Operational_auxiliary_reactor_adds_two_power','Held_power_becomes_spent_only_when_triggered','Pds_resolves_before_held_interception','A_single_held_weapon_can_attempt_only_one_saturation_intercept','Safe_reactor_overload_adds_one_power_and_one_strain')) {
        Assert-Contract ($source.Contains($marker)) "Power tests lack $marker"
    }
    Write-Host '       Checkpoint 32 test sources: 26 new Tactical Power facts and 668 total discovered cases verified.'
}

function Assert-CSharpContract {
    $markers = [ordered]@{
        'src/StarCluster.Core/Combat/Power/CombatBatteryState.cs' = @('CurrentCharges','DischargeLimitPerTurn','AddGeneratedPower')
        'src/StarCluster.Core/Combat/Power/CapacitorBankState.cs' = @('CompleteFtlTransition','ChargeRate','DischargeRate','OperationUsedThisTurn')
        'src/StarCluster.Core/Combat/Power/AuxiliaryReactorState.cs' = @('OperationalOutput','DegradedOutput','Contribute')
        'src/StarCluster.Core/Combat/Weapons/WeaponState.cs' = @('ConsumeAmmunitionForHeldFire')
        'src/StarCluster.Core/Combat/DirectFire/Tl1PowerEnvelopeSimulator.cs' = @('HeldDeclarationsA','HeldPowerEarmarkedA','OffensiveWeaponPowerSpentA','ApplyThresholdPowerSources','ResolveHeldInterception','EnergySafeBurst','ShieldRecoverySafeOverload')
        'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1PowerEnvelopeCalibrationRunner.cs' = @('RequiredVariantCount = 504','reactor-sweep','power-source-overlay','held-interception','MeanBaseReactorPowerPerTurnA','MeanPdsPowerPerTurnA','MeanFirmTrackRateA','variants.csv')
        'src/StarCluster.ScenarioRunner/Program.cs' = @('tl1-power-envelope-calibration','tl1-power-envelope-calibration-preflight','checkpoint-32-tl1-power-envelope-calibration')
    }
    foreach ($relative in $markers.Keys) {
        $source = Get-TextFile $relative
        foreach ($marker in $markers[$relative]) { Assert-Contract ($source.Contains($marker)) "$relative lacks marker $marker" }
    }

    $documents = Get-TextFile 'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1PowerEnvelopeCalibrationDocuments.cs'
    $simulator = Get-TextFile 'src/StarCluster.Core/Combat/DirectFire/Tl1PowerEnvelopeSimulator.cs'
    $runner = Get-TextFile 'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1PowerEnvelopeCalibrationRunner.cs'

    $documentBlock = Get-TextAfterMarker -Text $documents -Marker 'public sealed class Tl1PowerEnvelopeSideDocument'
    $profileTail = Get-TextAfterMarker -Text $simulator -Marker 'public sealed record Tl1PowerEnvelopeSideProfile'
    $profileBlock = Get-TextBeforeMarker -Text $profileTail -Marker 'public sealed record Tl1PowerEnvelopeProfile'
    $documentProperties = Get-PropertyNames -Text $documentBlock -Pattern 'public\s+[\w?<>]+\s+(\w+)\s*\{\s*get;'
    $profileProperties = Get-PropertyNames -Text $profileBlock -Pattern 'public\s+[\w?<>]+\s+(\w+)\s*\{\s*get;'
    $mapTail = Get-TextAfterMarker -Text $runner -Marker 'private static Tl1PowerEnvelopeSideProfile ToSide'
    $mapBlock = Get-TextBeforeMarker -Text $mapTail -Marker 'private static IReadOnlyList<GateResult>'
    $mapLeft = New-Object 'System.Collections.Generic.HashSet[string]'
    $mapRight = New-Object 'System.Collections.Generic.HashSet[string]'
    foreach ($match in [regex]::Matches($mapBlock,'(\w+)\s*=\s*side\.(\w+)')) {
        [void]$mapLeft.Add($match.Groups[1].Value)
        [void]$mapRight.Add($match.Groups[2].Value)
    }
    Assert-Contract (($documentProperties.Count -eq 51) -and ($profileProperties.Count -eq 51) -and ($mapLeft.Count -eq 51) -and ($mapRight.Count -eq 51)) 'Power side profile/document mapping cardinality mismatch'
    Assert-SameStringSet -Left $mapLeft -Right $profileProperties -Message 'Power side profile mapping mismatch'
    Assert-SameStringSet -Left $mapRight -Right $documentProperties -Message 'Power side document mapping mismatch'

    $resultTail = Get-TextAfterMarker -Text $simulator -Marker 'public sealed record Tl1PowerEnvelopeResult'
    $resultBlock = Get-TextBeforeMarker -Text $resultTail -Marker 'public sealed class Tl1PowerEnvelopeSimulator'
    $resultProperties = Get-PropertyNames -Text $resultBlock -Pattern 'public\s+[\w?<>]+\s+(\w+)\s*\{\s*get;'
    $runnerReferences = Get-PropertyNames -Text $runner -Pattern 'duel\.(\w+)'
    foreach ($reference in $runnerReferences) { Assert-Contract ($resultProperties.Contains($reference)) "Runner references missing result property: $reference" }
    $resultMapTail = Get-TextAfterMarker -Text $simulator -Marker 'private static Tl1PowerEnvelopeResult CreateResult'
    $resultMapBlock = Get-TextBeforeMarker -Text $resultMapTail -Marker 'private static bool IsTerminal'
    $resultAssignments = Get-PropertyNames -Text $resultMapBlock -Pattern '^\s*(\w+)\s*='
    Assert-SameStringSet -Left $resultAssignments -Right $resultProperties -Message 'Power result initializer mapping mismatch'

    $trialTail = Get-TextAfterMarker -Text $runner -Marker 'private sealed record TrialResult'
    $trialBlock = Get-TextBeforeMarker -Text $trialTail -Marker 'private sealed record VariantSummary'
    $trialProperties = Get-PropertyNames -Text $trialBlock -Pattern 'public\s+[\w?<>]+\s+(\w+)\s*\{\s*get;'
    $trialFrom = Get-TextAfterMarker -Text $trialBlock -Marker 'public static TrialResult From'
    $trialAssignments = Get-PropertyNames -Text $trialFrom -Pattern '^\s*(\w+)\s*='
    Assert-SameStringSet -Left $trialAssignments -Right $trialProperties -Message 'TrialResult mapping mismatch'

    $summaryTail = Get-TextAfterMarker -Text $runner -Marker 'private sealed record VariantSummary'
    $summaryPropertyBlock = Get-TextBeforeMarker -Text $summaryTail -Marker 'public static VariantSummary Create'
    $summaryProperties = Get-PropertyNames -Text $summaryPropertyBlock -Pattern 'public\s+[\w?<>]+\s+(\w+)\s*\{\s*get;'
    $summaryCreateTail = Get-TextAfterMarker -Text $summaryTail -Marker 'public static VariantSummary Create'
    $summaryCreate = Get-TextBeforeMarker -Text $summaryCreateTail -Marker 'private static double Rate'
    $summaryAssignments = Get-PropertyNames -Text $summaryCreate -Pattern '^\s*(\w+)\s*=(?!>)'
    Assert-SameStringSet -Left $summaryAssignments -Right $summaryProperties -Message 'VariantSummary mapping mismatch'

    $csvTail = Get-TextAfterMarker -Text $runner -Marker 'var csv = new StringBuilder('
    $headerEnd = $csvTail.IndexOf(");`r`n`r`n        foreach",[System.StringComparison]::Ordinal)
    if ($headerEnd -lt 0) { $headerEnd = $csvTail.IndexOf(");`n`n        foreach",[System.StringComparison]::Ordinal) }
    Assert-Contract ($headerEnd -ge 0) 'CSV header terminator was not found'
    $headerBlock = $csvTail.Substring(0,$headerEnd)
    $headerBuilder = New-Object System.Text.StringBuilder
    foreach ($match in [regex]::Matches($headerBlock,'"([^"\\]*(?:\\.[^"\\]*)*)"')) { [void]$headerBuilder.Append($match.Groups[1].Value) }
    $columns = @($headerBuilder.ToString().Trim().Split(','))
    $rowTail = Get-TextAfterMarker -Text $csvTail -Marker 'foreach (VariantSummary summary in summaries)'
    $rowBlock = Get-TextBeforeMarker -Text $rowTail -Marker '        File.WriteAllText('
    $valueCount = ([regex]::Matches($rowBlock,'Append\(C\(')).Count + ([regex]::Matches($rowBlock,'Append\(F\(')).Count + ([regex]::Matches($rowBlock,'Append\(summary\.Trials\)')).Count
    $uniqueColumns = New-Object 'System.Collections.Generic.HashSet[string]'
    foreach ($column in $columns) { [void]$uniqueColumns.Add($column) }
    Assert-Contract (($columns.Count -eq 119) -and ($uniqueColumns.Count -eq 119) -and ($valueCount -eq 119)) "Power variants.csv mapping mismatch: $($columns.Count) columns, $valueCount values"

    $sourceCount = @(Get-ChildItem -LiteralPath (Get-RepositoryPath 'src') -Filter '*.cs' -File -Recurse).Count
    $testCount = @(Get-ChildItem -LiteralPath (Get-RepositoryPath 'tests') -Filter '*.cs' -File -Recurse).Count
    Write-Host "       C# structural contracts: $sourceCount source and $testCount test files; power mappings and 119-column report verified."
}

function Get-DocxPlainText {
    param([Parameter(Mandatory = $true)][string]$Path)
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip = [System.IO.Compression.ZipFile]::OpenRead($Path)
    try {
        $builder = New-Object System.Text.StringBuilder
        foreach ($entry in @($zip.Entries | Where-Object { $_.FullName -like 'word/*.xml' })) {
            $reader = New-Object System.IO.StreamReader($entry.Open())
            try { $xmlText = $reader.ReadToEnd() } finally { $reader.Dispose() }
            try {
                [xml]$xml = $xmlText
                foreach ($node in $xml.SelectNodes('//*[local-name()="t"]')) { [void]$builder.Append($node.InnerText).Append(' ') }
            }
            catch { continue }
        }
        return ([regex]::Replace($builder.ToString(),'\s+',' '))
    }
    finally { $zip.Dispose() }
}

function Assert-DocumentationContract {
    $contracts = [ordered]@{
        'README.md' = @('Checkpoint 32','v0.4d','668 engine-independent tests','504 Tactical Power/reactor-envelope variants','does not require Python')
        'Checkpoint_32_Readme.txt' = @('complete replacement repository','Capacitor','Held Interception','504 Tactical Power/reactor-envelope variants','does not require Python')
        'docs/checkpoints/Checkpoint_32_TL1_Tactical_Power_Completion_And_Reactor_Envelope_Calibration.md' = @('504 variants','Held Interception','Auxiliary Reactor','Shield Battery')
        'docs/validation/Checkpoint_32_TL1_Tactical_Power_Completion_And_Reactor_Envelope_Calibration.md' = @('668 engine-independent tests','504 Tactical Power/reactor-envelope variants','idempotent')
        'docs/design/player_technology/TL1_Tactical_Power_And_Reactor_Envelope_Calibration_Plan_v0_1.md' = @('full after FTL travel','Reaction Capacity at 1','504 variants','0 through 8')
        'docs/Prototype_TODO.md' = @('Checkpoint 32 status','26 focused engine-independent facts','Tractor Beams')
    }
    foreach ($relative in $contracts.Keys) {
        $text = Get-TextFile $relative
        foreach ($marker in $contracts[$relative]) { Assert-Contract ($text.Contains($marker)) "$relative lacks marker $marker" }
    }
    $concept = Get-DocxPlainText (Get-RepositoryPath 'docs/Star_Cluster_Game_Concept_v0.4d.docx')
    foreach ($marker in @('Checkpoint 32 - TL1 Tactical Power Completion and Reactor Envelope Calibration','Power sources and storage','Held Interception','504 variants at 10,000 trials each','D-270','D-278','END OF DRAFT v0.4d')) {
        Assert-Contract ($concept.Contains($marker)) "Concept lacks marker $marker"
    }
}

function Assert-WorkbookContract {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $path = Get-RepositoryPath 'docs/design/player_technology/StarCluster_Player_TL_Framework_Draft_v0_12.xlsx'
    Assert-Contract (Test-Path -LiteralPath $path -PathType Leaf) 'Workbook v0.12 missing'
    $zip = [System.IO.Compression.ZipFile]::OpenRead($path)
    try {
        Assert-Contract (@($zip.Entries | Where-Object { $_.FullName -like 'xl/tables/*' }).Count -eq 0) 'Workbook contains structured tables'
        $workbookXml = Get-ZipEntryText -Zip $zip -EntryName 'xl/workbook.xml' -Required
        foreach ($sheet in @('Overview','TL1 Baseline','Checkpoint 29 Matrix','Checkpoint 30 PDS','Checkpoint 31 Defense','Checkpoint 32 Power','Design Decisions')) {
            Assert-Contract ($workbookXml.Contains(('name="{0}"' -f $sheet))) "Workbook missing sheet $sheet"
        }
        $builder = New-Object System.Text.StringBuilder
        foreach ($entry in @($zip.Entries | Where-Object { $_.FullName -like 'xl/*.xml' -or $_.FullName -like 'xl/worksheets/*.xml' })) {
            $reader = New-Object System.IO.StreamReader($entry.Open())
            try { [void]$builder.Append($reader.ReadToEnd()) } finally { $reader.Dispose() }
        }
        $allXml = $builder.ToString()
        foreach ($marker in @('Checkpoint 32 - TL1 Tactical Power Completion and Reactor Envelope Calibration','504 variants x 10,000 trials','D-278','Capacity 3 / charge 1 / discharge 2','full after FTL')) {
            Assert-Contract ($allXml.Contains($marker)) "Workbook lacks marker $marker"
        }
    }
    finally { $zip.Dispose() }
    Write-Host '       Workbook OOXML: retained Checkpoint 29-31 sheets, new Checkpoint 32 Power, Decisions through D-278, and no structured tables verified.'
}

function Assert-ScriptContract {
    $directory = Get-RepositoryPath 'tools/checkpoints/checkpoint-32'
    $manifestPlaceholder = '__MANIFEST' + '_COUNT__'
    foreach ($path in Get-ChildItem -LiteralPath $directory -Filter '*.ps1' -File) {
        $text = [System.IO.File]::ReadAllText($path.FullName)
        Assert-Contract (-not $text.Contains($manifestPlaceholder)) "Unresolved manifest placeholder in $($path.Name)"
    }
    $apply = Get-TextFile 'tools/checkpoints/checkpoint-32/apply_checkpoint_32.ps1'
    foreach ($marker in @('[1/15]','[15/15]','Running 668 engine-independent tests','Running 504 TL1 Tactical Power and Reactor-envelope variants','tl1-power-envelope-calibration','Engine-independent tests passed: 668.')) {
        Assert-Contract ($apply.Contains($marker)) "Apply script lacks marker $marker"
    }
    $registry = Get-TextFile 'tools/checkpoints/checkpoint-32/checkpoint_runtime_registry.ps1'
    foreach ($marker in @('function Register-CheckpointOperation','function Assert-CheckpointOperationRegistry','function Invoke-CheckpointOperation','function Test-CheckpointOperationRegistry')) {
        Assert-Contract ($registry.Contains($marker)) "Checkpoint operation registry lacks marker $marker"
    }
    foreach ($forbidden in @('Resolve-VerifiedPython3Command','Invoke-CheckpointPython3','Get-Command python','Get-Command py','python3.exe','python.exe')) {
        Assert-Contract (-not $registry.Contains($forbidden)) "Checkpoint operation registry still contains external Python dependency marker $forbidden"
    }
    foreach ($relative in @('tools/checkpoints/checkpoint-32/apply_checkpoint_32.ps1','tools/checkpoints/checkpoint-32/build_checkpoint_32_release.ps1','tools/checkpoints/checkpoint-32/validate_checkpoint_32_release.ps1')) {
        $body = Get-TextFile $relative
        Assert-Contract ($body.Contains(". (Join-Path `$PSScriptRoot 'checkpoint_runtime_registry.ps1')")) "$relative does not load the shared operation registry"
        Assert-Contract ($body.Contains("Register-CheckpointOperation -Name 'StaticPreflight'")) "$relative does not register StaticPreflight"
        Assert-Contract ($body.Contains("Invoke-CheckpointOperation -Name 'StaticPreflight'")) "$relative does not invoke StaticPreflight through the operation registry"
        foreach ($forbidden in @('Invoke-CheckpointPython3','static_preflight_checkpoint_32.py','Get-Command python','Get-Command py')) {
            Assert-Contract (-not $body.Contains($forbidden)) "$relative still contains Python dependency marker $forbidden"
        }
    }
    foreach ($key in @('RelativePathCompatibility','LocalArtifactPolicy','StaticPreflight')) {
        Assert-Contract ($apply.Contains("Register-CheckpointOperation -Name '$key'")) "Apply script does not register operation key $key"
    }
    Assert-Contract ($apply.Contains("Assert-CheckpointOperationRegistry -RequiredNames @('RelativePathCompatibility','LocalArtifactPolicy','StaticPreflight')")) 'Apply script does not validate all required operation keys'
    Assert-Contract ($apply.Contains('Test-CheckpointOperationRegistry')) 'Apply script does not run the operation registry smoke test'
    Assert-Contract ($apply.Contains("Invoke-CheckpointOperation -Name 'RelativePathCompatibility'")) 'Apply script does not invoke RelativePathCompatibility through the registry'
    Assert-Contract ($apply.Contains("Invoke-CheckpointOperation -Name 'LocalArtifactPolicy'")) 'Apply script does not invoke LocalArtifactPolicy through the registry'
    foreach ($stale in @('Test-WindowsPowerShellRelativePathCompatibility','Test-RepositoryLocalArtifactPolicy')) {
        Assert-Contract (-not $apply.Contains($stale)) "Apply script contains stale runtime helper name $stale"
    }
    Assert-Contract (-not (Test-Path -LiteralPath (Get-RepositoryPath 'tools/checkpoints/checkpoint-32/static_preflight_checkpoint_32.py'))) 'Obsolete Python static preflight remains packaged'
    Write-Host '       PowerShell operation registry: native static preflight and semantic operation dispatch are defined and used by all Checkpoint 32 scripts; no Python runtime is required.'
}

Assert-ManifestContract
Assert-ActiveDocumentsContract
Assert-BaselineContract
Assert-PhaseACapacitorFtlContract
Assert-RetainedStudiesContract
Assert-PowerStudyContract
Assert-TestContract
Assert-CSharpContract
Assert-DocumentationContract
Assert-WorkbookContract
Assert-ScriptContract

Write-Output 'Checkpoint 32 static preflight completed successfully.'
