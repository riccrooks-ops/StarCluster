using System.Linq;
using StarCluster.Core.Geometry;
using Xunit;

namespace StarCluster.Tests.Geometry;

public sealed class HexSupercoverLineTests
{
    [Fact]
    public void SameCoordinateReturnsOneCell()
    {
        var coordinate = new HexCoord(2, -1);

        HexCoord[] actual = HexGeometry
            .SupercoverLine(coordinate, coordinate)
            .ToArray();

        Assert.Equal(new[] { coordinate }, actual);
    }

    [Fact]
    public void UnambiguousLineMatchesOrdinaryLine()
    {
        var start = HexCoord.Zero;
        var end = new HexCoord(3, 0);

        Assert.Equal(
            HexGeometry.Line(start, end).ToArray(),
            HexGeometry.SupercoverLine(start, end).ToArray());
    }

    [Fact]
    public void BoundaryLineIncludesBothMiddleCells()
    {
        HexCoord[] actual = HexGeometry
            .SupercoverLine(HexCoord.Zero, new HexCoord(2, -1))
            .ToArray();

        HexCoord[] expected =
        [
            HexCoord.Zero,
            new HexCoord(1, 0),
            new HexCoord(1, -1),
            new HexCoord(2, -1),
        ];

        Assert.Equal(expected, actual);
    }

    [Fact]
    public void DiagonalBoundaryLineIncludesBothMiddleCells()
    {
        HexCoord[] actual = HexGeometry
            .SupercoverLine(HexCoord.Zero, new HexCoord(1, 1))
            .ToArray();

        HexCoord[] expected =
        [
            HexCoord.Zero,
            new HexCoord(1, 0),
            new HexCoord(0, 1),
            new HexCoord(1, 1),
        ];

        Assert.Equal(expected, actual);
    }

    [Fact]
    public void LongerBoundaryLineIncludesBothSidesAtEveryTie()
    {
        HexCoord[] actual = HexGeometry
            .SupercoverLine(HexCoord.Zero, new HexCoord(4, -2))
            .ToArray();

        HexCoord[] expected =
        [
            HexCoord.Zero,
            new HexCoord(1, 0),
            new HexCoord(1, -1),
            new HexCoord(2, -1),
            new HexCoord(3, -1),
            new HexCoord(3, -2),
            new HexCoord(4, -2),
        ];

        Assert.Equal(expected, actual);
    }

    [Fact]
    public void ReverseTraceTouchesTheSameSetOfCells()
    {
        var start = new HexCoord(-2, 1);
        var end = new HexCoord(2, -1);

        HexCoord[] forward = HexGeometry.SupercoverLine(start, end).ToArray();
        HexCoord[] reverse = HexGeometry.SupercoverLine(end, start).ToArray();

        Assert.Empty(forward.Except(reverse));
        Assert.Empty(reverse.Except(forward));
    }

    [Fact]
    public void TraceContainsNoDuplicateCoordinates()
    {
        HexCoord[] actual = HexGeometry
            .SupercoverLine(new HexCoord(-4, 2), new HexCoord(4, -2))
            .ToArray();

        Assert.Equal(actual.Length, actual.Distinct().Count());
    }

    [Fact]
    public void ConsecutiveReturnedCellsRemainAdjacent()
    {
        HexCoord[] actual = HexGeometry
            .SupercoverLine(HexCoord.Zero, new HexCoord(4, -2))
            .ToArray();

        for (int index = 1; index < actual.Length; index++)
        {
            Assert.Equal(1, actual[index - 1].DistanceTo(actual[index]));
        }
    }
}
