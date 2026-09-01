# Checkpoint 55 - Three-Generation Capacity and TL3 Low-Tech Capstone

## Purpose

Checkpoint 54a showed that adding a second unrestricted main weapon is an era-scale performance change, not a modest TL3 refinement. Checkpoint 55 therefore changes the long-range capacity architecture and re-screens TL3 as the mature low-tech cruiser.

This pass is candidate-only. Successful execution does not automatically promote a TL3 standard profile, AUX combination, power-support value, TL4 dual-main architecture, or TL7 third-main architecture.

## Frozen boundary

All **73 ScenarioRunner JSON files** present in accepted Checkpoint 54a are SHA-256 locked before the new studies run. All Checkpoint 54a stages remain in the workload as historical/regression evidence. The new Checkpoint 55 scenario files are additive.

TL1 and TL2 remain frozen for isolated tuning.

## Three-generation capacity direction

Normal main-weapon capacity:

- TL1-TL3: **1**
- TL4-TL6: **2**
- TL7-TL9: **3**

Normal AUX Capacity:

- TL1: 1
- TL2: 1
- TL3: 2
- TL4: 2
- TL5: 2
- TL6: 3
- TL7: 3
- TL8: 3
- TL9: 4

TL1/4/7 are generational foundations, TL2/5/8 are refinements, and TL3/6/9 are maturity/capstone levels. TL4's second main weapon and TL7's third remain provisional until their transitions are validated.

No arbitrary fire-control restriction is introduced. Legal installed weapons continue to operate under the existing power, ammunition, condition, range, and targeting rules. If unrestricted dual-main TL4 remains structurally unhealthy even with conservative component progression, prefer the simpler fallback of one main weapon throughout TL1-TL9.

## TL3 standard-profile screen

Four one-main TL3 vectors are evaluated:

1. **TL3 low-tech control** - accepted TL2 numerical combat values with TL3 AUX Capacity 2.
2. **Offense-only refinement** - modest targeting/accuracy/guidance improvements with TL2 defense, reactor, movement, damage, penetration, and range.
3. **Defense-only refinement** - modest Hull/Armor Integrity/Shield improvements with TL2 offense and reactor.
4. **Mature low-tech candidate** - combines the modest offense and defense changes with +1 reactor Tactical Power and a small PDS improvement.

The primary TL3 candidates do not increase direct-fire damage, penetration, maximum range, ship movement, or missile movement. No vector is automatically promoted.

## Two AUX Capacity

Thirteen curated capacity-2 loadouts are re-run with one main weapon. This removes the Checkpoint 54a dual-main throughput confound while preserving the same broad support concepts.

A separate thirteen-component isolation lane compares each TL3 AUX concept against a no-AUX diagnostic in all three weapon contexts and both orientations. The isolation lane should be consulted before changing a composite loadout value.

Campaign/endurance components remain allowed to be weak in a single duel if their repeated-engagement value is already established.

## Tactical Power envelope

Combat Battery, Power Capacitor, and Auxiliary Reactor are tested as isolated support concepts with one main weapon under:

- normal conditions;
- a common **5 TP** sustained diagnostic commitment versus no AUX; and
- pairwise support comparisons under the same stress.

The 5-TP commitment is a calibration stressor, not a universal hotel-load rule.

## Workload

Checkpoint 55 adds **819** Monte Carlo variants:

- 102 TL3 standard-profile variants;
- 585 one-main two-AUX variants;
- 78 AUX component-isolation variants; and
- 54 single-main Tactical Power-envelope variants.

Combined with the frozen Checkpoint 54a corpus, Checkpoint 55 contains **39 stages / 10,696 Monte Carlo variants / 106.96 million trials** at 10,000 trials per variant.

## Acceptance questions

Execution success is necessary but not sufficient. Review must answer:

- Does TL3 feel like a meaningful low-tech capstone without a second main weapon?
- Which of the control, offense-only, defense-only, or conservative mature profiles best defines the TL2-to-TL3 progression?
- Do the thirteen capacity-2 AUX loadouts retain meaningful opportunity cost under one-main combat?
- Which isolated AUX effects explain any combination outliers?
- Do Combat Battery, Power Capacitor, and Auxiliary Reactor become useful but non-compulsory under genuine single-main Tactical Power stress?
- Is the resulting mature TL3 baseline stable enough to test the provisional TL4 dual-main foundation next?

TL4-TL9 executable generation remains deferred until TL3 is explicitly accepted.
