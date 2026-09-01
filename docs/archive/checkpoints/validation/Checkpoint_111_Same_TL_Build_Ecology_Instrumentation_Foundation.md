# Checkpoint 111 - Same-TL Build Ecology Instrumentation Foundation

## Objective

Expand the Python research environment from subsystem-focused calibration into an instrumented build-level design-space laboratory without changing Star Cluster gameplay rules or promoting technology values.

## Accepted baseline

Checkpoint 110 is the native-accepted first-pass Power/Reactor calibration baseline. CP111 freezes the CP110 production/test surface and the untouched Python research base, consumes the CP109 whole-ladder candidate numerical matrix plus the CP110 retained Reactor profile, and adds a new same-TL ecology consumer.

## Primary population

- TL1-TL9.
- 12 exact-fill frontier builds per TL.
- Kinetic, Energy, and Missile Main Weapon families.
- Balanced, dual-main, dual-reactor, and family-specialist archetypes.
- 108 builds total.
- 66 unordered pairings per TL / 594 total.
- Both movement-order mirrors / 1,188 variants.
- Residual not-yet-numerical support capacity is recorded as zero-effect mission AUX Space. No build leaves free Space.

## Damage scope

CP111 Python ecology uses `layered_defense_hull_only`. It resolves Shield Armor, Shields, Armor Protection/Integrity, and Hull. Internal critical/subsystem damage remains outside the current research consumer and is explicitly reported as not simulated.

## Instrumentation gate

The primary ecology must exercise and report weapon/missile effects, PDS, track quality, ECM/ECCM, burn-through, Tactical Power allocation and shortfalls, Shield recharge/Hardener, Reactor overload, movement/fuel/map constraints, and layered damage. Risky Sensor/ECM/ECCM/STL overload paths remain zero-weight deterministic probes in CP111 rather than primary-doctrine behavior.

## Workload

Checked-in authoring evidence uses 100 trials/variant (118,800 engagements). The native substantive run uses 1,000 trials/variant (1,188,000 engagements). The checkpoint has no target win rate; dominance/weakness and movement-order signals are non-blocking review evidence.

Mixed-TL/legacy construction is registered but not executed and has zero CP111 inference weight. It will be added as a separate overlay after the fixed-TL baseline is accepted.

## Native acceptance

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-111\apply_checkpoint_111.ps1 -RepositoryOnly
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-111\apply_checkpoint_111.ps1
```

The normal invocation runs the Python self-tests, deterministic C#/Python parity fixtures, a one-trial-per-variant full ecology smoke, the 1,188,000-engagement substantive ecology, and runtime-output contract verification. Production C#/Godot source remains unchanged.
