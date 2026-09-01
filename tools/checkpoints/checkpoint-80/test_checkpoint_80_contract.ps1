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

function Read-NormalizedMarkdown {
    param([string]$RelativePath)
    $text = Read-Text $RelativePath
    return [string]($text.Replace('**','').Replace('__','').Replace('`',''))
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

Write-Host '       Validating native-dependency declarations...'
$guard = Join-Path $repositoryRoot 'tools\checkpoints\Test-NativeAcceptanceDependencies.ps1'
$normalRel = 'tools/calibration/checkpoints/checkpoint-80.json'
$deepRel = 'tools/calibration/checkpoints/checkpoint-80-deep-calibration.json'
$guardedPs = @(
    'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
    'tools/checkpoints/checkpoint-80/apply_checkpoint_80.ps1',
    'tools/checkpoints/checkpoint-80/test_checkpoint_80_contract.ps1',
    'tools/calibration/run_calibration_checkpoint.ps1'
)
$guardedDefs = @($normalRel, $deepRel)
& $guard -RepositoryRoot $repositoryRoot -PowerShellPaths $guardedPs -CheckpointDefinitionPaths $guardedDefs

Write-Host '       Validating Checkpoint 80 definitions and workload accounting...'
$normal = Read-Json $normalRel
$deep = Read-Json $deepRel
Assert-True ([string]$normal.checkpointId -eq '80' -and [string]$deep.checkpointId -eq '80') 'Checkpoint 80 definition ID mismatch.'
Assert-True ([string]$normal.manifestFile -eq 'CHECKPOINT_80_SHA256SUMS.txt' -and [string]$deep.manifestFile -eq 'CHECKPOINT_80_SHA256SUMS.txt') 'Checkpoint 80 manifest binding mismatch.'
Assert-True ([string]$normal.outputRoot -eq 'out/checkpoint-80' -and [string]$deep.outputRoot -eq 'out/checkpoint-80-deep-calibration') 'Checkpoint 80 output-root binding mismatch.'
Assert-True ((@($normal.nativeDependencyPrecheck.powerShellPaths) -join '|') -eq ($guardedPs -join '|')) 'Checkpoint 80 normal native-dependency PowerShell path binding mismatch.'
Assert-True ((@($deep.nativeDependencyPrecheck.powerShellPaths) -join '|') -eq ($guardedPs -join '|')) 'Checkpoint 80 deep native-dependency PowerShell path binding mismatch.'
Assert-True ((@($normal.nativeDependencyPrecheck.checkpointDefinitionPaths) -join '|') -eq ($guardedDefs -join '|')) 'Checkpoint 80 normal native-dependency definition binding mismatch.'
Assert-True ((@($deep.nativeDependencyPrecheck.checkpointDefinitionPaths) -join '|') -eq ($guardedDefs -join '|')) 'Checkpoint 80 deep native-dependency definition binding mismatch.'
Assert-True (@($normal.stages).Count -eq 11 -and [int]$normal.checkpointMetrics.stageCount -eq 11) 'Checkpoint 80 normal stage-count mismatch.'
Assert-True ([int]$normal.checkpointMetrics.monteCarloVariantCount -eq 72 -and [int]$normal.checkpointMetrics.trialsAtDefault -eq 720000 -and [int]$normal.checkpointMetrics.smokeVariantExecutions -eq 72 -and [int]$normal.checkpointMetrics.smokeTrialsAtDefault -eq 72 -and [int]$normal.checkpointMetrics.totalTrialExecutionsAtDefault -eq 720072) 'Checkpoint 80 normal workload accounting mismatch.'
Assert-True (@($deep.stages).Count -eq 33 -and [int]$deep.checkpointMetrics.stageCount -eq 33 -and [int]$deep.checkpointMetrics.monteCarloVariantCount -eq 1670 -and [int]$deep.checkpointMetrics.trialsAtDefault -eq 16700000 -and [int]$deep.checkpointMetrics.smokeVariantExecutions -eq 126 -and [int]$deep.checkpointMetrics.smokeTrialsAtDefault -eq 126 -and [int]$deep.checkpointMetrics.totalTrialExecutionsAtDefault -eq 16700126) 'Checkpoint 80 Deep Calibration workload accounting mismatch.'
$expectedStages = @('deterministic','tl1-phase-a','tl1-phase-b','tl1-installation-space-envelope','tl1-sensor-ew-foundation','tl2-ew-power-pressure-preflight','tl2-ew-power-pressure-smoke','tl2-ew-power-pressure-tall-viability','auxiliary-resource-endurance','checkpoint-53-resource-semantics-lock','runner-self-tests')
Assert-True ((@($normal.stages | ForEach-Object { [string]$_.id }) -join '|') -eq ($expectedStages -join '|')) 'Checkpoint 80 normal stage ordering mismatch.'
Assert-True ([string]$normal.primaryStudy.id -eq 'tl2-itc07-ew-power-pressure-tall-viability' -and [int]$normal.primaryStudy.variantCount -eq 72) 'Checkpoint 80 primary-study binding mismatch.'
Assert-True ([string]$deep.primaryStudy.id -eq 'tl2-itc07-ew-power-pressure-tall-viability' -and [int]$deep.primaryStudy.variantCount -eq 72) 'Checkpoint 80 Deep Calibration primary-study binding mismatch.'

$policy = Read-Json 'docs/design/testing/checkpoint_80_validation_suite_policy_v0_1.json'
Assert-True ([int]$policy.checkpoint -eq 80 -and [string]$policy.acceptedBaseline -eq '79a' -and -not [bool]$policy.blockingBalanceTargets) 'Checkpoint 80 validation policy identity mismatch.'
Assert-True ([int]$policy.normal.stageCount -eq 11 -and [int]$policy.normal.monteCarloVariantCount -eq 72 -and [int]$policy.normal.totalTrialExecutions -eq 720072) 'Checkpoint 80 validation policy normal workload mismatch.'
Assert-True ([int]$policy.deepCalibration.stageCount -eq 33 -and [int]$policy.deepCalibration.monteCarloVariantCount -eq 1670 -and [int]$policy.deepCalibration.totalTrialExecutions -eq 16700126) 'Checkpoint 80 validation policy Deep Calibration workload mismatch.'
Assert-True ([bool]$policy.powerAndTallViabilityControls.advancedTechnologyMayRequireMoreTacticalPower -and [bool]$policy.powerAndTallViabilityControls.tallPlayMustRemainViable -and [int]$policy.powerAndTallViabilityControls.productionReactorOutput -eq 5 -and [int]$policy.powerAndTallViabilityControls.diagnosticSensitivityReactorOutput -eq 6 -and [bool]$policy.powerAndTallViabilityControls.diagnosticSensitivityOnly -and [int]$policy.powerAndTallViabilityControls.missilePressureVariantCount -eq 36 -and [int]$policy.powerAndTallViabilityControls.directFirePressureVariantCount -eq 36 -and [bool]$policy.powerAndTallViabilityControls.noAutomaticCandidatePromotion) 'Checkpoint 80 power/tall-viability policy mismatch.'

Write-Host '       Validating frozen CP79a candidate architecture and CP80 Concept/Matrix authority...'
$concept = Read-DocxText 'docs/Star_Cluster_Game_Concept_v0.6r.docx'
Assert-True ($concept.Contains('Higher-TL equipment is not assumed to be automatically cheaper to power') -and $concept.Contains('power efficiency matures on a separate axis') -and $concept.Contains('systematic trap') -and $concept.Contains('Checkpoint 80 therefore compares the brute-force old-Sensor + ECCM2 path') -and $concept.Contains('C-054') -and $concept.Contains('Tall viability guardrail')) 'Concept v0.6r is missing the CP80 power-demand/tall-viability guardrail or study direction.'
$matrixMd = Read-NormalizedMarkdown 'docs/design/player_technology/Technology_Architecture_Matrix_v1.md'
Assert-True ($matrixMd.Contains('Advanced does not automatically mean cheaper to power') -and $matrixMd.Contains('Tall play must remain viable') -and $matrixMd.Contains('Checkpoint 79a evidence and Checkpoint 80 follow-up') -and $matrixMd.Contains('Reactor 6 is not promoted by that study')) 'Technology Architecture Matrix v1 Markdown is not synchronized to CP80 power/tall-viability direction.'
$matrix = Read-Json 'docs/archive/player_technology/pre-cp165-active/technology_architecture_matrix_v1.json'
Assert-True ([int]$matrix.checkpoint -eq 80) 'Technology Architecture Matrix v1 JSON checkpoint marker mismatch.'
Assert-True (@($matrix.globalGuardrails | Where-Object { [string]$_ -like '*Higher-TL systems may legitimately demand more Tactical Power*' }).Count -eq 1) 'Matrix v1 JSON is missing the advanced-power-demand guardrail.'
Assert-True (@($matrix.globalGuardrails | Where-Object { [string]$_ -like '*Tall research may expose real reactor*systematically make advanced equipment unusable*' }).Count -eq 1) 'Matrix v1 JSON is missing the tall-viability guardrail.'
Assert-True (@($matrix.acceptedEvidence).Count -ge 1 -and [string]$matrix.acceptedEvidence[0].checkpoint -eq '79a' -and [string]$matrix.acceptedEvidence[0].summarySha256 -eq 'eecbdf5a935d984655416c3fe4fae61308493cad778c89b2272f84ea5b761c61') 'Matrix v1 JSON does not retain accepted CP79a evidence.'
Assert-True ([int]$matrix.nextFocusedStudy.checkpoint -eq 80 -and [string]$matrix.nextFocusedStudy.studyId -eq 'tl2-itc07-ew-power-pressure-tall-viability' -and [int]$matrix.nextFocusedStudy.variantCount -eq 72 -and [int]$matrix.nextFocusedStudy.defaultSubstantiveTrials -eq 720000 -and -not [bool]$matrix.nextFocusedStudy.productionPromotion -and [string]$matrix.nextFocusedStudy.reactor6Status -eq 'diagnostic_sensitivity_only') 'Matrix v1 JSON CP80 study binding mismatch.'
Assert-Sha256 'docs/Star_Cluster_Game_Concept_v0.6r.docx' '0078184dbb4589aa902e24eaef627d8915e67d625fcceddc628fef6ad2b5dbd1'
Assert-Sha256 'docs/design/player_technology/Technology_Architecture_Matrix_v1.md' '51017af6771fee116c7eb6698b553b9e0d31e5ba306bde9c935f70076e615751'
Assert-Sha256 'docs/archive/player_technology/pre-cp165-active/technology_architecture_matrix_v1.json' 'f55fa115afc7d0470ec398efdcd7a7dae223ecb03d352c57a0e51ca654c06d5f'
Assert-Sha256 'docs/design/player_technology/StarCluster_Technology_Architecture_Matrix_v1.xlsx' 'f2c8d3040b2a1cd4b9ad0cab8348d56ee485491488317eef63499aec1f19d593'
Assert-Sha256 'docs/validation/archive/Checkpoint_79a_Policy_Telemetry_Study_Classification_Hotfix.md' '899ae3f899a3495625a7769d0b1ebe639fa044042e2dd5f78d3f45003a7c3d70'
Assert-Sha256 'src/StarCluster.ScenarioRunner/Scenarios/SensorEw/tl2-sew01-sensor-discrimination-isolation.json' '4bc354f5628b80c8176f3da94988394f5ee32f44796c30821d88de461bb17853'
Assert-Sha256 'docs/archive/player_technology/pre-cp165-active/tactical_computer_fire_control_profiles_v0_1.json' '3e688832495cc54a6aac15cdbfb5a1fef87959a4c9d07e8d67dcb844ea6e84cc'

Write-Host '       Validating CP80 Sensor/EW power-pressure study independently...'
$study = Read-Json 'src/StarCluster.ScenarioRunner/Scenarios/TL1Calibration/tl2-itc07-ew-power-pressure-tall-viability.json'
Assert-True ([string]$study.id -eq 'tl2-itc07-ew-power-pressure-tall-viability' -and @($study.variants).Count -eq 72 -and [int]$study.trialsPerVariant -eq 10000) 'CP80 study identity or variant count mismatch.'
Assert-True ([string]$study.sensorEwProfileCatalog -eq 'src/StarCluster.ScenarioRunner/Scenarios/SensorEw/tl2-sew01-sensor-discrimination-isolation.json') 'CP80 study must use the frozen CP79 Sensor/EW candidate catalog.'
$baselinePath = Join-Path $repositoryRoot 'docs\archive\player_technology\pre-cp165-active\tl1_core_combat_numerical_baseline_v0_3.csv'
$baselineHash = (Get-FileHash -LiteralPath $baselinePath -Algorithm SHA256).Hash.ToLowerInvariant()
Assert-True ($baselineHash -eq [string]$study.baselineSha256) 'CP80 study baseline hash does not match the current TL1 numerical baseline.'
Assert-True (@($study.builds).Count -eq 1 -and [string]$study.builds[0].id -eq 'balanced_generalist_ew_major' -and [int]$study.builds[0].usedSpace -eq 35 -and [int]$study.builds[0].freeSupportSpace -eq 0) 'CP80 must use exactly one 35-Space balanced_generalist_ew_major fixture.'
$groupNames = @($study.variants | ForEach-Object { [string]$_.comparisonGroup } | Sort-Object -Unique)
Assert-True ($groupNames.Count -eq 12) 'CP80 must contain exactly twelve comparison groups.'
$packageLabels = @('firm-reference-5tp','wide-eccm2-5tp','tall-dr1-eccm1-5tp','degraded-p25-5tp','wide-eccm2-6tp-sensitivity','tall-dr1-eccm1-6tp-sensitivity')
foreach ($groupName in $groupNames) {
    $group = @($study.variants | Where-Object { [string]$_.comparisonGroup -eq $groupName })
    Assert-True ($group.Count -eq 6) "CP80 comparison group '$groupName' must contain exactly six response packages."
    Assert-True ((@($group | ForEach-Object { [string]$_.profileLabel } | Sort-Object) -join '|') -eq (@($packageLabels | Sort-Object) -join '|')) "CP80 comparison group '$groupName' does not contain the exact six response packages."
}
Assert-True (@($study.variants | Where-Object { [string]$_.sideAFamily -eq 'Kinetic' }).Count -eq 36 -and @($study.variants | Where-Object { [string]$_.sideAFamily -eq 'Energy' }).Count -eq 36) 'CP80 must split Side-A Kinetic/Energy coverage 36/36.'
Assert-True (@($study.variants | Where-Object { [string]$_.sideBFamily -eq 'Missile' }).Count -eq 36 -and @($study.variants | Where-Object { [string]$_.sideBFamily -eq 'Kinetic' }).Count -eq 36) 'CP80 must split missile/direct-fire opponent pressure 36/36.'
Assert-True (@($study.variants | Where-Object { [string]$_.movementMode -eq 'HoldRange3' -and [string]$_.movementOrder -eq 'Simultaneous' }).Count -eq 24) 'CP80 fixed range-3 control coverage mismatch.'
Assert-True (@($study.variants | Where-Object { [string]$_.movementMode -eq 'TrackAwareOpponentRange' -and [string]$_.movementOrder -eq 'SideAFirst' }).Count -eq 24) 'CP80 Side-A-first dynamic coverage mismatch.'
Assert-True (@($study.variants | Where-Object { [string]$_.movementMode -eq 'TrackAwareOpponentRange' -and [string]$_.movementOrder -eq 'SideBFirst' }).Count -eq 24) 'CP80 Side-B-first dynamic coverage mismatch.'
Assert-True (@($study.variants | Where-Object { -not [bool]$_.pdsEnabled -or [int]$_.sideBReactorOutputOverride -ne 5 -or [int]$_.sideAEcmNormalPowerCostOverride -ne 1 -or [int]$_.sideBEcmNormalPowerCostOverride -ne 1 -or [int]$_.sideAEccmNormalPowerCostOverride -ne 1 -or [int]$_.sideBEccmNormalPowerCostOverride -ne 1 }).Count -eq 0) 'CP80 must keep PDS enabled, Side-B reactor 5, and normal EW cost at 1 TP/rating.'
Assert-True (@($study.variants | Where-Object { [string]$_.sideASensorOverloadPolicy -ne 'None' -or [string]$_.sideBSensorOverloadPolicy -ne 'None' -or [string]$_.sideAStlOverloadPolicy -ne 'None' -or [string]$_.sideBStlOverloadPolicy -ne 'None' }).Count -eq 0) 'CP80 must not introduce Sensor or STL overload changes.'

foreach ($variant in @($study.variants)) {
    $label = [string]$variant.profileLabel
    Assert-True ([int]$variant.sideBEcmNormalRatingOverride -eq $(if ($label -eq 'firm-reference-5tp') { 1 } else { 2 })) "CP80 '$($variant.id)' hostile ECM rating mismatch."
    Assert-True ([string]$variant.sideBEcmPolicy -eq $(if ($label -eq 'firm-reference-5tp') { 'None' } else { 'Normal' })) "CP80 '$($variant.id)' hostile ECM policy mismatch."
    if ($label -eq 'firm-reference-5tp') {
        Assert-True ([int]$variant.sideAReactorOutputOverride -eq 5 -and [string]$variant.sideASensorEwProfileId -eq 'tl1-balanced-0-control' -and [string]$variant.sideAEccmPolicy -eq 'None' -and -not [bool]$variant.sideAAllowsApproximateDirectFire) "CP80 '$($variant.id)' Firm reference is not clean."
    }
    elseif ($label -eq 'wide-eccm2-5tp') {
        Assert-True ([int]$variant.sideAReactorOutputOverride -eq 5 -and [string]$variant.sideASensorEwProfileId -eq 'tl1-balanced-0-control' -and [string]$variant.sideAEccmPolicy -eq 'ReactiveNormal' -and [int]$variant.sideAEccmNormalRatingOverride -eq 2 -and -not [bool]$variant.sideAAllowsApproximateDirectFire) "CP80 '$($variant.id)' wide ECCM2 5-TP package mismatch."
    }
    elseif ($label -eq 'tall-dr1-eccm1-5tp') {
        Assert-True ([int]$variant.sideAReactorOutputOverride -eq 5 -and [string]$variant.sideASensorEwProfileId -eq 'tl2-discrimination-1-candidate' -and [string]$variant.sideAEccmPolicy -eq 'ReactiveNormal' -and [int]$variant.sideAEccmNormalRatingOverride -eq 1 -and -not [bool]$variant.sideAAllowsApproximateDirectFire) "CP80 '$($variant.id)' tall DR1 + ECCM1 5-TP package mismatch."
    }
    elseif ($label -eq 'degraded-p25-5tp') {
        Assert-True ([int]$variant.sideAReactorOutputOverride -eq 5 -and [string]$variant.sideASensorEwProfileId -eq 'tl1-balanced-0-control' -and [string]$variant.sideAEccmPolicy -eq 'None' -and [bool]$variant.sideAAllowsApproximateDirectFire -and [int]$variant.sideAApproximateDirectFireAccuracyPenalty -eq 25) "CP80 '$($variant.id)' -25 degraded-fire fallback mismatch."
    }
    elseif ($label -eq 'wide-eccm2-6tp-sensitivity') {
        Assert-True ([int]$variant.sideAReactorOutputOverride -eq 6 -and [string]$variant.sideASensorEwProfileId -eq 'tl1-balanced-0-control' -and [string]$variant.sideAEccmPolicy -eq 'ReactiveNormal' -and [int]$variant.sideAEccmNormalRatingOverride -eq 2 -and -not [bool]$variant.sideAAllowsApproximateDirectFire) "CP80 '$($variant.id)' wide ECCM2 6-TP sensitivity mismatch."
    }
    elseif ($label -eq 'tall-dr1-eccm1-6tp-sensitivity') {
        Assert-True ([int]$variant.sideAReactorOutputOverride -eq 6 -and [string]$variant.sideASensorEwProfileId -eq 'tl2-discrimination-1-candidate' -and [string]$variant.sideAEccmPolicy -eq 'ReactiveNormal' -and [int]$variant.sideAEccmNormalRatingOverride -eq 1 -and -not [bool]$variant.sideAAllowsApproximateDirectFire) "CP80 '$($variant.id)' tall DR1 + ECCM1 6-TP sensitivity mismatch."
    }
    else {
        throw "Unexpected CP80 response package '$label'."
    }
}
Assert-True (@($study.variants | Where-Object { [int]$_.sideAReactorOutputOverride -eq 5 }).Count -eq 48 -and @($study.variants | Where-Object { [int]$_.sideAReactorOutputOverride -eq 6 }).Count -eq 24) 'CP80 must contain 48 production-reference 5-TP variants and 24 sensitivity-only 6-TP variants.'
Assert-True (@($study.variants | Where-Object { [bool]$_.sideAAllowsApproximateDirectFire }).Count -eq 12 -and @($study.variants | Where-Object { [bool]$_.sideAAllowsApproximateDirectFire -and [int]$_.sideAApproximateDirectFireAccuracyPenalty -ne 25 }).Count -eq 0) 'CP80 degraded-fire diagnostic must be exactly twelve explicit -25 variants.'
Assert-True (@($study.variants | Where-Object { [string]$_.sideBFamily -eq 'Missile' -and ([bool]$_.sideBAllowsApproximateDirectFire -or [int]$_.sideBApproximateDirectFireAccuracyPenalty -ne 0) }).Count -eq 0) 'CP80 must not grant missile degraded fire.'
Assert-Sha256 'src/StarCluster.ScenarioRunner/Scenarios/TL1Calibration/tl2-itc07-ew-power-pressure-tall-viability.json' '1bd583d7431b7f0a3cc31329e5e38900611c44713a534743dee74c0639ac17b7'

Write-Host '       Auditing CP80 actual-consumer runtime integration and shared global gates...'
$documents = Read-Text 'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatDocuments.cs'
$runner = Read-Text 'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs'
Assert-True ($documents.Contains('JsonPropertyName("sideASensorEwProfileId")') -and $documents.Contains('JsonPropertyName("sideBSensorEwProfileId")') -and $documents.Contains('JsonPropertyName("sideAEcmNormalRatingOverride")') -and $documents.Contains('JsonPropertyName("sideBEccmNormalRatingOverride")')) 'Integrated study document is missing per-side Sensor/EW or normal-rating fields.'
Assert-True ($runner.Contains('Tl2EwPowerPressureTallViabilityStudyId') -and $runner.Contains('ValidateTl2EwPowerPressureTallViabilityCoverage') -and $runner.Contains('WriteTl2EwPowerPressureTallViabilityReview') -and $runner.Contains('tl2-ew-power-pressure-tall-viability-review.csv')) 'CP80 study is not wired through actual-consumer validation and reporting.'
Assert-True ($runner.Contains('variant.SideASensorEwProfileId ?? variant.SensorEwProfileId') -and $runner.Contains('variant.SideBSensorEwProfileId ?? variant.SensorEwProfileId')) 'Integrated runner no longer preserves shared-profile fallback while resolving asymmetric Sensor/EW profiles.'
Assert-True ($runner.Contains('baseNormalPowerCost * normalRating') -and $runner.Contains('int rating = normalRating;')) 'Integrated EW normal rating no longer scales delivered rating and normal power through the actual consumer.'
$buildGatesStart = $runner.IndexOf('private static IReadOnlyList<Tl1IntegratedTacticalCombatGate> BuildGates(')
$writeOutputsStart = $runner.IndexOf('private static void WriteOutputs(', $buildGatesStart)
Assert-True ($buildGatesStart -ge 0 -and $writeOutputsStart -gt $buildGatesStart) 'Could not isolate BuildGates for CP80 gate audit.'
$gateBlock = $runner.Substring($buildGatesStart, $writeOutputsStart - $buildGatesStart)
$gateIds = @('tl2-c80-variant-coverage','tl2-c80-firm-reference-clean','tl2-c80-wide-eccm2-restores-firm','tl2-c80-tall-dr1-eccm1-restores-firm','tl2-c80-degraded-fire-remains-fallback','tl2-c80-six-power-sensitivity-executes','tl2-c80-opponent-pressure-coverage','tl2-c80-no-production-promotion','tl2-c80-outcomes-review-only')
foreach ($gateId in $gateIds) {
    $count = [regex]::Matches($gateBlock, [regex]::Escape('"' + $gateId + '"')).Count
    Assert-True ($count -eq 1) "Checkpoint 80 BuildGates block must contain exactly one '$gateId' gate."
}
Assert-True ([regex]::Matches($gateBlock, 'tl2-c80-').Count -eq 9) 'Checkpoint 80 release-gate block must contain exactly nine CP80 gates.'
$policyGateStart = $gateBlock.IndexOf('"policy-telemetry"', [StringComparison]::Ordinal)
$attackGateStart = $gateBlock.IndexOf('"attack-layer-telemetry"', $policyGateStart, [StringComparison]::Ordinal)
Assert-True ($policyGateStart -ge 0 -and $attackGateStart -gt $policyGateStart) 'Unable to isolate the shared policy-telemetry gate inside BuildGates.'
$policyGateText = $gateBlock.Substring($policyGateStart, $attackGateStart - $policyGateStart)
$cp80PolicyMentions = [regex]::Matches($policyGateText, 'Tl2EwPowerPressureTallViabilityStudyId').Count
Assert-True ($cp80PolicyMentions -eq 2) 'CP80 must be classified exactly twice inside shared policy-telemetry: once in the pass predicate and once in the diagnostic-message branch.'

Write-Host '       Validating production exclusions and missile/degraded-fire boundaries...'
$schema = Read-Json 'docs/design/player_technology/tl1_integrated_tactical_combat_schema_v0_19.json'
Assert-True ([string]$schema.'$id' -eq 'star-cluster-tl1-integrated-tactical-combat-schema-v0-19') 'Integrated combat schema v0.19 ID mismatch.'
$variantProperties = @($schema.'$defs'.variant.properties.PSObject.Properties.Name)
foreach ($property in @('sideASensorEwProfileId','sideBSensorEwProfileId','sideAEcmNormalRatingOverride','sideBEcmNormalRatingOverride','sideAEccmNormalRatingOverride','sideBEccmNormalRatingOverride','sideAReactorOutputOverride','sideBReactorOutputOverride')) {
    Assert-True ($variantProperties -contains $property) "Schema v0.19 is missing '$property'."
}
$baseline = Import-Csv (Join-Path $repositoryRoot 'docs\archive\player_technology\pre-cp165-active\tl1_core_combat_numerical_baseline_v0_3.csv')
$ecmMax = @($baseline | Where-Object { [string]$_.parameter_id -eq 'ecm_max' })
$eccmMax = @($baseline | Where-Object { [string]$_.parameter_id -eq 'eccm_max' })
$reactor = @($baseline | Where-Object { [string]$_.parameter_id -eq 'reactor_output' })
Assert-True ($ecmMax.Count -eq 1 -and $eccmMax.Count -eq 1 -and [int]$ecmMax[0].value -eq 1 -and [int]$eccmMax[0].value -eq 1) 'CP80 must not promote ECM/ECCM rating 2 into the TL1 production baseline.'
Assert-True ($reactor.Count -eq 1 -and [int]$reactor[0].value -eq 5) 'CP80 must not promote the 6-TP sensitivity into the TL1 production reactor baseline.'
$computerCatalog = Read-Json 'docs/archive/player_technology/pre-cp165-active/tactical_computer_fire_control_profiles_v0_1.json'
Assert-True (@($computerCatalog.profiles).Count -eq 1 -and [string]$computerCatalog.profiles[0].id -eq 'tl1-tactical-computer-fire-control' -and [int]$computerCatalog.profiles[0].technologyLevel -eq 1 -and [int]$computerCatalog.profiles[0].approximateTrackDirectFireAccuracyPenaltyPercentagePoints -eq 25 -and [bool]$computerCatalog.profiles[0].requiresExplicitWeaponCapability -and -not [bool]$computerCatalog.profiles[0].appliesToMissileTerminalAttacks) 'CP80 must not add a TL2 production Tactical Computer or alter TL1 degraded-fire ownership.'
$productionApproximateEnable = Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'src') -Recurse -File -Filter '*.cs' | Where-Object { $_.FullName -notlike '*StarCluster.ScenarioRunner*' } | Select-String -SimpleMatch 'allowsApproximateTrackFire: true'
Assert-True (@($productionApproximateEnable).Count -eq 0) 'CP80 must not enable degraded fire in production Core/Game weapon construction.'
$missileDoc = Read-NormalizedMarkdown 'docs/design/Missile_Guidance_Datalink_Sensor_And_Seeker_Architecture.md'
Assert-True ($missileDoc.Contains('Ordinary missile profiles') -and $missileDoc.Contains('Firm-terminal') -and $missileDoc.Contains('direct-fire degraded-fire trait')) 'Missile architecture no longer clearly preserves the ordinary Firm-terminal/degraded-fire boundary.'
$studyDoc = Read-NormalizedMarkdown 'docs/design/player_technology/TL2_EW_Power_Pressure_And_Tall_Viability_Study_v0_1.md'
Assert-True ($studyDoc.Contains('candidate/sensitivity values, not production authority') -and $studyDoc.Contains('Higher-TL equipment is allowed to demand more Tactical Power') -and $studyDoc.Contains('6-TP Side-A reactor sensitivity') -and $studyDoc.Contains('promotes nothing automatically')) 'CP80 study documentation is missing candidate, power-demand, sensitivity, or no-promotion guardrails.'
$calibrationArchitecture = Read-NormalizedMarkdown 'docs/design/Technology_Calibration_And_Simulation_Architecture.md'
Assert-True ($calibrationArchitecture.Contains('Checkpoint_80_Validation_Tiers.md') -and $calibrationArchitecture.Contains('Advanced power demand and tall viability') -and $calibrationArchitecture.Contains('Side-A reactor output 6 is included only as diagnostic sensitivity')) 'Current calibration architecture is not synchronized to CP80 validation tiers or power/tall-viability guidance.'

Write-Host '       Validating active-document/archive hygiene...'
$activeConcepts = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs') -File -Filter 'Star_Cluster_Game_Concept_v*.docx')
Assert-True ($activeConcepts.Count -eq 1 -and $activeConcepts[0].Name -eq 'Star_Cluster_Game_Concept_v0.6r.docx') 'Exactly Concept v0.6r must remain active under docs/.'
Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot 'docs\archive\Star_Cluster_Game_Concept_v0.6q.docx') -PathType Leaf) 'Concept v0.6q must remain archived for historical continuity.'
$validationFiles = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs\validation') -File -Filter 'Checkpoint_*.md')
Assert-True ($validationFiles.Count -eq 1 -and $validationFiles[0].Name -eq 'Checkpoint_80_TL2_EW_Power_Pressure_And_Tall_Viability.md') 'Exactly one CP80 active validation runbook must remain.'
Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot 'docs\validation\archive\Checkpoint_79a_Policy_Telemetry_Study_Classification_Hotfix.md') -PathType Leaf) 'Checkpoint 79a validation runbook must remain archived during CP80 normalization.'
$rootTxt = @(Get-ChildItem -LiteralPath $repositoryRoot -File -Filter '*.txt')
Assert-True ($rootTxt.Count -eq 1 -and $rootTxt[0].Name -eq 'CHECKPOINT_80_SHA256SUMS.txt') 'Repository root must contain only CHECKPOINT_80_SHA256SUMS.txt as .txt.'

Write-Host '       CP80 isolation: CP79a DR1/ECM2/ECCM2 candidates retained; 5 TP remains production reference and 6 TP is sensitivity only.'
Write-Host '       Normal workload: 11 stages / 72 substantive variants / 720,000 default substantive trials plus 72 smoke trials.'
Write-Host 'Checkpoint 80 contract validation passed.'
