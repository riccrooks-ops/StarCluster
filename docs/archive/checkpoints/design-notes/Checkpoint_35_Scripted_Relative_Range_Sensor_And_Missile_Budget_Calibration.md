# Checkpoint 35 - Scripted Relative-Range, Sensor, and Missile-Budget Calibration

## Purpose

Checkpoint 35 measures the first movement-dependent combat effects without defining a complete tactical movement system. Scenarios use a typed shared relative range and an optional turn-indexed schedule. The standard pattern begins at one range, changes separation at the start of Turn 2, and holds the new distance.

The abstraction preserves the future design space for absolute coordinates, headings, acceleration, pathfinding, board-edge tactics, and higher-TL pursuit.

## Core contract

- legal relative separation is 0-10 hexes;
- changes are unique, strictly ordered, and applied at the start of the named turn;
- the new range governs sensor/EW, Tactical Power, direct fire, missile launch, and missile resolution during that turn;
- no separate automatic movement track-loss penalty is added;
- live Missile Flights add the separation delta to remaining route;
- cumulative traveled distance remains spent against Maximum Range;
- a route change never restores missile range;
- new launches begin at the current separation;
- Held Main resolves before PDS on the actual arrival turn;
- one main launcher launches one Flight per turn;
- ordinary TL1 PDS retains Reaction Capacity 1.

## Focused study

`tl1-rc01-scripted-relative-range-study.json` contains 75 variants:

| Category | Variants |
|---|---:|
| Static controls | 9 |
| Scripted direct fire | 12 |
| Missile range budgets | 16 |
| Sensor/EW | 20 |
| Interception timing | 12 |
| Scalar outrun proofs | 6 |

Fifty-four asymmetric variants form 27 exact reciprocal side-swapped pairs. The study reports outcomes, duration, initial/final range, applied changes, Firm/denied track rates, launches, missile hits, range exhaustion, reroutes, Held and PDS activity, and remaining Hull.

## Mechanical gates

The compiled runner requires:

- exact study cardinality and category counts;
- exact reciprocal pairs;
- an exact-exhaustion Flight to consume its range without impact;
- passive track loss after crossing its range boundary;
- ECCM restoration at the selected boundary;
- faster-target pursuit to exhaust the Flight without impact;
- faster-missile pursuit to reach the target;
- delayed Held Main use and PDS fallback against surviving Flights.

## Deferred

Checkpoint 35 does not define absolute board coordinates, headings, facing, acceleration, turn radius, pathfinding, collision, occupancy, player movement commands, board edges, multiple independently moving ships, or higher-TL missile propulsion balance.
