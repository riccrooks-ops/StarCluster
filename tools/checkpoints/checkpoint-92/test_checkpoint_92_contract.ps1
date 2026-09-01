[CmdletBinding()]
param(
    [string]$RepositoryRoot
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($RepositoryRoot)) {
    $repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
} else {
    $repositoryRoot = (Resolve-Path $RepositoryRoot).Path
}

function Assert-True { param([bool]$Condition,[string]$Message) if (-not $Condition) { throw $Message } }
function RelPath { param([string]$RelativePath) return (Join-Path $repositoryRoot ($RelativePath.Replace('/','\'))) }
function Read-Text { param([string]$RelativePath) $p=RelPath $RelativePath; Assert-True (Test-Path -LiteralPath $p -PathType Leaf) "Required file '$RelativePath' is missing."; return [System.IO.File]::ReadAllText($p) }
function Read-Json { param([string]$RelativePath) return ((Read-Text $RelativePath) | ConvertFrom-Json) }
function Hash-Rel { param([string]$RelativePath) $p=RelPath $RelativePath; Assert-True (Test-Path -LiteralPath $p -PathType Leaf) "Hash target '$RelativePath' is missing."; return (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant() }
function Require-Contains { param([string]$Text,[string]$Needle,[string]$Message) Assert-True ($Text.IndexOf($Needle,[System.StringComparison]::OrdinalIgnoreCase) -ge 0) $Message }
function Has-Property { param($Object,[string]$Name) return ($null -ne $Object -and $null -ne $Object.PSObject.Properties[$Name]) }
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

Write-Host '       Validating native-dependency declarations and proven wrapper interface...'
$guard=RelPath 'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1'
$normalRel='tools/calibration/checkpoints/checkpoint-92.json'; $deepRel='tools/calibration/checkpoints/checkpoint-92-deep-calibration.json'
$guardedPs=@('tools/checkpoints/Test-NativeAcceptanceDependencies.ps1','tools/checkpoints/checkpoint-92/apply_checkpoint_92.ps1','tools/checkpoints/checkpoint-92/test_checkpoint_92_contract.ps1','tools/calibration/run_calibration_checkpoint.ps1')
& $guard -RepositoryRoot $repositoryRoot -PowerShellPaths $guardedPs -CheckpointDefinitionPaths @($normalRel,$deepRel)
$applyText=Read-Text 'tools/checkpoints/checkpoint-92/apply_checkpoint_92.ps1'
$provenHarnessCall='& $harness -CheckpointDefinition $definition -Trials $Trials -Jobs $Jobs -RepositoryOnly:$RepositoryOnly -NoClean:$NoClean'
Require-Contains $applyText $provenHarnessCall 'Checkpoint 92 wrapper must preserve the proven direct named-parameter harness invocation.'
Assert-True (-not [regex]::IsMatch($applyText,'&\s+\$harness\s+@[A-Za-z_][A-Za-z0-9_]*',[System.Text.RegularExpressions.RegexOptions]::IgnoreCase)) 'Checkpoint 92 wrapper must not invoke the calibration harness through splatted arguments.'
$guardText=Read-Text 'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1'
Require-Contains $guardText 'Assert-ProvenCheckpointHarnessInvocation' 'Native dependency/archive precheck must validate the checkpoint-wrapper harness interface.'
Require-Contains $guardText 'array splatting can silently become positional binding' 'Native dependency/archive precheck must explain the array-splat positional-binding failure mode.'

Write-Host '       Validating Checkpoint 92 deterministic workload and reference-only scope...'
$normal=Read-Json $normalRel; $deep=Read-Json $deepRel
Assert-True ([string]$normal.checkpointId -eq '92' -and [string]$deep.checkpointId -eq '92') 'Checkpoint 92 definition ID mismatch.'
Assert-True ([string]$normal.manifestFile -eq 'CHECKPOINT_92_SHA256SUMS.txt' -and [string]$deep.manifestFile -eq 'CHECKPOINT_92_SHA256SUMS.txt') 'Checkpoint 92 manifest binding mismatch.'
Assert-True (@($normal.stages).Count -eq 8 -and [int]$normal.checkpointMetrics.stageCount -eq 8) 'Checkpoint 92 normal definition must contain exactly 8 deterministic stages.'
Assert-True (@($deep.stages).Count -eq 8 -and [int]$deep.checkpointMetrics.stageCount -eq 8) 'Checkpoint 92 deep definition must contain the same 8 deterministic stages.'
foreach($d in @($normal,$deep)){
    Assert-True ([int]$d.checkpointMetrics.monteCarloVariantCount -eq 0 -and [long]$d.checkpointMetrics.trialsAtDefault -eq 0 -and [long]$d.checkpointMetrics.totalTrialExecutionsAtDefault -eq 0) 'Checkpoint 92 must not declare Monte Carlo workload.'
    Assert-True (-not [bool]$d.checkpointMetrics.deepCalibrationApplicable) 'Checkpoint 92 must declare Deep Calibration not applicable.'
    Assert-True ([bool]$d.checkpointMetrics.documentationReferenceOnly) 'Checkpoint 92 must remain documentation/reference-only.'
    $ids=@($d.stages | ForEach-Object { [string]$_.id })
    foreach($id in @('deterministic','tl1-phase-a','tl1-phase-b','tl1-installation-space-envelope','tl1-sensor-ew-foundation','auxiliary-resource-endurance','checkpoint-53-resource-semantics-lock','runner-self-tests')){ Assert-True ($ids -contains $id) "Checkpoint 92 is missing deterministic stage '$id'." }
    Assert-True (-not ($ids -contains 'cross-tl-build-permutation-screening')) 'Checkpoint 92 must not rerun the CP90 generalized Monte Carlo screen.'
    $self=@($d.stages | Where-Object { [string]$_.id -eq 'runner-self-tests' }); Assert-True ($self.Count -eq 1 -and [int]$self[0].metrics.selfTestCount -eq 56) 'Checkpoint 92 must expect 56 unchanged ScenarioRunner self-tests.'
}
$docPaths=@($normal.documentation | ForEach-Object { [string]$_ })
foreach($rel in @('docs/references/reference-mining/README.md','docs/references/reference-mining/source-index.json','docs/references/reference-mining/observation-index.json','docs/references/reference-mining/cross-source-themes.md','docs/validation/Checkpoint_92_Expanded_Spacedock_Reference_Corpus_And_Completed_Queue.md','docs/validation/evidence/checkpoint-91/CHECKPOINT_91_SHA256SUMS.txt','docs/validation/evidence/checkpoint-91/checkpoint-91-native-acceptance-provenance.json')){ Assert-True ($docPaths -contains $rel) "Checkpoint 92 documentation declarations are missing '$rel'." }

Write-Host '       Validating accepted Checkpoint 91 provenance and frozen implementation/game authorities...'
$cp91ManifestRel='docs/validation/evidence/checkpoint-91/CHECKPOINT_91_SHA256SUMS.txt'
$cp91Record=Read-Manifest $cp91ManifestRel
Assert-True ([int]$cp91Record.PhysicalLineCount -eq 1767 -and [int]$cp91Record.EntryCount -eq 1767) 'Accepted CP91 evidence manifest must contain exactly 1,767 unique entries.'
Assert-True ((Hash-Rel $cp91ManifestRel) -eq 'a35d727be7e1ca4ea03c96efcb7fcc4ae614e4beb5772c62c0eb4714d0c899e4') 'Embedded CP91 evidence manifest bytes do not match accepted CP91.'
$prov=Read-Json 'docs/validation/evidence/checkpoint-91/checkpoint-91-native-acceptance-provenance.json'
Assert-True ([string]$prov.status -eq 'Success' -and [string]$prov.checkpointDefinitionSha256 -eq 'f7a6ab0daba09999e4cc4e8868950624b5500321549c40256efbc9c30e180bde' -and [string]$prov.checkpointManifestSha256 -eq 'a35d727be7e1ca4ea03c96efcb7fcc4ae614e4beb5772c62c0eb4714d0c899e4') 'CP91 native provenance hash/status mismatch.'
Assert-True ([int]$prov.tests.passed -eq 863 -and [int]$prov.runner.passedStages -eq 8 -and [int]$prov.runner.selfTests -eq 56 -and [int]$prov.runner.failedGates -eq 0) 'CP91 native provenance build/test/runner summary mismatch.'
Assert-True ([int]$prov.monteCarlo.variantCount -eq 0 -and [long]$prov.monteCarlo.totalTrials -eq 0) 'CP91 provenance must record no Monte Carlo workload.'
$cp91=$cp91Record.Entries
$frozen=0
foreach($rel in @($cp91.Keys)){
    $freeze=$false
    if($rel.StartsWith('src/',[System.StringComparison]::Ordinal) -or $rel.StartsWith('tests/',[System.StringComparison]::Ordinal)){ $freeze=$true }
    elseif($rel -eq 'StarCluster.Calibration.sln' -or $rel -eq 'StarCluster.sln' -or $rel -eq 'global.json'){ $freeze=$true }
    elseif($rel -eq 'docs/Star_Cluster_Game_Concept_v0.6z.docx'){ $freeze=$true }
    elseif($rel.StartsWith('docs/design/player_technology/',[System.StringComparison]::Ordinal)){ $freeze=$true }
    elseif($rel.StartsWith('docs/development/',[System.StringComparison]::Ordinal)){ $freeze=$true }
    elseif($rel.StartsWith('docs/design/ai/',[System.StringComparison]::Ordinal)){ $freeze=$true }
    elseif($rel -eq 'docs/design/testing/Technology_Integration_Permutation_Suite_Architecture_v0_9.md' -or $rel -eq 'docs/design/testing/technology_integration_permutation_suite_v0_9.json'){ $freeze=$true }
    elseif($rel.StartsWith('docs/references/',[System.StringComparison]::Ordinal) -and $rel -ne 'docs/references/README.md' -and -not $rel.StartsWith('docs/references/reference-mining/',[System.StringComparison]::Ordinal)){ $freeze=$true }
    if($freeze){
        Assert-True ((Hash-Rel $rel) -eq [string]$cp91[$rel]) "Checkpoint 92 changed frozen accepted CP91 file '$rel'."
        $frozen++
    }
}
Assert-True ($frozen -eq 594) "Checkpoint 92 frozen CP91 audit covered $frozen files; expected 594."
foreach($rel in @('CHAT_README.md','tools/checkpoints/Test-NativeAcceptanceDependencies.ps1','tools/calibration/run_calibration_checkpoint.ps1')){ Assert-True ((Hash-Rel $rel) -eq [string]$cp91[$rel]) "Checkpoint 92 changed proven CP91 bootstrap/native-acceptance file '$rel'." }

Write-Host '       Validating completed Checkpoint 91 reference-mining queue and deduplication contracts...'
$rmReadme=Read-Text 'docs/references/reference-mining/README.md'
foreach($needle in @('Source -> Mined Observation -> Candidate Discussion -> Human Design Decision -> Appropriate Authority','does **not** become a Star Cluster rule','extends CP91','zero duplicate observation IDs','Source IDs are stable')){ Require-Contains $rmReadme $needle "Reference-mining README is missing architecture text '$needle'." }
$sourceIndex=Read-Json 'docs/references/reference-mining/source-index.json'
$obsIndex=Read-Json 'docs/references/reference-mining/observation-index.json'
Assert-True ([int]$sourceIndex.schemaVersion -eq 1 -and [string]$sourceIndex.id -eq 'external-reference-mining-source-index-v1' -and [string]$sourceIndex.checkpointIntroduced -eq '91' -and [string]$sourceIndex.authority -eq 'reference_only' -and [string]$sourceIndex.checkpointUpdated -eq '92') 'Reference-mining source index identity/schema/authority/update mismatch.'
Assert-True ([int]$sourceIndex.minedSourceCount -eq 30 -and [int]$sourceIndex.queuedSourceCount -eq 0 -and [int]$sourceIndex.sourceCount -eq 30 -and [int]$sourceIndex.completedQueueCount -eq 24 -and [int]$sourceIndex.reviewedDuplicateSourceCount -eq 16 -and [int]$sourceIndex.observationBearingSourceCount -eq 14 -and @($sourceIndex.sources).Count -eq 30) 'Reference-mining source counts mismatch.'
Assert-True ([int]$obsIndex.schemaVersion -eq 1 -and [string]$obsIndex.id -eq 'external-reference-mining-observation-index-v1' -and [string]$obsIndex.checkpointIntroduced -eq '91' -and [string]$obsIndex.authority -eq 'reference_only' -and [string]$obsIndex.checkpointUpdated -eq '92' -and [int]$obsIndex.observationCount -eq 195 -and @($obsIndex.observations).Count -eq 195) 'Reference-mining observation identity/schema/count/authority mismatch.'
$allowedRelationships=@('corroborates_existing','new_candidate','extends_candidate','conflicts_or_warns','context_only')
$allowedDispositions=@('retain_reference','discuss','defer','out_of_scope','reject','adopted')
$duplicateIds=@('SD-Q01','SD-Q02','SD-Q03','SD-Q04','SD-Q05','SD-Q07','SD-Q08','SD-Q11','SD-Q14','SD-Q16','SD-Q17','SD-Q18','SD-Q19','SD-Q20','SD-Q21','SD-Q22')
$newStandaloneIds=@('SD-Q06','SD-Q09','SD-Q10','SD-Q12','SD-Q13','SD-Q15','SD-Q23','SD-Q24')
$duplicateChapterExpected=@{
    'SD-Q01'=@{Chapter=19;Title='Range in Space Combat';Start='2:38:34'}; 'SD-Q02'=@{Chapter=18;Title='Kinetic vs Energy Weapons';Start='2:29:21'}; 'SD-Q03'=@{Chapter=17;Title='Radiation Weapons';Start='2:22:07'}; 'SD-Q04'=@{Chapter=16;Title='Turretted Weapons';Start='2:14:01'};
    'SD-Q05'=@{Chapter=15;Title='Mines';Start='2:05:57'}; 'SD-Q07'=@{Chapter=14;Title='Electromagnetic Weapons';Start='1:56:45'}; 'SD-Q08'=@{Chapter=13;Title='Advanced Laser Weapons';Start='1:48:01'}; 'SD-Q11'=@{Chapter=12;Title='Electronic Warfare';Start='1:38:29'};
    'SD-Q14'=@{Chapter=11;Title='Point Defence Weapons';Start='1:29:00'}; 'SD-Q16'=@{Chapter=8;Title='Macron Weapons';Start='1:02:33'}; 'SD-Q17'=@{Chapter=7;Title='Particle Weapons';Start='51:12'}; 'SD-Q18'=@{Chapter=6;Title='Laser Weapons';Start='40:41'};
    'SD-Q19'=@{Chapter=5;Title='Superweapons';Start='31:31'}; 'SD-Q20'=@{Chapter=4;Title='Nuclear Weapons';Start='21:39'}; 'SD-Q21'=@{Chapter=3;Title='Missile Weapons';Start='12:27'}; 'SD-Q22'=@{Chapter=2;Title='Kinetic Weapons';Start='1:24'}
}
$sourceMap=@{}; $dedupCount=0; $minedCount=0; $queuedCount=0; $obsSourceCount=0
foreach($s in @($sourceIndex.sources)){
    $sid=[string]$s.id; Assert-True (-not [string]::IsNullOrWhiteSpace($sid)) 'Reference source is missing an ID.'; Assert-True (-not $sourceMap.ContainsKey($sid)) "Reference source ID '$sid' is duplicated."; $sourceMap[$sid]=$s
    Assert-True ([string]$s.authority -eq 'reference_only') "Reference source '$sid' must remain reference_only."
    if([string]$s.status -eq 'mined'){
        $minedCount++
        Assert-True (-not [string]::IsNullOrWhiteSpace([string]$s.transcriptPath) -and -not [string]::IsNullOrWhiteSpace([string]$s.notePath)) "Mined source '$sid' must bind transcript and note paths."
        Assert-True ((Hash-Rel ([string]$s.transcriptPath)) -eq [string]$s.transcriptSha256) "Mined source '$sid' transcript hash mismatch."
        Assert-True (Test-Path -LiteralPath (RelPath ([string]$s.notePath)) -PathType Leaf) "Mined source '$sid' note is missing."
    } elseif([string]$s.status -eq 'queued'){
        $queuedCount++
    } else { throw "Reference source '$sid' has unsupported status '$($s.status)'." }
    if(@($s.observationIds).Count -gt 0){ $obsSourceCount++ }
    if(Has-Property $s 'deduplicationRequired' -and [bool]$s.deduplicationRequired){ $dedupCount++ }
}
Assert-True ($minedCount -eq 30 -and $queuedCount -eq 0 -and $dedupCount -eq 16 -and $obsSourceCount -eq 14) 'Reference source mined/queued/dedup/observation-bearing counts mismatch.'
foreach($i in 1..24){ $sid=('SD-Q{0:D2}' -f $i); Assert-True ($sourceMap.ContainsKey($sid) -and [string]$sourceMap[$sid].status -eq 'mined') "Former queue source '$sid' is not mined/reviewed." }
foreach($sid in $duplicateIds){
    $s=$sourceMap[$sid]; $exp=$duplicateChapterExpected[$sid]
    Assert-True ((Has-Property $s 'deduplicationRequired') -and [bool]$s.deduplicationRequired -and (Has-Property $s 'deduplicationReviewed') -and [bool]$s.deduplicationReviewed) "Duplicate source '$sid' is not fully marked for reviewed deduplication."
    Assert-True ([string]$s.contentRelationship -eq 'duplicate_of_mined_space_weapons_compilation_chapter' -and [string]$s.deduplicatedToSourceId -eq 'SD-SW') "Duplicate source '$sid' must point to SD-SW through the CP91 deduplication extension."
    Assert-True ([int]$s.deduplicatedChapter -eq [int]$exp['Chapter'] -and [string]$s.deduplicatedChapterTitle -eq [string]$exp['Title'] -and [string]$s.deduplicatedChapterStart -eq [string]$exp['Start']) "Duplicate source '$sid' chapter mapping drifted."
    Assert-True (@($s.observationIds).Count -eq 0) "Duplicate source '$sid' must create zero standalone observation IDs."
    Assert-True (@($s.mergedObservationIds).Count -gt 0) "Duplicate source '$sid' must reference the SD-SW observations used by its review."
}
foreach($sid in $newStandaloneIds){
    $s=$sourceMap[$sid]
    Assert-True (@($s.observationIds).Count -gt 0) "New standalone source '$sid' must carry observations."
    Assert-True ((Has-Property $s 'deduplicationReviewed') -and [bool]$s.deduplicationReviewed -and [string]$s.contentRelationship -eq 'standalone_nonduplicate_within_current_spacedock_corpus') "New standalone source '$sid' must record completed overlap review without a parallel status vocabulary."
}

$seenObs=@{}; $adopted=0; $discuss=0
foreach($o in @($obsIndex.observations)){
    $oid=[string]$o.id; Assert-True (-not [string]::IsNullOrWhiteSpace($oid) -and -not $seenObs.ContainsKey($oid)) "Observation ID '$oid' is blank or duplicated."; $seenObs[$oid]=$true
    $sid=[string]$o.sourceId; Assert-True ($sourceMap.ContainsKey($sid) -and [string]$sourceMap[$sid].status -eq 'mined') "Observation '$oid' references unknown/unmined source '$sid'."
    Assert-True ($allowedRelationships -contains [string]$o.relationship) "Observation '$oid' has unsupported relationship '$($o.relationship)'."
    Assert-True ($allowedDispositions -contains [string]$o.disposition) "Observation '$oid' has unsupported disposition '$($o.disposition)'."
    Assert-True (@($o.tags).Count -gt 0 -and @($o.projectAreas).Count -gt 0) "Observation '$oid' must carry tags/project areas."
    Assert-True ([string]$o.authorityEffect -eq 'none_unless_explicitly_adopted_elsewhere') "Observation '$oid' authority effect drifted."
    Assert-True (-not ($duplicateIds -contains $sid)) "Duplicate standalone source '$sid' must not own observation '$oid'."
    if([string]$o.disposition -eq 'adopted'){ $adopted++ }
    if([string]$o.disposition -eq 'discuss'){ $discuss++ }
}
Assert-True ($adopted -eq 0) 'Checkpoint 92 must not newly adopt any mined observation.'
Assert-True ($discuss -gt 70) 'Checkpoint 92 should preserve a substantial candidate-discussion queue.'
foreach($sid in @($sourceMap.Keys)){
    $noteText=Read-Text ([string]$sourceMap[$sid].notePath)
    $sourceObs=@($obsIndex.observations | Where-Object { [string]$_.sourceId -eq $sid })
    foreach($o in $sourceObs){ Require-Contains $noteText ([string]$o.id) "Source note for '$sid' is missing observation '$($o.id)'." }
    $declared=@($sourceMap[$sid].observationIds)
    Assert-True ($declared.Count -eq $sourceObs.Count) "Source '$sid' observationIds count does not match observation index."
    foreach($o in $sourceObs){ Assert-True ($declared -contains [string]$o.id) "Source '$sid' is missing declared observation '$($o.id)'." }
}
foreach($sid in $duplicateIds){ foreach($oid in @($sourceMap[$sid].mergedObservationIds)){ Assert-True ($seenObs.ContainsKey([string]$oid)) "Duplicate source '$sid' references missing merged observation '$oid'."; $mo=@($obsIndex.observations | Where-Object { [string]$_.id -eq [string]$oid }); Assert-True ($mo.Count -eq 1 -and [string]$mo[0].sourceId -eq 'SD-SW') "Duplicate source '$sid' merged observation '$oid' must belong to SD-SW." } }
$perSourceExpected=@{'SD-DC'=10;'SD-NL'=10;'SD-EW'=10;'SD-SM'=11;'SD-SW'=65;'SD-SG'=10;'SD-Q06'=8;'SD-Q09'=10;'SD-Q10'=10;'SD-Q12'=10;'SD-Q13'=9;'SD-Q15'=10;'SD-Q23'=11;'SD-Q24'=11}
foreach($sid in @($perSourceExpected.Keys)){ $c=@($obsIndex.observations | Where-Object { [string]$_.sourceId -eq $sid }).Count; Assert-True ($c -eq [int]$perSourceExpected[$sid]) "Observation count for '$sid' is $c; expected $($perSourceExpected[$sid])." }

Write-Host '       Validating reference-mining corpus hash manifest and cross-source synthesis...'
$rmManifestRel='docs/references/reference-mining/SHA256SUMS.txt'; $rmManifest=Read-Manifest $rmManifestRel
Assert-True ([int]$rmManifest.EntryCount -eq 64) 'Reference-mining SHA256SUMS must contain exactly 64 corpus files excluding itself.'
foreach($rel in @($rmManifest.Entries.Keys)){
    $fullRel='docs/references/reference-mining/' + [string]$rel
    Assert-True ((Hash-Rel $fullRel) -eq [string]$rmManifest.Entries[$rel]) "Reference-mining corpus hash mismatch for '$rel'."
}
$themes=Read-Text 'docs/references/reference-mining/cross-source-themes.md'
foreach($needle in @('Qualitative technology progression','Preserve weapon-family identity','Engagement envelope is a systems interaction','Model engineering consequences','Rare weapons should be events','Missile delivery, guidance and payload should remain separable','effective Ammo','Sensors, EW and stealth form an information ecology','FTL topology can populate the sector map','wormholes','not Star Cluster rules')){ Require-Contains $themes $needle "Cross-source themes are missing '$needle'." }
Require-Contains $themes 'Project-discussion candidate (not a source observation, not adopted)' 'PDS Ammo synthesis must be explicitly non-source and non-adopted.'
Require-Contains $themes 'even a low-TL ship can discover and exploit an extraordinary connection' 'FTL low-TL exploration synthesis is missing.'

Write-Host '       Validating current documentation authority and hygiene...'
Assert-True (-not (Test-Path -LiteralPath (RelPath 'docs/checkpoints'))) 'The obsolete docs/checkpoints tree must remain absent.'
Assert-ExactFileSet 'docs/design/testing' @('Checkpoint_92_Validation_Tiers.md','README.md','Technology_Integration_Permutation_Suite_Architecture_v0_9.md','checkpoint_92_validation_suite_policy_v0_1.json','technology_integration_permutation_suite_v0_9.json')
Assert-ExactFileSet 'docs/references/reference-mining' @('README.md','SHA256SUMS.txt','cross-source-themes.md','observation-index.json','source-index.json')
$expectedTranscriptNames=@($sourceIndex.sources | ForEach-Object { [System.IO.Path]::GetFileName([string]$_.transcriptPath) })
$expectedNoteNames=@($sourceIndex.sources | ForEach-Object { [System.IO.Path]::GetFileName([string]$_.notePath) })
Assert-ExactFileSet 'docs/references/reference-mining/spacedock/transcripts' $expectedTranscriptNames
Assert-ExactFileSet 'docs/references/reference-mining/spacedock/notes' $expectedNoteNames
$activeConcepts=@(Get-ChildItem -LiteralPath (RelPath 'docs') -File -Filter 'Star_Cluster_Game_Concept_v*.docx'); Assert-True ($activeConcepts.Count -eq 1 -and $activeConcepts[0].Name -eq 'Star_Cluster_Game_Concept_v0.6z.docx') 'Concept authority must remain exactly v0.6z.'
$activeValidation=@(Get-ChildItem -LiteralPath (RelPath 'docs/validation') -File -Filter 'Checkpoint_*.md'); Assert-True ($activeValidation.Count -eq 1 -and $activeValidation[0].Name -eq 'Checkpoint_92_Expanded_Spacedock_Reference_Corpus_And_Completed_Queue.md') 'Exactly one active CP92 validation runbook must remain.'
$activeAi=@(Get-ChildItem -LiteralPath (RelPath 'docs/design/ai') -File -Filter 'AI_Doctrine_Registry_Architecture_v*.md'); Assert-True ($activeAi.Count -eq 1 -and $activeAi[0].Name -eq 'AI_Doctrine_Registry_Architecture_v0_5.md') 'Exactly one active AI Doctrine Architecture v0.5 must remain.'
foreach($rel in @('docs/validation/archive/Checkpoint_91_External_Reference_Mining_Architecture_And_Initial_Spacedock_Design_Corpus.md','docs/archive/testing/Checkpoint_91_Validation_Tiers.md','docs/archive/testing/checkpoint_91_validation_suite_policy_v0_1.json')){ Assert-True (Test-Path -LiteralPath (RelPath $rel) -PathType Leaf) "Expected archived CP91 artifact '$rel' is missing." }
Assert-True ((Hash-Rel 'docs/validation/archive/Checkpoint_91_External_Reference_Mining_Architecture_And_Initial_Spacedock_Design_Corpus.md') -eq [string]$cp91['docs/validation/Checkpoint_91_External_Reference_Mining_Architecture_And_Initial_Spacedock_Design_Corpus.md']) 'Archived CP91 validation runbook must remain byte-identical to accepted CP91.'
Assert-True ((Hash-Rel 'docs/archive/testing/Checkpoint_91_Validation_Tiers.md') -eq [string]$cp91['docs/design/testing/Checkpoint_91_Validation_Tiers.md']) 'Archived CP91 validation tiers must remain byte-identical to accepted CP91.'
Assert-True ((Hash-Rel 'docs/archive/testing/checkpoint_91_validation_suite_policy_v0_1.json') -eq [string]$cp91['docs/design/testing/checkpoint_91_validation_suite_policy_v0_1.json']) 'Archived CP91 validation policy must remain byte-identical to accepted CP91.'
$docsReadme=Read-Text 'docs/README.md'; Require-Contains $docsReadme 'validation/Checkpoint_92_Expanded_Spacedock_Reference_Corpus_And_Completed_Queue.md' 'docs/README must point to active CP92 validation.'; Require-Contains $docsReadme 'Reference-mining material is **not** game authority' 'docs/README must state the reference-mining authority boundary.'
$chat=Read-Text 'CHAT_README.md'; Require-Contains $chat 'docs/references/reference-mining/README.md' 'CHAT_README must bootstrap external reference mining.'; Require-Contains $chat 'External reference-mining corpus' 'CHAT_README authority table must include reference mining.'; Require-Contains $chat 'proven direct named-parameter' 'CHAT_README must preserve proven checkpoint-wrapper harness invocation patterns.'; Require-Contains $chat 'full-repository archive' 'CHAT_README must preserve full-repository checkpoint delivery discipline.'
$refReadme=Read-Text 'docs/references/README.md'; Require-Contains $refReadme 'Checkpoint 92 completes that queue' 'Reference library README must describe the completed CP92 corpus.'
$testingReadme=Read-Text 'docs/design/testing/README.md'; Require-Contains $testingReadme 'checkpoint-92/apply_checkpoint_92.ps1' 'Testing README must point to CP92 wrapper.'
$rootReadme=Read-Text 'README.md'; Require-Contains $rootReadme 'Checkpoint 92' 'Root README must identify Checkpoint 92.'; Require-Contains $rootReadme 'direct named' 'Root README must document the proven harness invocation guard.'; Require-Contains $rootReadme '195 stable observations' 'Root README must summarize the expanded corpus.'
$activeValidationText=Read-Text 'docs/validation/Checkpoint_92_Expanded_Spacedock_Reference_Corpus_And_Completed_Queue.md'
Assert-True (-not [regex]::IsMatch($activeValidationText,'[\x00-\x08\x0B\x0C\x0E-\x1F]')) 'Active Checkpoint 92 validation runbook contains unexpected ASCII control characters.'
Require-Contains $activeValidationText '.\tools\checkpoints\checkpoint-92\apply_checkpoint_92.ps1 -RepositoryOnly' 'Checkpoint 92 validation runbook must contain the literal repository-only native command.'
$tiersText=Read-Text 'docs/design/testing/Checkpoint_92_Validation_Tiers.md'; Require-Contains $tiersText 'proven direct named-parameter' 'Checkpoint 92 validation tiers must include the wrapper-to-harness pre-check.'
$policy=Read-Json 'docs/design/testing/checkpoint_92_validation_suite_policy_v0_1.json'
Assert-True ([string]$policy.checkpoint -eq '92' -and -not [bool]$policy.monteCarlo.required -and -not [bool]$policy.deepCalibration.applicable -and [int]$policy.referenceMining.minedSourceCount -eq 30 -and [int]$policy.referenceMining.queuedSourceCount -eq 0 -and [int]$policy.referenceMining.reviewedDuplicateSourceCount -eq 16 -and [int]$policy.referenceMining.observationCount -eq 195) 'Checkpoint 92 validation policy mismatch.'
$rootTxt=@(Get-ChildItem -LiteralPath $repositoryRoot -File -Filter '*.txt'); Assert-True ($rootTxt.Count -eq 1 -and $rootTxt[0].Name -eq 'CHECKPOINT_92_SHA256SUMS.txt') 'Repository root must contain only CHECKPOINT_92_SHA256SUMS.txt as .txt.'

Write-Host 'Checkpoint 92 repository contracts passed (CP91 reference-mining architecture extended; queue completed; gameplay/simulation authority unchanged).'
