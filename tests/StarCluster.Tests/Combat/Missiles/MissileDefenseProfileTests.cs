using System;
using StarCluster.Core.Combat.Missiles;
using Xunit;

namespace StarCluster.Tests.Combat.Missiles;

public sealed class MissileDefenseProfileTests
{
    [Fact]
    public void StoresDataDrivenDefenseValues()
    {
        var profile = new MissileDefenseProfile(3, 2, 1);

        Assert.Equal(3, profile.TechnologyLevel);
        Assert.Equal(2, profile.InterceptionRangeHexes);
        Assert.Equal(1, profile.MaximumAttemptsPerPhase);
    }

    [Fact]
    public void NegativeTechnologyLevelIsRejected()
    {
        Assert.Throws<ArgumentOutOfRangeException>(
            () => new MissileDefenseProfile(-1, 1, 1));
    }

    [Fact]
    public void NegativeInterceptionRangeIsRejected()
    {
        Assert.Throws<ArgumentOutOfRangeException>(
            () => new MissileDefenseProfile(1, -1, 1));
    }

    [Fact]
    public void NonpositiveAttemptBudgetIsRejected()
    {
        Assert.Throws<ArgumentOutOfRangeException>(
            () => new MissileDefenseProfile(1, 1, 0));
    }
}
