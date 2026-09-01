# Checkpoint 22 - Monte Carlo Allocation and State-Preparation Optimization

> **Status: closed by Checkpoint 22d.** The original Checkpoint 22/22a attempt
> failed its allocation gate. Checkpoint 22b measured the dominant cost,
> Checkpoint 22c repaired calibration-map sizing and passed the complete
> behavioral and performance acceptance sequence, and Checkpoint 22d promotes
> that result to the accepted repository baseline. Checkpoint 21e remains the
> frozen behavioral reference.

## Purpose

Checkpoint 21e established a correct, reproducible 24-worker global trial-block
scheduler, but the accepted 288,000-trial full-flight run allocated roughly
6.04 TB of managed memory, or about 20.96 MB per trial. That allocation pressure
caused 10,628 Gen 0, 7,066 Gen 1, and 4,117 Gen 2 collections and limited compute
throughput to 229.46 trials per second despite approximately 75 percent total CPU
utilization.

Checkpoint 22 is a performance-only pass. Missile movement, pursuit, guidance,
datalink, sensor, Search/Wait, PDS, terminal-opportunity, terminal-attack,
relative-motion, technology, random-stream, and statistical semantics remain
unchanged.

## Reusable execution preparation

Each full-flight variant now creates one immutable `ScenarioExecutionPlan` before
its trials begin. The plan reuses:

- the parsed scenario action kinds;
- the authoritative `ScenarioInitializationRequest`;
- the stochastic PDS probability profile; and
- parsed defense definitions and immutable defense profiles.

Every trial still receives a fresh authoritative tactical map, ships, tracks,
Missile Flights, turn state, and interception context. State is not shared
between trials.

## Compact Monte Carlo execution

Deterministic scenarios and normal runner operations retain the complete diagnostic
journal. High-volume full-flight calibration defaults to `CompactMetrics`, which:

- records no per-event diagnostic objects or event-data dictionaries;
- captures required Monte Carlo observations directly while the authoritative
  Core services execute;
- applies identical track mutations without allocating unused
  `TacticalTrackUpdateResult` objects;
- keeps authoritative terminal opportunities and interception attempts;
- preserves error evidence and selected trial journals; and
- lazily formats random seeds only when they are serialized or fingerprinted.

The internal modes are `CompactMetrics` and `DiagnosticJournal`;
`--trial-execution diagnostic` executes the same prepared study through the
former full-journal observation path.

## Behavioral equivalence and performance gates

The apply script runs the same 24-variant, 32-trial proof in diagnostic and
compact modes. It requires byte-identical canonical result hashes, zero
mechanical failure categories, and identical one-worker and 24-worker compact
hashes.

The compact 24-worker proof must:

- retain at least 2.0x speedup over compact one-worker execution;
- allocate no more than 20 percent of the diagnostic proof's bytes per trial;
- preserve server GC and the 24-worker ceiling; and
- project the full 288,000-trial study to finish within 30 minutes.

The full study then runs once in compact mode at 24 workers. Its summary and
marginal CSV files must exactly match the accepted Checkpoint 21e behavioral
reference files. The full run also requires at least an 80 percent allocation
reduction and at least a 90 percent reduction in Gen 2 collections relative to
Checkpoint 21e.

## Validation

Checkpoint 22 requires a warning-as-error build, 506 tests, seven deterministic
scenarios, forty-one runner self-tests, ordinary worker independence,
diagnostic-versus-compact semantic equivalence, compact worker independence,
the allocation and scaling gates, and the unchanged 288-variant calibration.

No mechanical Godot validation is required.

## Checkpoint 22c repair direction

Checkpoint 22b proved that the original compact/diagnostic ratio gate used the
wrong denominator: both modes paid the same fixed radius-192 map-construction
cost. Checkpoint 22c preserves the intended 80 percent reduction as a frozen
absolute compact-allocation gate, sizes generated calibration maps per variant,
and requires complete radius-192 parity plus exact Checkpoint 21e full-study
CSV reproduction before acceptance.
