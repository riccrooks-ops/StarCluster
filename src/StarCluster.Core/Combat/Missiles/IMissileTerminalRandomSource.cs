namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Replaceable d100 source for seeker acquisition and terminal attack rolls.
/// </summary>
public interface IMissileTerminalRandomSource
{
    int NextD100();
}
