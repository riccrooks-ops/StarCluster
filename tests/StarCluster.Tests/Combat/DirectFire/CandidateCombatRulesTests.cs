using StarCluster.Core.Combat.Damage;
using StarCluster.Core.Combat.DirectFire;
using StarCluster.Core.Combat.Power;
using Xunit;

namespace StarCluster.Tests.Combat.DirectFire;

public sealed class CandidateCombatRulesTests
{
    [Fact]
    public void EnergyMainModesUseUniversalRoundedRelationships()
    {
        EnergyMainOutputResult low = EnergyMainOutputRules.Resolve(2, 5, EnergyMainOutputMode.Low);
        EnergyMainOutputResult standard = EnergyMainOutputRules.Resolve(2, 5, EnergyMainOutputMode.Standard);
        EnergyMainOutputResult overload = EnergyMainOutputRules.Resolve(2, 5, EnergyMainOutputMode.Overload);
        EnergyMainOutputResult late = EnergyMainOutputRules.Resolve(4, 9, EnergyMainOutputMode.Overload);

        Assert.Equal((1, 3, 0), (low.TacticalPowerCost, low.Damage, low.StrainGained));
        Assert.Equal((2, 5, 0), (standard.TacticalPowerCost, standard.Damage, standard.StrainGained));
        Assert.Equal((3, 8, 1), (overload.TacticalPowerCost, overload.Damage, overload.StrainGained));
        Assert.Equal((6, 14, 1), (late.TacticalPowerCost, late.Damage, late.StrainGained));
    }

    [Fact]
    public void ArmorTacticalRegenerationSpendsPowerUpToCapAndPristineIntegrity()
    {
        var armor = new ArmorLayerState("armor", 1, 1, 10, 7);
        var power = new TacticalPowerLedger();
        power.BeginTurn(5);

        ArmorTacticalRegenerationResult result =
            ArmorTacticalRegenerationService.Apply(armor, power, tacticalPowerCap: 2, combatRegenerationReserveAi: 2);

        Assert.Equal(2, result.TacticalPowerSpent);
        Assert.Equal(2, result.IntegrityRestored);
        Assert.Equal(9, armor.CurrentIntegrity);
        Assert.Equal(0, result.CombatRegenerationReserveRemaining);
        Assert.Equal(2, power.SpentPower);

        power.BeginTurn(5);
        ArmorTacticalRegenerationResult exhausted =
            ArmorTacticalRegenerationService.Apply(armor, power, tacticalPowerCap: 2, combatRegenerationReserveAi: result.CombatRegenerationReserveRemaining);
        Assert.Equal(0, exhausted.TacticalPowerSpent);
        Assert.Equal(0, exhausted.IntegrityRestored);
        Assert.Equal(9, armor.CurrentIntegrity);
    }

    [Fact]
    public void NonRegenerativeArmorUsesZeroCapAndSpendsNoPower()
    {
        var armor = new ArmorLayerState("crystalline", 2, 2, 12, 8);
        var power = new TacticalPowerLedger();
        power.BeginTurn(5);

        ArmorTacticalRegenerationResult result =
            ArmorTacticalRegenerationService.Apply(armor, power, tacticalPowerCap: 0, combatRegenerationReserveAi: 0);

        Assert.Equal(0, result.TacticalPowerSpent);
        Assert.Equal(0, result.IntegrityRestored);
        Assert.Equal(8, armor.CurrentIntegrity);
        Assert.Equal(0, result.CombatRegenerationReserveRemaining);
        Assert.Equal(0, power.SpentPower);
    }
}
