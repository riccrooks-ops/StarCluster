using StarCluster.Core.Combat.DirectFire;
using Xunit;

namespace StarCluster.Tests.Combat.DirectFire;

public sealed class Tl1EnergyDuelCalibrationTests
{
    [Fact]
    public void Standard_energy_mirror_resolves_simultaneously()
    {
        var simulator = new Tl1EnergyDuelSimulator(Tl1EnergyCalibrationProfile.EnergyMirror());
        Tl1EnergyDuelResult result = simulator.Run(() => 100, () => 100);
        Assert.Equal(Tl1DuelOutcome.MutualDestruction, result.Outcome);
        Assert.Equal(result.ShotsA, result.ShotsB);
        Assert.Equal(result.HitsA, result.HitsB);
    }

    [Fact]
    public void Low_output_spends_one_power_per_shot()
    {
        var simulator = new Tl1EnergyDuelSimulator(Tl1EnergyCalibrationProfile.EnergyMirror("low"));
        Tl1EnergyDuelResult result = simulator.Run(() => 100, () => 100);
        Assert.Equal(result.ShotsA, result.TacticalPowerSpentA);
        Assert.Equal(result.ShotsB, result.TacticalPowerSpentB);
    }

    [Fact]
    public void Standard_output_spends_two_power_per_shot()
    {
        var simulator = new Tl1EnergyDuelSimulator(Tl1EnergyCalibrationProfile.EnergyMirror("standard"));
        Tl1EnergyDuelResult result = simulator.Run(() => 100, () => 100);
        Assert.Equal(result.ShotsA * 2, result.TacticalPowerSpentA);
        Assert.Equal(result.ShotsB * 2, result.TacticalPowerSpentB);
    }

    [Fact]
    public void Safe_burst_uses_exactly_two_overload_shots_per_surviving_side()
    {
        var simulator = new Tl1EnergyDuelSimulator(Tl1EnergyCalibrationProfile.EnergyMirror("safe-burst"));
        Tl1EnergyDuelResult result = simulator.Run(() => 100, () => 100);
        Assert.Equal(2, result.SafeOverloadShotsA);
        Assert.Equal(2, result.SafeOverloadShotsB);
    }

    [Fact]
    public void Tactical_shield_recharge_never_spends_reserved_weapon_power()
    {
        Tl1EnergyCalibrationProfile baseline = Tl1EnergyCalibrationProfile.EnergyMirror();
        var side = baseline.SideA with { TacticalShieldRecharge = 2, ReactorOutput = 3 };
        var simulator = new Tl1EnergyDuelSimulator(baseline with { SideA = side, SideB = side });
        Tl1EnergyDuelResult result = simulator.Run(() => 100, () => 100);
        Assert.Equal(result.ShotsA * 2 + result.TacticalShieldRestoredA, result.TacticalPowerSpentA);
        Assert.True(result.TacticalShieldRestoredA <= result.ShotsA);
    }

    [Fact]
    public void Evasive_maneuvering_spends_one_additional_power_each_active_turn()
    {
        Tl1EnergyCalibrationProfile baseline = Tl1EnergyCalibrationProfile.EnergyMirror();
        var side = baseline.SideA with { Evasive = true };
        var simulator = new Tl1EnergyDuelSimulator(baseline with { SideA = side, SideB = side });
        Tl1EnergyDuelResult result = simulator.Run(() => 100, () => 100);
        Assert.Equal(result.ShotsA * 3, result.TacticalPowerSpentA);
        Assert.Equal(result.ShotsB * 3, result.TacticalPowerSpentB);
    }

    [Fact]
    public void Energy_weapon_has_no_ammunition_consumption()
    {
        var simulator = new Tl1EnergyDuelSimulator(Tl1EnergyCalibrationProfile.EnergyMirror());
        Tl1EnergyDuelResult result = simulator.Run(() => 100, () => 100);
        Assert.Equal(0, result.AmmunitionA);
        Assert.Equal(0, result.AmmunitionB);
    }

    [Fact]
    public void Kinetic_control_consumes_ammunition()
    {
        Tl1EnergyCalibrationProfile baseline = Tl1EnergyCalibrationProfile.EnergyMirror();
        var kinetic = new Tl1EnergySideProfile("kinetic", "standard", 20, 10, false, 5, 0, 100);
        var simulator = new Tl1EnergyDuelSimulator(baseline with { SideA = kinetic, SideB = kinetic });
        Tl1EnergyDuelResult result = simulator.Run(() => 100, () => 100);
        Assert.Equal(100 - result.ShotsA, result.AmmunitionA);
        Assert.Equal(100 - result.ShotsB, result.AmmunitionB);
    }

    [Fact]
    public void Insufficient_reactor_output_prevents_energy_fire_without_throwing()
    {
        Tl1EnergyCalibrationProfile baseline = Tl1EnergyCalibrationProfile.EnergyMirror();
        var powerless = baseline.SideA with { ReactorOutput = 1, Doctrine = "standard" };
        var simulator = new Tl1EnergyDuelSimulator(baseline with { SideA = powerless, SideB = powerless, TurnCap = 3 });
        Tl1EnergyDuelResult result = simulator.Run(() => 100, () => 100);
        Assert.Equal(Tl1DuelOutcome.Unresolved, result.Outcome);
        Assert.Equal(0, result.ShotsA);
        Assert.Equal(0, result.ShotsB);
    }

    [Fact]
    public void Side_swap_with_identical_rolls_reverses_cross_family_outcome()
    {
        Tl1EnergyCalibrationProfile baseline = Tl1EnergyCalibrationProfile.EnergyMirror();
        var kinetic = new Tl1EnergySideProfile("kinetic", "standard", 20, 10, false, 5, 0, 100);
        Tl1EnergyDuelResult first = new Tl1EnergyDuelSimulator(baseline with { SideB = kinetic }).Run(() => 70, () => 70);
        Tl1EnergyDuelResult second = new Tl1EnergyDuelSimulator(baseline with { SideA = kinetic }).Run(() => 70, () => 70);
        Assert.Equal(first.Outcome switch
        {
            Tl1DuelOutcome.SideAWins => Tl1DuelOutcome.SideBWins,
            Tl1DuelOutcome.SideBWins => Tl1DuelOutcome.SideAWins,
            _ => first.Outcome,
        }, second.Outcome);
    }
}
