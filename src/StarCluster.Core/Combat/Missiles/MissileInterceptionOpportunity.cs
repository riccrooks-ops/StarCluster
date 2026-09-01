namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Identifies why a defensive system is being offered an interception chance.
/// Standard point defense receives distinct terminal-entry and pre-attack
/// windows; those windows are not aliases for one automatic impact gate.
/// </summary>
public enum MissileInterceptionOpportunity
{
    Transit,
    Stationary,
    TerminalEntry,
    PreTerminalAttack,
}
