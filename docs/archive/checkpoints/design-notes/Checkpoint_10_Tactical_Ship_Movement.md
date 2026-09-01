# Star Cluster - Checkpoint 10: Tactical Ship Movement Foundations

## Purpose

Checkpoint 10 implements the first engine-independent tactical ship-movement
rules and connects them to the Godot prototype. It establishes explicit
Sublight Propulsion performance, deterministic shortest legal routes, movement
allowance checks, legal-destination overlays, committed map movement, hold
commands, and a stable tactical turn-phase cursor.

The checkpoint does **not** yet move enemy ships automatically or replan
in-flight missiles. Those behaviors remain the focused work for Checkpoint 11.
Concept v0.3b records their approved rules now so the design reference and the
implementation sequence remain synchronized.

## Engine-independent movement model

### Explicit sublight performance

`SublightMovementProfile` stores:

- Sublight Propulsion technology level, TL1 through TL9;
- maximum system-map hexes the ship may traverse in one Movement phase.

The final TL-to-movement table is deliberately not hard-coded. A profile's
allowance is supplied as balance data so later playtesting can change the
progression without changing route or command logic.

A zero allowance is legal and represents disabled or otherwise immobile
propulsion. Holding position remains legal.

### Route rules

`ShipMovementPlanner.FindRoute` applies these prototype rules:

1. Origin and destination must exist on the finite `SystemMap`.
2. The route contains both endpoints.
3. Consecutive cells are adjacent.
4. The shortest legal route is selected by breadth-first search.
5. Equal-length ties are deterministic because `HexCoord.Neighbors()` uses its
   fixed direction order.
6. Stars, planets, stations, and other ships block traversal and occupation.
7. Anomalies and wreckage do not block movement in the current abstraction.
8. The moving ship's occupied origin is legal.
9. Holding position is a zero-distance `Found` route.
10. A legal route longer than the current allowance is returned as
    `OutOfRange` and retained for UI explanation.
11. A solid occupied destination reports `Occupied`.
12. A destination that cannot be reached through any legal cells reports
    `NoRoute`.

`FindLegalDestinations` performs a bounded breadth-first traversal and returns
the origin plus every reachable destination within the allowance. It respects
routed distance rather than simple axial radius, so stars, planets, stations,
and ships can reduce or reshape the legal area.

### Command commitment

`ShipMovementService.Execute` accepts a map, stable ship ID, supplied current
coordinate, selected destination, and movement profile. It:

- verifies that the expected ship is at the supplied origin;
- calculates the authoritative route;
- rejects occupied, no-route, and over-allowance commands without changing the
  map;
- returns `Held` for an origin-to-origin command;
- commits a legal move through the existing `SystemMap.Move` operation;
- reports the final coordinate and complete plan.

Movement remains map state, not presentation state. Godot never changes the
ship's coordinate independently.

## Tactical turn cursor

`TacticalTurnState` implements the repeatable combat sequence:

1. Movement
2. Missile / Interception
3. Direct Fire
4. Damage
5. Damage Control

Advancing from Damage Control increments the turn number and returns to
Movement. Encounter Contact remains the setup step before this repeatable turn
cycle rather than a phase repeated every round.

Checkpoint 10 uses the phase cursor to enable or disable player movement in the
Godot prototype. Other prototype demonstrations are not yet fully phase-gated;
that will be tightened as missile, direct-fire, and damage commands become
complete systems.

## Godot presentation

The Checkpoint 09a responsive layout remains in place. Checkpoint 10 adds:

- a **Ship movement** overlay;
- highlighted legal destinations from `StarCluster.Core`;
- click-to-preview shortest routes;
- green legal and orange rejected route visualization;
- **Commit move** and **Hold** controls, limited to one player movement command per Movement phase;
- an explicit player movement profile display;
- current tactical turn and phase display;
- an **Advance phase** control;
- automatic recalculation of direct-fire and launch-time missile routes after a
  committed ship move;
- reset of the static demonstration salvo after the launching ship moves.

The prototype player profile is TL4 with an allowance of 3 hexes per Movement
phase. This is demonstration data, not a final TL progression.

## Concept v0.3b synchronization

Concept v0.3b is now current. It records:

- per-turn routed sublight movement from each ship's current coordinate;
- zero-cost holding position;
- movement blockers and explicit data-driven allowances;
- the possibility that a sufficiently fast high-TL ship can outrun a slower
  low-TL missile;
- missile replanning after ship movement from the missile's current coordinate
  toward its current tracked target coordinate;
- lifetime cumulative distance traveled against one fixed maximum range;
- no range restoration when a route is replaced;
- continued flight when the target is currently beyond remaining reach;
- waiting without movement or range consumption when no legal route currently
  exists;
- deferred handling for targets that can be proven permanently unreachable.

The executable missile-guidance portion remains Checkpoint 11.

## Automated coverage

Checkpoint 10 adds 24 engine-independent tests covering:

- valid and invalid movement profiles;
- explicit allowance data rather than implicit TL scaling;
- hold routes;
- open movement;
- route adjacency;
- star and planet detours;
- occupied ship and station destinations;
- anomaly coexistence;
- retained over-allowance route previews;
- enclosed no-route destinations;
- legal-destination enumeration;
- committed `SystemMap` movement;
- the complete tactical phase order and turn rollover.

The expected total is **232 passing tests**: 208 from Checkpoint 09a's verified
foundation plus 24 new tests.

## Installation

Extract the checkpoint archive directly into the Star Cluster repository root,
allowing `src`, `tests`, `tools`, and `docs` to merge. Close Godot before
applying the checkpoint, then run:

```powershell
Set-Location E:\dev\star-cluster
Set-ExecutionPolicy -Scope Process Bypass
.\tools\checkpoints\checkpoint-10\apply_checkpoint_10.ps1
```

## Files added or updated

```text
src\StarCluster.Core\Movement\SublightMovementProfile.cs
src\StarCluster.Core\Movement\ShipMovementStatus.cs
src\StarCluster.Core\Movement\ShipMovementRoute.cs
src\StarCluster.Core\Movement\ShipMovementResult.cs
src\StarCluster.Core\Movement\ShipMovementPlanner.cs
src\StarCluster.Core\Movement\ShipMovementExecutionStatus.cs
src\StarCluster.Core\Movement\ShipMovementExecutionResult.cs
src\StarCluster.Core\Movement\ShipMovementService.cs
src\StarCluster.Core\Combat\TacticalTurnPhase.cs
src\StarCluster.Core\Combat\TacticalTurnState.cs
tests\StarCluster.Tests\Movement\SublightMovementProfileTests.cs
tests\StarCluster.Tests\Movement\ShipMovementPlannerTests.cs
tests\StarCluster.Tests\Combat\TacticalTurnStateTests.cs
src\StarCluster.Game\Scripts\DemoScenario.cs
src\StarCluster.Game\Scripts\HexBoardView.cs
src\StarCluster.Game\Scripts\Main.cs
src\StarCluster.Game\Scripts\TargetingMode.cs
src\StarCluster.Game\README.md
tools\checkpoints\checkpoint-10\apply_checkpoint_10.ps1
docs\Star_Cluster_Game_Concept_v0.3b.docx
docs\archive\Star_Cluster_Game_Concept_v0.3a.docx
docs\checkpoints\Checkpoint_10_Tactical_Ship_Movement.md
docs\README.md
```

## Acceptance criteria

- The complete solution builds with zero errors.
- Preferably, zero warnings are reported.
- All 232 tests pass.
- `StarCluster.Core` remains free of Godot dependencies.
- Movement allowance is explicit data and is not inferred from TL by the route
  algorithms.
- Holding is legal at zero routed distance.
- Stars, planets, stations, and ships block movement.
- Anomalies and wreckage remain non-blocking.
- Legal destinations account for routed obstacles.
- Over-allowance routes remain available for previews but cannot be committed.
- Committed movement updates `SystemMap` through its authoritative operation.
- The tactical phase sequence rolls over correctly to the next turn.
- At 1280 x 800, the complete map remains visible and the right panel remains
  scrollable.
- Selecting **Ship movement** highlights legal destinations.
- Clicking a destination previews the route and status.
- **Commit move** changes the player's map position only during Movement.
- **Hold** leaves the ship in place and resolves its movement command for that phase.
- A committed move or hold cannot be repeated until the next Movement phase.
- Direct-fire and launch-time missile route displays update after movement.
- Concept v0.3b is current and v0.3a is preserved under `docs\archive`.

## Focus for Checkpoint 11

Checkpoint 11 should implement moving-target missile guidance while preserving
Checkpoint 08 launch-time behavior as a compatibility baseline. It should add:

- a replaceable future route on each in-flight salvo;
- cumulative lifetime distance traveled and derived remaining maximum range;
- current and last-known tracked target coordinates;
- guidance replanning after all ship movement;
- continued flight along an `OutOfRange` route;
- a waiting state that consumes no range when no route exists;
- arrival, interception, range-exhausted, lost-track, and permanent-impossibility
  outcomes;
- tests in which a fast ship outruns a slow missile and a close launch still
  catches a faster ship.
