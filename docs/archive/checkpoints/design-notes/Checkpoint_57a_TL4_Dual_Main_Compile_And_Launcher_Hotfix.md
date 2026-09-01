# Checkpoint 57a - TL4 Dual-Main Compile and Launcher Hotfix

## Scope

Checkpoint 57a is a **release hotfix only**. It preserves every Checkpoint 57 scenario, profile, workbook, Concept decision, variant, seed, and trial count. No combat or balance parameter changes are introduced.

The hotfix corrects three release defects found by the native Windows build:

1. Move the `tl4-foundation-two-main-telemetry` result gate from the pre-result `Validate()` method into `BuildGates()`, where `gates` and `results` exist.
2. Format nullable `InitialRangeHexes` safely in the Checkpoint 57 review CSV.
3. Remove Python from the user-facing checkpoint launcher; native validation requires only PowerShell and the pinned .NET SDK.

## Repository-only validation

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-57a\apply_checkpoint_57a.ps1 -RepositoryOnly
```

Expected: repository manifest verification, PowerShell syntax, architecture/hotfix contract, pinned SDK, clean warning-as-error build, tests, and repository-only harness checks.

## Full validation

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-57a\apply_checkpoint_57a.ps1 -Trials 10000 -Jobs 24
```

The simulation workload is unchanged from Checkpoint 57: **50 stages / 13,846 Monte Carlo variants / 138.46 million trials**. Results are written under `out\checkpoint-57a`.

## Acceptance

Acceptance requires the native build to complete with zero warnings/errors, all tests and all 50 stages to pass, and no failed gates. The resulting Monte Carlo evidence should be assessed as the original Checkpoint 57 TL4 screening evidence; 57a changes only release plumbing.
