using System;
using System.Collections.Generic;
using System.Linq;
using StarCluster.Core.Geometry;

namespace StarCluster.Core.Maps;

/// <summary>
/// Represents a finite, origin-centered, hexagonal map.
/// </summary>
/// <remarks>
/// The map stores logical axial coordinates only. It has no knowledge of
/// pixels, sprites, Godot, stars, planets, ships, or terrain.
/// </remarks>
public sealed class HexMap
{
    private readonly HashSet<HexCoord> _cellSet;
    private readonly IReadOnlyList<HexCoord> _cells;

    private HexMap(int radius)
    {
        Radius = radius;

        HexCoord[] cells = HexGeometry
            .CellsWithin(HexCoord.Zero, radius)
            .ToArray();

        _cellSet = new HashSet<HexCoord>(cells);
        _cells = Array.AsReadOnly(cells);
    }

    /// <summary>
    /// Gets the number of single-hex moves from the center to any corner.
    /// </summary>
    public int Radius { get; }

    /// <summary>
    /// Gets the number of hexes across the map through its center.
    /// </summary>
    public int Diameter => (2 * Radius) + 1;

    /// <summary>
    /// Gets the number of cells contained by this map.
    /// </summary>
    public int CellCount => _cells.Count;

    /// <summary>
    /// Gets every coordinate that exists on this map.
    /// </summary>
    public IReadOnlyList<HexCoord> Cells => _cells;

    /// <summary>
    /// Creates an origin-centered hexagonal map with the requested radius.
    /// </summary>
    /// <exception cref="ArgumentOutOfRangeException">
    /// Thrown when <paramref name="radius"/> is negative.
    /// </exception>
    public static HexMap CreateHexagon(int radius)
    {
        if (radius < 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(radius),
                radius,
                "Map radius cannot be negative.");
        }

        return new HexMap(radius);
    }

    /// <summary>
    /// Returns whether the coordinate exists on this finite map.
    /// </summary>
    public bool Contains(HexCoord coordinate) => _cellSet.Contains(coordinate);

    /// <summary>
    /// Returns whether the coordinate exists on the outer ring of the map.
    /// </summary>
    public bool IsBoundary(HexCoord coordinate) =>
        Contains(coordinate) && coordinate.Length() == Radius;

    /// <summary>
    /// Returns only the neighboring coordinates that remain inside the map.
    /// </summary>
    /// <exception cref="ArgumentOutOfRangeException">
    /// Thrown when <paramref name="coordinate"/> is not on this map.
    /// </exception>
    public IReadOnlyList<HexCoord> NeighborsOf(HexCoord coordinate)
    {
        if (!Contains(coordinate))
        {
            throw new ArgumentOutOfRangeException(
                nameof(coordinate),
                coordinate,
                "The coordinate is outside this map.");
        }

        HexCoord[] neighbors = coordinate
            .Neighbors()
            .Where(Contains)
            .ToArray();

        return Array.AsReadOnly(neighbors);
    }
}
