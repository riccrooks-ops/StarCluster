# Checkpoint 61 — TL1 35-Space Composed-Ship and Odd-Build Combat Study

## Goal

Accept the first explicit composed-ship combat bridge for the Checkpoint 60 TL1 35-Space construction envelope and collect diagnostic combat evidence for all six legal reference/odd builds without imposing a target win rate.

## Required normal acceptance

From a clean full-repository extraction with Godot closed, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-61\apply_checkpoint_61.ps1 -RepositoryOnly
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-61\apply_checkpoint_61.ps1
```

The first command verifies repository contract, manifest, checkpoint definitions, parser/static design contracts, and then invokes the harness repository-only path. The second performs the clean warning-as-error .NET build/tests and runs the 8-stage normal suite, including 54 composed-ship Monte Carlo variants.

The default is 10,000 trials per variant and 24 jobs. Override with `-Trials` or `-Jobs` only for diagnostics; acceptance evidence should use the default unless we explicitly agree otherwise.

## Optional Deep Calibration

Run only when broad historical stochastic requalification is desired:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-61\apply_checkpoint_61.ps1 -DeepCalibration
```

Deep Calibration is **not required for Checkpoint 61 acceptance**. It expands the workload to 20 stages / 1,080 Monte Carlo variants / 10.8 million trials at default settings.

## Required evidence

The normal run must pass all checkpoint and runner gates. In `out/checkpoint-61/tl1-composed-ship-odd-build-combat`, retain:

- `summary.json`, `gates.csv`, `variants.csv`, and `result.sha256.txt`;
- `composed-build-matrix.csv`;
- `composed-build-rollup.csv`;
- `composed-build-family-rollup.csv`.

The composed-build result gates verify coverage, no trial errors, second-main execution, multi-PDS telemetry, and observable Tactical Power contention. They deliberately do **not** gate a desired win percentage.

## Human review after acceptance

Review the six build rollups for power starvation/surplus, attack density, PDS concentration, shield opportunity cost, pacing, unresolved outcomes, and matchup sensitivity. Treat sensorless-build results as combat-isolation evidence only because this pass assumes an established Firm track and does not yet price full sensor/EW operational risk.

Do not change Space costs, component values, or stacking rules until the evidence identifies a concrete pathology and its mechanism.
