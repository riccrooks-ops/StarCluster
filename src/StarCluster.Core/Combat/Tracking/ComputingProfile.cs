using System;

namespace StarCluster.Core.Combat.Tracking;

/// <summary>
/// Data-driven ability to preserve and extrapolate imperfect sensor tracks.
/// </summary>
public sealed class ComputingProfile
{
    public ComputingProfile(
        int technologyLevel,
        int staleRetentionUpdates,
        int uncertaintyGrowthPerMissedUpdate = 1)
    {
        if (technologyLevel < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(technologyLevel));
        }

        if (staleRetentionUpdates < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(staleRetentionUpdates));
        }

        if (uncertaintyGrowthPerMissedUpdate < 1)
        {
            throw new ArgumentOutOfRangeException(
                nameof(uncertaintyGrowthPerMissedUpdate));
        }

        TechnologyLevel = technologyLevel;
        StaleRetentionUpdates = staleRetentionUpdates;
        UncertaintyGrowthPerMissedUpdate = uncertaintyGrowthPerMissedUpdate;
    }

    public int TechnologyLevel { get; }

    /// <summary>
    /// Number of missed observation epochs retained as Stale. The current
    /// prototype uses one tactical turn as one observation epoch. The legacy
    /// property name is retained for source compatibility.
    /// </summary>
    public int StaleRetentionUpdates { get; }

    public int UncertaintyGrowthPerMissedUpdate { get; }
}
