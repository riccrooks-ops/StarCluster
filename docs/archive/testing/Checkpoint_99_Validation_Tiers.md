# Checkpoint 99 Validation Tiers

## Must always run

1. Native dependency/interface precheck and CP99 repository contract.
2. Manifest and PowerShell syntax verification.
3. Pinned SDK 8.0.423 and warning-as-error build.
4. All xUnit tests (expected 876).
5. Deterministic missile, TL1 Phase A/B, construction, Sensor/EW, and resource-semantic regressions.
6. Accepted CP96 1,440-variant generated one-trial regression.
7. Accepted CP97 36-variant Adaptive Engage one-trial regression.
8. Accepted CP98 v0.7 generation/consumer 960-variant one-trial regression.
9. CP99 v0.8 mandatory-Sensor exact-edge preflight and generation: 11,776 legal builds, 37,184 edges, 181 strata, 362 logical pairs, 724 variants.
10. CP99 724-variant actual-consumer preflight.
11. CP99 one-trial-per-variant full-pipeline smoke.
12. CP99 bounded 724 x 250 = **181,000-trial** substantive exact-edge screen.
13. ScenarioRunner self-tests (expected 63).

Default total stochastic executions are **184,160**.

## Deep calibration

Deep Calibration is **not applicable** to CP99. The alias intentionally resolves to the same bounded workload. Increase trials only after reviewing the exact-edge marginal results and identifying a concrete uncertainty requiring tighter error bars.

## Blocking boundaries

Repository/build/test/schema/catalog/dispatch/referential-integrity failures are blocking. Mandatory Sensor legality, exact envelope/lattice/stratum/sample counts, declared one-axis/delta bindings, mirrored geometry, safe-Strain request suppression, and actual-consumer routing are deterministic gates. Win rates, marginal upgrade strength, mover-order gaps, unresolved tails, and technology-promotion decisions remain review evidence rather than automatic gates.
