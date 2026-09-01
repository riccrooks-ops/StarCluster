# Checkpoint 38 Validation Runbook

## Closure changes

Checkpoint 38 changes six contracts:

1. Tactical range decisions come through `ITacticalOrderPolicy` and an immutable decision context.
2. Scripted scenarios and the first preferred-range AI policy use the same order interface.
3. `RangeOrderResolver` resolves both ships simultaneously from actual STL condition and may throttle movement to a desired separation.
4. Maintain Preferred Range matches the opponent's actual throttled movement and does not oscillate by applying full thrust unnecessarily.
5. Missile position and cumulative range become independent of the launcher after launch.
6. The accepted internal-critical, Protected, Damage Control, component-condition, PDS, and Immobile Target rules are applied to integrated cross-family and dynamic-range fights.

## Authoritative Windows command

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\tools\checkpoints\checkpoint-38\apply_checkpoint_38.ps1 `
  -Trials 10000 `
  -Jobs 24
```

Use `-RepositoryOnly` for repository/definition checks without .NET execution and `-NoClean` only when intentionally preserving prior output.

## Blocking gates

1. `CHECKPOINT_38_SHA256SUMS.txt` validates every controlled repository file and rejects unexpected repository-owned files.
2. All PowerShell scripts parse under Windows PowerShell.
3. `tools/calibration/checkpoints/checkpoint-38.json` is valid and references existing executable, data, and documentation files.
4. .NET SDK 8.0.423 is selected.
5. `StarCluster.Calibration.sln` builds with warnings as errors.
6. All 780 compiled tests pass, including policy decisions, desired-range throttling, simultaneous pursuit, degraded/disabled STL, anti-crossing, and Maintain Preferred Range counter-movement.
7. Every configured ScenarioRunner stage exits successfully.
8. The 90-variant integrated study validates against `tl1_integrated_tactical_combat_schema_v0_1.json`.
9. Hold scenarios record no range change; dynamic scenarios record legal range changes.
10. At least one damaged drive coerces a requested movement order to Hold.
11. No same-turn Immobile Target modifier appears after a drive is disabled during the current damage window.
12. No missile exceeds six cumulative travel hexes and target movement never refunds spent range.
13. Integrated Damage Control uses the normal three-kit profile and records no invalid repair attempt.
14. Side A, Side B, mutual, and unresolved percentages total 100 percent for every variant.

Documentation is supporting evidence, not a substitute for executable gates.

## Expected workload

The definition contains 14 ScenarioRunner stages. At 10,000 trials, the retained Monte Carlo lanes contain **869 variants and 8,690,000 trials**. The new integrated stage contributes 90 variants and 900,000 trials. The expected compiled test total is **780**, and the ScenarioRunner self-test count remains **46**.

## Focused outputs

`out/checkpoint-38/tl1-integrated-tactical-combat` should contain:

- `summary.json`;
- `variants.csv`;
- `gates.csv`;
- `result.sha256.txt`.

The shared harness creates and incrementally updates:

- `out/checkpoint-38/acceptance-summary.json`;
- `out/checkpoint-38/acceptance-summary.txt`.

Preserve the complete `out/checkpoint-38` directory for assessment.

## Separate Godot integration lane

Routine calibration does not build `StarCluster.Game`. Run `tools/integration/run_full_solution_validation.ps1` at the next Godot/C# integration milestone.
