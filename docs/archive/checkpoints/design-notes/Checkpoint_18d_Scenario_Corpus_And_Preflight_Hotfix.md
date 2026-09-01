# Checkpoint 18d - Scenario Corpus and Preflight Hotfix

## Purpose

Checkpoint 18d corrects the two deterministic scenario failures exposed after Checkpoint 18c reached a clean 506/506 unit-test result. No Core combat rule changes are made.

## Corrections

### Valid pre-simulation missile history

`blocked-retained-report-search` previously seeded a non-adjacent travel-history jump from `(1,3)` to `(0,2)`. The scenario now records the physically valid route:

```text
(2,2) -> (2,3) -> (1,3) -> (0,3) -> (0,2)
```

Its expected lifetime distance and fuel expenditure are therefore four rather than three.

### Correct command-guided event expectation

`command-guided-live-datalink` previously expected final `ShipMovementResolved` before the per-entered-hex `TrackUpdated` event. The scenario now follows the authoritative movement order: step resolution, track refresh, final movement resolution, then missile datalink and terminal processing.

### Batch scenario preflight

The runner now deserializes and preflights every selected scenario before executing any scenario in the batch. Preflight reuses the production scenario mapper and explicitly reports malformed missile history with the missile ID, history index, prior coordinate, next coordinate, and hex distance. If any scenario is malformed, none are executed.

### Better event-order diagnostics

A failed ordered-event assertion now reports the event types and zero-based indexes already matched, plus every index at which the missing event type occurred. This makes a greedy-order mismatch diagnosable from the compact console output without requiring manual JSONL inspection.

## Acceptance

- solution builds with warnings treated as errors;
- **506/506** engine-independent tests pass;
- scenario preflight reports **7 passed, 0 failed**;
- all **7/7** deterministic headless scenarios pass; and
- no mechanical Godot validation is required.
