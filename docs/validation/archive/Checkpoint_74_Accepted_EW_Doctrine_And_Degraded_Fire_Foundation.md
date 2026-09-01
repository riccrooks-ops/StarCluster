# Checkpoint 74 - Accepted EW Doctrine and Degraded-Fire Foundation

## Intent

Checkpoint 74 first records the human-reviewed CP73 doctrine outcome as durable repository state. `tl1-ew-preserve-combat-package-v1` becomes the current TL1 EW default, `tl1-ew-reactive-eccm-v1` remains accepted supporting behavior, always-ECM remains a diagnostic control, and preserve-offense is explicitly rejected as the normal default. The registry pins CP73 result SHA-256 `667b553760b16ec63a67db52748a98bcb6daf7640bce21b3b7e4fc7d88da8613` and declares revalidation triggers. CP73 Monte Carlo is not rerun in the normal CP74 path.

The substantive CP74 mechanics study adds an explicit `AllowsApproximateTrackFire` weapon trait plus a data-driven accuracy penalty. Production weapon definitions are not changed. Missiles/torpedoes remain Firm/guidance-rule controlled and are excluded from the degraded-fire study.

## Controlled study

`tl1-itc16-approximate-track-degraded-fire` contains 20 variants: 2 direct-fire family orientations x 2 fixed ranges x 5 track/penalty cases. Bilateral normal ECM with no ECCM creates legitimate Approximate tracks at ranges 2 and 3. The sweep compares Firm reference, Approximate/Firm-only, and -10/-20/-30 percentage-point trait cases.

Release gates prove implementation and telemetry rather than a target win rate. The desired native evidence is whether degraded fire is useful but clearly inferior to Firm fire and which penalty region deserves later production weapon assignment.

## Normal native acceptance

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-74\apply_checkpoint_74.ps1 -RepositoryOnly
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-74\apply_checkpoint_74.ps1 -Jobs 24
```

Expected primary workload:

- 11 runner stages.
- 853 unit tests if no unrelated test-count changes occur.
- 924 deterministic Sensor/EW foundation rows.
- 20-variant actual-consumer degraded-fire preflight.
- 20 one-trial full-pipeline smoke executions.
- 20 substantive variants / 200,000 substantive trials.
- 46 ScenarioRunner self-tests.

## Post-run review

Review `degraded-fire-review.csv` for track state, blocked Firm-only controls, shot counts, mean final hit chance, hit percentage, pacing, and outcome changes. Do not promote a penalty or assign the trait to production weapons automatically from release gates.

## Deep Calibration

Do not run by default. Use `-DeepCalibration` only if normal results reveal a regression or a declared dependency change justifies broader work.
