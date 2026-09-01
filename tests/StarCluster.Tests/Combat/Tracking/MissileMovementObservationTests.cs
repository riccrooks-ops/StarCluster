using System.Linq;
using StarCluster.Core.Combat;
using StarCluster.Core.Combat.Missiles;
using StarCluster.Core.Combat.Tracking;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;
using Xunit;

namespace StarCluster.Tests.Combat.Tracking;

public sealed class MissileMovementObservationTests
{
    private readonly SystemMap _map = SystemMap.Create(
        5,
        MapObject.CreateStar("star-primary", "Primary Star"));
    private readonly ComputingProfile _computing = new(3, 3, 1);

    [Fact]
    public void FirmTrackedLauncherStartsTrailAtLaunchOrigin()
    {
        var repository = new TacticalTrackRepository();
        GuidedMissileSalvo salvo = CreateSalvo(new HexCoord(4, 0));

        MissileMovementObservationResult result = Apply(
            repository,
            salvo,
            new[] { new HexCoord(3, 0), new HexCoord(2, 0) },
            launchObservedAtOrigin: true,
            sensorRange: 2);

        TacticalTrackRecord track = repository.Get("player", salvo.Id)!;
        Assert.True(result.Steps[0].IsLaunchOrigin);
        Assert.True(result.Steps[0].SegmentStarted);
        Assert.Equal(TacticalTrackSourceType.TacticalSensors, track.SourceType);
        Assert.Equal(
            new[] { new HexCoord(4, 0), new HexCoord(2, 0) },
            track.ObservedCoordinateHistory.ToArray());
    }

    [Fact]
    public void UndetectedLauncherStartsTrailAtFirstDetectedEnteredHex()
    {
        var repository = new TacticalTrackRepository();
        GuidedMissileSalvo salvo = CreateSalvo(new HexCoord(4, 0));

        _ = Apply(
            repository,
            salvo,
            new[] { new HexCoord(3, 0), new HexCoord(2, 0), new HexCoord(1, 0) },
            launchObservedAtOrigin: false,
            sensorRange: 2);

        TacticalTrackRecord track = repository.Get("player", salvo.Id)!;
        Assert.Equal(
            new[] { new HexCoord(2, 0), new HexCoord(1, 0) },
            track.ObservedCoordinateHistory.ToArray());
        Assert.DoesNotContain(salvo.LaunchCoordinate, track.ObservedCoordinateHistory);
    }

    [Fact]
    public void ConsecutiveDetectedHexesExtendOneSegment()
    {
        var repository = new TacticalTrackRepository();
        GuidedMissileSalvo salvo = CreateSalvo(new HexCoord(3, 0));

        _ = Apply(
            repository,
            salvo,
            new[] { new HexCoord(2, 0), new HexCoord(1, 0) },
            launchObservedAtOrigin: false,
            sensorRange: 2);

        var segments = ObservedTravelTrailService.BuildSegments(
            repository.Get("player", salvo.Id)!.ObservedSamples);
        Assert.Single(segments);
        Assert.Equal(
            new[] { new HexCoord(2, 0), new HexCoord(1, 0) },
            segments[0].ToArray());
    }

    [Fact]
    public void MissedHexClosesObservedSegment()
    {
        var repository = new TacticalTrackRepository();
        GuidedMissileSalvo salvo = CreateSalvo(new HexCoord(1, 0));

        MissileMovementObservationResult result = Apply(
            repository,
            salvo,
            new[] { new HexCoord(1, 0), new HexCoord(3, 0) },
            launchObservedAtOrigin: false,
            sensorRange: 1);

        Assert.True(result.Steps[1].SegmentClosed);
        Assert.False(repository.Get("player", salvo.Id)!.HasOpenObservedSegment);
    }

    [Fact]
    public void ReacquisitionSameEpochStartsDisconnectedSegment()
    {
        var repository = new TacticalTrackRepository();
        GuidedMissileSalvo salvo = CreateSalvo(new HexCoord(1, 0));

        _ = Apply(
            repository,
            salvo,
            new[]
            {
                new HexCoord(1, 0),
                new HexCoord(3, 0),
                new HexCoord(1, -1),
            },
            launchObservedAtOrigin: false,
            sensorRange: 1);

        var segments = ObservedTravelTrailService.BuildSegments(
            repository.Get("player", salvo.Id)!.ObservedSamples);
        Assert.Equal(2, segments.Count);
        Assert.Equal(new HexCoord(1, 0), Assert.Single(segments[0]));
        Assert.Equal(new HexCoord(1, -1), Assert.Single(segments[1]));
    }

    [Fact]
    public void SameCoordinateReacquisitionStartsNewSegment()
    {
        var repository = new TacticalTrackRepository();
        GuidedMissileSalvo salvo = CreateSalvo(new HexCoord(1, 0));

        _ = Apply(
            repository,
            salvo,
            new[]
            {
                new HexCoord(1, 0),
                new HexCoord(3, 0),
                new HexCoord(1, 0),
            },
            launchObservedAtOrigin: false,
            sensorRange: 1);

        var segments = ObservedTravelTrailService.BuildSegments(
            repository.Get("player", salvo.Id)!.ObservedSamples);
        Assert.Equal(2, segments.Count);
        Assert.Equal(new HexCoord(1, 0), Assert.Single(segments[0]));
        Assert.Equal(new HexCoord(1, 0), Assert.Single(segments[1]));
    }

    [Fact]
    public void ObservedLaunchCanCreateOriginOnlyTrailBeforeContactIsLost()
    {
        var repository = new TacticalTrackRepository();
        GuidedMissileSalvo salvo = CreateSalvo(new HexCoord(4, 0));

        _ = Apply(
            repository,
            salvo,
            new[] { new HexCoord(4, -1) },
            launchObservedAtOrigin: true,
            sensorRange: 1);

        var segments = ObservedTravelTrailService.BuildSegments(
            repository.Get("player", salvo.Id)!.ObservedSamples);
        Assert.Single(segments);
        Assert.Equal(salvo.LaunchCoordinate, Assert.Single(segments[0]));
    }

    [Fact]
    public void SameHexContactIsFirmWithoutZeroLengthLineOfSightRay()
    {
        TacticalTrackObservation observation = SensorContactEvaluator.Observe(
            _map,
            "impacting-missile",
            new HexCoord(1, -2),
            new HexCoord(1, -2),
            new SensorProfile(3, 0, 0, requiresLineOfSight: true));

        Assert.True(observation.Detected);
        Assert.True(observation.Precise);
        Assert.Equal(new HexCoord(1, -2), observation.EstimatedCoordinate);
    }

    private MissileMovementObservationResult Apply(
        TacticalTrackRepository repository,
        GuidedMissileSalvo salvo,
        HexCoord[] entered,
        bool launchObservedAtOrigin,
        int sensorRange) =>
        MissileMovementObservationService.Apply(
            _map,
            repository,
            "player",
            new HexCoord(0, 0),
            salvo,
            entered,
            new SensorProfile(3, sensorRange, sensorRange, requiresLineOfSight: false),
            _computing,
            startingSequence: 0,
            trigger: TrackUpdateTrigger.MissileMovementCompleted,
            observationEpoch: 3,
            launchObservedAtOrigin: launchObservedAtOrigin);

    private static GuidedMissileSalvo CreateSalvo(HexCoord launchCoordinate) =>
        new(
            "hostile-1",
            TacticalSide.Enemy,
            "enemy",
            "player",
            launchCoordinate,
            new MissileFlightProfile(2, 10, 3));
}
