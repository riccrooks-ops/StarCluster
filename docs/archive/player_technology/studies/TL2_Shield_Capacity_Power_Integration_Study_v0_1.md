# TL2 Shield Capacity and Power Integration Study v0.1

## Decision question

Checkpoint 84 asks whether the first TL2 Shield improvement should be a modest increase in **Shield Capacity** and how that defensive progression interacts with the newly validated TL2 reactor working candidate. It does not design a complete TL2 shield generator.

## Accepted inputs

- TL1 shield reference: Capacity 2, 3 Installation Space, Base Recharge 1, tactical recharge 1 Shield per Tactical Power, tactical recharge cap 2 TP/turn, Shield Armor 0.
- TL1 reactor reference: Peak Fission, 5 Operational TP at 6 Space.
- CP83 TL2 Power/Reactor working candidate: Early Practical Fusion, 6 Operational TP at the same 6 Space. Only normal Operational output is promoted to working-candidate status.
- TL2 information-control working package: Tactical Computer +12 pp; Sensor DR1; ECM/ECCM ceilings 2 at 1 TP/rating; degraded-fire penalty remains -25 pp; Evasive Compensation remains 0.

## Isolated Shield axis

The Shield Capacity candidates are:

| Capacity | Role | Interpretation |
|---:|---|---|
| 2 | TL1 control | Accepted current working reference. |
| 3 | Primary TL2 candidate | Modest +1 capacity step. |
| 4 | Upper sensitivity | Deliberate integer-breakpoint probe, not the default promotion target. |

Held constant: shield-generator Space 3, Base Recharge 1, tactical recharge rate 1/TP, tactical recharge cap 2, Shield Armor 0, damage-condition behavior, no shield hardener, no shield overload, no sustained maintenance cost, and no new shield prerequisite.

## Factorial slice

The study activates only a dependency-relevant slice of the standing suite:

- Side A: Kinetic or Energy.
- Side B: Kinetic, Energy, or Missile.
- Geometry: fixed range 3, dynamic Side A first, dynamic Side B first.
- Information control: clean Firm reference or contemporary DR1 + reactive ECCM1 against ECM2.
- Side-A Shield Capacity: 2, 3, or 4.
- Side-A reactor: 5 or 6 Operational TP.
- Side B remains Shield 2 / Reactor 5.

This is **216 variants** at 10,000 substantive trials each by default, plus a 216-trial one-trial-per-variant smoke pass.

## Recharge and Tactical Power

CP84 deliberately uses the existing stateful turn-power planner. At turn refresh, Base Recharge occurs according to the existing rules; when the shield would still be below its effective maximum, the planner may request one Tactical Power for ordinary tactical recharge only if the remaining pool exceeds the prospective reservation for offense, PDS, and other currently planned combat uses. Reactive ECCM then competes in the normal pre-combat EW response window.

The runner now reports Side-A tactical-shield-recharge opportunities, Tactical Power actually spent on recharge, and opportunities denied by the prospective reserve. These are diagnostics, not a new player rule and not a new shield-recharge doctrine.

## Interpretation priorities

Review capacity deltas separately at Reactor 5 and Reactor 6, then review the Reactor 6-minus-5 delta at each capacity. Pay special attention to discrete weapon-damage breakpoints, time to armor/hull exposure, PDS availability against Missile opponents, ECCM power in contested lanes, offense prevented by insufficient power, and whether Shield 3 plus Reactor 6 creates a useful package without making Shield 2 or reactor choices irrelevant.

No win-rate target is a release gate. Shield 3 may be promoted to a validated TL2 working candidate only after human review. Shield 4 is an upper sensitivity unless its evidence warrants a later explicit decision.
