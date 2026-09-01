using System;
using System.Collections.Generic;
using StarCluster.Core.Geometry;

namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Reports the shortest legal missile route, its routed distance, and whether
/// the route fits within the requested maximum range.
/// </summary>
public sealed class MissileRouteResult
{
    private static readonly IReadOnlyList<HexCoord> EmptyPath =
        Array.AsReadOnly(Array.Empty<HexCoord>());

    internal MissileRouteResult(
        HexCoord origin,
        HexCoord target,
        int maximumRange,
        MissileRouteStatus status,
        MissileRoute? route)
    {
        Origin = origin;
        Target = target;
        MaximumRange = maximumRange;
        Status = status;
        Route = route;
    }

    public HexCoord Origin { get; }

    public HexCoord Target { get; }

    /// <summary>
    /// Gets the unobstructed axial distance between origin and target.
    /// </summary>
    public int DirectDistance => Origin.DistanceTo(Target);

    /// <summary>
    /// Gets the maximum routed distance requested by the caller.
    /// </summary>
    public int MaximumRange { get; }

    public MissileRouteStatus Status { get; }

    /// <summary>
    /// Gets the shortest legal route when one exists. Out-of-range results
    /// retain the route for diagnostics and user-interface previews.
    /// </summary>
    public MissileRoute? Route { get; }

    public bool HasRoute => Route is not null;

    public bool CanLaunch => Status == MissileRouteStatus.Found;

    public int? RoutedDistance => Route?.Distance;

    public IReadOnlyList<HexCoord> Path => Route?.Cells ?? EmptyPath;
}
