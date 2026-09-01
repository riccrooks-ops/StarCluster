# Checkpoint 41 Validation Runbook

## Closure changes

Checkpoint 41 accepts the Checkpoint 40 TL1 minimal-tactics baseline and adds a deterministic analytical screen for TL2 candidate derivation. It does not promote TL2 production values.

The checkpoint establishes these contracts:

1. Player technology uses piecewise low (TL1-3), medium (TL4-6), and high (TL7-9) bands with refinement and culmination within each band and stronger qualitative breakpoints at TL4 and TL7.
2. Scaling remains a vector of packet, accuracy, range, cadence, power, ammunition, movement, guidance, PDS, Shield, Armor, and Hull relationships; there is no universal combat score.
3. Exact packet transitions use the authoritative `LayeredDamageResolver` rather than a parallel simplified damage implementation.
4. The analytical duration model is calibrated to twelve accepted Checkpoint 40 TL1 mirror rows at Ranges 2-5.
5. A comparable complete TL2 package uses about 66.7 percent victory probability against a complete TL1 package as an initial target, with 60-72 percent as an exploratory band.
6. Three coherent candidate-only TL2 packages are screened: conservative refinement, balanced derived, and specialization-forward.
7. TL2 candidates retain Armor AP 0, ship Move 2, missile Move 3, and at least one point of Tactical Power margin.
8. AP, Shield Armor, APEN, SPEN, reaction capacity, and special modes remain deliberate milestone values rather than automatic per-TL increments.
9. Stable component IDs remain authoritative, but display names may be revised when the tested mechanical promise or tier placement does not fit.
10. The permanent prohibition against copied mutable production values remains active; accepted TL1 evidence is baseline-hash-bound and candidate values remain explicit study inputs.

## Authoritative Windows command

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\tools\checkpoints\checkpoint-41\apply_checkpoint_41.ps1 `
  -Trials 10000 `
  -Jobs 24
```

Use `-RepositoryOnly` for repository and typed-definition checks without .NET execution. Use `-NoClean` only when intentionally preserving prior output.

## Blocking gates

1. `CHECKPOINT_41_SHA256SUMS.txt` validates every controlled repository file and rejects unexpected repository-owned files.
2. All PowerShell scripts parse under Windows PowerShell.
3. `tools/calibration/checkpoints/checkpoint-41.json` is valid and references existing executable, data, and documentation files.
4. .NET SDK 8.0.423 is selected.
5. `StarCluster.Calibration.sln` builds with warnings as errors.
6. All 800 expected compiled tests pass.
7. The 7 deterministic missile scenarios, 54 Phase A cases, and 36 Phase B cases pass.
8. Every retained Checkpoint 40 ScenarioRunner stage exits successfully.
9. The TL2 scaling study validates against `combat_scaling_and_tl2_candidate_schema_v0_1.json` and the authoritative 131-row TL1 baseline hash.
10. The calibration evidence contains exactly twelve accepted TL1 mirror rows covering kinetic, energy, and missile at Ranges 2-5.
11. Every finite calibrated TL1 mirror estimate is within 12 percent of the accepted Checkpoint 40 result; the kinetic Range 5 no-fire control remains infinite/unresolved.
12. Exactly three TL2 candidates are screened.
13. Every TL2 candidate uses ship Move 2, missile Move 3, Armor AP 0, and a nonnegative Shield Armor value.
14. Every candidate has at least one point of Tactical Power margin under its standard analytical commitment.
15. The balanced-derived candidate remains inside the 60-72 percent full-package review band and within two percentage points of the 66.7 percent nominal target.
16. Candidate naming concerns remain explicit rather than silently changing stable IDs or promoting misleading display names.
17. Packet traces, protection breakpoints, same-TL grids, cross-TL grids, candidate reviews, and gates are written with a deterministic result hash.
18. The permanent deterministic-corpus baseline-binding preflight remains active.

## Expected workload

The definition contains **17 ScenarioRunner stages**. The new stage is deterministic and adds no Monte Carlo trials. At 10,000 trials, the retained Monte Carlo lanes remain **1,026 variants and 10,260,000 trials**. The expected compiled test total is **800**, and the ScenarioRunner self-test count remains **46**.

## Focused outputs

The new analytical stage writes to:

- `out/checkpoint-41/combat-scaling-tl2`.

Expected files:

- `summary.json`;
- `profiles.csv`;
- `tl1-calibration.csv`;
- `packet-traces.csv`;
- `protection-breakpoints.csv`;
- `same-tl-range-grid.csv`;
- `cross-tl-range-grid.csv`;
- `candidate-review.csv`;
- `gates.csv`;
- `result.sha256.txt`.

The shared harness creates and incrementally updates:

- `out/checkpoint-41/acceptance-summary.json`;
- `out/checkpoint-41/acceptance-summary.txt`.

Preserve the complete `out/checkpoint-41` directory for assessment.

## Interpretation boundary

Analytical passage is a screening result, not TL2 balance acceptance. The balanced-derived package is only the first recommended Monte Carlo candidate. No TL2 candidate value becomes production data until isolated subsystem studies, complete TL2 mirrors and cross-family fights, and complete TL2-versus-TL1 trials are reviewed.

## Separate Godot integration lane

Routine calibration does not build `StarCluster.Game`. Run `tools/integration/run_full_solution_validation.ps1` at the next Godot/C# integration milestone.
