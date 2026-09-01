# Star Cluster - Checkpoint 02: Hex Geometry Foundation

## Purpose

This checkpoint introduces the first real Star Cluster source code while keeping all game rules independent of Godot.

It adds:

- Immutable axial hex coordinates (`Q`, `R`, and derived `S`)
- The six neighboring directions
- Neighbor lookup and enumeration
- Hex distance calculations
- Coordinate addition and subtraction
- Automated xUnit tests

## Installation

1. Close any source files currently open in Visual Studio. Visual Studio itself may remain open.
2. Extract `StarCluster_Checkpoint_02_Hex_Geometry.zip` directly into:

   `E:\dev\star-cluster`

   The archive already contains the correct `src`, `tests`, `tools`, and `docs` folders.
3. Open PowerShell and run:

```powershell
Set-Location E:\dev\star-cluster
Set-ExecutionPolicy -Scope Process Bypass
.\tools\checkpoints\checkpoint-02\apply_checkpoint_02.ps1
```

The process-scoped execution-policy change applies only to that PowerShell window.

## Expected result

The script should:

1. Confirm the repository structure.
2. Confirm that `global.json` selects .NET SDK 8.0.423.
3. Remove the two generated template files:
   - `src\StarCluster.Core\Class1.cs`
   - `tests\StarCluster.Tests\UnitTest1.cs`
4. Build both projects.
5. Run the new tests.

A successful run should end with:

```text
Checkpoint 02 completed successfully.
```

The exact test duration may differ, but the expected test total is **15**.

## Files added

```text
src\StarCluster.Core\Geometry\HexCoord.cs
tests\StarCluster.Tests\Geometry\HexCoordTests.cs
tools\checkpoints\checkpoint-02\apply_checkpoint_02.ps1
docs\checkpoints\Checkpoint_02_Hex_Geometry.md
```

## C# concepts introduced

### `readonly record struct`

`HexCoord` is a small immutable value. Two coordinates with the same `Q` and `R` values compare as equal automatically.

This is conceptually similar to a compact Delphi record whose fields cannot be modified after construction and which has value-based equality.

### Axial coordinates

A hex is stored with two values:

```text
Q, R
```

A third cube-coordinate component is derived:

```text
S = -Q - R
```

The invariant is therefore always:

```text
Q + R + S = 0
```

This representation makes neighbors, range, distance, and later line-of-sight calculations much easier than storing screen pixel positions.

### Expression-bodied members

This C# form:

```csharp
public int S => -Q - R;
```

is a concise property whose value is calculated when read. It is roughly equivalent to a Delphi read-only property implemented by a getter.

### Iterators and `yield return`

`Neighbors()` produces the six adjacent cells one at a time. The caller can enumerate them without the method needing to create a separate mutable list.

### Operator overloads

The `+` and `-` operators allow coordinate translation:

```csharp
HexCoord destination = start + offset;
```

The operators are mathematical conveniences only; they do not move a ship or change game state.

## Review in Visual Studio

After the script succeeds:

1. Return to Visual Studio.
2. Allow Solution Explorer to refresh, or right-click the solution and select **Reload Project** only if necessary.
3. Open `HexCoord.cs` and `HexCoordTests.cs`.
4. Open **Test > Test Explorer**.
5. Select **Run All Tests** to confirm the same result inside Visual Studio.

## Checkpoint acceptance criteria

- Solution builds with no errors.
- Preferably, no compiler warnings are reported.
- All 15 tests pass.
- `StarCluster.Core` still has no Godot dependency.
- Hex coordinates are represented logically, not by screen pixels.
