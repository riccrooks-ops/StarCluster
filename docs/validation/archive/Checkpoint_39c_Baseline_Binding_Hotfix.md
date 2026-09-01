# Checkpoint 39c - Baseline Binding Hotfix

Checkpoint 39c corrects the stale deterministic-corpus expectations exposed after the provisional TL1 Kinetic Cannon changed from DAM 3 to DAM 4. It also closes the architectural cause rather than merely replacing individual expected numbers.

## Baseline-bound deterministic scenarios

Phase A scenario JSON may now use explicit value directives:

- `$baseline` reads a named value from the authoritative 131-value TL1 numerical baseline.
- `$input` reads from the case input after baseline resolution.
- `$actual` reads a produced operation result when an expected field must be related to another result field.
- `$add`, `$subtract`, `$multiply`, `$min`, and `$max` derive expectations without copying mutable values.

The runner validates directive syntax and parameter IDs during preflight. A baseline-binding guard rejects copied nonzero numerical literals at mutable weapon, Shield Recharge, and Reactor output paths.

The Phase A weapon-resource scenario now derives Kinetic damage, Shield absorption, remaining Shield capacity, Tactical Power, ammunition, armor state, and Hull state from the baseline and operation input. Changing `kinetic_damage` no longer requires editing those expectations.

## Phase B production profiles

Phase B cases now declare whether they use a `baseline` or `explicit` profile. Baseline profiles resolve weapon accuracy, targeting-computer condition, weapon damage, power, Hull, Reactor output, and the direct-fire accuracy formula from the same TL1 catalog. Preflight rejects copied numerical overrides in baseline-profile cases.

Qualitative mechanics fixtures may still opt into `explicit` profiles. This keeps low-level rule tests stable while preventing production-balance values from being duplicated across scenario files.

## Core deterministic fixtures

Core unit tests use a clearly named `MechanicsFixture` profile. Its purpose is to test simulator behavior at fixed inputs, not to mirror the current production balance. Production calibration profiles are created by `Tl1BaselineFactory` from the authoritative catalog.

## Scope

This hotfix does not change the Checkpoint 39 movement, missile, Kinetic, Shield, Damage Control, or disengagement mechanics. It changes how deterministic tests and calibration profiles obtain mutable baseline values.
