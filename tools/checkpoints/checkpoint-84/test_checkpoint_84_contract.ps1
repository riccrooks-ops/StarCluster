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
    $path = Join-Path $repositoryRoot ($RelativePath.Replace('/','\'))
    Assert-True (Test-Path -LiteralPath $path -PathType Leaf) "Required text file '$RelativePath' is missing."
    return [System.IO.File]::ReadAllText($path)
}
function Read-Json {
    param([string]$RelativePath)
    $text = Read-Text $RelativePath
    Assert-True (-not [string]::IsNullOrWhiteSpace($text)) "Required JSON file '$RelativePath' is empty."
    return ($text | ConvertFrom-Json)
}
function Read-ZipEntryText {
    param([string]$RelativePath, [string]$EntryName)
    $path = Join-Path $repositoryRoot ($RelativePath.Replace('/','\'))
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

Write-Host '       Validating native-dependency declarations...'
$guard = Join-Path $repositoryRoot 'tools\checkpoints\Test-NativeAcceptanceDependencies.ps1'
$normalRel = 'tools/calibration/checkpoints/checkpoint-84.json'
$deepRel = 'tools/calibration/checkpoints/checkpoint-84-deep-calibration.json'
$guardedPs = @(
    'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
    'tools/checkpoints/checkpoint-84/apply_checkpoint_84.ps1',
    'tools/checkpoints/checkpoint-84/test_checkpoint_84_contract.ps1',
    'tools/calibration/run_calibration_checkpoint.ps1'
)
$guardedDefs = @($normalRel, $deepRel)
& $guard -RepositoryRoot $repositoryRoot -PowerShellPaths $guardedPs -CheckpointDefinitionPaths $guardedDefs

Write-Host '       Validating Checkpoint 84 definitions and workload accounting...'
$normal = Read-Json $normalRel
$deep = Read-Json $deepRel
Assert-True ([string]$normal.checkpointId -eq '84' -and [string]$deep.checkpointId -eq '84') 'Checkpoint 84 definition ID mismatch.'
Assert-True ([string]$normal.manifestFile -eq 'CHECKPOINT_84_SHA256SUMS.txt' -and [string]$deep.manifestFile -eq 'CHECKPOINT_84_SHA256SUMS.txt') 'Checkpoint 84 manifest binding mismatch.'
Assert-True ([string]$normal.outputRoot -eq 'out/checkpoint-84' -and [string]$deep.outputRoot -eq 'out/checkpoint-84-deep-calibration') 'Checkpoint 84 output-root binding mismatch.'
Assert-True (@($normal.stages).Count -eq 11 -and [int]$normal.checkpointMetrics.stageCount -eq 11) 'Checkpoint 84 normal stage-count mismatch.'
Assert-True ([int]$normal.checkpointMetrics.monteCarloVariantCount -eq 216 -and [int]$normal.checkpointMetrics.trialsAtDefault -eq 2160000 -and [int]$normal.checkpointMetrics.smokeVariantExecutions -eq 216 -and [int]$normal.checkpointMetrics.smokeTrialsAtDefault -eq 216 -and [int]$normal.checkpointMetrics.totalTrialExecutionsAtDefault -eq 2160216) 'Checkpoint 84 normal workload mismatch.'
Assert-True (@($deep.stages).Count -eq 36 -and [int]$deep.checkpointMetrics.monteCarloVariantCount -eq 1910 -and [int]$deep.checkpointMetrics.trialsAtDefault -eq 19100000 -and [int]$deep.checkpointMetrics.smokeVariantExecutions -eq 366 -and [int]$deep.checkpointMetrics.smokeTrialsAtDefault -eq 366 -and [int]$deep.checkpointMetrics.totalTrialExecutionsAtDefault -eq 19100366) 'Checkpoint 84 Deep Calibration workload mismatch.'
$expectedNormal = @('deterministic','tl1-phase-a','tl1-phase-b','tl1-installation-space-envelope','tl1-sensor-ew-foundation','tl2-shield-capacity-power-integration-preflight','tl2-shield-capacity-power-integration-smoke','tl2-shield-capacity-power-integration-permutations','auxiliary-resource-endurance','checkpoint-53-resource-semantics-lock','runner-self-tests')
$normalIds = @($normal.stages | ForEach-Object { [string]$_.id })
Assert-True (($normalIds -join '|') -eq ($expectedNormal -join '|')) 'Checkpoint 84 normal stage ordering mismatch.'
$self = @($normal.stages | Where-Object { [string]$_.id -eq 'runner-self-tests' })
Assert-True ($self.Count -eq 1 -and [int]$self[0].metrics.selfTestCount -eq 49) 'Checkpoint 84 must expose 49 ScenarioRunner self-tests.'
Assert-True ([string]$normal.primaryStudy.id -eq 'tl2-itc10-shield-capacity-power-integration-permutations' -and [int]$normal.primaryStudy.variantCount -eq 216) 'Checkpoint 84 primary-study binding mismatch.'
Assert-True ((@($normal.nativeDependencyPrecheck.powerShellPaths) -join '|') -eq ($guardedPs -join '|')) 'Checkpoint 84 normal native-dependency PowerShell binding mismatch.'
Assert-True ((@($deep.nativeDependencyPrecheck.powerShellPaths) -join '|') -eq ($guardedPs -join '|')) 'Checkpoint 84 deep native-dependency PowerShell binding mismatch.'
Assert-True ((@($normal.nativeDependencyPrecheck.checkpointDefinitionPaths) -join '|') -eq ($guardedDefs -join '|')) 'Checkpoint 84 normal native-dependency definition binding mismatch.'
Assert-True ((@($deep.nativeDependencyPrecheck.checkpointDefinitionPaths) -join '|') -eq ($guardedDefs -join '|')) 'Checkpoint 84 deep native-dependency definition binding mismatch.'

Write-Host '       Validating accepted CP83 provenance and CP84 policy/candidate authority...'
$cp83 = Read-Json 'docs/validation/evidence/checkpoint-83/CP83_Native_Acceptance_Provenance.json'
Assert-True ([string]$cp83.status -eq 'accepted_native_windows' -and [string]$cp83.acceptance.status -eq 'Success') 'Accepted CP83 native provenance is missing or not successful.'
Assert-True ([int]$cp83.summary.unitTestsPassed -eq 863 -and [int]$cp83.summary.runnerStagesPassed -eq 11 -and [int]$cp83.summary.scenarioRunnerSelfTestsPassed -eq 48 -and [int]$cp83.summary.substantiveVariants -eq 96 -and [int]$cp83.summary.substantiveTrials -eq 960000 -and [int]$cp83.summary.failedGates -eq 0 -and [int]$cp83.summary.trialErrors -eq 0) 'Accepted CP83 native evidence metrics drifted.'
Assert-True ([string]$cp83.substantiveSummarySha256 -eq '04b39c033f19c7c7b1d1cfdaad001e13819e8b11fc072855c5e74e3753c0646a') 'Accepted CP83 substantive-summary hash drifted.'
Assert-True ([string]$cp83.repositoryManifestSha256 -eq 'ff1ee737afcd8b331d423b3dea54fd075fcfbe3ea50bd31ff30d8bf92f9719ed') 'Accepted CP83 repository-manifest hash drifted.'
Assert-True ([string]$cp83.checkpointDefinitionSha256 -eq 'cba4de1a9432117714a4926ac4f589cdfed7506971b92b29f41a995ea0034d5e') 'Accepted CP83 definition hash drifted.'

$policy = Read-Json 'docs/design/testing/checkpoint_84_validation_suite_policy_v0_1.json'
Assert-True ([int]$policy.checkpoint -eq 84 -and [string]$policy.acceptedBaseline -eq '83') 'Checkpoint 84 suite-policy identity mismatch.'
Assert-True ([int]$policy.acceptedTl2WorkingPackage.earlyPracticalFusionOperationalTp -eq 6 -and [int]$policy.acceptedTl2WorkingPackage.earlyPracticalFusionSpace -eq 6) 'Checkpoint 84 must carry the accepted CP83 reactor working candidate.'
Assert-True ([int]$policy.shieldCapacityControls.tl1ReferenceCapacity -eq 2 -and [int]$policy.shieldCapacityControls.primaryTl2CandidateCapacity -eq 3 -and [int]$policy.shieldCapacityControls.upperSensitivityCapacity -eq 4) 'Checkpoint 84 Shield-capacity sensitivity values mismatch.'
Assert-True ([int]$policy.shieldCapacityControls.shieldGeneratorSpaceHeld -eq 3 -and [int]$policy.shieldCapacityControls.baseRechargeHeld -eq 1 -and [int]$policy.shieldCapacityControls.tacticalRechargePerPowerHeld -eq 1 -and [int]$policy.shieldCapacityControls.tacticalRechargePowerCapHeld -eq 2 -and [int]$policy.shieldCapacityControls.shieldArmorHeld -eq 0) 'Checkpoint 84 Shield isolation controls mismatch.'
Assert-True (-not [bool]$policy.shieldCapacityControls.hardeningChanged -and -not [bool]$policy.shieldCapacityControls.conditionMappingChanged -and -not [bool]$policy.shieldCapacityControls.productionShieldPromoted) 'Checkpoint 84 must not bundle or promote other Shield properties.'
Assert-True ([string]$policy.permutationSuiteControls.suiteId -eq 'technology-integration-permutation-suite-v0_4' -and [string]$policy.permutationSuiteControls.studyId -eq 'tl2-itc10-shield-capacity-power-integration-permutations' -and [int]$policy.permutationSuiteControls.comparisonGroupCount -eq 18 -and [int]$policy.permutationSuiteControls.variantsPerComparisonGroup -eq 12 -and [bool]$policy.permutationSuiteControls.statefulTurnPowerPlanning) 'Checkpoint 84 permutation policy mismatch.'

$reactor = Read-Json 'docs/design/player_technology/tl2_power_reactor_candidate_profile_v0_1.json'
Assert-True ([int]$reactor.checkpoint -eq 84 -and [string]$reactor.status -eq 'validated_working_candidate_not_production_data') 'CP83 reactor result must be consolidated as a validated working candidate in CP84.'
Assert-True ([int]$reactor.tl2Candidate.normalOperationalOutput -eq 6 -and [int]$reactor.tl2Candidate.installationSpace -eq 6 -and [string]$reactor.tl2Candidate.candidateChange -eq 'operational_output_only') 'TL2 reactor working-candidate isolation mismatch.'
$reactor83 = @($reactor.acceptedEvidence | Where-Object { [string]$_.checkpoint -eq '83' })
Assert-True ($reactor83.Count -eq 1 -and [string]$reactor83[0].summarySha256 -eq '04b39c033f19c7c7b1d1cfdaad001e13819e8b11fc072855c5e74e3753c0646a') 'TL2 reactor working profile must retain accepted CP83 evidence.'

$shield = Read-Json 'docs/design/player_technology/tl2_shield_capacity_candidate_profile_v0_1.json'
Assert-True ([int]$shield.checkpoint -eq 84 -and [string]$shield.status -eq 'sensitivity_candidate_not_production_data' -and [string]$shield.researchOwnership -eq 'Shields / Defense') 'TL2 Shield candidate identity mismatch.'
Assert-True ([int]$shield.tl1Reference.installationSpace -eq 3 -and [int]$shield.tl1Reference.shieldCapacity -eq 2 -and [int]$shield.tl1Reference.baseRechargePerTurn -eq 1 -and [int]$shield.tl1Reference.tacticalRechargePerPower -eq 1 -and [int]$shield.tl1Reference.tacticalRechargePowerCap -eq 2 -and [int]$shield.tl1Reference.shieldArmor -eq 0) 'TL1 Shield reference mismatch.'
$shield3 = @($shield.tl2SensitivityCandidates | Where-Object { [int]$_.shieldCapacity -eq 3 -and [string]$_.role -eq 'primary_candidate' })
$shield4 = @($shield.tl2SensitivityCandidates | Where-Object { [int]$_.shieldCapacity -eq 4 -and [string]$_.role -eq 'upper_sensitivity' })
Assert-True ($shield3.Count -eq 1 -and $shield4.Count -eq 1) 'Shield 3 primary candidate / Shield 4 upper sensitivity roles mismatch.'
Assert-True (-not [bool]$shield.isolationControls.shieldHardenerAdded -and -not [bool]$shield.isolationControls.shieldOverloadAdded -and -not [bool]$shield.isolationControls.shieldConditionMappingChanged -and -not [bool]$shield.isolationControls.shieldPowerMaintenanceAdded -and -not [bool]$shield.isolationControls.productionValuesPromoted) 'Checkpoint 84 must isolate Shield Capacity from other Shield mechanics.'

Write-Host '       Validating Matrix v1 and standing permutation suite v0.4...'
$matrix = Read-Json 'docs/archive/player_technology/pre-cp165-active/technology_architecture_matrix_v1.json'
Assert-True ([int]$matrix.checkpoint -eq 84 -and [string]$matrix.authority.concept -eq 'docs/Star_Cluster_Game_Concept_v0.6v.docx') 'Matrix v1 CP84 authority binding mismatch.'
Assert-True ([string]$matrix.researchCategoryOwnership.powerReactor -eq 'Power / Reactor' -and [string]$matrix.researchCategoryOwnership.shield -eq 'Defensive Systems / Shields') 'Matrix v1 research ownership mismatch.'
$tl1 = @($matrix.tiers | Where-Object { [int]$_.technologyLevel -eq 1 })[0]
$tl2 = @($matrix.tiers | Where-Object { [int]$_.technologyLevel -eq 2 })[0]
Assert-True ([string]$tl2.powerReactor.status -eq 'validated_working_candidate' -and [int]$tl2.powerReactor.operationalTacticalPower -eq 6 -and [int]$tl2.powerReactor.installationSpace -eq 6) 'Matrix v1 must carry CP83 reactor working values.'
Assert-True ([int]$tl1.shield.shieldCapacity -eq 2 -and [int]$tl1.shield.installationSpace -eq 3 -and [int]$tl2.shield.shieldCapacityPrimaryCandidate -eq 3 -and [int]$tl2.shield.shieldCapacityUpperSensitivity -eq 4 -and [string]$tl2.shield.status -eq 'hypothesis') 'Matrix v1 Shield progression mismatch.'
Assert-True ([string]$matrix.workingPackages.tl2PowerReactorCandidate -eq 'docs/design/player_technology/tl2_power_reactor_candidate_profile_v0_1.json' -and [string]$matrix.workingPackages.tl2ShieldCapacityCandidate -eq 'docs/design/player_technology/tl2_shield_capacity_candidate_profile_v0_1.json') 'Matrix v1 working-package bindings mismatch.'

$suite = Read-Json 'docs/design/testing/technology_integration_permutation_suite_v0_4.json'
Assert-True ([string]$suite.id -eq 'technology-integration-permutation-suite-v0_4' -and [int]$suite.checkpoint -eq 84) 'Standing permutation suite v0.4 identity mismatch.'
Assert-True (@($suite.reusableAxes.powerReactorPackage).Count -ge 2 -and @($suite.reusableAxes.shieldCapacityPackage).Count -eq 4) 'Standing suite v0.4 must expose Power/Reactor and Shield axes.'
Assert-True ([int]$suite.powerReactorPackages.'tl1-peak-fission-5tp'.operationalTacticalPower -eq 5 -and [int]$suite.powerReactorPackages.'tl2-early-fusion-6tp-working'.operationalTacticalPower -eq 6) 'Standing suite v0.4 reactor packages mismatch.'
Assert-True ([int]$suite.shieldCapacityPackages.'tl1-shield-2'.shieldCapacity -eq 2 -and [int]$suite.shieldCapacityPackages.'tl2-shield-3-candidate'.shieldCapacity -eq 3 -and [int]$suite.shieldCapacityPackages.'shield-4-upper-sensitivity'.shieldCapacity -eq 4) 'Standing suite v0.4 Shield packages mismatch.'
Assert-True ([string]$suite.currentCoverage.currentStudy.id -eq 'tl2-itc10-shield-capacity-power-integration-permutations' -and [int]$suite.currentCoverage.currentStudy.variantCount -eq 216) 'Standing suite v0.4 current-study binding mismatch.'
Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot 'docs\design\testing\technology_integration_permutation_suite_v0_3.json') -PathType Leaf) 'Historical permutation suite v0.3 must remain for CP83 reproducibility.'

Write-Host '       Validating the 216-variant Shield Capacity / Power study independently...'
$studyRel = 'src/StarCluster.ScenarioRunner/Scenarios/TL1Calibration/tl2-itc10-shield-capacity-power-integration-permutations.json'
$study = Read-Json $studyRel
Assert-True ([string]$study.id -eq 'tl2-itc10-shield-capacity-power-integration-permutations' -and @($study.variants).Count -eq 216) 'Checkpoint 84 study identity/variant count mismatch.'
Assert-True (@($study.builds).Count -eq 1 -and [string]$study.builds[0].id -eq 'balanced_generalist_ew_major' -and [int]$study.builds[0].usedSpace -eq 35 -and [int]$study.builds[0].mainWeaponCount -eq 1 -and [int]$study.builds[0].mainReactorCount -eq 1 -and [bool]$study.builds[0].activeSensor -and [bool]$study.builds[0].shieldGenerator -and [int]$study.builds[0].kineticPdsCount -eq 1 -and [bool]$study.builds[0].ecmSuite -and [bool]$study.builds[0].eccmSuite) 'Checkpoint 84 fixed 35-Space EW/Shield fixture mismatch.'
$uniqueIds = @($study.variants | ForEach-Object { [string]$_.id } | Sort-Object -Unique)
Assert-True ($uniqueIds.Count -eq 216) 'Checkpoint 84 variant IDs must be unique.'
foreach ($capacity in @(2,3,4)) {
    Assert-True (@($study.variants | Where-Object { [int]$_.sideAShieldCapacityOverride -eq $capacity }).Count -eq 72) "Checkpoint 84 must contain exactly 72 Side-A Shield $capacity variants."
}
foreach ($output in @(5,6)) {
    Assert-True (@($study.variants | Where-Object { [int]$_.sideAReactorOutputOverride -eq $output }).Count -eq 108) "Checkpoint 84 must contain exactly 108 Side-A Reactor $output variants."
}
$groups = @($study.variants | Group-Object comparisonGroup)
Assert-True ($groups.Count -eq 18 -and @($groups | Where-Object { $_.Count -ne 12 }).Count -eq 0) 'Checkpoint 84 requires 18 comparison groups with twelve variants each.'
$familiesA = @($study.variants | ForEach-Object { [string]$_.sideAFamily } | Sort-Object -Unique)
$familiesB = @($study.variants | ForEach-Object { [string]$_.sideBFamily } | Sort-Object -Unique)
Assert-True (($familiesA -join '|') -eq 'Energy|Kinetic' -and ($familiesB -join '|') -eq 'Energy|Kinetic|Missile') 'Checkpoint 84 family coverage mismatch.'
Assert-True (@($study.variants | Where-Object { [int]$_.sideBShieldCapacityOverride -ne 2 -or [int]$_.sideBReactorOutputOverride -ne 5 -or [int]$_.sideATacticalComputerTargetingBonusOverride -ne 12 -or [int]$_.sideBTacticalComputerTargetingBonusOverride -ne 10 }).Count -eq 0) 'Checkpoint 84 Side-B/Computer controls drifted.'
Assert-True (@($study.variants | Where-Object { -not [bool]$_.baseShieldRechargeEnabled -or -not [bool]$_.pdsEnabled -or [bool]$_.evasiveManeuversEnabled -or [int]$_.startingFuel -ne 100 }).Count -eq 0) 'Checkpoint 84 power/recharge/PDS fixture drifted.'
Assert-True (@($study.variants | Where-Object { [string]$_.sideASensorOverloadPolicy -ne 'None' -or [string]$_.sideBSensorOverloadPolicy -ne 'None' -or [string]$_.sideAStlOverloadPolicy -ne 'None' -or [string]$_.sideBStlOverloadPolicy -ne 'None' }).Count -eq 0) 'Checkpoint 84 must not bundle Sensor/EW/STL overload changes.'
Assert-True (@($study.variants | Where-Object { [bool]$_.sideAAllowsApproximateDirectFire -or [bool]$_.sideBAllowsApproximateDirectFire -or [int]$_.sideAApproximateDirectFireAccuracyPenalty -ne 0 -or [int]$_.sideBApproximateDirectFireAccuracyPenalty -ne 0 }).Count -eq 0) 'Checkpoint 84 must not grant degraded fire or relax missile/direct-fire track rules.'
foreach ($group in $groups) {
    foreach ($environment in @('firm-reference','tall-dr1-eccm1')) {
        foreach ($capacity in @(2,3,4)) {
            foreach ($output in @(5,6)) {
                $label = $environment + '-s' + $capacity + '-r' + $output
                Assert-True (@($group.Group | Where-Object { [string]$_.profileLabel -eq $label }).Count -eq 1) "Checkpoint 84 group '$($group.Name)' is missing unique permutation '$label'."
            }
        }
    }
}
$firm = @($study.variants | Where-Object { [string]$_.profileLabel -like 'firm-reference-*' })
$tall = @($study.variants | Where-Object { [string]$_.profileLabel -like 'tall-dr1-eccm1-*' })
Assert-True ($firm.Count -eq 108 -and @($firm | Where-Object { [string]$_.sideASensorEwProfileId -ne 'tl1-balanced-0-control' -or [string]$_.sideBEcmPolicy -ne 'None' -or [string]$_.sideAEccmPolicy -ne 'None' }).Count -eq 0) 'Checkpoint 84 Firm-reference environment mismatch.'
Assert-True ($tall.Count -eq 108 -and @($tall | Where-Object { [string]$_.sideASensorEwProfileId -ne 'tl2-discrimination-1-candidate' -or [string]$_.sideBEcmPolicy -ne 'Normal' -or [int]$_.sideBEcmNormalRatingOverride -ne 2 -or [string]$_.sideAEccmPolicy -ne 'ReactiveNormal' -or [int]$_.sideAEccmNormalRatingOverride -ne 1 }).Count -eq 0) 'Checkpoint 84 tall DR1 + reactive ECCM1 environment mismatch.'

Write-Host '       Auditing CP84 actual-consumer integration, telemetry, gates, and report routing...'
$documents = Read-Text 'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatDocuments.cs'
Assert-True ($documents.Contains('sideAShieldCapacityOverride') -and $documents.Contains('sideBShieldCapacityOverride')) 'Scenario document does not expose per-side Shield Capacity overrides.'
$runner = Read-Text 'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs'
$studySymbol = 'Tl2ShieldCapacityPowerIntegrationStudyId'
Assert-True ((Count-Substring $runner $studySymbol) -eq 11) 'CP84 study ID must occur in exactly 11 integrated ScenarioRunner registration/consumer locations.'
Assert-True ($runner.Contains('ApplyShieldCapacityOverride(') -and $runner.Contains('return technology with { ShieldCapacity = shieldCapacity };')) 'CP84 Shield Capacity override consumer is missing or not isolated.'
Assert-True ($runner.Contains('TacticalShieldRechargeOpportunitiesA') -and $runner.Contains('TacticalShieldRechargePowerSpentA') -and $runner.Contains('TacticalShieldRechargeDeniedByReserveA') -and $runner.Contains('TacticalShieldRechargeOpportunitiesB') -and $runner.Contains('TacticalShieldRechargePowerSpentB') -and $runner.Contains('TacticalShieldRechargeDeniedByReserveB')) 'CP84 side-specific shield-recharge telemetry is incomplete.'
Assert-True ($runner.Contains('bool tacticalRechargeDeniedByReserve = tacticalRechargeOpportunity') -and $runner.Contains('reserveAfterRecharge')) 'CP84 stateful recharge reserve-denial consumer is missing.'
Assert-True ($runner.Contains('IsStatefulAuxiliaryStudy(string studyId) =>') -and $runner.Contains('studyId == Tl2ShieldCapacityPowerIntegrationStudyId')) 'CP84 must route through stateful turn-power planning.'
$buildGates = $runner.IndexOf('private static IReadOnlyList<Tl1IntegratedTacticalCombatGate> BuildGates', [System.StringComparison]::Ordinal)
Assert-True ($buildGates -gt 0) 'ScenarioRunner BuildGates function is missing.'
$c84Start = $runner.IndexOf('if (study.Id == Tl2ShieldCapacityPowerIntegrationStudyId)', $buildGates, [System.StringComparison]::Ordinal)
$c84End = $runner.IndexOf('if (IsCheckpoint57Study(study.Id))', $c84Start, [System.StringComparison]::Ordinal)
Assert-True ($c84Start -gt $buildGates -and $c84End -gt $c84Start) 'CP84 release-gate block could not be isolated inside BuildGates.'
$c84Gates = $runner.Substring($c84Start, $c84End - $c84Start)
$expectedGates = @(
    'tl2-c84-variant-coverage','tl2-c84-factorial-pairing-complete','tl2-c84-shield-capacity-isolation',
    'tl2-c84-reactor-working-candidate-held','tl2-c84-firm-reference-clean','tl2-c84-contemporary-dr1-eccm1-restores-firm',
    'tl2-c84-stateful-recharge-consumer-path','tl2-c84-no-recharge-hardening-overload-bundle','tl2-c84-no-evasive-compensation',
    'tl2-c84-no-production-shield-promotion','tl2-c84-outcomes-review-only')
foreach ($gate in $expectedGates) {
    Assert-True ((Count-Substring $c84Gates ('"' + $gate + '"')) -eq 1) "CP84 release-gate block must contain exactly one '$gate' gate."
}
Assert-True (([regex]::Matches($c84Gates, '"tl2-c84-[a-z0-9-]+"')).Count -eq 11) 'CP84 release-gate block must contain exactly 11 CP84 gates.'
Assert-True ($runner.Contains('ValidateTl2ShieldCapacityPowerIntegrationCoverage(') -and $runner.Contains('WriteTl2ShieldCapacityPowerIntegrationReview(') -and $runner.Contains('tl2-shield-capacity-power-integration-review.csv') -and $runner.Contains('tl2-shield-capacity-power-integration-paired-deltas.csv')) 'CP84 validation or report routing is incomplete.'
$selfTests = Read-Text 'src/StarCluster.ScenarioRunner/ScenarioRunnerSelfTests.cs'
Assert-True ($selfTests.Contains('CP84 Shield Capacity override preserves recharge, armor, reactor, and weapons') -and $selfTests.Contains('TestCp84ShieldCapacityOverrideSemantics')) 'CP84 Shield isolation self-test is missing.'

Write-Host '       Validating frozen production boundaries and authoritative documents...'
$baseline = Read-Text 'docs/archive/player_technology/pre-cp165-active/tl1_core_combat_numerical_baseline_v0_3.csv'
Assert-True ($baseline.Contains('Power,reactor_output,Main Reactor Tactical Power,5,TP per turn,TL1 Fission Reactor')) 'Production TL1 reactor output must remain 5 TP.'
Assert-True ($baseline.Contains('Shield,capacity') -or $baseline.Contains('Shield Capacity')) 'TL1 numerical baseline must retain its shield reference.'
$productionApproximateEnable = Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'src') -Recurse -File -Filter '*.cs' | Where-Object { $_.FullName -notlike '*StarCluster.ScenarioRunner*' } | Select-String -SimpleMatch 'allowsApproximateTrackFire: true'
Assert-True (@($productionApproximateEnable).Count -eq 0) 'Checkpoint 84 must not enable degraded fire on production Core/Game weapon construction.'
$missileDoc = Read-Text 'docs/design/Missile_Guidance_Datalink_Sensor_And_Seeker_Architecture.md'
Assert-True ($missileDoc.Contains('Ordinary missile profiles continue to require the legitimate Firm terminal solution')) 'Ordinary missile Firm-terminal architecture must remain preserved.'
$conceptText = Read-DocxText 'docs/Star_Cluster_Game_Concept_v0.6v.docx'
Assert-True ($conceptText.Contains('Checkpoint 83') -and $conceptText.Contains('6 Operational Tactical Power') -and $conceptText.Contains('validated') -and $conceptText.Contains('Operational output only')) 'Concept v0.6v must consolidate the accepted CP83 reactor result.'
Assert-True ($conceptText.Contains('Technology Integration Permutation Suite v0.4') -and $conceptText.Contains('Shield Capacity') -and $conceptText.Contains('C-058')) 'Concept v0.6v must document the CP84 Shield capacity integration study and suite v0.4.'
$matrixMd = Read-Text 'docs/design/player_technology/Technology_Architecture_Matrix_v1.md'
Assert-True ($matrixMd.Contains('Checkpoint 83') -and $matrixMd.Contains('validated working candidate') -and $matrixMd.Contains('Shield Capacity') -and $matrixMd.Contains('Checkpoint 84')) 'Technology Architecture Matrix v1 Markdown is not synchronized with CP83/CP84.'
$wbXml = Read-ZipEntryText 'docs/design/player_technology/StarCluster_Technology_Architecture_Matrix_v1.xlsx' 'xl/workbook.xml'
Assert-True ($wbXml.Contains('Power &amp; Reactor') -and $wbXml.Contains('Shields') -and $wbXml.Contains('TL2 Candidate') -and $wbXml.Contains('Architecture Matrix')) 'Matrix workbook is missing the Power/Reactor, Shields, TL2 Candidate, or Architecture Matrix sheet.'

Write-Host '       Proving CP84 changed no production Core/Game/tests and no unrelated ScenarioRunner consumers...'
$frozenManifest = Read-Text 'docs/validation/evidence/checkpoint-83/CHECKPOINT_83_SHA256SUMS.txt'
$frozenLines = @($frozenManifest -split "`r?`n" | Where-Object { $_ -match '^[0-9a-f]{64}  (src/StarCluster\.Core/|src/StarCluster\.Game/|tests/)' })
Assert-True ($frozenLines.Count -gt 300) 'Accepted CP83 frozen Core/Game/tests manifest coverage is unexpectedly small.'
foreach ($line in $frozenLines) {
    $m = [regex]::Match($line, '^([0-9a-f]{64})  (.+)$')
    Assert-True ($m.Success) 'Malformed CP83 frozen manifest line.'
    $relative = $m.Groups[2].Value
    $path = Join-Path $repositoryRoot ($relative.Replace('/','\'))
    Assert-True (Test-Path -LiteralPath $path -PathType Leaf) "Frozen CP83 file '$relative' is missing."
    $actual = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    Assert-True ($actual -eq $m.Groups[1].Value.ToLowerInvariant()) "Checkpoint 84 unexpectedly changed frozen production/test file '$relative'."
}
Write-Host ("       Frozen Core/Game/tests hashes: {0} files matched accepted Checkpoint 83." -f $frozenLines.Count)

$allowedScenarioRunnerChanges = @(
    'src/StarCluster.ScenarioRunner/ScenarioRunnerSelfTests.cs',
    'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatDocuments.cs',
    'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs'
)
$scenarioLines = @($frozenManifest -split "`r?`n" | Where-Object { $_ -match '^[0-9a-f]{64}  src/StarCluster\.ScenarioRunner/' })
Assert-True ($scenarioLines.Count -gt 100) 'Accepted CP83 ScenarioRunner manifest coverage is unexpectedly small.'
foreach ($line in $scenarioLines) {
    $m = [regex]::Match($line, '^([0-9a-f]{64})  (.+)$')
    $relative = $m.Groups[2].Value
    if ($allowedScenarioRunnerChanges -contains $relative) { continue }
    $path = Join-Path $repositoryRoot ($relative.Replace('/','\'))
    Assert-True (Test-Path -LiteralPath $path -PathType Leaf) "Frozen CP83 ScenarioRunner file '$relative' is missing."
    $actual = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    Assert-True ($actual -eq $m.Groups[1].Value.ToLowerInvariant()) "Checkpoint 84 unexpectedly changed unrelated ScenarioRunner file '$relative'."
}

Write-Host '       Validating active-document/archive hygiene...'
$activeConcepts = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs') -File -Filter 'Star_Cluster_Game_Concept_v*.docx')
Assert-True ($activeConcepts.Count -eq 1 -and $activeConcepts[0].Name -eq 'Star_Cluster_Game_Concept_v0.6v.docx') 'Exactly Concept v0.6v must remain active under docs/.'
Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot 'docs\archive\Star_Cluster_Game_Concept_v0.6u.docx') -PathType Leaf) 'Accepted Concept v0.6u must be archived.'
$oldConceptMatch = [regex]::Match($frozenManifest, '(?im)^([0-9a-f]{64})  docs/Star_Cluster_Game_Concept_v0\.6u\.docx$')
Assert-True ($oldConceptMatch.Success) 'Accepted CP83 manifest is missing Concept v0.6u.'
$archivedOldConcept = Join-Path $repositoryRoot 'docs\archive\Star_Cluster_Game_Concept_v0.6u.docx'
$archivedHash = (Get-FileHash -LiteralPath $archivedOldConcept -Algorithm SHA256).Hash.ToLowerInvariant()
Assert-True ($archivedHash -eq $oldConceptMatch.Groups[1].Value.ToLowerInvariant()) 'Archived Concept v0.6u bytes drifted from accepted CP83.'
$validationFiles = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs\validation') -File -Filter 'Checkpoint_*.md')
Assert-True ($validationFiles.Count -eq 1 -and $validationFiles[0].Name -eq 'Checkpoint_84_TL2_Shield_Capacity_Power_Integration_Permutation_Suite.md') 'Exactly one Checkpoint 84 active validation runbook must remain.'
Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot 'docs\validation\archive\Checkpoint_83_TL2_Power_Reactor_Progression_Permutation_Suite.md') -PathType Leaf) 'Accepted Checkpoint 83 validation runbook must be archived.'
Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot 'docs\validation\evidence\checkpoint-83\CHECKPOINT_83_SHA256SUMS.txt') -PathType Leaf) 'Accepted CP83 repository manifest must be preserved as evidence.'
$rootTxt = @(Get-ChildItem -LiteralPath $repositoryRoot -File -Filter '*.txt')
Assert-True ($rootTxt.Count -eq 1 -and $rootTxt[0].Name -eq 'CHECKPOINT_84_SHA256SUMS.txt') 'Repository root must contain only CHECKPOINT_84_SHA256SUMS.txt as .txt.'

Write-Host '       CP84 isolation: Shield Capacity 2/3/4 x Reactor 5/6; recharge, hardening, condition mapping, and Space held.'
Write-Host '       Standing suite: 18 combat/geometry groups x 2 information-control environments x 3 Shield capacities x 2 reactor outputs = 216 variants.'
Write-Host '       Normal workload: 11 stages / 216 substantive variants / 2,160,000 default substantive trials plus 216 smoke trials.'
Write-Host 'Checkpoint 84 contract validation passed.'
