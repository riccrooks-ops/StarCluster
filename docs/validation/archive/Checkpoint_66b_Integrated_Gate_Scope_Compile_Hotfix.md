# Checkpoint 66b - Integrated Gate Scope Compile Hotfix

> **66b hotfix scope:** Checkpoint 66/66a Concept v0.6e, overload mechanics, Strain rules, finite-map movement, fuel rules, study matrix, seeds, schema, baseline data, and Monte Carlo inputs are unchanged. The hotfix moves the Checkpoint 66 result-dependent release gates into `BuildGates(...)`, the method that owns `results`, `gates`, and `tolerance`, instead of leaving them in the pre-run `Validate(...)` method.

## Failure corrected

Checkpoint 66a RepositoryOnly passed, but the native warning-as-error build failed with 26 `CS0103` errors because the CP66 gate block referenced `gates`, `results`, and `tolerance` outside their scope. Checkpoint 66b makes no balance or simulation change; it corrects that source placement.

## Regression contract

The CP66b PowerShell contract now verifies that:

- the `tl1-c66-variant-coverage` gate marker occurs inside the source span of `BuildGates(...)`;
- that marker occurs after the `BuildGates(...)` declaration and before the next private static method;
- no CP66 `gates.Add(...)` block remains in `Validate(...)`;
- the existing numerical-baseline `parameter_id` schema guard and no-Python native dependency guard remain active.

## Repository-only validation

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-66b\apply_checkpoint_66b.ps1 -RepositoryOnly
```

## Normal acceptance

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-66b\apply_checkpoint_66b.ps1
```

Expected normal suite: **8 stages / 80 Monte Carlo variants / 800,000 default trials**.

Primary review artifact:

`out/checkpoint-66b/tl1-scripted-overload-tactics/scripted-overload-tactics-review.csv`

## Deep Calibration

Deep Calibration remains optional and is not required merely to accept this compile-scope hotfix.
