namespace StarCluster.Core.Maps;

/// <summary>
/// Describes the broad environmental terrain of a tactical map cell.
/// </summary>
/// <remarks>
/// Terrain is separate from occupants. For example, a ship may occupy open
/// space, a nebula, or an asteroid field without changing what the ship is.
/// </remarks>
public enum MapTerrain
{
    OpenSpace = 0,
    AsteroidField = 1,
    Nebula = 2,
}
