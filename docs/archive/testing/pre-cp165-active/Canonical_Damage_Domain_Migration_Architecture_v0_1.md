# Canonical Damage-Domain Migration Architecture v0.1

**Checkpoint:** 122  
**Status:** candidate architecture pending native Windows acceptance

## Purpose

Checkpoint 122 converts Star Cluster's canonical damage/defense integer ruler from the historical scale to an exact x2 scale. The migration is not a balance pass. Every currently promoted point-domain quantity is doubled so that one historical point equals two canonical points. CP121 demonstrated exact combat equivalence and showed that odd canonical values can provide useful half-step resolution; CP122 implements the ruler while promoting no odd half-step candidate.

## Canonical point domain

The following quantities use the x2 canonical point domain when active: weapon/warhead DAM, SPEN, APEN; Shield capacity, base/tactical recharge and Shield Armor; Armor Protection and Armor Integrity; Hull; temporary Shield overcapacity; flat Shield/Armor point bonuses; Shield Battery restoration; Ablative Armor point values; and other direct point magnitudes that participate in the same layered-damage arithmetic.

The following do **not** scale: accuracy/guidance/evasion percentages, PDS percentages or Reaction Capacity, range, movement, Tactical Power, Installation Space, ammunition counts, fuel, Sensor/EW ratings, repair-kit counts, component-condition steps, or technology level.

## Damage Control exception

Production Damage Control intentionally remains **1 Hull restored per successful Repair Kit** at the CP122 baseline. This is not exact x2 parity with the historical ruler and is an explicit gameplay decision. Future Hull technology may improve repair yield, but that progression is outside CP122.

The migration parity suite may artificially restore **2 canonical Hull per Repair Kit** solely to prove that the unit conversion itself is exact. That parity-only value must never leak into production Damage Control.

## Critical/H-X exception

Critical/H-X cadence is explicitly deferred. CP122 does not double, halve, remap, or otherwise change the internal critical stream. Critical cadence will be revisited when that system is fully implemented and ready for its own design/validation pass. No CP122 parity claim extends to not-yet-implemented critical-frequency semantics.

## Rounding rule

Degraded Energy damage retains the historical semantic rule after the unit conversion. The old rule was half normal damage, rounded upward in historical damage-point units. Under x2, the result therefore rounds upward to the next complete historical-equivalent unit (the next multiple of two canonical points), capped at the weapon's normal damage so degradation can never increase a future very-small odd packet. Example: historical D3 -> degraded D2 becomes canonical D6 -> degraded D4, not D3.

This scale-aware rounding applies only to damage-domain values. Tactical Power and other non-damage values continue using their existing rounding rules.

## Historical compatibility

Historical numerical authorities and checkpoint scenarios remain immutable. New canonical successors are introduced rather than overwriting v0.1/v0.3 files. Historical ScenarioRunner paths that exercise degraded Energy weapons explicitly request the legacy damage scale. New work should bind to the CP122 canonical authority document and successor catalogs.

## Acceptance gates

CP122 must fail native acceptance unless all of the following hold:

- every declared point-domain field in the canonical successors is exactly 2x its historical counterpart;
- every declared non-point field is unchanged;
- the production Repair Kit restores exactly 1 canonical Hull;
- the parity-only repair fixture restores 2 canonical Hull and matches the historical normalized state;
- degraded Energy damage is exact x2 equivalent for migrated even values;
- layered Shield/Armor/Hull resolution is exact under normalized x2 comparisons;
- historical research defaults still bind to the historical matrix;
- new canonical research can explicitly bind to the successor matrix;
- no odd CP121 half-step value is promoted;
- no critical/H-X cadence change is introduced;
- all Python tests, C# tests, parity fixtures, repository contracts, and JSON parsing pass.
