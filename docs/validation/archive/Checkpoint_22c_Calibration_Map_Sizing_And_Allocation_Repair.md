# Checkpoint 22c Validation - Calibration Map Sizing and Allocation Repair

## Run

Close Godot, extract the checkpoint overlay into the repository root, and run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-22c\apply_checkpoint_22c.ps1
```

## Expected scope

The pass performs a clean warning-as-error build, all existing regression
suites, an all-variant radius-192 parity proof, finer initialization allocation
attribution, worker/scaling proofs, and—only after the frozen allocation gate
passes—the complete 288,000-trial compact calibration.

## Preserve for assessment

Preserve the complete console output and these directories:

```text
out\checkpoint-22c-map-optimization-proof\
out\checkpoint-22c-allocation-profile\
out\checkpoint-22c-diagnostic-proof-j24\
out\checkpoint-22c-compact-proof-j1\
out\checkpoint-22c-compact-proof-j24\
out\checkpoint-22c-full-flight-pursuit-calibration\
```

The most important files are:

```text
map-optimization-summary.json
map-allocation-sweep.csv
map-radius-variants.csv
allocation-profile-summary.json
allocation-stages.csv
full-flight-summary.json
full-flight-execution.json
full-flight-summary.csv
full-flight-marginals.csv
full-flight-result.sha256
```

Neither `map-parity-failures.txt` nor `parity-failures.txt` may exist on a
passing run.

## Interpretation boundary

Checkpoint 22c is accepted only if the complete script succeeds, the accepted
Checkpoint 21e summary and marginal CSV hashes reproduce exactly, and the full
allocation and Gen 2 gates pass. A successful map proof or short allocation
profile alone does not supersede Checkpoint 21e.
