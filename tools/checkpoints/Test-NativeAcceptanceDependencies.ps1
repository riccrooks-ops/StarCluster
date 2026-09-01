[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$RepositoryRoot,
    [Parameter(Mandatory = $true)][string[]]$PowerShellPaths,
    [Parameter(Mandatory = $true)][string[]]$CheckpointDefinitionPaths,
    [string[]]$AllowedInterpreters = @()
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$defaultBlockedInterpreters = @('python', 'python3', 'py')
$allowedSet = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
foreach ($name in @($AllowedInterpreters)) { [void]$allowedSet.Add($name) }
$blockedInterpreters = @($defaultBlockedInterpreters | Where-Object { -not $allowedSet.Contains($_) })
$blockedSet = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
foreach ($name in $blockedInterpreters) { [void]$blockedSet.Add($name) }

function Resolve-RepositoryFile {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$RelativePath
    )

    $rootFull = [System.IO.Path]::GetFullPath($Root)
    $candidate = if ([System.IO.Path]::IsPathRooted($RelativePath)) {
        [System.IO.Path]::GetFullPath($RelativePath)
    }
    else {
        [System.IO.Path]::GetFullPath((Join-Path $rootFull $RelativePath))
    }
    $separator = [System.IO.Path]::DirectorySeparatorChar.ToString()
    $rootPrefix = if ($rootFull.EndsWith($separator)) { $rootFull } else { $rootFull + $separator }
    if (-not $candidate.StartsWith($rootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Native dependency precheck path escapes repository root: $RelativePath"
    }
    if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) {
        throw "Native dependency precheck file is missing: $RelativePath"
    }
    return $candidate
}

function Normalize-CommandToken {
    param([AllowNull()][string]$Token)
    if ([string]::IsNullOrWhiteSpace($Token)) { return $null }
    $clean = $Token.Trim().Trim([char[]]@([char]34, [char]39))
    $value = [System.IO.Path]::GetFileName($clean)
    if ($value.EndsWith('.exe', [System.StringComparison]::OrdinalIgnoreCase)) {
        $value = $value.Substring(0, $value.Length - 4)
    }
    return $value
}

function Assert-NotBlockedToken {
    param(
        [AllowNull()][string]$Token,
        [Parameter(Mandatory = $true)][string]$Context
    )
    $normalized = Normalize-CommandToken -Token $Token
    if ($null -ne $normalized -and $blockedSet.Contains($normalized)) {
        throw "Native acceptance dependency violation: blocked interpreter '$normalized' referenced by $Context. The active Windows acceptance path must remain PowerShell plus the pinned .NET SDK."
    }
}

function Get-ConstantStringValue {
    param([Parameter(Mandatory = $true)]$Ast)
    if ($Ast -is [System.Management.Automation.Language.StringConstantExpressionAst]) { return [string]$Ast.Value }
    if ($Ast -is [System.Management.Automation.Language.ExpandableStringExpressionAst] -and $Ast.NestedExpressions.Count -eq 0) { return [string]$Ast.Value }
    return $null
}

function Get-OptionalPropertyValue {
    param(
        [AllowNull()]$Object,
        [Parameter(Mandatory = $true)][string]$Name
    )

    if ($null -eq $Object) { return $null }
    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) { return $null }
    return $property.Value
}

function Assert-NoAliasCollidingFunctionNames {
    param(
        [Parameter(Mandatory = $true)][string]$RelativePath,
        [Parameter(Mandatory = $true)]$Ast
    )

    $functionDefinitions = @($Ast.FindAll({
        param($node)
        $node -is [System.Management.Automation.Language.FunctionDefinitionAst]
    }, $true))

    foreach ($functionDefinition in $functionDefinitions) {
        $functionName = [string]$functionDefinition.Name
        $alias = Get-Alias -Name $functionName -ErrorAction SilentlyContinue
        if ($null -ne $alias) {
            throw "Native acceptance PowerShell binding violation: $RelativePath defines function '$functionName', which collides case-insensitively with PowerShell alias '$($alias.Name)' -> '$($alias.Definition)'. Rename the helper to a descriptive non-alias name before native acceptance."
        }
    }

    return $functionDefinitions.Count
}

function Assert-ProvenCheckpointHarnessInvocation {
    param(
        [Parameter(Mandatory = $true)][string]$RelativePath,
        [Parameter(Mandatory = $true)][string]$FullPath,
        [Parameter(Mandatory = $true)]$Ast
    )

    $fileName = [System.IO.Path]::GetFileName($FullPath)
    if ($fileName -notlike 'apply_checkpoint_*.ps1') { return $false }

    $scriptText = [System.IO.File]::ReadAllText($FullPath)
    if ($scriptText.IndexOf('run_calibration_checkpoint.ps1', [System.StringComparison]::OrdinalIgnoreCase) -lt 0) { return $false }

    $harnessCommands = @($Ast.FindAll({
        param($node)
        if ($node -isnot [System.Management.Automation.Language.CommandAst]) { return $false }
        $text = $node.Extent.Text.Trim()
        return [regex]::IsMatch($text, '^&\s+\$harness(?:\s|$)', [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
    }, $true))

    if ($harnessCommands.Count -eq 0) {
        throw "Native acceptance interface violation: $RelativePath references run_calibration_checkpoint.ps1 but contains no executable '& `$harness ...' invocation for the pre-check to validate. Preserve the proven direct named-parameter wrapper interface."
    }

    $provenPattern = '^&\s+\$harness\s+-CheckpointDefinition\s+\$definition\s+-Trials\s+\$Trials\s+-Jobs\s+\$Jobs\s+-RepositoryOnly:\$RepositoryOnly\s+-NoClean:\$NoClean$'
    foreach ($command in $harnessCommands) {
        $commandText = [regex]::Replace($command.Extent.Text.Trim(), '\s+', ' ')
        if ([regex]::IsMatch($commandText, '&\s+\$harness\s+@[A-Za-z_][A-Za-z0-9_]*', [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)) {
            throw "Native acceptance interface violation: $RelativePath invokes the checkpoint harness through splatted arguments. Checkpoint wrappers must preserve the proven direct named-parameter call; array splatting can silently become positional binding and shift CheckpointDefinition into Trials or other typed parameters."
        }
        if (-not [regex]::IsMatch($commandText, $provenPattern, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)) {
            throw "Native acceptance interface violation: $RelativePath changed the checkpoint-harness call away from the native-validated form '& `$harness -CheckpointDefinition `$definition -Trials `$Trials -Jobs `$Jobs -RepositoryOnly:`$RepositoryOnly -NoClean:`$NoClean'. Preserve the proven interface unless a replacement is deliberately revalidated first."
        }
    }

    return $true
}

$powerShellCount = 0
$harnessWrapperCount = 0
$aliasCheckedFunctionCount = 0
foreach ($relative in $PowerShellPaths) {
    $path = Resolve-RepositoryFile -Root $RepositoryRoot -RelativePath $relative
    $tokens = $null
    $parseErrors = $null
    $ast = [System.Management.Automation.Language.Parser]::ParseFile($path, [ref]$tokens, [ref]$parseErrors)
    if (@($parseErrors).Count -gt 0) {
        throw "Native dependency precheck cannot inspect syntactically invalid PowerShell file: $relative"
    }

    $aliasCheckedFunctionCount += Assert-NoAliasCollidingFunctionNames -RelativePath $relative -Ast $ast

    if (Assert-ProvenCheckpointHarnessInvocation -RelativePath $relative -FullPath $path -Ast $ast) { $harnessWrapperCount++ }

    $commands = @($ast.FindAll({ param($node) $node -is [System.Management.Automation.Language.CommandAst] }, $true))
    foreach ($command in $commands) {
        $commandName = $command.GetCommandName()
        Assert-NotBlockedToken -Token $commandName -Context "$relative direct command"

        $normalizedCommand = Normalize-CommandToken -Token $commandName
        $elements = @($command.CommandElements)
        if ($elements.Count -lt 2) { continue }

        if ($normalizedCommand -in @('Start-Process', 'Get-Command', 'where', 'where.exe')) {
            $candidate = Get-ConstantStringValue -Ast $elements[1]
            Assert-NotBlockedToken -Token $candidate -Context "$relative $normalizedCommand argument"
        }
        elseif ($normalizedCommand -in @('cmd', 'cmd.exe')) {
            foreach ($element in $elements | Select-Object -Skip 1) {
                $candidate = Get-ConstantStringValue -Ast $element
                if ($null -eq $candidate) { continue }
                foreach ($piece in ($candidate -split '[\s;&|]+')) {
                    Assert-NotBlockedToken -Token $piece -Context "$relative cmd-mediated command"
                }
            }
        }
    }
    $powerShellCount++
}

$definitionCount = 0
foreach ($relative in $CheckpointDefinitionPaths) {
    $path = Resolve-RepositoryFile -Root $RepositoryRoot -RelativePath $relative
    $definition = Get-Content -LiteralPath $path -Raw | ConvertFrom-Json
    $stages = Get-OptionalPropertyValue -Object $definition -Name 'stages'
    foreach ($stage in @($stages)) {
        if ($null -eq $stage) { continue }
        $stageCommand = Get-OptionalPropertyValue -Object $stage -Name 'command'
        $stageId = Get-OptionalPropertyValue -Object $stage -Name 'id'
        $stageLabel = if ([string]::IsNullOrWhiteSpace([string]$stageId)) { '<unnamed>' } else { [string]$stageId }
        Assert-NotBlockedToken -Token ([string]$stageCommand) -Context "$relative runner stage '$stageLabel'"
    }
    $definitionCount++
}

if ($allowedSet.Count -gt 0) {
    $allowedDisplay = (@($AllowedInterpreters) -join ', ')
    Write-Host "       Native dependency precheck: $powerShellCount PowerShell paths and $definitionCount checkpoint definitions inspected; $harnessWrapperCount checkpoint harness interface(s) verified; $aliasCheckedFunctionCount function definition(s) alias-checked; explicitly allowed research interpreter(s): $allowedDisplay."
}
else {
    Write-Host "       Native dependency precheck: $powerShellCount PowerShell paths and $definitionCount checkpoint definitions inspected; $harnessWrapperCount checkpoint harness interface(s) verified; $aliasCheckedFunctionCount function definition(s) alias-checked; no Python runtime dependency."
}
