# Star Cluster - Checkpoint 03: Hex Regions and Lines

## Purpose

This checkpoint expands the engine-independent hex geometry foundation with three operations needed by the eventual tactical display and rules engine:

- Filled movement and sensor ranges
- Exact-radius rings
- Deterministic center-to-center hex lines

The new code still has no dependency on Godot.

## Installation

1. Extract `StarCluster_Checkpoint_03_Hex_Regions_And_Lines.zip` directly into:

   `E:\dev\star-cluster`

   Allow the archive to merge with the existing `src`, `tests`, `tools`, and `docs` directories.

2. Open PowerShell and run:

```powershell
Set-Location E:\dev\star-cluster
Set-ExecutionPolicy -Scope Process Bypass
.\tools\checkpoints\checkpoint-03\apply_checkpoint_03.ps1
```

The process-scoped execution-policy setting applies only to that PowerShell window.

## Expected result

The script should:

1. Verify the repository and Checkpoint 02 files.
2. Confirm that `global.json` selects .NET SDK 8.0.423.
3. Verify the new source and test files.
4. Build the solution.
5. Run all tests.

A successful run should end with:

```text
Checkpoint 03 completed successfully.
```

The expected total is **43 passing tests**: the original 15 plus 28 new test cases.

## Files added

```text
src\StarCluster.Core\Geometry\HexGeometry.cs
tests\StarCluster.Tests\Geometry\HexGeometryTests.cs
tools\checkpoints\checkpoint-03\apply_checkpoint_03.ps1
docs\checkpoints\Checkpoint_03_Hex_Regions_And_Lines.md
```

## New operations

### `HexGeometry.CellsWithin(center, radius)`

Returns the center and every cell whose hex distance from it is no greater than the radius.

The number of cells in a filled radius is:

```text
1 + 3r(r + 1)
```

Examples:

```text
radius 0:  1 cell
radius 1:  7 cells
radius 2: 19 cells
radius 3: 37 cells
radius 5: 91 cells
```

Likely uses in Star Cluster include:

- Legal movement destinations
- Sensor range overlays
- Weapon-range overlays
- Area effects
- Search and survey radii

### `HexGeometry.Ring(center, radius)`

Returns only cells at exactly the requested distance.

A positive-radius ring contains:

```text
6 x radius
```

Likely uses include:

- Procedural placement at a controlled distance
- Reinforcement entry regions
- Search perimeters
- Visual range boundaries

### `HexGeometry.Line(start, end)`

Returns a shortest center-to-center line that includes both endpoints.

The algorithm:

1. Treats each axial coordinate as a three-component cube coordinate.
2. Interpolates evenly from the starting cube point to the ending cube point.
3. Rounds each sample back to the nearest valid hex.
4. Restores the invariant `Q + R + S = 0` after rounding.

Likely uses include:

- Drawing intended movement paths
- Showing targeting lines
- Preliminary line-of-sight checks
- Beam and projectile animation paths

A geometric line can rarely pass exactly along the boundary between two hexes. This checkpoint uses a tiny fixed nudge to choose one deterministic side. A later line-of-sight checkpoint will define the actual gameplay policy for those boundary cases rather than silently treating this preliminary line as final combat doctrine.

## C# concepts introduced

### Static classes

`HexGeometry` is declared as a `static class`. It has no changing object state and is never instantiated. It groups related algorithms in a clear location.

### Read-only collections

The public methods return `IReadOnlyList<HexCoord>`. Callers can enumerate and index the results, but they cannot use the returned interface to add, remove, or replace cells.

### Capacity estimates

The internal lists are created with their expected final size. This is a modest efficiency improvement and also documents the known shape sizes.

### Linear interpolation

`Lerp` means linear interpolation. An amount of zero returns the starting value, one returns the ending value, and values in between return evenly spaced intermediate values.

### Index-from-end operator

The tests use:

```csharp
line[^1]
```

This means the final element of the collection. `^2` would mean the second-to-last element.

## Review in Visual Studio

After the script succeeds:

1. Open `HexGeometry.cs`.
2. Review `CellsWithin`, `Ring`, and `Line` separately.
3. Open `HexGeometryTests.cs` and compare each test group with its corresponding algorithm.
4. Open **Test > Test Explorer** and run all tests.

## Checkpoint acceptance criteria

- Solution builds with no errors.
- Preferably, no compiler warnings are reported.
- All 43 tests pass.
- `StarCluster.Core` still has no Godot dependency.
- Filled ranges contain the correct number of unique cells.
- Rings contain only cells at the requested distance.
- Lines include both endpoints and move through adjacent hexes only.
