[CmdletBinding()]
param()

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path

function Assert-True {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) { throw $Message }
}
function Get-OptionalPropertyValue {
    param([Parameter(Mandatory = $true)]$Object,[Parameter(Mandatory = $true)][string]$Name)
    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) { return $null }
    return $property.Value
}
function Read-Json {
    param([Parameter(Mandatory = $true)][string]$RelativePath)
    return Get-Content -LiteralPath (Join-Path $repositoryRoot $RelativePath) -Raw | ConvertFrom-Json
}

$guard = Join-Path $repositoryRoot 'tools\checkpoints\Test-NativeAcceptanceDependencies.ps1'
$normalRel = 'tools/calibration/checkpoints/checkpoint-73.json'
$deepRel = 'tools/calibration/checkpoints/checkpoint-73-deep-calibration.json'
$guardedPs = @(
    'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
    'tools/checkpoints/checkpoint-73/apply_checkpoint_73.ps1',
    'tools/checkpoints/checkpoint-73/test_checkpoint_73_contract.ps1',
    'tools/calibration/run_calibration_checkpoint.ps1'
)
& $guard -RepositoryRoot $repositoryRoot -PowerShellPaths $guardedPs -CheckpointDefinitionPaths @($normalRel, $deepRel)

$normal = Read-Json $normalRel
$deep = Read-Json $deepRel
Assert-True ([string]$normal.checkpointId -eq '73' -and [string]$deep.checkpointId -eq '73') 'Checkpoint 73 definition ID mismatch.'
Assert-True ([string]$normal.manifestFile -eq 'CHECKPOINT_73_SHA256SUMS.txt' -and [string]$deep.manifestFile -eq 'CHECKPOINT_73_SHA256SUMS.txt') 'Checkpoint 73 manifest binding mismatch.'
Assert-True (@($normal.stages).Count -eq 11) 'Checkpoint 73 normal suite must contain 11 stages.'
Assert-True (@($deep.stages).Count -eq 30) 'Checkpoint 73 Deep Calibration must contain 30 stages.'
Assert-True ([int]$normal.checkpointMetrics.monteCarloVariantCount -eq 24 -and [int]$normal.checkpointMetrics.trialsAtDefault -eq 240000 -and [int]$normal.checkpointMetrics.smokeTrialsAtDefault -eq 24 -and [int]$normal.checkpointMetrics.totalTrialExecutionsAtDefault -eq 240024) 'Checkpoint 73 normal workload mismatch.'
Assert-True ([int]$deep.checkpointMetrics.monteCarloVariantCount -eq 1568 -and [int]$deep.checkpointMetrics.trialsAtDefault -eq 15680000 -and [int]$deep.checkpointMetrics.smokeTrialsAtDefault -eq 24 -and [int]$deep.checkpointMetrics.totalTrialExecutionsAtDefault -eq 15680024) 'Checkpoint 73 Deep Calibration workload mismatch.'
foreach ($definitionDocument in @($normal, $deep)) {
    Assert-True ([bool]$definitionDocument.nativeDependencyPrecheck.required) 'Checkpoint 73 definitions must require native dependency precheck.'
    Assert-True ((@($definitionDocument.nativeDependencyPrecheck.powerShellPaths) -join '|') -eq ($guardedPs -join '|')) 'Checkpoint 73 native dependency PowerShell binding mismatch.'
    Assert-True ((@($definitionDocument.nativeDependencyPrecheck.checkpointDefinitionPaths) -join '|') -eq (@($normalRel,$deepRel) -join '|')) 'Checkpoint 73 native dependency definition binding mismatch.'
}

$policyRel = 'docs/design/testing/checkpoint_73_validation_suite_policy_v0_1.json'
$policy = Read-Json $policyRel
Assert-True ([int]$policy.normal.stageCount -eq 11 -and [int]$policy.normal.monteCarloVariantCount -eq 24 -and [int]$policy.normal.smokeTrials -eq 24 -and [int]$policy.normal.totalTrialExecutions -eq 240024) 'Checkpoint 73 normal validation-policy mismatch.'
Assert-True ([int]$policy.deepCalibration.stageCount -eq 30 -and [int]$policy.deepCalibration.monteCarloVariantCount -eq 1568 -and [int]$policy.deepCalibration.smokeTrials -eq 24 -and [int]$policy.deepCalibration.totalTrialExecutions -eq 15680024) 'Checkpoint 73 Deep Calibration validation-policy mismatch.'
Assert-True (-not [bool]$policy.blockingBalanceTargets -and -not [bool]$policy.aiDoctrineControls.promotionAutomatic -and [bool]$policy.aiDoctrineControls.playerInformationParityRequired -and [bool]$policy.aiDoctrineControls.evidenceDraftRequired) 'Checkpoint 73 doctrine evidence/promotion policy mismatch.'
Assert-True ([bool]$policy.studyControls.ecmBeforeEccm -and -not [bool]$policy.studyControls.ewInitiativeReroll -and [bool]$policy.studyControls.reservedPowerMeansUncommittedPower) 'Checkpoint 73 EW timing policy mismatch.'
Assert-True (-not [bool]$policy.productionControls.movementPhaseFireImplementedByCheckpoint73 -and -not [bool]$policy.productionControls.degradedFireImplementedByCheckpoint73) 'Checkpoint 73 must keep movement-phase fire and degraded fire Concept-only.'

$schemaRel = 'docs/design/player_technology/tl1_integrated_tactical_combat_schema_v0_17.json'
$schema = Read-Json $schemaRel
Assert-True ([string]$schema.'$id' -eq 'star-cluster-tl1-integrated-tactical-combat-schema-v0-17') 'Checkpoint 73 integrated-combat schema identity mismatch.'
$schemaProperties = $schema.properties
$schemaVariantProperties = $schema.'$defs'.variant.properties
Assert-True ($null -ne $schemaProperties.aiDoctrineCatalog -and $null -ne $schemaVariantProperties.sideAAiDoctrineId -and $null -ne $schemaVariantProperties.sideBAiDoctrineId) 'Checkpoint 73 schema must expose AI doctrine catalog and per-side doctrine IDs.'

$registrySchemaRel = 'docs/design/ai/ai_doctrine_registry_schema_v0_1.json'
$registryRel = 'docs/archive/ai/pre-cp165-active/ai_doctrine_registry_v0_1.json'
$evidenceSchemaRel = 'docs/design/ai/ai_doctrine_evidence_draft_schema_v0_1.json'
$registrySchema = Read-Json $registrySchemaRel
$registry = Read-Json $registryRel
$evidenceSchema = Read-Json $evidenceSchemaRel
Assert-True ([string]$registrySchema.'$id' -eq 'star-cluster-ai-doctrine-registry-schema-v0-1' -and [string]$registry.schemaVersion -eq 'star-cluster-ai-doctrine-registry-v1' -and [string]$registry.registryVersion -eq '0.1') 'Checkpoint 73 AI doctrine registry identity mismatch.'
Assert-True ([string]$evidenceSchema.'$id' -eq 'star-cluster-ai-doctrine-evidence-draft-schema-v0-1') 'Checkpoint 73 evidence-draft schema identity mismatch.'
$dependencies = @($registry.dependencies)
$doctrines = @($registry.doctrines)
$evidence = @($registry.evidence)
Assert-True ($dependencies.Count -ge 7 -and $doctrines.Count -eq 5 -and $evidence.Count -eq 2) 'Checkpoint 73 registry dependency/doctrine/evidence count mismatch.'
Assert-True (@($doctrines | Where-Object { [bool]$_.informationPolicy.usesHiddenEnemyRatings }).Count -eq 0) 'AI doctrines must never consume hidden enemy EW ratings.'
$accepted = @($doctrines | Where-Object { [string]$_.id -eq 'tl1-ew-reactive-eccm-v1' })
Assert-True ($accepted.Count -eq 1 -and [string]$accepted[0].status -eq 'accepted' -and [string]$accepted[0].acceptedCheckpoint -eq '72' -and [string]$accepted[0].ecmHeuristic -eq 'Never' -and [string]$accepted[0].eccmHeuristic -eq 'ReactiveOnFirmDegradation') 'CP72 reactive ECCM must remain the accepted registry doctrine.'
$cp72Evidence = @($evidence | Where-Object { [string]$_.id -eq 'cp72-reactive-eccm-accepted' })
Assert-True ($cp72Evidence.Count -eq 1 -and [string]$cp72Evidence[0].checkpoint -eq '72' -and [string]$cp72Evidence[0].studyId -eq 'tl1-itc14-reactive-ew-subphase' -and [string]$cp72Evidence[0].resultSha256 -eq 'cb30e4d3800a0474aaed0447390cd18542962915676cd710bd28db23b5cc4f04') 'CP72 reactive-ECCM evidence provenance mismatch.'
$candidates = @($doctrines | Where-Object { [string]$_.status -eq 'experimental' })
Assert-True ($candidates.Count -eq 3) 'Checkpoint 73 requires exactly three experimental ECM doctrines.'

$studyRel = 'src/StarCluster.ScenarioRunner/Scenarios/TL1Calibration/tl1-itc15-ew-ai-doctrine.json'
$study = Read-Json $studyRel
Assert-True ([string]$study.id -eq 'tl1-itc15-ew-ai-doctrine' -and [int]$study.trialsPerVariant -eq 10000 -and @($study.variants).Count -eq 24) 'Checkpoint 73 study identity/workload mismatch.'
Assert-True ([int64]$study.masterSeed -eq 730100 -and [string]$study.aiDoctrineCatalog -eq $registryRel) 'Checkpoint 73 master seed or registry binding mismatch.'
$variants = @($study.variants)
$doctrineIds = @('tl1-ew-none-v1','tl1-ew-always-ecm-reactive-eccm-v1','tl1-ew-preserve-offense-v1','tl1-ew-preserve-combat-package-v1')
foreach ($id in $doctrineIds) {
    Assert-True (@($variants | Where-Object { [string]$_.sideAAiDoctrineId -eq $id -and [string]$_.sideBAiDoctrineId -eq $id }).Count -eq 6) "Checkpoint 73 doctrine '$id' must occupy exactly six variants."
}
$pairings = @('Kinetic|Missile','Energy|Missile','Kinetic|Energy')
$orders = @('SideAFirst','SideBFirst')
foreach ($pair in $pairings) {
    $parts = $pair.Split('|')
    foreach ($order in $orders) {
        $context = @($variants | Where-Object { [string]$_.sideAFamily -eq $parts[0] -and [string]$_.sideBFamily -eq $parts[1] -and [string]$_.movementOrder -eq $order })
        Assert-True ($context.Count -eq 4) "Checkpoint 73 context $pair/$order must contain four doctrine variants."
    }
}
foreach ($v in $variants) {
    Assert-True ([string]$v.sideAAiDoctrineId -eq [string]$v.sideBAiDoctrineId) "Variant '$($v.id)' must use a symmetric doctrine pairing."
    Assert-True ([string]$v.sensorEwProfileId -eq 'balanced-0' -and [int]$v.sideAReactorOutputOverride -eq 5 -and [int]$v.sideBReactorOutputOverride -eq 5 -and [int]$v.startingFuel -eq 100 -and [int]$v.initialRangeHexes -eq 4) "Variant '$($v.id)' fixed Sensor/EW/power/geometry controls drifted."
    Assert-True ([string]$v.sideAEcmPolicy -eq 'None' -and [string]$v.sideBEcmPolicy -eq 'None' -and [string]$v.sideAEccmPolicy -eq 'None' -and [string]$v.sideBEccmPolicy -eq 'None') "Variant '$($v.id)' must route EW through AI doctrine rather than legacy per-variant policies."
    Assert-True ([int]$v.sideAEcmNormalPowerCostOverride -eq 1 -and [int]$v.sideBEcmNormalPowerCostOverride -eq 1 -and [int]$v.sideAEccmNormalPowerCostOverride -eq 1 -and [int]$v.sideBEccmNormalPowerCostOverride -eq 1) "Variant '$($v.id)' must preserve 1-TP ECM/ECCM costs."
    Assert-True ([string]$v.sideASensorOverloadPolicy -eq 'None' -and [string]$v.sideBSensorOverloadPolicy -eq 'None' -and [string]$v.sideAStlOverloadPolicy -eq 'None' -and [string]$v.sideBStlOverloadPolicy -eq 'None') "Variant '$($v.id)' must not confound doctrine with overload."
}

$coreRel = 'src/StarCluster.Core/Combat/Tactics/ElectronicWarfareDoctrineService.cs'
$runnerRel = 'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs'
$dtoRel = 'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1AiDoctrineDocuments.cs'
$coreText = Get-Content -LiteralPath (Join-Path $repositoryRoot $coreRel) -Raw
$runnerText = Get-Content -LiteralPath (Join-Path $repositoryRoot $runnerRel) -Raw
$dtoText = Get-Content -LiteralPath (Join-Path $repositoryRoot $dtoRel) -Raw
Assert-True ($coreText.Contains('PreserveOffenseAndEccm') -and $coreText.Contains('PreserveCombatPackageAndEccm') -and $coreText.Contains('ReactiveOnFirmDegradation')) 'Checkpoint 73 Core doctrine heuristics are incomplete.'
Assert-True (-not $coreText.Contains('EnemyEcmRating') -and -not $coreText.Contains('EnemyEccmRating') -and -not $coreText.Contains('EffectiveJammingMargin:')) 'Core AI doctrine context must not expose hidden enemy EW ratings or a numeric Jamming Margin input.'
Assert-True ($runnerText.Contains('LoadAiDoctrineRegistry') -and $runnerText.Contains('AllocateDoctrineEcm') -and $runnerText.Contains('AllocateDoctrineEccm') -and $runnerText.Contains('WriteTl1EwAiDoctrineEvidenceDraft') -and $runnerText.Contains('acceptedBaselineEvidenceIds') -and $runnerText.Contains('acceptedBaselineEvidenceResultSha256') -and $runnerText.Contains('ai-doctrine-evidence-draft.json')) 'Checkpoint 73 integrated runner AI-doctrine/evidence wiring is incomplete.'
Assert-True ($dtoText.Contains('Tl1AiDoctrineRegistryDocument') -and $dtoText.Contains('UsesHiddenEnemyRatings')) 'Checkpoint 73 registry DTO contract is incomplete.'

$concepts = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs') -File -Filter 'Star_Cluster_Game_Concept_v*.docx')
Assert-True ($concepts.Count -eq 1 -and $concepts[0].Name -eq 'Star_Cluster_Game_Concept_v0.6l.docx') 'Checkpoint 73 must expose exactly one active Concept v0.6l.'
Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot 'docs/archive/Star_Cluster_Game_Concept_v0.6k.docx') -PathType Leaf) 'Checkpoint 73 must archive Concept v0.6k.'
Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot 'docs/validation/Checkpoint_73_AI_Doctrine_Registry_And_TL1_EW_Decision_Policy.md') -PathType Leaf) 'Checkpoint 73 active validation runbook is missing.'

Write-Host 'Checkpoint 73 native dependency contract: PowerShell + pinned .NET only; active Python runtime dependencies are rejected before native work.'
Write-Host 'AI doctrine registry: CP72 reactive ECCM accepted with evidence/dependencies; three ECM activation heuristics remain experimental pending CP73 review.'
Write-Host 'AI information parity: own capability + observable track/emissions + uncommitted TP only; hidden enemy EW ratings and internal Jamming Margin are prohibited inputs.'
Write-Host 'Operational doctrine study: 4 doctrines x 3 weapon pairings x 2 movement orders = 24 variants / 240,000 default substantive trials plus 24 smoke trials.'
Write-Host 'Evidence capture: substantive output writes a hash-linked AI doctrine evidence draft; promotion is human-reviewed and never automatic.'
Write-Host 'Validation tiers: 11 normal stages / 24 substantive MC variants; Deep Calibration 30 stages / 1,568 substantive MC variants.'
Write-Host 'Checkpoint 73 contract validation passed.'
