using StarCluster.Core.Combat.Tactics;
using Xunit;

namespace StarCluster.Tests.Combat.Tactics;

public sealed class TacticalFuelRulesTests
{
    [Fact]
    public void BaselineUsesOneHundredFuelAndTwoPerHex()
    {
        TacticalFuelRules rules = TacticalFuelRules.Baseline;
        Assert.Equal(100, rules.StartingFuel);
        Assert.Equal(2, rules.FuelPerTraversedHex);
        Assert.Equal(6, rules.MovementCost(3, evasiveManeuvers: false));
    }

    [Fact]
    public void EvasiveManeuversCostFlatOneFuel()
    {
        TacticalFuelRules rules = TacticalFuelRules.Baseline;
        Assert.Equal(1, rules.MovementCost(0, evasiveManeuvers: true));
        Assert.Equal(7, rules.MovementCost(3, evasiveManeuvers: true));
    }

    [Fact]
    public void FuelCapsAffordableMovement()
    {
        TacticalFuelRules rules = TacticalFuelRules.Baseline;
        Assert.Equal(2, rules.AffordableMovementHexes(5, evasiveManeuvers: false));
        Assert.Equal(2, rules.AffordableMovementHexes(5, evasiveManeuvers: true));
    }
}
