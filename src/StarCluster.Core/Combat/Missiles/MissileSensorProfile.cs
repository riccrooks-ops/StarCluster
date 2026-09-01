using System;
using StarCluster.Core.Combat.Tracking;

namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Data-driven onboard navigation-sensor capability for a missile. The profile
/// is intentionally inferior to the same-technology ship sensor used by the
/// prototype and follows a passive-first, deterministic active-escalation rule.
/// </summary>
public sealed class MissileSensorProfile
{
    public MissileSensorProfile(
        int technologyLevel,
        bool isInstalled,
        int firmRangeHexes,
        int approximateRangeHexes,
        bool requiresLineOfSight = true,
        int activeModeRangeBonusHexes = 0,
        bool allowsActiveMode = true,
        int maximumLocalTrackAgeEpochs = 2)
    {
        if (technologyLevel < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(technologyLevel));
        }

        if (maximumLocalTrackAgeEpochs < 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(maximumLocalTrackAgeEpochs));
        }

        TechnologyLevel = technologyLevel;
        IsInstalled = isInstalled;
        AllowsActiveMode = allowsActiveMode;
        MaximumLocalTrackAgeEpochs = maximumLocalTrackAgeEpochs;
        Sensor = new SensorProfile(
            technologyLevel,
            firmRangeHexes,
            approximateRangeHexes,
            requiresLineOfSight,
            activeModeRangeBonusHexes);
    }

    public int TechnologyLevel { get; }

    public bool IsInstalled { get; }

    public bool AllowsActiveMode { get; }

    public int MaximumLocalTrackAgeEpochs { get; }

    public SensorProfile Sensor { get; }
}
