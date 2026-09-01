# Checkpoint 39 Validation Runbook

## Closure changes

Checkpoint 39 changes and measures seven contracts:

1. Ship STL Move equals STL Drive TL; Missile Move equals Missile Drive TL plus 1.
2. TL1 production movement is ship 1 / missile 2, with Godot 3/2 and legacy 4/1 retained only as diagnostic controls.
3. STL overload adds the drive's listed Move and carries power, fuel, Strain, forced-roll, and condition-step consequences.
4. The provisional production Kinetic Cannon is DAM 4/APEN 0; DAM 3, DAM 5, and DAM 4/APEN 1 remain paired comparison arms against an AP 1 diagnostic armor fixture while production armor remains AP 0.
5. Successful withdrawal/disengagement requires an explicit withdrawal objective; its active escape clock is not preempted by the pursuer mobility-mission-kill classification.
6. Integrated Shield recharge uses the shared service and a damageable Shield Generator.
7. Attack, defense-layer, recharge, order-status, and engagement-termination telemetry are reported separately.

## Authoritative Windows command

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\tools\checkpoints\checkpoint-39\apply_checkpoint_39.ps1 `
  -Trials 10000 `
  -Jobs 24
```

Use `-RepositoryOnly` for repository and typed-definition checks without .NET execution. Use `-NoClean` only when intentionally preserving prior output.

## Blocking gates

1. `CHECKPOINT_39_SHA256SUMS.txt` validates every controlled repository file and rejects unexpected repository-owned files.
2. All PowerShell scripts parse under Windows PowerShell.
3. `tools/calibration/checkpoints/checkpoint-39.json` is valid and references existing executable, data, and documentation files.
4. .NET SDK 8.0.423 is selected.
5. `StarCluster.Calibration.sln` builds with warnings as errors.
6. All expected compiled tests pass, including TL movement laws, overload outcomes, range-order statuses, and retained combat contracts.
7. Every configured ScenarioRunner stage exits successfully.
8. Both integrated study documents validate against `tl1_integrated_tactical_combat_schema_v0_2.json` and the current 131-row baseline hash.
9. The 90-variant production study retains all ordered family pairings and movement modes.
10. The 44-variant diagnostic study contains production 1/2, Godot 3/2, legacy 4/1, and overload-equivalent 2/2 profiles.
11. DAM 3/APEN 0, DAM 4/APEN 0, DAM 5/APEN 0, and DAM 4/APEN 1 arms all run under paired seeds.
12. Shield recharge and EvM on/off controls all run.
13. Integrated missile launch power is 0 TP, magazine capacity is 25 Flights per missile ship, and no missile exceeds its variant-specific cumulative travel budget.
14. No same-turn Immobile Target bonus appears after current-window STL damage.
15. Damage Control uses the normal three-kit profile and records no invalid attempt.
16. At least one pursuit lane records successful disengagement.
17. Non-pursuit variants and disengagement-disabled controls record zero Disengagement outcomes.
18. Attack-layer and requested-versus-resolved order telemetry are non-empty and internally consistent.
19. Side A, Side B, mutual, and unresolved percentages total 100 percent for every variant.

Documentation is supporting evidence, not a substitute for executable gates.

## Expected workload

The definition contains **15 ScenarioRunner stages**. At 10,000 trials, the retained and new Monte Carlo lanes contain **913 variants and 9,130,000 trials**. The expected compiled test total is **800**, and the ScenarioRunner self-test count remains **46**.

## Focused outputs

The production integrated lane writes to:

- `out/checkpoint-39/tl1-integrated-tactical-combat`.

The new diagnostic lane writes to:

- `out/checkpoint-39/tl1-movement-kinetic-pacing-diagnostics`.

Each contains `summary.json`, `variants.csv`, `gates.csv`, and `result.sha256.txt`.

The shared harness creates and incrementally updates:

- `out/checkpoint-39/acceptance-summary.json`;
- `out/checkpoint-39/acceptance-summary.txt`.

Preserve the complete `out/checkpoint-39` directory for assessment.

## Separate Godot integration lane

Routine calibration does not build `StarCluster.Game`. Run `tools/integration/run_full_solution_validation.ps1` at the next Godot/C# integration milestone.
