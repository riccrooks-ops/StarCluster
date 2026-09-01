# Checkpoint 72 - Reactive Pre-Combat EW Sub-Phase

## Intent

Checkpoint 72 promotes the agreed timing model into the executable tactical study while leaving CP71's numerical Sensor/EW model unchanged.

Authoritative timing under test:

**Movement -> post-Movement observation -> ECM declarations -> ECCM responses -> finalized tracks -> normal combat.**

EW does not reroll initiative. ECM receives one declaration layer; ECCM receives one response layer. Any Tactical Power available to those decisions is simply the ordinary uncommitted Available pool.

## Normal native acceptance

From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-72\apply_checkpoint_72.ps1 -RepositoryOnly
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-72\apply_checkpoint_72.ps1 -Jobs 24
```

Expected primary workload:

- 11 runner stages.
- 843 unit tests if no unrelated test count changes occur.
- 924 deterministic Sensor/EW foundation rows.
- 39-variant actual-consumer preflight.
- 39 one-trial smoke executions.
- 39 substantive variants / 390,000 substantive trials.
- 46 ScenarioRunner self-tests.

## Acceptance interpretation

Release gates verify wiring, coverage, power accounting, point-blank reactive ECCM non-use, ordinary-range reactive ECCM exercise, bilateral EW exercise, and absence of overload/static-range-penalty drift. Combat outcomes remain diagnostic.

## Deep Calibration

Do not run by default. Use `-DeepCalibration` only if the normal results or a later dependency change justify it.
