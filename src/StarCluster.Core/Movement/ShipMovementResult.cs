using System.Collections.Generic;
using StarCluster.Core.Geometry;

namespace StarCluster.Core.Movement;

/// <summary>
/// Provides a route-planning result suitable for rules, tests, and UI previews.
/// </summary>
public sealed class ShipMovementResult
{
    internal ShipMovementResult(
        ShipMovementStatus status,
        HexCoord origin,
        HexCoord destination,
        int maximumDistance,
        ShipMovementRoute? route)
    {
        Status = status;
        Origin = origin;
        Destination = destination;
        MaximumDistance = maximumDistance;
        Route = route;
    }

    public ShipMovementStatus Status { get; }

    public HexCoord Origin { get; }

    public HexCoord Destination { get; }

    public int DirectDistance => Origin.DistanceTo(Destination);

    public int MaximumDistance { get; }

    public ShipMovementRoute? Route { get; }

    public IReadOnlyList<HexCoord>? Path => Route?.Path;

    public int? RoutedDistance => Route?.Distance;

    public bool HasRoute => Route is not null;

    public bool CanMove => Status == ShipMovementStatus.Found;

    public bool IsHold => CanMove && Origin == Destination;
}
