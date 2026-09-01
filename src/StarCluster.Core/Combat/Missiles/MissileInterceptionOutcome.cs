namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Provisional result from one deterministic or rules-driven interception
/// attempt. Probability and technology contests remain separate policy.
/// </summary>
public enum MissileInterceptionOutcome
{
    Missed,
    Intercepted,
}
