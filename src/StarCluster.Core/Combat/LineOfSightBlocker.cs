using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;

namespace StarCluster.Core.Combat;

/// <summary>
/// Identifies one map object that blocks a direct-fire line of sight.
/// </summary>
public sealed record LineOfSightBlocker(
    HexCoord Coordinate,
    MapObject MapObject);
