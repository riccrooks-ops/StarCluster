using System;
using System.Linq;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;

namespace StarCluster.Core.Movement;

/// <summary>
/// Plans and commits one authoritative movement or hold command.
/// </summary>
public static class ShipMovementService
{
    public static ShipMovementExecutionResult Execute(
        SystemMap map,
        string shipId,
        HexCoord origin,
        HexCoord destination,
        SublightMovementProfile profile)
    {
        ArgumentNullException.ThrowIfNull(map);
        ArgumentException.ThrowIfNullOrWhiteSpace(shipId);
        ArgumentNullException.ThrowIfNull(profile);

        bool shipAtOrigin = map.GetCell(origin).Occupants.Any(
            item => item.Kind == MapObjectKind.Ship &&
                string.Equals(item.Id, shipId, StringComparison.Ordinal));

        if (!shipAtOrigin)
        {
            throw new InvalidOperationException(
                $"Ship '{shipId}' is not present at the supplied origin {origin}.");
        }

        ShipMovementResult plan = ShipMovementPlanner.FindRoute(
            map,
            origin,
            destination,
            profile.MaximumHexesPerTurn);

        if (!plan.CanMove)
        {
            return new ShipMovementExecutionResult(
                ShipMovementExecutionStatus.Rejected,
                plan,
                origin);
        }

        if (origin == destination)
        {
            return new ShipMovementExecutionResult(
                ShipMovementExecutionStatus.Held,
                plan,
                origin);
        }

        map.Move(shipId, destination);

        return new ShipMovementExecutionResult(
            ShipMovementExecutionStatus.Moved,
            plan,
            destination);
    }
}
