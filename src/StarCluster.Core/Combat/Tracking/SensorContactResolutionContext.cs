using System;

namespace StarCluster.Core.Combat.Tracking;

/// <summary>
/// Effective range envelope supplied to a sensor-resolution policy. A future
/// seeded probabilistic policy may consume the same context without changing
/// track management or presentation.
/// </summary>
public sealed class SensorContactResolutionContext
{
    public SensorContactResolutionContext(
        int distanceHexes,
        int effectiveFirmRangeHexes,
        int effectiveApproximateRangeHexes)
    {
        if (distanceHexes < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(distanceHexes));
        }

        if (effectiveFirmRangeHexes < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(effectiveFirmRangeHexes));
        }

        if (effectiveApproximateRangeHexes < effectiveFirmRangeHexes)
        {
            throw new ArgumentOutOfRangeException(
                nameof(effectiveApproximateRangeHexes));
        }

        DistanceHexes = distanceHexes;
        EffectiveFirmRangeHexes = effectiveFirmRangeHexes;
        EffectiveApproximateRangeHexes = effectiveApproximateRangeHexes;
    }

    public int DistanceHexes { get; }

    public int EffectiveFirmRangeHexes { get; }

    public int EffectiveApproximateRangeHexes { get; }
}
