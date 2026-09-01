using System;
using System.Collections.Generic;
using System.Linq;
using StarCluster.Core.Combat.Missiles;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;
using Xunit;

namespace StarCluster.Tests.Combat.Missiles;

public sealed class MissileRoutePlannerTests
{
    [Fact]
    public void EmptyMapUsesDirectShortestRoute()
    {
        SystemMap map = SystemMap.Create(4);
        var origin = new HexCoord(-2, 0);
        var target = new HexCoord(2, 0);

        MissileRouteResult result = MissileRoutePlanner.FindRoute(
            map,
            origin,
            target,
            maximumRange: 4);

        Assert.Equal(MissileRouteStatus.Found, result.Status);
        Assert.True(result.CanLaunch);
        Assert.True(result.HasRoute);
        Assert.Equal(4, result.DirectDistance);
        Assert.Equal(4, result.RoutedDistance);
        Assert.Equal(origin, result.Path[0]);
        Assert.Equal(target, result.Path[^1]);
    }

    [Fact]
    public void DirectRouteIncludesEveryExpectedCell()
    {
        SystemMap map = SystemMap.Create(3);

        MissileRouteResult result = MissileRoutePlanner.FindRoute(
            map,
            new HexCoord(-2, 0),
            new HexCoord(2, 0),
            maximumRange: 10);

        Assert.Equal(
            new[]
            {
                new HexCoord(-2, 0),
                new HexCoord(-1, 0),
                HexCoord.Zero,
                new HexCoord(1, 0),
                new HexCoord(2, 0),
            },
            result.Path);
    }

    [Fact]
    public void ConsecutiveRouteCellsAreAdjacent()
    {
        MapObject star = MapObject.CreateStar("star", "Primary");
        SystemMap map = SystemMap.Create(4, star);

        MissileRouteResult result = MissileRoutePlanner.FindRoute(
            map,
            new HexCoord(-3, 0),
            new HexCoord(3, 0),
            maximumRange: 10);

        Assert.True(result.HasRoute);

        for (int index = 1; index < result.Path.Count; index++)
        {
            Assert.Equal(1, result.Path[index - 1].DistanceTo(result.Path[index]));
        }
    }

    [Fact]
    public void RepeatedPlanningIsDeterministic()
    {
        SystemMap map = SystemMap.Create(
            4,
            MapObject.CreateStar("star", "Primary"));
        var origin = new HexCoord(-3, 0);
        var target = new HexCoord(3, 0);

        MissileRouteResult first = MissileRoutePlanner.FindRoute(
            map,
            origin,
            target,
            maximumRange: 10);
        MissileRouteResult second = MissileRoutePlanner.FindRoute(
            map,
            origin,
            target,
            maximumRange: 10);

        Assert.Equal(first.Path.ToArray(), second.Path.ToArray());
    }

    [Fact]
    public void CentralStarForcesDetour()
    {
        SystemMap map = SystemMap.Create(
            3,
            MapObject.CreateStar("star", "Primary"));

        MissileRouteResult result = MissileRoutePlanner.FindRoute(
            map,
            new HexCoord(-2, 0),
            new HexCoord(2, 0),
            maximumRange: 10);

        Assert.Equal(MissileRouteStatus.Found, result.Status);
        Assert.Equal(4, result.DirectDistance);
        Assert.Equal(5, result.RoutedDistance);
        Assert.DoesNotContain(HexCoord.Zero, result.Path.Skip(1).SkipLast(1));
    }

    [Fact]
    public void DetourDistanceCanExceedDirectDistance()
    {
        SystemMap map = SystemMap.Create(
            4,
            MapObject.CreateStar("star", "Primary"));

        MissileRouteResult result = MissileRoutePlanner.FindRoute(
            map,
            new HexCoord(-3, 0),
            new HexCoord(3, 0),
            maximumRange: 20);

        Assert.True(result.RoutedDistance!.Value > result.DirectDistance);
    }

    [Fact]
    public void PlanetForcesDetour()
    {
        SystemMap map = SystemMap.Create(3);
        map.Place(
            MapObject.CreatePlanet("planet", "World"),
            HexCoord.Zero);

        MissileRouteResult result = MissileRoutePlanner.FindRoute(
            map,
            new HexCoord(-2, 0),
            new HexCoord(2, 0),
            maximumRange: 10);

        Assert.True(result.CanLaunch);
        Assert.DoesNotContain(HexCoord.Zero, result.Path.Skip(1).SkipLast(1));
        Assert.Equal(5, result.RoutedDistance);
    }

    [Fact]
    public void ShipDoesNotBlockRoute()
    {
        SystemMap map = SystemMap.Create(3);
        map.Place(MapObject.CreateShip("ship", "Screen"), HexCoord.Zero);

        MissileRouteResult result = MissileRoutePlanner.FindRoute(
            map,
            new HexCoord(-2, 0),
            new HexCoord(2, 0),
            maximumRange: 4);

        Assert.True(result.CanLaunch);
        Assert.Contains(HexCoord.Zero, result.Path);
        Assert.Equal(4, result.RoutedDistance);
    }

    [Fact]
    public void StationDoesNotBlockRoute()
    {
        SystemMap map = SystemMap.Create(3);
        map.Place(MapObject.CreateStation("station", "Outpost"), HexCoord.Zero);

        MissileRouteResult result = MissileRoutePlanner.FindRoute(
            map,
            new HexCoord(-2, 0),
            new HexCoord(2, 0),
            maximumRange: 4);

        Assert.True(result.CanLaunch);
        Assert.Contains(HexCoord.Zero, result.Path);
    }

    [Fact]
    public void AnomalyDoesNotBlockRoute()
    {
        SystemMap map = SystemMap.Create(3);
        map.Place(MapObject.CreateAnomaly("anomaly", "Signal"), HexCoord.Zero);

        MissileRouteResult result = MissileRoutePlanner.FindRoute(
            map,
            new HexCoord(-2, 0),
            new HexCoord(2, 0),
            maximumRange: 4);

        Assert.True(result.CanLaunch);
        Assert.Contains(HexCoord.Zero, result.Path);
    }

    [Fact]
    public void WreckageDoesNotBlockRoute()
    {
        SystemMap map = SystemMap.Create(3);
        map.Place(MapObject.CreateWreckage("wreck", "Debris"), HexCoord.Zero);

        MissileRouteResult result = MissileRoutePlanner.FindRoute(
            map,
            new HexCoord(-2, 0),
            new HexCoord(2, 0),
            maximumRange: 4);

        Assert.True(result.CanLaunch);
        Assert.Contains(HexCoord.Zero, result.Path);
    }

    [Fact]
    public void TargetPlanetCellMayBeRouteEndpoint()
    {
        SystemMap map = SystemMap.Create(3);
        var target = new HexCoord(2, 0);
        map.Place(MapObject.CreatePlanet("planet", "Target World"), target);

        MissileRouteResult result = MissileRoutePlanner.FindRoute(
            map,
            HexCoord.Zero,
            target,
            maximumRange: 2);

        Assert.True(result.CanLaunch);
        Assert.Equal(target, result.Path[^1]);
        Assert.Equal(2, result.RoutedDistance);
    }

    [Fact]
    public void OriginPlanetCellMayBeRouteEndpoint()
    {
        SystemMap map = SystemMap.Create(3);
        var origin = new HexCoord(-2, 0);
        map.Place(MapObject.CreatePlanet("planet", "Launch World"), origin);

        MissileRouteResult result = MissileRoutePlanner.FindRoute(
            map,
            origin,
            HexCoord.Zero,
            maximumRange: 2);

        Assert.True(result.CanLaunch);
        Assert.Equal(origin, result.Path[0]);
    }

    [Fact]
    public void ExactMaximumRangeCanLaunch()
    {
        SystemMap map = SystemMap.Create(3);

        MissileRouteResult result = MissileRoutePlanner.FindRoute(
            map,
            new HexCoord(-2, 0),
            new HexCoord(2, 0),
            maximumRange: 4);

        Assert.Equal(MissileRouteStatus.Found, result.Status);
        Assert.True(result.CanLaunch);
    }

    [Fact]
    public void RouteBeyondMaximumRangeIsReported()
    {
        SystemMap map = SystemMap.Create(3);

        MissileRouteResult result = MissileRoutePlanner.FindRoute(
            map,
            new HexCoord(-2, 0),
            new HexCoord(2, 0),
            maximumRange: 3);

        Assert.Equal(MissileRouteStatus.OutOfRange, result.Status);
        Assert.False(result.CanLaunch);
        Assert.True(result.HasRoute);
        Assert.Equal(4, result.RoutedDistance);
    }

    [Fact]
    public void OutOfRangeResultRetainsShortestRoute()
    {
        SystemMap map = SystemMap.Create(
            3,
            MapObject.CreateStar("star", "Primary"));

        MissileRouteResult result = MissileRoutePlanner.FindRoute(
            map,
            new HexCoord(-2, 0),
            new HexCoord(2, 0),
            maximumRange: 4);

        Assert.Equal(MissileRouteStatus.OutOfRange, result.Status);
        Assert.NotNull(result.Route);
        Assert.Equal(5, result.Route!.Distance);
        Assert.Equal(6, result.Path.Count);
    }

    [Fact]
    public void NoRouteWhenOriginIsSurroundedByPlanets()
    {
        SystemMap map = SystemMap.Create(2);

        for (int direction = 0; direction < HexCoord.DirectionCount; direction++)
        {
            map.Place(
                MapObject.CreatePlanet($"planet-{direction}", $"World {direction}"),
                HexCoord.Zero.Neighbor(direction));
        }

        MissileRouteResult result = MissileRoutePlanner.FindRoute(
            map,
            HexCoord.Zero,
            new HexCoord(2, 0),
            maximumRange: 10);

        Assert.Equal(MissileRouteStatus.NoRoute, result.Status);
        Assert.False(result.CanLaunch);
        Assert.False(result.HasRoute);
        Assert.Null(result.Route);
        Assert.Null(result.RoutedDistance);
        Assert.Empty(result.Path);
    }

    [Fact]
    public void SameCellProducesZeroDistanceRoute()
    {
        SystemMap map = SystemMap.Create(2);
        var coordinate = new HexCoord(1, 0);

        MissileRouteResult result = MissileRoutePlanner.FindRoute(
            map,
            coordinate,
            coordinate,
            maximumRange: 0);

        Assert.Equal(MissileRouteStatus.Found, result.Status);
        Assert.Equal(0, result.DirectDistance);
        Assert.Equal(0, result.RoutedDistance);
        Assert.Equal(new[] { coordinate }, result.Path);
    }

    [Fact]
    public void NegativeMaximumRangeThrows()
    {
        SystemMap map = SystemMap.Create(2);

        Assert.Throws<ArgumentOutOfRangeException>(() =>
            MissileRoutePlanner.FindRoute(
                map,
                HexCoord.Zero,
                new HexCoord(1, 0),
                maximumRange: -1));
    }

    [Fact]
    public void OriginOutsideMapThrows()
    {
        SystemMap map = SystemMap.Create(2);

        Assert.Throws<ArgumentOutOfRangeException>(() =>
            MissileRoutePlanner.FindRoute(
                map,
                new HexCoord(3, 0),
                HexCoord.Zero,
                maximumRange: 10));
    }

    [Fact]
    public void TargetOutsideMapThrows()
    {
        SystemMap map = SystemMap.Create(2);

        Assert.Throws<ArgumentOutOfRangeException>(() =>
            MissileRoutePlanner.FindRoute(
                map,
                HexCoord.Zero,
                new HexCoord(3, 0),
                maximumRange: 10));
    }

    [Fact]
    public void RouteNeverEntersBlockingIntermediateCell()
    {
        SystemMap map = SystemMap.Create(
            4,
            MapObject.CreateStar("star", "Primary"));
        map.Place(
            MapObject.CreatePlanet("planet-a", "World A"),
            new HexCoord(0, 1));
        map.Place(
            MapObject.CreatePlanet("planet-b", "World B"),
            new HexCoord(1, -1));

        MissileRouteResult result = MissileRoutePlanner.FindRoute(
            map,
            new HexCoord(-3, 0),
            new HexCoord(3, 0),
            maximumRange: 20);

        Assert.True(result.HasRoute);

        foreach (HexCoord coordinate in result.Path.Skip(1).SkipLast(1))
        {
            Assert.DoesNotContain(
                map.GetCell(coordinate).Occupants,
                item => item.BlocksMissileTravel);
        }
    }

    [Fact]
    public void ReversedJourneyHasSameShortestDistance()
    {
        SystemMap map = SystemMap.Create(
            4,
            MapObject.CreateStar("star", "Primary"));
        var first = new HexCoord(-3, 0);
        var second = new HexCoord(3, 0);

        MissileRouteResult outbound = MissileRoutePlanner.FindRoute(
            map,
            first,
            second,
            maximumRange: 20);
        MissileRouteResult inbound = MissileRoutePlanner.FindRoute(
            map,
            second,
            first,
            maximumRange: 20);

        Assert.Equal(outbound.RoutedDistance, inbound.RoutedDistance);
    }

    [Fact]
    public void PlanningDoesNotModifyMapOccupants()
    {
        SystemMap map = SystemMap.Create(
            3,
            MapObject.CreateStar("star", "Primary"));
        MapObject ship = MapObject.CreateShip("ship", "Target");
        map.Place(ship, new HexCoord(2, 0));
        Dictionary<HexCoord, string[]> before = map.Cells.ToDictionary(
            cell => cell.Coordinate,
            cell => cell.Occupants.Select(item => item.Id).ToArray());

        MissileRoutePlanner.FindRoute(
            map,
            new HexCoord(-2, 0),
            new HexCoord(2, 0),
            maximumRange: 10);

        foreach (MapCell cell in map.Cells)
        {
            Assert.Equal(
                before[cell.Coordinate],
                cell.Occupants.Select(item => item.Id).ToArray());
        }
    }

    [Fact]
    public void ZeroMaximumRangeRejectsAdjacentRoute()
    {
        SystemMap map = SystemMap.Create(2);

        MissileRouteResult result = MissileRoutePlanner.FindRoute(
            map,
            HexCoord.Zero,
            new HexCoord(1, 0),
            maximumRange: 0);

        Assert.Equal(MissileRouteStatus.OutOfRange, result.Status);
        Assert.Equal(1, result.RoutedDistance);
    }
}
