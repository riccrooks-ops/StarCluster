# Checkpoint 69c - Sensor/EW Candidate Catalog Binding Hotfix

## Scope

Checkpoint 69c is a runtime-binding successor hotfix for Checkpoint 69b. Native CP69b validation confirmed the pinned .NET SDK, warning-as-error build, all 835 engine-independent C# tests, deterministic moving-missile scenarios, TL1 Phase A, TL1 Phase B, the TL1 35-Space construction envelope, and the 924-row deterministic Sensor/EW foundation stage. The first operational candidate stage then failed before its own preflight banner with `Value cannot be null. (Parameter 'source')`.

The failure was in the integrated runner's Sensor/EW catalog loader. `Tl1SensorEwFoundationStudy` is a positional record with PascalCase CLR property names, while the authoritative catalog uses camelCase JSON. The dedicated foundation runner already deserializes that catalog case-insensitively, but the integrated runner reused its case-sensitive study options. Deserialization therefore left `Candidates` unbound, and the subsequent `ToDictionary(...)` call received a null source.

## Hotfix

- Make `LoadSensorEwProfiles(...)` use a dedicated copy of the integrated JSON options with `PropertyNameCaseInsensitive = true`, matching the authoritative foundation-runner binding contract.
- Add an explicit null guard for `catalog.Candidates` before dictionary construction so any future binding mismatch produces a domain-specific error instead of a generic LINQ `source` exception.
- Add an executable `tl1-integrated-tactical-combat-preflight` stage for the CP69 candidate study before the full Monte Carlo stage. This invokes the actual C# consumer loader and coverage validator without trials.
- Add a 72-variant, one-trial-per-variant execution smoke immediately after preflight. It runs the complete simulation, gate, and review-writer path before the 720,000-trial study.
- Add checkpoint-contract guards requiring the consumer-binding option, explicit candidate null guard, executable preflight, and 72-trial full-pipeline smoke in both normal and Deep Calibration definitions.
- Make top-level ScenarioRunner failures print the full exception (including stack trace) rather than only `Exception.Message`, so any remaining native-only failure identifies its actual call site.
- Retain the CP69a/69b compile fixes unchanged.
- Preserve Concept v0.6h, Balanced-0/1/2 ranges, same-hex Sensor/EW semantics, study JSON, seeds, 100-fuel/5-TP controls, Monte Carlo workload, and diagnostic release gates unchanged.

## Acceptance

From a clean extraction on native Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-69c\apply_checkpoint_69c.ps1 -RepositoryOnly
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-69c\apply_checkpoint_69c.ps1 -Jobs 24
```

Normal acceptance is now **11 runner stages / 72 substantive Monte Carlo variants / 720,000 substantive default trials / 924 deterministic Sensor/EW rows**, plus **72 smoke trials**. The preflight adds no trials; the smoke adds only one execution per candidate variant. Deep Calibration remains optional unless the normal run exposes an interacting regression.
