namespace StarCluster.Core.Movement;

/// <summary>
/// Describes the result of planning a tactical ship movement route.
/// </summary>
public enum ShipMovementStatus
{
    Found,
    OutOfRange,
    Occupied,
    NoRoute,
}
