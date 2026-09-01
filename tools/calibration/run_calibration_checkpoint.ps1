[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$CheckpointDefinition,
    [int]$Trials = 0,
    [int]$Jobs = 0,
    [switch]$RepositoryOnly,
    [switch]$NoClean
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

function Get-RepositoryRoot {
    return (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
}

function Get-NormalizedRelativePath {
    param(
        [Parameter(Mandatory = $true)][string]$BasePath,
        [Parameter(Mandatory = $true)][string]$FullPath
    )

    $baseFullPath = [System.IO.Path]::GetFullPath($BasePath)
    $separator = [System.IO.Path]::DirectorySeparatorChar.ToString()
    $alternate = [System.IO.Path]::AltDirectorySeparatorChar.ToString()
    if (-not $baseFullPath.EndsWith($separator) -and -not $baseFullPath.EndsWith($alternate)) {
        $baseFullPath += $separator
    }

    $targetFullPath = [System.IO.Path]::GetFullPath($FullPath)
    if (-not $targetFullPath.StartsWith($baseFullPath, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Path $targetFullPath is outside repository root $baseFullPath."
    }

    return $targetFullPath.Substring($baseFullPath.Length).Replace('\', '/')
}

function Resolve-RepositoryPath {
    param(
        [Parameter(Mandatory = $true)][string]$RepositoryRoot,
        [Parameter(Mandatory = $true)][string]$RelativePath
    )

    if ([System.IO.Path]::IsPathRooted($RelativePath)) {
        $candidate = [System.IO.Path]::GetFullPath($RelativePath)
    }
    else {
        $candidate = [System.IO.Path]::GetFullPath((Join-Path $RepositoryRoot $RelativePath))
    }

    [void](Get-NormalizedRelativePath -BasePath $RepositoryRoot -FullPath $candidate)
    return $candidate
}

function Test-IsGeneratedOrLocalPath {
    param([Parameter(Mandatory = $true)][string]$RelativePath)

    $path = $RelativePath.Replace('\', '/')
    if ($path -like '.git/*' -or
        $path -like '.vs/*' -or
        $path -like '.vscode/*' -or
        $path -like '.idea/*' -or
        $path -like 'out/*' -or
        $path -like 'src/StarCluster.Game/.godot/*' -or
        $path -match '(^|/)(bin|obj|TestResults)/') {
        return $true
    }

    if ($path -match '(^|/)__pycache__/' -or $path -match '\.pyc$') {
        return $true
    }

    if ($path -match '\.(user|userosscache|sln\.docstates|uid)$' -or
        $path -match '(^|/)\.suo$' -or
        $path -match '(^|/)(\.DS_Store|Thumbs\.db)$') {
        return $true
    }

    return $false
}

function Test-RepositoryManifest {
    param(
        [Parameter(Mandatory = $true)][string]$RepositoryRoot,
        [Parameter(Mandatory = $true)][string]$ManifestRelativePath
    )

    $manifestPath = Resolve-RepositoryPath -RepositoryRoot $RepositoryRoot -RelativePath $ManifestRelativePath
    if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
        throw "Repository manifest $ManifestRelativePath was not found."
    }

    $manifestName = [System.IO.Path]::GetFileName($manifestPath)
    $entries = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
    $verified = 0
    foreach ($line in Get-Content -LiteralPath $manifestPath) {
        if ([string]::IsNullOrWhiteSpace($line) -or $line.StartsWith('#')) { continue }
        $match = [regex]::Match($line, '^([0-9a-fA-F]{64})  (.+)$')
        if (-not $match.Success) { throw "Malformed repository manifest line: $line" }
        $expectedHash = $match.Groups[1].Value.ToLowerInvariant()
        $relativePath = $match.Groups[2].Value.Replace('\', '/')
        if ([System.IO.Path]::IsPathRooted($relativePath) -or $relativePath.Split('/') -contains '..') {
            throw "Unsafe repository manifest path: $relativePath"
        }
        if ($relativePath.Equals($manifestName, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw 'The repository manifest must not contain itself.'
        }
        if (-not $entries.Add($relativePath)) { throw "Duplicate repository manifest path: $relativePath" }

        $filePath = Resolve-RepositoryPath -RepositoryRoot $RepositoryRoot -RelativePath $relativePath
        if (-not (Test-Path -LiteralPath $filePath -PathType Leaf)) { throw "Manifest file $relativePath was not found." }
        $actualHash = (Get-FileHash -LiteralPath $filePath -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actualHash -ne $expectedHash) { throw "Manifest hash mismatch for ${relativePath}: $actualHash expected $expectedHash." }
        $verified++
    }

    if ($verified -eq 0) { throw 'Repository manifest contains no file entries.' }

    $manifestFullPath = [System.IO.Path]::GetFullPath($manifestPath)
    $unexpected = @()
    $ignored = 0
    foreach ($file in Get-ChildItem -LiteralPath $RepositoryRoot -File -Recurse -Force) {
        if ([System.IO.Path]::GetFullPath($file.FullName) -eq $manifestFullPath) { continue }
        $relative = Get-NormalizedRelativePath -BasePath $RepositoryRoot -FullPath $file.FullName
        if ($entries.Contains($relative)) { continue }
        if (Test-IsGeneratedOrLocalPath -RelativePath $relative) { $ignored++; continue }
        $unexpected += $relative
    }

    if ($unexpected.Count -gt 0) {
        throw ("Repository contains files not locked by the manifest:`n{0}" -f (($unexpected | Sort-Object) -join "`n"))
    }

    Write-Host "       Repository manifest: $verified files hash-verified; no unexpected repository-owned files."
    if ($ignored -gt 0) { Write-Host "       Ignored local/generated artifacts: $ignored." }
}

function Test-PowerShellSyntax {
    param([Parameter(Mandatory = $true)][string]$RepositoryRoot)

    $failures = @()
    $count = 0
    foreach ($script in Get-ChildItem -LiteralPath $RepositoryRoot -Filter '*.ps1' -File -Recurse) {
        $tokens = $null
        $errors = $null
        [void][System.Management.Automation.Language.Parser]::ParseFile($script.FullName, [ref]$tokens, [ref]$errors)
        $count++
        foreach ($parseError in @($errors | Where-Object { $null -ne $_ })) {
            $relative = Get-NormalizedRelativePath -BasePath $RepositoryRoot -FullPath $script.FullName
            $failures += ("{0}:{1}:{2}: {3}" -f $relative, $parseError.Extent.StartLineNumber, $parseError.Extent.StartColumnNumber, $parseError.Message)
        }
    }
    if ($failures.Count -gt 0) { throw ("PowerShell parser rejected repository scripts:`n{0}" -f ($failures -join "`n")) }
    Write-Host "       PowerShell syntax: $count scripts parsed successfully."
}

function Test-DefinitionProperty {
    param(
        [Parameter(Mandatory = $true)]$Definition,
        [Parameter(Mandatory = $true)][string]$Name
    )

    $property = $Definition.PSObject.Properties[$Name]
    return ($null -ne $property -and $null -ne $property.Value)
}

function Read-CheckpointDefinition {
    param(
        [Parameter(Mandatory = $true)][string]$RepositoryRoot,
        [Parameter(Mandatory = $true)][string]$DefinitionPath
    )

    $resolved = Resolve-RepositoryPath -RepositoryRoot $RepositoryRoot -RelativePath $DefinitionPath
    if (-not (Test-Path -LiteralPath $resolved -PathType Leaf)) { throw "Checkpoint definition $DefinitionPath was not found." }
    $definition = Get-Content -LiteralPath $resolved -Raw | ConvertFrom-Json

    foreach ($property in @('schemaVersion', 'checkpointId', 'title', 'sdkVersion', 'configuration', 'calibrationSolution', 'testProject', 'runnerProject', 'manifestFile', 'outputRoot', 'defaultTrials', 'defaultJobs', 'stages')) {
        if (-not (Test-DefinitionProperty -Definition $definition -Name $property)) {
            throw "Checkpoint definition is missing required property $property."
        }
    }

    if ([int]$definition.schemaVersion -ne 1) { throw "Unsupported checkpoint-definition schema version $($definition.schemaVersion)." }
    foreach ($property in @('checkpointId', 'title', 'sdkVersion', 'configuration', 'calibrationSolution', 'testProject', 'runnerProject', 'manifestFile', 'outputRoot')) {
        if ([string]::IsNullOrWhiteSpace([string]$definition.$property)) { throw "Checkpoint definition property $property must not be empty." }
    }
    if ([int]$definition.defaultTrials -lt 1) { throw 'Checkpoint defaultTrials must be positive.' }
    if ([int]$definition.defaultJobs -lt 1) { throw 'Checkpoint defaultJobs must be positive.' }

    foreach ($relative in @($definition.calibrationSolution, $definition.testProject, $definition.runnerProject, $definition.manifestFile)) {
        $path = Resolve-RepositoryPath -RepositoryRoot $RepositoryRoot -RelativePath ([string]$relative)
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Checkpoint definition references missing file $relative." }
    }

    $outputPath = Resolve-RepositoryPath -RepositoryRoot $RepositoryRoot -RelativePath ([string]$definition.outputRoot)
    if (Test-Path -LiteralPath $outputPath -PathType Leaf) { throw "Checkpoint outputRoot points to a file: $($definition.outputRoot)." }

    $stageIds = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
    $stages = @($definition.stages)
    if ($stages.Count -eq 0) { throw 'Checkpoint definition must contain at least one runner stage.' }
    foreach ($stage in $stages) {
        foreach ($property in @('id', 'name', 'command', 'arguments')) {
            if (-not (Test-DefinitionProperty -Definition $stage -Name $property)) {
                throw "Every runner stage requires $property."
            }
        }
        if ([string]::IsNullOrWhiteSpace([string]$stage.id) -or [string]::IsNullOrWhiteSpace([string]$stage.name) -or [string]::IsNullOrWhiteSpace([string]$stage.command)) {
            throw 'Runner stage id, name, and command must not be empty.'
        }
        if (-not $stageIds.Add([string]$stage.id)) { throw "Duplicate runner stage id $($stage.id)." }
        foreach ($argument in @($stage.arguments)) {
            if ($null -eq $argument) { throw "Runner stage $($stage.id) contains a null argument." }
        }
    }

    Write-Host "       Checkpoint definition: $($definition.checkpointId) - $($definition.title); $($stages.Count) runner stages."
    return $definition
}

function Invoke-RequiredNativeDependencyPrecheck {
    param(
        [Parameter(Mandatory = $true)][string]$RepositoryRoot,
        [Parameter(Mandatory = $true)]$Definition,
        [Parameter(Mandatory = $true)][string]$DefinitionPath
    )

    $match = [regex]::Match([string]$Definition.checkpointId, '^(\d+)')
    if (-not $match.Success) { return }
    $checkpointNumber = [int]$match.Groups[1].Value
    if ($checkpointNumber -lt 66) { return }

    if (-not (Test-DefinitionProperty -Definition $Definition -Name 'nativeDependencyPrecheck')) {
        throw "Checkpoint $($Definition.checkpointId) requires nativeDependencyPrecheck metadata."
    }
    $precheck = $Definition.nativeDependencyPrecheck
    foreach ($property in @('required', 'script', 'powerShellPaths', 'checkpointDefinitionPaths')) {
        if (-not (Test-DefinitionProperty -Definition $precheck -Name $property)) {
            throw "Checkpoint $($Definition.checkpointId) nativeDependencyPrecheck is missing $property."
        }
    }
    if (-not [bool]$precheck.required) {
        throw "Checkpoint $($Definition.checkpointId) nativeDependencyPrecheck must be required."
    }

    $scriptRelative = [string]$precheck.script
    $scriptPath = Resolve-RepositoryPath -RepositoryRoot $RepositoryRoot -RelativePath $scriptRelative
    if (-not (Test-Path -LiteralPath $scriptPath -PathType Leaf)) {
        throw "Native dependency precheck script was not found: $scriptRelative"
    }

    $powerShellPaths = @($precheck.powerShellPaths | ForEach-Object { [string]$_ })
    $definitionPaths = @($precheck.checkpointDefinitionPaths | ForEach-Object { [string]$_ })
    if ($powerShellPaths.Count -eq 0 -or $definitionPaths.Count -eq 0) {
        throw "Checkpoint $($Definition.checkpointId) nativeDependencyPrecheck paths must not be empty."
    }

    $resolvedDefinitionPath = Resolve-RepositoryPath -RepositoryRoot $RepositoryRoot -RelativePath $DefinitionPath
    $activeDefinitionRelative = Get-NormalizedRelativePath -BasePath $RepositoryRoot -FullPath $resolvedDefinitionPath
    $normalizedDefinitionPaths = @($definitionPaths | ForEach-Object { $_.Replace('\', '/') })
    if (-not ($normalizedDefinitionPaths -contains $activeDefinitionRelative)) {
        throw "Checkpoint $($Definition.checkpointId) native dependency precheck must inspect its active definition $activeDefinitionRelative."
    }

    $allowedInterpreters = @()
    if (Test-DefinitionProperty -Definition $precheck -Name 'allowedInterpreters') {
        $allowedInterpreters = @($precheck.allowedInterpreters | ForEach-Object { [string]$_ })
    }

    & $scriptPath -RepositoryRoot $RepositoryRoot -PowerShellPaths $powerShellPaths -CheckpointDefinitionPaths $definitionPaths -AllowedInterpreters $allowedInterpreters
}

function Show-DocumentationStatus {
    param(
        [Parameter(Mandatory = $true)][string]$RepositoryRoot,
        [Parameter(Mandatory = $true)]$Definition
    )

    $documentationProperty = $Definition.PSObject.Properties['documentation']
    $documents = if ($null -eq $documentationProperty) { @() } else { @($documentationProperty.Value) }
    if ($documents.Count -eq 0) {
        Write-Host '       Documentation status: no documentation files declared.'
        return
    }

    $missing = @()
    foreach ($relative in $documents) {
        try {
            $path = Resolve-RepositoryPath -RepositoryRoot $RepositoryRoot -RelativePath ([string]$relative)
            if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { $missing += [string]$relative }
        }
        catch {
            $missing += [string]$relative
        }
    }

    if ($missing.Count -gt 0) {
        Write-Warning ("Documentation files are missing or invalid, but calibration will continue:`n{0}" -f ($missing -join "`n"))
    }
    else {
        Write-Host "       Documentation status: $($documents.Count) declared files present (non-blocking)."
    }
}

function Resolve-DotNetExecutable {
    $command = Get-Command -Name 'dotnet' -CommandType Application -ErrorAction Stop | Select-Object -First 1
    if ($null -eq $command -or [string]::IsNullOrWhiteSpace([string]$command.Path)) {
        throw 'A working dotnet executable was not found.'
    }
    return [string]$command.Path
}

function Invoke-NativeCommand {
    param(
        [Parameter(Mandatory = $true)][string]$Executable,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][string]$Description
    )

    $exitCode = -1
    $previousPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        & $Executable @Arguments
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousPreference
    }
    if ($exitCode -ne 0) { throw "$Description failed with exit code $exitCode." }
}

function Get-DotNetSdkVersion {
    param([Parameter(Mandatory = $true)][string]$DotNetPath)

    $exitCode = -1
    $output = @()
    $previousPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $output = @(& $DotNetPath --version 2>&1)
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousPreference
    }

    if ($exitCode -ne 0) { throw "dotnet --version failed with exit code $exitCode." }
    $version = (($output | ForEach-Object { [string]$_ }) -join "`n").Trim()
    if ([string]::IsNullOrWhiteSpace($version)) { throw 'dotnet --version returned no version.' }
    return $version
}

function Expand-CheckpointArgument {
    param(
        [Parameter(Mandatory = $true)][string]$Value,
        [Parameter(Mandatory = $true)][string]$OutputRoot,
        [Parameter(Mandatory = $true)][int]$Trials,
        [Parameter(Mandatory = $true)][int]$Jobs
    )

    return $Value.Replace('{OutputRoot}', $OutputRoot).Replace('{Trials}', [string]$Trials).Replace('{Jobs}', [string]$Jobs)
}

function Invoke-RunnerStage {
    param(
        [Parameter(Mandatory = $true)][string]$DotNetPath,
        [Parameter(Mandatory = $true)][string]$RunnerProject,
        [Parameter(Mandatory = $true)][string]$Configuration,
        [Parameter(Mandatory = $true)]$Stage,
        [Parameter(Mandatory = $true)][string]$OutputRoot,
        [Parameter(Mandatory = $true)][int]$Trials,
        [Parameter(Mandatory = $true)][int]$Jobs
    )

    $expandedArguments = @()
    foreach ($argument in @($Stage.arguments)) {
        $expandedArguments += Expand-CheckpointArgument -Value ([string]$argument) -OutputRoot $OutputRoot -Trials $Trials -Jobs $Jobs
    }

    $executor = 'dotnet-runner'
    if ((Test-DefinitionProperty -Definition $Stage -Name 'executor') -and -not [string]::IsNullOrWhiteSpace([string]$Stage.executor)) {
        $executor = [string]$Stage.executor
    }

    if ($executor -eq 'dotnet-runner') {
        $runnerArguments = @('run', '--project', $RunnerProject, '--configuration', $Configuration, '--no-build', '--', [string]$Stage.command)
        $runnerArguments += $expandedArguments
        Invoke-NativeCommand -Executable $DotNetPath -Arguments $runnerArguments -Description ([string]$Stage.name)
        return
    }

    if ($executor -eq 'powershell-script') {
        if (-not (Test-DefinitionProperty -Definition $Stage -Name 'script')) { throw "Runner stage $($Stage.id) uses powershell-script but declares no script." }
        $scriptPath = Resolve-RepositoryPath -RepositoryRoot (Get-RepositoryRoot) -RelativePath ([string]$Stage.script)
        if (-not (Test-Path -LiteralPath $scriptPath -PathType Leaf)) { throw "Runner stage script was not found: $($Stage.script)" }
        & $scriptPath -Command ([string]$Stage.command) -Arguments $expandedArguments
        return
    }

    throw "Runner stage $($Stage.id) declares unsupported executor '$executor'."
}


function New-AcceptanceSummary {
    param(
        [Parameter(Mandatory = $true)]$Definition,
        [Parameter(Mandatory = $true)][string]$RepositoryRoot,
        [Parameter(Mandatory = $true)][string]$OutputRootPath,
        [Parameter(Mandatory = $true)][string]$DefinitionRelativePath,
        [Parameter(Mandatory = $true)][int]$Trials,
        [Parameter(Mandatory = $true)][int]$Jobs,
        [Parameter(Mandatory = $true)][bool]$RepositoryOnlyMode
    )

    $manifestPath = Resolve-RepositoryPath -RepositoryRoot $RepositoryRoot -RelativePath ([string]$Definition.manifestFile)
    $resolvedDefinitionPath = Resolve-RepositoryPath -RepositoryRoot $RepositoryRoot -RelativePath $DefinitionRelativePath
    $normalizedDefinitionPath = Get-NormalizedRelativePath -BasePath $RepositoryRoot -FullPath $resolvedDefinitionPath
    $primaryVariants = 0
    $primaryId = $null
    if (Test-DefinitionProperty -Definition $Definition -Name 'primaryStudy') {
        $primaryId = [string]$Definition.primaryStudy.id
        if (Test-DefinitionProperty -Definition $Definition.primaryStudy -Name 'variantCount') {
            $primaryVariants = [int]$Definition.primaryStudy.variantCount
        }
    }

    return [ordered]@{
        schemaVersion = 1
        checkpointId = [string]$Definition.checkpointId
        checkpointTitle = [string]$Definition.title
        checkpointDefinition = $normalizedDefinitionPath
        checkpointDefinitionSha256 = (Get-FileHash -LiteralPath $resolvedDefinitionPath -Algorithm SHA256).Hash.ToLowerInvariant()
        checkpointManifest = [string]$Definition.manifestFile
        checkpointManifestSha256 = (Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash.ToLowerInvariant()
        status = 'Running'
        repositoryOnly = $RepositoryOnlyMode
        startedUtc = [DateTime]::UtcNow.ToString('o')
        completedUtc = $null
        elapsedSeconds = 0.0
        sdk = [ordered]@{
            expected = [string]$Definition.sdkVersion
            actual = $null
        }
        configuration = [string]$Definition.configuration
        requested = [ordered]@{
            trialsPerVariant = $Trials
            jobs = $Jobs
        }
        build = [ordered]@{
            cleanExecuted = $false
            succeeded = $false
            warnings = $null
            errors = $null
            elapsedSeconds = 0.0
        }
        tests = [ordered]@{
            succeeded = $false
            total = 0
            passed = 0
            failed = 0
            skipped = 0
            elapsedSeconds = 0.0
            trxPath = $null
        }
        primaryStudy = [ordered]@{
            id = $primaryId
            variantCount = $primaryVariants
            trialsPerVariant = $Trials
            totalTrials = [long]$primaryVariants * [long]$Trials
        }
        aggregates = [ordered]@{
            configuredRunnerStages = @($Definition.stages).Count
            runnerStagesPassed = 0
            runnerStagesFailed = 0
            deterministicCases = 0
            mechanicsCases = 0
            variants = 0
            trials = [long]0
            selfTests = 0
            failedGates = 0
        }
        stages = (New-Object System.Collections.ArrayList)
        outputPaths = [ordered]@{
            root = Get-NormalizedRelativePath -BasePath $RepositoryRoot -FullPath $OutputRootPath
            acceptanceJson = (Get-NormalizedRelativePath -BasePath $RepositoryRoot -FullPath (Join-Path $OutputRootPath 'acceptance-summary.json'))
            acceptanceText = (Get-NormalizedRelativePath -BasePath $RepositoryRoot -FullPath (Join-Path $OutputRootPath 'acceptance-summary.txt'))
        }
        firstFailure = $null
    }
}

function Write-AcceptanceSummary {
    param(
        [Parameter(Mandatory = $true)]$Summary,
        [Parameter(Mandatory = $true)][string]$OutputRootPath
    )

    [void](New-Item -ItemType Directory -Path $OutputRootPath -Force)
    $jsonPath = Join-Path $OutputRootPath 'acceptance-summary.json'
    $jsonTemporary = "$jsonPath.tmp"
    $Summary | ConvertTo-Json -Depth 16 | Set-Content -LiteralPath $jsonTemporary -Encoding UTF8
    Move-Item -LiteralPath $jsonTemporary -Destination $jsonPath -Force

    $textPath = Join-Path $OutputRootPath 'acceptance-summary.txt'
    $textTemporary = "$textPath.tmp"
    $lines = New-Object System.Collections.Generic.List[string]
    foreach ($line in @(
        "STAR CLUSTER CHECKPOINT $($Summary.checkpointId) ACCEPTANCE SUMMARY",
        "Status: $($Summary.status)",
        "Definition: $($Summary.checkpointDefinition)",
        "Definition SHA-256: $($Summary.checkpointDefinitionSha256)",
        "Manifest: $($Summary.checkpointManifest)",
        "Manifest SHA-256: $($Summary.checkpointManifestSha256)",
        "Started UTC: $($Summary.startedUtc)",
        "Completed UTC: $($Summary.completedUtc)",
        ("Elapsed seconds: {0:N3}" -f [double]$Summary.elapsedSeconds),
        "SDK expected/actual: $($Summary.sdk.expected) / $($Summary.sdk.actual)",
        "Build warnings/errors: $($Summary.build.warnings) / $($Summary.build.errors)",
        ("Build elapsed seconds: {0:N3}" -f [double]$Summary.build.elapsedSeconds),
        "Tests passed/failed/skipped/total: $($Summary.tests.passed) / $($Summary.tests.failed) / $($Summary.tests.skipped) / $($Summary.tests.total)",
        ("Test elapsed seconds: {0:N3}" -f [double]$Summary.tests.elapsedSeconds),
        "Test results: $($Summary.tests.trxPath)",
        "Runner stages passed/failed/configured: $($Summary.aggregates.runnerStagesPassed) / $($Summary.aggregates.runnerStagesFailed) / $($Summary.aggregates.configuredRunnerStages)",
        "Deterministic cases: $($Summary.aggregates.deterministicCases)",
        "Mechanics cases: $($Summary.aggregates.mechanicsCases)",
        "Calibration variants/trials: $($Summary.aggregates.variants) / $($Summary.aggregates.trials)",
        "Primary study variants/trials: $($Summary.primaryStudy.variantCount) / $($Summary.primaryStudy.totalTrials)",
        "ScenarioRunner self-tests: $($Summary.aggregates.selfTests)",
        "Failed gates: $($Summary.aggregates.failedGates)",
        "Output root: $($Summary.outputPaths.root)",
        "Acceptance JSON: $($Summary.outputPaths.acceptanceJson)",
        "Acceptance text: $($Summary.outputPaths.acceptanceText)",
        "First failure: $($Summary.firstFailure)"
    )) {
        [void]$lines.Add($line)
    }
    if ($Summary.stages.Count -gt 0) {
        [void]$lines.Add('')
        [void]$lines.Add('RUNNER STAGES')
        foreach ($stage in $Summary.stages) {
            [void]$lines.Add(("{0}: {1}; elapsed {2:N3}s; failed gates {3}; output {4}" -f
                $stage.id,
                $stage.status,
                [double]$stage.elapsedSeconds,
                [int]$stage.failedGates,
                $stage.outputPath))
        }
    }
    Set-Content -LiteralPath $textTemporary -Value $lines -Encoding UTF8
    Move-Item -LiteralPath $textTemporary -Destination $textPath -Force
}

function Read-TrxCounters {
    param([Parameter(Mandatory = $true)][string]$TrxPath)

    [xml]$document = Get-Content -LiteralPath $TrxPath -Raw
    $counters = $document.SelectSingleNode("//*[local-name()='Counters']")
    if ($null -eq $counters) { throw "TRX counters were not found in $TrxPath." }
    return [ordered]@{
        total = [int]$counters.total
        passed = [int]$counters.passed
        failed = [int]$counters.failed
        skipped = [int]$counters.notExecuted
    }
}

function Get-StageOutputRelativePath {
    param(
        [Parameter(Mandatory = $true)]$Stage,
        [Parameter(Mandatory = $true)][string]$OutputRoot,
        [Parameter(Mandatory = $true)][int]$Trials,
        [Parameter(Mandatory = $true)][int]$Jobs
    )

    $expanded = @()
    foreach ($argument in @($Stage.arguments)) {
        $expanded += Expand-CheckpointArgument -Value ([string]$argument) -OutputRoot $OutputRoot -Trials $Trials -Jobs $Jobs
    }
    for ($index = 0; $index -lt $expanded.Count - 1; $index++) {
        if ($expanded[$index] -eq '--output-dir') { return [string]$expanded[$index + 1] }
    }
    return $null
}

function Add-StageGateMetricsToAcceptanceSummary {
    param(
        [Parameter(Mandatory = $true)]$Summary,
        [Parameter(Mandatory = $true)][string]$RepositoryRoot,
        [AllowNull()][string]$StageOutput
    )

    if ([string]::IsNullOrWhiteSpace($StageOutput)) { return 0 }
    $stageOutputPath = Resolve-RepositoryPath -RepositoryRoot $RepositoryRoot -RelativePath $StageOutput
    $summaryPath = Join-Path $stageOutputPath 'summary.json'
    if (-not (Test-Path -LiteralPath $summaryPath -PathType Leaf)) { return 0 }

    try {
        $stageSummary = Get-Content -LiteralPath $summaryPath -Raw | ConvertFrom-Json
        $failedGateCount = 0
        if (Test-DefinitionProperty -Definition $stageSummary -Name 'failedGates') {
            $failedGateCount = [int]$stageSummary.failedGates
        }
        elseif (Test-DefinitionProperty -Definition $stageSummary -Name 'gates') {
            $gates = $stageSummary.gates
            if ((Test-DefinitionProperty -Definition $gates -Name 'failed')) {
                $failedGateCount = @($gates.failed).Count
            }
            else {
                $failedGateCount = @($gates | Where-Object { -not [bool]$_.passed }).Count
            }
        }
        $Summary.aggregates.failedGates += $failedGateCount
        return $failedGateCount
    }
    catch {
        Write-Warning "Unable to read failed-gate metrics from $summaryPath`: $($_.Exception.Message)"
        return 0
    }
}

function Add-StageMetricsToAcceptanceSummary {
    param(
        [Parameter(Mandatory = $true)]$Summary,
        [Parameter(Mandatory = $true)]$Stage,
        [Parameter(Mandatory = $true)][int]$Trials
    )

    if (-not (Test-DefinitionProperty -Definition $Stage -Name 'metrics')) { return }
    $metrics = $Stage.metrics
    if (Test-DefinitionProperty -Definition $metrics -Name 'deterministicCases') {
        $Summary.aggregates.deterministicCases += [int]$metrics.deterministicCases
    }
    if (Test-DefinitionProperty -Definition $metrics -Name 'caseCount') {
        $Summary.aggregates.mechanicsCases += [int]$metrics.caseCount
    }
    if (Test-DefinitionProperty -Definition $metrics -Name 'variantCount') {
        $variantCount = [int]$metrics.variantCount
        $countTowardVariantAggregate = $true
        if (Test-DefinitionProperty -Definition $metrics -Name 'countTowardVariantAggregate') {
            $countTowardVariantAggregate = [bool]$metrics.countTowardVariantAggregate
        }
        if ($countTowardVariantAggregate) {
            $Summary.aggregates.variants += $variantCount
        }
        $usesTrials = $false
        if (Test-DefinitionProperty -Definition $metrics -Name 'usesTrials') {
            $usesTrials = [bool]$metrics.usesTrials
        }
        if ($usesTrials) {
            $stageTrials = [long]$Trials
            if (Test-DefinitionProperty -Definition $metrics -Name 'trialsPerVariant') {
                $stageTrials = [long]$metrics.trialsPerVariant
            }
            $Summary.aggregates.trials += [long]$variantCount * $stageTrials
        }
    }
    if (Test-DefinitionProperty -Definition $metrics -Name 'selfTestCount') {
        $Summary.aggregates.selfTests += [int]$metrics.selfTestCount
    }
}

$OperationRegistry = [ordered]@{}

function Register-CalibrationOperation {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][scriptblock]$Operation
    )
    if ($OperationRegistry.Contains($Name)) { throw "Calibration operation $Name is already registered." }
    $OperationRegistry[$Name] = $Operation
}

function Invoke-CalibrationOperation {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [object[]]$Arguments = @()
    )
    if (-not $OperationRegistry.Contains($Name)) { throw "Calibration operation $Name is not registered." }
    return & $OperationRegistry[$Name] @Arguments
}

function Test-CalibrationOperationRegistry {
    param([Parameter(Mandatory = $true)][string[]]$RequiredOperations)

    foreach ($name in $RequiredOperations) {
        if (-not $OperationRegistry.Contains($name)) { throw "Calibration operation $name is not registered." }
        if ($OperationRegistry[$name] -isnot [scriptblock]) { throw "Calibration operation $name is not executable." }
    }
    Write-Host "       Operation registry: $($RequiredOperations.Count) stable semantic operations registered."
}

Register-CalibrationOperation -Name 'RepositoryManifest' -Operation ${function:Test-RepositoryManifest}
Register-CalibrationOperation -Name 'PowerShellSyntax' -Operation ${function:Test-PowerShellSyntax}
Register-CalibrationOperation -Name 'CheckpointDefinition' -Operation ${function:Read-CheckpointDefinition}
Register-CalibrationOperation -Name 'NativeDependencyPrecheck' -Operation ${function:Invoke-RequiredNativeDependencyPrecheck}
Register-CalibrationOperation -Name 'DocumentationStatus' -Operation ${function:Show-DocumentationStatus}
Register-CalibrationOperation -Name 'DotNetExecutable' -Operation ${function:Resolve-DotNetExecutable}
Register-CalibrationOperation -Name 'DotNetSdkVersion' -Operation ${function:Get-DotNetSdkVersion}
Register-CalibrationOperation -Name 'RunnerStage' -Operation ${function:Invoke-RunnerStage}

$requiredOperations = @('RepositoryManifest', 'PowerShellSyntax', 'CheckpointDefinition', 'NativeDependencyPrecheck', 'DocumentationStatus', 'DotNetExecutable', 'DotNetSdkVersion', 'RunnerStage')
Test-CalibrationOperationRegistry -RequiredOperations $requiredOperations

$repositoryRoot = Get-RepositoryRoot
$definitionPath = $CheckpointDefinition
$acceptanceSummary = $null
$outputRootPath = $null
$runStopwatch = [System.Diagnostics.Stopwatch]::StartNew()
Push-Location $repositoryRoot
try {
    $definition = Invoke-CalibrationOperation -Name 'CheckpointDefinition' -Arguments @($repositoryRoot, $definitionPath)
    Invoke-CalibrationOperation -Name 'NativeDependencyPrecheck' -Arguments @($repositoryRoot, $definition, $definitionPath)
    $effectiveTrials = if ($Trials -gt 0) { $Trials } else { [int]$definition.defaultTrials }
    $effectiveJobs = if ($Jobs -gt 0) { $Jobs } else { [int]$definition.defaultJobs }
    if ($effectiveTrials -lt 1) { throw 'Trials must be positive.' }
    if ($effectiveJobs -lt 1) { throw 'Jobs must be positive.' }

    $outputRootPath = Resolve-RepositoryPath -RepositoryRoot $repositoryRoot -RelativePath ([string]$definition.outputRoot)
    if (-not $NoClean) {
        Remove-Item -LiteralPath $outputRootPath -Recurse -Force -ErrorAction SilentlyContinue
    }
    [void](New-Item -ItemType Directory -Path $outputRootPath -Force)
    $outputRoot = Get-NormalizedRelativePath -BasePath $repositoryRoot -FullPath $outputRootPath
    $acceptanceSummary = New-AcceptanceSummary -Definition $definition -RepositoryRoot $repositoryRoot -OutputRootPath $outputRootPath -DefinitionRelativePath $definitionPath -Trials $effectiveTrials -Jobs $effectiveJobs -RepositoryOnlyMode ([bool]$RepositoryOnly)
    Write-AcceptanceSummary -Summary $acceptanceSummary -OutputRootPath $outputRootPath

    $stages = @($definition.stages)
    $totalSteps = 5 + $stages.Count

    Write-Host "[1/$totalSteps] Verifying repository integrity and PowerShell syntax..."
    Invoke-CalibrationOperation -Name 'RepositoryManifest' -Arguments @($repositoryRoot, [string]$definition.manifestFile)
    Invoke-CalibrationOperation -Name 'PowerShellSyntax' -Arguments @($repositoryRoot)
    Write-AcceptanceSummary -Summary $acceptanceSummary -OutputRootPath $outputRootPath

    Write-Host "[2/$totalSteps] Reading calibration settings and non-blocking documentation status..."
    Write-Host "       Trials: $effectiveTrials; jobs: $effectiveJobs; output: $($definition.outputRoot)."
    Invoke-CalibrationOperation -Name 'DocumentationStatus' -Arguments @($repositoryRoot, $definition)
    if ($RepositoryOnly) {
        $acceptanceSummary.status = 'RepositoryValidated'
        $acceptanceSummary.completedUtc = [DateTime]::UtcNow.ToString('o')
        $acceptanceSummary.elapsedSeconds = $runStopwatch.Elapsed.TotalSeconds
        Write-AcceptanceSummary -Summary $acceptanceSummary -OutputRootPath $outputRootPath
        Write-Host ''
        Write-Host "Checkpoint $($definition.checkpointId) repository validation completed successfully."
        return
    }

    Write-Host "[3/$totalSteps] Confirming the pinned .NET SDK..."
    $dotnetPath = Invoke-CalibrationOperation -Name 'DotNetExecutable'
    $sdkVersion = Invoke-CalibrationOperation -Name 'DotNetSdkVersion' -Arguments @($dotnetPath)
    $acceptanceSummary.sdk.actual = $sdkVersion
    Write-Host "       SDK: $sdkVersion"
    if ($sdkVersion -ne [string]$definition.sdkVersion) { throw "Expected .NET SDK $($definition.sdkVersion), found $sdkVersion." }
    Write-AcceptanceSummary -Summary $acceptanceSummary -OutputRootPath $outputRootPath

    Write-Host "[4/$totalSteps] Building the headless calibration solution with warnings as errors..."
    $buildStopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    if (-not $NoClean) {
        Invoke-NativeCommand -Executable $dotnetPath -Arguments @('clean', [string]$definition.calibrationSolution, '--configuration', [string]$definition.configuration, '--nologo') -Description 'Calibration clean'
        $acceptanceSummary.build.cleanExecuted = $true
    }
    Invoke-NativeCommand -Executable $dotnetPath -Arguments @('build', [string]$definition.calibrationSolution, '--configuration', [string]$definition.configuration, '--nologo', '-warnaserror') -Description 'Calibration build'
    $buildStopwatch.Stop()
    $acceptanceSummary.build.succeeded = $true
    $acceptanceSummary.build.warnings = 0
    $acceptanceSummary.build.errors = 0
    $acceptanceSummary.build.elapsedSeconds = $buildStopwatch.Elapsed.TotalSeconds
    Write-AcceptanceSummary -Summary $acceptanceSummary -OutputRootPath $outputRootPath

    Write-Host "[5/$totalSteps] Running engine-independent C# tests..."
    $testResultsPath = Join-Path $outputRootPath 'test-results'
    [void](New-Item -ItemType Directory -Path $testResultsPath -Force)
    $testStopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    $testFailure = $null
    try {
        Invoke-NativeCommand -Executable $dotnetPath -Arguments @('test', [string]$definition.testProject, '--configuration', [string]$definition.configuration, '--no-build', '--nologo', '--logger', 'trx;LogFileName=checkpoint-tests.trx', '--results-directory', $testResultsPath) -Description 'Engine-independent test suite'
    }
    catch {
        $testFailure = $_
    }
    finally {
        $testStopwatch.Stop()
    }
    $trxPath = Join-Path $testResultsPath 'checkpoint-tests.trx'
    if (Test-Path -LiteralPath $trxPath -PathType Leaf) {
        $testCounters = Read-TrxCounters -TrxPath $trxPath
        $acceptanceSummary.tests.succeeded = ($testCounters.failed -eq 0 -and $null -eq $testFailure)
        $acceptanceSummary.tests.total = $testCounters.total
        $acceptanceSummary.tests.passed = $testCounters.passed
        $acceptanceSummary.tests.failed = $testCounters.failed
        $acceptanceSummary.tests.skipped = $testCounters.skipped
        $acceptanceSummary.tests.trxPath = Get-NormalizedRelativePath -BasePath $repositoryRoot -FullPath $trxPath
    }
    $acceptanceSummary.tests.elapsedSeconds = $testStopwatch.Elapsed.TotalSeconds
    Write-AcceptanceSummary -Summary $acceptanceSummary -OutputRootPath $outputRootPath
    if ($null -ne $testFailure) { throw $testFailure }

    $step = 6
    foreach ($stage in $stages) {
        Write-Host "[$step/$totalSteps] Running $($stage.name)..."
        $stageOutput = Get-StageOutputRelativePath -Stage $stage -OutputRoot $outputRoot -Trials $effectiveTrials -Jobs $effectiveJobs
        $stageRecord = [ordered]@{
            id = [string]$stage.id
            name = [string]$stage.name
            command = [string]$stage.command
            status = 'Running'
            startedUtc = [DateTime]::UtcNow.ToString('o')
            completedUtc = $null
            elapsedSeconds = 0.0
            outputPath = $stageOutput
            failedGates = 0
        }
        [void]$acceptanceSummary.stages.Add($stageRecord)
        Write-AcceptanceSummary -Summary $acceptanceSummary -OutputRootPath $outputRootPath
        $stageStopwatch = [System.Diagnostics.Stopwatch]::StartNew()
        try {
            Invoke-CalibrationOperation -Name 'RunnerStage' -Arguments @($dotnetPath, [string]$definition.runnerProject, [string]$definition.configuration, $stage, $outputRoot, $effectiveTrials, $effectiveJobs)
            $stageStopwatch.Stop()
            $stageRecord.status = 'Passed'
            $stageRecord.completedUtc = [DateTime]::UtcNow.ToString('o')
            $stageRecord.elapsedSeconds = $stageStopwatch.Elapsed.TotalSeconds
            $acceptanceSummary.aggregates.runnerStagesPassed++
            Add-StageMetricsToAcceptanceSummary -Summary $acceptanceSummary -Stage $stage -Trials $effectiveTrials
            $stageRecord.failedGates = Add-StageGateMetricsToAcceptanceSummary -Summary $acceptanceSummary -RepositoryRoot $repositoryRoot -StageOutput $stageOutput
        }
        catch {
            $stageStopwatch.Stop()
            $stageRecord.status = 'Failed'
            $stageRecord.completedUtc = [DateTime]::UtcNow.ToString('o')
            $stageRecord.elapsedSeconds = $stageStopwatch.Elapsed.TotalSeconds
            $acceptanceSummary.aggregates.runnerStagesFailed++
            $stageRecord.failedGates = Add-StageGateMetricsToAcceptanceSummary -Summary $acceptanceSummary -RepositoryRoot $repositoryRoot -StageOutput $stageOutput
            throw
        }
        finally {
            Write-AcceptanceSummary -Summary $acceptanceSummary -OutputRootPath $outputRootPath
        }
        $step++
    }

    $acceptanceSummary.status = 'Success'
    $acceptanceSummary.completedUtc = [DateTime]::UtcNow.ToString('o')
    $acceptanceSummary.elapsedSeconds = $runStopwatch.Elapsed.TotalSeconds
    Write-AcceptanceSummary -Summary $acceptanceSummary -OutputRootPath $outputRootPath
    Write-Host ''
    Write-Host "Checkpoint $($definition.checkpointId) headless calibration completed successfully."
    Write-Host "All C# tests and $($stages.Count) configured runner stages returned successful exit codes."
    Write-Host "Acceptance summaries: $outputRoot/acceptance-summary.json and acceptance-summary.txt."
    Write-Host 'Godot and StarCluster.Game were not required for this calibration run.'
}
catch {
    if ($null -ne $acceptanceSummary -and $null -ne $outputRootPath) {
        $acceptanceSummary.status = 'Failure'
        $acceptanceSummary.completedUtc = [DateTime]::UtcNow.ToString('o')
        $acceptanceSummary.elapsedSeconds = $runStopwatch.Elapsed.TotalSeconds
        if ($null -eq $acceptanceSummary.firstFailure) {
            $acceptanceSummary.firstFailure = [string]$_.Exception.Message
        }
        Write-AcceptanceSummary -Summary $acceptanceSummary -OutputRootPath $outputRootPath
    }
    throw
}
finally {
    $runStopwatch.Stop()
    Pop-Location
}
