# Checkpoint 78 - Technology Architecture Matrix and Concept Synchronization

## Purpose

Checkpoint 78 is an architecture/documentation checkpoint built on accepted Checkpoint 77a. It introduces **Technology Architecture Matrix v1** for Tactical Computer, Sensor, ECM, and ECCM progression and synchronizes Concept v0.6q with that roadmap.

This checkpoint deliberately changes **no production combat values, runtime mechanics, AI doctrine, or Monte Carlo study inputs**. The TL2 row is candidate design only.

## What must be true

- Concept v0.6q is the only active Concept under `docs/`.
- Matrix v1 exists in Markdown, JSON, and XLSX review formats and all three express the same status/ownership model.
- Tactical Computer remains owned by Computing / Fire Control.
- Sensor, ECM, and ECCM remain distinct progression streams within Sensors / EW; the matrix does not create new player-visible research disciplines.
- TL1 architecture is unchanged: Tactical Computer degraded-fire rating -25 pp, weapon-specific permission, Sensor Discrimination Resistance 0, same-hex Burn-through +1, normal ECM/ECCM rating 1 at 1 TP, and ordinary missile Firm-terminal rules.
- TL2 is explicitly candidate-only: legacy +12 ordinary targeting for revalidation; degraded fire held at -25; Sensor Discrimination Resistance 1 proposed while the Balanced-0 range fixture is held; ECM/ECCM normal ceilings 2 at 1 TP/rating proposed; new TL2 overload/efficiency behavior deferred.
- No TL2 profile is added to the production Tactical Computer fire-control catalog.
- No production weapon receives Approximate-track direct-fire permission.
- Normal acceptance remains the accepted deterministic 8-stage suite with zero Monte Carlo variants. Deep Calibration is not required for this checkpoint.

## Native validation

First run the repository-only contract:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-78\apply_checkpoint_78.ps1 -RepositoryOnly
```

Expected repository-only behavior:

- native dependency precheck succeeds without a Python runtime dependency;
- Checkpoint 78 definition/manifest bindings are correct;
- Concept, Matrix v1, current architecture documents, and machine-readable data agree;
- TL2 candidates are proven non-production;
- historical architecture files remain explicitly historical;
- repository manifest validation succeeds.

Then run normal acceptance:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-78\apply_checkpoint_78.ps1 -Jobs 24
```

Expected normal acceptance:

- pinned .NET SDK 8.0.423;
- warning-as-error build with zero warnings/errors;
- approximately 863 unit tests if no unrelated test-count changes occurred;
- 8/8 runner stages;
- 47 ScenarioRunner self-tests;
- zero Monte Carlo variants/trials;
- zero failed gates and zero trial errors.

## Deep Calibration

Do **not** run Deep Calibration merely because Matrix v1 sketches TL2-TL9 roles. The matrix is not a numerical promotion. Deep Calibration remains available only if native acceptance exposes a regression or a later substantive technology pass changes a declared dependency that requires broader revalidation.

## Next substantive pass

After Checkpoint 78 acceptance, build a focused **TL2 technology-progression calibration** from Matrix v1. Revalidate the legacy +12 Tactical Computer targeting candidate under the current architecture and test the proposed Sensor Discrimination Resistance 1 / ECM 2 / ECCM 2 relationships with mixed-TL, Tactical Power, degraded-fire/ECCM, PDS, movement, and missile-pressure controls before promoting TL2 values.
