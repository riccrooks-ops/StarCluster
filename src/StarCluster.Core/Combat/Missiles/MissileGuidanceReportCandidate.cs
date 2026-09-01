using System;

namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// One immutable report candidate available to a missile at a guidance
/// decision point.
/// </summary>
public sealed class MissileGuidanceReportCandidate
{
    public MissileGuidanceReportCandidate(
        MissileGuidanceReportSource source,
        MissileTargetTrackSnapshot snapshot,
        int sourceObservationEpoch,
        int uncertaintyRadiusHexes,
        int age)
    {
        if (!Enum.IsDefined(source))
        {
            throw new ArgumentOutOfRangeException(nameof(source));
        }

        Snapshot = snapshot ?? throw new ArgumentNullException(nameof(snapshot));

        if (sourceObservationEpoch < 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(sourceObservationEpoch));
        }

        if (uncertaintyRadiusHexes < 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(uncertaintyRadiusHexes));
        }

        if (age < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(age));
        }

        Source = source;
        SourceObservationEpoch = sourceObservationEpoch;
        UncertaintyRadiusHexes = uncertaintyRadiusHexes;
        Age = age;
    }

    public MissileGuidanceReportSource Source { get; }

    public MissileTargetTrackSnapshot Snapshot { get; }

    public int SourceObservationEpoch { get; }

    public int UncertaintyRadiusHexes { get; }

    public int Age { get; }

    public bool IsUsable =>
        Source != MissileGuidanceReportSource.None &&
        Snapshot.HasGuidanceCoordinate;

    public static MissileGuidanceReportCandidate? FromDatalink(
        MissileDatalinkUpdateResult update)
    {
        ArgumentNullException.ThrowIfNull(update);

        if (update.GuidanceSource == MissileGuidanceReportSource.None ||
            !update.GuidanceSnapshot.HasGuidanceCoordinate)
        {
            return null;
        }

        MissileDatalinkReport? retained = update.RetainedReport;
        int uncertainty = retained?.EffectiveUncertaintyRadiusHexes ??
            update.GuidanceSnapshot.UncertaintyRadiusHexes;

        return new MissileGuidanceReportCandidate(
            update.GuidanceSource,
            update.GuidanceSnapshot,
            retained?.SourceObservationEpoch ?? 0,
            uncertainty,
            retained?.AgePhases ?? 0);
    }

    public static MissileGuidanceReportCandidate? FromLocalSensor(
        MissileLocalTrackReport? report)
    {
        if (report is null)
        {
            return null;
        }

        return new MissileGuidanceReportCandidate(
            MissileGuidanceReportSource.LocalSensor,
            report.CreateGuidanceSnapshot(),
            report.SourceObservationEpoch,
            report.UncertaintyRadiusHexes,
            report.AgeEpochs);
    }
}
