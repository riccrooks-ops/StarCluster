# Checkpoint 69b - Sensor/EW Candidate Nullable-Control Compile Hotfix

## Scope

Checkpoint 69b is a compile-only successor hotfix for Checkpoint 69a. The native Checkpoint 69a RepositoryOnly path completed successfully. The warning-as-error .NET build also confirmed that CP69a fixed the missing candidate-review `Conditional(...)` helper, but compilation still stopped in `ValidateTl1SensorEwCandidateCombatCoverage(...)` because three nullable variant-control properties were used directly in a non-nullable `||` chain.

## Hotfix

- Replace direct use of nullable `EvasiveManeuversEnabled`, `PdsEnabled`, and `EscapeDisengagementEnabled` in the CP69 fixed-control validator with explicit nullable-safe value assertions: `!= false`, `!= true`, and `!= false` respectively.
- Keep the CP69a shield-recharge coalescing fix and candidate-review local `Conditional(...)` helper unchanged.
- Add checkpoint-contract regression checks that reject the raw nullable Boolean chain and require the explicit fixed-control assertions.
- Preserve Concept v0.6h, Balanced-0/1/2 ranges, same-hex Sensor/EW semantics, all study JSON, seeds, 100-fuel/5-TP controls, validation tiers, and release gates unchanged.

## Acceptance

From a clean extraction on native Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-69b\apply_checkpoint_69b.ps1 -RepositoryOnly
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-69b\apply_checkpoint_69b.ps1 -Jobs 24
```

Normal acceptance remains **9 stages / 72 Monte Carlo variants / 720,000 default trials / 924 deterministic Sensor/EW rows**. Deep Calibration is not required for this compile-only hotfix unless the normal run exposes an interacting regression.
