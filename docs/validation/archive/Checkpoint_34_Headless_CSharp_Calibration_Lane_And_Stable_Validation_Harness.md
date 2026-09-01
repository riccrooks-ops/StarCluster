# Checkpoint 34 Validation Runbook

## Command

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\tools\checkpoints\checkpoint-34\apply_checkpoint_34.ps1
```

The default workload is 10,000 trials per Monte Carlo variant with 24 workers. Override with `-Trials` or `-Jobs` when necessary.

## Blocking gates

1. `CHECKPOINT_34_SHA256SUMS.txt` validates every controlled repository file.
2. All PowerShell scripts parse.
3. `tools/calibration/checkpoints/checkpoint-34.json` is valid and references existing executable/data files.
4. .NET SDK 8.0.423 is selected.
5. `StarCluster.Calibration.sln` builds with warnings as errors.
6. `StarCluster.Tests` passes.
7. Every configured ScenarioRunner stage exits successfully.

The harness does not parse console prose to count tests or variants. The C# tests and ScenarioRunner validators own those semantic contracts and return nonzero on failure.

## Non-blocking documentation report

The harness reports whether the declared Concept, workbook, and validation runbook exist. Missing documentation produces a warning but does not stop mechanical testing. README wording, document sentences, workbook markers, and source-code string fragments are never calibration gates.

## Expected configured runner stages

- accepted deterministic moving-missile scenarios;
- TL1 Phase A mechanics corpus;
- TL1 Phase B direct-fire corpus;
- kinetic calibration;
- energy calibration;
- no-counter weapon matrix;
- PDS/interception calibration;
- layered defensive-system calibration;
- 294-variant main-power/interception correction study;
- ScenarioRunner self-tests.

## Separate integration milestone

Use `tools/integration/run_full_solution_validation.ps1` when a checkpoint must prove Godot/C# integration. That lane builds `StarCluster.sln`; it is not part of routine technology calibration.
