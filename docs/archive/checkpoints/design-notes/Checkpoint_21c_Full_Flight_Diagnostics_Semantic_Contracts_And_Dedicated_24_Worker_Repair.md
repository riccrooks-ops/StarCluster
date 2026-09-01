# Checkpoint 21c - Full-Flight Diagnostics, Semantic Contracts, and Dedicated 24-Worker Repair

## Purpose

Checkpoint 21c repairs the two issues exposed by the Checkpoint 21b scheduler
proof without replacing the authoritative `StarCluster.Core` missile model.
The pass corrects a Search/Wait diagnostic classification, replaces an
overly literal occluded-datalink assertion with a semantic contract, separates
scheduler reproducibility from gameplay statistics, and makes the requested
24-way parallelism explicit through dedicated variant workers.

The accepted terminal, interception, guidance, range, fuel, and Search/Wait
rules are unchanged.

## Candidate-coordinate Search/Wait diagnostics

A Missile Flight following a retained or otherwise imperfect report can reach
the report's candidate coordinate after the target has moved elsewhere. Core
correctly resolves that state as non-co-located `AcquisitionFailed` and enters
`Searching`. The runner previously mislabeled the resolution as
`MissileTerminalAcquisitionResolved`, which caused the Monte Carlo invariant to
report terminal mechanics without a terminal opportunity.

Checkpoint 21c reserves `MissileTerminalAcquisitionResolved` for resolutions
where `TargetCoLocated` is true. A non-co-located candidate-coordinate arrival
instead emits `MissileSearchActivated` with:

- `searchTrigger=CandidateCoordinateReached`;
- `targetCoLocated=False`;
- the current fuel/range state; and
- the authoritative Core reason.

Stationary Search/Wait retries continue to emit `MissileSearchActivated` with
`searchTrigger=StationaryRetry`. Terminal opportunities remain authoritative
records with source classes for missile entry, target entry, action-start
co-location, and stationary search retry.

## Semantic datalink contract

An initially occluded trial is valid when it resolves before the Missile Flight
performs its first guidance update. Therefore, it is incorrect to require every
occluded trial to contain a `Blocked` update event.

The repaired contract is behavioral:

- an occluded Flight may never use fresh datalink guidance;
- if an occluded Flight attempts a datalink update, the update must be Blocked
  and must not be Live;
- a live-link Flight may not observe a Blocked update;
- if a live-link Flight attempts an update, it must observe Live; and
- no update event is required when terminal resolution occurs before the first
  missile guidance update.

The summary now reports update-attempt, Blocked, Live, and semantic-contract
failure probabilities separately. Variant failures are divided into trial
errors, datalink-contract failures, terminal-opportunity invariant failures,
and unexplained unresolved outcomes. `errors.jsonl` is preserved whenever a
trial errors even when routine trial journals are discarded.

## Relative-motion comparison scope

The movement fixtures are relative-motion trajectories, not facings or weapon
arcs. Star Cluster does not currently model orientation, turn rate, armor
facings, or directional PDS coverage.

For stationary and straight-retreat trajectories, an initially occluded-to-live
datalink comparison retains a nondecreasing inferential expectation. For
`crossing-weave` and `turnback`, the comparison is descriptive. A stale course
can occasionally intersect a later target path while repeated pursuit of the
current coordinate consumes more range, so live guidance is not guaranteed to
improve every individual trajectory under the current non-predictive guidance
law.

The complete calibration still produces 864 paired marginal rows:

- 720 inferential rows participate in Holm-corrected acceptance; and
- 144 crossing-weave/turnback datalink rows are descriptive and cannot fail the
  directional statistical gate.

## Dedicated 24-worker scheduling

The scheduler uses a bounded queue and dedicated long-running variant workers:

- `--jobs 24` creates at most 24 variant workers;
- each worker executes one variant at a time;
- every variant runs its trials serially with one inner worker;
- no nested 24-by-24 parallelism is allowed;
- a synchronized first wave proves that all available workers can become
  active; and
- immutable runner/Core assembly hashes are cached once per process rather than reread by every concurrent variant; and
- canonical output is sorted after execution, independent of completion order.

The scheduler proof is now a purpose-built 24-variant corpus covering four
missile profiles, three missile TLs, two datalink states, and all four
relative-motion trajectories. It runs at both `--jobs 1` and `--jobs 24` with
statistical gameplay gates disabled. It must produce identical canonical hashes
and zero mechanical failure categories. The 24-worker run must report a peak of
24 active variant workers.

The full 288-variant, 288,000-trial calibration runs once at `--jobs 24`, with
all mechanical and applicable statistical gates enabled.

## Validation

Checkpoint 21c requires:

- 506 engine-independent tests;
- seven deterministic scenarios;
- thirty-four runner self-tests;
- ordinary Monte Carlo hash equality at `--jobs 1` and `--jobs 24`;
- scheduler-proof hash equality across one and twenty-four workers;
- exactly 24 scheduler-proof variants and a 24/24 peak-worker report;
- 288 full-flight variants at 1,000 trials each using `--jobs 24`;
- zero trial errors, semantic datalink failures, terminal-opportunity invariant
  failures, and unexplained unresolved outcomes;
- 720 inferential and 144 descriptive paired marginals;
- common-random-number verification; and
- zero practical, Holm-significant contradictory inferential marginals.

No mechanical Godot validation is required.
