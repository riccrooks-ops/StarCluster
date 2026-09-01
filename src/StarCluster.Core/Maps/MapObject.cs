using System;

namespace StarCluster.Core.Maps;

/// <summary>
/// Represents one identifiable object placed on a tactical system map.
/// </summary>
/// <remarks>
/// This is intentionally a small immutable domain value. Combat statistics,
/// ownership, cargo, crew, and visual presentation will belong to later
/// systems rather than being embedded in the map layer.
/// </remarks>
public sealed record MapObject
{
    private MapObject(string id, string name, MapObjectKind kind)
    {
        if (string.IsNullOrWhiteSpace(id))
        {
            throw new ArgumentException(
                "A map object ID cannot be empty or whitespace.",
                nameof(id));
        }

        if (string.IsNullOrWhiteSpace(name))
        {
            throw new ArgumentException(
                "A map object name cannot be empty or whitespace.",
                nameof(name));
        }

        Id = id;
        Name = name;
        Kind = kind;
    }

    /// <summary>
    /// Gets the stable identifier used by the logical map and save data.
    /// </summary>
    public string Id { get; }

    /// <summary>
    /// Gets the player-facing or diagnostic name of the object.
    /// </summary>
    public string Name { get; }

    /// <summary>
    /// Gets the object's broad tactical-map category.
    /// </summary>
    public MapObjectKind Kind { get; }

    /// <summary>
    /// Gets whether the object occupies the cell's one exclusive solid slot.
    /// </summary>
    /// <remarks>
    /// The current prototype treats stars, planets, ships, and stations as
    /// solid. Anomalies and wreckage are informational or diffuse occupants
    /// and may share a cell with a solid object.
    /// </remarks>
    public bool IsSolid => Kind is
        MapObjectKind.Star or
        MapObjectKind.Planet or
        MapObjectKind.Ship or
        MapObjectKind.Station;

    /// <summary>
    /// Gets whether this map layer permits the object to move between cells.
    /// </summary>
    public bool CanMove => Kind == MapObjectKind.Ship;

    /// <summary>
    /// Gets whether the object blocks direct-fire line of sight when it lies
    /// between the firing and target cells.
    /// </summary>
    /// <remarks>
    /// Only stars and planets block direct fire in the current prototype.
    /// Ships, stations, anomalies, and wreckage do not yet provide screening.
    /// </remarks>
    public bool BlocksDirectFire => Kind is
        MapObjectKind.Star or
        MapObjectKind.Planet;

    /// <summary>
    /// Gets whether a guided missile route may pass through this object's cell.
    /// </summary>
    /// <remarks>
    /// Stars and planets are currently impassable to missiles. Ships,
    /// stations, anomalies, and wreckage do not prevent route traversal;
    /// interception and collision effects belong to later combat systems.
    /// Route endpoints are handled separately by the route planner so a
    /// blocking body may still be the intended target.
    /// </remarks>
    public bool BlocksMissileTravel => Kind is
        MapObjectKind.Star or
        MapObjectKind.Planet;

    public static MapObject CreateStar(string id, string name) =>
        new(id, name, MapObjectKind.Star);

    public static MapObject CreatePlanet(string id, string name) =>
        new(id, name, MapObjectKind.Planet);

    public static MapObject CreateShip(string id, string name) =>
        new(id, name, MapObjectKind.Ship);

    public static MapObject CreateStation(string id, string name) =>
        new(id, name, MapObjectKind.Station);

    public static MapObject CreateAnomaly(string id, string name) =>
        new(id, name, MapObjectKind.Anomaly);

    public static MapObject CreateWreckage(string id, string name) =>
        new(id, name, MapObjectKind.Wreckage);
}
