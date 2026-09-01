using System;
using System.Collections.Generic;

namespace StarCluster.Core.Geometry;

/// <summary>
/// Provides deterministic algorithms that operate on axial hex coordinates.
/// </summary>
public static class HexGeometry
{
    private const double LineNudge = 1e-6;

    /// <summary>
    /// Returns the center cell and every cell no farther than
    /// <paramref name="radius"/> moves from it.
    /// </summary>
    /// <exception cref="ArgumentOutOfRangeException">
    /// Thrown when <paramref name="radius"/> is negative.
    /// </exception>
    public static IReadOnlyList<HexCoord> CellsWithin(HexCoord center, int radius)
    {
        ValidateRadius(radius);

        int estimatedCount = 1 + (3 * radius * (radius + 1));
        var cells = new List<HexCoord>(estimatedCount);

        for (int deltaQ = -radius; deltaQ <= radius; deltaQ++)
        {
            int minimumDeltaR = Math.Max(-radius, -deltaQ - radius);
            int maximumDeltaR = Math.Min(radius, -deltaQ + radius);

            for (int deltaR = minimumDeltaR;
                 deltaR <= maximumDeltaR;
                 deltaR++)
            {
                cells.Add(center + new HexCoord(deltaQ, deltaR));
            }
        }

        return cells.AsReadOnly();
    }

    /// <summary>
    /// Returns every cell exactly <paramref name="radius"/> moves from
    /// <paramref name="center"/> in a stable traversal order.
    /// </summary>
    /// <remarks>
    /// Radius zero returns only the center cell. A positive-radius ring
    /// contains exactly six times the radius cells.
    /// </remarks>
    /// <exception cref="ArgumentOutOfRangeException">
    /// Thrown when <paramref name="radius"/> is negative.
    /// </exception>
    public static IReadOnlyList<HexCoord> Ring(HexCoord center, int radius)
    {
        ValidateRadius(radius);

        if (radius == 0)
        {
            return Array.AsReadOnly(new[] { center });
        }

        var cells = new List<HexCoord>(HexCoord.DirectionCount * radius);

        // Begin at the southwest corner of the ring, then walk one complete
        // side in each of the six axial directions.
        HexCoord current = center + Scale(HexCoord.Directions[4], radius);

        for (int direction = 0;
             direction < HexCoord.DirectionCount;
             direction++)
        {
            for (int step = 0; step < radius; step++)
            {
                cells.Add(current);
                current = current.Neighbor(direction);
            }
        }

        return cells.AsReadOnly();
    }

    /// <summary>
    /// Returns a deterministic shortest center-to-center hex line, including
    /// both endpoints.
    /// </summary>
    /// <remarks>
    /// Exact rounding ties are resolved toward one consistent side. Use
    /// <see cref="SupercoverLine"/> when every hex touched by an exact
    /// boundary line must be included.
    /// </remarks>
    public static IReadOnlyList<HexCoord> Line(HexCoord start, HexCoord end) =>
        LineWithNudge(
            start,
            end,
            LineNudge,
            LineNudge,
            -2 * LineNudge);

    /// <summary>
    /// Returns one trace step for every hex of range from
    /// <paramref name="start"/> to <paramref name="end"/>, including both
    /// endpoints.
    /// </summary>
    /// <remarks>
    /// An ordinary step contains one cell. When the segment lies exactly
    /// along a boundary, the step contains both adjacent cells. Preserving
    /// this grouping allows combat rules to distinguish a grazing line from
    /// a line that passes through a blocking cell.
    /// </remarks>
    public static IReadOnlyList<HexLineStep> SupercoverSteps(
        HexCoord start,
        HexCoord end)
    {
        IReadOnlyList<HexCoord> firstSide = LineWithNudge(
            start,
            end,
            LineNudge,
            LineNudge,
            -2 * LineNudge);

        IReadOnlyList<HexCoord> secondSide = LineWithNudge(
            start,
            end,
            -LineNudge,
            -LineNudge,
            2 * LineNudge);

        if (firstSide.Count != secondSide.Count)
        {
            throw new InvalidOperationException(
                "Opposite-side hex traces produced different step counts.");
        }

        var steps = new List<HexLineStep>(firstSide.Count);

        for (int index = 0; index < firstSide.Count; index++)
        {
            HexCoord first = firstSide[index];
            HexCoord second = secondSide[index];

            IReadOnlyList<HexCoord> cells = first == second
                ? Array.AsReadOnly(new[] { first })
                : Array.AsReadOnly(new[] { first, second });

            steps.Add(new HexLineStep(index, cells));
        }

        return steps.AsReadOnly();
    }

    /// <summary>
    /// Returns every hex touched by the center-to-center segment from
    /// <paramref name="start"/> to <paramref name="end"/>, including both
    /// endpoints.
    /// </summary>
    /// <remarks>
    /// Most lines touch one cell at each range step. When the segment lies
    /// exactly along a boundary, both adjacent cells are returned. The order
    /// is deterministic and advances outward from the start. Use
    /// <see cref="SupercoverSteps"/> when the per-range grouping matters.
    /// </remarks>
    public static IReadOnlyList<HexCoord> SupercoverLine(
        HexCoord start,
        HexCoord end)
    {
        IReadOnlyList<HexLineStep> steps = SupercoverSteps(start, end);
        var cells = new List<HexCoord>(steps.Count * 2);
        var seen = new HashSet<HexCoord>();

        foreach (HexLineStep step in steps)
        {
            foreach (HexCoord coordinate in step.Cells)
            {
                AddIfNew(coordinate, cells, seen);
            }
        }

        return cells.AsReadOnly();
    }

    private static void ValidateRadius(int radius)
    {
        if (radius < 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(radius),
                radius,
                "Radius cannot be negative.");
        }
    }

    private static HexCoord Scale(HexCoord coordinate, int factor) =>
        new(coordinate.Q * factor, coordinate.R * factor);

    private static double Lerp(double start, double end, double amount) =>
        start + ((end - start) * amount);

    private static IReadOnlyList<HexCoord> LineWithNudge(
        HexCoord start,
        HexCoord end,
        double nudgeQ,
        double nudgeR,
        double nudgeS)
    {
        int distance = start.DistanceTo(end);

        if (distance == 0)
        {
            return Array.AsReadOnly(new[] { start });
        }

        var cells = new List<HexCoord>(distance + 1);

        double startQ = start.Q + nudgeQ;
        double startR = start.R + nudgeR;
        double startS = start.S + nudgeS;
        double endQ = end.Q + nudgeQ;
        double endR = end.R + nudgeR;
        double endS = end.S + nudgeS;

        for (int step = 0; step <= distance; step++)
        {
            double amount = step / (double)distance;
            double q = Lerp(startQ, endQ, amount);
            double r = Lerp(startR, endR, amount);
            double s = Lerp(startS, endS, amount);

            cells.Add(RoundCube(q, r, s));
        }

        return cells.AsReadOnly();
    }

    private static void AddIfNew(
        HexCoord coordinate,
        ICollection<HexCoord> cells,
        ISet<HexCoord> seen)
    {
        if (seen.Add(coordinate))
        {
            cells.Add(coordinate);
        }
    }

    private static HexCoord RoundCube(double q, double r, double s)
    {
        int roundedQ = (int)Math.Round(q, MidpointRounding.AwayFromZero);
        int roundedR = (int)Math.Round(r, MidpointRounding.AwayFromZero);
        int roundedS = (int)Math.Round(s, MidpointRounding.AwayFromZero);

        double qDifference = Math.Abs(roundedQ - q);
        double rDifference = Math.Abs(roundedR - r);
        double sDifference = Math.Abs(roundedS - s);

        // Restore the cube-coordinate invariant after independently rounding
        // all three components: Q + R + S must equal zero.
        if (qDifference > rDifference && qDifference > sDifference)
        {
            roundedQ = -roundedR - roundedS;
        }
        else if (rDifference > sDifference)
        {
            roundedR = -roundedQ - roundedS;
        }
        else
        {
            roundedS = -roundedQ - roundedR;
        }

        return new HexCoord(roundedQ, roundedR);
    }
}
