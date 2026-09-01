# Checkpoint 21a - Full-Flight Opportunity, Movement, Horizon, and 24-Worker Scheduler Repair

## Purpose

Checkpoint 21a repairs the full-flight calibration evidence exposed by the
Checkpoint 21 acceptance run. The underlying Core pursuit, guidance,
interception, and terminal mechanics remain authoritative and are not replaced.
The repair makes terminal opportunities source-complete, replaces a duplicated
movement fixture, derives an operational safety cap from missile endurance, and
moves full-flight parallelism to a bounded variant-level scheduler.

## Terminal-opportunity authority

`ScenarioExecutor` now records terminal opportunities as authoritative runner
state rather than inferring them later from one diagnostic event. Each
opportunity records one source:

- `MissileEnteredTargetHex`;
- `TargetEnteredMissileHex`;
- `ActionBeganColocated`; or
- `StationarySearchRetry`.

This closes the Checkpoint 21 hole where a moving target could enter a Missile
Flight's existing hex and proceed through terminal PDS or attack resolution
without incrementing the terminal-opportunity metric. The matching diagnostic
event is still emitted in causal order before terminal-entry interception.
Monte Carlo trials fail their invariant if terminal PDS, acquisition, or attack
occurs without a matching authoritative opportunity, or if authoritative and
diagnostic opportunity counts diverge.

## Movement corpus

The prior `lateral` policy was geometrically equivalent to straight retreat
from the selected starting bearing. It is replaced by `crossing-weave`, a
deterministic four-turn crossing loop. The former `reversal` fixture is retained
under the more explicit name `turnback`; it is an edge-case target policy rather
than a general model of evasive maneuvering.

The matrix remains:

- four representative missile profiles;
- missile TL 2, 4, and 6;
- target propulsion TL 2, 4, and 6;
- stationary, straight-retreat, crossing-weave, and turnback policies; and
- live and initially occluded launcher datalinks.

That preserves 288 variants and 288,000 main-study trials.

## Endurance-derived operational cap

A fixed eight-turn horizon could leave long-endurance missiles unresolved for
reasons unrelated to the rule under study. Every materialized scenario now
sets an `operationalTurnLimit` derived from:

- maximum missile range;
- retained-datalink lifetime when installed;
- missile-local track lifetime when installed; and
- a safety buffer,

with a study-defined minimum. The runner classifies a still-active Missile
Flight at that cap as an explained `OperationalTimeout`. Any nonterminal result
that does not reach the configured cap is `UnexplainedUnresolved` and fails the
variant. Reports retain both classifications rather than hiding them in one
undifferentiated horizon bucket.

## 24-worker scheduler

The Checkpoint 21 runner sent `--jobs 24` into one small variant at a time. That
left most of a 16-core/32-thread host idle. Checkpoint 21a instead schedules
independent variants through a bounded `Parallel.ForEach` queue:

- at most 24 variants execute concurrently;
- every variant uses one inner Monte Carlo worker;
- no nested 24-by-24 parallelism is permitted;
- variant-local directories and accumulators avoid shared write locks;
- discarded trial journals are not written to disk during non-resume runs; and
- canonical results are sorted by stable variant ID after all workers finish.

Trial seeds continue to depend only on the study seed namespace, trial index,
and random-stream ID. Worker count and completion order cannot change the
canonical result hash or common-random-number pairing.

`full-flight-execution.json` and `full-flight-variant-execution.csv` report the
requested worker count, enforced worker limit, peak active workers, total
trials, elapsed time, throughput, and per-variant elapsed time. Timing and
worker telemetry are deliberately excluded from the canonical result hash.

## Statistical comparison scope

The corrected study reports paired terminal-opportunity and effective-hit
marginals for:

- adjacent missile TL values across all policies;
- adjacent target-propulsion TL values for stationary and straight-retreat
  policies, where a monotonic expectation is defined; and
- initially occluded-to-live datalink changes.

Crossing-weave and turnback target-speed comparisons remain reported in the
variant table but are not assigned a simplistic monotonic target-TL rule. The
paired marginal family therefore contains 864 rows. Common random numbers,
Holm correction, and the one-percentage-point practical-effect threshold remain
unchanged.

## Validation

Checkpoint 21a requires:

- 506 engine-independent tests;
- seven deterministic scenarios;
- twenty-nine runner self-tests;
- ordinary stochastic reproducibility at `--jobs 1` and `--jobs 24`;
- full-flight scheduler reproducibility at `--jobs 1` and `--jobs 24`;
- an enforced 24-worker full-flight ceiling with one inner worker per variant;
- 288 full-flight variants passing 1,000 trials each;
- zero terminal-opportunity invariant failures;
- zero unexplained unresolved outcomes;
- all 864 paired marginals verifying common random numbers; and
- zero practical, Holm-significant contradictory marginals.

No mechanical Godot validation is required.
