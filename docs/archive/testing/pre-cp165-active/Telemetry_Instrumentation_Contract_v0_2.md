# Telemetry Instrumentation Contract v0.2

**Checkpoint:** 126  
**Parent authority:** Telemetry Instrumentation Contract v0.1 / CP124

## Purpose

CP126 preserves all 47 CP124 raw metrics and adds 14 full-System-Map/Adaptive-Engage/Missile-geometry metrics. The resulting **61 raw metrics** are the reconstructible evidence authority for the fidelity and attribution study.

Derived rates remain secondary. If a causal claim cannot be reconstructed from raw counters/quantities and variant/build metadata, the analysis is incomplete.

## Preserved ownership rules

- **Attacker-owned:** direct attack eligibility/shots/hits, Missile launches, weapon/payload choice and attack-side expenditure.
- **Target/defender-owned:** Missile terminal arrival/guidance/hit flow, PDS attempts/intercepts, and damage received by layer.
- **Observer/ship-owned:** track state, Sensor/EW state, movement/fuel, Tactical Power and overload behavior.
- **Repairing-ship-owned:** Damage Control attempts, successes and Hull restored.

The CP120 lesson remains binding: a Missile hit-per-launch rate combines **target-side terminal hits** with **attacker-side launches**.

## New CP126 raw metrics

| Metric | Dimension | Owner | Meaning |
|---|---|---|---|
| `search_moves` | movement | actor | one-hex pre-contact search moves actually performed |
| `adaptive_close_orders` | tactics | actor | post-contact Close orders |
| `adaptive_open_orders` | tactics | actor | post-contact Open orders |
| `adaptive_maintain_orders` | tactics | actor | post-contact preferred-range maintenance orders |
| `adaptive_standoff_orders` | tactics | actor | orders preserving/recovering a legitimately demonstrated one-sided standoff |
| `boundary_end_moves` | movement | actor | moves that end on the finite System Map boundary |
| `contact_established_turn` | information | observer | first turn on which contact is established; zero/unset according to consumer convention when not established |
| `missile_movement_hexes` | missile geometry | attacker | actual System Map hexes traversed by active Missiles |
| `missile_reroutes` | missile geometry | attacker | Missile movement phases whose chosen path differs because target geometry changed |
| `missile_target_movement_reroutes` | missile geometry | attacker | reroutes attributable to target movement since prior Missile movement |
| `missile_range_exhausted` | missile geometry | attacker | Missiles expended/terminated by reaching maximum travel without terminal arrival |
| `maximum_missile_distance_traveled` | missile geometry | attacker | greatest total traveled distance observed for an owned Missile |
| `maximum_own_attack_range` | tactics | actor | greatest range at which the actor has actually demonstrated a legal attack |
| `maximum_observed_opponent_attack_range` | tactics | observer | greatest range at which the opponent has been observed to demonstrate a legal attack |

The machine-readable authority is `telemetry_instrumentation_contract_v0_2.json`.

## Physical identity and mirror studies

For CP126 full-map studies, stochastic streams belong to **physical ship identity and event type**, not Side A/Side B processing order. Side-swapped/mover-swapped variants therefore preserve the same physical random streams after perspective normalization.

This is required for the blocking CP126 symmetry gate and is also the preferred basis for paired sensitivity conditions using common random numbers.

## Geometry requirements

Movement telemetry must distinguish:

- search movement before contact;
- post-contact tactical order;
- full 2D finite-map destination/path;
- map-boundary interaction;
- actual Missile path/travel/rerouting;
- post-Movement combat geometry.

A precomputed ETA is not an acceptable substitute for actual Missile travel in a CP126 full-map result.

## Blocking validation

CP126 acceptance requires:

1. all 61 metrics to exist with unique names and declared ownership;
2. shared C#/Python geometry fixtures to pass;
3. 2,250 physical mirror comparisons to have zero mismatches;
4. every planned full-map smoke variant to execute without trial error;
5. the substantive run, when executed, to preserve the same telemetry schema and zero trial errors.

## Explicit limits

- Internal critical/subsystem damage remains outside the Python research consumer.
- Damage Control reference progression remains instrumented but is not the primary CP126 combat variable.
- CP126 executes only pure-TL ships; mixed-/legacy-TL component combinations remain deferred.
- Balance outcomes are review evidence and are not telemetry-validation gates.
