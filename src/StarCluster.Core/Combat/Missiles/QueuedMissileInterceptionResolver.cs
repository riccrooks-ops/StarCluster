using System;
using System.Collections.Generic;
using System.Linq;

namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Deterministic interception outcome queue for scripted scenarios. Once the
/// queue is exhausted the last supplied outcome repeats, matching the fixed
/// terminal d100 source's repeat-last behavior.
/// </summary>
public sealed class QueuedMissileInterceptionResolver : IMissileInterceptionResolver
{
    private readonly IReadOnlyList<MissileInterceptionOutcome> _outcomes;
    private int _index;

    public QueuedMissileInterceptionResolver(
        params MissileInterceptionOutcome[] outcomes)
    {
        if (outcomes is null || outcomes.Length == 0)
        {
            throw new ArgumentException(
                "At least one interception outcome is required.",
                nameof(outcomes));
        }

        foreach (MissileInterceptionOutcome outcome in outcomes)
        {
            if (!Enum.IsDefined(outcome))
            {
                throw new ArgumentOutOfRangeException(nameof(outcomes));
            }
        }

        _outcomes = Array.AsReadOnly(outcomes.ToArray());
    }

    public int OutcomesConsumed => _index;

    public MissileInterceptionOutcome Resolve(MissileInterceptionAttempt attempt)
    {
        ArgumentNullException.ThrowIfNull(attempt);
        int index = Math.Min(_index, _outcomes.Count - 1);
        _index++;
        return _outcomes[index];
    }
}
