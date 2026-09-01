using System;
using System.Collections.Generic;
using System.Linq;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;
using Xunit;

namespace StarCluster.Tests.Maps;

public sealed class HexMapTests
{
    [Fact]
    public void CreateHexagon_RejectsNegativeRadius()
    {
        Assert.Throws<ArgumentOutOfRangeException>(
            () => HexMap.CreateHexagon(-1));
    }

    [Fact]
    public void RadiusZero_ContainsOnlyOrigin()
    {
        HexMap map = HexMap.CreateHexagon(0);

        Assert.Equal(0, map.Radius);
        Assert.Equal(1, map.Diameter);
        Assert.Equal(1, map.CellCount);
        Assert.Equal(new[] { HexCoord.Zero }, map.Cells);
        Assert.True(map.IsBoundary(HexCoord.Zero));
    }

    [Theory]
    [InlineData(1, 3, 7)]
    [InlineData(5, 11, 91)]
    [InlineData(8, 17, 217)]
    public void DimensionsMatchHexagonFormula(
        int radius,
        int expectedDiameter,
        int expectedCellCount)
    {
        HexMap map = HexMap.CreateHexagon(radius);

        Assert.Equal(radius, map.Radius);
        Assert.Equal(expectedDiameter, map.Diameter);
        Assert.Equal(expectedCellCount, map.CellCount);
    }

    [Fact]
    public void CellsAreUniqueAndInsideConfiguredRadius()
    {
        HexMap map = HexMap.CreateHexagon(5);

        Assert.Equal(map.CellCount, map.Cells.Distinct().Count());
        Assert.All(map.Cells, cell => Assert.True(cell.Length() <= map.Radius));
    }

    [Fact]
    public void ContainsDistinguishesExistingAndOutsideCoordinates()
    {
        HexMap map = HexMap.CreateHexagon(5);

        Assert.True(map.Contains(HexCoord.Zero));
        Assert.True(map.Contains(new HexCoord(5, 0)));
        Assert.True(map.Contains(new HexCoord(3, 2)));
        Assert.False(map.Contains(new HexCoord(6, 0)));
        Assert.False(map.Contains(new HexCoord(5, 1)));
    }

    [Fact]
    public void IsBoundaryRecognizesOnlyTheOuterRing()
    {
        HexMap map = HexMap.CreateHexagon(5);

        Assert.True(map.IsBoundary(new HexCoord(5, 0)));
        Assert.True(map.IsBoundary(new HexCoord(0, -5)));
        Assert.False(map.IsBoundary(HexCoord.Zero));
        Assert.False(map.IsBoundary(new HexCoord(4, 0)));
        Assert.False(map.IsBoundary(new HexCoord(6, 0)));
    }

    [Fact]
    public void CenterHasSixNeighborsOnPositiveRadiusMap()
    {
        HexMap map = HexMap.CreateHexagon(5);

        IReadOnlyList<HexCoord> neighbors = map.NeighborsOf(HexCoord.Zero);

        Assert.Equal(HexCoord.DirectionCount, neighbors.Count);
        Assert.Equal(HexCoord.Directions, neighbors);
    }

    [Fact]
    public void CornerHasOnlyThreeNeighborsInsideMap()
    {
        HexMap map = HexMap.CreateHexagon(5);
        var corner = new HexCoord(5, 0);
        HexCoord[] expected =
        {
            new(5, -1),
            new(4, 0),
            new(4, 1),
        };

        IReadOnlyList<HexCoord> actual = map.NeighborsOf(corner);

        Assert.Equal(expected, actual);
    }

    [Fact]
    public void NeighborsOf_RejectsCoordinateOutsideMap()
    {
        HexMap map = HexMap.CreateHexagon(5);

        Assert.Throws<ArgumentOutOfRangeException>(
            () => map.NeighborsOf(new HexCoord(6, 0)));
    }

    [Fact]
    public void CurrentDesignDefaultsMatchDocumentedMapSizes()
    {
        Assert.Equal(5, MapDefaults.SystemRadius);
        Assert.Equal(11, MapDefaults.SystemDiameter);
        Assert.Equal(8, MapDefaults.ClusterRadius);
        Assert.Equal(17, MapDefaults.ClusterDiameter);
    }

    [Fact]
    public void DefaultsCanCreateMapsWithoutEmbeddingSizesInHexMap()
    {
        HexMap systemMap = HexMap.CreateHexagon(MapDefaults.SystemRadius);
        HexMap clusterMap = HexMap.CreateHexagon(MapDefaults.ClusterRadius);

        Assert.Equal(MapDefaults.SystemDiameter, systemMap.Diameter);
        Assert.Equal(MapDefaults.ClusterDiameter, clusterMap.Diameter);
        Assert.Equal(91, systemMap.CellCount);
        Assert.Equal(217, clusterMap.CellCount);
    }
}
