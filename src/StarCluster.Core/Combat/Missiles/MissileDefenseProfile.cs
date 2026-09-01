using System;

namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Data-driven interception envelope and attempt budget for one defensive
/// system. Exact technology progression and hit probabilities remain deferred.
/// </summary>
public sealed class MissileDefenseProfile
{
    public MissileDefenseProfile(
        int technologyLevel,
        int interceptionRangeHexes,
        int maximumAttemptsPerPhase)
    {
        if (technologyLevel < 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(technologyLevel),
                technologyLevel,
                "Technology level cannot be negative.");
        }

        if (interceptionRangeHexes < 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(interceptionRangeHexes),
                interceptionRangeHexes,
                "Interception range cannot be negative.");
        }

        if (maximumAttemptsPerPhase <= 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(maximumAttemptsPerPhase),
                maximumAttemptsPerPhase,
                "At least one interception attempt per phase is required.");
        }

        TechnologyLevel = technologyLevel;
        InterceptionRangeHexes = interceptionRangeHexes;
        MaximumAttemptsPerPhase = maximumAttemptsPerPhase;
    }

    public int TechnologyLevel { get; }

    public int InterceptionRangeHexes { get; }

    public int MaximumAttemptsPerPhase { get; }
}
