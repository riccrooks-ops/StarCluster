using StarCluster.Core.Combat.Components;
using StarCluster.Core.Combat.Damage;
using StarCluster.Core.Combat.Power;
using StarCluster.Core.Combat.Weapons;
using Xunit;

namespace StarCluster.Tests.Combat.Weapons;

public sealed class WeaponStateTests
{
    [Fact]
    public void KineticWeaponSpendsAmmunitionAndOnePower()
    {
        WeaponState weapon = CreateKineticWeapon();
        TacticalPowerLedger power = CreatePower();
        LayeredDefenseState defense = CreateDefense();

        WeaponFireResult result = weapon.Fire(power, defense, hit: true);

        Assert.Equal(1, result.TacticalPowerSpent);
        Assert.Equal(11, result.RemainingAmmunition);
        Assert.Equal(4, power.AvailablePower);
    }

    [Fact]
    public void EnergyWeaponSpendsPowerAndNoAmmunition()
    {
        WeaponState weapon = CreateEnergyWeapon();
        TacticalPowerLedger power = CreatePower();

        WeaponFireResult result = weapon.Fire(power, CreateDefense(), hit: true);

        Assert.Equal(2, result.TacticalPowerSpent);
        Assert.Null(result.RemainingAmmunition);
        Assert.Equal(3, power.AvailablePower);
    }

    [Fact]
    public void MissileLauncherSpendsAmmunitionAndNoLaunchPower()
    {
        WeaponState weapon = CreateMissileLauncher();
        TacticalPowerLedger power = CreatePower();

        WeaponFireResult result = weapon.Fire(power, CreateDefense(), hit: true);

        Assert.Equal(0, result.TacticalPowerSpent);
        Assert.Equal(7, result.RemainingAmmunition);
    }

    [Fact]
    public void MissStillSpendsSelectedWeaponResources()
    {
        WeaponState weapon = CreateEnergyWeapon();
        TacticalPowerLedger power = CreatePower();
        LayeredDefenseState defense = CreateDefense();

        WeaponFireResult result = weapon.Fire(power, defense, hit: false);

        Assert.False(result.Hit);
        Assert.Null(result.DamageResolution);
        Assert.Equal(3, power.AvailablePower);
        Assert.Equal(6, defense.CurrentShieldCapacity);
    }

    [Fact]
    public void WeaponCannotFireWithoutRequiredAmmunition()
    {
        var weapon = new WeaponState(CreateKineticWeapon().Profile, 0);

        Assert.Throws<InvalidOperationException>(() =>
            weapon.Fire(CreatePower(), CreateDefense(), hit: true));
    }


    [Fact]
    public void AmmunitionFedWeaponStartsWithOneReadyPackage()
    {
        WeaponState weapon = CreateMissileLauncher();

        Assert.Equal(1, weapon.ReadyAmmunition);
        Assert.Equal(7, weapon.ReserveAmmunition);
        Assert.Equal(8, weapon.CurrentAmmunition);
    }

    [Fact]
    public void AutomaticLoaderKeepsOnePackageReadyUntilTheLastShot()
    {
        var weapon = new WeaponState(CreateMissileLauncher().Profile, 2);

        weapon.Fire(CreatePower(), CreateDefense(), hit: false);

        Assert.Equal(1, weapon.ReadyAmmunition);
        Assert.Equal(0, weapon.ReserveAmmunition);
        Assert.Equal(1, weapon.CurrentAmmunition);

        weapon.Fire(CreatePower(), CreateDefense(), hit: false);

        Assert.Equal(0, weapon.ReadyAmmunition);
        Assert.Equal(0, weapon.ReserveAmmunition);
        Assert.Equal(0, weapon.CurrentAmmunition);
    }

    [Fact]
    public void ChargePaymentsAdvanceProgressAndSpendPower()
    {
        var charged = CreateChargedWeapon();
        TacticalPowerLedger power = CreatePower();

        charged.PayCharge(power);

        Assert.Equal(1, charged.ChargeProgress);
        Assert.False(charged.IsReady);
        Assert.Equal(1, power.SpentPower);
        Assert.Throws<InvalidOperationException>(() =>
            charged.PayCharge(power));
    }

    [Fact]
    public void ConsecutiveChargePaymentMakesReadyAndMissedTurnResets()
    {
        var charged = CreateChargedWeapon();
        TacticalPowerLedger power = CreatePower();
        charged.PayCharge(power);
        charged.BeginTurn();
        power.BeginTurn(5);

        charged.PayCharge(power);

        Assert.True(charged.IsReady);
        Assert.Equal(2, charged.ChargeProgress);

        var missed = CreateChargedWeapon();
        TacticalPowerLedger missedPower = CreatePower();
        missed.PayCharge(missedPower);
        missed.BeginTurn();
        missedPower.BeginTurn(5);
        missed.BeginTurn();

        Assert.Equal(0, missed.ChargeProgress);
        Assert.False(missed.IsReady);
    }

    [Fact]
    public void RetentionUpkeepSpendsPowerAndPreservesReadyState()
    {
        var charged = CreateChargedWeapon();
        charged.LoadState(2, isReady: true, retentionTurns: 0);
        TacticalPowerLedger power = CreatePower();

        charged.PayRetention(power);

        Assert.True(charged.IsReady);
        Assert.Equal(1, charged.RetentionTurns);
        Assert.Equal(1, power.SpentPower);
        Assert.Throws<InvalidOperationException>(() =>
            charged.PayRetention(power));

        charged.BeginTurn();
        power.BeginTurn(5);
        Assert.Throws<InvalidOperationException>(() => charged.Fire());
    }

    [Fact]
    public void RetentionMaximumRejectsFurtherNormalRetention()
    {
        var charged = new ChargedWeaponState(2, 1, true, 1, maximumRetentionTurns: 1);
        charged.LoadState(2, isReady: true, retentionTurns: 1);

        Assert.Throws<InvalidOperationException>(() =>
            charged.PayRetention(CreatePower()));

        var nonRetaining = new ChargedWeaponState(
            requiredChargeTurns: 2,
            chargePowerPerTurn: 1,
            retentionAllowed: false,
            retentionUpkeep: 0);
        nonRetaining.LoadState(
            2,
            isReady: true,
            retentionTurns: 0,
            readyPowerPaidThisTurn: true);

        nonRetaining.BeginTurn();

        Assert.False(nonRetaining.IsReady);
        Assert.Equal(0, nonRetaining.ChargeProgress);
    }

    [Fact]
    public void FiringSafelyDischargesReadyWeapon()
    {
        var charged = CreateChargedWeapon();
        charged.LoadState(
            2,
            isReady: true,
            retentionTurns: 1,
            readyPowerPaidThisTurn: true);

        charged.Fire();

        Assert.False(charged.IsReady);
        Assert.Equal(0, charged.ChargeProgress);
        Assert.Equal(0, charged.RetentionTurns);
    }

    [Fact]
    public void DisabledWeaponSafelyDischargesCharge()
    {
        var charged = CreateChargedWeapon();
        charged.LoadState(2, isReady: true, retentionTurns: 0);

        charged.ApplyCondition(ComponentCondition.Disabled);

        Assert.False(charged.IsReady);
        Assert.Equal(0, charged.ChargeProgress);
    }

    [Fact]
    public void FtlTransitionClearsChargeAndReadyState()
    {
        var charged = CreateChargedWeapon();
        charged.LoadState(2, isReady: true, retentionTurns: 1);

        charged.ResetForFtlTransition();

        Assert.False(charged.IsReady);
        Assert.Equal(0, charged.ChargeProgress);
        Assert.Equal(0, charged.RetentionTurns);
    }

    private static WeaponState CreateKineticWeapon() => new(new WeaponProfile(
        "kinetic",
        WeaponFamily.Kinetic,
        "standard",
        new AttackPacket(4, 0, 1),
        tacticalPowerCost: 1,
        ammunitionCost: 1,
        pristineAmmunition: 12));

    private static WeaponState CreateEnergyWeapon() => new(new WeaponProfile(
        "energy",
        WeaponFamily.Energy,
        "standard",
        new AttackPacket(3, 1, 1),
        tacticalPowerCost: 2,
        ammunitionCost: 0,
        pristineAmmunition: null));

    private static WeaponState CreateMissileLauncher() => new(new WeaponProfile(
        "missile",
        WeaponFamily.Missile,
        "standard",
        new AttackPacket(5, 1, 2),
        tacticalPowerCost: 0,
        ammunitionCost: 1,
        pristineAmmunition: 8));

    private static ChargedWeaponState CreateChargedWeapon() => new(
        requiredChargeTurns: 2,
        chargePowerPerTurn: 1,
        retentionAllowed: true,
        retentionUpkeep: 1);

    private static TacticalPowerLedger CreatePower()
    {
        var power = new TacticalPowerLedger();
        power.BeginTurn(5);
        return power;
    }

    private static LayeredDefenseState CreateDefense() => new(
        pristineShieldCapacity: 6,
        currentShieldCapacity: 6,
        shieldArmor: 0,
        armorLayers: new[] { new ArmorLayerState("armor-1", 2, 2, 6, 6) },
        pristineHull: 12,
        currentHull: 12);
}
