using System.Linq;
using StarCluster.Core.Combat.Tracking;
using StarCluster.Core.Geometry;
using Xunit;

namespace StarCluster.Tests.Combat.Tracking;

public sealed class ObservedTravelTrailSegmentTests
{
    [Fact]
    public void EmptySamplesProduceNoSegments()
    {
        Assert.Empty(ObservedTravelTrailService.BuildSegments(
            System.Array.Empty<ObservedTrackSample>()));
    }

    [Fact]
    public void ConsecutiveEpochsProduceOneContinuousSegment()
    {
        var first = new HexCoord(1, 0);
        var second = new HexCoord(2, 0);

        var segments = ObservedTravelTrailService.BuildSegments(new[]
        {
            new ObservedTrackSample(first, 1),
            new ObservedTrackSample(second, 2),
        });

        Assert.Single(segments);
        Assert.Equal(new[] { first, second }, segments[0].ToArray());
    }

    [Fact]
    public void SameEpochMovementRemainsContinuous()
    {
        var first = new HexCoord(1, 0);
        var second = new HexCoord(2, 0);

        var segments = ObservedTravelTrailService.BuildSegments(new[]
        {
            new ObservedTrackSample(first, 2),
            new ObservedTrackSample(second, 2),
        });

        Assert.Single(segments);
        Assert.Equal(2, segments[0].Count);
    }

    [Fact]
    public void MissedEpochCreatesDisconnectedSegments()
    {
        var first = new HexCoord(1, 0);
        var second = new HexCoord(3, 0);

        var segments = ObservedTravelTrailService.BuildSegments(new[]
        {
            new ObservedTrackSample(first, 1),
            new ObservedTrackSample(second, 3),
        });

        Assert.Equal(2, segments.Count);
        Assert.Equal(first, Assert.Single(segments[0]));
        Assert.Equal(second, Assert.Single(segments[1]));
    }

    [Fact]
    public void ReacquisitionAfterGapNeverBridgesHiddenMovement()
    {
        var first = new HexCoord(1, 1);
        var second = new HexCoord(2, 1);
        var reacquired = new HexCoord(4, -1);

        var segments = ObservedTravelTrailService.BuildSegments(new[]
        {
            new ObservedTrackSample(first, 1),
            new ObservedTrackSample(second, 2),
            new ObservedTrackSample(reacquired, 4),
        });

        Assert.Equal(2, segments.Count);
        Assert.Equal(new[] { first, second }, segments[0].ToArray());
        Assert.Equal(reacquired, Assert.Single(segments[1]));
    }

    [Fact]
    public void HostileContactReportsUnobservedGapAfterReacquisition()
    {
        var repository = new TacticalTrackRepository();
        var computing = new ComputingProfile(3, 3, 1);
        TacticalTrackUpdateService.Apply(
            repository,
            "player",
            TacticalTrackObservation.Firm("hostile-1", new HexCoord(1, 0)),
            computing,
            sequence: 1,
            TrackUpdateTrigger.MissileMovementCompleted,
            observationEpoch: 1);
        TacticalTrackUpdateService.Apply(
            repository,
            "player",
            TacticalTrackObservation.Missed("hostile-1"),
            computing,
            sequence: 2,
            TrackUpdateTrigger.ShipMovementCommitted,
            observationEpoch: 2);
        TacticalTrackUpdateService.Apply(
            repository,
            "player",
            TacticalTrackObservation.Firm("hostile-1", new HexCoord(3, -1)),
            computing,
            sequence: 3,
            TrackUpdateTrigger.ShipMovementCommitted,
            observationEpoch: 3);

        var salvo = new StarCluster.Core.Combat.Missiles.GuidedMissileSalvo(
            "hostile-1",
            StarCluster.Core.Combat.TacticalSide.Enemy,
            "enemy",
            "player",
            new HexCoord(3, -1),
            new StarCluster.Core.Combat.Missiles.MissileFlightProfile(2, 10, 2));

        TacticalMissileContact contact = Assert.Single(
            TacticalMissileKnowledgeService.Build(
                new[] { salvo },
                repository,
                "player",
                StarCluster.Core.Combat.TacticalSide.Player));

        Assert.True(contact.HasUnobservedTravelGap);
        Assert.Equal(2, contact.VisibleTravelSegments.Count);
    }
}
