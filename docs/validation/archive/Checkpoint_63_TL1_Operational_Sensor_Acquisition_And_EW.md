# Checkpoint 63 — TL1 Operational Sensor, Acquisition, and EW

Checkpoint 63 follows accepted Checkpoint 62. It keeps the accepted TL1 35-Space construction envelope, production 5-TP reactor, and retained combat numbers unchanged. The new work restores operational Firm-track acquisition to the six composed-ship packages so the cost/value of the optional active sensor can be measured rather than assumed away.

## Required acceptance

From a clean extraction on Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-63\apply_checkpoint_63.ps1 -RepositoryOnly
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-63\apply_checkpoint_63.ps1
```

The normal run defaults to **10,000 trials per variant** and **24 workers**. It contains **8 stages / 72 current-study variants / 720,000 Monte Carlo trials**.

Inspect `out/checkpoint-63/tl1-operational-sensor-acquisition-ew/` and retain at least:

- `gates.csv`
- `variants.csv`
- `operational-sensor-acquisition-matrix.csv`
- `operational-sensor-build-rollup.csv`
- `operational-sensor-paired-review.csv`

No target win percentage is a release gate. Mechanical gates verify the acquisition-regime matrix, active-sensor power use, passive sensing on ships without the optional suite, paired AutoActive/PassiveOnly parity for sensorless builds, EW-pressure exercise, and the fixed established-Firm Side-B control.

## Optional Deep Calibration

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-63\apply_checkpoint_63.ps1 -DeepCalibration
```

Deep Calibration is **not required for Checkpoint 63 acceptance**. It expands to **22 stages / 1,260 Monte Carlo variants / 12,600,000 default trials**, adding the accepted Checkpoint 62 and Checkpoint 61 studies plus the older stochastic TL1 corpus.

## Interpretation

- TL1 production reactor output remains **5 TP**.
- FullVolleyFirst is the current offensive-isolation policy; DefenseFirst remains a legitimate selectable posture but is not allowed to confound this sensor study.
- All cruisers retain core passive sensing. `activeSensor=false` means the optional 3-Space active suite is absent, not that the ship is blind.
- Side B retains an established Firm solution so only Side A acquisition changes.
- The EW1 lane is an abstract one-point net range penalty, not a final ECM/ECCM installation or power-cost ruling.
- This pass requires Firm authorization for all main-weapon families. Missile-specific Approximate-cue/seeker behavior remains a later missile-guidance study.
- Energy APEN and other latent/contextual capabilities must not be retuned merely because this TL1 matchup underexercises them.
