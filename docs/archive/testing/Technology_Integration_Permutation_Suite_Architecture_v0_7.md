# Technology Integration Permutation Suite Architecture v0.7

## Purpose

This is the standing architecture for reusable technology-integration coverage. It defines **what combination space exists and how broad screens enter the combat consumer**; it is not a checkpoint result log and does not promote gameplay values by itself.

Detailed simulation methodology remains in `docs/development/Simulation_Development_Guidelines.md`. Current game mechanics remain in the active Game Concept. Current/candidate technology properties remain in the Technology Architecture Matrix and machine profiles.

## Cross-TL legal-build foundation

The current foundation enumerates a 35-Space cruiser shell with independent technology choices for weapon family/profile, reactor, Tactical Computer, Sensor, Shield, Armor, ECM, and ECCM. Construction legality follows actual Installation Space and explicit compatibility/prerequisite rules. Simultaneous Tactical Power sufficiency is **not** a construction-legality filter.

The first bounded envelope contains four weapon choices and seven binary TL1/TL2 axes, yielding 512 legal technology combinations. Enumeration retains complete-era, mixed-generation, tall/wide-like, awkward, and apparently suboptimal legal combinations rather than pruning them by intuition.

The potential pairing envelope is larger than the first Monte Carlo screen. The architecture therefore separates:

1. deterministic legal-build enumeration;
2. deterministic pairing/recipe selection or later stratified sampling;
3. generated integrated-study output;
4. actual-consumer preflight;
5. one-trial full-pipeline smoke; and
6. bounded substantive screening with escalation only where evidence warrants it.

## Current bounded executable slice

The current screen selects 13 named recipes spanning TL1 family anchors, contemporary TL2 working packages, isolated Kinetic subsystem advances, grouped information-control advancement, grouped power/defense advancement, and a modern-nonweapon mixed build. Six pairing groups expand to 64 ordered logical pairings.

Each logical pairing runs three geometry/order contexts:

- fixed Range 3 / simultaneous;
- dynamic TrackAwareOpponentRange / Side A moves first; and
- dynamic TrackAwareOpponentRange / Side B moves first.

This produces 192 generated combat variants. The slice is deliberately representative rather than exhaustive; all 512 legal builds remain visible in the deterministic enumeration output for later sampling and expansion.

## Attack-eligibility / combat-activity guard

Physical weapon range is not sufficient to define a usable movement goal. Track quality, Sensor/EW state, missile guidance/terminal requirements, Tactical Power, and other current prerequisites may make a target attack-ineligible.

When the fixed Range-3 reference materially fires a direct-fire weapon or launches missiles, each paired dynamic context must retain nonzero activity for that same attack type unless the study explicitly declares a withdrawal/search/no-fire control. This prevents movement doctrine from converting a valid combat lane into a false 40-turn/no-fire result merely by moving outside its own usable information/guidance envelope.

## Progression interpretation

A locally validated candidate remains provisional. The standing suite must reveal whether complete TL packages, mixed-generation builds, and family-specific subsystem advances create discontinuities, dead zones, dominant combinations, or unexpected synergies elsewhere in the TL lattice.

Shared axes remain measurement tools. They do not require symmetric family progression or a uniform TL stat ladder.
