# Checkpoint 102 Validation Tiers

## Must-always-run native acceptance

CP102 changes executable construction/progression/runtime consumers, so native acceptance is intentionally stronger than CP101. It must run the pinned .NET SDK 8.0.423 warning-as-error build, the full xUnit suite, retained deterministic/mechanics stages, the native-accepted CP99 v0.8 TL1/TL2 preflight/generation regression, the CP102 v7 construction-envelope preflight, the CP102 v7 16-transition preflight/generation, the generated integrated-combat actual-consumer preflight, the 32-variant one-trial full-pipeline smoke, resource-semantics locks, and ScenarioRunner self-tests.

The user-facing acceptance sequence is itself a release gate: run `-RepositoryOnly`, then run the full checkpoint immediately in the **same clean extracted repository tree**. Generated `out/checkpoint-102/` artifacts must never become repository-owned inputs to the second invocation.

RepositoryOnly also includes a compile-surface guard for the changed `CrossTlProgressionEdge` consumer path. It derives the record's declared members and validates the `edge.<member>` accesses used by the cross-TL runner before the native build, so stale refactoring aliases such as object-style `LowerBuild`/`HigherBuild` access fail during preflight rather than at CS1061 compilation. This guard supplements, and never replaces, the pinned warning-as-error build.

Corrected replacement 2 also makes the **generated-study producer/consumer registration surface** a RepositoryOnly gate. The contract reads `generatedStudyId` directly from the authoritative v1.0 cross-TL producer document and requires the integrated tactical consumer to register that exact ID in required-variant dispatch, Adaptive Engage/operational Sensor-EW classification, generalized build legality, dedicated pre-run coverage validation, stateful build-level power/auxiliary handling, and safe output routing. This prevents a producer from successfully generating a structurally valid study that the next actual-consumer stage rejects as an unsupported study ID.

Corrected replacement 3 adds a **zero-cost weapon execution preflight** because CP102 is the first integrated consumer to make an ordinary direct-fire weapon legitimately cost 0 Tactical Power. RepositoryOnly verifies that the authoritative v1.0 `k3` option remains `powerCost: 0`, that direct-fire and missile attack paths share the zero-safe spend helper, and that the old raw `Spend(performance.TacticalPowerCost)` call is absent. The compiled CP102 generated-study preflight then executes the helper at 0 TP and 1 TP before any smoke trial. The ScenarioRunner self-test repeats the same invariant. Trial exceptions must retain variant/trial context plus the full exception and stack trace rather than being silently reduced to an aggregate counter.

## Pipeline smoke

The 32 variants are **smoke only**: 16 declared TL2->TL3 transitions times two movement-order geometries, one trial per variant. They prove deserialization, runtime binding, legal execution, and gate plumbing. Win rates, damage rates, survival, or other stochastic outcomes from these 32 trials are not balance evidence.

## Substantive Monte Carlo

**Not applicable.** CP102 implements the accepted CP101 TL3 table without changing its values. Broad TL1/TL2/TL3 population/permutation measurement belongs to a later checkpoint (provisionally CP103) after CP102 passes native acceptance.

## Deep Calibration

Not applicable. The deep alias uses the same bounded acceptance workload.
