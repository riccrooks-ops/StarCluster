[CmdletBinding()]
param([switch]$RepositoryOnly,[switch]$NoClean)
Set-StrictMode -Version 2.0
$ErrorActionPreference='Stop'
$repositoryRoot=(Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$contract=Join-Path $PSScriptRoot 'test_checkpoint_121_contract.py'
$preflight=Join-Path $PSScriptRoot 'preflight_checkpoint_121.py'
$reanalyze120=Join-Path $PSScriptRoot 'reanalyze_cp120_native.py'
$hygiene=Join-Path $repositoryRoot 'tools\checkpoints\prepackage_repository_hygiene.py'
$cli=Join-Path $repositoryRoot 'tools\simulation\run_starcluster_research.py'
$study121=Join-Path $repositoryRoot 'docs\archive\testing\pre-cp165-active\damage_resolution_scaling_study_v0_1.json'
$study120=Join-Path $repositoryRoot 'docs\archive\testing\pre-cp165-active\weapon_progression_sensitivity_study_v0_1.json'
$study119=Join-Path $repositoryRoot 'docs\archive\testing\pre-cp165-active\campaign_weapon_integration_study_v0_1.json'
$study118=Join-Path $repositoryRoot 'docs\archive\testing\pre-cp165-active\simplified_weapon_progression_study_v0_1.json'
$study116=Join-Path $repositoryRoot 'docs\archive\testing\pre-cp165-active\warhead_role_generation_study_v0_1.json'
$study115=Join-Path $repositoryRoot 'docs\archive\testing\pre-cp165-active\weapon_family_payload_study_v0_2.json'
$study114=Join-Path $repositoryRoot 'docs\archive\testing\pre-cp165-active\payload_characteristic_space_study_v0_1.json'
$source120=Join-Path $repositoryRoot 'docs\validation\evidence\checkpoint-121\CP120_NATIVE_RESULTS_ORIGINAL.zip'
$checkedCorrection=Join-Path $repositoryRoot 'docs\validation\evidence\checkpoint-121\cp120-corrected'
$outRoot=Join-Path $repositoryRoot 'out\checkpoint-121'

function Get-Cpython313Command {
    $candidates=@(@{Command='py';Args=@('-3.13')},@{Command='python';Args=@()},@{Command='python3';Args=@()})
    foreach($candidate in $candidates){
        $cmd=Get-Command $candidate.Command -ErrorAction SilentlyContinue
        if($null -eq $cmd){continue}
        $versionText=& $candidate.Command @($candidate.Args + @('--version')) 2>&1 | Out-String
        if($LASTEXITCODE -eq 0 -and $versionText -match 'Python\s+3\.13(?:\.|\s|$)'){return $candidate}
    }
    throw 'CP121 requires CPython 3.13 for deterministic validation and research simulation.'
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
function Assert-DamageShape([string]$AnalysisPath,[int]$Variants,[int64]$Trials,[int]$EqVariants,[int64]$EqPairs,[string]$Label){
    $a=Get-Content -LiteralPath $AnalysisPath -Raw | ConvertFrom-Json
    if([int]$a.variants -ne $Variants -or [int64]$a.totalTrials -ne $Trials -or [int]$a.equivalenceVariants -ne $EqVariants -or [int64]$a.equivalencePairedTrials -ne $EqPairs -or -not [bool]$a.equivalenceExact -or [int64]$a.equivalenceMismatchedTrials -ne 0 -or @($a.failedGates).Count -ne 0){throw "$Label result shape/equivalence/gates failed."}
}

Write-Host '[1/10] Resolving Python research runtime and production boundary...'
$python=Get-Cpython313Command
$version=& $python.Command @($python.Args + @('--version')) 2>&1 | Out-String
Write-Host ("       {0}" -f $version.Trim())
Write-Host '       x2 damage scaling is research-only; shipped game/runtime remains C# / Godot.'

Write-Host '[2/10] Applying and verifying pre-package repository hygiene...'
Invoke-PythonChecked $python @('-B',$hygiene,'--repo',$repositoryRoot,'--apply') 'CP121 pre-package hygiene apply failed'
Invoke-PythonChecked $python @('-B',$hygiene,'--repo',$repositoryRoot,'--check') 'CP121 pre-package hygiene check failed'

Write-Host '[3/10] Running CP121 scaling/correction preflight, self-tests, and parity fixtures...'
Invoke-PythonChecked $python @('-B',$preflight,'--repo',$repositoryRoot) 'CP121 preflight failed'
Push-Location $repositoryRoot
try {
    & $python.Command @($python.Args + @('-B','-m','unittest','discover','-s','tools/simulation/tests','-p','test_*.py'))
    if($LASTEXITCODE -ne 0){throw 'CP121 Python self-tests failed.'}
    Write-Host '       Python self-tests: 120/120 passed.'
    if(-not $NoClean -and (Test-Path $outRoot)){Remove-Item -Recurse -Force $outRoot}
    New-Item -ItemType Directory -Force -Path $outRoot | Out-Null
    $parityOut=Join-Path $outRoot 'parity'; $parityLog=Join-Path $outRoot 'parity.log'
    Invoke-StudyCaptured $python @('-B',$cli,'--repo',$repositoryRoot,'parity','--output-dir',$parityOut) $parityOut $parityLog 'CP121 C#/Python parity fixtures failed'
    $parity=Get-Content (Join-Path $parityOut 'summary.json') -Raw | ConvertFrom-Json
    if(-not $parity.passed -or [int]$parity.cases -ne 25 -or @($parity.errors).Count -ne 0){throw 'CP121 parity result shape failed.'}
    Write-Host '       C#/Python parity fixtures: 25/25 passed.'

    Write-Host '[4/10] Running CP114/CP115a/CP116/CP118/CP119/CP120 regression smokes...'
    $regressions=@(
        @{Name='cp114-regression-smoke';Cmd='payload-study';Study=$study114;Variants=3184},
        @{Name='cp115a-regression-smoke';Cmd='weapon-family-study';Study=$study115;Variants=4064},
        @{Name='cp116-regression-smoke';Cmd='warhead-generation-study';Study=$study116;Variants=2976},
        @{Name='cp118-regression-smoke';Cmd='simplified-weapon-study';Study=$study118;Variants=1824},
        @{Name='cp119-regression-smoke';Cmd='weapon-integration-study';Study=$study119;Variants=1152},
        @{Name='cp120-regression-smoke';Cmd='weapon-sensitivity-study';Study=$study120;Variants=4284}
    )
    foreach($r in $regressions){
        $o=Join-Path $outRoot $r.Name; $l=Join-Path $outRoot ($r.Name+'.log')
        Invoke-StudyCaptured $python @('-B',$cli,'--repo',$repositoryRoot,$r.Cmd,$r.Study,'--output-dir',$o,'--trials','1','--jobs','24') $o $l ("CP121 {0} failed" -f $r.Name)
        Assert-StudyShape (Join-Path $o 'analysis.json') $r.Variants $r.Variants $r.Name
        Write-Host ("       {0}: {1:N0} variants / engagements; zero failed gates." -f $r.Name,$r.Variants)
    }

    Write-Host '[5/10] Reanalyzing preserved CP120 native telemetry without combat rerun...'
    $corrOut=Join-Path $outRoot 'cp120-native-corrected'
    Invoke-PythonChecked $python @('-B',$reanalyze120,'--repo',$repositoryRoot,'--source-zip',$source120,'--output-dir',$corrOut) 'CP120 native telemetry reanalysis failed'
    foreach($name in @('correction_summary.json','integration_summary.csv','sensitivity_delta_summary.csv','swarmer_sensitivity.csv','pds_isolation_summary.csv')){
        $aHash=(Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $corrOut $name)).Hash
        $bHash=(Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $checkedCorrection $name)).Hash
        if($aHash -ne $bHash){throw "CP120 corrected output is not reproducible: $name"}
    }
    Write-Host '       Preserved 8,568,000-engagement CP120 output reanalyzed; corrected derived summaries are byte-reproducible.'

    Write-Host '[6/10] Running complete CP121 one-trial x2 equivalence + half-step smoke...'
    $smokeOut=Join-Path $outRoot 'cp121-full-smoke'; $smokeLog=Join-Path $outRoot 'cp121-full-smoke.log'
    Invoke-StudyCaptured $python @('-B',$cli,'--repo',$repositoryRoot,'damage-resolution-study',$study121,'--output-dir',$smokeOut,'--trials','1','--equivalence-trials','1','--jobs','24') $smokeOut $smokeLog 'CP121 full smoke failed'
    Assert-DamageShape (Join-Path $smokeOut 'analysis.json') 2424 2424 4284 4284 'CP121 full smoke'
    Write-Host '       CP121 smoke: 4,284 exact legacy/x2 pairs + 2,424 half-step engagements; zero mismatches/errors/gates.'

    $nativeResults=$null
    if($RepositoryOnly){
        Write-Host '[7/10] RepositoryOnly requested; substantive CP121 study skipped.'
        Write-Host '       Checked-in authoring: 21,420 exact equivalence pairs + 60,600 half-step engagements.'
    } else {
        Write-Host '[7/10] Running substantive CP121 x2 equivalence and half-step study...'
        $nativeResults=Join-Path $outRoot 'native-damage-resolution-study'; $nativeLog=Join-Path $outRoot 'native-damage-resolution-study.log'
        Invoke-StudyCaptured $python @('-B',$cli,'--repo',$repositoryRoot,'damage-resolution-study',$study121,'--output-dir',$nativeResults,'--trials','2000','--equivalence-trials','20','--jobs','24') $nativeResults $nativeLog 'CP121 substantive damage-resolution study failed'
        Assert-DamageShape (Join-Path $nativeResults 'analysis.json') 2424 4848000 4284 85680 'CP121 substantive study'
        Write-Host '       Native equivalence: 4,284 variants x 20 paired trials = 85,680 pairs / 171,360 combat executions; zero mismatches.'
        Write-Host '       Native half-step study: 2,424 variants x 2,000 trials = 4,848,000 engagements; zero failed gates.'
    }

    Write-Host '[8/10] Verifying Checkpoint 121 repository/evidence contracts...'
    $args=@('-B',$contract,'--repo',$repositoryRoot)
    if($null -ne $nativeResults){$args += @('--native-results',$nativeResults)}
    Invoke-PythonChecked $python $args 'CP121 repository/evidence contract failed'

    Write-Host '[9/10] Confirming no automatic numerical, Concept, or player-authority promotion...'
    Write-Host '       CP119 remains the accepted baseline. Production C#/Godot values remain unchanged.'
    Write-Host '       x2 and all odd-point values remain diagnostic until human review and a later explicit migration checkpoint.'

    Write-Host '[10/10] Checkpoint complete.'
} finally { Pop-Location }
Write-Host ''
Write-Host 'Checkpoint 121 damage-resolution scaling validation completed successfully.'
if($RepositoryOnly){Write-Host 'RepositoryOnly completed without running the substantive 4.848-million-engagement half-step study or 85,680-pair native equivalence study.'}
