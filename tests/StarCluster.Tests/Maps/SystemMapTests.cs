using System;
using System.Collections.Generic;
using System.Linq;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;
using Xunit;

namespace StarCluster.Tests.Maps;

public sealed class SystemMapTests
{
    [Fact]
    public void CurrentSystemDefaultCreatesElevenAcrossMap()
    {
        SystemMap map = SystemMap.Create(MapDefaults.SystemRadius);

        Assert.Equal(5, map.Geometry.Radius);
        Assert.Equal(11, map.Geometry.Diameter);
        Assert.Equal(91, map.Cells.Count);
    }

    [Fact]
    public void CreateWithoutStarLeavesOriginEmpty()
    {
        SystemMap map = SystemMap.Create(2);

        Assert.Null(map.Star);
        Assert.Empty(map.GetCell(HexCoord.Zero).Occupants);
    }

    [Fact]
    public void CreateWithStarPlacesItAtOrigin()
    {
        MapObject star = MapObject.CreateStar("star-sol", "Sol");

        SystemMap map = SystemMap.Create(2, star);

        Assert.Same(star, map.Star);
        Assert.Equal(new[] { star }, map.GetCell(HexCoord.Zero).Occupants);
        Assert.True(map.TryGetLocation(star.Id, out HexCoord location));
        Assert.Equal(HexCoord.Zero, location);
    }

    [Fact]
    public void CreateRejectsNonStarAsCentralStar()
    {
        MapObject planet = MapObject.CreatePlanet("planet-earth", "Earth");

        Assert.Throws<ArgumentException>(
            () => SystemMap.Create(2, planet));
    }

    [Fact]
    public void PlaceRejectsCoordinateOutsideMap()
    {
        SystemMap map = SystemMap.Create(2);
        MapObject ship = MapObject.CreateShip("ship-1", "Explorer");

        Assert.Throws<ArgumentOutOfRangeException>(
            () => map.Place(ship, new HexCoord(3, 0)));
    }

    [Fact]
    public void PlaceRejectsDuplicateObjectId()
    {
        SystemMap map = SystemMap.Create(2);
        MapObject first = MapObject.CreateShip("shared-id", "Explorer");
        MapObject second = MapObject.CreateAnomaly("shared-id", "Echo");
        map.Place(first, new HexCoord(1, 0));

        Assert.Throws<ArgumentException>(
            () => map.Place(second, new HexCoord(0, 1)));
    }

    [Fact]
    public void PlaceRejectsSecondStar()
    {
        SystemMap map = SystemMap.Create(
            2,
            MapObject.CreateStar("star-1", "Primary"));
        MapObject secondStar = MapObject.CreateStar("star-2", "Secondary");

        Assert.Throws<InvalidOperationException>(
            () => map.Place(secondStar, HexCoord.Zero));
    }

    [Fact]
    public void PlaceRejectsStarAwayFromOrigin()
    {
        SystemMap map = SystemMap.Create(2);
        MapObject star = MapObject.CreateStar("star-1", "Primary");

        Assert.Throws<InvalidOperationException>(
            () => map.Place(star, new HexCoord(1, 0)));
    }

    [Fact]
    public void PlaceAllowsPlanetAwayFromOrigin()
    {
        SystemMap map = SystemMap.Create(2);
        MapObject planet = MapObject.CreatePlanet("planet-1", "New Terra");
        var location = new HexCoord(1, 0);

        map.Place(planet, location);

        Assert.Equal(new[] { planet }, map.GetCell(location).Occupants);
        Assert.True(map.TryGetLocation(planet.Id, out HexCoord actual));
        Assert.Equal(location, actual);
    }

    [Fact]
    public void SolidObjectCannotShareCellWithAnotherSolidObject()
    {
        SystemMap map = SystemMap.Create(2);
        var location = new HexCoord(1, 0);
        map.Place(MapObject.CreatePlanet("planet-1", "World"), location);

        Assert.Throws<InvalidOperationException>(
            () => map.Place(
                MapObject.CreateShip("ship-1", "Explorer"),
                location));
    }

    [Fact]
    public void NonSolidObjectCanShareCellWithSolidObject()
    {
        SystemMap map = SystemMap.Create(2);
        var location = new HexCoord(1, 0);
        MapObject planet = MapObject.CreatePlanet("planet-1", "World");
        MapObject anomaly = MapObject.CreateAnomaly("anomaly-1", "Signal");

        map.Place(planet, location);
        map.Place(anomaly, location);

        Assert.Equal(new[] { planet, anomaly }, map.GetCell(location).Occupants);
    }

    [Fact]
    public void MultipleNonSolidObjectsCanShareCell()
    {
        SystemMap map = SystemMap.Create(2);
        var location = new HexCoord(1, -1);
        MapObject anomaly = MapObject.CreateAnomaly("anomaly-1", "Signal");
        MapObject wreckage = MapObject.CreateWreckage("wreck-1", "Debris");

        map.Place(anomaly, location);
        map.Place(wreckage, location);

        Assert.Equal(new[] { anomaly, wreckage }, map.GetCell(location).Occupants);
        Assert.False(map.GetCell(location).HasSolidOccupant);
    }

    [Fact]
    public void GetCellRejectsCoordinateOutsideMap()
    {
        SystemMap map = SystemMap.Create(2);

        Assert.Throws<ArgumentOutOfRangeException>(
            () => map.GetCell(new HexCoord(3, 0)));
    }

    [Fact]
    public void SetTerrainUpdatesOnlyRequestedCell()
    {
        SystemMap map = SystemMap.Create(2);
        var location = new HexCoord(1, 0);

        map.SetTerrain(location, MapTerrain.Nebula);

        Assert.Equal(MapTerrain.Nebula, map.GetCell(location).Terrain);
        Assert.Equal(MapTerrain.OpenSpace, map.GetCell(HexCoord.Zero).Terrain);
    }

    [Fact]
    public void MoveShipTransfersItToEmptyDestination()
    {
        SystemMap map = SystemMap.Create(2);
        MapObject ship = MapObject.CreateShip("ship-1", "Explorer");
        var origin = new HexCoord(1, 0);
        var destination = new HexCoord(0, 1);
        map.Place(ship, origin);

        map.Move(ship.Id, destination);

        Assert.Empty(map.GetCell(origin).Occupants);
        Assert.Equal(new[] { ship }, map.GetCell(destination).Occupants);
        Assert.True(map.TryGetLocation(ship.Id, out HexCoord actual));
        Assert.Equal(destination, actual);
    }

    [Fact]
    public void MoveShipCannotEnterCellWithSolidObject()
    {
        SystemMap map = SystemMap.Create(2);
        MapObject ship = MapObject.CreateShip("ship-1", "Explorer");
        var origin = new HexCoord(1, 0);
        var destination = new HexCoord(0, 1);
        map.Place(ship, origin);
        map.Place(MapObject.CreatePlanet("planet-1", "World"), destination);

        Assert.Throws<InvalidOperationException>(
            () => map.Move(ship.Id, destination));

        Assert.True(map.TryGetLocation(ship.Id, out HexCoord actual));
        Assert.Equal(origin, actual);
    }

    [Theory]
    [InlineData(MapObjectKind.Star)]
    [InlineData(MapObjectKind.Planet)]
    [InlineData(MapObjectKind.Station)]
    public void MoveRejectsImmovableSolidObjects(MapObjectKind kind)
    {
        SystemMap map = SystemMap.Create(2);
        MapObject mapObject = CreateForKind(kind, $"object-{kind}");
        HexCoord origin = kind == MapObjectKind.Star
            ? HexCoord.Zero
            : new HexCoord(1, 0);
        map.Place(mapObject, origin);

        Assert.Throws<InvalidOperationException>(
            () => map.Move(mapObject.Id, new HexCoord(0, 1)));
    }

    [Fact]
    public void MoveRejectsDestinationOutsideMap()
    {
        SystemMap map = SystemMap.Create(2);
        MapObject ship = MapObject.CreateShip("ship-1", "Explorer");
        var origin = new HexCoord(1, 0);
        map.Place(ship, origin);

        Assert.Throws<ArgumentOutOfRangeException>(
            () => map.Move(ship.Id, new HexCoord(3, 0)));

        Assert.True(map.TryGetLocation(ship.Id, out HexCoord actual));
        Assert.Equal(origin, actual);
    }

    [Fact]
    public void RemoveClearsCellAndLocationIndex()
    {
        SystemMap map = SystemMap.Create(2);
        MapObject ship = MapObject.CreateShip("ship-1", "Explorer");
        var location = new HexCoord(1, 0);
        map.Place(ship, location);

        MapObject removed = map.Remove(ship.Id);

        Assert.Same(ship, removed);
        Assert.Empty(map.GetCell(location).Occupants);
        Assert.False(map.TryGetLocation(ship.Id, out _));
    }

    [Fact]
    public void RemoveMissingObjectThrows()
    {
        SystemMap map = SystemMap.Create(2);

        Assert.Throws<KeyNotFoundException>(
            () => map.Remove("missing"));
    }

    [Fact]
    public void TryGetLocationReturnsFalseForUnknownOrNullId()
    {
        SystemMap map = SystemMap.Create(2);

        Assert.False(map.TryGetLocation("missing", out _));
        Assert.False(map.TryGetLocation(null!, out _));
    }

    [Fact]
    public void GeometryRemainsIndependentOfMapContents()
    {
        HexMap geometry = HexMap.CreateHexagon(2);
        SystemMap system = SystemMap.Create(
            2,
            MapObject.CreateStar("star-1", "Primary"));
        system.Place(
            MapObject.CreatePlanet("planet-1", "World"),
            new HexCoord(1, 0));

        Assert.Equal(geometry.Cells, system.Geometry.Cells);
        Assert.Equal(geometry.CellCount, system.Cells.Count);
        Assert.All(geometry.Cells, coordinate => Assert.True(system.Geometry.Contains(coordinate)));
    }

    [Theory]
    [InlineData(MapObjectKind.Star, true, false)]
    [InlineData(MapObjectKind.Planet, true, false)]
    [InlineData(MapObjectKind.Ship, true, true)]
    [InlineData(MapObjectKind.Station, true, false)]
    [InlineData(MapObjectKind.Anomaly, false, false)]
    [InlineData(MapObjectKind.Wreckage, false, false)]
    public void ObjectFactoriesAssignExpectedPrototypeTraits(
        MapObjectKind kind,
        bool expectedSolid,
        bool expectedMovable)
    {
        MapObject mapObject = CreateForKind(kind, $"object-{kind}");

        Assert.Equal(kind, mapObject.Kind);
        Assert.Equal(expectedSolid, mapObject.IsSolid);
        Assert.Equal(expectedMovable, mapObject.CanMove);
    }

    private static MapObject CreateForKind(MapObjectKind kind, string id) =>
        kind switch
        {
            MapObjectKind.Star => MapObject.CreateStar(id, "Star"),
            MapObjectKind.Planet => MapObject.CreatePlanet(id, "Planet"),
            MapObjectKind.Ship => MapObject.CreateShip(id, "Ship"),
            MapObjectKind.Station => MapObject.CreateStation(id, "Station"),
            MapObjectKind.Anomaly => MapObject.CreateAnomaly(id, "Anomaly"),
            MapObjectKind.Wreckage => MapObject.CreateWreckage(id, "Wreckage"),
            _ => throw new ArgumentOutOfRangeException(nameof(kind), kind, null),
        };
}
