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
function Count-Substring {
    param([string]$Text, [string]$Needle)
    if ([string]::IsNullOrEmpty($Needle)) { return 0 }
    $count = 0
    $start = 0
    while (($start = $Text.IndexOf($Needle, $start, [System.StringComparison]::Ordinal)) -ge 0) {
        $count++
        $start += $Needle.Length
    }
    return $count
}
function Assert-FrozenFile {
    param([string]$RelativePath, [string]$ManifestText)
    $escaped = [regex]::Escape($RelativePath.Replace('\','/'))
    $match = [regex]::Match($ManifestText, "(?im)^([0-9a-f]{64})  $escaped$")
    Assert-True ($match.Success) "Accepted CP82a manifest does not contain '$RelativePath'."
    $path = Join-Path $repositoryRoot ($RelativePath.Replace('/','\'))
    Assert-True (Test-Path -LiteralPath $path -PathType Leaf) "Frozen CP82a file '$RelativePath' is missing."
    $actual = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    Assert-True ($actual -eq $match.Groups[1].Value.ToLowerInvariant()) "Checkpoint 83 unexpectedly changed frozen CP82a file '$RelativePath'."
}

Write-Host '       Validating native-dependency declarations...'
$guard = Join-Path $repositoryRoot 'tools\checkpoints\Test-NativeAcceptanceDependencies.ps1'
$normalRel = 'tools/calibration/checkpoints/checkpoint-83.json'
$deepRel = 'tools/calibration/checkpoints/checkpoint-83-deep-calibration.json'
$guardedPs = @(
    'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
    'tools/checkpoints/checkpoint-83/apply_checkpoint_83.ps1',
    'tools/checkpoints/checkpoint-83/test_checkpoint_83_contract.ps1',
    'tools/calibration/run_calibration_checkpoint.ps1'
)
$guardedDefs = @($normalRel, $deepRel)
& $guard -RepositoryRoot $repositoryRoot -PowerShellPaths $guardedPs -CheckpointDefinitionPaths $guardedDefs

Write-Host '       Validating Checkpoint 83 definitions and workload accounting...'
$normal = Read-Json $normalRel
$deep = Read-Json $deepRel
Assert-True ([string]$normal.checkpointId -eq '83' -and [string]$deep.checkpointId -eq '83') 'Checkpoint 83 definition ID mismatch.'
Assert-True ([string]$normal.manifestFile -eq 'CHECKPOINT_83_SHA256SUMS.txt' -and [string]$deep.manifestFile -eq 'CHECKPOINT_83_SHA256SUMS.txt') 'Checkpoint 83 manifest binding mismatch.'
Assert-True ([string]$normal.outputRoot -eq 'out/checkpoint-83' -and [string]$deep.outputRoot -eq 'out/checkpoint-83-deep-calibration') 'Checkpoint 83 output-root binding mismatch.'
Assert-True (@($normal.stages).Count -eq 11 -and [int]$normal.checkpointMetrics.stageCount -eq 11) 'Checkpoint 83 normal stage-count mismatch.'
Assert-True ([int]$normal.checkpointMetrics.monteCarloVariantCount -eq 96 -and [int]$normal.checkpointMetrics.trialsAtDefault -eq 960000 -and [int]$normal.checkpointMetrics.smokeVariantExecutions -eq 96 -and [int]$normal.checkpointMetrics.totalTrialExecutionsAtDefault -eq 960096) 'Checkpoint 83 normal workload mismatch.'
Assert-True (@($deep.stages).Count -eq 36 -and [int]$deep.checkpointMetrics.monteCarloVariantCount -eq 1790 -and [int]$deep.checkpointMetrics.trialsAtDefault -eq 17900000 -and [int]$deep.checkpointMetrics.smokeVariantExecutions -eq 246 -and [int]$deep.checkpointMetrics.totalTrialExecutionsAtDefault -eq 17900246) 'Checkpoint 83 Deep Calibration workload mismatch.'
$expectedNormal = @('deterministic','tl1-phase-a','tl1-phase-b','tl1-installation-space-envelope','tl1-sensor-ew-foundation','tl2-power-reactor-progression-permutation-preflight','tl2-power-reactor-progression-permutation-smoke','tl2-power-reactor-progression-permutations','auxiliary-resource-endurance','checkpoint-53-resource-semantics-lock','runner-self-tests')
$normalIds = @($normal.stages | ForEach-Object { [string]$_.id })
Assert-True (($normalIds -join '|') -eq ($expectedNormal -join '|')) 'Checkpoint 83 normal stage ordering mismatch.'
$self = @($normal.stages | Where-Object { [string]$_.id -eq 'runner-self-tests' })
Assert-True ($self.Count -eq 1 -and [int]$self[0].metrics.selfTestCount -eq 48) 'Checkpoint 83 must retain 48 ScenarioRunner self-tests.'
Assert-True ([string]$normal.primaryStudy.id -eq 'tl2-itc09-power-reactor-progression-permutations' -and [int]$normal.primaryStudy.variantCount -eq 96) 'Checkpoint 83 primary-study binding mismatch.'
Assert-True ((@($normal.nativeDependencyPrecheck.powerShellPaths) -join '|') -eq ($guardedPs -join '|')) 'Checkpoint 83 normal native-dependency PowerShell binding mismatch.'
Assert-True ((@($deep.nativeDependencyPrecheck.powerShellPaths) -join '|') -eq ($guardedPs -join '|')) 'Checkpoint 83 deep native-dependency PowerShell binding mismatch.'
Assert-True ((@($normal.nativeDependencyPrecheck.checkpointDefinitionPaths) -join '|') -eq ($guardedDefs -join '|')) 'Checkpoint 83 normal native-dependency definition binding mismatch.'
Assert-True ((@($deep.nativeDependencyPrecheck.checkpointDefinitionPaths) -join '|') -eq ($guardedDefs -join '|')) 'Checkpoint 83 deep native-dependency definition binding mismatch.'

Write-Host '       Validating Power/Reactor candidate isolation and standing-suite authority...'
$policy = Read-Json 'docs/design/testing/checkpoint_83_validation_suite_policy_v0_1.json'
Assert-True ([int]$policy.checkpoint -eq 83 -and [string]$policy.acceptedBaseline -eq '82a') 'Checkpoint 83 suite-policy identity mismatch.'
Assert-True ([int]$policy.powerReactorCandidateControls.mainReactorSpaceHeld -eq 6 -and [int]$policy.powerReactorCandidateControls.tl1OperationalTp -eq 5 -and [int]$policy.powerReactorCandidateControls.tl2CandidateOperationalTp -eq 6 -and [bool]$policy.powerReactorCandidateControls.productionTl2ReactorPromoted -eq $false) 'Checkpoint 83 Power/Reactor policy values mismatch.'
Assert-True (-not [bool]$policy.powerReactorCandidateControls.overloadChanged -and -not [bool]$policy.powerReactorCandidateControls.efficiencyChanged -and -not [bool]$policy.powerReactorCandidateControls.storageChanged -and -not [bool]$policy.powerReactorCandidateControls.auxiliaryGenerationChanged) 'Checkpoint 83 must isolate normal reactor output from other Power properties.'
$candidate = Read-Json 'docs/design/player_technology/tl2_power_reactor_candidate_profile_v0_1.json'
Assert-True ([int]$candidate.checkpoint -eq 83 -and [string]$candidate.researchOwnership -eq 'Power / Reactor') 'TL2 Power/Reactor candidate identity mismatch.'
Assert-True ([int]$candidate.tl1Reference.installationSpace -eq 6 -and [int]$candidate.tl1Reference.normalOperationalOutput -eq 5) 'TL1 reactor reference mismatch.'
Assert-True ([int]$candidate.tl2Candidate.installationSpace -eq 6 -and [int]$candidate.tl2Candidate.normalOperationalOutput -eq 6 -and [string]$candidate.tl2Candidate.candidateChange -eq 'operational_output_only') 'TL2 reactor candidate isolation mismatch.'
Assert-True (-not [bool]$candidate.capabilityFrontierCheck.antiStackingRuleAdded -and [int]$candidate.capabilityFrontierCheck.twoTl1Reactors.installationSpace -eq 12 -and [int]$candidate.capabilityFrontierCheck.twoTl1Reactors.operationalTp -eq 10) 'TL2 reactor candidate must compare real legacy stacking costs without an arbitrary anti-stacking rule.'
$cp80 = @($candidate.acceptedEvidence | Where-Object { [string]$_.checkpoint -eq '80' })
Assert-True ($cp80.Count -eq 1 -and [string]$cp80[0].summarySha256 -eq '596a90b51ae73691e5571b270785f445faed7ed443177f52aa5effff429cb992') 'TL2 reactor candidate must retain accepted CP80 sensitivity provenance.'

$matrix = Read-Json 'docs/archive/player_technology/pre-cp165-active/technology_architecture_matrix_v1.json'
Assert-True ([int]$matrix.checkpoint -eq 83 -and [string]$matrix.authority.concept -eq 'docs/Star_Cluster_Game_Concept_v0.6u.docx') 'Matrix v1 CP83 authority binding mismatch.'
Assert-True ([string]$matrix.researchCategoryOwnership.powerReactor -eq 'Power / Reactor') 'Matrix v1 must own Power/Reactor as its existing research discipline.'
$tl1 = @($matrix.tiers | Where-Object { [int]$_.technologyLevel -eq 1 })[0]
$tl2 = @($matrix.tiers | Where-Object { [int]$_.technologyLevel -eq 2 })[0]
Assert-True ([int]$tl1.powerReactor.operationalTacticalPower -eq 5 -and [int]$tl1.powerReactor.installationSpace -eq 6) 'Matrix v1 TL1 Power/Reactor reference mismatch.'
Assert-True ([int]$tl2.powerReactor.operationalTacticalPowerCandidate -eq 6 -and [int]$tl2.powerReactor.installationSpace -eq 6 -and [string]$tl2.powerReactor.status -eq 'legacy_candidate') 'Matrix v1 TL2 Power/Reactor candidate mismatch.'
Assert-True ([string]$matrix.workingPackages.tl2PowerReactorCandidate -eq 'docs/design/player_technology/tl2_power_reactor_candidate_profile_v0_1.json') 'Matrix v1 Power/Reactor candidate binding mismatch.'
$suite = Read-Json 'docs/design/testing/technology_integration_permutation_suite_v0_3.json'
Assert-True ([string]$suite.id -eq 'technology-integration-permutation-suite-v0_3' -and [int]$suite.checkpoint -eq 83) 'Standing permutation suite v0.3 identity mismatch.'
Assert-True (@($suite.reusableAxes.powerReactorPackage).Count -eq 3 -and @($suite.reusableAxes.powerReactorPackage) -contains 'tl2-early-fusion-6tp-candidate') 'Standing permutation suite v0.3 must expose Power/Reactor as a first-class axis.'
Assert-True ([int]$suite.powerReactorPackages.'tl1-peak-fission-5tp'.operationalTacticalPower -eq 5 -and [int]$suite.powerReactorPackages.'tl2-early-fusion-6tp-candidate'.operationalTacticalPower -eq 6 -and -not [bool]$suite.powerReactorPackages.'tl2-early-fusion-6tp-candidate'.productionPromotion) 'Standing permutation suite v0.3 reactor package values mismatch.'
Assert-True ([string]$suite.currentCoverage.currentStudy.id -eq 'tl2-itc09-power-reactor-progression-permutations' -and [int]$suite.currentCoverage.currentStudy.variantCount -eq 96) 'Standing permutation suite v0.3 current-study binding mismatch.'
Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot 'docs\design\testing\technology_integration_permutation_suite_v0_2.json') -PathType Leaf) 'Historical permutation suite v0.2 must remain for CP82a reproducibility.'

Write-Host '       Validating the 96-variant Power/Reactor study independently...'
$studyRel = 'src/StarCluster.ScenarioRunner/Scenarios/TL1Calibration/tl2-itc09-power-reactor-progression-permutations.json'
$study = Read-Json $studyRel
Assert-True ([string]$study.id -eq 'tl2-itc09-power-reactor-progression-permutations' -and @($study.variants).Count -eq 96) 'Checkpoint 83 study identity/variant count mismatch.'
Assert-True (@($study.builds).Count -eq 1 -and [int]$study.builds[0].usedSpace -eq 35 -and [int]$study.builds[0].mainReactorCount -eq 1 -and [bool]$study.builds[0].ecmSuite -and [bool]$study.builds[0].eccmSuite) 'Checkpoint 83 fixed 35-Space EW fixture mismatch.'
$reactor5 = @($study.variants | Where-Object { [int]$_.sideAReactorOutputOverride -eq 5 })
$reactor6 = @($study.variants | Where-Object { [int]$_.sideAReactorOutputOverride -eq 6 })
Assert-True ($reactor5.Count -eq 48 -and $reactor6.Count -eq 48) 'Checkpoint 83 must contain 48 variants at each reactor output.'
$groups = @($study.variants | Group-Object comparisonGroup)
Assert-True ($groups.Count -eq 12 -and @($groups | Where-Object { $_.Count -ne 8 }).Count -eq 0) 'Checkpoint 83 requires 12 comparison groups with eight variants each.'
$familiesA = @($study.variants | ForEach-Object { [string]$_.sideAFamily } | Sort-Object -Unique)
$familiesB = @($study.variants | ForEach-Object { [string]$_.sideBFamily } | Sort-Object -Unique)
Assert-True (($familiesA -join '|') -eq 'Energy|Kinetic' -and ($familiesB -join '|') -eq 'Kinetic|Missile') 'Checkpoint 83 family coverage mismatch.'
Assert-True (@($study.variants | Where-Object { [int]$_.sideBReactorOutputOverride -ne 5 -or [int]$_.sideATacticalComputerTargetingBonusOverride -ne 12 -or [int]$_.sideBTacticalComputerTargetingBonusOverride -ne 10 }).Count -eq 0) 'Checkpoint 83 computer/reactor control values drifted.'
Assert-True (@($study.variants | Where-Object { [string]$_.sideASensorOverloadPolicy -ne 'None' -or [string]$_.sideBSensorOverloadPolicy -ne 'None' -or [string]$_.sideAStlOverloadPolicy -ne 'None' -or [string]$_.sideBStlOverloadPolicy -ne 'None' }).Count -eq 0) 'Checkpoint 83 must not combine the reactor candidate with overload changes.'
$labels = @($study.variants | ForEach-Object { [string]$_.profileLabel })
foreach ($package in @('firm-reference','wide-eccm2','tall-dr1-eccm1','degraded-p25')) {
    Assert-True (@($labels | Where-Object { $_ -eq ($package + '-r5') }).Count -eq 12 -and @($labels | Where-Object { $_ -eq ($package + '-r6') }).Count -eq 12) "Checkpoint 83 package '$package' is not exactly paired 12x at r5/r6."
}
$degraded = @($study.variants | Where-Object { [string]$_.profileLabel -like 'degraded-p25-*' })
Assert-True ($degraded.Count -eq 24 -and @($degraded | Where-Object { -not [bool]$_.sideAAllowsApproximateDirectFire -or [int]$_.sideAApproximateDirectFireAccuracyPenalty -ne 25 -or [string]$_.sideAEccmPolicy -ne 'None' }).Count -eq 0) 'Checkpoint 83 degraded-fire diagnostic package mismatch.'
Assert-True (@($study.variants | Where-Object { [bool]$_.sideBAllowsApproximateDirectFire -or [int]$_.sideBApproximateDirectFireAccuracyPenalty -ne 0 }).Count -eq 0) 'Checkpoint 83 must not grant degraded fire to Side B or missiles.'

Write-Host '       Auditing CP83 actual-consumer integration, shared gates, and report routing...'
$runner = Read-Text 'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs'
$studySymbol = 'Tl2PowerReactorProgressionPermutationStudyId'
Assert-True ((Count-Substring $runner $studySymbol) -eq 10) 'CP83 study ID must occur in exactly 10 integrated ScenarioRunner registration/consumer locations.'
foreach ($prior in @('Tl2SensorEwDiscriminationIsolationStudyId','Tl2EwPowerPressureTallViabilityStudyId','Tl2TacticalComputerEwPermutationStudyId')) {
    Assert-True ((Count-Substring $runner $prior) -eq 10) "Prior current-TL2 study integration count drifted for '$prior'."
}
$reactiveMarker = '// The current reactive-EW studies use the explicit pre-combat EW response window.'
$reactiveIndex = $runner.IndexOf($reactiveMarker, [System.StringComparison]::Ordinal)
Assert-True ($reactiveIndex -gt 0) 'Reactive-EW study-family marker is missing.'
$reactiveStart = [Math]::Max(0, $reactiveIndex - 1800)
$reactiveBlock = $runner.Substring($reactiveStart, $reactiveIndex - $reactiveStart + $reactiveMarker.Length)
Assert-True ((Count-Substring $reactiveBlock $studySymbol) -eq 1) 'CP83 must appear exactly once in the current reactive-EW study-family whitelist.'
$policyStart = $runner.IndexOf('"policy-telemetry"', [System.StringComparison]::Ordinal)
$attackStart = $runner.IndexOf('"attack-layer-telemetry"', $policyStart, [System.StringComparison]::Ordinal)
Assert-True ($policyStart -gt 0 -and $attackStart -gt $policyStart) 'Shared policy-telemetry gate block could not be isolated.'
$policyBlock = $runner.Substring($policyStart, $attackStart - $policyStart)
Assert-True ((Count-Substring $policyBlock $studySymbol) -eq 2) 'CP83 shared policy-telemetry gate must classify the study exactly twice.'
$buildGates = $runner.IndexOf('private static IReadOnlyList<Tl1IntegratedTacticalCombatGate> BuildGates', [System.StringComparison]::Ordinal)
Assert-True ($buildGates -gt 0) 'ScenarioRunner BuildGates function is missing.'
$c83Start = $runner.IndexOf('if (study.Id == Tl2PowerReactorProgressionPermutationStudyId)', $buildGates, [System.StringComparison]::Ordinal)
$c83End = $runner.IndexOf('if (study.Id == Tl2CandidateStudyId)', $c83Start, [System.StringComparison]::Ordinal)
Assert-True ($c83Start -gt $buildGates -and $c83End -gt $c83Start) 'CP83 release-gate block could not be isolated inside BuildGates.'
$c83Gates = $runner.Substring($c83Start, $c83End - $c83Start)
$expectedGates = @(
    'tl2-c83-variant-coverage','tl2-c83-paired-permutation-completeness','tl2-c83-reactor-output-isolation',
    'tl2-c83-firm-reference-clean','tl2-c83-contemporary-dr1-eccm1-restores-firm','tl2-c83-wide-eccm2-restores-firm',
    'tl2-c83-degraded-fire-penalty-held','tl2-c83-sensor-ew-overload-isolation','tl2-c83-no-evasive-compensation',
    'tl2-c83-no-production-promotion','tl2-c83-outcomes-review-only')
foreach ($gate in $expectedGates) {
    Assert-True ((Count-Substring $c83Gates ('"' + $gate + '"')) -eq 1) "CP83 release-gate block must contain exactly one '$gate' gate."
}
Assert-True (([regex]::Matches($c83Gates, '"tl2-c83-[a-z0-9-]+"')).Count -eq 11) 'CP83 release-gate block must contain exactly 11 CP83 gates.'
Assert-True ($runner.Contains('ValidateTl2PowerReactorProgressionPermutationCoverage(') -and $runner.Contains('WriteTl2PowerReactorProgressionPermutationReview(') -and $runner.Contains('tl2-power-reactor-progression-permutations-review.csv') -and $runner.Contains('tl2-power-reactor-progression-permutations-paired-deltas.csv')) 'CP83 validation or report routing is incomplete.'

Write-Host '       Validating frozen runtime boundaries, Concept v0.6u, and Matrix/workbook synchronization...'
$baseline = Read-Text 'docs/archive/player_technology/pre-cp165-active/tl1_core_combat_numerical_baseline_v0_3.csv'
Assert-True ($baseline.Contains('Power,reactor_output,Main Reactor Tactical Power,5,TP per turn,TL1 Fission Reactor')) 'Production TL1 reactor output must remain 5 TP.'
$productionApproximateEnable = Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'src') -Recurse -File -Filter '*.cs' | Where-Object { $_.FullName -notlike '*StarCluster.ScenarioRunner*' } | Select-String -SimpleMatch 'allowsApproximateTrackFire: true'
Assert-True (@($productionApproximateEnable).Count -eq 0) 'Checkpoint 83 must not enable degraded fire on production Core/Game weapon construction.'
$missileDoc = Read-Text 'docs/design/Missile_Guidance_Datalink_Sensor_And_Seeker_Architecture.md'
Assert-True ($missileDoc.Contains('Ordinary missile profiles continue to require the legitimate Firm terminal solution')) 'Ordinary missile Firm-terminal architecture must remain preserved.'
$conceptText = Read-DocxText 'docs/Star_Cluster_Game_Concept_v0.6u.docx'
Assert-True ($conceptText.Contains('Power / Reactor are independent progression streams for design and calibration') -or $conceptText.Contains('Power / Reactor are independent progression streams')) 'Concept v0.6u must include Power/Reactor in the independent progression-stream model.'
Assert-True ($conceptText.Contains('Early Practical Fusion candidate at 6 Operational Tactical Power') -and $conceptText.Contains('Operational output only') -and $conceptText.Contains('arbitrary anti-stacking rule')) 'Concept v0.6u Power/Reactor candidate isolation is incomplete.'
Assert-True ($conceptText.Contains('Technology Integration Permutation Suite v0.3') -and $conceptText.Contains('C-057')) 'Concept v0.6u standing-suite/decision synchronization is incomplete.'
$matrixMd = Read-Text 'docs/design/player_technology/Technology_Architecture_Matrix_v1.md'
Assert-True ($matrixMd.Contains('Early Practical Fusion') -and $matrixMd.Contains('6 Operational TP / 6 Space') -and $matrixMd.Contains('Checkpoint 83') -and $matrixMd.Contains('arbitrary anti-stacking rule')) 'Technology Architecture Matrix v1 Power/Reactor synchronization is incomplete.'
$wbXml = Read-ZipEntryText 'docs/design/player_technology/StarCluster_Technology_Architecture_Matrix_v1.xlsx' 'xl/workbook.xml'
Assert-True ($wbXml.Contains('Power &amp; Reactor') -and $wbXml.Contains('TL2 Candidate') -and $wbXml.Contains('Architecture Matrix')) 'Matrix workbook is missing the Power/Reactor or required planning sheets.'

Write-Host '       Proving CP83 changed no production Core/Game/tests outside the integrated study consumer...'
$frozenManifest = Read-Text 'docs/validation/evidence/checkpoint-82a/CHECKPOINT_82a_SHA256SUMS.txt'
$lines = @($frozenManifest -split "`r?`n" | Where-Object {
    $_ -match '^[0-9a-f]{64}  (src/StarCluster\.Core/|src/StarCluster\.Game/|tests/)'
})
Assert-True ($lines.Count -gt 300) 'Accepted CP82a frozen Core/Game/tests manifest coverage is unexpectedly small.'
foreach ($line in $lines) {
    $m = [regex]::Match($line, '^([0-9a-f]{64})  (.+)$')
    Assert-True ($m.Success) 'Malformed CP82a frozen manifest line.'
    $relative = $m.Groups[2].Value
    $path = Join-Path $repositoryRoot ($relative.Replace('/','\'))
    Assert-True (Test-Path -LiteralPath $path -PathType Leaf) "Frozen CP82a file '$relative' is missing."
    $actual = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    Assert-True ($actual -eq $m.Groups[1].Value.ToLowerInvariant()) "Checkpoint 83 unexpectedly changed frozen production/test file '$relative'."
}
Write-Host ("       Frozen Core/Game/tests hashes: {0} files matched accepted Checkpoint 82a." -f $lines.Count)

Write-Host '       Validating active-document/archive hygiene...'
$activeConcepts = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs') -File -Filter 'Star_Cluster_Game_Concept_v*.docx')
Assert-True ($activeConcepts.Count -eq 1 -and $activeConcepts[0].Name -eq 'Star_Cluster_Game_Concept_v0.6u.docx') 'Exactly Concept v0.6u must remain active under docs/.'
Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot 'docs\archive\Star_Cluster_Game_Concept_v0.6t.docx') -PathType Leaf) 'Accepted Concept v0.6t must be archived.'
# The active v0.6t path is intentionally archived in CP83; verify the archived bytes against CP82a.
$oldConceptMatch = [regex]::Match($frozenManifest, '(?im)^([0-9a-f]{64})  docs/Star_Cluster_Game_Concept_v0\.6t\.docx$')
Assert-True ($oldConceptMatch.Success) 'Accepted CP82a manifest is missing Concept v0.6t.'
$archivedOldConcept = Join-Path $repositoryRoot 'docs\archive\Star_Cluster_Game_Concept_v0.6t.docx'
$archivedHash = (Get-FileHash -LiteralPath $archivedOldConcept -Algorithm SHA256).Hash.ToLowerInvariant()
Assert-True ($archivedHash -eq $oldConceptMatch.Groups[1].Value.ToLowerInvariant()) 'Archived Concept v0.6t bytes drifted from accepted CP82a.'
$validationFiles = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs\validation') -File -Filter 'Checkpoint_*.md')
Assert-True ($validationFiles.Count -eq 1 -and $validationFiles[0].Name -eq 'Checkpoint_83_TL2_Power_Reactor_Progression_Permutation_Suite.md') 'Exactly one Checkpoint 83 active validation runbook must remain.'
Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot 'docs\validation\archive\Checkpoint_82a_Matrix_Historical_TL2_Production_Authority_Clarification_Hotfix.md') -PathType Leaf) 'Accepted Checkpoint 82a validation runbook must be archived.'
$rootTxt = @(Get-ChildItem -LiteralPath $repositoryRoot -File -Filter '*.txt')
Assert-True ($rootTxt.Count -eq 1 -and $rootTxt[0].Name -eq 'CHECKPOINT_83_SHA256SUMS.txt') 'Repository root must contain only CHECKPOINT_83_SHA256SUMS.txt as .txt.'

Write-Host '       CP83 isolation: 5-TP Peak Fission vs 6-TP Early Fusion at fixed 6 Space; Operational output only.'
Write-Host '       Standing suite: 12 combat/geometry groups x 4 information-control environments x 2 reactor outputs = 96 variants.'
Write-Host '       Normal workload: 11 stages / 96 substantive variants / 960,000 default substantive trials plus 96 smoke trials.'
Write-Host 'Checkpoint 83 contract validation passed.'
