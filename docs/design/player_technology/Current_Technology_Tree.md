# Star Cluster Current TL1-TL9 Technology Tree

**Status:** Current working design after native-validated CP164 isolated power closure; prepared for whole-system integration.

This is the single active human-readable TL tree. Detailed provenance lives in `current_working_technology_baseline.json`. Frozen production/PF4 files remain compatibility sources only.

## Core systems and power

| TL | Cruiser Space | Hull | Main Reactor S/TP | APU TP/S | STL Move/S | FTL Move/S | Computer S | Sensor S |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 35 | 24.0 | 6 / 5 | 1 / 2 | 1 / 5 | 1 / 5 | 3 | 3 |
| 2 | 35 | 24.0 | 6 / 6 | 1 / 2 | 2 / 5 | 2 / 5 | 3 | 3 |
| 3 | 36 | 26.0 | 6 / 7 | 1 / 2 | 3 / 5 | 3 / 5 | 3 | 3 |
| 4 | 36 | 26.0 | 6 / 8 | 1 / 2 | 4 / 5 | 4 / 5 | 3 | 3 |
| 5 | 37 | 28.0 | 6 / 9 | 2 / 2 | 5 / 5 | 4 / 5 | 3 | 3 |
| 6 | 37 | 28.0 | 6 / 10 | 2 / 2 | 6 / 5 | 6 / 5 | 2 | 3 |
| 7 | 38 | 30.0 | 6 / 11 | 2 / 2 | 7 / 5 | 7 / 5 | 2 | 2 |
| 8 | 38 | 30.0 | 6 / 12 | 2 / 2 | 8 / 5 | 9 / 5 | 2 | 2 |
| 9 | 39 | 32.0 | 6 / 13 | 2 / 2 | 9 / 5 | 12 / 5 | 2 | 2 |

**Power closure:** Main Reactor remains 6 Space and produces 5-13 Operational TP. APU remains 2 Space: +1 TP at TL1-4 and +2 TP at TL5-9. No arbitrary APU copy cap.

## Universal direct-fire modifiers

- Firm track: **0 pp**.
- Approximate track: **-25 pp** when permitted.
- Extended range (`Standard Range < range <= Maximum Range`): **-10 pp**.
- Approximate and Extended penalties **stack**.
- Beyond Maximum Range is illegal; Missiles do not use this direct-fire range penalty.

## Shield, Armor, DEF/RES, and recovery

| TL | Shield Cap | Shield S | Shield DEF % | Recharge/TP | Armor Cap | Armor S | Armor RES % | Armor Regen/TP | Regen Reserve |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 16.0 | 3 | 20 | 2 (cap 1 TP) | 12.0 | 0 | 20 | 0 (cap 0 TP) | 0 |
| 2 | 18.0 | 3 | 22 | 2 (cap 1 TP) | 14.0 | 0 | 22 | 0 (cap 0 TP) | 0 |
| 3 | 20.0 | 3 | 24 | 2 (cap 1 TP) | 16.0 | 0 | 24 | 0 (cap 0 TP) | 0 |
| 4 | 22.0 | 3 | 26 | 2 (cap 1 TP) | 18.0 | 0 | 26 | 0 (cap 0 TP) | 0 |
| 5 | 24.0 | 3 | 28 | 2 (cap 1 TP) | 20.0 | 0 | 28 | 0 (cap 0 TP) | 0 |
| 6 | 26.0 | 3 | 30 | 2 (cap 1 TP) | 18.0 | 0 | 30 | 2 (cap 1 TP) | 6 |
| 7 | 28.0 | 2 | 32 | 2 (cap 1 TP) | 20.0 | 0 | 32 | 2 (cap 1 TP) | 8 |
| 8 | 30.0 | 2 | 34 | 2 (cap 2 TP) | 22.0 | 0 | 34 | 2 (cap 2 TP) | 12 |
| 9 | 32.0 | 2 | 36 | 2 (cap 2 TP) | 24.0 | 0 | 36 | 2 (cap 2 TP) | 16 |

Shield DEF is whole-packet deflection after SPEN reduction (45 pp cap). Armor RES is fractional mitigation after APEN reduction (95 pp cap).

## Main weapons

### Kinetic

| TL | S | ACC | DAM | APEN | SPEN | TP | Std R | Max R | Ammo |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 6 | 20 | 9 | 8 | 0 | 2 | 2 | 4 | 100 |
| 2 | 6 | 20 | 10 | 9 | 0 | 2 | 2 | 4 | 100 |
| 3 | 6 | 20 | 12 | 10 | 0 | 2 | 2 | 4 | 100 |
| 4 | 6 | 30 | 13 | 10 | 0 | 2 | 2 | 4 | 100 |
| 5 | 6 | 30 | 14 | 11 | 0 | 3 | 2 | 4 | 100 |
| 6 | 6 | 30 | 15 | 12 | 0 | 3 | 2 | 6 | 100 |
| 7 | 6 | 32 | 15 | 13 | 0 | 3 | 3 | 6 | 100 |
| 8 | 6 | 35 | 19 | 14 | 0 | 4 | 3 | 6 | 100 |
| 9 | 6 | 35 | 20 | 14 | 0 | 4 | 3 | 7 | 100 |

### Energy

| TL | S | ACC | SPEN | Low TP/DAM | Standard TP/DAM | Overload TP/DAM | Std R | Max R |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 6 | 30 | 10 | 2/2 | 3/8 | 4/12 | 3 | 4 |
| 2 | 6 | 30 | 13 | 2/4 | 3/8 | 6/14 | 3 | 5 |
| 3 | 6 | 30 | 14 | 1/4 | 2/10 | 4/14 | 3 | 6 |
| 4 | 6 | 30 | 16 | 2/6 | 4/10 | 6/16 | 3 | 6 |
| 5 | 6 | 30 | 17 | 3/6 | 5/10 | 7/18 | 5 | 7 |
| 6 | 6 | 35 | 18 | 2/6 | 4/12 | 6/22 | 5 | 7 |
| 7 | 6 | 35 | 19 | 3/6 | 5/14 | 8/22 | 5 | 7 |
| 8 | 6 | 35 | 20 | 4/8 | 6/16 | 9/24 | 5 | 8 |
| 9 | 6 | 35 | 22 | 3/8 | 6/18 | 8/24 | 5 | 9 |

### Missile and Swarmer

| TL | S | Flights | Launch TP | Move | Range | Guidance % | GP DAM | SPEN | APEN | Swarmer |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 6 | 25 | 1 | 2 | 6 | 70 | 12 | 0 | 0 | - |
| 2 | 6 | 25 | 1 | 3 | 7 | 70 | 13 | 0 | 0 | 2 x 7 |
| 3 | 6 | 25 | 1 | 4 | 7 | 75 | 15 | 0 | 0 | 2 x 7 |
| 4 | 6 | 25 | 1 | 5 | 8 | 75 | 17 | 0 | 0 | 2 x 8 |
| 5 | 6 | 25 | 2 | 6 | 9 | 80 | 19 | 0 | 0 | 2 x 9 |
| 6 | 6 | 25 | 2 | 7 | 10 | 85 | 21 | 0 | 0 | 2 x 9 |
| 7 | 6 | 25 | 2 | 8 | 10 | 85 | 23 | 0 | 0 | 2 x 10 |
| 8 | 6 | 25 | 2 | 9 | 11 | 90 | 25 | 0 | 0 | 2 x 11 |
| 9 | 6 | 25 | 3 | 10 | 12 | 95 | 27 | 0 | 0 | 2 x 12 |

## Point Defense

### Kinetic PDS

| TL | S | Base % | Max RC | RC1 TP | RC2 TP | RC3 TP | Ammo | Range | Range-1 attempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 2 | 8 | 1 | 2 | - | - | 75 | 0 | False |
| 2 | 2 | 8 | 1 | 2 | - | - | 75 | 0 | False |
| 3 | 2 | 8 | 1 | 2 | - | - | 75 | 0 | False |
| 4 | 2 | 10 | 1 | 2 | - | - | 75 | 0 | False |
| 5 | 2 | 10 | 1 | 2 | - | - | 75 | 0 | False |
| 6 | 2 | 10 | 1 | 2 | - | - | 75 | 0 | False |
| 7 | 2 | 12 | 2 | 1 | 3 | - | 75 | 0 | False |
| 8 | 2 | 12 | 2 | 1 | 3 | - | 75 | 0 | False |
| 9 | 2 | 12 | 2 | 1 | 3 | - | 75 | 0 | False |
### Energy PDS

| TL | S | Base % | Max RC | RC1 TP | RC2 TP | RC3 TP | Ammo | Range | Range-1 attempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 2 | 10 | 1 | 2 | - | - | None | 0 | False |
| 2 | 2 | 10 | 1 | 2 | - | - | None | 0 | False |
| 3 | 2 | 10 | 1 | 2 | - | - | None | 0 | False |
| 4 | 2 | 10 | 2 | 2 | 3 | - | None | 0 | False |
| 5 | 2 | 10 | 2 | 2 | 3 | - | None | 0 | False |
| 6 | 2 | 10 | 2 | 2 | 3 | - | None | 0 | False |
| 7 | 2 | 10 | 2 | 2 | 4 | - | None | 0 | False |
| 8 | 2 | 10 | 2 | 2 | 4 | - | None | 0 | False |
| 9 | 2 | 10 | 2 | 2 | 3 | - | None | 0 | False |
### AMM PDS

| TL | S | Base % | Max RC | RC1 TP | RC2 TP | RC3 TP | Ammo | Range | Range-1 attempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 2 | 0 | 1 | 1 | - | - | 25 | 0 | False |
| 2 | 2 | 5 | 1 | 1 | - | - | 25 | 0 | False |
| 3 | 2 | 5 | 2 | 1 | 2 | - | 25 | 0 | False |
| 4 | 2 | 5 | 2 | 1 | 2 | - | 25 | 0 | False |
| 5 | 2 | 5 | 2 | 1 | 2 | - | 25 | 0 | False |
| 6 | 2 | 5 | 2 | 1 | 2 | - | 25 | 0 | False |
| 7 | 2 | 5 | 3 | 1 | 2 | 3 | 25 | 1 | True |
| 8 | 2 | 5 | 3 | 1 | 2 | 3 | 25 | 1 | True |
| 9 | 2 | 5 | 3 | 1 | 2 | 3 | 25 | 1 | True |

## Sensors, ECM, ECCM

| TL | Sensor S | Passive F/A | Active-low F/A @ TP | Active-high F/A @ TP | Sensor DR | ECM rating @ TP | ECCM rating @ TP |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 3 | 1/3 | 3/4 @ 1 | None/None @ None | 0 | 1 @ 1 | 1 @ 1 |
| 2 | 3 | 1/3 | 3/4 @ 1 | None/None @ None | 1 | 2 @ 2 | 2 @ 2 |
| 3 | 3 | 1/3 | 3/4 @ 1 | 4/5 @ 2 | 1 | 2 @ 1 | 2 @ 1 |
| 4 | 3 | 2/4 | 4/5 @ 1 | 5/6 @ 2 | 2 | 2 @ 1 | 2 @ 1 |
| 5 | 3 | 2/4 | 4/5 @ 1 | 5/6 @ 2 | 2 | 3 @ 2 | 3 @ 2 |
| 6 | 3 | 3/5 | 5/6 @ 1 | 6/7 @ 2 | 3 | 3 @ 2 | 3 @ 2 |
| 7 | 2 | 3/6 | 5/7 @ 1 | 7/8 @ 2 | 3 | 3 @ 1 | 3 @ 1 |
| 8 | 2 | 4/7 | 6/8 @ 1 | 8/9 @ 2 | 4 | 4 @ 2 | 4 @ 2 |
| 9 | 2 | 5/8 | 7/9 @ 1 | 9/10 @ 2 | 5 | 4 @ 1 | 4 @ 1 |

## Damage Control

| TL | Prepared Kits | TP/attempt | Degraded->Operational % | Disabled->Degraded % | Hull repair % | Hull restored |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 3 | 1 | 70 | 50 | 40 | 1 |
| 2 | 3 | 1 | 70 | 50 | 40 | 1 |
| 3 | 4 | 1 | 75 | 55 | 45 | 1 |
| 4 | 4 | 1 | 75 | 55 | 45 | 1 |
| 5 | 5 | 1 | 75 | 55 | 45 | 1 |
| 6 | 5 | 1 | 75 | 55 | 45 | 1 |
| 7 | 6 | 1 | 80 | 60 | 50 | 2 |
| 8 | 6 | 1 | 80 | 60 | 50 | 2 |
| 9 | 7 | 1 | 85 | 65 | 55 | 3 |

## Selected Auxiliary systems

| System | First TL | Space | Current effect | Identity |
| --- | --- | --- | --- | --- |
| APU | TL1 | 2 | +1 TP TL1-4; +2 TP TL5-9 | Modular auxiliary Tactical Power |
| Shield Battery | TL1 | 1 | TL1: restore=2, charges=1, tp=0; TL2: restore=2, charges=1, tp=0; TL3: restore=2, charges=1, tp=0; TL4: restore=4, charges=2, tp=0; TL5: restore=4, charges=2, tp=0; TL6: restore=6, charges=3, tp=0; TL7: restore=6, charges=3, tp=0; TL8: restore=8, charges=3, tp=0; TL9: restore=8, charges=3, tp=0 | finite emergency Shield restoration; automatic research-AI discharge below 50 percent Shield only; finite charges |
| Shield Booster | TL2 | 1 | TL2: capacityBonus=2, tp=0; TL3: capacityBonus=2, tp=0; TL4: capacityBonus=4, tp=0; TL5: capacityBonus=4, tp=0; TL6: capacityBonus=6, tp=0; TL7: capacityBonus=6, tp=0; TL8: capacityBonus=8, tp=0; TL9: capacityBonus=8, tp=0 | passive increase to maximum Shield Capacity |
| Shield Hardener | TL3 | 1 | TL3: defBonusPp=5, tp=1; TL4: defBonusPp=5, tp=1; TL5: defBonusPp=10, tp=1; TL6: defBonusPp=10, tp=1; TL7: defBonusPp=15, tp=1; TL8: defBonusPp=15, tp=1; TL9: defBonusPp=20, tp=1 | powered Shield DEF bonus; broad protection, strongest against Energy but not SPEN-specific |
| Ablative Armor | TL1 | 1 | TL1: ablativeIntegrity=2, tp=0; TL2: ablativeIntegrity=2, tp=0; TL3: ablativeIntegrity=2, tp=0; TL4: ablativeIntegrity=4, tp=0; TL5: ablativeIntegrity=4, tp=0; TL6: ablativeIntegrity=8, tp=0; TL7: ablativeIntegrity=8, tp=0; TL8: ablativeIntegrity=10, tp=0; TL9: ablativeIntegrity=10, tp=0 | one expendable outer layer that absorbs raw post-Shield damage before primary Armor; no tactical repair |
| Energized Armor | TL5 | 1 | TL5: resBonusPp=5, tp=1; TL6: resBonusPp=5, tp=1; TL7: resBonusPp=10, tp=1; TL8: resBonusPp=15, tp=1; TL9: resBonusPp=20, tp=1 | powered Armor RES bonus; passive Armor remains functional when unpowered |
| Crystalline Armor | TL6 | 0 | TL6: capacityBonus=2, resBonusPp=0, tp=0; TL7: capacityBonus=4, resBonusPp=5, tp=0; TL8: capacityBonus=8, resBonusPp=15, tp=0; TL9: capacityBonus=10, resBonusPp=20, tp=0 | non-regenerative Crystalline Armor branch: additional Armor capacity plus RES; sacrifices tactical Armor regeneration |
| Field Stabilizer | TL7 | 1 | TL7: spenReduction=16, tp=1; TL8: spenReduction=18, tp=1; TL9: spenReduction=20, tp=1 | anti-SPEN Shield tuner: while active, subtract its rating from incoming SPEN before effective Shield DEF is calculated; cannot reduce SPEN below zero |
| Repair Drone Bay | TL2 | 1 | TL2: additionalActionsPerPhase=1, additionalPreparedRepairKits=3, droneAttemptTp=1, differentTargetRequired=True, sameTargetRerollAllowed=False; TL3: additionalActionsPerPhase=1, additionalPreparedRepairKits=4, droneAttemptTp=1, differentTargetRequired=True, sameTargetRerollAllowed=False; TL4: additionalActionsPerPhase=1, additionalPreparedRepairKits=4, droneAttemptTp=1, differentTargetRequired=True, sameTargetRerollAllowed=False; TL5: additionalActionsPerPhase=1, additionalPreparedRepairKits=5, droneAttemptTp=1, differentTargetRequired=True, sameTargetRerollAllowed=False; TL6: additionalActionsPerPhase=1, additionalPreparedRepairKits=5, droneAttemptTp=1, differentTargetRequired=True, sameTargetRerollAllowed=False; TL7: additionalActionsPerPhase=1, additionalPreparedRepairKits=6, droneAttemptTp=1, differentTargetRequired=True, sameTargetRerollAllowed=False; TL8: additionalActionsPerPhase=1, additionalPreparedRepairKits=6, droneAttemptTp=1, differentTargetRequired=True, sameTargetRerollAllowed=False; TL9: additionalActionsPerPhase=1, additionalPreparedRepairKits=7, droneAttemptTp=1, differentTargetRequired=True, sameTargetRerollAllowed=False | adds one additional Damage Control action per Damage Control phase; crew and Drone actions must target different eligible repair targets in that phase; never a same-target reroll |
| Kinetic Magazine | TL1 | 1 | TL1: ammoBonus=25, tp=0; TL2: ammoBonus=25, tp=0; TL3: ammoBonus=25, tp=0; TL4: ammoBonus=25, tp=0; TL5: ammoBonus=25, tp=0; TL6: ammoBonus=25, tp=0; TL7: ammoBonus=25, tp=0; TL8: ammoBonus=25, tp=0; TL9: ammoBonus=25, tp=0 | +25 Kinetic ammunition; duel outcome effectively nonbinding in CP158; value is endurance/logistics |
| Missile Magazine | TL1 | 1 | TL1: ammoBonus=25, tp=0; TL2: ammoBonus=25, tp=0; TL3: ammoBonus=25, tp=0; TL4: ammoBonus=25, tp=0; TL5: ammoBonus=25, tp=0; TL6: ammoBonus=25, tp=0; TL7: ammoBonus=25, tp=0; TL8: ammoBonus=25, tp=0; TL9: ammoBonus=25, tp=0 | +25 Missile Flights; duel outcome effectively nonbinding in CP158; value is endurance/logistics |

## Whole-system integration still open

- Integrate Main Reactor Operational/Degraded/Emergency state transitions into whole-system combat.
- Define/integrate mature APU damaged behavior and distributed resilience.
- Integrate Repair Drone distinct-target component Damage Control in the full combat kernel.
- Investigate tactical allocator monotonicity (CP164 TL8 Energy/ECM regression).
- After whole-system validation, explicitly promote current working research values into production authority.

Closed isolated subsystem values should reopen only when whole-system evidence demonstrates a pathology.
