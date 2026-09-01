using System;
using System.Collections.Generic;
using StarCluster.Core.Combat;
using StarCluster.Core.Combat.Missiles;
using StarCluster.Core.Geometry;

namespace StarCluster.Core.Combat.Tracking;

/// <summary>
/// Observer-safe presentation state for one missile salvo. Hostile coordinates
/// are track-derived; authoritative hostile travel history and route plans are
/// never exposed through this object.
/// </summary>
public sealed class TacticalMissileContact
{
    internal TacticalMissileContact(
        string salvoId,
        TacticalSide ownerSide,
        string launcherId,
        string targetId,
        HexCoord coordinate,
        TacticalTrackQuality trackQuality,
        int uncertaintyRadiusHexes,
        GuidedMissileStatus status,
        int distanceTraveled,
        int totalFuelSpent,
        int maximumRange,
        string? interceptedByDefenseSystemId,
        IEnumerable<HexCoord> visibleTravelHistory,
        IEnumerable<IReadOnlyList<HexCoord>> visibleTravelSegments,
        MissileRouteResult? visibleLastExecutedRoute)
    {
        SalvoId = salvoId;
        OwnerSide = ownerSide;
        LauncherId = launcherId;
        TargetId = targetId;
        Coordinate = coordinate;
        TrackQuality = trackQuality;
        UncertaintyRadiusHexes = uncertaintyRadiusHexes;
        Status = status;
        DistanceTraveled = distanceTraveled;
        TotalFuelSpent = totalFuelSpent;
        MaximumRange = maximumRange;
        InterceptedByDefenseSystemId = interceptedByDefenseSystemId;
        VisibleTravelHistory = Array.AsReadOnly(
            new List<HexCoord>(visibleTravelHistory).ToArray());
        var segments = new List<IReadOnlyList<HexCoord>>();
        foreach (IReadOnlyList<HexCoord> segment in visibleTravelSegments)
        {
            segments.Add(Array.AsReadOnly(new List<HexCoord>(segment).ToArray()));
        }
        VisibleTravelSegments = Array.AsReadOnly(segments.ToArray());
        VisibleLastExecutedRoute = visibleLastExecutedRoute;
    }

    public string SalvoId { get; }

    public TacticalSide OwnerSide { get; }

    public string LauncherId { get; }

    public string TargetId { get; }

    public HexCoord Coordinate { get; }

    public TacticalTrackQuality TrackQuality { get; }

    public int UncertaintyRadiusHexes { get; }

    public GuidedMissileStatus Status { get; }

    public int DistanceTraveled { get; }

    public int TotalFuelSpent { get; }

    public int MaximumRange { get; }

    public int RemainingRange => Math.Max(0, MaximumRange - TotalFuelSpent);

    public string? InterceptedByDefenseSystemId { get; }

    public IReadOnlyList<HexCoord> VisibleTravelHistory { get; }

    public IReadOnlyList<IReadOnlyList<HexCoord>> VisibleTravelSegments { get; }

    public bool HasUnobservedTravelGap => VisibleTravelSegments.Count > 1;

    public MissileRouteResult? VisibleLastExecutedRoute { get; }

    public bool IsTerminal => Status is
        GuidedMissileStatus.Expended or
        GuidedMissileStatus.Dud or
        GuidedMissileStatus.RangeExhausted or
        GuidedMissileStatus.Intercepted or
        GuidedMissileStatus.SelfDestructed or
        GuidedMissileStatus.Destroyed;
}
