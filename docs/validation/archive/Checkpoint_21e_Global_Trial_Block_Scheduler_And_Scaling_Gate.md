# Checkpoint 21e Validation - Global Trial-Block Scheduler and Scaling Gate

## Apply and execute

Close Godot and run from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-21e\apply_checkpoint_21e.ps1
```

## Expected automated result

- .NET SDK 8.0.423 selected;
- solution builds with zero warnings and zero errors;
- 506/506 engine-independent tests pass;
- seven deterministic scenarios pass;
- thirty-seven runner self-tests pass;
- ordinary stochastic outputs match at `--jobs 1` and `--jobs 24`;
- the 24-variant scheduler proof runs 32 trials per variant at `--jobs 1` and
  `--jobs 24` with identical canonical hashes;
- both scheduler proofs report zero trial, datalink-contract,
  terminal-opportunity-invariant, and unexplained-unresolved failures;
- the parallel proof reports 24/24 active global trial-block workers;
- server GC is enabled;
- all scheduled blocks complete exactly once;
- compute throughput at 24 workers is at least 2.0 times the one-worker rate;
- the proof projects the 288,000-trial study to complete within 30 minutes;
- only after the scaling gate passes, the complete 288-variant study runs at
  `--jobs 24`;
- all 288 variants pass;
- 720 inferential and 144 descriptive marginals are reported;
- no Holm-significant inferential contradiction remains; and
- all mechanical failure categories remain zero.

If the scaling gate fails, the script stops before the full calibration and
preserves both scheduler-proof output directories for review.

## Output to preserve

After a successful run, compress and return:

```text
out\checkpoint-21e-full-flight-pursuit-calibration
```

Also retain:

```text
out\checkpoint-21e-scheduler-proof-j1
out\checkpoint-21e-scheduler-proof-j24
```

No mechanical Godot validation is required.
