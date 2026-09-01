# Technology Integration Permutation Suite Architecture v0.1

## Purpose

This architecture defines a reusable, data-driven scenario-matrix pattern for cross-subsystem technology calibration. It responds to the growing interaction surface among Tactical Computers, Sensors, ECM/ECCM, Tactical Power, weapons, PDS, movement, and later-TL capabilities without turning every checkpoint into a new bespoke simulator.

## Core rule

A standing permutation suite declares reusable **axes** and **frozen dimensions**. A focused checkpoint selects the smallest Cartesian block that answers its present question. The suite is extended when an interacting dependency changes; unrelated axes are not rerun merely because they exist.

The machine-readable definition is `technology_integration_permutation_suite_v0_1.json`.

## Checkpoint 81 block

Checkpoint 81 uses five axes:

- Side-A direct-fire family: Kinetic / Energy.
- Opponent family: Missile / Kinetic.
- Geometry: fixed range 3 / dynamic Side-A-first / dynamic Side-B-first.
- EW response package: clean Firm reference / old-Sensor + ECCM2 / DR1 + ECCM1 / explicit -25 degraded-fire fallback.
- Side-A Tactical Computer ordinary targeting assistance: +10 / +12 percentage points.

The resulting block is **96 variants**. Within every context and EW package, +10 and +12 share the integrated runner's `comparisonGroup`, so corresponding trials use the same deterministic random streams. This common-random-number pairing improves sensitivity to the relatively small +2 percentage-point computer change without making a win-rate target a release gate.

## Frozen dimensions

Checkpoint 81 holds the accepted 5-TP production reactor reference, TL1 weapon/defense/movement values, TL1 -25 degraded-fire penalty, Evasive Compensation 0, Sensor range, Sensor/EW overload behavior, and ordinary missile Firm-terminal architecture. DR1/ECM2/ECCM2 remain TL2 working candidates derived from CP79a/CP80 evidence rather than production data.

## Extension policy

Future checkpoints should extend this suite or create a sibling standing suite when the same technology-integration question recurs. Do not force every subsystem into one giant Cartesian product: preserve causal interpretability, declare dependency triggers, run actual-consumer preflight plus one-trial smoke after structural changes, and keep balance outcomes as human-reviewed evidence.
