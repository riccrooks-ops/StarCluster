[CmdletBinding()]
param()

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path

function Assert-True { param([bool]$Condition,[string]$Message) if (-not $Condition) { throw $Message } }
function Read-Text { param([string]$RelativePath) $p=Join-Path $repositoryRoot ($RelativePath.Replace('/','\')); Assert-True (Test-Path -LiteralPath $p -PathType Leaf) "Required file '$RelativePath' is missing."; [System.IO.File]::ReadAllText($p) }
function Read-Json { param([string]$RelativePath) (Read-Text $RelativePath) | ConvertFrom-Json }
function Read-ZipEntryText {
    param([string]$RelativePath,[string]$EntryName)
    $p=Join-Path $repositoryRoot ($RelativePath.Replace('/','\')); Assert-True (Test-Path -LiteralPath $p -PathType Leaf) "Archive '$RelativePath' is missing."
    Add-Type -AssemblyName System.IO.Compression.FileSystem -ErrorAction Stop | Out-Null
    $z=[System.IO.Compression.ZipFile]::OpenRead($p)
    try { $e=$z.GetEntry($EntryName); Assert-True ($null -ne $e) "Archive '$RelativePath' is missing '$EntryName'."; $s=$e.Open(); $r=New-Object System.IO.StreamReader($s); try { [string]$r.ReadToEnd() } finally { $r.Dispose() } } finally { $z.Dispose() }
}
function Read-DocxText { param([string]$RelativePath) [xml]$x=Read-ZipEntryText $RelativePath 'word/document.xml'; [string]$x.DocumentElement.InnerText }
function Parse-Manifest {
    param([string]$RelativePath)
    $map=@{}
    foreach ($line in (Read-Text $RelativePath -split "`r?`n")) {
        if ($line -match '^([0-9a-fA-F]{64})  (.+)$') { $map[$matches[2].Replace('\','/')]=$matches[1].ToLowerInvariant() }
    }
    return $map
}
function Hash-Rel { param([string]$RelativePath) $p=Join-Path $repositoryRoot ($RelativePath.Replace('/','\')); Assert-True (Test-Path -LiteralPath $p -PathType Leaf) "Hash target '$RelativePath' is missing."; (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant() }

Write-Host '       Validating native-dependency declarations...'
$guard=Join-Path $repositoryRoot 'tools\checkpoints\Test-NativeAcceptanceDependencies.ps1'
$normalRel='tools/calibration/checkpoints/checkpoint-85.json'
$deepRel='tools/calibration/checkpoints/checkpoint-85-deep-calibration.json'
$guardedPs=@('tools/checkpoints/Test-NativeAcceptanceDependencies.ps1','tools/checkpoints/checkpoint-85/apply_checkpoint_85.ps1','tools/checkpoints/checkpoint-85/test_checkpoint_85_contract.ps1','tools/calibration/run_calibration_checkpoint.ps1')
$guardedDefs=@($normalRel,$deepRel)
& $guard -RepositoryRoot $repositoryRoot -PowerShellPaths $guardedPs -CheckpointDefinitionPaths $guardedDefs

Write-Host '       Validating Checkpoint 85 definitions and workload accounting...'
$normal=Read-Json $normalRel; $deep=Read-Json $deepRel
Assert-True ([string]$normal.checkpointId -eq '85' -and [string]$deep.checkpointId -eq '85') 'Checkpoint 85 definition ID mismatch.'
Assert-True ([string]$normal.manifestFile -eq 'CHECKPOINT_85_SHA256SUMS.txt' -and [string]$deep.manifestFile -eq 'CHECKPOINT_85_SHA256SUMS.txt') 'Checkpoint 85 manifest binding mismatch.'
Assert-True ([string]$normal.outputRoot -eq 'out/checkpoint-85' -and [string]$deep.outputRoot -eq 'out/checkpoint-85-deep-calibration') 'Checkpoint 85 output-root binding mismatch.'
Assert-True (@($normal.stages).Count -eq 11 -and [int]$normal.checkpointMetrics.stageCount -eq 11) 'Checkpoint 85 normal stage-count mismatch.'
Assert-True ([int]$normal.checkpointMetrics.monteCarloVariantCount -eq 288 -and [int]$normal.checkpointMetrics.trialsAtDefault -eq 2880000 -and [int]$normal.checkpointMetrics.smokeVariantExecutions -eq 288 -and [int]$normal.checkpointMetrics.smokeTrialsAtDefault -eq 288 -and [int]$normal.checkpointMetrics.totalTrialExecutionsAtDefault -eq 2880288) 'Checkpoint 85 normal workload mismatch.'
Assert-True (@($deep.stages).Count -eq 36 -and [int]$deep.checkpointMetrics.monteCarloVariantCount -eq 1982 -and [int]$deep.checkpointMetrics.trialsAtDefault -eq 19820000 -and [int]$deep.checkpointMetrics.smokeVariantExecutions -eq 438 -and [int]$deep.checkpointMetrics.smokeTrialsAtDefault -eq 438 -and [int]$deep.checkpointMetrics.totalTrialExecutionsAtDefault -eq 19820438) 'Checkpoint 85 Deep Calibration workload mismatch.'
$expectedNormal=@('deterministic','tl1-phase-a','tl1-phase-b','tl1-installation-space-envelope','tl1-sensor-ew-foundation','tl2-armor-ap-ai-shield-integration-preflight','tl2-armor-ap-ai-shield-integration-smoke','tl2-armor-ap-ai-shield-integration-permutations','auxiliary-resource-endurance','checkpoint-53-resource-semantics-lock','runner-self-tests')
Assert-True ((@($normal.stages | ForEach-Object {[string]$_.id}) -join '|') -eq ($expectedNormal -join '|')) 'Checkpoint 85 normal stage ordering mismatch.'
$self=@($normal.stages | Where-Object {[string]$_.id -eq 'runner-self-tests'}); Assert-True ($self.Count -eq 1 -and [int]$self[0].metrics.selfTestCount -eq 50) 'Checkpoint 85 must expose 50 ScenarioRunner self-tests.'
Assert-True ([string]$normal.primaryStudy.id -eq 'tl2-itc11-armor-ap-ai-shield-integration-permutations' -and [int]$normal.primaryStudy.variantCount -eq 288) 'Checkpoint 85 primary-study binding mismatch.'
Assert-True ((@($normal.nativeDependencyPrecheck.powerShellPaths) -join '|') -eq ($guardedPs -join '|')) 'Checkpoint 85 native-dependency PowerShell binding mismatch.'
Assert-True ((@($normal.nativeDependencyPrecheck.checkpointDefinitionPaths) -join '|') -eq ($guardedDefs -join '|')) 'Checkpoint 85 native-dependency definition binding mismatch.'

Write-Host '       Validating the 288-cell Armor AP/AI x Shield integration study...'
$scenarioRel='src/StarCluster.ScenarioRunner/Scenarios/TL1Calibration/tl2-itc11-armor-ap-ai-shield-integration-permutations.json'
$study=Read-Json $scenarioRel; $variants=@($study.variants)
Assert-True ([string]$study.id -eq 'tl2-itc11-armor-ap-ai-shield-integration-permutations' -and $variants.Count -eq 288) 'CP85 study ID/count mismatch.'
Assert-True (@($variants | Select-Object -ExpandProperty id -Unique).Count -eq 288) 'CP85 variant IDs must be unique.'
$groups=@($variants | Group-Object comparisonGroup); Assert-True ($groups.Count -eq 18 -and (@($groups | Where-Object {$_.Count -ne 16}).Count -eq 0)) 'CP85 must contain 18 comparison groups of 16 variants.'
Assert-True (@($variants | Where-Object {[int]$_.sideAReactorOutputOverride -ne 6 -or [int]$_.sideBReactorOutputOverride -ne 5}).Count -eq 0) 'CP85 reactor controls drifted.'
Assert-True (@($variants | Where-Object {[int]$_.sideBShieldCapacityOverride -ne 2 -or [int]$_.sideBPrimaryArmorProtectionOverride -ne 0 -or [int]$_.sideBPrimaryArmorIntegrityOverride -ne 4}).Count -eq 0) 'CP85 Side-B defense control drifted.'
Assert-True (@($variants | Where-Object {[int]$_.sideAShieldCapacityOverride -notin @(2,3)}).Count -eq 0) 'CP85 Side-A Shield axis drifted.'
Assert-True (@($variants | Where-Object {[int]$_.sideAPrimaryArmorProtectionOverride -notin @(0,1) -or [int]$_.sideAPrimaryArmorIntegrityOverride -notin @(4,5)}).Count -eq 0) 'CP85 Side-A Armor axes drifted.'
foreach ($g in $groups) {
    foreach ($env in @('firm-reference','tall-dr1-eccm1')) {
        foreach ($shield in @(2,3)) {
            foreach ($ap in @(0,1)) { foreach ($ai in @(4,5)) {
                $label="$env-s$shield-ap$ap-ai$ai"
                $m=@($g.Group | Where-Object {[string]$_.label -eq $label -and [int]$_.sideAShieldCapacityOverride -eq $shield -and [int]$_.sideAPrimaryArmorProtectionOverride -eq $ap -and [int]$_.sideAPrimaryArmorIntegrityOverride -eq $ai})
                Assert-True ($m.Count -eq 1) "CP85 pairing missing/duplicated '$label' in '$($g.Name)'."
            }}
        }
    }
}
Assert-True (@($variants | Where-Object {[string]$_.sideAFamily -notin @('Kinetic','Energy')}).Count -eq 0) 'CP85 Side-A family axis drifted.'
Assert-True (@($variants | Where-Object {[string]$_.sideBFamily -notin @('Kinetic','Energy','Missile')}).Count -eq 0) 'CP85 Side-B family axis drifted.'

Write-Host '       Validating ScenarioRunner integration hooks and report contracts...'
$docsCode=Read-Text 'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatDocuments.cs'
$runnerCode=Read-Text 'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs'
$selfCode=Read-Text 'src/StarCluster.ScenarioRunner/ScenarioRunnerSelfTests.cs'
foreach ($needle in @('SideAPrimaryArmorIntegrityOverride','SideBPrimaryArmorIntegrityOverride','SideAPrimaryArmorProtectionOverride','SideBPrimaryArmorProtectionOverride')) { Assert-True ($docsCode.Contains($needle)) "Missing CP85 document field '$needle'." }
foreach ($needle in @('tl2-itc11-armor-ap-ai-shield-integration-permutations','ValidateTl2ArmorApAiShieldIntegrationCoverage','ApplyArmorOverrides','WriteTl2ArmorApAiShieldIntegrationReview','tl2-armor-ap-ai-shield-integration-review.csv','tl2-armor-ap-ai-shield-integration-paired-deltas.csv','tl2-c85-variant-coverage','tl2-c85-armor-axis-isolation','tl2-c85-shield-working-candidate-cross','tl2-c85-apen-counterplay-reference','tl2-c85-no-production-armor-promotion')) { Assert-True ($runnerCode.Contains($needle)) "Missing CP85 runner hook '$needle'." }
Assert-True ($selfCode.Contains('CP85 Armor AP/AI overrides are independent and preserve shield, reactor, and weapons') -and $selfCode.Contains('TestCp85ArmorOverrideSemantics')) 'CP85 Armor override self-test is missing.'

Write-Host '       Validating current architecture/documentation authority...'
$matrix=Read-Text 'docs/design/player_technology/Technology_Architecture_Matrix_v1.md'
$suite=Read-Text 'docs/design/testing/Technology_Integration_Permutation_Suite_Architecture_v0_5.md'
$studyDoc=Read-Text 'docs/design/player_technology/TL2_Armor_AP_AI_Shield_Integration_Study_v0_1.md'
$concept=Read-DocxText 'docs/Star_Cluster_Game_Concept_v0.6w.docx'
foreach ($needle in @('Shield Capacity 3','AP 0 / AI 4','AP 0 / AI 5','AP 1 / AI 4','AP 1 / AI 5','Checkpoint 85')) { Assert-True ($matrix.Contains($needle) -or $concept.Contains($needle) -or $studyDoc.Contains($needle)) "Current documentation is missing '$needle'." }
Assert-True ($suite.Contains('Technology Integration Permutation Suite v0.5') -and $suite.Contains('Armor')) 'Standing suite v0.5 Armor architecture is missing.'
Assert-True ($concept.Contains('C-059') -and $concept.Contains('Checkpoint 85') -and $concept.Contains('Armor Protection') -and $concept.Contains('Armor Integrity')) 'Concept v0.6w CP85 decision text is missing.'
$workbookXml=Read-ZipEntryText 'docs/design/player_technology/StarCluster_Technology_Architecture_Matrix_v1.xlsx' 'xl/workbook.xml'
Assert-True ($workbookXml.Contains('name="Armor"')) 'Technology Matrix workbook is missing the Armor sheet.'

Write-Host '       Validating accepted CP84 provenance and frozen production code...'
$cp84ManifestRel='docs/validation/evidence/checkpoint-84/CHECKPOINT_84_SHA256SUMS.txt'
$cp84Manifest=Parse-Manifest $cp84ManifestRel
Assert-True ($cp84Manifest.Count -gt 1500) 'Accepted CP84 evidence manifest is incomplete.'
$prov=Read-Json 'docs/validation/evidence/checkpoint-84/checkpoint-84-native-acceptance-provenance.json'
Assert-True ([string]$prov.acceptanceSummary.status -eq 'Success') 'CP84 provenance must record successful native acceptance.'
Assert-True ([string]$prov.designDisposition.shieldCapacity3Space3 -eq 'validated_working_candidate') 'CP84 provenance must record Shield 3 as validated.'
$allowedRunner=@('src/StarCluster.ScenarioRunner/ScenarioRunnerSelfTests.cs','src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatDocuments.cs','src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs')
foreach ($rel in @($cp84Manifest.Keys | Sort-Object)) {
    $freeze=$rel.StartsWith('src/StarCluster.Core/') -or $rel.StartsWith('src/StarCluster.Game/') -or $rel.StartsWith('tests/') -or ($rel.StartsWith('src/StarCluster.ScenarioRunner/') -and $allowedRunner -notcontains $rel)
    if ($freeze) { Assert-True ((Hash-Rel $rel) -eq [string]$cp84Manifest[$rel]) "Unexpected CP85 drift from accepted CP84 in '$rel'." }
}
$oldConceptRel='docs/Star_Cluster_Game_Concept_v0.6v.docx'
Assert-True ($cp84Manifest.ContainsKey($oldConceptRel)) 'Accepted CP84 manifest is missing Concept v0.6v.'
Assert-True ((Hash-Rel 'docs/archive/Star_Cluster_Game_Concept_v0.6v.docx') -eq [string]$cp84Manifest[$oldConceptRel]) 'Archived Concept v0.6v bytes drifted from accepted CP84.'
Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot 'docs\validation\archive\Checkpoint_84_TL2_Shield_Capacity_Power_Integration_Permutation_Suite.md') -PathType Leaf) 'Accepted CP84 validation runbook must be archived.'
$activeValidation=@(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs\validation') -File -Filter 'Checkpoint_*.md')
Assert-True ($activeValidation.Count -eq 1 -and $activeValidation[0].Name -eq 'Checkpoint_85_TL2_Armor_AP_AI_Shield_Integration_Permutation_Suite.md') 'Exactly one CP85 active validation runbook must remain.'
$activeConcept=@(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs') -File -Filter 'Star_Cluster_Game_Concept_v*.docx')
Assert-True ($activeConcept.Count -eq 1 -and $activeConcept[0].Name -eq 'Star_Cluster_Game_Concept_v0.6w.docx') 'Exactly one Concept v0.6w active document must remain.'
$rootTxt=@(Get-ChildItem -LiteralPath $repositoryRoot -File -Filter '*.txt')
Assert-True ($rootTxt.Count -eq 1 -and $rootTxt[0].Name -eq 'CHECKPOINT_85_SHA256SUMS.txt') 'Repository root must contain only CHECKPOINT_85_SHA256SUMS.txt as .txt.'

Write-Host '       CP85 isolation: AP0/AI4 control vs AI5, AP1, and AP1+AI5; Shield2/3 cross; Reactor6 held for Side A.'
Write-Host '       Standing suite: 18 combat/geometry groups x 2 information-control environments x 2 Shields x 4 Armor packages = 288 variants.'
Write-Host '       Normal workload: 11 stages / 288 substantive variants / 2,880,000 default substantive trials plus 288 smoke trials.'
Write-Host 'Checkpoint 85 contract validation passed.'
