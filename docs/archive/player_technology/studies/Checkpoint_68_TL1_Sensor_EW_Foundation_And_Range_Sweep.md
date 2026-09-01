# Checkpoint 68 - TL1 Sensor/EW Foundation and Range Sweep

## Scope

Checkpoint 68 updates the authoritative Concept to v0.6g and adds a deterministic Sensor/EW foundation study before any new production sensor ranges are promoted into integrated combat.

The new causal model separates:

- passive/active physical sensing reach;
- emission-assisted Approximate detection from Active Sensors or ECM;
- ECM degradation of Firm discrimination;
- ECCM mitigation of ECM without extending sensor reach;
- occlusion as a hard LOS gate.

It also formalizes that movement order is determined after pre-Movement Tactical Power commitments, and that a prepared STL overload may be stood down without refunding TP, spending overload fuel, adding Strain, or healing Strain.

## Acceptance commands

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-68\apply_checkpoint_68.ps1 -RepositoryOnly
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-68\apply_checkpoint_68.ps1
```

Deep Calibration remains optional:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-68\apply_checkpoint_68.ps1 -DeepCalibration
```

## Expected normal suite

- 8 stages;
- 0 Monte Carlo variants;
- 792 deterministic Sensor/EW sweep rows;
- PowerShell plus pinned .NET only; Python runtime dependencies are rejected before native work.

## Interpretation

Checkpoint 68 does not select a winning TL1 sensor envelope. Review the deterministic candidate summary and range sweep after acceptance. A later checkpoint may promote one candidate (or a refinement) into the numerical baseline and integrated tactical-combat runner.
