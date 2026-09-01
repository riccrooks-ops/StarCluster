# Checkpoint 66d - Policy Telemetry Classification Hotfix

## Scope

Checkpoint 66d is a release-gate integration hotfix for the Checkpoint 66 scripted bounded-overload study. The Checkpoint 66c native run proved that RepositoryOnly, the pinned .NET build, 821 engine-independent tests, deterministic scenarios, TL1 Phase A, TL1 Phase B, the construction envelope, and all 80 overload-study variants execute successfully. The overload study then reported exactly one failed gate: `policy-telemetry`.

The shared policy-telemetry gate historically distinguishes studies that intentionally mix PreferredRange and scripted/opponent-aware order sources from studies that use a single policy family. Checkpoint 66 uses `TrackAwareOpponentRange` throughout and therefore belongs with Checkpoint 65 and the other single-policy opponent-aware studies. Its new study ID was omitted from that shared classification.

## Hotfix

- Add `Tl1ScriptedOverloadTacticsStudyId` to both branches of the shared `policy-telemetry` single-policy classification.
- Preserve the requirement that every result records positive order requests.
- Preserve the 80-variant overload study, seeds, baseline v0.2, Concept v0.6e, overload/Strain mechanics, fuel, map geometry, and all other release gates unchanged.
- Add a cross-study integration contract that verifies CP66 is registered in required-variant dispatch, pre-run validation, shared policy telemetry, study-specific gates, and review-output routing.
- Retain all earlier CP66 hotfix guards: no Python native dependency, numerical-baseline `parameter_id/value` schema, C# gate scope, and catalog/baseline binding.

## Acceptance

From a clean full-repository extraction:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-66d\apply_checkpoint_66d.ps1 -RepositoryOnly
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-66d\apply_checkpoint_66d.ps1
```

Normal acceptance remains 8 stages / 80 Monte Carlo variants / 800,000 trials at the default 10,000 trials per variant. Deep Calibration is not required for this hotfix.
