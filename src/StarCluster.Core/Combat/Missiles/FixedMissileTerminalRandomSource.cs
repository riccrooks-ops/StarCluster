using System;
using System.Collections.Generic;

namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Deterministic d100 source for engine-independent tests and repeatable
/// fixtures. Once the supplied sequence is exhausted, the final value repeats.
/// </summary>
public sealed class FixedMissileTerminalRandomSource : IMissileTerminalRandomSource
{
    private readonly IReadOnlyList<int> _rolls;
    private int _index;

    public FixedMissileTerminalRandomSource(params int[] rolls)
    {
        if (rolls is null || rolls.Length == 0)
        {
            throw new ArgumentException(
                "At least one d100 roll is required.",
                nameof(rolls));
        }

        foreach (int roll in rolls)
        {
            ValidateRoll(roll);
        }

        _rolls = Array.AsReadOnly((int[])rolls.Clone());
    }

    public int NextD100()
    {
        int index = Math.Min(_index, _rolls.Count - 1);
        _index++;
        return _rolls[index];
    }

    private static void ValidateRoll(int roll)
    {
        if (roll is < 1 or > 100)
        {
            throw new ArgumentOutOfRangeException(
                nameof(roll),
                roll,
                "A d100 roll must be from 1 through 100.");
        }
    }
}
