using System;
using System.Linq;
using StarCluster.Core.Geometry;
using Xunit;

namespace StarCluster.Tests.Geometry;

public sealed class HexGeometryTests
{
    [Fact]
    public void CellsWithin_RejectsNegativeRadius()
    {
        Assert.Throws<ArgumentOutOfRangeException>(
            () => HexGeometry.CellsWithin(HexCoord.Zero, -1));
    }

    [Fact]
    public void CellsWithin_AtZeroContainsOnlyCenter()
    {
        var center = new HexCoord(4, -2);

        HexCoord[] actual = HexGeometry.CellsWithin(center, 0).ToArray();

        Assert.Equal(new[] { center }, actual);
    }

    [Fact]
    public void CellsWithin_AtOneContainsCenterAndNeighbors()
    {
        var center = new HexCoord(3, -2);
        HexCoord[] expected = center.Neighbors().Append(center).ToArray();

        HexCoord[] actual = HexGeometry.CellsWithin(center, 1).ToArray();

        Assert.Equal(7, actual.Length);
        Assert.Empty(expected.Except(actual));
        Assert.Empty(actual.Except(expected));
    }

    [Theory]
    [InlineData(0, 1)]
    [InlineData(1, 7)]
    [InlineData(2, 19)]
    [InlineData(3, 37)]
    [InlineData(5, 91)]
    public void CellsWithin_CountMatchesHexAreaFormula(int radius, int expected)
    {
        Assert.Equal(expected, HexGeometry.CellsWithin(HexCoord.Zero, radius).Count);
    }

    [Fact]
    public void CellsWithin_ContainsOnlyUniqueCellsInsideRadius()
    {
        const int radius = 4;
        var center = new HexCoord(-3, 5);
        HexCoord[] cells = HexGeometry.CellsWithin(center, radius).ToArray();

        Assert.Equal(cells.Length, cells.Distinct().Count());
        Assert.All(cells, cell => Assert.True(center.DistanceTo(cell) <= radius));
    }

    [Fact]
    public void CellsWithin_IsTranslationInvariant()
    {
        var center = new HexCoord(6, -4);
        HexCoord[] originCells = HexGeometry.CellsWithin(HexCoord.Zero, 2).ToArray();
        HexCoord[] translatedCells = HexGeometry.CellsWithin(center, 2).ToArray();
        HexCoord[] expected = originCells.Select(cell => cell + center).ToArray();

        Assert.Empty(expected.Except(translatedCells));
        Assert.Empty(translatedCells.Except(expected));
    }

    [Fact]
    public void Ring_RejectsNegativeRadius()
    {
        Assert.Throws<ArgumentOutOfRangeException>(
            () => HexGeometry.Ring(HexCoord.Zero, -1));
    }

    [Fact]
    public void Ring_AtZeroContainsOnlyCenter()
    {
        var center = new HexCoord(-2, 7);

        Assert.Equal(new[] { center }, HexGeometry.Ring(center, 0));
    }

    [Theory]
    [InlineData(1, 6)]
    [InlineData(2, 12)]
    [InlineData(3, 18)]
    [InlineData(5, 30)]
    public void Ring_CountMatchesCircumference(int radius, int expected)
    {
        Assert.Equal(expected, HexGeometry.Ring(HexCoord.Zero, radius).Count);
    }

    [Fact]
    public void Ring_ContainsUniqueCellsAtExactRadius()
    {
        const int radius = 3;
        var center = new HexCoord(2, -5);
        HexCoord[] cells = HexGeometry.Ring(center, radius).ToArray();

        Assert.Equal(cells.Length, cells.Distinct().Count());
        Assert.All(cells, cell => Assert.Equal(radius, center.DistanceTo(cell)));
    }

    [Fact]
    public void Ring_IsSubsetOfFilledRange()
    {
        var center = new HexCoord(1, 1);
        HexCoord[] ring = HexGeometry.Ring(center, 4).ToArray();
        HexCoord[] filledRange = HexGeometry.CellsWithin(center, 4).ToArray();

        Assert.Empty(ring.Except(filledRange));
    }

    [Fact]
    public void Line_AtSameCoordinateContainsOneCell()
    {
        var coordinate = new HexCoord(5, -3);

        Assert.Equal(new[] { coordinate }, HexGeometry.Line(coordinate, coordinate));
    }

    [Theory]
    [InlineData(0, 0, 4, 0)]
    [InlineData(0, 0, 3, -3)]
    [InlineData(-2, 5, 4, -1)]
    [InlineData(7, -4, 2, 3)]
    public void Line_IncludesEndpointsAndShortestStepCount(
        int startQ,
        int startR,
        int endQ,
        int endR)
    {
        var start = new HexCoord(startQ, startR);
        var end = new HexCoord(endQ, endR);
        HexCoord[] line = HexGeometry.Line(start, end).ToArray();

        Assert.Equal(start, line[0]);
        Assert.Equal(end, line[^1]);
        Assert.Equal(start.DistanceTo(end) + 1, line.Length);
    }

    [Fact]
    public void Line_UsesOnlyAdjacentSteps()
    {
        HexCoord[] line = HexGeometry
            .Line(new HexCoord(-4, 2), new HexCoord(5, -3))
            .ToArray();

        for (int index = 1; index < line.Length; index++)
        {
            Assert.Equal(1, line[index - 1].DistanceTo(line[index]));
        }
    }

    [Fact]
    public void Line_AlongQAxisMatchesExpectedCells()
    {
        HexCoord[] expected =
        {
            new(0, 0),
            new(1, 0),
            new(2, 0),
            new(3, 0),
        };

        Assert.Equal(expected, HexGeometry.Line(expected[0], expected[^1]));
    }

    [Fact]
    public void Line_AlongDiagonalMatchesExpectedCells()
    {
        HexCoord[] expected =
        {
            new(0, 0),
            new(1, -1),
            new(2, -2),
            new(3, -3),
        };

        Assert.Equal(expected, HexGeometry.Line(expected[0], expected[^1]));
    }

    [Fact]
    public void Line_OffAxisMatchesExpectedCells()
    {
        HexCoord[] expected =
        {
            new(0, 0),
            new(1, 0),
            new(2, -1),
            new(3, -1),
        };

        Assert.Equal(expected, HexGeometry.Line(expected[0], expected[^1]));
    }

    [Fact]
    public void Line_IsTranslationInvariant()
    {
        var offset = new HexCoord(7, -2);
        var start = new HexCoord(-1, 1);
        var end = new HexCoord(4, -2);
        HexCoord[] original = HexGeometry.Line(start, end).ToArray();
        HexCoord[] translated = HexGeometry.Line(start + offset, end + offset).ToArray();
        HexCoord[] expected = original.Select(cell => cell + offset).ToArray();

        Assert.Equal(expected, translated);
    }
}
