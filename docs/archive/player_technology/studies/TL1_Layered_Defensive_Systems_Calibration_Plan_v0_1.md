# TL1 Layered Defensive Systems Calibration Plan v0.1

## Purpose

Checkpoint 31 corrects the first executable PDS assumptions from Checkpoint 30 and then adds the remaining non-overload TL1 defensive systems needed before reactor-envelope balancing. The pass remains a single-engagement calibration. It does not introduce drydock turnaround, between-engagement resupply, campaign logistics, component damage, overload, held main-weapon interception, or multiple installed PDS components.

The core question is no longer merely whether PDS fires. The study asks how three causally distinct defensive layers interact:

1. **Solution access:** Passive Sensors, Active Sensors, ECM, and ECCM determine whether a Current/Firm firing solution exists.
2. **Terminal interception:** Kinetic PDS, AMM PDS, and Energy PDS attack incoming Missile Flights after a legal threat reaches the terminal envelope.
3. **Damage-layer defense:** Evasive Maneuvering, Shield Armor from a Shield Hardener, tactical shield recharge, and finite Shield Battery restoration reduce or repair damage that reaches the ship.

Keeping these layers distinct prevents ECM from becoming a generic hit penalty, PDS from becoming a sensor substitute, or shield support from being credited for attacks that never obtained a legal solution.

## Corrected ammunition and Ready Package contract

All ammunition quantities are total carried capacity. One package begins loaded in the weapon or PDS installation; the remainder is reserve. After an attack, the automatic loader immediately moves one reserve package into the Ready position when available.

| Ammunition-fed system | Total capacity | Initially Ready | Initial reserve |
|---|---:|---:|---:|
| TL1 Kinetic Cannon | 100 | 1 | 99 |
| TL1 Missile Launcher | 25 Missile Flights | 1 | 24 |
| TL1 Kinetic PDS | 50 packages | 1 | 49 |
| TL1 AMM PDS | 25 interceptors | 1 | 24 |

The Ready Package is included in, not added to, total capacity. Energy weapons and Energy PDS remain ammunition-independent. The calibration records single-engagement expenditure and remaining capacity; campaign endurance may be extrapolated from those results without inventing an untested resupply interval.

## Corrected PDS fire-control contract

Each PDS installation remains capable of local autonomous operation. Loss of the ship Targeting Computer therefore removes assistance but does not disable PDS.

- Disabled, Destroyed, or unavailable Targeting Computer: local base chance only.
- Degraded TL1 Targeting Computer: local base chance +5 percentage points.
- Operational TL1 Targeting Computer: local base chance +10 percentage points.
- The computer bonus changes interception resolution only. It does not add Reaction Capacity, create an interception window, expand the terminal envelope, or make an otherwise illegal target eligible.

The equal-TL local bases remain provisional:

| PDS family | Readiness | Reaction Capacity | Local base | Ammunition |
|---|---:|---:|---:|---:|
| Kinetic PDS | 1 TP | 1 | 35% | 50 total |
| AMM PDS | 1 TP | 1 | 50% | 25 total |
| Energy PDS | 2 TP | 1 | 40% | Unlimited conventional shots |

Own Evasive Maneuvering applies the -5 percentage-point firing penalty to ship-mounted Kinetic and Energy PDS. It does **not** penalize an AMM after launch because the interceptor maneuvers and guides independently. Target EvM does not separately penalize PDS because the target of the interception is the Missile Flight.

## Sensor and electronic-warfare contract

The Checkpoint 31 duel fixture assumes the contact is detected and isolates whether it is discriminated precisely enough for a Firm firing solution.

- Passive TL1 Sensors provide Firm through range 3.
- Active Sensors at 1 TP provide Firm through range 5.
- Active Sensors at 2 TP provide Firm through range 6.
- Active Sensor power changes range, not accuracy or maximum track quality.
- Powered TL1 ECM has rating 1 and reduces an opposing observer's effective Firm range by one hex.
- Powered TL1 ECCM has rating 1 and cancels one opposing ECM rating for that observer-target evaluation.
- Effective ECM is `max(0, target ECM - observer ECCM)`.
- ECM and ECCM affect the hard Firm-solution gate. After Firm exists, they do not impose a second accuracy penalty.
- A Targeting Computer improves attack or PDS resolution after Firm exists; it does not create Firm.

The fixed calibration doctrine commits Powered systems in this order: PDS readiness, ECM, ECCM, Active Sensors, Shield Hardener, EvM, tactical shield recharge, and finally the main weapon. This is a reproducible study doctrine, not a permanent player-control restriction. Actual committed power is reported so a request that cannot fit inside the unchanged 5 TP envelope is visible rather than silently supplied.

## Shield-defense contract

- Base shield recharge occurs at Turn Refresh.
- Tactical recharge then restores one Shield per TP, up to the existing two-TP cap and never beyond missing capacity.
- A Powered Shield Hardener supplies one Shield Armor while active. Shield Armor reduces shield-facing damage after SPEN bypass and before Shield Capacity loss.
- The TL1 Shield Battery carries three charges and restores three Shield per charge.
- A standard battery may discharge at most one whole charge per turn.
- In this fixed doctrine, a battery automatically discharges at Turn Refresh when the shield was collapsed at the beginning of that turn, after base recharge. It does not raise a shield during the same turn in which that shield collapsed.
- Excess battery restoration is wasted. The battery is not overloadable.

## Executable sweep

The new study contains **171 variants at 10,000 trials each**, divided into five explicit categories:

| Category | Variants | Coverage |
|---|---:|---|
| Accepted controls | 6 | Kinetic, Energy, and Missile mirrors at ranges 0 and 2 with the Firm gate enabled |
| PDS rule corrections | 36 | All three PDS families at +0/+5/+10 Targeting Computer assistance, steady and EvM postures, with reciprocal side swaps |
| Sensor/EW boundaries | 57 | Passive, Active-1, and Active-2 limits; ECM edge/denial cases; ECCM restoration; all three weapon families |
| Shield defenses | 36 | Shield Hardener, tactical recharge 1/2, Shield Battery, and Hardener-plus-recharge against Kinetic, Energy, and Missile attacks |
| Layered defenses | 36 | PDS+ECM, PDS+EvM, PDS+Hardener, full five-TP packages, and two-flight saturation for all PDS families |

All asymmetric cases have reciprocal side swaps. Mirror and paired gates test side-order neutrality for outcomes, Firm/denied turns, and PDS interceptions. Direct/terminal attack rolls and PDS rolls retain separate deterministic random streams.

## Required reporting

Each variant reports at least:

- win, mutual-destruction, and unresolved rates;
- mean duel duration;
- direct-fire hits, Missile Flights launched, terminal attacks, and missile hits;
- PDS attempts, interceptions, and finite ammunition expenditure;
- Firm-track and track-denied turns;
- committed Active Sensor, ECM, ECCM, PDS, and Shield Hardener power;
- tactical shield-recharge power and Shield Battery charges used;
- remaining Hull, main ammunition, and finite PDS ammunition.

These outputs distinguish hard denial, interception, damage mitigation, restoration, power starvation, ammunition exhaustion, and genuine combat stalls.

## Explicitly deferred

Checkpoint 31 does not calibrate:

- alternative reactor envelopes, Auxiliary Reactors, Combat Batteries, or Capacitor Banks;
- overload, Strain, or overload Failure Tables;
- held main-weapon interception;
- multiple PDS installations or player-selected reaction allocation;
- probabilistic sensor resolution, stealth, cooperative ECM screens, environmental interference, or active-emission detection bonuses;
- missile peer guidance, seeker-specific terminal ECCM, or datalink interruption inside this compact duel fixture;
- component degradation, destruction, Damage Control, or repair;
- multi-engagement logistics or drydock turnaround;
- final weapon or defensive-system balance values.

Reactor-envelope calibration follows only after the completed defensive suite reveals which legal combinations naturally compete for the existing 5 TP pool.
