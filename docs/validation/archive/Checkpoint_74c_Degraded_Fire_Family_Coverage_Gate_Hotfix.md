# Checkpoint 74c - Degraded-Fire Family-Coverage Gate Hotfix

## Intent

Checkpoint 74c is a release-gate-only hotfix for Checkpoint 74/74a/74b. Native CP74b successfully passed repository validation, the clean warning-as-error build, all 853 unit tests, deterministic scenarios, mechanics corpora, construction checks, Sensor/EW foundation, and the CP74 actual-consumer preflight. All 20 one-trial degraded-fire smoke variants then executed successfully. After execution, the shared integrated-combat `weapon-family-coverage` release gate rejected the study because it still required Kinetic, Energy, and Missile coverage for every integrated study.

That assumption is invalid for CP74 by design: the degraded-fire foundation deliberately isolates Kinetic and Energy direct fire, while missile/torpedo guidance remains a separate Firm-track system and is explicitly excluded from degraded fire. CP74c therefore makes the shared family-coverage gate study-aware: CP74 requires Kinetic and Energy coverage; all existing studies retain their prior Kinetic/Energy/Missile requirement. The preflight status line is made study-aware for the same reason.

No combat mechanics, study inputs, candidate penalties, AI doctrine, Concept content, production weapon definitions, Tactical Power behavior, or outcome gates change.

## Native evidence preceding the hotfix

The CP74b native run established before the gate failure:

- warning-as-error build: 0 warnings, 0 errors;
- 853/853 unit tests passed;
- deterministic and TL1 Phase A/B corpora passed;
- TL1 construction and Sensor/EW foundation passed;
- CP74 actual-consumer preflight passed;
- all 20 one-trial smoke variants completed without trial errors;
- the smoke report listed exactly one failed gate: `weapon-family-coverage`.

This hotfix targets only that contradictory shared classification.

## Degraded-fire foundation retained unchanged

`tl1-itc16-approximate-track-degraded-fire` remains the same 20-variant diagnostic: 2 direct-fire family orientations x 2 fixed ranges x 5 track/penalty cases. Production weapons remain Firm-only. The diagnostic trait remains opt-in, its -10/-20/-30 percentage-point candidates remain study-only, and missiles/torpedoes remain excluded from degraded direct fire.

## Native acceptance

Extract this complete repository over the repository root, then run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-74c\apply_checkpoint_74c.ps1 -RepositoryOnly
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-74c\apply_checkpoint_74c.ps1 -Jobs 24
```

Expected normal workload remains unchanged:

- 11 runner stages.
- 853 unit tests if no unrelated test-count changes occur.
- 924 deterministic Sensor/EW foundation rows.
- 20-variant actual-consumer degraded-fire preflight.
- 20 one-trial full-pipeline smoke executions.
- 20 substantive variants / 200,000 substantive trials.
- 46 ScenarioRunner self-tests.

## Deep Calibration

Do not run by default. CP74c changes only shared release-gate classification/status text for the CP74 direct-fire-only study and does not change a substantive gameplay dependency.
