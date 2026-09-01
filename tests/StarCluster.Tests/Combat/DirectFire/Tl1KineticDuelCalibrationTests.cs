using StarCluster.Core.Combat.DirectFire;
using Xunit;

namespace StarCluster.Tests.Combat.DirectFire;

public sealed class Tl1KineticDuelCalibrationTests
{
    [Fact]
    public void MechanicsFixtureAllHitsMutuallyDestroysOnTurnSix()
    {
        Tl1CalibrationDuelResult result = Run(Tl1DuelCalibrationProfile.MechanicsFixture());
        Assert.Equal(Tl1DuelOutcome.MutualDestruction, result.Outcome);
        Assert.Equal(6, result.Turns);
    }

    [Fact]
    public void MechanicsFixtureCarriesOneHundredAttackPackages()
    {
        Tl1CalibrationDuelResult result = Run(Tl1DuelCalibrationProfile.MechanicsFixture());
        Assert.Equal(94, result.AmmunitionA);
        Assert.Equal(94, result.AmmunitionB);
    }

    [Fact]
    public void DamageTwoExtendsAllHitDuelToTurnSixteen()
    {
        Tl1DuelCalibrationProfile profile = Tl1DuelCalibrationProfile.MechanicsFixture() with { WeaponDamage = 2 };
        Assert.Equal(16, Run(profile).Turns);
    }

    [Fact]
    public void DamageFiveShortensAllHitDuelToTurnFive()
    {
        Tl1DuelCalibrationProfile profile = Tl1DuelCalibrationProfile.MechanicsFixture() with { WeaponDamage = 5 };
        Assert.Equal(5, Run(profile).Turns);
    }

    [Fact]
    public void ShieldFourExtendsAllHitDuelToTurnSeven()
    {
        Tl1DuelCalibrationProfile profile = Tl1DuelCalibrationProfile.MechanicsFixture() with { ShieldCapacity = 4 };
        Assert.Equal(7, Run(profile).Turns);
    }

    [Fact]
    public void ArmorProtectionTwoWithoutApenDoesNotDeleteOrdinaryDamage()
    {
        Tl1DuelCalibrationProfile profile = Tl1DuelCalibrationProfile.MechanicsFixture() with { ArmorProtection = 2 };
        Tl1CalibrationDuelResult result = Run(profile);
        Assert.Equal(Tl1DuelOutcome.MutualDestruction, result.Outcome);
        Assert.Equal(6, result.Turns);
        Assert.Equal(2, result.SideA.Defense.ArmorLayers.Single().CurrentProtection);
        Assert.Equal(2, result.SideB.Defense.ArmorLayers.Single().CurrentProtection);
    }

    [Fact]
    public void ArmorProtectionTwoFullyHardensApenTwo()
    {
        Tl1DuelCalibrationProfile profile = Tl1DuelCalibrationProfile.MechanicsFixture() with { ArmorProtection = 2, ArmorPenetration = 2 };
        Tl1CalibrationDuelResult result = Run(profile);
        Assert.Equal(Tl1DuelOutcome.MutualDestruction, result.Outcome);
        Assert.Equal(6, result.Turns);
        Assert.Equal(2, result.SideA.Defense.ArmorLayers.Single().CurrentProtection);
        Assert.Equal(2, result.SideB.Defense.ArmorLayers.Single().CurrentProtection);
    }

    [Fact]
    public void AllMissesRemainUnresolvedAtTurnCapWithoutExhaustingAmmo()
    {
        var simulator = new Tl1KineticDuelSimulator(Tl1DuelCalibrationProfile.MechanicsFixture() with { TurnCap = 12 });
        Tl1CalibrationDuelResult result = simulator.Run(() => 2, () => 2);
        Assert.Equal(Tl1DuelOutcome.Unresolved, result.Outcome);
        Assert.Equal(88, result.AmmunitionA);
        Assert.Equal(88, result.AmmunitionB);
    }

    private static Tl1CalibrationDuelResult Run(Tl1DuelCalibrationProfile profile)
    {
        var simulator = new Tl1KineticDuelSimulator(profile);
        return simulator.Run(() => 50, () => 50);
    }
}
