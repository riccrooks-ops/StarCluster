# Checkpoint 40 Validation Runbook

## Closure changes

Checkpoint 40 adds and measures six contracts:

1. The production minimal-tactics grid covers every ordered kinetic, energy, and missile pairing at Ranges 2, 3, 4, and 5.
2. Primary variants Hold range and disable movement, overload, withdrawal, EvM, Damage Control, and Protected Compartmentation while retaining automatic baseline systems.
3. Production values remain Kinetic DAM 4/APEN 0, Armor AP 0, TL1 ship Move 1, and TL1 missile Move 2.
4. A complete AP 1 grid runs as a diagnostic without changing production armor.
5. Range 4 one-factor controls cover Damage Control, EvM, Protected Compartmentation, Shield recharge, and missile-facing PDS.
6. Review bands and pacing flags are written as non-blocking evidence; implementation and coverage contracts remain blocking.

## Authoritative Windows command

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\tools\checkpoints\checkpoint-40\apply_checkpoint_40.ps1 `
  -Trials 10000 `
  -Jobs 24
```

Use `-RepositoryOnly` for repository and typed-definition checks without .NET execution. Use `-NoClean` only when intentionally preserving prior output.

## Blocking gates

1. `CHECKPOINT_40_SHA256SUMS.txt` validates every controlled repository file and rejects unexpected repository-owned files.
2. All PowerShell scripts parse under Windows PowerShell.
3. `tools/calibration/checkpoints/checkpoint-40.json` is valid and references existing executable, data, and documentation files.
4. .NET SDK 8.0.423 is selected.
5. `StarCluster.Calibration.sln` builds with warnings as errors.
6. All 800 expected compiled tests pass.
7. The 7 deterministic missile scenarios, 54 Phase A cases, and 36 Phase B cases pass.
8. Every configured ScenarioRunner stage exits successfully.
9. The three integrated study documents validate against `tl1_integrated_tactical_combat_schema_v0_2.json` and the current 131-row baseline hash.
10. The minimal-tactics study contains exactly 113 unique variants.
11. The AP 0 primary grid and AP 1 diagnostic grid each contain all 36 ordered pairing/range combinations.
12. Primary variants record no range change, EvM, Damage Control, Protected Compartmentation, or Disengagement.
13. Production primary variants use Kinetic DAM 4/APEN 0, Armor AP 0, ship Move 1, and missile Move 2.
14. Range 4 single-factor control counts are complete.
15. PDS-disabled controls record no PDS attempts or interceptions.
16. Missile travel remains within each missile's cumulative range budget.
17. Damage Control controls use the normal three-kit profile and record no invalid attempts.
18. Outcome accounting totals 100 percent and P90 remains within the 40-turn bound.
19. Attack, defense-layer, order-status, and missile telemetry are populated and internally consistent.
20. The permanent deterministic-corpus baseline-binding preflight remains active.

Balance review bands in `review-grid.csv` are deliberately non-blocking.

## Expected workload

The definition contains **16 ScenarioRunner stages**. At 10,000 trials, the retained and new Monte Carlo lanes contain **1,026 variants and 10,260,000 trials**. The expected compiled test total is **800**, and the ScenarioRunner self-test count remains **46**.

## Focused outputs

The new minimal-tactics lane writes to:

- `out/checkpoint-40/tl1-minimal-tactics-baseline`.

It contains `summary.json`, `variants.csv`, `gates.csv`, `review-grid.csv`, and `result.sha256.txt`.

The shared harness creates and incrementally updates:

- `out/checkpoint-40/acceptance-summary.json`;
- `out/checkpoint-40/acceptance-summary.txt`.

Preserve the complete `out/checkpoint-40` directory for assessment.

## Separate Godot integration lane

Routine calibration does not build `StarCluster.Game`. Run `tools/integration/run_full_solution_validation.ps1` at the next Godot/C# integration milestone.
