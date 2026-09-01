using System;
using StarCluster.Core.Combat;
using StarCluster.Core.Combat.DirectFire;
using StarCluster.Core.Combat.Missiles;
using StarCluster.Core.Geometry;
using Xunit;

namespace StarCluster.Tests.Combat.DirectFire;

public sealed class DirectFireOrderTests
{
    [Fact]
    public void ProfileRejectsNegativeTechnologyLevel()
    {
        Assert.Throws<ArgumentOutOfRangeException>(
            () => new DirectFireWeaponProfile(-1, 3));
    }

    [Fact]
    public void ProfileRejectsNegativeRange()
    {
        Assert.Throws<ArgumentOutOfRangeException>(
            () => new DirectFireWeaponProfile(1, -1));
    }

    [Fact]
    public void ProfileMayDeclareApproximateTrackCapabilityWithoutOwningPenalty()
    {
        var profile = new DirectFireWeaponProfile(
            1,
            4,
            allowsApproximateTrackFire: true);

        Assert.True(profile.AllowsApproximateTrackFire);
    }

    [Fact]
    public void FireAtShipRecordsMutuallyExclusiveShipTarget()
    {
        DirectFireOrder order = DirectFireOrder.FireAtShip(
            "order",
            "weapon",
            "ship-player",
            TacticalSide.Player,
            new HexCoord(-2, 0),
            new DirectFireWeaponProfile(3, 4),
            "ship-enemy");

        Assert.Equal(DirectFireOrderType.FireAtShip, order.OrderType);
        Assert.Equal("ship-enemy", order.TargetShipId);
        Assert.Null(order.TargetMissileSalvoId);
        Assert.False(order.CreatesHeldInterception);
    }

    [Fact]
    public void SpecificInterceptionRecordsOnlyNamedSalvo()
    {
        DirectFireOrder order = CreateSpecificOrder("hostile-2");

        Assert.Equal(
            DirectFireOrderType.InterceptSpecificMissile,
            order.OrderType);
        Assert.Equal("hostile-2", order.TargetMissileSalvoId);
        Assert.True(order.CreatesHeldInterception);
    }

    [Fact]
    public void HoldForAnyMissileHasNoSpecificTarget()
    {
        DirectFireOrder order = DirectFireOrder.HoldForAnyMissile(
            "order",
            "weapon",
            "ship-player",
            TacticalSide.Player,
            new HexCoord(-2, 0),
            new DirectFireWeaponProfile(3, 4));

        Assert.Equal(
            DirectFireOrderType.HoldForAnyMissile,
            order.OrderType);
        Assert.Null(order.TargetMissileSalvoId);
        Assert.True(order.CreatesHeldInterception);
    }

    [Fact]
    public void HoldFireCreatesNoInterceptionLayer()
    {
        DirectFireOrder order = DirectFireOrder.HoldFire(
            "order",
            "weapon",
            "ship-player",
            TacticalSide.Player,
            new HexCoord(-2, 0),
            new DirectFireWeaponProfile(3, 4));

        Assert.Equal(DirectFireOrderType.HoldFire, order.OrderType);
        Assert.False(order.CreatesHeldInterception);
    }

    [Fact]
    public void NonInterceptWeaponRejectsSpecificMissileOrder()
    {
        var profile = new DirectFireWeaponProfile(
            3,
            4,
            canInterceptMissiles: false);

        Assert.Throws<ArgumentException>(() =>
            DirectFireOrder.InterceptSpecificMissile(
                "order",
                "weapon",
                "ship-player",
                TacticalSide.Player,
                new HexCoord(-2, 0),
                profile,
                "hostile"));
    }

    [Fact]
    public void NonInterceptWeaponRejectsHoldForAnyOrder()
    {
        var profile = new DirectFireWeaponProfile(
            3,
            4,
            canInterceptMissiles: false);

        Assert.Throws<ArgumentException>(() =>
            DirectFireOrder.HoldForAnyMissile(
                "order",
                "weapon",
                "ship-player",
                TacticalSide.Player,
                new HexCoord(-2, 0),
                profile));
    }

    [Fact]
    public void HeldOrderCreatesOneShotLineOfSightDefense()
    {
        MissileDefenseSystem defense = CreateSpecificOrder("hostile-2")
            .CreateHeldDefenseSystem("held-main", priority: 2);

        Assert.Equal(
            MissileDefenseSourceType.HeldDirectFireWeapon,
            defense.SourceType);
        Assert.Equal("hostile-2", defense.TargetMissileSalvoId);
        Assert.True(defense.RequiresLineOfSight);
        Assert.Equal(4, defense.Profile.InterceptionRangeHexes);
        Assert.Equal(1, defense.Profile.MaximumAttemptsPerPhase);
        Assert.Equal(2, defense.Priority);
    }

    [Fact]
    public void ShipAttackCannotCreateHeldDefense()
    {
        DirectFireOrder order = DirectFireOrder.FireAtShip(
            "order",
            "weapon",
            "ship-player",
            TacticalSide.Player,
            new HexCoord(-2, 0),
            new DirectFireWeaponProfile(3, 4),
            "ship-enemy");

        Assert.Throws<InvalidOperationException>(
            () => order.CreateHeldDefenseSystem("invalid"));
    }

    private static DirectFireOrder CreateSpecificOrder(string salvoId) =>
        DirectFireOrder.InterceptSpecificMissile(
            "order",
            "weapon",
            "ship-player",
            TacticalSide.Player,
            new HexCoord(-2, 0),
            new DirectFireWeaponProfile(3, 4),
            salvoId);
}
