# Technology Integration Permutation Suite Architecture v0.6

## Purpose

This standing architecture defines reusable integration axes. It is not a checkpoint history and does not require the full Cartesian product at every pass. Focused studies activate only the dependency-relevant slice; locally validated candidates are then carried into broader mixed-TL validation.

## Core rules

- Preserve subsystem-family identity. Shared sensitivity axes make comparisons clean; they do not require symmetric progression.
- Keep Power/Reactor, Shield, Armor AP, Armor AI, information control, degraded-fire permission, doctrine, weapon family, and weapon-penetration package independently selectable where the runtime supports them.
- Treat legal construction and simultaneous Tactical Power sufficiency separately.
- Retain extreme but legal builds so screening can discover real boundaries rather than curator assumptions.
- Use common random streams for candidate/control pairings when practical.
- Run actual-consumer preflight and a one-trial full-pipeline smoke before substantive Monte Carlo.
- Statistical outcomes are review evidence; deterministic gates verify shape, routing, isolation, and mechanical invariants.

## Current reusable progression packages

- TL1 and locally validated TL2 information-control packages.
- Peak-Fission 5-TP and Early-Practical-Fusion 6-TP reactor packages.
- Shield Capacity 2 reference and Shield Capacity 3 local working candidate; Shield 4 remains an upper sensitivity only.
- Armor AP0/AI4 reference, AP0/AI5 local working candidate, AP1 deferred candidate, and AP1/AI5 upper integration sensitivity.
- Family-specific Kinetic/Energy/Missile penetration packages exposing control, APEN sensitivity, SPEN sensitivity, and combined upper sensitivity without implying universal progression.

## Current activated slice

The current weapon-penetration slice contains **288 variants**: three attacker families x four penetration profiles x four Shield/AP target packages (AI5 fixed) x two information-control environments x three geometry/order contexts. Both sides hold Reactor 6 so penetration, not old-reactor power starvation, is the causal variable.

## Cross-TL direction

The suite is evolving toward arbitrary legal build enumeration and pairing across subsystem TLs. It must eventually support mixed-TL subsystems, complete TL-vs-TL ships, tall/wide research, and unusual legal specialization. Because the possible pairing count will grow rapidly, enumeration and cheap screening may be exhaustive while expensive Monte Carlo is escalated selectively to boundary, outlier, uncertain, and promotion-relevant regions.

Detailed methodology belongs in `docs/development/Simulation_Development_Guidelines.md`.
