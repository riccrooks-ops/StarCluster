using StarCluster.Core.Geometry;

namespace StarCluster.Core.Movement;

public sealed class ShipMovementExecutionResult
{
    internal ShipMovementExecutionResult(
        ShipMovementExecutionStatus status,
        ShipMovementResult plan,
        HexCoord finalCoordinate)
    {
        Status = status;
        Plan = plan;
        FinalCoordinate = finalCoordinate;
    }

    public ShipMovementExecutionStatus Status { get; }

    public ShipMovementResult Plan { get; }

    public HexCoord FinalCoordinate { get; }

    public bool WasCommitted =>
        Status is ShipMovementExecutionStatus.Moved or ShipMovementExecutionStatus.Held;
}
