# Checkpoint 37 Validation Runbook

## Closure changes

Checkpoint 37 changes five contracts:

1. The provisional ordinary TL1 internal critical density is 33 1/3 percent.
2. Damage Control eligibility requires an actual legal repair target before any attempt or resource use.
3. The ordinary TL1 profile remains three Repair Kits; five kits exist only in tagged calibration fixtures.
4. The focused Damage Control study uses component-first and restrained Hull-repair doctrines with separate attempt, success, activation, and resource accounting.
5. Immobile Target accuracy uses a start-of-turn STL snapshot and cannot begin retroactively in the damage window that disables the drive.

## Authoritative Windows command

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\tools\checkpoints\checkpoint-37\apply_checkpoint_37.ps1 `
  -Trials 10000 `
  -Jobs 24
```

Use `-RepositoryOnly` for repository/definition checks without .NET execution and `-NoClean` only when intentionally preserving prior output.

## Blocking gates

1. `CHECKPOINT_37_SHA256SUMS.txt` validates every controlled repository file and rejects unexpected repository-owned files.
2. All PowerShell scripts parse under Windows PowerShell.
3. `tools/calibration/checkpoints/checkpoint-37.json` is valid and references existing executable, data, and documentation files.
4. .NET SDK 8.0.423 is selected.
5. `StarCluster.Calibration.sln` builds with warnings as errors.
6. All compiled tests pass, including pristine/no-target Damage Control checks, five-kit isolation, following-turn direct-fire and missile snapshots, and PDS independence.
7. Every configured ScenarioRunner stage exits successfully.
8. The 64-variant Damage Control study validates against `tl1_damage_control_calibration_schema_v0_1.json` and completes with no invalid target, threshold, reserve, resource, or trial errors.
9. Every non-None 33 1/3 percent doctrine lane reaches subsystem repair attempts.
10. The 8-variant pacing study validates against `tl1_combat_pacing_schema_v0_1.json` and completes with no same-turn Immobile bonus or invalid repair attempt.
11. Every 33 1/3 percent pacing lane observes at least one following-turn Immobile Target attack across the authoritative trial set.
12. Destruction, mission-kill, and unresolved percentages total 100 percent in each pacing variant.

README, Concept, workbook, source-text phrases, and console text are supporting evidence, not substitutes for executable gates.

## Expected workload

The definition contains 13 ScenarioRunner stages:

- accepted deterministic moving-missile scenarios;
- TL1 Phase A mechanics;
- TL1 Phase B direct fire;
- 29 kinetic variants;
- 31 energy variants;
- 48 no-counter weapon-matrix variants;
- 59 corrected PDS/interception variants;
- 171 layered defensive-system variants;
- 294 main-power/interception correction variants;
- 75 scripted relative-range variants;
- 64 Damage Control eligibility/doctrine variants;
- 8 integrated combat-pacing variants;
- ScenarioRunner self-tests.

At 10,000 trials, the retained Monte Carlo lanes contain 779 variants and 7,790,000 trials.

## Focused outputs

`out/checkpoint-37/tl1-damage-control-calibration` should contain:

- `summary.json`;
- `variants.csv`;
- `gates.csv`;
- `component-frequency.csv`;
- `repair-target-frequency.csv`;
- `hull-band.csv`;
- `result.sha256.txt`.

`out/checkpoint-37/tl1-combat-pacing` should contain:

- `summary.json`;
- `variants.csv`;
- `gates.csv`;
- `result.sha256.txt`.

The shared harness creates and incrementally updates:

- `out/checkpoint-37/acceptance-summary.json`;
- `out/checkpoint-37/acceptance-summary.txt`.

Preserve the complete `out/checkpoint-37` directory for assessment.

## Separate Godot integration lane

Routine calibration does not build `StarCluster.Game`. Run `tools/integration/run_full_solution_validation.ps1` at the next Godot/C# integration milestone.
