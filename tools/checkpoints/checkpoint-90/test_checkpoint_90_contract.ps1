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
function Require-Property { param($Object,[string]$Name,[string]$Context) Assert-True ($null -ne $Object.PSObject.Properties[$Name]) "$Context is missing property '$Name'." }
function Read-Manifest {
    param([string]$RelativePath)
    $p=RelPath $RelativePath; Assert-True (Test-Path -LiteralPath $p -PathType Leaf) "Manifest '$RelativePath' is missing."
    $lines=@(Get-Content -LiteralPath $p); $map=@{}; $lineNo=0
    foreach($line in $lines){
        $lineNo++
        Assert-True (-not [string]::IsNullOrWhiteSpace([string]$line)) "Manifest '$RelativePath' contains blank line $lineNo."
        $m=[regex]::Match([string]$line,'^([0-9a-fA-F]{64})  (.+)$')
        Assert-True $m.Success "Manifest '$RelativePath' has malformed line $lineNo."
        $rel=$m.Groups[2].Value.Replace('\','/')
        Assert-True (-not $map.ContainsKey($rel)) "Manifest '$RelativePath' duplicates '$rel'."
        $map[$rel]=$m.Groups[1].Value.ToLowerInvariant()
    }
    return [pscustomobject]@{ PhysicalLineCount=$lines.Count; EntryCount=$map.Count; Entries=$map }
}
function Assert-ExactFileSet {
    param([string]$RelativeDirectory,[string[]]$Expected)
    $p=RelPath $RelativeDirectory; Assert-True (Test-Path -LiteralPath $p -PathType Container) "Directory '$RelativeDirectory' is missing."
    $actual=@(Get-ChildItem -LiteralPath $p -File | ForEach-Object { $_.Name } | Sort-Object)
    $want=@($Expected | Sort-Object)
    Assert-True ($actual.Count -eq $want.Count) "Directory '$RelativeDirectory' has $($actual.Count) active files; expected $($want.Count)."
    for($i=0;$i -lt $want.Count;$i++){ Assert-True ([string]$actual[$i] -eq [string]$want[$i]) "Directory '$RelativeDirectory' active file set drifted: expected '$($want[$i])', found '$($actual[$i])'." }
}
function Get-Axis {
    param($Study,[string]$Id)
    $matches=@($Study.axes | Where-Object { [string]$_.id -eq $Id })
    Assert-True ($matches.Count -eq 1) "Cross-TL foundation must contain exactly one '$Id' axis."
    return $matches[0]
}
function Count-Occurrences {
    param([string]$Text,[string]$Needle)
    if ([string]::IsNullOrEmpty($Needle)) { return 0 }
    $count=0; $start=0
    while(($idx=$Text.IndexOf($Needle,$start,[System.StringComparison]::Ordinal)) -ge 0){ $count++; $start=$idx+$Needle.Length }
    return $count
}

Write-Host '       Validating native-dependency declarations...'
$guard=RelPath 'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1'
$normalRel='tools/calibration/checkpoints/checkpoint-90.json'; $deepRel='tools/calibration/checkpoints/checkpoint-90-deep-calibration.json'
$guardedPs=@('tools/checkpoints/Test-NativeAcceptanceDependencies.ps1','tools/checkpoints/checkpoint-90/apply_checkpoint_90.ps1','tools/checkpoints/checkpoint-90/test_checkpoint_90_contract.ps1','tools/calibration/run_calibration_checkpoint.ps1')
& $guard -RepositoryRoot $repositoryRoot -PowerShellPaths $guardedPs -CheckpointDefinitionPaths @($normalRel,$deepRel)

Write-Host '       Validating Checkpoint 90 definitions and workload accounting...'
$normal=Read-Json $normalRel; $deep=Read-Json $deepRel
Assert-True ([string]$normal.checkpointId -eq '90' -and [string]$deep.checkpointId -eq '90') 'Checkpoint 90 definition ID mismatch.'
Assert-True ([string]$normal.manifestFile -eq 'CHECKPOINT_90_SHA256SUMS.txt' -and [string]$deep.manifestFile -eq 'CHECKPOINT_90_SHA256SUMS.txt') 'Checkpoint 90 manifest binding mismatch.'
Assert-True (@($normal.stages).Count -eq 13 -and [int]$normal.checkpointMetrics.stageCount -eq 13) 'Checkpoint 90 normal definition must contain 13 stages.'
Assert-True (@($deep.stages).Count -eq 14 -and [int]$deep.checkpointMetrics.stageCount -eq 14) 'Checkpoint 90 Deep Calibration definition must contain 14 stages.'
Assert-True ([int]$normal.checkpointMetrics.monteCarloVariantCount -eq 432 -and [long]$normal.checkpointMetrics.trialsAtDefault -eq 4320000 -and [long]$normal.checkpointMetrics.totalTrialExecutionsAtDefault -eq 4320432) 'Checkpoint 90 normal workload accounting mismatch.'
Assert-True ([int]$deep.checkpointMetrics.monteCarloVariantCount -eq 720 -and [long]$deep.checkpointMetrics.trialsAtDefault -eq 7200000 -and [long]$deep.checkpointMetrics.totalTrialExecutionsAtDefault -eq 7200432) 'Checkpoint 90 Deep Calibration workload accounting mismatch.'
Assert-True ([string]$normal.primaryStudy.id -eq 'tl2-itc15-cross-tl-generalized-legal-build-screening' -and [int]$normal.primaryStudy.variantCount -eq 432) 'Checkpoint 90 primary-study metadata mismatch.'
$normalIds=@($normal.stages | ForEach-Object { [string]$_.id })
foreach($id in @('deterministic','tl1-phase-a','tl1-phase-b','tl1-installation-space-envelope','tl1-sensor-ew-foundation','cross-tl-build-permutation-preflight','cross-tl-build-permutation-generation','cross-tl-generated-study-preflight','cross-tl-generated-study-smoke','cross-tl-build-permutation-screening','auxiliary-resource-endurance','checkpoint-53-resource-semantics-lock','runner-self-tests')){ Assert-True ($normalIds -contains $id) "Checkpoint 90 is missing stage '$id'." }
$self=@($normal.stages | Where-Object { [string]$_.id -eq 'runner-self-tests' }); Assert-True ($self.Count -eq 1 -and [int]$self[0].metrics.selfTestCount -eq 56) 'Checkpoint 90 must expect 56 ScenarioRunner self-tests.'
$preMatches=@($normal.stages | Where-Object { [string]$_.id -eq 'cross-tl-build-permutation-preflight' }); Assert-True ($preMatches.Count -eq 1) 'Checkpoint 90 must contain exactly one generalized preflight stage.'; $pre=$preMatches[0]
$genMatches=@($normal.stages | Where-Object { [string]$_.id -eq 'cross-tl-build-permutation-generation' }); Assert-True ($genMatches.Count -eq 1) 'Checkpoint 90 must contain exactly one generalized generation stage.'; $gen=$genMatches[0]
$smokeMatches=@($normal.stages | Where-Object { [string]$_.id -eq 'cross-tl-generated-study-smoke' }); Assert-True ($smokeMatches.Count -eq 1) 'Checkpoint 90 must contain exactly one generated smoke stage.'; $smoke=$smokeMatches[0]
$screenMatches=@($normal.stages | Where-Object { [string]$_.id -eq 'cross-tl-build-permutation-screening' }); Assert-True ($screenMatches.Count -eq 1) 'Checkpoint 90 must contain exactly one generated screening stage.'; $screen=$screenMatches[0]
Assert-True ([string]$pre.arguments[1] -eq 'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/cross-tl-build-permutation-foundation-v0_3.json' -and [int]$pre.metrics.legalBuildCount -eq 22592 -and [int]$pre.metrics.generatedVariantCount -eq 432) 'Checkpoint 90 preflight stage binding/metrics mismatch.'
Assert-True ([long]$gen.metrics.orientedPairingEnvelope -eq 510398464 -and [int]$gen.metrics.logicalPairingCount -eq 144 -and [bool]$gen.metrics.redundantEwNonAdditive) 'Checkpoint 90 generator stage metrics mismatch.'
Assert-True ([int]$smoke.metrics.variantCount -eq 432 -and [int]$smoke.metrics.totalSmokeTrials -eq 432 -and [int]$screen.metrics.variantCount -eq 432 -and [string]$screen.metrics.standingPermutationSuite -eq 'v0.9') 'Checkpoint 90 smoke/screening metrics mismatch.'

Write-Host '       Validating the generalized 22,592-build legal envelope...'
$studyRel='src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/cross-tl-build-permutation-foundation-v0_3.json'
$study=Read-Json $studyRel
Assert-True ([string]$study.schemaVersion -eq 'star-cluster-cross-tl-build-permutation-v3' -and [string]$study.checkpoint -eq '90') 'Cross-TL foundation v0.3 identity/schema mismatch.'
foreach($prop in @('constructionGuardrails','stratifiedPairingSelection','axes','namedRecipes','pairingGroups','geometries')){ Require-Property $study $prop 'Cross-TL foundation v0.3' }
$g=$study.constructionGuardrails
Assert-True ([int]$g.minimumMainWeaponCount -eq 1 -and [int]$g.minimumReactorCount -eq 1 -and [bool]$g.additionalMainWeaponsOptional -and [bool]$g.additionalReactorsOptional -and [bool]$g.duplicationMustBeExplicit) 'Generalized construction guardrail must require 1 Main Weapon + 1 Reactor while preserving optional explicit duplication.'
Assert-True ([bool]$g.redundantEwInstallationsAllowed -and -not [bool]$g.ecmSameTypeRatingsAdditive -and -not [bool]$g.eccmSameTypeRatingsAdditive -and [string]$g.ewDuplicateResolution -eq 'highest_applicable_functional_rating' -and -not [bool]$g.powerSufficiencyIsConstructionLegalityFilter) 'Generalized EW/power construction guardrails mismatch.'
Assert-True ([int]$study.totalInstallationSpace -eq 35 -and [int]$study.fixedShellSpace -eq 10 -and [int]$study.fixedShell.stlDriveSpace -eq 5 -and [int]$study.fixedShell.ftlDriveSpace -eq 5) 'Checkpoint 90 fixed shell/Installation Space mismatch.'
$axisIds=@($study.axes | ForEach-Object { [string]$_.id }); foreach($id in @('weapon','reactor','computer','sensor','shield','armor','ecm','eccm','pds')){ Assert-True ($axisIds -contains $id) "Checkpoint 90 is missing '$id' axis." }; Assert-True ($axisIds.Count -eq 9) 'Checkpoint 90 must have exactly nine generalized axes.'
$weapon=Get-Axis $study 'weapon'; $reactor=Get-Axis $study 'reactor'; $computer=Get-Axis $study 'computer'; $sensor=Get-Axis $study 'sensor'; $shield=Get-Axis $study 'shield'; $armor=Get-Axis $study 'armor'; $ecm=Get-Axis $study 'ecm'; $eccm=Get-Axis $study 'eccm'; $pds=Get-Axis $study 'pds'
Assert-True (@($weapon.options).Count -eq 8 -and @($reactor.options).Count -eq 4 -and @($computer.options).Count -eq 2 -and @($sensor.options).Count -eq 3 -and @($shield.options).Count -eq 3 -and @($armor.options).Count -eq 2 -and @($ecm.options).Count -eq 6 -and @($eccm.options).Count -eq 6 -and @($pds.options).Count -eq 2) 'Checkpoint 90 generalized axis option counts mismatch.'
[long]$raw = 8*4*2*3*3*2*6*6*2
Assert-True ($raw -eq 82944 -and [long]$study.expectedRawCombinationCount -eq $raw) 'Checkpoint 90 raw Cartesian accounting mismatch.'

# Independently enumerate all raw combinations using only Space/multiplicity data from the foundation.
$legal=0; $exact=0; $oneW=0; $twoW=0; $oneR=0; $twoR=0; $dualDual=0; $dupEcm=0; $dupEccm=0; $mixedEcm=0; $mixedEccm=0; $spaceCounts=@{}
foreach($w in @($weapon.options)){
foreach($r in @($reactor.options)){
foreach($c in @($computer.options)){
foreach($s in @($sensor.options)){
foreach($sh in @($shield.options)){
foreach($a in @($armor.options)){
foreach($e in @($ecm.options)){
foreach($ee in @($eccm.options)){
foreach($pd in @($pds.options)){
    $used=10+[int]$w.space+[int]$r.space+[int]$c.space+[int]$s.space+[int]$sh.space+[int]$a.space+[int]$e.space+[int]$ee.space+[int]$pd.space
    $mw=[int]$w.mainWeaponCount; $rc=[int]$r.reactorCount
    if($used -le 35 -and $mw -ge 1 -and $rc -ge 1){
        $legal++; if($used -eq 35){$exact++}; if($mw -eq 1){$oneW++}elseif($mw -eq 2){$twoW++}; if($rc -eq 1){$oneR++}elseif($rc -eq 2){$twoR++}; if($mw -eq 2 -and $rc -eq 2){$dualDual++}
        $er=@($e.ewRatings); $eer=@($ee.ewRatings); if($er.Count -eq 2){$dupEcm++; if(([int]$er[0] -ne [int]$er[1])){$mixedEcm++}}; if($eer.Count -eq 2){$dupEccm++; if(([int]$eer[0] -ne [int]$eer[1])){$mixedEccm++}}
        $key=[string]$used; if(-not $spaceCounts.ContainsKey($key)){$spaceCounts[$key]=0}; $spaceCounts[$key]++
    }
}}}}}}}}}
Assert-True ($legal -eq 22592 -and $legal -eq [int]$study.expectedLegalBuildCount) "Generalized legal-build count mismatch: observed $legal."
Assert-True ($exact -eq 4672 -and $exact -eq [int]$study.expectedExactFillBuildCount) "Exact-fill build count mismatch: observed $exact."
Assert-True ($oneW -eq 20320 -and $twoW -eq 2272 -and $oneR -eq 20320 -and $twoR -eq 2272 -and $dualDual -eq 0) 'Main Weapon/Reactor multiplicity distribution mismatch.'
Assert-True ($dupEcm -eq 9792 -and $dupEccm -eq 9792 -and $mixedEcm -gt 0 -and $mixedEccm -gt 0) 'Redundant/mixed ECM/ECCM build coverage mismatch.'
$expectedSpace=@{'25'=32;'26'=128;'27'=352;'28'=640;'29'=1120;'30'=1792;'31'=2528;'32'=3200;'33'=3648;'34'=4480;'35'=4672}
foreach($key in $expectedSpace.Keys){ Assert-True ($spaceCounts.ContainsKey($key) -and [int]$spaceCounts[$key] -eq [int]$expectedSpace[$key]) "Legal-build Space distribution mismatch at $key Space." }
Assert-True ([long]$study.expectedOrientedPairingEnvelope -eq ([long]$legal*[long]$legal) -and [long]$study.expectedUnorderedWithSelfPairingEnvelope -eq (([long]$legal*([long]$legal+1))/2)) 'Generalized pairing-envelope arithmetic mismatch.'

foreach($axis in @($ecm,$eccm)){
    foreach($o in @($axis.options)){
        $ratings=@($o.ewRatings); Assert-True ($ratings.Count -le 2) "EW option '$($o.id)' exceeds supported redundancy multiplicity."
        foreach($rating in $ratings){ Assert-True ([int]$rating -in @(1,2)) "EW option '$($o.id)' has unsupported rating '$rating'." }
        if([bool]$o.installed){ Assert-True ($ratings.Count -ge 1) "Installed EW option '$($o.id)' lacks a physical rating." } else { Assert-True ($ratings.Count -eq 0) "Absent EW option '$($o.id)' must have no ratings." }
        Assert-True ([int]$o.space -eq $ratings.Count) "EW option '$($o.id)' must consume one Installation Space per physical suite in the current catalog."
    }
}
Assert-True (@($study.namedRecipes).Count -eq 20 -and [int]$study.expectedNamedRecipeCount -eq 20) 'Checkpoint 90 named-recipe count mismatch.'
$namedPairs=0; foreach($pg in @($study.pairingGroups)){ $namedPairs += @($pg.sideARecipes).Count * @($pg.sideBRecipes).Count }
Assert-True ($namedPairs -eq 48 -and [int]$study.expectedNamedLogicalPairingCount -eq 48) 'Checkpoint 90 named pairing count mismatch.'
$sel=$study.stratifiedPairingSelection
Assert-True ([bool]$sel.enabled -and [int]$sel.targetPerCell -eq 4 -and @($sel.compositionClasses).Count -eq 4 -and @($sel.progressionStrata).Count -eq 6 -and [int]$sel.nearDistanceMaximum -eq 2 -and [int]$sel.equalLowAdvancedMaximum -eq 3 -and [int]$sel.expectedSampleCount -eq 96 -and [int]$study.expectedStratifiedLogicalPairingCount -eq 96) 'Checkpoint 90 progression-distance stratified sampling-cell accounting mismatch.'
foreach($stratum in @('side_a_lower_near','side_a_lower_far','equal_low','equal_high','side_a_higher_near','side_a_higher_far')){ Assert-True (@($sel.progressionStrata) -contains $stratum) "Checkpoint 90 is missing progression stratum '$stratum'." }
Assert-True ([int]$study.expectedLogicalPairingCount -eq 144 -and @($study.geometries).Count -eq 3 -and [int]$study.expectedGeneratedVariantCount -eq 432) 'Checkpoint 90 logical-pairing/geometry/variant accounting mismatch.'

Write-Host '       Validating ScenarioRunner generator, runtime multiplicity, and screening hooks...'
$generator=Read-Text 'src/StarCluster.ScenarioRunner/CrossTlIntegration/CrossTlBuildPermutationRunner.cs'
foreach($needle in @('SchemaVersionV3','CrossTlStratifiedPairingSelectionDocument','SelectStratifiedPairings','ProgressionDirection','ProgressionDistance','ProgressionStratum','CompositionPairClass','EcmSuiteRatings','EccmSuiteRatings','expectedStratifiedLogicalPairingCount','highest_applicable_functional_rating','generated-physical-builds-match-referenced-builds')){ Require-Contains $generator $needle "Cross-TL generator is missing CP90 hook '$needle'." }
$docs=Read-Text 'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatDocuments.cs'
foreach($needle in @('ecmSuiteRatings','eccmSuiteRatings','advancedComponentCount','crossTlCompositionClass')){ Require-Contains $docs $needle "Integrated build document is missing CP90 field '$needle'." }
$integrated=Read-Text 'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs'
$studyLiteral='tl2-itc15-cross-tl-generalized-legal-build-screening'
Assert-True ((Count-Occurrences $integrated $studyLiteral) -eq 1) 'Integrated combat runner must centralize the CP90 study ID literal exactly once.'
Assert-True ((Count-Occurrences $integrated 'CrossTlGeneralizedLegalBuildScreeningStudyId') -ge 10) 'Integrated combat runner has incomplete CP90 named-constant study-ID integration.'
foreach($needle in @('RequiredCrossTlGeneralizedLegalBuildScreeningVariantCount = 432','ValidateCrossTlGeneralizedLegalBuildScreeningCoverage','FunctionalEwInstallation','ResolveFunctionalEwInstallation','ResolveHighestFunctionalEwRatingForSelfTest','ecm-{ecmIndex}','eccm-{eccmIndex}','cross-tl-absolute-combat-viability','cross-tl-dynamic-combat-activity','cross-tl-ew-redundancy-non-additive-contract','cross-tl-generalized-build-review.csv','cross-tl-generalized-strata-review.csv')){ Require-Contains $integrated $needle "Integrated combat runner is missing CP90 hook '$needle'." }
$selfTests=Read-Text 'src/StarCluster.ScenarioRunner/ScenarioRunnerSelfTests.cs'
foreach($needle in @('CP90 generalized cross-TL Cartesian foundation expands multiplicity and progression strata','CP90 redundant ECM/ECCM resolves highest functional rating without additive stacking','TestCp90GeneralizedCrossTlFoundation','ProgressionStratumForSelfTest','TestCp90NonAdditiveEwRedundancy')){ Require-Contains $selfTests $needle "ScenarioRunner self-tests are missing '$needle'." }

Write-Host '       Validating current documentation authority and hygiene...'
Assert-True (-not (Test-Path -LiteralPath (RelPath 'docs/checkpoints'))) 'The obsolete docs/checkpoints tree must remain absent.'
Assert-ExactFileSet 'docs/design/player_technology' @('README.md','StarCluster_Technology_Architecture_Matrix_v1.xlsx','Technology_Architecture_Matrix_v1.md','auxiliary_component_catalog_schema_v0_1.json','auxiliary_component_catalog_v0_1.json','checkpoint_54_tl3_runtime_profile_candidates_v0_1.json','checkpoint_55_tl3_lowtech_profile_candidates_v0_1.json','component_installation_space_catalog_v1.json','pds_tl1_tl2_characteristics_v0_3.json','tactical_computer_fire_control_profiles_v0_1.json','technology_architecture_matrix_v1.json','tl1_35_space_player_cruiser_baseline_v0_9.json','tl1_core_combat_numerical_baseline_v0_1.csv','tl1_core_combat_numerical_baseline_v0_2.csv','tl1_core_combat_numerical_baseline_v0_3.csv','tl2_armor_ap_ai_candidate_profile_v0_2.json','tl2_computing_sensor_ew_working_profile_v0_2.json','tl2_power_reactor_candidate_profile_v0_2.json','tl2_shield_capacity_candidate_profile_v0_2.json','tl2_weapon_penetration_working_profile_v0_2.json')
Assert-ExactFileSet 'docs/design/testing' @('Checkpoint_90_Validation_Tiers.md','README.md','Technology_Integration_Permutation_Suite_Architecture_v0_9.md','checkpoint_90_validation_suite_policy_v0_1.json','technology_integration_permutation_suite_v0_9.json')
$activeConcepts=@(Get-ChildItem -LiteralPath (RelPath 'docs') -File -Filter 'Star_Cluster_Game_Concept_v*.docx'); Assert-True ($activeConcepts.Count -eq 1 -and $activeConcepts[0].Name -eq 'Star_Cluster_Game_Concept_v0.6z.docx') 'Concept authority must remain exactly v0.6z.'
$activeValidation=@(Get-ChildItem -LiteralPath (RelPath 'docs/validation') -File -Filter 'Checkpoint_*.md'); Assert-True ($activeValidation.Count -eq 1 -and $activeValidation[0].Name -eq 'Checkpoint_90_Generalized_Legal_Build_And_Cross_TL_Stratified_Screening.md') 'Exactly one active CP90 validation runbook must remain.'
$activeAi=@(Get-ChildItem -LiteralPath (RelPath 'docs/design/ai') -File -Filter 'AI_Doctrine_Registry_Architecture_v*.md'); Assert-True ($activeAi.Count -eq 1 -and $activeAi[0].Name -eq 'AI_Doctrine_Registry_Architecture_v0_5.md') 'Exactly one active AI Doctrine Architecture v0.5 must remain.'
foreach($rel in @('docs/archive/testing/Technology_Integration_Permutation_Suite_Architecture_v0_8.md','docs/archive/testing/technology_integration_permutation_suite_v0_8.json','docs/archive/testing/Checkpoint_89_Validation_Tiers.md','docs/archive/testing/checkpoint_89_validation_suite_policy_v0_1.json','docs/validation/archive/Checkpoint_89_Documentation_Repository_Consolidation_And_EW_Multiplicity.md')){ Assert-True (Test-Path -LiteralPath (RelPath $rel) -PathType Leaf) "Expected archived CP89 artifact '$rel' is missing." }
$docsReadme=Read-Text 'docs/README.md'; Require-Contains $docsReadme 'Technology_Integration_Permutation_Suite_Architecture_v0_9.md' 'docs/README must identify standing suite v0.9.'; Require-Contains $docsReadme 'Component Catalog' 'docs/README must preserve Component Catalog navigation.'
$matrix=Read-Json 'docs/archive/player_technology/pre-cp165-active/technology_architecture_matrix_v1.json'; Assert-True ([int]$matrix.checkpoint -eq 90 -and [string]$matrix.integrationCoverage.standingPermutationSuite -eq 'v0.9' -and [int]$matrix.integrationCoverage.legalBuildCount -eq 22592) 'Technology Matrix integration-coverage metadata mismatch.'
$suite=Read-Json 'docs/design/testing/technology_integration_permutation_suite_v0_9.json'; $cg=$suite.legalBuildEnumeration.constructionGuardrails
Assert-True ([int]$suite.checkpoint -eq 90 -and [string]$suite.legalBuildEnumeration.schema -eq 'star-cluster-cross-tl-build-permutation-v3' -and [int]$suite.legalBuildEnumeration.currentLegalBuildCount -eq 22592 -and [int]$suite.legalBuildEnumeration.currentBoundedScreen.generatedVariantCount -eq 432) 'Standing suite v0.9 generalized envelope metadata mismatch.'
Assert-True ([bool]$cg.redundantEwInstallationsAllowed -and -not [bool]$cg.ecmSameTypeRatingsAdditive -and -not [bool]$cg.eccmSameTypeRatingsAdditive -and [string]$cg.ewDuplicateResolution -eq 'highest_applicable_functional_rating') 'Standing suite v0.9 must preserve non-additive EW redundancy.'
$catalog=Read-Json 'docs/archive/player_technology/pre-cp165-active/component_installation_space_catalog_v1.json'; Assert-True ([int]$catalog.checkpoint -eq 89) 'Component Catalog should remain the unchanged CP89 authority in CP90.'

Write-Host '       Validating accepted CP89 provenance and frozen implementation/reference files...'
$cp89ManifestRel='docs/validation/evidence/checkpoint-89/CHECKPOINT_89_SHA256SUMS.txt'; $cp89Record=Read-Manifest $cp89ManifestRel
Assert-True ([int]$cp89Record.PhysicalLineCount -eq 1724 -and [int]$cp89Record.EntryCount -eq 1724) 'Accepted CP89 evidence manifest must contain exactly 1,724 unique entries.'
Assert-True ((Hash-Rel $cp89ManifestRel) -eq 'e049ed2d8260de30cdca9719af2b9487c62a7c25979c0649a0542752eaa4f1ec') 'Embedded CP89 evidence manifest bytes do not match accepted CP89.'
$prov=Read-Json 'docs/validation/evidence/checkpoint-89/checkpoint-89-native-acceptance-provenance.json'
Assert-True ([string]$prov.status -eq 'Success' -and [string]$prov.checkpointDefinitionSha256 -eq '664ab740d50e8950d13563fde139bd331de983e86ae69a4fe41a5e19c5738a91' -and [string]$prov.checkpointManifestSha256 -eq 'e049ed2d8260de30cdca9719af2b9487c62a7c25979c0649a0542752eaa4f1ec' -and [int]$prov.testsPassed -eq 863 -and [int]$prov.runnerSelfTests -eq 54 -and [int]$prov.failedGates -eq 0) 'CP89 native provenance mismatch.'
$cp89=$cp89Record.Entries
$allowedScenarioRunner=@(
 'src/StarCluster.ScenarioRunner/CrossTlIntegration/CrossTlBuildPermutationRunner.cs',
 'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs',
 'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatDocuments.cs',
 'src/StarCluster.ScenarioRunner/ScenarioRunnerSelfTests.cs'
)
$frozenCount=0
foreach($rel in @($cp89.Keys)){
    $freeze=$false
    if($rel.StartsWith('src/StarCluster.Core/',[System.StringComparison]::Ordinal) -or $rel.StartsWith('src/StarCluster.Game/',[System.StringComparison]::Ordinal) -or $rel.StartsWith('tests/',[System.StringComparison]::Ordinal)){ $freeze=$true }
    elseif($rel.StartsWith('src/StarCluster.ScenarioRunner/',[System.StringComparison]::Ordinal) -and -not ($allowedScenarioRunner -contains $rel)){ $freeze=$true }
    elseif($rel -eq 'docs/Star_Cluster_Game_Concept_v0.6z.docx' -or $rel -eq 'docs/design/player_technology/StarCluster_Technology_Architecture_Matrix_v1.xlsx' -or $rel -eq 'docs/archive/player_technology/pre-cp165-active/component_installation_space_catalog_v1.json' -or $rel -eq 'docs/design/ai/AI_Doctrine_Registry_Architecture_v0_5.md'){ $freeze=$true }
    elseif($rel.StartsWith('docs/references/',[System.StringComparison]::Ordinal) -and -not $rel.EndsWith('/README.md',[System.StringComparison]::OrdinalIgnoreCase)){ $freeze=$true }
    if($freeze){ Assert-True ((Hash-Rel $rel) -eq [string]$cp89[$rel]) "Checkpoint 90 changed frozen accepted file '$rel'."; $frozenCount++ }
}
Assert-True ($frozenCount -gt 500) "Checkpoint 90 frozen-baseline audit unexpectedly covered only $frozenCount files."

Write-Host 'Checkpoint 90 repository contracts passed.'
