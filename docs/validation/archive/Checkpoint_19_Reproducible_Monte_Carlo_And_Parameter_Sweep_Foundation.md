# Checkpoint 19 Validation - Reproducible Monte Carlo and Parameter Sweeps

## Required action

Close Godot, extract the complete Checkpoint 19 overlay into the repository root
with overwrite enabled, and run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-19\apply_checkpoint_19.ps1
```

The apply script performs all required mechanical validation. No Godot run and
no human-in-the-loop combat sequence are required.

## Expected automated result

- .NET SDK 8.0.423 selected;
- build succeeds with zero warnings and errors;
- 506/506 engine-independent tests pass;
- seven deterministic scenarios preflight and pass;
- eight runner self-tests pass;
- the 2,000-trial reproducibility study passes at `--jobs 1`, `12`, and `24`;
- the three reproducibility sweep hashes are identical;
- a resumed 24-worker run reuses 2,000 trials, executes zero, and preserves the
  canonical hash;
- all three 5,000-trial terminal probability variants pass their expected
  probability tolerances; and
- exactly this validation file remains active under `docs\validation`.

## Worker-count validation matrix

```text
--jobs 1
--jobs 12
--jobs 24
```

## Output directories

```text
out\checkpoint-19-repro-j1
out\checkpoint-19-repro-j12
out\checkpoint-19-repro-j24
out\checkpoint-19-terminal-probability-validation
```

Preserve these directories only if the apply script fails or if a later review
requests the statistical results. Normal successful handoff requires only the
console output and, when requested, a compact ZIP of the output directories.

## Failure handoff

If any step fails, provide:

- the complete PowerShell output;
- the affected output directory or directories;
- `runner-error.txt` or trial errors when present; and
- the command used if it differed from the apply script.

Do not attempt to reproduce a Monte Carlo failure in Godot.

## Results template

- Build: PASS / FAIL
- Engine-independent tests: ___ / 506
- Deterministic scenarios: ___ / 7
- Runner self-tests: ___ / 8
- Reproducibility jobs 1: PASS / FAIL
- Reproducibility jobs 12: PASS / FAIL
- Reproducibility jobs 24: PASS / FAIL
- Worker-independent hashes: PASS / FAIL
- Resume: PASS / FAIL
- Probability sweep: ___ / 3
- Notes:
