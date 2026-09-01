[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$RepositoryRoot
)

$ErrorActionPreference = 'Stop'
$script:Root = (Resolve-Path -LiteralPath $RepositoryRoot).Path

function Get-RepoPath {
    param([Parameter(Mandatory = $true)][string]$RelativePath)
    return Join-Path $script:Root $RelativePath
}

function Assert-Contract {
    param([Parameter(Mandatory = $true)][bool]$Condition,[Parameter(Mandatory = $true)][string]$Message)
    if (-not $Condition) { throw $Message }
}

function Get-Text {
    param([Parameter(Mandatory = $true)][string]$RelativePath)
    $path = Get-RepoPath $RelativePath
    Assert-Contract (Test-Path -LiteralPath $path -PathType Leaf) "Missing file $RelativePath"
    return Get-Content -LiteralPath $path -Raw
}

function Read-Json {
    param([Parameter(Mandatory = $true)][string]$RelativePath)
    return (Get-Text $RelativePath | ConvertFrom-Json)
}

function Get-DocxText {
    param([Parameter(Mandatory = $true)][string]$RelativePath)
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $path = Get-RepoPath $RelativePath
    $zip = [System.IO.Compression.ZipFile]::OpenRead($path)
    try {
        $entry = $zip.GetEntry('word/document.xml')
        Assert-Contract ($null -ne $entry) "$RelativePath lacks word/document.xml"
        $reader = New-Object System.IO.StreamReader($entry.Open())
        try { $xmlText = $reader.ReadToEnd() } finally { $reader.Dispose() }
        $xml = New-Object System.Xml.XmlDocument
        $xml.LoadXml($xmlText)
        $ns = New-Object System.Xml.XmlNamespaceManager($xml.NameTable)
        $ns.AddNamespace('w','http://schemas.openxmlformats.org/wordprocessingml/2006/main')
        return (($xml.SelectNodes('//w:t',$ns) | ForEach-Object { $_.InnerText }) -join ' ')
    }
    finally { $zip.Dispose() }
}

function Get-XlsxXmlText {
    param([Parameter(Mandatory = $true)][string]$RelativePath)
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $path = Get-RepoPath $RelativePath
    $zip = [System.IO.Compression.ZipFile]::OpenRead($path)
    try {
        $names = @($zip.Entries | ForEach-Object { $_.FullName })
        Assert-Contract (@($names | Where-Object { $_ -like 'xl/tables/*' }).Count -eq 0) 'Workbook contains prohibited structured table parts.'
        $all = New-Object System.Text.StringBuilder
        foreach ($entry in @($zip.Entries | Where-Object { $_.FullName -like 'xl/*.xml' -or $_.FullName -like 'xl/worksheets/*.xml' })) {
            $reader = New-Object System.IO.StreamReader($entry.Open())
            try { [void]$all.Append($reader.ReadToEnd()) } finally { $reader.Dispose() }
        }
        return $all.ToString()
    }
    finally { $zip.Dispose() }
}

function Test-Manifest {
    $manifestPath = Get-RepoPath 'CHECKPOINT_33_SHA256SUMS.txt'
    Assert-Contract (Test-Path -LiteralPath $manifestPath -PathType Leaf) 'Checkpoint 33 manifest is missing.'
    $seen = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
    $count = 0
    foreach ($line in Get-Content -LiteralPath $manifestPath) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        $match = [regex]::Match($line,'^([0-9a-fA-F]{64})  (.+)$')
        Assert-Contract ($match.Success) "Malformed manifest line: $line"
        $relative = $match.Groups[2].Value.Replace('/','\')
        Assert-Contract ($relative -ne 'CHECKPOINT_33_SHA256SUMS.txt') 'Manifest contains itself.'
        Assert-Contract ($seen.Add($relative)) "Duplicate manifest path $relative"
        $path = Get-RepoPath $relative
        Assert-Contract (Test-Path -LiteralPath $path -PathType Leaf) "Manifest file missing: $relative"
        $actual = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
        Assert-Contract ($actual -eq $match.Groups[1].Value.ToLowerInvariant()) "Manifest hash mismatch: $relative"
        $count++
    }
    Assert-Contract ($count -eq 673) "Manifest contains $count files; expected 673."
    Write-Host "       Static manifest contract: $count files hash-verified."
}

function Test-BaselineAndLinkedJson {
    $baselineRelative = 'docs/archive/player_technology/pre-cp165-active/tl1_core_combat_numerical_baseline_v0_1.csv'
    $baselinePath = Get-RepoPath $baselineRelative
    $rows = @(Import-Csv -LiteralPath $baselinePath)
    Assert-Contract ($rows.Count -eq 127) "Baseline row count $($rows.Count), expected 127."
    Assert-Contract (($rows | Select-Object -ExpandProperty parameter_id -Unique).Count -eq 127) 'Baseline IDs are not unique.'
    $hash = (Get-FileHash -LiteralPath $baselinePath -Algorithm SHA256).Hash.ToLowerInvariant()
    $expectedHash = '11f533483d502ffa6b8dd2df5c0659e07d2281f0c2fd0b8b1360340a2cf06991'
    Assert-Contract ($hash -eq $expectedHash) "Baseline hash is $hash, expected $expectedHash."
    $byId = @{}
    foreach ($row in $rows) { $byId[[string]$row.parameter_id] = [string]$row.value }
    $expected = @{
        reactor_output='5'; reactor_degraded_output='3'; reactor_emergency_output='1';
        kinetic_power='1'; missile_launch_power='0';
        shield_overcapacity_cost='1'; shield_overcapacity_amount='1';
        aux_reactor_output='1'; aux_reactor_degraded_output='0';
        kinetic_pds_reactions='1'
    }
    foreach ($key in $expected.Keys) {
        Assert-Contract ($byId.ContainsKey($key) -and $byId[$key] -eq $expected[$key]) "Baseline $key must equal $($expected[$key])."
    }
    $linked = 0
    foreach ($file in Get-ChildItem -LiteralPath (Get-RepoPath 'src/StarCluster.ScenarioRunner/Scenarios') -Filter '*.json' -Recurse -File) {
        $json = Get-Content -LiteralPath $file.FullName -Raw | ConvertFrom-Json
        if ($json.PSObject.Properties.Name -contains 'baselineSha256') {
            Assert-Contract ([string]$json.baselineSha256 -eq $expectedHash) "Baseline hash mismatch in $($file.FullName)."
            $linked++
        }
    }
    Assert-Contract ($linked -eq 25) "Found $linked baseline-linked scenario documents; expected 25."
    Write-Host '       Technology/test data: 127 baseline values and 25 baseline-linked scenario documents verified.'
}

function Get-RegisteredPhaseACase {
    param(
        [Parameter(Mandatory = $true)][hashtable]$RegistryEntry,
        [Parameter(Mandatory = $true)][string]$SemanticName
    )

    $documentPath = [string]($RegistryEntry['Document'])
    $caseId = [string]($RegistryEntry['CaseId'])
    $document = Read-Json $documentPath
    $matches = @($document.cases | Where-Object { [string]$_.id -ceq $caseId })
    Assert-Contract ($matches.Count -eq 1) "Phase A case registry entry $SemanticName must resolve exactly once to ${documentPath}::${caseId}; found $($matches.Count)."
    return $matches[0]
}

function Test-PhaseAContracts {
    $phaseACaseRegistry = [ordered]@{
        UnusedKineticHold = @{
            Document = 'src/StarCluster.ScenarioRunner/Scenarios/TL1PhaseA/tl1-a06-held-interception-unused.json'
            CaseId = 'a06-c02'
        }
        TriggeredKineticHold = @{
            Document = 'src/StarCluster.ScenarioRunner/Scenarios/TL1PhaseA/tl1-a07-held-interception-fires.json'
            CaseId = 'a07-c02'
        }
        KineticWeaponPacket = @{
            Document = 'src/StarCluster.ScenarioRunner/Scenarios/TL1PhaseA/tl1-a11-weapon-resource-packets.json'
            CaseId = 'a11-c01'
        }
    }

    $unusedKineticHold = Get-RegisteredPhaseACase -RegistryEntry $phaseACaseRegistry['UnusedKineticHold'] -SemanticName 'UnusedKineticHold'
    $triggeredKineticHold = Get-RegisteredPhaseACase -RegistryEntry $phaseACaseRegistry['TriggeredKineticHold'] -SemanticName 'TriggeredKineticHold'
    $kineticWeaponPacket = Get-RegisteredPhaseACase -RegistryEntry $phaseACaseRegistry['KineticWeaponPacket'] -SemanticName 'KineticWeaponPacket'

    Assert-Contract ([string]$unusedKineticHold.input.holdId -ceq 'kinetic-hold') 'Unused Kinetic hold registry entry resolved the wrong fixture.'
    Assert-Contract ([int]$unusedKineticHold.input.powerCost -eq 1) 'Unused Kinetic hold must earmark 1 TP.'
    Assert-Contract ([int]$unusedKineticHold.expected.afterDeclaration.earmarked -eq 1) 'Unused Kinetic hold fixture lacks 1 earmarked TP.'
    Assert-Contract ([int]$unusedKineticHold.expected.finalPower.spent -eq 0) 'Unused Kinetic hold must release without spending TP.'

    Assert-Contract ([string]$triggeredKineticHold.input.holdId -ceq 'kinetic-hold') 'Triggered Kinetic hold registry entry resolved the wrong fixture.'
    Assert-Contract ([int]$triggeredKineticHold.input.powerCost -eq 1) 'Triggered Kinetic hold must cost 1 TP.'
    Assert-Contract ([int]$triggeredKineticHold.expected.finalPower.spent -eq 1) 'Triggered Kinetic hold must spend 1 TP.'

    Assert-Contract ([string]$kineticWeaponPacket.input.weapon -ceq 'kinetic') 'Kinetic weapon-packet registry entry resolved the wrong fixture.'
    Assert-Contract ([int]$kineticWeaponPacket.expected.fire.tacticalPowerSpent -eq 1) 'Kinetic weapon packet must spend 1 TP.'

    Write-Host '       Phase A resource contracts: exact registered cases prove Kinetic fire and held fire spend/earmark 1 TP; unused holds release correctly.'
}

function Test-PowerStudy {
    $schema = Read-Json 'docs/design/player_technology/tl1_power_envelope_calibration_schema_v0_2.json'
    $study = Read-Json 'src/StarCluster.ScenarioRunner/Scenarios/TL1Calibration/tl1-pe02-main-power-interception-correction-study.json'
    Assert-Contract ([string]$schema.'$id' -eq 'star-cluster-tl1-power-envelope-calibration-v2') 'Power schema ID mismatch.'
    Assert-Contract ([int]$schema.properties.variants.minItems -eq 294 -and [int]$schema.properties.variants.maxItems -eq 294) 'Power schema must require 294 variants.'
    Assert-Contract ([string]$study.schemaVersion -eq 'star-cluster-tl1-power-envelope-calibration-v2') 'Power study schemaVersion mismatch.'
    Assert-Contract ([string]$study.id -eq 'tl1-pe02-main-power-interception-correction-study') 'Power study ID mismatch.'
    Assert-Contract ([int]$study.masterSeed -eq 330100 -and [int]$study.trialsPerVariant -eq 10000) 'Power study seed/trial contract mismatch.'
    $variants = @($study.variants)
    Assert-Contract ($variants.Count -eq 294) "Power study has $($variants.Count) variants, expected 294."
    $expectedCategories = @{
        'accepted-control'=6; 'reactor-sweep'=40; 'single-consumer'=64; 'layered-sweep'=64;
        'power-source-overlay'=60; 'overload-boundary'=30; 'held-interception'=30
    }
    foreach ($category in $expectedCategories.Keys) {
        $actual = @($variants | Where-Object { [string]$_.category -eq $category }).Count
        Assert-Contract ($actual -eq $expectedCategories[$category]) "Category $category has $actual variants; expected $($expectedCategories[$category])."
    }
    $focused = @($variants | Where-Object { [string]$_.category -in @('reactor-sweep','single-consumer','layered-sweep') })
    $outputs = @($focused | ForEach-Object { [int]$_.sideA.reactorOutput; [int]$_.sideB.reactorOutput } | Sort-Object -Unique)
    Assert-Contract (($outputs -join ',') -eq '3,4,5,6') "Focused Reactor outputs are $($outputs -join ','), expected 3,4,5,6."
    foreach ($variant in $variants) {
        foreach ($side in @($variant.sideA,$variant.sideB)) {
            Assert-Contract ([int]$side.auxiliaryReactorOutput -in @(0,1)) "Variant $($variant.id) uses non-TL1 Auxiliary output $($side.auxiliaryReactorOutput)."
        }
    }
    $byId = @{}
    foreach ($variant in $variants) {
        Assert-Contract (-not $byId.ContainsKey([string]$variant.id)) "Duplicate variant ID $($variant.id)."
        $byId[[string]$variant.id] = $variant
    }
    foreach ($variant in $variants) {
        $pair = [string]$variant.pairId
        if ([string]::IsNullOrWhiteSpace($pair)) { continue }
        Assert-Contract ($byId.ContainsKey($pair)) "Variant $($variant.id) references missing pair $pair."
        $partner = $byId[$pair]
        Assert-Contract ([string]$partner.pairId -eq [string]$variant.id) "Pair $($variant.id)/$pair is not reciprocal."
        $a = $variant.sideA | ConvertTo-Json -Depth 50 -Compress
        $b = $variant.sideB | ConvertTo-Json -Depth 50 -Compress
        $pa = $partner.sideA | ConvertTo-Json -Depth 50 -Compress
        $pb = $partner.sideB | ConvertTo-Json -Depth 50 -Compress
        Assert-Contract ($a -eq $pb -and $b -eq $pa) "Pair $($variant.id)/$pair is not an exact side swap."
    }
    foreach ($id in @('pe-reactor-energy-standard-r2-p3','pe-single-energy-epds-r2-p5','pe-layer-energy-full-defense-r2-p5','pe-overlay-aux-a-r2-p4','pe-overload-overcapacity-r2-p1','pe-held-kinetic-standard-r2-p1','pe-held-pds-saturation-r2-p5')) {
        Assert-Contract ($byId.ContainsKey($id)) "Required power-correction variant $id is missing."
    }
    Write-Host '       TL1 power-correction study: 294 variants, exact categories, outputs 3-6, +1 Auxiliary overlays, overloads, Held Main, and reciprocal pairs verified.'
}

function Test-TestSources {
    $facts=0; $theories=0; $inline=0
    foreach ($file in Get-ChildItem -LiteralPath (Get-RepoPath 'tests') -Filter '*.cs' -Recurse -File) {
        $text = Get-Content -LiteralPath $file.FullName -Raw
        $facts += ([regex]::Matches($text,'\[Fact\]')).Count
        $theories += ([regex]::Matches($text,'\[Theory\]')).Count
        $inline += ([regex]::Matches($text,'\[InlineData\(')).Count
    }
    Assert-Contract ($facts -eq 594 -and $theories -eq 20 -and $inline -eq 80 -and ($facts+$inline) -eq 674) "Test cardinality $facts/$theories/$inline/$($facts+$inline), expected 594/20/80/674."
    $power = Get-Text 'tests/StarCluster.Tests/Combat/Power/Tl1TacticalPowerCompletionTests.cs'
    Assert-Contract (([regex]::Matches($power,'\[Fact\]')).Count -eq 32) 'Checkpoint 33 Tactical Power test source must contain 32 facts.'
    foreach ($marker in @('Held_main_resolves_before_pds_and_preserves_pds_ammunition_on_success','Pds_attempts_a_flight_that_survives_held_main','Held_kinetic_interception_earmarks_and_spends_one_power','Kinetic_main_fire_spends_one_tactical_power','Kinetic_main_cannot_fire_without_tactical_power','Missile_launch_remains_zero_power','Tl1_shield_overcapacity_adds_one_temporary_point_per_activation','Operational_tl1_auxiliary_reactor_adds_one_power','Degraded_tl1_auxiliary_reactor_adds_no_tactical_power')) {
        Assert-Contract ($power.Contains($marker)) "Power tests missing $marker."
    }
    Write-Host '       Checkpoint 33 test sources: 32 focused Tactical Power facts and 674 total discovered cases verified.'
}

function Test-SourceContracts {
    $sim = Get-Text 'src/StarCluster.Core/Combat/DirectFire/Tl1PowerEnvelopeSimulator.cs'
    foreach ($marker in @('ShieldOvercapacityAmount = 1','Held Main engages at the longer interception window','new AttackPacket(3, 1, 0),','profile.Ammunition')) {
        Assert-Contract ($sim.Contains($marker)) "Power simulator missing $marker."
    }
    $heldIndex = $sim.IndexOf('if (ResolveHeldInterception')
    $pdsIndex = $sim.IndexOf('if (ResolvePdsAgainstMissile')
    Assert-Contract ($heldIndex -ge 0 -and $pdsIndex -gt $heldIndex) 'Held Main must be invoked before PDS in missile-impact resolution.'
    $kineticBlock = [regex]::Match($sim,'WeaponFamily\.Kinetic,[\s\S]{0,180}?new AttackPacket\(3, 1, 0\),\s*1,\s*1,').Success
    Assert-Contract ($kineticBlock) 'Power simulator Kinetic profile must cost 1 TP and 1 ammunition.'
    foreach ($relative in @('src/StarCluster.Core/Combat/DirectFire/Tl1KineticDuelSimulator.cs','src/StarCluster.Core/Combat/DirectFire/Tl1KineticMirrorDuel.cs','src/StarCluster.Core/Combat/DirectFire/Tl1WeaponMatrixSimulator.cs','src/StarCluster.Core/Combat/DirectFire/Tl1EnergyDuelSimulator.cs','src/StarCluster.ScenarioRunner/TL1PhaseB/Tl1PhaseBRunner.cs','tests/StarCluster.Tests/Combat/DirectFire/Tl1DirectFireAccuracyTests.cs','tests/StarCluster.Tests/Combat/Weapons/WeaponStateTests.cs')) {
        $text = Get-Text $relative
        Assert-Contract (-not [regex]::IsMatch($text,'WeaponFamily\.Kinetic,[\s\S]{0,240}?new AttackPacket\([^)]*\),\s*(?:tacticalPowerCost:\s*)?0,\s*(?:ammunitionCost:\s*)?1')) "$relative retains a zero-power Kinetic weapon profile."
    }
    $weaponStateTests = Get-Text 'tests/StarCluster.Tests/Combat/Weapons/WeaponStateTests.cs'
    Assert-Contract ([regex]::IsMatch($weaponStateTests,'WeaponFamily\.Missile,[\s\S]{0,180}?tacticalPowerCost:\s*0,\s*ammunitionCost:\s*1')) 'WeaponStateTests Missile Launcher fixture must retain zero launch power and one ammunition.'
    Assert-Contract (-not [regex]::IsMatch($weaponStateTests,'WeaponFamily\.Missile,[\s\S]{0,180}?tacticalPowerCost:\s*[1-9]')) 'WeaponStateTests Missile Launcher fixture must not acquire Tactical Power cost.'
    $baselineFactory = Get-Text 'src/StarCluster.ScenarioRunner/TL1/Tl1BaselineFactory.cs'
    Assert-Contract ([regex]::IsMatch($baselineFactory,'WeaponFamily\.Missile,[\s\S]{0,420}?baseline\.GetInt\("missile_launch_power"\)')) 'Authoritative Missile Launcher construction must read missile_launch_power from the zero-TP baseline value.'
    $runner = Get-Text 'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1PowerEnvelopeCalibrationRunner.cs'
    $runnerContractRegistry = [ordered]@{
        VariantCount = 'private\s+const\s+int\s+RequiredVariantCount\s*=\s*294\s*;'
        ReactorSweep = 'outputs\.SequenceEqual\(Enumerable\.Range\(3,\s*4\)\)'
        AuxiliaryOutput = 'auxiliaryOutputs\.SequenceEqual\(new\[\]\s*\{\s*1\s*\}\)'
        HeldKineticBoundary = 'RequireVariant\(study,\s*"pe-held-kinetic-standard-r2-p1"\)'
        HeldPdsSaturationBoundary = 'RequireVariant\(study,\s*"pe-held-pds-saturation-r2-p5"\)'
    }
    foreach ($contractName in $runnerContractRegistry.Keys) {
        Assert-Contract ([regex]::IsMatch($runner, $runnerContractRegistry[$contractName])) "Correction runner semantic contract missing: $contractName."
    }
    $program = Get-Text 'src/StarCluster.ScenarioRunner/Program.cs'
    foreach ($marker in @('tl1-pe02-main-power-interception-correction-study.json','checkpoint-33-tl1-power-correction-calibration')) {
        Assert-Contract ($program.Contains($marker)) "Program defaults missing $marker."
    }
    Write-Host '       C# structural contracts: corrected Kinetic power, Held-before-PDS order, overcapacity, Auxiliary output, runner counts, and defaults verified.'
}

function Test-DocumentsAndWorkbook {
    $activeConcepts = @(Get-ChildItem -LiteralPath (Get-RepoPath 'docs') -Filter 'Star_Cluster_Game_Concept_v*.docx' -File)
    Assert-Contract ($activeConcepts.Count -eq 1 -and $activeConcepts[0].Name -eq 'Star_Cluster_Game_Concept_v0.4e.docx') 'Active Concept set is invalid.'
    $activeRunbooks = @(Get-ChildItem -LiteralPath (Get-RepoPath 'docs/validation') -Filter 'Checkpoint_*.md' -File)
    Assert-Contract ($activeRunbooks.Count -eq 1 -and $activeRunbooks[0].Name -eq 'Checkpoint_33_TL1_Main_Weapon_Power_And_Interception_Order_Correction.md') 'Active validation runbook set is invalid.'
    $requiredText = @{
        'README.md'=@('Checkpoint 33','v0.4e','674 engine-independent tests','294 main-power/interception correction variants','does not require Python');
        'Checkpoint_33_Readme.txt'=@('complete replacement repository','Kinetic Cannon','Held Main before PDS','294 main-power/interception correction variants');
        'docs/checkpoints/Checkpoint_33_TL1_Main_Weapon_Power_And_Interception_Order_Correction.md'=@('Kinetic Cannon fire spends 1 TP','Held Main resolves before PDS','294 variants');
        'docs/validation/Checkpoint_33_TL1_Main_Weapon_Power_And_Interception_Order_Correction.md'=@('674 engine-independent tests','294 main-power/interception correction variants','idempotent');
        'docs/design/player_technology/TL1_Main_Weapon_Power_And_Interception_Correction_Plan_v0_1.md'=@('1 temporary Shield Point','+1 TP while Operational','294 variants','3-6 TP');
        'docs/Prototype_TODO.md'=@('Checkpoint 33 status','Kinetic main fire','Held Main before PDS')
    }
    foreach ($relative in $requiredText.Keys) {
        $text=Get-Text $relative
        foreach ($marker in $requiredText[$relative]) { Assert-Contract ($text.Contains($marker)) "$relative missing $marker." }
    }
    $concept = Get-DocxText 'docs/Star_Cluster_Game_Concept_v0.4e.docx'
    foreach ($marker in @('Checkpoint 33 - TL1 Main-Weapon Power and Interception-Order Correction','Held Main resolves before PDS','D-279','D-285','END OF DRAFT v0.4e')) {
        Assert-Contract ($concept.Contains($marker)) "Concept missing $marker."
    }
    $xlsx = Get-XlsxXmlText 'docs/design/player_technology/StarCluster_Player_TL_Framework_Draft_v0_13.xlsx'
    foreach ($marker in @('Checkpoint 33 Correction','294 variants x 10,000 trials','D-285','Held Main then PDS','Operational +1 / Degraded +0','standard 1 TP')) {
        Assert-Contract ($xlsx.Contains($marker)) "Workbook missing $marker."
    }
    Write-Host '       Documentation and workbook: Concept v0.4e, Decisions through D-285, v0.13 correction sheet, and active-runbook normalization verified.'
}

function Test-PowerShellHarness {
    $directory = Get-RepoPath 'tools/checkpoints/checkpoint-33'
    foreach ($name in @('apply_checkpoint_33.ps1','build_checkpoint_33_release.ps1','validate_checkpoint_33_release.ps1','static_preflight_checkpoint_33.ps1','checkpoint_runtime_registry.ps1')) {
        Assert-Contract (Test-Path -LiteralPath (Join-Path $directory $name) -PathType Leaf) "Checkpoint harness missing $name."
    }
    $registry = Get-Text 'tools/checkpoints/checkpoint-33/checkpoint_runtime_registry.ps1'
    foreach ($marker in @('Register-CheckpointOperation','Assert-CheckpointOperationRegistry','Invoke-CheckpointOperation','Test-CheckpointOperationRegistry')) {
        Assert-Contract ($registry.Contains($marker)) "Operation registry missing $marker."
    }
    foreach ($relative in @('tools/checkpoints/checkpoint-33/apply_checkpoint_33.ps1','tools/checkpoints/checkpoint-33/build_checkpoint_33_release.ps1','tools/checkpoints/checkpoint-33/validate_checkpoint_33_release.ps1')) {
        $text = Get-Text $relative
        Assert-Contract ($text.Contains('checkpoint_runtime_registry.ps1')) "$relative does not load the operation registry."
        Assert-Contract (-not $text.Contains('python')) "$relative reintroduces a Python runtime dependency."
    }
    $preflight = Get-Text 'tools/checkpoints/checkpoint-33/static_preflight_checkpoint_33.ps1'
    foreach ($marker in @('Get-RegisteredPhaseACase','UnusedKineticHold','a06-c02','TriggeredKineticHold','a07-c02','KineticWeaponPacket','a11-c01','runnerContractRegistry','VariantCount','ReactorSweep','AuxiliaryOutput','HeldKineticBoundary','HeldPdsSaturationBoundary')) {
        Assert-Contract ($preflight.Contains($marker)) "Static preflight semantic registry is missing $marker."
    }
    Assert-Contract (-not $preflight.Contains("[string]`$_.id -match 'kinetic'")) 'Static preflight retains the obsolete heuristic Kinetic case selector.'
    $obsoleteRunnerMessagePattern = 'Correction runner missing ' + '$marker.'
    Assert-Contract (-not $preflight.Contains($obsoleteRunnerMessagePattern)) 'Static preflight retains narrative runner-message matching instead of semantic source contracts.'

    $apply = Get-Text 'tools/checkpoints/checkpoint-33/apply_checkpoint_33.ps1'
    foreach ($marker in @('[1/15]','[15/15]','Running 674 engine-independent tests','Running 294 TL1 main-power/interception correction variants','Engine-independent tests passed: 674.')) {
        Assert-Contract ($apply.Contains($marker)) "Apply script missing $marker."
    }
    Write-Host '       PowerShell operation registry and native preflight are defined and used; no Python runtime is required.'
}

Test-Manifest
Test-BaselineAndLinkedJson
Test-PhaseAContracts
Test-PowerStudy
Test-TestSources
Test-SourceContracts
Test-DocumentsAndWorkbook
Test-PowerShellHarness
Write-Output 'Checkpoint 33 static preflight completed successfully.'
