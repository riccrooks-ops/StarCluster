# Checkpoint 62 — TL1 Tactical Power Doctrine and Reactor Output Sensitivity

Checkpoint 62 is a focused follow-up to accepted Checkpoint 61. It does not change the accepted 35-Space construction envelope or production TL1 reactor output. It tests whether power-sensitive composed-build outcomes depend on player-facing power-allocation doctrine and on a controlled ±1 TP reactor-output sensitivity band.

## Required acceptance

From a clean extraction on Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-62\apply_checkpoint_62.ps1 -RepositoryOnly
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-62\apply_checkpoint_62.ps1
```

The normal run defaults to **10,000 trials per variant** and **24 workers**. It contains 8 stages and 108 current-study variants (1,080,000 Monte Carlo trials).

Inspect `out/checkpoint-62/tl1-power-doctrine-reactor-sensitivity/` and retain at least:

- `gates.csv`
- `variants.csv`
- `power-doctrine-reactor-matrix.csv`
- `power-doctrine-build-rollup.csv`
- `power-doctrine-reactor-rollup.csv`

No target win percentage is a release gate. The release gates verify study shape, no trial errors, doctrine/reactor coverage, real Tactical Power pressure, and actual PDS allocation sensitivity.

## Optional Deep Calibration

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-62\apply_checkpoint_62.ps1 -DeepCalibration
```

Deep Calibration is **not required for Checkpoint 62 acceptance**. It expands to 21 stages / 1,188 Monte Carlo variants / 11,880,000 default trials and includes the accepted Checkpoint 61 broad composed-build matrix as historical regression evidence.

## Interpretation

The production TL1 reactor remains **5 TP**. Reactor outputs 4 and 6 are sensitivity probes only. Energy APEN and other contextual capabilities must not be dismissed merely because the present TL1 control does not fully exercise them. Sensorless builds remain established-Firm-track isolation results until a later sensor/acquisition/EW-coupled study.
