namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Current launcher-to-missile communications state. This relationship is
/// independent of the launcher's sensor line of sight to the target.
/// </summary>
public enum MissileDatalinkState
{
    Unavailable,
    Live,
    Blocked,
}
