using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using StarCluster.Core.Geometry;

namespace StarCluster.Core.Maps;

/// <summary>
/// Holds the mutable logical contents of one finite tactical system map.
/// </summary>
/// <remarks>
/// The underlying <see cref="HexMap"/> still defines only which coordinates
/// exist. This class layers terrain and occupants over that geometry while
/// remaining independent of Godot, sprites, pixels, and input handling.
/// </remarks>
public sealed class SystemMap
{
    private readonly Dictionary<HexCoord, MapCell> _cellsByCoordinate;
    private readonly IReadOnlyList<MapCell> _cells;
    private readonly Dictionary<string, MapObject> _objectsById =
        new(StringComparer.Ordinal);
    private readonly Dictionary<string, HexCoord> _locationsById =
        new(StringComparer.Ordinal);

    private SystemMap(HexMap geometry)
    {
        Geometry = geometry;

        MapCell[] cells = geometry.Cells
            .Select(coordinate => new MapCell(coordinate))
            .ToArray();

        _cellsByCoordinate = cells.ToDictionary(cell => cell.Coordinate);
        _cells = Array.AsReadOnly(cells);
    }

    /// <summary>
    /// Gets the finite immutable geometry that defines the map boundary.
    /// </summary>
    public HexMap Geometry { get; }

    /// <summary>
    /// Gets every map cell in the same deterministic order as the geometry.
    /// </summary>
    public IReadOnlyList<MapCell> Cells => _cells;

    /// <summary>
    /// Gets the map's star, or <see langword="null"/> for a starless map.
    /// </summary>
    public MapObject? Star => _objectsById.Values
        .SingleOrDefault(item => item.Kind == MapObjectKind.Star);

    /// <summary>
    /// Creates a tactical system map with an optional single central star.
    /// </summary>
    /// <exception cref="ArgumentException">
    /// Thrown when <paramref name="centralStar"/> is not a star.
    /// </exception>
    public static SystemMap Create(int radius, MapObject? centralStar = null)
    {
        if (centralStar is not null && centralStar.Kind != MapObjectKind.Star)
        {
            throw new ArgumentException(
                "The optional central object must be a star.",
                nameof(centralStar));
        }

        var map = new SystemMap(HexMap.CreateHexagon(radius));

        if (centralStar is not null)
        {
            map.Place(centralStar, HexCoord.Zero);
        }

        return map;
    }

    /// <summary>
    /// Gets the cell at an existing coordinate.
    /// </summary>
    /// <exception cref="ArgumentOutOfRangeException">
    /// Thrown when <paramref name="coordinate"/> is outside the map.
    /// </exception>
    public MapCell GetCell(HexCoord coordinate)
    {
        if (!_cellsByCoordinate.TryGetValue(coordinate, out MapCell? cell))
        {
            throw new ArgumentOutOfRangeException(
                nameof(coordinate),
                coordinate,
                "The coordinate is outside this system map.");
        }

        return cell;
    }

    /// <summary>
    /// Assigns broad environmental terrain to an existing cell.
    /// </summary>
    public void SetTerrain(HexCoord coordinate, MapTerrain terrain) =>
        GetCell(coordinate).Terrain = terrain;

    /// <summary>
    /// Places an object at an existing coordinate.
    /// </summary>
    /// <remarks>
    /// A cell can contain at most one solid object. Non-solid anomalies and
    /// wreckage may coexist with other occupants. A system map can contain at
    /// most one star, and that star must be at axial origin `(0,0)`.
    /// </remarks>
    public void Place(MapObject mapObject, HexCoord coordinate)
    {
        ArgumentNullException.ThrowIfNull(mapObject);

        MapCell cell = GetCell(coordinate);

        if (_objectsById.ContainsKey(mapObject.Id))
        {
            throw new ArgumentException(
                $"A map object with ID '{mapObject.Id}' is already placed.",
                nameof(mapObject));
        }

        ValidateStarPlacement(mapObject, coordinate);

        if (mapObject.IsSolid && cell.HasSolidOccupant)
        {
            throw new InvalidOperationException(
                $"Cell {coordinate} already contains a solid object.");
        }

        cell.Add(mapObject);
        _objectsById.Add(mapObject.Id, mapObject);
        _locationsById.Add(mapObject.Id, coordinate);
    }

    /// <summary>
    /// Moves a placed ship to another existing coordinate.
    /// </summary>
    /// <remarks>
    /// Only ships are mobile at this layer. Stars, planets, stations,
    /// anomalies, and wreckage cannot be moved by this operation.
    /// </remarks>
    public void Move(string objectId, HexCoord destination)
    {
        MapObject mapObject = GetPlacedObject(objectId);

        if (!mapObject.CanMove)
        {
            throw new InvalidOperationException(
                $"Map object '{objectId}' of kind {mapObject.Kind} cannot move.");
        }

        MapCell destinationCell = GetCell(destination);
        HexCoord origin = _locationsById[objectId];

        if (origin == destination)
        {
            return;
        }

        if (mapObject.IsSolid && destinationCell.HasSolidOccupant)
        {
            throw new InvalidOperationException(
                $"Cell {destination} already contains a solid object.");
        }

        MapCell originCell = GetCell(origin);

        if (!originCell.Remove(mapObject))
        {
            throw new InvalidOperationException(
                $"Map object '{objectId}' was indexed but missing from its cell.");
        }

        destinationCell.Add(mapObject);
        _locationsById[objectId] = destination;
    }

    /// <summary>
    /// Removes and returns a placed object.
    /// </summary>
    public MapObject Remove(string objectId)
    {
        MapObject mapObject = GetPlacedObject(objectId);
        HexCoord coordinate = _locationsById[objectId];
        MapCell cell = GetCell(coordinate);

        if (!cell.Remove(mapObject))
        {
            throw new InvalidOperationException(
                $"Map object '{objectId}' was indexed but missing from its cell.");
        }

        _objectsById.Remove(objectId);
        _locationsById.Remove(objectId);

        return mapObject;
    }

    /// <summary>
    /// Attempts to locate a placed object by its stable identifier.
    /// </summary>
    public bool TryGetLocation(string objectId, out HexCoord coordinate)
    {
        if (objectId is null)
        {
            coordinate = default;
            return false;
        }

        return _locationsById.TryGetValue(objectId, out coordinate);
    }

    private MapObject GetPlacedObject(string objectId)
    {
        if (string.IsNullOrWhiteSpace(objectId))
        {
            throw new ArgumentException(
                "A map object ID cannot be empty or whitespace.",
                nameof(objectId));
        }

        if (!_objectsById.TryGetValue(objectId, out MapObject? mapObject))
        {
            throw new KeyNotFoundException(
                $"No placed map object has ID '{objectId}'.");
        }

        return mapObject;
    }

    private void ValidateStarPlacement(
        MapObject mapObject,
        HexCoord coordinate)
    {
        if (mapObject.Kind != MapObjectKind.Star)
        {
            return;
        }

        if (coordinate != HexCoord.Zero)
        {
            throw new InvalidOperationException(
                "A system map star must occupy the origin (0,0).");
        }

        if (Star is not null)
        {
            throw new InvalidOperationException(
                "A system map can contain at most one star.");
        }
    }
}
