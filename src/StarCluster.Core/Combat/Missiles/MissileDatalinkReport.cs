using System;
using StarCluster.Core.Geometry;

namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// One copied launcher report retained by a missile. It is deliberately a
/// value snapshot rather than a live reference to the launcher's track.
/// </summary>
public sealed class MissileDatalinkReport
{
    internal MissileDatalinkReport(
        string targetId,
        MissileTargetTrackQuality receivedQuality,
        HexCoord guidanceCoordinate,
        int sourceObservationEpoch,
        int receivedGuidancePhase,
        int receivedUncertaintyRadiusHexes,
        int agePhases)
    {
        if (string.IsNullOrWhiteSpace(targetId))
        {
            throw new ArgumentException(
                "A target ID is required.",
                nameof(targetId));
        }

        if (receivedQuality == MissileTargetTrackQuality.Lost ||
            !Enum.IsDefined(receivedQuality))
        {
            throw new ArgumentOutOfRangeException(
                nameof(receivedQuality),
                receivedQuality,
                "A retained datalink report must contain a usable coordinate.");
        }

        if (sourceObservationEpoch <= 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(sourceObservationEpoch));
        }

        if (receivedGuidancePhase <= 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(receivedGuidancePhase));
        }

        if (receivedUncertaintyRadiusHexes < 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(receivedUncertaintyRadiusHexes));
        }

        if (agePhases < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(agePhases));
        }

        TargetId = targetId;
        ReceivedQuality = receivedQuality;
        GuidanceCoordinate = guidanceCoordinate;
        SourceObservationEpoch = sourceObservationEpoch;
        ReceivedGuidancePhase = receivedGuidancePhase;
        ReceivedUncertaintyRadiusHexes = receivedUncertaintyRadiusHexes;
        AgePhases = agePhases;
    }

    public string TargetId { get; }

    public MissileTargetTrackQuality ReceivedQuality { get; }

    public HexCoord GuidanceCoordinate { get; }

    public int SourceObservationEpoch { get; }

    public int ReceivedGuidancePhase { get; }

    public int ReceivedUncertaintyRadiusHexes { get; }

    public int AgePhases { get; }

    public int EffectiveUncertaintyRadiusHexes => checked(
        ReceivedUncertaintyRadiusHexes + AgePhases);

    public MissileTargetTrackQuality GetEffectiveQuality(
        int maximumRetainedReportAgePhases)
    {
        if (maximumRetainedReportAgePhases < 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(maximumRetainedReportAgePhases));
        }

        if (AgePhases == 0)
        {
            return ReceivedQuality;
        }

        return AgePhases <= maximumRetainedReportAgePhases
            ? MissileTargetTrackQuality.Stale
            : MissileTargetTrackQuality.Lost;
    }

    public MissileTargetTrackSnapshot CreateGuidanceSnapshot(
        int maximumRetainedReportAgePhases)
    {
        MissileTargetTrackQuality effectiveQuality =
            GetEffectiveQuality(maximumRetainedReportAgePhases);

        return effectiveQuality switch
        {
            MissileTargetTrackQuality.Current =>
                MissileTargetTrackSnapshot.Current(
                    TargetId,
                    GuidanceCoordinate,
                    EffectiveUncertaintyRadiusHexes),
            MissileTargetTrackQuality.Approximate =>
                MissileTargetTrackSnapshot.Approximate(
                    TargetId,
                    GuidanceCoordinate,
                    EffectiveUncertaintyRadiusHexes),
            MissileTargetTrackQuality.Stale =>
                MissileTargetTrackSnapshot.Stale(
                    TargetId,
                    GuidanceCoordinate,
                    EffectiveUncertaintyRadiusHexes),
            _ => MissileTargetTrackSnapshot.Lost(TargetId),
        };
    }

    internal MissileDatalinkReport AgeOnePhase() => new(
        TargetId,
        ReceivedQuality,
        GuidanceCoordinate,
        SourceObservationEpoch,
        ReceivedGuidancePhase,
        ReceivedUncertaintyRadiusHexes,
        checked(AgePhases + 1));

    internal static MissileDatalinkReport CopyFrom(
        MissileTargetTrackSnapshot launcherTrack,
        int sourceObservationEpoch,
        int receivedGuidancePhase)
    {
        ArgumentNullException.ThrowIfNull(launcherTrack);

        if (!launcherTrack.GuidanceCoordinate.HasValue)
        {
            throw new ArgumentException(
                "The launcher track has no coordinate to copy.",
                nameof(launcherTrack));
        }

        return new MissileDatalinkReport(
            launcherTrack.TargetId,
            launcherTrack.Quality,
            launcherTrack.GuidanceCoordinate.Value,
            sourceObservationEpoch,
            receivedGuidancePhase,
            launcherTrack.UncertaintyRadiusHexes,
            agePhases: 0);
    }
}
