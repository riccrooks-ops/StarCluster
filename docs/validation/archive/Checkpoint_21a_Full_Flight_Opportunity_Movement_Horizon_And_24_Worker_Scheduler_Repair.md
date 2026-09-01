# Checkpoint 21a Validation - Full-Flight Opportunity, Movement, Horizon, and 24-Worker Scheduler Repair

## Apply and execute

Close Godot and run from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-21a\apply_checkpoint_21a.ps1
```

## Expected automated result

- .NET SDK 8.0.423 selected;
- solution builds with zero warnings and zero errors;
- 506/506 engine-independent tests pass;
- seven deterministic headless scenarios pass;
- twenty-nine runner self-tests pass;
- the ordinary stochastic hash matches at `--jobs 1` and `--jobs 24`;
- a reduced full-flight study produces the same canonical hash at `--jobs 1`
  and `--jobs 24`;
- the full-flight scheduler enforces a 24-worker ceiling and one inner trial
  worker per variant;
- full-flight preflight reports 288 variants across four missile profiles;
- all 288 variants complete 1,000 trials each at `--jobs 24`;
- every variant reports zero terminal-opportunity invariant failures and zero
  unexplained unresolved outcomes;
- all 864 paired marginals verify common random numbers;
- no practical, Holm-significant contradictory marginal is reported; and
- exactly this Checkpoint 21a validation file remains active.

## Output to preserve

Compress and return:

```text
out\checkpoint-21a-full-flight-pursuit-calibration
```

The compact output should include:

- `full-flight-summary.json`;
- `full-flight-summary.csv`;
- `full-flight-marginals.csv`;
- `full-flight-result.sha256`;
- `full-flight-execution.json`;
- `full-flight-variant-execution.csv`; and
- compact per-variant manifests, canonical results, and execution provenance.

Routine acceptance discards trial journals. The execution report is
noncanonical telemetry; its timestamps and timings do not affect the result
hash.

## No Godot run

No mechanical Godot validation is required.
