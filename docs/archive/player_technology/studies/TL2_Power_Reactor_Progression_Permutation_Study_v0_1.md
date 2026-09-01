# TL2 Power / Reactor Progression Permutation Study v0.1

## Purpose

Checkpoint 83 adds **Power / Reactor** as a first-class axis in the standing Technology Integration Permutation Suite. The first current-architecture question is deliberately narrow: revalidate the historical **6 Tactical Power** TL2 reactor-output candidate as an **Early Practical Fusion** hypothesis against the accepted TL1 **5 Tactical Power Peak-Fission** reference.

The study does **not** promote a production TL2 reactor. It tests whether a one-point Operational-output increase at the same 6-Space reactor footprint expands the contemporary combat-package envelope without erasing meaningful Tactical Power pressure.

## Candidate isolation

The paired candidate changes only Side A normal reactor output:

- TL1 control: **5 TP**, 6-Space Main Reactor reference;
- TL2 candidate: **6 TP**, 6-Space Main Reactor study candidate;
- Side B remains at **5 TP**;
- Side A Tactical Computer remains the validated TL2 **+12 pp** working candidate;
- degraded-fire computer penalty remains **-25 pp**;
- Evasive Compensation remains **0**;
- DR1 / ECM2 / ECCM2 information-control working values are reused where the scenario package calls for them;
- Sensor range and Sensor/EW overload behavior remain unchanged;
- reactor Degraded/Disabled output, overload, efficiency, storage, auxiliary-reactor behavior, and Space reduction remain deferred.

The 6-TP value is therefore an **Operational-output candidate**, not a complete TL2 Fusion reactor profile.

## Standing-suite slice

The study uses **96 variants**: 12 combat/geometry contexts x four information-control environments x two reactor outputs.

Contexts:

- Side A direct-fire family: Kinetic or Energy;
- opponent family: Missile or Kinetic;
- geometry: fixed range 3, dynamic Side A first, or dynamic Side B first.

Information-control environments:

1. `firm-reference` - clean Firm control;
2. `wide-eccm2` - old Sensor + ECCM2 brute-force Firm restoration under ECM2;
3. `tall-dr1-eccm1` - contemporary DR1 + ECCM1 Firm-restoring path under ECM2;
4. `degraded-p25` - explicit study-only weapon capability using the -25 Approximate-track fallback with no ECCM.

Each environment is paired at `r5` and `r6` using the same `comparisonGroup`, preserving common random streams where the consumer permits it.

## Questions for review

The release gates validate configuration and mechanics only. Human review should examine:

- where 6 TP materially reduces insufficient-power prevention;
- whether Energy/Missile and other high-demand packages gain substantially more than low-demand packages;
- whether the contemporary DR1 + ECCM1 route remains attractive rather than becoming irrelevant once power rises;
- whether the wide old-Sensor + ECCM2 route becomes viable without becoming a universally superior substitute;
- whether -25 degraded fire remains a meaningful fallback rather than a preferred replacement for Firm restoration;
- whether the extra TP simply erases all interesting power choices in clean/direct-fire contexts;
- whether one 6-Space/6-TP reactor meaningfully expands output density relative to one 6-Space/5-TP reactor without requiring an arbitrary ban on multiple older reactors.

## Capability-frontier / stacking interpretation

The candidate is allowed to coexist with mature TL1 reactors. Two TL1 reactors would provide more total output than one TL2 candidate, but would consume **12 Space instead of 6 Space** and therefore pay the real ship-design opportunity cost. CP83 does not add an anti-stacking restriction merely to force Early Fusion to dominate.

## Promotion boundary

No value is automatically promoted by this study. A successful run may support carrying **6 TP Operational at 6 Space** forward as a validated TL2 Power/Reactor working candidate. All other TL2 reactor characteristics remain separate future design questions unless explicitly promoted later.
