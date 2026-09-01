using System;
using StarCluster.Core.Combat.Missiles;
using StarCluster.Core.Geometry;
using Xunit;

namespace StarCluster.Tests.Combat.Missiles;

public sealed class MissileGuidanceArbitrationTests
{
    [Fact]
    public void BlankTargetIdentifierIsRejected()
    {
        Assert.Throws<ArgumentException>(
            () => MissileGuidanceArbitrator.Select(string.Empty));
    }

    [Fact]
    public void NoCandidatesProducesNoUsableDecision()
    {
        MissileGuidanceDecision result =
            MissileGuidanceArbitrator.Select(TargetId);

        Assert.False(result.HasUsableReport);
        Assert.Equal(MissileGuidanceReportSource.None, result.SelectedSource);
        Assert.Equal(MissileTargetTrackQuality.Lost, result.SelectedSnapshot.Quality);
    }

    [Fact]
    public void CurrentQualityBeatsNewerApproximateQuality()
    {
        MissileGuidanceDecision result = MissileGuidanceArbitrator.Select(
            TargetId,
            Candidate(
                MissileGuidanceReportSource.RetainedDatalink,
                MissileTargetTrackSnapshot.Current(TargetId, new HexCoord(1, 1)),
                epoch: 2,
                uncertainty: 0),
            Candidate(
                MissileGuidanceReportSource.LocalSensor,
                MissileTargetTrackSnapshot.Approximate(TargetId, new HexCoord(2, 2)),
                epoch: 9,
                uncertainty: 1));

        Assert.Equal(MissileGuidanceReportSource.RetainedDatalink, result.SelectedSource);
    }

    [Fact]
    public void ApproximateQualityBeatsNewerStaleQuality()
    {
        MissileGuidanceDecision result = MissileGuidanceArbitrator.Select(
            TargetId,
            Candidate(
                MissileGuidanceReportSource.FreshDatalink,
                MissileTargetTrackSnapshot.Approximate(TargetId, new HexCoord(1, 1)),
                epoch: 2,
                uncertainty: 1),
            Candidate(
                MissileGuidanceReportSource.LocalSensor,
                MissileTargetTrackSnapshot.Stale(TargetId, new HexCoord(2, 2)),
                epoch: 9,
                uncertainty: 1));

        Assert.Equal(MissileGuidanceReportSource.FreshDatalink, result.SelectedSource);
    }

    [Fact]
    public void NewerObservationWinsAtEqualQuality()
    {
        MissileGuidanceDecision result = MissileGuidanceArbitrator.Select(
            TargetId,
            Candidate(
                MissileGuidanceReportSource.FreshDatalink,
                MissileTargetTrackSnapshot.Current(TargetId, new HexCoord(1, 1)),
                epoch: 3,
                uncertainty: 0),
            Candidate(
                MissileGuidanceReportSource.LocalSensor,
                MissileTargetTrackSnapshot.Current(TargetId, new HexCoord(2, 2)),
                epoch: 4,
                uncertainty: 0));

        Assert.Equal(MissileGuidanceReportSource.LocalSensor, result.SelectedSource);
        Assert.Equal(new HexCoord(2, 2), result.SelectedSnapshot.GuidanceCoordinate!.Value);
    }

    [Fact]
    public void LowerUncertaintyWinsAtEqualQualityAndEpoch()
    {
        MissileGuidanceDecision result = MissileGuidanceArbitrator.Select(
            TargetId,
            Candidate(
                MissileGuidanceReportSource.FreshDatalink,
                MissileTargetTrackSnapshot.Approximate(TargetId, new HexCoord(1, 1)),
                epoch: 4,
                uncertainty: 2),
            Candidate(
                MissileGuidanceReportSource.LocalSensor,
                MissileTargetTrackSnapshot.Approximate(TargetId, new HexCoord(2, 2)),
                epoch: 4,
                uncertainty: 1));

        Assert.Equal(MissileGuidanceReportSource.LocalSensor, result.SelectedSource);
    }

    [Fact]
    public void LocalSensorWinsAnOtherwiseExactTie()
    {
        MissileGuidanceDecision result = MissileGuidanceArbitrator.Select(
            TargetId,
            Candidate(
                MissileGuidanceReportSource.FreshDatalink,
                MissileTargetTrackSnapshot.Current(TargetId, new HexCoord(1, 1)),
                epoch: 4,
                uncertainty: 0),
            Candidate(
                MissileGuidanceReportSource.LocalSensor,
                MissileTargetTrackSnapshot.Current(TargetId, new HexCoord(1, 1)),
                epoch: 4,
                uncertainty: 0));

        Assert.Equal(MissileGuidanceReportSource.LocalSensor, result.SelectedSource);
        Assert.Contains("local sensor", result.Reason.ToLowerInvariant());
    }

    [Fact]
    public void NewerFreshDatalinkBeatsOlderLocalSensorAtEqualQuality()
    {
        MissileGuidanceDecision result = MissileGuidanceArbitrator.Select(
            TargetId,
            Candidate(
                MissileGuidanceReportSource.FreshDatalink,
                MissileTargetTrackSnapshot.Current(TargetId, new HexCoord(1, 1)),
                epoch: 5,
                uncertainty: 0),
            Candidate(
                MissileGuidanceReportSource.LocalSensor,
                MissileTargetTrackSnapshot.Current(TargetId, new HexCoord(2, 2)),
                epoch: 4,
                uncertainty: 0));

        Assert.Equal(MissileGuidanceReportSource.FreshDatalink, result.SelectedSource);
    }

    [Fact]
    public void LocalCandidateFactoryPreservesCoordinateAndUncertainty()
    {
        StarCluster.Core.Maps.SystemMap map =
            StarCluster.Core.Maps.SystemMap.Create(
                StarCluster.Core.Maps.MapDefaults.SystemRadius,
                StarCluster.Core.Maps.MapObject.CreateStar("star", "Primary"));
        MissileLocalSensorObservationResult observation =
            MissileLocalSensorService.Observe(
                map,
                "missile",
                TargetId,
                new HexCoord(3, 2),
                new HexCoord(0, 2),
                new MissileSensorProfile(
                    2,
                    true,
                    firmRangeHexes: 1,
                    approximateRangeHexes: 3,
                    allowsActiveMode: false),
                previousTrack: null,
                StarCluster.Core.Combat.Tracking.SensorSignatureProfile.Neutral,
                StarCluster.Core.Combat.Tracking.SensorMode.Passive,
                StarCluster.Core.Combat.Tracking.ElectronicWarfareProfile.None,
                targetJammingEnabled: false,
                StarCluster.Core.Combat.Tracking.SensorEnvironmentProfile.ClearSpace,
                observationEpoch: 3);

        MissileGuidanceReportCandidate candidate =
            MissileGuidanceReportCandidate.FromLocalSensor(
                observation.TrackReport)!;

        Assert.Equal(MissileGuidanceReportSource.LocalSensor, candidate.Source);
        Assert.Equal(
            new HexCoord(0, 2),
            candidate.Snapshot.GuidanceCoordinate!.Value);
        Assert.Equal(1, candidate.UncertaintyRadiusHexes);
        Assert.Equal(1, candidate.Snapshot.UncertaintyRadiusHexes);
    }

    [Fact]
    public void LostCandidateIsIgnored()
    {
        MissileGuidanceDecision result = MissileGuidanceArbitrator.Select(
            TargetId,
            Candidate(
                MissileGuidanceReportSource.LocalSensor,
                MissileTargetTrackSnapshot.Lost(TargetId),
                epoch: 5,
                uncertainty: 0));

        Assert.False(result.HasUsableReport);
    }

    private static MissileGuidanceReportCandidate Candidate(
        MissileGuidanceReportSource source,
        MissileTargetTrackSnapshot snapshot,
        int epoch,
        int uncertainty) =>
        new(source, snapshot, epoch, uncertainty, age: 0);

    private const string TargetId = "target";
}
