# Star Cluster - Checkpoint 05: System Map Contents

## Purpose

Checkpoint 04 established the finite coordinates that exist on a map. This
checkpoint layers the first game-domain state over that geometry while keeping
all rules independent of Godot.

It adds:

- `MapTerrain` for open space, asteroid fields, and nebulae
- `MapObjectKind` for stars, planets, ships, stations, anomalies, and wreckage
- Immutable `MapObject` values with stable IDs
- `MapCell` terrain and read-only occupant views
- `SystemMap` placement, movement, removal, and lookup operations
- The single-star-at-origin system-map invariant
- Exclusive occupancy for solid objects
- Coexistence of diffuse or informational non-solid occupants
- Automated xUnit coverage for all new behavior

No Godot dependency is introduced.

## Current tactical-map invariants

The checkpoint deliberately implements a small set of clear rules:

1. A system map may contain zero or one star.
2. When present, the star must occupy axial origin `(0,0)`.
3. Stars, planets, ships, and stations are currently treated as solid objects.
4. A cell can contain no more than one solid object.
5. Anomalies and wreckage are currently non-solid and may share a cell.
6. Only ships can move through the map-state operation.
7. Terrain and occupants are separate concepts.

The solid and mobile traits are prototype rules centralized in `MapObject` and
can be revised later without altering the underlying hex geometry.

## Installation

Extract the checkpoint archive directly into:

`E:\dev\star-cluster`

Allow it to merge with the existing `src`, `tests`, `tools`, and `docs`
folders. Then run:

```powershell
Set-Location E:\dev\star-cluster
Set-ExecutionPolicy -Scope Process Bypass
.\tools\checkpoints\checkpoint-05\apply_checkpoint_05.ps1
```

## Expected result

The script should:

1. Confirm Checkpoints 02 through 04 are present.
2. Confirm that `global.json` selects .NET SDK 8.0.423.
3. Confirm all Checkpoint 05 source and test files exist.
4. Confirm synchronized project documentation is present.
5. Build the solution.
6. Run the complete test suite.

A successful run should end with:

```text
Checkpoint 05 completed successfully.
```

The expected total is **86 passing tests**.

## Files added

```text
src\StarCluster.Core\Maps\MapTerrain.cs
src\StarCluster.Core\Maps\MapObjectKind.cs
src\StarCluster.Core\Maps\MapObject.cs
src\StarCluster.Core\Maps\MapCell.cs
src\StarCluster.Core\Maps\SystemMap.cs
tests\StarCluster.Tests\Maps\SystemMapTests.cs
tools\checkpoints\checkpoint-05\apply_checkpoint_05.ps1
docs\checkpoints\Checkpoint_05_System_Map_Contents.md
```

The package also carries the complete current `docs` folder in accordance with
the documentation-maintenance policy.

## Design notes

### Geometry and contents remain separate

`HexMap` still answers only whether a coordinate exists. `SystemMap` owns the
mutable terrain and occupant state for those coordinates. This means hex
mathematics can remain stable even as later gameplay adds factions, combat,
sensors, cargo, research, and visual effects.

### Why objects use stable string IDs

The map indexes objects by a stable ID rather than by display name. Names are
not guaranteed to be unique and may change. The initial string form also keeps
tests and save-data inspection readable. A dedicated strongly typed ID can be
introduced later if it proves useful.

### Why cells expose a read-only occupant list

Callers can inspect cell state but cannot modify its occupants directly. All
placement, movement, and removal must pass through `SystemMap`, which preserves
the map invariants and object-location index.

### Why anomalies and wreckage are non-solid for now

These categories represent diffuse phenomena or points of interest in the
current abstraction. Allowing them to coexist with a ship or planet supports
scanning, salvage, and incident-site gameplay without needing multiple spatial
layers. Playtesting can later refine individual object traits.

### What is intentionally deferred

This checkpoint does not yet define:

- Direct-fire line-of-sight blocking
- Movement range or pathfinding
- Ownership or factions
- Ship combat statistics
- Orbital motion
- Planetary or stellar generation
- Rendering and input

The next checkpoint can define direct-fire obstruction by stars and planets,
including an explicit policy for geometric lines that pass exactly between two
hexes.

## Review in Visual Studio

After the script succeeds:

1. Open the five new files under `StarCluster.Core\Maps`.
2. Open `SystemMapTests.cs` under the test project.
3. In **Test > Test Explorer**, select **Run All Tests**.
4. Confirm the complete suite passes.
5. Place a breakpoint inside `SystemMap.Place` and run one placement test to
   observe the cell and object-location indexes being updated together.

## Checkpoint acceptance criteria

- Solution builds with zero errors.
- Preferably, zero compiler warnings are reported.
- All 86 tests pass.
- A starless system is allowed.
- A present star is unique and fixed at `(0,0)`.
- Two solid objects cannot occupy one cell.
- Non-solid occupants may coexist in a cell.
- Only ships can be moved by `SystemMap.Move`.
- Object removal clears both the cell and location index.
- `StarCluster.Core` still has no Godot dependency.
