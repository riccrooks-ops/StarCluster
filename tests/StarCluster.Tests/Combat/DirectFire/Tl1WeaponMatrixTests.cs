using StarCluster.Core.Combat.DirectFire;
using Xunit;

namespace StarCluster.Tests.Combat.DirectFire;

public sealed class Tl1WeaponMatrixTests
{
    private static Tl1WeaponMatrixSideProfile Side(
        string family,
        bool evasive = false,
        int ammunition = 100,
        int guidance = 55,
        int damage = 5,
        int speed = 1,
        int range = 6,
        int targetMove = 0) => new(
            family,
            "standard",
            family == "energy" ? 25 : family == "kinetic" ? 20 : 0,
            family == "missile" ? 0 : 10,
            evasive,
            5,
            family == "missile" && ammunition == 100 ? 24 : ammunition,
            guidance,
            damage,
            1,
            2,
            speed,
            range,
            targetMove);

    private static Tl1WeaponMatrixProfile Profile(
        Tl1WeaponMatrixSideProfile a,
        Tl1WeaponMatrixSideProfile b,
        int range = 2,
        int turnCap = 100) => new(
            2, 0, 1, 0, 4, 12, range, 5, turnCap, a, b);

    [Fact]
    public void Revised_evm_is_ten_defense_and_five_own_fire()
    {
        var accuracy = new DirectFireAccuracyProfile(50, 20, 10, 5, 10, 5);
        Assert.Equal(60, DirectFireAccuracyCalculator.Calculate(accuracy, 2, true, false).FinalChance);
        Assert.Equal(65, DirectFireAccuracyCalculator.Calculate(accuracy, 2, false, true).FinalChance);
        Assert.Equal(55, DirectFireAccuracyCalculator.Calculate(accuracy, 2, true, true).FinalChance);
    }

    [Fact]
    public void Missile_mirror_consumes_finite_magazines()
    {
        Tl1WeaponMatrixResult result = new Tl1WeaponMatrixSimulator(Profile(Side("missile"), Side("missile")))
            .Run(() => 100, () => 100);
        Assert.True(result.LaunchesA > 0);
        Assert.Equal(24 - result.LaunchesA, result.AmmunitionA);
        Assert.Equal(24 - result.LaunchesB, result.AmmunitionB);
    }

    [Fact]
    public void Missile_flight_respects_travel_delay()
    {
        Tl1WeaponMatrixResult result = new Tl1WeaponMatrixSimulator(Profile(Side("missile"), Side("missile"), range: 4))
            .Run(() => 100, () => 100);
        Assert.True(result.Turns >= 4);
        Assert.True(result.MissileHitsA > 0);
    }

    [Fact]
    public void Missile_below_required_range_exhausts_without_hitting()
    {
        var missile = Side("missile", range: 3);
        Tl1WeaponMatrixResult result = new Tl1WeaponMatrixSimulator(Profile(missile, missile, range: 4, turnCap: 20))
            .Run(() => 100, () => 100);
        Assert.Equal(0, result.MissileHitsA);
        Assert.True(result.RangeExhaustedA > 0);
        Assert.Equal(Tl1DuelOutcome.Unresolved, result.Outcome);
    }

    [Fact]
    public void Equal_speed_target_can_outlast_low_tl_missile()
    {
        var missile = Side("missile", targetMove: 1);
        Tl1WeaponMatrixResult result = new Tl1WeaponMatrixSimulator(Profile(missile, missile, range: 2, turnCap: 20))
            .Run(() => 100, () => 100);
        Assert.Equal(0, result.MissileHitsA);
        Assert.True(result.RangeExhaustedA > 0);
    }

    [Fact]
    public void Faster_missile_closes_the_same_geometry()
    {
        var missile = Side("missile", speed: 2, targetMove: 1);
        Tl1WeaponMatrixResult result = new Tl1WeaponMatrixSimulator(Profile(missile, missile, range: 2))
            .Run(() => 100, () => 100);
        Assert.True(result.MissileHitsA > 0);
    }

    [Fact]
    public void Target_evm_reduces_terminal_guidance()
    {
        var missile = Side("missile", guidance: 55);
        var evasiveTarget = Side("kinetic", evasive: true);
        Tl1WeaponMatrixResult miss = new Tl1WeaponMatrixSimulator(Profile(missile, evasiveTarget, range: 0, turnCap: 1))
            .Run(() => 50, () => 1);
        Assert.Equal(0, miss.MissileHitsA);
    }

    [Fact]
    public void Cross_family_duel_preserves_launched_missile_resolution()
    {
        var missile = Side("missile", damage: 20);
        var kinetic = Side("kinetic");
        Tl1WeaponMatrixResult result = new Tl1WeaponMatrixSimulator(Profile(missile, kinetic, range: 2, turnCap: 20))
            .Run(() => 100, () => 100);
        Assert.NotEqual(Tl1DuelOutcome.Unresolved, result.Outcome);
    }
}
