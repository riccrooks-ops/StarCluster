# Checkpoint 66a - Numerical Baseline CSV Contract Hotfix

> **66a hotfix scope:** Checkpoint 66 Concept v0.6e, overload mechanics, Strain rules, finite-map movement, fuel rules, study matrix, seeds, schema, baseline data, and Monte Carlo inputs are unchanged. The hotfix corrects the PowerShell checkpoint contract to read the authoritative numerical-baseline CSV column `parameter_id` instead of a nonexistent `key` property under StrictMode.

## Objective

Validate the Checkpoint 66 scripted bounded-overload tactics study while preserving the durable no-Python native-acceptance guard and all accepted Checkpoint 65b tactical-geometry foundations.

## Contract hotfix

- `tl1_core_combat_numerical_baseline_v0_2.csv` is authoritative and uses the columns `section, parameter_id, display_name, value, ...`.
- The CP66a contract validates that at least one row exists and that `parameter_id` and `value` columns are present before any row lookup.
- Numeric lookups use `parameter_id` and require exactly one matching row.
- A regression assertion rejects reintroduction of the invalid `$_.key` access.
- No Python runtime is permitted in the active native acceptance path.

## Repository-only validation

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-66a\apply_checkpoint_66a.ps1 -RepositoryOnly
```

RepositoryOnly must pass the native dependency guard, CP66a contract, complete repository manifest, PowerShell parser, checkpoint definitions, documentation status, and pinned SDK checks without executing Monte Carlo stages.

## Normal acceptance

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-66a\apply_checkpoint_66a.ps1
```

Expected normal suite: **8 stages / 80 Monte Carlo variants / 800,000 default trials**.

Primary review artifact:

`out/checkpoint-66a/tl1-scripted-overload-tactics/scripted-overload-tactics-review.csv`

No target win rate is a release gate. Review overload geometry, Tactical Power opportunity costs, fuel, Strain usage, movement-order effects, and contextual weapon-family behavior.

## Deep Calibration

Deep Calibration remains optional:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-66a\apply_checkpoint_66a.ps1 -DeepCalibration
```

Expected deep suite: **25 stages / 1,484 Monte Carlo variants / 14,840,000 default trials**. Do not run it merely to accept this hotfix unless the normal study exposes a historical dependency that warrants it.
