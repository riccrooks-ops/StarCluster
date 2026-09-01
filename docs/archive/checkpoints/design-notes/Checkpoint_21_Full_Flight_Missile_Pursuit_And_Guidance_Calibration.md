# Checkpoint 21 - Full-Flight Missile Pursuit and Guidance Calibration

## Purpose

Checkpoint 21 extends the accepted headless simulation host from terminal-only
calibration to complete pre-existing-flight, turn-by-turn pursuit. It measures
outcomes per launched Missile Flight after target movement, route recomputation,
datalink updates, onboard sensing, range expenditure, Search/Wait, terminal
PDS, and terminal resolution have all executed through `StarCluster.Core`.

The pass does not add Godot controls and does not promote the provisional TL
catalog to final game rules.

## Authoritative setup

Each materialized scenario uses the shared scenario initializer. It creates the
map and ships, seeds launcher and target intelligence, reconstructs one
pre-existing Missile Flight with an adjacent three-hex travel history and a
retained launcher report, refreshes ordinary tracks, and then begins Turn 1
Movement.

The missile and target are placed away from the star so the live-link control
cannot be accidentally occluded. Occluded variants add a short planet screen
between launcher and Missile Flight while preserving a valid already-flown
route around the screen. The target and missile remain on the far side of that
screen, allowing autonomous sensing without exposing the launcher link.

A scenario may set `stopWhenAllMissilesTerminal`. The runner then stops its
script immediately after all initialized Missile Flights reach terminal flight
states; unused later-turn actions are not executed.

## Matrix

The study crosses:

- four capability profiles: command-guided, seeker-only, sensor-only, and
  sensor plus seeker;
- missile TL 2, 4, and 6;
- target propulsion TL 2, 4, and 6;
- stationary, straight-retreat, lateral, and reversal target policies; and
- live and occluded launcher datalinks.

This produces 288 variants. The acceptance run uses 1,000 trials per variant,
for 288,000 total trials with `--jobs 24`.

The target moves first in each turn. The Missile Flight then executes one normal
Missile / Interception action. Route planning, per-entered-hex sensing,
guidance arbitration, fuel/range accounting, terminal-entry PDS,
pre-attack PDS, and terminal resolution remain Core responsibilities.

## Provisional movement values

The Checkpoint 20 TL catalog now also declares ship movement allowances:

- TL 1-2: 1 hex per turn;
- TL 3-4: 2 hexes per turn;
- TL 5-6: 3 hexes per turn;
- TL 7-8: 4 hexes per turn; and
- TL 9: 5 hexes per turn.

These values are experimental inputs. They are not yet permanent hull or
propulsion rules.

## Reporting

`pursuit-calibrate` produces compact JSON and CSV reports containing:

- probability of reaching a terminal opportunity;
- effective-hit probability per launched Missile Flight;
- interception, Search/Wait, range exhaustion, self-destruction, dud, miss, and unresolved-horizon rates;
- blocked datalink and retained-report-expiration rates;
- fresh-datalink, retained-datalink, and local-sensor guidance usage;
- active missile-sensor usage;
- average turns, missile actions, route replans, distance, total fuel, and
  stationary-search fuel; and
- relative missile/target speed class.

The runner uses the accepted common-random-numbers contract. It reports paired
marginals for terminal opportunity and effective hit across adjacent missile
TL, adjacent target-propulsion TL where a monotonic direction is meaningful,
and occluded-to-live datalink changes. Holm correction and the one-percentage-
point practical threshold remain unchanged.

The reversal policy is reported but is not assigned a monotonic target-speed
expectation because a faster reversal can alternately improve and worsen
geometry.

## Validation

Checkpoint 21 requires:

- 506 engine-independent tests;
- seven deterministic scenarios;
- twenty-two runner self-tests;
- worker-independent stochastic hashes at `--jobs 1` and `--jobs 24`;
- 288 full-flight variants passing preflight and execution;
- shared-stream verification for every paired marginal; and
- zero practical, Holm-significant contradictory marginals.

No mechanical Godot validation is required.
