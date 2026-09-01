# Star Cluster Technology Integration Permutation Suite Architecture v0.13

## Purpose

Version 0.13 is the standing mixed-TL integration/testing architecture for the next broader development phase. It preserves the accepted generalized TL1/TL2 35-Space construction envelope and deterministic sampled pairing population, adds an explicit legal **single-axis progression lattice**, and moves the broad combat consumer from historical TrackAware/preselected geometry to **Encounter / Adaptive Engage** from opposite map edges.

This document owns testing architecture only. It does not promote component values, define a universal technology score, or choose a production initiative system.

## Preserved legal envelope

The active foundation continues to enumerate:

- 82,944 raw combinations;
- 22,592 legal combat builds;
- 4,672 exact-fill builds;
- 11,328 near-fill builds;
- 6,592 underfilled builds;
- mandatory at least one Main Weapon and one Reactor;
- optional second Main Weapon and/or Reactor subject to normal Space legality;
- optional Sensor, Shield, PDS, ECM, and ECCM installations; and
- explicit non-additive ECM/ECCM redundancy.

No ship is rejected merely because its installed systems cannot all be powered simultaneously. Tactical Power pressure remains an operational/design tradeoff.

## Single-axis progression lattice

A progression edge connects two legal builds that are identical except for one declared TL1->TL2 working option and, for the current lattice, consume the same Installation Space. This gives the review layer an explicit answer to “what changed when this subsystem advanced?” without collapsing a complete ship to one scalar TL.

The v0.13/v0.7 lattice contains **65,648 legal edges** across 12 declared transitions:

| transition | legal edges | exact-fill edges |
|---|---:|---:|
| Kinetic single k1 -> k2 | 5,080 | 888 |
| Kinetic double k1x2 -> k2x2 | 568 | 280 |
| Reactor single r1 -> r2 | 10,160 | 1,776 |
| Reactor double r1x2 -> r2x2 | 1,136 | 560 |
| Tactical Computer c1 -> c2 | 11,296 | 2,336 |
| Sensor s1 -> s2 | 5,888 | 1,472 |
| Shield sh1 -> sh2 | 5,888 | 1,472 |
| Armor a1 -> a2 | 11,296 | 2,336 |
| ECM single ecm1 -> ecm2 | 3,904 | 640 |
| ECM double ecm1x2 -> ecm2x2 | 3,264 | 768 |
| ECCM single eccm1 -> eccm2 | 3,904 | 640 |
| ECCM double eccm1x2 -> eccm2x2 | 3,264 | 768 |

The lattice introduces **no new TL3 values and no new TL2 component statistics**. Energy, Missile, PDS, and Propulsion do not receive invented TL2 transitions merely for symmetry. Propulsion remains outside the current independent lattice until the Technology Matrix explicitly owns a contemporary progression candidate.

The higher-TL endpoint is not required to win every matchup. The lattice exists to expose Pareto improvement, role changes, opportunity costs, integer breakpoints, and possible legacy-stacking domination under the same legal construction rules.

## Preserved sampled population

Version 0.13 preserves the accepted deterministic sample architecture and pair-selection seed **940177**:

- 48 named diagnostic logical pairings;
- 384 statistical logical pairings from 192 unordered base pairs;
- 48 zero-weight diversity logical pairings from 24 unordered base pairs;
- 480 logical pairings total.

Population-representative weights remain attached only to the statistical sample. Named and diversity overlays remain diagnostic evidence.

## Adaptive Encounter consumer

Every generated broad-screen pairing is now exercised in exactly two geometries:

1. `EngageAdaptive` / `SideAFirst` / initial range 10;
2. `EngageAdaptive` / `SideBFirst` / initial range 10.

This produces **960 generated variants**. Ships begin at opposite radius-5 edges, search before contact, and after contact use the same player-information-parity combat blackboard and Engage policy validated in CP97. No opponent weapon-family/TL reach is injected into tactical decisions.

Mover order remains a diagnostic dimension. Version 0.13 intentionally does **not** change initiative or introduce simultaneous movement.

## Adaptive overload availability

The combat blackboard distinguishes range/state keyed overload failure from own-capability exhaustion. A safe-Strain-exhausted ECCM or Active Sensor overload is unavailable until an explicit future rule restores that capability; moving closer or observing a changed enemy emission does not restore Strain. A Tactical Power denial may be reconsidered after a real own-power-state change.

Broad Adaptive Engage screens therefore require zero recorded **safe-Strain-denied overload requests**. This is an AI/capability-reasoning invariant, not a balance target.

## Bounded CP98 study

The candidate CP98 substantive screen uses:

- 480 logical pairings;
- 2 mirrored Adaptive Engage mover orders;
- 960 variants;
- seed 980100; and
- 250 trials per variant = **240,000 substantive trials**.

Before substantive execution, the actual consumer must pass generator preflight, generation, generated-study actual-consumer preflight, and a one-trial-per-variant full-pipeline smoke. Accepted CP96 and CP97 consumers remain one-trial regressions rather than being substantively replayed.

## Release/preflight rules

1. Generator and actual-consumer declarations must agree on study ID, variant count, movement mode/order, initial range, profile catalogs, AI doctrine, and runtime IDs.
2. The progression-lattice counts must be independently reproducible from the declared legal envelope and transition list.
3. Generated build IDs and every referenced technology/AUX/Sensor-EW/doctrine ID must resolve before Monte Carlo.
4. Shared/global telemetry classifications used by full gates must be exercised by actual-consumer preflight through the same helper/binding where practical.
5. New C# mutation surfaces must pass warnings-as-errors native build; static release checks additionally scan common nullable/type-binding failure patterns before packaging.
6. Results report family identity, Space, progression magnitude/direction, information-control dimensions, mover order, standoff/closure, and overload usage explicitly.
7. Win rates and apparent upgrade strength are review evidence. No automatic component promotion or retuning is permitted.

## Next expansion

If the broad Adaptive Engage screen is native-clean, use its results to identify which subsystem interactions merit focused work and which missing technology families deserve reference-informed progression candidates. Do not increase trial counts mechanically; spend additional simulation only where uncertainty or a concrete design question justifies it.
