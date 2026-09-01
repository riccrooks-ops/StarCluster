namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Timing point at which the missile evaluated its local sensor and guidance
/// candidates.
/// </summary>
public enum MissileGuidanceObservationOpportunity
{
    ActionStart,
    AfterEnteredHex,
    TargetMovement,
    SensorStateChanged,
    WaitingForTrack,
}
