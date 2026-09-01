# Player TL1-TL9 Technology Architecture v0.8

## Purpose

Checkpoint 56 preserves the accepted three-generation capacity cadence and refines TL3 as the mature low-tech cruiser. TL1/TL2 and all accepted Checkpoint 55b evidence remain frozen. The working TL3 numerical base is the modest offense-only refinement; Hull, Armor Integrity, and Shield Capacity are tested one point at a time before any defensive change is promoted.

## Three-generation cadence

| Generation | Foundation | Refinement | Maturity | Main Weapon Capacity | AUX progression |
|---|---:|---:|---:|---:|---|
| Low tech | TL1 | TL2 | TL3 | 1 throughout | 1 / 1 / 2 |
| Mid tech | TL4 | TL5 | TL6 | 2 throughout (provisional) | 2 / 2 / 3 |
| High tech | TL7 | TL8 | TL9 | 3 throughout (provisional) | 3 / 3 / 4 |

Main Weapon capacity remains `1 / 1 / 1 / 2 / 2 / 2 / 3 / 3 / 3`; AUX Capacity remains `1 / 1 / 2 / 2 / 2 / 3 / 3 / 3 / 4`. No arbitrary firing restriction is introduced. If the later TL4 one-to-two weapon transition proves structurally unhealthy, the preferred fallback remains one main weapon through TL9.

## TL3 defensive microsteps

Checkpoint 55b showed that the offense-only TL3 refinement produces a modest progression while the bundled +1 Hull / +1 Armor Integrity / +1 Shield Capacity defensive package is too large. Checkpoint 56 therefore uses `tl3-offense-refinement` as the working base and screens exactly three one-point additions: Hull +1, Armor Integrity +1, and Shield Capacity +1. No candidate is automatically promoted.

## Independent AUX-system rule

Every installed AUX system is independent. A rule such as “one discharge per turn” applies to one installed Combat Battery, not to all Batteries aboard the ship. Two Batteries therefore own separate charge pools and may each discharge once in the same tactical turn. Two Capacitors own separate stored-power and operation states and may each charge or discharge according to their own state. Damage to one installed power AUX does not automatically disable its twin.

Duplicate installations are legal unless a specific physical or rules reason later forbids them. This is a general installation rule, not a special exception for power systems.

## Equal-capacity power comparisons

A one-slot power AUX is not expected to equal a two-slot Auxiliary Reactor by itself. The primary TL3 power comparison consumes the full two-point AUX budget:

- Auxiliary Reactor: capacity 2, +1 sustained TP.
- Battery + Battery: two independent finite reserves.
- Capacitor + Capacitor: two independent reusable time-shifting stores.
- Battery + Capacitor: finite reserve plus reusable time shifting.

Mixed one-slot power + one-slot tactical AUX builds remain valid and are evaluated separately for flexibility rather than raw parity with the Reactor.

## TL3 power characteristic sweep

Combat Battery candidates isolate charge count and magnitude: `B3G1`, `B4G1`, `B3G2`, and `B4G2`. `B3G1` is the existing 3-charge, +1 TP control. Each Battery may discharge at most once per turn, with no encounter cap.

Power Capacitor candidates isolate stored capacity and discharge magnitude: `C2D1`, `C3D1`, `C2D2`, and `C3D2`. Charge rate remains 1 TP per operation for this screen so attribution is clear. Each Capacitor may charge or discharge once per turn and creates no net energy over a complete charge/discharge cycle.

A TL3 Battery or Capacitor candidate does not imply a TL4 successor. Their standard progression may end with low-tech maturity while older equipment remains installable later.

## Checkpoint 56 runtime evidence

Checkpoint 56 adds six studies totaling 1,995 Monte Carlo variants:

- `tl3-itc04-defensive-microstep-screening`: 108 variants.
- `tl3-aux04-offense-base-two-capacity-screening`: 585 variants.
- `tl3-aux05-shield-breakpoint-screening`: 72 variants.
- `tl3-aux06-tl2-tl3-production-progression`: 702 variants.
- `tl3-pwr03-component-characteristic-sweep`: 168 variants.
- `tl3-pwr04-equal-capacity-power-loadouts`: 360 variants.

All 79 ScenarioRunner JSON files present in accepted Checkpoint 55b are SHA-256 frozen before the six new studies are added. The complete Checkpoint 56 workload is 45 stages and 12,691 Monte Carlo variants at the default trial count. TL4-TL9 runtime generation remains deferred.
