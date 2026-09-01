# Checkpoint 35 Validation Runbook

## Command

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\tools\checkpoints\checkpoint-35\apply_checkpoint_35.ps1
```

The default workload is 10,000 trials per Monte Carlo variant with 24 workers. Use `-Trials`, `-Jobs`, `-RepositoryOnly`, or `-NoClean` only as supported by the stable harness.

## Blocking gates

1. `CHECKPOINT_35_SHA256SUMS.txt` validates every controlled repository file and rejects unexpected repository-owned files.
2. All PowerShell scripts parse.
3. `tools/calibration/checkpoints/checkpoint-35.json` is valid and references existing executable/data files.
4. .NET SDK 8.0.423 is selected.
5. `StarCluster.Calibration.sln` builds with warnings as errors.
6. `StarCluster.Tests` passes.
7. Every configured ScenarioRunner stage exits successfully.

No README, Concept, workbook, source-text phrase, or console-text phrase is a mechanical gate.

## Expected workload

The stable harness should report 11 configured runner stages and 16 total stages:

- accepted deterministic moving-missile scenarios;
- TL1 Phase A mechanics;
- TL1 Phase B direct fire;
- kinetic calibration;
- energy calibration;
- no-counter weapon matrix;
- corrected PDS/interception calibration;
- layered defensive-system calibration;
- 294-case main-power/interception correction study;
- 75-case scripted relative-range calibration;
- ScenarioRunner self-tests.

The source tree contains nine new focused facts, increasing the expected compiled test total from 674 to 683.

## Result archive

Preserve the complete `out/checkpoint-35` directory after a successful run. The new `tl1-range-control-calibration` directory contains `summary.json`, `variants.csv`, and `gates.csv`.

## Separate integration lane

The routine command does not build `StarCluster.Game`. Run `tools/integration/run_full_solution_validation.ps1` only when a Godot/C# integration milestone is required.
