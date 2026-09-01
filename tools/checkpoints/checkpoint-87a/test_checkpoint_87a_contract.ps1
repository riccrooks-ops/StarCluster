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
function Read-ZipEntryText {
    param([string]$RelativePath,[string]$EntryName)
    $p = Join-Path $repositoryRoot ($RelativePath.Replace('/','\'))
    Assert-True (Test-Path -LiteralPath $p -PathType Leaf) "Archive '$RelativePath' is missing."
    Add-Type -AssemblyName System.IO.Compression.FileSystem -ErrorAction Stop | Out-Null
    $z = [System.IO.Compression.ZipFile]::OpenRead($p)
    try {
        $e = $z.GetEntry($EntryName)
        Assert-True ($null -ne $e) "Archive '$RelativePath' is missing '$EntryName'."
        $s = $e.Open()
        $r = New-Object System.IO.StreamReader($s)
        try { return [string]$r.ReadToEnd() } finally { $r.Dispose(); $s.Dispose() }
    } finally { $z.Dispose() }
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
        Assert-True (-not [string]::IsNullOrWhiteSpace($line)) "Manifest '$RelativePath' contains a blank line at $lineNumber."
        $m = [regex]::Match($line, '^([0-9a-fA-F]{64})  (.+)$')
        Assert-True ($m.Success) "Manifest '$RelativePath' has malformed line $lineNumber."
        $relative = $m.Groups[2].Value.Replace('\','/')
        Assert-True (-not $map.ContainsKey($relative)) "Manifest '$RelativePath' duplicates '$relative'."
        $map[$relative] = $m.Groups[1].Value.ToLowerInvariant()
    }
    return [pscustomobject]@{ Path=$p; PhysicalLineCount=$lines.Count; EntryCount=$map.Count; Entries=$map }
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
function Find-Axis {
    param($Study,[string]$Id)
    $matches = @($Study.axes | Where-Object { [string]$_.id -eq $Id })
    Assert-True ($matches.Count -eq 1) "Cross-TL definition must contain exactly one '$Id' axis."
    return $matches[0]
}
function Find-Option {
    param($Axis,[string]$Id,[string]$Context)
    $matches = @($Axis.options | Where-Object { [string]$_.id -eq $Id })
    Assert-True ($matches.Count -eq 1) "$Context must contain exactly one '$Id' option."
    return $matches[0]
}

Write-Host '       Validating native-dependency declarations...'
$guard = Join-Path $repositoryRoot 'tools\checkpoints\Test-NativeAcceptanceDependencies.ps1'
$normalRel = 'tools/calibration/checkpoints/checkpoint-87a.json'
$deepRel = 'tools/calibration/checkpoints/checkpoint-87a-deep-calibration.json'
$guardedPs = @(
    'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
    'tools/checkpoints/checkpoint-87a/apply_checkpoint_87a.ps1',
    'tools/checkpoints/checkpoint-87a/test_checkpoint_87a_contract.ps1',
    'tools/calibration/run_calibration_checkpoint.ps1'
)
$guardedDefs = @($normalRel,$deepRel)
& $guard -RepositoryRoot $repositoryRoot -PowerShellPaths $guardedPs -CheckpointDefinitionPaths $guardedDefs

Write-Host '       Validating Checkpoint 87a definitions and unchanged CP87 workload accounting...'
$normal = Read-Json $normalRel
$deep = Read-Json $deepRel
Assert-True ([string]$normal.checkpointId -eq '87a' -and [string]$deep.checkpointId -eq '87a') 'Checkpoint 87a definition ID mismatch.'
Assert-True ([string]$normal.manifestFile -eq 'CHECKPOINT_87a_SHA256SUMS.txt' -and [string]$deep.manifestFile -eq 'CHECKPOINT_87a_SHA256SUMS.txt') 'Checkpoint 87a manifest binding mismatch.'
Assert-True ([string]$normal.outputRoot -eq 'out/checkpoint-87a' -and [string]$deep.outputRoot -eq 'out/checkpoint-87a-deep-calibration') 'Checkpoint 87a output-root binding mismatch.'
Assert-True (@($normal.stages).Count -eq 13 -and [int]$normal.checkpointMetrics.stageCount -eq 13) 'Checkpoint 87a normal stage-count mismatch.'
Assert-True ([int]$normal.checkpointMetrics.monteCarloVariantCount -eq 192 -and [int]$normal.checkpointMetrics.trialsAtDefault -eq 1920000 -and [int]$normal.checkpointMetrics.smokeVariantExecutions -eq 192 -and [int]$normal.checkpointMetrics.smokeTrialsAtDefault -eq 192 -and [int]$normal.checkpointMetrics.totalTrialExecutionsAtDefault -eq 1920192) 'Checkpoint 87a normal workload mismatch.'
Assert-True (@($deep.stages).Count -eq 14 -and [int]$deep.checkpointMetrics.stageCount -eq 14) 'Checkpoint 87a Deep Calibration stage-count mismatch.'
Assert-True ([int]$deep.checkpointMetrics.monteCarloVariantCount -eq 480 -and [int]$deep.checkpointMetrics.trialsAtDefault -eq 4800000 -and [int]$deep.checkpointMetrics.smokeVariantExecutions -eq 192 -and [int]$deep.checkpointMetrics.totalTrialExecutionsAtDefault -eq 4800192) 'Checkpoint 87a Deep Calibration workload mismatch.'
Assert-True ([string]$normal.primaryStudy.id -eq 'tl2-itc13-cross-tl-build-permutation-screening' -and [int]$normal.primaryStudy.variantCount -eq 192) 'Checkpoint 87a primary-study metadata mismatch.'
$expectedNormal = @(
    'deterministic','tl1-phase-a','tl1-phase-b','tl1-installation-space-envelope','tl1-sensor-ew-foundation',
    'cross-tl-build-permutation-preflight','cross-tl-build-permutation-generation','cross-tl-generated-study-preflight',
    'cross-tl-generated-study-smoke','cross-tl-build-permutation-screening','auxiliary-resource-endurance',
    'checkpoint-53-resource-semantics-lock','runner-self-tests'
)
$normalIds = @($normal.stages | ForEach-Object { [string]$_.id })
Assert-True (($normalIds -join '|') -eq ($expectedNormal -join '|')) 'Checkpoint 87a normal stage order/identity mismatch.'
$deepIds = @($deep.stages | ForEach-Object { [string]$_.id })
Assert-True (($deepIds -contains 'cp86-weapon-penetration-regression') -and $deepIds[-1] -eq 'runner-self-tests') 'Checkpoint 87a Deep Calibration must add the accepted CP86 penetration regression before final retained stages.'
$generationStage = @($normal.stages | Where-Object { [string]$_.id -eq 'cross-tl-build-permutation-generation' })
$consumerPreflight = @($normal.stages | Where-Object { [string]$_.id -eq 'cross-tl-generated-study-preflight' })
$consumerSmoke = @($normal.stages | Where-Object { [string]$_.id -eq 'cross-tl-generated-study-smoke' })
$consumerStudy = @($normal.stages | Where-Object { [string]$_.id -eq 'cross-tl-build-permutation-screening' })
Assert-True ($generationStage.Count -eq 1 -and [string]$generationStage[0].command -eq 'cross-tl-build-permutation') 'Checkpoint 87a is missing the native generator stage.'
Assert-True ($consumerPreflight.Count -eq 1 -and [string]$consumerPreflight[0].command -eq 'tl1-integrated-tactical-combat-preflight') 'Checkpoint 87a is missing generated-study actual-consumer preflight.'
Assert-True ($consumerSmoke.Count -eq 1 -and [string]$consumerSmoke[0].command -eq 'tl1-integrated-tactical-combat') 'Checkpoint 87a is missing generated-study full-pipeline smoke.'
Assert-True ($consumerStudy.Count -eq 1 -and [string]$consumerStudy[0].command -eq 'tl1-integrated-tactical-combat') 'Checkpoint 87a is missing the substantive generated-study consumer stage.'
$generatedPath = '{OutputRoot}/cross-tl-build-permutation/generated-integrated-combat-study.json'
Assert-True ((@($consumerPreflight[0].arguments) -contains $generatedPath) -and (@($consumerSmoke[0].arguments) -contains $generatedPath) -and (@($consumerStudy[0].arguments) -contains $generatedPath)) 'All generated-study consumer stages must read the generator output path.'
$selfTestStage = @($normal.stages | Where-Object { [string]$_.id -eq 'runner-self-tests' })
Assert-True ($selfTestStage.Count -eq 1 -and [int]$selfTestStage[0].metrics.selfTestCount -eq 52) 'Checkpoint 87a must require 52 ScenarioRunner self-tests.'

Write-Host '       Validating the 512-build legal envelope and 192-variant generated slice...'
$crossRel = 'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/cross-tl-build-permutation-foundation-v0_1.json'
$cross = Read-Json $crossRel
Assert-True ([string]$cross.schemaVersion -eq 'star-cluster-cross-tl-build-permutation-v1' -and [string]$cross.id -eq 'cross-tl-build-permutation-foundation-v0_1') 'Cross-TL foundation schema/id mismatch.'
Assert-True ([int]$cross.totalInstallationSpace -eq 35 -and [int]$cross.fixedShellSpace -eq 12) 'Cross-TL foundation must retain the 35-Space / 12-Space fixed-shell envelope.'
Assert-True (@($cross.axes).Count -eq 8) 'Cross-TL foundation must contain exactly eight technology axes.'
$expectedOptionCounts = @{ weapon=4; reactor=2; computer=2; sensor=2; shield=2; armor=2; ecm=2; eccm=2 }
$rawCount = [int64]1
$spaceSums = @(0)
foreach ($axisId in @('weapon','reactor','computer','sensor','shield','armor','ecm','eccm')) {
    $axis = Find-Axis $cross $axisId
    $options = @($axis.options)
    Assert-True ($options.Count -eq [int]$expectedOptionCounts[$axisId]) "Cross-TL axis '$axisId' option count mismatch."
    $rawCount = $rawCount * [int64]$options.Count
    $nextSpaceSums = @()
    foreach ($sum in $spaceSums) {
        foreach ($option in $options) {
            Require-Property $option 'space' "Cross-TL $axisId option"
            $nextSpaceSums += ([int]$sum + [int]$option.space)
        }
    }
    $spaceSums = $nextSpaceSums
}
Assert-True ($rawCount -eq 512 -and [int]$cross.expectedLegalBuildCount -eq 512) 'Cross-TL raw/legal build count must be 512.'
Assert-True ($spaceSums.Count -eq 512 -and @($spaceSums | Where-Object { ([int]$_ + [int]$cross.fixedShellSpace) -ne 35 }).Count -eq 0) 'Every CP87 foundation combination must exactly fill 35 Installation Space.'
Assert-True ([int]$cross.expectedNamedRecipeCount -eq 13 -and @($cross.namedRecipes).Count -eq 13) 'Cross-TL named-recipe count mismatch.'
$recipeIds = @($cross.namedRecipes | ForEach-Object { [string]$_.id })
Assert-True (@($recipeIds | Select-Object -Unique).Count -eq 13) 'Cross-TL named-recipe IDs must be unique.'
foreach ($recipe in @($cross.namedRecipes)) {
    Require-Property $recipe 'selections' "Named recipe '$($recipe.id)'"
    foreach ($axisId in @('weapon','reactor','computer','sensor','shield','armor','ecm','eccm')) {
        $prop = $recipe.selections.PSObject.Properties[$axisId]
        Assert-True ($null -ne $prop) "Named recipe '$($recipe.id)' is missing '$axisId'."
        $axis = Find-Axis $cross $axisId
        Assert-True (@($axis.options | Where-Object { [string]$_.id -eq [string]$prop.Value }).Count -eq 1) "Named recipe '$($recipe.id)' selects an unknown '$axisId' option."
    }
}
$pairKeys = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
foreach ($group in @($cross.pairingGroups)) {
    foreach ($a in @($group.sideARecipes)) {
        Assert-True ($recipeIds -contains [string]$a) "Pairing group '$($group.id)' references unknown Side A recipe '$a'."
        foreach ($b in @($group.sideBRecipes)) {
            Assert-True ($recipeIds -contains [string]$b) "Pairing group '$($group.id)' references unknown Side B recipe '$b'."
            Assert-True ($pairKeys.Add(([string]$a + '|' + [string]$b))) "Duplicate ordered recipe pairing '$a|$b'."
        }
    }
}
Assert-True ($pairKeys.Count -eq 64 -and [int]$cross.expectedLogicalPairingCount -eq 64) 'Cross-TL foundation must expand to exactly 64 unique ordered logical pairings.'
Assert-True (@($cross.geometries).Count -eq 3 -and [int]$cross.expectedGeometryCount -eq 3 -and [int]$cross.expectedGeneratedVariantCount -eq 192) 'Cross-TL geometry/generated-variant counts mismatch.'
$fixedGeometry = @($cross.geometries | Where-Object { [string]$_.movementMode -eq 'HoldRange3' -and [string]$_.movementOrder -eq 'Simultaneous' -and [int]$_.initialRangeHexes -eq 3 })
$dynamicA = @($cross.geometries | Where-Object { [string]$_.movementMode -eq 'TrackAwareOpponentRange' -and [string]$_.movementOrder -eq 'SideAFirst' -and [int]$_.initialRangeHexes -eq 3 })
$dynamicB = @($cross.geometries | Where-Object { [string]$_.movementMode -eq 'TrackAwareOpponentRange' -and [string]$_.movementOrder -eq 'SideBFirst' -and [int]$_.initialRangeHexes -eq 3 })
Assert-True ($fixedGeometry.Count -eq 1 -and $dynamicA.Count -eq 1 -and $dynamicB.Count -eq 1) 'Cross-TL geometries must be fixed Range 3 plus both TrackAware movement orders.'
$weaponAxis = Find-Axis $cross 'weapon'
$k1 = Find-Option $weaponAxis 'k1' 'Weapon axis'
$k2 = Find-Option $weaponAxis 'k2' 'Weapon axis'
$e1 = Find-Option $weaponAxis 'e1' 'Weapon axis'
$m1 = Find-Option $weaponAxis 'm1' 'Weapon axis'
Assert-True ([string]$k1.family -eq 'Kinetic' -and [int]$k1.shieldPenetration -eq 1 -and [int]$k1.armorPenetration -eq 0) 'Kinetic TL1 penetration reference drifted.'
Assert-True ([string]$k2.family -eq 'Kinetic' -and [int]$k2.shieldPenetration -eq 1 -and [int]$k2.armorPenetration -eq 1 -and [string]$k2.status -eq 'locally_validated_working_candidate') 'Kinetic TL2 APEN1 working candidate is not carried correctly.'
Assert-True ([string]$e1.family -eq 'Energy' -and [int]$e1.shieldPenetration -eq 1 -and [int]$e1.armorPenetration -eq 1) 'Energy current penetration profile drifted.'
Assert-True ([string]$m1.family -eq 'Missile' -and [int]$m1.shieldPenetration -eq 1 -and [int]$m1.armorPenetration -eq 2) 'Missile current penetration profile drifted.'
$crossText = Read-Text $crossRel
Assert-NoText $crossText 'powerOvercommitIllegal' 'Cross-TL foundation must not add a power-sufficiency construction filter.'

Write-Host '       Validating ScenarioRunner generator, consumer hooks, and combat-activity gates...'
$program = Read-Text 'src/StarCluster.ScenarioRunner/Program.cs'
$generator = Read-Text 'src/StarCluster.ScenarioRunner/CrossTlIntegration/CrossTlBuildPermutationRunner.cs'
$selfTests = Read-Text 'src/StarCluster.ScenarioRunner/ScenarioRunnerSelfTests.cs'
$integrated = Read-Text 'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs'
foreach ($needle in @('cross-tl-build-permutation','cross-tl-build-permutation-preflight','RunCrossTlBuildPermutation')) { Require-Contains $program $needle "Program.cs is missing CP87 command '$needle'." }
foreach ($needle in @('expectedLegalBuildCount','legal-builds.csv','named-builds.csv','pairing-plan.csv','generated-integrated-combat-study.json','power-overcommit-not-legality-filter','track-aware-dynamic-geometry','262144L','131328L')) { Require-Contains $generator $needle "Cross-TL generator is missing required contract '$needle'." }
Require-Contains $selfTests 'CP87 cross-TL Cartesian enumeration preserves the 512-build foundation envelope' 'ScenarioRunner self-tests are missing the CP87 Cartesian-count self-test.'
Require-Contains $selfTests 'oriented == 262144L && unorderedWithSelf == 131328L' 'CP87 self-test is missing pairing-envelope arithmetic.'
$studyId = 'tl2-itc13-cross-tl-build-permutation-screening'
$studySymbol = 'CrossTlBuildPermutationScreeningStudyId'
$literalBindingCount = [regex]::Matches($integrated,[regex]::Escape($studyId)).Count
$symbolIntegrationCount = [regex]::Matches($integrated,[regex]::Escape($studySymbol)).Count
Assert-True ($literalBindingCount -eq 1) 'Integrated combat runner must bind the CP87 study-ID literal exactly once through its named constant.'
Assert-True ($symbolIntegrationCount -ge 11) 'Integrated combat runner has incomplete CP87 named-constant study-ID integration.'
foreach ($needle in @(
    'private const string CrossTlBuildPermutationScreeningStudyId',
    'studyId == CrossTlBuildPermutationScreeningStudyId',
    'CrossTlBuildPermutationScreeningStudyId =>',
    'study.Id == CrossTlBuildPermutationScreeningStudyId'
)) { Require-Contains $integrated $needle "Integrated combat runner is missing CP87 study-ID integration form '$needle'." }
foreach ($needle in @('RequiredCrossTlBuildPermutationScreeningVariantCount = 192','ValidateCrossTlBuildPermutationScreeningCoverage','cross-tl-dynamic-combat-activity','cross-tl-screening-outcomes-review-only','WriteCrossTlBuildPermutationScreeningReview','cross-tl-screening-review.csv','TrackAwareOpponentRange')) { Require-Contains $integrated $needle "Integrated combat runner is missing CP87 hook '$needle'." }
Require-Contains $integrated 'fixedMissileActive' 'CP87 combat-activity gate must compare missile launch activity to the fixed reference.'
Require-Contains $integrated 'fixedDirectActive' 'CP87 combat-activity gate must compare direct-fire activity to the fixed reference.'

Write-Host '       Validating current technology, standing-suite, AI, and development authorities...'
$weaponProfile = Read-Json 'docs/archive/player_technology/pre-cp165-active/tl2_weapon_penetration_working_profile_v0_2.json'
Require-Property $weaponProfile 'families' 'TL2 weapon penetration working profile'
Require-Property $weaponProfile.families 'Kinetic' 'TL2 weapon penetration families'
Require-Property $weaponProfile.families 'Energy' 'TL2 weapon penetration families'
Require-Property $weaponProfile.families 'Missile' 'TL2 weapon penetration families'
Assert-True ([int]$weaponProfile.families.Kinetic.tl2WorkingCandidate.shieldPenetration -eq 1 -and [int]$weaponProfile.families.Kinetic.tl2WorkingCandidate.armorPenetration -eq 1 -and [string]$weaponProfile.families.Kinetic.tl2WorkingCandidate.status -eq 'locally_validated_working_candidate') 'Working profile must carry Kinetic SPEN1/APEN1 as the TL2 local candidate.'
Assert-True ($null -eq $weaponProfile.families.Energy.tl2WorkingCandidate -and $null -eq $weaponProfile.families.Missile.tl2WorkingCandidate) 'Energy and Missile must not receive automatic TL2 penetration candidates.'
Assert-True (-not [bool]$weaponProfile.promotionPolicy.automaticPromotion -and [bool]$weaponProfile.promotionPolicy.sharedSensitivityDoesNotImplySharedProgression) 'Working profile must prohibit automatic/symmetric weapon promotion.'

$matrix = Read-Json 'docs/archive/player_technology/pre-cp165-active/technology_architecture_matrix_v1.json'
Assert-True ([string]$matrix.weaponFamilyPenetrationArchitecture.profile -eq 'docs/archive/player_technology/pre-cp165-active/tl2_weapon_penetration_working_profile_v0_2.json') 'Technology Matrix does not point to the current weapon-penetration working profile.'
Assert-True ([int]$matrix.weaponFamilyPenetrationArchitecture.tl2WorkingCandidates.Kinetic.shieldPenetration -eq 1 -and [int]$matrix.weaponFamilyPenetrationArchitecture.tl2WorkingCandidates.Kinetic.armorPenetration -eq 1) 'Technology Matrix Kinetic working penetration candidate drifted.'
Assert-True ($null -eq $matrix.weaponFamilyPenetrationArchitecture.tl2WorkingCandidates.Energy -and $null -eq $matrix.weaponFamilyPenetrationArchitecture.tl2WorkingCandidates.Missile) 'Technology Matrix must retain no Energy/Missile TL2 penetration promotion.'
Assert-True (-not [bool]$matrix.weaponFamilyPenetrationArchitecture.automaticSymmetricPromotion) 'Technology Matrix must prohibit symmetric weapon promotion.'
Assert-True ([string]$matrix.integrationArchitecture.standingPermutationSuite -eq 'docs/design/testing/technology_integration_permutation_suite_v0_7.json' -and [int]$matrix.integrationArchitecture.currentLegalBuildEnvelope -eq 512 -and [int]$matrix.integrationArchitecture.currentBoundedCombatScreenVariants -eq 192) 'Technology Matrix cross-TL integration architecture drifted.'

$suite = Read-Json 'docs/design/testing/technology_integration_permutation_suite_v0_7.json'
Assert-True ([string]$suite.id -eq 'technology-integration-permutation-suite-v0_7' -and [int]$suite.checkpoint -eq 87) 'Standing integration suite v0.7 identity mismatch.'
Require-Property $suite 'legalBuildEnumeration' 'Standing integration suite v0.7'
Assert-True ([int]$suite.legalBuildEnumeration.currentLegalBuildCount -eq 512 -and [int]$suite.legalBuildEnumeration.orientedPairingEnvelope -eq 262144 -and [int]$suite.legalBuildEnumeration.unorderedWithSelfPairingEnvelope -eq 131328) 'Standing suite legal-build/pairing envelope mismatch.'
Assert-True ([string]$suite.currentCoverage.currentStudy.id -eq $studyId -and [int]$suite.currentCoverage.currentStudy.variantCount -eq 192) 'Standing suite current generated-study coverage mismatch.'
$suiteText = Read-Text 'docs/design/testing/technology_integration_permutation_suite_v0_7.json'
Require-Contains $suiteText 'simultaneous Tactical Power insufficiency is an operational tradeoff' 'Standing suite must preserve the no-power-legality-filter rule.'
Require-Contains $suiteText 'Dynamic movement/range doctrine must preserve attack eligibility' 'Standing suite must carry the attack-eligibility guard.'

$simGuidelines = Read-Text 'docs/development/Simulation_Development_Guidelines.md'
foreach ($needle in @('Generated-study pipeline for broad permutations','Combat-activity and attack-eligibility guards','Power pressure and tactical allocation are intended operational tradeoffs','not a checkpoint journal')) { Require-Contains $simGuidelines $needle "Simulation Development Guidelines are missing durable rule '$needle'." }
Assert-NoText $simGuidelines '1635e098' 'Simulation Development Guidelines must not accumulate checkpoint result hashes.'
$ai = Read-Text 'docs/design/ai/AI_Doctrine_Registry_Architecture_v0_4.md'
Require-Contains $ai 'not a checkpoint diary' 'AI doctrine authority must remain a reusable-lesson document rather than a checkpoint journal.'
Require-Contains $ai 'Range goals must remain attack-eligible' 'AI doctrine authority is missing the reusable attack-eligibility lesson.'
Assert-NoText $ai 'primarySummarySha256' 'AI doctrine authority must not become a raw evidence/result log.'
Assert-NoText $ai '2,880,000' 'AI doctrine authority must not accumulate checkpoint trial counts.'

$rootReadme = Read-Text 'README.md'
Require-Contains $rootReadme 'Checkpoint 87a' 'Root README must identify Checkpoint 87a.'
Require-Contains $rootReadme 'CHAT_README.md' 'Root README must preserve the mandatory session bootstrap.'
$designReadme = Read-Text 'docs/design/README.md'
Require-Contains $designReadme 'AI_Doctrine_Registry_Architecture_v0_4.md' 'Design README must point to AI doctrine v0.4.'
Require-Contains $designReadme 'Technology_Integration_Permutation_Suite_Architecture_v0_7.md' 'Design README must point to standing suite v0.7.'
$testingReadme = Read-Text 'docs/design/testing/README.md'
Require-Contains $testingReadme 'Checkpoint_87_Validation_Tiers.md' 'Testing README must point to CP87 validation tiers.'
Require-Contains $testingReadme 'technology_integration_permutation_suite_v0_7.json' 'Testing README must point to standing suite v0.7.'
$techReadme = Read-Text 'docs/design/player_technology/README.md'
Require-Contains $techReadme 'tl2_weapon_penetration_working_profile_v0_2.json' 'Player Technology README must point to the current weapon working profile.'
Require-Contains $techReadme 'not a checkpoint diary' 'Player Technology README must preserve documentation-hygiene guidance.'
$todo = Read-Text 'docs/Prototype_TODO.md'
Require-Contains $todo 'Checkpoint 87a' 'Prototype TODO must identify Checkpoint 87a.'
Require-Contains $todo 'current-action list' 'Prototype TODO must remain an action list rather than a checkpoint journal.'

$policy = Read-Json 'docs/design/testing/checkpoint_87_validation_suite_policy_v0_1.json'
Assert-True ([string]$policy.checkpointId -eq '87' -and [int]$policy.mustRun.legalBuildCount -eq 512 -and [int]$policy.mustRun.generatedVariantCount -eq 192 -and [int]$policy.mustRun.scenarioRunnerSelfTestsExpected -eq 52) 'CP87 validation-suite policy counts mismatch.'
Assert-True (-not [bool]$policy.constructionLegality.simultaneousTacticalPowerSufficiencyRequired -and [bool]$policy.mustRun.dynamicCombatActivityGateRequired) 'CP87 validation-suite policy must preserve construction/power and combat-activity rules.'

$workbookXml = Read-ZipEntryText 'docs/design/player_technology/StarCluster_Technology_Architecture_Matrix_v1.xlsx' 'xl/workbook.xml'
foreach ($sheetName in @('Overview','TL2 Candidate','Weapon Penetration','Integration Guardrails')) { Assert-True ($workbookXml.Contains(('name="' + $sheetName + '"'))) "Technology Matrix workbook is missing '$sheetName'." }
Assert-True (-not $workbookXml.Contains('name="Validation Plan"')) 'Technology Matrix workbook must not regain the retired Validation Plan sheet.'

Write-Host '       Validating accepted CP86a provenance, unchanged Concept, and frozen production code...'
$cp86ManifestRel = 'docs/validation/evidence/checkpoint-86a/CHECKPOINT_86a_SHA256SUMS.txt'
$cp86Record = Read-Manifest $cp86ManifestRel
$cp86Manifest = $cp86Record.Entries
$prov = Read-Json 'docs/validation/evidence/checkpoint-86a/checkpoint-86a-native-acceptance-provenance.json'
$acceptedCp86ManifestSha = '5202769a7c31a60c574bc77adecebbe3ce1c38b5d65253d11d9f61907784d5a2'
Assert-True ([string]$prov.acceptanceSummary.status -eq 'Success') 'CP86a provenance must record successful native acceptance.'
Assert-True ([string]$prov.acceptanceSummary.checkpointManifestSha256 -eq $acceptedCp86ManifestSha) 'CP86a provenance manifest SHA-256 is not the accepted value.'
Assert-True ((Hash-Rel $cp86ManifestRel) -eq $acceptedCp86ManifestSha) 'Embedded CP86a evidence-manifest bytes do not match accepted provenance.'
Assert-True ([int]$cp86Record.PhysicalLineCount -eq 1678 -and [int]$cp86Record.EntryCount -eq 1678) 'Accepted CP86a evidence manifest must contain exactly 1,678 unique entries.'
Assert-True ([string]$prov.designDisposition.kineticApen1 -eq 'locally_validated_working_candidate') 'CP86a provenance must carry Kinetic APEN1 as locally validated.'
Assert-True ([bool]$prov.durableSimulationLesson.attackEligibilityAwareMovement -and [bool]$prov.durableSimulationLesson.combatActivityGateRequired) 'CP86a provenance must carry the durable attack-eligibility/combat-activity lesson.'
$conceptRel = 'docs/Star_Cluster_Game_Concept_v0.6x.docx'
Assert-True ($cp86Manifest.ContainsKey($conceptRel)) 'Accepted CP86a manifest is missing Concept v0.6x.'
Assert-True ((Hash-Rel $conceptRel) -eq [string]$cp86Manifest[$conceptRel]) 'CP87 must not change Concept v0.6x; gameplay rules are outside this checkpoint.'

$allowedRunner = @(
    'src/StarCluster.ScenarioRunner/Program.cs',
    'src/StarCluster.ScenarioRunner/ScenarioRunnerSelfTests.cs',
    'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs'
)
foreach ($rel in @($cp86Manifest.Keys | Sort-Object)) {
    $freeze = $rel.StartsWith('src/StarCluster.Core/') -or $rel.StartsWith('src/StarCluster.Game/') -or $rel.StartsWith('tests/') -or ($rel.StartsWith('src/StarCluster.ScenarioRunner/') -and $allowedRunner -notcontains $rel)
    if ($freeze) {
        Assert-True ((Hash-Rel $rel) -eq [string]$cp86Manifest[$rel]) "Unexpected CP87 drift from accepted CP86a in '$rel'."
    }
}
$oldRunbookRel = 'docs/validation/Checkpoint_86a_CP86_Standing_Suite_Promotion_Contract_Hotfix.md'
Assert-True ($cp86Manifest.ContainsKey($oldRunbookRel)) 'Accepted CP86a manifest is missing its active validation runbook.'
Assert-True ((Hash-Rel 'docs/validation/archive/Checkpoint_86a_CP86_Standing_Suite_Promotion_Contract_Hotfix.md') -eq [string]$cp86Manifest[$oldRunbookRel]) 'Archived CP86a validation runbook bytes drifted from accepted CP86a.'

$cp87ArchivedRunbook = 'docs/validation/archive/Checkpoint_87_Cross_TL_Legal_Build_Permutation_Foundation.md'
Assert-True ((Hash-Rel $cp87ArchivedRunbook) -eq '60aab2d58db2ed4507188003f8c2afabbed870e72f876539d5d6152908e066e6') 'Archived CP87 validation runbook bytes drifted in the CP87a hotfix.'
$cp87HotfixFrozen = @{
    'src/StarCluster.ScenarioRunner/Program.cs' = '60f3b5c725b068ebd766fb219670fcb8eb4940535513887970aa26776c9fbacd'
    'src/StarCluster.ScenarioRunner/ScenarioRunnerSelfTests.cs' = 'ec4b2de5eb58eef18b88576e1bb9bc5472c51e6dd94927bc2e2a273a79407036'
    'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs' = '273096258b6d517bf26d46de792c1908ffcb14ce8af99199eb98f7e84d25a799'
    'src/StarCluster.ScenarioRunner/CrossTlIntegration/CrossTlBuildPermutationRunner.cs' = '99749fab74c78bbe149d97c52203e8cbd0e8703762b615cef61a7a138181a216'
    'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/cross-tl-build-permutation-foundation-v0_1.json' = '05bb2b29e9358edaf05331f7920166287741a21c480d547dc45ce8378c9f3097'
    'docs/Star_Cluster_Game_Concept_v0.6x.docx' = 'bc7cd26238a72f33fb153c4ab69bd412a5997b13e602849aefa2e8d412565c2c'
    'docs/design/testing/technology_integration_permutation_suite_v0_7.json' = '30c775575980da7ad53b7e3fb6b8ac7b7249c110656b21e8540c4ef6f0194724'
    'docs/design/ai/AI_Doctrine_Registry_Architecture_v0_4.md' = '4a374c6f6190c2f36c3b267a006d29472606ec5f512301eef3573a6417cdee73'
    'docs/design/player_technology/StarCluster_Technology_Architecture_Matrix_v1.xlsx' = '7f8068d02164ee683846fa024f03bca4a1ab5c868d3b3727c15eff241cf257c2'
    'docs/design/testing/Checkpoint_87_Validation_Tiers.md' = '116d79e420f2ff116b4f4ef59663007ce76452805d94ddac9064c5b531985bae'
    'docs/design/testing/checkpoint_87_validation_suite_policy_v0_1.json' = '3efeceedfd7807fae5cafc800433620caf535f2c828a4ec24b1a01e1b59b83a2'
}
foreach ($rel in @($cp87HotfixFrozen.Keys)) {
    Assert-True ((Hash-Rel $rel) -eq [string]$cp87HotfixFrozen[$rel]) "CP87a hotfix unexpectedly changed CP87 substantive file '$rel'."
}

$activeValidation = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs\validation') -File -Filter 'Checkpoint_*.md')
Assert-True ($activeValidation.Count -eq 1 -and $activeValidation[0].Name -eq 'Checkpoint_87a_CP87_Study_ID_Integration_Contract_Hotfix.md') 'Exactly one CP87a active validation runbook must remain.'
$activeConcept = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs') -File -Filter 'Star_Cluster_Game_Concept_v*.docx')
Assert-True ($activeConcept.Count -eq 1 -and $activeConcept[0].Name -eq 'Star_Cluster_Game_Concept_v0.6x.docx') 'Exactly one unchanged Concept v0.6x active document must remain.'
$rootTxt = @(Get-ChildItem -LiteralPath $repositoryRoot -File -Filter '*.txt')
Assert-True ($rootTxt.Count -eq 1 -and $rootTxt[0].Name -eq 'CHECKPOINT_87a_SHA256SUMS.txt') 'Repository root must contain only CHECKPOINT_87a_SHA256SUMS.txt as .txt.'

Write-Host '       CP87a preserves CP87 foundation: 512 legal TL1/TL2 working-envelope builds; 64 ordered representative pairings; 192 generated integrated variants.'
Write-Host '       CP87 quality guard: dynamic TrackAware contexts must preserve attack types active in their fixed Range-3 references.'
Write-Host '       CP87 promotion boundary: integration outcomes remain human-review evidence; no candidate is promoted automatically.'
Write-Host '       Normal workload: 13 stages / 192 substantive variants / 1,920,000 default substantive trials plus 192 smoke trials.'
Write-Host 'Checkpoint 87a contract validation passed.'
