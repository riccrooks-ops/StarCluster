[CmdletBinding()]
param()

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path

function Assert-True {
    param([bool]$Condition,[string]$Message)
    if (-not $Condition) { throw $Message }
}
function Read-Text {
    param([string]$RelativePath)
    $p = Join-Path $repositoryRoot ($RelativePath.Replace('/','\'))
    Assert-True (Test-Path -LiteralPath $p -PathType Leaf) "Required file '$RelativePath' is missing."
    return [System.IO.File]::ReadAllText($p)
}
function Read-Json {
    param([string]$RelativePath)
    return ((Read-Text $RelativePath) | ConvertFrom-Json)
}
function Hash-Rel {
    param([string]$RelativePath)
    $p = Join-Path $repositoryRoot ($RelativePath.Replace('/','\'))
    Assert-True (Test-Path -LiteralPath $p -PathType Leaf) "Hash target '$RelativePath' is missing."
    return (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()
}
function Require-Property {
    param($Object,[string]$PropertyName,[string]$Context)
    Assert-True ($null -ne $Object) "$Context is null."
    Assert-True ($null -ne $Object.PSObject.Properties[$PropertyName]) "$Context is missing required property '$PropertyName'."
}
function Require-Contains {
    param([string]$Text,[string]$Needle,[string]$Message)
    Assert-True ($Text.IndexOf($Needle,[System.StringComparison]::OrdinalIgnoreCase) -ge 0) $Message
}
function Assert-NoText {
    param([string]$Text,[string]$Needle,[string]$Message)
    Assert-True ($Text.IndexOf($Needle,[System.StringComparison]::OrdinalIgnoreCase) -lt 0) $Message
}
function Read-Manifest {
    param([string]$RelativePath)
    $p = Join-Path $repositoryRoot ($RelativePath.Replace('/','\'))
    Assert-True (Test-Path -LiteralPath $p -PathType Leaf) "Manifest '$RelativePath' is missing."
    $lines = @(Get-Content -LiteralPath $p)
    Assert-True ($lines.Count -gt 0) "Manifest '$RelativePath' is empty."
    $map = @{}
    $lineNumber = 0
    foreach ($line in $lines) {
        $lineNumber++
        Assert-True (-not [string]::IsNullOrWhiteSpace([string]$line)) "Manifest '$RelativePath' contains a blank line at $lineNumber."
        $m = [regex]::Match([string]$line, '^([0-9a-fA-F]{64})  (.+)$')
        Assert-True ($m.Success) "Manifest '$RelativePath' has malformed line $lineNumber."
        $relative = $m.Groups[2].Value.Replace('\','/')
        Assert-True (-not $map.ContainsKey($relative)) "Manifest '$RelativePath' duplicates '$relative'."
        $map[$relative] = $m.Groups[1].Value.ToLowerInvariant()
    }
    return [pscustomobject]@{ PhysicalLineCount=$lines.Count; EntryCount=$map.Count; Entries=$map }
}
function Read-ZipEntryText {
    param([string]$RelativePath,[string]$EntryName)
    $p = Join-Path $repositoryRoot ($RelativePath.Replace('/','\'))
    Assert-True (Test-Path -LiteralPath $p -PathType Leaf) "Archive '$RelativePath' is missing."
    Add-Type -AssemblyName System.IO.Compression.FileSystem -ErrorAction Stop | Out-Null
    $z = [System.IO.Compression.ZipFile]::OpenRead($p)
    try {
        $e = $z.GetEntry($EntryName)
        Assert-True ($null -ne $e) "Archive '$RelativePath' is missing '$EntryName'."
        $stream = $e.Open()
        $reader = New-Object System.IO.StreamReader($stream)
        try { return [string]$reader.ReadToEnd() } finally { $reader.Dispose(); $stream.Dispose() }
    } finally { $z.Dispose() }
}
function Find-Axis {
    param($Study,[string]$Id)
    $matches = @($Study.axes | Where-Object { $null -ne $_.PSObject.Properties['id'] -and [string]$_.id -eq $Id })
    Assert-True ($matches.Count -eq 1) "Cross-TL definition must contain exactly one '$Id' axis."
    return $matches[0]
}

Write-Host '       Validating native-dependency declarations...'
$guard = Join-Path $repositoryRoot 'tools\checkpoints\Test-NativeAcceptanceDependencies.ps1'
$normalRel = 'tools/calibration/checkpoints/checkpoint-88.json'
$deepRel = 'tools/calibration/checkpoints/checkpoint-88-deep-calibration.json'
$guardedPs = @(
    'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
    'tools/checkpoints/checkpoint-88/apply_checkpoint_88.ps1',
    'tools/checkpoints/checkpoint-88/test_checkpoint_88_contract.ps1',
    'tools/calibration/run_calibration_checkpoint.ps1'
)
$guardedDefs = @($normalRel,$deepRel)
& $guard -RepositoryRoot $repositoryRoot -PowerShellPaths $guardedPs -CheckpointDefinitionPaths $guardedDefs

Write-Host '       Validating Checkpoint 88 definitions and workload accounting...'
$normal = Read-Json $normalRel
$deep = Read-Json $deepRel
Assert-True ([string]$normal.checkpointId -eq '88' -and [string]$deep.checkpointId -eq '88') 'Checkpoint 88 definition ID mismatch.'
Assert-True ([string]$normal.manifestFile -eq 'CHECKPOINT_88_SHA256SUMS.txt' -and [string]$deep.manifestFile -eq 'CHECKPOINT_88_SHA256SUMS.txt') 'Checkpoint 88 manifest binding mismatch.'
Assert-True ([string]$normal.outputRoot -eq 'out/checkpoint-88' -and [string]$deep.outputRoot -eq 'out/checkpoint-88-deep-calibration') 'Checkpoint 88 output-root binding mismatch.'
Assert-True (@($normal.stages).Count -eq 13 -and [int]$normal.checkpointMetrics.stageCount -eq 13) 'Checkpoint 88 normal stage-count mismatch.'
Assert-True ([int]$normal.checkpointMetrics.monteCarloVariantCount -eq 288 -and [int]$normal.checkpointMetrics.trialsAtDefault -eq 2880000 -and [int]$normal.checkpointMetrics.smokeVariantExecutions -eq 288 -and [int]$normal.checkpointMetrics.totalTrialExecutionsAtDefault -eq 2880288) 'Checkpoint 88 normal workload mismatch.'
Assert-True (@($deep.stages).Count -eq 14 -and [int]$deep.checkpointMetrics.stageCount -eq 14 -and [int]$deep.checkpointMetrics.monteCarloVariantCount -eq 576 -and [int]$deep.checkpointMetrics.totalTrialExecutionsAtDefault -eq 5760288) 'Checkpoint 88 Deep Calibration workload mismatch.'
Assert-True ([string]$normal.primaryStudy.id -eq 'tl2-itc14-cross-tl-power-aware-information-control-screening' -and [int]$normal.primaryStudy.variantCount -eq 288) 'Checkpoint 88 primary-study metadata mismatch.'
$normalIds = @($normal.stages | ForEach-Object { [string]$_.id })
$expectedNormal = @('deterministic','tl1-phase-a','tl1-phase-b','tl1-installation-space-envelope','tl1-sensor-ew-foundation','cross-tl-build-permutation-preflight','cross-tl-build-permutation-generation','cross-tl-generated-study-preflight','cross-tl-generated-study-smoke','cross-tl-build-permutation-screening','auxiliary-resource-endurance','checkpoint-53-resource-semantics-lock','runner-self-tests')
Assert-True (($normalIds -join '|') -eq ($expectedNormal -join '|')) 'Checkpoint 88 normal stage order/identity mismatch.'
$runnerStage = @($normal.stages | Where-Object { [string]$_.id -eq 'runner-self-tests' })
Assert-True ($runnerStage.Count -eq 1 -and [int]$runnerStage[0].metrics.selfTestCount -eq 54) 'Checkpoint 88 must expect 54 ScenarioRunner self-tests.'

Write-Host '       Validating the mandatory-core 512-build / 288-variant generated study...'
$studyRel = 'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/cross-tl-build-permutation-foundation-v0_2.json'
$study = Read-Json $studyRel
Assert-True ([string]$study.schemaVersion -eq 'star-cluster-cross-tl-build-permutation-v2' -and [string]$study.checkpoint -eq '88') 'Cross-TL foundation v0.2 identity/schema mismatch.'
foreach ($prop in @('constructionGuardrails','aiDoctrineCatalog','aiDoctrineId','variantIdPrefix','axes','namedRecipes','pairingGroups','geometries')) { Require-Property $study $prop 'Cross-TL foundation v0.2' }
$g = $study.constructionGuardrails
Assert-True ([int]$g.minimumMainWeaponCount -eq 1 -and [int]$g.minimumReactorCount -eq 1 -and [bool]$g.additionalMainWeaponsOptional -and [bool]$g.additionalReactorsOptional -and [bool]$g.duplicationMustBeExplicit) 'Cross-TL construction guardrail must require 1 Main Weapon + 1 Reactor while preserving optional explicit duplication.'
Assert-True ([string]$study.aiDoctrineCatalog -eq 'docs/archive/ai/pre-cp165-active/ai_doctrine_registry_v0_2.json' -and [string]$study.aiDoctrineId -eq 'tl1-ew-preserve-combat-package-v1') 'CP88 generated study must bind the accepted preserve-combat-package doctrine.'
Assert-True ([int]$study.expectedLegalBuildCount -eq 512 -and [int]$study.expectedNamedRecipeCount -eq 29 -and [int]$study.expectedLogicalPairingCount -eq 96 -and [int]$study.expectedGeometryCount -eq 3 -and [int]$study.expectedGeneratedVariantCount -eq 288) 'CP88 expected study cardinalities mismatch.'
$axes = @($study.axes)
Assert-True ($axes.Count -eq 8) 'CP88 must retain eight independent working-envelope axes.'
$raw = 1L
foreach ($axis in $axes) { $raw = $raw * @($axis.options).Count }
Assert-True ($raw -eq 512L) "CP88 raw Cartesian envelope must remain 512; found $raw."
$weapon = Find-Axis $study 'weapon'; $reactor = Find-Axis $study 'reactor'
Assert-True (@($weapon.options | Where-Object { $null -eq $_.PSObject.Properties['mainWeaponCount'] -or [int]$_.mainWeaponCount -lt 1 }).Count -eq 0) 'Every CP88 weapon option must explicitly contribute at least one Main Weapon.'
Assert-True (@($reactor.options | Where-Object { $null -eq $_.PSObject.Properties['reactorCount'] -or [int]$_.reactorCount -lt 1 }).Count -eq 0) 'Every CP88 reactor option must explicitly contribute at least one Reactor.'
$recipeIds = @($study.namedRecipes | ForEach-Object { [string]$_.id })
Assert-True ($recipeIds.Count -eq 29 -and @($recipeIds | Select-Object -Unique).Count -eq 29) 'CP88 requires 29 unique named recipes.'
$infoRecipes = @($study.namedRecipes | Where-Object { [string]$_.id -like 'info-*-r6' })
Assert-True ($infoRecipes.Count -eq 16) 'CP88 must contain all 16 information-control attribution recipes.'
$pairCount = 0
$pairKeys = @{}
foreach ($group in @($study.pairingGroups)) {
    foreach ($a in @($group.sideARecipes)) { foreach ($b in @($group.sideBRecipes)) {
        Assert-True ($recipeIds -contains [string]$a) "Unknown Side-A recipe '$a'."
        Assert-True ($recipeIds -contains [string]$b) "Unknown Side-B recipe '$b'."
        $key = ([string]$a) + '|' + ([string]$b)
        Assert-True (-not $pairKeys.ContainsKey($key)) "Duplicate ordered pairing '$key'."
        $pairKeys[$key] = $true; $pairCount++
    }}
}
Assert-True ($pairCount -eq 96) "CP88 requires 96 unique ordered logical pairings; found $pairCount."
Assert-True (@($study.geometries).Count -eq 3) 'CP88 requires three geometry/order contexts.'

Write-Host '       Validating generator, rated-cost doctrine, consumer hooks, and activity gates...'
$generator = Read-Text 'src/StarCluster.ScenarioRunner/CrossTlIntegration/CrossTlBuildPermutationRunner.cs'
foreach ($needle in @('SchemaVersionV2','constructionGuardrails','MeetsMinimumCombatCore','mandatory-combat-core','MainWeaponCount','ReactorCount','AiDoctrineCatalog','SideAAiDoctrineId','SideBAiDoctrineId')) { Require-Contains $generator $needle "Cross-TL generator is missing CP88 hook '$needle'." }
Require-Contains $generator 'AdditionalMainWeaponsOptional' 'Generator must preserve optional second Main Weapons.'
Require-Contains $generator 'AdditionalReactorsOptional' 'Generator must preserve optional second Reactors.'
$integrated = Read-Text 'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs'
$studyLiteral = 'tl2-itc14-cross-tl-power-aware-information-control-screening'
Assert-True (([regex]::Matches($integrated,[regex]::Escape($studyLiteral))).Count -eq 1) 'CP88 study ID must have exactly one centralized literal binding.'
Assert-True (([regex]::Matches($integrated,'CrossTlPowerAwareInformationControlScreeningStudyId')).Count -ge 10) 'Integrated combat runner has incomplete CP88 study-ID integration.'
foreach ($needle in @('RequiredCrossTlPowerAwareInformationControlScreeningVariantCount = 288','ValidateCrossTlPowerAwareInformationControlScreeningCoverage','EffectiveRatedEwPowerCost','normalRating: ecmNormalRating','normalRating: eccmNormalRating','cross-tl-absolute-combat-viability','cross-tl-dynamic-combat-activity','cross-tl-power-aware-ew-doctrine','cross-tl-information-control-power-review.csv')) { Require-Contains $integrated $needle "Integrated combat runner is missing CP88 hook '$needle'." }
$tests = Read-Text 'src/StarCluster.ScenarioRunner/ScenarioRunnerSelfTests.cs'
Require-Contains $tests 'TestCp88MinimumCombatCoreGuardrail' 'ScenarioRunner self-tests must cover the mandatory combat core.'
Require-Contains $tests 'TestCp88RatedEwAffordability' 'ScenarioRunner self-tests must cover rating-scaled EW affordability.'

Write-Host '       Validating documentation authority and durable-development boundaries...'
$chat = Read-Text 'CHAT_README.md'
Require-Contains $chat 'Every legal combat ship needs a Main Weapon and a Reactor' 'CHAT_README must preserve the mandatory combat-core bootstrap rule.'
$sim = Read-Text 'docs/development/Simulation_Development_Guidelines.md'
Require-Contains $sim 'minimum combat core' 'Simulation guidelines must require enumeration to enforce the Concept combat core.'
Require-Contains $sim 'fixed/reference lane must itself be viable' 'Simulation guidelines must carry the absolute fixed-reference viability rule.'
Assert-NoText $sim '8842ce0e' 'Simulation guidelines must not become a checkpoint hash/result log.'
$ai = Read-Text 'docs/design/ai/AI_Doctrine_Registry_Architecture_v0_5.md'
Require-Contains $ai 'actual effective cost' 'AI doctrine v0.5 must use actual effective rated-system affordability.'
Require-Contains $ai 'not a checkpoint diary' 'AI doctrine authority must remain a reusable-lesson document.'
Assert-NoText $ai '1,920,000' 'AI doctrine authority must not accumulate checkpoint trial counts.'
$suite = Read-Json 'docs/design/testing/technology_integration_permutation_suite_v0_8.json'
Assert-True ([string]$suite.id -eq 'technology-integration-permutation-suite-v0_8' -and [int]$suite.checkpoint -eq 88) 'Standing suite v0.8 identity mismatch.'
Assert-True ([int]$suite.legalBuildEnumeration.currentLegalBuildCount -eq 512 -and [int]$suite.currentCoverage.currentStudy.variantCount -eq 288) 'Standing suite v0.8 coverage mismatch.'
Assert-True ([int]$suite.legalBuildEnumeration.constructionGuardrails.minimumMainWeaponCount -eq 1 -and [int]$suite.legalBuildEnumeration.constructionGuardrails.minimumReactorCount -eq 1 -and [bool]$suite.legalBuildEnumeration.constructionGuardrails.additionalMainWeaponsOptional -and [bool]$suite.legalBuildEnumeration.constructionGuardrails.additionalReactorsOptional) 'Standing suite v0.8 construction guardrail mismatch.'
Require-Contains (Read-Text 'docs/design/testing/Technology_Integration_Permutation_Suite_Architecture_v0_8.md') 'Intended-active fixed references' 'Standing suite architecture must carry absolute combat viability.'
$matrix = Read-Json 'docs/archive/player_technology/pre-cp165-active/technology_architecture_matrix_v1.json'
Assert-True ([string]$matrix.integrationArchitecture.standingPermutationSuite -eq 'docs/design/testing/technology_integration_permutation_suite_v0_8.json' -and [int]$matrix.integrationArchitecture.currentBoundedCombatScreenVariants -eq 288) 'Technology Matrix integration pointer/count drifted.'
Assert-True ([int]$matrix.integrationArchitecture.constructionGuardrails.minimumMainWeaponCount -eq 1 -and [int]$matrix.integrationArchitecture.constructionGuardrails.minimumReactorCount -eq 1) 'Technology Matrix must carry the authoritative minimum combat core.'
$conceptRel = 'docs/Star_Cluster_Game_Concept_v0.6y.docx'
$conceptXml = Read-ZipEntryText $conceptRel 'word/document.xml'
Require-Contains $conceptXml 'Version 0.6y' 'Concept title/version must identify v0.6y.'
Assert-NoText $conceptXml '0.6x' 'Active Concept v0.6y must not retain the superseded v0.6x version marker.'
Require-Contains $conceptXml 'Every legal player or AI combat ship must include at least one Main Weapon and at least one Main Reactor' 'Concept v0.6y is missing the player/AI minimum combat-core rule.'
$headerXml = Read-ZipEntryText $conceptRel 'word/header1.xml'
Require-Contains $headerXml 'v0.6y' 'Concept v0.6y running header was not updated.'
$workbookXml = Read-ZipEntryText 'docs/design/player_technology/StarCluster_Technology_Architecture_Matrix_v1.xlsx' 'xl/workbook.xml'
foreach ($sheetName in @('Overview','Architecture Matrix','TL2 Candidate','Integration Guardrails','Weapon Penetration')) { Assert-True ($workbookXml.Contains(('name="' + $sheetName + '"'))) "Technology Matrix workbook is missing '$sheetName'." }

Write-Host '       Validating accepted CP87a provenance and frozen unrelated production code...'
$cp87ManifestRel = 'docs/validation/evidence/checkpoint-87a/CHECKPOINT_87a_SHA256SUMS.txt'
$cp87Record = Read-Manifest $cp87ManifestRel
$acceptedCp87ManifestSha = 'd58c2bc843f4bf6094a65fe9a886ceba0d295104be01ce6ae572e0b756ef3302'
Assert-True ([int]$cp87Record.PhysicalLineCount -eq 1698 -and [int]$cp87Record.EntryCount -eq 1698) 'Accepted CP87a evidence manifest must contain exactly 1,698 unique entries.'
Assert-True ((Hash-Rel $cp87ManifestRel) -eq $acceptedCp87ManifestSha) 'Embedded CP87a evidence-manifest bytes do not match the accepted manifest.'
$prov = Read-Json 'docs/validation/evidence/checkpoint-87a/checkpoint-87a-native-acceptance-provenance.json'
Assert-True ([string]$prov.acceptanceSummary.status -eq 'Success' -and [string]$prov.acceptanceSummary.checkpointDefinitionSha256 -eq '2683d1c09228301dc0830518851ed086ad62fc64d3d528421a6c95fb55de7c88' -and [string]$prov.acceptanceSummary.primarySummarySha256 -eq '8842ce0e704cc0bbc815c717fbebedf395812629cc83f46455029ac0a483472a') 'CP87a native provenance hashes/status drifted.'
Assert-True ([bool]$prov.screeningWarnings.informationControlCliffObserved -and [bool]$prov.screeningWarnings.energyMirrorPowerDeadlockObserved -and -not [bool]$prov.screeningWarnings.candidatePromotionFromScreen) 'CP87a provenance must preserve the diagnostic integration warnings without promotion.'
$cp87 = $cp87Record.Entries
$allowedRunner = @(
    'src/StarCluster.ScenarioRunner/CrossTlIntegration/CrossTlBuildPermutationRunner.cs',
    'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs',
    'src/StarCluster.ScenarioRunner/ScenarioRunnerSelfTests.cs'
)
foreach ($rel in @($cp87.Keys)) {
    $freeze = $rel.StartsWith('src/StarCluster.Core/',[System.StringComparison]::Ordinal) -or
        $rel.StartsWith('src/StarCluster.Game/',[System.StringComparison]::Ordinal) -or
        $rel.StartsWith('tests/',[System.StringComparison]::Ordinal) -or
        ($rel.StartsWith('src/StarCluster.ScenarioRunner/',[System.StringComparison]::Ordinal) -and -not ($allowedRunner -contains $rel))
    if ($freeze) {
        Assert-True ((Hash-Rel $rel) -eq [string]$cp87[$rel]) "CP88 changed frozen CP87a code '$rel'."
    }
}
$oldConceptHash = [string]$cp87['docs/Star_Cluster_Game_Concept_v0.6x.docx']
Assert-True (-not [string]::IsNullOrWhiteSpace($oldConceptHash)) 'CP87a manifest lacks active Concept v0.6x.'
Assert-True ((Hash-Rel 'docs/archive/Star_Cluster_Game_Concept_v0.6x.docx') -eq $oldConceptHash) 'Archived Concept v0.6x must remain byte-identical to the accepted CP87a concept.'

Write-Host 'Checkpoint 88 repository contracts passed.'
