namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Authoritative result of the most recent terminal opportunity or attack.
/// </summary>
public enum MissileTerminalOutcome
{
    None,
    AcquisitionFailed,
    Intercepted,
    Dud,
    Miss,
    Hit,
    CriticalHit,
    SelfDestructed,
}
