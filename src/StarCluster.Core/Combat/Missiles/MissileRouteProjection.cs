using StarCluster.Core.Combat.Tracking;
using StarCluster.Core.Geometry;

namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Non-mutating preview of the route a salvo would attempt during its next
/// guidance phase using the supplied observer track.
/// </summary>
public sealed class MissileRouteProjection
{
    internal MissileRouteProjection(
        string salvoId,
        MissileRouteProjectionStatus status,
        TacticalTrackQuality? trackQuality,
        HexCoord? guidanceCoordinate,
        MissileRouteResult? routePlan)
    {
        SalvoId = salvoId;
        Status = status;
        TrackQuality = trackQuality;
        GuidanceCoordinate = guidanceCoordinate;
        RoutePlan = routePlan;
    }

    public string SalvoId { get; }

    public MissileRouteProjectionStatus Status { get; }

    public TacticalTrackQuality? TrackQuality { get; }

    public HexCoord? GuidanceCoordinate { get; }

    public MissileRouteResult? RoutePlan { get; }

    public bool HasRoute => RoutePlan?.HasRoute == true;
}
