# Telemetry Instrumentation Contract v0.1

**Checkpoint:** 124  
**Purpose:** make instrumentation correctness a blocking acceptance gate before larger CP123-baseline studies.

## Core rule

Raw counters and raw quantities are the authority. Derived rates must be reconstructible from them. A summary column may be useful, but it must never be the only place where a causal quantity exists.

## Ownership rules

- **Attacker-owned:** attack eligibility, direct shots/hits, Missile launches, weapon/payload choice, weapon power, launch ammunition consumption.
- **Target/defender-owned:** Missile terminal arrivals, guidance attempts, Missile hits, PDS attempts/intercepts, and damage received by layer.
- **Observer/ship-owned:** track quality, ECM/ECCM effects, burn-through preservation, Sensor mode, movement/fuel, Tactical Power allocation and overload use.
- **Repairing-ship-owned:** Damage Control attempts, successes, and Hull restored.

The attacker/target split is deliberate. In particular, `missile_hit_per_launch` must combine **target-side missile hits** with **attacker-side launches**. CP120 demonstrated why this must be explicit.

## Required dimensions

The machine-readable authority `telemetry_instrumentation_contract_v0_1.json` defines 47 raw metrics covering movement/fuel, geometry, track quality, EW, Tactical Power, overload, attack eligibility, direct weapons, Missile terminal flow, PDS, penetration/layered damage, and Damage Control.

Build/variant outputs separately record TL, weapon family, Missile payload family, Main Weapon/Reactor multiplicity, Shield, ECM/ECCM multiplicity, PDS family, Shield Hardener, Installation Space, mission/AUX fill, Tactical Power supply/demand, movement order, and scenario group.

## Blocking deterministic probes

CP124 must prove, before any larger study:

1. layered-damage telemetry matches an independent deterministic oracle;
2. CP123 split Missile delivery/guidance/payload profiles compose correctly;
3. a Swarmer remains one Flight/terminal roll with two internal packets and bounded PDS penalty;
4. Damage Control yields 1 Hull at TL1, 2 at TL7, and 3 at TL9 on a successful reference attempt;
5. duplicate ECM/ECCM installations remain redundancy-only and non-additive;
6. Missile launches are attacker-side while terminal/guidance/hit telemetry is target-side;
7. every required raw metric exists in the research telemetry schema.

## Explicit consumer limits

This contract does **not** pretend the Python ecology consumer implements every production mechanic. Internal critical/subsystem damage remains outside it. The current ecology Missile travel model uses ETA-to-terminal travel and does not reproduce the full C# moving-target range-exhaustion behavior. Damage Control counters/profile resolution are validated but Damage Control is not scheduled into the CP124 combat smoke. These limitations must remain visible in future study definitions and analyses.
