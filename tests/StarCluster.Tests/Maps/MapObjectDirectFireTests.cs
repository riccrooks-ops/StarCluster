using System;
using StarCluster.Core.Maps;
using Xunit;

namespace StarCluster.Tests.Maps;

public sealed class MapObjectDirectFireTests
{
    [Theory]
    [InlineData(MapObjectKind.Star, true)]
    [InlineData(MapObjectKind.Planet, true)]
    [InlineData(MapObjectKind.Ship, false)]
    [InlineData(MapObjectKind.Station, false)]
    [InlineData(MapObjectKind.Anomaly, false)]
    [InlineData(MapObjectKind.Wreckage, false)]
    public void OnlyStarsAndPlanetsBlockDirectFire(
        MapObjectKind kind,
        bool expected)
    {
        MapObject mapObject = CreateForKind(kind);

        Assert.Equal(expected, mapObject.BlocksDirectFire);
    }

    private static MapObject CreateForKind(MapObjectKind kind) =>
        kind switch
        {
            MapObjectKind.Star => MapObject.CreateStar("star", "Star"),
            MapObjectKind.Planet => MapObject.CreatePlanet("planet", "Planet"),
            MapObjectKind.Ship => MapObject.CreateShip("ship", "Ship"),
            MapObjectKind.Station => MapObject.CreateStation("station", "Station"),
            MapObjectKind.Anomaly => MapObject.CreateAnomaly("anomaly", "Anomaly"),
            MapObjectKind.Wreckage => MapObject.CreateWreckage("wreckage", "Wreckage"),
            _ => throw new ArgumentOutOfRangeException(nameof(kind), kind, null),
        };
}
