using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using StarCluster.Core.Geometry;

namespace StarCluster.Core.Maps;

/// <summary>
/// Stores the environmental and occupant state associated with one existing
/// coordinate on a tactical system map.
/// </summary>
public sealed class MapCell
{
    private readonly List<MapObject> _occupants = new();
    private readonly ReadOnlyCollection<MapObject> _readOnlyOccupants;

    internal MapCell(HexCoord coordinate)
    {
        Coordinate = coordinate;
        Terrain = MapTerrain.OpenSpace;
        _readOnlyOccupants = _occupants.AsReadOnly();
    }

    /// <summary>
    /// Gets the immutable axial coordinate of this cell.
    /// </summary>
    public HexCoord Coordinate { get; }

    /// <summary>
    /// Gets the broad environmental terrain currently assigned to the cell.
    /// </summary>
    public MapTerrain Terrain { get; internal set; }

    /// <summary>
    /// Gets a read-only view of the objects occupying the cell.
    /// </summary>
    public IReadOnlyList<MapObject> Occupants => _readOnlyOccupants;

    /// <summary>
    /// Gets whether the cell currently contains a solid object.
    /// </summary>
    public bool HasSolidOccupant => _occupants.Any(item => item.IsSolid);

    internal void Add(MapObject mapObject) => _occupants.Add(mapObject);

    internal bool Remove(MapObject mapObject) => _occupants.Remove(mapObject);
}
