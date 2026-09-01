namespace StarCluster.Core.Combat.Tracking;

/// <summary>
/// Identifies where a track update originated. The source is retained so later
/// rules can distinguish navigation data, tactical sensors, seekers, and local
/// defensive acquisition.
/// </summary>
public enum TacticalTrackSourceType
{
    NavigationDatabase,
    PreviousIntelligence,
    TacticalSensors,
    MissileSeeker,
    LocalPointDefenseSensor,
    ObservedLaunch,
    MissileOnboardSensor,
}
