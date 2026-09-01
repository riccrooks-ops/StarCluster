namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Broad lifetime state for a moving-target Missile Flight. Terminal acquisition
/// and attack detail is carried separately by <see cref="MissileTerminalState"/>
/// and <see cref="MissileTerminalResolution"/>.
/// </summary>
public enum GuidedMissileStatus
{
    InFlight,
    WaitingForRoute,
    WaitingForTrack,
    Searching,
    Expended,
    Dud,
    RangeExhausted,
    Intercepted,
    SelfDestructed,
    Destroyed,
}
