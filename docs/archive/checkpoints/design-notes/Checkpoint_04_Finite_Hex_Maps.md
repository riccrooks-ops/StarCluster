# Star Cluster - Checkpoint 04: Finite Hex Maps

## Purpose

Checkpoint 02 defined individual axial coordinates. Checkpoint 03 added filled
regions, rings, and straight hex lines. This checkpoint turns that unbounded
geometry into a finite logical map.

It adds:

- `HexMap`, an origin-centered finite hexagonal map
- Configurable map radius rather than a hard-coded board size
- Diameter and cell-count reporting
- Fast membership tests for coordinates
- Boundary detection
- Neighbor filtering at map edges
- Centralized prototype defaults for the system and cluster maps
- Automated xUnit coverage for the new behavior

No Godot dependency is introduced.

## Current design defaults

The values are kept in `MapDefaults` so they remain easy to revise:

```text
System map:  radius 5, diameter 11, 91 cells
Cluster map: radius 8, diameter 17, 217 cells
```

These values are current design decisions, not restrictions inside `HexMap`.
For example, this remains valid:

```csharp
HexMap experimentalMap = HexMap.CreateHexagon(radius: 12);
```

## Installation

Extract the checkpoint archive directly into:

`E:\dev\star-cluster`

Allow it to merge with the existing `src`, `tests`, `tools`, and `docs`
folders. Then run:

```powershell
Set-Location E:\dev\star-cluster
Set-ExecutionPolicy -Scope Process Bypass
.\tools\checkpoints\checkpoint-04\apply_checkpoint_04.ps1
```

## Expected result

The script should:

1. Confirm Checkpoints 02 and 03 are present.
2. Confirm that `global.json` selects .NET SDK 8.0.423.
3. Confirm the new map source and test files exist.
4. Confirm the v0.3 concept document and checkpoint documentation are present.
5. Build the solution.
6. Run the complete test suite.

A successful run should end with:

```text
Checkpoint 04 completed successfully.
```

The expected total is **56 passing tests**.

## Files added

```text
src\StarCluster.Core\Maps\HexMap.cs
src\StarCluster.Core\Maps\MapDefaults.cs
tests\StarCluster.Tests\Maps\HexMapTests.cs
tools\checkpoints\checkpoint-04\apply_checkpoint_04.ps1
docs\checkpoints\Checkpoint_04_Finite_Hex_Maps.md
```

The package also carries the complete current `docs` folder in accordance with
the documentation-maintenance policy.

## Design notes

### Why the map is centered at `(0,0)`

The logical board is centered on the axial origin. On a system map, a single
star can later be placed at `(0,0)` when one is present. On the strategic map,
the home system may be placed a configurable number of hexes away from the
origin without moving the board itself.

### Why `HexMap` does not contain stars or ships yet

This checkpoint establishes only which coordinates exist. Occupants, terrain,
sector knowledge, and line-of-sight obstruction will be layered on top in later
checkpoints. Keeping those concerns separate makes the foundation easier to
test and avoids premature assumptions.

### `HashSet<HexCoord>` and the read-only cell list

`HexMap` maintains two internal views:

- A `HashSet<HexCoord>` for fast `Contains` checks
- A read-only list for safe, deterministic enumeration

The caller can inspect the map but cannot add or remove cells.

### `sealed class`

`HexMap` is declared `sealed` because it represents one concrete invariant:
an origin-centered finite hexagon. We will add behavior by composing map state
with it rather than inheriting specialized subclasses.

## Review in Visual Studio

After the script succeeds:

1. Open `Maps\HexMap.cs` and `Maps\MapDefaults.cs`.
2. Open `Maps\HexMapTests.cs` under the test project.
3. In **Test > Test Explorer**, select **Run All Tests**.
4. Confirm the complete suite passes.

## Checkpoint acceptance criteria

- Solution builds with zero errors.
- Preferably, zero compiler warnings are reported.
- All 56 tests pass.
- A radius-5 map contains 91 cells and has diameter 11.
- A radius-8 map contains 217 cells and has diameter 17.
- Coordinates outside the finite board are rejected by map queries that require
  an existing cell.
- `StarCluster.Core` still has no Godot dependency.
