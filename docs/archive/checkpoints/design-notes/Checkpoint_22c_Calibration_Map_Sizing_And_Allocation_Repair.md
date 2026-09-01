# Checkpoint 22c - Calibration Map Sizing and Allocation Repair

## Status

Checkpoint 22c completed successfully and is accepted through Checkpoint 22d
as the current implementation and performance baseline. Checkpoint 21e remains
the frozen behavioral reference used to prove exact output preservation.

Checkpoint 22b measured approximately 20.86 MB allocated per compact trial and
attributed 98.3 percent of that total to runtime initialization. Finer review
identified the fixed radius-192 calibration map as the common dominant object:
it eagerly materializes 111,169 hex cells for every trial even though most
scripted pursuit variants use a small fraction of that topology.

## Map-sizing policy

The gameplay map implementation is unchanged. Only the generated full-flight
calibration scenarios receive variant-sized maps.

For each variant, the generator now:

1. materializes the complete scripted target movement sequence;
2. computes the centered-hex radius required by every explicit ship, Missile
   Flight, prior-track, occluder, and scripted destination coordinate;
3. adds a two-hex safety margin; and
4. uses the larger of that result and radius 5.

The former radius-192 scenario remains available through
`FullFlightMapSizingMode.ReferenceRadius192` solely for parity proof. Mutable
maps are still freshly created for every trial; no map state is shared or reset
between trials.

## Direct proof

`map-optimization-proof` performs three independent checks:

- direct `SystemMap.Create` allocation measurements at radii 5, 28, 64, 100,
  and 192, which must increase monotonically with cell count;
- explicit-coordinate containment for all 288 generated variants; and
- canonical compact-trial parity across four common-random-number trials for
  every optimized variant and its radius-192 reference counterpart.

The proof writes:

- `map-optimization-summary.json`;
- `map-allocation-sweep.csv`;
- `map-radius-variants.csv`;
- `map-optimization-report.txt`; and
- `map-parity-failures.txt` only on a mismatch.

For the locked study, the expected optimized radius range is 30 through 102,
with an average radius of 38.25 and average cell retention below five percent
of the radius-192 topology.

## Finer initialization attribution

Core initialization accepts an optional stage recorder used only by the
headless profiler. It subdivides `RuntimeInitialization` into:

- map creation;
- static-object placement;
- ship-state creation;
- prior-track seeding;
- Missile Flight state creation;
- turn and journal creation;
- initial track refresh;
- initialization diagnostics; and
- result construction.

Normal game and deterministic callers pass no recorder. The profiling contract
requires all child stages to remain bounded by their parent and preserves exact
profiled/unprofiled canonical outcomes.

## Frozen allocation gate

The failed diagnostic-versus-compact ratio is replaced by a frozen absolute
regression target derived from the successful Checkpoint 22b compact profile:

```text
Checkpoint 22b compact baseline: 20,863,918 bytes/trial
Checkpoint 22c maximum:           4,172,784 bytes/trial
```

This preserves the intended 80 percent reduction while preventing both sides of
a relative ratio from shrinking together. Diagnostic-versus-compact canonical
parity remains mandatory as a separate semantic gate.

## Acceptance sequence

The apply script requires:

- a clean warning-as-error solution build under .NET SDK 8.0.423;
- 506 engine-independent tests;
- seven deterministic scenarios;
- 46 runner self-tests;
- 288/288 optimized-versus-radius-192 canonical matches across four trials per variant;
- zero explicit-coordinate failures;
- monotonic map-allocation scaling;
- compact profiled allocation no greater than 4,172,784 bytes per trial;
- worker-independent ordinary and full-flight hashes;
- diagnostic/compact scheduler-proof parity;
- at least 2.0x jobs-24 scheduler-proof speedup;
- a projected full-study runtime no greater than 30 minutes;
- the complete 288,000-trial compact calibration;
- exact Checkpoint 21e summary and marginal CSV hashes;
- at least 80 percent full-run allocation reduction; and
- at least 90 percent full-run Gen 2 collection reduction.

No mechanical Godot validation is required because this pass changes only the
headless calibration scenario topology and optional profiling instrumentation.


## Accepted result

The reviewed Checkpoint 22c run passed the warning-as-error build, 506 tests,
seven deterministic scenarios, 46 runner self-tests, 288/288 radius-192 parity
comparisons, the frozen allocation gate, worker/mode parity, and the complete
288,000-trial calibration. It achieved 93.97 percent profiled compact allocation
reduction, 93.72 percent full-run allocation reduction, 91.13 percent Gen 2
collection reduction, and exact Checkpoint 21e summary and marginal CSV
reproduction. The accepted canonical result hash is:

```text
226677d3b9d2fded9e529ab5b897f6ec0e5251eb27937208f571cbb9b184ee28
```
