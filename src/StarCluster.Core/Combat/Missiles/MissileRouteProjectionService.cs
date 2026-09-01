using System;
using StarCluster.Core.Combat.Tracking;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;

namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Produces a projected next route without advancing the salvo, consuming
/// range, changing status, or replacing its last executed route.
/// </summary>
public static class MissileRouteProjectionService
{
    public static MissileRouteProjection Project(
        SystemMap map,
        GuidedMissileSalvo salvo,
        TacticalTrackRecord? targetTrack) =>
        Project(
            map,
            salvo,
            salvo.CurrentCoordinate,
            targetTrack?.Quality,
            targetTrack is { Quality: not TacticalTrackQuality.Lost }
                ? targetTrack.EstimatedCoordinate
                : null);

    /// <summary>
    /// Projects from an observer-safe missile origin and supplied target
    /// estimate. This overload prevents presentation code from substituting an
    /// authoritative hostile missile coordinate for an imperfect observer track.
    /// </summary>
    public static MissileRouteProjection Project(
        SystemMap map,
        GuidedMissileSalvo salvo,
        HexCoord projectedOriginCoordinate,
        TacticalTrackQuality? targetTrackQuality,
        HexCoord? guidanceCoordinate)
    {
        ArgumentNullException.ThrowIfNull(map);
        ArgumentNullException.ThrowIfNull(salvo);

        if (salvo.IsTerminal)
        {
            return new MissileRouteProjection(
                salvo.Id,
                MissileRouteProjectionStatus.Terminal,
                targetTrackQuality,
                guidanceCoordinate: null,
                routePlan: null);
        }

        if (salvo.RemainingRange == 0)
        {
            return new MissileRouteProjection(
                salvo.Id,
                MissileRouteProjectionStatus.RangeExhausted,
                targetTrackQuality,
                guidanceCoordinate: null,
                routePlan: null);
        }

        if (!guidanceCoordinate.HasValue)
        {
            return new MissileRouteProjection(
                salvo.Id,
                MissileRouteProjectionStatus.WaitingForTrack,
                targetTrackQuality,
                guidanceCoordinate: null,
                routePlan: null);
        }

        MissileRouteResult route = MissileRoutePlanner.FindRoute(
            map,
            projectedOriginCoordinate,
            guidanceCoordinate.Value,
            salvo.RemainingRange);

        return new MissileRouteProjection(
            salvo.Id,
            route.HasRoute
                ? MissileRouteProjectionStatus.Available
                : MissileRouteProjectionStatus.WaitingForRoute,
            targetTrackQuality,
            guidanceCoordinate,
            route);
    }
}
