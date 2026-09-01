# TL2 Opponent-Aware Range Control and Promotion Decision v0.1

## Purpose

Checkpoint 47 determines whether the provisional TL2 weapon families remain credible choices when movement policy considers both the ship's own weapon envelope and the observed opponent envelope. It changes no weapon characteristic, component value, or technology level.

## Profiles

- **Leading provisional reference:** `tl2-r45-armor-step-conservative-direct-fire`
- **Structural control:** `tl2-r45-hull-step-conservative-direct-fire`

Neither profile is production data and successful execution does not promote either profile automatically.

## Opponent-aware rule

The candidate policy is generic rather than family-specific.

1. If the ship's weapon outranges the observed opponent, seek the outer edge of the ship's useful firing envelope.
2. If the ship is outranged, seek the outer edge of its established preferred band while applying pressure.
3. If maximum ranges are equal, retain the established preferred-band target.
4. If the opponent envelope is unknown, fall back to the established family-only Preferred Range doctrine.

For the current families this requests Kinetic range 2, Energy range 5 against Kinetic, Energy range 4 against Missile, and Missile range 6 against Kinetic or Energy.

## Study grid

The primary study contains exactly 148 variants.

- 72 retained family-only Preferred Range controls: 2 profiles x 3 unordered family pairs x 2 orientations x starting ranges 1-6.
- 72 opponent-aware lanes with the same profile, family, orientation, and starting-range coverage.
- 4 fixed Range 5 Kinetic/Energy controls: 2 profiles x 2 orientations.

All dynamic variants use paired random streams and disable disengagement.

## Interpretation

The study does not require equal family results. It asks whether tactical starting range and range-control doctrine create credible advantages for more than one family. Close-range Kinetic superiority and long-range Energy or Missile superiority are acceptable. Broad compulsory choice or practical irrelevance remains the warning condition.

Policy telemetry records requested range and decision basis so design conclusions can distinguish tactical doctrine from weapon statistics.

## Promotion boundary

Checkpoint 47 may provide evidence for a later human decision to adopt Armor Step plus Conservative Direct Fire as the provisional TL2 reference. The runner does not promote a profile, weapon value, or AUX family automatically.
