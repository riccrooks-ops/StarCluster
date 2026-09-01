using System;
using System.Linq;
using StarCluster.Core.Combat;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;
using Xunit;

namespace StarCluster.Tests.Combat;

public sealed class DirectFireLineOfSightTests
{
    [Fact]
    public void AdjacentCellsHaveClearLineWithNoIntermediateCells()
    {
        SystemMap map = SystemMap.Create(2);

        DirectFireLineOfSightResult result = DirectFireLineOfSight.Evaluate(
            map,
            HexCoord.Zero,
            new HexCoord(1, 0));

        Assert.Equal(LineOfSightQuality.Clear, result.Quality);
        Assert.True(result.IsClear);
        Assert.True(result.HasLineOfSight);
        Assert.Empty(result.TestedCells);
        Assert.Empty(result.Blockers);
        Assert.Empty(result.Grazings);
        Assert.Null(result.Blockage);
    }

    [Fact]
    public void EmptyDistantLineIsClear()
    {
        SystemMap map = SystemMap.Create(3);

        DirectFireLineOfSightResult result = DirectFireLineOfSight.Evaluate(
            map,
            new HexCoord(-2, 0),
            new HexCoord(2, 0));

        Assert.Equal(LineOfSightQuality.Clear, result.Quality);
        Assert.True(result.IsClear);
        Assert.Equal(
            new[]
            {
                new HexCoord(-1, 0),
                HexCoord.Zero,
                new HexCoord(1, 0),
            },
            result.TestedCells);
    }

    [Fact]
    public void IntermediatePlanetBlocksDirectFire()
    {
        SystemMap map = SystemMap.Create(3);
        MapObject planet = MapObject.CreatePlanet("planet", "World");
        map.Place(planet, HexCoord.Zero);

        DirectFireLineOfSightResult result = DirectFireLineOfSight.Evaluate(
            map,
            new HexCoord(-2, 0),
            new HexCoord(2, 0));

        Assert.Equal(LineOfSightQuality.Blocked, result.Quality);
        Assert.True(result.IsBlocked);
        Assert.False(result.HasLineOfSight);
        LineOfSightBlocker blocker = Assert.Single(result.Blockers);
        Assert.Equal(HexCoord.Zero, blocker.Coordinate);
        Assert.Same(planet, blocker.MapObject);
        Assert.NotNull(result.Blockage);
        Assert.Equal(2, result.Blockage!.RangeStep);
    }

    [Fact]
    public void IntermediateStarBlocksDirectFire()
    {
        MapObject star = MapObject.CreateStar("star", "Primary");
        SystemMap map = SystemMap.Create(3, star);

        DirectFireLineOfSightResult result = DirectFireLineOfSight.Evaluate(
            map,
            new HexCoord(-2, 0),
            new HexCoord(2, 0));

        Assert.True(result.IsBlocked);
        LineOfSightBlocker blocker = Assert.Single(result.Blockers);
        Assert.Equal(HexCoord.Zero, blocker.Coordinate);
        Assert.Same(star, blocker.MapObject);
    }

    [Fact]
    public void IntermediateShipDoesNotBlockDirectFire()
    {
        SystemMap map = SystemMap.Create(3);
        map.Place(MapObject.CreateShip("ship", "Screen"), HexCoord.Zero);

        DirectFireLineOfSightResult result = DirectFireLineOfSight.Evaluate(
            map,
            new HexCoord(-2, 0),
            new HexCoord(2, 0));

        Assert.True(result.IsClear);
    }

    [Fact]
    public void IntermediateStationDoesNotBlockDirectFire()
    {
        SystemMap map = SystemMap.Create(3);
        map.Place(MapObject.CreateStation("station", "Outpost"), HexCoord.Zero);

        DirectFireLineOfSightResult result = DirectFireLineOfSight.Evaluate(
            map,
            new HexCoord(-2, 0),
            new HexCoord(2, 0));

        Assert.True(result.IsClear);
    }

    [Theory]
    [InlineData(MapObjectKind.Anomaly)]
    [InlineData(MapObjectKind.Wreckage)]
    public void NonSolidObjectsDoNotBlockDirectFire(MapObjectKind kind)
    {
        SystemMap map = SystemMap.Create(3);
        MapObject mapObject = kind == MapObjectKind.Anomaly
            ? MapObject.CreateAnomaly("object", "Signal")
            : MapObject.CreateWreckage("object", "Debris");
        map.Place(mapObject, HexCoord.Zero);

        DirectFireLineOfSightResult result = DirectFireLineOfSight.Evaluate(
            map,
            new HexCoord(-2, 0),
            new HexCoord(2, 0));

        Assert.True(result.IsClear);
    }

    [Theory]
    [InlineData(MapTerrain.AsteroidField)]
    [InlineData(MapTerrain.Nebula)]
    public void PrototypeTerrainDoesNotYetBlockDirectFire(MapTerrain terrain)
    {
        SystemMap map = SystemMap.Create(3);
        map.SetTerrain(HexCoord.Zero, terrain);

        DirectFireLineOfSightResult result = DirectFireLineOfSight.Evaluate(
            map,
            new HexCoord(-2, 0),
            new HexCoord(2, 0));

        Assert.True(result.IsClear);
    }

    [Fact]
    public void BlockingObjectInOriginCellIsIgnored()
    {
        SystemMap map = SystemMap.Create(3);
        var origin = new HexCoord(-2, 0);
        map.Place(MapObject.CreatePlanet("planet", "Origin World"), origin);

        DirectFireLineOfSightResult result = DirectFireLineOfSight.Evaluate(
            map,
            origin,
            new HexCoord(2, 0));

        Assert.True(result.IsClear);
    }

    [Fact]
    public void BlockingObjectInTargetCellIsIgnored()
    {
        SystemMap map = SystemMap.Create(3);
        var target = new HexCoord(2, 0);
        map.Place(MapObject.CreatePlanet("planet", "Target World"), target);

        DirectFireLineOfSightResult result = DirectFireLineOfSight.Evaluate(
            map,
            new HexCoord(-2, 0),
            target);

        Assert.True(result.IsClear);
    }

    [Fact]
    public void BoundaryLineGrazesObjectOnFirstSide()
    {
        SystemMap map = SystemMap.Create(2);
        MapObject planet = MapObject.CreatePlanet("planet", "Upper World");
        map.Place(planet, new HexCoord(1, 0));

        DirectFireLineOfSightResult result = DirectFireLineOfSight.Evaluate(
            map,
            HexCoord.Zero,
            new HexCoord(2, -1));

        Assert.Equal(LineOfSightQuality.Grazing, result.Quality);
        Assert.True(result.IsGrazing);
        Assert.True(result.HasLineOfSight);
        Assert.Empty(result.Blockers);
        LineOfSightGrazing grazing = Assert.Single(result.Grazings);
        Assert.Equal(1, grazing.RangeStep);
        Assert.Equal(new HexCoord(1, 0), grazing.BlockedCoordinate);
        Assert.Equal(new HexCoord(1, -1), grazing.OpenCoordinate);
        Assert.Same(planet, Assert.Single(grazing.Blockers).MapObject);
    }

    [Fact]
    public void BoundaryLineGrazesObjectOnSecondSide()
    {
        SystemMap map = SystemMap.Create(2);
        MapObject planet = MapObject.CreatePlanet("planet", "Lower World");
        map.Place(planet, new HexCoord(1, -1));

        DirectFireLineOfSightResult result = DirectFireLineOfSight.Evaluate(
            map,
            HexCoord.Zero,
            new HexCoord(2, -1));

        Assert.True(result.IsGrazing);
        LineOfSightGrazing grazing = Assert.Single(result.Grazings);
        Assert.Equal(new HexCoord(1, -1), grazing.BlockedCoordinate);
        Assert.Equal(new HexCoord(1, 0), grazing.OpenCoordinate);
        Assert.Same(planet, Assert.Single(grazing.Blockers).MapObject);
    }

    [Fact]
    public void BoundaryLineIsClearWhenNeitherSideContainsBlocker()
    {
        SystemMap map = SystemMap.Create(2);

        DirectFireLineOfSightResult result = DirectFireLineOfSight.Evaluate(
            map,
            HexCoord.Zero,
            new HexCoord(2, -1));

        Assert.True(result.IsClear);
        Assert.Equal(
            new[] { new HexCoord(1, 0), new HexCoord(1, -1) },
            result.TestedCells);
    }

    [Fact]
    public void BoundaryLineIsBlockedWhenBothSidesContainBlockers()
    {
        SystemMap map = SystemMap.Create(2);
        MapObject first = MapObject.CreatePlanet("planet-a", "World A");
        MapObject second = MapObject.CreatePlanet("planet-b", "World B");
        map.Place(first, new HexCoord(1, 0));
        map.Place(second, new HexCoord(1, -1));

        DirectFireLineOfSightResult result = DirectFireLineOfSight.Evaluate(
            map,
            HexCoord.Zero,
            new HexCoord(2, -1));

        Assert.True(result.IsBlocked);
        Assert.False(result.HasLineOfSight);
        Assert.Empty(result.Grazings);
        Assert.Equal(2, result.Blockers.Count);
        Assert.NotNull(result.Blockage);
        Assert.True(result.Blockage!.IsBoundaryPinch);
        Assert.Contains(result.Blockers, blocker => blocker.MapObject == first);
        Assert.Contains(result.Blockers, blocker => blocker.MapObject == second);
    }

    [Fact]
    public void MoreDistantBlockersAreOmittedAfterNearestObstruction()
    {
        SystemMap map = SystemMap.Create(4);
        MapObject near = MapObject.CreatePlanet("near", "Near World");
        MapObject far = MapObject.CreatePlanet("far", "Far World");
        map.Place(near, new HexCoord(1, 0));
        map.Place(far, new HexCoord(3, 0));

        DirectFireLineOfSightResult result = DirectFireLineOfSight.Evaluate(
            map,
            HexCoord.Zero,
            new HexCoord(4, 0));

        LineOfSightBlocker blocker = Assert.Single(result.Blockers);
        Assert.Same(near, blocker.MapObject);
        Assert.DoesNotContain(result.Blockers, item => item.MapObject == far);
    }

    [Fact]
    public void OriginOutsideMapIsRejected()
    {
        SystemMap map = SystemMap.Create(2);

        Assert.Throws<ArgumentOutOfRangeException>(
            () => DirectFireLineOfSight.Evaluate(
                map,
                new HexCoord(3, 0),
                HexCoord.Zero));
    }

    [Fact]
    public void TargetOutsideMapIsRejected()
    {
        SystemMap map = SystemMap.Create(2);

        Assert.Throws<ArgumentOutOfRangeException>(
            () => DirectFireLineOfSight.Evaluate(
                map,
                HexCoord.Zero,
                new HexCoord(3, 0)));
    }

    [Fact]
    public void SameOriginAndTargetAreRejected()
    {
        SystemMap map = SystemMap.Create(2);

        Assert.Throws<ArgumentException>(
            () => DirectFireLineOfSight.Evaluate(
                map,
                HexCoord.Zero,
                HexCoord.Zero));
    }

    [Fact]
    public void NullMapIsRejected()
    {
        Assert.Throws<ArgumentNullException>(
            () => DirectFireLineOfSight.Evaluate(
                null!,
                HexCoord.Zero,
                new HexCoord(1, 0)));
    }

    [Fact]
    public void TestedCellsNeverIncludeOriginOrTarget()
    {
        SystemMap map = SystemMap.Create(3);
        var origin = new HexCoord(-2, 1);
        var target = new HexCoord(2, -1);

        DirectFireLineOfSightResult result = DirectFireLineOfSight.Evaluate(
            map,
            origin,
            target);

        Assert.DoesNotContain(origin, result.TestedCells);
        Assert.DoesNotContain(target, result.TestedCells);
    }

    [Fact]
    public void ResultPreservesRequestedEndpoints()
    {
        SystemMap map = SystemMap.Create(3);
        var origin = new HexCoord(-2, 1);
        var target = new HexCoord(2, -1);

        DirectFireLineOfSightResult result = DirectFireLineOfSight.Evaluate(
            map,
            origin,
            target);

        Assert.Equal(origin, result.Origin);
        Assert.Equal(target, result.Target);
    }

    [Fact]
    public void EqualRangeBoundaryBlockersUseStableCoordinateOrder()
    {
        SystemMap map = SystemMap.Create(2);
        map.Place(
            MapObject.CreatePlanet("planet-a", "World A"),
            new HexCoord(1, 0));
        map.Place(
            MapObject.CreatePlanet("planet-b", "World B"),
            new HexCoord(1, -1));

        DirectFireLineOfSightResult result = DirectFireLineOfSight.Evaluate(
            map,
            HexCoord.Zero,
            new HexCoord(2, -1));

        Assert.Equal(
            new[] { new HexCoord(1, -1), new HexCoord(1, 0) },
            result.Blockers.Select(blocker => blocker.Coordinate));
    }

    [Fact]
    public void MultipleBoundaryGrazingsAreAccumulated()
    {
        SystemMap map = SystemMap.Create(4);
        MapObject near = MapObject.CreatePlanet("near", "Near World");
        MapObject far = MapObject.CreatePlanet("far", "Far World");
        map.Place(near, new HexCoord(1, 0));
        map.Place(far, new HexCoord(3, -2));

        DirectFireLineOfSightResult result = DirectFireLineOfSight.Evaluate(
            map,
            HexCoord.Zero,
            new HexCoord(4, -2));

        Assert.True(result.IsGrazing);
        Assert.Equal(2, result.GrazingCount);
        Assert.Equal(new[] { 1, 3 }, result.Grazings.Select(item => item.RangeStep));
        Assert.Same(near, Assert.Single(result.Grazings[0].Blockers).MapObject);
        Assert.Same(far, Assert.Single(result.Grazings[1].Blockers).MapObject);
    }

    [Fact]
    public void DirectBlockageAfterGrazingPreservesEarlierGrazing()
    {
        SystemMap map = SystemMap.Create(4);
        MapObject grazingPlanet = MapObject.CreatePlanet("graze", "Grazing World");
        MapObject blockingPlanet = MapObject.CreatePlanet("block", "Blocking World");
        map.Place(grazingPlanet, new HexCoord(1, 0));
        map.Place(blockingPlanet, new HexCoord(2, -1));

        DirectFireLineOfSightResult result = DirectFireLineOfSight.Evaluate(
            map,
            HexCoord.Zero,
            new HexCoord(4, -2));

        Assert.True(result.IsBlocked);
        Assert.Equal(1, result.GrazingCount);
        Assert.Same(grazingPlanet, Assert.Single(result.Grazings[0].Blockers).MapObject);
        Assert.Same(blockingPlanet, Assert.Single(result.Blockers).MapObject);
        Assert.Equal(2, result.Blockage!.RangeStep);
    }

    [Fact]
    public void DirectBlockageStopsEvaluationBeforeLaterGrazing()
    {
        SystemMap map = SystemMap.Create(4);
        MapObject blockingPlanet = MapObject.CreatePlanet("block", "Blocking World");
        MapObject laterPlanet = MapObject.CreatePlanet("later", "Later World");
        map.Place(blockingPlanet, new HexCoord(2, -1));
        map.Place(laterPlanet, new HexCoord(3, -2));

        DirectFireLineOfSightResult result = DirectFireLineOfSight.Evaluate(
            map,
            HexCoord.Zero,
            new HexCoord(4, -2));

        Assert.True(result.IsBlocked);
        Assert.Empty(result.Grazings);
        Assert.Same(blockingPlanet, Assert.Single(result.Blockers).MapObject);
    }

    [Fact]
    public void GrazingQualityIsSymmetricWhenTraceIsReversed()
    {
        SystemMap map = SystemMap.Create(4);
        map.Place(
            MapObject.CreatePlanet("near", "Near World"),
            new HexCoord(1, 0));
        map.Place(
            MapObject.CreatePlanet("far", "Far World"),
            new HexCoord(3, -2));

        DirectFireLineOfSightResult forward = DirectFireLineOfSight.Evaluate(
            map,
            HexCoord.Zero,
            new HexCoord(4, -2));
        DirectFireLineOfSightResult reverse = DirectFireLineOfSight.Evaluate(
            map,
            new HexCoord(4, -2),
            HexCoord.Zero);

        Assert.Equal(LineOfSightQuality.Grazing, forward.Quality);
        Assert.Equal(forward.Quality, reverse.Quality);
        Assert.Equal(forward.GrazingCount, reverse.GrazingCount);
    }

    [Fact]
    public void BoundaryPinchQualityIsSymmetricWhenTraceIsReversed()
    {
        SystemMap map = SystemMap.Create(2);
        map.Place(
            MapObject.CreatePlanet("a", "World A"),
            new HexCoord(1, 0));
        map.Place(
            MapObject.CreatePlanet("b", "World B"),
            new HexCoord(1, -1));

        DirectFireLineOfSightResult forward = DirectFireLineOfSight.Evaluate(
            map,
            HexCoord.Zero,
            new HexCoord(2, -1));
        DirectFireLineOfSightResult reverse = DirectFireLineOfSight.Evaluate(
            map,
            new HexCoord(2, -1),
            HexCoord.Zero);

        Assert.True(forward.IsBlocked);
        Assert.True(reverse.IsBlocked);
        Assert.True(forward.Blockage!.IsBoundaryPinch);
        Assert.True(reverse.Blockage!.IsBoundaryPinch);
    }

    [Fact]
    public void GrazingStarBehavesLikeGrazingPlanet()
    {
        MapObject star = MapObject.CreateStar("star", "Primary");
        SystemMap map = SystemMap.Create(3, star);

        DirectFireLineOfSightResult result = DirectFireLineOfSight.Evaluate(
            map,
            new HexCoord(-1, 0),
            new HexCoord(1, -1));

        Assert.True(result.IsGrazing);
        Assert.Same(star, Assert.Single(result.Grazings[0].Blockers).MapObject);
    }

    [Fact]
    public void GrazingResultHasNoCompleteBlockers()
    {
        SystemMap map = SystemMap.Create(2);
        map.Place(
            MapObject.CreatePlanet("planet", "World"),
            new HexCoord(1, 0));

        DirectFireLineOfSightResult result = DirectFireLineOfSight.Evaluate(
            map,
            HexCoord.Zero,
            new HexCoord(2, -1));

        Assert.True(result.IsGrazing);
        Assert.Empty(result.Blockers);
        Assert.Null(result.Blockage);
    }

    [Fact]
    public void ClearResultReportsZeroGrazingCount()
    {
        SystemMap map = SystemMap.Create(3);

        DirectFireLineOfSightResult result = DirectFireLineOfSight.Evaluate(
            map,
            new HexCoord(-2, 0),
            new HexCoord(2, 0));

        Assert.Equal(0, result.GrazingCount);
        Assert.False(result.IsGrazing);
        Assert.False(result.IsBlocked);
    }

    [Fact]
    public void BlockedResultDoesNotReportLineOfSight()
    {
        SystemMap map = SystemMap.Create(3);
        map.Place(MapObject.CreatePlanet("planet", "World"), HexCoord.Zero);

        DirectFireLineOfSightResult result = DirectFireLineOfSight.Evaluate(
            map,
            new HexCoord(-2, 0),
            new HexCoord(2, 0));

        Assert.False(result.HasLineOfSight);
        Assert.False(result.IsClear);
        Assert.False(result.IsGrazing);
    }
}
