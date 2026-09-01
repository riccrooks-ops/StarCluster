namespace StarCluster.Core.Combat.Tracking;

/// <summary>
/// Quality returned by a sensor-resolution policy after hard geometry and
/// profile modifiers have been evaluated.
/// </summary>
public enum SensorContactResolution
{
    Firm,
    Approximate,
    Missed,
}
