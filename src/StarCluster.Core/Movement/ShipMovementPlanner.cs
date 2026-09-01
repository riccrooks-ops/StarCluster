using System;
using System.Collections.Generic;
using System.Linq;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;

namespace StarCluster.Core.Movement;

/// <summary>
/// Finds deterministic shortest ship routes and legal destinations on a
/// finite system map.
/// </summary>
public static class ShipMovementPlanner
{
    public static ShipMovementResult FindRoute(
        SystemMap map,
        HexCoord origin,
        HexCoord destination,
        int maximumDistance)
    {
        ArgumentNullException.ThrowIfNull(map);
        ValidateMaximumDistance(maximumDistance);
        ValidateCoordinate(map, origin, nameof(origin));
        ValidateCoordinate(map, destination, nameof(destination));

        if (origin == destination)
        {
            return new ShipMovementResult(
                ShipMovementStatus.Found,
                origin,
                destination,
                maximumDistance,
                new ShipMovementRoute(new[] { origin }));
        }

        if (IsBlocked(map, destination))
        {
            return new ShipMovementResult(
                ShipMovementStatus.Occupied,
                origin,
                destination,
                maximumDistance,
                route: null);
        }

        Dictionary<HexCoord, HexCoord> predecessors = new();
        HashSet<HexCoord> visited = new() { origin };
        Queue<HexCoord> frontier = new();
        frontier.Enqueue(origin);

        bool found = false;

        while (frontier.Count > 0 && !found)
        {
            HexCoord current = frontier.Dequeue();

            foreach (HexCoord neighbor in current.Neighbors())
            {
                if (!map.Geometry.Contains(neighbor) ||
                    visited.Contains(neighbor) ||
                    IsBlocked(map, neighbor))
                {
                    continue;
                }

                visited.Add(neighbor);
                predecessors.Add(neighbor, current);

                if (neighbor == destination)
                {
                    found = true;
                    break;
                }

                frontier.Enqueue(neighbor);
            }
        }

        if (!found)
        {
            return new ShipMovementResult(
                ShipMovementStatus.NoRoute,
                origin,
                destination,
                maximumDistance,
                route: null);
        }

        ShipMovementRoute route = ReconstructRoute(origin, destination, predecessors);
        ShipMovementStatus status = route.Distance <= maximumDistance
            ? ShipMovementStatus.Found
            : ShipMovementStatus.OutOfRange;

        return new ShipMovementResult(
            status,
            origin,
            destination,
            maximumDistance,
            route);
    }

    public static IReadOnlyList<HexCoord> FindLegalDestinations(
        SystemMap map,
        HexCoord origin,
        int maximumDistance)
    {
        ArgumentNullException.ThrowIfNull(map);
        ValidateMaximumDistance(maximumDistance);
        ValidateCoordinate(map, origin, nameof(origin));

        List<HexCoord> destinations = new() { origin };
        HashSet<HexCoord> visited = new() { origin };
        Queue<(HexCoord Coordinate, int Distance)> frontier = new();
        frontier.Enqueue((origin, 0));

        while (frontier.Count > 0)
        {
            (HexCoord current, int distance) = frontier.Dequeue();
            if (distance >= maximumDistance)
            {
                continue;
            }

            foreach (HexCoord neighbor in current.Neighbors())
            {
                if (!map.Geometry.Contains(neighbor) ||
                    visited.Contains(neighbor) ||
                    IsBlocked(map, neighbor))
                {
                    continue;
                }

                visited.Add(neighbor);
                destinations.Add(neighbor);
                frontier.Enqueue((neighbor, distance + 1));
            }
        }

        return Array.AsReadOnly(destinations.ToArray());
    }

    private static ShipMovementRoute ReconstructRoute(
        HexCoord origin,
        HexCoord destination,
        IReadOnlyDictionary<HexCoord, HexCoord> predecessors)
    {
        List<HexCoord> reversed = new() { destination };
        HexCoord current = destination;

        while (current != origin)
        {
            current = predecessors[current];
            reversed.Add(current);
        }

        reversed.Reverse();
        return new ShipMovementRoute(reversed);
    }

    private static bool IsBlocked(SystemMap map, HexCoord coordinate) =>
        map.GetCell(coordinate).Occupants.Any(IsMovementBlockingObject);

    private static bool IsMovementBlockingObject(MapObject mapObject) =>
        mapObject.Kind is
            MapObjectKind.Star or
            MapObjectKind.Planet or
            MapObjectKind.Ship or
            MapObjectKind.Station;

    private static void ValidateMaximumDistance(int maximumDistance)
    {
        if (maximumDistance < 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(maximumDistance),
                maximumDistance,
                "Maximum movement distance cannot be negative.");
        }
    }

    private static void ValidateCoordinate(
        SystemMap map,
        HexCoord coordinate,
        string parameterName)
    {
        if (!map.Geometry.Contains(coordinate))
        {
            throw new ArgumentOutOfRangeException(
                parameterName,
                coordinate,
                "The coordinate must exist on the system map.");
        }
    }
}
