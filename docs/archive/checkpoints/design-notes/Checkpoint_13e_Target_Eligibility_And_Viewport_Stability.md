# Checkpoint 13e — Target Eligibility and Tactical Viewport Stability

## Purpose

Checkpoint 13e tightens the distinction between inspecting a contact, targeting it immediately, and reserving a weapon for future interception. It also prevents changing right-panel feedback text from resizing or recentering the tactical map.

The governing rule is simple:

- ordinary ship fire requires a current Firm track, current weapon LOS, and current range;
- a specific missile order requires a current Firm track and current weapon LOS;
- a specific missile may be reserved only when it is presently visible but still outside weapon range;
- a stale, approximate, lost, unknown, or currently occluded missile cannot receive a specific order;
- **Hold main weapon for any missile** is the correct order when no particular missile is presently targetable.

## Engine-independent target eligibility

Checkpoint 13e adds a shared direct-fire eligibility service and explicit result states. Both command execution and Godot presentation consume the same result so a disabled button cannot disagree with the authoritative command gate.

### Ship attack

A ship attack is legal only when all of the following are true at Direct Fire commitment time:

- the selected ship has a Firm track;
- a usable tracked coordinate exists;
- weapon LOS is clear;
- the ship is within the main weapon's current range.

Ships have already completed Movement, so blocked or out-of-range ship attacks are not suspended for later in the turn.

### Specific missile interception

A specific missile order requires:

- an intercept-capable main weapon;
- a Firm current missile track;
- a usable current missile coordinate;
- clear current weapon LOS.

If the missile is in range, the weapon fires immediately during Direct Fire. If it is outside range but otherwise eligible, the weapon may reserve against that named missile and fire if it enters range during Missile / Interception.

A missile that is stale or behind an obstruction may still be clicked for inspection, but it receives a muted inspection ring rather than the yellow weapon-target ring. The specific-interception button remains disabled and the panel directs the player to **Hold main weapon for any missile**.

## Tactical viewport stability

The right panel now resides inside a fixed-width layout host. Wrapped status and feedback text can change without increasing the HBox minimum size, shrinking the board, moving the board center, changing zoom, or clipping the bottom row.

The tactical map should change layout only for scenario initialization, reset, or an actual window resize—not because a command changed a label.

## Resolution-cue lifetime

Missile impact and interception cues persist through the Damage phase. They clear when leaving Damage for Damage Control or when another tactical action replaces them. This keeps the visible result present while the phase that will eventually apply its consequences is active.

## Repeatable validation encounter

Continue using `docs/validation/archive/Tested_Tactical_Regression_Checkpoints_09_Through_17a.md` with the same movement coordinates.

Checkpoint 13e-specific checks:

- Turn 1 ship fire is enabled only with Firm track, clear LOS, and range;
- Turn 2 `hostile-1` can be intercepted immediately when its current firing solution is valid;
- Turn 3 the stale/occluded `hostile-1` remains inspectable, but specific interception is unavailable and no yellow weapon-target ring appears;
- Turn 3 **Hold main weapon for any missile** remains available;
- committing any Direct Fire order does not move, resize, recenter, or clip the tactical map;
- Turn 4 `IMPACT x2` remains visible during Damage and clears on entry to Damage Control.

## Automated coverage

Checkpoint 13e adds 10 engine-independent tests covering:

- Firm-track requirements for ship and missile targets;
- usable tracked-coordinate requirements;
- current LOS requirements;
- current ship-weapon range requirements;
- immediate specific-missile interception;
- range-only specific-missile reserve;
- non-intercept-capable weapon rejection.

Expected complete test count: **421**.
