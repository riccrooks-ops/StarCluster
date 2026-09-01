using System;
using StarCluster.Core.Combat.Missiles;
using Xunit;

namespace StarCluster.Tests.Combat.Missiles;

public sealed class MissileFlightProfileTests
{
    [Fact]
    public void TechnologyLevelOneIsAccepted()
    {
        var profile = new MissileFlightProfile(1, 4, 1);

        Assert.Equal(1, profile.TechnologyLevel);
        Assert.Equal(4, profile.MaximumRange);
        Assert.Equal(1, profile.SpeedHexesPerTurn);
    }

    [Fact]
    public void TechnologyLevelNineIsAccepted()
    {
        var profile = new MissileFlightProfile(9, 12, 4);

        Assert.Equal(9, profile.TechnologyLevel);
    }

    [Theory]
    [InlineData(0)]
    [InlineData(10)]
    [InlineData(-1)]
    public void TechnologyLevelOutsideOneThroughNineThrows(int technologyLevel)
    {
        Assert.Throws<ArgumentOutOfRangeException>(() =>
            new MissileFlightProfile(technologyLevel, 4, 1));
    }

    [Theory]
    [InlineData(0)]
    [InlineData(-1)]
    public void NonpositiveMaximumRangeThrows(int maximumRange)
    {
        Assert.Throws<ArgumentOutOfRangeException>(() =>
            new MissileFlightProfile(1, maximumRange, 1));
    }

    [Theory]
    [InlineData(0)]
    [InlineData(-1)]
    public void NonpositiveSpeedThrows(int speed)
    {
        Assert.Throws<ArgumentOutOfRangeException>(() =>
            new MissileFlightProfile(1, 4, speed));
    }

    [Theory]
    [InlineData(0, 3, 0)]
    [InlineData(1, 3, 1)]
    [InlineData(3, 3, 1)]
    [InlineData(4, 3, 2)]
    [InlineData(7, 3, 3)]
    [InlineData(9, 3, 3)]
    [InlineData(10, 3, 4)]
    public void TravelTurnsUseCeilingDivision(
        int routedDistance,
        int speed,
        int expectedTurns)
    {
        var profile = new MissileFlightProfile(1, 20, speed);

        Assert.Equal(
            expectedTurns,
            profile.EstimateTravelTurns(routedDistance));
    }

    [Fact]
    public void NegativeRoutedDistanceThrows()
    {
        var profile = new MissileFlightProfile(1, 4, 1);

        Assert.Throws<ArgumentOutOfRangeException>(() =>
            profile.EstimateTravelTurns(-1));
    }
}
