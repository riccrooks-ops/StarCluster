# Checkpoint 69a - Sensor/EW Candidate Compile Hotfix

## Scope

Checkpoint 69a is a compile-only hotfix for Checkpoint 69. The native Checkpoint 69 RepositoryOnly path completed successfully, including the no-Python dependency guard, manifest verification, PowerShell syntax checks, checkpoint contract, and repository validation. The warning-as-error .NET build then exposed two C# integration defects in `Tl1IntegratedTacticalCombatRunner.cs` before any simulation stage ran.

## Hotfix

- Replace the nullable `!v.BaseShieldRechargeEnabled` fixed-control check with an existing-default-preserving `!(v.BaseShieldRechargeEnabled ?? true)` comparison so the Boolean expression remains non-nullable.
- Add the missing method-local `Conditional(...)` helper inside `WriteTl1SensorEwCandidateCombatReview(...)`; the identically named helpers in neighboring report writers are intentionally local and are not visible across methods.
- Add checkpoint-contract regressions that reject the nullable negation form and require the candidate-review writer to define its own conditional-win helper.
- Preserve Concept v0.6h, Balanced-0/1/2 ranges, same-hex Sensor/EW semantics, all study JSON, seeds, 100-fuel/5-TP controls, validation tiers, and all release gates unchanged.

## Acceptance

From a clean extraction on native Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-69a\apply_checkpoint_69a.ps1 -RepositoryOnly
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-69a\apply_checkpoint_69a.ps1 -Jobs 24
```

Normal acceptance remains **9 stages / 72 Monte Carlo variants / 720,000 default trials / 924 deterministic Sensor/EW rows**. Deep Calibration is not required for this compile hotfix unless the normal run exposes an interacting regression.
