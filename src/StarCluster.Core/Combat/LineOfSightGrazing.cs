using System;
using System.Collections.Generic;
using StarCluster.Core.Geometry;

namespace StarCluster.Core.Combat;

/// <summary>
/// Describes one exact-boundary grazing encountered by a direct-fire trace.
/// </summary>
public sealed class LineOfSightGrazing
{
    internal LineOfSightGrazing(
        int rangeStep,
        HexCoord blockedCoordinate,
        HexCoord openCoordinate,
        IReadOnlyList<LineOfSightBlocker> blockers)
    {
        if (rangeStep <= 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(rangeStep),
                rangeStep,
                "A grazing must occur after the origin cell.");
        }

        if (blockedCoordinate == openCoordinate)
        {
            throw new ArgumentException(
                "The blocked and open boundary coordinates must differ.",
                nameof(openCoordinate));
        }

        Blockers = blockers ?? throw new ArgumentNullException(nameof(blockers));

        if (blockers.Count == 0)
        {
            throw new ArgumentException(
                "A grazing must identify at least one blocking object.",
                nameof(blockers));
        }

        RangeStep = rangeStep;
        BlockedCoordinate = blockedCoordinate;
        OpenCoordinate = openCoordinate;
    }

    /// <summary>
    /// Gets the range step at which the grazing occurs.
    /// </summary>
    public int RangeStep { get; }

    /// <summary>
    /// Gets the boundary-adjacent coordinate containing the star or planet.
    /// </summary>
    public HexCoord BlockedCoordinate { get; }

    /// <summary>
    /// Gets the opposite boundary-adjacent coordinate that remains open.
    /// </summary>
    public HexCoord OpenCoordinate { get; }

    /// <summary>
    /// Gets the objects responsible for this grazing event.
    /// </summary>
    public IReadOnlyList<LineOfSightBlocker> Blockers { get; }
}
