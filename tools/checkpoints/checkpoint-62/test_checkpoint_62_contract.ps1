[CmdletBinding()]
param()

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path

function Assert-True([bool]$Condition, [string]$Message) { if (-not $Condition) { throw $Message } }
function Read-Json([string]$Path) { Assert-True (Test-Path -LiteralPath $Path -PathType Leaf) "Missing JSON file: $Path"; return (Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json) }
function Find-ById($Items, [string]$Id) { foreach ($item in @($Items)) { if ([string]$item.id -eq $Id) { return $item } }; return $null }

$baseline = Read-Json (Join-Path $repositoryRoot 'docs\design\player_technology\tl1_35_space_player_cruiser_baseline_v0_4.json')
$envelope = Read-Json (Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\Scenarios\ArchitectureTechnology\tl1-space01-35-space-construction-envelope.json')
$study = Read-Json (Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\Scenarios\TL1Calibration\tl1-itc05-35-space-power-doctrine-reactor-sensitivity.json')
$profiles = Read-Json (Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\Scenarios\ArchitectureTechnology\tl1-tl2-standard-runtime-profiles-v0_3.json')
$schema = Read-Json (Join-Path $repositoryRoot 'docs\design\player_technology\tl1_integrated_tactical_combat_schema_v0_8.json')
$policy = Read-Json (Join-Path $repositoryRoot 'docs\design\testing\checkpoint_62_validation_suite_policy_v0_1.json')
$active = Read-Json (Join-Path $repositoryRoot 'tools\calibration\checkpoints\checkpoint-62.json')
$deep = Read-Json (Join-Path $repositoryRoot 'tools\calibration\checkpoints\checkpoint-62-deep-calibration.json')

Assert-True ([int]$baseline.checkpoint -eq 62) 'TL1 baseline must identify Checkpoint 62.'
Assert-True ([int]$baseline.installationSpace.playerCruiserTotal -eq 35) 'TL1 player cruiser must remain 35 Space.'
Assert-True ([int]$baseline.installationSpace.mandatoryCoreTotal -eq 25) 'TL1 mandatory core must remain 25 Space.'
Assert-True ([int]$baseline.deterministicArchitectureEnvelope.macroLoadoutCount -eq 27) 'Deterministic envelope must retain 27 macro loadouts.'
Assert-True ([int]$baseline.deterministicArchitectureEnvelope.weaponPowerVariantCount -eq 96) 'Deterministic envelope must retain 96 weapon/power variants.'
Assert-True ([int]$baseline.powerDoctrineReactorSensitivityStudy.variantCount -eq 108) 'Checkpoint 62 baseline must define 108 sensitivity variants.'
Assert-True ([int]$baseline.powerDoctrineReactorSensitivityStudy.productionReactorOutputRemains -eq 5) 'Production TL1 reactor output must remain 5 TP.'
Assert-True (-not [bool]$baseline.powerDoctrineReactorSensitivityStudy.balanceTargetsBlocking) 'Checkpoint 62 outcomes must remain diagnostic rather than target-gated.'

Assert-True ([string]$envelope.id -eq 'tl1-space01-35-space-construction-envelope' -and [int]$envelope.checkpoint -eq 60) 'Checkpoint 60 deterministic envelope must remain frozen as the construction source.'
Assert-True (@($envelope.referenceBuilds).Count -eq 7) 'Envelope must retain six legal builds plus the 37-Space illegal control.'

$production = Find-ById $profiles.profiles 'tl1-production'
Assert-True ($null -ne $production) 'TL1 production runtime profile is missing.'
Assert-True ([int]$production.powerAndControl.reactorOutput -eq 5) 'Checkpoint 62 may not silently change the production TL1 reactor from 5 TP.'

Assert-True ([string]$study.id -eq 'tl1-itc05-35-space-power-doctrine-reactor-sensitivity') 'Unexpected Checkpoint 62 study ID.'
Assert-True (@($study.builds).Count -eq 4) 'Checkpoint 62 study must define exactly four power-sensitive legal builds.'
Assert-True (@($study.variants).Count -eq 108) 'Checkpoint 62 study must define exactly 108 variants.'
$expectedBuildIds = @('balanced_generalist_major','pds_saturator','dual_main_dual_pds','shielded_pds_fortress')
$buildIds = @($study.builds | ForEach-Object { [string]$_.id })
Assert-True (($buildIds | Select-Object -Unique).Count -eq 4) 'Checkpoint 62 build IDs must be unique.'
foreach ($id in $expectedBuildIds) { Assert-True ($buildIds -contains $id) "Missing Checkpoint 62 build: $id" }

$families = @('Kinetic','Energy','Missile')
$doctrines = @('DefenseFirst','PrimaryFireFirst','FullVolleyFirst')
$reactors = @(4,5,6)
foreach ($buildId in $expectedBuildIds) {
    $build = Find-ById $study.builds $buildId
    foreach ($family in $families) {
        $paired = @($study.variants | Where-Object { [string]$_.sideABuildId -eq $buildId -and [string]$_.sideAFamily -eq $family })
        Assert-True ($paired.Count -eq 9) "Expected nine paired sensitivity variants for $buildId / $family."
        Assert-True (@($paired | ForEach-Object { [string]$_.comparisonGroup } | Select-Object -Unique).Count -eq 1) "Paired sensitivity lane must share one comparisonGroup for $buildId / $family."
        foreach ($doctrine in $doctrines) {
            foreach ($reactor in $reactors) {
                $matches = @($paired | Where-Object { [string]$_.sideATacticalPowerDoctrine -eq $doctrine -and [int]$_.sideAReactorOutputOverride -eq $reactor })
                Assert-True ($matches.Count -eq 1) "Missing unique $buildId / $family / $doctrine / R$reactor variant."
                $v = $matches[0]
                Assert-True ([string]$v.sideBBuildId -eq 'balanced_generalist_major' -and [string]$v.sideBFamily -eq 'Missile') "Variant $($v.id) must use the balanced Missile opponent."
                Assert-True ([string]$v.sideBTacticalPowerDoctrine -eq 'DefenseFirst' -and [int]$v.sideBReactorOutputOverride -eq 5) "Variant $($v.id) must keep Side B on the accepted production power control."
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
}

$variantProps = $schema.'$defs'.variant.properties
Assert-True ($null -ne $variantProps.sideATacticalPowerDoctrine -and $null -ne $variantProps.sideBTacticalPowerDoctrine) 'Integrated-combat schema v0.8 is missing Tactical Power doctrine fields.'
Assert-True ($null -ne $variantProps.sideAReactorOutputOverride -and $null -ne $variantProps.sideBReactorOutputOverride) 'Integrated-combat schema v0.8 is missing reactor-output sensitivity fields.'

$must = @($policy.mustAlwaysRunStageIds)
$deepOnly = @($policy.deepCalibrationStageIds)
Assert-True ($must.Count -eq 8 -and $must -contains 'tl1-power-doctrine-reactor-sensitivity' -and -not ($must -contains 'tl1-composed-ship-odd-build-combat')) 'Checkpoint 62 normal suite must contain the current sensitivity study and retire Checkpoint 61 Monte Carlo from the normal lineup.'
Assert-True ($deepOnly.Count -eq 13 -and $deepOnly -contains 'tl1-composed-ship-odd-build-combat') 'Checkpoint 62 Deep Calibration must retain Checkpoint 61 composed-build regression plus twelve historical stochastic stages.'
Assert-True ([int]$active.checkpointMetrics.stageCount -eq 8 -and [int]$active.checkpointMetrics.monteCarloVariantCount -eq 108 -and [int]$active.checkpointMetrics.trialsAtDefault -eq 1080000) 'Checkpoint 62 active workload metrics mismatch.'
Assert-True ([int]$deep.checkpointMetrics.stageCount -eq 21 -and [int]$deep.checkpointMetrics.monteCarloVariantCount -eq 1188 -and [int]$deep.checkpointMetrics.trialsAtDefault -eq 11880000) 'Checkpoint 62 Deep workload metrics mismatch.'
$activeIds = @($active.stages | ForEach-Object { [string]$_.id })
$deepIds = @($deep.stages | ForEach-Object { [string]$_.id })
Assert-True ($activeIds[3] -eq 'tl1-installation-space-envelope' -and $activeIds[4] -eq 'tl1-power-doctrine-reactor-sensitivity') 'Checkpoint 62 construction/sensitivity stages are out of order.'
Assert-True ($deepIds[4] -eq 'tl1-power-doctrine-reactor-sensitivity' -and $deepIds[5] -eq 'tl1-composed-ship-odd-build-combat') 'Checkpoint 62 Deep Calibration must run current sensitivity before Checkpoint 61 historical regression.'

$runnerPath = Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\TL1Calibration\Tl1IntegratedTacticalCombatRunner.cs'
$docPath = Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\TL1Calibration\Tl1IntegratedTacticalCombatDocuments.cs'
$runner = Get-Content -LiteralPath $runnerPath -Raw
$docs = Get-Content -LiteralPath $docPath -Raw
Assert-True ($docs -match 'Tl1TacticalPowerDoctrine' -and $docs -match 'sideAReactorOutputOverride') 'Integrated combat document model is missing Checkpoint 62 doctrine/reactor controls.'
Assert-True ($runner -match 'tl1-itc05-35-space-power-doctrine-reactor-sensitivity') 'Integrated runner is missing the Checkpoint 62 study ID.'
Assert-True ($runner -match 'PrimaryFireFirst' -and $runner -match 'FullVolleyFirst' -and $runner -match 'pdsPowerBudget') 'Integrated runner is missing the Checkpoint 62 PDS power-allocation doctrine.'
Assert-True ($runner -match 'ReactorOutputPerMain' -and $runner -match 'power-doctrine-reactor-matrix.csv' -and $runner -match 'tl1-c62-outcomes-review-only') 'Integrated runner is missing Checkpoint 62 reactor sensitivity/review outputs.'

$validationFiles = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs\validation') -File -Filter '*.md')
Assert-True ($validationFiles.Count -eq 1 -and $validationFiles[0].Name -eq 'Checkpoint_62_TL1_Tactical_Power_Doctrine_And_Reactor_Output_Sensitivity.md') 'Exactly one Checkpoint 62 active validation runbook must remain.'
Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot 'docs\validation\archive\Checkpoint_61_TL1_35_Space_Composed_Ship_And_Odd_Build_Combat_Study.md') -PathType Leaf) 'Checkpoint 61 runbook must be archived.'

$rootTxt = @(Get-ChildItem -LiteralPath $repositoryRoot -File -Filter '*.txt')
Assert-True ($rootTxt.Count -eq 1 -and $rootTxt[0].Name -eq 'CHECKPOINT_62_SHA256SUMS.txt') 'Repository root must contain only the current Checkpoint 62 manifest as a .txt file.'
$archivedTxt = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs\archive') -Recurse -File -Filter '*.txt')
Assert-True ($archivedTxt.Count -eq 0) 'Generated historical checkpoint .txt artifacts must not remain under docs/archive.'

Write-Host '       Checkpoint 62 design contract: four power-sensitive legal TL1 builds x three weapon families x three doctrines x three reactor-output probes = 108 variants.'
Write-Host '       Production TL1 reactor remains 5 TP; 4 and 6 are sensitivity probes only.'
Write-Host '       Doctrine controls: DefenseFirst, PrimaryFireFirst, FullVolleyFirst; no target win rate is a release gate.'
Write-Host '       Archive hygiene: historical generated checkpoint .txt logs/manifests/readmes are excluded from current packaging.'
Write-Host '       Validation tiers: 8 normal stages / 108 MC variants; Deep Calibration 21 stages / 1,188 MC variants.'
