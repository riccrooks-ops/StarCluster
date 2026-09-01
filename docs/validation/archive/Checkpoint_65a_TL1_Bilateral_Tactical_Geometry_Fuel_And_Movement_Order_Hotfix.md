# Checkpoint 65a - TL1 Bilateral Tactical Geometry, Fuel, and Movement Order Hotfix


> **65a hotfix scope:** Checkpoint 65 mechanics, Concept v0.6d, study inputs, seeds, and combat code are unchanged. The hotfix corrects the release apply script so it does not read PowerShell `$LASTEXITCODE` before any native process has initialized that variable. The 65a static preflight contains a regression assertion for this exact StrictMode failure.
## Objective

Validate the finite radius-5 tactical-map movement foundation, authoritative tactical fuel accounting, bilateral operational sensing, and mirrored movement-order bounds without changing accepted TL1 component balance or implementing the full tactical-response AI.

## Authoritative rules

- Concept: `docs/Star_Cluster_Game_Concept_v0.6d.docx`.
- Tactical map: radius 5 / diameter 11 / 91 cells.
- Tactical fuel: 200 starting fuel; 2 fuel per ship hex actually traversed; EvM +1 fuel per turn.
- Existing Tactical Power commitment windows and overload/Strain rules remain authoritative.
- Movement order does not reopen the pre-Movement Tactical Power window.
- Ordinary post-Movement attacks use final positions; closest approach/path history is not a normal attack coordinate.
- No target win rate is a release gate.

## Repository-only validation

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-65a\apply_checkpoint_65a.ps1 -RepositoryOnly
```

RepositoryOnly must verify the complete manifest and checkpoint contracts, archive hygiene, active runbook identity, Concept/schema/baseline/study references, exact 54-variant study matrix, finite-map/fuel fields, historical Checkpoint 64 input preservation, PowerShell parser contracts, and static C#/CSV shape checks.

## Normal acceptance

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-65a\apply_checkpoint_65a.ps1
```

Expected normal suite: **8 stages / 54 Monte Carlo variants / 540,000 trials at the default 10,000 trials per variant**.

Native acceptance must use the pinned .NET SDK, clean warning-as-error build, unit tests, and all checkpoint stages. The TL1 bilateral tactical-geometry study must report zero failed gates and zero trial errors.

Primary review artifact:

`out/checkpoint-65a/tl1-bilateral-tactical-geometry/bilateral-geometry-movement-order-paired-review.csv`

Review movement-order bounds, final/closest range, fuel, boundary turns, bilateral track behavior, missile range exhaustion, and downstream outcomes. Do not convert the evidence into predetermined balance targets.

## Deep Calibration

Deep Calibration is optional for this checkpoint:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-65a\apply_checkpoint_65a.ps1 -DeepCalibration
```

Expected deep suite: **24 stages / 1,404 Monte Carlo variants / 14,040,000 default trials**.

Do not run Deep Calibration merely to accept Checkpoint 65a unless the normal study exposes a dependency requiring a historical stochastic rerun.
