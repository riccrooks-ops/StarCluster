namespace StarCluster.Core.Combat.InternalDamage;

public enum ShipCondition
{
    FullyOperational = 0,
    Degraded = 1,
    Disabled = 2,
    PendingDestruction = 3,
    Destroyed = 4,
}

public sealed record ShipCapabilitySnapshot(
    ShipCondition Condition,
    bool HasOffensiveCapability,
    bool HasStandardStlMovement,
    bool HasFtlDeparture,
    bool HasActiveDefense,
    bool HasEvasiveManeuvers,
    bool HasCommunications,
    bool HasUsablePower,
    bool CanAttemptDamageControl,
    IReadOnlyList<string> Tags);
