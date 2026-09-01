# Checkpoint 20a Validation - Calibration Reporting Guard Hotfix

## Apply and execute

Close Godot and run from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-20a\apply_checkpoint_20a.ps1
```

## Expected automated result

- .NET SDK 8.0.423 selected;
- solution builds with zero warnings and zero errors;
- 506/506 engine-independent tests pass;
- seven deterministic headless scenarios pass;
- twelve runner self-tests pass;
- Checkpoint 19 reproducibility hashes match at `--jobs 1` and `--jobs 24`;
- calibration preflight reports 108 variants across four profiles;
- all 108 variants pass 2,000 trials each at `--jobs 24`;
- no statistically contradictory adjacent-TL marginal is reported; and
- exactly this Checkpoint 20a validation file remains active.

## Output to preserve

Compress and return:

```text
out\checkpoint-20-terminal-tl-calibration
```

The hotfix changes no simulation mechanics or statistical values. It only
repairs the source-text reporting guard that previously stopped before build.

## No Godot run

No mechanical Godot validation is required.
