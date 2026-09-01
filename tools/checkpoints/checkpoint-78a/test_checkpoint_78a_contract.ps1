[CmdletBinding()]
param()

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
function Assert-True {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) { throw $Message }
}
function Read-Text {
    param([string]$RelativePath)
    $path = Join-Path $repositoryRoot $RelativePath
    Assert-True (Test-Path -LiteralPath $path -PathType Leaf) "Required text file '$RelativePath' is missing."
    $text = [System.IO.File]::ReadAllText($path)
    Assert-True ($null -ne $text) "Required text file '$RelativePath' returned a null text value."
    return [string]$text
}
function Normalize-DocumentationText {
    param([string]$Text)
    if ($null -eq $Text) { return '' }
    return ([string]$Text).Replace('**', '').Replace('__', '')
}
function Read-Json {
    param([string]$RelativePath)
    $text = Read-Text $RelativePath
    Assert-True (-not [string]::IsNullOrWhiteSpace($text)) "Required JSON file '$RelativePath' is empty."
    return ($text | ConvertFrom-Json)
}
function Read-DocxText {
    param([string]$RelativePath)
    $path = Join-Path $repositoryRoot $RelativePath
    Assert-True (Test-Path -LiteralPath $path -PathType Leaf) "Required DOCX '$RelativePath' is missing."

    Add-Type -AssemblyName System.IO.Compression.FileSystem -ErrorAction Stop | Out-Null
    $archive = $null
    try {
        $archive = [System.IO.Compression.ZipFile]::OpenRead($path)
        $entry = $archive.GetEntry('word/document.xml')
        Assert-True ($null -ne $entry) "DOCX '$RelativePath' is missing word/document.xml."
        $stream = $null
        $reader = $null
        try {
            $stream = $entry.Open()
            $reader = New-Object System.IO.StreamReader($stream)
            $xmlText = $reader.ReadToEnd()
            Assert-True (-not [string]::IsNullOrWhiteSpace($xmlText)) "DOCX '$RelativePath' has empty word/document.xml content."
            [xml]$xml = $xmlText
            Assert-True ($null -ne $xml.DocumentElement) "DOCX '$RelativePath' document.xml has no document element."
            $text = [string]$xml.DocumentElement.InnerText
            Assert-True (-not [string]::IsNullOrWhiteSpace($text)) "DOCX '$RelativePath' produced no document text."
            return $text
        }
        finally {
            if ($null -ne $reader) { $reader.Dispose() }
            elseif ($null -ne $stream) { $stream.Dispose() }
        }
    }
    finally {
        if ($null -ne $archive) { $archive.Dispose() }
    }
}
function Assert-ZipEntry {
    param([string]$RelativePath, [string]$EntryName)
    $path = Join-Path $repositoryRoot $RelativePath
    Assert-True (Test-Path -LiteralPath $path -PathType Leaf) "Required archive '$RelativePath' is missing."
    Add-Type -AssemblyName System.IO.Compression.FileSystem -ErrorAction Stop | Out-Null
    $archive = $null
    try {
        $archive = [System.IO.Compression.ZipFile]::OpenRead($path)
        Assert-True ($null -ne $archive.GetEntry($EntryName)) "Archive '$RelativePath' is missing '$EntryName'."
    }
    finally {
        if ($null -ne $archive) { $archive.Dispose() }
    }
}

Write-Host '       Validating native-dependency declarations...'
$guard = Join-Path $repositoryRoot 'tools\checkpoints\Test-NativeAcceptanceDependencies.ps1'
$normalRel = 'tools/calibration/checkpoints/checkpoint-78a.json'
$deepRel = 'tools/calibration/checkpoints/checkpoint-78a-deep-calibration.json'
$guardedPs = @(
    'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
    'tools/checkpoints/checkpoint-78a/apply_checkpoint_78a.ps1',
    'tools/checkpoints/checkpoint-78a/test_checkpoint_78a_contract.ps1',
    'tools/calibration/run_calibration_checkpoint.ps1'
)
$guardedDefs = @($normalRel, $deepRel)
& $guard -RepositoryRoot $repositoryRoot -PowerShellPaths $guardedPs -CheckpointDefinitionPaths $guardedDefs

Write-Host '       Validating Checkpoint 78a definitions and unchanged workload accounting...'
$normal = Read-Json $normalRel
$deep = Read-Json $deepRel
Assert-True ([string]$normal.checkpointId -eq '78a' -and [string]$deep.checkpointId -eq '78a') 'Checkpoint 78a definition ID mismatch.'
Assert-True ([string]$normal.manifestFile -eq 'CHECKPOINT_78A_SHA256SUMS.txt' -and [string]$deep.manifestFile -eq 'CHECKPOINT_78A_SHA256SUMS.txt') 'Checkpoint 78a manifest binding mismatch.'
Assert-True ([string]$normal.outputRoot -eq 'out/checkpoint-78a' -and [string]$deep.outputRoot -eq 'out/checkpoint-78a-deep-calibration') 'Checkpoint 78a output-root binding mismatch.'
Assert-True ((@($normal.nativeDependencyPrecheck.powerShellPaths) -join '|') -eq ($guardedPs -join '|')) 'Checkpoint 78a normal native-dependency PowerShell path binding mismatch.'
Assert-True ((@($deep.nativeDependencyPrecheck.powerShellPaths) -join '|') -eq ($guardedPs -join '|')) 'Checkpoint 78a deep native-dependency PowerShell path binding mismatch.'
Assert-True ((@($normal.nativeDependencyPrecheck.checkpointDefinitionPaths) -join '|') -eq ($guardedDefs -join '|')) 'Checkpoint 78a normal native-dependency definition binding mismatch.'
Assert-True ((@($deep.nativeDependencyPrecheck.checkpointDefinitionPaths) -join '|') -eq ($guardedDefs -join '|')) 'Checkpoint 78a deep native-dependency definition binding mismatch.'
Assert-True (@($normal.stages).Count -eq 8 -and @($deep.stages).Count -eq 30) 'Checkpoint 78a stage-count mismatch.'
Assert-True ([int]$normal.checkpointMetrics.stageCount -eq 8 -and [int]$normal.checkpointMetrics.monteCarloVariantCount -eq 0 -and [int]$normal.checkpointMetrics.trialsAtDefault -eq 0) 'Checkpoint 78a normal suite must contain no Monte Carlo workload.'
Assert-True ([int]$deep.checkpointMetrics.stageCount -eq 30 -and [int]$deep.checkpointMetrics.monteCarloVariantCount -eq 1598 -and [int]$deep.checkpointMetrics.trialsAtDefault -eq 15980000) 'Checkpoint 78a Deep Calibration workload mismatch.'
$expectedStages = @('deterministic','tl1-phase-a','tl1-phase-b','tl1-installation-space-envelope','tl1-sensor-ew-foundation','auxiliary-resource-endurance','checkpoint-53-resource-semantics-lock','runner-self-tests')
$stageIds = @($normal.stages | ForEach-Object { [string]$_.id })
Assert-True (($stageIds -join '|') -eq ($expectedStages -join '|')) 'Checkpoint 78a normal stage ordering mismatch.'
$normalSelfTest = @($normal.stages | Where-Object { [string]$_.id -eq 'runner-self-tests' })
Assert-True ($normalSelfTest.Count -eq 1 -and [int]$normalSelfTest[0].metrics.selfTestCount -eq 47) 'Checkpoint 78a ScenarioRunner self-test count mismatch.'
foreach ($definition in @($normal, $deep)) {
    foreach ($docPath in @($definition.documentation)) {
        Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot ([string]$docPath)) -PathType Leaf) "Checkpoint 78a definition references missing documentation/input '$docPath'."
    }
}

Write-Host '       Validating Technology Architecture Matrix v1 structure and research ownership...'
$matrixRel = 'docs/archive/player_technology/pre-cp165-active/technology_architecture_matrix_v1.json'
$matrix = Read-Json $matrixRel
Assert-True ([int]$matrix.schemaVersion -eq 1 -and [string]$matrix.id -eq 'technology-architecture-matrix-v1') 'Technology Architecture Matrix v1 identity/schema mismatch.'
Assert-True ([string]$matrix.status -eq 'design_hypothesis_not_production_data' -and -not [bool]$matrix.authority.productionDataChanged -and -not [bool]$matrix.authority.automaticPromotion) 'Matrix v1 must remain a non-production, human-promoted design roadmap.'
Assert-True (@($matrix.tiers).Count -eq 9) 'Matrix v1 must define exactly TL1 through TL9.'
$matrixTls = @($matrix.tiers | ForEach-Object { [int]$_.technologyLevel })
Assert-True (($matrixTls -join '|') -eq '1|2|3|4|5|6|7|8|9') 'Matrix v1 TL ordering mismatch.'
Assert-True ([string]$matrix.researchCategoryOwnership.tacticalComputer -eq 'Computing / Fire Control') 'Tactical Computer research-category ownership mismatch.'
Assert-True ([string]$matrix.researchCategoryOwnership.sensor -eq 'Sensors / EW' -and [string]$matrix.researchCategoryOwnership.ecm -eq 'Sensors / EW' -and [string]$matrix.researchCategoryOwnership.eccm -eq 'Sensors / EW') 'Sensor/ECM/ECCM must remain progression streams inside Sensors / EW.'
Assert-True ([string]$matrix.researchCategoryOwnership.note -match 'do not create additional player-visible research categories') 'Matrix v1 must explicitly reject accidental research-tree proliferation.'

$tl1Matrix = @($matrix.tiers | Where-Object { [int]$_.technologyLevel -eq 1 })[0]
$tl2Matrix = @($matrix.tiers | Where-Object { [int]$_.technologyLevel -eq 2 })[0]
Assert-True ([string]$tl1Matrix.tacticalComputer.status -eq 'current_working' -and [int]$tl1Matrix.tacticalComputer.approximateTrackPenaltyPp -eq -25 -and [int]$tl1Matrix.tacticalComputer.ordinaryTargetingAssistanceOperationalPp -eq 10 -and [int]$tl1Matrix.tacticalComputer.ordinaryTargetingAssistanceDegradedPp -eq 5) 'Matrix v1 TL1 Tactical Computer anchor mismatch.'
Assert-True ([int]$tl1Matrix.sensor.sensorDiscriminationResistance -eq 0 -and [int]$tl1Matrix.sensor.sameHexBurnThroughResistance -eq 1) 'Matrix v1 TL1 Sensor discrimination/burn-through anchor mismatch.'
Assert-True ([int]$tl1Matrix.ecm.normalRatingCeiling -eq 1 -and [int]$tl1Matrix.ecm.tpPerRating -eq 1 -and [int]$tl1Matrix.eccm.normalRatingCeiling -eq 1 -and [int]$tl1Matrix.eccm.tpPerRating -eq 1) 'Matrix v1 TL1 ECM/ECCM anchor mismatch.'
Assert-True ([string]$tl1Matrix.sensor.rangeFixture.status -eq 'candidate_fixture_not_production') 'Balanced-0 TL1 range envelope must remain a candidate fixture, not production data.'

Assert-True ([string]$tl2Matrix.tacticalComputer.status -eq 'legacy_candidate' -and [int]$tl2Matrix.tacticalComputer.ordinaryTargetingAssistanceOperationalPp -eq 12 -and [int]$tl2Matrix.tacticalComputer.approximateTrackPenaltyPp -eq -25) 'Matrix v1 TL2 Tactical Computer candidate must retain legacy +12 targeting and hold degraded fire at -25.'
Assert-True ([string]$tl2Matrix.sensor.status -eq 'hypothesis' -and [int]$tl2Matrix.sensor.sensorDiscriminationResistance -eq 1 -and [string]$tl2Matrix.sensor.rangeFixture.status -eq 'hold_tl1_balanced0_candidate_for_isolation') 'Matrix v1 TL2 Sensor hypothesis mismatch.'
Assert-True ([int]$tl2Matrix.ecm.normalRatingCeiling -eq 2 -and [int]$tl2Matrix.ecm.tpPerRating -eq 1 -and [string]$tl2Matrix.ecm.overload -eq 'defer_in_first_tl2_isolation_study') 'Matrix v1 TL2 ECM hypothesis mismatch.'
Assert-True ([int]$tl2Matrix.eccm.normalRatingCeiling -eq 2 -and [int]$tl2Matrix.eccm.tpPerRating -eq 1 -and [string]$tl2Matrix.eccm.overload -eq 'defer_in_first_tl2_isolation_study') 'Matrix v1 TL2 ECCM hypothesis mismatch.'
foreach ($tier in @($matrix.tiers | Where-Object { [int]$_.technologyLevel -ge 3 })) {
    Assert-True ([string]$tier.tacticalComputer.status -eq 'deferred' -and [string]$tier.sensor.status -eq 'deferred' -and [string]$tier.ecm.status -eq 'deferred' -and [string]$tier.eccm.status -eq 'deferred') "Matrix v1 TL$([int]$tier.technologyLevel) must remain conceptual/deferred rather than numerically promoted."
}

Write-Host '       Validating TL2 candidate jamming arithmetic...'
$examples = @($matrix.tl2CandidateInteractionExamples)
Assert-True ($examples.Count -eq 5) 'Matrix v1 must retain five declared TL2 EW interaction examples.'
foreach ($example in $examples) {
    $expected = [Math]::Max(0, [int]$example.ecm - [int]$example.eccm - [int]$example.sensorResistance - [int]$example.burnThrough)
    Assert-True ([int]$example.effectiveJammingMargin -eq $expected) "Matrix v1 jamming arithmetic mismatch for '$([string]$example.case)'."
}
$expectedMargins = @(0,1,0,0,1)
$actualMargins = @($examples | ForEach-Object { [int]$_.effectiveJammingMargin })
Assert-True (($actualMargins -join '|') -eq ($expectedMargins -join '|')) 'Matrix v1 TL2 interaction margins no longer match the intended tall/wide hypothesis.'

Write-Host '       Validating TL1 runtime authority and proving TL2 remains non-production...'
$computerData = Read-Json 'docs/archive/player_technology/pre-cp165-active/tactical_computer_fire_control_profiles_v0_1.json'
Assert-True ([int]$computerData.schemaVersion -eq 1 -and @($computerData.profiles).Count -eq 1) 'Tactical Computer fire-control catalog must still contain only the TL1 profile.'
$tl1 = $computerData.profiles[0]
Assert-True ([int]$tl1.technologyLevel -eq 1 -and [int]$tl1.approximateTrackDirectFireAccuracyPenaltyPercentagePoints -eq 25) 'Production/working TL1 Tactical Computer degraded-fire value must remain 25 percentage points.'
Assert-True (@($computerData.profiles | Where-Object { [int]$_.technologyLevel -eq 2 }).Count -eq 0) 'Checkpoint 78 must not add a TL2 production Tactical Computer fire-control profile.'
Assert-True ([bool]$tl1.requiresExplicitWeaponCapability -and -not [bool]$tl1.appliesToMissileTerminalAttacks) 'TL1 degraded-fire ownership boundaries mismatch.'
Assert-True ([string]$tl1.conditionMappingStatus -eq 'deferred') 'Tactical Computer damage-condition mapping must remain deferred.'
Assert-True ([bool]$computerData.guardrails.eccmCounterplayMustRemainEconomicallyRelevant -and [bool]$computerData.guardrails.revalidateWhenComputerEcmEccmOrSensorProgressionChanges) 'Tactical Computer/EW progression guardrails missing.'

$tl1Baseline = Import-Csv (Join-Path $repositoryRoot 'docs\archive\player_technology\pre-cp165-active\tl1_core_combat_numerical_baseline_v0_3.csv')
function Get-BaselineValue {
    param([string]$Metric)
    $row = @($tl1Baseline | Where-Object { [string]$_.parameter_id -eq $Metric })
    Assert-True ($row.Count -eq 1) "TL1 numerical baseline metric '$Metric' missing or duplicated."
    return [int]$row[0].value
}
Assert-True ((Get-BaselineValue 'ecm_max') -eq 1 -and (Get-BaselineValue 'eccm_max') -eq 1) 'Checkpoint 78a must not change TL1 normal ECM/ECCM ceilings.'

$weaponSource = Read-Text 'src/StarCluster.Core/Combat/DirectFire/DirectFireWeaponProfile.cs'
$computerSource = Read-Text 'src/StarCluster.Core/Combat/DirectFire/TacticalComputerFireControlProfile.cs'
$eligibilitySource = Read-Text 'src/StarCluster.Core/Combat/DirectFire/DirectFireTargetEligibility.cs'
Assert-True ($weaponSource.Contains('AllowsApproximateTrackFire') -and -not $weaponSource.Contains('ApproximateTrackAccuracyPenalty')) 'DirectFireWeaponProfile must continue to own permission but not the degraded-fire number.'
Assert-True ($computerSource.Contains('ApproximateTrackDirectFireAccuracyPenalty') -and $computerSource.Contains('SupportsApproximateTrackDirectFire')) 'TacticalComputerFireControlProfile degraded-fire rating missing.'
Assert-True ($eligibilitySource.Contains('weapon.AllowsApproximateTrackFire') -and $eligibilitySource.Contains('tacticalComputer is { SupportsApproximateTrackDirectFire: true }')) 'Direct-fire eligibility must continue to require both weapon permission and computer support.'
$gameMain = Read-Text 'src/StarCluster.Game/Scripts/Main.cs'
Assert-True (-not $gameMain.Contains('allowsApproximateTrackFire: true')) 'Checkpoint 78a must not enable degraded fire on the Godot production/demo main weapon.'
$productionApproximateEnable = Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'src') -Recurse -File -Filter '*.cs' | Where-Object { $_.FullName -notlike '*StarCluster.ScenarioRunner*' } | Select-String -SimpleMatch 'allowsApproximateTrackFire: true'
Assert-True (@($productionApproximateEnable).Count -eq 0) 'Checkpoint 78a must not enable degraded fire in production Core/Game weapon construction.'

Write-Host '       Validating Concept v0.6q and focused architecture synchronization...'
$conceptText = Read-DocxText 'docs/Star_Cluster_Game_Concept_v0.6q.docx'
Assert-True ($conceptText.Contains('8.6 Technology architecture matrices and staged calibration')) 'Concept v0.6q is missing the staged Technology Architecture Matrix section.'
Assert-True ($conceptText.Contains('whole-ladder TL1-TL9 Technology Architecture Matrix')) 'Concept v0.6q is missing the whole-ladder roadmap rule.'
Assert-True ($conceptText.Contains('legacy candidates carried forward from older evidence')) 'Concept v0.6q is missing matrix status semantics.'
Assert-True ($conceptText.Contains('Tactical Computer remains owned by Computing / Fire Control')) 'Concept v0.6q is missing Tactical Computer research-category ownership.'
Assert-True ($conceptText.Contains('Sensor, ECM, and ECCM remain distinct streams within the existing Sensors / EW discipline')) 'Concept v0.6q is missing Sensor/EW progression-stream ownership.'
Assert-True ($conceptText.Contains('legacy +12 percentage-point ordinary Tactical Computer targeting value') -and $conceptText.Contains('degraded-fire penalty initially remains -25') -and $conceptText.Contains('Sensor Discrimination Resistance 1') -and $conceptText.Contains('normal ECM/ECCM rating ceilings of 2')) 'Concept v0.6q is missing the explicitly provisional TL2 candidate package.'
Assert-True ($conceptText.Contains('None of those TL2 candidate values is production data')) 'Concept v0.6q must state that TL2 Matrix values are non-production candidates.'
Assert-True ($conceptText.Contains('Degraded-fire fallback guardrail') -or $conceptText.Contains('degraded-fire fallback guardrail')) 'Concept v0.6q is missing the degraded-fire/ECCM guardrail.'
Assert-True ($conceptText.Contains('Technology Architecture Matrix') -and $conceptText.Contains('Progression stream')) 'Concept v0.6q glossary additions are missing.'
Assert-True ($conceptText.Contains('C-052') -and $conceptText.Contains('C-053')) 'Concept v0.6q decision-register additions are missing.'
Assert-True (-not ($conceptText -match 'Checkpoint\s+7[0-9]')) 'Active Concept must not contain checkpoint-history prose for Checkpoints 70-79.'

$matrixMd = Read-Text 'docs/design/player_technology/Technology_Architecture_Matrix_v1.md'
Assert-True ($matrixMd.Contains('design hypothesis, not production data') -and $matrixMd.Contains('Whole-ladder architecture') -and $matrixMd.Contains('TL2 first-pass candidate package')) 'Matrix v1 Markdown authority/status sections are incomplete.'
Assert-True ($matrixMd.Contains('Firm-only') -or $matrixMd.Contains('Firm-terminal')) 'Matrix v1 must preserve missile/direct-fire architecture separation.'
Assert-ZipEntry 'docs/design/player_technology/StarCluster_Technology_Architecture_Matrix_v1.xlsx' 'xl/workbook.xml'
Assert-ZipEntry 'docs/design/player_technology/StarCluster_Technology_Architecture_Matrix_v1.xlsx' 'xl/worksheets/sheet1.xml'

$technologyReadme = Read-Text 'docs/design/player_technology/README.md'
$designReadme = Read-Text 'docs/design/README.md'
$technologyArchitecture = Read-Text 'docs/design/Technology_Calibration_And_Simulation_Architecture.md'
$tacticalComputerArchitecture = Read-Text 'docs/design/player_technology/Tactical_Computer_Degraded_Fire_Architecture_v0_1.md'
Assert-True ($technologyReadme.Contains('Technology_Architecture_Matrix_v1.md') -and $technologyReadme.Contains('Legacy candidate') -and $technologyReadme.Contains('not a production catalog')) 'Player technology README is not synchronized with Matrix v1.'
$technologyReadmeSemantic = Normalize-DocumentationText $technologyReadme
Assert-True ($technologyReadmeSemantic.Contains('Historical `Player_TL1_TL9_Technology_Architecture_*`') -and $technologyReadmeSemantic.Contains('not current authority')) 'Historical technology tables are not clearly separated from Matrix v1 authority.'
Write-Host '       Historical authority wording: markup-normalized semantic check passed.'
Assert-True ($designReadme.Contains('Technology_Architecture_Matrix_v1.md') -and $designReadme.Contains('sequential TL-by-TL promotion')) 'Design authority index is missing Matrix v1.'
Assert-True ($technologyArchitecture.Contains('Whole-ladder architecture roadmap') -and $technologyArchitecture.Contains('current/working') -and $technologyArchitecture.Contains('legacy candidate') -and $technologyArchitecture.Contains('does not promote those values into runtime data')) 'Technology calibration architecture is not synchronized with the matrix lifecycle.'
$tacticalComputerArchitectureSemantic = Normalize-DocumentationText $tacticalComputerArchitecture
Assert-True ($tacticalComputerArchitectureSemantic.Contains('Technology_Architecture_Matrix_v1.md') -and $tacticalComputerArchitectureSemantic.Contains('holds the TL1 -25 percentage-point degraded-fire rating into the first TL2 candidate')) 'Tactical Computer architecture is not synchronized with Matrix v1.'

$missileDoc = Read-Text 'docs/design/Missile_Guidance_Datalink_Sensor_And_Seeker_Architecture.md'
Assert-True ($missileDoc.Contains('large barrage into the estimated target volume') -and $missileDoc.Contains('Ordinary missile profiles continue to require the legitimate Firm terminal solution')) 'Missile architecture must preserve Firm baseline and volume-saturation future capability.'
$missileTerminalTests = Read-Text 'tests/StarCluster.Tests/Combat/Missiles/MissileTerminalResolutionTests.cs'
Assert-True ($missileTerminalTests.Contains('PeerGuidanceCannotAuthorizeBaselineCommandGuidedTerminalAttack') -and $missileTerminalTests.Contains('SensorPlusSeekerRejectsRemoteApproximateCueWithoutLocalNavigationTrack')) 'Accepted missile terminal-guidance guardrail regressions are missing.'

Write-Host '       Validating active-document/archive hygiene...'
$activeConcepts = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs') -File -Filter 'Star_Cluster_Game_Concept_v*.docx')
Assert-True ($activeConcepts.Count -eq 1 -and $activeConcepts[0].Name -eq 'Star_Cluster_Game_Concept_v0.6q.docx') 'Exactly Concept v0.6q must remain active under docs/.'
Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot 'docs\archive\Star_Cluster_Game_Concept_v0.6p.docx') -PathType Leaf) 'Concept v0.6p must be archived.'
Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot 'docs\validation\archive\Checkpoint_77a_PowerShell_5_1_DOCX_Contract_Reader_Hotfix.md') -PathType Leaf) 'Checkpoint 77a validation runbook must be archived.'
$validationFiles = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs\validation') -File -Filter 'Checkpoint_*.md')
Assert-True ($validationFiles.Count -eq 1 -and $validationFiles[0].Name -eq 'Checkpoint_78a_Historical_Authority_Contract_Hotfix.md') 'Exactly one Checkpoint 78a active validation runbook must remain.'
$rootTxt = @(Get-ChildItem -LiteralPath $repositoryRoot -File -Filter '*.txt')
Assert-True ($rootTxt.Count -eq 1 -and $rootTxt[0].Name -eq 'CHECKPOINT_78A_SHA256SUMS.txt') 'Repository root must contain only CHECKPOINT_78A_SHA256SUMS.txt as .txt.'

Write-Host '       Matrix v1: whole-ladder roadmap with TL1 current, TL2 candidate/hypothesis, TL3-TL9 deferred.'
Write-Host '       TL2 first-pass hypothesis: +12 ordinary targeting candidate; degraded fire held -25; Sensor DR 1; ECM/ECCM ceiling 2 at 1 TP/rating.'
Write-Host '       Research ownership: Tactical Computer -> Computing / Fire Control; Sensor/ECM/ECCM -> Sensors / EW.'
Write-Host '       Production behavior unchanged; normal acceptance remains 8 deterministic stages / 0 Monte Carlo variants.'
Write-Host 'Checkpoint 78a contract validation passed.'
