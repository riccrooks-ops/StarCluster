using System.Linq;
using StarCluster.Core.Combat.Tracking;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;
using Xunit;

namespace StarCluster.Tests.Combat.Tracking;

public sealed class NavigationAndSystemEntryTests
{
    [Fact]
    public void EveryStarIsAutomaticallyPreKnown()
    {
        SystemMap map = CreateMap();
        NavigationKnowledge knowledge = NavigationKnowledge.FromSystemMap(map);

        Assert.True(knowledge.IsKnown("star-primary"));
        Assert.Equal(MapObjectKind.Star, knowledge.Get("star-primary")!.Kind);
    }

    [Fact]
    public void UnchartedPlanetIsNotAutomaticallyKnown()
    {
        SystemMap map = CreateMap();
        map.Place(
            MapObject.CreatePlanet("planet", "Uncharted World"),
            new HexCoord(2, -2));

        NavigationKnowledge knowledge = NavigationKnowledge.FromSystemMap(map);

        Assert.False(knowledge.IsKnown("planet"));
    }

    [Fact]
    public void ExplicitlyChartedPlanetIsIncluded()
    {
        SystemMap map = CreateMap();
        map.Place(
            MapObject.CreatePlanet("planet", "Charted World"),
            new HexCoord(2, -2));

        NavigationKnowledge knowledge = NavigationKnowledge.FromSystemMap(
            map,
            new[] { "planet" });

        Assert.True(knowledge.IsKnown("planet"));
    }

    [Fact]
    public void InitialTrackUpdateCreatesContactBeforeSnapshotBuild()
    {
        SystemMap map = CreateMap();
        map.Place(
            MapObject.CreateShip("ship-player", "Player Ship"),
            new HexCoord(-2, 2));
        map.Place(
            MapObject.CreateShip("ship-enemy", "Enemy Ship"),
            new HexCoord(0, 2));
        var repository = new TacticalTrackRepository();

        SystemEntryTrackInitializer.Initialize(
            repository,
            "ship-player",
            new[]
            {
                TacticalTrackObservation.Firm(
                    "ship-enemy",
                    new HexCoord(0, 2)),
            },
            new ComputingProfile(2, 2),
            sequence: 1);

        TacticalMapKnowledgeSnapshot snapshot = TacticalMapKnowledgeService.Build(
            map,
            NavigationKnowledge.FromSystemMap(map),
            repository,
            "ship-player",
            new[] { "ship-player" },
            trackSequence: 1);

        Assert.NotNull(snapshot.Find("ship-enemy"));
    }

    [Fact]
    public void ScenarioResetUsesExplicitResetTrigger()
    {
        var repository = new TacticalTrackRepository();
        var results = SystemEntryTrackInitializer.Initialize(
            repository,
            "observer",
            new[]
            {
                TacticalTrackObservation.Firm("target", new HexCoord(1, 0)),
            },
            new ComputingProfile(2, 2),
            sequence: 1,
            trigger: TrackUpdateTrigger.ScenarioReset);

        Assert.All(results, result =>
            Assert.Equal(TrackUpdateTrigger.ScenarioReset, result.Trigger));
    }

    [Fact]
    public void NavigationKnownStarAppearsWithoutSensorTrack()
    {
        SystemMap map = CreateMap();
        TacticalMapKnowledgeSnapshot snapshot = TacticalMapKnowledgeService.Build(
            map,
            NavigationKnowledge.FromSystemMap(map),
            new TacticalTrackRepository(),
            "observer",
            Enumerable.Empty<string>(),
            trackSequence: 0);

        TacticalMapContact contact = snapshot.Find("star-primary")!;
        Assert.NotNull(contact);
        Assert.Equal(
            TacticalMapContactSource.NavigationKnowledge,
            contact.Source);
    }

    private static SystemMap CreateMap() =>
        SystemMap.Create(
            5,
            MapObject.CreateStar("star-primary", "Primary Star"));
}
