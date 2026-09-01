# TL1 Sensor/EW Foundation and Range Sweep v0.1

## Purpose

Checkpoint 68 separates three concepts that earlier integrated studies compressed into one effective Firm-range number:

1. **sensor reach** - whether the observer's passive/active hardware can detect and discriminate the target at the current range;
2. **emission-assisted detection** - whether the target reveals itself by operating Active Sensors or ECM; and
3. **EW discrimination** - whether hostile ECM spoils a Firm-quality observation and whether ECCM preserves it.

This is a deterministic foundation study. It does **not** promote a new TL1 sensor range table into production combat and it does not rebalance weapons. The accepted Checkpoint 67a integrated-combat inputs remain frozen historical evidence until a later checkpoint deliberately adopts one new envelope.

## Rules under test

- TL1 forward candidates have **one rated normal Active Sensor mode** before overload. Multiple normal low/high settings are reserved as a possible higher-TL capability.
- Forward candidates use **1 TP** for that one normal Active mode and **+1 additional TP** for the listed overload mode.
- Active Sensor overload extends reach only. It does not provide ECCM and does not directly improve attack accuracy.
- An enemy operating Active Sensors may be passively detected as an emission source within that emitting sensor's current detection envelope. Emission-only information is capped at **Approximate**.
- An enemy operating ECM is deliberately conspicuous. With unobstructed tactical LOS, ECM establishes at least an emission-sourced **Approximate** contact across the radius-5 tactical map. Exact ECM strength remains hidden.
- Sensor reach determines the baseline track state first. Net ECM is then `max(0, target ECM - observer ECCM)`. Positive net ECM degrades an otherwise Firm observation to Approximate; it does not reduce the physical sensor envelope or erase an already detected target.
- ECCM counters ECM discrimination only. ECCM cannot extend physical detection range or promote a baseline Approximate observation to Firm.
- Occlusion blocks both ordinary sensing and emission-assisted contact outside the same hex.
- Physical weapon range remains separate from attack eligibility. A weapon can physically reach farther than current sensors can establish a legal target solution.

## TL1 candidate sweep

The radius-5 tactical map has a maximum separation of 10 hexes. The sweep evaluates every range 0-10 across twelve deterministic sensor/emission/EW contexts.

| Candidate | Passive Firm/Approx | Normal Active Firm/Approx | Normal Active TP | Overload Firm/Approx | Intent |
|---|---:|---:|---:|---:|---|
| legacy-cp67-control | 3 / 5 | 6 / 9 | 2 | 8 / 11 | Historical scale control only |
| intimate-1 | 1 / 2 | 2 / 3 | 1 | 3 / 4 | Very close TL1 sensing; modest overload |
| intimate-2 | 1 / 2 | 2 / 3 | 1 | 4 / 5 | Same normal reach; stronger overload decision |
| balanced-1 | 1 / 2 | 3 / 4 | 1 | 4 / 5 | Moderate normal reach; modest overload |
| balanced-2 | 1 / 2 | 3 / 4 | 1 | 5 / 6 | Moderate normal reach; stronger overload |
| passive-plus | 2 / 3 | 3 / 4 | 1 | 4 / 5 | Tests whether stronger passive sensing crowds out the optional Active suite |

The historical control represents the old maximum CP67 active envelope as one comparison point; it is not a forward single-mode candidate.

## Physical weapon reach reference

The accepted TL1 physical weapon ranges remain unchanged during this checkpoint:

- Kinetic Cannon maximum range: **4**;
- Energy Cannon maximum range: **5**;
- Missile Flight physical travel range: **6**.

A candidate sensor envelope is therefore allowed to leave part of a weapon's physical range unusable without another legitimate source of targeting information. This is intentional and supports independent/tall-vs-wide technology progression. Missile launch/terminal eligibility remains guidance-architecture-specific; this deterministic sensor sweep does not collapse every missile architecture into the direct-fire Firm-track rule.

## Prepared STL overload clarification

Checkpoint 68 also formalizes the already-discussed commitment/execution distinction:

- STL-overload Tactical Power is committed before Movement and before movement order is known.
- When that ship moves, the player may **execute** or **stand down** the prepared overload.
- Standing down gives no movement bonus, spends no overload-specific fuel, adds no Strain, removes no existing Strain, and does not refund/release the committed Tactical Power.
- Standing down is therefore optionality under initiative uncertainty, not a repair mechanism.
- Out-of-combat Strain recovery is expected to be a lower-pressure rest/stabilization Damage Control activity, probably without Repair Kit consumption; exact recovery timing/capacity remains deferred.

## Release interpretation

Checkpoint 68 release gates are structural/causal rather than balance targets. They verify the new separation of reach, emission-assisted detection, ECM discrimination, ECCM mitigation, occlusion, the single-mode TL1 candidate architecture, and the existence of weapon ranges beyond some candidate Firm envelopes. No candidate wins merely because it maximizes Firm coverage.
