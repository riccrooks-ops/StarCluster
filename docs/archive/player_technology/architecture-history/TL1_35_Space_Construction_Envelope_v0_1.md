# TL1 35-Space Construction Envelope v0.1

## Purpose

Checkpoint 60 turns the Checkpoint 59 35-Installation-Space concept into a deterministic construction envelope before any new Monte Carlo combat balancing is added. The goal is to expose the arithmetic of normal and deliberately odd legal TL1 designs while preserving the previously validated TL1 combat, power, damage, PDS, sensor, propulsion, and Damage Control mechanics as the numerical seed.

This is not a ship-class slot table and it is not a promotion screen. It is a construction sanity check.

## Working TL1 architecture

The player cruiser has **35 Installation Spaces**.

The mandatory player core is **25 Space**:

| Primary system | Space | Rule |
|---|---:|---|
| Main weapon | 6 | At least one; additional main weapons are allowed when Space permits. |
| Main reactor | 6 | At least one; additional main reactors are allowed when Space permits. |
| STL drive | 5 | Exactly one primary architecture. |
| FTL drive | 5 | Exactly one primary architecture for the player cruiser. |
| Tactical computer / fire control | 3 | Exactly one primary architecture. |

The current optional major-system test footprints are Active Sensor 3, Shield Generator 3, and Kinetic PDS 2. Residual Space is intentionally left **untyped support Space** in the deterministic enumerator. That avoids prematurely locking the exact TL1 AUX/ammunition catalogue while still preserving the Checkpoint 59 balanced reference, which uses its two residual Space for provisional PDS ammunition support plus one small AUX.

Base primary armor remains hull-integrated/external and consumes no Installation Space.

## Deterministic envelope

With the current footprints, exhaustive enumeration produces:

- **27 legal macro loadouts** before choosing main-weapon family;
- **96 weapon/power variants** after applying the retained TL1 Kinetic, Energy, and Missile standard power demands;
- **4 exact-fill macro loadouts**;
- at most **2 main weapons** in a legal TL1 player build;
- at most **2 main reactors** in a legal TL1 player build;
- at most **5 current-footprint Kinetic PDS installations** when every other optional major system is omitted;
- no legal build containing both 2 main weapons and 2 main reactors, because the fixed primary architectures plus those four large systems consume **37 Space** before any optional equipment.

These are consequences of the working arithmetic, not hard-coded class limits. If later technology changes Space costs or Hull TL changes the cruiser budget, the envelope must be recomputed.

## Nominal Tactical Power diagnostic

The deterministic power diagnostic deliberately asks a narrow question: if the ship tries to fire every installed main weapon once at the retained TL1 standard setting, ready every installed Kinetic PDS, and run an installed Active Sensor at its 1-TP setting in the same turn, can the installed Operational main reactors supply that demand?

It uses the accepted TL1 seed:

- Operational Fission Reactor: **5 TP**;
- Kinetic main weapon standard fire: **1 TP**;
- Energy main weapon standard fire: **2 TP**;
- Missile launch: **0 TP**;
- Kinetic PDS readiness: **1 TP** per installation;
- Active Sensor setting 1: **1 TP**.

Shield-field maintenance remains core-powered. Tactical shield recharge, Evasive Maneuvering, overload, and AUX effects are excluded from this diagnostic so the result remains interpretable.

Across the 96 variants:

- **5** have negative nominal power margin;
- **10** exactly consume available reactor output;
- nominal power margin ranges from **-2 to +10 TP**.

A negative margin does **not** make a ship construction-illegal. It means the player cannot operate every nominally counted system simultaneously and must make a tactical power choice. This separation is intentional.

## Reference and odd-build candidates

The deterministic study preserves the following candidates for the next combat-simulation pass:

| Candidate | Major-system footprint | Used | Free | Why keep it |
|---|---|---:|---:|---|
| Balanced generalist | 1 weapon, 1 reactor, Active Sensor, Shield, 1 PDS | 33 | 2 | Current reference ship; residual Space supports the provisional ammo/AUX concept. |
| Dual-main striker | 2 weapons, 1 reactor, Active Sensor | 34 | 1 | Tests whether a second attack package creates a healthy glass-cannon tradeoff. |
| Dual-reactor power core | 1 weapon, 2 reactors, Active Sensor | 34 | 1 | Tests whether large TL1 power surplus has useful opportunity cost or becomes dead Space. |
| PDS saturator | 1 weapon, 1 reactor, 5 PDS | 35 | 0 | Deliberately extreme terminal-defense build; also stresses Tactical Power. |
| Dual-main / dual-PDS | 2 weapons, 1 reactor, 2 PDS | 35 | 0 | Exact-fill offense/terminal-defense stress build with no Shield or Active Sensor. |
| Shielded PDS fortress | 1 weapon, 1 reactor, Shield, 3 PDS | 34 | 1 | Tests concentrated terminal defense plus renewable defense without active sensing. |
| Dual-main / dual-reactor core | 2 weapons, 2 reactors | 37 | -2 | Intentional illegal control proving the current TL1 budget excludes this configuration naturally. |

None of the legal odd builds should be prohibited merely because it looks unusual. The next combat pass should discover whether its strengths and weaknesses are healthy under the accepted mechanics. If a legal design is pathological, prefer correcting component Space/performance/resource relationships over inventing a special anti-stacking rule unless the fiction independently requires one.

## Next validation step

After native Checkpoint 60 validation, use the deterministic envelope to define a small composed-ship Monte Carlo matrix. That matrix should compare normal reference ships and the odd candidates above across the three TL1 main-weapon families. It should report consequences such as power starvation/surplus, attack-package density, PDS coverage, defense loss, pacing, and matchup sensitivity. It must not impose a predetermined win percentage.
