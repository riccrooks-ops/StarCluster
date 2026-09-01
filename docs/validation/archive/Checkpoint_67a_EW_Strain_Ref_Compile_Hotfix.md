# Checkpoint 67a - EW Strain Ref Compile Hotfix

## Scope

Checkpoint 67a is a compile-only hotfix for Checkpoint 67. The native Checkpoint 67 run proved RepositoryOnly, the no-Python dependency guard, repository manifest/parser validation, and the pinned SDK startup all work. The warning-as-error build then reported CS0206 at the new bilateral ECM/ECCM allocation call sites because ordinary `IntegratedSide.EcmStrain` and `IntegratedSide.EccmStrain` properties were passed directly as `ref` arguments.

## Hotfix

- Copy each EW Strain property into a local variable before calling the existing `AllocateEwSystem(..., ref strain, ...)` helper.
- Assign the mutated local Strain value back to the property immediately after the helper returns.
- Add a checkpoint-contract regression that rejects direct `ref`/`out` use of those properties and requires the local-copy/assign-back pattern.
- Preserve Concept v0.6f, the 100-fuel baseline, the 60-variant study, seeds, overload/EW mechanics, TP windows, Strain values, and all study/release gates unchanged.

## Acceptance

From a clean extraction:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-67a\apply_checkpoint_67a.ps1 -RepositoryOnly
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-67a\apply_checkpoint_67a.ps1
```

Normal acceptance remains 8 stages / 60 Monte Carlo variants / 600,000 trials. Deep Calibration is not required for this compile hotfix.
