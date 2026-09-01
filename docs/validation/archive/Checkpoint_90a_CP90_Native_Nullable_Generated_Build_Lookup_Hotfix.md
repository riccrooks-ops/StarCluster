# Checkpoint 90a - CP90 Native Nullable Generated-Build Lookup Hotfix

## Purpose

Checkpoint 90a is a native-build hotfix for the unchanged Checkpoint 90 generalized legal-build/cross-TL screening study. The first CP90 native normal-acceptance build failed under nullable warnings-as-errors with CS8600 at the two generated-build `TryGetValue` lookups in `Tl1IntegratedTacticalCombatRunner.cs`.

CP90a changes only the generated-build validation lookup so dictionary misses/null values are represented as nullable outputs and rejected explicitly before the build objects are dereferenced. It does **not** change the 22,592-build legal envelope, the 432-variant generated screen, technology values, runtime combat behavior, study data, Concept, Technology Matrix, standing permutation architecture, or AI doctrine.

The superseded CP90 validation runbook is archived at `docs/validation/archive/Checkpoint_90_Generalized_Legal_Build_And_Cross_TL_Stratified_Screening.md`.

## Hotfix contract

The native contract must verify that:

1. the unsafe non-nullable `out Tl1IntegratedShipBuildDocument buildA/buildB` lookup pattern is absent;
2. Side-A and Side-B generated build lookups use nullable outputs and explicitly reject null/missing builds;
3. CP90 generator, build-document schema, self-tests, study JSON, Concept v0.6z, Technology Matrix, Component Catalog, and standing suite v0.9 remain byte-identical to the generated CP90 repository;
4. accepted CP89 provenance/frozen-content checks still pass;
5. the full CP90 workload and all study gates remain unchanged.

## Native acceptance

Run repository validation first:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-90a\apply_checkpoint_90a.ps1 -RepositoryOnly
```

Then run normal acceptance:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-90a\apply_checkpoint_90a.ps1 -Jobs 24
```

Expected normal workload remains 13 runner stages, 56 ScenarioRunner self-tests, 432 one-trial smoke executions, and 432 substantive variants / 4,320,000 substantive trials at the default 10,000 trials per variant.

Deep Calibration is not recommended initially; the CP90 experimental scope is unchanged.
