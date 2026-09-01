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
    Assert-True (-not [string]::IsNullOrWhiteSpace($text)) "Required JSON '$RelativePath' is empty."
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
            Assert-True (-not [string]::IsNullOrWhiteSpace($xmlText)) "DOCX '$RelativePath' has empty document.xml content."
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
    finally { if ($null -ne $archive) { $archive.Dispose() } }
}
function Read-ZipEntryText {
    param([string]$RelativePath, [string]$EntryName)
    $path = Join-Path $repositoryRoot $RelativePath
    Assert-True (Test-Path -LiteralPath $path -PathType Leaf) "Required package '$RelativePath' is missing."
    Add-Type -AssemblyName System.IO.Compression.FileSystem -ErrorAction Stop | Out-Null
    $archive = $null
    try {
        $archive = [System.IO.Compression.ZipFile]::OpenRead($path)
        $entry = $archive.GetEntry($EntryName)
        Assert-True ($null -ne $entry) "Package '$RelativePath' is missing '$EntryName'."
        $stream = $entry.Open(); $reader = New-Object System.IO.StreamReader($stream)
        try { return [string]$reader.ReadToEnd() }
        finally { $reader.Dispose() }
    }
    finally { if ($null -ne $archive) { $archive.Dispose() } }
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
$normalRel = 'tools/calibration/checkpoints/checkpoint-81a.json'
$deepRel = 'tools/calibration/checkpoints/checkpoint-81a-deep-calibration.json'
$guardedPs = @(
    'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
    'tools/checkpoints/checkpoint-81a/apply_checkpoint_81a.ps1',
    'tools/checkpoints/checkpoint-81a/test_checkpoint_81a_contract.ps1',
    'tools/calibration/run_calibration_checkpoint.ps1'
)
$guardedDefs = @($normalRel,$deepRel)
& $guard -RepositoryRoot $repositoryRoot -PowerShellPaths $guardedPs -CheckpointDefinitionPaths $guardedDefs

Write-Host '       Validating Checkpoint 81a definitions and unchanged CP81 workload accounting...'
$normal = Read-Json $normalRel
$deep = Read-Json $deepRel
Assert-True ([string]$normal.checkpointId -eq '81a' -and [string]$deep.checkpointId -eq '81a') 'Checkpoint 81a definition ID mismatch.'
Assert-True ([string]$normal.manifestFile -eq 'CHECKPOINT_81a_SHA256SUMS.txt' -and [string]$deep.manifestFile -eq 'CHECKPOINT_81a_SHA256SUMS.txt') 'Checkpoint 81a manifest binding mismatch.'
Assert-True ([string]$normal.outputRoot -eq 'out/checkpoint-81a' -and [string]$deep.outputRoot -eq 'out/checkpoint-81a-deep-calibration') 'Checkpoint 81a output-root binding mismatch.'
Assert-True ((@($normal.nativeDependencyPrecheck.powerShellPaths) -join '|') -eq ($guardedPs -join '|')) 'Checkpoint 81a normal native-dependency PowerShell path binding mismatch.'
Assert-True ((@($deep.nativeDependencyPrecheck.powerShellPaths) -join '|') -eq ($guardedPs -join '|')) 'Checkpoint 81a deep native-dependency PowerShell path binding mismatch.'
Assert-True ((@($normal.nativeDependencyPrecheck.checkpointDefinitionPaths) -join '|') -eq ($guardedDefs -join '|')) 'Checkpoint 81a normal native-dependency definition binding mismatch.'
Assert-True ((@($deep.nativeDependencyPrecheck.checkpointDefinitionPaths) -join '|') -eq ($guardedDefs -join '|')) 'Checkpoint 81a deep native-dependency definition binding mismatch.'
Assert-True (@($normal.stages).Count -eq 11 -and [int]$normal.checkpointMetrics.stageCount -eq 11) 'Checkpoint 81a normal stage-count mismatch.'
Assert-True ([int]$normal.checkpointMetrics.monteCarloVariantCount -eq 96 -and [int]$normal.checkpointMetrics.trialsAtDefault -eq 960000 -and [int]$normal.checkpointMetrics.smokeVariantExecutions -eq 96 -and [int]$normal.checkpointMetrics.smokeTrialsAtDefault -eq 96 -and [int]$normal.checkpointMetrics.totalTrialExecutionsAtDefault -eq 960096) 'Checkpoint 81a normal workload accounting mismatch.'
Assert-True (@($deep.stages).Count -eq 33 -and [int]$deep.checkpointMetrics.stageCount -eq 33 -and [int]$deep.checkpointMetrics.monteCarloVariantCount -eq 1694 -and [int]$deep.checkpointMetrics.trialsAtDefault -eq 16940000 -and [int]$deep.checkpointMetrics.smokeVariantExecutions -eq 150 -and [int]$deep.checkpointMetrics.smokeTrialsAtDefault -eq 150 -and [int]$deep.checkpointMetrics.totalTrialExecutionsAtDefault -eq 16940150) 'Checkpoint 81a Deep Calibration workload accounting mismatch.'
$expectedStages = @('deterministic','tl1-phase-a','tl1-phase-b','tl1-installation-space-envelope','tl1-sensor-ew-foundation','tl2-tactical-computer-ew-permutation-preflight','tl2-tactical-computer-ew-permutation-smoke','tl2-tactical-computer-ew-integration-permutations','auxiliary-resource-endurance','checkpoint-53-resource-semantics-lock','runner-self-tests')
Assert-True ((@($normal.stages | ForEach-Object { [string]$_.id }) -join '|') -eq ($expectedStages -join '|')) 'Checkpoint 81a normal stage ordering mismatch.'
$normalSelfTestStages = @($normal.stages | Where-Object { [string]$_.id -eq 'runner-self-tests' })
$deepSelfTestStages = @($deep.stages | Where-Object { [string]$_.id -eq 'runner-self-tests' })
Assert-True ($normalSelfTestStages.Count -eq 1 -and [int]$normalSelfTestStages[0].metrics.selfTestCount -eq 48 -and $deepSelfTestStages.Count -eq 1 -and [int]$deepSelfTestStages[0].metrics.selfTestCount -eq 48) 'Checkpoint 81a ScenarioRunner self-test workload must declare the unchanged 48 tests in normal and Deep Calibration definitions.'
Assert-True ([string]$normal.primaryStudy.id -eq 'tl2-itc08-tactical-computer-ew-integration-permutations' -and [int]$normal.primaryStudy.variantCount -eq 96) 'Checkpoint 81a primary-study binding mismatch.'
Assert-True ([string]$deep.primaryStudy.id -eq 'tl2-itc08-tactical-computer-ew-integration-permutations' -and [int]$deep.primaryStudy.variantCount -eq 96) 'Checkpoint 81a Deep Calibration primary-study binding mismatch.'

$policy = Read-Json 'docs/design/testing/checkpoint_81_validation_suite_policy_v0_1.json'
Assert-True ([int]$policy.checkpoint -eq 81 -and [string]$policy.acceptedBaseline -eq '80' -and -not [bool]$policy.blockingBalanceTargets) 'Checkpoint 81 validation policy identity mismatch.'
Assert-True ([int]$policy.normal.stageCount -eq 11 -and [int]$policy.normal.monteCarloVariantCount -eq 96 -and [int]$policy.normal.totalTrialExecutions -eq 960096) 'Checkpoint 81 policy normal workload mismatch.'
Assert-True ([int]$policy.deepCalibration.stageCount -eq 33 -and [int]$policy.deepCalibration.monteCarloVariantCount -eq 1694 -and [int]$policy.deepCalibration.totalTrialExecutions -eq 16940150) 'Checkpoint 81 policy Deep Calibration workload mismatch.'
Assert-True ([int]$policy.candidateControls.tl1TacticalComputerTargetingPp -eq 10 -and [int]$policy.candidateControls.tl2CandidateTacticalComputerTargetingPp -eq 12 -and [int]$policy.candidateControls.tl1TacticalComputerDegradedFirePenaltyPercentagePoints -eq 25 -and [int]$policy.candidateControls.evasiveCompensationPp -eq 0 -and [int]$policy.candidateControls.productionReactorOutput -eq 5 -and -not [bool]$policy.candidateControls.productionTl2ValuesPromoted) 'Checkpoint 81 candidate isolation policy mismatch.'
Assert-True ([int]$policy.permutationSuiteControls.geometryCount -eq 3 -and [int]$policy.permutationSuiteControls.comparisonGroupCount -eq 12 -and [int]$policy.permutationSuiteControls.variantsPerComparisonGroup -eq 8 -and [bool]$policy.permutationSuiteControls.pairedCommonRandomStreams -and [bool]$policy.permutationSuiteControls.dependencyRelevantSubmatrixOnly -and -not [bool]$policy.permutationSuiteControls.automaticFullCartesianRerun) 'Checkpoint 81 permutation-suite policy mismatch.'

Write-Host '       Validating Concept v0.6s, Technology Architecture Matrix, and standing permutation-suite authority...'
$concept = Read-DocxText 'docs/Star_Cluster_Game_Concept_v0.6s.docx'
Assert-True ($concept.Contains('Checkpoints 79a and 80 now provide accepted diagnostic evidence') -and $concept.Contains('legacy TL2 Tactical Computer +12 percentage-point ordinary-targeting candidate') -and $concept.Contains('Technology Integration Permutation Suites') -and $concept.Contains('dependency-relevant submatrix') -and $concept.Contains('C-055') -and $concept.Contains('Technology Integration Permutation Suite')) 'Concept v0.6s is missing CP80 evidence, CP81 direction, or standing permutation-suite architecture.'
$matrixMd = Read-NormalizedMarkdown 'docs/design/player_technology/Technology_Architecture_Matrix_v1.md'
Assert-True ($matrixMd.Contains('Checkpoint 79a / 80 evidence and Checkpoint 81 follow-up') -and $matrixMd.Contains('596a90b51ae73691e5571b270785f445faed7ed443177f52aa5effff429cb992') -and $matrixMd.Contains('Technology Integration Permutation Suite') -and $matrixMd.Contains('96-variant paired +10/+12 comparison')) 'Technology Architecture Matrix v1 Markdown is not synchronized to CP80 evidence and CP81.'
$matrix = Read-Json 'docs/archive/player_technology/pre-cp165-active/technology_architecture_matrix_v1.json'
Assert-True ([int]$matrix.checkpoint -eq 81 -and [string]$matrix.authority.concept -eq 'docs/Star_Cluster_Game_Concept_v0.6s.docx') 'Matrix v1 JSON authority marker mismatch.'
$cp80Evidence = @($matrix.acceptedEvidence | Where-Object { [string]$_.checkpoint -eq '80' })
Assert-True ($cp80Evidence.Count -eq 1 -and [string]$cp80Evidence[0].summarySha256 -eq '596a90b51ae73691e5571b270785f445faed7ed443177f52aa5effff429cb992') 'Matrix v1 JSON does not retain accepted CP80 evidence.'
Assert-True ([int]$matrix.nextFocusedStudy.checkpoint -eq 81 -and [string]$matrix.nextFocusedStudy.studyId -eq 'tl2-itc08-tactical-computer-ew-integration-permutations' -and [int]$matrix.nextFocusedStudy.variantCount -eq 96 -and [int]$matrix.nextFocusedStudy.defaultSubstantiveTrials -eq 960000 -and -not [bool]$matrix.nextFocusedStudy.productionPromotion) 'Matrix v1 JSON CP81 study binding mismatch.'
$suite = Read-Json 'docs/design/testing/technology_integration_permutation_suite_v0_1.json'
Assert-True ([string]$suite.id -eq 'technology-integration-permutation-suite-v0_1' -and [string]$suite.currentStudyId -eq 'tl2-itc08-tactical-computer-ew-integration-permutations' -and [int]$suite.expectedCartesianProductCount -eq 96) 'Standing technology-integration suite identity/count mismatch.'
Assert-True ([string]$suite.pairedComparison.sharedRandomStreamKey -eq 'comparisonGroup' -and [int]$suite.pairedComparison.control -eq 10 -and [int]$suite.pairedComparison.candidate -eq 12) 'Standing suite paired-comparison definition mismatch.'
Assert-True ([int]$suite.frozenDimensions.reactorOutput -eq 5 -and [int]$suite.frozenDimensions.degradedFirePenaltyPp -eq 25 -and [int]$suite.frozenDimensions.evasiveCompensationPp -eq 0 -and -not [bool]$suite.frozenDimensions.sensorRangeChanged -and -not [bool]$suite.frozenDimensions.sensorOverloadChanged -and -not [bool]$suite.frozenDimensions.ewOverloadChanged) 'Standing suite frozen dimensions mismatch.'
$workbookXml = Read-ZipEntryText 'docs/design/player_technology/StarCluster_Technology_Architecture_Matrix_v1.xlsx' 'xl/workbook.xml'
Assert-True ($workbookXml.Contains('Overview') -and $workbookXml.Contains('Architecture Matrix') -and $workbookXml.Contains('TL2 Candidate') -and $workbookXml.Contains('Tactical Computer') -and $workbookXml.Contains('Sensor') -and $workbookXml.Contains('ECM &amp; ECCM') -and $workbookXml.Contains('Validation Plan')) 'Technology Architecture Matrix workbook is missing an expected sheet.'
Assert-Sha256 'docs/archive/Star_Cluster_Game_Concept_v0.6r.docx' '0078184dbb4589aa902e24eaef627d8915e67d625fcceddc628fef6ad2b5dbd1'
Assert-Sha256 'docs/archive/player_technology/pre-cp165-active/tactical_computer_fire_control_profiles_v0_1.json' '3e688832495cc54a6aac15cdbfb5a1fef87959a4c9d07e8d67dcb844ea6e84cc'
Assert-Sha256 'docs/archive/player_technology/pre-cp165-active/tl1_core_combat_numerical_baseline_v0_3.csv' 'd3020245a1fe2d28f6795c96c3c331d905ed02ef5210f3ab661e3475f70cf5be'
Assert-Sha256 'src/StarCluster.ScenarioRunner/Scenarios/SensorEw/tl2-sew01-sensor-discrimination-isolation.json' '4bc354f5628b80c8176f3da94988394f5ee32f44796c30821d88de461bb17853'
Assert-Sha256 'src/StarCluster.ScenarioRunner/Scenarios/TL1Calibration/tl2-itc07-ew-power-pressure-tall-viability.json' '1bd583d7431b7f0a3cc31329e5e38900611c44713a534743dee74c0639ac17b7'
Assert-Sha256 'docs/validation/archive/Checkpoint_80_TL2_EW_Power_Pressure_And_Tall_Viability.md' '98d86ad9958c6ca6a1e203090d8a91c107a20105b79244899dc57c16b2192fcc'
Assert-Sha256 'docs/validation/archive/Checkpoint_81_TL2_Tactical_Computer_EW_Integration_Permutation_Suite.md' 'cf30f3cb80d1013856861d20ee263ebc93304cbdd4ef015a9225e90af62018a2'
Assert-Sha256 'docs/Star_Cluster_Game_Concept_v0.6s.docx' 'a45f31fad68bc58890e7b3dc5abf4da61904c87507d9a35a966831ce3fccd9e8'
Assert-Sha256 'docs/design/player_technology/Technology_Architecture_Matrix_v1.md' 'fde6c193ac48f4c152e1f6aa84ad5075fe0b1b169a947f9e8fec41c4e99478d9'
Assert-Sha256 'docs/archive/player_technology/pre-cp165-active/technology_architecture_matrix_v1.json' '17ff5436b5dd03892191ca66632ced201bcbd9552344e040a85b8cc84a67d42d'
Assert-Sha256 'docs/design/player_technology/StarCluster_Technology_Architecture_Matrix_v1.xlsx' '4acbb6fe2ac39b59fc2a9e02c2502d3b304ee650b516290471c1f8ee2e81d997'
Assert-Sha256 'docs/design/player_technology/tl1_integrated_tactical_combat_schema_v0_20.json' 'd22324069982bb2c6dfc442ba7ac63aec69d5a42570c48eff2175b0b0b1e3425'
Assert-Sha256 'src/StarCluster.ScenarioRunner/Scenarios/TL1Calibration/tl2-itc08-tactical-computer-ew-integration-permutations.json' '489aeb3cf1598de643e14ea1a5120dff348a5836bc896e1472e0d598bc6e7812'
Assert-Sha256 'docs/design/testing/technology_integration_permutation_suite_v0_1.json' '28c5afb1ee511eb5701d876070a1b7b83806b79e4e032dfade4311432ffac605'
Assert-Sha256 'docs/design/testing/checkpoint_81_validation_suite_policy_v0_1.json' 'c5af35a2322803ef018a05e593cff592b1ca6c5025a4a98cd010402a7c0a346b'

Write-Host '       Validating the 96-variant Tactical Computer/EW permutation study independently...'
$study = Read-Json 'src/StarCluster.ScenarioRunner/Scenarios/TL1Calibration/tl2-itc08-tactical-computer-ew-integration-permutations.json'
Assert-True ([string]$study.id -eq 'tl2-itc08-tactical-computer-ew-integration-permutations' -and @($study.variants).Count -eq 96 -and [int]$study.trialsPerVariant -eq 10000) 'CP81 study identity or variant count mismatch.'
Assert-True (@($study.builds).Count -eq 1 -and [string]$study.builds[0].id -eq 'balanced_generalist_ew_major' -and [int]$study.builds[0].usedSpace -eq 35) 'CP81 must use exactly one 35-Space balanced_generalist_ew_major fixture.'
$baselinePath = Join-Path $repositoryRoot 'docs\archive\player_technology\pre-cp165-active\tl1_core_combat_numerical_baseline_v0_3.csv'
$baselineHash = (Get-FileHash -LiteralPath $baselinePath -Algorithm SHA256).Hash.ToLowerInvariant()
Assert-True ($baselineHash -eq [string]$study.baselineSha256) 'CP81 study baseline hash mismatch.'
$groups = @($study.variants | ForEach-Object { [string]$_.comparisonGroup } | Sort-Object -Unique)
Assert-True ($groups.Count -eq 12) 'CP81 must contain exactly twelve comparison groups.'
$expectedLabels = @('firm-reference-c10','firm-reference-c12','wide-eccm2-c10','wide-eccm2-c12','tall-dr1-eccm1-c10','tall-dr1-eccm1-c12','degraded-p25-c10','degraded-p25-c12')
foreach ($groupName in $groups) {
    $group = @($study.variants | Where-Object { [string]$_.comparisonGroup -eq $groupName })
    Assert-True ($group.Count -eq 8) "CP81 comparison group '$groupName' must contain exactly eight variants."
    Assert-True ((@($group | ForEach-Object { [string]$_.profileLabel } | Sort-Object) -join '|') -eq (@($expectedLabels | Sort-Object) -join '|')) "CP81 comparison group '$groupName' does not contain the exact four EW packages x two computer candidates."
}
Assert-True (@($study.variants | Where-Object { [string]$_.sideAFamily -eq 'Kinetic' }).Count -eq 48 -and @($study.variants | Where-Object { [string]$_.sideAFamily -eq 'Energy' }).Count -eq 48) 'CP81 Side-A family coverage must split 48/48.'
Assert-True (@($study.variants | Where-Object { [string]$_.sideBFamily -eq 'Missile' }).Count -eq 48 -and @($study.variants | Where-Object { [string]$_.sideBFamily -eq 'Kinetic' }).Count -eq 48) 'CP81 opponent-family coverage must split 48/48.'
Assert-True (@($study.variants | Where-Object { [string]$_.movementMode -eq 'HoldRange3' -and [string]$_.movementOrder -eq 'Simultaneous' }).Count -eq 32) 'CP81 fixed-range geometry coverage mismatch.'
Assert-True (@($study.variants | Where-Object { [string]$_.movementMode -eq 'TrackAwareOpponentRange' -and [string]$_.movementOrder -eq 'SideAFirst' }).Count -eq 32) 'CP81 Side-A-first geometry coverage mismatch.'
Assert-True (@($study.variants | Where-Object { [string]$_.movementMode -eq 'TrackAwareOpponentRange' -and [string]$_.movementOrder -eq 'SideBFirst' }).Count -eq 32) 'CP81 Side-B-first geometry coverage mismatch.'
Assert-True (@($study.variants | Where-Object { [int]$_.sideATacticalComputerTargetingBonusOverride -eq 10 }).Count -eq 48 -and @($study.variants | Where-Object { [int]$_.sideATacticalComputerTargetingBonusOverride -eq 12 }).Count -eq 48) 'CP81 Tactical Computer candidate coverage must split +10/+12 48/48.'
Assert-True (@($study.variants | Where-Object { [int]$_.sideBTacticalComputerTargetingBonusOverride -ne 10 }).Count -eq 0) 'CP81 Side-B Tactical Computer must remain at +10.'
Assert-True (@($study.variants | Where-Object { [int]$_.sideAReactorOutputOverride -ne 5 -or [int]$_.sideBReactorOutputOverride -ne 5 }).Count -eq 0) 'CP81 must hold both reactor outputs at 5 TP.'
Assert-True (@($study.variants | Where-Object { [string]$_.sideASensorOverloadPolicy -ne 'None' -or [string]$_.sideBSensorOverloadPolicy -ne 'None' -or [string]$_.sideAStlOverloadPolicy -ne 'None' -or [string]$_.sideBStlOverloadPolicy -ne 'None' }).Count -eq 0) 'CP81 must not introduce Sensor/STL overload changes.'
Assert-True (@($study.variants | Where-Object { [bool]$_.sideAAllowsApproximateDirectFire }).Count -eq 24 -and @($study.variants | Where-Object { [bool]$_.sideAAllowsApproximateDirectFire -and [int]$_.sideAApproximateDirectFireAccuracyPenalty -ne 25 }).Count -eq 0) 'CP81 must contain exactly 24 explicit -25 degraded-fire diagnostic variants.'
Assert-True (@($study.variants | Where-Object { [string]$_.sideBFamily -eq 'Missile' -and ([bool]$_.sideBAllowsApproximateDirectFire -or [int]$_.sideBApproximateDirectFireAccuracyPenalty -ne 0) }).Count -eq 0) 'CP81 must not grant missiles degraded fire.'
foreach ($variant in @($study.variants)) {
    $label = [string]$variant.profileLabel
    $package = $label -replace '-c(10|12)$',''
    $computer = [int]$variant.sideATacticalComputerTargetingBonusOverride
    Assert-True ($computer -eq 10 -or $computer -eq 12) "CP81 '$($variant.id)' has unexpected computer candidate."
    if ($package -eq 'firm-reference') {
        Assert-True ([string]$variant.sideBEcmPolicy -eq 'None' -and [string]$variant.sideAEccmPolicy -eq 'None' -and [string]$variant.sideASensorEwProfileId -eq 'tl1-balanced-0-control' -and -not [bool]$variant.sideAAllowsApproximateDirectFire) "CP81 '$($variant.id)' Firm-reference package mismatch."
    }
    elseif ($package -eq 'wide-eccm2') {
        Assert-True ([string]$variant.sideBEcmPolicy -eq 'Normal' -and [int]$variant.sideBEcmNormalRatingOverride -eq 2 -and [string]$variant.sideASensorEwProfileId -eq 'tl1-balanced-0-control' -and [string]$variant.sideAEccmPolicy -eq 'ReactiveNormal' -and [int]$variant.sideAEccmNormalRatingOverride -eq 2 -and -not [bool]$variant.sideAAllowsApproximateDirectFire) "CP81 '$($variant.id)' wide ECCM2 package mismatch."
    }
    elseif ($package -eq 'tall-dr1-eccm1') {
        Assert-True ([string]$variant.sideBEcmPolicy -eq 'Normal' -and [int]$variant.sideBEcmNormalRatingOverride -eq 2 -and [string]$variant.sideASensorEwProfileId -eq 'tl2-discrimination-1-candidate' -and [string]$variant.sideAEccmPolicy -eq 'ReactiveNormal' -and [int]$variant.sideAEccmNormalRatingOverride -eq 1 -and -not [bool]$variant.sideAAllowsApproximateDirectFire) "CP81 '$($variant.id)' tall DR1 + ECCM1 package mismatch."
    }
    elseif ($package -eq 'degraded-p25') {
        Assert-True ([string]$variant.sideBEcmPolicy -eq 'Normal' -and [int]$variant.sideBEcmNormalRatingOverride -eq 2 -and [string]$variant.sideASensorEwProfileId -eq 'tl1-balanced-0-control' -and [string]$variant.sideAEccmPolicy -eq 'None' -and [bool]$variant.sideAAllowsApproximateDirectFire -and [int]$variant.sideAApproximateDirectFireAccuracyPenalty -eq 25) "CP81 '$($variant.id)' degraded-fire package mismatch."
    }
    else { throw "Unexpected CP81 EW package '$package'." }
}

Write-Host '       Auditing CP81 actual-consumer integration, shared gates, and report routing...'
$documents = Read-Text 'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatDocuments.cs'
$runner = Read-Text 'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs'
Assert-True ($documents.Contains('JsonPropertyName("sideATacticalComputerTargetingBonusOverride")') -and $documents.Contains('JsonPropertyName("sideBTacticalComputerTargetingBonusOverride")')) 'Integrated study document is missing per-side Tactical Computer targeting overrides.'
Assert-True ($runner.Contains('Tl2TacticalComputerEwPermutationStudyId') -and $runner.Contains('ValidateTl2TacticalComputerEwPermutationCoverage') -and $runner.Contains('ApplyTacticalComputerTargetingOverride') -and $runner.Contains('WriteTl2TacticalComputerEwPermutationReview') -and $runner.Contains('tl2-tactical-computer-ew-integration-permutations-review.csv') -and $runner.Contains('tl2-tactical-computer-ew-integration-permutations-paired-deltas.csv')) 'CP81 study is not wired through dispatch, validation, override application, and reporting.'
$reactiveEwStart = $runner.IndexOf('if (studyId == Tl1ReactiveEwSubphaseStudyId ||', [StringComparison]::Ordinal)
$reactiveEwEnd = if ($reactiveEwStart -ge 0) { $runner.IndexOf('{', $reactiveEwStart, [StringComparison]::Ordinal) } else { -1 }
Assert-True ($reactiveEwStart -ge 0 -and $reactiveEwEnd -gt $reactiveEwStart) 'Unable to isolate the current reactive-EW study classification block.'
$reactiveEwStudyBlock = $runner.Substring($reactiveEwStart, $reactiveEwEnd - $reactiveEwStart)
Assert-True ([regex]::Matches($reactiveEwStudyBlock, 'Tl2TacticalComputerEwPermutationStudyId').Count -eq 1) 'CP81 study must be classified exactly once in the current reactive-EW sub-phase whitelist.'
Assert-True ($reactiveEwStudyBlock.Contains('Tl2SensorEwDiscriminationIsolationStudyId') -and $reactiveEwStudyBlock.Contains('Tl2EwPowerPressureTallViabilityStudyId')) 'CP81a must preserve the earlier TL2 reactive-EW study classifications while adding CP81.'
Assert-True ($runner.Contains('int localPdsBaseChance = technology.EffectivePdsChance - technology.TargetingBonus;') -and $runner.Contains('EffectivePdsChance = Math.Clamp(localPdsBaseChance + targetingBonus, 0, 95)')) 'Tactical Computer override must preserve the PDS local base and change only main-computer assistance.'
Assert-True ($runner.Contains('variant.SideATacticalComputerTargetingBonusOverride') -and $runner.Contains('variant.SideBTacticalComputerTargetingBonusOverride')) 'CP81 override is not applied per side.'
$selfTests = Read-Text 'src/StarCluster.ScenarioRunner/ScenarioRunnerSelfTests.cs'
Assert-True ($selfTests.Contains('CP81 Tactical Computer override preserves local PDS base and missile guidance') -and $selfTests.Contains('ApplyTacticalComputerTargetingOverride(control, 12)') -and $selfTests.Contains('candidate.EffectivePdsChance == 47') -and $selfTests.Contains('candidate.Missile.GuidanceChance == 63')) 'CP81 deterministic runner self-test no longer proves Tactical Computer override, PDS-assistance, and missile-guidance separation.'
$buildGatesStart = $runner.IndexOf('private static IReadOnlyList<Tl1IntegratedTacticalCombatGate> BuildGates(')
$writeOutputsStart = $runner.IndexOf('private static void WriteOutputs(', $buildGatesStart)
Assert-True ($buildGatesStart -ge 0 -and $writeOutputsStart -gt $buildGatesStart) 'Could not isolate BuildGates for CP81 gate audit.'
$gateBlock = $runner.Substring($buildGatesStart, $writeOutputsStart - $buildGatesStart)
$gateIds = @('tl2-c81-variant-coverage','tl2-c81-paired-permutation-completeness','tl2-c81-targeting-delta-applied','tl2-c81-firm-reference-clean','tl2-c81-contemporary-dr1-eccm1-restores-firm','tl2-c81-wide-eccm2-restores-firm','tl2-c81-degraded-fire-penalty-held','tl2-c81-five-power-isolation','tl2-c81-no-evasive-compensation','tl2-c81-no-production-promotion','tl2-c81-outcomes-review-only')
foreach ($gateId in $gateIds) {
    $count = [regex]::Matches($gateBlock, [regex]::Escape('"' + $gateId + '"')).Count
    Assert-True ($count -eq 1) "Checkpoint 81 BuildGates block must contain exactly one '$gateId' gate."
}
Assert-True ([regex]::Matches($gateBlock, 'tl2-c81-').Count -eq 11) 'Checkpoint 81 release-gate block must contain exactly eleven CP81 gates.'
$policyGateStart = $gateBlock.IndexOf('"policy-telemetry"', [StringComparison]::Ordinal)
$attackGateStart = $gateBlock.IndexOf('"attack-layer-telemetry"', $policyGateStart, [StringComparison]::Ordinal)
Assert-True ($policyGateStart -ge 0 -and $attackGateStart -gt $policyGateStart) 'Unable to isolate the shared policy-telemetry gate inside BuildGates.'
$policyGateText = $gateBlock.Substring($policyGateStart, $attackGateStart - $policyGateStart)
Assert-True ([regex]::Matches($policyGateText, 'Tl2TacticalComputerEwPermutationStudyId').Count -eq 2) 'CP81 must be classified exactly twice inside shared policy-telemetry: pass predicate and diagnostic branch.'

Write-Host '       Validating schema v0.20, production exclusions, and missile boundaries...'
$schema = Read-Json 'docs/design/player_technology/tl1_integrated_tactical_combat_schema_v0_20.json'
Assert-True ([string]$schema.'$id' -eq 'star-cluster-tl1-integrated-tactical-combat-schema-v0-20') 'Integrated combat schema v0.20 ID mismatch.'
$variantProps = @($schema.'$defs'.variant.properties.PSObject.Properties.Name)
foreach ($property in @('sideATacticalComputerTargetingBonusOverride','sideBTacticalComputerTargetingBonusOverride','sideASensorEwProfileId','sideBSensorEwProfileId','sideAEcmNormalRatingOverride','sideBEcmNormalRatingOverride','sideAEccmNormalRatingOverride','sideBEccmNormalRatingOverride')) {
    Assert-True ($variantProps -contains $property) "Schema v0.20 is missing '$property'."
}
$baseline = Import-Csv (Join-Path $repositoryRoot 'docs\archive\player_technology\pre-cp165-active\tl1_core_combat_numerical_baseline_v0_3.csv')
$reactor = @($baseline | Where-Object { [string]$_.parameter_id -eq 'reactor_output' })
$ecmMax = @($baseline | Where-Object { [string]$_.parameter_id -eq 'ecm_max' })
$eccmMax = @($baseline | Where-Object { [string]$_.parameter_id -eq 'eccm_max' })
Assert-True ($reactor.Count -eq 1 -and [int]$reactor[0].value -eq 5) 'CP81 must not change production reactor output from 5.'
Assert-True ($ecmMax.Count -eq 1 -and $eccmMax.Count -eq 1 -and [int]$ecmMax[0].value -eq 1 -and [int]$eccmMax[0].value -eq 1) 'CP81 must not promote ECM/ECCM rating 2 into the TL1 production baseline.'
$computerCatalog = Read-Json 'docs/archive/player_technology/pre-cp165-active/tactical_computer_fire_control_profiles_v0_1.json'
Assert-True (@($computerCatalog.profiles).Count -eq 1 -and [string]$computerCatalog.profiles[0].id -eq 'tl1-tactical-computer-fire-control' -and [int]$computerCatalog.profiles[0].technologyLevel -eq 1 -and [int]$computerCatalog.profiles[0].approximateTrackDirectFireAccuracyPenaltyPercentagePoints -eq 25 -and [bool]$computerCatalog.profiles[0].requiresExplicitWeaponCapability -and -not [bool]$computerCatalog.profiles[0].appliesToMissileTerminalAttacks) 'CP81 must not add a production TL2 Tactical Computer or alter TL1 degraded-fire ownership.'
$productionApprox = Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'src') -Recurse -File -Filter '*.cs' | Where-Object { $_.FullName -notlike '*StarCluster.ScenarioRunner*' } | Select-String -SimpleMatch 'allowsApproximateTrackFire: true'
Assert-True (@($productionApprox).Count -eq 0) 'CP81 must not enable degraded fire in production Core/Game weapon construction.'
$missileDoc = Read-NormalizedMarkdown 'docs/design/Missile_Guidance_Datalink_Sensor_And_Seeker_Architecture.md'
Assert-True ($missileDoc.Contains('Ordinary missile profiles') -and $missileDoc.Contains('Firm-terminal') -and $missileDoc.Contains('direct-fire degraded-fire trait')) 'Missile architecture no longer clearly preserves the ordinary Firm-terminal/degraded-fire boundary.'
$studyDoc = Read-NormalizedMarkdown 'docs/design/player_technology/TL2_Tactical_Computer_EW_Integration_Permutation_Study_v0_1.md'
Assert-True ($studyDoc.Contains('+12 percentage-point ordinary Tactical Computer targeting') -and $studyDoc.Contains('96 variants') -and $studyDoc.Contains('common random stream') -and $studyDoc.Contains('No value is automatically promoted')) 'CP81 study documentation is missing candidate, paired-permutation, or no-promotion guidance.'
$calibrationArchitecture = Read-NormalizedMarkdown 'docs/design/Technology_Calibration_And_Simulation_Architecture.md'
Assert-True ($calibrationArchitecture.Contains('Checkpoint_81_Validation_Tiers.md') -and $calibrationArchitecture.Contains('Standing technology-integration permutation suites')) 'Current calibration architecture is not synchronized to CP81 validation tiers/permutation suites.'

Write-Host '       Validating active-document/archive hygiene...'
$activeConcepts = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs') -File -Filter 'Star_Cluster_Game_Concept_v*.docx')
Assert-True ($activeConcepts.Count -eq 1 -and $activeConcepts[0].Name -eq 'Star_Cluster_Game_Concept_v0.6s.docx') 'Exactly Concept v0.6s must remain active under docs/.'
Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot 'docs\archive\Star_Cluster_Game_Concept_v0.6r.docx') -PathType Leaf) 'Concept v0.6r must be archived for continuity.'
$validationFiles = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs\validation') -File -Filter 'Checkpoint_*.md')
Assert-True ($validationFiles.Count -eq 1 -and $validationFiles[0].Name -eq 'Checkpoint_81a_Reactive_EW_Study_Classification_Hotfix.md') 'Exactly one CP81a active validation runbook must remain.'
Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot 'docs\validation\archive\Checkpoint_81_TL2_Tactical_Computer_EW_Integration_Permutation_Suite.md') -PathType Leaf) 'Failed CP81 validation runbook must be archived for hotfix continuity.'
Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot 'docs\validation\archive\Checkpoint_80_TL2_EW_Power_Pressure_And_Tall_Viability.md') -PathType Leaf) 'Checkpoint 80 validation runbook must remain archived.'
$rootTxt = @(Get-ChildItem -LiteralPath $repositoryRoot -File -Filter '*.txt')
Assert-True ($rootTxt.Count -eq 1 -and $rootTxt[0].Name -eq 'CHECKPOINT_81a_SHA256SUMS.txt') 'Repository root must contain only CHECKPOINT_81a_SHA256SUMS.txt as .txt.'

Write-Host '       CP81a hotfix: CP81 permutation study now executes through the current reactive-EW sub-phase; all candidate values remain frozen.'
Write-Host '       Normal workload: 11 stages / 96 substantive variants / 960,000 default substantive trials plus 96 smoke trials.'
Write-Host 'Checkpoint 81a contract validation passed.'
