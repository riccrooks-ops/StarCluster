# Star Cluster - Checkpoint 07: Grazing Line of Sight

## Purpose

Checkpoint 06 established deterministic supercover traces and a conservative
binary direct-fire rule. This checkpoint preserves the geometry but refines the
combat-facing interpretation into three outcomes:

- `Clear`
- `Grazing`
- `Blocked`

It also preserves every separate one-sided boundary grazing so a later attack
resolver can apply a cumulative, potentially capped targeting penalty. The
geometry layer deliberately does not assign the numeric penalty.

No Godot dependency is introduced.

## Revised direct-fire rules

1. The origin and target must be different existing system-map cells.
2. The origin and target cells are excluded from obstruction testing.
3. A star or planet crossed through an ordinary intermediate cell blocks
   direct fire.
4. At an exact boundary step:
   - no blocking body on either side is `Clear`;
   - a blocking body on one side and open space on the other is one `Grazing`;
   - blocking bodies on both sides are `Blocked`.
5. Multiple one-sided grazings remain separate and are reported in traversal
   order.
6. A later complete blockage ends evaluation; earlier grazings remain available
   for diagnostics, but the overall result is `Blocked`.
7. Ships, stations, anomalies, wreckage, asteroid fields, and nebulae retain
   their Checkpoint 06 prototype behavior and do not block direct fire.
8. Range, target track, movement, weapon readiness, and attack accuracy remain
   separate combat concerns.

## New geometry grouping

`HexGeometry.SupercoverSteps` returns one `HexLineStep` for each range step.
An ordinary step contains one coordinate. An exact boundary step contains the
two adjacent coordinates touched at that distance.

This grouping is necessary because a flattened supercover line cannot tell the
combat layer whether two cells were touched at the same boundary step or at two
successive ordinary steps.

## Result model

`DirectFireLineOfSightResult` now exposes:

- `Quality`
- `Grazings`
- `GrazingCount`
- `Blockage`
- `Blockers` as a compatibility view of the complete blockage
- `IsClear`, `IsGrazing`, `IsBlocked`, and `HasLineOfSight`

Each `LineOfSightGrazing` records:

- range step
- blocked-side coordinate
- open-side coordinate
- responsible star or planet

Each `LineOfSightBlockage` records the first completely obstructed range step
and its blockers.

## Missile design recorded, not yet implemented

Concept v0.3a records missiles and torpedoes as guided time-of-flight weapons.
They may route around stars and planets when an adequate target track exists.
Routed path length, rather than only straight-line distance, is expected to
govern range expenditure and travel time. Longer routes also create more
interception opportunities.

Missile Weapons TL may improve selected traits such as:

- maximum range
- flight speed
- guidance quality
- path efficiency or maneuverability
- payload
- resistance to interception

The exact progression remains open for playtesting. This checkpoint does not
yet create in-flight missiles or pathfinding.

## Installation

Extract the checkpoint archive directly into:

`E:\dev\star-cluster`

Allow it to merge with the existing `src`, `tests`, `tools`, and `docs`
folders. Then run:

```powershell
Set-Location E:\dev\star-cluster
Set-ExecutionPolicy -Scope Process Bypass
.\tools\checkpoints\checkpoint-07\apply_checkpoint_07.ps1
```

The script archives Concept v0.3, removes the superseded active copy, verifies
Concept v0.3a, builds the solution, and runs all tests.

## Expected result

A successful run should end with:

```text
Checkpoint 07 completed successfully.
```

The expected total is **141 passing tests**.

## Files added or updated

```text
src\StarCluster.Core\Geometry\HexGeometry.cs                    (updated)
src\StarCluster.Core\Geometry\HexLineStep.cs
src\StarCluster.Core\Combat\LineOfSightQuality.cs
src\StarCluster.Core\Combat\LineOfSightGrazing.cs
src\StarCluster.Core\Combat\LineOfSightBlockage.cs
src\StarCluster.Core\Combat\DirectFireLineOfSightResult.cs      (updated)
src\StarCluster.Core\Combat\DirectFireLineOfSight.cs            (updated)
tests\StarCluster.Tests\Geometry\HexSupercoverStepTests.cs
tests\StarCluster.Tests\Combat\DirectFireLineOfSightTests.cs    (updated)
tools\checkpoints\checkpoint-07\apply_checkpoint_07.ps1
docs\Star_Cluster_Game_Concept_v0.3a.docx
docs\archive\Star_Cluster_Game_Concept_v0.3.docx
docs\checkpoints\Checkpoint_07_Grazing_Line_Of_Sight.md
```

The package carries the complete synchronized `docs` folder.

## Design notes

### Why grazing events are counted rather than scored here

Whether one grazing should impose a fixed penalty, a percentage penalty, a
diminishing penalty, or a capped cumulative penalty is a balance decision. The
spatial layer should report what the line touched, not decide weapon accuracy.
This keeps geometry deterministic and reusable for every direct-fire weapon.

### Why a two-sided boundary is blocked

A trace lying exactly between two blocking celestial bodies has no open side.
Treating that geometry as blocked avoids a zero-width firing corridor while
still allowing one-sided boundary shots at a penalty.

### Why a blockage remains decisive after earlier grazings

A later ordinary crossing or two-sided boundary pinch makes direct fire
impossible regardless of earlier partial obstruction. The prior grazings are
retained for inspection and tests, but the result quality is `Blocked`.

### Why missile routing remains separate

Direct-fire line of sight and missile navigation answer different questions.
Energy and projectile weapons need a geometric firing line. A missile instead
needs a legal path, sufficient routed range, travel time, guidance, and a valid
target track. Keeping these services separate avoids encoding missile behavior
as exceptions inside direct-fire logic.

## Review in Visual Studio

After the script succeeds:

1. Open `HexLineStep.cs` and `HexGeometry.SupercoverSteps`.
2. Compare the flattened `SupercoverLine` with the step-grouped representation.
3. Open `DirectFireLineOfSight.cs` and follow ordinary, one-sided boundary, and
   two-sided boundary handling.
4. Inspect tests for multiple grazings and direction reversal.
5. In **Test > Test Explorer**, select **Run All Tests**.

## Checkpoint acceptance criteria

- Solution builds with zero errors.
- Preferably, zero compiler warnings are reported.
- All 141 tests pass.
- Ordinary interior crossings by a star or planet are blocked.
- One-sided exact-boundary contacts are grazing rather than blocked.
- Two-sided exact-boundary contacts are blocked.
- Multiple grazings are preserved separately and in traversal order.
- Reversing a trace preserves the overall quality and grazing count.
- No numeric grazing penalty is assigned in the geometry layer.
- Concept v0.3a is current and v0.3 is preserved under `docs\archive`.
- `StarCluster.Core` still has no Godot dependency.
