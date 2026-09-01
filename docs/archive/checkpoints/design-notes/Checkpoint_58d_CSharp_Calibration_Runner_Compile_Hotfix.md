# Checkpoint 58d - C# Calibration Runner Compile Hotfix

## Purpose

Checkpoint 58d is a release-only compile hotfix for Checkpoint 58c. Native Windows repository-only validation for 58c passed, but the full warnings-as-errors build exposed four C# diagnostics in `Tl1IntegratedTacticalCombatRunner.cs` before any Monte Carlo stage could begin.

The first pair (`CS1061`) came from the Checkpoint 58 single-main gate reading `SideASecondaryFamily` and `SideBSecondaryFamily` from `Tl1IntegratedTacticalCombatVariantSummary`. Those members are not part of the summary record; the authoritative secondary-family values live on each `Tl1IntegratedTacticalCombatVariantDocument`. Checkpoint 58d therefore evaluates the gate against `study.Variants`.

The second pair (`CS8602`) came from calling `StartsWith` directly on nullable `ProfileLabel` values in the powered-defense power-pairing matrix shape check. Checkpoint 58d uses null-conditional `?.StartsWith(...) == true` predicates, preserving the exact expected counts while satisfying nullable analysis.

No ScenarioRunner study JSON, Monte Carlo variant, simulation parameter, weapon/defense value, Concept v0.5e content, workbook v0.39 value, or Checkpoint 58 gameplay decision changes in this hotfix. The Checkpoint 58a `powerCost` correction, 58b nested-ZIP manifest correction, and 58c PowerShell regex/format correction are retained.

## Repository-only gate

From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-58d\apply_checkpoint_58d.ps1 -RepositoryOnly
```

Expected sequence:

1. Frozen Checkpoint 57a and Checkpoint 58 architecture contracts pass.
2. Checkpoint 58d regression assertions confirm the single-main gate reads `study.Variants`, rejects the stale summary-field expression, and uses nullable-safe powered-defense label predicates.
3. The complete Checkpoint 58d repository manifest and all PowerShell scripts validate.

## Full build and workload

Run the full checkpoint with the normal defaults:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-58d\apply_checkpoint_58d.ps1
```

The build must complete with zero warnings and zero errors before calibration stages run. The workload remains 56 runner stages, 14,746 Monte Carlo variants, and 147.46 million trials at 10,000 trials per variant with 24 workers. Results are written to `out/checkpoint-58d`.
