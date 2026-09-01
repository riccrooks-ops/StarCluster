namespace StarCluster.Core.Combat.Tracking;

/// <summary>
/// State changes that can request a track refresh. Track Update is an engine
/// event, not a player-visible tactical phase.
/// </summary>
public enum TrackUpdateTrigger
{
    SystemEntry,
    ScenarioReset,
    ShipMovementCommitted,
    ShipMovementStepCommitted,
    MissileLaunched,
    MissileMovementCompleted,
    SensorStateChanged,
    ObjectSpawned,
    ObjectDestroyed,
}
