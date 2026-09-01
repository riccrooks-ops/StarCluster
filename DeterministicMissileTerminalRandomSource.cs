using StarCluster.Core.Combat.Missiles;

namespace StarCluster.ScenarioRunner;

public sealed class DeterministicMissileTerminalRandomSource : IMissileTerminalRandomSource
{
    private readonly DeterministicRandomStream _stream;

    public DeterministicMissileTerminalRandomSource(ulong seed)
    {
        _stream = new DeterministicRandomStream(seed);
    }

    public int NextD100() => _stream.NextD100();
}
