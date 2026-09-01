# Checkpoint 21d Validation - Nullable Dequeue Build Hotfix

## Apply and execute

Close Godot and run from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-21d\apply_checkpoint_21d.ps1
```

## Build repair

The prior run stopped at warning-as-error `CS8600` because
`ConcurrentQueue<T>.TryDequeue` was assigned directly to a non-nullable work
item. The scheduler must contain both:

```text
out PreparedFullFlightCalibrationVariant? item
if (item is null)
```

The non-nullable dequeue declaration is forbidden. No mechanical or stochastic
contract changes in this hotfix.

## Expected automated result

- .NET SDK 8.0.423 selected;
- solution builds with zero warnings and zero errors;
- 506/506 engine-independent tests pass;
- seven deterministic scenarios pass;
- thirty-four runner self-tests pass;
- ordinary stochastic outputs match at `--jobs 1` and `--jobs 24`;
- the dedicated 24-variant scheduler corpus passes at `--jobs 1` and
  `--jobs 24` with identical canonical hashes;
- scheduler telemetry reports peak 24/24 active workers in the 24-worker run;
- the full study executes `288 variants x 1,000 trials = 288,000 trials` at
  `--jobs 24`;
- all 288 variants pass with zero trial, datalink-contract,
  terminal-opportunity-invariant, and unexplained-unresolved failures;
- 720 inferential and 144 descriptive marginals are reported;
- no Holm-significant inferential contradiction remains; and
- exactly this Checkpoint 21d runbook remains active.

## Output to preserve

Compress and return:

```text
out\checkpoint-21d-full-flight-pursuit-calibration
```

Also retain the console output so worker peak, elapsed time, and throughput can
be reviewed.

No mechanical Godot validation is required.
