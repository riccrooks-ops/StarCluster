[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repositoryRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
Push-Location $repositoryRoot

function Assert-FileContains {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string[]]$Patterns,
        [Parameter(Mandatory = $true)][string]$Description
    )
    if (-not (Test-Path $Path)) {
        throw "$Description file $Path was not found. Re-extract the complete Checkpoint 18 package."
    }
    foreach ($pattern in $Patterns) {
        if (-not (Select-String -Path $Path -Pattern ([regex]::Escape($pattern)) -Quiet)) {
            throw "$Description is missing required content: $pattern"
        }
    }
}

function Assert-FileNotContains {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string[]]$Patterns,
        [Parameter(Mandatory = $true)][string]$Description
    )
    if (-not (Test-Path $Path)) {
        throw "$Description file $Path was not found. Re-extract the complete Checkpoint 18 package."
    }
    foreach ($pattern in $Patterns) {
        if (Select-String -Path $Path -Pattern ([regex]::Escape($pattern)) -Quiet) {
            throw "$Description still contains forbidden content: $pattern"
        }
    }
}

function Assert-ConceptPrintLayout {
    param([Parameter(Mandatory = $true)][string]$Path)

    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $archive = [System.IO.Compression.ZipFile]::OpenRead((Resolve-Path $Path).Path)
    try {
        $entry = $archive.GetEntry('word/document.xml')
        if ($null -eq $entry) { throw "Concept document $Path has no word/document.xml entry." }
        $reader = New-Object System.IO.StreamReader($entry.Open())
        try { [xml]$documentXml = $reader.ReadToEnd() }
        finally { $reader.Dispose() }

        $wordNamespace = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
        $sectionProperties = $documentXml.GetElementsByTagName('sectPr', $wordNamespace)
        if ($sectionProperties.Count -eq 0) { throw "Concept document $Path contains no section properties." }
        $minimumPrintableWidth = [int]::MaxValue
        foreach ($section in $sectionProperties) {
            $pageSizes = $section.GetElementsByTagName('pgSz', $wordNamespace)
            $pageMargins = $section.GetElementsByTagName('pgMar', $wordNamespace)
            if ($pageSizes.Count -eq 0 -or $pageMargins.Count -eq 0) {
                throw "Concept document $Path contains a section without explicit page size and margins."
            }
            $pageSize = $pageSizes.Item(0)
            $pageMargin = $pageMargins.Item(0)
            $pageWidth = [int]$pageSize.GetAttribute('w', $wordNamespace)
            $leftMargin = [int]$pageMargin.GetAttribute('left', $wordNamespace)
            $rightMargin = [int]$pageMargin.GetAttribute('right', $wordNamespace)
            if ($leftMargin -lt 700 -or $rightMargin -lt 700) {
                throw "Concept section margins are too narrow: left=$leftMargin, right=$rightMargin twips."
            }
            $printableWidth = $pageWidth - $leftMargin - $rightMargin
            if ($printableWidth -le 0) { throw 'Concept section has a non-positive printable width.' }
            if ($printableWidth -lt $minimumPrintableWidth) { $minimumPrintableWidth = $printableWidth }
        }

        $tables = $documentXml.GetElementsByTagName('tbl', $wordNamespace)
        foreach ($table in $tables) {
            $tableGrids = $table.GetElementsByTagName('tblGrid', $wordNamespace)
            if ($tableGrids.Count -gt 0) {
                $gridColumns = $tableGrids.Item(0).GetElementsByTagName('gridCol', $wordNamespace)
                $gridWidth = 0
                foreach ($gridColumn in $gridColumns) {
                    $columnWidthText = $gridColumn.GetAttribute('w', $wordNamespace)
                    if ($columnWidthText) { $gridWidth += [int]$columnWidthText }
                }
                if ($gridWidth -gt $minimumPrintableWidth) {
                    throw "Concept contains a table grid of $gridWidth twips, wider than printable width $minimumPrintableWidth."
                }
            }
            $tableIndents = $table.GetElementsByTagName('tblInd', $wordNamespace)
            if ($tableIndents.Count -gt 0) {
                $indentText = $tableIndents.Item(0).GetAttribute('w', $wordNamespace)
                if ($indentText -and [int]$indentText -lt 0) {
                    throw "Concept contains a table with negative left indent $indentText twips."
                }
            }
        }
    }
    finally { $archive.Dispose() }
}

function Assert-ReferenceManifest {
    param(
        [Parameter(Mandatory = $true)][string]$Directory,
        [Parameter(Mandatory = $true)][string]$ManifestPath
    )
    if (-not (Test-Path $ManifestPath)) { throw "Reference manifest $ManifestPath was not found." }
    foreach ($line in Get-Content $ManifestPath) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        if ($line -notmatch '^([0-9a-fA-F]{64})\s+(.+)$') {
            throw "Malformed reference manifest line: $line"
        }
        $expectedHash = $Matches[1].ToLowerInvariant()
        $relativeName = $Matches[2]
        $referencePath = Join-Path $Directory $relativeName
        if (-not (Test-Path $referencePath)) {
            throw "Reference file $relativeName is missing from $Directory."
        }
        $actualHash = (Get-FileHash $referencePath -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actualHash -ne $expectedHash) {
            throw "Reference file $relativeName hash is $actualHash, expected $expectedHash."
        }
    }
}

try {
    Write-Host '[1/14] Verifying repository and accepted Checkpoint 17c baseline...'
    if (-not (Test-Path '.\StarCluster.sln')) {
        throw "StarCluster.sln was not found at $repositoryRoot. Extract the package into the repository root."
    }
    foreach ($priorFile in @(
        '.\docs\checkpoints\Checkpoint_17c_Presentation_Concept_Power_Repair_And_Reference_Handoff.md',
        '.\tools\checkpoints\checkpoint-17c\apply_checkpoint_17c.ps1',
        '.\src\StarCluster.Game\Scripts\Main.cs',
        '.\src\StarCluster.Game\Scripts\HexBoardView.cs',
        '.\tests\StarCluster.Tests\Combat\Missiles\MissileLocalSensorGuidanceTests.cs')) {
        if (-not (Test-Path $priorFile)) {
            throw "Required Checkpoint 17c baseline file $priorFile was not found."
        }
    }

    $expectedV03rHash = '633e0f90e31183158f1ec156965ea9beed339948f4b089c393312a9722033dc8'
    $priorRootConcept = '.\docs\Star_Cluster_Game_Concept_v0.3r.docx'
    $priorArchivedConcept = '.\docs\archive\Star_Cluster_Game_Concept_v0.3r.docx'
    if (Test-Path $priorRootConcept) { $priorConceptPath = $priorRootConcept }
    elseif (Test-Path $priorArchivedConcept) { $priorConceptPath = $priorArchivedConcept }
    else { throw 'Required accepted Concept v0.3r was not found in docs or docs\archive.' }
    $priorHash = (Get-FileHash $priorConceptPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($priorHash -ne $expectedV03rHash) {
        throw "Accepted Concept v0.3r hash is $priorHash, expected $expectedV03rHash."
    }

    Write-Host '[2/14] Confirming that Godot is closed...'
    $godotProcesses = Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -like 'Godot*' }
    if ($godotProcesses) {
        $processNames = ($godotProcesses.ProcessName | Sort-Object -Unique) -join ', '
        throw "Close the Godot editor and debug window before applying Checkpoint 18. Running process(es): $processNames"
    }

    Write-Host '[3/14] Checking the pinned .NET SDK...'
    $sdkVersion = dotnet --version
    Write-Host "       SDK: $sdkVersion"
    if ($sdkVersion -ne '8.0.423') {
        throw "Expected .NET SDK 8.0.423 from global.json, but dotnet selected $sdkVersion."
    }

    Write-Host '[4/14] Verifying separate flight and terminal state...'
    foreach ($terminalFile in @(
        '.\src\StarCluster.Core\Combat\Missiles\MissileTerminalState.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileTerminalOutcome.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileTerminalResolution.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileTerminalResolutionService.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileTerminalProfile.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileTerminalSeekerProfile.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileGuidanceComputerProfile.cs',
        '.\src\StarCluster.Core\Combat\Missiles\SeededMissileTerminalRandomSource.cs')) {
        if (-not (Test-Path $terminalFile)) {
            throw "Required Checkpoint 18 terminal file $terminalFile was not found."
        }
    }
    Assert-FileContains '.\src\StarCluster.Core\Combat\Missiles\GuidedMissileSalvo.cs' @(
        'public MissileTerminalState TerminalState',
        'public MissileTerminalResolution? LastTerminalResolution',
        'public int StationarySearchFuelSpent',
        'public int TotalFuelSpent',
        'internal bool SpendStationarySearchFuel()',
        'internal void RecordTerminalAttack') 'Checkpoint 18 missile lifetime state'
    Assert-FileNotContains '.\src\StarCluster.Core\Combat\Missiles\GuidedMissileStatus.cs' @(
        'Arrived') 'Checkpoint 18 broad missile status'

    Write-Host '[5/14] Verifying source-neutral Current/Firm terminal eligibility and seeker assistance...'
    Assert-FileContains '.\src\StarCluster.Core\Combat\Missiles\MissileTerminalResolutionService.cs' @(
        'reportSource == MissileGuidanceReportSource.FreshDatalink',
        'datalinkState == MissileDatalinkState.Live',
        'reportSource == MissileGuidanceReportSource.PeerGuidance',
        'reportSource == MissileGuidanceReportSource.LocalSensor',
        'bool seekerOnly = seekerInstalled && !onboardNavigationSensorInstalled;',
        'MissileTargetTrackQuality.Approximate',
        'seeker.TerminalEccmStrength',
        'salvo.TerminalProfile.Seeker.AccuracyBonusPercent',
        'if (roll == 1)',
        'else if (roll == 100)') 'Checkpoint 18 terminal eligibility and d100 contract'
    Assert-FileContains '.\src\StarCluster.Core\Combat\Missiles\MissileGuidanceReportSource.cs' @(
        'PeerGuidance') 'Checkpoint 18 guidance source taxonomy'

    Write-Host '[6/14] Verifying two distinct PDS terminal windows...'
    Assert-FileContains '.\src\StarCluster.Core\Combat\Missiles\MissileInterceptionOpportunity.cs' @(
        'TerminalEntry',
        'PreTerminalAttack') 'Checkpoint 18 interception opportunities'
    Assert-FileContains '.\src\StarCluster.Core\Combat\Missiles\MissileInterceptionPhaseContext.cs' @(
        '_pdsTerminalAttemptsUsed',
        '_resolvedPdsWindows',
        'if (terminalUsed >= 2)',
        'MissileInterceptionOpportunity.Transit or',
        'MissileInterceptionOpportunity.TerminalEntry or',
        'MissileInterceptionOpportunity.PreTerminalAttack') 'Checkpoint 18 layered and two-window PDS enforcement'
    foreach ($guidanceFile in @(
        '.\src\StarCluster.Core\Combat\Missiles\MissileGuidanceService.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileAutonomousGuidanceService.cs')) {
        Assert-FileContains $guidanceFile @(
            'MissileInterceptionOpportunity.TerminalEntry',
            'MissileInterceptionOpportunity.PreTerminalAttack',
            'MissileTerminalResolutionService.EvaluateAcquisition',
            'MissileTerminalResolutionService.ResolveAttack') 'Checkpoint 18 terminal sequence'
    }

    Write-Host '[7/14] Verifying search fuel, explicit outcomes, and no Arrived shortcut...'
    Assert-FileContains '.\src\StarCluster.Core\Combat\Missiles\MissileGuidanceService.cs' @(
        'ResolveStationarySearchActivation',
        'salvo.SpendStationarySearchFuel();',
        'salvo.EnterSearchWait(acquisition);') 'Checkpoint 18 compatibility search flow'
    Assert-FileContains '.\src\StarCluster.Core\Combat\Missiles\MissileAutonomousGuidanceService.cs' @(
        'salvo.SpendStationarySearchFuel();',
        'EnterSearchAtCandidate',
        'isNewArrival') 'Checkpoint 18 autonomous search flow'
    # Historical overlay extraction could leave the superseded pre-guidance
    # MissileSalvo model in an otherwise current repository. Remove those exact
    # obsolete files before semantic validation; they were replaced at
    # Checkpoint 11 and must not compile or contribute tests.
    foreach ($obsoleteMissileFile in @(
        '.\src\StarCluster.Core\Combat\Missiles\MissileAdvanceResult.cs',
        '.\src\StarCluster.Core\Combat\Missiles\MissileSalvo.cs',
        '.\tests\StarCluster.Tests\Combat\Missiles\MissileSalvoTests.cs')) {
        Remove-Item $obsoleteMissileFile -Force -ErrorAction SilentlyContinue
    }

    $sourceAndTests = Get-ChildItem '.\src', '.\tests' -Recurse -File -Filter '*.cs' |
        Where-Object { $_.FullName -notmatch '\\(bin|obj)\\' }
    $forbiddenArrival = $sourceAndTests |
        Select-String -Pattern 'GuidedMissileStatus\.Arrived|HasArrived'
    if ($forbiddenArrival) {
        $forbiddenArrival | ForEach-Object {
            Write-Host ("       {0}:{1}: {2}" -f $_.Path, $_.LineNumber, $_.Line.Trim())
        }
        throw 'Checkpoint 18 canonical source/tests still contain the old Arrived-as-impact shortcut.'
    }

    Write-Host '[8/14] Verifying Godot terminal integration and observer-safe presentation...'
    Assert-FileContains '.\src\StarCluster.Game\Scripts\Main.cs' @(
        'private const string CheckpointVersion = "checkpoint-18";',
        'new SeededMissileTerminalRandomSource(1801)',
        'Standard PDS may fire once on terminal entry and once immediately before a surviving Missile Flight attacks.',
        'MissileTerminalOutcome.CriticalHit',
        'GuidedMissileStatus.Searching',
        'MissileTerminalAcquisitionResolved',
        'MissileTerminalAttackResolved',
        'MissileSelfDestructed') 'Checkpoint 18 Godot integration'
    Assert-FileContains '.\src\StarCluster.Game\Scripts\HexBoardView.cs' @(
        'GuidedMissileStatus.Searching',
        'DrawSymbol(center, "?"') 'Checkpoint 18 tactical missile marker presentation'

    Write-Host '[9/14] Verifying the new engine-independent terminal test matrix...'
    $terminalTestPath = '.\tests\StarCluster.Tests\Combat\Missiles\MissileTerminalResolutionTests.cs'
    if (-not (Test-Path $terminalTestPath)) {
        throw "Required Checkpoint 18 terminal test file $terminalTestPath was not found."
    }
    $terminalFactCount = (Select-String -Path $terminalTestPath -Pattern '^\s*\[Fact\]\s*$').Count
    if ($terminalFactCount -ne 22) {
        throw "Expected 22 Checkpoint 18 terminal tests, found $terminalFactCount."
    }
    Assert-FileContains $terminalTestPath @(
        'CommandGuidedMissileAcceptsLiveFirmDatalink',
        'SensorEquippedMissileMayUseOwnCurrentFirmReport',
        'PeerGuidanceCanSupplyCurrentFirmTerminalReport',
        'PdsReceivesTerminalEntryAndPreAttackOpportunities',
        'FailedArrivalAcquisitionDoesNotSpendStationarySearchFuel',
        'LaterStationarySearchConsumesOneFuelAndCanAttackImmediately',
        'FailedTerminalOpportunityWithNoFuelSelfDestructsSafely') 'Checkpoint 18 terminal test matrix'

    Write-Host '[10/14] Verifying synchronized Checkpoint 18 documentation...'
    foreach ($documentationFile in @(
        '.\docs\README.md',
        '.\docs\Prototype_TODO.md',
        '.\docs\checkpoints\Checkpoint_18_Unified_Missile_Terminal_Solutions_Search_And_Seeker_Assistance.md',
        '.\docs\validation\Checkpoint_18_Unified_Missile_Terminal_Solutions_Search_And_Seeker_Assistance.md',
        '.\docs\validation\archive\Checkpoint_17c_Presentation_Concept_And_Reference_Handoff.md',
        '.\docs\design\Missile_Guidance_Datalink_Sensor_And_Seeker_Architecture.md',
        '.\src\StarCluster.Game\README.md')) {
        if (-not (Test-Path $documentationFile)) {
            throw "Required Checkpoint 18 documentation file $documentationFile was not found."
        }
    }
    # Extraction overlays do not delete superseded current artifacts. Remove the
    # accepted 17c root copy/runbook now that their archived copies are verified.
    Remove-Item '.\docs\Star_Cluster_Game_Concept_v0.3r.docx' -Force -ErrorAction SilentlyContinue
    Remove-Item '.\docs\validation\Checkpoint_17c_Presentation_Concept_And_Reference_Handoff.md' -Force -ErrorAction SilentlyContinue

    $activeValidationFiles = @(Get-ChildItem '.\docs\validation' -File -Filter '*.md')
    if ($activeValidationFiles.Count -ne 1 -or
        $activeValidationFiles[0].Name -ne 'Checkpoint_18_Unified_Missile_Terminal_Solutions_Search_And_Seeker_Assistance.md') {
        throw 'Checkpoint 18 must leave exactly one active validation runbook.'
    }
    Assert-FileContains '.\docs\validation\Checkpoint_18_Unified_Missile_Terminal_Solutions_Search_And_Seeker_Assistance.md' @(
        'Two distinct PDS windows',
        'Search/Wait',
        '493/493') 'Checkpoint 18 active validation runbook'

    Write-Host '[11/14] Verifying Concept v0.3s, title repair, and archive continuity...'
    foreach ($conceptFile in @(
        '.\docs\Star_Cluster_Game_Concept_v0.3s.docx',
        '.\docs\archive\Star_Cluster_Game_Concept_v0.3r.docx')) {
        if (-not (Test-Path $conceptFile)) { throw "Required Concept file $conceptFile was not found." }
    }
    $archivedHash = (Get-FileHash '.\docs\archive\Star_Cluster_Game_Concept_v0.3r.docx' -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($archivedHash -ne $expectedV03rHash) {
        throw "Archived Concept v0.3r hash is $archivedHash, expected $expectedV03rHash."
    }
    $expectedV03sHash = '2cf4b68eff1d2ac1a1d532de5e216e3432cc64f6494f2435230b4f86b1c86ea4'
    $currentHash = (Get-FileHash '.\docs\Star_Cluster_Game_Concept_v0.3s.docx' -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($currentHash -ne $expectedV03sHash) {
        throw "Concept v0.3s hash is $currentHash, expected $expectedV03sHash. Re-extract the complete Checkpoint 18 package."
    }
    Assert-ConceptPrintLayout '.\docs\Star_Cluster_Game_Concept_v0.3s.docx'
    Assert-FileContains '.\docs\README.md' @(
        'Star_Cluster_Game_Concept_v0.3s.docx',
        'Checkpoint_18_Unified_Missile_Terminal_Solutions_Search_And_Seeker_Assistance.md') 'Documentation index'

    Write-Host '[12/14] Verifying the unchanged packaged reference library...'
    $expectedReferenceManifestHash = '070ced666ad12a448d6767769ac4ff6e38379ecb5d182dae7ce83f9bad786db4'
    $referenceManifestHash = (Get-FileHash '.\docs\references\SHA256SUMS.txt' -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($referenceManifestHash -ne $expectedReferenceManifestHash) {
        throw "Reference manifest hash is $referenceManifestHash, expected $expectedReferenceManifestHash."
    }
    Assert-ReferenceManifest '.\docs\references' '.\docs\references\SHA256SUMS.txt'
    $referenceCount = (Get-ChildItem '.\docs\references' -File | Where-Object { $_.Name -notin @('README.md', 'SHA256SUMS.txt') }).Count
    if ($referenceCount -ne 12) {
        throw "Expected 12 packaged external reference files, found $referenceCount."
    }

    Write-Host '[13/14] Refreshing Godot metadata, building, and running 493 tests...'
    Remove-Item -Recurse -Force '.\src\StarCluster.Game\.godot\mono' -ErrorAction SilentlyContinue
    $solutionOutput = dotnet sln '.\StarCluster.sln' list
    if ($LASTEXITCODE -ne 0) { throw "dotnet sln list failed with exit code $LASTEXITCODE." }
    $solutionText = $solutionOutput | Out-String
    if ($solutionText -notmatch 'StarCluster.Game.csproj') {
        dotnet sln '.\StarCluster.sln' add '.\src\StarCluster.Game\StarCluster.Game.csproj'
        if ($LASTEXITCODE -ne 0) { throw "Could not add StarCluster.Game to the solution; exit code $LASTEXITCODE." }
    }

    dotnet build '.\StarCluster.sln' --nologo -warnaserror
    if ($LASTEXITCODE -ne 0) { throw "dotnet build failed with exit code $LASTEXITCODE." }

    $testOutput = dotnet test '.\tests\StarCluster.Tests\StarCluster.Tests.csproj' --no-build --nologo
    $testOutput | Write-Host
    if ($LASTEXITCODE -ne 0) { throw "dotnet test failed with exit code $LASTEXITCODE." }
    $testText = $testOutput | Out-String
    if ($testText -notmatch 'Passed:\s+493') { throw 'The complete suite did not report the expected 493 passed tests.' }
    if (Select-String -Path '.\src\StarCluster.Core\StarCluster.Core.csproj' -Pattern 'Godot' -Quiet) {
        throw 'StarCluster.Core unexpectedly contains a Godot dependency.'
    }

    Write-Host '[14/14] Removing superseded current-root and active-validation artifacts...'
    foreach ($obsoleteFile in @(
        '.\docs\Star_Cluster_Game_Concept_v0.3r.docx',
        '.\docs\validation\Checkpoint_17c_Presentation_Concept_And_Reference_Handoff.md')) {
        Remove-Item $obsoleteFile -Force -ErrorAction SilentlyContinue
    }

    Write-Host ''
    Write-Host 'Checkpoint 18 completed successfully.'
    Write-Host 'Expected engine-independent tests passed: 493.'
    Write-Host 'Concept v0.3s is current; exact v0.3r is archived.'
    Write-Host 'Reopen Godot and run docs\validation\Checkpoint_18_Unified_Missile_Terminal_Solutions_Search_And_Seeker_Assistance.md.'
    Write-Host 'Preserve the matching checkpoint-18 logs and requested screenshots.'
}
finally {
    Pop-Location
}
