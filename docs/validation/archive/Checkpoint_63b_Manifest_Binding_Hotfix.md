# Checkpoint 63b - Manifest Binding Hotfix

Checkpoint 63b is a packaging/validation-contract hotfix to Checkpoint 63a. It changes **no combat mechanics, sensor mechanics, study variants, seeds, weapon statistics, reactor output, power doctrine, movement behavior, or release-gate semantics**.

Checkpoint 63a correctly shipped the current root manifest as `CHECKPOINT_63A_SHA256SUMS.txt`, but its apply script reused `tools/calibration/checkpoints/checkpoint-63.json`. That historical definition still declared `CHECKPOINT_63_SHA256SUMS.txt`, which the Checkpoint 62+ repository-cleanup policy had correctly retired. Native `-RepositoryOnly` validation therefore stopped before build/test execution with `Checkpoint definition references missing file CHECKPOINT_63_SHA256SUMS.txt.`

Checkpoint 63b fixes the binding explicitly:

- normal definition: `tools/calibration/checkpoints/checkpoint-63b.json`;
- deep definition: `tools/calibration/checkpoints/checkpoint-63b-deep-calibration.json`;
- both definitions bind `CHECKPOINT_63B_SHA256SUMS.txt`;
- normal output root is `out/checkpoint-63b`;
- Deep Calibration output root is `out/checkpoint-63b-deep-calibration`; and
- static/PowerShell contracts now assert those identities so this exact regression cannot pass preflight again.

The Checkpoint 63a passive-core gate correction remains intact: a passive-only lane may legitimately remain `NoTrack` when geometry keeps it outside passive range, while sensorless builds must still evaluate their core passive sensing without active-sensor power and demonstrate passive acquisition where geometry permits.

## Required acceptance

From a clean extraction on Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-63b\apply_checkpoint_63b.ps1 -RepositoryOnly
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-63b\apply_checkpoint_63b.ps1
```

The normal run remains **8 stages / 72 Monte Carlo variants / 720,000 default trials**, using the production **5 TP** TL1 reactor and **FullVolleyFirst** doctrine. No target win rate is a release gate.

Deep Calibration remains optional and is not required for Checkpoint 63b acceptance:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-63b\apply_checkpoint_63b.ps1 -DeepCalibration
```

Deep Calibration remains **22 stages / 1,260 Monte Carlo variants / 12,600,000 default trials**.

## Interpretation guardrails

All cruisers retain core passive sensing; the optional Active Sensor suite extends that baseline rather than creating sensing from nothing. Side B remains established-Firm in the Checkpoint 63 operational study. Energy APEN and other contextual advantages must not be demoted merely because the present TL1 opponent underexercises them.
