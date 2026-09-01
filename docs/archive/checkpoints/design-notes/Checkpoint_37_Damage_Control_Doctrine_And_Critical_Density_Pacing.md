# Checkpoint 37 - Damage Control Doctrine and Critical-Density Pacing

## Purpose

Checkpoint 36b closed Protected Compartmentation finite-track parity and introduced the +10 Immobile Target accuracy modifier. Checkpoint 37 makes Damage Control eligibility explicit, replaces the eager calibration repair policy with controlled doctrines, records repair results at the correct level of detail, adopts 33 1/3 percent as the provisional ordinary TL1 internal critical density, and begins integrated combat-pacing measurement.

## Provisional ordinary TL1 internal critical density

Ordinary TL1 ships now use one X per three-position stratum as the provisional baseline:

- ordinary placement selects one deterministic seeded position within each stratum;
- Protected Compartmentation retains the same finite X count and places each retained X as late as possible;
- the final original-Hull position remains H through the accepted terminal swap safeguard;
- 25 percent remains in the pacing study as the principal lower-density control;
- the density is provisional until broader weapon, defense, movement, withdrawal, and mixed-TL scenarios establish whether it produces the desired tempo.

The density does not directly change Hull loss. Its pacing effect is indirect through subsystem degradation, mission kills, loss of movement or defense, and Damage Control decisions.

## Damage Control eligibility

Damage Control can be attempted only when all of the following are true:

1. the ship is surviving and is neither Pending Destruction nor Destroyed;
2. at least one legal repair target exists: missing Hull, or a Degraded/Disabled component;
3. Damage Control Capacity remains this turn;
4. at least one Repair Kit remains;
5. sufficient spendable Tactical Power remains.

Operational components do not require repair. Destroyed components cannot be repaired in combat. A failed precondition causes no attempt, no repair roll, no Tactical Power expenditure, no Repair Kit expenditure, and no queued effect.

The ship capability snapshot advertises `CanAttemptDamageControl` only when repairable damage and usable power are actually present.

## Player profile versus calibration profile

The player-facing TL1 profile remains:

- Damage Control Capacity 1;
- three Repair Kits;
- 1 Tactical Power and one Repair Kit per attempt;
- Degraded to Operational 70 percent;
- Disabled to Degraded 50 percent;
- restore 1 Hull 40 percent;
- successful repairs activate at the following Turn Refresh.

Checkpoint 37 adds a separate five-kit calibration profile. The extra two kits are a study allowance only. They ensure that steady early Hull damage cannot exhaust the entire sample before subsystem repair choices occur.

## Damage Control doctrines under test

The 64-variant doctrine study crosses 25 and 33 1/3 percent density, ordinary and Protected placement, kinetic and missile component tables, steady and burst Hull packets, and four doctrines:

| Doctrine | Component behavior | Hull behavior |
|---|---|---|
| None | no attempt | no attempt |
| ComponentOnly | Disabled first, then Degraded | never |
| HullHalf | Disabled first, then Degraded | only at 6 Hull or fewer |
| HullHalfReserveOne | Disabled first, then Degraded | only at 6 Hull or fewer and never spends the final kit on Hull |

Component priority is deterministic for calibration: Main Reactor, STL, primary weapon/launcher, Shield Generator, FTL, then other eligible components. This is a test doctrine, not yet the final player or AI doctrine.

## Repair accounting

The study separately records:

- total, component, and Hull attempts;
- Degraded-target and Disabled-target attempts;
- roll success rates for each target type;
- next-turn component and Hull activations;
- next-turn Hull repair activations (each restores one Hull point);
- component selected and component targeted frequency;
- Repair Kits and Tactical Power consumed;
- Repair Kits remaining and kits available when the first X is crossed;
- no-target, no-power, and no-kit skips;
- doctrine deferrals;
- threshold, reserve, and invalid-target violations;
- final component-condition distribution and Disabled-before-destruction frequency.

A successful roll and an activated repair are intentionally separate measurements because the effect is delayed until Turn Refresh.

## Combat-pacing probe

The 8-variant mirror-duel probe compares:

- 25 versus 33 1/3 percent density;
- ordinary versus Protected placement;
- Damage Control off versus component-first/reserve-one Damage Control.

The fixture uses the accepted TL1 Kinetic Cannon, SI 2, AP 1 / AI 4 armor, 12 Hull, two-hex range, ordinary Targeting Computer and EvM modifiers, component-conditioned weapon, reactor, Targeting Computer, and Evasive Maneuvers behavior, simultaneous committed return fire, and a 40-turn safety bound.

It reports:

- mean, median, P75, and P90 combat turns;
- percentage of combats lasting more than 18 turns;
- destruction, mission-kill, and unresolved rates;
- first X, first consequential subsystem impairment, and first Immobile snapshot turn;
- critical selections and following-turn Immobile bonus attacks;
- Damage Control attempts, successes, activations, and resources remaining.

No gate assumes that 33 1/3 percent must shorten combat. The study measures whether greater subsystem variation accelerates mission kills, reduces offense and lengthens combat, or produces a mixed effect.

## Immobile Target timing closure

At the start of each combat turn, the target STL condition is captured in an immutable combat snapshot. Every direct-fire or terminal-missile attack committed in that simultaneous window uses the captured condition.

Therefore:

- Operational or Degraded STL at the snapshot gives no Immobile Target bonus that turn;
- Disabled or Destroyed STL at the snapshot gives +10 percentage points;
- STL damage suffered later in that turn cannot retroactively change committed accuracy;
- successful Damage Control that restores STL at Turn Refresh removes the bonus before the new turn snapshot;
- PDS interception does not read target STL condition and remains unchanged.

## Explicit deferrals

- final density lock after broader Phase G and mixed-TL pacing;
- final player/AI Damage Control doctrine and Hull threshold;
- whether player-facing Repair Kit quantities rise above three;
- surrender, retreat, morale, and objective-specific mission-kill behavior;
- exact crew effects, boarding, and out-of-combat Ship Repair;
- multiple weapon mounts and full legal ship construction.
