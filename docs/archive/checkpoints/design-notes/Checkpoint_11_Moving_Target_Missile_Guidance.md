# Star Cluster - Checkpoint 11: Moving-Target Missile Guidance

## Purpose

Checkpoint 11 implements the first engine-independent moving-target missile
lifetime and connects it to the tactical Godot prototype. An in-flight guided
salvo now replans during each Missile / Interception phase from its current
coordinate toward an explicitly supplied sensor-track coordinate. Replanning
changes only the future route: distance already traveled remains spent against
one fixed lifetime maximum range.

This checkpoint also adds a full **Reset map / scenario** command to the right
panel and prevents the tactical phase cursor from leaving Movement until the
player has committed a move or explicitly held position. These presentation
changes address the possibility of accidentally advancing out of Movement and
then having no convenient way to restart the fixture.

Checkpoint 08's static `MissileSalvo` remains available as a compatibility
baseline. Checkpoint 11 introduces `GuidedMissileSalvo` rather than silently
changing the established launch-time class.

## Engine-independent target tracks

`MissileTargetTrackSnapshot` is the only target-location input accepted by the
new guidance service. Missile code does not inspect a target ship directly.

A snapshot has one of three qualities:

- `Current`: guidance may use the target's current coordinate;
- `Stale`: guidance may use an explicitly supplied last-known coordinate;
- `Lost`: no guidance coordinate is available during this phase.

The guided salvo records the current tracked coordinate when one exists, its
last-known coordinate, and the quality of the most recent track. Reaching a
current coordinate produces arrival. Reaching only a stale last-known
coordinate produces `WaitingForTrack`, not a false impact.

The prototype currently supplies a perfect current track for the player ship.
The explicit snapshot boundary preserves a later seam for sensor quality,
jamming, decoys, Tactical Officer effects, and target-lock loss.

## Guided missile lifetime

`GuidedMissileSalvo` records:

- stable salvo, launcher, and target IDs;
- launch and current coordinates;
- explicit missile flight profile;
- cumulative lifetime distance traveled;
- remaining range derived as maximum range minus cumulative travel;
- guidance-phase count;
- current and last-known target-track coordinates;
- latest route plan;
- current lifetime status.

The supported statuses are:

- `InFlight`;
- `WaitingForRoute`;
- `WaitingForTrack`;
- `Arrived`;
- `RangeExhausted`;
- `Intercepted`;
- `Destroyed`.

Arrival, range exhaustion, interception, and destruction are terminal. The
checkpoint exposes explicit interception and destruction markers but does not
yet implement weapon-versus-missile interception resolution.

## Per-phase guidance rules

`MissileGuidanceService.AdvanceOnePhase` applies these rules:

1. Reject a target track whose stable target ID does not match the salvo.
2. Leave a terminal salvo unchanged.
3. Record the supplied track snapshot.
4. If no guidance coordinate is available, wait without moving or spending
   range.
5. If the missile is already at a current tracked coordinate, arrive.
6. If no range remains before movement and the target has not been reached,
   become `RangeExhausted`.
7. Replan from the missile's current coordinate to the supplied guidance
   coordinate using the remaining lifetime range as the route planner's current
   range budget.
8. If no legal route exists, become `WaitingForRoute` and consume no range.
9. If a route exists but is longer than remaining range, retain the
   `OutOfRange` route and continue along it while range remains.
10. Move by no more than missile speed and remaining lifetime range.
11. Add every entered hex permanently to cumulative distance traveled.
12. Arrive only at a current tracked coordinate. At a stale last-known
    coordinate, wait for a new track.
13. If the final range hex is spent without arrival, become
    `RangeExhausted`.

A later phase always replans again. A target that moves, or a changing
battlefield that creates a route, can therefore cause a waiting missile to
resume. No permanent-impossibility detector is introduced; that decision
remains deferred as recorded in Concept v0.3b.

## Faster ships and finite-range pursuit

The tests now demonstrate both sides of the intended relationship:

- a target that increases separation faster than a slow finite-range missile
  closes can force the missile to expend its complete range without impact;
- a missile launched close enough, or with enough speed, can still reach a
  faster-moving target before separation becomes decisive.

The tests use explicit profile values. No final TL-to-speed or TL-to-range table
is embedded in the algorithms.

## Godot prototype workflow

The missile demonstration is now incoming rather than player-launched:

1. Begin in turn 1 Movement.
2. Commit a player move or press **Hold**.
3. Advance to **Missile / Interception**.
4. Press **Launch incoming**. The enemy missile appears at the enemy ship and
   the missile phase is resolved for that turn.
5. Complete the remaining phases.
6. On the next turn, move the player again.
7. During Missile / Interception, press **Advance guidance**.
8. The missile replans from its current coordinate to the player's new tracked
   coordinate, moves by its speed, and retains all range already spent.

The missile overlay displays the latest in-flight route when available. Before
first guidance, it displays the current enemy-to-player launch route. The state
panel reports current position, cumulative range use, remaining range, latest
route status, and lifetime status.

## Reset and phase-safety improvements

The right panel now contains **Reset map / scenario** near the top. It rebuilds
the selected fixture and restores:

- both ships to their original coordinates;
- turn 1 Movement;
- no missile in flight;
- no movement preview or selection;
- unresolved player movement;
- recalculated line of sight, launch route, and legal destinations.

The former missile **Launch / reset** wording is removed. Missile launch and
full scenario reset are now separate commands.

The **Advance to Missile / Interception** button is disabled until the player
commits a legal move or presses **Hold**. This prevents an accidental phase
advance from silently closing the current Movement opportunity. The full reset
remains available in every phase.

## Automated coverage

Checkpoint 11 adds 24 engine-independent tests:

- 4 target-track snapshot tests;
- 4 guided-salvo lifetime and terminal-state tests;
- 16 guidance-service tests.

Coverage includes current, stale, and lost tracks; speed-limited movement;
arrival; route replacement; cumulative range; retained out-of-range routes;
no-route waiting; resumption after target movement; stale-coordinate waiting;
range exhaustion; terminal-state immobility; target-ID validation; a fast ship
outrunning a slower missile; and a close launch catching a moving target.

The expected complete suite is **256 passing tests**: 232 from Checkpoint 10
plus 24 new Checkpoint 11 tests.

## Installation

Extract the checkpoint archive directly into the Star Cluster repository root,
allowing `src`, `tests`, `tools`, and `docs` to merge. Close Godot before
applying the checkpoint, then run:

```powershell
Set-Location E:\dev\star-cluster
Set-ExecutionPolicy -Scope Process Bypass
.\tools\checkpoints\checkpoint-11\apply_checkpoint_11.ps1
```

## Files added or updated

```text
src\StarCluster.Core\Combat\Missiles\MissileTargetTrackQuality.cs
src\StarCluster.Core\Combat\Missiles\MissileTargetTrackSnapshot.cs
src\StarCluster.Core\Combat\Missiles\GuidedMissileStatus.cs
src\StarCluster.Core\Combat\Missiles\GuidedMissileAdvanceResult.cs
src\StarCluster.Core\Combat\Missiles\GuidedMissileSalvo.cs
src\StarCluster.Core\Combat\Missiles\MissileGuidanceService.cs
tests\StarCluster.Tests\Combat\Missiles\MissileTargetTrackSnapshotTests.cs
tests\StarCluster.Tests\Combat\Missiles\GuidedMissileSalvoTests.cs
tests\StarCluster.Tests\Combat\Missiles\MissileGuidanceServiceTests.cs
src\StarCluster.Game\Scripts\HexBoardView.cs
src\StarCluster.Game\Scripts\Main.cs
src\StarCluster.Game\README.md
tools\checkpoints\checkpoint-11\apply_checkpoint_11.ps1
docs\checkpoints\Checkpoint_11_Moving_Target_Missile_Guidance.md
docs\README.md
```

The synchronized package continues to include Concept v0.3b and its archived
predecessors. No concept revision is required because v0.3b already records the
implemented replanning, cumulative-range, no-route waiting, and pursuit rules.

## Acceptance criteria

- The complete solution builds with zero errors.
- Preferably, zero compiler warnings are reported.
- All 256 tests pass.
- `StarCluster.Core` remains free of Godot dependencies.
- Guidance receives an explicit track snapshot rather than querying a target.
- A new route begins at the missile's current coordinate.
- Replanning never resets cumulative distance or remaining range.
- An `OutOfRange` in-flight route is retained and followed while fuel remains.
- `NoRoute` and `Lost` states wait without consuming range.
- A waiting missile can resume when a later target coordinate has a route.
- A stale last-known coordinate cannot create a false target impact.
- A missile is terminal only after arrival, full range expenditure,
  interception, or destruction.
- A faster ship can outrun a sufficiently slow finite-range missile.
- A close or faster missile can still intercept the moving target.
- **Reset map / scenario** fully restores the selected fixture from every phase.
- Movement cannot be skipped accidentally; move or hold is required before
  advancing from Movement.
- The moving player remains the incoming missile's target after every committed
  movement.
- Concept v0.3b remains the current design reference.

## Suggested Godot smoke test

1. Open the project and press F5.
2. Confirm **Advance to Missile / Interception** is disabled before movement.
3. Preview a destination, then press **Reset map / scenario** and confirm the
   preview clears and both ships return to their initial positions.
4. Move the player behind the star, advance to Missile / Interception, and
   launch the incoming missile.
5. Complete the turn, move the player again, and advance guidance during the
   next missile phase.
6. Confirm the missile marker moves from its previous position, the displayed
   route changes toward the player's new coordinate, and traveled range does
   not reset.
7. Press **Reset map / scenario** while the missile is in flight and confirm
   turn 1 Movement, original ship positions, no missile, and fresh overlays.
8. Switch to Direct fire after a movement that places the star between the
   ships and confirm line of sight is still recalculated from authoritative map
   state.

## Deferred work

Checkpoint 11 does not yet implement:

- target-track quality checks, jamming, decoys, or seeker contests;
- automatic enemy movement or AI;
- point-defense or held-energy interception resolution;
- payload, impact, damage, or area effects;
- multiple simultaneous salvos;
- permanent-impossibility detection;
- final TL progression or missile-family balance.
