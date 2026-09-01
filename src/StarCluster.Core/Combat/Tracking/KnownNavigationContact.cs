using System;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;

namespace StarCluster.Core.Combat.Tracking;

/// <summary>
/// Stable charted object supplied by navigation knowledge rather than tactical
/// detection. Every star is pre-known by policy.
/// </summary>
public sealed class KnownNavigationContact
{
    internal KnownNavigationContact(
        string objectId,
        string name,
        MapObjectKind kind,
        HexCoord coordinate)
    {
        if (string.IsNullOrWhiteSpace(objectId))
        {
            throw new ArgumentException("An object ID is required.", nameof(objectId));
        }

        ObjectId = objectId;
        Name = name;
        Kind = kind;
        Coordinate = coordinate;
    }

    public string ObjectId { get; }

    public string Name { get; }

    public MapObjectKind Kind { get; }

    public HexCoord Coordinate { get; }
}
