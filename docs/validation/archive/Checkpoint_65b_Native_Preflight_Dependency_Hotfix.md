# Checkpoint 65b - Native Preflight Dependency Hotfix

> **65b hotfix scope:** Checkpoint 65/65a Concept v0.6d, combat mechanics, finite-map movement, fuel rules, study matrix, seeds, schema, baseline, and Monte Carlo inputs are unchanged. Checkpoint 65b removes the accidental Python runtime dependency from the native acceptance path.

## Objective

Validate the accepted Checkpoint 65 finite radius-5 tactical-map movement foundation, authoritative tactical fuel accounting, bilateral operational sensing, and mirrored movement-order bounds while restoring the proven native acceptance architecture: PowerShell contract checks followed by the shared pinned-.NET checkpoint harness.

## Native dependency contract

- RepositoryOnly and normal acceptance require Windows PowerShell and the pinned .NET SDK used by the shared harness.
- The active Checkpoint 65b apply script must not invoke `python`, `python3`, `py`, or another external scripting runtime.
- Checkpoint-specific static assertions run in `test_checkpoint_65b_contract.ps1`.
- The shared harness performs full repository-manifest verification, PowerShell parser validation, checkpoint-definition validation, pinned SDK validation, warning-as-error build/tests, and runner-stage execution.

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
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-65b\apply_checkpoint_65b.ps1 -RepositoryOnly
```

RepositoryOnly must verify the complete manifest and checkpoint contracts, archive hygiene, active runbook identity, Concept/schema/baseline/study references, the exact 54-variant matrix, finite-map/fuel fields, historical Checkpoint 64 input preservation, and PowerShell parser contracts without requiring Python.

## Normal acceptance

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-65b\apply_checkpoint_65b.ps1
```

Expected normal suite: **8 stages / 54 Monte Carlo variants / 540,000 trials at the default 10,000 trials per variant**.

Native acceptance must use the pinned .NET SDK, clean warning-as-error build, unit tests, and all checkpoint stages. The bilateral tactical-geometry study must report zero failed gates and zero trial errors.

Primary review artifact:

`out/checkpoint-65b/tl1-bilateral-tactical-geometry/bilateral-geometry-movement-order-paired-review.csv`

## Deep Calibration

Deep Calibration remains optional:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-65b\apply_checkpoint_65b.ps1 -DeepCalibration
```

Expected deep suite: **24 stages / 1,404 Monte Carlo variants / 14,040,000 default trials**.

Do not run Deep Calibration merely to accept Checkpoint 65b unless the normal study exposes a dependency requiring a historical stochastic rerun.
