# Star Cluster - Checkpoint 11a: Turn-by-Turn Missile Presentation Hotfix

## Purpose

Checkpoint 11a removes ambiguity from the Godot moving-missile demonstration
and makes the launch-turn behavior explicit and testable. A launch now creates
the guided salvo and resolves **exactly one** Missile / Interception guidance
and movement advance. A route that requires later turns remains visibly in
flight; the prototype never performs a hidden resolve-to-completion loop.

The hotfix follows local Checkpoint 11 testing in which a two-hex shot correctly
appeared to hit during the launch phase, while a longer route around the central
star was not sufficiently clear about whether later turns had been simulated.

## Engine-independent launch operation

`MissileLaunchService.LaunchAndAdvanceOnePhase` now owns the atomic launch
operation:

1. create one `GuidedMissileSalvo` at the launcher coordinate;
2. pass the explicit target-track snapshot to
   `MissileGuidanceService.AdvanceOnePhase`;
3. resolve no more than missile speed and remaining lifetime range;
4. return both the new salvo and the single-phase advance report;
5. perform no loop and no automatic later-turn processing.

This gives presentation layers and later combat orchestration one unambiguous
entry point for launch-phase movement.

A target within the missile's speed allowance may still be hit in the launch
phase. That is a legitimate one-phase impact, not fast-forwarding. A longer
route advances only the allowed number of hexes and remains `InFlight`.

## Godot workflow changes

The missile controls are renamed:

- **Launch + advance once** creates the incoming missile and resolves one
  launch-phase advance;
- **Advance once** performs one later guidance advance during a later Missile /
  Interception phase.

The right panel now reports:

- that the last missile command advanced exactly one guidance phase;
- the starting and ending coordinates for that command;
- the number of hexes moved in the phase;
- cumulative range spent and remaining range;
- an explicit outcome: `IMPACT`, `IN FLIGHT`, `WAITING`, or
  `RANGE EXHAUSTED`;
- a stationary-target estimate for additional phases when a route remains.

The launch-route estimate is labeled as a **stationary-target** estimate rather
than implying that those phases have already been resolved.

The map marker now distinguishes terminal results:

- `*` for an active or waiting guided salvo;
- a ring and `!` for impact;
- `x` for range exhaustion, interception, or destruction.

## Tactical phase guard

When a nonterminal missile exists at the beginning of Missile / Interception,
the general phase-advance button is disabled until **Advance once** resolves
that missile phase. This prevents the prototype from silently skipping an
in-flight missile's required guidance advance.

The user may still pass through Missile / Interception when no missile exists.
A terminal missile does not block later phase progression.

## Automated coverage

Checkpoint 11a adds five engine-independent tests for the launch operation:

- a close target is hit during the single launch advance;
- a long route remains in flight after one advance;
- launch never moves beyond missile speed or performs multiple guidance phases;
- no-route launch waits without spending range;
- lost-track launch waits without spending range.

The expected complete suite is **261 passing tests**: 256 from Checkpoint 11
plus five Checkpoint 11a tests.

## Installation

Extract the checkpoint archive directly into the Star Cluster repository root,
close Godot, and run:

```powershell
Set-Location E:\dev\star-cluster
Set-ExecutionPolicy -Scope Process Bypass
.\tools\checkpoints\checkpoint-11a\apply_checkpoint_11a.ps1
```

## Files added or updated

```text
src\StarCluster.Core\Combat\Missiles\GuidedMissileLaunchResult.cs
src\StarCluster.Core\Combat\Missiles\MissileLaunchService.cs
tests\StarCluster.Tests\Combat\Missiles\MissileLaunchServiceTests.cs
src\StarCluster.Game\Scripts\Main.cs
src\StarCluster.Game\Scripts\HexBoardView.cs
src\StarCluster.Game\README.md
tools\checkpoints\checkpoint-11a\apply_checkpoint_11a.ps1
docs\checkpoints\Checkpoint_11a_Turn_By_Turn_Missile_Presentation_Hotfix.md
docs\README.md
```

Concept v0.3b remains current. This hotfix clarifies and enforces the already
approved per-turn missile behavior; it does not change the design direction.

## Acceptance criteria

- The complete solution builds with zero errors and preferably zero warnings.
- All 261 tests pass.
- `StarCluster.Core` remains free of Godot dependencies.
- Launch invokes one and only one guidance phase.
- A two-hex target may be hit immediately by a speed-two missile.
- A route requiring three phases remains in flight after the launch phase.
- The UI explicitly states that later missile phases were not simulated.
- An active missile cannot be skipped by the general phase-advance control.
- The missile's position, traveled range, remaining range, and status remain
  visible between turns.
- Reset map / scenario still restores the complete fixture to turn 1 Movement.

## Suggested Godot smoke test

1. Start the blocked-fire scenario and move the player behind the star.
2. Advance to Missile / Interception.
3. Note the stationary-target launch estimate.
4. Press **Launch + advance once**.
5. Confirm the message says exactly one guidance phase advanced and reports two
   moved hexes.
6. Confirm the missile marker remains between the enemy and player with status
   `InFlight`, rather than appearing at the target.
7. Complete the turn, move the player, and return to Missile / Interception.
8. Confirm the general phase-advance button is disabled until **Advance once**
   is pressed.
9. Press **Advance once** and confirm the route replans from the missile's
   prior coordinate toward the player's new coordinate.
10. Repeat until impact or range exhaustion, verifying cumulative traveled
    range never resets.
11. Repeat with a target two hexes from the launcher and confirm an immediate
    launch-phase impact is explicitly labeled `IMPACT`.
