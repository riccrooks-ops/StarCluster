[CmdletBinding()]
param()

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path

function Assert-True([bool]$Condition, [string]$Message) { if (-not $Condition) { throw $Message } }
function Read-Json([string]$Path) { Assert-True (Test-Path -LiteralPath $Path -PathType Leaf) "Missing JSON file: $Path"; return (Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json) }
function Find-ById($Items, [string]$Id) { foreach ($item in @($Items)) { if ([string]$item.id -eq $Id) { return $item } }; return $null }

$baseline = Read-Json (Join-Path $repositoryRoot 'docs\design\player_technology\tl1_35_space_player_cruiser_baseline_v0_6.json')
$study = Read-Json (Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\Scenarios\TL1Calibration\tl1-itc07-35-space-track-aware-movement-acquisition.json')
$profiles = Read-Json (Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\Scenarios\ArchitectureTechnology\tl1-tl2-standard-runtime-profiles-v0_3.json')
$schema = Read-Json (Join-Path $repositoryRoot 'docs\design\player_technology\tl1_integrated_tactical_combat_schema_v0_10.json')
$policy = Read-Json (Join-Path $repositoryRoot 'docs\design\testing\checkpoint_64_validation_suite_policy_v0_1.json')
$active = Read-Json (Join-Path $repositoryRoot 'tools\calibration\checkpoints\checkpoint-64.json')
$deep = Read-Json (Join-Path $repositoryRoot 'tools\calibration\checkpoints\checkpoint-64-deep-calibration.json')

Assert-True ([string]$active.checkpointId -eq '64' -and [string]$deep.checkpointId -eq '64') 'Checkpoint 64 definitions must identify checkpoint 64.'
Assert-True ([string]$active.manifestFile -eq 'CHECKPOINT_64_SHA256SUMS.txt' -and [string]$deep.manifestFile -eq 'CHECKPOINT_64_SHA256SUMS.txt') 'Checkpoint 64 definitions must bind CHECKPOINT_64_SHA256SUMS.txt.'
Assert-True ([string]$active.outputRoot -eq 'out/checkpoint-64' -and [string]$deep.outputRoot -eq 'out/checkpoint-64-deep-calibration') 'Checkpoint 64 output roots must be checkpoint-specific.'
Assert-True (@($active.documentation) -contains 'docs/validation/Checkpoint_64_TL1_Track_Aware_Movement_And_Acquisition.md' -and @($deep.documentation) -contains 'docs/validation/Checkpoint_64_TL1_Track_Aware_Movement_And_Acquisition.md') 'Checkpoint 64 definitions must reference the active runbook.'

Assert-True ([int]$baseline.checkpoint -eq 64) 'TL1 baseline must identify Checkpoint 64.'
Assert-True ([int]$baseline.installationSpace.playerCruiserTotal -eq 35 -and [int]$baseline.installationSpace.mandatoryCoreTotal -eq 25) 'TL1 35-Space construction baseline changed unexpectedly.'
Assert-True ([int]$baseline.trackAwareMovementAcquisitionStudy.variantCount -eq 90) 'Checkpoint 64 baseline must define 90 track-aware variants.'
Assert-True ([int]$baseline.trackAwareMovementAcquisitionStudy.productionReactorOutput -eq 5) 'Production TL1 reactor output must remain 5 TP.'
Assert-True ([string]$baseline.trackAwareMovementAcquisitionStudy.tacticalPowerDoctrine -eq 'FullVolleyFirst') 'Checkpoint 64 must retain FullVolleyFirst.'
Assert-True (-not [bool]$baseline.trackAwareMovementAcquisitionStudy.balanceTargetsBlocking) 'Checkpoint 64 outcomes must remain diagnostic.'

$production = Find-ById $profiles.profiles 'tl1-production'
Assert-True ($null -ne $production -and [int]$production.powerAndControl.reactorOutput -eq 5) 'TL1 production runtime profile must remain 5 TP.'

Assert-True ([string]$study.id -eq 'tl1-itc07-35-space-track-aware-movement-acquisition') 'Unexpected Checkpoint 64 study ID.'
Assert-True (@($study.builds).Count -eq 6) 'Checkpoint 64 study must define all six accepted builds.'
Assert-True (@($study.variants).Count -eq 90) 'Checkpoint 64 study must define exactly 90 variants.'
$expectedBuildIds = @('balanced_generalist_major','dual_main_striker_major','dual_reactor_power_core','pds_saturator','dual_main_dual_pds','shielded_pds_fortress')
$expectedBuilds = @{
    balanced_generalist_major = @(1,1,$true,$true,1,33,2)
    dual_main_striker_major = @(2,1,$true,$false,0,34,1)
    dual_reactor_power_core = @(1,2,$true,$false,0,34,1)
    pds_saturator = @(1,1,$false,$false,5,35,0)
    dual_main_dual_pds = @(2,1,$false,$false,2,35,0)
    shielded_pds_fortress = @(1,1,$false,$true,3,34,1)
}
foreach ($id in $expectedBuildIds) {
    $b = Find-ById $study.builds $id
    Assert-True ($null -ne $b) "Missing Checkpoint 64 build: $id"
    $e = $expectedBuilds[$id]
    Assert-True ([int]$b.mainWeaponCount -eq [int]$e[0] -and [int]$b.mainReactorCount -eq [int]$e[1] -and [bool]$b.activeSensor -eq [bool]$e[2] -and [bool]$b.shieldGenerator -eq [bool]$e[3] -and [int]$b.kineticPdsCount -eq [int]$e[4] -and [int]$b.usedSpace -eq [int]$e[5] -and [int]$b.freeSupportSpace -eq [int]$e[6]) "Frozen build arithmetic mismatch: $id"
}

$families = @('Kinetic','Energy','Missile')
$regimes = @(
    @{ Label='established-firm-control'; Policy='EstablishedFirm'; Ew=0; Move='OpponentAwareRange' },
    @{ Label='legacy-auto-active-clear'; Policy='AutoActive'; Ew=0; Move='OpponentAwareRange' },
    @{ Label='track-aware-auto-active-clear'; Policy='AcquisitionFirstAutoActive'; Ew=0; Move='TrackAwareOpponentRange' },
    @{ Label='legacy-auto-active-ew1'; Policy='AutoActive'; Ew=1; Move='OpponentAwareRange' },
    @{ Label='track-aware-auto-active-ew1'; Policy='AcquisitionFirstAutoActive'; Ew=1; Move='TrackAwareOpponentRange' }
)
foreach ($buildId in $expectedBuildIds) {
    $build = Find-ById $study.builds $buildId
    foreach ($family in $families) {
        $paired = @($study.variants | Where-Object { [string]$_.sideABuildId -eq $buildId -and [string]$_.sideAFamily -eq $family })
        Assert-True ($paired.Count -eq 5) "Expected five paired regimes for $buildId / $family."
        Assert-True (@($paired | ForEach-Object { [string]$_.comparisonGroup } | Select-Object -Unique).Count -eq 1) "Paired lane must share comparisonGroup for $buildId / $family."
        foreach ($regime in $regimes) {
            $matches = @($paired | Where-Object { [string]$_.profileLabel -eq $regime.Label -and [string]$_.sideATrackPolicy -eq $regime.Policy -and [int]$_.sideANetEwRangePenalty -eq $regime.Ew -and [string]$_.movementMode -eq $regime.Move })
            Assert-True ($matches.Count -eq 1) "Missing unique $buildId / $family / $($regime.Label) variant."
            $v = $matches[0]
            Assert-True ([string]$v.sideBBuildId -eq 'balanced_generalist_major' -and [string]$v.sideBFamily -eq 'Missile') "Variant $($v.id) must use the balanced Missile opponent."
            Assert-True ([string]$v.sideATacticalPowerDoctrine -eq 'FullVolleyFirst' -and [string]$v.sideBTacticalPowerDoctrine -eq 'FullVolleyFirst') "Variant $($v.id) must use FullVolleyFirst."
            Assert-True ([int]$v.sideAReactorOutputOverride -eq 5 -and [int]$v.sideBReactorOutputOverride -eq 5) "Variant $($v.id) must hold reactor output at 5 TP."
            Assert-True ([string]$v.sideBTrackPolicy -eq 'EstablishedFirm' -and [int]$v.sideBNetEwRangePenalty -eq 0) "Variant $($v.id) must retain Side B established-Firm control."
            Assert-True ([string]$v.sideAProfileId -eq 'tl1-production' -and [string]$v.sideBProfileId -eq 'tl1-production') "Variant $($v.id) must use TL1 production profiles."
            Assert-True ([string]$v.sideAAuxiliaryProfileId -eq 'aux-r53-none-tl1' -and [string]$v.sideBAuxiliaryProfileId -eq 'aux-r53-none-tl1') "Variant $($v.id) must use zero-effect AUX."
            Assert-True ([int]$v.initialRangeHexes -eq 4) "Variant $($v.id) must begin at Range 4."
            if ([int]$build.mainWeaponCount -eq 2) {
                Assert-True ([string]$v.sideASecondaryFamily -eq $family) "Dual-main variant $($v.id) must duplicate its Side-A family."
            } else {
                Assert-True ($null -eq $v.PSObject.Properties['sideASecondaryFamily']) "Single-main variant $($v.id) may not install a secondary family."
            }
        }
    }
}

$variantProps = $schema.'$defs'.variant.properties
Assert-True (@($variantProps.movementMode.enum) -contains 'TrackAwareOpponentRange') 'Schema v0.10 is missing TrackAwareOpponentRange.'
Assert-True (@($variantProps.sideATrackPolicy.enum) -contains 'AcquisitionFirstAutoActive' -and @($variantProps.sideBTrackPolicy.enum) -contains 'AcquisitionFirstAutoActive') 'Schema v0.10 is missing AcquisitionFirstAutoActive.'

$must = @($policy.mustAlwaysRunStageIds)
$deepOnly = @($policy.deepCalibrationStageIds)
Assert-True ($must.Count -eq 8 -and $must -contains 'tl1-track-aware-movement-acquisition' -and -not ($must -contains 'tl1-operational-sensor-acquisition-ew')) 'Checkpoint 64 normal suite must contain only the current stochastic study.'
Assert-True ($deepOnly.Count -eq 15 -and $deepOnly[0] -eq 'tl1-operational-sensor-acquisition-ew' -and $deepOnly -contains 'tl1-power-doctrine-reactor-sensitivity' -and $deepOnly -contains 'tl1-composed-ship-odd-build-combat') 'Checkpoint 64 Deep Calibration historical stage policy mismatch.'
Assert-True ([int]$active.checkpointMetrics.stageCount -eq 8 -and [int]$active.checkpointMetrics.monteCarloVariantCount -eq 90 -and [int]$active.checkpointMetrics.trialsAtDefault -eq 900000) 'Checkpoint 64 active workload metrics mismatch.'
Assert-True ([int]$deep.checkpointMetrics.stageCount -eq 23 -and [int]$deep.checkpointMetrics.monteCarloVariantCount -eq 1350 -and [int]$deep.checkpointMetrics.trialsAtDefault -eq 13500000) 'Checkpoint 64 Deep workload metrics mismatch.'
$activeIds = @($active.stages | ForEach-Object { [string]$_.id })
$deepIds = @($deep.stages | ForEach-Object { [string]$_.id })
Assert-True ($activeIds[3] -eq 'tl1-installation-space-envelope' -and $activeIds[4] -eq 'tl1-track-aware-movement-acquisition') 'Checkpoint 64 active stage order mismatch.'
Assert-True ($deepIds[4] -eq 'tl1-track-aware-movement-acquisition' -and $deepIds[5] -eq 'tl1-operational-sensor-acquisition-ew' -and $deepIds[6] -eq 'tl1-power-doctrine-reactor-sensitivity') 'Checkpoint 64 Deep stage order mismatch.'

$runnerPath = Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\TL1Calibration\Tl1IntegratedTacticalCombatRunner.cs'
$docPath = Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\TL1Calibration\Tl1IntegratedTacticalCombatDocuments.cs'
$runner = Get-Content -LiteralPath $runnerPath -Raw
$docs = Get-Content -LiteralPath $docPath -Raw
Assert-True ($docs -match 'TrackAwareOpponentRange' -and $docs -match 'AcquisitionFirstAutoActive') 'Integrated combat document model is missing Checkpoint 64 opt-in controls.'
Assert-True ($runner -match 'tl1-itc07-35-space-track-aware-movement-acquisition' -and $runner -match 'TrackAwareDoctrineFor' -and $runner -match 'MaximumFirmRangeForMovementPlan') 'Integrated runner is missing track-aware movement behavior.'
Assert-True ($runner -match 'policy == Tl1OperationalTrackPolicy.AcquisitionFirstAutoActive' -and $runner -match 'side.Power.SpendablePower') 'Integrated runner is missing acquisition-first sensor power behavior.'
Assert-True ($runner -match 'tl1-c64-track-aware-response-observed' -and $runner -match 'track-aware-acquisition-paired-review.csv') 'Integrated runner is missing Checkpoint 64 diagnostic gates/outputs.'
Assert-True ($runner -match 'sensorless ships are not required to defeat equal-speed standoff' -or $runner -match 'sensorless ships are not required') 'Checkpoint 64 must preserve valid standoff interpretation.'

$validationFiles = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs\validation') -File -Filter '*.md')
Assert-True ($validationFiles.Count -eq 1 -and $validationFiles[0].Name -eq 'Checkpoint_64_TL1_Track_Aware_Movement_And_Acquisition.md') 'Exactly one Checkpoint 64 active validation runbook must remain.'
Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot 'docs\validation\archive\Checkpoint_63b_Manifest_Binding_Hotfix.md') -PathType Leaf) 'Accepted Checkpoint 63b runbook must be archived.'

$rootTxt = @(Get-ChildItem -LiteralPath $repositoryRoot -File -Filter '*.txt')
Assert-True ($rootTxt.Count -eq 1 -and $rootTxt[0].Name -eq 'CHECKPOINT_64_SHA256SUMS.txt') 'Repository root must contain only CHECKPOINT_64_SHA256SUMS.txt as a .txt file.'
$archivedTxt = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs\archive') -Recurse -File -Filter '*.txt')
Assert-True ($archivedTxt.Count -eq 0) 'Generated historical checkpoint .txt artifacts must not remain under docs/archive.'

Write-Host '       Checkpoint 64 design contract: six accepted TL1 builds x three weapon families x five paired movement/acquisition regimes = 90 variants.'
Write-Host '       Production TL1 reactor remains 5 TP; FullVolleyFirst remains fixed.'
Write-Host '       Track-aware movement caps desired weapon range by supportable Firm range; valid opponent standoff remains allowed.'
Write-Host '       Acquisition-first active sensing may consume power before PDS/weapon execution when Firm is otherwise unavailable.'
Write-Host '       No target win rate is a release gate; contextual capabilities such as Energy APEN remain preserved.'
Write-Host '       Validation tiers: 8 normal stages / 90 MC variants; Deep Calibration 23 stages / 1,350 MC variants.'
