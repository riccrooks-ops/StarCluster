namespace StarCluster.Core.Movement;

/// <summary>
/// Describes one attempted authoritative ship movement step.
/// </summary>
public enum ShipMovementStepExecutionStatus
{
    Moved,
    RejectedMovementComplete,
    RejectedNotAdjacent,
    RejectedIllegalDestination,
}
