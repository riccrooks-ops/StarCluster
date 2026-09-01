using System;
using StarCluster.Core.Combat.Tracking;
using StarCluster.Core.Geometry;

namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Engine-independent sensor-track input supplied to one missile guidance pass.
/// The guidance system never queries a target ship directly.
/// </summary>
public sealed class MissileTargetTrackSnapshot
{
    private MissileTargetTrackSnapshot(
        string targetId,
        MissileTargetTrackQuality quality,
        HexCoord? currentCoordinate,
        HexCoord? estimatedCoordinate,
        HexCoord? lastKnownCoordinate,
        int uncertaintyRadiusHexes)
    {
        if (string.IsNullOrWhiteSpace(targetId))
        {
            throw new ArgumentException("A target-track ID is required.", nameof(targetId));
        }

        if (uncertaintyRadiusHexes < 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(uncertaintyRadiusHexes));
        }

        TargetId = targetId;
        Quality = quality;
        CurrentCoordinate = currentCoordinate;
        EstimatedCoordinate = estimatedCoordinate;
        LastKnownCoordinate = lastKnownCoordinate;
        UncertaintyRadiusHexes = uncertaintyRadiusHexes;
    }

    public string TargetId { get; }

    public MissileTargetTrackQuality Quality { get; }

    public HexCoord? CurrentCoordinate { get; }

    public HexCoord? EstimatedCoordinate { get; }

    public HexCoord? LastKnownCoordinate { get; }

    public int UncertaintyRadiusHexes { get; }

    public HexCoord? GuidanceCoordinate => Quality switch
    {
        MissileTargetTrackQuality.Current => CurrentCoordinate,
        MissileTargetTrackQuality.Approximate => EstimatedCoordinate,
        MissileTargetTrackQuality.Stale => LastKnownCoordinate,
        _ => null,
    };

    public bool HasGuidanceCoordinate => GuidanceCoordinate.HasValue;

    public static MissileTargetTrackSnapshot Current(
        string targetId,
        HexCoord currentCoordinate,
        int uncertaintyRadiusHexes = 0) =>
        new(
            targetId,
            MissileTargetTrackQuality.Current,
            currentCoordinate,
            currentCoordinate,
            currentCoordinate,
            uncertaintyRadiusHexes);

    public static MissileTargetTrackSnapshot Approximate(
        string targetId,
        HexCoord estimatedCoordinate,
        int uncertaintyRadiusHexes = 1) =>
        new(
            targetId,
            MissileTargetTrackQuality.Approximate,
            currentCoordinate: null,
            estimatedCoordinate,
            lastKnownCoordinate: estimatedCoordinate,
            uncertaintyRadiusHexes);

    public static MissileTargetTrackSnapshot Stale(
        string targetId,
        HexCoord lastKnownCoordinate,
        int uncertaintyRadiusHexes = 1) =>
        new(
            targetId,
            MissileTargetTrackQuality.Stale,
            currentCoordinate: null,
            estimatedCoordinate: null,
            lastKnownCoordinate,
            uncertaintyRadiusHexes);

    public static MissileTargetTrackSnapshot Lost(string targetId) =>
        new(
            targetId,
            MissileTargetTrackQuality.Lost,
            currentCoordinate: null,
            estimatedCoordinate: null,
            lastKnownCoordinate: null,
            uncertaintyRadiusHexes: 0);

    public static MissileTargetTrackSnapshot FromTacticalTrack(
        string targetId,
        TacticalTrackRecord? record)
    {
        if (record is null ||
            record.Quality == TacticalTrackQuality.Lost ||
            !record.EstimatedCoordinate.HasValue)
        {
            return Lost(targetId);
        }

        return record.Quality switch
        {
            TacticalTrackQuality.Firm => Current(
                targetId,
                record.EstimatedCoordinate.Value,
                record.UncertaintyRadiusHexes),
            TacticalTrackQuality.Approximate => Approximate(
                targetId,
                record.EstimatedCoordinate.Value,
                record.UncertaintyRadiusHexes),
            TacticalTrackQuality.Stale => Stale(
                targetId,
                record.EstimatedCoordinate.Value,
                record.UncertaintyRadiusHexes),
            _ => Lost(targetId),
        };
    }
}
