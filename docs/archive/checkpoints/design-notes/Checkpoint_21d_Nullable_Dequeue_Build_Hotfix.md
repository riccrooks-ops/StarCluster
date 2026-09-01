# Checkpoint 21d - Nullable Dequeue Build Hotfix

## Purpose

Checkpoint 21d repairs the single C# compiler error that prevented the
Checkpoint 21c acceptance run from beginning. The .NET 8 nullable annotations
for `ConcurrentQueue<T>.TryDequeue` permit a null result when the method returns
false. The dedicated scheduler declared the `out` variable as non-nullable,
which produced warning-as-error `CS8600` even though the queue is populated only
with non-null work items.

Checkpoint 21c mechanics are unchanged. This hotfix does not alter Core missile
behavior, target movement, terminal opportunities, the semantic datalink
contract, common-random-number streams, the 24-worker scheduler topology, study
cardinality, formulas, or statistical gates.

## Nullable work-item repair

The scheduler now dequeues into the nullable type required by the framework
contract:

```csharp
out PreparedFullFlightCalibrationVariant? item
```

Before dispatch, it explicitly rejects an impossible null work item:

```csharp
if (item is null)
{
    throw new InvalidOperationException(
        "The full-flight variant queue returned a null work item.");
}
```

This satisfies nullable flow analysis without using the null-forgiving operator
and preserves deterministic exception aggregation should malformed work ever be
introduced.

## Preserved Checkpoint 21c contracts

The complete Checkpoint 21c acceptance sequence is rerun. In particular:

- non-co-located `CandidateCoordinateReached` events remain Search/Wait rather
  than terminal acquisition;
- the semantic datalink contract remains behavioral rather than event-count
  based;
- failed trials retain `errors.jsonl`;
- dedicated long-running variant workers remain capped at 24 with one serial
  inner trial lane per variant;
- the scheduler proof remains a dedicated 24-variant corpus at `--jobs 1` and
  `--jobs 24`;
- the full study remains 288 variants at 1,000 trials each;
- the paired family remains 720 inferential rows and 144 crossing-weave/turnback datalink rows reported descriptively; and
- zero mechanical failure categories and zero Holm-significant inferential
  contradictions remain required.

The Checkpoint 21c study identifier is intentionally preserved so the trial
seeds and common-random-number streams are identical to the intended 21c run.
Only output directories use the Checkpoint 21d label.

## Validation

Checkpoint 21d requires a clean warning-as-error solution build, 506 tests,
seven deterministic scenarios, thirty-four runner self-tests, ordinary worker
independence, identical dedicated scheduler-proof hashes at one and twenty-four
workers, a measured 24/24 active-worker peak, and a passing 288,000-trial full
calibration.

No mechanical Godot validation is required.
