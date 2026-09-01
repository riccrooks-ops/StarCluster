# Checkpoint 22b Validation - Allocation Attribution and Optimization Triage

## Run

Close Godot, extract the checkpoint overlay into the repository root, and run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-22b\apply_checkpoint_22b.ps1
```

## Expected scope

This pass performs a clean build, the unchanged engine-independent regression
suite, the deterministic scenario corpus, 43 runner self-tests, and a short
single-worker allocation profile. It does not invoke the failed Checkpoint 22
allocation gate or the 288,000-trial calibration.

## Preserve for assessment

Preserve the complete console output and:

```text
out\checkpoint-22b-allocation-profile\
```

The most important files are:

```text
allocation-profile-summary.json
allocation-stages.csv
allocation-trials.csv
allocation-profile-report.txt
```

`parity-failures.txt` must not exist on a passing run.

## Interpretation boundary

Checkpoint 22b passing means the profiler is behaviorally neutral and provides
bounded attribution. It does not mean the allocation problem is solved.
Checkpoint 21e remains the accepted behavioral baseline until a later
optimization pass reproduces its canonical calibration outputs and passes the
original performance gates.
