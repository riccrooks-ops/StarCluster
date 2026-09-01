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
    $p=Join-Path $repositoryRoot ($RelativePath.Replace('/','\'))
    Assert-True (Test-Path -LiteralPath $p -PathType Leaf) "Required file '$RelativePath' is missing."
    [System.IO.File]::ReadAllText($p)
}
function Read-Json {
    param([string]$RelativePath)
    (Read-Text $RelativePath) | ConvertFrom-Json
}
function Read-ZipEntryText {
    param([string]$RelativePath,[string]$EntryName)
    $p=Join-Path $repositoryRoot ($RelativePath.Replace('/','\'))
    Assert-True (Test-Path -LiteralPath $p -PathType Leaf) "Archive '$RelativePath' is missing."
    Add-Type -AssemblyName System.IO.Compression.FileSystem -ErrorAction Stop | Out-Null
    $z=[System.IO.Compression.ZipFile]::OpenRead($p)
    try {
        $e=$z.GetEntry($EntryName)
        Assert-True ($null -ne $e) "Archive '$RelativePath' is missing '$EntryName'."
        $s=$e.Open()
        $r=New-Object System.IO.StreamReader($s)
        try { [string]$r.ReadToEnd() } finally { $r.Dispose(); $s.Dispose() }
    } finally { $z.Dispose() }
}
function Read-DocxText {
    param([string]$RelativePath)
    [xml]$x=Read-ZipEntryText $RelativePath 'word/document.xml'
    [string]$x.DocumentElement.InnerText
}
function Read-Manifest {
    param([string]$RelativePath)
    $p=Join-Path $repositoryRoot ($RelativePath.Replace('/','\'))
    Assert-True (Test-Path -LiteralPath $p -PathType Leaf) "Manifest '$RelativePath' is missing."
    $lines=@(Get-Content -LiteralPath $p)
    Assert-True ($lines.Count -gt 0) "Manifest '$RelativePath' is empty."
    $map=@{}
    $lineNumber=0
    foreach ($line in $lines) {
        $lineNumber++
        Assert-True (-not [string]::IsNullOrWhiteSpace($line)) "Manifest '$RelativePath' contains a blank line at $lineNumber."
        $m=[regex]::Match($line, '^([0-9a-fA-F]{64})  (.+)$')
        Assert-True ($m.Success) "Manifest '$RelativePath' has malformed line $lineNumber."
        $relative=$m.Groups[2].Value.Replace('\','/')
        Assert-True (-not $map.ContainsKey($relative)) "Manifest '$RelativePath' duplicates '$relative'."
        $map[$relative]=$m.Groups[1].Value.ToLowerInvariant()
    }
    [pscustomobject]@{ Path=$p; PhysicalLineCount=$lines.Count; EntryCount=$map.Count; Entries=$map }
}
function Hash-Rel {
    param([string]$RelativePath)
    $p=Join-Path $repositoryRoot ($RelativePath.Replace('/','\'))
    Assert-True (Test-Path -LiteralPath $p -PathType Leaf) "Hash target '$RelativePath' is missing."
    (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()
}
function Require-Property {
    param($Object,[string]$PropertyName,[string]$Context)
    Assert-True ($null -ne $Object.PSObject.Properties[$PropertyName]) "$Context is missing required property '$PropertyName'."
}
function Assert-NoText {
    param([string]$Text,[string]$Needle,[string]$Message)
    Assert-True ($Text.IndexOf($Needle,[System.StringComparison]::OrdinalIgnoreCase) -lt 0) $Message
}

Write-Host '       Validating native-dependency declarations...'
$guard=Join-Path $repositoryRoot 'tools\checkpoints\Test-NativeAcceptanceDependencies.ps1'
$normalRel='tools/calibration/checkpoints/checkpoint-86a.json'
$deepRel='tools/calibration/checkpoints/checkpoint-86a-deep-calibration.json'
$guardedPs=@(
    'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
    'tools/checkpoints/checkpoint-86a/apply_checkpoint_86a.ps1',
    'tools/checkpoints/checkpoint-86a/test_checkpoint_86a_contract.ps1',
    'tools/calibration/run_calibration_checkpoint.ps1'
)
$guardedDefs=@($normalRel,$deepRel)
& $guard -RepositoryRoot $repositoryRoot -PowerShellPaths $guardedPs -CheckpointDefinitionPaths $guardedDefs

Write-Host '       Validating Checkpoint 86a definitions and unchanged CP86 workload accounting...'
$normal=Read-Json $normalRel
$deep=Read-Json $deepRel
Assert-True ([string]$normal.checkpointId -eq '86a' -and [string]$deep.checkpointId -eq '86a') 'Checkpoint 86a definition ID mismatch.'
Assert-True ([string]$normal.manifestFile -eq 'CHECKPOINT_86a_SHA256SUMS.txt' -and [string]$deep.manifestFile -eq 'CHECKPOINT_86a_SHA256SUMS.txt') 'Checkpoint 86a manifest binding mismatch.'
Assert-True ([string]$normal.outputRoot -eq 'out/checkpoint-86a' -and [string]$deep.outputRoot -eq 'out/checkpoint-86a-deep-calibration') 'Checkpoint 86a output-root binding mismatch.'
Assert-True (@($normal.stages).Count -eq 11 -and [int]$normal.checkpointMetrics.stageCount -eq 11) 'Checkpoint 86a normal stage-count mismatch.'
Assert-True ([int]$normal.checkpointMetrics.monteCarloVariantCount -eq 288 -and [int]$normal.checkpointMetrics.trialsAtDefault -eq 2880000 -and [int]$normal.checkpointMetrics.smokeVariantExecutions -eq 288 -and [int]$normal.checkpointMetrics.smokeTrialsAtDefault -eq 288 -and [int]$normal.checkpointMetrics.totalTrialExecutionsAtDefault -eq 2880288) 'Checkpoint 86a normal workload mismatch.'
Assert-True (@($deep.stages).Count -eq 36 -and [int]$deep.checkpointMetrics.stageCount -eq 36 -and [int]$deep.checkpointMetrics.monteCarloVariantCount -eq 1982 -and [int]$deep.checkpointMetrics.trialsAtDefault -eq 19820000 -and [int]$deep.checkpointMetrics.smokeVariantExecutions -eq 438 -and [int]$deep.checkpointMetrics.smokeTrialsAtDefault -eq 438 -and [int]$deep.checkpointMetrics.totalTrialExecutionsAtDefault -eq 19820438) 'Checkpoint 86a Deep Calibration workload mismatch.'
$expectedNormal=@(
    'deterministic','tl1-phase-a','tl1-phase-b','tl1-installation-space-envelope','tl1-sensor-ew-foundation',
    'tl2-weapon-penetration-layered-defense-preflight','tl2-weapon-penetration-layered-defense-smoke','tl2-weapon-penetration-layered-defense-permutations',
    'auxiliary-resource-endurance','checkpoint-53-resource-semantics-lock','runner-self-tests'
)
Assert-True ((@($normal.stages | ForEach-Object {[string]$_.id}) -join '|') -eq ($expectedNormal -join '|')) 'Checkpoint 86a normal stage ordering mismatch.'
$self=@($normal.stages | Where-Object {[string]$_.id -eq 'runner-self-tests'})
Assert-True ($self.Count -eq 1 -and [int]$self[0].metrics.selfTestCount -eq 51) 'Checkpoint 86a must expose 51 ScenarioRunner self-tests.'
Assert-True ([string]$normal.primaryStudy.id -eq 'tl2-itc12-weapon-penetration-layered-defense-permutations' -and [int]$normal.primaryStudy.variantCount -eq 288) 'Checkpoint 86a primary-study binding mismatch.'
Assert-True ((@($normal.nativeDependencyPrecheck.powerShellPaths) -join '|') -eq ($guardedPs -join '|')) 'Checkpoint 86a native-dependency PowerShell binding mismatch.'
Assert-True ((@($normal.nativeDependencyPrecheck.checkpointDefinitionPaths) -join '|') -eq ($guardedDefs -join '|')) 'Checkpoint 86a native-dependency definition binding mismatch.'

Write-Host '       Validating the 288-cell weapon-penetration x layered-defense study...'
$scenarioRel='src/StarCluster.ScenarioRunner/Scenarios/TL1Calibration/tl2-itc12-weapon-penetration-layered-defense-permutations.json'
$study=Read-Json $scenarioRel
$variants=@($study.variants)
Assert-True ([string]$study.id -eq 'tl2-itc12-weapon-penetration-layered-defense-permutations' -and $variants.Count -eq 288) 'CP86 study ID/count mismatch.'
Assert-True ([int]$study.trialsPerVariant -eq 10000) 'CP86 default trials-per-variant must remain 10,000.'
Assert-True ([string]$study.auxiliaryProfileCatalog -eq 'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/tl1-tl2-auxiliary-runtime-profiles-v0_3.json') 'CP86 auxiliary-profile catalog binding drifted.'
Assert-True ([string]$study.sensorEwProfileCatalog -eq 'src/StarCluster.ScenarioRunner/Scenarios/SensorEw/tl2-sew01-sensor-discrimination-isolation.json') 'CP86 Sensor/EW catalog binding drifted.'
$builds=@($study.builds)
Assert-True ($builds.Count -eq 1) 'CP86 must use exactly one fixed 35-Space reference build.'
$build=$builds[0]
foreach ($p in @('id','mainWeaponCount','mainReactorCount','activeSensor','shieldGenerator','kineticPdsCount','ecmSuite','eccmSuite','usedSpace','freeSupportSpace')) { Require-Property $build $p 'CP86 reference build' }
Assert-True ([string]$build.id -eq 'balanced_generalist_ew_major' -and [int]$build.mainWeaponCount -eq 1 -and [int]$build.mainReactorCount -eq 1 -and [bool]$build.activeSensor -and [bool]$build.shieldGenerator -and [int]$build.kineticPdsCount -eq 1 -and [bool]$build.ecmSuite -and [bool]$build.eccmSuite -and [int]$build.usedSpace -eq 35 -and [int]$build.freeSupportSpace -eq 0) 'CP86 fixed 35-Space reference build drifted.'

$requiredVariantProperties=@(
    'id','comparisonGroup','profileLabel','sideAFamily','sideBFamily','sideABuildId','sideBBuildId',
    'sideAAuxiliaryProfileId','sideBAuxiliaryProfileId','tacticalMapRadius','startingFuel','movementFuelPerHex','evasiveManeuverFuelCost',
    'sideAReactorOutputOverride','sideBReactorOutputOverride','sideAShieldCapacityOverride','sideBShieldCapacityOverride',
    'sideAPrimaryArmorProtectionOverride','sideAPrimaryArmorIntegrityOverride','sideBPrimaryArmorProtectionOverride','sideBPrimaryArmorIntegrityOverride',
    'sideAWeaponShieldPenetrationOverride','sideAWeaponArmorPenetrationOverride','sideBWeaponShieldPenetrationOverride','sideBWeaponArmorPenetrationOverride',
    'sideASensorEwProfileId','sideBSensorEwProfileId','sideAEcmPolicy','sideBEcmPolicy','sideAEccmPolicy','sideBEccmPolicy',
    'sideATacticalComputerTargetingBonusOverride','sideBTacticalComputerTargetingBonusOverride','sideATrackPolicy','sideBTrackPolicy',
    'sideASensorOverloadPolicy','sideBSensorOverloadPolicy','sideAStlOverloadPolicy','sideBStlOverloadPolicy',
    'sideATacticalPowerDoctrine','sideBTacticalPowerDoctrine','baseShieldRechargeEnabled','pdsEnabled','evasiveManeuversEnabled',
    'movementMode','movementOrder','initialRangeHexes','sideAAllowsApproximateDirectFire','sideBAllowsApproximateDirectFire'
)
for ($i=0; $i -lt $variants.Count; $i++) {
    $v=$variants[$i]
    foreach ($propertyName in $requiredVariantProperties) { Require-Property $v $propertyName "CP86 variant index $i" }
}
Assert-True (@($variants | Select-Object -ExpandProperty id -Unique).Count -eq 288) 'CP86 variant IDs must be unique.'
Assert-True (@($variants | Where-Object {$null -ne $_.PSObject.Properties['label']}).Count -eq 0) 'CP86 schema drift: use profileLabel, not legacy label.'
$groups=@($variants | Group-Object comparisonGroup)
$expectedGroups=@('c86-k-r3','c86-k-afirst','c86-k-bfirst','c86-e-r3','c86-e-afirst','c86-e-bfirst','c86-m-r3','c86-m-afirst','c86-m-bfirst')
Assert-True ($groups.Count -eq 9 -and (@($groups | Where-Object {$_.Count -ne 32}).Count -eq 0)) 'CP86 must contain 9 comparison groups of 32 variants.'
Assert-True ((@($groups.Name | Sort-Object) -join '|') -eq (@($expectedGroups | Sort-Object) -join '|')) 'CP86 comparison-group IDs drifted.'

$familyProfile=@{
    'Kinetic'=@{ control=@(1,0); apen=@(1,1); spen=@(2,0); combined=@(2,1) }
    'Energy'=@{ control=@(1,1); apen=@(1,2); spen=@(2,1); combined=@(2,2) }
    'Missile'=@{ control=@(1,2); apen=@(1,3); spen=@(2,2); combined=@(2,3) }
}
$groupFamily=@{ 'c86-k-r3'='Kinetic'; 'c86-k-afirst'='Kinetic'; 'c86-k-bfirst'='Kinetic'; 'c86-e-r3'='Energy'; 'c86-e-afirst'='Energy'; 'c86-e-bfirst'='Energy'; 'c86-m-r3'='Missile'; 'c86-m-afirst'='Missile'; 'c86-m-bfirst'='Missile' }
$environments=@('firm-reference','tall-dr1-eccm1')
$penetrationLabels=@('control','apen','spen','combined')
foreach ($g in $groups) {
    $family=[string]$groupFamily[$g.Name]
    Assert-True (-not [string]::IsNullOrWhiteSpace($family)) "CP86 group '$($g.Name)' has no expected family mapping."
    foreach ($env in $environments) {
        foreach ($shield in @(2,3)) {
            foreach ($ap in @(0,1)) {
                foreach ($penetration in $penetrationLabels) {
                    $label="$env-$penetration-s$shield-ap$ap-ai5"
                    $matches=@($g.Group | Where-Object {[string]$_.profileLabel -eq $label})
                    Assert-True ($matches.Count -eq 1) "CP86 pairing missing/duplicated '$label' in '$($g.Name)'."
                    $v=$matches[0]
                    $expected=@($familyProfile[$family][$penetration])
                    Assert-True ([string]$v.sideAFamily -eq $family -and [string]$v.sideBFamily -eq $family) "CP86 family isolation drifted in '$($v.id)'."
                    Assert-True ([int]$v.sideAWeaponShieldPenetrationOverride -eq [int]$expected[0] -and [int]$v.sideAWeaponArmorPenetrationOverride -eq [int]$expected[1]) "CP86 Side-A penetration profile drifted in '$($v.id)'."
                    $controlExpected=@($familyProfile[$family]['control'])
                    Assert-True ([int]$v.sideBWeaponShieldPenetrationOverride -eq [int]$controlExpected[0] -and [int]$v.sideBWeaponArmorPenetrationOverride -eq [int]$controlExpected[1]) "CP86 Side-B control penetration profile drifted in '$($v.id)'."
                    Assert-True ([int]$v.sideBShieldCapacityOverride -eq $shield -and [int]$v.sideBPrimaryArmorProtectionOverride -eq $ap -and [int]$v.sideBPrimaryArmorIntegrityOverride -eq 5) "CP86 target defense factorial drifted in '$($v.id)'."
                }
            }
        }
    }
}
foreach ($family in @('Kinetic','Energy','Missile')) { Assert-True (@($variants | Where-Object {[string]$_.sideAFamily -eq $family}).Count -eq 96) "CP86 family '$family' must have 96 variants." }
foreach ($penetration in $penetrationLabels) { Assert-True (@($variants | Where-Object {[string]$_.profileLabel -match "-$penetration-"}).Count -eq 72) "CP86 penetration profile '$penetration' must have 72 variants." }
foreach ($shield in @(2,3)) { foreach ($ap in @(0,1)) { Assert-True (@($variants | Where-Object {[int]$_.sideBShieldCapacityOverride -eq $shield -and [int]$_.sideBPrimaryArmorProtectionOverride -eq $ap -and [int]$_.sideBPrimaryArmorIntegrityOverride -eq 5}).Count -eq 72) "CP86 target defense S$shield/AP$ap/AI5 must have 72 variants." } }
Assert-True (@($variants | Where-Object {[int]$_.sideAReactorOutputOverride -ne 6 -or [int]$_.sideBReactorOutputOverride -ne 6}).Count -eq 0) 'CP86 must hold both reactors at 6 Operational TP.'
Assert-True (@($variants | Where-Object {[int]$_.sideAShieldCapacityOverride -ne 3 -or [int]$_.sideAPrimaryArmorProtectionOverride -ne 0 -or [int]$_.sideAPrimaryArmorIntegrityOverride -ne 5}).Count -eq 0) 'CP86 must hold Side-A defense at Shield3/AP0/AI5.'
Assert-True (@($variants | Where-Object {[string]$_.sideABuildId -ne 'balanced_generalist_ew_major' -or [string]$_.sideBBuildId -ne 'balanced_generalist_ew_major' -or [string]$_.sideAAuxiliaryProfileId -ne 'aux-r53-none-tl1' -or [string]$_.sideBAuxiliaryProfileId -ne 'aux-r53-none-tl1'}).Count -eq 0) 'CP86 reference build/auxiliary-profile binding drifted.'
Assert-True (@($variants | Where-Object {[int]$_.tacticalMapRadius -ne 5 -or [int]$_.startingFuel -ne 100 -or [int]$_.movementFuelPerHex -ne 2 -or [int]$_.evasiveManeuverFuelCost -ne 1}).Count -eq 0) 'CP86 tactical-map/fuel baseline drifted.'
Assert-True (@($variants | Where-Object {-not [bool]$_.baseShieldRechargeEnabled -or -not [bool]$_.pdsEnabled -or [bool]$_.evasiveManeuversEnabled}).Count -eq 0) 'CP86 stateful defense consumer path drifted.'
Assert-True (@($variants | Where-Object {[string]$_.sideATacticalPowerDoctrine -ne 'FullVolleyFirst' -or [string]$_.sideBTacticalPowerDoctrine -ne 'FullVolleyFirst'}).Count -eq 0) 'CP86 Tactical Power doctrine drifted.'
Assert-True (@($variants | Where-Object {[string]$_.sideATrackPolicy -ne 'AcquisitionFirstAutoActive' -or [string]$_.sideBTrackPolicy -ne 'AcquisitionFirstAutoActive'}).Count -eq 0) 'CP86 track policy drifted.'
Assert-True (@($variants | Where-Object {[string]$_.sideASensorOverloadPolicy -ne 'None' -or [string]$_.sideBSensorOverloadPolicy -ne 'None' -or [string]$_.sideAStlOverloadPolicy -ne 'None' -or [string]$_.sideBStlOverloadPolicy -ne 'None'}).Count -eq 0) 'CP86 overload isolation drifted.'
Assert-True (@($variants | Where-Object {[bool]$_.sideAAllowsApproximateDirectFire -or [bool]$_.sideBAllowsApproximateDirectFire}).Count -eq 0) 'CP86 degraded-fire capability must remain off.'
Assert-True (@($variants | Where-Object {[int]$_.sideATacticalComputerTargetingBonusOverride -ne 12 -or [int]$_.sideBTacticalComputerTargetingBonusOverride -ne 10}).Count -eq 0) 'CP86 Tactical Computer working/control values drifted.'
$firm=@($variants | Where-Object {[string]$_.profileLabel -like 'firm-reference-*'})
$tall=@($variants | Where-Object {[string]$_.profileLabel -like 'tall-dr1-eccm1-*'})
Assert-True ($firm.Count -eq 144 -and $tall.Count -eq 144) 'CP86 information-control environments must split 144/144.'
Assert-True (@($firm | Where-Object {[string]$_.sideASensorEwProfileId -ne 'tl1-balanced-0-control' -or [string]$_.sideBSensorEwProfileId -ne 'tl1-balanced-0-control' -or [string]$_.sideAEcmPolicy -ne 'None' -or [string]$_.sideBEcmPolicy -ne 'None' -or [string]$_.sideAEccmPolicy -ne 'None' -or [string]$_.sideBEccmPolicy -ne 'None'}).Count -eq 0) 'CP86 Firm-reference environment is not clean.'
Assert-True (@($tall | Where-Object {[string]$_.sideASensorEwProfileId -ne 'tl2-discrimination-1-candidate' -or [string]$_.sideBSensorEwProfileId -ne 'tl1-balanced-0-control' -or [string]$_.sideAEccmPolicy -ne 'ReactiveNormal' -or [string]$_.sideBEcmPolicy -ne 'Normal' -or [int]$_.sideAEccmNormalRatingOverride -ne 1 -or [int]$_.sideBEcmNormalRatingOverride -ne 2}).Count -eq 0) 'CP86 DR1+ECCM1 vs ECM2 environment drifted.'
Assert-True (@($variants | Where-Object {[string]$_.comparisonGroup -like '*-r3' -and ([string]$_.movementMode -ne 'HoldRange3' -or [string]$_.movementOrder -ne 'Simultaneous' -or [int]$_.initialRangeHexes -ne 3)}).Count -eq 0) 'CP86 fixed-R3 geometry drifted.'
Assert-True (@($variants | Where-Object {[string]$_.comparisonGroup -like '*-afirst' -and ([string]$_.movementMode -ne 'PreferredRange' -or [string]$_.movementOrder -ne 'SideAFirst' -or [int]$_.initialRangeHexes -ne 3)}).Count -eq 0) 'CP86 Side-A-first geometry drifted.'
Assert-True (@($variants | Where-Object {[string]$_.comparisonGroup -like '*-bfirst' -and ([string]$_.movementMode -ne 'PreferredRange' -or [string]$_.movementOrder -ne 'SideBFirst' -or [int]$_.initialRangeHexes -ne 3)}).Count -eq 0) 'CP86 Side-B-first geometry drifted.'

Write-Host '       Validating ScenarioRunner integration hooks and report contracts...'
$docsCode=Read-Text 'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatDocuments.cs'
$runnerCode=Read-Text 'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs'
$selfCode=Read-Text 'src/StarCluster.ScenarioRunner/ScenarioRunnerSelfTests.cs'
foreach ($needle in @('SideAWeaponShieldPenetrationOverride','SideBWeaponShieldPenetrationOverride','SideAWeaponArmorPenetrationOverride','SideBWeaponArmorPenetrationOverride')) { Assert-True ($docsCode.Contains($needle)) "Missing CP86 document field '$needle'." }
foreach ($needle in @(
    'tl2-itc12-weapon-penetration-layered-defense-permutations','ValidateTl2WeaponPenetrationLayeredDefenseCoverage','ApplyPrimaryWeaponPenetrationOverrides',
    'WriteTl2WeaponPenetrationLayeredDefenseReview','tl2-weapon-penetration-layered-defense-review.csv','tl2-weapon-penetration-layered-defense-paired-deltas.csv'
)) { Assert-True ($runnerCode.Contains($needle)) "Missing CP86 runner hook '$needle'." }
Assert-True ([regex]::Matches($runnerCode,'Tl2WeaponPenetrationLayeredDefenseStudyId').Count -eq 11) 'CP86 study ID must be registered across all expected runner dispatch/classification/report paths.'
$gateIds=@(
    'tl2-c86-variant-coverage','tl2-c86-penetration-profile-coverage','tl2-c86-layered-defense-factorial','tl2-c86-family-specific-isolation',
    'tl2-c86-defense-working-candidates-held','tl2-c86-reactor6-contemporary-baseline','tl2-c86-firm-reference-clean',
    'tl2-c86-contemporary-dr1-eccm1-restores-firm','tl2-c86-stateful-defense-consumer-path','tl2-c86-no-universal-production-promotion'
)
foreach ($gateId in $gateIds) {
    $count=[regex]::Matches($runnerCode,[regex]::Escape($gateId)).Count
    Assert-True ($count -eq 1) "CP86 gate '$gateId' must occur exactly once in the runner; found $count."
}
Assert-True ($selfCode.Contains('CP86 weapon penetration override changes only the selected family SPEN/APEN') -and $selfCode.Contains('TestCp86WeaponPenetrationOverrideSemantics')) 'CP86 weapon-penetration self-test is missing.'

Write-Host '       Validating documentation authority, continuity, and hygiene...'
$chat=Read-Text 'CHAT_README.md'
foreach ($needle in @('Mandatory for every new ChatGPT development session','Authority boundaries','Preserve subsystem-family identity','Do not balance nine isolated tiers','Enumerate legal extremes','reference authorities, not dumping grounds','Simulation_Development_Guidelines.md','docs/design/ai/AI_Doctrine_Registry_Architecture_*.md')) { Assert-True ($chat.Contains($needle)) "CHAT_README.md is missing required continuity anchor '$needle'." }
$sim=Read-Text 'docs/development/Simulation_Development_Guidelines.md'
foreach ($needle in @('not a checkpoint journal','Locally validated working candidate','Cross-TL validated candidate','Preserve subsystem-family identity','Legal-build enumeration','Cross-TL progression checks','screening')) { Assert-True ($sim.Contains($needle)) "Simulation Development Guidelines are missing '$needle'." }
$ai=Read-Text 'docs/design/ai/AI_Doctrine_Registry_Architecture_v0_3.md'
foreach ($needle in @('not a checkpoint diary','Respond to observable conditions rather than hidden causes','Preserve the combat package, not merely offense','A legal ship may be deliberately power-constrained','Family identity matters to AI evaluation too')) { Assert-True ($ai.Contains($needle)) "AI doctrine v0.3 is missing durable lesson '$needle'." }
Assert-True ([regex]::Matches($ai,'(?i)Checkpoint\s+\d').Count -eq 0) 'AI doctrine v0.3 must not contain numbered checkpoint history.'
Assert-True ([regex]::Matches($ai,'(?i)\b[0-9a-f]{64}\b').Count -eq 0) 'AI doctrine v0.3 must not contain evidence hashes.'
$matrix=Read-Text 'docs/design/player_technology/Technology_Architecture_Matrix_v1.md'
foreach ($needle in @('AP0 / AI5','Weapon-family penetration architecture','No symmetric promotion is implied','Preserve subsystem-family identity')) { Assert-True ($matrix.Contains($needle)) "Technology Matrix Markdown is missing '$needle'." }
Assert-True ([regex]::Matches($matrix,'(?i)Checkpoint\s+\d').Count -eq 0) 'Current Technology Matrix Markdown must not be a checkpoint journal.'
Assert-True ([regex]::Matches($matrix,'(?i)\b[0-9a-f]{64}\b').Count -eq 0) 'Current Technology Matrix Markdown must not contain evidence hashes.'
$matrixJsonText=Read-Text 'docs/archive/player_technology/pre-cp165-active/technology_architecture_matrix_v1.json'
foreach ($forbidden in @('acceptedEvidence','summarySha256','nextIntegrationStep')) { Assert-NoText $matrixJsonText $forbidden "Current Technology Matrix JSON contains obsolete checkpoint-history field '$forbidden'." }
$suite=Read-Text 'docs/design/testing/Technology_Integration_Permutation_Suite_Architecture_v0_6.md'
foreach ($needle in @('Technology Integration Permutation Suite Architecture v0.6','Preserve subsystem-family identity','Cross-TL direction','arbitrary legal build enumeration')) { Assert-True ($suite.Contains($needle)) "Standing suite v0.6 is missing '$needle'." }
Assert-True ([regex]::Matches($suite,'(?i)Checkpoint\s+\d').Count -eq 0) 'Standing suite architecture must not be a checkpoint diary.'
$suiteJson=Read-Json 'docs/design/testing/technology_integration_permutation_suite_v0_6.json'
Assert-True ($null -ne $suiteJson) 'Standing suite v0.6 JSON is unreadable.'
$suiteJsonText=Read-Text 'docs/design/testing/technology_integration_permutation_suite_v0_6.json'
Assert-NoText $suiteJsonText 'acceptedEvidence' 'Standing suite JSON must not embed accepted checkpoint evidence.'
Assert-NoText $suiteJsonText 'summarySha256' 'Standing suite JSON must not embed checkpoint summary hashes.'
Require-Property $suiteJson 'weaponPenetrationPackages' 'Standing suite v0.6 JSON'
$standingWeaponPromotion=$suiteJson.weaponPenetrationPackages
Require-Property $standingWeaponPromotion 'automaticPromotion' 'Standing suite v0.6 weapon-penetration package'
Require-Property $standingWeaponPromotion 'promotionPolicy' 'Standing suite v0.6 weapon-penetration package'
Assert-True ([bool]$standingWeaponPromotion.automaticPromotion -eq $false -and [string]$standingWeaponPromotion.promotionPolicy -eq 'family_specific_human_review') 'Standing suite JSON must disable automatic weapon promotion and require family-specific human review.'
Assert-True (@($suiteJson.activationPolicy | Where-Object {[string]$_ -like '*does not imply symmetric promotion*'}).Count -ge 1) 'Standing suite JSON must explicitly state that shared sensitivity does not imply symmetric promotion.'
$weaponProfile=Read-Json 'docs/design/player_technology/tl2_weapon_penetration_sensitivity_profile_v0_1.json'
Assert-True ([bool]$weaponProfile.promotionPolicy.automaticPromotion -eq $false -and [bool]$weaponProfile.promotionPolicy.familySpecificHumanReview -and [bool]$weaponProfile.promotionPolicy.sharedSensitivityDoesNotImplySharedProgression) 'Weapon penetration sensitivity profile must forbid automatic symmetric promotion and require family-specific review.'
$concept=Read-DocxText 'docs/Star_Cluster_Game_Concept_v0.6x.docx'
Assert-True ($concept.Contains('C-060') -and $concept.Contains('Subsystem families retain mechanical identity')) 'Concept v0.6x is missing the durable subsystem-family identity rule.'
foreach ($forbidden in @('ScenarioRunner','Monte Carlo','StarCluster.Core','Godot','.NET','Technology Integration Permutation Suite','trialsPerVariant','RepositoryOnly')) { Assert-NoText $concept $forbidden "Concept v0.6x still contains non-game development term '$forbidden'." }
$conceptCheckpointCount=[regex]::Matches($concept,'(?i)Checkpoint').Count
Assert-True ($conceptCheckpointCount -le 2) 'Concept v0.6x contains too much checkpoint/development-process material after the authority scrub.'
$workbookXml=Read-ZipEntryText 'docs/design/player_technology/StarCluster_Technology_Architecture_Matrix_v1.xlsx' 'xl/workbook.xml'
foreach ($sheetName in @('Armor','Weapon Penetration','Integration Guardrails')) { Assert-True ($workbookXml.Contains(('name="' + $sheetName + '"'))) "Technology Matrix workbook is missing '$sheetName'." }
Assert-True (-not $workbookXml.Contains('name="Validation Plan"')) 'Technology Matrix workbook must not retain the old Validation Plan sheet.'
$legacyCalibration=Read-Text 'docs/design/Technology_Calibration_And_Simulation_Architecture.md'
Assert-True ($legacyCalibration.Contains('Simulation_Development_Guidelines.md') -and $legacyCalibration.Contains('Do not append checkpoint history')) 'Legacy calibration architecture pointer is not directing readers to the durable development authority.'
$rootReadme=Read-Text 'README.md'
Assert-True ($rootReadme.Contains('Checkpoint 86a') -and $rootReadme.Contains('CHAT_README.md')) 'Root README is not pointing to Checkpoint 86a and the mandatory chat bootstrap.'
$docsReadme=Read-Text 'docs/README.md'
Assert-True ($docsReadme.Contains('CHAT_README.md') -and $docsReadme.Contains('Long-lived authorities are not checkpoint diaries')) 'Documentation README is missing the bootstrap/hygiene boundary.'
$techReadme=Read-Text 'docs/design/player_technology/README.md'
Assert-True ($techReadme.Contains('not a checkpoint diary') -and $techReadme.Contains('tl2_weapon_penetration_sensitivity_profile_v0_1.json') -and $techReadme.Contains('Simulation_Development_Guidelines.md')) 'Player Technology README is stale or has drifted from CP86 authority.'
$testingReadme=Read-Text 'docs/design/testing/README.md'
Assert-True ($testingReadme.Contains('Checkpoint_86_Validation_Tiers.md') -and $testingReadme.Contains('technology_integration_permutation_suite_v0_6.json') -and $testingReadme.Contains('not a checkpoint result log')) 'Testing README is stale or has drifted from CP86 authority.'
Assert-NoText $testingReadme 'Current must-always-run validation tier: `Checkpoint_85' 'Testing README still points to the superseded Checkpoint 85 active tier.'
$todo=Read-Text 'docs/Prototype_TODO.md'
Assert-True ($todo.Contains('Prototype TODO - Checkpoint 86a') -and $todo.Contains('current-action list') -and $todo.Contains('family-specific weapon-penetration permutations')) 'Prototype TODO is stale or has drifted from CP86a.'
Assert-NoText $todo 'Prototype TODO - Checkpoint 85' 'Prototype TODO still identifies the superseded Checkpoint 85 line.'

Write-Host '       Validating accepted CP85b provenance and frozen production code...'
$cp85ManifestRel='docs/validation/evidence/checkpoint-85b/CHECKPOINT_85b_SHA256SUMS.txt'
$cp85ManifestRecord=Read-Manifest $cp85ManifestRel
$cp85Manifest=$cp85ManifestRecord.Entries
$prov=Read-Json 'docs/validation/evidence/checkpoint-85b/checkpoint-85b-native-acceptance-provenance.json'
$acceptedCp85ManifestSha='88b21a2879847a8c50a454b9f904e6e490a2a803b59ce6e083121b275f27ac45'
Assert-True ([string]$prov.acceptanceSummary.status -eq 'Success') 'CP85b provenance must record successful native acceptance.'
Assert-True ([string]$prov.acceptanceSummary.checkpointManifestSha256 -eq $acceptedCp85ManifestSha) 'CP85b provenance manifest SHA-256 is not the accepted value.'
Assert-True ((Hash-Rel $cp85ManifestRel) -eq $acceptedCp85ManifestSha) 'Embedded CP85b evidence-manifest bytes do not match accepted native provenance.'
Assert-True ([int]$cp85ManifestRecord.PhysicalLineCount -eq 1647 -and [int]$cp85ManifestRecord.EntryCount -eq 1647) 'Accepted CP85b evidence manifest must contain exactly 1,647 unique entries.'
Write-Host ("       Accepted CP85b evidence manifest: {0} physical lines / {1} unique entries; SHA-256 matched provenance." -f $cp85ManifestRecord.PhysicalLineCount,$cp85ManifestRecord.EntryCount)
Assert-True ([string]$prov.designDisposition.armorAp0Ai5 -eq 'locally_validated_working_candidate') 'CP85b provenance must carry AP0/AI5 as locally validated.'
Assert-True ([string]$prov.designDisposition.armorAp1Ai4 -eq 'experimental_deferred_candidate') 'CP85b provenance must keep AP1/AI4 deferred.'
Assert-True ([string]$prov.designDisposition.shieldCapacity3Space3 -eq 'carried_locally_validated_working_candidate') 'CP85b provenance must carry Shield3/3 Space.'
Assert-True ([string]$prov.designDisposition.reactor6Tp6Space -eq 'carried_locally_validated_working_candidate') 'CP85b provenance must carry Reactor6/6 Space.'
$allowedRunner=@(
    'src/StarCluster.ScenarioRunner/ScenarioRunnerSelfTests.cs',
    'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatDocuments.cs',
    'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs'
)
foreach ($rel in @($cp85Manifest.Keys | Sort-Object)) {
    $freeze=$rel.StartsWith('src/StarCluster.Core/') -or $rel.StartsWith('src/StarCluster.Game/') -or $rel.StartsWith('tests/') -or ($rel.StartsWith('src/StarCluster.ScenarioRunner/') -and $allowedRunner -notcontains $rel)
    if ($freeze) { Assert-True ((Hash-Rel $rel) -eq [string]$cp85Manifest[$rel]) "Unexpected CP86 drift from accepted CP85b in '$rel'." }
}
$oldConceptRel='docs/Star_Cluster_Game_Concept_v0.6w.docx'
Assert-True ($cp85Manifest.ContainsKey($oldConceptRel)) 'Accepted CP85b manifest is missing Concept v0.6w.'
Assert-True ((Hash-Rel 'docs/archive/Star_Cluster_Game_Concept_v0.6w.docx') -eq [string]$cp85Manifest[$oldConceptRel]) 'Archived Concept v0.6w bytes drifted from accepted CP85b.'
$oldRunbookRel='docs/validation/Checkpoint_85b_CP85_Native_Contract_Provenance_Manifest_Hotfix.md'
Assert-True ($cp85Manifest.ContainsKey($oldRunbookRel)) 'Accepted CP85b manifest is missing its active validation runbook.'
Assert-True ((Hash-Rel 'docs/validation/archive/Checkpoint_85b_CP85_Native_Contract_Provenance_Manifest_Hotfix.md') -eq [string]$cp85Manifest[$oldRunbookRel]) 'Archived CP85b validation runbook bytes drifted from accepted CP85b.'
$activeValidation=@(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs\validation') -File -Filter 'Checkpoint_*.md')
Assert-True ($activeValidation.Count -eq 1 -and $activeValidation[0].Name -eq 'Checkpoint_86a_CP86_Standing_Suite_Promotion_Contract_Hotfix.md') 'Exactly one CP86a active validation runbook must remain.'
$activeConcept=@(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs') -File -Filter 'Star_Cluster_Game_Concept_v*.docx')
Assert-True ($activeConcept.Count -eq 1 -and $activeConcept[0].Name -eq 'Star_Cluster_Game_Concept_v0.6x.docx') 'Exactly one Concept v0.6x active document must remain.'
$rootTxt=@(Get-ChildItem -LiteralPath $repositoryRoot -File -Filter '*.txt')
Assert-True ($rootTxt.Count -eq 1 -and $rootTxt[0].Name -eq 'CHECKPOINT_86a_SHA256SUMS.txt') 'Repository root must contain only CHECKPOINT_86a_SHA256SUMS.txt as .txt.'

Write-Host '       CP86 continuity: CHAT_README + durable simulation/AI authorities + Concept gameplay-only scrub.'
Write-Host '       CP86 study: 3 weapon families x 4 penetration profiles x 4 target defenses x 2 information environments x 3 geometries = 288 variants.'
Write-Host '       Promotion boundary: common APEN/SPEN sensitivities are experimental instruments; no universal family promotion is permitted.'
Write-Host '       Normal workload: 11 stages / 288 substantive variants / 2,880,000 default substantive trials plus 288 smoke trials.'
Write-Host 'Checkpoint 86a contract validation passed.'
