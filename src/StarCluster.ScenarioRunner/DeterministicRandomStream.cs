namespace StarCluster.ScenarioRunner;

/// <summary>
/// Small platform-independent SplitMix64 stream used by the headless runner.
/// A trial receives its own derived stream seeds, so execution order and worker
/// count cannot change its random sequence.
/// </summary>
public sealed class DeterministicRandomStream
{
    private ulong _state;

    public DeterministicRandomStream(ulong seed)
    {
        _state = seed;
    }

    public ulong NextUInt64()
    {
        _state += 0x9E3779B97F4A7C15UL;
        ulong value = _state;
        value = (value ^ (value >> 30)) * 0xBF58476D1CE4E5B9UL;
        value = (value ^ (value >> 27)) * 0x94D049BB133111EBUL;
        return value ^ (value >> 31);
    }

    public int NextD100() => checked((int)(NextUInt64() % 100UL) + 1);
}
