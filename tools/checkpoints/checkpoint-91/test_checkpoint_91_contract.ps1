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

Write-Host '       Validating native-dependency declarations...'
$guard=RelPath 'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1'
$normalRel='tools/calibration/checkpoints/checkpoint-91.json'; $deepRel='tools/calibration/checkpoints/checkpoint-91-deep-calibration.json'
$guardedPs=@('tools/checkpoints/Test-NativeAcceptanceDependencies.ps1','tools/checkpoints/checkpoint-91/apply_checkpoint_91.ps1','tools/checkpoints/checkpoint-91/test_checkpoint_91_contract.ps1','tools/calibration/run_calibration_checkpoint.ps1')
& $guard -RepositoryRoot $repositoryRoot -PowerShellPaths $guardedPs -CheckpointDefinitionPaths @($normalRel,$deepRel)
$applyText=Read-Text 'tools/checkpoints/checkpoint-91/apply_checkpoint_91.ps1'
$provenHarnessCall='& $harness -CheckpointDefinition $definition -Trials $Trials -Jobs $Jobs -RepositoryOnly:$RepositoryOnly -NoClean:$NoClean'
Require-Contains $applyText $provenHarnessCall 'Checkpoint 91 wrapper must preserve the proven direct named-parameter harness invocation.'
Assert-True (-not [regex]::IsMatch($applyText,'&\s+\$harness\s+@[A-Za-z_][A-Za-z0-9_]*',[System.Text.RegularExpressions.RegexOptions]::IgnoreCase)) 'Checkpoint 91 wrapper must not invoke the calibration harness through splatted arguments.'
$guardText=Read-Text 'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1'
Require-Contains $guardText 'Assert-ProvenCheckpointHarnessInvocation' 'Native dependency/archive precheck must validate the checkpoint-wrapper harness interface.'
Require-Contains $guardText 'array splatting can silently become positional binding' 'Native dependency/archive precheck must explain the array-splat positional-binding failure mode.'

Write-Host '       Validating Checkpoint 91 deterministic workload and documentation-only scope...'
$normal=Read-Json $normalRel; $deep=Read-Json $deepRel
Assert-True ([string]$normal.checkpointId -eq '91' -and [string]$deep.checkpointId -eq '91') 'Checkpoint 91 definition ID mismatch.'
Assert-True ([string]$normal.manifestFile -eq 'CHECKPOINT_91_SHA256SUMS.txt' -and [string]$deep.manifestFile -eq 'CHECKPOINT_91_SHA256SUMS.txt') 'Checkpoint 91 manifest binding mismatch.'
Assert-True (@($normal.stages).Count -eq 8 -and [int]$normal.checkpointMetrics.stageCount -eq 8) 'Checkpoint 91 normal definition must contain exactly 8 deterministic stages.'
Assert-True (@($deep.stages).Count -eq 8 -and [int]$deep.checkpointMetrics.stageCount -eq 8) 'Checkpoint 91 deep definition must contain the same 8 deterministic stages.'
foreach($d in @($normal,$deep)){
    Assert-True ([int]$d.checkpointMetrics.monteCarloVariantCount -eq 0 -and [long]$d.checkpointMetrics.trialsAtDefault -eq 0 -and [long]$d.checkpointMetrics.totalTrialExecutionsAtDefault -eq 0) 'Checkpoint 91 must not declare Monte Carlo workload.'
    Assert-True (-not [bool]$d.checkpointMetrics.deepCalibrationApplicable) 'Checkpoint 91 must declare Deep Calibration not applicable.'
    $ids=@($d.stages | ForEach-Object { [string]$_.id })
    foreach($id in @('deterministic','tl1-phase-a','tl1-phase-b','tl1-installation-space-envelope','tl1-sensor-ew-foundation','auxiliary-resource-endurance','checkpoint-53-resource-semantics-lock','runner-self-tests')){ Assert-True ($ids -contains $id) "Checkpoint 91 is missing deterministic stage '$id'." }
    Assert-True (-not ($ids -contains 'cross-tl-build-permutation-screening')) 'Checkpoint 91 must not rerun the CP90 generalized Monte Carlo screen.'
    $self=@($d.stages | Where-Object { [string]$_.id -eq 'runner-self-tests' }); Assert-True ($self.Count -eq 1 -and [int]$self[0].metrics.selfTestCount -eq 56) 'Checkpoint 91 must expect 56 unchanged ScenarioRunner self-tests.'
}
$docPaths=@($normal.documentation | ForEach-Object { [string]$_ })
foreach($rel in @('docs/references/reference-mining/README.md','docs/references/reference-mining/source-index.json','docs/references/reference-mining/observation-index.json','docs/references/reference-mining/cross-source-themes.md','docs/validation/Checkpoint_91_External_Reference_Mining_Architecture_And_Initial_Spacedock_Design_Corpus.md','docs/validation/evidence/checkpoint-90a/CHECKPOINT_90a_SHA256SUMS.txt','docs/validation/evidence/checkpoint-90a/checkpoint-90a-native-acceptance-provenance.json')){ Assert-True ($docPaths -contains $rel) "Checkpoint 91 documentation declarations are missing '$rel'." }

Write-Host '       Validating accepted CP90a provenance and frozen implementation/game authorities...'
$cp90aManifestRel='docs/validation/evidence/checkpoint-90a/CHECKPOINT_90a_SHA256SUMS.txt'
$cp90aRecord=Read-Manifest $cp90aManifestRel
Assert-True ([int]$cp90aRecord.PhysicalLineCount -eq 1741 -and [int]$cp90aRecord.EntryCount -eq 1741) 'Accepted CP90a evidence manifest must contain exactly 1,741 unique entries.'
Assert-True ((Hash-Rel $cp90aManifestRel) -eq '8637eb74b97b2f6e5bea67e2c727b5650b6e5e2b1ca80a7b7b9cd54ac6c0ce2c') 'Embedded CP90a evidence manifest bytes do not match accepted CP90a.'
$prov=Read-Json 'docs/validation/evidence/checkpoint-90a/checkpoint-90a-native-acceptance-provenance.json'
Assert-True ([string]$prov.status -eq 'Success' -and [string]$prov.checkpointDefinitionSha256 -eq 'eabd5d18f695b5a7244e23dd4d1f85a76d2719bb2d010d4ea530d9ee71c3f7af' -and [string]$prov.checkpointManifestSha256 -eq '8637eb74b97b2f6e5bea67e2c727b5650b6e5e2b1ca80a7b7b9cd54ac6c0ce2c') 'CP90a native provenance hash/status mismatch.'
Assert-True ([int]$prov.tests.passed -eq 863 -and [int]$prov.runner.passedStages -eq 13 -and [int]$prov.runner.selfTests -eq 56 -and [int]$prov.runner.failedGates -eq 0) 'CP90a native provenance build/test/runner summary mismatch.'
Assert-True ([string]$prov.primaryStudy.summarySha256 -eq '0d9a66194c18ca7897405bd34d2190038df75531ba8060430666ea6b39a88854' -and [long]$prov.primaryStudy.substantiveTrials -eq 4320000 -and [int]$prov.primaryStudy.smokeTrials -eq 432) 'CP90a substantive provenance mismatch.'
$cp90a=$cp90aRecord.Entries
$frozen=0
foreach($rel in @($cp90a.Keys)){
    $freeze=$false
    if($rel.StartsWith('src/',[System.StringComparison]::Ordinal) -or $rel.StartsWith('tests/',[System.StringComparison]::Ordinal)){ $freeze=$true }
    elseif($rel -eq 'StarCluster.Calibration.sln' -or $rel -eq 'global.json'){ $freeze=$true }
    elseif($rel -eq 'docs/Star_Cluster_Game_Concept_v0.6z.docx'){ $freeze=$true }
    elseif($rel.StartsWith('docs/design/player_technology/',[System.StringComparison]::Ordinal)){ $freeze=$true }
    elseif($rel.StartsWith('docs/development/',[System.StringComparison]::Ordinal)){ $freeze=$true }
    elseif($rel.StartsWith('docs/design/ai/',[System.StringComparison]::Ordinal)){ $freeze=$true }
    elseif($rel -eq 'docs/design/testing/Technology_Integration_Permutation_Suite_Architecture_v0_9.md' -or $rel -eq 'docs/design/testing/technology_integration_permutation_suite_v0_9.json'){ $freeze=$true }
    elseif($rel.StartsWith('docs/references/',[System.StringComparison]::Ordinal) -and $rel -ne 'docs/references/README.md'){ $freeze=$true }
    if($freeze){
        Assert-True ((Hash-Rel $rel) -eq [string]$cp90a[$rel]) "Checkpoint 91 changed frozen accepted CP90a file '$rel'."
        $frozen++
    }
}
Assert-True ($frozen -eq 593) "Checkpoint 91 frozen CP90a audit covered $frozen files; expected 593."

Write-Host '       Validating reference-mining source and observation corpus...'
$rmReadme=Read-Text 'docs/references/reference-mining/README.md'
foreach($needle in @('Source -> Mined Observation -> Candidate Discussion -> Human Design Decision -> Appropriate Authority','does **not** become a Star Cluster rule','Adopted','Deduplicate')){ Require-Contains $rmReadme $needle "Reference-mining README is missing authority/lifecycle text '$needle'." }
$sourceIndex=Read-Json 'docs/references/reference-mining/source-index.json'
$obsIndex=Read-Json 'docs/references/reference-mining/observation-index.json'
Assert-True ([string]$sourceIndex.id -eq 'external-reference-mining-source-index-v1' -and [string]$sourceIndex.authority -eq 'reference_only') 'Reference-mining source index identity/authority mismatch.'
Assert-True ([int]$sourceIndex.minedSourceCount -eq 6 -and [int]$sourceIndex.queuedSourceCount -eq 24 -and [int]$sourceIndex.sourceCount -eq 30 -and @($sourceIndex.sources).Count -eq 30) 'Reference-mining source counts mismatch.'
Assert-True ([string]$obsIndex.id -eq 'external-reference-mining-observation-index-v1' -and [string]$obsIndex.authority -eq 'reference_only' -and [int]$obsIndex.observationCount -eq 70 -and @($obsIndex.observations).Count -eq 70) 'Reference-mining observation count/authority mismatch.'
$allowedRelationships=@('corroborates_existing','new_candidate','extends_candidate','conflicts_or_warns','context_only')
$allowedDispositions=@('retain_reference','discuss','defer','out_of_scope','reject','adopted')
$sourceMap=@{}; $dedupCount=0; $minedCount=0; $queuedCount=0
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
        Assert-True ($null -eq $s.transcriptPath -and $null -eq $s.notePath) "Queued source '$sid' must not pretend to have transcript/note content."
    } else { throw "Reference source '$sid' has unsupported status '$($s.status)'." }
    if($null -ne $s.PSObject.Properties['deduplicationRequired'] -and [bool]$s.deduplicationRequired){ $dedupCount++ }
}
Assert-True ($minedCount -eq 6 -and $queuedCount -eq 24 -and $dedupCount -eq 13) 'Reference source mined/queued/dedup counts mismatch.'
foreach($sid in @('SD-DC','SD-NL','SD-EW','SD-SM','SD-SW','SD-SG')){ Assert-True ($sourceMap.ContainsKey($sid) -and [string]$sourceMap[$sid].status -eq 'mined') "Initial mined source '$sid' is missing." }
$seenObs=@{}; $adopted=0; $discuss=0
foreach($o in @($obsIndex.observations)){
    $oid=[string]$o.id; Assert-True (-not [string]::IsNullOrWhiteSpace($oid) -and -not $seenObs.ContainsKey($oid)) "Observation ID '$oid' is blank or duplicated."; $seenObs[$oid]=$true
    $sid=[string]$o.sourceId; Assert-True ($sourceMap.ContainsKey($sid) -and [string]$sourceMap[$sid].status -eq 'mined') "Observation '$oid' references unknown/unmined source '$sid'."
    Assert-True ($allowedRelationships -contains [string]$o.relationship) "Observation '$oid' has unsupported relationship '$($o.relationship)'."
    Assert-True ($allowedDispositions -contains [string]$o.disposition) "Observation '$oid' has unsupported disposition '$($o.disposition)'."
    Assert-True (@($o.tags).Count -gt 0 -and @($o.projectAreas).Count -gt 0) "Observation '$oid' must carry tags/project areas."
    Assert-True ([string]$o.authorityEffect -eq 'none_unless_explicitly_adopted_elsewhere') "Observation '$oid' authority effect drifted."
    if([string]$o.disposition -eq 'adopted'){ $adopted++ }
    if([string]$o.disposition -eq 'discuss'){ $discuss++ }
}
Assert-True ($adopted -eq 0) 'Checkpoint 91 must not newly adopt any mined observation.'
Assert-True ($discuss -gt 30) 'Checkpoint 91 should preserve the substantial candidate-discussion queue identified in the mining session.'

# Ensure every observation ID is represented in its source note without relying on prose order.
foreach($sid in @('SD-DC','SD-NL','SD-EW','SD-SM','SD-SW','SD-SG')){
    $noteText=Read-Text ([string]$sourceMap[$sid].notePath)
    $sourceObs=@($obsIndex.observations | Where-Object { [string]$_.sourceId -eq $sid })
    foreach($o in $sourceObs){ Require-Contains $noteText ([string]$o.id) "Source note for '$sid' is missing observation '$($o.id)'." }
}
$perSourceExpected=@{'SD-DC'=10;'SD-NL'=10;'SD-EW'=10;'SD-SM'=11;'SD-SW'=19;'SD-SG'=10}
foreach($sid in @($perSourceExpected.Keys)){ $c=@($obsIndex.observations | Where-Object { [string]$_.sourceId -eq $sid }).Count; Assert-True ($c -eq [int]$perSourceExpected[$sid]) "Observation count for '$sid' is $c; expected $($perSourceExpected[$sid])." }

Write-Host '       Validating reference-mining corpus hash manifest and cross-source synthesis...'
$rmManifestRel='docs/references/reference-mining/SHA256SUMS.txt'; $rmManifest=Read-Manifest $rmManifestRel
Assert-True ([int]$rmManifest.EntryCount -eq 16) 'Reference-mining SHA256SUMS must contain exactly 16 corpus files excluding itself.'
foreach($rel in @($rmManifest.Entries.Keys)){
    $fullRel='docs/references/reference-mining/' + [string]$rel
    Assert-True ((Hash-Rel $fullRel) -eq [string]$rmManifest.Entries[$rel]) "Reference-mining corpus hash mismatch for '$rel'."
}
$themes=Read-Text 'docs/references/reference-mining/cross-source-themes.md'
foreach($needle in @('Qualitative technology progression','Architectural technology breakthroughs','Preserve weapon-family identity','Engagement envelope is a systems interaction','Specialized counterplay','Model engineering consequences','Rare weapons should be events','not Star Cluster rules')){ Require-Contains $themes $needle "Cross-source themes are missing '$needle'." }

Write-Host '       Validating current documentation authority and hygiene...'
Assert-True (-not (Test-Path -LiteralPath (RelPath 'docs/checkpoints'))) 'The obsolete docs/checkpoints tree must remain absent.'
Assert-ExactFileSet 'docs/design/testing' @('Checkpoint_91_Validation_Tiers.md','README.md','Technology_Integration_Permutation_Suite_Architecture_v0_9.md','checkpoint_91_validation_suite_policy_v0_1.json','technology_integration_permutation_suite_v0_9.json')
Assert-ExactFileSet 'docs/references/reference-mining' @('README.md','SHA256SUMS.txt','cross-source-themes.md','observation-index.json','source-index.json')
Assert-ExactFileSet 'docs/references/reference-mining/spacedock/transcripts' @('spacedock_damage_control.md','spacedock_energy_weapons.md','spacedock_nuclear_lasers.md','spacedock_space_weapons_compilation.md','spacedock_spinal_mounts.md','spacedock_spin_gravity.md')
Assert-ExactFileSet 'docs/references/reference-mining/spacedock/notes' @('damage-control.md','energy-weapons.md','nuclear-lasers.md','space-weapons-compilation.md','spinal-mounts.md','spin-gravity.md')
$activeConcepts=@(Get-ChildItem -LiteralPath (RelPath 'docs') -File -Filter 'Star_Cluster_Game_Concept_v*.docx'); Assert-True ($activeConcepts.Count -eq 1 -and $activeConcepts[0].Name -eq 'Star_Cluster_Game_Concept_v0.6z.docx') 'Concept authority must remain exactly v0.6z.'
$activeValidation=@(Get-ChildItem -LiteralPath (RelPath 'docs/validation') -File -Filter 'Checkpoint_*.md'); Assert-True ($activeValidation.Count -eq 1 -and $activeValidation[0].Name -eq 'Checkpoint_91_External_Reference_Mining_Architecture_And_Initial_Spacedock_Design_Corpus.md') 'Exactly one active CP91 validation runbook must remain.'
$activeAi=@(Get-ChildItem -LiteralPath (RelPath 'docs/design/ai') -File -Filter 'AI_Doctrine_Registry_Architecture_v*.md'); Assert-True ($activeAi.Count -eq 1 -and $activeAi[0].Name -eq 'AI_Doctrine_Registry_Architecture_v0_5.md') 'Exactly one active AI Doctrine Architecture v0.5 must remain.'
foreach($rel in @('docs/validation/archive/Checkpoint_90a_CP90_Native_Nullable_Generated_Build_Lookup_Hotfix.md','docs/archive/testing/Checkpoint_90_Validation_Tiers.md','docs/archive/testing/checkpoint_90_validation_suite_policy_v0_1.json')){ Assert-True (Test-Path -LiteralPath (RelPath $rel) -PathType Leaf) "Expected archived CP90/90a artifact '$rel' is missing." }
Assert-True ((Hash-Rel 'docs/validation/archive/Checkpoint_90a_CP90_Native_Nullable_Generated_Build_Lookup_Hotfix.md') -eq [string]$cp90a['docs/validation/Checkpoint_90a_CP90_Native_Nullable_Generated_Build_Lookup_Hotfix.md']) 'Archived CP90a validation runbook must remain byte-identical to accepted CP90a.'
Assert-True ((Hash-Rel 'docs/archive/testing/Checkpoint_90_Validation_Tiers.md') -eq [string]$cp90a['docs/design/testing/Checkpoint_90_Validation_Tiers.md']) 'Archived CP90 validation tiers must remain byte-identical to accepted CP90a.'
Assert-True ((Hash-Rel 'docs/archive/testing/checkpoint_90_validation_suite_policy_v0_1.json') -eq [string]$cp90a['docs/design/testing/checkpoint_90_validation_suite_policy_v0_1.json']) 'Archived CP90 validation policy must remain byte-identical to accepted CP90a.'
$docsReadme=Read-Text 'docs/README.md'; Require-Contains $docsReadme 'references/reference-mining/README.md' 'docs/README must navigate to reference mining.'; Require-Contains $docsReadme 'Reference-mining material is **not** game authority' 'docs/README must state the reference-mining authority boundary.'
$chat=Read-Text 'CHAT_README.md'; Require-Contains $chat 'docs/references/reference-mining/README.md' 'CHAT_README must bootstrap external reference mining.'; Require-Contains $chat 'External reference-mining corpus' 'CHAT_README authority table must include reference mining.'
$refReadme=Read-Text 'docs/references/README.md'; Require-Contains $refReadme 'Active external reference mining' 'Reference library README must point to the active mining corpus.'
$rootReadme=Read-Text 'README.md'; Require-Contains $rootReadme 'Checkpoint 91' 'Root README must identify Checkpoint 91.'; Require-Contains $rootReadme 'direct named-parameter' 'Root README must document the proven harness invocation guard.'
Require-Contains $chat 'proven direct named-parameter' 'CHAT_README must require proven checkpoint-wrapper harness invocation patterns.'
Require-Contains $chat 'full-repository archive' 'CHAT_README must preserve full-repository checkpoint delivery discipline.'
$activeValidationText=Read-Text 'docs/validation/Checkpoint_91_External_Reference_Mining_Architecture_And_Initial_Spacedock_Design_Corpus.md'
Assert-True (-not [regex]::IsMatch($activeValidationText,'[\x00-\x08\x0B\x0C\x0E-\x1F]')) 'Active Checkpoint 91 validation runbook contains unexpected ASCII control characters.'
Require-Contains $activeValidationText '.\tools\checkpoints\checkpoint-91\apply_checkpoint_91.ps1 -RepositoryOnly' 'Checkpoint 91 validation runbook must contain the literal repository-only native command.'
$tiersText=Read-Text 'docs/design/testing/Checkpoint_91_Validation_Tiers.md'; Require-Contains $tiersText 'proven direct named-parameter' 'Checkpoint 91 validation tiers must include the wrapper-to-harness pre-check.'
$policy=Read-Json 'docs/design/testing/checkpoint_91_validation_suite_policy_v0_1.json'
Assert-True ([string]$policy.checkpoint -eq '91' -and -not [bool]$policy.monteCarlo.required -and -not [bool]$policy.deepCalibration.applicable -and [int]$policy.referenceMining.observationCount -eq 70) 'Checkpoint 91 validation policy mismatch.'

Write-Host 'Checkpoint 91 repository contracts passed (reference-mining corpus preserved; CP90a gameplay/simulation authority unchanged).'
