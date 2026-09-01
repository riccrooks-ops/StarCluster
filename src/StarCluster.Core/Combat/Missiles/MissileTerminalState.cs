namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Terminal-lifecycle state kept separate from broad missile flight status so
/// movement, acquisition, attack resolution, and final disposition do not
/// collapse into one combinatorial enum.
/// </summary>
public enum MissileTerminalState
{
    None,
    Opportunity,
    SearchWait,
    FirmSolution,
    Resolved,
}
