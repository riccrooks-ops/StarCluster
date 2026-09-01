using System;

namespace StarCluster.Core.Combat.Tracking;

/// <summary>
/// Deterministic tactical sensing penalty supplied by the current environment.
/// Nebulae, storms, damage, and similar effects may later provide specialized
/// profiles without changing the contact evaluator.
/// </summary>
public sealed class SensorEnvironmentProfile
{
    public SensorEnvironmentProfile(string id, int rangePenaltyHexes)
    {
        if (string.IsNullOrWhiteSpace(id))
        {
            throw new ArgumentException("An environment profile ID is required.", nameof(id));
        }

        if (rangePenaltyHexes < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(rangePenaltyHexes));
        }

        Id = id;
        RangePenaltyHexes = rangePenaltyHexes;
    }

    public static SensorEnvironmentProfile ClearSpace { get; } =
        new("clear-space", 0);

    public string Id { get; }

    public int RangePenaltyHexes { get; }
}
