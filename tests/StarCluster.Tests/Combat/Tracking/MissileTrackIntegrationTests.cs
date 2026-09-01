using StarCluster.Core.Combat;
using StarCluster.Core.Combat.Missiles;
using StarCluster.Core.Combat.Tracking;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;
using Xunit;

namespace StarCluster.Tests.Combat.Tracking;

public sealed class MissileTrackIntegrationTests
{
    [Fact]
    public void ApproximateTrackConvertsToApproximateMissileSnapshot()
    {
        TacticalTrackRecord record = CreateTrack(
            TacticalTrackObservation.Approximate(
                "target",
                new HexCoord(3, 0)));

        MissileTargetTrackSnapshot snapshot =
            MissileTargetTrackSnapshot.FromTacticalTrack("target", record);

        Assert.Equal(MissileTargetTrackQuality.Approximate, snapshot.Quality);
        Assert.Equal(new HexCoord(3, 0), snapshot.GuidanceCoordinate);
    }

    [Fact]
    public void PrecisionDirectFireRequiresFirmTrack()
    {
        TacticalTrackRecord firm = CreateTrack(
            TacticalTrackObservation.Firm("target", new HexCoord(2, 0)));
        TacticalTrackRecord approximate = CreateTrack(
            TacticalTrackObservation.Approximate("target", new HexCoord(2, 0)));

        Assert.True(DirectFireTrackEligibility.CanTarget(firm));
        Assert.False(DirectFireTrackEligibility.CanTarget(approximate));
        Assert.False(DirectFireTrackEligibility.CanTarget(null));
    }

    [Fact]
    public void RouteProjectionDoesNotMutateSalvoLifetimeState()
    {
        SystemMap map = CreateMap();
        GuidedMissileSalvo salvo = CreateSalvo();
        TacticalTrackRecord track = CreateTrack(
            TacticalTrackObservation.Firm("target", new HexCoord(3, 0)));

        MissileRouteProjection projection =
            MissileRouteProjectionService.Project(map, salvo, track);

        Assert.True(projection.HasRoute);
        Assert.Equal(0, salvo.DistanceTraveled);
        Assert.Equal(GuidedMissileStatus.InFlight, salvo.Status);
        Assert.Null(salvo.LastRoutePlan);
    }

    [Fact]
    public void StaleTrackCanProjectPursuitToLastKnownCoordinate()
    {
        SystemMap map = CreateMap();
        GuidedMissileSalvo salvo = CreateSalvo();
        var repository = new TacticalTrackRepository();
        TacticalTrackRecord track = repository.SeedPriorIntelligence(
            "observer",
            "target",
            new HexCoord(3, 0),
            0);

        MissileRouteProjection projection =
            MissileRouteProjectionService.Project(map, salvo, track);

        Assert.Equal(TacticalTrackQuality.Stale, projection.TrackQuality);
        Assert.True(projection.HasRoute);
    }

    [Fact]
    public void LostTrackProjectsWaitingForTrack()
    {
        SystemMap map = CreateMap();
        GuidedMissileSalvo salvo = CreateSalvo();

        MissileRouteProjection projection =
            MissileRouteProjectionService.Project(map, salvo, targetTrack: null);

        Assert.Equal(
            MissileRouteProjectionStatus.WaitingForTrack,
            projection.Status);
        Assert.Null(projection.RoutePlan);
    }

    [Fact]
    public void ApproximateGuidanceMovesTowardEstimateWithoutClaimingImpact()
    {
        SystemMap map = CreateMap();
        var salvo = new GuidedMissileSalvo(
            "salvo",
            TacticalSide.Player,
            "launcher",
            "target",
            new HexCoord(-1, 1),
            new MissileFlightProfile(2, 6, 4));

        GuidedMissileAdvanceResult result = MissileGuidanceService.AdvanceOnePhase(
            map,
            salvo,
            MissileTargetTrackSnapshot.Approximate(
                "target",
                new HexCoord(1, 1)));

        Assert.Equal(2, result.DistanceTraveledThisPhase);
        Assert.Equal(GuidedMissileStatus.Searching, result.Status);
        Assert.True(salvo.HasTerminalOpportunity);
    }

    private static TacticalTrackRecord CreateTrack(
        TacticalTrackObservation observation)
    {
        var repository = new TacticalTrackRepository();
        TacticalTrackUpdateService.Apply(
            repository,
            "observer",
            observation,
            new ComputingProfile(2, 2),
            1,
            TrackUpdateTrigger.SystemEntry);
        return repository.Get("observer", observation.TargetId)!;
    }

    private static SystemMap CreateMap() =>
        SystemMap.Create(
            4,
            MapObject.CreateStar("star-primary", "Primary Star"));

    private static GuidedMissileSalvo CreateSalvo() => new(
        "salvo",
        TacticalSide.Player,
        "launcher",
        "target",
        new HexCoord(-3, 0),
        new MissileFlightProfile(2, 8, 2));
}
