using System;
using System.Collections.Generic;

namespace StarCluster.Core.Geometry;

/// <summary>
/// Describes one range step of a center-to-center hex trace.
/// </summary>
/// <remarks>
/// An ordinary step touches one hex. When the geometric line lies exactly
/// along a boundary, the step touches the two adjacent hexes.
/// </remarks>
public sealed class HexLineStep
{
    internal HexLineStep(
        int distanceFromStart,
        IReadOnlyList<HexCoord> cells)
    {
        if (distanceFromStart < 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(distanceFromStart),
                distanceFromStart,
                "Distance from the start cannot be negative.");
        }

        Cells = cells ?? throw new ArgumentNullException(nameof(cells));

        if (cells.Count is < 1 or > 2)
        {
            throw new ArgumentException(
                "A hex-line step must touch one or two cells.",
                nameof(cells));
        }

        DistanceFromStart = distanceFromStart;
    }

    /// <summary>
    /// Gets the number of hex-range steps from the trace origin.
    /// </summary>
    public int DistanceFromStart { get; }

    /// <summary>
    /// Gets the one ordinary cell or two boundary-adjacent cells touched at
    /// this range step.
    /// </summary>
    public IReadOnlyList<HexCoord> Cells { get; }

    /// <summary>
    /// Gets whether the trace lies exactly along a boundary at this step.
    /// </summary>
    public bool IsBoundary => Cells.Count == 2;
}
