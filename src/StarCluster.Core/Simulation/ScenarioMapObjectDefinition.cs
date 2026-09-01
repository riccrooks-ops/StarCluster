using System;
using StarCluster.Core.Geometry;

namespace StarCluster.Core.Simulation;

/// <summary>
/// One non-star map object placed before authoritative scenario initialization.
/// </summary>
public sealed class ScenarioMapObjectDefinition
{
    public ScenarioMapObjectDefinition(
        string id,
        string name,
        ScenarioMapObjectKind kind,
        HexCoord coordinate)
    {
        if (string.IsNullOrWhiteSpace(id))
        {
            throw new ArgumentException("A stable object ID is required.", nameof(id));
        }

        if (string.IsNullOrWhiteSpace(name))
        {
            throw new ArgumentException("An object name is required.", nameof(name));
        }

        if (!Enum.IsDefined(kind))
        {
            throw new ArgumentOutOfRangeException(nameof(kind));
        }

        if (kind == ScenarioMapObjectKind.Ship)
        {
            throw new ArgumentException(
                "Ships must be supplied through ScenarioShipDefinition so their tactical profiles are available.",
                nameof(kind));
        }

        Id = id;
        Name = name;
        Kind = kind;
        Coordinate = coordinate;
    }

    public string Id { get; }

    public string Name { get; }

    public ScenarioMapObjectKind Kind { get; }

    public HexCoord Coordinate { get; }
}
