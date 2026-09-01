using System;
using System.Collections.Generic;
using System.Linq;
using StarCluster.Core.Geometry;

namespace StarCluster.Core.Movement;

/// <summary>
/// Immutable ordered route for one tactical ship movement command.
/// </summary>
public sealed class ShipMovementRoute
{
    private readonly IReadOnlyList<HexCoord> _path;

    public ShipMovementRoute(IEnumerable<HexCoord> path)
    {
        ArgumentNullException.ThrowIfNull(path);

        HexCoord[] materialized = path.ToArray();
        if (materialized.Length == 0)
        {
            throw new ArgumentException("A movement route must contain at least one coordinate.", nameof(path));
        }

        for (int index = 1; index < materialized.Length; index++)
        {
            if (materialized[index - 1].DistanceTo(materialized[index]) != 1)
            {
                throw new ArgumentException(
                    "Every consecutive movement-route coordinate must be adjacent.",
                    nameof(path));
            }
        }

        _path = Array.AsReadOnly(materialized);
    }

    public IReadOnlyList<HexCoord> Path => _path;

    public HexCoord Origin => _path[0];

    public HexCoord Destination => _path[^1];

    public int Distance => _path.Count - 1;
}
