using System;
using StarCluster.Core.Combat.Tracking;
using StarCluster.Core.Geometry;

namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Missile-owned local sensor report. It is separate from launcher and retained
/// datalink reports and never exposes authoritative target state unless the
/// local sensor actually observed it.
/// </summary>
public sealed class MissileLocalTrackReport
{
    internal MissileLocalTrackReport(
        string targetId,
        MissileTargetTrackQuality quality,
        HexCoord guidanceCoordinate,
        int sourceObservationEpoch,
        int uncertaintyRadiusHexes,
        SensorMode sensorMode,
        int ageEpochs,
        int? lastAgedObservationEpoch)
    {
        if (string.IsNullOrWhiteSpace(targetId))
        {
            throw new ArgumentException(
                "A target ID is required.",
                nameof(targetId));
        }

        if (quality == MissileTargetTrackQuality.Lost ||
            !Enum.IsDefined(quality))
        {
            throw new ArgumentOutOfRangeException(nameof(quality));
        }

        if (sourceObservationEpoch <= 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(sourceObservationEpoch));
        }

        if (uncertaintyRadiusHexes < 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(uncertaintyRadiusHexes));
        }

        if (!Enum.IsDefined(sensorMode))
        {
            throw new ArgumentOutOfRangeException(nameof(sensorMode));
        }

        if (ageEpochs < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(ageEpochs));
        }

        TargetId = targetId;
        Quality = quality;
        GuidanceCoordinate = guidanceCoordinate;
        SourceObservationEpoch = sourceObservationEpoch;
        UncertaintyRadiusHexes = uncertaintyRadiusHexes;
        SensorMode = sensorMode;
        AgeEpochs = ageEpochs;
        LastAgedObservationEpoch = lastAgedObservationEpoch;
    }

    public string TargetId { get; }

    public MissileTargetTrackQuality Quality { get; }

    public HexCoord GuidanceCoordinate { get; }

    public int SourceObservationEpoch { get; }

    public int UncertaintyRadiusHexes { get; }

    public SensorMode SensorMode { get; }

    public int AgeEpochs { get; }

    public int? LastAgedObservationEpoch { get; }

    public MissileTargetTrackSnapshot CreateGuidanceSnapshot() => Quality switch
    {
        MissileTargetTrackQuality.Current =>
            MissileTargetTrackSnapshot.Current(
                TargetId,
                GuidanceCoordinate,
                UncertaintyRadiusHexes),
        MissileTargetTrackQuality.Approximate =>
            MissileTargetTrackSnapshot.Approximate(
                TargetId,
                GuidanceCoordinate,
                UncertaintyRadiusHexes),
        MissileTargetTrackQuality.Stale =>
            MissileTargetTrackSnapshot.Stale(
                TargetId,
                GuidanceCoordinate,
                UncertaintyRadiusHexes),
        _ => MissileTargetTrackSnapshot.Lost(TargetId),
    };
}
