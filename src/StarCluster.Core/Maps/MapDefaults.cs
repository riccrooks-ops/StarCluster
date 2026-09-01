namespace StarCluster.Core.Maps;

/// <summary>
/// Holds the current prototype map dimensions in one place.
/// </summary>
/// <remarks>
/// These values are working design defaults, not assumptions embedded in the
/// geometry algorithms. They can be changed later without rewriting HexMap.
/// </remarks>
public static class MapDefaults
{
    /// <summary>
    /// Radius of an 11-hex-diameter tactical system map.
    /// </summary>
    public const int SystemRadius = 5;

    /// <summary>
    /// Diameter of the current tactical system map.
    /// </summary>
    public const int SystemDiameter = (2 * SystemRadius) + 1;

    /// <summary>
    /// Radius of the current 17-hex-diameter strategic cluster map.
    /// </summary>
    public const int ClusterRadius = 8;

    /// <summary>
    /// Diameter of the current strategic cluster map.
    /// </summary>
    public const int ClusterDiameter = (2 * ClusterRadius) + 1;
}
