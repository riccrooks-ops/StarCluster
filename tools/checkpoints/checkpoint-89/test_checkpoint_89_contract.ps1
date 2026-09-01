[CmdletBinding()]
param()

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path

function Assert-True { param([bool]$Condition,[string]$Message) if (-not $Condition) { throw $Message } }
function RelPath { param([string]$RelativePath) return (Join-Path $repositoryRoot ($RelativePath.Replace('/','\'))) }
function Read-Text { param([string]$RelativePath) $p=RelPath $RelativePath; Assert-True (Test-Path -LiteralPath $p -PathType Leaf) "Required file '$RelativePath' is missing."; return [System.IO.File]::ReadAllText($p) }
function Read-Json { param([string]$RelativePath) return ((Read-Text $RelativePath) | ConvertFrom-Json) }
function Hash-Rel { param([string]$RelativePath) $p=RelPath $RelativePath; Assert-True (Test-Path -LiteralPath $p -PathType Leaf) "Hash target '$RelativePath' is missing."; return (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant() }
function Require-Contains { param([string]$Text,[string]$Needle,[string]$Message) Assert-True ($Text.IndexOf($Needle,[System.StringComparison]::OrdinalIgnoreCase) -ge 0) $Message }
function Assert-NoText { param([string]$Text,[string]$Needle,[string]$Message) Assert-True ($Text.IndexOf($Needle,[System.StringComparison]::OrdinalIgnoreCase) -lt 0) $Message }
function Read-Manifest {
    param([string]$RelativePath)
    $p=RelPath $RelativePath; Assert-True (Test-Path -LiteralPath $p -PathType Leaf) "Manifest '$RelativePath' is missing."
    $lines=@(Get-Content -LiteralPath $p); $map=@{}; $lineNo=0
    foreach($line in $lines){ $lineNo++; Assert-True (-not [string]::IsNullOrWhiteSpace([string]$line)) "Manifest '$RelativePath' contains blank line $lineNo."; $m=[regex]::Match([string]$line,'^([0-9a-fA-F]{64})  (.+)$'); Assert-True $m.Success "Manifest '$RelativePath' has malformed line $lineNo."; $rel=$m.Groups[2].Value.Replace('\','/'); Assert-True (-not $map.ContainsKey($rel)) "Manifest '$RelativePath' duplicates '$rel'."; $map[$rel]=$m.Groups[1].Value.ToLowerInvariant() }
    return [pscustomobject]@{ PhysicalLineCount=$lines.Count; EntryCount=$map.Count; Entries=$map }
}
function Read-ZipEntryText {
    param([string]$RelativePath,[string]$EntryName)
    $p=RelPath $RelativePath; Assert-True (Test-Path -LiteralPath $p -PathType Leaf) "Archive '$RelativePath' is missing."
    Add-Type -AssemblyName System.IO.Compression.FileSystem -ErrorAction Stop | Out-Null
    $z=[System.IO.Compression.ZipFile]::OpenRead($p)
    try { $e=$z.GetEntry($EntryName); Assert-True ($null -ne $e) "Archive '$RelativePath' is missing '$EntryName'."; $stream=$e.Open(); $reader=New-Object System.IO.StreamReader($stream); try { return [string]$reader.ReadToEnd() } finally { $reader.Dispose(); $stream.Dispose() } } finally { $z.Dispose() }
}
function Read-ZipPrefixText {
    param([string]$RelativePath,[string]$Prefix)
    $p=RelPath $RelativePath; Add-Type -AssemblyName System.IO.Compression.FileSystem -ErrorAction Stop | Out-Null
    $z=[System.IO.Compression.ZipFile]::OpenRead($p)
    try { $sb=New-Object System.Text.StringBuilder; foreach($e in @($z.Entries | Where-Object { $_.FullName.StartsWith($Prefix,[System.StringComparison]::OrdinalIgnoreCase) -and $_.FullName.EndsWith('.xml',[System.StringComparison]::OrdinalIgnoreCase) })) { $stream=$e.Open(); $reader=New-Object System.IO.StreamReader($stream); try { [void]$sb.AppendLine($reader.ReadToEnd()) } finally { $reader.Dispose(); $stream.Dispose() } }; return $sb.ToString() } finally { $z.Dispose() }
}
function Assert-ExactFileSet {
    param([string]$RelativeDirectory,[string[]]$Expected)
    $p=RelPath $RelativeDirectory; Assert-True (Test-Path -LiteralPath $p -PathType Container) "Directory '$RelativeDirectory' is missing."
    $actual=@(Get-ChildItem -LiteralPath $p -File | ForEach-Object { $_.Name } | Sort-Object)
    $want=@($Expected | Sort-Object)
    Assert-True ($actual.Count -eq $want.Count) "Directory '$RelativeDirectory' has $($actual.Count) active files; expected $($want.Count)."
    for($i=0;$i -lt $want.Count;$i++){ Assert-True ([string]$actual[$i] -eq [string]$want[$i]) "Directory '$RelativeDirectory' active file set drifted: expected '$($want[$i])', found '$($actual[$i])'." }
}

Write-Host '       Validating native-dependency declarations...'
$guard=RelPath 'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1'
$normalRel='tools/calibration/checkpoints/checkpoint-89.json'; $deepRel='tools/calibration/checkpoints/checkpoint-89-deep-calibration.json'
$guardedPs=@('tools/checkpoints/Test-NativeAcceptanceDependencies.ps1','tools/checkpoints/checkpoint-89/apply_checkpoint_89.ps1','tools/checkpoints/checkpoint-89/test_checkpoint_89_contract.ps1','tools/calibration/run_calibration_checkpoint.ps1')
& $guard -RepositoryRoot $repositoryRoot -PowerShellPaths $guardedPs -CheckpointDefinitionPaths @($normalRel,$deepRel)

Write-Host '       Validating Checkpoint 89 definitions and deterministic workload...'
$normal=Read-Json $normalRel; $deep=Read-Json $deepRel
Assert-True ([string]$normal.checkpointId -eq '89' -and [string]$deep.checkpointId -eq '89') 'Checkpoint 89 definition ID mismatch.'
Assert-True ([string]$normal.manifestFile -eq 'CHECKPOINT_89_SHA256SUMS.txt' -and [string]$deep.manifestFile -eq 'CHECKPOINT_89_SHA256SUMS.txt') 'Checkpoint 89 manifest binding mismatch.'
Assert-True (@($normal.stages).Count -eq 8 -and @($deep.stages).Count -eq 8) 'Checkpoint 89 must contain exactly eight deterministic/self-test stages in both definitions.'
Assert-True ([int]$normal.checkpointMetrics.monteCarloVariantCount -eq 0 -and [int]$normal.checkpointMetrics.trialsAtDefault -eq 0 -and [int]$deep.checkpointMetrics.monteCarloVariantCount -eq 0) 'Checkpoint 89 must not run Monte Carlo.'
$normalIds=@($normal.stages | ForEach-Object { [string]$_.id })
foreach($id in @('deterministic','tl1-phase-a','tl1-phase-b','tl1-installation-space-envelope','tl1-sensor-ew-foundation','auxiliary-resource-endurance','checkpoint-53-resource-semantics-lock','runner-self-tests')){ Assert-True ($normalIds -contains $id) "Checkpoint 89 is missing stage '$id'." }
$self=@($normal.stages | Where-Object { [string]$_.id -eq 'runner-self-tests' }); Assert-True ($self.Count -eq 1 -and [int]$self[0].metrics.selfTestCount -eq 54) 'Checkpoint 89 must expect 54 ScenarioRunner self-tests.'

Write-Host '       Validating active documentation layout and navigation...'
Assert-True (-not (Test-Path -LiteralPath (RelPath 'docs/checkpoints'))) 'The parallel docs/checkpoints history tree must not exist after CP89 consolidation.'
Assert-True (-not (Test-Path -LiteralPath (RelPath 'docs/design/player_technology/archive'))) 'Historical technology material must not remain nested under the active player_technology directory.'
$concepts=@(Get-ChildItem -LiteralPath (RelPath 'docs') -File -Filter 'Star_Cluster_Game_Concept_v*.docx')
Assert-True ($concepts.Count -eq 1 -and $concepts[0].Name -eq 'Star_Cluster_Game_Concept_v0.6z.docx') 'Exactly one active Concept v0.6z must exist in docs root.'
Assert-True (Test-Path -LiteralPath (RelPath 'docs/archive/concepts/Star_Cluster_Game_Concept_v0.6y.docx') -PathType Leaf) 'Superseded Concept v0.6y must be archived.'
Assert-ExactFileSet 'docs/design/player_technology' @('README.md','StarCluster_Technology_Architecture_Matrix_v1.xlsx','Technology_Architecture_Matrix_v1.md','auxiliary_component_catalog_schema_v0_1.json','auxiliary_component_catalog_v0_1.json','checkpoint_54_tl3_runtime_profile_candidates_v0_1.json','checkpoint_55_tl3_lowtech_profile_candidates_v0_1.json','component_installation_space_catalog_v1.json','pds_tl1_tl2_characteristics_v0_3.json','tactical_computer_fire_control_profiles_v0_1.json','technology_architecture_matrix_v1.json','tl1_35_space_player_cruiser_baseline_v0_9.json','tl1_core_combat_numerical_baseline_v0_1.csv','tl1_core_combat_numerical_baseline_v0_2.csv','tl1_core_combat_numerical_baseline_v0_3.csv','tl2_armor_ap_ai_candidate_profile_v0_2.json','tl2_computing_sensor_ew_working_profile_v0_2.json','tl2_power_reactor_candidate_profile_v0_2.json','tl2_shield_capacity_candidate_profile_v0_2.json','tl2_weapon_penetration_working_profile_v0_2.json')
Assert-ExactFileSet 'docs/design/testing' @('Checkpoint_89_Validation_Tiers.md','README.md','Technology_Integration_Permutation_Suite_Architecture_v0_8.md','checkpoint_89_validation_suite_policy_v0_1.json','technology_integration_permutation_suite_v0_8.json')
$aiArchitectures=@(Get-ChildItem -LiteralPath (RelPath 'docs/design/ai') -File -Filter 'AI_Doctrine_Registry_Architecture_*.md')
Assert-True ($aiArchitectures.Count -eq 1 -and $aiArchitectures[0].Name -eq 'AI_Doctrine_Registry_Architecture_v0_5.md') 'Exactly one current AI Doctrine Architecture must remain active.'
$activeValidation=@(Get-ChildItem -LiteralPath (RelPath 'docs/validation') -File -Filter 'Checkpoint_*.md')
Assert-True ($activeValidation.Count -eq 1 -and $activeValidation[0].Name -eq 'Checkpoint_89_Documentation_Repository_Consolidation_And_EW_Multiplicity.md') 'Exactly one active checkpoint validation document must remain.'
foreach($rel in @('docs/archive/README.md','docs/archive/player_technology/architecture-history/Player_TL1_TL9_Technology_Architecture_v0_10.md','docs/archive/player_technology/workbooks/StarCluster_Player_TL_Framework_Draft_v0_39.xlsx','docs/archive/player_technology/studies/TL2_Weapon_Penetration_And_Layered_Defense_Integration_Study_v0_1.md','docs/archive/testing/Checkpoint_88_Validation_Tiers.md','docs/archive/ai/AI_Doctrine_Registry_Architecture_v0_4.md')){ Assert-True (Test-Path -LiteralPath (RelPath $rel) -PathType Leaf) "Expected archived artifact '$rel' is missing." }
$docsReadme=Read-Text 'docs/README.md'; Require-Contains $docsReadme 'Component Catalog' 'docs/README must point directly to the Component Catalog.'; Require-Contains $docsReadme 'archive/' 'docs/README must explain the archive boundary.'
$chat=Read-Text 'CHAT_README.md'; Require-Contains $chat 'Active documentation directories must stay small and navigable' 'CHAT_README must carry the documentation-hygiene guardrail.'; Require-Contains $chat 'component_installation_space_catalog_v1.json' 'CHAT_README must point to the component catalog.'

Write-Host '       Validating Concept, component catalog, Matrix, and EW multiplicity authority...'
$conceptRel='docs/Star_Cluster_Game_Concept_v0.6z.docx'; $conceptXml=Read-ZipEntryText $conceptRel 'word/document.xml'; $headerXml=Read-ZipEntryText $conceptRel 'word/header1.xml'
Require-Contains $conceptXml 'Version 0.6z' 'Concept must identify version 0.6z.'; Require-Contains $headerXml 'v0.6z' 'Concept running header must identify v0.6z.'
foreach($needle in @('Multiple ECM suites and multiple ECCM suites may be installed','same-type local ratings are never additive','ECM2 + ECM2 remains ECM2','C-061','Non-additive EW redundancy')){ Require-Contains $conceptXml $needle "Concept v0.6z is missing EW multiplicity authority '$needle'." }
$catalog=Read-Json 'docs/archive/player_technology/pre-cp165-active/component_installation_space_catalog_v1.json'
Assert-True ([string]$catalog.id -eq 'component-installation-space-catalog-v1' -and [int]$catalog.checkpoint -eq 89) 'Component catalog identity mismatch.'
Assert-True ([int]$catalog.globalRules.minimumMainWeaponCount -eq 1 -and [int]$catalog.globalRules.minimumReactorCount -eq 1 -and -not [bool]$catalog.globalRules.simultaneousTacticalPowerSufficiencyRequiredForConstruction) 'Component catalog construction core/power rule mismatch.'
$ecm=@($catalog.components | Where-Object { $null -ne $_.PSObject.Properties['id'] -and [string]$_.id -eq 'ecm_suite' }); $eccm=@($catalog.components | Where-Object { $null -ne $_.PSObject.Properties['id'] -and [string]$_.id -eq 'eccm_suite' })
Assert-True ($ecm.Count -eq 1 -and $eccm.Count -eq 1 -and [int]$ecm[0].installationSpace -eq 1 -and [int]$eccm[0].installationSpace -eq 1 -and [bool]$ecm[0].multiplicityAllowed -and [bool]$eccm[0].multiplicityAllowed) 'ECM/ECCM component catalog footprint/multiplicity mismatch.'
Require-Contains ([string]$ecm[0].stackingBehavior) 'ECM2 + ECM2 = ECM2' 'ECM redundancy must be explicitly non-additive.'; Require-Contains ([string]$eccm[0].stackingBehavior) 'ECCM2 + ECCM2 = ECCM2' 'ECCM redundancy must be explicitly non-additive.'
$matrix=Read-Json 'docs/archive/player_technology/pre-cp165-active/technology_architecture_matrix_v1.json'
Assert-True ([int]$matrix.checkpoint -eq 89 -and [string]$matrix.authority.concept -eq 'docs/Star_Cluster_Game_Concept_v0.6z.docx' -and [string]$matrix.authority.componentInstallationSpaceCatalog -eq 'docs/archive/player_technology/pre-cp165-active/component_installation_space_catalog_v1.json') 'Technology Matrix authority/catalog pointer mismatch.'
foreach($tl in @(1,2)){ $tier=@($matrix.tiers | Where-Object { [int]$_.technologyLevel -eq $tl }); Assert-True ($tier.Count -eq 1) "Matrix TL$tl missing."; foreach($k in @('ecm','eccm')){ $o=$tier[0].$k; Assert-True ([int]$o.installationSpace -eq 1 -and [bool]$o.multiplicityAllowedForRedundancy -and -not [bool]$o.sameTypeRatingsAdditive -and [string]$o.sameTypeResolution -eq 'highest_applicable_functional_rating') "Matrix TL$tl $k multiplicity rule mismatch." } }
$suite=Read-Json 'docs/design/testing/technology_integration_permutation_suite_v0_8.json'; $cg=$suite.legalBuildEnumeration.constructionGuardrails
Assert-True ([int]$suite.checkpoint -eq 89 -and [bool]$cg.redundantEwInstallationsAllowed -and -not [bool]$cg.ecmSameTypeRatingsAdditive -and -not [bool]$cg.eccmSameTypeRatingsAdditive -and [string]$cg.ewDuplicateResolution -eq 'highest_applicable_functional_rating') 'Standing suite must carry non-additive EW redundancy into future generalized enumeration.'
$wbXml=Read-ZipEntryText 'docs/design/player_technology/StarCluster_Technology_Architecture_Matrix_v1.xlsx' 'xl/workbook.xml'; Require-Contains $wbXml 'name="Component Catalog"' 'Technology workbook must contain Component Catalog sheet.'
$sheetXml=Read-ZipPrefixText 'docs/design/player_technology/StarCluster_Technology_Architecture_Matrix_v1.xlsx' 'xl/worksheets/'
foreach($needle in @('Current Component Installation Space Catalog','ECM2 + ECM2 = ECM2','ECCM2 + ECCM2 = ECCM2','Non-additive EW redundancy','Concept v0.6z')){ Require-Contains $sheetXml $needle "Technology workbook is missing '$needle'." }

Write-Host '       Validating accepted CP88 provenance and frozen implementation/reference files...'
$cp88ManifestRel='docs/validation/evidence/checkpoint-88/CHECKPOINT_88_SHA256SUMS.txt'; $cp88Record=Read-Manifest $cp88ManifestRel
Assert-True ([int]$cp88Record.PhysicalLineCount -eq 1713 -and [int]$cp88Record.EntryCount -eq 1713) 'Accepted CP88 evidence manifest must contain exactly 1,713 unique entries.'
Assert-True ((Hash-Rel $cp88ManifestRel) -eq 'c1f389f86633903cf38c608ed791827c2e91eb7f8e50923a7ff5589b8f2f75fa') 'Embedded CP88 evidence manifest bytes do not match accepted CP88.'
$prov=Read-Json 'docs/validation/evidence/checkpoint-88/checkpoint-88-native-acceptance-provenance.json'
Assert-True ([string]$prov.acceptanceSummary.status -eq 'Success' -and [string]$prov.acceptanceSummary.checkpointDefinitionSha256 -eq 'f4085cca9af0dafa6866d01cdcfa7244fd50c89753c266a4685e537a374cb2b1' -and [string]$prov.acceptanceSummary.primarySummarySha256 -eq 'df4714078ed6a9884e40a34652864b44788ea606b69606ff82fbc8d1c6e1b5c9') 'CP88 native provenance hash/status mismatch.'
$cp88=$cp88Record.Entries
foreach($rel in @($cp88.Keys)){
    $freeze=$rel.StartsWith('src/',[System.StringComparison]::Ordinal) -or $rel.StartsWith('tests/',[System.StringComparison]::Ordinal)
    if($freeze){ Assert-True ((Hash-Rel $rel) -eq [string]$cp88[$rel]) "CP89 changed frozen implementation/test file '$rel'." }
    if($rel.StartsWith('docs/references/',[System.StringComparison]::Ordinal) -and -not $rel.EndsWith('/README.md',[System.StringComparison]::OrdinalIgnoreCase)){ Assert-True ((Hash-Rel $rel) -eq [string]$cp88[$rel]) "CP89 changed preserved user reference '$rel'." }
}
$oldConceptHash=[string]$cp88['docs/Star_Cluster_Game_Concept_v0.6y.docx']; Assert-True (-not [string]::IsNullOrWhiteSpace($oldConceptHash)) 'CP88 manifest lacks Concept v0.6y.'; Assert-True ((Hash-Rel 'docs/archive/concepts/Star_Cluster_Game_Concept_v0.6y.docx') -eq $oldConceptHash) 'Archived Concept v0.6y must remain byte-identical to accepted CP88.'

Write-Host 'Checkpoint 89 repository contracts passed.'
