[CmdletBinding()]
param([string]$RepositoryRoot)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($RepositoryRoot)) {
    $repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
} else {
    $repositoryRoot = (Resolve-Path $RepositoryRoot).Path
}

function Assert-True {
    param([bool]$Condition,[string]$Message)
    if (-not $Condition) { throw $Message }
}
function RelPath {
    param([string]$RelativePath)
    Join-Path $repositoryRoot ($RelativePath.Replace('/','\'))
}
function Read-Text {
    param([string]$RelativePath)
    $path = RelPath $RelativePath
    Assert-True (Test-Path -LiteralPath $path -PathType Leaf) "Required file '$RelativePath' is missing."
    [IO.File]::ReadAllText($path)
}
function Read-Json {
    param([string]$RelativePath)
    (Read-Text $RelativePath) | ConvertFrom-Json
}
function Hash-Rel {
    param([string]$RelativePath)
    (Get-FileHash -LiteralPath (RelPath $RelativePath) -Algorithm SHA256).Hash.ToLowerInvariant()
}
function Assert-ExactFileSet {
    param([string]$RelativeDirectory,[string[]]$Expected)
    $actual = @(Get-ChildItem -LiteralPath (RelPath $RelativeDirectory) -File | ForEach-Object Name | Sort-Object)
    $wanted = @($Expected | Sort-Object)
    Assert-True ($actual.Count -eq $wanted.Count) "Directory '$RelativeDirectory' active file count drifted."
    for ($i = 0; $i -lt $wanted.Count; $i++) {
        Assert-True ($actual[$i] -eq $wanted[$i]) "Directory '$RelativeDirectory' active file set drifted: expected '$($wanted[$i])', found '$($actual[$i])'."
    }
}
function Read-Manifest {
    param([string]$RelativePath)
    $map = @{}
    $lines = @(Get-Content -LiteralPath (RelPath $RelativePath))
    $lineNumber = 0
    foreach ($line in $lines) {
        $lineNumber++
        $match = [regex]::Match([string]$line,'^([0-9a-fA-F]{64})  (.+)$')
        Assert-True $match.Success "Manifest '$RelativePath' malformed at line $lineNumber."
        $relative = $match.Groups[2].Value.Replace('\','/')
        Assert-True (-not $map.ContainsKey($relative)) "Manifest '$RelativePath' duplicates '$relative'."
        $map[$relative] = $match.Groups[1].Value.ToLowerInvariant()
    }
    [pscustomobject]@{ EntryCount = $map.Count; Entries = $map }
}
function Test-IsGeneratedOrLocalPath {
    param([string]$RelativePath)
    $path = $RelativePath.Replace('\','/')
    if ($path -like '.git/*' -or $path -like '.vs/*' -or $path -like '.vscode/*' -or $path -like '.idea/*' -or $path -like 'out/*' -or $path -like 'src/StarCluster.Game/.godot/*' -or $path -match '(^|/)(bin|obj|TestResults)/') { return $true }
    if ($path -match '(^|/)__pycache__/' -or $path -match '\.pyc$') { return $true }
    if ($path -match '\.(user|userosscache|sln\.docstates|uid)$' -or $path -match '(^|/)\.suo$' -or $path -match '(^|/)(\.DS_Store|Thumbs\.db)$') { return $true }
    return $false
}
function Get-Cp105RepositoryOwnedFileSet {
    $map = @{}
    foreach ($file in @(Get-ChildItem -LiteralPath $repositoryRoot -Recurse -File -Force)) {
        $relative = $file.FullName.Substring($repositoryRoot.Length).TrimStart('\','/').Replace('\','/')
        if ($relative -eq 'CHECKPOINT_105_SHA256SUMS.txt') { continue }
        if (Test-IsGeneratedOrLocalPath -RelativePath $relative) { continue }
        $map[$relative] = $true
    }
    return $map
}
function Assert-FrozenAgainstCp104Manifest {
    param($Manifest,[string]$RelativePath)
    Assert-True ($Manifest.Entries.ContainsKey($RelativePath)) "Frozen CP104 manifest does not contain '$RelativePath'."
    Assert-True ((Hash-Rel $RelativePath) -eq [string]$Manifest.Entries[$RelativePath]) "CP105 unexpectedly changed frozen CP104 path '$RelativePath'."
}
function Assert-ObjectJsonEqual {
    param($Left,$Right,[string]$Message)
    $a = $Left | ConvertTo-Json -Depth 50 -Compress
    $b = $Right | ConvertTo-Json -Depth 50 -Compress
    Assert-True ($a -eq $b) $Message
}

Write-Host '       Validating accepted CP104 provenance and frozen executable surfaces...'
Assert-True ((Hash-Rel 'docs/validation/evidence/checkpoint-104/CHECKPOINT_104_SHA256SUMS.txt') -eq '03edf5b92afb5f6dc8073040b6e9bd58fb0c73f603f8d5cdc284ae00f6e9ace4') 'Embedded accepted CP104 manifest hash drifted.'
Assert-True ((Hash-Rel 'docs/validation/evidence/checkpoint-104/checkpoint-104-native-acceptance-summary.json') -eq 'efbfa92cf1e40e560e1d7c117c32ee28a106663acdde0532cc652ebf901ad6bb') 'Embedded CP104 native acceptance summary drifted.'
$accepted = Read-Json 'docs/validation/evidence/checkpoint-104/checkpoint-104-native-acceptance-summary.json'
Assert-True ([string]$accepted.status -eq 'Success') 'Embedded CP104 acceptance must be Success.'
Assert-True ([int]$accepted.tests.passed -eq 876 -and [int]$accepted.tests.failed -eq 0) 'Embedded CP104 xUnit evidence drifted.'
Assert-True ([int]$accepted.aggregates.runnerStagesPassed -eq 20 -and [int]$accepted.aggregates.failedGates -eq 0) 'Embedded CP104 stage/gate evidence drifted.'
Assert-True ([int]$accepted.aggregates.trials -eq 128288) 'Embedded CP104 trial accounting drifted.'
$cp104Provenance = Read-Json 'docs/validation/evidence/checkpoint-104/provenance.json'
Assert-True ([string]$cp104Provenance.nativeResultsArchiveSha256 -eq '4819182f19f9e5b9248846eacad0cb3a1385cc23dd745a40378062a9f0b37550') 'CP104 native-results provenance drifted.'
$cp104Manifest = Read-Manifest 'docs/validation/evidence/checkpoint-104/CHECKPOINT_104_SHA256SUMS.txt'
foreach ($prefix in @('src/','tests/','tools/simulation/','tools/calibration/')) {
    foreach ($relative in @($cp104Manifest.Entries.Keys | Where-Object { $_.StartsWith($prefix,[StringComparison]::Ordinal) })) {
        Assert-FrozenAgainstCp104Manifest -Manifest $cp104Manifest -RelativePath ([string]$relative)
    }
}
foreach ($relative in @(
    'docs/design/player_technology/StarCluster_Technology_Architecture_Matrix_v1.xlsx',
    'docs/archive/player_technology/pre-cp165-active/tl1_35_space_player_cruiser_baseline_v0_9.json',
    'docs/archive/player_technology/pre-cp165-active/tl3_base_technology_candidates_v0_2.json',
    'docs/archive/player_technology/pre-cp165-active/tl3_base_build_sanity_v0_1.json',
    'docs/archive/player_technology/pre-cp165-active/tl3_executable_implementation_profile_v0_1.json'
)) {
    Assert-FrozenAgainstCp104Manifest -Manifest $cp104Manifest -RelativePath $relative
}
$componentCatalog = Read-Json 'docs/archive/player_technology/pre-cp165-active/component_installation_space_catalog_v1.json'
$frozenComponentCatalog = Read-Json 'docs/validation/evidence/checkpoint-104/component_installation_space_catalog_v1.json'
Assert-ObjectJsonEqual -Left $componentCatalog.globalRules -Right $frozenComponentCatalog.globalRules -Message 'CP105 must not change component Installation-Space global rules.'
foreach ($component in @($componentCatalog.components)) { if ($null -ne $component.PSObject.Properties['source']) { $component.source = '' } }
foreach ($component in @($frozenComponentCatalog.components)) { if ($null -ne $component.PSObject.Properties['source']) { $component.source = '' } }
Assert-ObjectJsonEqual -Left $componentCatalog.components -Right $frozenComponentCatalog.components -Message 'CP105 must not change component Installation-Space values; source metadata may only follow Concept v0.7e.'
Assert-True ([int]$componentCatalog.checkpoint -eq 105 -and [string]$componentCatalog.authority.concept -eq 'docs/Star_Cluster_Game_Concept_v0.7e.docx') 'Component catalog lifecycle metadata must point to CP105 / Concept v0.7e.'
Assert-True (-not (Test-Path -LiteralPath (RelPath 'tools/calibration/checkpoints/checkpoint-105.json'))) 'CP105 must not create a calibration definition.'
Assert-True (-not (Test-Path -LiteralPath (RelPath 'tools/calibration/checkpoints/checkpoint-105-deep-calibration.json'))) 'CP105 must not create a Deep Calibration definition.'

Write-Host '       Validating CP105 architecture definition and active Concept authority...'
$definition = Read-Json 'tools/checkpoints/checkpoint-105/checkpoint_105_architecture_definition.json'
Assert-True ([string]$definition.checkpointId -eq '105') 'CP105 architecture definition checkpoint drifted.'
Assert-True ([string]$definition.scope -eq 'technology_architecture_only') 'CP105 architecture scope drifted.'
Assert-True (-not [bool]$definition.numericalTlTableChanged -and -not [bool]$definition.simulationOrCalibrationRun) 'CP105 must remain architecture-only.'
Assert-True ([int]$definition.declaredTrials -eq 0 -and @($definition.stages).Count -eq 0) 'CP105 must remain zero-trial/zero-stage.'
Assert-True (-not [bool]$definition.dotnetBuildRequired -and -not [bool]$definition.pythonRequired) 'CP105 must not require .NET or Python.'
$activeConcepts = @(Get-ChildItem -LiteralPath (RelPath 'docs') -File -Filter 'Star_Cluster_Game_Concept*.docx' | ForEach-Object Name)
Assert-True ($activeConcepts.Count -eq 1 -and $activeConcepts[0] -eq 'Star_Cluster_Game_Concept_v0.7e.docx') 'Exactly Concept v0.7e must be active.'
Assert-True (Test-Path -LiteralPath (RelPath 'docs/archive/concepts/Star_Cluster_Game_Concept_v0.7d.docx') -PathType Leaf) 'Concept v0.7d archive continuity is missing.'
$conceptText = Read-Text 'docs/design/player_technology/Technology_Family_Storyboard_v1.md'
Assert-True ($conceptText.IndexOf('TL1 is a highly mature slightly futuristic baseline',[StringComparison]::OrdinalIgnoreCase) -ge 0) 'Storyboard must retain the soft TL1 era tone.'
Assert-True ($conceptText.IndexOf('TL2-4 broadly feel like lower science fiction',[StringComparison]::OrdinalIgnoreCase) -ge 0) 'Storyboard must retain the soft TL2-4 era tone.'
Assert-True ($conceptText.IndexOf('TL5-7 higher science fiction',[StringComparison]::OrdinalIgnoreCase) -ge 0) 'Storyboard must retain the soft TL5-7 era tone.'
Assert-True ($conceptText.IndexOf('TL8-9 increasingly science fantasy',[StringComparison]::OrdinalIgnoreCase) -ge 0) 'Storyboard must retain the soft TL8-9 era tone.'

Write-Host '       Validating technology-family storyboard and lifecycle/status semantics...'
$storyboard = Read-Json 'docs/design/player_technology/technology_family_storyboard_v1.json'
Assert-True ([string]$storyboard.checkpoint -eq '105') 'Storyboard checkpoint must be string 105.'
Assert-True (-not [bool]$storyboard.numericalTlTableChanged -and -not [bool]$storyboard.simulationOrCalibrationRun) 'Storyboard must declare no numerical/simulation change.'
Assert-True (@($storyboard.normalPlayerTlRange).Count -eq 2 -and [int]$storyboard.normalPlayerTlRange[0] -eq 1 -and [int]$storyboard.normalPlayerTlRange[1] -eq 9) 'Normal player TL range must remain 1-9.'
Assert-True ([bool]$storyboard.precursorTl10Shorthand) 'Storyboard must retain TL10 as Precursor shorthand.'
$allowedStatuses = @('base','existing','candidate','deferred','exotic')
$allowedRoles = @('core_family','maturation','branch','cross_pollinated_derivative','legacy_revival','operating_capability','specialist_auxiliary','one_off','infrastructure','campaign_technology','weird_science','precursor_artifact')
foreach ($status in $allowedStatuses) { Assert-True ($null -ne $storyboard.statusDefinitions.$status) "Storyboard status '$status' is missing." }
foreach ($role in $allowedRoles) { Assert-True ($null -ne $storyboard.structuralRoleDefinitions.$role) "Storyboard structural role '$role' is missing." }
$disciplines = @($storyboard.disciplines)
Assert-True ($disciplines.Count -eq 10) 'Storyboard must contain 10 visible research disciplines.'
$lineageCount = 0
$beatCount = 0
$tl10BeatCount = 0
foreach ($discipline in $disciplines) {
    $lineages = @($discipline.lineages)
    $lineageCount += $lineages.Count
    foreach ($lineage in $lineages) {
        foreach ($beat in @($lineage.beats)) {
            $beatCount++
            $status = [string]$beat.status
            $role = [string]$beat.role
            Assert-True ($allowedStatuses -contains $status) "Storyboard beat '$($beat.title)' has invalid status '$status'."
            Assert-True ($allowedRoles -contains $role) "Storyboard beat '$($beat.title)' has invalid structural role '$role'."
            $tl = [int]$beat.tl
            Assert-True ($tl -ge 1 -and $tl -le 10) "Storyboard beat '$($beat.title)' has invalid TL '$tl'."
            if ($tl -eq 10) {
                $tl10BeatCount++
                Assert-True ($status -eq 'exotic' -and $role -eq 'precursor_artifact') "TL10 beat '$($beat.title)' must be Exotic/Precursor-only."
            }
        }
    }
}
Assert-True ($lineageCount -eq 31) 'Storyboard must contain 31 technology lineages.'
Assert-True ($beatCount -ge 200) 'Storyboard must retain the deep-dive beat coverage.'
Assert-True ($tl10BeatCount -ge 4) 'Storyboard must preserve explicit Precursor/TL10-shorthand examples.'
# Required Power-family story anchors.
$power = @($disciplines | Where-Object { [string]$_.name -eq 'Power' })
Assert-True ($power.Count -eq 1) 'Storyboard must contain exactly one Power discipline.'
$powerBeats = @($power[0].lineages | ForEach-Object { @($_.beats) })
$powerTitles = @($powerBeats | ForEach-Object { [string]$_.title })
foreach ($required in @('Peak Fission','Early Practical Fusion','Mature Compact Fusion','High-Output Fusion','Early Antimatter / Peak Fusion coexistence','Mature Antimatter','High-Output Antimatter','Fractional/Direct Matter Conversion / Peak Antimatter coexistence','Total Matter Conversion')) {
    Assert-True ($powerTitles -contains $required) "Power family story is missing '$required'."
}
Assert-True ($powerTitles -contains 'Direct-conversion / advanced-containment fission specialist') 'Power family must preserve a later Fission revival.'

Write-Host '       Validating technology idea register, cross-pollination map, and reference synthesis...'
$ideas = Read-Json 'docs/design/player_technology/technology_idea_register_v1.json'
$ideaRows = @($ideas.ideas)
Assert-True ($ideaRows.Count -eq 120) 'CP105 idea register must contain 120 preserved anchors/ideas.'
$ids = @{}
$statusSeen = @{}
foreach ($idea in $ideaRows) {
    $id = [string]$idea.id
    Assert-True (-not $ids.ContainsKey($id)) "Idea register duplicates '$id'."
    $ids[$id] = $true
    $status = [string]$idea.status
    $role = [string]$idea.role
    Assert-True ($allowedStatuses -contains $status) "Idea '$id' has invalid status '$status'."
    Assert-True ($allowedRoles -contains $role) "Idea '$id' has invalid structural role '$role'."
    $statusSeen[$status] = $true
    if ([string]$idea.provisionalWindow -eq 'TL10 shorthand') {
        Assert-True ($status -eq 'exotic') "Idea '$id' uses TL10 shorthand but is not Exotic."
    }
}
foreach ($status in $allowedStatuses) { Assert-True ($statusSeen.ContainsKey($status)) "Idea register must contain lifecycle status '$status'." }
function Assert-IdeaStatus {
    param([string]$Title,[string]$Status)
    $rows = @($ideaRows | Where-Object { [string]$_.title -eq $Title })
    Assert-True ($rows.Count -eq 1) "Idea register must contain exactly one '$Title'."
    Assert-True ([string]$rows[0].status -eq $Status) "Idea '$Title' must be status '$Status'."
}
Assert-IdeaStatus 'Early Practical Fusion Main Reactor' 'existing'
Assert-IdeaStatus 'Early Antimatter Main Reactor' 'existing'
Assert-IdeaStatus 'Ion Cannon / Charged-Particle Cannon' 'candidate'
Assert-IdeaStatus 'Advanced Fission Specialist Reactor' 'base'
Assert-IdeaStatus 'Singularity / Black-Hole Gun' 'exotic'
Assert-IdeaStatus 'Phase Cloak' 'exotic'
Assert-IdeaStatus 'Matter-Bond Disruptor' 'deferred'
$crossText = Read-Text 'docs/design/player_technology/Cross_Pollination_And_Legacy_Revival_Map_v1.md'
Assert-True ($crossText.IndexOf('legacy revival',[StringComparison]::OrdinalIgnoreCase) -ge 0) 'Cross-pollination map must define legacy revival.'
Assert-True ($crossText.IndexOf('Fission',[StringComparison]::OrdinalIgnoreCase) -ge 0) 'Cross-pollination map must preserve Fission revival examples.'
$referenceText = Read-Text 'docs/references/reference-mining/technology-architecture/CP105_Technology_Architecture_Reference_Synthesis.md'
foreach ($needle in @('Spacedock','Terra Invicta','NASA','CERN','originality')) {
    Assert-True ($referenceText.IndexOf($needle,[StringComparison]::OrdinalIgnoreCase) -ge 0) "Reference synthesis must include '$needle'."
}
$sourceIndex = Read-Json 'docs/references/reference-mining/technology-architecture/web-source-index.json'
Assert-True (@($sourceIndex.sources).Count -ge 15) 'CP105 source index is unexpectedly sparse.'

Write-Host '       Validating no numerical TL-table or research-engine change...'
$matrix = Read-Json 'docs/archive/player_technology/pre-cp165-active/technology_architecture_matrix_v1.json'
$frozenMatrix = Read-Json 'docs/validation/evidence/checkpoint-104/technology_architecture_matrix_v1.json'
Assert-ObjectJsonEqual -Left $matrix.tiers -Right $frozenMatrix.tiers -Message 'CP105 must not change the Technology Matrix tiers table.'
Assert-True ([int]$matrix.checkpoint -eq 105) 'Technology Matrix documentation checkpoint must be 105.'
Assert-True ([string]$matrix.authority.concept -eq 'docs/Star_Cluster_Game_Concept_v0.7e.docx') 'Technology Matrix must point to Concept v0.7e.'
Assert-True (-not [bool]$matrix.authority.numericalTlChartChangedByCp105) 'Technology Matrix must declare no CP105 numerical change.'
Assert-True ([string]$matrix.integrationArchitecture.cp105TechnologyFamilyStoryboard -eq 'docs/design/player_technology/technology_family_storyboard_v1.json') 'Technology Matrix must point to the CP105 family storyboard.'
Assert-True (-not [bool]$matrix.integrationArchitecture.cp105SimulationOrCalibrationRun) 'Technology Matrix must declare no CP105 simulation/calibration.'
$policy = Read-Json 'docs/design/testing/checkpoint_105_validation_suite_policy_v0_1.json'
Assert-True ([int]$policy.declaredTrials -eq 0 -and -not [bool]$policy.numericalTlChartChanged -and -not [bool]$policy.simulationOrCalibrationRun) 'CP105 validation policy must remain architecture-only.'

Write-Host '       Validating active documentation and final repository manifest...'
Assert-ExactFileSet 'docs/design/testing' @('README.md','Checkpoint_105_Validation_Tiers.md','checkpoint_105_validation_suite_policy_v0_1.json','Technology_Integration_Permutation_Suite_Architecture_v0_19.md','technology_integration_permutation_suite_v0_19.json')
Assert-ExactFileSet 'docs/validation' @('README.md','Checkpoint_105_Technology_Family_Architecture_Foundation.md')
foreach ($path in @(
    'README.md','CHAT_README.md','docs/README.md','docs/Prototype_TODO.md','docs/design/README.md','docs/design/player_technology/README.md','docs/design/testing/README.md','docs/validation/README.md','docs/references/README.md','docs/references/reference-mining/README.md'
)) {
    $text = Read-Text $path
    Assert-True ($text.IndexOf('Checkpoint 105',[StringComparison]::OrdinalIgnoreCase) -ge 0 -or $text.IndexOf('CP105',[StringComparison]::OrdinalIgnoreCase) -ge 0) "Active document '$path' must recognize CP105."
}
$manifest = Read-Manifest 'CHECKPOINT_105_SHA256SUMS.txt'
$actual = Get-Cp105RepositoryOwnedFileSet
Assert-True ($actual.Count -eq $manifest.EntryCount) "CP105 manifest entry count $($manifest.EntryCount) does not match repository-owned file count $($actual.Count)."
foreach ($relative in $manifest.Entries.Keys) {
    Assert-True ($actual.ContainsKey([string]$relative)) "CP105 manifest lists missing/unowned path '$relative'."
    Assert-True ((Hash-Rel ([string]$relative)) -eq [string]$manifest.Entries[[string]$relative]) "CP105 manifest hash mismatch for '$relative'."
}
foreach ($relative in $actual.Keys) {
    Assert-True ($manifest.Entries.ContainsKey([string]$relative)) "Repository-owned path '$relative' is missing from CP105 manifest."
}
Assert-True (-not $manifest.Entries.ContainsKey('CHECKPOINT_104_SHA256SUMS.txt')) 'Superseded CP104 root manifest must not remain repository-owned in CP105.'

Write-Host "       CP105 contract verified: $($manifest.EntryCount) repository-owned files; accepted CP104 evidence preserved; 10 disciplines / 31 lineages / $beatCount storyboard beats / 120 idea-register entries; zero trials; zero numerical TL-table change."
