using StarCluster.Core.Geometry;

namespace StarCluster.Core.Movement;

/// <summary>
/// Result of entering at most one adjacent tactical hex.
/// </summary>
public sealed class ShipMovementStepExecutionResult
{
    internal ShipMovementStepExecutionResult(
        ShipMovementStepExecutionStatus status,
        ShipMovementTurnState state,
        HexCoord coordinateBefore,
        HexCoord coordinateAfter,
        ShipMovementResult? plan)
    {
        Status = status;
        State = state;
        CoordinateBefore = coordinateBefore;
        CoordinateAfter = coordinateAfter;
        Plan = plan;
    }

    public ShipMovementStepExecutionStatus Status { get; }

    public ShipMovementTurnState State { get; }

    public HexCoord CoordinateBefore { get; }

    public HexCoord CoordinateAfter { get; }

    public ShipMovementResult? Plan { get; }

    public bool WasCommitted => Status == ShipMovementStepExecutionStatus.Moved;
}
