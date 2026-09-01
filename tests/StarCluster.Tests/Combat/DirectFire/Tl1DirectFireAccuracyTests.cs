using StarCluster.Core.Combat.Components;
using StarCluster.Core.Combat.Damage;
using StarCluster.Core.Combat.DirectFire;
using StarCluster.Core.Combat.Power;
using StarCluster.Core.Combat.Weapons;
using Xunit;

namespace StarCluster.Tests.Combat.DirectFire;

public sealed class Tl1DirectFireAccuracyTests
{
    [Theory]
    [InlineData(20, 10, 0, false, false, 80)]
    [InlineData(25, 10, 0, false, false, 85)]
    [InlineData(20, 10, 2, false, false, 70)]
    [InlineData(25, 10, 2, false, false, 75)]
    [InlineData(20, 10, 2, true, false, 60)]
    [InlineData(20, 10, 2, true, true, 55)]
    [InlineData(25, 5, 2, false, false, 70)]
    [InlineData(20, 0, 2, false, false, 60)]
    public void CalculatorMatchesAcceptedTl1Examples(
        int weaponAccuracy, int computerBonus, int range,
        bool targetEvasive, bool shooterEvasive, int expected)
    {
        var profile = Profile(weaponAccuracy, computerBonus);
        DirectFireAccuracyResult result = DirectFireAccuracyCalculator.Calculate(
            profile, range, targetEvasive, shooterEvasive);
        Assert.Equal(expected, result.FinalChance);
    }


    [Theory]
    [InlineData(ComponentCondition.Operational, 0)]
    [InlineData(ComponentCondition.Degraded, 0)]
    [InlineData(ComponentCondition.Disabled, 10)]
    [InlineData(ComponentCondition.Destroyed, 10)]
    public void Disabled_or_destroyed_stl_adds_immobile_target_bonus(
        ComponentCondition stlCondition,
        int expectedBonus)
    {
        DirectFireAccuracyResult result = DirectFireAccuracyCalculator.Calculate(
            Profile(20, 10),
            rangeHexes: 2,
            targetEvasive: true,
            shooterEvasive: false,
            targetStlCondition: stlCondition);

        Assert.Equal(expectedBonus, result.TargetMobilityBonus);
        Assert.Equal(60 + expectedBonus, result.FinalChance);
    }

    [Fact]
    public void Immobile_target_bonus_stacks_normally_with_evasive_maneuvers()
    {
        DirectFireAccuracyResult mobile = DirectFireAccuracyCalculator.Calculate(
            Profile(20, 10), 2, targetEvasive: true, shooterEvasive: false);
        DirectFireAccuracyResult immobile = DirectFireAccuracyCalculator.Calculate(
            Profile(20, 10), 2, targetEvasive: true, shooterEvasive: false,
            targetStlCondition: ComponentCondition.Disabled);

        Assert.Equal(60, mobile.FinalChance);
        Assert.Equal(70, immobile.FinalChance);
    }

    [Theory]
    [InlineData(1, 80, DirectFireRollOutcome.CriticalMiss)]
    [InlineData(20, 80, DirectFireRollOutcome.Miss)]
    [InlineData(21, 80, DirectFireRollOutcome.Hit)]
    [InlineData(99, 80, DirectFireRollOutcome.Hit)]
    [InlineData(100, 80, DirectFireRollOutcome.CriticalHit)]
    public void RollHighMappingIsExact(int roll, int chance, DirectFireRollOutcome expected)
    {
        Assert.Equal(expected, DirectFireHitResolver.Resolve(roll, chance));
    }

    [Fact]
    public void AccuracyIsBoundedAtFiveAndNinetyFive()
    {
        Assert.Equal(95, DirectFireAccuracyCalculator.Calculate(
            Profile(100, 100), 0, false, false).FinalChance);
        Assert.Equal(5, DirectFireAccuracyCalculator.Calculate(
            Profile(-100, -100), 20, true, true).FinalChance);
    }

    [Theory]
    [InlineData(ComponentCondition.Operational, 10)]
    [InlineData(ComponentCondition.Degraded, 5)]
    [InlineData(ComponentCondition.Disabled, 0)]
    [InlineData(ComponentCondition.Destroyed, 0)]
    public void TargetingComputerBonusUsesConditionOnly(ComponentCondition condition, int expected)
    {
        Assert.Equal(expected, Tl1TargetingComputer.Bonus(condition));
    }

    [Fact]
    public void SimultaneousWindowAllowsMutualDestruction()
    {
        DirectFireCombatant a = Combatant("A", hull: 3);
        DirectFireCombatant b = Combatant("B", hull: 3);
        WeaponState wa = Weapon("A-gun", damage: 3);
        WeaponState wb = Weapon("B-gun", damage: 3);
        var orders = new[]
        {
            new SimultaneousDirectFireOrder(a, b, wa, Profile(20, 10), 0, false, false, 50),
            new SimultaneousDirectFireOrder(b, a, wb, Profile(20, 10), 0, false, false, 50),
        };

        SimultaneousDirectFireBatchResult result = SimultaneousDirectFireResolver.Resolve(orders);

        Assert.True(result.MutualDestruction);
        Assert.True(a.IsDestroyed);
        Assert.True(b.IsDestroyed);
        Assert.All(result.Attacks, attack => Assert.Equal(DirectFireRollOutcome.Hit, attack.Outcome));
    }

    [Fact]
    public void SequentialProcessingDoesNotCancelCommittedReturnFire()
    {
        DirectFireCombatant a = Combatant("A", hull: 3);
        DirectFireCombatant b = Combatant("B", hull: 3);
        SimultaneousDirectFireBatchResult result = SimultaneousDirectFireResolver.Resolve(new[]
        {
            new SimultaneousDirectFireOrder(a, b, Weapon("A-gun", 3), Profile(20, 10), 0, false, false, 50),
            new SimultaneousDirectFireOrder(b, a, Weapon("B-gun", 3), Profile(20, 10), 0, false, false, 50),
        });
        Assert.Equal(2, result.Attacks.Count);
        Assert.Equal(0, a.Defense.CurrentHull);
        Assert.Equal(0, b.Defense.CurrentHull);
    }

    [Fact]
    public void MissStillConsumesAmmunition()
    {
        DirectFireCombatant a = Combatant("A", hull: 10);
        DirectFireCombatant b = Combatant("B", hull: 10);
        WeaponState weapon = Weapon("gun", 3, ammunition: 2);
        SimultaneousDirectFireBatchResult result = SimultaneousDirectFireResolver.Resolve(new[]
        {
            new SimultaneousDirectFireOrder(a, b, weapon, Profile(20, 10), 0, false, false, 2),
        });
        Assert.Equal(DirectFireRollOutcome.Miss, result.Attacks[0].Outcome);
        Assert.Equal(1, weapon.CurrentAmmunition);
        Assert.Equal(10, b.Defense.CurrentHull);
    }

    [Fact]
    public void SameWeaponCannotBeCommittedTwice()
    {
        DirectFireCombatant a = Combatant("A", hull: 10);
        DirectFireCombatant b = Combatant("B", hull: 10);
        WeaponState weapon = Weapon("gun", 3);
        var orders = new[]
        {
            new SimultaneousDirectFireOrder(a, b, weapon, Profile(20, 10), 0, false, false, 50),
            new SimultaneousDirectFireOrder(a, b, weapon, Profile(20, 10), 0, false, false, 50),
        };
        Assert.Throws<InvalidOperationException>(() => SimultaneousDirectFireResolver.Resolve(orders));
    }


    [Fact]
    public void KineticMirrorAllHitsMutuallyDestroysOnTurnSix()
    {
        Tl1DuelResult result = Duel().Run(Enumerable.Repeat(50, 12).ToArray(), Enumerable.Repeat(50, 12).ToArray());
        Assert.Equal(Tl1DuelOutcome.MutualDestruction, result.Outcome);
        Assert.Equal(6, result.TurnsResolved);
    }

    [Fact]
    public void KineticMirrorOpeningMissGivesOtherSideWin()
    {
        int[] a = new[] { 2 }.Concat(Enumerable.Repeat(50, 11)).ToArray();
        Tl1DuelResult result = Duel().Run(a, Enumerable.Repeat(50, 12).ToArray());
        Assert.Equal(Tl1DuelOutcome.SideBWins, result.Outcome);
        Assert.Equal(0, result.SideA.Defense.CurrentHull);
        Assert.Equal(2, result.SideB.Defense.CurrentHull);
    }

    [Fact]
    public void KineticMirrorAllMissesIsUnresolvedAtCap()
    {
        Tl1DuelResult result = Duel().Run(Enumerable.Repeat(2, 12).ToArray(), Enumerable.Repeat(2, 12).ToArray());
        Assert.Equal(Tl1DuelOutcome.Unresolved, result.Outcome);
        Assert.Equal(12, result.TurnsResolved);
    }

    [Fact]
    public void KineticMirrorConsumesOneAmmoPerTurn()
    {
        Tl1DuelResult result = Duel().Run(Enumerable.Repeat(2, 12).ToArray(), Enumerable.Repeat(2, 12).ToArray());
        Assert.Equal(88, result.Turns[^1].AmmunitionA);
        Assert.Equal(88, result.Turns[^1].AmmunitionB);
    }

    [Fact]
    public void KineticMirrorBothEvasiveUsesFiftyFivePercentAtRangeTwo()
    {
        var duel = new Tl1KineticMirrorDuel(12, 2, true, true, Profile(20, 10));
        Tl1DuelResult result = duel.Run(Enumerable.Repeat(51, 12).ToArray(), Enumerable.Repeat(51, 12).ToArray());
        Assert.Equal(Tl1DuelOutcome.MutualDestruction, result.Outcome);
    }

    private static Tl1KineticMirrorDuel Duel() => new(12, 0, false, false, Profile(20, 10));

    private static DirectFireAccuracyProfile Profile(int weaponAccuracy, int computerBonus) =>
        new(50, weaponAccuracy, computerBonus, 5, 10, 5);

    private static DirectFireCombatant Combatant(string id, int hull) => new(
        id,
        new LayeredDefenseState(0, 0, 0, Array.Empty<ArmorLayerState>(), hull, hull),
        CreatePowerLedger(),
        100,
        10);

    private static TacticalPowerLedger CreatePowerLedger()
    {
        var ledger = new TacticalPowerLedger();
        ledger.BeginTurn(5);
        return ledger;
    }

    private static WeaponState Weapon(string id, int damage, int? ammunition = 12) => new(
        new WeaponProfile(
            id,
            WeaponFamily.Kinetic,
            "standard",
            new AttackPacket(damage, 0, 0),
            1,
            ammunition is null ? 0 : 1,
            ammunition));
}
