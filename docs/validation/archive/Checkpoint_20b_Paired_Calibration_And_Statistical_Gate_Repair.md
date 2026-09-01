# Checkpoint 20b Validation - Paired Calibration and Statistical Gate Repair

## Apply and execute

Close Godot and run from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-20b\apply_checkpoint_20b.ps1
```

## Expected automated result

- .NET SDK 8.0.423 selected;
- solution builds with zero warnings and zero errors;
- 506/506 engine-independent tests pass;
- seven deterministic headless scenarios pass;
- sixteen runner self-tests pass;
- Checkpoint 19 reproducibility hashes match at `--jobs 1` and `--jobs 24`;
- calibration preflight reports 108 variants across four profiles;
- all 108 variants pass 2,000 trials each at `--jobs 24`;
- all 216 adjacent-TL comparisons verify common random numbers;
- the 63 analytically flat comparisons have zero paired observed delta;
- no practical, Holm-significant contradictory marginal is reported; and
- exactly this Checkpoint 20b validation file remains active.

## Output to preserve

Compress and return:

```text
out\checkpoint-20b-terminal-tl-calibration
```

The compact result should contain result schema version 2, the shared
random-seed namespace, paired marginal counts and confidence intervals, raw and
Holm-adjusted p-values, pairing fingerprints, and the unchanged per-variant
analytical error checks.

## No Godot run

No mechanical Godot validation is required.
