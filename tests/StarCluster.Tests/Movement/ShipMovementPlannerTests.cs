using System;
using System.Linq;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;
using StarCluster.Core.Movement;
using Xunit;

namespace StarCluster.Tests.Movement;

public sealed class ShipMovementPlannerTests
{
    [Fact]
    public void HoldPositionIsAZeroDistanceFoundRoute()
    {
        (SystemMap map, HexCoord origin) = CreateMapWithPlayer();

        ShipMovementResult result = ShipMovementPlanner.FindRoute(map, origin, origin, 0);

        Assert.Equal(ShipMovementStatus.Found, result.Status);
        Assert.True(result.IsHold);
        Assert.Equal(0, result.RoutedDistance);
        Assert.Single(result.Path!);
    }

    [Fact]
    public void OpenDestinationWithinAllowanceIsFound()
    {
        (SystemMap map, HexCoord origin) = CreateMapWithPlayer();
        var destination = new HexCoord(-1, 1);

        ShipMovementResult result = ShipMovementPlanner.FindRoute(map, origin, destination, 2);

        Assert.Equal(ShipMovementStatus.Found, result.Status);
        Assert.True(result.CanMove);
        Assert.Equal(origin, result.Path![0]);
        Assert.Equal(destination, result.Path[^1]);
    }

    [Fact]
    public void RouteUsesAdjacentCellsOnly()
    {
        (SystemMap map, HexCoord origin) = CreateMapWithPlayer(radius: 3);
        var destination = new HexCoord(2, -1);

        ShipMovementResult result = ShipMovementPlanner.FindRoute(map, origin, destination, 8);

        Assert.NotNull(result.Path);
        Assert.All(
            result.Path!.Zip(result.Path.Skip(1)),
            pair => Assert.Equal(1, pair.First.DistanceTo(pair.Second)));
    }

    [Fact]
    public void StarIsAvoidedAsAnIntermediateCell()
    {
        (SystemMap map, HexCoord origin) = CreateMapWithPlayer(radius: 3);
        var destination = new HexCoord(2, 0);

        ShipMovementResult result = ShipMovementPlanner.FindRoute(map, origin, destination, 8);

        Assert.Equal(ShipMovementStatus.Found, result.Status);
        Assert.DoesNotContain(new HexCoord(0, 0), result.Path!);
        Assert.True(result.RoutedDistance > result.DirectDistance);
    }

    [Fact]
    public void PlanetIsAvoidedAsAnIntermediateCell()
    {
        (SystemMap map, HexCoord origin) = CreateMapWithPlayer(radius: 3);
        var blocker = new HexCoord(-1, 0);
        var destination = new HexCoord(1, 0);
        map.Place(MapObject.CreatePlanet("planet-blocker", "Blocker"), blocker);

        ShipMovementResult result = ShipMovementPlanner.FindRoute(map, origin, destination, 8);

        Assert.Equal(ShipMovementStatus.Found, result.Status);
        Assert.DoesNotContain(blocker, result.Path!);
    }

    [Fact]
    public void ShipOccupiedDestinationIsRejected()
    {
        (SystemMap map, HexCoord origin) = CreateMapWithPlayer();
        var destination = new HexCoord(-1, 1);
        map.Place(MapObject.CreateShip("ship-other", "Other Ship"), destination);

        ShipMovementResult result = ShipMovementPlanner.FindRoute(map, origin, destination, 2);

        Assert.Equal(ShipMovementStatus.Occupied, result.Status);
        Assert.False(result.HasRoute);
    }

    [Fact]
    public void StationOccupiedDestinationIsRejected()
    {
        (SystemMap map, HexCoord origin) = CreateMapWithPlayer();
        var destination = new HexCoord(-1, 1);
        map.Place(MapObject.CreateStation("station", "Station"), destination);

        ShipMovementResult result = ShipMovementPlanner.FindRoute(map, origin, destination, 2);

        Assert.Equal(ShipMovementStatus.Occupied, result.Status);
    }

    [Fact]
    public void AnomalyDoesNotBlockMovement()
    {
        (SystemMap map, HexCoord origin) = CreateMapWithPlayer();
        var destination = new HexCoord(-1, 1);
        map.Place(MapObject.CreateAnomaly("anomaly", "Anomaly"), destination);

        ShipMovementResult result = ShipMovementPlanner.FindRoute(map, origin, destination, 2);

        Assert.Equal(ShipMovementStatus.Found, result.Status);
    }

    [Fact]
    public void OverAllowanceRouteIsRetainedForPreview()
    {
        (SystemMap map, HexCoord origin) = CreateMapWithPlayer(radius: 3);
        var destination = new HexCoord(2, -1);

        ShipMovementResult result = ShipMovementPlanner.FindRoute(map, origin, destination, 1);

        Assert.Equal(ShipMovementStatus.OutOfRange, result.Status);
        Assert.True(result.HasRoute);
        Assert.True(result.RoutedDistance > result.MaximumDistance);
    }

    [Fact]
    public void EnclosedDestinationReportsNoRoute()
    {
        (SystemMap map, HexCoord origin) = CreateMapWithPlayer(radius: 3);
        var destination = new HexCoord(1, 0);
        int blockerNumber = 0;

        foreach (HexCoord neighbor in destination.Neighbors())
        {
            if (!map.Geometry.Contains(neighbor) || neighbor == new HexCoord(0, 0))
            {
                continue;
            }

            map.Place(
                MapObject.CreatePlanet($"planet-{blockerNumber}", $"Blocker {blockerNumber}"),
                neighbor);
            blockerNumber++;
        }

        ShipMovementResult result = ShipMovementPlanner.FindRoute(map, origin, destination, 9);

        Assert.Equal(ShipMovementStatus.NoRoute, result.Status);
        Assert.False(result.HasRoute);
    }

    [Fact]
    public void LegalDestinationsIncludeHoldAndReachableCells()
    {
        (SystemMap map, HexCoord origin) = CreateMapWithPlayer();

        var destinations = ShipMovementPlanner.FindLegalDestinations(map, origin, 1);

        Assert.Contains(origin, destinations);
        Assert.Contains(new HexCoord(-1, 0), destinations);
        Assert.All(destinations, item => Assert.True(origin.DistanceTo(item) <= 1));
    }

    [Fact]
    public void LegalDestinationsExcludeSolidOccupiedCells()
    {
        (SystemMap map, HexCoord origin) = CreateMapWithPlayer();
        var occupied = new HexCoord(-1, 0);
        map.Place(MapObject.CreatePlanet("planet", "Planet"), occupied);

        var destinations = ShipMovementPlanner.FindLegalDestinations(map, origin, 1);

        Assert.DoesNotContain(occupied, destinations);
    }

    [Fact]
    public void MovementServiceCommitsThePlannedMove()
    {
        (SystemMap map, HexCoord origin) = CreateMapWithPlayer();
        var destination = new HexCoord(-1, 1);
        var profile = new SublightMovementProfile(3, 2);

        ShipMovementExecutionResult result = ShipMovementService.Execute(
            map,
            PlayerId,
            origin,
            destination,
            profile);

        Assert.Equal(ShipMovementExecutionStatus.Moved, result.Status);
        Assert.Equal(destination, result.FinalCoordinate);
        Assert.DoesNotContain(map.GetCell(origin).Occupants, item => item.Id == PlayerId);
        Assert.Contains(map.GetCell(destination).Occupants, item => item.Id == PlayerId);
    }

    private static (SystemMap Map, HexCoord PlayerPosition) CreateMapWithPlayer(int radius = 2)
    {
        SystemMap map = SystemMap.Create(
            radius,
            MapObject.CreateStar("star", "Primary Star"));
        var origin = new HexCoord(-radius, 0);
        map.Place(MapObject.CreateShip(PlayerId, "Player Ship"), origin);
        return (map, origin);
    }

    private const string PlayerId = "ship-player";
}
