# Player TL1-TL9 Technology Architecture v0.7

## Purpose

Checkpoint 55 adopts the three-generation progression model agreed after Checkpoint 54a. TL1/TL2 remain frozen. Checkpoint 54a remains frozen sensitivity evidence showing that a second unrestricted main weapon is too large for TL3. TL3 is therefore re-screened as the **mature low-tech cruiser: one main weapon, two AUX Capacity**.

## Three-generation cadence

| Generation | Foundation | Refinement | Maturity | Main Weapon Capacity | AUX progression |
|---|---:|---:|---:|---:|---|
| Low tech | TL1 | TL2 | TL3 | 1 throughout | 1 / 1 / 2 |
| Mid tech | TL4 | TL5 | TL6 | 2 throughout | 2 / 2 / 3 |
| High tech | TL7 | TL8 | TL9 | 3 throughout | 3 / 3 / 4 |

The resulting TL1-TL9 curves are:

- Main Weapon capacity: `1 / 1 / 1 / 2 / 2 / 2 / 3 / 3 / 3`.
- AUX Capacity: `1 / 1 / 2 / 2 / 2 / 3 / 3 / 3 / 4`.

TL1, TL4, and TL7 are foundational architecture changes. TL2, TL5, and TL8 refine the current generation. TL3, TL6, and TL9 are mature culminations. Individual component statistics should improve selectively rather than all jumping at each technology level.

## No arbitrary firing restrictions

A legal installed main weapon behaves normally. The design does not add a special rule saying that an installed second or third battery cannot fire merely to control progression. Tactical Power, ammunition, condition, range, tracking, and targeting eligibility remain the natural constraints.

The TL4 dual-main and TL7 three-main steps are provisional until their transition studies are run. If the TL4 one-to-two weapon transition remains structurally unbalanceable with conservative component statistics, the preferred fallback is one main weapon through TL9 with generational component improvement, not an artificial fire-control prohibition.

## TL3 low-tech capstone screening

Checkpoint 55 uses four deliberately conservative one-main profiles:

1. **TL2-equivalent control** - exact accepted TL2 numbers at TL3, isolating the second AUX point.
2. **Offense-only refinement** - small targeting/accuracy/guidance improvements; damage, penetration, range, movement, and weapon power costs remain unchanged.
3. **Defense-only refinement** - modest Hull, Armor Integrity, and Shield Capacity improvements while offense remains TL2-equivalent.
4. **Mature low-tech candidate** - combines those modest offense/defense changes with +1 reactor output and a small PDS refinement. It still has one main weapon and no damage, penetration, range, or movement jump.

No profile is automatically promoted.

## TL3 two-AUX design space

TL3 keeps the 2 AUX milestone. Checkpoint 55 re-runs the thirteen Checkpoint 54 capacity-2 combinations with **one** main weapon and adds isolated component diagnostics for the thirteen represented TL3 support systems. This separates the value of Shield Booster, Shield Battery, Shield Power Stabilizer, Auxiliary Reactor, PDS, endurance modules, and other support effects from the now-historical dual-main environment.

## Tactical Power envelope

Combat Battery, Power Capacitor, and Auxiliary Reactor are isolated in a one-main TL3 ship under normal conditions and a common 5-TP sustained diagnostic load. The load is diagnostic only; it is not a universal hotel-load rule. Accepted Battery and Capacitor resource semantics remain unchanged.

## Runtime boundary

Checkpoint 55 adds four studies totaling 819 Monte Carlo variants:

- `tl3-itc03-low-tech-capstone-profile-screening`: 102 variants.
- `tl3-aux02-low-tech-capstone-two-capacity-screening`: 585 variants.
- `tl3-aux03-component-isolation`: 78 variants.
- `tl3-pwr02-single-main-power-envelope`: 54 variants.

All 73 ScenarioRunner JSON files present in accepted Checkpoint 54a are SHA-256 frozen. The Checkpoint 54a two-bay studies remain executable historical controls, but they no longer define legal TL3 production capacity.

TL4-TL9 runtime generation remains deferred until the corrected TL3 low-tech capstone is explicitly reviewed.
