[CmdletBinding()]
param()

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path

function Assert-True([bool]$Condition, [string]$Message) { if (-not $Condition) { throw $Message } }
function Read-Json([string]$Path) { Assert-True (Test-Path -LiteralPath $Path -PathType Leaf) "Missing JSON file: $Path"; return (Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json) }
function Find-ById($Items, [string]$Id) { foreach ($item in @($Items)) { if ([string]$item.id -eq $Id) { return $item } }; return $null }

$baseline = Read-Json (Join-Path $repositoryRoot 'docs\design\player_technology\tl1_35_space_player_cruiser_baseline_v0_5.json')
$envelope = Read-Json (Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\Scenarios\ArchitectureTechnology\tl1-space01-35-space-construction-envelope.json')
$study = Read-Json (Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\Scenarios\TL1Calibration\tl1-itc06-35-space-operational-sensor-acquisition-ew.json')
$profiles = Read-Json (Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\Scenarios\ArchitectureTechnology\tl1-tl2-standard-runtime-profiles-v0_3.json')
$schema = Read-Json (Join-Path $repositoryRoot 'docs\design\player_technology\tl1_integrated_tactical_combat_schema_v0_9.json')
$policy = Read-Json (Join-Path $repositoryRoot 'docs\design\testing\checkpoint_63_validation_suite_policy_v0_1.json')
$active = Read-Json (Join-Path $repositoryRoot 'tools\calibration\checkpoints\checkpoint-63b.json')
$deep = Read-Json (Join-Path $repositoryRoot 'tools\calibration\checkpoints\checkpoint-63b-deep-calibration.json')
Assert-True ([string]$active.checkpointId -eq '63b' -and [string]$deep.checkpointId -eq '63b') 'Checkpoint 63b definitions must identify checkpoint 63b.'
Assert-True ([string]$active.manifestFile -eq 'CHECKPOINT_63B_SHA256SUMS.txt' -and [string]$deep.manifestFile -eq 'CHECKPOINT_63B_SHA256SUMS.txt') 'Checkpoint 63b definitions must bind the current CHECKPOINT_63B_SHA256SUMS.txt manifest.'
Assert-True ([string]$active.outputRoot -eq 'out/checkpoint-63b' -and [string]$deep.outputRoot -eq 'out/checkpoint-63b-deep-calibration') 'Checkpoint 63b output roots must be checkpoint-specific.'
Assert-True (@($active.documentation) -contains 'docs/validation/Checkpoint_63b_Manifest_Binding_Hotfix.md' -and @($deep.documentation) -contains 'docs/validation/Checkpoint_63b_Manifest_Binding_Hotfix.md') 'Checkpoint 63b definitions must reference the active 63b runbook.'

Assert-True ([int]$baseline.checkpoint -eq 63) 'TL1 baseline must identify Checkpoint 63.'
Assert-True ([int]$baseline.installationSpace.playerCruiserTotal -eq 35) 'TL1 player cruiser must remain 35 Space.'
Assert-True ([int]$baseline.installationSpace.mandatoryCoreTotal -eq 25) 'TL1 mandatory core must remain 25 Space.'
Assert-True ([int]$baseline.deterministicArchitectureEnvelope.macroLoadoutCount -eq 27) 'Deterministic envelope must retain 27 macro loadouts.'
Assert-True ([int]$baseline.deterministicArchitectureEnvelope.weaponPowerVariantCount -eq 96) 'Deterministic envelope must retain 96 weapon/power variants.'
Assert-True ([int]$baseline.operationalSensorAcquisitionStudy.variantCount -eq 72) 'Checkpoint 63 baseline must define 72 sensor/acquisition variants.'
Assert-True ([int]$baseline.operationalSensorAcquisitionStudy.productionReactorOutput -eq 5) 'Production TL1 reactor output must remain 5 TP.'
Assert-True ([string]$baseline.operationalSensorAcquisitionStudy.tacticalPowerDoctrine -eq 'FullVolleyFirst') 'Checkpoint 63 must use FullVolleyFirst for offensive isolation.'
Assert-True (-not [bool]$baseline.operationalSensorAcquisitionStudy.balanceTargetsBlocking) 'Checkpoint 63 outcomes must remain diagnostic rather than target-gated.'
Assert-True ([int]$baseline.operationalSensorAcquisitionStudy.acceptedSensorEnvelope.passiveFirm -eq 3 -and [int]$baseline.operationalSensorAcquisitionStudy.acceptedSensorEnvelope.passiveApproximate -eq 5) 'Passive TL1 sensor envelope mismatch.'
Assert-True ([int]$baseline.operationalSensorAcquisitionStudy.acceptedSensorEnvelope.active1Firm -eq 5 -and [int]$baseline.operationalSensorAcquisitionStudy.acceptedSensorEnvelope.active2Firm -eq 6) 'Active TL1 Firm envelope mismatch.'

Assert-True ([string]$envelope.id -eq 'tl1-space01-35-space-construction-envelope' -and [int]$envelope.checkpoint -eq 60) 'Checkpoint 60 deterministic envelope must remain frozen as the construction source.'
Assert-True (@($envelope.referenceBuilds).Count -eq 7) 'Envelope must retain six legal builds plus the 37-Space illegal control.'

$production = Find-ById $profiles.profiles 'tl1-production'
Assert-True ($null -ne $production) 'TL1 production runtime profile is missing.'
Assert-True ([int]$production.powerAndControl.reactorOutput -eq 5) 'Checkpoint 63b may not silently change the production TL1 reactor from 5 TP.'

Assert-True ([string]$study.id -eq 'tl1-itc06-35-space-operational-sensor-acquisition-ew') 'Unexpected Checkpoint 63b study ID.'
Assert-True (@($study.builds).Count -eq 6) 'Checkpoint 63b study must define all six accepted legal composed builds.'
Assert-True (@($study.variants).Count -eq 72) 'Checkpoint 63b study must define exactly 72 variants.'
$expectedBuildIds = @('balanced_generalist_major','dual_main_striker_major','dual_reactor_power_core','pds_saturator','dual_main_dual_pds','shielded_pds_fortress')
$buildIds = @($study.builds | ForEach-Object { [string]$_.id })
Assert-True (($buildIds | Select-Object -Unique).Count -eq 6) 'Checkpoint 63b build IDs must be unique.'
foreach ($id in $expectedBuildIds) { Assert-True ($buildIds -contains $id) "Missing Checkpoint 63 build: $id" }

$families = @('Kinetic','Energy','Missile')
$regimes = @(
    @{ Label='established-firm-control'; Policy='EstablishedFirm'; Ew=0 },
    @{ Label='operational-passive-clear'; Policy='PassiveOnly'; Ew=0 },
    @{ Label='operational-auto-active-clear'; Policy='AutoActive'; Ew=0 },
    @{ Label='operational-auto-active-ew1'; Policy='AutoActive'; Ew=1 }
)
foreach ($buildId in $expectedBuildIds) {
    $build = Find-ById $study.builds $buildId
    foreach ($family in $families) {
        $paired = @($study.variants | Where-Object { [string]$_.sideABuildId -eq $buildId -and [string]$_.sideAFamily -eq $family })
        Assert-True ($paired.Count -eq 4) "Expected four paired acquisition variants for $buildId / $family."
        Assert-True (@($paired | ForEach-Object { [string]$_.comparisonGroup } | Select-Object -Unique).Count -eq 1) "Paired acquisition lane must share one comparisonGroup for $buildId / $family."
        foreach ($regime in $regimes) {
            $matches = @($paired | Where-Object { [string]$_.profileLabel -eq $regime.Label -and [string]$_.sideATrackPolicy -eq $regime.Policy -and [int]$_.sideANetEwRangePenalty -eq $regime.Ew })
            Assert-True ($matches.Count -eq 1) "Missing unique $buildId / $family / $($regime.Label) variant."
            $v = $matches[0]
            Assert-True ([string]$v.sideBBuildId -eq 'balanced_generalist_major' -and [string]$v.sideBFamily -eq 'Missile') "Variant $($v.id) must use the balanced Missile opponent."
            Assert-True ([string]$v.sideATacticalPowerDoctrine -eq 'FullVolleyFirst' -and [string]$v.sideBTacticalPowerDoctrine -eq 'FullVolleyFirst') "Variant $($v.id) must use FullVolleyFirst on both sides."
            Assert-True ([int]$v.sideAReactorOutputOverride -eq 5 -and [int]$v.sideBReactorOutputOverride -eq 5) "Variant $($v.id) must hold reactor output at production 5 TP."
            Assert-True ([string]$v.sideBTrackPolicy -eq 'EstablishedFirm' -and [int]$v.sideBNetEwRangePenalty -eq 0) "Variant $($v.id) must retain established-Firm Side B control."
            Assert-True ([string]$v.sideAProfileId -eq 'tl1-production' -and [string]$v.sideBProfileId -eq 'tl1-production') "Variant $($v.id) must use TL1 production profiles."
            Assert-True ([string]$v.sideAAuxiliaryProfileId -eq 'aux-r53-none-tl1' -and [string]$v.sideBAuxiliaryProfileId -eq 'aux-r53-none-tl1') "Variant $($v.id) must use zero-effect AUX profiles."
            Assert-True ([string]$v.movementMode -eq 'OpponentAwareRange' -and [int]$v.initialRangeHexes -eq 4) "Variant $($v.id) must use the Range-4 opponent-aware control."
            if ([int]$build.mainWeaponCount -eq 2) {
                Assert-True ([string]$v.sideASecondaryFamily -eq $family) "Dual-main variant $($v.id) must duplicate its Side-A family."
            } else {
                Assert-True ($null -eq $v.PSObject.Properties['sideASecondaryFamily']) "Single-main variant $($v.id) may not install a secondary family."
            }
        }
    }
}

$variantProps = $schema.'$defs'.variant.properties
Assert-True ($null -ne $variantProps.sideATrackPolicy -and $null -ne $variantProps.sideBTrackPolicy) 'Integrated-combat schema v0.9 is missing track-policy fields.'
Assert-True ($null -ne $variantProps.sideANetEwRangePenalty -and $null -ne $variantProps.sideBNetEwRangePenalty) 'Integrated-combat schema v0.9 is missing net-EW range fields.'
Assert-True ($null -ne $variantProps.sideATacticalPowerDoctrine -and $null -ne $variantProps.sideAReactorOutputOverride) 'Integrated-combat schema v0.9 must retain Checkpoint 62 power controls.'

$must = @($policy.mustAlwaysRunStageIds)
$deepOnly = @($policy.deepCalibrationStageIds)
Assert-True ($must.Count -eq 8 -and $must -contains 'tl1-operational-sensor-acquisition-ew' -and -not ($must -contains 'tl1-power-doctrine-reactor-sensitivity')) 'Checkpoint 63b normal suite must contain the current sensor study and retire Checkpoint 62 Monte Carlo from the normal lineup.'
Assert-True ($deepOnly.Count -eq 14 -and $deepOnly -contains 'tl1-power-doctrine-reactor-sensitivity' -and $deepOnly -contains 'tl1-composed-ship-odd-build-combat') 'Checkpoint 63b Deep Calibration must retain Checkpoints 62 and 61 plus twelve historical stochastic stages.'
Assert-True ([int]$active.checkpointMetrics.stageCount -eq 8 -and [int]$active.checkpointMetrics.monteCarloVariantCount -eq 72 -and [int]$active.checkpointMetrics.trialsAtDefault -eq 720000) 'Checkpoint 63b active workload metrics mismatch.'
Assert-True ([int]$deep.checkpointMetrics.stageCount -eq 22 -and [int]$deep.checkpointMetrics.monteCarloVariantCount -eq 1260 -and [int]$deep.checkpointMetrics.trialsAtDefault -eq 12600000) 'Checkpoint 63b Deep workload metrics mismatch.'
$activeIds = @($active.stages | ForEach-Object { [string]$_.id })
$deepIds = @($deep.stages | ForEach-Object { [string]$_.id })
Assert-True ($activeIds[3] -eq 'tl1-installation-space-envelope' -and $activeIds[4] -eq 'tl1-operational-sensor-acquisition-ew') 'Checkpoint 63b construction/sensor stages are out of order.'
Assert-True ($deepIds[4] -eq 'tl1-operational-sensor-acquisition-ew' -and $deepIds[5] -eq 'tl1-power-doctrine-reactor-sensitivity' -and $deepIds[6] -eq 'tl1-composed-ship-odd-build-combat') 'Checkpoint 63b Deep Calibration must run current sensor study before Checkpoints 62 and 61 historical regressions.'

$runnerPath = Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\TL1Calibration\Tl1IntegratedTacticalCombatRunner.cs'
$docPath = Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\TL1Calibration\Tl1IntegratedTacticalCombatDocuments.cs'
$runner = Get-Content -LiteralPath $runnerPath -Raw
$docs = Get-Content -LiteralPath $docPath -Raw
Assert-True ($docs -match 'Tl1OperationalTrackPolicy' -and $docs -match 'sideANetEwRangePenalty') 'Integrated combat document model is missing Checkpoint 63b track/EW controls.'
Assert-True ($runner -match 'tl1-itc06-35-space-operational-sensor-acquisition-ew') 'Integrated runner is missing the Checkpoint 63b study ID.'
Assert-True ($runner -match 'AllocateOperationalSensor' -and $runner -match 'ResolveTrackQuality' -and $runner -match 'TrackUnavailable') 'Integrated runner is missing operational sensor acquisition/fire-authorization behavior.'
Assert-True ($runner -match 'operational-sensor-acquisition-matrix.csv' -and $runner -match 'tl1-c63-outcomes-review-only') 'Integrated runner is missing Checkpoint 63b review outputs/gates.'
Assert-True ($runner -match 'A lane may legitimately remain NoTrack' -and $runner -match 'sensorEnvelope.PassiveFirmRange' -and $runner -match 'sensorlessBuildIds.All') 'Checkpoint 63b passive-core hotfix gate semantics are missing.'

$validationFiles = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs\validation') -File -Filter '*.md')
Assert-True ($validationFiles.Count -eq 1 -and $validationFiles[0].Name -eq 'Checkpoint_63b_Manifest_Binding_Hotfix.md') 'Exactly one Checkpoint 63b active validation runbook must remain.'
Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot 'docs\validation\archive\Checkpoint_63a_Passive_Core_Gate_Hotfix.md') -PathType Leaf) 'Superseded Checkpoint 63a runbook must be archived.'
Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot 'docs\validation\archive\Checkpoint_63_TL1_Operational_Sensor_Acquisition_And_EW.md') -PathType Leaf) 'Superseded Checkpoint 63 runbook must be archived.'
Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot 'docs\validation\archive\Checkpoint_62_TL1_Tactical_Power_Doctrine_And_Reactor_Output_Sensitivity.md') -PathType Leaf) 'Checkpoint 62 runbook must remain archived.'

$rootTxt = @(Get-ChildItem -LiteralPath $repositoryRoot -File -Filter '*.txt')
Assert-True ($rootTxt.Count -eq 1 -and $rootTxt[0].Name -eq 'CHECKPOINT_63B_SHA256SUMS.txt') 'Repository root must contain only the current Checkpoint 63b manifest as a .txt file.'
$archivedTxt = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs\archive') -Recurse -File -Filter '*.txt')
Assert-True ($archivedTxt.Count -eq 0) 'Generated historical checkpoint .txt artifacts must not remain under docs/archive.'

Write-Host '       Checkpoint 63b design contract: six accepted TL1 builds x three weapon families x four paired acquisition regimes = 72 variants.'
Write-Host '       Production TL1 reactor remains 5 TP; FullVolleyFirst isolates sensing from known power-allocation pathology.'
Write-Host '       All cruisers retain passive sensing; optional active sensors extend range at 1/2 TP and Side B remains established-Firm.'
Write-Host '       No target win rate is a release gate; contextual capabilities such as Energy APEN remain preserved for relevant matchups.'
Write-Host '       Validation tiers: 8 normal stages / 72 MC variants; Deep Calibration 22 stages / 1,260 MC variants.'
