# Checkpoint 36b - Protected Compartmentation Closure and Immobile Target Accuracy

## Purpose

Checkpoint 36 established deterministic H/X internal damage, weighted Critical Exposure, component conditions, combat Damage Control, ship-state closure, and FTL/missile exit safeguards. Checkpoint 36a corrected one precision-critical test expectation. Checkpoint 36b closes the remaining calibration boundary and adds a tactical consequence for complete STL failure.

## Protected Compartmentation closure

Ordinary ships place one seeded X inside each stratum. Protected Compartmentation preserves the exact number of ordinary seeded X markers reachable across the original finite Max Hull span, including partial final strata, and relocates each retained marker as late as possible.

When a retained protected X would occupy the final Max Hull position and the preceding position is H, the two swap:

```text
HHHX -> HHXH
```

This keeps the final point structural, preserves the paired ordinary X count, and prevents the Characteristic from silently lowering effective critical density. The deterministic stream continues after original Max Hull for any later Hull repair without replaying crossed positions.

Executable proof includes:

- unit tests over all five densities and 512 seeds;
- typed preflight over all five densities and 1,024 seeds;
- a calibration gate requiring exact ordinary/protected mean X-count parity in every no-Damage-Control pair;
- a terminal-H preflight requirement for the 12-Hull study tracks.

## Immobile Target

A target whose STL Drive is Disabled or Destroyed gains the initial tunable **Immobile Target** modifier:

- +10 percentage points to incoming ship-target attack accuracy;
- begins on the following turn, consistent with propulsion damage timing;
- applies to direct fire, Held Main, terminal missile attacks, and future attacks using the standard ship-target accuracy system;
- stacks normally with operational or Degraded EvM;
- does not reveal the ship, establish or improve a track, identify a contact, or affect PDS interception;
- is removed when Damage Control restores STL to Degraded at Turn Refresh.

The +10 value is the initial counterweight to the current EvM scale and remains tunable.

## Retained Checkpoint 36 contract

- Each Hull-reaching point removes one Hull and crosses one persistent hidden position.
- H has no additional effect; X selects one component by Critical Exposure and applies one condition step.
- Destroyed components remain selectable and do not reroll.
- Natural-100 precision criticals add one separate seeded component step after normal H/X processing.
- Hull zero becomes Pending Destruction until all committed Damage-phase packets and critical effects finish.
- Final destruction causes no generic external-damage explosion.
- TL1 Damage Control uses Capacity 1, three Repair Kits, one attempt per turn, and 1 TP plus one kit per attempt.
- Regular arrival/departure uses legal outer-ring Jump Perimeter hexes; Emergency FTL may begin anywhere.
- Every FTL power-up is public but non-positional and uses the entire Turn Power Envelope for one vulnerable turn.
- FTL declaration immediately self-destructs all outbound Missile Flights; successful player departure removes unresolved inbound Flights and closes the encounter.

## Initial Critical Exposure

- Main Reactor 2;
- STL Drive 2;
- FTL Drive, Shield Generator, Shield Hardener, each weapon/launcher, PDS, each damageable magazine, and each explicitly damageable Auxiliary 1;
- Electronics group 1 with secondary selection among Active Sensors, Targeting Computer, Communications, ECM, and ECCM.

Passive Sensors, Damage Control, and undefined auxiliaries without a damage profile remain excluded.

## Focused executable study

The 80-variant matrix remains:

| Factor | Values |
|---|---|
| Density | 15, 20, 25, 33 1/3, 50 percent |
| Placement | seeded, Protected |
| Damage Control | off, on |
| Loadout | kinetic, missile |
| Damage tempo | steady, burst |

The study reports first-critical position, X count, repeated selections, component conditions, Disabled-before-destruction frequency, Hull-band state, repair use/success, and Repair Kit consumption.

## Explicit deferrals

- final ordinary H/X density selection;
- Oversized Engines and Distributed Shield Grid Characteristics;
- exact Emergency-jump scatter;
- crew effects on Damage Control;
- out-of-combat Ship Repair;
- multiple mounts and full legal ship construction.
