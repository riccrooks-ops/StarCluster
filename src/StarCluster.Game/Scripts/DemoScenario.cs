using System;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;
using StarCluster.Core.Movement;

namespace StarCluster.Game;

/// <summary>
/// Holds one repeatable system-map arrangement used to exercise the
/// presentation layer. The logical map remains authoritative; Godot only
/// previews commands and displays committed results.
/// </summary>
public sealed class DemoScenario
{
    public DemoScenario(
        string name,
        string description,
        SystemMap map,
        string playerShipId,
        string enemyShipId,
        HexCoord playerPosition,
        HexCoord enemyPosition)
    {
        Name = name;
        Description = description;
        Map = map;
        PlayerShipId = playerShipId;
        EnemyShipId = enemyShipId;
        PlayerPosition = playerPosition;
        EnemyPosition = enemyPosition;
    }

    public string Name { get; }

    public string Description { get; }

    public SystemMap Map { get; }

    public string PlayerShipId { get; }

    public string EnemyShipId { get; }

    public HexCoord PlayerPosition { get; private set; }

    public HexCoord EnemyPosition { get; private set; }


    public ShipMovementStepExecutionResult MovePlayerShipOneHex(
        HexCoord destination,
        ShipMovementTurnState state)
    {
        ArgumentNullException.ThrowIfNull(state);

        ShipMovementStepExecutionResult result =
            ShipMovementTurnService.ExecuteStep(
                Map,
                PlayerShipId,
                state,
                destination);

        if (result.WasCommitted)
        {
            PlayerPosition = result.CoordinateAfter;
        }

        return result;
    }

    public ShipMovementExecutionResult MovePlayerShip(
        HexCoord destination,
        SublightMovementProfile profile)
    {
        ArgumentNullException.ThrowIfNull(profile);

        ShipMovementExecutionResult result = ShipMovementService.Execute(
            Map,
            PlayerShipId,
            PlayerPosition,
            destination,
            profile);

        if (result.WasCommitted)
        {
            PlayerPosition = result.FinalCoordinate;
        }

        return result;
    }
}
