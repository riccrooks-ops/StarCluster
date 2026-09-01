# Checkpoint 36b Validation Runbook

## Closure changes

Checkpoint 36b changes two mechanical contracts:

1. Protected Compartmentation preserves the paired ordinary seeded finite-track X count. A terminal protected X swaps with the adjacent H when possible.
2. Disabled or Destroyed STL creates Immobile Target, adding +10 percentage points to incoming ship-target attack accuracy beginning next turn. It does not affect detection, tracks, or PDS interception.

Checkpoint 36a's precision-critical test correction remains included.

## Authoritative Windows command

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\tools\checkpoints\checkpoint-36\apply_checkpoint_36.ps1 `
  -Trials 10000 `
  -Jobs 24
```

Use `-RepositoryOnly` for repository/definition checks without .NET execution and `-NoClean` only when intentionally preserving prior output.

## Blocking gates

1. `CHECKPOINT_36_SHA256SUMS.txt` validates every controlled repository file and rejects unexpected repository-owned files.
2. All PowerShell scripts parse under Windows PowerShell.
3. `tools/calibration/checkpoints/checkpoint-36.json` is valid and references existing executable, data, and documentation files.
4. .NET SDK 8.0.423 is selected.
5. `StarCluster.Calibration.sln` builds with warnings as errors.
6. `StarCluster.Tests` passes; the expected compiled total is 748.
7. Every configured ScenarioRunner stage exits successfully.
8. The internal-damage study validates against `tl1_internal_damage_calibration_schema_v0_1.json`; its 80-variant typed preflight and mechanical gates pass.
9. Protected Compartmentation preflight proves paired finite X-count equality over five densities and 1,024 seeds, with a terminal H on every 12-Hull protected track.
10. The calibration gate `protected-preserves-finite-x-count` passes for every no-Damage-Control ordinary/protected pair.

README, Concept, workbook, source-text phrases, and console-text phrases are documentation evidence, not substitutes for executable mechanical gates.

## Expected workload

The definition contains 12 ScenarioRunner stages:

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
- 80 internal-damage/component-condition/Damage-Control variants;
- 46 ScenarioRunner self-tests.

At 10,000 trials, the retained Monte Carlo lanes contain 787 variants and 7,870,000 trials.

## Acceptance summaries

The shared harness creates and incrementally updates:

- `out/checkpoint-36/acceptance-summary.json`
- `out/checkpoint-36/acceptance-summary.txt`

Preserve the complete `out/checkpoint-36` directory for assessment.

## Focused study outputs

`out/checkpoint-36/tl1-internal-damage-calibration` should contain:

- `summary.json`;
- `variants.csv`;
- `gates.csv`;
- `component-frequency.csv`;
- `hull-band.csv`;
- `result.sha256.txt`.

## Separate Godot integration lane

Routine calibration does not build `StarCluster.Game`. Run `tools/integration/run_full_solution_validation.ps1` at the next Godot/C# integration milestone.
