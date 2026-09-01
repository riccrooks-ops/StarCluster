[CmdletBinding()]
param([switch]$RepositoryOnly,[switch]$NoClean)
Set-StrictMode -Version 2.0
$ErrorActionPreference='Stop'
$repositoryRoot=(Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$contract=Join-Path $PSScriptRoot 'test_checkpoint_119_contract.py'
$preflight=Join-Path $PSScriptRoot 'preflight_checkpoint_119.py'
$hygiene=Join-Path $repositoryRoot 'tools\checkpoints\prepackage_repository_hygiene.py'
$cli=Join-Path $repositoryRoot 'tools\simulation\run_starcluster_research.py'
$study119=Join-Path $repositoryRoot 'docs\archive\testing\pre-cp165-active\campaign_weapon_integration_study_v0_1.json'
$study118=Join-Path $repositoryRoot 'docs\archive\testing\pre-cp165-active\simplified_weapon_progression_study_v0_1.json'
$study116=Join-Path $repositoryRoot 'docs\archive\testing\pre-cp165-active\warhead_role_generation_study_v0_1.json'
$study115=Join-Path $repositoryRoot 'docs\archive\testing\pre-cp165-active\weapon_family_payload_study_v0_2.json'
$study114=Join-Path $repositoryRoot 'docs\archive\testing\pre-cp165-active\payload_characteristic_space_study_v0_1.json'
$outRoot=Join-Path $repositoryRoot 'out\checkpoint-119'

function Get-Cpython313Command {
    $candidates=@(@{Command='py';Args=@('-3.13')},@{Command='python';Args=@()},@{Command='python3';Args=@()})
    foreach($candidate in $candidates){
        $cmd=Get-Command $candidate.Command -ErrorAction SilentlyContinue
        if($null -eq $cmd){continue}
        $versionText=& $candidate.Command @($candidate.Args + @('--version')) 2>&1 | Out-String
        if($LASTEXITCODE -eq 0 -and $versionText -match 'Python\s+3\.13(?:\.|\s|$)'){return $candidate}
    }
    throw 'CP119 requires CPython 3.13 for deterministic validation and research simulation.'
}
function Invoke-PythonChecked([object]$Python,[string[]]$Arguments,[string]$FailureMessage){
    & $Python.Command @($Python.Args + $Arguments)
    if($LASTEXITCODE -ne 0){throw "$FailureMessage (exit code $LASTEXITCODE)."}
}
function Invoke-StudyCaptured([object]$Python,[string[]]$Arguments,[string]$OutputDir,[string]$LogPath,[string]$FailureMessage){
    & $Python.Command @($Python.Args + $Arguments) > $LogPath 2>&1
    $exitCode=$LASTEXITCODE
    if($exitCode -ne 0){
        foreach($candidate in @((Join-Path $OutputDir 'analysis.json'),(Join-Path $OutputDir 'summary.json'))){
            if(Test-Path -LiteralPath $candidate){
                try {
                    $failure=Get-Content -LiteralPath $candidate -Raw | ConvertFrom-Json
                    if($null -ne $failure.failedGates -and @($failure.failedGates).Count -gt 0){Write-Host ("       Failed gates: {0}" -f (@($failure.failedGates) -join ', ')) -ForegroundColor Red}
                    if($null -ne $failure.gates -and $null -ne $failure.gates.failed -and @($failure.gates.failed).Count -gt 0){Write-Host ("       Failed gates: {0}" -f (@($failure.gates.failed) -join ', ')) -ForegroundColor Red}
                    if($null -ne $failure.error){Write-Host ("       Error: {0}" -f $failure.error) -ForegroundColor Red}
                } catch { Write-Host ("       Could not parse {0} after failure." -f $candidate) -ForegroundColor Yellow }
            }
        }
        if(Test-Path -LiteralPath $LogPath){
            Write-Host '       Study output tail:' -ForegroundColor Yellow
            Get-Content -LiteralPath $LogPath -Tail 60 | ForEach-Object { Write-Host ("       $_") }
        }
        throw "$FailureMessage (exit code $exitCode)."
    }
}
function Assert-StudyShape([string]$AnalysisPath,[int]$Variants,[int64]$Trials,[string]$Label){
    $a=Get-Content -LiteralPath $AnalysisPath -Raw | ConvertFrom-Json
    if([int]$a.variants -ne $Variants -or [int64]$a.totalTrials -ne $Trials -or @($a.failedGates).Count -ne 0){throw "$Label result shape/gates failed."}
}

Write-Host '[1/9] Resolving Python research runtime and production boundary...'
$python=Get-Cpython313Command
$version=& $python.Command @($python.Args + @('--version')) 2>&1 | Out-String
Write-Host ("       {0}" -f $version.Trim())
Write-Host '       Python is permitted for research/testing; shipped game/runtime remains C# / Godot.'

Write-Host '[2/9] Applying and verifying pre-package repository hygiene...'
Invoke-PythonChecked $python @('-B',$hygiene,'--repo',$repositoryRoot,'--apply') 'CP119 pre-package hygiene apply failed'
Invoke-PythonChecked $python @('-B',$hygiene,'--repo',$repositoryRoot,'--check') 'CP119 pre-package hygiene check failed'

Write-Host '[3/9] Running CP119 KISS/substantive-path preflight, self-tests, and parity fixtures...'
Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot) 'CP119 campaign-integration preflight failed'
Push-Location $repositoryRoot
try {
    & $python.Command @($python.Args + @('-B','-m','unittest','discover','-s','tools/simulation/tests','-p','test_*.py'))
    if($LASTEXITCODE -ne 0){throw 'CP119 Python self-tests failed.'}
    Write-Host '       Python self-tests: 97/97 passed.'
    if(-not $NoClean -and (Test-Path $outRoot)){Remove-Item -Recurse -Force $outRoot}
    New-Item -ItemType Directory -Force -Path $outRoot | Out-Null
    $parityOut=Join-Path $outRoot 'parity'; $parityLog=Join-Path $outRoot 'parity.log'
    Invoke-StudyCaptured $python @('-B',$cli,'--repo',$repositoryRoot,'parity','--output-dir',$parityOut) $parityOut $parityLog 'CP119 C#/Python parity fixtures failed'
    $parity=Get-Content (Join-Path $parityOut 'summary.json') -Raw | ConvertFrom-Json
    if(-not $parity.passed -or [int]$parity.cases -ne 25 -or @($parity.errors).Count -ne 0){throw 'CP119 parity result shape failed.'}
    Write-Host '       C#/Python parity fixtures: 25/25 passed.'

    Write-Host '[4/9] Running CP114/CP115a/CP116/CP118 regression smokes...'
    $cp114Out=Join-Path $outRoot 'cp114-regression-smoke'; $cp114Log=Join-Path $outRoot 'cp114-regression-smoke.log'
    Invoke-StudyCaptured $python @('-B',$cli,'--repo',$repositoryRoot,'payload-study',$study114,'--output-dir',$cp114Out,'--trials','1','--jobs','24') $cp114Out $cp114Log 'CP119 CP114 regression smoke failed'
    Assert-StudyShape (Join-Path $cp114Out 'analysis.json') 3184 3184 'CP114 regression smoke'
    Write-Host '       CP114 regression smoke: 3,184 variants / 3,184 engagements; zero failed gates.'
    $cp115Out=Join-Path $outRoot 'cp115a-regression-smoke'; $cp115Log=Join-Path $outRoot 'cp115a-regression-smoke.log'
    Invoke-StudyCaptured $python @('-B',$cli,'--repo',$repositoryRoot,'weapon-family-study',$study115,'--output-dir',$cp115Out,'--trials','1','--jobs','24') $cp115Out $cp115Log 'CP119 CP115a regression smoke failed'
    Assert-StudyShape (Join-Path $cp115Out 'analysis.json') 4064 4064 'CP115a regression smoke'
    Write-Host '       CP115a regression smoke: 4,064 variants / 4,064 engagements; zero failed gates.'
    $cp116Out=Join-Path $outRoot 'cp116-regression-smoke'; $cp116Log=Join-Path $outRoot 'cp116-regression-smoke.log'
    Invoke-StudyCaptured $python @('-B',$cli,'--repo',$repositoryRoot,'warhead-generation-study',$study116,'--output-dir',$cp116Out,'--trials','1','--jobs','24') $cp116Out $cp116Log 'CP119 CP116 regression smoke failed'
    Assert-StudyShape (Join-Path $cp116Out 'analysis.json') 2976 2976 'CP116 regression smoke'
    Write-Host '       CP116 regression smoke: 2,976 variants / 2,976 engagements; zero failed gates.'
    $cp118Out=Join-Path $outRoot 'cp118-regression-smoke'; $cp118Log=Join-Path $outRoot 'cp118-regression-smoke.log'
    Invoke-StudyCaptured $python @('-B',$cli,'--repo',$repositoryRoot,'simplified-weapon-study',$study118,'--output-dir',$cp118Out,'--trials','1','--jobs','24') $cp118Out $cp118Log 'CP119 CP118 regression smoke failed'
    Assert-StudyShape (Join-Path $cp118Out 'analysis.json') 1824 1824 'CP118 regression smoke'
    Write-Host '       CP118 regression smoke: 1,824 variants / 1,824 engagements; zero failed gates.'

    Write-Host '[5/9] Running CP119 all-variant one-trial smoke...'
    $smokeOut=Join-Path $outRoot 'smoke'; $smokeLog=Join-Path $outRoot 'smoke.log'
    Invoke-StudyCaptured $python @('-B',$cli,'--repo',$repositoryRoot,'weapon-integration-study',$study119,'--output-dir',$smokeOut,'--trials','1','--jobs','24') $smokeOut $smokeLog 'CP119 all-variant one-trial smoke failed'
    Assert-StudyShape (Join-Path $smokeOut 'analysis.json') 1152 1152 'CP119 smoke'
    Write-Host '       CP119 smoke: 1,152 variants / 1,152 engagements; zero failed gates.'

    $nativeResults=$null
    if($RepositoryOnly){
        Write-Host '[6/9] RepositoryOnly requested; substantive native campaign-integration study skipped.'
        Write-Host '       Checked-in bounded authoring evidence remains 57,600 engagements and is diagnostic only.'
    } else {
        Write-Host '[6/9] Running substantive campaign-weighted weapon-integration study...'
        $nativeResults=Join-Path $outRoot 'native-weapon-integration-study'; $nativeLog=Join-Path $outRoot 'native-weapon-integration-study.log'
        Invoke-StudyCaptured $python @('-B',$cli,'--repo',$repositoryRoot,'weapon-integration-study',$study119,'--output-dir',$nativeResults,'--trials','2000','--jobs','24') $nativeResults $nativeLog 'CP119 substantive campaign-integration study failed'
        Assert-StudyShape (Join-Path $nativeResults 'analysis.json') 1152 2304000 'CP119 substantive study'
        Write-Host '       Native study: 1,152 variants / 2,304,000 engagements; zero failed gates.'
    }

    Write-Host '[7/9] Verifying Checkpoint 119 repository/evidence contracts...'
    $args=@('-B',$contract,'--repo',$repositoryRoot)
    if($null -ne $nativeResults){$args += @('--native-results',$nativeResults)}
    Invoke-PythonChecked $python $args 'CP119 repository/evidence contract failed'

    Write-Host '[8/9] Confirming no automatic numerical or player-authority promotion...'
    Write-Host '       CP109/CP110 numerical authority and CP117 player-facing weapon authorities remain frozen.'
    Write-Host '       CP119 working GP/Swarmer/Kinetic candidates remain diagnostic until human review.'

    Write-Host '[9/9] Checkpoint complete.'
} finally { Pop-Location }
Write-Host ''
Write-Host 'Checkpoint 119 campaign-weighted weapon integration validation completed successfully.'
if($RepositoryOnly){Write-Host 'RepositoryOnly completed without running the substantive 2.304-million-engagement study.'}
