using System;
using System.Collections.Generic;
using System.Linq;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;

namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Finds deterministic shortest guided-missile routes around stars and
/// planets on a finite tactical system map.
/// </summary>
public static class MissileRoutePlanner
{
    /// <summary>
    /// Finds the shortest legal route from <paramref name="origin"/> to
    /// <paramref name="target"/> and compares its routed distance with
    /// <paramref name="maximumRange"/>.
    /// </summary>
    /// <remarks>
    /// Stars and planets are impassable intermediate cells. The origin and
    /// target cells remain legal endpoints even when they contain a blocking
    /// body, allowing later systems to support launches from or attacks on
    /// such locations. Neighbor expansion follows the stable axial direction
    /// order, making equal-length route ties deterministic.
    /// </remarks>
    public static MissileRouteResult FindRoute(
        SystemMap map,
        HexCoord origin,
        HexCoord target,
        int maximumRange)
    {
        ArgumentNullException.ThrowIfNull(map);

        if (maximumRange < 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(maximumRange),
                maximumRange,
                "Maximum missile range cannot be negative.");
        }

        // GetCell performs the finite-map validation and provides a consistent
        // exception for coordinates outside the tactical map.
        map.GetCell(origin);
        map.GetCell(target);

        if (origin == target)
        {
            var zeroDistanceRoute = new MissileRoute(new[] { origin });
            return CreateResult(
                origin,
                target,
                maximumRange,
                zeroDistanceRoute);
        }

        var frontier = new Queue<HexCoord>();
        var previous = new Dictionary<HexCoord, HexCoord>();
        var visited = new HashSet<HexCoord> { origin };

        frontier.Enqueue(origin);

        while (frontier.Count > 0)
        {
            HexCoord current = frontier.Dequeue();

            foreach (HexCoord neighbor in map.Geometry.NeighborsOf(current))
            {
                if (!visited.Add(neighbor))
                {
                    continue;
                }

                if (neighbor != target && IsMissileBlocked(map, neighbor))
                {
                    continue;
                }

                previous.Add(neighbor, current);

                if (neighbor == target)
                {
                    MissileRoute route = ReconstructRoute(
                        origin,
                        target,
                        previous);

                    return CreateResult(
                        origin,
                        target,
                        maximumRange,
                        route);
                }

                frontier.Enqueue(neighbor);
            }
        }

        return new MissileRouteResult(
            origin,
            target,
            maximumRange,
            MissileRouteStatus.NoRoute,
            route: null);
    }

    private static bool IsMissileBlocked(SystemMap map, HexCoord coordinate) =>
        map.GetCell(coordinate)
            .Occupants
            .Any(item => item.BlocksMissileTravel);

    private static MissileRoute ReconstructRoute(
        HexCoord origin,
        HexCoord target,
        IReadOnlyDictionary<HexCoord, HexCoord> previous)
    {
        var reversed = new List<HexCoord> { target };
        HexCoord current = target;

        while (current != origin)
        {
            current = previous[current];
            reversed.Add(current);
        }

        reversed.Reverse();
        return new MissileRoute(reversed);
    }

    private static MissileRouteResult CreateResult(
        HexCoord origin,
        HexCoord target,
        int maximumRange,
        MissileRoute route)
    {
        MissileRouteStatus status = route.Distance <= maximumRange
            ? MissileRouteStatus.Found
            : MissileRouteStatus.OutOfRange;

        return new MissileRouteResult(
            origin,
            target,
            maximumRange,
            status,
            route);
    }
}
