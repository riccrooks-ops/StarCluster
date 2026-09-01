# Checkpoint 22a Validation - Monte Carlo Allocation and State Preparation

## Apply and execute

Close Godot and run from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-22a\apply_checkpoint_22a.ps1
```

## Expected automated result

- .NET SDK 8.0.423 selected;
- solution builds with zero warnings and zero errors;
- 506/506 engine-independent tests pass;
- seven deterministic scenarios pass;
- forty-one runner self-tests pass;
- ordinary stochastic outputs match at `--jobs 1` and `--jobs 24`;
- the 24-variant proof runs 32 trials per variant through diagnostic mode and
  compact mode;
- diagnostic and compact canonical hashes are identical;
- compact outputs match at `--jobs 1` and `--jobs 24`;
- all proof runs report zero trial, datalink-contract,
  terminal-opportunity-invariant, and unexplained-unresolved failures;
- the compact parallel proof reports 24/24 active workers;
- compact 24-worker throughput is at least 2.0 times compact one-worker
  throughput;
- compact allocation per trial is no more than 20 percent of diagnostic
  allocation per trial;
- the proof projects the 288,000-trial study to complete within 30 minutes;
- the full study runs in compact mode at `--jobs 24` only after the proof gates
  pass;
- all 288 variants pass;
- 720 inferential and 144 descriptive marginals are reported;
- no Holm-significant inferential contradiction remains;
- all mechanical failure categories remain zero;
- full summary and marginal CSV files exactly match the accepted Checkpoint 21e
  behavioral references;
- full-run allocation is at least 80 percent lower than Checkpoint 21e; and
- full-run Gen 2 collections are at least 90 percent lower than Checkpoint 21e.

## Output to preserve

After a successful run, compress and return:

```text
out\checkpoint-22-full-flight-pursuit-calibration
```

Also retain:

```text
out\checkpoint-22-diagnostic-proof-j24
out\checkpoint-22-compact-proof-j1
out\checkpoint-22-compact-proof-j24
```

No mechanical Godot validation is required.
