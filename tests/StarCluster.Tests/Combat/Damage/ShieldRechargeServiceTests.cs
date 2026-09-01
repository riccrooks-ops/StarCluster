using StarCluster.Core.Combat.Components;
using StarCluster.Core.Combat.Damage;
using StarCluster.Core.Combat.Power;
using Xunit;

namespace StarCluster.Tests.Combat.Damage;

public sealed class ShieldRechargeServiceTests
{
    [Fact]
    public void OperationalShieldReceivesBaseAndTacticalRecharge()
    {
        LayeredDefenseState defense = CreateDefense(2);
        TacticalPowerLedger power = CreatePower();

        ShieldRechargeResult result = ShieldRechargeService.ApplyTurnStart(
            defense,
            ComponentCondition.Operational,
            CreateProfile(),
            power,
            requestedTacticalPower: 2);

        Assert.Equal(1, result.BaseRestored);
        Assert.Equal(2, result.TacticalPowerSpent);
        Assert.Equal(2, result.TacticalRestored);
        Assert.Equal(5, defense.CurrentShieldCapacity);
    }

    [Fact]
    public void RechargeNeverExceedsPristineCapacity()
    {
        LayeredDefenseState defense = CreateDefense(5);
        TacticalPowerLedger power = CreatePower();

        ShieldRechargeResult result = ShieldRechargeService.ApplyTurnStart(
            defense,
            ComponentCondition.Operational,
            CreateProfile(),
            power,
            requestedTacticalPower: 2);

        Assert.Equal(6, defense.CurrentShieldCapacity);
        Assert.Equal(0, result.TacticalPowerSpent);
    }

    [Fact]
    public void DegradedShieldUsesReducedProfile()
    {
        LayeredDefenseState defense = CreateDefense(2);
        TacticalPowerLedger power = CreatePower();

        ShieldRechargeResult result = ShieldRechargeService.ApplyTurnStart(
            defense,
            ComponentCondition.Degraded,
            CreateProfile(),
            power,
            requestedTacticalPower: 2);

        Assert.Equal(0, result.BaseRestored);
        Assert.Equal(1, result.TacticalPowerSpent);
        Assert.Equal(3, defense.CurrentShieldCapacity);
    }

    [Fact]
    public void DisabledShieldCannotRecharge()
    {
        LayeredDefenseState defense = CreateDefense(2);
        TacticalPowerLedger power = CreatePower();

        ShieldRechargeResult result = ShieldRechargeService.ApplyTurnStart(
            defense,
            ComponentCondition.Disabled,
            CreateProfile(),
            power,
            requestedTacticalPower: 2);

        Assert.Equal(0, result.BaseRestored);
        Assert.Equal(0, result.TacticalPowerSpent);
        Assert.Equal(2, defense.CurrentShieldCapacity);
    }

    [Fact]
    public void TemporaryOvercapacityClearsBeforeRecharge()
    {
        LayeredDefenseState defense = CreateDefense(6);
        defense.AddTemporaryShieldOvercapacity(2);
        TacticalPowerLedger power = CreatePower();

        ShieldRechargeResult result = ShieldRechargeService.ApplyTurnStart(
            defense,
            ComponentCondition.Operational,
            CreateProfile(),
            power,
            requestedTacticalPower: 2);

        Assert.Equal(2, result.TemporaryCapacityLost);
        Assert.Equal(6, defense.CurrentShieldCapacity);
        Assert.Equal(0, defense.TemporaryShieldOvercapacity);
    }

    private static ShieldRechargeProfile CreateProfile() => new(
        operationalBaseRecharge: 1,
        tacticalRechargePerPower: 1,
        operationalTacticalPowerCap: 2,
        degradedBaseRecharge: 0,
        degradedTacticalPowerCap: 1);

    private static TacticalPowerLedger CreatePower()
    {
        var power = new TacticalPowerLedger();
        power.BeginTurn(5);
        return power;
    }

    private static LayeredDefenseState CreateDefense(int currentShield) => new(
        pristineShieldCapacity: 6,
        currentShieldCapacity: currentShield,
        shieldArmor: 0,
        armorLayers: new[] { new ArmorLayerState("armor-1", 2, 2, 6, 6) },
        pristineHull: 12,
        currentHull: 12);
}
