using System;

namespace StarCluster.Core.Combat.Tracking;

/// <summary>
/// Current KISS policy: Firm inside the effective Firm envelope, Approximate
/// inside the remaining effective envelope, and Missed beyond it.
/// </summary>
public sealed class DeterministicSensorContactResolutionPolicy :
    ISensorContactResolutionPolicy
{
    private DeterministicSensorContactResolutionPolicy()
    {
    }

    public static DeterministicSensorContactResolutionPolicy Instance { get; } =
        new();

    public SensorContactResolution Resolve(
        SensorContactResolutionContext context)
    {
        ArgumentNullException.ThrowIfNull(context);

        if (context.DistanceHexes <= context.EffectiveFirmRangeHexes)
        {
            return SensorContactResolution.Firm;
        }

        return context.DistanceHexes <= context.EffectiveApproximateRangeHexes
            ? SensorContactResolution.Approximate
            : SensorContactResolution.Missed;
    }
}
