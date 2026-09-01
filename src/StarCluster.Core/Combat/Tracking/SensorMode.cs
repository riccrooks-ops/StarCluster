namespace StarCluster.Core.Combat.Tracking;

/// <summary>
/// Current operating mode of a tactical sensor installation. Passive sensing
/// preserves the baseline profile. Active sensing may extend effective range,
/// while the target's own active emissions may also increase its signature.
/// </summary>
public enum SensorMode
{
    Passive,
    Active,
}
