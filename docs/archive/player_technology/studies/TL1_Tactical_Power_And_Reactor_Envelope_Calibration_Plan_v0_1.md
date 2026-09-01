# TL1 Tactical Power Completion and Reactor Envelope Calibration Plan v0.1

## Purpose

Checkpoint 32 completes the static TL1 Tactical Power economy before any reactor-output value is promoted from a provisional fixture to a balance recommendation. The study measures hard affordability thresholds, resource substitution, and component opportunity costs. It does not attempt optimal tactics, movement, target selection, or campaign logistics.

## Accepted scope decisions

- Sweep renewable reactor output at every integer from 0 through 8 Tactical Power.
- Retain 5 TP as the existing control, 3 TP as the current Degraded output, and 1 TP as Emergency Output.
- Treat an Auxiliary Reactor as a comparison overlay rather than normal TL1-hull equipment: +2 TP Operational, +1 TP Degraded, and 0 TP Disabled or Destroyed.
- A Combat Battery carries three charges, injects +2 Available TP per discharge, permits one discharge per turn, and cannot be recharged in combat.
- A Capacitor Bank has Capacity 3, Charge Rate 1, and Discharge Rate 2. An installed bank is full after FTL travel. Stored charge persists through Turn Refresh; combat charging or discharging permits one operation per turn.
- Implement Held Interception for Kinetic and Energy main weapons. Power is earmarked when required, becomes Spent only if the shot triggers, and is released unused when the interception window closes; the reserved offensive cycle is lost either way.
- Keep PDS Reaction Capacity at 1. Reaction Capacity remains a separate component statistic.
- One installed main Missile Launcher launches at most one Missile Flight per turn. Two-flight input is retained only as a multiple-launcher or coordinated-saturation boundary.
- Shield Batteries remain finite shipyard/drydock-restored emergency reserves and are excluded from ordinary reactor-package valuation.
- Exclude Tractor Beams, Tractor overload, STL Drive overload, and all movement-dependent valuation.

## Power ledger

Every requested package is resolved through one authoritative Tactical Power ledger:

1. renewable main-Reactor output;
2. Auxiliary Reactor contribution, when present;
3. safe Reactor overload, when scripted and below the Strain Limit;
4. threshold discharge from a full or partially charged Capacitor Bank;
5. threshold Combat Battery discharge;
6. Powered commitments;
7. Spent actions and Tactical Shield recharge;
8. Held Interception or main-weapon earmarks;
9. unused-power and unfunded-request accounting;
10. optional end-of-turn Capacitor charging when no Capacitor operation has occurred.

The study reports each source separately. Temporary or finite power is never folded into the named renewable reactor output.

## Fixed doctrines

The study uses fixed, nonadaptive allocation priorities:

- **Defense-first:** request PDS, ECM, ECCM, Active Sensors, Shield Hardener, EvM, Shield overload/recovery, and Tactical Shield recharge before reserving the main weapon.
- **Offense-first:** reserve the selected main-weapon cycle first, then request the same defensive package.
- **Threshold Combat Battery:** discharge only when one +2 TP injection can make the scripted package affordable.
- **Threshold-and-recharge Capacitor:** discharge only when the required shortfall is within the stored charge and Discharge Rate; otherwise charge one TP at the end of a turn when legal and useful.
- **Held Interception:** always reserve the selected eligible main weapon against the first incoming Missile Flight; do not fire offensively that turn.

These doctrines deliberately avoid opponent-aware optimization. They expose component edges and failure modes.

## Overload boundaries

Checkpoint 32 evaluates only overloads that have interpretable effects in static combat:

- Reactor safe overload: +1 TP and +1 Reactor Strain.
- Energy Cannon safe burst: 3 TP, DAM 4, SPEN 1, APEN 1, and +1 weapon Strain for the first two eligible turns.
- Active Sensor safe overload: +1 TP, +2 Firm range, and +1 Sensor Strain.
- ECM/ECCM safe overload: +1 TP, +1 rating, and +1 system Strain.
- Shield Hardener safe overload: +1 TP, +1 Shield Armor, and +1 Hardener Strain.
- Shield overcapacity: 1 TP for +2 temporary Shield while Shields are operating.
- Shield recovery overload: 1 TP to add +2 to the next legal recharge while Shields are collapsed.

Forced overload and failure consequences remain outside this first reactor-envelope sweep.

## Evaluation matrix

The executable study contains 504 variants at 10,000 trials each:

| Category | Variants | Purpose |
|---|---:|---|
| Accepted controls | 6 | Retain Kinetic, Energy, and Missile mirrors at ranges 0 and 2. |
| Reactor sweep | 90 | Five offense packages at renewable outputs 0-8 with reciprocal side swaps. |
| Single consumers | 144 | Eight individual power-demand packages at outputs 0-8. |
| Layered sweep | 144 | Eight multi-system packages at outputs 0-8, including defense-first and offense-first priorities. |
| Power-source overlays | 60 | Auxiliary Reactor, full/depleted Capacitor, Combat Battery, and Reactor-overload threshold comparisons. |
| Overload boundaries | 30 | Static Energy, Sensor, EW, Shield Hardener, overcapacity, and recovery edges. |
| Held Interception | 30 | Kinetic/Energy hold costs, triggered/unused holds, PDS ordering, and a two-flight saturation boundary. |

Every asymmetric variant has an exact reciprocal side swap. Common random streams remain separated for direct/terminal attacks, PDS, and Held Interception.

## Required outputs

For each side and variant, report:

- victory, mutual destruction, unresolved outcome, and mean turns;
- requested package full-funding and partial-funding rates;
- main-weapon shots, launches, hits, and ammunition remaining;
- PDS attempts and interceptions;
- Held declarations, attempts, interceptions, unused holds, and lost offensive cycles;
- renewable, Auxiliary, Reactor-overload, Combat Battery, and Capacitor power;
- Powered, Spent, unused, and total envelope power per turn;
- individual unfunded requests for PDS, Sensors, ECM, ECCM, Hardener, EvM, Shield overload, recharge, held fire, and main weapons;
- final Capacitor charge and Combat Battery charges consumed;
- Reactor, Energy, Sensor, ECM, ECCM, Hardener, and Shield Generator Strain.

## Interpretation guardrails

- A hard stall, mutual sensor denial, exhausted store, or unaffordable package is a valid boundary proof.
- A green gate proves determinism, reciprocal fairness, and contract fidelity; it does not prove final balance.
- Win rate is secondary to affordability thresholds in this pass.
- Reactor output should not be selected merely to fund every desirable system. The useful range is where basic operation is possible, low-output modes remain relevant, and additional defense requires visible tradeoffs.
- Auxiliary Reactors, Capacitors, Combat Batteries, and overload are alternatives or temporary bridges, not anonymous additions to base output.
