using StarCluster.Core.Combat.Tracking;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;
using Xunit;

namespace StarCluster.Tests.Combat.Tracking;

public sealed class TacticalMapKnowledgeTests
{
    [Fact]
    public void UnknownShipDoesNotLeakIntoSnapshot()
    {
        (SystemMap map, NavigationKnowledge navigation) = CreateMap();
        TacticalMapKnowledgeSnapshot snapshot = TacticalMapKnowledgeService.Build(
            map,
            navigation,
            new TacticalTrackRepository(),
            "ship-player",
            new[] { "ship-player" },
            0);

        Assert.Null(snapshot.Find("ship-enemy"));
    }

    [Fact]
    public void FirmShipTrackIsVisible()
    {
        (SystemMap map, NavigationKnowledge navigation) = CreateMap();
        var repository = new TacticalTrackRepository();
        TacticalTrackUpdateService.Apply(
            repository,
            "ship-player",
            TacticalTrackObservation.Firm(
                "ship-enemy",
                new HexCoord(2, 0)),
            new ComputingProfile(2, 2),
            1,
            TrackUpdateTrigger.SystemEntry);

        TacticalMapContact contact = TacticalMapKnowledgeService.Build(
            map,
            navigation,
            repository,
            "ship-player",
            new[] { "ship-player" },
            1).Find("ship-enemy")!;

        Assert.Equal(TacticalTrackQuality.Firm, contact.TrackQuality);
        Assert.Equal(new HexCoord(2, 0), contact.Coordinate);
    }

    [Fact]
    public void StaleTrackUsesLastObservedCoordinateRatherThanTruePosition()
    {
        (SystemMap map, NavigationKnowledge navigation) = CreateMap();
        var repository = new TacticalTrackRepository();
        repository.SeedPriorIntelligence(
            "ship-player",
            "ship-enemy",
            new HexCoord(1, 1),
            sequence: 0);

        TacticalMapContact contact = TacticalMapKnowledgeService.Build(
            map,
            navigation,
            repository,
            "ship-player",
            new[] { "ship-player" },
            1).Find("ship-enemy")!;

        Assert.Equal(TacticalTrackQuality.Stale, contact.TrackQuality);
        Assert.Equal(new HexCoord(1, 1), contact.Coordinate);
        Assert.NotEqual(new HexCoord(2, 0), contact.Coordinate);
    }

    [Fact]
    public void LostTrackIsNotVisible()
    {
        (SystemMap map, NavigationKnowledge navigation) = CreateMap();
        var repository = new TacticalTrackRepository();
        var computing = new ComputingProfile(2, 0);
        TacticalTrackUpdateService.Apply(
            repository,
            "ship-player",
            TacticalTrackObservation.Firm("ship-enemy", new HexCoord(2, 0)),
            computing,
            1,
            TrackUpdateTrigger.SystemEntry);
        TacticalTrackUpdateService.Apply(
            repository,
            "ship-player",
            TacticalTrackObservation.Missed("ship-enemy"),
            computing,
            2,
            TrackUpdateTrigger.ShipMovementCommitted);

        TacticalMapKnowledgeSnapshot snapshot = TacticalMapKnowledgeService.Build(
            map,
            navigation,
            repository,
            "ship-player",
            new[] { "ship-player" },
            2);

        Assert.Null(snapshot.Find("ship-enemy"));
    }

    private static (SystemMap Map, NavigationKnowledge Navigation) CreateMap()
    {
        SystemMap map = SystemMap.Create(
            4,
            MapObject.CreateStar("star-primary", "Primary Star"));
        map.Place(
            MapObject.CreateShip("ship-player", "Player Ship"),
            new HexCoord(-2, 0));
        map.Place(
            MapObject.CreateShip("ship-enemy", "Enemy Ship"),
            new HexCoord(2, 0));
        return (map, NavigationKnowledge.FromSystemMap(map));
    }
}
