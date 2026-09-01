using StarCluster.Core.Maps;
using Xunit;

namespace StarCluster.Tests.Maps;

public sealed class MapObjectMissileTests
{
    [Theory]
    [InlineData(MapObjectKind.Star)]
    [InlineData(MapObjectKind.Planet)]
    public void CelestialBodiesBlockMissileTravel(MapObjectKind kind)
    {
        MapObject mapObject = kind == MapObjectKind.Star
            ? MapObject.CreateStar("object", "Primary")
            : MapObject.CreatePlanet("object", "World");

        Assert.True(mapObject.BlocksMissileTravel);
    }

    [Theory]
    [InlineData(MapObjectKind.Ship)]
    [InlineData(MapObjectKind.Station)]
    [InlineData(MapObjectKind.Anomaly)]
    [InlineData(MapObjectKind.Wreckage)]
    public void OtherMapObjectsDoNotBlockMissileTravel(MapObjectKind kind)
    {
        MapObject mapObject = kind switch
        {
            MapObjectKind.Ship => MapObject.CreateShip("object", "Ship"),
            MapObjectKind.Station => MapObject.CreateStation("object", "Station"),
            MapObjectKind.Anomaly => MapObject.CreateAnomaly("object", "Signal"),
            _ => MapObject.CreateWreckage("object", "Debris"),
        };

        Assert.False(mapObject.BlocksMissileTravel);
    }
}
