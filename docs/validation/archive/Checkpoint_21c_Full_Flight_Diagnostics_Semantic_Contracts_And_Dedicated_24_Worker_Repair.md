# Checkpoint 21c Validation - Full-Flight Diagnostics, Semantic Contracts, and Dedicated 24-Worker Repair

## Apply and execute

Close Godot and run from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-21c\apply_checkpoint_21c.ps1
```

## Required diagnostic behavior

A non-co-located Missile Flight that reaches a stale candidate coordinate must
emit `MissileSearchActivated` with `searchTrigger=CandidateCoordinateReached`.
It must not emit `MissileTerminalAcquisitionResolved`. Terminal acquisition
remains reserved for a physically co-located target.

Occluded-datalink validation is semantic. Fresh datalink guidance is forbidden
while occluded. A guidance update, when attempted, must report Blocked and not
Live. A trial that resolves before its first guidance update is valid and does
not need a Blocked event.

## Scheduler proof

The acceptance script runs a dedicated 24-variant scheduler corpus twice:

```text
--jobs 1
--jobs 24
```

Each run uses eight trials per variant and skips gameplay statistical gates. The
canonical hashes must match. The one-worker execution must report peak 1/1; the
24-worker execution must report peak 24/24. Both must retain one inner trial
worker per variant and report zero mechanical failure categories.

## Full calibration

The complete study then runs once:

```text
288 variants x 1,000 trials = 288,000 trials
--jobs 24
```

The expected paired family contains 864 rows: 720 inferential rows and 144
descriptive relative-motion datalink rows. Only the inferential family receives
Holm correction and directional acceptance.

## Expected automated result

- .NET SDK 8.0.423 selected;
- solution builds with zero warnings and zero errors;
- 506/506 engine-independent tests pass;
- seven deterministic scenarios pass;
- thirty-four runner self-tests pass;
- ordinary stochastic results match at `--jobs 1` and `--jobs 24`;
- the 24-variant scheduler-proof hashes match at `--jobs 1` and `--jobs 24`;
- scheduler telemetry reports one inner trial worker per variant and peak 24/24
  active workers for `--jobs 24`;
- all 288 full-flight variants pass at `--jobs 24`;
- common random numbers are verified;
- zero trial errors, datalink semantic-contract failures,
  terminal-opportunity invariant failures, and unexplained unresolved outcomes
  are reported;
- 720 inferential and 144 descriptive marginals are reported;
- zero statistically contradictory inferential marginals remain after Holm
  correction; and
- exactly this Checkpoint 21c validation file remains active.

## Output to preserve

Compress and return:

```text
out\checkpoint-21c-full-flight-pursuit-calibration
```

The compact output includes the canonical summary, paired marginals, result
hash, execution telemetry, per-variant compact results, and any `errors.jsonl`
files. Routine full trial journals are discarded.

## No Godot run

No mechanical Godot validation is required.
