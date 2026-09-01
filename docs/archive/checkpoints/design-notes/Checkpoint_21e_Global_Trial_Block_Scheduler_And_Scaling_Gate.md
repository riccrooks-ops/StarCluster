# Checkpoint 21e - Global Trial-Block Scheduler and Scaling Gate

## Purpose

Checkpoint 21e replaces the rejected coarse full-flight scheduler. Checkpoint
21d proved that 24 variant threads could be started, but the 24-worker run was
slower than the one-worker proof and the full 288,000-trial run consumed roughly
one hour at low total CPU utilization. The old design launched one complete
`MonteCarloBatchRunner` per active variant, causing each worker to repeat batch
setup, aggregation, allocation, and output work while the process used
workstation garbage collection.

This pass changes only runner execution and telemetry. Core missile movement,
guidance, datalink, terminal-opportunity, PDS, Search/Wait, terminal outcomes,
relative-motion fixtures, study inputs, random-stream identity, and statistical
gates remain unchanged.

## Global trial-block scheduler

The runner now creates one deterministic work plan across every materialized
variant and trial. Work is divided into small blocks and consumed by one shared
queue with a hard ceiling of 24 dedicated workers.

- 32-trial scheduler proofs use blocks of 4 trials.
- 1,000-trial calibration variants use blocks of 16 trials.
- Each `(variant, trial index)` appears in exactly one block.
- Workers perform no file output.
- Results are written into predetermined variant/trial slots.
- Per-variant aggregation and file output occur after all compute workers finish.
- Canonical summaries remain sorted by stable variant ID.
- Trial seeds continue to depend only on the study namespace, trial index, and
  stream ID; execution order cannot alter a result.

The ScenarioRunner executable enables server and concurrent garbage collection
so independent, allocation-heavy trials can use multiple GC heaps rather than
serializing behind workstation-GC pressure.

## Performance telemetry

`full-flight-execution.json` schema 3 records:

- block size and count;
- completed blocks;
- compute and output-finalization time;
- total and compute-only throughput;
- process CPU time and effective processor cores;
- normalized CPU utilization;
- `Environment.ProcessorCount` and Windows process-affinity width;
- server-GC state;
- allocated bytes and generation collection counts; and
- per-variant trial/block counts and accumulated compute time.

Progress is printed every five percent during the compute stage.

## Early scaling gate

The apply script runs the same 24-variant, 32-trial proof at `--jobs 1` and
`--jobs 24`. It requires:

- identical canonical hashes;
- zero mechanical failure categories;
- 24/24 active workers in the parallel proof;
- server GC enabled;
- a complete global block plan; and
- at least 2.0x compute-throughput speedup with a projected full-study runtime
  no greater than 30 minutes.

The 288,000-trial calibration does not start if the scaling gate fails. This
prevents another long low-utilization run while preserving diagnostic output for
review.

## Validation

Checkpoint 21e requires a warning-as-error build, 506 tests, seven deterministic
scenarios, thirty-seven runner self-tests, ordinary Monte Carlo worker
independence, a passing and materially faster scheduler proof, and then the full
288-variant calibration at 24 workers.

No mechanical Godot validation is required.
