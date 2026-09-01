using System;
using System.Linq;
using StarCluster.Core.Geometry;
using Xunit;

namespace StarCluster.Tests.Geometry;

public sealed class HexCoordTests
{
    [Fact]
    public void S_IsDerivedFromQAndR()
    {
        var coordinate = new HexCoord(4, -1);

        Assert.Equal(-3, coordinate.S);
        Assert.Equal(0, coordinate.Q + coordinate.R + coordinate.S);
    }

    [Fact]
    public void RecordStruct_UsesValueEquality()
    {
        var first = new HexCoord(2, -3);
        var second = new HexCoord(2, -3);
        var different = new HexCoord(2, -2);

        Assert.Equal(first, second);
        Assert.NotEqual(first, different);
    }

    [Fact]
    public void Directions_ContainsSixUniqueUnitVectors()
    {
        Assert.Equal(HexCoord.DirectionCount, HexCoord.Directions.Count);
        Assert.Equal(HexCoord.DirectionCount, HexCoord.Directions.Distinct().Count());
        Assert.All(HexCoord.Directions, direction => Assert.Equal(1, direction.Length()));
    }

    [Fact]
    public void Neighbor_ReturnsExpectedCellsInClockwiseOrder()
    {
        var origin = HexCoord.Zero;
        HexCoord[] expected =
        {
            new(1, 0),
            new(1, -1),
            new(0, -1),
            new(-1, 0),
            new(-1, 1),
            new(0, 1),
        };

        HexCoord[] actual = Enumerable
            .Range(0, HexCoord.DirectionCount)
            .Select(origin.Neighbor)
            .ToArray();

        Assert.Equal(expected, actual);
    }

    [Fact]
    public void Neighbors_ReturnsAllSixAdjacentCells()
    {
        var center = new HexCoord(3, -2);

        HexCoord[] actual = center.Neighbors().ToArray();

        Assert.Equal(HexCoord.DirectionCount, actual.Length);
        Assert.All(actual, neighbor => Assert.Equal(1, center.DistanceTo(neighbor)));
        Assert.Equal(HexCoord.DirectionCount, actual.Distinct().Count());
    }

    [Theory]
    [InlineData(-1)]
    [InlineData(6)]
    [InlineData(100)]
    public void Neighbor_RejectsInvalidDirection(int direction)
    {
        Assert.Throws<ArgumentOutOfRangeException>(
            () => HexCoord.Zero.Neighbor(direction));
    }

    [Theory]
    [InlineData(0, 0, 0)]
    [InlineData(1, 0, 1)]
    [InlineData(2, -1, 2)]
    [InlineData(-4, 1, 4)]
    [InlineData(3, 3, 6)]
    public void Length_ReturnsDistanceFromOrigin(int q, int r, int expected)
    {
        var coordinate = new HexCoord(q, r);

        Assert.Equal(expected, coordinate.Length());
    }

    [Fact]
    public void DistanceTo_IsSymmetric()
    {
        var first = new HexCoord(-2, 5);
        var second = new HexCoord(4, -1);

        Assert.Equal(first.DistanceTo(second), second.DistanceTo(first));
        Assert.Equal(6, first.DistanceTo(second));
    }

    [Fact]
    public void AdditionAndSubtraction_TranslateCoordinates()
    {
        var start = new HexCoord(2, -1);
        var offset = new HexCoord(-3, 4);

        Assert.Equal(new HexCoord(-1, 3), start + offset);
        Assert.Equal(start, (start + offset) - offset);
    }
}
