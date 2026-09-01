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

function Assert-Sha256 {
    param([string]$RelativePath, [string]$Expected)
    $path = Join-Path $repositoryRoot $RelativePath
    Assert-True (Test-Path -LiteralPath $path -PathType Leaf) "Required frozen file '$RelativePath' is missing."
    $actual = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    Assert-True ($actual -eq $Expected) "Frozen file '$RelativePath' changed unexpectedly. Expected $Expected, got $actual."
}

function Get-Margin {
    param([int]$Ecm, [int]$Eccm, [int]$SensorDr, [int]$BurnThrough)
    return [Math]::Max(0, $Ecm - $Eccm - $SensorDr - $BurnThrough)
}

Write-Host '       Validating native-dependency declarations...'
$guard = Join-Path $repositoryRoot 'tools\checkpoints\Test-NativeAcceptanceDependencies.ps1'
$normalRel = 'tools/calibration/checkpoints/checkpoint-79.json'
$deepRel = 'tools/calibration/checkpoints/checkpoint-79-deep-calibration.json'
$guardedPs = @(
    'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
    'tools/checkpoints/checkpoint-79/apply_checkpoint_79.ps1',
    'tools/checkpoints/checkpoint-79/test_checkpoint_79_contract.ps1',
    'tools/calibration/run_calibration_checkpoint.ps1'
)
$guardedDefs = @($normalRel, $deepRel)
& $guard -RepositoryRoot $repositoryRoot -PowerShellPaths $guardedPs -CheckpointDefinitionPaths $guardedDefs

Write-Host '       Validating Checkpoint 79 definitions and workload accounting...'
$normal = Read-Json $normalRel
$deep = Read-Json $deepRel
Assert-True ([string]$normal.checkpointId -eq '79' -and [string]$deep.checkpointId -eq '79') 'Checkpoint 79 definition ID mismatch.'
Assert-True ([string]$normal.manifestFile -eq 'CHECKPOINT_79_SHA256SUMS.txt' -and [string]$deep.manifestFile -eq 'CHECKPOINT_79_SHA256SUMS.txt') 'Checkpoint 79 manifest binding mismatch.'
Assert-True ([string]$normal.outputRoot -eq 'out/checkpoint-79' -and [string]$deep.outputRoot -eq 'out/checkpoint-79-deep-calibration') 'Checkpoint 79 output-root binding mismatch.'
Assert-True ((@($normal.nativeDependencyPrecheck.powerShellPaths) -join '|') -eq ($guardedPs -join '|')) 'Checkpoint 79 normal native-dependency PowerShell path binding mismatch.'
Assert-True ((@($deep.nativeDependencyPrecheck.powerShellPaths) -join '|') -eq ($guardedPs -join '|')) 'Checkpoint 79 deep native-dependency PowerShell path binding mismatch.'
Assert-True ((@($normal.nativeDependencyPrecheck.checkpointDefinitionPaths) -join '|') -eq ($guardedDefs -join '|')) 'Checkpoint 79 normal native-dependency definition binding mismatch.'
Assert-True ((@($deep.nativeDependencyPrecheck.checkpointDefinitionPaths) -join '|') -eq ($guardedDefs -join '|')) 'Checkpoint 79 deep native-dependency definition binding mismatch.'
Assert-True (@($normal.stages).Count -eq 11 -and [int]$normal.checkpointMetrics.stageCount -eq 11) 'Checkpoint 79 normal stage-count mismatch.'
Assert-True ([int]$normal.checkpointMetrics.monteCarloVariantCount -eq 54 -and [int]$normal.checkpointMetrics.trialsAtDefault -eq 540000 -and [int]$normal.checkpointMetrics.smokeTrialsAtDefault -eq 54 -and [int]$normal.checkpointMetrics.totalTrialExecutionsAtDefault -eq 540054) 'Checkpoint 79 normal workload accounting mismatch.'
Assert-True (@($deep.stages).Count -eq 33 -and [int]$deep.checkpointMetrics.stageCount -eq 33 -and [int]$deep.checkpointMetrics.monteCarloVariantCount -eq 1652 -and [int]$deep.checkpointMetrics.trialsAtDefault -eq 16520000 -and [int]$deep.checkpointMetrics.smokeTrialsAtDefault -eq 108) 'Checkpoint 79 Deep Calibration workload accounting mismatch.'
$expectedStages = @('deterministic','tl1-phase-a','tl1-phase-b','tl1-installation-space-envelope','tl1-sensor-ew-foundation','tl2-sensor-ew-discrimination-preflight','tl2-sensor-ew-discrimination-smoke','tl2-sensor-ew-discrimination-isolation','auxiliary-resource-endurance','checkpoint-53-resource-semantics-lock','runner-self-tests')
$stageIds = @($normal.stages | ForEach-Object { [string]$_.id })
Assert-True (($stageIds -join '|') -eq ($expectedStages -join '|')) 'Checkpoint 79 normal stage ordering mismatch.'
$primary = $normal.primaryStudy
Assert-True ([string]$primary.id -eq 'tl2-itc06-sensor-ew-discrimination-isolation' -and [int]$primary.variantCount -eq 54) 'Checkpoint 79 primary-study binding mismatch.'
$preflightStage = @($normal.stages | Where-Object { [string]$_.id -eq 'tl2-sensor-ew-discrimination-preflight' })
$smokeStage = @($normal.stages | Where-Object { [string]$_.id -eq 'tl2-sensor-ew-discrimination-smoke' })
$primaryStage = @($normal.stages | Where-Object { [string]$_.id -eq 'tl2-sensor-ew-discrimination-isolation' })
Assert-True ($preflightStage.Count -eq 1 -and [string]$preflightStage[0].command -eq 'tl1-integrated-tactical-combat-preflight' -and [bool]$preflightStage[0].metrics.actualConsumerDeserializer -and [bool]$preflightStage[0].metrics.perSideSensorProfiles -and [bool]$preflightStage[0].metrics.normalEwRatingOverride) 'Checkpoint 79 actual-consumer preflight stage mismatch.'
Assert-True ($smokeStage.Count -eq 1 -and [int]$smokeStage[0].metrics.totalSmokeTrials -eq 54 -and [bool]$smokeStage[0].metrics.fullPipelineExecution) 'Checkpoint 79 full-pipeline smoke stage mismatch.'
Assert-True ($primaryStage.Count -eq 1 -and [int]$primaryStage[0].metrics.variantCount -eq 54 -and -not [bool]$primaryStage[0].metrics.balanceTargetsBlocking -and -not [bool]$primaryStage[0].metrics.tl2ComputerTargetingCandidateApplied -and -not [bool]$primaryStage[0].metrics.sensorRangeChanged -and -not [bool]$primaryStage[0].metrics.sensorOverloadChanged -and -not [bool]$primaryStage[0].metrics.ewOverloadChanged) 'Checkpoint 79 primary-stage isolation metrics mismatch.'
$normalSelfTest = @($normal.stages | Where-Object { [string]$_.id -eq 'runner-self-tests' })
Assert-True ($normalSelfTest.Count -eq 1 -and [int]$normalSelfTest[0].metrics.selfTestCount -eq 47) 'Checkpoint 79 ScenarioRunner self-test count mismatch.'
foreach ($definition in @($normal, $deep)) {
    foreach ($docPath in @($definition.documentation)) {
        Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot ([string]$docPath)) -PathType Leaf) "Checkpoint 79 definition references missing documentation/input '$docPath'."
    }
}

Write-Host '       Validating frozen Concept/Matrix authority and TL2 candidate status...'
Assert-Sha256 'docs/Star_Cluster_Game_Concept_v0.6q.docx' 'a1a9ddb95fbc15f433ec8b2b9aaa44d0f9c07ac1d04117421580b0a11e91f270'
Assert-Sha256 'docs/design/player_technology/Technology_Architecture_Matrix_v1.md' 'c497c3a7069c54705b37c316a0aa0aeceade2c82b7b7d99694066c68c2bbb4eb'
Assert-Sha256 'docs/archive/player_technology/pre-cp165-active/technology_architecture_matrix_v1.json' 'e823786a24848cc8cde5f37c8a4ac6e7de90e79a64e8b0e17722c2dbf00868b1'
Assert-Sha256 'docs/design/player_technology/StarCluster_Technology_Architecture_Matrix_v1.xlsx' 'a8c445e5f4208eef743e95344a8a4f7aec09f77632dccb40c43525826d251141'
Assert-Sha256 'docs/design/player_technology/Tactical_Computer_Degraded_Fire_Architecture_v0_1.md' '5afd5820d4c3887302bf0052d98335d4b2cacf0e20f4f50cbcdceeabb6ae5e6c'
Assert-Sha256 'docs/design/Missile_Guidance_Datalink_Sensor_And_Seeker_Architecture.md' 'd48f9cb2d30729a61d21db80f59377f29533e9a8c03988fced2a88234524a244'
$matrix = Read-Json 'docs/archive/player_technology/pre-cp165-active/technology_architecture_matrix_v1.json'
$tl2Matrix = @($matrix.tiers | Where-Object { [int]$_.technologyLevel -eq 2 })
Assert-True ($tl2Matrix.Count -eq 1) 'Matrix v1 TL2 row missing or duplicated.'
$tl2 = $tl2Matrix[0]
Assert-True ([string]$tl2.tacticalComputer.status -eq 'legacy_candidate' -and [int]$tl2.tacticalComputer.ordinaryTargetingAssistanceOperationalPp -eq 12 -and [int]$tl2.tacticalComputer.approximateTrackPenaltyPp -eq -25) 'Matrix v1 TL2 Tactical Computer candidate drifted.'
Assert-True ([int]$tl2.sensor.sensorDiscriminationResistance -eq 1 -and [int]$tl2.ecm.normalRatingCeiling -eq 2 -and [int]$tl2.ecm.tpPerRating -eq 1 -and [int]$tl2.eccm.normalRatingCeiling -eq 2 -and [int]$tl2.eccm.tpPerRating -eq 1) 'Matrix v1 TL2 Sensor/ECM/ECCM candidate drifted.'
Assert-True ([string]$matrix.status -eq 'design_hypothesis_not_production_data' -and -not [bool]$matrix.authority.productionDataChanged -and -not [bool]$matrix.authority.automaticPromotion) 'Matrix v1 must remain candidate-only during CP79.'
$conceptText = Read-DocxText 'docs/Star_Cluster_Game_Concept_v0.6q.docx'
Assert-True ($conceptText.Contains('None of those TL2 candidate values is production data') -and $conceptText.Contains('Sensor Discrimination Resistance 1') -and $conceptText.Contains('normal ECM/ECCM rating ceilings of 2') -and $conceptText.Contains('degraded-fire penalty initially remains -25')) 'Concept v0.6q no longer expresses the provisional TL2 package or non-production guardrail.'

Write-Host '       Validating CP79 Sensor/EW catalog and arithmetic isolation...'
$sensorCatalog = Read-Json 'src/StarCluster.ScenarioRunner/Scenarios/SensorEw/tl2-sew01-sensor-discrimination-isolation.json'
Assert-True ([string]$sensorCatalog.id -eq 'tl2-sew01-sensor-discrimination-isolation' -and [int]$sensorCatalog.checkpoint -eq 79 -and @($sensorCatalog.candidates).Count -eq 2) 'CP79 Sensor/EW catalog identity or candidate count mismatch.'
$tl1Sensor = @($sensorCatalog.candidates | Where-Object { [string]$_.id -eq 'tl1-balanced-0-control' })
$tl2Sensor = @($sensorCatalog.candidates | Where-Object { [string]$_.id -eq 'tl2-discrimination-1-candidate' })
Assert-True ($tl1Sensor.Count -eq 1 -and $tl2Sensor.Count -eq 1) 'CP79 Sensor/EW control/candidate profiles missing.'
foreach ($profile in @($tl1Sensor[0], $tl2Sensor[0])) {
    Assert-True ([int]$profile.passiveFirmRange -eq 1 -and [int]$profile.passiveApproximateRange -eq 3 -and [int]$profile.activeFirmRange -eq 3 -and [int]$profile.activeApproximateRange -eq 4 -and [int]$profile.activePowerCost -eq 1 -and [int]$profile.activeOverloadAdditionalPowerCost -eq 1 -and [int]$profile.activeOverloadFirmBonus -eq 1 -and [int]$profile.activeOverloadApproximateBonus -eq 1 -and [int]$profile.pointBlankBurnThroughResistance -eq 1) 'CP79 must hold Balanced-0 range/power/overload/burn-through values constant.'
}
Assert-True ([int]$tl1Sensor[0].discriminationResistance -eq 0 -and [int]$tl2Sensor[0].discriminationResistance -eq 1) 'CP79 must isolate Sensor DR 0 versus 1.'
Assert-True ((Get-Margin 1 1 0 0) -eq 0) 'TL1 ECM1/ECCM1 control arithmetic mismatch.'
Assert-True ((Get-Margin 2 1 0 0) -eq 1) 'TL1 Sensor + ECM2/ECCM1 arithmetic mismatch.'
Assert-True ((Get-Margin 2 2 0 0) -eq 0) 'TL1 Sensor + ECM2/ECCM2 arithmetic mismatch.'
Assert-True ((Get-Margin 1 0 1 0) -eq 0) 'TL2 DR1 versus ECM1 arithmetic mismatch.'
Assert-True ((Get-Margin 2 0 1 0) -eq 1) 'TL2 DR1 versus ECM2 arithmetic mismatch.'
Assert-True ((Get-Margin 2 1 1 0) -eq 0) 'TL2 DR1 + ECCM1 versus ECM2 arithmetic mismatch.'

Write-Host '       Validating the 54-variant TL2 operational study independently...'
$study = Read-Json 'src/StarCluster.ScenarioRunner/Scenarios/TL1Calibration/tl2-itc06-sensor-ew-discrimination-isolation.json'
Assert-True ([string]$study.id -eq 'tl2-itc06-sensor-ew-discrimination-isolation' -and [int]$study.trialsPerVariant -eq 10000 -and [string]$study.baselineSha256 -eq 'd3020245a1fe2d28f6795c96c3c331d905ed02ef5210f3ab661e3475f70cf5be') 'CP79 study identity/baseline/default-trial contract mismatch.'
Assert-True (@($study.variants).Count -eq 54 -and @($study.builds).Count -eq 1) 'CP79 study must contain exactly 54 variants and one build.'
Assert-True ([string]$study.sensorEwProfileCatalog -eq 'src/StarCluster.ScenarioRunner/Scenarios/SensorEw/tl2-sew01-sensor-discrimination-isolation.json') 'CP79 study Sensor/EW catalog binding mismatch.'
$groups = @('c79-kvm-r3','c79-evm-r3','c79-kvm-afirst','c79-kvm-bfirst','c79-evm-afirst','c79-evm-bfirst')
$packages = @('firm-reference','tl1-ecm1-eccm1-control','tl1-vs-ecm2-firm-only-no-eccm','tl1-vs-ecm2-eccm1','tl1-vs-ecm2-eccm2','tl1-vs-ecm2-p25-no-eccm','tl2dr1-vs-ecm1-no-eccm','tl2dr1-vs-ecm2-firm-only-no-eccm','tl2dr1-vs-ecm2-eccm1')
foreach ($group in $groups) {
    $context = @($study.variants | Where-Object { [string]$_.comparisonGroup -eq $group })
    Assert-True ($context.Count -eq 9) "CP79 context '$group' must contain exactly nine packages."
    foreach ($package in $packages) {
        Assert-True (@($context | Where-Object { [string]$_.profileLabel -eq $package }).Count -eq 1) "CP79 context '$group' is missing unique package '$package'."
    }
}
$degraded = @($study.variants | Where-Object { [bool]$_.sideAAllowsApproximateDirectFire })
Assert-True ($degraded.Count -eq 6 -and @($degraded | Where-Object { [string]$_.profileLabel -ne 'tl1-vs-ecm2-p25-no-eccm' }).Count -eq 0 -and @($degraded | Where-Object { [int]$_.sideAApproximateDirectFireAccuracyPenalty -ne 25 }).Count -eq 0) 'CP79 degraded fire must exist only in the six explicit -25 Side-A fallback variants.'
Assert-True (@($study.variants | Where-Object { [string]$_.sideAProfileId -ne 'tl1-production' -or [string]$_.sideBProfileId -ne 'tl1-production' }).Count -eq 0) 'CP79 must exclude the legacy TL2 +12 Tactical Computer profile from the first EW isolation.'
Assert-True (@($study.variants | Where-Object { [string]$_.sideBSensorEwProfileId -ne 'tl1-balanced-0-control' }).Count -eq 0) 'CP79 Side B must remain on the TL1 sensor control.'
Assert-True (@($study.variants | Where-Object { [string]$_.sideASensorOverloadPolicy -ne 'None' -or [string]$_.sideBSensorOverloadPolicy -ne 'None' -or [string]$_.sideAStlOverloadPolicy -ne 'None' -or [string]$_.sideBStlOverloadPolicy -ne 'None' }).Count -eq 0) 'CP79 must not introduce Sensor/STL overload changes.'
Assert-True (@($study.variants | Where-Object { [string]$_.sideAEcmPolicy -ne 'None' -or [string]$_.sideBEccmPolicy -ne 'None' }).Count -eq 0) 'CP79 must isolate hostile Side-B ECM and Side-A ECCM response.'
Assert-True (@($study.variants | Where-Object { [int]$_.sideAEcmNormalPowerCostOverride -ne 1 -or [int]$_.sideBEcmNormalPowerCostOverride -ne 1 -or [int]$_.sideAEccmNormalPowerCostOverride -ne 1 -or [int]$_.sideBEccmNormalPowerCostOverride -ne 1 }).Count -eq 0) 'CP79 must hold ECM/ECCM cost at 1 TP per rating.'
Assert-True (@($study.variants | Where-Object { [string]$_.sideBFamily -ne 'Missile' -or [bool]$_.sideBAllowsApproximateDirectFire -or [int]$_.sideBApproximateDirectFireAccuracyPenalty -ne 0 }).Count -eq 0) 'CP79 must not grant missile degraded fire.'

Write-Host '       Auditing CP79 actual-consumer runtime integration...'
$documents = Read-Text 'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatDocuments.cs'
$runner = Read-Text 'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs'
Assert-True ($documents.Contains('JsonPropertyName("sideASensorEwProfileId")') -and $documents.Contains('JsonPropertyName("sideBSensorEwProfileId")') -and $documents.Contains('JsonPropertyName("sideAEcmNormalRatingOverride")') -and $documents.Contains('JsonPropertyName("sideBEccmNormalRatingOverride")')) 'Integrated study document is missing per-side Sensor/EW or normal-rating fields.'
Assert-True ($runner.Contains('variant.SideASensorEwProfileId ?? variant.SensorEwProfileId') -and $runner.Contains('variant.SideBSensorEwProfileId ?? variant.SensorEwProfileId')) 'Integrated runner does not preserve shared-profile fallback while resolving per-side Sensor/EW profiles.'
Assert-True ($runner.Contains('baseNormalPowerCost * normalRating') -and $runner.Contains('int rating = normalRating;')) 'Integrated EW normal rating does not scale power and delivered rating through the actual consumer.'
Assert-True ($runner.Contains('observerProfile,') -and $runner.Contains('targetProfile,') -and $runner.Contains('SensorEwFoundationProfile ewProfileA') -and $runner.Contains('SensorEwFoundationProfile ewProfileB')) 'Integrated Sensor/EW resolver is not using asymmetric observer/target profiles.'
Assert-True ($runner.Contains('Tl2SensorEwDiscriminationIsolationStudyId') -and $runner.Contains('ValidateTl2SensorEwDiscriminationIsolationCoverage') -and $runner.Contains('WriteTl2SensorEwDiscriminationIsolationReview')) 'CP79 study is not wired through validation and reporting.'
$buildGatesStart = $runner.IndexOf('private static IReadOnlyList<Tl1IntegratedTacticalCombatGate> BuildGates(')
$writeOutputsStart = $runner.IndexOf('private static void WriteOutputs(', $buildGatesStart)
Assert-True ($buildGatesStart -ge 0 -and $writeOutputsStart -gt $buildGatesStart) 'Could not isolate BuildGates for CP79 gate audit.'
$gateBlock = $runner.Substring($buildGatesStart, $writeOutputsStart - $buildGatesStart)
$gateIds = @('tl2-c79-variant-coverage','tl2-c79-firm-reference-clean','tl2-c79-tl1-rating1-control-restores','tl2-c79-tl1-sensor-ecm2-blocks','tl2-c79-tl1-eccm1-insufficient-against-ecm2','tl2-c79-wide-eccm2-restores','tl2-c79-tall-sensor-resists-old-ecm','tl2-c79-tall-sensor-alone-still-blocked-by-ecm2','tl2-c79-tall-plus-eccm1-restores','tl2-c79-degraded-fire-remains-explicit-fallback','tl2-c79-outcomes-review-only')
foreach ($gateId in $gateIds) {
    $count = [regex]::Matches($gateBlock, [regex]::Escape('"' + $gateId + '"')).Count
    Assert-True ($count -eq 1) "Checkpoint 79 BuildGates block must contain exactly one '$gateId' gate."
}
Assert-True ([regex]::Matches($gateBlock, 'tl2-c79-').Count -eq 11) 'Checkpoint 79 release-gate block must contain exactly eleven CP79 gates.'

Write-Host '       Validating schema v0.19 and production exclusions...'
$schema = Read-Json 'docs/design/player_technology/tl1_integrated_tactical_combat_schema_v0_19.json'
Assert-True ([string]$schema.'$id' -eq 'star-cluster-tl1-integrated-tactical-combat-schema-v0-19') 'Integrated combat schema v0.19 ID mismatch.'
$variantProperties = @($schema.'$defs'.variant.properties.PSObject.Properties.Name)
foreach ($property in @('sideASensorEwProfileId','sideBSensorEwProfileId','sideAEcmNormalRatingOverride','sideBEcmNormalRatingOverride','sideAEccmNormalRatingOverride','sideBEccmNormalRatingOverride')) {
    Assert-True ($variantProperties -contains $property) "Schema v0.19 is missing '$property'."
}
$baseline = Import-Csv (Join-Path $repositoryRoot 'docs\archive\player_technology\pre-cp165-active\tl1_core_combat_numerical_baseline_v0_3.csv')
$ecmMax = @($baseline | Where-Object { [string]$_.parameter_id -eq 'ecm_max' })
$eccmMax = @($baseline | Where-Object { [string]$_.parameter_id -eq 'eccm_max' })
Assert-True ($ecmMax.Count -eq 1 -and $eccmMax.Count -eq 1 -and [int]$ecmMax[0].value -eq 1 -and [int]$eccmMax[0].value -eq 1) 'CP79 must not promote ECM/ECCM rating 2 into the TL1 production baseline.'
$computerCatalog = Read-Json 'docs/archive/player_technology/pre-cp165-active/tactical_computer_fire_control_profiles_v0_1.json'
Assert-True (@($computerCatalog.profiles).Count -eq 1 -and [string]$computerCatalog.profiles[0].id -eq 'tl1-tactical-computer-fire-control' -and [int]$computerCatalog.profiles[0].technologyLevel -eq 1 -and [int]$computerCatalog.profiles[0].approximateTrackDirectFireAccuracyPenaltyPercentagePoints -eq 25 -and [bool]$computerCatalog.profiles[0].requiresExplicitWeaponCapability -and -not [bool]$computerCatalog.profiles[0].appliesToMissileTerminalAttacks) 'CP79 must not add a TL2 production Tactical Computer profile or alter the TL1 -25 degraded-fire architecture.'
$productionApproximateEnable = Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'src') -Recurse -File -Filter '*.cs' | Where-Object { $_.FullName -notlike '*StarCluster.ScenarioRunner*' } | Select-String -SimpleMatch 'allowsApproximateTrackFire: true'
Assert-True (@($productionApproximateEnable).Count -eq 0) 'CP79 must not enable degraded fire in production Core/Game weapon construction.'
$studyDoc = Read-Text 'docs/design/player_technology/TL2_Sensor_EW_Discrimination_Isolation_Study_v0_1.md'
Assert-True ($studyDoc.Contains('not production authority') -and $studyDoc.Contains('legacy TL2 Tactical Computer +12 ordinary-targeting candidate') -and $studyDoc.Contains('1 TP/rating') -and $studyDoc.Contains('Ordinary missiles remain on their accepted Firm-terminal architecture')) 'CP79 study documentation is missing isolation or production guardrails.'
$calibrationArchitecture = Read-Text 'docs/design/Technology_Calibration_And_Simulation_Architecture.md'
Assert-True ($calibrationArchitecture.Contains('Checkpoint_79_Validation_Tiers.md') -and $calibrationArchitecture.Contains('Cross-TL Sensor/EW diagnostic plumbing') -and $calibrationArchitecture.Contains('one Tactical Power per rating')) 'Current calibration architecture is not synchronized to CP79 Sensor/EW diagnostic plumbing or validation tiers.'

Write-Host '       Validating active-document/archive hygiene...'
$activeConcepts = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs') -File -Filter 'Star_Cluster_Game_Concept_v*.docx')
Assert-True ($activeConcepts.Count -eq 1 -and $activeConcepts[0].Name -eq 'Star_Cluster_Game_Concept_v0.6q.docx') 'Exactly Concept v0.6q must remain active under docs/.'
$validationFiles = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs\validation') -File -Filter 'Checkpoint_*.md')
Assert-True ($validationFiles.Count -eq 1 -and $validationFiles[0].Name -eq 'Checkpoint_79_TL2_Sensor_EW_Discrimination_And_Rating_Isolation.md') 'Exactly one CP79 active validation runbook must remain.'
Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot 'docs\validation\archive\Checkpoint_78a_Historical_Authority_Contract_Hotfix.md') -PathType Leaf) 'Checkpoint 78a validation runbook must be archived during CP79 normalization.'
$rootTxt = @(Get-ChildItem -LiteralPath $repositoryRoot -File -Filter '*.txt')
Assert-True ($rootTxt.Count -eq 1 -and $rootTxt[0].Name -eq 'CHECKPOINT_79_SHA256SUMS.txt') 'Repository root must contain only CHECKPOINT_79_SHA256SUMS.txt as .txt.'

Write-Host '       CP79 isolation: TL1 combat/computer retained; Sensor DR 1 and ECM/ECCM rating 2 remain diagnostic candidates.'
Write-Host '       Normal workload: 11 stages / 54 substantive variants / 540,000 default substantive trials plus 54 smoke trials.'
Write-Host 'Checkpoint 79 contract validation passed.'
