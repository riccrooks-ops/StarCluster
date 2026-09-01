using StarCluster.Core.Combat.Components;
using StarCluster.Core.Combat.InternalDamage;
using StarCluster.Core.Combat.Tactics;
using Xunit;

namespace StarCluster.Tests.Combat.Tactics;

public sealed class TechnologyMovementRulesTests
{
    [Fact]
    public void Tl1ShipMovesOneHex()
    {
        Assert.Equal(1, TechnologyMovementRules.ShipStlMovement(1));
    }

    [Fact]
    public void Tl9ShipMovesNineHexes()
    {
        Assert.Equal(9, TechnologyMovementRules.ShipStlMovement(9));
    }

    [Fact]
    public void Tl1MissileMovesTwoHexes()
    {
        Assert.Equal(2, TechnologyMovementRules.MissileMovement(1));
    }

    [Fact]
    public void Tl9MissileMovesTenHexes()
    {
        Assert.Equal(10, TechnologyMovementRules.MissileMovement(9));
    }

    [Fact]
    public void StlOverloadDoublesListedTl1Movement()
    {
        Assert.Equal(1, TechnologyMovementRules.StlOverloadMovementBonus(1));
        Assert.Equal(2, TechnologyMovementRules.ShipStlMovementWithOverload(1));
    }

    [Fact]
    public void DegradedTl1DriveStillMovesOneHexWithoutOverload()
    {
        Assert.Equal(
            1,
            ComponentPerformance.StlMovement(
                TechnologyMovementRules.ShipStlMovement(1),
                ComponentCondition.Degraded));
    }

    [Fact]
    public void TechnologyLevelBelowOneIsRejected()
    {
        Assert.Throws<ArgumentOutOfRangeException>(() =>
            TechnologyMovementRules.ShipStlMovement(0));
    }

    [Fact]
    public void TechnologyLevelAboveNineIsRejected()
    {
        Assert.Throws<ArgumentOutOfRangeException>(() =>
            TechnologyMovementRules.MissileMovement(10));
    }
}
