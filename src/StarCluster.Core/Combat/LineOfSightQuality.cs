namespace StarCluster.Core.Combat;

/// <summary>
/// Describes the geometric quality of a direct-fire line of sight.
/// </summary>
public enum LineOfSightQuality
{
    /// <summary>
    /// No intermediate star or planet touches the firing line.
    /// </summary>
    Clear,

    /// <summary>
    /// Direct fire remains possible, but the line grazes one or more stars or
    /// planets along exact hex boundaries.
    /// </summary>
    Grazing,

    /// <summary>
    /// A star or planet fully obstructs the line, so direct fire is not
    /// geometrically possible.
    /// </summary>
    Blocked,
}
