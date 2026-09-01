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
    Assert-True ($null -ne $text) "Required text file '$RelativePath' returned a null text value."
    return [string]$text
}
function Read-Json {
    param([string]$RelativePath)
    $text = Read-Text $RelativePath
    Assert-True (-not [string]::IsNullOrWhiteSpace($text)) "Required JSON file '$RelativePath' is empty."
    return ($text | ConvertFrom-Json)
}
function Read-DocxText {
    param([string]$RelativePath)
    $path = Join-Path $repositoryRoot $RelativePath
    Assert-True (Test-Path -LiteralPath $path -PathType Leaf) "Required DOCX '$RelativePath' is missing."

    Add-Type -AssemblyName System.IO.Compression.FileSystem -ErrorAction Stop | Out-Null
    $archive = $null
    try {
        $archive = [System.IO.Compression.ZipFile]::OpenRead($path)
        $entry = $archive.GetEntry('word/document.xml')
        Assert-True ($null -ne $entry) "DOCX '$RelativePath' is missing word/document.xml."

        $stream = $null
        $reader = $null
        try {
            $stream = $entry.Open()
            $reader = New-Object System.IO.StreamReader($stream)
            $xmlText = $reader.ReadToEnd()
            Assert-True (-not [string]::IsNullOrWhiteSpace($xmlText)) "DOCX '$RelativePath' has empty word/document.xml content."

            [xml]$xml = $xmlText
            Assert-True ($null -ne $xml.DocumentElement) "DOCX '$RelativePath' document.xml has no document element."
            $text = [string]$xml.DocumentElement.InnerText
            Assert-True (-not [string]::IsNullOrWhiteSpace($text)) "DOCX '$RelativePath' produced no document text."
            return $text
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

Write-Host '       Validating native-dependency declarations...'
$guard = Join-Path $repositoryRoot 'tools\checkpoints\Test-NativeAcceptanceDependencies.ps1'
$normalRel = 'tools/calibration/checkpoints/checkpoint-77a.json'
$deepRel = 'tools/calibration/checkpoints/checkpoint-77a-deep-calibration.json'
$guardedPs = @(
    'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1',
    'tools/checkpoints/checkpoint-77a/apply_checkpoint_77a.ps1',
    'tools/checkpoints/checkpoint-77a/test_checkpoint_77a_contract.ps1',
    'tools/calibration/run_calibration_checkpoint.ps1'
)
$guardedDefs = @($normalRel, $deepRel)
& $guard -RepositoryRoot $repositoryRoot -PowerShellPaths $guardedPs -CheckpointDefinitionPaths $guardedDefs

Write-Host '       Validating Checkpoint 77a definitions and unchanged workload accounting...'
$normal = Read-Json $normalRel
$deep = Read-Json $deepRel
Assert-True ([string]$normal.checkpointId -eq '77a' -and [string]$deep.checkpointId -eq '77a') 'Checkpoint 77a definition ID mismatch.'
Assert-True ([string]$normal.manifestFile -eq 'CHECKPOINT_77A_SHA256SUMS.txt' -and [string]$deep.manifestFile -eq 'CHECKPOINT_77A_SHA256SUMS.txt') 'Checkpoint 77a manifest binding mismatch.'
Assert-True ([string]$normal.outputRoot -eq 'out/checkpoint-77a' -and [string]$deep.outputRoot -eq 'out/checkpoint-77a-deep-calibration') 'Checkpoint 77a output-root binding mismatch.'
Assert-True ((@($normal.nativeDependencyPrecheck.powerShellPaths) -join '|') -eq ($guardedPs -join '|')) 'Checkpoint 77a normal native-dependency PowerShell path binding mismatch.'
Assert-True ((@($deep.nativeDependencyPrecheck.powerShellPaths) -join '|') -eq ($guardedPs -join '|')) 'Checkpoint 77a deep native-dependency PowerShell path binding mismatch.'
Assert-True ((@($normal.nativeDependencyPrecheck.checkpointDefinitionPaths) -join '|') -eq ($guardedDefs -join '|')) 'Checkpoint 77a normal native-dependency definition binding mismatch.'
Assert-True ((@($deep.nativeDependencyPrecheck.checkpointDefinitionPaths) -join '|') -eq ($guardedDefs -join '|')) 'Checkpoint 77a deep native-dependency definition binding mismatch.'
Assert-True (@($normal.stages).Count -eq 8 -and @($deep.stages).Count -eq 30) 'Checkpoint 77a stage-count mismatch.'
Assert-True ([int]$normal.checkpointMetrics.stageCount -eq 8 -and [int]$normal.checkpointMetrics.monteCarloVariantCount -eq 0 -and [int]$normal.checkpointMetrics.trialsAtDefault -eq 0) 'Checkpoint 77a normal suite must contain no Monte Carlo workload.'
Assert-True ([int]$deep.checkpointMetrics.stageCount -eq 30 -and [int]$deep.checkpointMetrics.monteCarloVariantCount -eq 1598 -and [int]$deep.checkpointMetrics.trialsAtDefault -eq 15980000) 'Checkpoint 77a Deep Calibration workload mismatch.'
$expectedStages = @('deterministic','tl1-phase-a','tl1-phase-b','tl1-installation-space-envelope','tl1-sensor-ew-foundation','auxiliary-resource-endurance','checkpoint-53-resource-semantics-lock','runner-self-tests')
$stageIds = @($normal.stages | ForEach-Object { [string]$_.id })
Assert-True (($stageIds -join '|') -eq ($expectedStages -join '|')) 'Checkpoint 77a normal stage ordering mismatch.'
$normalSelfTest = @($normal.stages | Where-Object { [string]$_.id -eq 'runner-self-tests' })
Assert-True ($normalSelfTest.Count -eq 1 -and [int]$normalSelfTest[0].metrics.selfTestCount -eq 47) 'Checkpoint 77a ScenarioRunner self-test count mismatch.'
foreach ($definition in @($normal, $deep)) {
    foreach ($docPath in @($definition.documentation)) {
        Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot ([string]$docPath)) -PathType Leaf) "Checkpoint 77a definition references missing documentation/input '$docPath'."
    }
}

Write-Host '       Validating Tactical Computer degraded-fire ownership...'
$computerData = Read-Json 'docs/archive/player_technology/pre-cp165-active/tactical_computer_fire_control_profiles_v0_1.json'
Assert-True ([int]$computerData.schemaVersion -eq 1 -and @($computerData.profiles).Count -eq 1) 'Tactical Computer fire-control catalog shape mismatch.'
$tl1 = $computerData.profiles[0]
Assert-True ([int]$tl1.technologyLevel -eq 1 -and [int]$tl1.approximateTrackDirectFireAccuracyPenaltyPercentagePoints -eq 25) 'TL1 Tactical Computer degraded-fire value must be 25 percentage points.'
Assert-True ([bool]$tl1.requiresExplicitWeaponCapability -and -not [bool]$tl1.appliesToMissileTerminalAttacks) 'TL1 degraded-fire ownership boundaries mismatch.'
Assert-True ([string]$tl1.conditionMappingStatus -eq 'deferred') 'Tactical Computer damage-condition mapping must remain deferred.'
Assert-True ([bool]$computerData.guardrails.eccmCounterplayMustRemainEconomicallyRelevant -and [bool]$computerData.guardrails.revalidateWhenComputerEcmEccmOrSensorProgressionChanges) 'Tactical Computer/EW progression guardrails missing.'

$weaponSource = Read-Text 'src/StarCluster.Core/Combat/DirectFire/DirectFireWeaponProfile.cs'
$computerSource = Read-Text 'src/StarCluster.Core/Combat/DirectFire/TacticalComputerFireControlProfile.cs'
$eligibilitySource = Read-Text 'src/StarCluster.Core/Combat/DirectFire/DirectFireTargetEligibility.cs'
$trackEligibilitySource = Read-Text 'src/StarCluster.Core/Combat/Tracking/DirectFireTrackEligibility.cs'
Assert-True ($weaponSource.Contains('AllowsApproximateTrackFire') -and -not $weaponSource.Contains('ApproximateTrackAccuracyPenalty')) 'DirectFireWeaponProfile must own degraded-fire permission but not its numerical penalty.'
Assert-True ($computerSource.Contains('ApproximateTrackDirectFireAccuracyPenalty') -and $computerSource.Contains('SupportsApproximateTrackDirectFire')) 'TacticalComputerFireControlProfile degraded-fire rating missing.'
Assert-True ($eligibilitySource.Contains('weapon.AllowsApproximateTrackFire') -and $eligibilitySource.Contains('tacticalComputer is { SupportsApproximateTrackDirectFire: true }') -and $eligibilitySource.Contains('tacticalComputer!.ApproximateTrackDirectFireAccuracyPenalty')) 'Direct-fire eligibility must require both weapon permission and supporting Tactical Computer and use the computer penalty.'
Assert-True (-not $trackEligibilitySource.Contains('DirectFireWeaponProfile')) 'Generic DirectFireTrackEligibility must not duplicate weapon/computer degraded-fire resolution.'

$eligibilityTests = Read-Text 'tests/StarCluster.Tests/Combat/DirectFire/DirectFireTargetEligibilityTests.cs'
$computerTests = Read-Text 'tests/StarCluster.Tests/Combat/DirectFire/TacticalComputerFireControlProfileTests.cs'
Assert-True ($eligibilityTests.Contains('TraitWeaponMayFireOnApproximateTrackWithTacticalComputerPenalty') -and $eligibilityTests.Contains('TraitWeaponStillRejectsApproximateTrackWithoutComputerSupport') -and $eligibilityTests.Contains('MissileInterceptionRemainsFirmOnlyEvenForTraitWeapon')) 'Direct-fire degraded-fire ownership regressions are incomplete.'
Assert-True ($computerTests.Contains('Tl1ArchitectureMayRepresentTwentyFivePointDegradedFirePenalty')) 'TL1 Tactical Computer -25 deterministic regression missing.'
$missileTerminalTests = Read-Text 'tests/StarCluster.Tests/Combat/Missiles/MissileTerminalResolutionTests.cs'
Assert-True ($missileTerminalTests.Contains('PeerGuidanceCannotAuthorizeBaselineCommandGuidedTerminalAttack') -and $missileTerminalTests.Contains('PeerGuidanceCanAuthorizeTerminalAttackWhenProfileExplicitlyAllowsIt') -and $missileTerminalTests.Contains('SensorPlusSeekerRejectsRemoteApproximateCueWithoutLocalNavigationTrack') -and $missileTerminalTests.Contains('SensorPlusSeekerCanRefineLocalApproximateNavigationTrackIntoFirm')) 'Accepted missile terminal-guidance guardrail regressions are missing.'

Write-Host '       Validating retained study semantics and production exclusions...'
$runner = Read-Text 'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs'
Assert-True ($runner.Contains('tacticalComputerApproximateTrackAccuracyPenalty') -and $runner.Contains('SideAApproximateDirectFireAccuracyPenalty')) 'Retained integrated study must interpret historical penalty fields as computer-derived calibration overrides.'
$gameMain = Read-Text 'src/StarCluster.Game/Scripts/Main.cs'
Assert-True (-not $gameMain.Contains('allowsApproximateTrackFire: true')) 'Checkpoint 77 must not enable degraded fire on the Godot production/demo main weapon.'
$productionApproximateEnable = Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'src') -Recurse -File -Filter '*.cs' | Where-Object { $_.FullName -notlike '*StarCluster.ScenarioRunner*' } | Select-String -SimpleMatch 'allowsApproximateTrackFire: true'
Assert-True (@($productionApproximateEnable).Count -eq 0) 'Checkpoint 77 must not enable degraded fire in production Core/Game weapon construction.'
Assert-True ($gameMain.Contains('PrototypeVersion = "tactical-prototype"') -and -not $gameMain.Contains('Checkpoint 18') -and -not $gameMain.Contains('checkpoint-18')) 'Godot presentation must not advertise stale Checkpoint 18 identity.'

Write-Host '       Validating PowerShell 5.1-safe Concept extraction and missile architecture synchronization...'
$conceptText = Read-DocxText 'docs/Star_Cluster_Game_Concept_v0.6p.docx'
Assert-True (-not [string]::IsNullOrWhiteSpace($conceptText)) 'Concept v0.6p DOCX text extraction returned empty content.'
Assert-True ($conceptText.Contains('current TL1 Tactical Computer degraded-fire rating is -25 percentage points')) 'Concept v0.6p is missing the TL1 Tactical Computer -25 degraded-fire rule.'
Assert-True ($conceptText.Contains('weapon owns only permission') -or $conceptText.Contains('weapon owns permission')) 'Concept v0.6p is missing degraded-fire ownership separation.'
Assert-True ($conceptText.Contains('Swarmer concept is deliberate volume saturation')) 'Concept v0.6p is missing the Swarmer volume-saturation clarification.'
Assert-True (-not ($conceptText -match 'Checkpoint\s+7[0-9]')) 'Active Concept must not contain checkpoint-history prose for Checkpoints 70-79.'
Assert-True (-not $conceptText.Contains('Filenames include the checkpoint identifier') -and -not $conceptText.Contains('Checkpoint 69 tests one normal TL1 Active mode')) 'Active Concept retains obsolete checkpoint-specific logging or sensor glossary wording.'
Assert-True ($conceptText.Contains('stable implementation/diagnostic identifier') -and $conceptText.Contains('diagnostic-contract/build and session identifiers')) 'Active Concept diagnostic-log vocabulary is not synchronized with the runtime scrub.'
$missileDoc = Read-Text 'docs/design/Missile_Guidance_Datalink_Sensor_And_Seeker_Architecture.md'
Assert-True ($missileDoc.Contains('large barrage into the estimated target volume') -and $missileDoc.Contains('Ordinary missile profiles continue to require the legitimate Firm terminal solution')) 'Missile architecture must preserve Firm baseline and clarify volume-saturation future capability.'
$missileCurrent = ($missileDoc -split '## Historical implementation and validation notes')[0]
Assert-True (-not ($missileCurrent -match 'Checkpoint\s+(15|16|17|18|19|20|21)')) 'Current-rule portion of missile architecture still contains checkpoint-specific implementation wording.'

Write-Host '       Validating documentation/runtime cleanup...'
Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot 'docs\archive\source-readmes\StarCluster.Game_README_checkpoint18_history.md') -PathType Leaf) 'Historical Godot README archive missing.'
Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot 'docs\archive\source-readmes\StarCluster.ScenarioRunner_README_historical_checkpoint_commands.md') -PathType Leaf) 'Historical ScenarioRunner README archive missing.'
Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot 'docs\archive\source-readmes\Calibration_Harness_README_historical_checkpoint_commands.md') -PathType Leaf) 'Historical calibration-harness README archive missing.'
Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot 'docs\archive\design-readmes\Player_Technology_README_checkpoint69d_history.md') -PathType Leaf) 'Historical player-technology README archive missing.'
$gameReadme = Read-Text 'src/StarCluster.Game/README.md'
$runnerReadme = Read-Text 'src/StarCluster.ScenarioRunner/README.md'
$technologyReadme = Read-Text 'docs/design/player_technology/README.md'
$calibrationReadme = Read-Text 'tools/calibration/README.md'
Assert-True (-not $gameReadme.Contains('Checkpoint 18 retains') -and $gameReadme.Contains('tactical-prototype')) 'Current Godot README still contains stale checkpoint authority.'
Assert-True ($runnerReadme.Contains('Tactical Computer/fire-control degraded-fire penalty') -and -not $runnerReadme.Contains('## Checkpoint 48')) 'Current ScenarioRunner README did not replace accumulated checkpoint commands.'
Assert-True ($technologyReadme.Contains('Tactical_Computer_Degraded_Fire_Architecture_v0_1.md') -and -not $technologyReadme.Contains('Star_Cluster_Game_Concept_v0.6h.docx')) 'Player technology README is not current.'
Assert-True ($calibrationReadme.Contains('Validation tiers') -and $calibrationReadme.Contains('actual-consumer preflight') -and -not $calibrationReadme.Contains('## Checkpoint 35')) 'Calibration harness README still presents historical checkpoint chronology as current guidance.'
$designReadme = Read-Text 'docs/design/README.md'
$technologyArchitecture = Read-Text 'docs/design/Technology_Calibration_And_Simulation_Architecture.md'
$aiArchitecture = Read-Text 'docs/design/ai/AI_Doctrine_Registry_Architecture_v0_2.md'
Assert-True ($designReadme.Contains('Authority order') -and $designReadme.Contains('Tactical_Computer_Degraded_Fire_Architecture_v0_1.md') -and $designReadme.Contains('Historical material')) 'Current design-document authority/navigation index is incomplete.'
Assert-True ($technologyArchitecture.Contains('Authority and scope') -and $technologyArchitecture.Contains('Tactical Computer/fire-control profile owns the **numerical accuracy penalty**') -and $technologyArchitecture.Contains('actual-consumer preflight') -and -not $technologyArchitecture.Contains('## Checkpoint 21a')) 'Technology calibration architecture is not a concise current-authority guide.'
Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot 'docs\archive\design-architecture\Technology_Calibration_And_Simulation_Architecture_historical_checkpoint_evolution.md') -PathType Leaf) 'Historical Technology Calibration checkpoint chronology archive missing.'
Assert-True ($aiArchitecture.Contains('Current accepted TL1 EW doctrine') -and $aiArchitecture.Contains('Current degraded-fire interaction') -and $aiArchitecture.Contains('weapon/variant/upgrade') -and $aiArchitecture.Contains('Tactical Computer')) 'AI doctrine architecture is not synchronized with the current degraded-fire ownership boundary.'

$scenarioInitialization = Read-Text 'src/StarCluster.Core/Simulation/ScenarioInitializationService.cs'
Assert-True ($scenarioInitialization.Contains('DiagnosticContractVersion = "checkpoint-19"') -and -not $scenarioInitialization.Contains('private const string CheckpointVersion')) 'Frozen scenario diagnostic label must be explicitly identified as a compatibility contract, not current checkpoint identity.'

Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot 'docs\validation\archive\Checkpoint_77_Architecture_Concept_And_Runtime_Scrub.md') -PathType Leaf) 'Checkpoint 77 architecture-scrub runbook must be archived by the 77a hotfix.'

$activeConcepts = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs') -File -Filter 'Star_Cluster_Game_Concept_v*.docx')
Assert-True ($activeConcepts.Count -eq 1 -and $activeConcepts[0].Name -eq 'Star_Cluster_Game_Concept_v0.6p.docx') 'Exactly Concept v0.6p must remain active under docs/.'
Assert-True (Test-Path -LiteralPath (Join-Path $repositoryRoot 'docs\archive\Star_Cluster_Game_Concept_v0.6o.docx') -PathType Leaf) 'Concept v0.6o must be archived.'
$validationFiles = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'docs\validation') -File -Filter 'Checkpoint_*.md')
Assert-True ($validationFiles.Count -eq 1 -and $validationFiles[0].Name -eq 'Checkpoint_77a_PowerShell_5_1_DOCX_Contract_Reader_Hotfix.md') 'Exactly one Checkpoint 77a active validation runbook must remain.'
$rootTxt = @(Get-ChildItem -LiteralPath $repositoryRoot -File -Filter '*.txt')
Assert-True ($rootTxt.Count -eq 1 -and $rootTxt[0].Name -eq 'CHECKPOINT_77A_SHA256SUMS.txt') 'Repository root must contain only CHECKPOINT_77A_SHA256SUMS.txt as .txt.'

Write-Host '       Degraded-fire architecture: weapon permission + Tactical Computer penalty; TL1 = -25 pp; Firm and missile-interception guardrails preserved.'
Write-Host '       Documentation scrub: Concept v0.6p current, source READMEs consolidated, stale checkpoint presentation labels removed, historical evidence retained in archives.'
Write-Host '       Validation tiers: 8 normal deterministic stages / 0 Monte Carlo variants; Deep Calibration remains optional at 30 stages / 1,598 variants.'
Write-Host '       PowerShell 5.1-safe DOCX reader: DocumentElement.InnerText + explicit null/empty guards.'
Write-Host 'Checkpoint 77a contract validation passed.'
