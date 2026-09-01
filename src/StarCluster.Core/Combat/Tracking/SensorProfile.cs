using System;

namespace StarCluster.Core.Combat.Tracking;

/// <summary>
/// Data-driven tactical sensor capability. Exact TL progression and final
/// probability remain deferred, while passive/active range behavior is now an
/// explicit profile value.
/// </summary>
public sealed class SensorProfile
{
    public SensorProfile(
        int technologyLevel,
        int firmRangeHexes,
        int approximateRangeHexes,
        bool requiresLineOfSight = true,
        int activeModeRangeBonusHexes = 0)
    {
        if (technologyLevel < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(technologyLevel));
        }

        if (firmRangeHexes < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(firmRangeHexes));
        }

        if (approximateRangeHexes < firmRangeHexes)
        {
            throw new ArgumentOutOfRangeException(
                nameof(approximateRangeHexes),
                approximateRangeHexes,
                "Approximate range cannot be less than firm range.");
        }

        if (activeModeRangeBonusHexes < 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(activeModeRangeBonusHexes));
        }

        TechnologyLevel = technologyLevel;
        FirmRangeHexes = firmRangeHexes;
        ApproximateRangeHexes = approximateRangeHexes;
        RequiresLineOfSight = requiresLineOfSight;
        ActiveModeRangeBonusHexes = activeModeRangeBonusHexes;
    }

    public int TechnologyLevel { get; }

    public int FirmRangeHexes { get; }

    public int ApproximateRangeHexes { get; }

    public bool RequiresLineOfSight { get; }

    public int ActiveModeRangeBonusHexes { get; }
}
