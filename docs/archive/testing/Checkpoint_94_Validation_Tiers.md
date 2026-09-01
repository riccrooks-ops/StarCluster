# Checkpoint 94 Validation Tiers

Checkpoint 94 is a **sampling-quality and analysis-architecture** checkpoint. It does not promote gameplay values. Native Windows acceptance is authoritative.

## Must always run

The normal CP94 wrapper runs these release gates in order:

1. native dependency and proven wrapper-interface precheck;
2. CP94 repository/frozen-baseline contract;
3. repository manifest and PowerShell parser validation;
4. pinned .NET SDK 8.0.423 check;
5. warning-as-error clean build;
6. all engine-independent C# tests;
7. accepted deterministic moving-missile scenarios;
8. TL1 Phase A and Phase B deterministic mechanics corpora;
9. TL1 Installation Space deterministic envelope;
10. TL1 Sensor/EW deterministic foundation;
11. CP94 22,592-build v0.5 permutation generator preflight;
12. CP94 full generation of the 1,440-variant study;
13. generated-study actual-consumer preflight;
14. 1 trial per each of the 1,440 generated variants through the full consumer pipeline;
15. substantive 1,440-variant cross-TL screen at the configured trial count;
16. deterministic resource-endurance and Checkpoint-53 resource-semantics locks; and
17. **58 expected ScenarioRunner self-tests**.

The checkpoint definition exposes **13 configured runner stages** because several deterministic/build checks are harness-level steps rather than separate runner stages.

## CP94 bounded substantive workload

The default is **1,500 trials per variant** across **1,440 variants**:

- substantive trials: **2,160,000**;
- one-trial smoke executions: **1,440**;
- total trial executions including smoke: **2,161,440**.

The study remains review-only for balance outcomes. Blocking gates protect deterministic invariants, consumer integration, telemetry consistency, population-weight accounting, ready-range metadata, retained side/family/context activity cohorts after ready geometry is actually reached, and a substantive case where required mutual ready geometry is reached yet a matched pair still produces zero family-appropriate main-weapon actions on both sides.

A dynamic zero-action pairing that never reaches its required mutual ready range is surfaced as a movement/doctrine diagnostic and is not silently treated as an illegal build or as the same failure mode. A pair where only one side acts after mutual ready geometry is reached is reported separately as `ready_geometry_reached_but_one_side_inactive` and remains visible to the side/family/context activity guard.

## Sampling-quality release conditions

The v0.5 generator must deterministically prove:

- 82,944 raw combinations and 22,592 legal builds;
- 4,672 exact-fill / 11,328 near-fill / 6,592 underfilled builds;
- 96 populated primary cells;
- exactly 192 statistical unordered base pairs under the bounded adaptive allocation;
- at least one and at most five statistical representatives per cell;
- 384 mirrored statistical orientations;
- exactly 24 diversity unordered base pairs in the 12 highest-population cells;
- 48 mirrored diversity orientations with zero inference weight;
- 48 retained named logical pairings;
- 480 total logical pairings and 1,440 generated variants;
- statistical representative weights recovering the complete 255,187,936 unordered-distinct population;
- exact ready-range/class consistency; and
- valid weapon-family/information-control secondary-coverage metadata.

The actual combat consumer must preserve side-specific telemetry, individual observed-engagement diagnosis, raw/population-weighted all-legal vs structurally-ready vs observed-active reports, and mover-order-neutral/initiative-sensitivity reports.

## Deep Calibration

**Deep Calibration is not applicable to Checkpoint 94.** `-DeepCalibration` is retained only as a compatibility alias for the same bounded workload. Larger samples and/or higher trials should be considered only after CP94 is native-clean and its sampling-quality reports are reviewed.

## Proven invocation contract

The checkpoint wrapper must continue to invoke the common harness by **direct named-parameter invocation**:

```powershell
& $harness -CheckpointDefinition $definition -Trials $Trials -Jobs $Jobs -RepositoryOnly:$RepositoryOnly -NoClean:$NoClean
```

Array splatting or positional forwarding is not an accepted replacement for this proven interface without deliberate validation.
