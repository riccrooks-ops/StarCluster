# Checkpoint 74b - ScenarioRunner Compile Hotfix

## Intent

Checkpoint 74b is a compile-only hotfix for Checkpoint 74/74a. The native CP74a `-RepositoryOnly` validation passed, then the normal native build exposed one stale type name in the new CP74 degraded-fire study validator: `ValidateTl1ApproximateTrackDegradedFireCoverage` declared its Sensor/EW catalog parameter as the nonexistent `Tl1OperationalSensorEnvelope`. The rest of the integrated runner, including the actual loaded catalog, consistently uses `SensorEwFoundationProfile`.

During pre-package review, a second compile-only issue was also found before another native run: the new degraded-fire CSV writer called `ConditionalSideAWinPercent(result)` without defining that report helper. CP74b therefore corrects the validator signature and adds the missing report-only helper. It changes no combat mechanics, study inputs, AI doctrine, Concept content, production weapon definitions, candidate penalties, release-gate semantics, or expected workload.

The CP74b contract explicitly rejects the stale nonexistent type, requires the actual Sensor/EW catalog type in the validator signature, requires the report helper, and SHA-freezes the substantive CP74 files after these compile-only corrections.

## Degraded-fire foundation retained unchanged

`tl1-itc16-approximate-track-degraded-fire` remains the same 20-variant diagnostic: 2 direct-fire family orientations x 2 fixed ranges x 5 track/penalty cases. Production weapons remain Firm-only. The diagnostic trait remains opt-in, its -10/-20/-30 percentage-point candidates remain study-only, and missiles/torpedoes remain excluded from degraded direct fire.

## Native acceptance

Extract this complete repository over the repository root, then run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-74b\apply_checkpoint_74b.ps1 -RepositoryOnly
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-74b\apply_checkpoint_74b.ps1 -Jobs 24
```

Expected normal workload remains unchanged from CP74/CP74a:

- 11 runner stages.
- 853 unit tests if no unrelated test-count changes occur.
- 924 deterministic Sensor/EW foundation rows.
- 20-variant actual-consumer degraded-fire preflight.
- 20 one-trial full-pipeline smoke executions.
- 20 substantive variants / 200,000 substantive trials.
- 46 ScenarioRunner self-tests.

## Deep Calibration

Do not run by default. CP74b changes only compile-time/report wiring (the stale validator type name and the missing review helper) and does not change a substantive dependency that would justify Deep Calibration.
