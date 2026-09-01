using System;
using System.Collections.Generic;
using System.Linq;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;

namespace StarCluster.Core.Movement;

/// <summary>
/// Owns turn-scoped ship movement allowance, destination planning, one-hex
/// commitment, and early movement completion.
/// </summary>
public static class ShipMovementTurnService
{
    public static ShipMovementTurnState Begin(
        HexCoord startingCoordinate,
        SublightMovementProfile profile)
    {
        ArgumentNullException.ThrowIfNull(profile);
        return new ShipMovementTurnState(
            profile.MaximumHexesPerTurn,
            new[] { startingCoordinate },
            isComplete: false);
    }

    public static ShipMovementResult PlanDestination(
        SystemMap map,
        ShipMovementTurnState state,
        HexCoord destination)
    {
        ArgumentNullException.ThrowIfNull(map);
        ArgumentNullException.ThrowIfNull(state);
        return ShipMovementPlanner.FindRoute(
            map,
            state.CurrentCoordinate,
            destination,
            state.RemainingDistance);
    }

    public static IReadOnlyList<HexCoord> FindLegalDestinations(
        SystemMap map,
        ShipMovementTurnState state)
    {
        ArgumentNullException.ThrowIfNull(map);
        ArgumentNullException.ThrowIfNull(state);

        if (state.IsComplete)
        {
            return Array.AsReadOnly(new[] { state.CurrentCoordinate });
        }

        return ShipMovementPlanner.FindLegalDestinations(
            map,
            state.CurrentCoordinate,
            state.RemainingDistance);
    }

    public static ShipMovementStepExecutionResult ExecuteStep(
        SystemMap map,
        string shipId,
        ShipMovementTurnState state,
        HexCoord destination)
    {
        ArgumentNullException.ThrowIfNull(map);
        ArgumentException.ThrowIfNullOrWhiteSpace(shipId);
        ArgumentNullException.ThrowIfNull(state);

        HexCoord origin = state.CurrentCoordinate;
        ValidateShipAtOrigin(map, shipId, origin);

        if (state.IsComplete || state.RemainingDistance == 0)
        {
            return new ShipMovementStepExecutionResult(
                ShipMovementStepExecutionStatus.RejectedMovementComplete,
                state,
                origin,
                origin,
                plan: null);
        }

        if (origin.DistanceTo(destination) != 1)
        {
            return new ShipMovementStepExecutionResult(
                ShipMovementStepExecutionStatus.RejectedNotAdjacent,
                state,
                origin,
                origin,
                plan: null);
        }

        ShipMovementResult plan = ShipMovementPlanner.FindRoute(
            map,
            origin,
            destination,
            maximumDistance: 1);
        if (!plan.CanMove)
        {
            return new ShipMovementStepExecutionResult(
                ShipMovementStepExecutionStatus.RejectedIllegalDestination,
                state,
                origin,
                origin,
                plan);
        }

        map.Move(shipId, destination);
        ShipMovementTurnState updatedState = state.CommitStep(destination);

        return new ShipMovementStepExecutionResult(
            ShipMovementStepExecutionStatus.Moved,
            updatedState,
            origin,
            destination,
            plan);
    }

    public static ShipMovementTurnState EndMovement(
        ShipMovementTurnState state)
    {
        ArgumentNullException.ThrowIfNull(state);
        return state.Complete();
    }

    private static void ValidateShipAtOrigin(
        SystemMap map,
        string shipId,
        HexCoord origin)
    {
        bool shipAtOrigin = map.GetCell(origin).Occupants.Any(
            item => item.Kind == MapObjectKind.Ship &&
                string.Equals(item.Id, shipId, StringComparison.Ordinal));

        if (!shipAtOrigin)
        {
            throw new InvalidOperationException(
                $"Ship '{shipId}' is not present at the movement state's current coordinate {origin}.");
        }
    }
}
