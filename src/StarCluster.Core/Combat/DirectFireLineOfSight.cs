using System;
using System.Collections.Generic;
using System.Linq;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;

namespace StarCluster.Core.Combat;

/// <summary>
/// Evaluates direct-fire line of sight on a tactical system map.
/// </summary>
public static class DirectFireLineOfSight
{
    /// <summary>
    /// Traces the center-to-center line between two existing map cells.
    /// </summary>
    /// <remarks>
    /// A star or planet crossed through an ordinary intermediate cell blocks
    /// direct fire. At an exact boundary step, one blocked side produces a
    /// grazing result while blockers on both sides fully obstruct the shot.
    /// Separate one-sided grazings are accumulated for later combat penalties.
    /// The origin and target cells never obstruct their own trace.
    /// </remarks>
    /// <exception cref="ArgumentNullException">
    /// Thrown when <paramref name="map"/> is null.
    /// </exception>
    /// <exception cref="ArgumentException">
    /// Thrown when origin and target are the same coordinate.
    /// </exception>
    /// <exception cref="ArgumentOutOfRangeException">
    /// Thrown when either coordinate is outside the map.
    /// </exception>
    public static DirectFireLineOfSightResult Evaluate(
        SystemMap map,
        HexCoord origin,
        HexCoord target)
    {
        ArgumentNullException.ThrowIfNull(map);

        // GetCell performs finite-map validation while keeping geometry and
        // content ownership inside SystemMap.
        map.GetCell(origin);
        map.GetCell(target);

        if (origin == target)
        {
            throw new ArgumentException(
                "Direct-fire origin and target must be different cells.",
                nameof(target));
        }

        HexLineStep[] intermediateSteps = HexGeometry
            .SupercoverSteps(origin, target)
            .Where(step =>
                step.DistanceFromStart > 0 &&
                step.DistanceFromStart < origin.DistanceTo(target))
            .ToArray();

        HexCoord[] testedCells = intermediateSteps
            .SelectMany(step => step.Cells)
            .Distinct()
            .ToArray();

        var grazings = new List<LineOfSightGrazing>();
        LineOfSightBlockage? blockage = null;

        foreach (HexLineStep step in intermediateSteps)
        {
            CellBlockers[] sides = step.Cells
                .Select(coordinate => new CellBlockers(
                    coordinate,
                    FindBlockers(map, coordinate)))
                .ToArray();

            if (!step.IsBoundary)
            {
                IReadOnlyList<LineOfSightBlocker> blockers = sides[0].Blockers;

                if (blockers.Count > 0)
                {
                    blockage = new LineOfSightBlockage(
                        step.DistanceFromStart,
                        blockers);
                    break;
                }

                continue;
            }

            CellBlockers[] blockedSides = sides
                .Where(side => side.Blockers.Count > 0)
                .ToArray();

            if (blockedSides.Length == 2)
            {
                LineOfSightBlocker[] blockers = blockedSides
                    .SelectMany(side => side.Blockers)
                    .OrderBy(blocker => blocker.Coordinate.Q)
                    .ThenBy(blocker => blocker.Coordinate.R)
                    .ThenBy(blocker => blocker.MapObject.Id, StringComparer.Ordinal)
                    .ToArray();

                blockage = new LineOfSightBlockage(
                    step.DistanceFromStart,
                    Array.AsReadOnly(blockers));
                break;
            }

            if (blockedSides.Length == 1)
            {
                CellBlockers blockedSide = blockedSides[0];
                CellBlockers openSide = sides.Single(
                    side => side.Blockers.Count == 0);

                grazings.Add(new LineOfSightGrazing(
                    step.DistanceFromStart,
                    blockedSide.Coordinate,
                    openSide.Coordinate,
                    blockedSide.Blockers));
            }
        }

        return new DirectFireLineOfSightResult(
            origin,
            target,
            Array.AsReadOnly(testedCells),
            grazings.AsReadOnly(),
            blockage);
    }

    private static IReadOnlyList<LineOfSightBlocker> FindBlockers(
        SystemMap map,
        HexCoord coordinate)
    {
        LineOfSightBlocker[] blockers = map
            .GetCell(coordinate)
            .Occupants
            .Where(mapObject => mapObject.BlocksDirectFire)
            .Select(mapObject => new LineOfSightBlocker(
                coordinate,
                mapObject))
            .OrderBy(blocker => blocker.MapObject.Id, StringComparer.Ordinal)
            .ToArray();

        return Array.AsReadOnly(blockers);
    }

    private sealed record CellBlockers(
        HexCoord Coordinate,
        IReadOnlyList<LineOfSightBlocker> Blockers);
}
