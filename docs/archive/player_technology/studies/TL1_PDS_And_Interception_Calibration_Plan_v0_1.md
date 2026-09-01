# TL1 PDS and Interception Calibration Plan v0.1

> **Checkpoint 31 supersession note:** This file records the original Checkpoint 30 isolation plan. Checkpoint 31 retains it for history but supersedes its ammunition, Targeting Computer, and EvM assumptions: Kinetic PDS now carries 50 total packages, AMM PDS carries 25 total interceptors, both begin with one Ready Package included in total capacity, the main Targeting Computer may assist PDS, and AMM interception is exempt from the launching ship's EvM firing penalty. See `TL1_Layered_Defensive_Systems_Calibration_Plan_v0_1.md`.

## Purpose

Checkpoint 30 adds the first defensive subsystem to the accepted Checkpoint 29e stripped-down weapon foundation. The complete no-counter kinetic/energy/missile matrix remains unchanged and continues to serve as the control.

This pass asks whether TL1 point defense functions coherently before ECM, ECCM, richer sensor effects, held main-weapon interception, damage control, component damage, or broad Tactical Power doctrine is added. The purpose is to expose mechanical breakage and threshold behavior, not to force final weapon parity.

## Accepted TL1 PDS inputs

| PDS family | Powered readiness | Reaction Capacity | Equal-TL chance | Ammunition |
|---|---:|---:|---:|---:|
| Kinetic PDS | 1 TP | 1 attempt/turn | 35% | 12 packages |
| AMM PDS | 1 TP | 1 attempt/turn | 50% | 6 interceptors |
| Energy PDS | 2 TP | 1 attempt/turn | 40% | Unlimited conventional shots |

These values already exist in the authoritative TL1 numerical baseline. Checkpoint 30 makes them executable without promoting them to final balance values.

## Resolution contract

1. PDS readiness is a Powered commitment established at Turn Refresh. It is paid before EvM and main-weapon fire in the fixed calibration doctrine.
2. A PDS attack normally spends no additional Tactical Power.
3. Kinetic PDS and AMM consume one package per attempted interception, whether the attempt succeeds or fails. Energy PDS consumes no conventional ammunition.
4. PDS is self-contained and does not use the main Targeting Computer bonus.
5. EvM's -5 percentage-point own-fire penalty applies to the ship-mounted PDS interception chance. Target EvM does not separately penalize PDS because the PDS attacks the Missile Flight rather than the ship.
6. Standard PDS may act at terminal entry and, if a legal Firm terminal solution remains, immediately before the missile attack. Reaction Capacity is shared across all Missile Flights and both windows in the turn.
7. The TL1 baseline Reaction Capacity of 1 therefore permits only one total PDS attempt per turn. A Reaction Capacity 2 sensitivity control exposes both windows or permits a second incoming Flight to be engaged when capacity remains.
8. An intercepted Missile Flight is removed before terminal Guidance and cannot deal damage.
9. The stripped calibration assumes every surviving arriving Missile Flight has a legal terminal solution. ECM, seeker acquisition, datalink failure, and track uncertainty remain outside this pass.

## Saturation control

The ordinary missile doctrine launches one Missile Flight per turn. The saturation fixture launches two Flights per turn from the same 24-flight magazine. It is not a new permanent launcher rule; it is a diagnostic control that tests whether a one-reaction defense leaks threats rather than becoming missile immunity.

## Executable matrix

The study contains 59 variants at 10,000 trials each:

- no-missile-threat readiness controls;
- kinetic, AMM, and energy PDS versus ordinary missiles at ranges 0, 2, and 4;
- all three PDS families mounted on kinetic and energy direct-fire ships;
- no-PDS and PDS-equipped saturation comparisons;
- kinetic-PDS chance, Reaction Capacity, ammunition, and power-availability sensitivity controls;
- EvM plus PDS;
- missile mirrors with PDS on both ships;
- missile mirrors with PDS on only one ship;
- side-swapped partners for every asymmetric matchup.

The runner reports:

- terminal outcomes and duel duration;
- Missile Flights launched and reaching terminal Guidance;
- successful missile hits;
- PDS attempts and interceptions;
- terminal-entry and pre-attack attempts separately;
- finite PDS ammunition use;
- total Powered TP committed to PDS readiness;
- remaining Hull;
- mirror-side-bias and side-swap gates.

Direct/terminal attack randomness and PDS interception randomness use separate deterministic streams. This preserves reproducibility and prevents adding PDS from shifting unrelated attack rolls merely by consuming a different number of random values.

## Mechanical-breakage questions

Checkpoint 30 should identify, without immediately inventing counter-rules:

- whether baseline PDS ever fires when powered and supplied;
- whether interception actually prevents Guidance and damage;
- whether finite PDS ammunition depletes correctly;
- whether Reaction Capacity is shared across Flights and windows;
- whether saturation can leak through one-reaction defense;
- whether PDS makes ordinary missiles completely nonviable;
- whether unpowered or empty PDS is correctly inactive;
- whether side assignment changes aggregate results;
- whether any PDS family creates a new hard stall or immunity state.

## Explicitly deferred

Checkpoint 30 does not add:

- ECM or ECCM;
- seeker or datalink modifications;
- PDS technology-level deltas beyond the listed sensitivity controls;
- held direct-fire interception;
- multiple installed PDS components;
- target-priority UI or player-selectable defensive allocation;
- component damage, degradation, or repair;
- richer Tactical Power doctrine, batteries, capacitors, or auxiliary reactors;
- final balance rulings.
