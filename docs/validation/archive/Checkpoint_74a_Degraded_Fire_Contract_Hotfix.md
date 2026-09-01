# Checkpoint 74a - Degraded-Fire Contract Hotfix

## Intent

Checkpoint 74a is a contract-only hotfix for Checkpoint 74. The first native `-RepositoryOnly` run correctly stopped before build or Monte Carlo, but the CP74 static contract used the wrong source-file signature for degraded-fire accuracy plumbing: it required the public `AccuracyModifier` result property name to appear inside `DirectFireTargetEligibility.cs`, even though the property is correctly declared by `DirectFireTargetEligibilityResult.cs` and the eligibility service passes the lowercase `accuracyModifier` value into that result.

CP74a changes no game mechanics, study inputs, AI doctrine, Concept content, or production component definitions. The contract now validates the actual cross-file wiring and freezes the substantive CP74 files by SHA-256 so the hotfix cannot silently become a mechanics change.

## Degraded-fire foundation retained unchanged

`tl1-itc16-approximate-track-degraded-fire` remains the same 20-variant diagnostic: 2 direct-fire family orientations x 2 fixed ranges x 5 track/penalty cases. Production weapons remain Firm-only. The diagnostic trait remains opt-in, its -10/-20/-30 percentage-point candidates remain study-only, and missiles/torpedoes remain excluded from degraded direct fire.

## Native acceptance

Extract this complete repository over the repository root, then run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-74a\apply_checkpoint_74a.ps1 -RepositoryOnly
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-74a\apply_checkpoint_74a.ps1 -Jobs 24
```

Expected normal workload remains unchanged from CP74:

- 11 runner stages.
- 853 unit tests if no unrelated test-count changes occur.
- 924 deterministic Sensor/EW foundation rows.
- 20-variant actual-consumer degraded-fire preflight.
- 20 one-trial full-pipeline smoke executions.
- 20 substantive variants / 200,000 substantive trials.
- 46 ScenarioRunner self-tests.

## Deep Calibration

Do not run by default. The CP74a hotfix does not change any substantive dependency that would justify Deep Calibration.
