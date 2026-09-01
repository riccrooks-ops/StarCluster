# Player TL1-TL9 Technology Architecture v0.3

## Purpose

Checkpoint 51 accepts the Checkpoint 50 cruiser-capacity curve as the working installation baseline, corrects all three standard PDS sub-families to TL1 entry, and enables a deliberately limited table-driven runtime bridge for TL1 and TL2. Checkpoint 48-50 runtime scenarios remain frozen regression controls.

## Governing hierarchy

**Family -> Sub-family -> TL-specific implementation** remains authoritative. Availability and effectiveness are separate: a sub-family may exist at TL1 while still having modest accuracy, power efficiency, ammunition efficiency, reliability, or reaction performance. Flavor never creates unapproved target classes or mechanics.

## Accepted cruiser installation capacity

| TL | Weapon Bays | AUX Capacity |
|---:|---:|---:|
| 1 | 1 | 1 |
| 2 | 1 | 1 |
| 3 | 2 | 2 |
| 4 | 2 | 2 |
| 5 | 2 | 3 |
| 6 | 3 | 3 |
| 7 | 3 | 3 |
| 8 | 3 | 4 |
| 9 | 4 | 4 |

The Checkpoint 48 TL2 AUX=2 configuration remains historical screening evidence only. Normal TL1 and TL2 cruisers each have one AUX Capacity.

## PDS entry-floor correction

All three standard PDS sub-families begin at **TL1**:

- Kinetic Point-Defense Battery
- Energy Point-Defense Array
- Anti-Missile Missile Battery

All inherit the common PDS family contract: terminal defensive target eligibility is shared, standard PDS cannot attack enemy ships, and differences come from explicit characteristics such as accuracy, Reaction Capacity, Tactical Power, ammunition or charge use, evasive compensation, and reliability. Boarding-craft eligibility remains part of the family contract even where the current calibration runner only exercises missile threats.

Checkpoint 51 does **not** relabel the old screening values as TL1. The architecture-derived TL1 PDS candidates are deliberately modest, with selective TL2 refinement rather than automatic improvement to every characteristic.

## Limited runtime bridge

`tl1-tl2-standard-runtime-profiles-v0_1.json` is the authoritative runtime table for the accepted TL1 and TL2 standard combat vectors used by the new study. Its TL1 row is required to reproduce the frozen TL1 baseline exactly before execution.

`tl1-tl2-auxiliary-runtime-profiles-v0_1.json` contains only architecture-legal, currently modeled combat AUX candidates for the one-slot TL1/TL2 matrix. Architecture-legal strategic or not-yet-modeled AUX systems remain in the architecture but are not assigned zero-value combat profiles merely to force them into a battle matrix.

The new architecture-derived study covers TL1v1, TL2v2, and both TL1v2 orientations in Kinetic, Energy, and Missile contexts. No-AUX configurations remain isolated diagnostics.

## Preservation and promotion boundary

The Checkpoint 48-50 scenario corpus is retained byte-for-byte. Checkpoint 51 adds a new study rather than mutating the historical AUX screening study. Successful execution proves plumbing, legality, coverage, and evidence generation only; it does not automatically promote a PDS value, AUX profile, higher-TL value, or production loadout. TL3-TL9 table-driven combat generation remains deferred.
