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
    Assert-True ($null -ne $text) "Required text file '$RelativePath' returned null."
    return [string]$text
}
function Read-Json {
    param([string]$RelativePath)
    $text = Read-Text $RelativePath
    Assert-True (-not [string]::IsNullOrWhiteSpace($text)) "Required JSON file '$RelativePath' is empty."
    return ($text | ConvertFrom-Json)
}
function Read-ZipEntryText {
    param([string]$RelativePath, [string]$EntryName)
    $path = Join-Path $repositoryRoot $RelativePath
    Assert-True (Test-Path -LiteralPath $path -PathType Leaf) "Required archive '$RelativePath' is missing."
    Add-Type -AssemblyName System.IO.Compression.FileSystem -ErrorAction Stop | Out-Null
    $archive = $null
    try {
        $archive = [System.IO.Compression.ZipFile]::OpenRead($path)
        $entry = $archive.GetEntry($EntryName)
        Assert-True ($null -ne $entry) "Archive '$RelativePath' is missing '$EntryName'."
        $stream = $null
        $reader = $null
        try {
            $stream = $entry.Open()
            $reader = New-Object System.IO.StreamReader($stream)
            return [string]$reader.ReadToEnd()
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
function Read-DocxText {
    param([string]$RelativePath)
    $xmlText = Read-ZipEntryText $RelativePath 'word/document.xml'
    Assert-True (-not [string]::IsNullOrWhiteSpace($xmlText)) "DOCX '$RelativePath' has empty word/document.xml."
    [xml]$xml = $xmlText
    Assert-True ($null -ne $xml.DocumentElement) "DOCX '$RelativePath' has no document element."
    $text = [string]$xml.DocumentElement.InnerText
    Assert-True (-not [string]::IsNullOrWhiteSpace($text)) "DOCX '$RelativePath' produced no text."
    return $text
}
function Get-ExpectedManifestHash {
    param([string]$RelativePath)
    $manifest = Read-Text 'docs/validation/evidence/checkpoint-81a/CHECKPOINT_81a_SHA256SUMS.txt'
    $escaped = [regex]::Escape($RelativePath.Replace('\\','/'))
    $match = [regex]::Match($manifest, "(?im)^([0-9a-f]{64})  $escaped$")
    Assert-True ($match.Success) "CP81a frozen manifest does not contain '$RelativePath'."
    return $match.Groups[1].Value.ToLowerInvariant()
}

Write-Host '       Validating native-dependency declarations...'
$guard = Join-Path $repositoryRoot 'tools\checkpoints\Test-NativeAcceptanceDependencies.ps1'
$normalRel = 'tools/calibration/checkpoints/checkpoint-82a.json'
$deepRel = 'tools/calibration/checkpoints/checkpoint-82a-deep-calibration.json'
$guardedPs = @(
    'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
    'tools/checkpoints/checkpoint-82a/apply_checkpoint_82a.ps1',
    'tools/checkpoints/checkpoint-82a/test_checkpoint_82a_contract.ps1',
    'tools/calibration/run_calibration_checkpoint.ps1'
)
$guardedDefs = @($normalRel, $deepRel)
& $guard -RepositoryRoot $repositoryRoot -PowerShellPaths $guardedPs -CheckpointDefinitionPaths $guardedDefs

Write-Host '       Validating Checkpoint 82a definitions and unchanged deterministic workload...'
$normal = Read-Json $normalRel
$deep = Read-Json $deepRel
Assert-True ([string]$normal.checkpointId -eq '82a' -and [string]$deep.checkpointId -eq '82a') 'Checkpoint 82a definition ID mismatch.'
Assert-True ([string]$normal.manifestFile -eq 'CHECKPOINT_82a_SHA256SUMS.txt' -and [string]$deep.manifestFile -eq 'CHECKPOINT_82a_SHA256SUMS.txt') 'Checkpoint 82a manifest binding mismatch.'
Assert-True ([string]$normal.outputRoot -eq 'out/checkpoint-82a' -and [string]$deep.outputRoot -eq 'out/checkpoint-82a-deep-calibration') 'Checkpoint 82a output-root binding mismatch.'
Assert-True (@($normal.stages).Count -eq 8 -and [int]$normal.checkpointMetrics.stageCount -eq 8) 'Checkpoint 82a normal stage-count mismatch.'
Assert-True ([int]$normal.checkpointMetrics.monteCarloVariantCount -eq 0 -and [int]$normal.checkpointMetrics.trialsAtDefault -eq 0) 'Checkpoint 82a normal suite must contain no Monte Carlo workload.'
Assert-True (@($deep.stages).Count -eq 33 -and [int]$deep.checkpointMetrics.monteCarloVariantCount -eq 1694 -and [int]$deep.checkpointMetrics.trialsAtDefault -eq 16940000) 'Checkpoint 82a Deep Calibration workload must preserve the accepted CP81a coverage.'
$normalStageIds = @($normal.stages | ForEach-Object { [string]$_.id })
$expectedNormal = @('deterministic','tl1-phase-a','tl1-phase-b','tl1-installation-space-envelope','tl1-sensor-ew-foundation','auxiliary-resource-endurance','checkpoint-53-resource-semantics-lock','runner-self-tests')
Assert-True (($normalStageIds -join '|') -eq ($expectedNormal -join '|')) 'Checkpoint 82a normal stage ordering mismatch.'
$self = @($normal.stages | Where-Object { [string]$_.id -eq 'runner-self-tests' })
Assert-True ($self.Count -eq 1 -and [int]$self[0].metrics.selfTestCount -eq 48) 'Checkpoint 82a must retain 48 ScenarioRunner self-tests.'
Assert-True ((@($normal.nativeDependencyPrecheck.powerShellPaths) -join '|') -eq ($guardedPs -join '|')) 'Checkpoint 82a normal native-dependency PowerShell binding mismatch.'
Assert-True ((@($deep.nativeDependencyPrecheck.powerShellPaths) -join '|') -eq ($guardedPs -join '|')) 'Checkpoint 82a deep native-dependency PowerShell binding mismatch.'
Assert-True ((@($normal.nativeDependencyPrecheck.checkpointDefinitionPaths) -join '|') -eq ($guardedDefs -join '|')) 'Checkpoint 82a normal native-dependency definition binding mismatch.'
Assert-True ((@($deep.nativeDependencyPrecheck.checkpointDefinitionPaths) -join '|') -eq ($guardedDefs -join '|')) 'Checkpoint 82a deep native-dependency definition binding mismatch.'

Write-Host '       Validating TL2 information-control working package...'
$profile = Read-Json 'docs/design/player_technology/tl2_computing_sensor_ew_working_profile_v0_1.json'
Assert-True ([string]$profile.status -eq 'validated_working_candidate_not_production_component_data') 'TL2 working profile status mismatch.'
Assert-True ([int]$profile.tacticalComputer.ordinaryTargetingAssistanceOperationalPp -eq 12) 'TL2 Tactical Computer working targeting must be +12 pp.'
Assert-True ([int]$profile.tacticalComputer.approximateTrackDirectFirePenaltyPp -eq -25) 'TL2 degraded-fire working penalty must remain -25 pp.'
Assert-True ([int]$profile.tacticalComputer.evasiveCompensationPp -eq 0) 'TL2 Evasive Compensation must remain 0.'
Assert-True ([int]$profile.sensor.discriminationResistance -eq 1) 'TL2 Sensor DR working candidate must be 1.'
Assert-True ([string]$profile.sensor.rangeStatus -eq 'unchanged_study_fixture_not_tl2_promotion') 'TL2 Sensor physical reach must remain unpromoted.'
Assert-True ([int]$profile.ecm.normalRatingCeiling -eq 2 -and [int]$profile.ecm.tpPerRating -eq 1) 'TL2 ECM working candidate must be ceiling 2 at 1 TP/rating.'
Assert-True ([int]$profile.eccm.normalRatingCeiling -eq 2 -and [int]$profile.eccm.tpPerRating -eq 1) 'TL2 ECCM working candidate must be ceiling 2 at 1 TP/rating.'
Assert-True ([string]$profile.ecm.newTl2OverloadBehavior -eq 'deferred_not_promoted' -and [string]$profile.eccm.newTl2OverloadBehavior -eq 'deferred_not_promoted') 'New TL2 ECM/ECCM overload behavior must remain deferred.'
Assert-True ([int]$profile.referenceEnvironment.tacticalPowerReference -eq 5 -and [string]$profile.referenceEnvironment.reactorSixStatus -eq 'diagnostic_sensitivity_only_not_promoted') 'Checkpoint 82a must not promote reactor output 6.'
Assert-True (@($profile.acceptedEvidence).Count -eq 3) 'TL2 working profile must bind exactly the three accepted evidence checkpoints.'
$e79 = @($profile.acceptedEvidence | Where-Object { [string]$_.checkpoint -eq '79a' }); $e80 = @($profile.acceptedEvidence | Where-Object { [string]$_.checkpoint -eq '80' }); $e81 = @($profile.acceptedEvidence | Where-Object { [string]$_.checkpoint -eq '81a' })
Assert-True ($e79.Count -eq 1 -and [string]$e79[0].summarySha256 -eq 'eecbdf5a935d984655416c3fe4fae61308493cad778c89b2272f84ea5b761c61') 'CP79a evidence hash mismatch.'
Assert-True ($e80.Count -eq 1 -and [string]$e80[0].summarySha256 -eq '596a90b51ae73691e5571b270785f445faed7ed443177f52aa5effff429cb992') 'CP80 evidence hash mismatch.'
Assert-True ($e81.Count -eq 1 -and [string]$e81[0].summarySha256 -eq 'e0e351298a5c276179b20a72376aeef02a93c9c995031acebfab4d6b643d1c6c') 'CP81a evidence hash mismatch.'

Write-Host '       Validating Matrix v1 and standing permutation-suite v0.2...'
$matrix = Read-Json 'docs/archive/player_technology/pre-cp165-active/technology_architecture_matrix_v1.json'
Assert-True ([int]$matrix.checkpoint -eq 82 -and [string]$matrix.authority.concept -eq 'docs/Star_Cluster_Game_Concept_v0.6t.docx') 'Matrix v1 CP82 consolidation authority binding mismatch.'
Assert-True ($null -ne $matrix.statusDefinitions.validated_working_candidate) 'Matrix v1 must define validated_working_candidate status.'
$tl2 = @($matrix.tiers | Where-Object { [int]$_.technologyLevel -eq 2 })
Assert-True ($tl2.Count -eq 1) 'Matrix v1 must contain exactly one TL2 row.'
Assert-True ([string]$tl2[0].tacticalComputer.status -eq 'validated_working_candidate' -and [int]$tl2[0].tacticalComputer.ordinaryTargetingAssistanceOperationalPp -eq 12 -and [int]$tl2[0].tacticalComputer.approximateTrackPenaltyPp -eq -25 -and [int]$tl2[0].tacticalComputer.evasiveCompensationPp -eq 0) 'Matrix v1 TL2 Tactical Computer working values mismatch.'
Assert-True ([string]$tl2[0].sensor.status -eq 'validated_working_candidate' -and [int]$tl2[0].sensor.sensorDiscriminationResistance -eq 1) 'Matrix v1 TL2 Sensor working value mismatch.'
Assert-True ([string]$tl2[0].ecm.status -eq 'validated_working_candidate' -and [int]$tl2[0].ecm.normalRatingCeiling -eq 2 -and [int]$tl2[0].ecm.tpPerRating -eq 1) 'Matrix v1 TL2 ECM working values mismatch.'
Assert-True ([string]$tl2[0].eccm.status -eq 'validated_working_candidate' -and [int]$tl2[0].eccm.normalRatingCeiling -eq 2 -and [int]$tl2[0].eccm.tpPerRating -eq 1) 'Matrix v1 TL2 ECCM working values mismatch.'
Assert-True ([string]$matrix.workingPackages.tl2ComputingSensorEw -eq 'docs/design/player_technology/tl2_computing_sensor_ew_working_profile_v0_1.json') 'Matrix v1 working-package binding mismatch.'
Assert-True (@($matrix.acceptedEvidence | Where-Object { [string]$_.checkpoint -eq '81a' }).Count -eq 1) 'Matrix v1 must include accepted CP81a evidence.'

$suite = Read-Json 'docs/design/testing/technology_integration_permutation_suite_v0_2.json'
Assert-True ([string]$suite.id -eq 'technology-integration-permutation-suite-v0_2' -and [int]$suite.checkpoint -eq 82) 'Standing permutation suite v0.2 identity mismatch.'
Assert-True ([int]$suite.validatedTechnologyPackages.'tl2-information-control-working'.tacticalComputerTargetingPp -eq 12 -and [int]$suite.validatedTechnologyPackages.'tl2-information-control-working'.sensorDiscriminationResistance -eq 1 -and [int]$suite.validatedTechnologyPackages.'tl2-information-control-working'.ecmNormalCeiling -eq 2 -and [int]$suite.validatedTechnologyPackages.'tl2-information-control-working'.eccmNormalCeiling -eq 2) 'Suite v0.2 TL2 package values mismatch.'
$activation = (@($suite.activationPolicy) -join ' ')
Assert-True ($activation.Contains('actual-consumer preflight') -and $activation.Contains('one-trial full-pipeline smoke') -and $activation.Contains('shared/global release-gate classifications') -and $activation.Contains('study-family whitelists') -and $activation.Contains('report routing') -and $activation.Contains('schema/baseline bindings')) 'Suite v0.2 is missing the required integrated-study QA audit coverage.'
Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot 'docs\design\testing\technology_integration_permutation_suite_v0_1.json') -PathType Leaf) 'Historical permutation suite v0.1 must remain for CP81 reproducibility.'

Write-Host '       Validating Concept v0.6t and active documentation semantics...'
$conceptText = Read-DocxText 'docs/Star_Cluster_Game_Concept_v0.6t.docx'
Assert-True ($conceptText.Contains('validated working candidates supported by contemporary evidence but not yet promoted into production component data')) 'Concept v0.6t is missing validated-working-candidate status semantics.'
Assert-True ($conceptText.Contains('Checkpoints 79a, 80, and 81a now establish the first validated TL2 Computing / Sensor-EW working candidate package')) 'Concept v0.6t is missing accepted TL2 working-package consolidation.'
Assert-True ($conceptText.Contains('Tactical Computer ordinary targeting assistance +12 percentage points') -and $conceptText.Contains('computer-owned degraded-fire penalty held at -25 percentage points') -and $conceptText.Contains('Sensor Discrimination Resistance 1') -and $conceptText.Contains('normal ECM and ECCM rating ceilings 2 at one Tactical Power per rating')) 'Concept v0.6t working-package values are incomplete.'
Assert-True ($conceptText.Contains('not a complete production TL2 combat profile')) 'Concept v0.6t must distinguish the working package from a complete production TL2 profile.'
Assert-True ($conceptText.Contains('historical profiles named tl2-production remain compatibility evidence unless explicitly reconciled and promoted')) 'Concept v0.6t must distinguish historical tl2-production identifiers from current authority.'
Assert-True ($conceptText.Contains('C-056') -and $conceptText.Contains('Validated working candidate')) 'Concept v0.6t decision/glossary synchronization is incomplete.'

$matrixMd = Read-Text 'docs/design/player_technology/Technology_Architecture_Matrix_v1.md'
$matrixMdNormalized = [string]($matrixMd.Replace('**','').Replace('__','').Replace('`',''))
Assert-True ($matrixMd.Contains('Validated working candidate') -and $matrixMd.Contains('Accepted Checkpoint 79a / 80 / 81a evidence') -and $matrixMd.Contains('Checkpoint 82 is a **deterministic evidence-consolidation and architecture checkpoint**')) 'Matrix v1 Markdown consolidation is incomplete.'
Assert-True ($matrixMdNormalized.Contains('Historical runtime/study identifiers such as tl2-production are retained for deterministic compatibility and reproducibility only; they are not current Matrix v1 authority unless explicitly reconciled and promoted.')) 'Matrix v1 must explicitly separate historical tl2-production compatibility identifiers from current authority.'
$calArch = Read-Text 'docs/design/Technology_Calibration_And_Simulation_Architecture.md'
Assert-True ($calArch.Contains('validated working candidate') -and $calArch.Contains('technology_integration_permutation_suite_v0_2.json')) 'Technology calibration architecture is not synchronized with CP82.'
$testingReadme = Read-Text 'docs/design/testing/README.md'
Assert-True ($testingReadme.Contains('Checkpoint_82_Validation_Tiers.md') -and $testingReadme.Contains('Cross-study integration audit')) 'Testing README is not synchronized with CP82.'
$wbXml = Read-ZipEntryText 'docs/design/player_technology/StarCluster_Technology_Architecture_Matrix_v1.xlsx' 'xl/workbook.xml'
Assert-True ($wbXml.Contains('TL2 Candidate') -and $wbXml.Contains('Architecture Matrix')) 'Matrix workbook is missing required sheets.'
$overviewXml = Read-ZipEntryText 'docs/design/player_technology/StarCluster_Technology_Architecture_Matrix_v1.xlsx' 'xl/worksheets/sheet1.xml'
$tl2SheetXml = Read-ZipEntryText 'docs/design/player_technology/StarCluster_Technology_Architecture_Matrix_v1.xlsx' 'xl/worksheets/sheet3.xml'
Assert-True ($overviewXml.Contains('tl2-production') -and $overviewXml.Contains('deterministic compatibility') -and $overviewXml.Contains('not current Matrix v1 authority')) 'Matrix workbook Overview must mirror the historical tl2-production authority clarification.'
Assert-True ($tl2SheetXml.Contains('tl2-production') -and $tl2SheetXml.Contains('deterministic compatibility') -and $tl2SheetXml.Contains('not current Matrix v1 authority')) 'Matrix workbook TL2 Candidate sheet must mirror the historical tl2-production authority clarification.'

Write-Host '       Proving production source/tests remain byte-identical to accepted Checkpoint 81a...'
$frozenManifest = Read-Text 'docs/validation/evidence/checkpoint-81a/CHECKPOINT_81a_SHA256SUMS.txt'
$sourceLines = @($frozenManifest -split "`r?`n" | Where-Object { $_ -match '^[0-9a-f]{64}  (src|tests)/' })
Assert-True ($sourceLines.Count -gt 500) 'Frozen CP81a source/test manifest coverage is unexpectedly small.'
foreach ($line in $sourceLines) {
    $m = [regex]::Match($line, '^([0-9a-f]{64})  (.+)$')
    Assert-True ($m.Success) 'Malformed frozen CP81a source/test manifest line.'
    $expected = $m.Groups[1].Value.ToLowerInvariant()
    $relative = $m.Groups[2].Value
    $path = Join-Path $repositoryRoot ($relative.Replace('/','\'))
    Assert-True (Test-Path -LiteralPath $path -PathType Leaf) "Frozen source/test file '$relative' is missing."
    $actual = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    Assert-True ($actual -eq $expected) "Checkpoint 82a unexpectedly changed source/test file '$relative'."
}
Write-Host ("       Frozen source/test hashes: {0} files matched Checkpoint 81a." -f $sourceLines.Count)

Write-Host '       Validating production exclusions and missile boundaries...'
$productionApproximateEnable = Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'src') -Recurse -File -Filter '*.cs' | Where-Object { $_.FullName -notlike '*StarCluster.ScenarioRunner*' } | Select-String -SimpleMatch 'allowsApproximateTrackFire: true'
Assert-True (@($productionApproximateEnable).Count -eq 0) 'Checkpoint 82a must not enable degraded fire on production Core/Game weapon construction.'
$missileDoc = Read-Text 'docs/design/Missile_Guidance_Datalink_Sensor_And_Seeker_Architecture.md'
Assert-True ($missileDoc.Contains('Ordinary missile profiles continue to require the legitimate Firm terminal solution')) 'Ordinary missile Firm-terminal architecture must remain preserved.'

Write-Host '       Validating active-document/archive hygiene...'
$activeConcepts = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs') -File -Filter 'Star_Cluster_Game_Concept_v*.docx')
Assert-True ($activeConcepts.Count -eq 1 -and $activeConcepts[0].Name -eq 'Star_Cluster_Game_Concept_v0.6t.docx') 'Exactly Concept v0.6t must remain active under docs/.'
Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot 'docs\archive\Star_Cluster_Game_Concept_v0.6s.docx') -PathType Leaf) 'Concept v0.6s must be archived.'
$validationFiles = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs\validation') -File -Filter 'Checkpoint_*.md')
Assert-True ($validationFiles.Count -eq 1 -and $validationFiles[0].Name -eq 'Checkpoint_82a_Matrix_Historical_TL2_Production_Authority_Clarification_Hotfix.md') 'Exactly one Checkpoint 82a active validation runbook must remain.'
Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot 'docs\validation\archive\Checkpoint_81a_Reactive_EW_Study_Classification_Hotfix.md') -PathType Leaf) 'Checkpoint 81a validation runbook must be archived.'
Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot 'docs\validation\archive\Checkpoint_82_TL2_Information_Control_Working_Package_Consolidation.md') -PathType Leaf) 'Failed Checkpoint 82 validation runbook must be archived for continuity.'
$rootTxt = @(Get-ChildItem -LiteralPath $repositoryRoot -File -Filter '*.txt')
Assert-True ($rootTxt.Count -eq 1 -and $rootTxt[0].Name -eq 'CHECKPOINT_82a_SHA256SUMS.txt') 'Repository root must contain only CHECKPOINT_82a_SHA256SUMS.txt as .txt.'

Write-Host '       CP82 consolidation: +12 Computer / DR1 Sensor / ECM2 / ECCM2 working candidates; -25 degraded fire; EvComp 0.'
Write-Host '       Explicit non-promotions: Sensor reach, reactor growth, new TL2 overload/efficiency, weapon degraded-fire entitlement, missile Approximate terminal behavior.'
Write-Host '       Normal workload: 8 deterministic stages / 0 Monte Carlo variants.'
Write-Host 'Checkpoint 82a contract validation passed.'
