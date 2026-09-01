[CmdletBinding()]
param([string]$RepositoryRoot)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($RepositoryRoot)) {
    $repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
} else {
    $repositoryRoot = (Resolve-Path $RepositoryRoot).Path
}

function Assert-True {
    param([bool]$Condition,[string]$Message)
    if (-not $Condition) { throw $Message }
}
function RelPath {
    param([string]$RelativePath)
    Join-Path $repositoryRoot ($RelativePath.Replace('/','\'))
}
function Read-Text {
    param([string]$RelativePath)
    $path = RelPath $RelativePath
    Assert-True (Test-Path -LiteralPath $path -PathType Leaf) "Required file '$RelativePath' is missing."
    [IO.File]::ReadAllText($path)
}
function Read-Json {
    param([string]$RelativePath)
    (Read-Text $RelativePath) | ConvertFrom-Json
}
function Hash-Rel {
    param([string]$RelativePath)
    (Get-FileHash -LiteralPath (RelPath $RelativePath) -Algorithm SHA256).Hash.ToLowerInvariant()
}
function Assert-Sequence {
    param($Actual,[string[]]$Expected,[string]$Message)
    $actualArray = @($Actual)
    Assert-True ($actualArray.Count -eq $Expected.Count) $Message
    for ($i = 0; $i -lt $Expected.Count; $i++) {
        Assert-True ([string]$actualArray[$i] -eq $Expected[$i]) $Message
    }
}
function Assert-ExactFileSet {
    param([string]$RelativeDirectory,[string[]]$Expected)
    $actual = @(Get-ChildItem -LiteralPath (RelPath $RelativeDirectory) -File | ForEach-Object Name | Sort-Object)
    $wanted = @($Expected | Sort-Object)
    Assert-True ($actual.Count -eq $wanted.Count) "Directory '$RelativeDirectory' active file count drifted."
    for ($i = 0; $i -lt $wanted.Count; $i++) {
        Assert-True ($actual[$i] -eq $wanted[$i]) "Directory '$RelativeDirectory' active file set drifted: expected '$($wanted[$i])', found '$($actual[$i])'."
    }
}
function Read-Manifest {
    param([string]$RelativePath)
    $map = @{}
    $lines = @(Get-Content -LiteralPath (RelPath $RelativePath))
    $lineNumber = 0
    foreach ($line in $lines) {
        $lineNumber++
        $match = [regex]::Match([string]$line,'^([0-9a-fA-F]{64})  (.+)$')
        Assert-True $match.Success "Manifest '$RelativePath' malformed at line $lineNumber."
        $relative = $match.Groups[2].Value.Replace('\','/')
        Assert-True (-not $map.ContainsKey($relative)) "Manifest '$RelativePath' duplicates '$relative'."
        $map[$relative] = $match.Groups[1].Value.ToLowerInvariant()
    }
    [pscustomobject]@{ EntryCount = $map.Count; Entries = $map }
}
function Test-IsGeneratedOrLocalPath {
    param([string]$RelativePath)
    $path = $RelativePath.Replace('\','/')
    if ($path -like '.git/*' -or $path -like '.vs/*' -or $path -like '.vscode/*' -or $path -like '.idea/*' -or $path -like 'out/*' -or $path -like 'src/StarCluster.Game/.godot/*' -or $path -match '(^|/)(bin|obj|TestResults)/') { return $true }
    if ($path -match '(^|/)__pycache__/' -or $path -match '\.pyc$') { return $true }
    if ($path -match '\.(user|userosscache|sln\.docstates|uid)$' -or $path -match '(^|/)\.suo$' -or $path -match '(^|/)(\.DS_Store|Thumbs\.db)$') { return $true }
    return $false
}
function Get-Cp104RepositoryOwnedFileSet {
    $map = @{}
    foreach ($file in @(Get-ChildItem -LiteralPath $repositoryRoot -Recurse -File -Force)) {
        $relative = $file.FullName.Substring($repositoryRoot.Length).TrimStart('\','/').Replace('\','/')
        if ($relative -eq 'CHECKPOINT_104_SHA256SUMS.txt') { continue }
        if (Test-IsGeneratedOrLocalPath -RelativePath $relative) { continue }
        $map[$relative] = $true
    }
    return $map
}
function Assert-Cp104GeneratedArtifactSequencePreflight {
    param($Expected)
    $outputDir = RelPath 'out/checkpoint-104'
    $null = New-Item -ItemType Directory -Path $outputDir -Force
    $probePath = Join-Path $outputDir 'repository-only-sequence-probe.json'
    '{"checkpoint":"104","generated":true}' | Set-Content -LiteralPath $probePath -Encoding UTF8
    try {
        $after = Get-Cp104RepositoryOwnedFileSet
        Assert-True ($after.Count -eq $Expected.Count) 'RepositoryOnly-generated artifacts must not change the repository-owned file set.'
        foreach ($relative in $Expected.Keys) {
            Assert-True ($after.ContainsKey([string]$relative)) "RepositoryOnly sequence preflight lost repository-owned path '$relative'."
        }
    } finally {
        Remove-Item -LiteralPath $probePath -Force -ErrorAction SilentlyContinue
    }
}

Write-Host '       Validating accepted CP103 provenance and frozen mechanics/research surfaces...'
Assert-True ((Hash-Rel 'docs/validation/evidence/checkpoint-103/CHECKPOINT_103_SHA256SUMS.txt') -eq 'ecc3b0c4db276f8302d320143cfee9e9e649d8ad601efb193aa5e600414a4ae2') 'Embedded accepted CP103 manifest hash drifted.'
Assert-True ((Hash-Rel 'docs/validation/evidence/checkpoint-103/checkpoint-103-native-acceptance-summary.json') -eq '5c60557113228e26646d7f6e85c5bc92cf48849366ac34b44c797738edc4f173') 'Embedded CP103 native acceptance summary drifted.'
Assert-True ((Hash-Rel 'docs/validation/evidence/checkpoint-103/cp103-primary-substantive-variants.csv') -eq 'f368aac3a83d4232b7a08fc601b8844d5dacb64777826c34ba1ae5f85a1c0a4f') 'Embedded accepted CP103 primary variants drifted.'
Assert-True ((Hash-Rel 'docs/validation/evidence/checkpoint-103/cp103-analysis.json') -eq 'd05e554c2ad116d24c4f38668832e663cf644ee9cfde3b2fb233992b13348d65') 'Embedded accepted CP103 analysis drifted.'
Assert-True ((Hash-Rel 'tools/calibration/checkpoints/checkpoint-103.json') -eq 'f9fa4ae6bb2063f504d8a347757ae503a8d7594167c19ba92b185ba71db92caf') 'Accepted CP103 normal definition drifted.'
Assert-True ((Hash-Rel 'src/StarCluster.ScenarioRunner/CrossTlIntegration/CrossTlBuildPermutationRunner.cs') -eq '6cebb3efa11e1fea63cab88377b9de0960b3d5e2a9029385a72556c87afe2984') 'CP104 must not change the frozen cross-TL C# research runner.'
Assert-True ((Hash-Rel 'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs') -eq '8c46eb15814737a1dae80c3320be385361b054c6f8c3cce96afd4dd3a4cc525e') 'CP104 must not change the frozen integrated C# research runner.'
Assert-True ((Hash-Rel 'src/StarCluster.ScenarioRunner/ScenarioRunnerSelfTests.cs') -eq 'af3bb02e64f371f20a4ed6051c7f90fbec960ed6fc614960893d17e28ee858ce') 'CP104 must not change accepted ScenarioRunner self-tests.'

$accepted = Read-Json 'docs/validation/evidence/checkpoint-103/checkpoint-103-native-acceptance-summary.json'
Assert-True ([string]$accepted.status -eq 'Success') 'Embedded CP103 acceptance summary must be successful.'
Assert-True ([int]$accepted.tests.passed -eq 876 -and [int]$accepted.tests.failed -eq 0) 'Embedded CP103 xUnit evidence drifted.'
Assert-True ([int]$accepted.aggregates.failedGates -eq 0) 'Embedded CP103 acceptance must contain zero failed gates.'

Write-Host '       Validating CP104 v1.3 diagnostic declaration and higher-TL handoff gate...'
$study = Read-Json 'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/cross-tl-build-permutation-foundation-v1_3.json'
Assert-True ([string]$study.schemaVersion -eq 'star-cluster-cross-tl-build-permutation-v8') 'CP104 must use cross-TL schema v8.'
Assert-True ([string]$study.checkpoint -eq '104') 'CP104 study checkpoint must be JSON string 104.'
Assert-True ([string]$study.coverageMode -eq 'diagnostic_overlay') 'CP104 study must remain diagnostic_overlay.'
Assert-True ([int64]$study.expectedRawCombinationCount -eq 124002900) 'CP104 declared raw option product drifted.'
Assert-True ([int]$study.expectedLegalBuildCount -eq 52) 'CP104 expected legal named-build count drifted.'
Assert-True ([int]$study.expectedExactFillBuildCount -eq 12 -and [int]$study.expectedNearFillBuildCount -eq 14 -and [int]$study.expectedUnderfilledBuildCount -eq 26) 'CP104 Space-class counts drifted.'
Assert-True (@($study.namedRecipes).Count -eq 56 -and [int]$study.expectedNamedRecipeCount -eq 56) 'CP104 named recipe count drifted.'
Assert-True (@($study.pairingGroups).Count -eq 128 -and [int]$study.expectedLogicalPairingCount -eq 128) 'CP104 logical pairing count drifted.'
Assert-True (@($study.geometries).Count -eq 2 -and [int]$study.expectedGeneratedVariantCount -eq 256) 'CP104 geometry/variant contract drifted.'
Assert-True ([int]$study.trialsPerVariant -eq 500) 'CP104 must retain 500 trials per substantive variant.'
Assert-True ([string]$study.researchSimulationEngine -eq 'starcluster-python-research-v1' -and [string]$study.pythonRuntimeMajorMinor -eq '3.13') 'CP104 Python research-engine declaration drifted.'
$categories = @($study.diagnosticCategories | ForEach-Object { [string]$_ })
Assert-Sequence $categories @('legacy-response','movement','energy-synergy','power-hotspot','control') 'CP104 diagnostic categories drifted.'
Assert-True ([bool]$study.higherTlExpansionGate.afterCheckpoint104) 'CP104 must retain the higher-TL expansion gate.'
Assert-True ([string]$study.higherTlExpansionGate.defaultNextPhase -eq 'extend-basic-subsystem-tl-chart-beyond-tl3') 'CP104 higher-TL next phase drifted.'
Assert-True ([bool]$study.higherTlExpansionGate.additionalTl3CalibrationOnlyForArchitecturalDefect) 'Further TL3 calibration must remain architecture-defect-only after CP104.'

Write-Host '       Validating CP104 Python command surface and active documentation authority...'
$cliText = Read-Text 'tools/simulation/starcluster_research/cli.py'
Assert-True ($cliText.IndexOf('analyze-cp104',[StringComparison]::Ordinal) -ge 0) 'Python CLI must expose analyze-cp104.'
$runnerText = Read-Text 'tools/simulation/starcluster_research/runner.py'
Assert-True ($runnerText.IndexOf('def analyze_cp104',[StringComparison]::Ordinal) -ge 0) 'Python runner must implement analyze_cp104.'
$schema = Read-Json 'tools/simulation/schemas/cross_tl_v8.schema.json'
$checkpointEnum = @($schema.properties.checkpoint.enum | ForEach-Object { [string]$_ })
Assert-True ($checkpointEnum.Count -eq 2 -and $checkpointEnum[0] -eq '103' -and $checkpointEnum[1] -eq '104') 'V8 schema must accept string checkpoints 103 and 104 only.'
$runtime = Read-Json 'tools/simulation/PYTHON_RUNTIME.json'
Assert-True ([string]$runtime.majorMinor -eq '3.13' -and [bool]$runtime.stdlibOnly) 'CP104 Python runtime must remain stdlib-only CPython 3.13.x.'
$suite = Read-Json 'docs/design/testing/technology_integration_permutation_suite_v0_19.json'
Assert-True ([int]$suite.checkpoint -eq 104 -and [bool]$suite.currentCoverage.cp104TargetedDiagnosticClosure.automaticTechnologyChange -eq $false) 'Standing permutation suite CP104 lifecycle drifted.'
$matrix = Read-Json 'docs/archive/player_technology/pre-cp165-active/technology_architecture_matrix_v1.json'
Assert-True ([int]$matrix.checkpoint -eq 104) 'Technology Matrix must identify CP104 as the current documentation checkpoint.'
Assert-True ([string]$matrix.integrationArchitecture.standingPermutationSuite -eq 'docs/design/testing/technology_integration_permutation_suite_v0_19.json') 'Technology Matrix standing permutation-suite pointer drifted.'
Assert-True ([bool]$matrix.integrationArchitecture.cp103NativeAccepted -and -not [bool]$matrix.integrationArchitecture.cp104AutomaticPromotion) 'Technology Matrix CP103/CP104 lifecycle drifted.'
Assert-True ([string]$matrix.integrationArchitecture.postCp104DefaultPhase -eq 'extend_basic_subsystem_tl_chart_beyond_tl3') 'Technology Matrix post-CP104 planning gate drifted.'

Assert-ExactFileSet 'docs/design/testing' @('README.md','Checkpoint_104_Validation_Tiers.md','checkpoint_104_validation_suite_policy_v0_1.json','Technology_Integration_Permutation_Suite_Architecture_v0_19.md','technology_integration_permutation_suite_v0_19.json')
Assert-ExactFileSet 'docs/validation' @('README.md','Checkpoint_104_TL3_Diagnostic_Closure_And_Higher_TL_Expansion_Gate.md')
$activeConcepts = @(Get-ChildItem -LiteralPath (RelPath 'docs') -File -Filter 'Star_Cluster_Game_Concept*.docx' | ForEach-Object Name)
Assert-True ($activeConcepts.Count -eq 1 -and $activeConcepts[0] -eq 'Star_Cluster_Game_Concept_v0.7d.docx') 'Exactly Concept v0.7d must remain active; CP104 changes no Concept rule/value.'
foreach ($path in @('README.md','CHAT_README.md','docs/README.md','docs/design/README.md','docs/design/player_technology/README.md','docs/design/testing/README.md','docs/validation/README.md','docs/Prototype_TODO.md','docs/design/testing/Technology_Integration_Permutation_Suite_Architecture_v0_19.md','docs/validation/Checkpoint_104_TL3_Diagnostic_Closure_And_Higher_TL_Expansion_Gate.md')) {
    $text = Read-Text $path
    Assert-True ($text.IndexOf('CP102 Corrected Replacement 3 is the latest native-accepted',[StringComparison]::OrdinalIgnoreCase) -lt 0) "Active document '$path' retains stale CP102 latest-acceptance authority."
}

Write-Host '       Validating final repository manifest and RepositoryOnly-to-full-run sequence safety...'
$manifest = Read-Manifest 'CHECKPOINT_104_SHA256SUMS.txt'
$actual = Get-Cp104RepositoryOwnedFileSet
Assert-True ($actual.Count -eq $manifest.EntryCount) "CP104 manifest entry count $($manifest.EntryCount) does not match repository-owned file count $($actual.Count)."
foreach ($relative in $manifest.Entries.Keys) {
    Assert-True ($actual.ContainsKey([string]$relative)) "CP104 manifest lists missing/unowned path '$relative'."
    Assert-True ((Hash-Rel ([string]$relative)) -eq [string]$manifest.Entries[[string]$relative]) "CP104 manifest hash mismatch for '$relative'."
}
foreach ($relative in $actual.Keys) {
    Assert-True ($manifest.Entries.ContainsKey([string]$relative)) "Repository-owned path '$relative' is missing from CP104 manifest."
}
Assert-True (-not $manifest.Entries.ContainsKey('CHECKPOINT_103_SHA256SUMS.txt')) 'Superseded CP103 root manifest must not remain repository-owned in CP104.'
Assert-Cp104GeneratedArtifactSequencePreflight -Expected $actual

Write-Host "       CP104 contract verified: $($manifest.EntryCount) repository-owned files; accepted CP103 evidence preserved; v1.3 52 named legal builds / 128 pairings / 256 variants / 128,000 substantive trials; higher-TL expansion gate retained; zero automatic promotion."
