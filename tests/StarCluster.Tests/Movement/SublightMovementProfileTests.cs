using System;
using StarCluster.Core.Movement;
using Xunit;

namespace StarCluster.Tests.Movement;

public sealed class SublightMovementProfileTests
{
    [Fact]
    public void ConstructorStoresExplicitTechnologyAndAllowance()
    {
        var profile = new SublightMovementProfile(4, 3);

        Assert.Equal(4, profile.TechnologyLevel);
        Assert.Equal(3, profile.MaximumHexesPerTurn);
    }

    [Fact]
    public void ConstructorAllowsZeroMovementForDisabledPropulsion()
    {
        var profile = new SublightMovementProfile(2, 0);

        Assert.Equal(0, profile.MaximumHexesPerTurn);
    }

    [Fact]
    public void ConstructorRejectsTechnologyBelowOne()
    {
        Assert.Throws<ArgumentOutOfRangeException>(
            () => new SublightMovementProfile(0, 1));
    }

    [Fact]
    public void ConstructorRejectsTechnologyAboveNine()
    {
        Assert.Throws<ArgumentOutOfRangeException>(
            () => new SublightMovementProfile(10, 1));
    }

    [Fact]
    public void ConstructorRejectsNegativeMovement()
    {
        Assert.Throws<ArgumentOutOfRangeException>(
            () => new SublightMovementProfile(1, -1));
    }

    [Fact]
    public void TechnologyLevelDoesNotImplicitlyDetermineAllowance()
    {
        var slowerHighTechnology = new SublightMovementProfile(8, 2);
        var fasterLowTechnology = new SublightMovementProfile(2, 4);

        Assert.True(
            slowerHighTechnology.MaximumHexesPerTurn <
            fasterLowTechnology.MaximumHexesPerTurn);
    }
}
