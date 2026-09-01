using System;

namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Data-driven terminal fire-control bounds supplied by a missile Guidance
/// Computer. Exact technology progression remains provisional.
/// </summary>
public sealed class MissileGuidanceComputerProfile
{
    public MissileGuidanceComputerProfile(
        int technologyLevel,
        int baseHitChancePercent,
        int minimumHitChancePercent,
        int maximumHitChancePercent)
    {
        if (technologyLevel < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(technologyLevel));
        }

        ValidatePercent(baseHitChancePercent, nameof(baseHitChancePercent));
        ValidatePercent(minimumHitChancePercent, nameof(minimumHitChancePercent));
        ValidatePercent(maximumHitChancePercent, nameof(maximumHitChancePercent));
        if (minimumHitChancePercent > maximumHitChancePercent)
        {
            throw new ArgumentException(
                "Minimum hit chance cannot exceed maximum hit chance.");
        }

        TechnologyLevel = technologyLevel;
        BaseHitChancePercent = baseHitChancePercent;
        MinimumHitChancePercent = minimumHitChancePercent;
        MaximumHitChancePercent = maximumHitChancePercent;
    }

    public int TechnologyLevel { get; }

    public int BaseHitChancePercent { get; }

    public int MinimumHitChancePercent { get; }

    public int MaximumHitChancePercent { get; }

    public int ClampHitChance(int chancePercent) => Math.Clamp(
        chancePercent,
        MinimumHitChancePercent,
        MaximumHitChancePercent);

    private static void ValidatePercent(int value, string parameterName)
    {
        if (value is < 0 or > 100)
        {
            throw new ArgumentOutOfRangeException(
                parameterName,
                value,
                "Percent values must be from 0 through 100.");
        }
    }
}
