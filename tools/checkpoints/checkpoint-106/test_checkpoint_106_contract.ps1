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
function Assert-ObjectJsonEqual {
    param($Left,$Right,[string]$Message)
    $a = $Left | ConvertTo-Json -Depth 50 -Compress
    $b = $Right | ConvertTo-Json -Depth 50 -Compress
    Assert-True ($a -eq $b) $Message
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
    $lineNumber = 0
    foreach ($line in @(Get-Content -LiteralPath (RelPath $RelativePath))) {
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
function Get-Cp106RepositoryOwnedFileSet {
    $map = @{}
    foreach ($file in @(Get-ChildItem -LiteralPath $repositoryRoot -Recurse -File -Force)) {
        $relative = $file.FullName.Substring($repositoryRoot.Length).TrimStart('\','/').Replace('\','/')
        if ($relative -eq 'CHECKPOINT_106_SHA256SUMS.txt') { continue }
        if (Test-IsGeneratedOrLocalPath -RelativePath $relative) { continue }
        $map[$relative] = $true
    }
    return $map
}

Write-Host '       Validating accepted CP105 provenance and frozen CP104 numerical/executable authority...'
Assert-True ((Hash-Rel 'docs/validation/evidence/checkpoint-105/CHECKPOINT_105_SHA256SUMS.txt') -eq 'bfde82f7b59f6323784cd9a76b78ce548b37d08d6d268540c30914a50e7a6385') 'Accepted CP105 manifest hash drifted.'
Assert-True ((Hash-Rel 'tools/checkpoints/checkpoint-105/checkpoint_105_architecture_definition.json') -eq 'ca8ca231066e8d80ac0c605a6a28cf1efd2a5dab0664d645327273a764f860d5') 'Accepted CP105 architecture definition drifted.'
Assert-True ((Hash-Rel 'docs/archive/concepts/Star_Cluster_Game_Concept_v0.7e.docx') -eq '32c20b3c210f8bdee7f72ea07d76985a3e35de4b988186f98dc71965647ac360') 'Accepted Concept v0.7e archive drifted.'
$accepted105 = Read-Json 'docs/validation/evidence/checkpoint-105/checkpoint-105-accepted-provenance.json'
Assert-True ([string]$accepted105.status -eq 'Accepted' -and [int]$accepted105.repositoryOwnedFiles -eq 2037) 'Accepted CP105 provenance record drifted.'
$matrix = Read-Json 'docs/archive/player_technology/pre-cp165-active/technology_architecture_matrix_v1.json'
$frozenMatrix = Read-Json 'docs/validation/evidence/checkpoint-104/technology_architecture_matrix_v1.json'
Assert-ObjectJsonEqual -Left $matrix.tiers -Right $frozenMatrix.tiers -Message 'CP106 must not change the Technology Matrix tiers table.'
Assert-True (-not [bool]$matrix.authority.numericalTlChartChangedByCp106) 'Matrix must declare no CP106 numerical change.'
Assert-True (-not (Test-Path -LiteralPath (RelPath 'tools/calibration/checkpoints/checkpoint-106.json'))) 'CP106 must not create a calibration definition.'
Assert-True (-not (Test-Path -LiteralPath (RelPath 'tools/calibration/checkpoints/checkpoint-106-deep-calibration.json'))) 'CP106 must not create a Deep Calibration definition.'

Write-Host '       Validating active Concept and technology architecture...'
$definition = Read-Json 'tools/checkpoints/checkpoint-106/checkpoint_106_architecture_definition.json'
Assert-True ([string]$definition.checkpointId -eq '106' -and [string]$definition.acceptedBaseline -eq '105') 'CP106 definition identity drifted.'
Assert-True (-not [bool]$definition.numericalTlTableChanged -and -not [bool]$definition.simulationOrCalibrationRun -and [int]$definition.declaredTrials -eq 0) 'CP106 definition must remain architecture-only.'
$activeConcepts = @(Get-ChildItem -LiteralPath (RelPath 'docs') -File -Filter 'Star_Cluster_Game_Concept*.docx' | ForEach-Object Name)
Assert-True ($activeConcepts.Count -eq 1 -and $activeConcepts[0] -eq 'Star_Cluster_Game_Concept_v0.7f.docx') 'Exactly Concept v0.7f must be active.'
$storyboard = Read-Json 'docs/archive/player_technology/pre-cp165-active/technology_family_storyboard_v1_1.json'
Assert-True ([string]$storyboard.checkpoint -eq '106') 'Storyboard checkpoint drifted.'
$disciplines = @($storyboard.disciplines)
Assert-True ($disciplines.Count -eq 10) 'Storyboard must preserve 10 visible disciplines.'
$lineages = @($disciplines | ForEach-Object { @($_.lineages) })
$beats = @($lineages | ForEach-Object { @($_.beats) })
Assert-True ($lineages.Count -eq 32 -and $beats.Count -ge 214) 'Storyboard must contain 32 lineages and at least 214 beats.'
foreach ($beat in $beats) {
    Assert-True ($null -ne $beat.PSObject.Properties['relatedResearch']) "Storyboard beat '$($beat.title)' lacks relatedResearch."
    Assert-True ($null -ne $beat.PSObject.Properties['hardExternalPrerequisites']) "Storyboard beat '$($beat.title)' lacks explicit hard-prerequisite metadata."
    Assert-True (@($beat.hardExternalPrerequisites).Count -eq 0) "CP106 must not silently promote a hard external prerequisite for '$($beat.title)'."
}
$energyPds = @($lineages | Where-Object { [string]$_.id -eq 'energy-pds' })
Assert-True ($energyPds.Count -eq 1 -and [string]$energyPds[0].owner -eq 'Energy Weapons') 'Separate Energy PDS lineage is missing.'
$energyTl1 = @($energyPds[0].beats | Where-Object { [int]$_.tl -eq 1 -and [string]$_.status -eq 'base' })
Assert-True ($energyTl1.Count -eq 1 -and [string]$energyTl1[0].story -match '2-TP readiness' -and [string]$energyTl1[0].story -match 'no conventional ammunition') 'Energy PDS TL1 identity drifted.'
$ablative = @($lineages | Where-Object { [string]$_.id -eq 'armor-enhancements' } | ForEach-Object { @($_.beats) } | Where-Object { [string]$_.title -eq 'Ablative outer layer' })
Assert-True ($ablative.Count -eq 1 -and [int]$ablative[0].tl -eq 1 -and [string]$ablative[0].story -match 'starting cruiser' -and [string]$ablative[0].story -match 'Installation Space') 'TL1 starting-legal ablative role drifted.'
$localAmm = @($lineages | Where-Object { [string]$_.id -eq 'amm' } | ForEach-Object { @($_.beats) } | Where-Object { [string]$_.title -eq 'Baseline local AMM point defense' })
Assert-True ($localAmm.Count -eq 1 -and [int]$localAmm[0].tl -eq 1 -and [string]$localAmm[0].boundary -match 'not the later long-range') 'Local AMM versus long-range AMM distinction drifted.'
$storyText = Read-Text 'docs/design/player_technology/Technology_Family_Storyboard_v1_1.md'
foreach ($needle in @('vertical spine','non-gating','TL1 is a highly mature slightly futuristic baseline','Energy / Beam Point Defense')) {
    Assert-True ($storyText.IndexOf($needle,[StringComparison]::OrdinalIgnoreCase) -ge 0) "Storyboard must contain '$needle'."
}

Write-Host '       Validating idea inventory and foundation completeness ledger...'
$register = Read-Json 'docs/design/player_technology/technology_idea_register_v1_1.json'
$ideas = @($register.ideas)
Assert-True ($ideas.Count -eq 136) 'Idea Register must contain 136 entries.'
$ideaIds = @{}
foreach ($idea in $ideas) {
    Assert-True (-not $ideaIds.ContainsKey([string]$idea.id)) "Idea register duplicates '$($idea.id)'."
    $ideaIds[[string]$idea.id] = $true
}
foreach ($requiredTitle in @('Advanced Beam Point-Defense Maturation','Baseline Energy / Beam Point Defense','Baseline Local AMM Point Defense','TL1 Ablative Outer Armor Layer','Medical Bay','Fuel Processor','Expedition Fuel / Endurance Module','Advanced Shuttle / Mission Bay','Scientific Laboratory Module','Mining and Extraction Module','General Fabrication Module','Expanded Cargo Bay','Magazine Expansion','Communications Relay / Mission Communications Suite','Hardened Control and Cybersecurity Architecture','Matter Transport / Portal System')) {
    Assert-True (@($ideas | Where-Object { [string]$_.title -eq $requiredTitle }).Count -eq 1) "Idea Register is missing '$requiredTitle'."
}
$audit = Read-Json 'docs/design/player_technology/Technology_Foundation_Completeness_Audit_v1.json'
$domains = @($audit.domains)
Assert-True ($domains.Count -eq 20) 'Foundation audit must contain 20 domains.'
foreach ($domain in $domains) {
    Assert-True (@('established','partial','abstracted','deferred','out_of_scope') -contains [string]$domain.foundationStatus) "Domain '$($domain.id)' has invalid status."
    Assert-True (@($domain.playerFacingState).Count -gt 0 -and @($domain.technologyHooks).Count -gt 0 -and -not [string]::IsNullOrWhiteSpace([string]$domain.abstractionBoundary)) "Domain '$($domain.id)' is incomplete."
}
foreach ($domainId in @('installation-capacity','thermal-radiation','crew-marines','life-support-medical','fuel-endurance','cargo-resources','ammunition-stores','repair-salvage-fabrication','shuttle-mission-systems','science-research','extraction-processing','exploration-comms','home-infrastructure','hazards-environment','cyber-autonomy','exotic-mobility')) {
    Assert-True (@($domains | Where-Object { [string]$_.id -eq $domainId }).Count -eq 1) "Foundation domain '$domainId' is missing."
}
$excludedText = @($audit.explicitlyExcludedComplexity) -join ' '
foreach ($needle in @('heat meter','radiator hit locations','radiation-dose','food/water/oxygen','per-component staffing')) {
    Assert-True ($excludedText.IndexOf($needle,[StringComparison]::OrdinalIgnoreCase) -ge 0) "Foundation exclusions must include '$needle'."
}

Write-Host '       Validating complete reference-observation disposition...'
$observations = Read-Json 'docs/references/reference-mining/observation-index.json'
$coverage = Read-Json 'docs/references/reference-mining/technology-architecture/cp106_reference_observation_coverage_v1.json'
$coverageRows = @($coverage.rows)
Assert-True ([int]$observations.observationCount -eq 195 -and @($observations.observations).Count -eq 195) 'Preserved observation corpus drifted.'
Assert-True ([bool]$coverage.complete -and [int]$coverage.observationCount -eq 195 -and [int]$coverage.coverageCount -eq 195 -and $coverageRows.Count -eq 195) 'Coverage ledger must completely dispose 195 observations.'
$sourceIds = @{}
foreach ($observation in @($observations.observations)) { $sourceIds[[string]$observation.id] = $true }
$coveredIds = @{}
foreach ($row in $coverageRows) {
    $id = [string]$row.observationId
    Assert-True ($sourceIds.ContainsKey($id)) "Coverage row '$id' is not in observation-index.json."
    Assert-True (-not $coveredIds.ContainsKey($id)) "Coverage ledger duplicates '$id'."
    Assert-True (@('incorporated','foundation_captured','abstraction_guardrail','deferred','excluded') -contains [string]$row.coverageOutcome) "Coverage row '$id' has invalid outcome."
    Assert-True (@($row.destinations).Count -gt 0 -and -not [string]::IsNullOrWhiteSpace([string]$row.coverageReason)) "Coverage row '$id' lacks a destination/reason."
    $coveredIds[$id] = $true
}
Assert-True ($coveredIds.Count -eq $sourceIds.Count) 'Coverage ID set is incomplete.'

Write-Host '       Validating active documentation and repository manifest...'
$cross = Read-Text 'docs/design/player_technology/Cross_Pollination_And_Legacy_Revival_Map_v1_1.md'
foreach ($needle in @('vertical spines come first','non-gating','legacy revival','anti-gatekeeper tests')) {
    Assert-True ($cross.IndexOf($needle,[StringComparison]::OrdinalIgnoreCase) -ge 0) "Cross-pollination map must contain '$needle'."
}
$policy = Read-Json 'docs/design/testing/checkpoint_106_validation_suite_policy_v0_1.json'
Assert-True ([int]$policy.declaredTrials -eq 0 -and -not [bool]$policy.numericalTlChartChanged -and -not [bool]$policy.simulationOrCalibrationRun) 'CP106 validation policy must remain architecture-only.'
Assert-ExactFileSet 'docs/design/testing' @('README.md','Checkpoint_106_Validation_Tiers.md','checkpoint_106_validation_suite_policy_v0_1.json','Technology_Integration_Permutation_Suite_Architecture_v0_20.md','technology_integration_permutation_suite_v0_20.json')
Assert-ExactFileSet 'docs/validation' @('README.md','Checkpoint_106_Technology_Foundation_Completeness_Audit.md')
foreach ($path in @('README.md','CHAT_README.md','docs/README.md','docs/design/player_technology/README.md','docs/design/testing/README.md','docs/validation/README.md','docs/references/reference-mining/README.md')) {
    Assert-True ((Read-Text $path).IndexOf('CP106',[StringComparison]::OrdinalIgnoreCase) -ge 0 -or (Read-Text $path).IndexOf('Checkpoint 106',[StringComparison]::OrdinalIgnoreCase) -ge 0) "Active document '$path' must recognize CP106."
}
$manifest = Read-Manifest 'CHECKPOINT_106_SHA256SUMS.txt'
$actual = Get-Cp106RepositoryOwnedFileSet
Assert-True ($actual.Count -eq $manifest.EntryCount) "CP106 manifest count $($manifest.EntryCount) does not match repository-owned file count $($actual.Count)."
foreach ($relative in $manifest.Entries.Keys) {
    Assert-True ($actual.ContainsKey([string]$relative)) "CP106 manifest lists missing path '$relative'."
    Assert-True ((Hash-Rel ([string]$relative)) -eq [string]$manifest.Entries[[string]$relative]) "CP106 manifest hash mismatch for '$relative'."
}
foreach ($relative in $actual.Keys) {
    Assert-True ($manifest.Entries.ContainsKey([string]$relative)) "Repository-owned path '$relative' is missing from CP106 manifest."
}

Write-Host "       CP106 contract verified: $($manifest.EntryCount) repository-owned files; 10 disciplines / 32 lineages / $($beats.Count) beats / 136 ideas / 20 foundation domains / 195 observations; zero trials; zero numerical TL-table change."
