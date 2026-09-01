# Checkpoint 31 - TL1 Layered Defensive Systems Calibration

Checkpoint 31 corrects the PDS fire-control and ammunition assumptions exposed by Checkpoint 30, then adds the remaining non-overload TL1 defensive systems needed before reactor-envelope calibration. The pass is intentionally a **single-engagement** study. It preserves every accepted deterministic and Monte Carlo lane as a control and does not introduce between-engagement resupply, drydock turnaround, overload, held main-weapon interception, or final balance values.

## Accepted design corrections

### Ready Package and finite ammunition

Every finite ammunition-fed main weapon or PDS installation begins with one preloaded Ready Package included in total carried capacity. After an attempt, the automatic loader immediately draws one package from reserve when available.

| System | Total carried | Ready | Reserve |
|---|---:|---:|---:|
| TL1 Kinetic Cannon | 100 | 1 | 99 |
| TL1 Missile Launcher | 25 | 1 | 24 |
| TL1 Kinetic PDS | 50 | 1 | 49 |
| TL1 AMM PDS | 25 | 1 | 24 |

Energy weapons and Energy PDS remain ammunition-independent. The study records remaining ammunition so later campaign endurance can be extrapolated without defining an artificial engagement count or resupply interval.

### PDS fire control

PDS remains self-contained and can operate on its local base chance when the main Targeting Computer is unavailable. After a legal interception opportunity exists, the ship computer may assist resolution:

- Operational: +10 percentage points;
- Degraded: +5 percentage points;
- Disabled, Destroyed, or absent: +0.

The assistance does not create an interception window, increase Reaction Capacity, extend the terminal envelope, or make an illegal target eligible.

Own Evasive Maneuvering applies the accepted -5 percentage-point firing penalty to ship-mounted Kinetic and Energy PDS. AMM PDS is exempt because the interceptor guides and maneuvers independently after launch.

## Added defensive layers

### Sensors and electronic warfare

The compact duel fixture assumes the contact is detected and isolates the Firm-solution gate:

- Passive Sensors provide Firm through range 3.
- Active Sensors at 1 TP provide Firm through range 5.
- Active Sensors at 2 TP provide Firm through range 6.
- Powered TL1 ECM rating 1 reduces the opposing observer's Firm range by one hex.
- Powered TL1 ECCM rating 1 cancels one opposing ECM rating.
- Effective ECM is `max(0, target ECM - observer ECCM)`.
- ECM/ECCM changes legal Firm access only; no second accuracy modifier is applied after Firm exists.
- The Targeting Computer improves resolution after Firm exists but does not create Firm.

### Shield defenses

- A Powered TL1 Shield Hardener supplies 1 Shield Armor.
- Tactical shield recharge restores 1 Shield per TP after base recharge, up to 2 TP and missing capacity.
- A TL1 Shield Battery carries three charges and restores 3 Shield per charge.
- The fixed battery doctrine uses at most one whole charge at Turn Refresh when the shield began that turn collapsed, after base recharge.
- A battery cannot raise a shield during the same turn in which it collapsed; excess restoration is wasted.

## Fixed power doctrine

The reactor remains at the unchanged provisional TL1 output of 5 Tactical Power. The calibration commits Powered systems in deterministic order:

1. PDS readiness;
2. ECM;
3. ECCM;
4. Active Sensors;
5. Shield Hardener;
6. Evasive Maneuvering;
7. tactical shield recharge;
8. main-weapon fire.

This ordering is a reproducible study doctrine, not a permanent player restriction. Actual committed power is reported, so combinations that do not fit are visible as real opportunity costs rather than silently receiving extra power.

## Executable evaluation space

The new study contains **171 variants at 10,000 trials each**:

| Category | Variants | Purpose |
|---|---:|---|
| Accepted controls | 6 | Kinetic, Energy, and Missile mirrors at ranges 0 and 2 with the Firm gate active |
| PDS rule corrections | 36 | Three PDS families across +0/+5/+10 computer assistance and steady/EvM postures |
| Sensor/EW boundaries | 57 | Passive/Active range limits, ECM denial edges, ECCM restoration, and all weapon families |
| Shield defenses | 36 | Hardener, recharge 1/2, Battery, and Hardener-plus-recharge against K/E/M |
| Layered defenses | 36 | PDS+ECM, PDS+EvM, PDS+Hardener, full five-TP packages, and two-flight saturation |

All asymmetric variants have reciprocal side swaps. Mirror and paired gates check side-order neutrality for outcomes, PDS interceptions, and Firm/denied turns. Direct/terminal attacks and PDS interception retain separate deterministic random streams.

## Required reporting

Each variant reports outcomes and duration plus direct hits, Missile Flights launched, terminal attacks, missile hits, PDS attempts/interceptions, finite ammunition use, Ready/reserve state, Firm and denied turns, system power commitments, tactical shield restoration, Shield Battery charges, remaining Hull, and unresolved combat.

The reporting separates five distinct causes of survival:

- no legal Firm solution;
- terminal interception;
- EvM or Shield Armor mitigation;
- shield restoration;
- offensive power starvation caused by defensive commitments.

## Test and validation totals

- 642 engine-independent tests.
- 7 accepted deterministic moving-missile scenarios.
- 12 Phase A documents / 54 cases.
- 7 Phase B documents / 36 cases.
- 29 kinetic calibration variants at 10,000 trials each.
- 31 energy calibration variants at 10,000 trials each.
- 48 no-counter weapon-matrix variants at 10,000 trials each.
- 59 corrected PDS/interception variants at 10,000 trials each.
- 171 layered defensive-system variants at 10,000 trials each.
- 46 ScenarioRunner self-tests.

## Deferred

Checkpoint 31 deliberately defers alternative reactor envelopes, Auxiliary Reactors, Combat Batteries, Capacitor Banks, overload and Strain, held main-weapon interception, multiple PDS installations, component damage, probabilistic sensor resolution, cooperative ECM screens, detailed seeker/datalink EW, multi-engagement logistics, and final balance rulings.

The next interpretation pass should use the complete defensive results to decide which rules are mechanically healthy and which values deserve further sensitivity studies. Reactor-envelope changes follow only after those opportunity costs are visible.
