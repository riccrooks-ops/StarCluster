using StarCluster.Core.Combat.Components;
using StarCluster.Core.Combat.Damage;
using StarCluster.Core.Combat.InternalDamage;
using StarCluster.Core.Combat.Power;
using StarCluster.Core.Combat.Weapons;
using Xunit;

namespace StarCluster.Tests.Combat.InternalDamage;

public sealed class CanonicalDamageScaleMigrationTests
{
    [Fact]
    public void Canonical_damage_scale_is_two_legacy_points()
    {
        Assert.Equal(2, DamagePointScale.Current);
        Assert.Equal(1, DamagePointScale.Legacy);
        Assert.Equal(10, DamagePointScale.ToCanonical(5));
    }

    [Theory]
    [InlineData(0, 0)]
    [InlineData(1, 1)]
    [InlineData(2, 2)]
    [InlineData(3, 2)]
    [InlineData(4, 2)]
    [InlineData(5, 4)]
    [InlineData(6, 4)]
    [InlineData(7, 4)]
    [InlineData(8, 4)]
    [InlineData(9, 6)]
    [InlineData(10, 6)]
    [InlineData(11, 6)]
    [InlineData(12, 6)]
    public void Canonical_energy_degraded_damage_rounds_on_legacy_equivalent_steps(
        int canonicalDamage,
        int expected)
    {
        Assert.Equal(
            expected,
            DamagePointScale.HalfDamageRoundedUp(canonicalDamage));
    }

    [Theory]
    [InlineData(0)]
    [InlineData(1)]
    [InlineData(2)]
    [InlineData(3)]
    [InlineData(4)]
    [InlineData(5)]
    [InlineData(6)]
    [InlineData(7)]
    [InlineData(8)]
    [InlineData(9)]
    [InlineData(10)]
    [InlineData(11)]
    [InlineData(12)]
    public void Canonical_energy_degradation_is_exact_x2_equivalent_for_migrated_values(
        int legacyDamage)
    {
        int legacy = ComponentPerformance.Weapon(
            WeaponFamily.Energy,
            ComponentCondition.Degraded,
            legacyDamage,
            normalPowerCost: 3,
            damagePointScale: DamagePointScale.Legacy).Damage;
        ConditionedWeaponPerformance canonical = ComponentPerformance.Weapon(
            WeaponFamily.Energy,
            ComponentCondition.Degraded,
            DamagePointScale.ToCanonical(legacyDamage),
            normalPowerCost: 3,
            damagePointScale: DamagePointScale.Current);

        Assert.Equal(DamagePointScale.ToCanonical(legacy), canonical.Damage);
        Assert.Equal(2, canonical.TacticalPowerCost);
    }

    [Fact]
    public void Production_damage_control_still_restores_exactly_one_canonical_hull()
    {
        ShipDamageState ship = RepairShip(pristineHull: 24, currentHull: 20);
        var power = new TacticalPowerLedger();
        power.BeginTurn(5);
        ship.BeginTurn();

        DamageControlAttemptResult attempt =
            DamageControlService.AttemptHullRepair(ship, power, roll: 1);
        Assert.True(attempt.Succeeded);
        Assert.Equal(20, ship.Defense.CurrentHull);

        ship.ApplyPendingRepairsAtTurnRefresh();

        Assert.Equal(21, ship.Defense.CurrentHull);
        Assert.Equal(2, ship.DamageControl.RepairKitsRemaining);
    }

    [Fact]
    public void Parity_fixture_may_artificially_restore_two_canonical_hull()
    {
        var legacy = new LayeredDefenseState(
            0, 0, 0, Array.Empty<ArmorLayerState>(), 12, 10);
        var canonical = new LayeredDefenseState(
            0, 0, 0, Array.Empty<ArmorLayerState>(), 24, 20);

        Assert.Equal(1, legacy.RestoreHull(1));
        Assert.Equal(2, canonical.RestoreHull(2));
        Assert.Equal(legacy.CurrentHull * 2, canonical.CurrentHull);
    }

    private static ShipDamageState RepairShip(int pristineHull, int currentHull)
    {
        var component = new ShipComponentState(
            new ShipComponentDefinition(
                "reactor",
                ShipComponentKind.MainReactor,
                1,
                capabilities: ShipComponentCapability.PowerSource));
        return new ShipDamageState(
            new LayeredDefenseState(
                0,
                0,
                0,
                Array.Empty<ArmorLayerState>(),
                pristineHull,
                currentHull),
            new InternalDamageTrack(
                InternalCriticalDensity.Percent25,
                protectedCompartmentation: true,
                seed: 1,
                originalHullSpan: pristineHull),
            new[] { component },
            criticalExposureSeed: 1,
            isPlayerShip: true);
    }
}
