# Star Cluster - Checkpoint 06: Direct-Fire Line of Sight

## Purpose

Checkpoint 05 established stars, planets, ships, stations, anomalies,
wreckage, terrain, and occupancy on a finite tactical system map. This
checkpoint adds the first combat-facing spatial rule: whether direct fire has
an unobstructed line between two map cells.

It adds:

- `HexGeometry.SupercoverLine` for every hex touched by a center-to-center line
- An explicit conservative rule for exact hex-boundary lines
- `MapObject.BlocksDirectFire` as a centralized prototype trait
- `DirectFireLineOfSight` as an engine-independent evaluator
- `DirectFireLineOfSightResult` with tested cells and nearest blockers
- `LineOfSightBlocker` values pairing blocker coordinates and map objects
- Automated xUnit coverage for ordinary, boundary, clear, blocked, and invalid
  traces

No Godot dependency is introduced.

## Current direct-fire rules

The checkpoint deliberately implements a small, explicit policy:

1. Direct fire traces a center-to-center segment between two different map
   cells.
2. The origin and target cells are excluded from obstruction testing.
3. Stars and planets block direct fire when they occupy an intermediate cell.
4. Ships and stations do not currently screen other targets.
5. Anomalies and wreckage do not block direct fire.
6. Asteroid fields and nebulae do not yet block direct fire.
7. If a geometric line lies exactly along the boundary between two hexes,
   either adjacent star or planet blocks the shot.
8. A result reports blockers only at the nearest obstructed range step; more
   distant objects are irrelevant once the line is blocked.

This is a conservative boundary policy: the player cannot fire through a
zero-width crack created solely by hex rounding. It is symmetric in the
important gameplay sense that a blocker on either touched side obstructs the
line.

## Installation

Extract the checkpoint archive directly into:

`E:\dev\star-cluster`

Allow it to merge with the existing `src`, `tests`, `tools`, and `docs`
folders. Then run:

```powershell
Set-Location E:\dev\star-cluster
Set-ExecutionPolicy -Scope Process Bypass
.\tools\checkpoints\checkpoint-06\apply_checkpoint_06.ps1
```

## Expected result

The script should:

1. Confirm Checkpoints 02 through 05 are present.
2. Confirm that `global.json` selects .NET SDK 8.0.423.
3. Confirm all Checkpoint 06 source and test files exist.
4. Confirm synchronized project documentation is present.
5. Build the solution.
6. Run the complete test suite.

A successful run should end with:

```text
Checkpoint 06 completed successfully.
```

The expected total is **124 passing tests**.

## Files added or updated

```text
src\StarCluster.Core\Geometry\HexGeometry.cs                  (updated)
src\StarCluster.Core\Maps\MapObject.cs                       (updated)
src\StarCluster.Core\Combat\LineOfSightBlocker.cs
src\StarCluster.Core\Combat\DirectFireLineOfSightResult.cs
src\StarCluster.Core\Combat\DirectFireLineOfSight.cs
tests\StarCluster.Tests\Geometry\HexSupercoverLineTests.cs
tests\StarCluster.Tests\Maps\MapObjectDirectFireTests.cs
tests\StarCluster.Tests\Combat\DirectFireLineOfSightTests.cs
tools\checkpoints\checkpoint-06\apply_checkpoint_06.ps1
docs\checkpoints\Checkpoint_06_Direct_Fire_Line_Of_Sight.md
```

The package also carries the complete current `docs` folder in accordance with
the documentation-maintenance policy.

## Design notes

### Why a supercover line is separate from the ordinary line

`HexGeometry.Line` returns one deterministic shortest sequence of cells. That
is useful for displays and ordinary path visualization, but a mathematically
exact line can occasionally run along the boundary between two hexes. Choosing
only one side would let an obstruction disappear depending on an arbitrary
rounding tie.

`HexGeometry.SupercoverLine` evaluates the line with equal and opposite tiny
cube-coordinate nudges, then combines the results in outward traversal order.
Ordinary lines remain unchanged. Exact ties include both touched cells.

### Why stars and planets block, but ships and stations do not

The current combat abstraction treats stellar and planetary bodies as
large-scale occluders. Ships and stations occupy a tactical hex but are too
small to provide automatic screening at this scale. A later combat rule could
add intentional screening, formation protection, or station occlusion without
changing the geometry algorithm.

### Why terrain does not yet block

Asteroid fields and nebulae are retained as terrain state, but their combat
effects have not been defined. They may later impose accuracy, sensor, movement,
or damage modifiers. Deferring those effects prevents an accidental rule from
becoming entrenched before the sensor and weapon systems exist.

### Why only nearest blockers are returned

Once a nearer star or planet blocks direct fire, farther objects cannot affect
the outcome. Returning all blockers at the nearest range also handles an exact
boundary where two adjacent objects obstruct the same crossing. This is more
informative than selecting one arbitrarily while avoiding irrelevant objects
behind the first obstruction.

### What is intentionally deferred

This checkpoint does not yet define:

- Weapon range
- Attack accuracy or movement penalties
- Energy, projectile, or missile resolution
- Indirect missile attacks around an occluder
- Sensor detection and target-lock requirements
- Terrain-based visibility or accuracy modifiers
- Ship or station screening
- Pathfinding and movement costs
- Godot rendering of traced lines

The next checkpoint can introduce ship movement allowance and pathfinding, or
begin the minimal Godot presentation spike now that finite maps, contents, and
direct-fire geometry are testable.

## Review in Visual Studio

After the script succeeds:

1. Open the updated `HexGeometry.cs` and compare `Line` with `SupercoverLine`.
2. Open `DirectFireLineOfSight.cs` and follow the three stages: validate,
   trace intermediate cells, then find the nearest blockers.
3. Open `DirectFireLineOfSightTests.cs` and inspect the two-cell boundary case
   from `(0,0)` to `(2,-1)`.
4. In **Test > Test Explorer**, select **Run All Tests**.
5. Place a breakpoint inside `FindNearestBlockers` and run
   `BoundaryLineReturnsBothNearestBlockers`.

## Checkpoint acceptance criteria

- Solution builds with zero errors.
- Preferably, zero compiler warnings are reported.
- All 124 tests pass.
- Ordinary and boundary supercover traces are deterministic.
- A star or planet on either side of an exact boundary blocks direct fire.
- Origin and target cells do not block their own trace.
- Ships, stations, anomalies, wreckage, and current terrain do not block.
- Only nearest-range blockers are reported.
- `StarCluster.Core` still has no Godot dependency.
