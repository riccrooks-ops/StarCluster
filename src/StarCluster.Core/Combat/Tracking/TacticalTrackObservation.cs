using System;
using StarCluster.Core.Geometry;

namespace StarCluster.Core.Combat.Tracking;

/// <summary>
/// One sensor report supplied to the track manager. A missed report contains no
/// authoritative coordinate and therefore cannot create a new contact.
/// </summary>
public sealed class TacticalTrackObservation
{
    private TacticalTrackObservation(
        string targetId,
        bool detected,
        bool precise,
        HexCoord? estimatedCoordinate,
        int uncertaintyRadiusHexes,
        TacticalTrackSourceType sourceType)
    {
        if (string.IsNullOrWhiteSpace(targetId))
        {
            throw new ArgumentException("A target ID is required.", nameof(targetId));
        }

        if (uncertaintyRadiusHexes < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(uncertaintyRadiusHexes));
        }

        if (detected && !estimatedCoordinate.HasValue)
        {
            throw new ArgumentException(
                "A detected contact requires an estimated coordinate.",
                nameof(estimatedCoordinate));
        }

        TargetId = targetId;
        Detected = detected;
        Precise = precise;
        EstimatedCoordinate = estimatedCoordinate;
        UncertaintyRadiusHexes = uncertaintyRadiusHexes;
        SourceType = sourceType;
    }

    public string TargetId { get; }

    public bool Detected { get; }

    public bool Precise { get; }

    public HexCoord? EstimatedCoordinate { get; }

    public int UncertaintyRadiusHexes { get; }

    public TacticalTrackSourceType SourceType { get; }

    public static TacticalTrackObservation Firm(
        string targetId,
        HexCoord coordinate,
        TacticalTrackSourceType sourceType = TacticalTrackSourceType.TacticalSensors) =>
        new(targetId, true, true, coordinate, 0, sourceType);

    public static TacticalTrackObservation Approximate(
        string targetId,
        HexCoord estimatedCoordinate,
        int uncertaintyRadiusHexes = 1,
        TacticalTrackSourceType sourceType = TacticalTrackSourceType.TacticalSensors) =>
        new(
            targetId,
            true,
            false,
            estimatedCoordinate,
            Math.Max(1, uncertaintyRadiusHexes),
            sourceType);

    public static TacticalTrackObservation Missed(
        string targetId,
        TacticalTrackSourceType sourceType = TacticalTrackSourceType.TacticalSensors) =>
        new(targetId, false, false, null, 0, sourceType);
}
