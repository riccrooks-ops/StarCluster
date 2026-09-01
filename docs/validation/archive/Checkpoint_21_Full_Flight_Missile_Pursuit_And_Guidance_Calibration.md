# Checkpoint 21 Validation - Full-Flight Missile Pursuit and Guidance Calibration

## Apply and execute

Close Godot and run from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-21\apply_checkpoint_21.ps1
```

## Expected automated result

- .NET SDK 8.0.423 selected;
- solution builds with zero warnings and zero errors;
- 506/506 engine-independent tests pass;
- seven deterministic headless scenarios pass;
- twenty-two runner self-tests pass;
- Checkpoint 19 reproducibility hashes match at `--jobs 1` and `--jobs 24`;
- full-flight preflight reports 288 variants across four missile profiles;
- all 288 variants complete 1,000 trials each at `--jobs 24`;
- all paired marginals verify common random numbers;
- no practical, Holm-significant contradictory marginal is reported; and
- exactly this Checkpoint 21 validation file remains active.

## Output to preserve

Compress and return:

```text
out\checkpoint-21-full-flight-pursuit-calibration
```

The compact output should include:

- `full-flight-summary.json`;
- `full-flight-summary.csv`;
- `full-flight-marginals.csv`;
- `full-flight-result.sha256`; and
- compact per-variant manifests, canonical results, and execution provenance.

Routine acceptance discards trial journals. Detailed trial traces can be added
later for selected anomalies or representative cases.

## No Godot run

No mechanical Godot validation is required.
