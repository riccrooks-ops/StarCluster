# Checkpoint 19 - Reproducible Monte Carlo and Parameter-Sweep Foundation

## Purpose

Checkpoint 19 extends the accepted Checkpoint 18d headless scenario runner into
a reproducible stochastic simulation harness. It adds no new missile combat
rules and does not use Godot for mechanical validation.

The checkpoint's purpose is to prove that repeated trials, parallel execution,
resume behavior, aggregation, and parameter overrides are trustworthy before
Monte Carlo output is used to tune TL progressions or component values.

## Implemented runner modes

- `single` executes one deterministic scenario. `run` remains an alias.
- `run-all` preflights and executes the seven deterministic regression
  scenarios.
- `batch` repeats one scenario for a requested number of stochastic trials.
- `sweep` materializes named variants from one base scenario by applying
  versioned JSON-path overrides.
- `self-test` validates runner-specific seed, statistics, override,
  parallelism, and resume contracts.

## Reproducible random contract

Each trial receives stable seeds derived only from:

- the master seed;
- the variant ID;
- the zero-based trial index; and
- an explicit random-stream ID.

Interception and terminal d100 resolution use separate SplitMix64-derived
streams. A change in interception call count therefore cannot silently shift
terminal attack rolls. Trial results are stored and aggregated in trial-index
order, so `--jobs 1`, `--jobs 12`, and `--jobs 24` must produce byte-identical
canonical aggregate results.

Checkpoint 19 supplies `interceptionChancePercent` as an explicit stochastic
scenario input. This is a harness-validation seam only. Final interception
probability formulas and TL progressions remain deferred.

## Resume and output contract

A batch writes:

- `manifest.json` with scenario, seed, variant, runner assembly, and Core
  assembly identity;
- `trials.jsonl` with one compact record per completed trial;
- `results.json` as the canonical worker-independent aggregate;
- `result.sha256`;
- `metrics.csv` with counts, proportions, and Wilson 95% confidence intervals;
- `execution.json` with worker count, timing, and resume accounting; and
- optional representative traces only when requested.

`--resume` validates the run identity and every stored trial seed before reuse.
The requested trial count may increase. Completed trials are flushed after each
checkpoint block, allowing interrupted large runs to continue without changing
the final result.

Canonical results deliberately exclude timing, worker count, timestamps, and
output paths.

## Parameter-sweep contract

A sweep references one base scenario and applies named overrides such as:

```json
{
  "path": "defenses[0].interceptionChancePercent",
  "value": 40
}
```

Each variant may specify its own trial count, master seed, expected metric
probabilities, and maximum absolute error. The sweep summary records each
variant's materialized scenario hash, canonical result hash, expectation
comparison, and pass/fail status.

Checkpoint 19 Monte Carlo batches intentionally require exactly one primary
Missile Flight. Multi-flight statistical aggregation is deferred so the first
probability contract cannot silently choose or merge ambiguous outcomes.

## Statistical metrics

The first aggregate contract reports unconditional per-launched-flight
frequencies for:

- TerminalEntry interception;
- PreTerminalAttack interception;
- terminal acquisition attempt and success;
- terminal attack resolution;
- Search/Wait activation;
- every final terminal outcome and flight status; and
- average distance, total fuel, and stationary-search fuel.

Every probability metric includes a Wilson 95% confidence interval.

## Validation studies

Two packaged studies are included:

1. `checkpoint-19-reproducibility.sweep.json`
   - one 40% PDS variant;
   - 2,000 trials;
   - run at 1, 12, and 24 workers;
   - all three `sweep-summary.json` hashes must match;
   - rerunning the 24-worker output with `--resume` must reuse all trials and
     preserve the same hash.

2. `checkpoint-19-terminal-probability-validation.sweep.json`
   - 0%, 40%, and 100% terminal-PDS variants;
   - 5,000 trials per variant;
   - expected unconditional terminal-stage and attack-outcome probabilities;
   - compact expectation tolerance checks.

For the 40% PDS fixture, the analytical unconditional probabilities are:

- TerminalEntry interception: 0.4000;
- PreTerminalAttack interception: 0.2400;
- ordinary hit: 0.2844;
- ordinary miss: 0.0684;
- dud: 0.0036; and
- critical hit: 0.0036.

The two terminal defense windows are sequential: the second 40% attempt exists
only after the first attempt misses.

## Unchanged authoritative mechanics

Checkpoint 19 preserves:

- held direct-fire interception during Transit and Stationary only;
- standard PDS during TerminalEntry and PreTerminalAttack only;
- shared authoritative scenario initialization;
- source-neutral Current/Firm terminal eligibility;
- seeker-assisted acquisition and accuracy;
- Search/Wait fuel accounting; and
- all seven accepted Checkpoint 18d deterministic scenarios.

Concept v0.3s and the external reference library are unchanged.

## Acceptance target

- solution builds with zero warnings and zero errors;
- 506/506 engine-independent tests pass;
- 7/7 deterministic headless scenarios pass;
- 8/8 runner self-tests pass;
- reproducibility sweep passes at 1, 12, and 24 workers with identical hashes;
- 24-worker resume reuses all 2,000 completed trials and preserves the hash;
- 3/3 terminal probability variants pass; and
- no mechanical Godot validation is required.
