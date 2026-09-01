using System;
using System.Collections.Generic;
using System.Linq;
using StarCluster.Core.Geometry;

namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Stores one deterministic guided-missile path through adjacent system-map
/// cells, including both the launch and target cells.
/// </summary>
public sealed class MissileRoute
{
    private readonly IReadOnlyList<HexCoord> _cells;

    internal MissileRoute(IEnumerable<HexCoord> cells)
    {
        ArgumentNullException.ThrowIfNull(cells);

        HexCoord[] materialized = cells.ToArray();

        if (materialized.Length == 0)
        {
            throw new ArgumentException(
                "A missile route must contain at least one cell.",
                nameof(cells));
        }

        for (int index = 1; index < materialized.Length; index++)
        {
            if (materialized[index - 1].DistanceTo(materialized[index]) != 1)
            {
                throw new ArgumentException(
                    "Consecutive missile-route cells must be adjacent.",
                    nameof(cells));
            }
        }

        _cells = Array.AsReadOnly(materialized);
    }

    /// <summary>
    /// Gets the ordered route cells, including origin and target.
    /// </summary>
    public IReadOnlyList<HexCoord> Cells => _cells;

    /// <summary>
    /// Gets the launch coordinate.
    /// </summary>
    public HexCoord Origin => _cells[0];

    /// <summary>
    /// Gets the target coordinate.
    /// </summary>
    public HexCoord Target => _cells[^1];

    /// <summary>
    /// Gets the number of single-hex transitions in the route.
    /// </summary>
    public int Distance => _cells.Count - 1;
}
