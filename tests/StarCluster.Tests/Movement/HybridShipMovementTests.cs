using System.Linq;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;
using StarCluster.Core.Movement;
using Xunit;

namespace StarCluster.Tests.Movement;

public sealed class HybridShipMovementTests
{
    [Fact]
    public void BeginStoresAllowanceAndStartingCoordinate()
    {
        var profile = new SublightMovementProfile(4, 3);
        var start = new HexCoord(-2, 0);

        ShipMovementTurnState state = ShipMovementTurnService.Begin(start, profile);

        Assert.Equal(start, state.StartingCoordinate);
        Assert.Equal(start, state.CurrentCoordinate);
        Assert.Equal(3, state.MaximumDistance);
        Assert.Equal(3, state.RemainingDistance);
        Assert.Equal(0, state.DistanceSpent);
        Assert.False(state.IsComplete);
        Assert.Single(state.ExecutedPath);
    }

    [Fact]
    public void OneHexStepCommitsAndDecrementsRemainingAllowance()
    {
        (SystemMap map, HexCoord start) = CreateMapWithPlayer();
        ShipMovementTurnState state = Begin(start, allowance: 3);
        var destination = new HexCoord(-2, 0);

        ShipMovementStepExecutionResult result = ShipMovementTurnService.ExecuteStep(
            map,
            PlayerId,
            state,
            destination);

        Assert.True(result.WasCommitted);
        Assert.Equal(ShipMovementStepExecutionStatus.Moved, result.Status);
        Assert.Equal(destination, result.State.CurrentCoordinate);
        Assert.Equal(1, result.State.DistanceSpent);
        Assert.Equal(2, result.State.RemainingDistance);
        Assert.Contains(map.GetCell(destination).Occupants, item => item.Id == PlayerId);
    }

    [Fact]
    public void NonAdjacentStepIsRejectedWithoutMovingShip()
    {
        (SystemMap map, HexCoord start) = CreateMapWithPlayer();
        ShipMovementTurnState state = Begin(start, allowance: 3);
        var destination = new HexCoord(0, 0);

        ShipMovementStepExecutionResult result = ShipMovementTurnService.ExecuteStep(
            map,
            PlayerId,
            state,
            destination);

        Assert.Equal(ShipMovementStepExecutionStatus.RejectedNotAdjacent, result.Status);
        Assert.False(result.WasCommitted);
        Assert.Equal(start, result.State.CurrentCoordinate);
        Assert.Contains(map.GetCell(start).Occupants, item => item.Id == PlayerId);
    }

    [Fact]
    public void OccupiedAdjacentStepIsRejectedWithoutSpendingMovement()
    {
        (SystemMap map, HexCoord start) = CreateMapWithPlayer();
        ShipMovementTurnState state = Begin(start, allowance: 3);
        var destination = new HexCoord(-2, 0);
        map.Place(MapObject.CreatePlanet("planet", "Planet"), destination);

        ShipMovementStepExecutionResult result = ShipMovementTurnService.ExecuteStep(
            map,
            PlayerId,
            state,
            destination);

        Assert.Equal(
            ShipMovementStepExecutionStatus.RejectedIllegalDestination,
            result.Status);
        Assert.Equal(3, result.State.RemainingDistance);
        Assert.Equal(start, result.State.CurrentCoordinate);
    }

    [Fact]
    public void ExecutedPathRecordsEveryEnteredHex()
    {
        (SystemMap map, HexCoord start) = CreateMapWithPlayer();
        ShipMovementTurnState state = Begin(start, allowance: 3);

        state = Move(map, state, new HexCoord(-2, 0));
        state = Move(map, state, new HexCoord(-1, 0));

        Assert.Equal(
            new[] { start, new HexCoord(-2, 0), new HexCoord(-1, 0) },
            state.ExecutedPath);
    }

    [Fact]
    public void ExhaustingAllowanceCompletesMovementAutomatically()
    {
        (SystemMap map, HexCoord start) = CreateMapWithPlayer();
        ShipMovementTurnState state = Begin(start, allowance: 2);

        state = Move(map, state, new HexCoord(-2, 0));
        state = Move(map, state, new HexCoord(-1, 0));

        Assert.True(state.IsComplete);
        Assert.Equal(0, state.RemainingDistance);

        ShipMovementStepExecutionResult rejected = ShipMovementTurnService.ExecuteStep(
            map,
            PlayerId,
            state,
            new HexCoord(0, -1));
        Assert.Equal(
            ShipMovementStepExecutionStatus.RejectedMovementComplete,
            rejected.Status);
    }

    [Fact]
    public void EndMovementCompletesEarlyWithoutChangingCoordinate()
    {
        (SystemMap map, HexCoord start) = CreateMapWithPlayer();
        ShipMovementTurnState state = Begin(start, allowance: 3);
        state = Move(map, state, new HexCoord(-2, 0));

        ShipMovementTurnState completed = ShipMovementTurnService.EndMovement(state);

        Assert.True(completed.IsComplete);
        Assert.Equal(new HexCoord(-2, 0), completed.CurrentCoordinate);
        Assert.Equal(2, completed.RemainingDistance);

        ShipMovementStepExecutionResult rejected = ShipMovementTurnService.ExecuteStep(
            map,
            PlayerId,
            completed,
            new HexCoord(-1, 0));
        Assert.Equal(
            ShipMovementStepExecutionStatus.RejectedMovementComplete,
            rejected.Status);
    }

    [Fact]
    public void DistantDestinationCanBePlannedAfterManualSidestep()
    {
        (SystemMap map, HexCoord start) = CreateMapWithPlayer(radius: 4);
        ShipMovementTurnState state = Begin(start, allowance: 3);
        state = Move(map, state, new HexCoord(-4, 1));
        var finalDestination = new HexCoord(-2, 0);

        ShipMovementResult plan = ShipMovementTurnService.PlanDestination(
            map,
            state,
            finalDestination);

        Assert.True(plan.CanMove);
        Assert.Equal(2, state.RemainingDistance);
        Assert.Equal(2, plan.RoutedDistance);
        Assert.Equal(state.CurrentCoordinate, plan.Path![0]);
        Assert.Equal(finalDestination, plan.Path[^1]);
    }

    [Fact]
    public void RemainingLegalDestinationsAreRecomputedFromCurrentCoordinate()
    {
        (SystemMap map, HexCoord start) = CreateMapWithPlayer(radius: 3);
        ShipMovementTurnState state = Begin(start, allowance: 2);
        state = Move(map, state, new HexCoord(-3, 1));

        var legal = ShipMovementTurnService.FindLegalDestinations(map, state);

        Assert.Contains(state.CurrentCoordinate, legal);
        Assert.All(
            legal,
            coordinate => Assert.True(state.CurrentCoordinate.DistanceTo(coordinate) <= 1));
        Assert.DoesNotContain(new HexCoord(-1, 0), legal);
    }

    [Fact]
    public void PlannedDestinationCanBeExecutedAsAuthoritativeSteps()
    {
        (SystemMap map, HexCoord start) = CreateMapWithPlayer(radius: 4);
        ShipMovementTurnState state = Begin(start, allowance: 3);
        var destination = new HexCoord(-1, 0);
        ShipMovementResult plan = ShipMovementTurnService.PlanDestination(
            map,
            state,
            destination);

        foreach (HexCoord next in plan.Path!.Skip(1))
        {
            state = Move(map, state, next);
        }

        Assert.Equal(destination, state.CurrentCoordinate);
        Assert.Equal(plan.RoutedDistance!.Value, state.DistanceSpent);
        Assert.Equal(plan.Path!.ToArray(), state.ExecutedPath.ToArray());
    }

    [Fact]
    public void PlannerRetainsOverRemainingRouteForPreview()
    {
        (SystemMap map, HexCoord start) = CreateMapWithPlayer(radius: 4);
        ShipMovementTurnState state = Begin(start, allowance: 2);
        state = Move(map, state, new HexCoord(-4, 1));

        ShipMovementResult plan = ShipMovementTurnService.PlanDestination(
            map,
            state,
            new HexCoord(0, -1));

        Assert.Equal(ShipMovementStatus.OutOfRange, plan.Status);
        Assert.True(plan.HasRoute);
        Assert.Equal(1, plan.MaximumDistance);
    }

    [Fact]
    public void CompletedMovementOffersOnlyCurrentCoordinate()
    {
        (SystemMap map, HexCoord start) = CreateMapWithPlayer();
        ShipMovementTurnState state = ShipMovementTurnService.EndMovement(
            Begin(start, allowance: 3));

        var legal = ShipMovementTurnService.FindLegalDestinations(map, state);

        Assert.Single(legal);
        Assert.Equal(start, legal[0]);
    }

    private static ShipMovementTurnState Begin(HexCoord start, int allowance) =>
        ShipMovementTurnService.Begin(
            start,
            new SublightMovementProfile(4, allowance));

    private static ShipMovementTurnState Move(
        SystemMap map,
        ShipMovementTurnState state,
        HexCoord destination)
    {
        ShipMovementStepExecutionResult result = ShipMovementTurnService.ExecuteStep(
            map,
            PlayerId,
            state,
            destination);
        Assert.True(result.WasCommitted);
        return result.State;
    }

    private static (SystemMap Map, HexCoord PlayerPosition) CreateMapWithPlayer(
        int radius = 3)
    {
        SystemMap map = SystemMap.Create(
            radius,
            MapObject.CreateStar("star", "Primary Star"));
        var start = new HexCoord(-radius, 0);
        map.Place(MapObject.CreateShip(PlayerId, "Player Ship"), start);
        return (map, start);
    }

    private const string PlayerId = "ship-player";
}
