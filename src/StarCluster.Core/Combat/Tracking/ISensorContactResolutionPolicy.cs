namespace StarCluster.Core.Combat.Tracking;

/// <summary>
/// Replaceable policy seam for deterministic or future seeded probabilistic
/// contact resolution. Occlusion remains a hard rule enforced before this
/// policy is called.
/// </summary>
public interface ISensorContactResolutionPolicy
{
    SensorContactResolution Resolve(SensorContactResolutionContext context);
}
