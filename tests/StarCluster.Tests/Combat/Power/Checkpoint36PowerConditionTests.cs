using StarCluster.Core.Combat.Components;
using StarCluster.Core.Combat.Power;
using Xunit;

namespace StarCluster.Tests.Combat.Power;

public sealed class Checkpoint36PowerConditionTests
{
    [Fact]
    public void Degraded_auxiliary_reactor_produces_then_cools_for_one_turn()
    {
        var auxiliary = new AuxiliaryReactorState(
            1, 1, ComponentCondition.Degraded);
        var power = new TacticalPowerLedger();
        auxiliary.BeginTurn();
        power.BeginTurn(0);
        Assert.Equal(1, auxiliary.Contribute(power));

        auxiliary.BeginTurn();
        power.BeginTurn(0);
        Assert.True(auxiliary.CoolingThisTurn);
        Assert.Equal(0, auxiliary.Contribute(power));

        auxiliary.BeginTurn();
        power.BeginTurn(0);
        Assert.Equal(1, auxiliary.Contribute(power));
    }

    [Fact]
    public void Degraded_capacitor_discharge_blocks_next_turn_recharge_only()
    {
        var capacitor = new CapacitorBankState(
            3, 1, 2, storedPower: 2, condition: ComponentCondition.Degraded);
        var power = new TacticalPowerLedger();
        power.BeginTurn(0);
        capacitor.BeginTurn();
        capacitor.Discharge(power, 1);

        power.BeginTurn(2);
        capacitor.BeginTurn();
        Assert.True(capacitor.RechargeBlockedThisTurn);
        Assert.Throws<InvalidOperationException>(() =>
            capacitor.Charge(power, 1));

        power.BeginTurn(2);
        capacitor.BeginTurn();
        Assert.False(capacitor.RechargeBlockedThisTurn);
        Assert.Equal(1, capacitor.Charge(power, 1));
    }

    [Fact]
    public void Disabled_capacitor_traps_charge_and_destroyed_loses_it()
    {
        var capacitor = new CapacitorBankState(3, 1, 2, storedPower: 2);
        var power = new TacticalPowerLedger();
        power.BeginTurn(0);
        capacitor.SetCondition(ComponentCondition.Disabled);
        capacitor.BeginTurn();

        Assert.Throws<InvalidOperationException>(() =>
            capacitor.Discharge(power, 1));
        Assert.Equal(2, capacitor.StoredPower);

        capacitor.SetCondition(ComponentCondition.Destroyed);
        Assert.Equal(0, capacitor.StoredPower);
    }

    [Fact]
    public void Combat_battery_first_hit_halves_capacity_and_charge_rounded_up()
    {
        var battery = new CombatBatteryState(5, 2, 1, currentCharges: 5);

        battery.ApplyCriticalHit();

        Assert.Equal(ComponentCondition.Degraded, battery.Condition);
        Assert.Equal(3, battery.CurrentCapacity);
        Assert.Equal(3, battery.CurrentCharges);
    }

    [Fact]
    public void Combat_battery_second_hit_destroys_remaining_charge()
    {
        var battery = new CombatBatteryState(5, 2, 1, currentCharges: 5);
        battery.ApplyCriticalHit();

        battery.ApplyCriticalHit();

        Assert.Equal(ComponentCondition.Destroyed, battery.Condition);
        Assert.Equal(0, battery.CurrentCharges);
    }
}
