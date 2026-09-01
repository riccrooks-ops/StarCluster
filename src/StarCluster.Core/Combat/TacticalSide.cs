namespace StarCluster.Core.Combat;

/// <summary>
/// Prototype tactical ownership shared by ships, missiles, and defensive
/// systems. Unspecified exists only for compatibility with pre-ownership
/// missile callers.
/// </summary>
public enum TacticalSide
{
    Unspecified,
    Player,
    Enemy,
}
