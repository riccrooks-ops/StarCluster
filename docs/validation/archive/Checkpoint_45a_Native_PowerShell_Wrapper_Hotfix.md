# Checkpoint 45a Validation - Native PowerShell Wrapper Hotfix

## Scope

Checkpoint 45a changes only the native validation entrypoint and release packaging. It removes the accidental Python runtime dependency from the Checkpoint 45 execution path. The Checkpoint 45 C# implementation, 1,188-variant primary study, candidate profiles, balance philosophy, and all retained stages are unchanged.

## Run

From a clean full-repository extraction in native Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-45a\apply_checkpoint_45a.ps1 -Trials 10000 -Jobs 24
```

Repository-only validation:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-45a\apply_checkpoint_45a.ps1 -RepositoryOnly
```

Python is not required. The wrapper invokes only the shared PowerShell checkpoint harness and the pinned .NET SDK.

## Required automated results

- Repository manifest verification passes with no unexpected repository-owned files.
- Exact .NET SDK 8.0.423 is used.
- Warning-as-error calibration build passes.
- All tests pass with no skips or failures.
- All 21 retained stages pass.
- The primary stage runs exactly 1,188 variants.
- All primary gates pass and every trial reports zero errors.
- The complete evidence package is written under `out/checkpoint-45a`.

## Assessment cautions

The Checkpoint 45 design cautions remain authoritative: do not seek exact family parity, do not combine withdrawal controls with ordinary combat, and do not promote a candidate solely because it is numerically closest to a target percentage.
