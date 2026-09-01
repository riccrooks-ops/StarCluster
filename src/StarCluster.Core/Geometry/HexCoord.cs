using System;
using System.Collections.Generic;

namespace StarCluster.Core.Geometry;

/// <summary>
/// Identifies one hexagonal map cell using axial coordinates.
/// </summary>
/// <remarks>
/// Axial coordinates store two values, Q and R. The third cube-coordinate
/// component, S, is derived from Q + R + S = 0.
/// </remarks>
public readonly record struct HexCoord(int Q, int R)
{
    /// <summary>
    /// Number of neighboring cells surrounding every hex.
    /// </summary>
    public const int DirectionCount = 6;

    private static readonly IReadOnlyList<HexCoord> DirectionVectors =
        Array.AsReadOnly(
            new[]
            {
                new HexCoord(1, 0),
                new HexCoord(1, -1),
                new HexCoord(0, -1),
                new HexCoord(-1, 0),
                new HexCoord(-1, 1),
                new HexCoord(0, 1),
            });

    /// <summary>
    /// The origin cell.
    /// </summary>
    public static HexCoord Zero { get; } = new(0, 0);

    /// <summary>
    /// Gets the derived third cube-coordinate component.
    /// </summary>
    public int S => -Q - R;

    /// <summary>
    /// Gets the six direction vectors in clockwise order.
    /// </summary>
    public static IReadOnlyList<HexCoord> Directions => DirectionVectors;

    /// <summary>
    /// Returns the adjacent cell in the requested direction.
    /// </summary>
    /// <param name="direction">A direction index from 0 through 5.</param>
    /// <exception cref="ArgumentOutOfRangeException">
    /// Thrown when <paramref name="direction"/> is outside the valid range.
    /// </exception>
    public HexCoord Neighbor(int direction)
    {
        if ((uint)direction >= DirectionCount)
        {
            throw new ArgumentOutOfRangeException(
                nameof(direction),
                direction,
                $"Direction must be from 0 through {DirectionCount - 1}.");
        }

        return this + DirectionVectors[direction];
    }

    /// <summary>
    /// Enumerates all six adjacent cells.
    /// </summary>
    public IEnumerable<HexCoord> Neighbors()
    {
        for (int direction = 0; direction < DirectionCount; direction++)
        {
            yield return Neighbor(direction);
        }
    }

    /// <summary>
    /// Returns the minimum number of single-hex moves required to reach another cell.
    /// </summary>
    public int DistanceTo(HexCoord other)
    {
        int deltaQ = Math.Abs(Q - other.Q);
        int deltaR = Math.Abs(R - other.R);
        int deltaS = Math.Abs(S - other.S);

        return (deltaQ + deltaR + deltaS) / 2;
    }

    /// <summary>
    /// Returns the distance from the origin.
    /// </summary>
    public int Length() => DistanceTo(Zero);

    public static HexCoord operator +(HexCoord left, HexCoord right) =>
        new(left.Q + right.Q, left.R + right.R);

    public static HexCoord operator -(HexCoord left, HexCoord right) =>
        new(left.Q - right.Q, left.R - right.R);
}
