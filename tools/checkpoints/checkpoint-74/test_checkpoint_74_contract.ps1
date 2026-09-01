[CmdletBinding()]
param()
Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
function Assert-True { param([bool]$Condition,[string]$Message) if (-not $Condition) { throw $Message } }
function Read-Json { param([string]$RelativePath) Get-Content -LiteralPath (Join-Path $repositoryRoot $RelativePath) -Raw | ConvertFrom-Json }
$guard = Join-Path $repositoryRoot 'tools\checkpoints\Test-NativeAcceptanceDependencies.ps1'
$normalRel='tools/calibration/checkpoints/checkpoint-74.json'
$deepRel='tools/calibration/checkpoints/checkpoint-74-deep-calibration.json'
$guardedPs=@('tools/checkpoints/Test-NativeAcceptanceDependencies.ps1','tools/checkpoints/checkpoint-74/apply_checkpoint_74.ps1','tools/checkpoints/checkpoint-74/test_checkpoint_74_contract.ps1','tools/calibration/run_calibration_checkpoint.ps1')
& $guard -RepositoryRoot $repositoryRoot -PowerShellPaths $guardedPs -CheckpointDefinitionPaths @($normalRel,$deepRel)
$normal=Read-Json $normalRel; $deep=Read-Json $deepRel
Assert-True ([string]$normal.checkpointId -eq '74' -and [string]$deep.checkpointId -eq '74') 'Checkpoint 74 definition ID mismatch.'
Assert-True ([string]$normal.manifestFile -eq 'CHECKPOINT_74_SHA256SUMS.txt' -and [string]$deep.manifestFile -eq 'CHECKPOINT_74_SHA256SUMS.txt') 'Checkpoint 74 manifest binding mismatch.'
Assert-True (@($normal.stages).Count -eq 11 -and @($deep.stages).Count -eq 30) 'Checkpoint 74 stage-count mismatch.'
Assert-True ([int]$normal.checkpointMetrics.monteCarloVariantCount -eq 20 -and [int]$normal.checkpointMetrics.trialsAtDefault -eq 200000 -and [int]$normal.checkpointMetrics.smokeTrialsAtDefault -eq 20 -and [int]$normal.checkpointMetrics.totalTrialExecutionsAtDefault -eq 200020) 'Checkpoint 74 normal workload mismatch.'
Assert-True ([int]$deep.checkpointMetrics.monteCarloVariantCount -eq 1564 -and [int]$deep.checkpointMetrics.trialsAtDefault -eq 15640000 -and [int]$deep.checkpointMetrics.smokeTrialsAtDefault -eq 20 -and [int]$deep.checkpointMetrics.totalTrialExecutionsAtDefault -eq 15640020) 'Checkpoint 74 Deep Calibration workload mismatch.'
$policy=Read-Json 'docs/design/testing/checkpoint_74_validation_suite_policy_v0_1.json'
Assert-True ([string]$policy.aiDoctrineControls.registryVersion -eq '0.2' -and [string]$policy.aiDoctrineControls.defaultEwDoctrine -eq 'tl1-ew-preserve-combat-package-v1' -and -not [bool]$policy.aiDoctrineControls.cp73RerunRequired) 'Checkpoint 74 AI doctrine-promotion policy mismatch.'
Assert-True ([bool]$policy.productionControls.degradedFireFoundationImplementedByCheckpoint74 -and -not [bool]$policy.productionControls.productionWeaponDegradedFireEnabledByCheckpoint74 -and -not [bool]$policy.productionControls.movementPhaseFireImplementedByCheckpoint74) 'Checkpoint 74 production/deferred-feature policy mismatch.'
$registry=Read-Json 'docs/archive/ai/pre-cp165-active/ai_doctrine_registry_v0_2.json'
Assert-True ([string]$registry.registryVersion -eq '0.2' -and [string]$registry.defaults.'electronic-warfare' -eq 'tl1-ew-preserve-combat-package-v1') 'Checkpoint 74 registry default mismatch.'
$doctrines=@($registry.doctrines)
$default=@($doctrines|Where-Object{[string]$_.id -eq 'tl1-ew-preserve-combat-package-v1'})
Assert-True ($default.Count -eq 1 -and [string]$default[0].status -eq 'accepted' -and [string]$default[0].acceptedCheckpoint -eq '73') 'Preserve-combat-package must be accepted from CP73.'
$reactive=@($doctrines|Where-Object{[string]$_.id -eq 'tl1-ew-reactive-eccm-v1'})
Assert-True ($reactive.Count -eq 1 -and [string]$reactive[0].status -eq 'accepted') 'Reactive ECCM must remain accepted.'
$rejected=@($doctrines|Where-Object{[string]$_.id -eq 'tl1-ew-preserve-offense-v1'})
Assert-True ($rejected.Count -eq 1 -and [string]$rejected[0].status -eq 'rejected') 'Preserve-offense must remain recorded as rejected evidence.'
Assert-True (@($doctrines|Where-Object{[bool]$_.informationPolicy.usesHiddenEnemyRatings}).Count -eq 0) 'AI doctrine must preserve player information parity.'
$cp73Evidence=@($registry.evidence|Where-Object{[string]$_.checkpoint -eq '73'})
Assert-True ($cp73Evidence.Count -eq 3 -and @($cp73Evidence|Where-Object{[string]$_.resultSha256 -ne '667b553760b16ec63a67db52748a98bcb6daf7640bce21b3b7e4fc7d88da8613'}).Count -eq 0) 'CP73 doctrine evidence hash/provenance mismatch.'
$schema=Read-Json 'docs/design/player_technology/tl1_integrated_tactical_combat_schema_v0_18.json'
Assert-True ([string]$schema.'$id' -eq 'star-cluster-tl1-integrated-tactical-combat-schema-v0-18' -and $null -ne $schema.'$defs'.variant.properties.sideAAllowsApproximateDirectFire -and $null -ne $schema.'$defs'.variant.properties.sideAApproximateDirectFireAccuracyPenalty) 'Checkpoint 74 integrated schema degraded-fire controls missing.'
$study=Read-Json 'src/StarCluster.ScenarioRunner/Scenarios/TL1Calibration/tl1-itc16-approximate-track-degraded-fire.json'
Assert-True ([string]$study.id -eq 'tl1-itc16-approximate-track-degraded-fire' -and [int]$study.trialsPerVariant -eq 10000 -and @($study.variants).Count -eq 20 -and [int64]$study.masterSeed -eq 740100) 'Checkpoint 74 study identity/workload mismatch.'
$variants=@($study.variants)
foreach($group in @($variants|Group-Object comparisonGroup)){ Assert-True ($group.Count -eq 5) "CP74 group '$($group.Name)' must contain five variants." }
Assert-True (@($variants|Where-Object{[string]$_.profileLabel -eq 'firm-reference'}).Count -eq 4 -and @($variants|Where-Object{[string]$_.profileLabel -eq 'approx-firm-only'}).Count -eq 4 -and @($variants|Where-Object{[string]$_.profileLabel -match '^approx-p(10|20|30)$'}).Count -eq 12) 'Checkpoint 74 control/penalty coverage mismatch.'
Assert-True (@($variants|Where-Object{[string]$_.sideAFamily -eq 'Missile' -or [string]$_.sideBFamily -eq 'Missile'}).Count -eq 0) 'Checkpoint 74 degraded-fire study must exclude missiles.'
$core=Get-Content -LiteralPath (Join-Path $repositoryRoot 'src/StarCluster.Core/Combat/DirectFire/DirectFireWeaponProfile.cs') -Raw
$elig=Get-Content -LiteralPath (Join-Path $repositoryRoot 'src/StarCluster.Core/Combat/DirectFire/DirectFireTargetEligibility.cs') -Raw
$runner=Get-Content -LiteralPath (Join-Path $repositoryRoot 'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs') -Raw
Assert-True ($core.Contains('AllowsApproximateTrackFire') -and $core.Contains('ApproximateTrackAccuracyPenalty')) 'Core weapon degraded-fire trait missing.'
Assert-True ($elig.Contains('TacticalTrackQuality.Approximate') -and $elig.Contains('AccuracyModifier')) 'Core degraded-fire eligibility wiring missing.'
Assert-True ($runner.Contains('Tl1ApproximateTrackDegradedFireStudyId') -and $runner.Contains('WriteTl1ApproximateTrackDegradedFireReview') -and $runner.Contains('approximateTrackAccuracyPenalty')) 'Integrated CP74 study wiring missing.'
$concepts=@(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs') -File -Filter 'Star_Cluster_Game_Concept_v*.docx')
Assert-True ($concepts.Count -eq 1 -and $concepts[0].Name -eq 'Star_Cluster_Game_Concept_v0.6m.docx') 'Checkpoint 74 must expose exactly one active Concept v0.6m.'
Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot 'docs/archive/Star_Cluster_Game_Concept_v0.6l.docx') -PathType Leaf) 'Checkpoint 74 must archive Concept v0.6l.'
Write-Host 'Checkpoint 74: CP73 preserve-combat-package EW doctrine promoted; CP73 Monte Carlo remains dependency-triggered rather than routinely rerun.'
Write-Host 'Degraded-fire foundation: production weapons remain Firm-only; controlled -10/-20/-30 Approximate-track direct-fire sweep only; missiles excluded.'
Write-Host 'Validation tiers: 11 normal stages / 20 substantive MC variants; Deep Calibration 30 stages / 1,564 substantive MC variants.'
Write-Host 'Checkpoint 74 contract validation passed.'
