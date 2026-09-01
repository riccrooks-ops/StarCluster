# Checkpoint 69d - Sensor/EW Candidate Active-Power Gate Hotfix

## Scope

Checkpoint 69d is a release-gate semantics hotfix for Checkpoint 69c. Native CP69c validation confirmed the pinned .NET SDK, warning-as-error build, all 835 engine-independent C# tests, deterministic moving-missile scenarios, TL1 Phase A, TL1 Phase B, the TL1 35-Space construction envelope, the 924-row deterministic Sensor/EW foundation stage, and the new actual-consumer integrated loader/coverage preflight. The 72-variant one-trial smoke then executed all variants successfully but failed the `tl1-c69-normal-active-power-bounded` gate.

The simulation telemetry is cumulative per trial: `MeanActiveSensorPowerCommitted*` is the mean total Tactical Power committed to Active Sensors over an entire trial, while `MeanActiveSensorPoweredTurns*` counts powered sensor evaluations. The CP69c gate incorrectly compared cumulative per-trial power directly to the single-use 1-TP normal-mode cost. A multi-turn engagement could therefore fail even when every individual normal Active Sensor commitment cost exactly 1 TP.

## Hotfix

- Preserve the simulation and all Sensor/EW mechanics unchanged.
- Replace the erroneous `MeanActiveSensorPowerCommitted <= 1` assertion in clear-normal lanes with the telemetry-appropriate invariant `MeanActiveSensorPowerCommitted == MeanActiveSensorPoweredTurns` for both sides. Because all forward TL1 candidates use a 1-TP normal Active mode and clear-normal lanes forbid Sensor overload, this equality proves the intended 1-TP per powered evaluation cost without confusing cumulative trial power with per-use power.
- Add checkpoint-contract guards that reject the obsolete cumulative `<= 1` gate and require the powered-evaluation equality.
- Retain CP69c's actual-consumer preflight, 72-variant one-trial full-pipeline smoke, full exception diagnostics, candidate-catalog binding fix, and all CP69a/69b compile fixes.
- Preserve Concept v0.6h, Balanced-0/1/2 ranges, same-hex Sensor/EW semantics, study JSON, seeds, 100-fuel/5-TP controls, Monte Carlo workload, and diagnostic outcome policy unchanged.

## Acceptance

From a clean extraction on native Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-69d\apply_checkpoint_69d.ps1 -RepositoryOnly
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-69d\apply_checkpoint_69d.ps1 -Jobs 24
```

Normal acceptance remains **11 runner stages / 72 substantive Monte Carlo variants / 720,000 substantive default trials / 924 deterministic Sensor/EW rows**, plus **72 smoke trials**. Deep Calibration remains optional unless the normal run exposes an interacting regression.
