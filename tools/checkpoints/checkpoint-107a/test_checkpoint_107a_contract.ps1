[CmdletBinding()]
param([string]$RepositoryRoot)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($RepositoryRoot)) {
    $repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
}
else {
    $repositoryRoot = (Resolve-Path $RepositoryRoot).Path
}

function Assert-True {
    param([bool]$Condition,[string]$Message)
    if (-not $Condition) { throw $Message }
}

function Get-RepositoryPath {
    param([string]$RelativePath)
    Join-Path $repositoryRoot ($RelativePath.Replace('/','\'))
}

function Read-RepositoryText {
    param([string]$RelativePath)
    $path = Get-RepositoryPath $RelativePath
    Assert-True (Test-Path -LiteralPath $path -PathType Leaf) "Required file '$RelativePath' is missing."
    [IO.File]::ReadAllText($path)
}

function Read-RepositoryJson {
    param([string]$RelativePath)
    (Read-RepositoryText $RelativePath) | ConvertFrom-Json
}

function Get-RepositoryHash {
    param([string]$RelativePath)
    (Get-FileHash -LiteralPath (Get-RepositoryPath $RelativePath) -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Assert-ObjectJsonEqual {
    param($Left,$Right,[string]$Message)
    $leftJson = $Left | ConvertTo-Json -Depth 50 -Compress
    $rightJson = $Right | ConvertTo-Json -Depth 50 -Compress
    Assert-True ($leftJson -eq $rightJson) $Message
}

function Test-IsGeneratedOrLocalPath {
    param([string]$RelativePath)
    $path = $RelativePath.Replace('\','/')
    if ($path -like '.git/*' -or $path -like '.vs/*' -or $path -like '.vscode/*' -or $path -like '.idea/*' -or $path -like 'out/*' -or $path -like 'src/StarCluster.Game/.godot/*' -or $path -match '(^|/)(bin|obj|TestResults)/') { return $true }
    if ($path -match '(^|/)__pycache__/' -or $path -match '\.pyc$') { return $true }
    if ($path -match '\.(user|userosscache|sln\.docstates|uid)$' -or $path -match '(^|/)\.suo$' -or $path -match '(^|/)(\.DS_Store|Thumbs\.db)$') { return $true }
    return $false
}

Write-Host '       Validating accepted CP106 provenance and frozen CP104 numerical/executable authority...'
Assert-True ((Get-RepositoryHash 'docs/validation/evidence/checkpoint-106/CHECKPOINT_106_SHA256SUMS.txt') -eq '9fcaa72a6e99c9e3707a6f1af37ede31f3856d949507f16f3ce0b4ab46731be4') 'Accepted CP106 manifest evidence hash drifted.'
$matrix = Read-RepositoryJson 'docs/archive/player_technology/pre-cp165-active/technology_architecture_matrix_v1.json'
$frozenMatrix = Read-RepositoryJson 'docs/validation/evidence/checkpoint-104/technology_architecture_matrix_v1.json'
Assert-ObjectJsonEqual -Left $matrix.tiers -Right $frozenMatrix.tiers -Message 'CP107a must not change matrix tiers.'
Assert-True (-not (Test-Path -LiteralPath (Get-RepositoryPath 'tools/calibration/checkpoints/checkpoint-107.json'))) 'CP107 must not create a calibration definition.'
Assert-True (-not (Test-Path -LiteralPath (Get-RepositoryPath 'tools/calibration/checkpoints/checkpoint-107a.json'))) 'CP107a must not create a calibration definition.'
Assert-True ((Get-RepositoryHash 'docs/archive/player_technology/pre-cp165-active/auxiliary_component_catalog_v0_1.json') -eq '3fc539ec8d851a3ba7c95777237d4533fd27c32ccc414a474f468178945856e6') 'Legacy CP43 auxiliary catalog compatibility snapshot drifted.'
Assert-True ((Get-RepositoryHash 'docs/archive/player_technology/pre-cp165-active/auxiliary_component_catalog_schema_v0_1.json') -eq 'b00205d3b9c5ba05a899cc7ced933ba8a42a5fce8241c54893de073bb46db405') 'Legacy CP43 auxiliary schema compatibility snapshot drifted.'
Assert-True ((Get-RepositoryHash 'docs/design/player_technology/Technology_Foundation_Completeness_Audit_v1.json') -eq 'b906a06c97e5096f284e2719a4e3e4618d400f1ade9f646c7853341ca428dcf4') 'Legacy CP106 foundation-audit input snapshot drifted.'

Write-Host '       Validating CP107 design-content freeze and CP107a acceptance hotfix...'
Assert-True ((Get-RepositoryHash 'docs/validation/evidence/checkpoint-107-unaccepted/CHECKPOINT_107_SHA256SUMS.txt') -eq '4e83048a7eb0b55a3cf35a66ecd569361057c96695c7e8ba8eac413b98b575a1') 'Unaccepted CP107 manifest evidence hash drifted.'
$definition = Read-RepositoryJson 'tools/checkpoints/checkpoint-107a/checkpoint_107a_architecture_definition.json'
Assert-True ([string]$definition.checkpointId -eq '107a' -and [string]$definition.acceptedBaseline -eq '106' -and [string]$definition.contentCheckpoint -eq '107') 'CP107a definition identity drifted.'
Assert-True (-not [bool]$definition.numericalTlTableChanged -and -not [bool]$definition.newTl4Tl9BalanceValuesAssigned -and -not [bool]$definition.simulationOrCalibrationRun -and [int]$definition.declaredTrials -eq 0) 'CP107a must remain architecture-only.'
Assert-True (-not [bool]$definition.hotfix.designContentChanged -and [bool]$definition.hotfix.precheckHardened) 'CP107a must remain a pure acceptance-infrastructure hotfix.'
$guardText = Read-RepositoryText 'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1'
Assert-True ($guardText.IndexOf('Assert-NoAliasCollidingFunctionNames',[StringComparison]::Ordinal) -ge 0) 'Native precheck alias-collision guard is missing.'
Assert-True ($guardText.IndexOf('FunctionDefinitionAst',[StringComparison]::Ordinal) -ge 0) 'Native precheck must inspect PowerShell function definitions through the AST.'
Assert-True ($guardText.IndexOf('Get-Alias -Name $functionName',[StringComparison]::Ordinal) -ge 0) 'Native precheck must compare function names against PowerShell aliases.'
$guardPath = Get-RepositoryPath 'tools/checkpoints/Test-NativeAcceptanceDependencies.ps1'
$selfTestDirectory = Get-RepositoryPath 'out/checkpoint-107a'
$selfTestPath = Join-Path $selfTestDirectory 'native_precheck_alias_collision_fixture.ps1'
$selfTestRelativePath = 'out/checkpoint-107a/native_precheck_alias_collision_fixture.ps1'
New-Item -ItemType Directory -Path $selfTestDirectory -Force | Out-Null
[IO.File]::WriteAllText($selfTestPath, "function H { param([string]`$Value) return `$Value }`r`n")
$aliasCollisionRejected = $false
try {
    & $guardPath -RepositoryRoot $repositoryRoot -PowerShellPaths @($selfTestRelativePath) -CheckpointDefinitionPaths @('tools/checkpoints/checkpoint-107a/checkpoint_107a_architecture_definition.json')
}
catch {
    $aliasCollisionRejected = $_.Exception.Message.IndexOf('collides case-insensitively with PowerShell alias',[StringComparison]::OrdinalIgnoreCase) -ge 0
}
finally {
    Remove-Item -LiteralPath $selfTestPath -Force -ErrorAction SilentlyContinue
}
Assert-True $aliasCollisionRejected 'Native precheck alias-collision self-test did not reject a function named H.'

$cp107ContentHashes = @{
    'docs/Star_Cluster_Game_Concept_v0.7g.docx' = '20dd862e2364c1d68c7487037941bf28cc179ac04a24862c30f002b0c4c7520a'
    'docs/archive/player_technology/pre-cp165-active/technology_component_table_v0_1.json' = '6b78ac530d63e2cb16c2627427a30d8774df9c2aa4d9ab24af56861cc09b1331'
    'docs/design/player_technology/StarCluster_Provisional_TL1_TL9_Technology_Component_Table_v0_1.xlsx' = '5b3d92eb29cb805e7aeb21e2d2fb904829b3d669a7679400757136f560250d79'
    'docs/design/player_technology/auxiliary_component_catalog_v0_2.json' = '39466faab58961d4bdf8c9b82679971c8c1995baab38efa4c8222333649ecf12'
    'docs/design/player_technology/Technology_Foundation_Completeness_Audit_v1_1.json' = 'a9440f33693c8dfc971587fcd3233e6d5bdbe7f7111bb2519f0428aeec62b066'
    'docs/design/player_technology/technology_idea_register_v1_2.json' = '326f866663a364aca95511169ece0bcd9eb3d97bf05568cf4ffce7f27d72cebc'
}
foreach ($relativePath in $cp107ContentHashes.Keys) {
    Assert-True ((Get-RepositoryHash $relativePath) -eq $cp107ContentHashes[$relativePath]) "CP107a acceptance hotfix changed frozen CP107 design content '$relativePath'."
}

Write-Host '       Validating provisional TL1-TL9 technology/component table...'
$table = Read-RepositoryJson 'docs/archive/player_technology/pre-cp165-active/technology_component_table_v0_1.json'
Assert-True ([string]$table.checkpoint -eq '107') 'Technology table must remain the unchanged CP107 architecture artifact.'
Assert-True (-not [bool]$table.contracts.balanceCalibrationRun -and -not [bool]$table.contracts.newTl4Tl9NumericalValuesAssigned -and -not [bool]$table.contracts.existingTl1Tl3NumericalValuesChanged) 'Numerical boundary drifted.'
Assert-True ([int]$table.contracts.startingShuttles -eq 1) 'Starting shuttle count must be one.'
Assert-True ([int]$table.contracts.workingTacticalFuelCapacity -eq 100 -and [int]$table.contracts.workingFuelPerTraversedHex -eq 2 -and [int]$table.contracts.workingEvasiveManeuverFuelPerTurn -eq 1) 'Fuel working scale drifted.'
Assert-True ([int]$table.contracts.ablativeArmorSpace -eq 1) 'Ablative Armor must cost one Space.'
$grid = @($table.grid)
Assert-True ($grid.Count -eq 90) 'Table must contain 10x9 grid rows.'
$entries = @($table.lineageEntries)
Assert-True ($entries.Count -eq 214) 'Table must translate exactly 214 Storyboard beats.'
$hardPrerequisiteEntries = @($entries | Where-Object { @($_.hardExternalPrerequisites).Count -gt 0 })
Assert-True ($hardPrerequisiteEntries.Count -eq 0) 'CP107 architecture must promote zero hard external prerequisites.'
$disciplineNames = @($table.standardLineages.PSObject.Properties.Name)
Assert-True ($disciplineNames.Count -eq 10) 'Table must contain 10 visible disciplines.'
foreach ($disciplineName in $disciplineNames) {
    $rows = @($grid | Where-Object { [string]$_.discipline -eq [string]$disciplineName })
    Assert-True ($rows.Count -eq 9) "Discipline '$disciplineName' must have TL1-TL9 rows."
}

Write-Host '       Validating support-component and documentation consistency...'
$auxiliaryCatalog = Read-RepositoryJson 'docs/design/player_technology/auxiliary_component_catalog_v0_2.json'
Assert-True ([bool]$auxiliaryCatalog.foundation.universalInstallationSpace -and [bool]$auxiliaryCatalog.foundation.auxiliaryIsRoleNotPool) 'Support catalog must use universal Space.'
$ablative = @($auxiliaryCatalog.components | Where-Object { [string]$_.id -eq 'ablative-armor' })
Assert-True ($ablative.Count -eq 1 -and [int]$ablative[0].space -eq 1) 'Ablative component mismatch.'
foreach ($componentId in @('medical-bay','fuel-processor','fabricator','scientific-laboratory','mining-module','cargo-expansion','hangar-mission-bay')) {
    Assert-True (@($auxiliaryCatalog.components | Where-Object { [string]$_.id -eq $componentId }).Count -eq 1) "Missing support component '$componentId'."
}
$foundationAudit = Read-RepositoryJson 'docs/design/player_technology/Technology_Foundation_Completeness_Audit_v1_1.json'
Assert-True ([string]$foundationAudit.checkpoint -eq '107' -and @($foundationAudit.domains).Count -eq 20) 'Foundation audit drifted.'
$ideaRegister = Read-RepositoryJson 'docs/design/player_technology/technology_idea_register_v1_2.json'
Assert-True ([string]$ideaRegister.checkpoint -eq '107' -and @($ideaRegister.ideas).Count -eq 136) 'Idea Register v1.2 drifted.'
$activeConcepts = @(Get-ChildItem -LiteralPath (Get-RepositoryPath 'docs') -File -Filter 'Star_Cluster_Game_Concept*.docx' | ForEach-Object Name)
Assert-True ($activeConcepts.Count -eq 1 -and $activeConcepts[0] -eq 'Star_Cluster_Game_Concept_v0.7g.docx') 'Exactly Concept v0.7g must be active.'
foreach ($relativePath in @('README.md','CHAT_README.md','docs/README.md','docs/design/player_technology/README.md','docs/design/testing/README.md','docs/validation/README.md')) {
    $text = Read-RepositoryText $relativePath
    Assert-True ($text.IndexOf('107a',[StringComparison]::OrdinalIgnoreCase) -ge 0) "Active document '$relativePath' must recognize CP107a."
}

Write-Host '       Validating full repository manifest...'
$manifestPath = Get-RepositoryPath 'CHECKPOINT_107A_SHA256SUMS.txt'
Assert-True (Test-Path -LiteralPath $manifestPath) 'CP107a manifest is missing.'
$manifestEntries = @{}
foreach ($line in Get-Content -LiteralPath $manifestPath) {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    $match = [regex]::Match([string]$line,'^([0-9a-fA-F]{64})  (.+)$')
    Assert-True $match.Success "Malformed manifest row '$line'."
    $relativePath = $match.Groups[2].Value.Replace('\','/')
    Assert-True (-not $manifestEntries.ContainsKey($relativePath)) "Manifest duplicates '$relativePath'."
    $manifestEntries[$relativePath] = $match.Groups[1].Value.ToLowerInvariant()
}
$repositoryOwnedFiles = @{}
foreach ($file in Get-ChildItem -LiteralPath $repositoryRoot -Recurse -File -Force) {
    $relativePath = $file.FullName.Substring($repositoryRoot.Length).TrimStart('\','/').Replace('\','/')
    if ($relativePath -eq 'CHECKPOINT_107A_SHA256SUMS.txt') { continue }
    if (Test-IsGeneratedOrLocalPath -RelativePath $relativePath) { continue }
    $repositoryOwnedFiles[$relativePath] = $true
}
Assert-True ($repositoryOwnedFiles.Count -eq $manifestEntries.Count) "Repository-owned file count drifted: actual $($repositoryOwnedFiles.Count), manifest $($manifestEntries.Count)."
foreach ($relativePath in $repositoryOwnedFiles.Keys) {
    Assert-True ($manifestEntries.ContainsKey($relativePath)) "Manifest missing '$relativePath'."
    Assert-True ((Get-RepositoryHash $relativePath) -eq $manifestEntries[$relativePath]) "Manifest hash mismatch for '$relativePath'."
}

Write-Host ("       CP107a contract verified: {0} repository-owned files; CP107 design content frozen; 10 disciplines / 32 source lineages / 214 beats / 136 ideas / 20 foundation domains; zero hard gates; zero trials; zero numerical TL4-TL9 values." -f $repositoryOwnedFiles.Count)
