using System.Linq;
using StarCluster.Core.Geometry;
using Xunit;

namespace StarCluster.Tests.Geometry;

public sealed class HexSupercoverStepTests
{
    [Fact]
    public void SameCoordinateReturnsOneOrdinaryStep()
    {
        var coordinate = new HexCoord(2, -1);

        HexLineStep step = Assert.Single(
            HexGeometry.SupercoverSteps(coordinate, coordinate));

        Assert.Equal(0, step.DistanceFromStart);
        Assert.False(step.IsBoundary);
        Assert.Equal(new[] { coordinate }, step.Cells);
    }

    [Fact]
    public void StepCountEqualsDistancePlusOne()
    {
        var start = new HexCoord(-2, 1);
        var end = new HexCoord(3, -1);

        Assert.Equal(
            start.DistanceTo(end) + 1,
            HexGeometry.SupercoverSteps(start, end).Count);
    }

    [Fact]
    public void OrdinaryLineHasOneCellAtEveryStep()
    {
        HexLineStep[] steps = HexGeometry
            .SupercoverSteps(HexCoord.Zero, new HexCoord(4, 0))
            .ToArray();

        Assert.All(steps, step => Assert.Single(step.Cells));
        Assert.DoesNotContain(steps, step => step.IsBoundary);
    }

    [Fact]
    public void ExactBoundaryStepContainsBothAdjacentCells()
    {
        HexLineStep[] steps = HexGeometry
            .SupercoverSteps(HexCoord.Zero, new HexCoord(2, -1))
            .ToArray();

        Assert.Equal(3, steps.Length);
        Assert.False(steps[0].IsBoundary);
        Assert.True(steps[1].IsBoundary);
        Assert.False(steps[2].IsBoundary);
        Assert.Equal(
            new[] { new HexCoord(1, 0), new HexCoord(1, -1) },
            steps[1].Cells);
    }

    [Fact]
    public void LongerTracePreservesMultipleBoundarySteps()
    {
        HexLineStep[] steps = HexGeometry
            .SupercoverSteps(HexCoord.Zero, new HexCoord(4, -2))
            .ToArray();

        Assert.Equal(new[] { 1, 3 },
            steps.Where(step => step.IsBoundary)
                .Select(step => step.DistanceFromStart));
    }

    [Fact]
    public void DistanceFromStartAdvancesSequentially()
    {
        HexLineStep[] steps = HexGeometry
            .SupercoverSteps(new HexCoord(-3, 1), new HexCoord(3, -2))
            .ToArray();

        Assert.Equal(
            Enumerable.Range(0, steps.Length),
            steps.Select(step => step.DistanceFromStart));
    }

    [Fact]
    public void FlattenedStepsMatchSupercoverLine()
    {
        var start = new HexCoord(-4, 2);
        var end = new HexCoord(4, -2);

        HexCoord[] flattened = HexGeometry
            .SupercoverSteps(start, end)
            .SelectMany(step => step.Cells)
            .Distinct()
            .ToArray();

        Assert.Equal(HexGeometry.SupercoverLine(start, end).ToArray(), flattened);
    }

    [Fact]
    public void ReverseTraceHasSameNumberOfBoundarySteps()
    {
        var start = new HexCoord(-4, 2);
        var end = new HexCoord(4, -2);

        int forward = HexGeometry
            .SupercoverSteps(start, end)
            .Count(step => step.IsBoundary);
        int reverse = HexGeometry
            .SupercoverSteps(end, start)
            .Count(step => step.IsBoundary);

        Assert.Equal(forward, reverse);
    }
}
