# Checkpoint 22b - Allocation Attribution and Optimization Triage

## Status

**Historical diagnostic status.** At execution time, Checkpoint 22 remained unaccepted. Its source hotfix compiled and all behavioral
checks passed, but compact execution retained 99.6 percent of diagnostic
allocation instead of no more than 20 percent. Checkpoint 21e was the
accepted behavioral baseline at that point. Checkpoint 22d later closed the
program and accepted the Checkpoint 22c implementation.

Checkpoint 22b is a diagnostic checkpoint. It does not relax the failed gate,
run the 288,000-trial calibration, or claim an allocation optimization.

## Purpose

Checkpoint 22 assumed that diagnostic journal materialization dominated the
roughly 20.96 MB allocated by every full-flight trial. The Checkpoint 22a proof
showed that suppressing the journal saved only about 75 KB per trial. The next
implementation change therefore requires measured attribution rather than
another speculative optimization.

Checkpoint 22b adds a low-overhead, single-thread allocation profiler around the
existing authoritative trial path. It measures both `DiagnosticJournal` and
`CompactMetrics` over the unchanged 24-variant scheduler-proof corpus.

## Measurement model

`ScenarioAllocationProfile` uses
`GC.GetAllocatedBytesForCurrentThread()` and `Stopwatch.GetTimestamp()`.
Each trial executes synchronously on one profiling worker, allowing nested stage
measurements without event objects, dictionaries, or profiler callbacks.

The top-level stages are mutually exclusive:

- seed derivation;
- trial setup;
- executor construction;
- ship movement;
- missile advancement;
- phase advancement;
- scenario finalization; and
- Monte Carlo result projection.

Nested detail is also recorded for:

- runtime initialization;
- ship route planning, step execution, target observation, and track refresh;
- interception-context construction;
- datalink update;
- authoritative missile guidance advancement;
- missile outcome capture; and
- post-missile track refresh.

Derived residual rows expose allocation inside each parent that has not yet been
instrumented more narrowly. The output reports both per-thread attributed bytes
and process-wide allocation deltas for the same calls.

## Corpus and parity

The default run performs one warm-up trial and four measured trials for every
one of the 24 scheduler-proof variants in each execution mode. That yields 96
measured diagnostic trials and 96 measured compact trials.

Every matching diagnostic and compact trial uses identical study, variant,
trial index, master seed, and stream namespace. Canonical
`MonteCarloTrialResult` JSON must match exactly for all 96 pairs.

## Artifacts

The command writes:

- `allocation-profile-summary.json` - corpus contract, mode totals, attribution
  coverage, hierarchy validity, and all stage rows;
- `allocation-stages.csv` - aggregate analysis-ready stage table;
- `allocation-trials.csv` - one row per measured trial with variant metadata,
  operational counts, process-wide allocation, and every attributed stage;
- `allocation-profile-report.txt` - compact human-readable ranking; and
- `parity-failures.txt` only if any canonical pair differs.

## Validation

The apply script requires:

- the pinned .NET SDK 8.0.423;
- targeted guards against the Checkpoint 22 namespace and serializer regressions;
- deletion of stale `bin`, `obj`, and Godot Mono temporary output;
- a clean warning-as-error solution build;
- 506 engine-independent tests;
- seven deterministic scenarios;
- 43 runner self-tests, including profile/no-profile semantic parity and bounded
  stage hierarchy;
- 24 scheduler-proof variants;
- 96/96 diagnostic-versus-compact canonical matches;
- zero trial errors;
- valid parent/child allocation hierarchy; and
- at least 90 percent top-level attribution coverage in both modes.

No allocation-reduction target is imposed in this checkpoint. The measured
largest top-level and detail stages determine the next targeted optimization.
No mechanical Godot validation is required.

## Completed diagnostic result

The local Checkpoint 22b run passed its clean build, 506 tests, seven scenarios,
43 runner self-tests, and 96/96 compact/diagnostic parity pairs. Compact
allocation measured 20,863,918 attributed bytes per trial. Runtime
initialization accounted for 20,507,139 bytes per trial (98.3 percent), while
all post-initialization simulation stages together accounted for roughly 357
KB per trial. This evidence selected calibration-map construction as the
Checkpoint 22c target.
