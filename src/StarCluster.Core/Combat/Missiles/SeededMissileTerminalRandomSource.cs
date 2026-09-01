using System;

namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Seeded d100 stream for replayable prototype encounters.
/// </summary>
public sealed class SeededMissileTerminalRandomSource : IMissileTerminalRandomSource
{
    private readonly Random _random;

    public SeededMissileTerminalRandomSource(int seed)
    {
        _random = new Random(seed);
    }

    public int NextD100() => _random.Next(1, 101);
}
