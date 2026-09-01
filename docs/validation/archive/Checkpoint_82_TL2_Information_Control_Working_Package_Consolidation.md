# Checkpoint 82 - TL2 Information-Control Working Package Consolidation

## Purpose

Checkpoint 82 consolidates the accepted Checkpoint 79a, 80, and 81a evidence for the first current-architecture TL2 Tactical Computer / Sensor / ECM / ECCM package. This is an architecture/documentation checkpoint, not a new balance study.

## Validated working candidates

The current TL2 information-control working package carries:

- Tactical Computer ordinary targeting assistance: **+12 percentage points**;
- Tactical Computer degraded-fire penalty: **-25 percentage points**;
- Evasive Compensation: **0**;
- Sensor Discrimination Resistance: **1**;
- ECM normal rating ceiling: **2**, at **1 TP/rating**;
- ECCM normal rating ceiling: **2**, at **1 TP/rating**.

These are **validated working candidates** for further TL2 integration. They are not a complete production TL2 combat profile.

Explicitly not promoted by this checkpoint:

- no TL2 Sensor physical-range increase;
- no reactor-output increase;
- no new TL2 Sensor/ECM/ECCM overload or efficiency mode;
- no weapon degraded-fire entitlement;
- no missile Approximate-terminal capability.

## Accepted evidence

- Checkpoint 79a: `tl2-itc06-sensor-ew-discrimination-isolation`, summary SHA-256 `eecbdf5a935d984655416c3fe4fae61308493cad778c89b2272f84ea5b761c61`.
- Checkpoint 80: `tl2-itc07-ew-power-pressure-tall-viability`, summary SHA-256 `596a90b51ae73691e5571b270785f445faed7ed443177f52aa5effff429cb992`.
- Checkpoint 81a: `tl2-itc08-tactical-computer-ew-integration-permutations`, summary SHA-256 `e0e351298a5c276179b20a72376aeef02a93c9c995031acebfab4d6b643d1c6c`.

## Standing suite

`technology_integration_permutation_suite_v0_2.json` is now the current planning definition. It makes the validated TL2 information-control package a reusable axis, while retaining the CP81 v0.1 definition unchanged for historical reproducibility. Future studies should extend only the subsystem dimension whose dependency changed and must pass the full cross-study integration audit before handoff.

## Historical compatibility

Historical ScenarioRunner studies contain identifiers such as `tl2-production`. Those identifiers remain frozen compatibility data. They do not become current authority merely because their names contain `production`. The current Concept, Matrix v1, and `tl2_computing_sensor_ew_working_profile_v0_1.json` define the present interpretation.

## Native acceptance

Run repository-only validation first, then the normal native checkpoint:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-82\apply_checkpoint_82.ps1 -RepositoryOnly
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-82\apply_checkpoint_82.ps1 -Jobs 24
```

Expected normal workload: **8 stages, approximately 863 unit tests, 48 ScenarioRunner self-tests, 0 Monte Carlo variants/trials**. Deep Calibration is not required for this checkpoint.
