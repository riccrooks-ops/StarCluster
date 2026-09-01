namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Describes the outcome of guided-missile route planning.
/// </summary>
public enum MissileRouteStatus
{
    /// <summary>
    /// A legal route exists and fits within the requested maximum range.
    /// </summary>
    Found,

    /// <summary>
    /// A legal route exists, but its routed distance exceeds maximum range.
    /// </summary>
    OutOfRange,

    /// <summary>
    /// No legal route connects the origin and target on the finite map.
    /// </summary>
    NoRoute,
}
