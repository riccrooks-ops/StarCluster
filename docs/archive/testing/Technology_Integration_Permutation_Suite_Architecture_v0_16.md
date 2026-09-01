# Star Cluster Technology Integration Permutation Suite Architecture v0.16

## Purpose

Version 0.16 keeps the **native-accepted CP99 TL1/TL2 exact-edge architecture as the executable baseline** and adds a registered, machine-readable layer for the complete TL3 base technology candidates. This is the transition from "prove the TL1/TL2 lattice works" to "grow the technology ladder without forcing every subsystem into the same kind of upgrade."

TL3 registration is deliberately **not** runtime activation. Several candidates introduce a new operating capability, an Installation Space change, or an optional component unlock that CP99's same-Space replacement-edge model cannot represent honestly. Those candidates enter the standing architecture now so subsequent work can expand the consumer around the technology design rather than distort the technology design to fit the old consumer.

This document owns testing/integration architecture only. Component intent and candidate values are owned by the Technology Matrix and `tl3_base_technology_candidates_v0_2.json`; game-facing mechanics belong in the Concept.

## Native-accepted executable baseline

CP99 remains the current executable cross-TL reference:

- 35-Space player cruiser;
- mandatory Main Weapon, Reactor, and installed Sensor;
- 82,944 raw TL1/TL2 combinations;
- 11,776 legal builds;
- 2,944 exact-fill, 6,656 near-fill, and 2,176 underfilled builds;
- 37,184 legal TL1 -> TL2 exact same-Space progression edges;
- 181 populated exact-edge strata;
- 362 deterministic lower->higher pairs; and
- 724 mirrored range-10 Adaptive Engage variants.

The CP99 native evidence is accepted. Its exact-edge screen remains a regression/attribution reference; v0.16 does not rerun its 181,000-trial substantive study merely because the technology table now contains TL3 conceptual candidates.

## Initial TL3 registered candidates

| Transition | Progression kind | Space delta | Registered candidate |
|---|---|---:|---|
| Tactical Computer TL2 -> TL3 | Capability addition | 0 | Hold +12 ordinary targeting and -25 Approximate penalty; add +5 pp Evasive Compensation |
| Sensor TL2 -> TL3 | Operating-mode addition | 0 | Hold DR1/passive reach; add Low Active 3/4 @ 1 TP and High Active 4/5 @ 2 TP, no Strain |
| ECM TL2 -> TL3 | Power efficiency | 0 | Hold rating ceiling 2; full-strength normal operation falls from 2 TP to 1 TP |
| ECCM TL2 -> TL3 | Power efficiency | 0 | Hold rating ceiling 2; full-strength normal operation falls from 2 TP to 1 TP |
| Reactor TL2 -> TL3 | Miniaturization | -1 | Hold 6 Operational TP; reduce Main Reactor footprint from 6 Space to 5 Space |
| Shields TL2 -> TL3 | Optional component unlock | +1 if installed | Hold primary Capacity 3; unlock optional 1-Space Shield Hardener committing 1 TP for SA1 |
| Armor TL2 -> TL3 | Protection maturation | 0 | AP0/AI5 -> AP1/AI5 |

Kinetic, Energy, and Missile penetration are held at their current profiles in this core pass. TL3 main-weapon family progression, PDS, STL/FTL, and the broader Auxiliary catalogue remain incomplete by design.

## Why CP99's exact-edge model is no longer sufficient by itself

CP99 intentionally required a same-Space lower/higher edge so a marginal TL1 -> TL2 statistic could be isolated without construction-resource confounding. TL3 introduces two legitimate progression forms that break that assumption:

1. **miniaturization**, where the higher endpoint intentionally releases Installation Space; and
2. **optional capability unlocks**, where a research advance makes a new component available rather than replacing the old component in-place.

Future generalized progression therefore needs an explicit transition type and Space delta. A miniaturization edge should report the freed Space as part of the technology benefit rather than discarding the edge. An unlock edge should compare legal designs under a declared fit policy rather than pretending the optional component is an automatic stat on the primary system.

## Runtime activation boundary

A registered TL3 candidate becomes combat-consumer eligible only after the owning mechanic is represented explicitly:

- Evasive Compensation must be read from the installed Tactical Computer and offset only the ship's own Evasive-fire penalty to a minimum of zero.
- Sensor Low/High Active modes must have explicit power/emission/range semantics; High Active is normal operation and does not consume Strain.
- TL3 ECM/ECCM must support a fixed 1-TP full-strength normal cost without changing the non-additive rating rule.
- TL3 reactor enumeration must accept a 5-Space Main Reactor while preserving 6 TP output and legal legacy-reactor stacking.
- Shield Hardener must remain a separate optional powered support component, not an implicit Shield Generator statistic.
- TL3 Armor must expose AP1/AI5 through the ordinary layered-defense resolver.

Before any substantive TL3 Monte Carlo, the expanded consumer must receive an actual-consumer preflight and a tiny full-pipeline smoke. Mover order remains mirrored while production initiative is unresolved.

## Progression interpretation

The registered TL3 row is intentionally uneven. A technology level may add a mode, reduce power burden, reduce Space burden, unlock a support component, or improve a primary defensive property. It does not need to increase every number. This preserves the tall/wide research model and lets mature technology improve integration instead of behaving like a universal scalar combat multiplier.

No TL3 candidate is automatically promoted by v0.16 or by Checkpoint 101. The immediate purpose is to establish a coherent complete base table and data contract so TL3 can later be implemented by one generalized cross-TL system without forcing the optional catalog to be complete first.


## CP101 complete TL3 base registration

CP101 completes the **base conceptual TL3 row** without enabling TL3 combat consumers. Suite v0.16 registers 16 transition records spanning Hull capacity, Computer/Sensor/EW, reactor miniaturization, STL/FTL performance, Shields/Armor, three Main-Weapon families, and three PDS families. The accepted CP99 foundation v0.8 remains the executable TL1/TL2 consumer.

The new build boundary is explicit: TL3 Hull capacity is 36; 1W/1R uses 27 Space, 2W/1R uses 33, 1W/2R uses 32, and 2W/2R uses 38 and is therefore illegal by 2 Space. Power sufficiency is still not a construction filter. A dual-main single-reactor build may fire both weapons when family/mode costs permit, but it must pay the real opportunity cost in sensing, EW, PDS, hardening, EvM, and recharge.

Additional Auxiliaries, pinnacle legacy-family equipment such as a future Optimum Fission Reactor, specialist weapon variants, detailed missile subcomponents, and production initiative remain outside this base-table registration.
