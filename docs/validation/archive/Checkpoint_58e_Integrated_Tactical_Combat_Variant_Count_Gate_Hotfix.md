# Checkpoint 58e - Integrated Tactical Combat Variant-Count Gate Hotfix

## Purpose

Checkpoint 58e is a release-only validation hotfix for Checkpoint 58d. The native Windows 58d run passed repository validation, the pinned .NET SDK gate, and the warnings-as-errors build, then progressed through stage 54. At stage 55, `tl4-itc04-single-main-axis-screening` completed all 144 variants but the aggregate `variant-count` gate failed with `Expected 0; observed 144.`

The defect was duplicated required-variant-count dispatch in `Tl1IntegratedTacticalCombatRunner.cs`. `Validate()` contained the six Checkpoint 58 study IDs and correct counts, while `BuildGates()` retained the pre-Checkpoint-58 mapping and silently defaulted unknown IDs to zero. Checkpoint 58e centralizes this contract in `RequiredVariantCountForStudy(string studyId)` and uses that helper from both validation and gate construction. Unsupported study IDs now fail explicitly instead of becoming an expected count of zero.

Checkpoint 58e also improves late-failure diagnostics. Per-variant output is labeled `RESULT` rather than `PASS`, because aggregate gates have not yet run at that point. After gate evaluation and output writing, each failed gate is printed as `FAILED GATE <id>: <detail>` before the final study summary.

No simulation parameter, study JSON, Monte Carlo variant, weapon/defense value, gameplay mechanic, Concept v0.5e content, workbook v0.39 value, or architecture decision changes. The Checkpoint 58a `powerCost` validator correction, 58b retained-ZIP manifest correction, 58c PowerShell format-string correction, and 58d C# compile correction are retained.

## Repository-only gate

From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-58e\apply_checkpoint_58e.ps1 -RepositoryOnly
```

Expected sequence:

1. Frozen Checkpoint 57a and Checkpoint 58 architecture contracts pass.
2. Regression assertions confirm one authoritative required-count helper is used by both `Validate()` and `BuildGates()` and covers all six Checkpoint 58 studies.
3. Regression assertions confirm aggregate failures are printed explicitly and per-variant lines no longer claim `PASS` before gate evaluation.
4. The complete Checkpoint 58e repository manifest and all PowerShell scripts validate.

## Full build and workload

Run the full checkpoint with the normal defaults:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-58e\apply_checkpoint_58e.ps1
```

The build must complete with zero warnings and zero errors before calibration stages run. The workload remains 56 runner stages, 14,746 Monte Carlo variants, and 147.46 million trials at 10,000 trials per variant with 24 workers. Results are written to `out/checkpoint-58e`.

Stage 55 should no longer fail `variant-count` for `tl4-itc04-single-main-axis-screening`; its required count is 144. If any later aggregate gate fails, the console transcript should now include the exact gate ID and detail without requiring a separate `gates.csv` query.
