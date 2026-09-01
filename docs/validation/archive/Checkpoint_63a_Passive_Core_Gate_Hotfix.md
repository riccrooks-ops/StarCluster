# Checkpoint 63a - Passive-Core Gate Hotfix

Checkpoint 63a is a release-gate hotfix to Checkpoint 63. It does **not** change the accepted TL1 sensor envelope, the six 35-Space builds, the 72-variant study matrix, the production 5-TP reactor, FullVolleyFirst doctrine, movement rules, weapon authorization rules, or any combat number.

The Checkpoint 63 native run completed all 72 variants but exposed an over-strong gate: `tl1-c63-passive-core-not-blind` required every passive-only sensorless lane to observe at least one Firm or Approximate track. A valid lane may remain outside the passive envelope after movement for the entire engagement and therefore correctly report only `NoTrack`. That is an out-of-range result, not a blind ship.

Checkpoint 63a corrects only that assertion. The gate now verifies that the accepted passive envelope remains nonzero, every passive-only sensorless lane performs sensor evaluations without committing active-sensor power, and each sensorless build demonstrates successful passive acquisition in at least one paired weapon-family lane where geometry permits it.

## Required acceptance

From a clean extraction on Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-63a\apply_checkpoint_63a.ps1 -RepositoryOnly
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-63a\apply_checkpoint_63a.ps1
```

The normal run remains **8 stages / 72 current-study variants / 720,000 Monte Carlo trials** at the default 10,000 trials per variant and 24 workers.

Inspect `out/checkpoint-63/tl1-operational-sensor-acquisition-ew/` and retain at least:

- `gates.csv`
- `variants.csv`
- `operational-sensor-acquisition-matrix.csv`
- `operational-sensor-build-rollup.csv`
- `operational-sensor-paired-review.csv`

No target win percentage is a release gate.

## Optional Deep Calibration

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-63a\apply_checkpoint_63a.ps1 -DeepCalibration
```

Deep Calibration remains **not required** for Checkpoint 63a acceptance. It is unchanged from Checkpoint 63.

## Interpretation guardrails

- TL1 production reactor output remains **5 TP**.
- FullVolleyFirst remains the offensive-isolation doctrine for this study.
- All cruisers retain core passive sensing; `activeSensor=false` means passive-only, not blind.
- A passive-only lane can legitimately remain `NoTrack` if combat geometry stays beyond the passive Approximate envelope.
- Side B remains established-Firm so only Side A acquisition changes.
- Energy APEN and other latent/contextual capabilities remain protected from retuning based on a matchup that does not exercise them.
