using System;

namespace StarCluster.Core.Combat.Tracking;

/// <summary>
/// Installed electronic-warfare capability. Jamming is applied only while the
/// owning target has enabled it. Counter-jamming is a passive capability of the
/// observer for this deterministic foundation.
/// </summary>
public sealed class ElectronicWarfareProfile
{
    public ElectronicWarfareProfile(
        int technologyLevel,
        int jammingRangePenaltyHexes,
        int counterJammingStrength)
    {
        if (technologyLevel < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(technologyLevel));
        }

        if (jammingRangePenaltyHexes < 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(jammingRangePenaltyHexes));
        }

        if (counterJammingStrength < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(counterJammingStrength));
        }

        TechnologyLevel = technologyLevel;
        JammingRangePenaltyHexes = jammingRangePenaltyHexes;
        CounterJammingStrength = counterJammingStrength;
    }

    public static ElectronicWarfareProfile None { get; } = new(0, 0, 0);

    public int TechnologyLevel { get; }

    public int JammingRangePenaltyHexes { get; }

    public int CounterJammingStrength { get; }
}
