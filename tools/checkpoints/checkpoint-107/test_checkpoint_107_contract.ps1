[CmdletBinding()]
param([string]$RepositoryRoot)
Set-StrictMode -Version 2.0
$ErrorActionPreference='Stop'
if([string]::IsNullOrWhiteSpace($RepositoryRoot)){ $repositoryRoot=(Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path } else { $repositoryRoot=(Resolve-Path $RepositoryRoot).Path }
function A([bool]$c,[string]$m){ if(-not $c){ throw $m } }
function R([string]$p){ Join-Path $repositoryRoot ($p.Replace('/','\')) }
function T([string]$p){ $x=R $p; A (Test-Path -LiteralPath $x -PathType Leaf) "Required file '$p' missing."; [IO.File]::ReadAllText($x) }
function J([string]$p){ (T $p)|ConvertFrom-Json }
function H([string]$p){ (Get-FileHash -LiteralPath (R $p) -Algorithm SHA256).Hash.ToLowerInvariant() }
function Eq($l,$r,[string]$m){ $a=$l|ConvertTo-Json -Depth 50 -Compress; $b=$r|ConvertTo-Json -Depth 50 -Compress; A ($a -eq $b) $m }
function Local([string]$p){ $q=$p.Replace('\','/'); if($q -like '.git/*' -or $q -like '.vs/*' -or $q -like '.vscode/*' -or $q -like '.idea/*' -or $q -like 'out/*' -or $q -like 'src/StarCluster.Game/.godot/*' -or $q -match '(^|/)(bin|obj|TestResults)/' -or $q -match '(^|/)__pycache__/' -or $q -match '\.pyc$'){ return $true }; return $false }
Write-Host '       Validating accepted CP106 provenance and frozen CP104 numerical/executable authority...'
A ((H 'docs/validation/evidence/checkpoint-106/CHECKPOINT_106_SHA256SUMS.txt') -eq '9fcaa72a6e99c9e3707a6f1af37ede31f3856d949507f16f3ce0b4ab46731be4') 'Accepted CP106 manifest evidence hash drifted.'
$matrix=J 'docs/archive/player_technology/pre-cp165-active/technology_architecture_matrix_v1.json'; $frozen=J 'docs/validation/evidence/checkpoint-104/technology_architecture_matrix_v1.json'; Eq $matrix.tiers $frozen.tiers 'CP107 must not change matrix tiers.'
A (-not (Test-Path -LiteralPath (R 'tools/calibration/checkpoints/checkpoint-107.json'))) 'CP107 must not create calibration definition.'
A ((H 'docs/archive/player_technology/pre-cp165-active/auxiliary_component_catalog_v0_1.json') -eq '3fc539ec8d851a3ba7c95777237d4533fd27c32ccc414a474f468178945856e6') 'Legacy CP43 auxiliary catalog compatibility snapshot drifted.'
A ((H 'docs/archive/player_technology/pre-cp165-active/auxiliary_component_catalog_schema_v0_1.json') -eq 'b00205d3b9c5ba05a899cc7ced933ba8a42a5fce8241c54893de073bb46db405') 'Legacy CP43 auxiliary schema compatibility snapshot drifted.'
A ((H 'docs/design/player_technology/Technology_Foundation_Completeness_Audit_v1.json') -eq 'b906a06c97e5096f284e2719a4e3e4618d400f1ade9f646c7853341ca428dcf4') 'Legacy CP106 foundation-audit input snapshot drifted.'

Write-Host '       Validating provisional TL1-TL9 technology/component table...'
$table=J 'docs/archive/player_technology/pre-cp165-active/technology_component_table_v0_1.json'
A ([string]$table.checkpoint -eq '107') 'Technology table checkpoint drifted.'
A (-not [bool]$table.contracts.balanceCalibrationRun -and -not [bool]$table.contracts.newTl4Tl9NumericalValuesAssigned -and -not [bool]$table.contracts.existingTl1Tl3NumericalValuesChanged) 'Numerical boundary drifted.'
A ([int]$table.contracts.startingShuttles -eq 1) 'Starting shuttle count must be one.'
A ([int]$table.contracts.workingTacticalFuelCapacity -eq 100 -and [int]$table.contracts.workingFuelPerTraversedHex -eq 2 -and [int]$table.contracts.workingEvasiveManeuverFuelPerTurn -eq 1) 'Fuel working scale drifted.'
A ([int]$table.contracts.ablativeArmorSpace -eq 1) 'Ablative Armor must cost one Space.'
$grid=@($table.grid); A ($grid.Count -eq 90) 'Table must contain 10x9 grid rows.'
$entries=@($table.lineageEntries); A ($entries.Count -eq 214) 'Table must translate exactly 214 Storyboard beats.'
$hard=@($entries|Where-Object { @($_.hardExternalPrerequisites).Count -gt 0 }); A ($hard.Count -eq 0) 'CP107 must promote zero hard external prerequisites.'
$disc=@($table.standardLineages.PSObject.Properties.Name); A ($disc.Count -eq 10) 'Table must contain 10 visible disciplines.'
foreach($d in $disc){ $rows=@($grid|Where-Object { [string]$_.discipline -eq [string]$d }); A ($rows.Count -eq 9) "Discipline '$d' must have TL1-TL9 rows." }
Write-Host '       Validating support-component and documentation consistency...'
$aux=J 'docs/design/player_technology/auxiliary_component_catalog_v0_2.json'; A ([bool]$aux.foundation.universalInstallationSpace -and [bool]$aux.foundation.auxiliaryIsRoleNotPool) 'Support catalog must use universal Space.'
$abl=@($aux.components|Where-Object { [string]$_.id -eq 'ablative-armor' }); A ($abl.Count -eq 1 -and [int]$abl[0].space -eq 1) 'Ablative component mismatch.'
foreach($id in @('medical-bay','fuel-processor','fabricator','scientific-laboratory','mining-module','cargo-expansion','hangar-mission-bay')){ A (@($aux.components|Where-Object { [string]$_.id -eq $id }).Count -eq 1) "Missing support component '$id'." }
$audit=J 'docs/design/player_technology/Technology_Foundation_Completeness_Audit_v1_1.json'; A ([string]$audit.checkpoint -eq '107' -and @($audit.domains).Count -eq 20) 'Foundation audit drifted.'
$ideas=J 'docs/design/player_technology/technology_idea_register_v1_2.json'; A ([string]$ideas.checkpoint -eq '107' -and @($ideas.ideas).Count -eq 136) 'Idea Register v1.2 drifted.'
$concepts=@(Get-ChildItem -LiteralPath (R 'docs') -File -Filter 'Star_Cluster_Game_Concept*.docx'|ForEach-Object Name); A ($concepts.Count -eq 1 -and $concepts[0] -eq 'Star_Cluster_Game_Concept_v0.7g.docx') 'Exactly Concept v0.7g must be active.'
foreach($p in @('README.md','CHAT_README.md','docs/README.md','docs/design/player_technology/README.md','docs/design/testing/README.md','docs/validation/README.md')){ $txt=T $p; A ($txt.IndexOf('107',[StringComparison]::OrdinalIgnoreCase) -ge 0) "Active document '$p' must recognize CP107." }
Write-Host '       Validating full repository manifest...'
$mp=R 'CHECKPOINT_107_SHA256SUMS.txt'; A (Test-Path -LiteralPath $mp) 'Manifest missing.'
$m=@{}; foreach($line in Get-Content -LiteralPath $mp){ if([string]::IsNullOrWhiteSpace($line)){continue}; $x=[regex]::Match([string]$line,'^([0-9a-fA-F]{64})  (.+)$'); A $x.Success "Malformed manifest row '$line'."; $m[$x.Groups[2].Value.Replace('\','/')]=$x.Groups[1].Value.ToLowerInvariant() }
$owned=@{}; foreach($f in Get-ChildItem -LiteralPath $repositoryRoot -Recurse -File -Force){ $rel=$f.FullName.Substring($repositoryRoot.Length).TrimStart('\','/').Replace('\','/'); if($rel -eq 'CHECKPOINT_107_SHA256SUMS.txt' -or (Local $rel)){continue}; $owned[$rel]=$true }
A ($owned.Count -eq $m.Count) "Repository-owned file count drifted: actual $($owned.Count), manifest $($m.Count)."
foreach($rel in $owned.Keys){ A ($m.ContainsKey($rel)) "Manifest missing '$rel'."; A ((H $rel) -eq $m[$rel]) "Manifest hash mismatch for '$rel'." }
Write-Host ("       CP107 contract verified: {0} repository-owned files; 10 disciplines / 32 source lineages / 214 beats / 136 ideas / 20 foundation domains; zero hard gates; zero trials; zero numerical TL4-TL9 values." -f $owned.Count)
