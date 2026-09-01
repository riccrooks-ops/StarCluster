# TL1 Sensor Discrimination Resistance and Burn-through Study v0.1

## Current architecture interpretation

This file is retained as historical Sensor/EW evidence from before the current degraded-fire ownership split. Current architecture keeps the sensor result separate: track quality is resolved first from sensing, ECM, ECCM, discrimination resistance, and burn-through. Only afterward may a specific degraded-fire-capable direct-fire weapon use an Approximate track, with the numerical penalty supplied by the ship Tactical Computer/fire-control profile. The current TL1 computer working value is -25 percentage points. The sensor study itself does not grant degraded fire, and ordinary missiles remain Firm-terminal by default.

## Purpose

Checkpoint 70a showed that increasing normal TL1 ECM Tactical Power cost from 1 through 5 TP does not reliably create healthy counterplay. The underlying discrimination effect remains a hard Firm-track veto until the jammer reaches a weapon/sensor power cliff; high-cost lanes may become stalemates, while a missile jammer can continue attacking because normal missile launch power is zero.

Checkpoint 71 therefore leaves normal ECM/ECCM at rating 1 / 1 TP and tests a more physical discrimination model: intrinsic **Sensor Discrimination Resistance** plus range-derived **Burn-through Resistance** oppose ECM after ECCM.

## Provisional resolver

The engine resolves the observation envelope and emission-assisted contact first. It then computes:

`Jamming Margin = max(0, ECM - ECCM - Sensor Discrimination Resistance - Burn-through Resistance)`

A positive remaining Jamming Margin may degrade an otherwise Firm observation to Approximate. A zero margin leaves the underlying observation unchanged. None of these terms extend sensor range or promote an underlying Approximate observation to Firm.

For the CP71 TL1 experiment:

- Balanced-0 remains the fixed envelope: Passive 1/3, Active 3/4 at 1 TP, Overload 4/5 (overload disabled in this study);
- intrinsic Sensor Discrimination Resistance = **0**;
- same-hex Burn-through Resistance = **+1**;
- Burn-through Resistance at all ranges greater than zero = **0**;
- normal ECM = rating **1 at 1 TP**;
- normal ECCM = rating **1 at 1 TP**;
- same-hex LOS remains unoccludable;
- ECM emission provenance remains visible;
- stronger future ECM is allowed to overcome insufficient resistance.

Old Sensor/EW catalogs remain reproducible because the new profile fields default to zero when absent. CP69/CP70 inputs therefore preserve their historical no-burn-through behavior if rerun.

## Matrix and paired evidence

Study ID: `tl1-itc13-sensor-discrimination-burnthrough`.

The study reuses the nine CP70a geometry/family contexts but keeps only the cost-1 packages:

- clear/no EW;
- Side-B ECM 1 with no Side-A ECCM;
- Side-B ECM 1 with matching Side-A ECCM 1.

Six operational contexts use Kinetic-vs-Missile, Energy-vs-Missile, and Kinetic-vs-Energy under both movement orders. Three fixed point-blank contexts use Kinetic-vs-Missile, Kinetic-vs-Energy, and Energy-vs-Kinetic at range zero with no movement. This produces **27 variants / 270,000 substantive trials**.

CP71 deliberately keeps the CP70a `masterSeed` and each context's `comparisonGroup`. The integrated runner derives stochastic streams from `comparisonGroup`, so CP71 lanes are paired to the corresponding CP70a cost-1 lanes while changing only the Sensor/EW catalog semantics.

## What should change

At fixed range zero, ordinary ECM 1 should no longer automatically degrade an otherwise Firm observation because +1 burn-through cancels its positive margin. Direct-fire opponents should therefore regain legal firing opportunities without requiring ECCM.

## What should not change

At range one and beyond, the provisional burn-through term is zero. Uncountered ECM 1 must remain capable of degrading Firm to Approximate. ECCM remains a specialized counter, and ECM remains conspicuous rather than reducing physical sensor reach.

The study has no target win-rate gate. The relevant evidence is Firm/Approximate track time, direct-fire eligibility, ECM/ECCM power commitment, geometry, combat outcomes, and any new family asymmetry.

## Deferred degraded fire

The Concept now records weapon-specific degraded fire for future design: selected direct-fire weapons may eventually carry an Approximate-Track/Volume-Fire trait that allows firing into an estimated volume at a substantial penalty. Current architecture assigns that numerical penalty to the ship Tactical Computer/fire-control profile rather than to the weapon. This is not universal, is not implemented in CP71, and does not replace the separate missile datalink/navigation-sensor/seeker architecture.
