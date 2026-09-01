# Checkpoint 12a — Direct-Fire Commitment and Layered Interception

## Purpose

Checkpoint 12a corrects the tactical phase order and closes two Godot integration gaps discovered during local testing:

- returning to Movement after Direct Fire could leave stale targeting state active and prevent the player ship from being selected again;
- generic interception occurred before Direct Fire, allowing the prototype to imply that one weapon could intercept a missile and still attack the enemy ship in the same turn.

The hotfix moves Direct Fire before missile movement, requires an explicit main-weapon commitment, preserves a separate Point Defense System auxiliary layer, centralizes phase-entry state restoration, and removes the Checkpoint 12 nullable compiler warning.

## Revised tactical phase order

Repeatable combat turns now resolve in this order:

1. Movement
2. Direct Fire
3. Missile / Interception
4. Damage
5. Damage Control

This lets the player decide whether a main direct-fire weapon attacks offensively or remains available for missile defense before missiles move or are launched later in the turn.

## Main direct-fire weapon commitments

During Direct Fire, the player must choose exactly one action for the prototype main weapon:

- **Fire main weapon at selected ship** — resolves against the selected enemy ship, subject to current range and line of sight.
- **Intercept selected missile** — commits the weapon to one existing hostile salvo. If that missile is already in range and line of sight, the shot resolves immediately. Otherwise, the order remains suspended until the same salvo becomes eligible during the upcoming Missile / Interception phase.
- **Hold main weapon for any missile** — reserves the weapon for the first eligible hostile salvo during the upcoming missile phase, including a missile launched after the order was committed.
- **Hold main weapon fire** — explicitly spends no offensive or interception shot and allows the phase to advance.

A main weapon cannot attack a ship and intercept a missile during the same turn unless a later special capability explicitly overrides that rule.

## Layered interception

`DirectFireOrder`, `DirectFireWeaponProfile`, and `DirectFireOrderType` are engine-independent Core types. Missile-interception commitments convert into a `MissileDefenseSystem` identified as `HeldDirectFireWeapon`.

Checkpoint 12a distinguishes two independent defensive sources:

- **Held main weapon** — longer prototype range, one attempt, requires line of sight, and may be tied to one salvo or the first eligible hostile salvo.
- **Point Defense System auxiliary** — short-range automatic reaction with its own attempt budget and no consumption of the main weapon action.

The held main weapon has earlier deterministic priority. If it misses, the PDS may receive a later opportunity when the missile enters its envelope. If the earlier layer intercepts the salvo, later layers do not fire redundantly.

A held order that never becomes eligible expires after the Missile / Interception phase. The weapon remains spent for that turn because the player deliberately reserved it.

## Line of sight and target specificity

Held direct-fire interception requires both range and direct-fire line of sight. `MissileInterceptionPhaseContext` therefore accepts the current `SystemMap` when any defensive system requires line of sight.

A selected-missile order ignores every other hostile salvo. A hold-for-any order spends its one attempt on the first eligible hostile salvo according to deterministic salvo and defense ordering.

## Godot phase-state restoration

All phase transitions now pass through one phase-entry method. Entering Movement explicitly:

- restores Ship movement mode;
- clears Direct Fire and missile selections;
- clears route previews and stale combat targeting;
- resets the movement-resolved flag;
- recalculates legal destinations from the current player position;
- reenables movement input without requiring a full encounter reset.

Entering Direct Fire similarly clears stale selections, resets the direct-fire commitment, and selects the Direct fire overlay. Missile markers remain visible in Direct Fire so an existing hostile salvo can be selected.

## Warning cleanup

The nullable `TryGetValue` output in `Main.cs` is now represented as nullable and explicitly checked before dereference, eliminating the Checkpoint 12 `CS8600` warning without suppressing nullable analysis.

## Tests

Checkpoint 12a adds 18 engine-independent tests:

- 10 direct-fire profile and order tests;
- 8 target-specific, hold-for-any, line-of-sight, and layered-interception tests.

The existing tactical-turn tests are updated for the new phase order.

Expected complete suite after application: **311 tests**.

## Local validation

Close Godot, extract the package into the repository root, then run:

```powershell
Set-Location E:\dev\star-cluster
Set-ExecutionPolicy -Scope Process Bypass
.\tools\checkpoints\checkpoint-12a\apply_checkpoint_12a.ps1
```

Then press F5 in Godot and validate:

1. Move or hold, then confirm the next phase is Direct Fire.
2. Select the red ship and fire the main weapon; confirm the main weapon cannot also be reserved for interception.
3. On a later turn with an existing hostile missile, select it during Direct Fire and commit a specific interception order.
4. Reserve the main weapon for any missile, then launch an enemy missile during Missile / Interception and confirm the held order can react.
5. Set the deterministic result to MISS and confirm the held main weapon and PDS can produce two separate attempts when both envelopes become eligible.
6. Set the result to INTERCEPT and confirm later layers do not fire after the missile is destroyed.
7. Select an enemy during Direct Fire, complete the turn, and confirm the next Movement phase automatically restores ship selection and legal destinations.
8. Repeat several complete turns without resetting the encounter.
9. Reset from Movement, Direct Fire, Missile / Interception, and after impact; confirm turn 1 Movement is restored every time.

## Deferred

- final direct-fire damage and accuracy;
- final weapon and PDS range progressions;
- probabilistic interception and TL contests;
- multiple installed direct-fire weapons and independent commitments;
- ammunition, heat, power, and crew effects;
- target-track quality, spoofing, reacquisition, and electronic warfare;
- AI weapon-commitment policy.

## Next candidate checkpoint

After local acceptance, the strongest next pass is **target-track quality and sensor/electronic-warfare foundations**. The action-economy and layered-defense seams are now explicit enough for sensor quality to affect missile guidance, direct-fire eligibility, and interception without revisiting phase order.
