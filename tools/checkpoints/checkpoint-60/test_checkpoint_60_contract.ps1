[CmdletBinding()]
param()

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path

function Assert-True([bool]$Condition, [string]$Message) { if (-not $Condition) { throw $Message } }
function Read-Json([string]$Path) { Assert-True (Test-Path -LiteralPath $Path -PathType Leaf) "Missing JSON file: $Path"; return (Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json) }
function Find-ById($Items, [string]$Id) { foreach ($item in @($Items)) { if ([string]$item.id -eq $Id) { return $item } }; return $null }

$baseline = Read-Json (Join-Path $repositoryRoot 'docs\design\player_technology\tl1_35_space_player_cruiser_baseline_v0_2.json')
$study = Read-Json (Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\Scenarios\ArchitectureTechnology\tl1-space01-35-space-construction-envelope.json')
$policy = Read-Json (Join-Path $repositoryRoot 'docs\design\testing\checkpoint_60_validation_suite_policy_v0_1.json')
$active = Read-Json (Join-Path $repositoryRoot 'tools\calibration\checkpoints\checkpoint-60.json')
$deep = Read-Json (Join-Path $repositoryRoot 'tools\calibration\checkpoints\checkpoint-60-deep-calibration.json')
$legacy = Read-Json (Join-Path $repositoryRoot 'tools\calibration\checkpoints\checkpoint-58e.json')

Assert-True ([int]$baseline.checkpoint -eq 60) 'TL1 baseline must identify Checkpoint 60.'
Assert-True ([int]$baseline.installationSpace.playerCruiserTotal -eq 35) 'TL1 player cruiser must use the working 35-Space baseline.'
Assert-True ([int]$baseline.installationSpace.mandatoryCoreTotal -eq 25) 'TL1 mandatory core must total 25 Space.'
Assert-True ([int]$baseline.installationSpace.basePrimaryArmorSpace -eq 0) 'Base primary armor must consume zero Installation Space.'
Assert-True ([int]$baseline.deterministicArchitectureEnvelope.macroLoadoutCount -eq 27) 'Baseline must record 27 legal macro loadouts.'
Assert-True ([int]$baseline.deterministicArchitectureEnvelope.weaponPowerVariantCount -eq 96) 'Baseline must record 96 weapon/power variants.'
Assert-True (-not ([bool]$baseline.deterministicArchitectureEnvelope.dualMainDualReactorCoreLegalAtTl1)) 'Dual-main/dual-reactor core must remain outside the TL1 envelope.'

$components = @($baseline.installationSpace.components)
$weapon = Find-ById $components 'main_weapon'
$reactor = Find-ById $components 'main_reactor'
$stl = Find-ById $components 'stl_drive'
$ftl = Find-ById $components 'ftl_drive'
$computer = Find-ById $components 'tactical_computer'
Assert-True ($null -ne $weapon -and [int]$weapon.space -eq 6 -and [bool]$weapon.duplicable) 'TL1 main weapon footprint/duplication mismatch.'
Assert-True ($null -ne $reactor -and [int]$reactor.space -eq 6 -and [bool]$reactor.duplicable) 'TL1 main reactor footprint/duplication mismatch.'
Assert-True ($null -ne $stl -and [int]$stl.space -eq 5 -and (-not [bool]$stl.duplicable) -and [int]$stl.ordinaryMiniaturizationFloor -eq 4) 'TL1 STL primary architecture mismatch.'
Assert-True ($null -ne $ftl -and [int]$ftl.space -eq 5 -and (-not [bool]$ftl.duplicable) -and [int]$ftl.ordinaryMiniaturizationFloor -eq 4) 'TL1 FTL primary architecture mismatch.'
Assert-True ($null -ne $computer -and [int]$computer.space -eq 3 -and (-not [bool]$computer.duplicable)) 'TL1 tactical-computer primary architecture mismatch.'

Assert-True ([string]$study.schemaVersion -eq 'star-cluster-tl1-installation-space-envelope-v1') 'Unexpected Checkpoint 60 architecture study schema.'
Assert-True ([string]$study.id -eq 'tl1-space01-35-space-construction-envelope' -and [int]$study.checkpoint -eq 60) 'Unexpected Checkpoint 60 architecture study identity.'
Assert-True ([int]$study.totalSpace -eq 35) 'Architecture study total Space mismatch.'
Assert-True ([int]$study.expected.macroLoadoutCount -eq 27 -and [int]$study.expected.weaponPowerVariantCount -eq 96) 'Architecture study cardinality expectations mismatch.'
Assert-True ([int]$study.expected.exactFillMacroCount -eq 4) 'Architecture study exact-fill expectation mismatch.'
Assert-True ([int]$study.expected.maximumMainWeapons -eq 2 -and [int]$study.expected.maximumMainReactors -eq 2 -and [int]$study.expected.maximumKineticPds -eq 5) 'Architecture study stacking extrema mismatch.'
Assert-True ([int]$study.expected.dualMainDualReactorSpace -eq 37 -and (-not [bool]$study.expected.dualMainDualReactorLegal)) 'Architecture study dual-main/dual-reactor control mismatch.'
Assert-True ([int]$study.expected.nominalPowerOvercommitVariantCount -eq 5 -and [int]$study.expected.nominalPowerExactVariantCount -eq 10) 'Architecture study nominal power counts mismatch.'
Assert-True ([int]$study.expected.minimumPowerMargin -eq -2 -and [int]$study.expected.maximumPowerMargin -eq 10) 'Architecture study power-margin range mismatch.'
Assert-True (@($study.referenceBuilds).Count -eq 7) 'Architecture study must retain six legal candidates plus one illegal control.'

$must = @($policy.mustAlwaysRunStageIds)
$deepOnly = @($policy.deepCalibrationStageIds)
$archived = @($policy.archivedHistoricalStageIds)
Assert-True ($must.Count -eq 7) 'Checkpoint 60 must-always-run stage count must be 7.'
Assert-True ($must -contains 'tl1-installation-space-envelope') 'Checkpoint 60 must-always-run policy must include the architecture envelope.'
Assert-True ($deepOnly.Count -eq 12) 'Checkpoint 60 Deep Calibration addition count must remain 12.'
Assert-True ($archived.Count -eq 38) 'Checkpoint 60 historical-only stage count must remain 38.'

$legacyIds = @($legacy.stages | ForEach-Object { [string]$_.id })
$legacyClassified = @($must | Where-Object { $_ -ne 'tl1-installation-space-envelope' }) + $deepOnly + $archived
Assert-True ($legacyClassified.Count -eq 56) 'Checkpoint 60 policy must still classify all 56 Checkpoint 58e runner stages.'
Assert-True (($legacyClassified | Select-Object -Unique).Count -eq 56) 'Checkpoint 60 inherited stage classifications must be mutually exclusive.'
foreach ($id in $legacyIds) { Assert-True ($legacyClassified -contains $id) "Legacy stage is not classified by Checkpoint 60: $id" }

$activeIds = @($active.stages | ForEach-Object { [string]$_.id })
Assert-True ($activeIds.Count -eq 7) 'Checkpoint 60 active definition must contain 7 runner stages.'
Assert-True ($activeIds[3] -eq 'tl1-installation-space-envelope') 'Architecture envelope must run after TL1 Phase B in the active definition.'
foreach ($stage in @($active.stages)) {
    $usesTrials = $false
    $metricsProp = $stage.PSObject.Properties['metrics']
    if ($null -ne $metricsProp) {
        $usesProp = $stage.metrics.PSObject.Properties['usesTrials']
        if ($null -ne $usesProp) { $usesTrials = [bool]$usesProp.Value }
    }
    Assert-True (-not $usesTrials) "Default active suite may not contain Monte Carlo stage $($stage.id)."
}
Assert-True ([int]$active.checkpointMetrics.stageCount -eq 7 -and [int]$active.checkpointMetrics.monteCarloVariantCount -eq 0) 'Active checkpoint workload metrics mismatch.'

$deepIds = @($deep.stages | ForEach-Object { [string]$_.id })
Assert-True ($deepIds.Count -eq 19) 'Checkpoint 60 Deep Calibration definition must contain 19 runner stages.'
Assert-True ($deepIds[3] -eq 'tl1-installation-space-envelope') 'Architecture envelope must also run in Deep Calibration.'
Assert-True ([int]$deep.checkpointMetrics.stageCount -eq 19 -and [int]$deep.checkpointMetrics.monteCarloVariantCount -eq 1026 -and [int]$deep.checkpointMetrics.trialsAtDefault -eq 10260000) 'Deep Calibration workload metrics mismatch.'

$programPath = Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\Program.cs'
$runnerPath = Join-Path $repositoryRoot 'src\StarCluster.ScenarioRunner\TL1Architecture\Tl1InstallationSpaceEnvelopeRunner.cs'
Assert-True (Test-Path -LiteralPath $runnerPath -PathType Leaf) 'Missing TL1 Installation Space envelope runner.'
$program = Get-Content -LiteralPath $programPath -Raw
$runner = Get-Content -LiteralPath $runnerPath -Raw
Assert-True ($program -match 'tl1-installation-space-envelope') 'ScenarioRunner command registration is missing.'
Assert-True ($runner -match 'construction-legality-independent-of-nominal-power') 'Architecture runner must preserve the power-vs-legality distinction.'
Assert-True ($runner -match 'BuildWeaponPatterns') 'Architecture runner must enumerate weapon-family combinations deterministically.'

$validationFiles = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs\validation') -File -Filter '*.md')
Assert-True ($validationFiles.Count -eq 1 -and $validationFiles[0].Name -eq 'Checkpoint_60_TL1_35_Space_Construction_Envelope_And_Odd_Build_Foundation.md') 'Exactly one Checkpoint 60 active validation runbook must remain.'
Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot 'docs\Star_Cluster_Game_Concept_v0.6c.docx') -PathType Leaf) 'Concept v0.6c must be active.'
Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot 'docs\archive\Star_Cluster_Game_Concept_v0.6b.docx') -PathType Leaf) 'Concept v0.6b must be archived.'

Write-Host '       Checkpoint 60 design contract: deterministic 35-Space envelope with 27 macro loadouts and 96 retained TL1 weapon/power variants.'
Write-Host '       TL1 stacking envelope: max 2 main weapons, max 2 main reactors, max 5 current-footprint kinetic PDS; dual-main/dual-reactor core remains 37 Space.'
Write-Host '       Nominal power diagnostic: 5 overcommit variants, 10 exact-output variants, margin range -2..+10 TP; power overcommit does not invalidate construction.'
Write-Host '       Validation tiers: 7 must-always-run runner stages; Deep Calibration adds the retained 12 stochastic studies for 1,026 variants / 10.26 million default trials.'
