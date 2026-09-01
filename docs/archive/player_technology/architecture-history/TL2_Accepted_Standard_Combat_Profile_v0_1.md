# TL2 Accepted Standard Combat Profile v0.1

## Decision

Checkpoint 48 promotes **Armor Step + Conservative Direct Fire** as the accepted standard TL2 combat profile. The machine-readable profile ID is `tl2-production` in `src/StarCluster.ScenarioRunner/Scenarios/AuxiliaryTechnology/tl2-accepted-standard-combat-profile-v0_1.json`.

The promotion follows Checkpoints 45 through 47, which established that the package provides a reasonable one-TL advantage while preserving credible Kinetic, Energy, and Missile roles under competent range control.

## Accepted numerical vector

- Hull: 12
- Armor Integrity: 5
- Armor Protection: 0
- Shield Capacity: 2
- Shield Base Recharge: 1
- Reactor Tactical Power: 6
- Targeting bonus: 12 percentage points
- STL movement: 2 hexes
- Missile movement: 3 hexes
- Kinetic direct-fire accuracy bonus: 23 percentage points
- Energy direct-fire accuracy bonus: 28 percentage points
- Missile terminal guidance: 60 percent

Weapon damage, penetration, maximum range, power, and ammunition remain in family. The full authoritative vector is stored in the JSON profile.

## Design rationale

The package advances Armor Integrity by one step while leaving Hull and Shield capacity at their TL1 values. Direct-fire accuracy receives the conservative family-consistent increase. Propulsion, reactor, missile guidance, and logistics retain their established TL2 identity.

The result is not intended to make every family equal. Kinetic remains powerful after closing, Energy has a meaningful middle-to-standoff envelope, and Missiles retain the longest reach. Positioning and range control determine which advantage can be expressed.

## Historical controls

`tl2-r45-hull-step-conservative-direct-fire` and all earlier candidates remain frozen analytical controls. They are not standard player values.

## Information boundary

Opponent-aware range control remains an ideal calibration doctrine. Production AI must later act only on capabilities it legitimately knows, estimates, or observes during combat.
