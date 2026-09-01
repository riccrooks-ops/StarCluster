using System;

namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Deterministic resolver used by tests and the current Godot demonstration.
/// </summary>
public sealed class FixedMissileInterceptionResolver : IMissileInterceptionResolver
{
    public FixedMissileInterceptionResolver(MissileInterceptionOutcome outcome)
    {
        if (!Enum.IsDefined(outcome))
        {
            throw new ArgumentOutOfRangeException(nameof(outcome), outcome, null);
        }

        Outcome = outcome;
    }

    public MissileInterceptionOutcome Outcome { get; }

    public MissileInterceptionOutcome Resolve(MissileInterceptionAttempt attempt)
    {
        ArgumentNullException.ThrowIfNull(attempt);
        return Outcome;
    }
}
