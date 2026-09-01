namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Policy seam for deterministic tests and later probability, TL, sensor,
/// weapon, and officer rules.
/// </summary>
public interface IMissileInterceptionResolver
{
    MissileInterceptionOutcome Resolve(MissileInterceptionAttempt attempt);
}
