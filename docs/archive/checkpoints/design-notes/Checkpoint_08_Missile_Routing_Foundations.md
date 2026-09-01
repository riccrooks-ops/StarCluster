# Star Cluster - Checkpoint 08: Missile Routing Foundations

## Purpose

Checkpoint 08 establishes the first engine-independent model for guided
missiles and torpedoes. It implements deterministic shortest-path routing
around stars and planets, routed range checks, explicit missile speed, derived
travel time, and an in-flight logical salvo that advances along its route.

This checkpoint deliberately does not yet implement target-track quality,
mid-flight replanning, interception, guidance checks, damage, payloads, or
weapon firing rules. Those systems can be added on top of the stable route and
flight-state foundation.

No Godot dependency is introduced.

## Routing rules

1. The origin and target must be existing cells on the finite `SystemMap`.
2. The route contains both origin and target.
3. Every consecutive route cell must be adjacent.
4. Stars and planets are impassable intermediate cells.
5. Ships, stations, anomalies, and wreckage do not block missile travel yet.
6. The origin and target remain legal endpoints even if a star or planet is
   present there. This preserves future options such as planetary bombardment
   or missiles launched from a planetary installation.
7. The planner returns the shortest legal route by breadth-first search.
8. Equal-length ties are deterministic because neighbors are expanded in the
   fixed axial direction order.
9. Routed distance, not direct axial distance, is authoritative for missile
   range.
10. A legal route longer than maximum range is reported as `OutOfRange` and is
    retained for diagnostics and user-interface previews.
11. A completely enclosed destination or origin produces `NoRoute`.

## Route-planning result

`MissileRoutePlanner.FindRoute` returns a `MissileRouteResult` with:

- `Status`: `Found`, `OutOfRange`, or `NoRoute`
- `DirectDistance`
- `RoutedDistance`
- `MaximumRange`
- `Route`
- `Path`
- `HasRoute`
- `CanLaunch`

An out-of-range result still exposes the shortest legal route. A no-route
result has no route or path.

## Flight performance

`MissileFlightProfile` currently stores:

- Missile Weapons technology level, from TL1 through TL9
- Maximum routed range
- Speed in hexes per missile-movement turn

This checkpoint intentionally does not hard-code the final range and speed for
each TL. Those numbers are balance data and may change substantially during
playtesting. Keeping them explicit prevents route algorithms from depending on
a premature progression table.

Travel time is derived by ceiling division:

```text
travel turns = ceil(routed distance / speed in hexes per turn)
```

For example, a routed distance of 7 at speed 3 requires 3 missile-movement
turns.

## Logical missile salvo

`MissileSalvo` is a logical in-flight combat state rather than a normal
`MapObject`.

It records:

- stable salvo ID
- launcher ID
- target ID
- planned route
- flight profile
- current route index and coordinate
- distance traveled and remaining
- total and estimated remaining travel turns
- arrival state

`AdvanceOneTurn` moves the salvo by at most its speed and returns every route
cell entered in traversal order. This gives later interception and animation
systems precise per-turn movement information.

The salvo is not inserted into `SystemMap`, so it does not occupy a solid cell
or interfere with ship, planet, or station placement. Godot may later render a
salvo marker without making that marker authoritative game state.

## Static route limitation

The route is a launch-time plan to the selected target coordinate. This
checkpoint does not automatically replan for a moving target or a changed
battlefield. Later guidance rules may:

- update the target coordinate from a maintained sensor track;
- replan the remaining route;
- consume guidance capability or impose penalties;
- lose the target and continue to a last-known position;
- fail when no legal or in-range revised route exists.

Keeping that behavior deferred avoids choosing guidance semantics before the
sensor and target-track systems exist.

## Installation

Extract the checkpoint archive directly into:

`E:\dev\star-cluster`

Allow it to merge with the existing `src`, `tests`, `tools`, and `docs`
folders. Then run:

```powershell
Set-Location E:\dev\star-cluster
Set-ExecutionPolicy -Scope Process Bypass
.\tools\checkpoints\checkpoint-08\apply_checkpoint_08.ps1
```

## Expected result

A successful run should end with:

```text
Checkpoint 08 completed successfully.
```

The expected total is **208 passing tests**.

## Files added or updated

```text
src\StarCluster.Core\Maps\MapObject.cs                         (updated)
src\StarCluster.Core\Combat\Missiles\MissileRouteStatus.cs
src\StarCluster.Core\Combat\Missiles\MissileRoute.cs
src\StarCluster.Core\Combat\Missiles\MissileRouteResult.cs
src\StarCluster.Core\Combat\Missiles\MissileRoutePlanner.cs
src\StarCluster.Core\Combat\Missiles\MissileFlightProfile.cs
src\StarCluster.Core\Combat\Missiles\MissileAdvanceResult.cs
src\StarCluster.Core\Combat\Missiles\MissileSalvo.cs
tests\StarCluster.Tests\Combat\Missiles\MissileRoutePlannerTests.cs
tests\StarCluster.Tests\Combat\Missiles\MissileFlightProfileTests.cs
tests\StarCluster.Tests\Combat\Missiles\MissileSalvoTests.cs
tests\StarCluster.Tests\Maps\MapObjectMissileTests.cs
tools\checkpoints\checkpoint-08\apply_checkpoint_08.ps1
docs\checkpoints\Checkpoint_08_Missile_Routing_Foundations.md
docs\README.md                                                  (updated)
```

The package carries the complete synchronized `docs` folder. Concept v0.3a
remains current because it already records missile routing, time of flight,
range, target-track, interception, and TL-improvement direction.

## Design notes

### Why breadth-first search is sufficient

System maps currently contain only 91 cells, and every traversable step has the
same cost. Breadth-first search therefore guarantees a shortest route with
little complexity. A weighted algorithm can replace it later if terrain,
gravity, or guidance introduces differing movement costs.

### Why range uses routed distance

A star or planet can force a missile to travel farther than the direct axial
separation. Using routed distance makes obstacles tactically meaningful and
creates natural interactions among range, speed, interception exposure, and
positioning.

### Why out-of-range routes are retained

The user interface may need to show why a launch is impossible, how many
additional range hexes are required, or how an obstruction lengthens the path.
Discarding the route would force a second planning pass solely for explanation.

### Why ships do not block the route yet

Ships are potential interception participants and targets, not permanent
navigation walls. Collision, proximity fuzes, screening, and interception
belong to later missile-combat rules rather than the path planner.

### Why the TL table is deferred

The concept establishes that higher missile TL should improve selected traits,
but not necessarily every trait at every level. Encoding a fixed one-through-
nine range and speed table now would turn an early hypothesis into a hidden
rule. The profile stores the values explicitly until playtesting supports a
progression.

## Review in Visual Studio

After the script succeeds:

1. Open `MissileRoutePlanner.cs` and follow the breadth-first search.
2. Compare `DirectDistance` and `RoutedDistance` in the obstacle tests.
3. Open `MissileFlightProfile.cs` and inspect the travel-turn calculation.
4. Open `MissileSalvo.cs` and follow `AdvanceOneTurn`.
5. Inspect tests for a central-star detour, no-route enclosure, out-of-range
   diagnostics, per-turn movement, and map-occupancy independence.
6. In **Test > Test Explorer**, select **Run All Tests**.

## Checkpoint acceptance criteria

- Solution builds with zero errors.
- Preferably, zero compiler warnings are reported.
- All 208 tests pass.
- Empty-space routes use a shortest direct path.
- Stars and planets are avoided as intermediate cells.
- Route ties are deterministic.
- Routed distance can exceed direct distance.
- Exact-range routes are launchable.
- Over-range routes are retained and reported as `OutOfRange`.
- Enclosed routes report `NoRoute`.
- Travel turns derive from routed distance and speed.
- Salvos advance through ordered route cells and stop on arrival.
- Salvos do not occupy `SystemMap` cells.
- No final TL progression, target-track, interception, or damage rule is
  prematurely encoded.
- Concept v0.3a remains current.
- `StarCluster.Core` still has no Godot dependency.
