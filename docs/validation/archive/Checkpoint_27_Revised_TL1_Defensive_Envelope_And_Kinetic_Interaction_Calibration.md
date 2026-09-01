# Checkpoint 27 Validation Runbook

## Acceptance sequence

1. Verify the complete repository manifest and PowerShell parser contracts.
2. Verify Concept v0.3y, workbook v0.7, 126-value baseline, all Phase A/B hash links, the 29-variant kinetic calibration study, and focused test source.
3. Confirm Godot is closed and .NET SDK 8.0.423 is selected.
4. Clean-build with warnings as errors.
5. Run the complete engine-independent suite; expected total: 597.
6. Run seven accepted moving-missile scenarios.
7. Run 12 Phase A documents / 54 cases.
8. Run seven Phase B documents / 36 cases.
9. Run the kinetic calibration at 10,000 trials per variant with up to 24 workers.
10. Run 46 ScenarioRunner self-tests.

The kinetic calibration must report 29 variants, all symmetry gates passing, and write `summary.json`, `variants.csv`, and `gates.csv`. Outputs must include Wilson 95% outcome intervals and per-layer final-state metrics. A passing run proves deterministic execution and unbiased pairing; numerical balance remains subject to review of the produced distributions.

## Checkpoint 27c Phase A fixture, compiler, and validator hotfix

The application validator is now idempotent across the documented two-command workflow. After `-RepositoryContractOnly` normalizes the stale Checkpoint 26 active runbook, the subsequent full run validates the archived historical copy rather than requiring the removed fixture. The runbook-normalization self-test also uses Checkpoint 27 as its expected active document.
