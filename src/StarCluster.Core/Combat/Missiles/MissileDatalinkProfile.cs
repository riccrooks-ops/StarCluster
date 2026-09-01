using System;

namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Data-driven launcher-to-missile communications capability. A blocked link
/// delivers no new report; the missile may retain a prior copy for a bounded
/// number of later guidance phases.
/// </summary>
public sealed class MissileDatalinkProfile
{
    public MissileDatalinkProfile(
        int technologyLevel,
        bool isInstalled = true,
        bool requiresLineOfSight = true,
        int maximumRetainedReportAgePhases = 3)
    {
        if (technologyLevel < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(technologyLevel));
        }

        if (maximumRetainedReportAgePhases < 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(maximumRetainedReportAgePhases));
        }

        TechnologyLevel = technologyLevel;
        IsInstalled = isInstalled;
        RequiresLineOfSight = requiresLineOfSight;
        MaximumRetainedReportAgePhases = maximumRetainedReportAgePhases;
    }

    public static MissileDatalinkProfile None { get; } = new(
        technologyLevel: 0,
        isInstalled: false,
        requiresLineOfSight: false,
        maximumRetainedReportAgePhases: 0);

    public int TechnologyLevel { get; }

    public bool IsInstalled { get; }

    public bool RequiresLineOfSight { get; }

    public int MaximumRetainedReportAgePhases { get; }
}
