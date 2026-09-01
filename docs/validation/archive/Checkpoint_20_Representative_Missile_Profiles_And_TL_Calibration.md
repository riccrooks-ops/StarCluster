# Checkpoint 20 Validation - Representative Missile Profiles and TL Calibration

## Apply and execute

Close Godot and run from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-20\apply_checkpoint_20.ps1
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
- exactly this Checkpoint 20 validation file remains active.

## Output to preserve

Compress and return:

```text
out\checkpoint-20-terminal-tl-calibration
```

The most important files are:

- `calibration-summary.json`;
- `calibration-summary.csv`;
- `calibration-marginals.csv`;
- `calibration-result.sha256`; and
- the compact per-variant `results.json`, `manifest.json`, `execution.json`, and
  `execution-history.jsonl` files.

Per-trial journals are intentionally omitted from the acceptance run. Rerun the
`calibrate` command with `--keep-trials` only when a particular variant requires
trial-level diagnosis.

## No Godot run

No mechanical Godot validation is required. Godot remains reserved for
player-facing input, rendering, visibility, and presentation smoke checks.
