using StarCluster.Core.Combat.Components;
using StarCluster.Core.Combat.Damage;
using StarCluster.Core.Combat.DirectFire;
using StarCluster.Core.Combat.Power;
using StarCluster.Core.Combat.Weapons;
using Xunit;

namespace StarCluster.Tests.Combat.Power;

public sealed class Tl1TacticalPowerCompletionTests
{
    private static int CriticalMissRoll() => 1;
    private static int CriticalHitRoll() => 100;

    [Fact]
    public void Combat_battery_injects_two_available_power()
    {
        var ledger = new TacticalPowerLedger();
        ledger.BeginTurn(3);
        var battery = new CombatBatteryState(3, 2, 1);
        battery.BeginTurn();

        Assert.Equal(2, battery.Discharge(ledger));
        Assert.Equal(5, ledger.Envelope);
        Assert.Equal(2, battery.CurrentCharges);
    }

    [Fact]
    public void Combat_battery_is_limited_to_one_discharge_per_turn()
    {
        var ledger = new TacticalPowerLedger();
        ledger.BeginTurn(0);
        var battery = new CombatBatteryState(3, 2, 1);
        battery.BeginTurn();
        battery.Discharge(ledger);

        Assert.Throws<InvalidOperationException>(() => battery.Discharge(ledger));
    }

    [Fact]
    public void Combat_battery_can_discharge_again_after_turn_refresh()
    {
        var ledger = new TacticalPowerLedger();
        var battery = new CombatBatteryState(3, 2, 1);
        ledger.BeginTurn(0);
        battery.BeginTurn();
        battery.Discharge(ledger);
        ledger.BeginTurn(0);
        battery.BeginTurn();

        Assert.Equal(2, battery.Discharge(ledger));
        Assert.Equal(1, battery.CurrentCharges);
    }

    [Fact]
    public void Combat_battery_cannot_discharge_after_exhaustion()
    {
        var ledger = new TacticalPowerLedger();
        var battery = new CombatBatteryState(1, 2, 1);
        ledger.BeginTurn(0);
        battery.BeginTurn();
        battery.Discharge(ledger);
        ledger.BeginTurn(0);
        battery.BeginTurn();

        Assert.Throws<InvalidOperationException>(() => battery.Discharge(ledger));
    }

    [Fact]
    public void Unused_combat_battery_power_expires_at_turn_refresh()
    {
        var ledger = new TacticalPowerLedger();
        var battery = new CombatBatteryState(3, 2, 1);
        ledger.BeginTurn(3);
        battery.BeginTurn();
        battery.Discharge(ledger);
        Assert.Equal(5, ledger.AvailablePower);

        ledger.BeginTurn(3);

        Assert.Equal(3, ledger.AvailablePower);
    }

    [Fact]
    public void Capacitor_bank_defaults_to_full_capacity()
    {
        var capacitor = new CapacitorBankState(3, 1, 2);

        Assert.Equal(3, capacitor.StoredPower);
    }

    [Fact]
    public void Ftl_transition_refills_a_depleted_capacitor()
    {
        var ledger = new TacticalPowerLedger();
        ledger.BeginTurn(0);
        var capacitor = new CapacitorBankState(3, 1, 2, storedPower: 1);
        capacitor.BeginTurn();
        capacitor.Discharge(ledger, 1);

        capacitor.CompleteFtlTransition();

        Assert.Equal(3, capacitor.StoredPower);
        Assert.False(capacitor.OperationUsedThisTurn);
    }

    [Fact]
    public void Capacitor_discharge_is_limited_by_rate()
    {
        var ledger = new TacticalPowerLedger();
        ledger.BeginTurn(3);
        var capacitor = new CapacitorBankState(3, 1, 2);
        capacitor.BeginTurn();

        Assert.Equal(2, capacitor.Discharge(ledger, 3));
        Assert.Equal(5, ledger.Envelope);
        Assert.Equal(1, capacitor.StoredPower);
    }

    [Fact]
    public void Capacitor_charge_is_limited_by_rate_and_spends_power()
    {
        var ledger = new TacticalPowerLedger();
        ledger.BeginTurn(3);
        var capacitor = new CapacitorBankState(3, 1, 2, storedPower: 0);
        capacitor.BeginTurn();

        Assert.Equal(1, capacitor.Charge(ledger, 2));
        Assert.Equal(1, capacitor.StoredPower);
        Assert.Equal(1, ledger.SpentPower);
    }

    [Fact]
    public void Capacitor_allows_only_one_operation_per_turn()
    {
        var ledger = new TacticalPowerLedger();
        ledger.BeginTurn(3);
        var capacitor = new CapacitorBankState(3, 1, 2, storedPower: 1);
        capacitor.BeginTurn();
        capacitor.Discharge(ledger, 1);

        Assert.Throws<InvalidOperationException>(() => capacitor.Charge(ledger, 1));
    }

    [Fact]
    public void Capacitor_stored_power_persists_through_turn_refresh()
    {
        var ledger = new TacticalPowerLedger();
        ledger.BeginTurn(0);
        var capacitor = new CapacitorBankState(3, 1, 2, storedPower: 2);
        capacitor.BeginTurn();
        capacitor.Discharge(ledger, 1);
        ledger.BeginTurn(0);
        capacitor.BeginTurn();

        Assert.Equal(1, capacitor.StoredPower);
    }

    [Fact]
    public void Operational_tl1_auxiliary_reactor_adds_one_power()
    {
        var ledger = new TacticalPowerLedger();
        ledger.BeginTurn(3);
        var auxiliary = new AuxiliaryReactorState(1, 0);

        Assert.Equal(1, auxiliary.Contribute(ledger));
        Assert.Equal(4, ledger.Envelope);
    }

    [Fact]
    public void Degraded_tl1_auxiliary_reactor_adds_no_tactical_power()
    {
        var ledger = new TacticalPowerLedger();
        ledger.BeginTurn(3);
        var auxiliary = new AuxiliaryReactorState(1, 0, ComponentCondition.Degraded);

        Assert.Equal(0, auxiliary.Contribute(ledger));
        Assert.Equal(3, ledger.Envelope);
    }

    [Fact]
    public void Disabled_auxiliary_reactor_adds_no_power()
    {
        var ledger = new TacticalPowerLedger();
        ledger.BeginTurn(3);
        var auxiliary = new AuxiliaryReactorState(1, 0, ComponentCondition.Disabled);

        Assert.Equal(0, auxiliary.Contribute(ledger));
        Assert.Equal(3, ledger.Envelope);
    }

    [Fact]
    public void Destroyed_auxiliary_reactor_adds_no_power()
    {
        var ledger = new TacticalPowerLedger();
        ledger.BeginTurn(3);
        var auxiliary = new AuxiliaryReactorState(1, 0, ComponentCondition.Destroyed);

        Assert.Equal(0, auxiliary.Contribute(ledger));
    }

    [Fact]
    public void Held_fire_consumes_one_ready_ammunition_package()
    {
        WeaponState weapon = CreateFiniteKineticWeapon(50);

        weapon.ConsumeAmmunitionForHeldFire();

        Assert.Equal(49, weapon.CurrentAmmunition);
        Assert.Equal(1, weapon.ReadyAmmunition);
        Assert.Equal(48, weapon.ReserveAmmunition);
    }

    [Fact]
    public void Held_power_becomes_spent_only_when_triggered()
    {
        var ledger = new TacticalPowerLedger();
        ledger.BeginTurn(3);
        ledger.Earmark("held", 2);
        Assert.Equal(2, ledger.EarmarkedPower);
        Assert.Equal(0, ledger.SpentPower);

        Assert.Equal(2, ledger.TriggerEarmark("held"));
        Assert.Equal(0, ledger.EarmarkedPower);
        Assert.Equal(2, ledger.SpentPower);
    }

    [Fact]
    public void Unused_held_power_is_released_without_becoming_spent()
    {
        var ledger = new TacticalPowerLedger();
        ledger.BeginTurn(3);
        ledger.Earmark("held", 2);

        Assert.Equal(2, ledger.ReleaseEarmark("held"));
        Assert.Equal(0, ledger.EarmarkedPower);
        Assert.Equal(0, ledger.SpentPower);
        Assert.Equal(3, ledger.SpendablePower);
    }

    [Fact]
    public void Held_energy_interception_triggers_against_an_incoming_missile()
    {
        Tl1PowerEnvelopeResult result = new Tl1PowerEnvelopeSimulator(
            Profile(
                Side("energy", reactor: 2, held: true),
                Side("missile"),
                turnCap: 1))
            .Run(CriticalMissRoll, CriticalHitRoll, nextHeldRollA: CriticalHitRoll);

        Assert.Equal(1, result.HeldDeclarationsA);
        Assert.Equal(1, result.HeldAttemptsA);
        Assert.Equal(1, result.HeldInterceptsA);
        Assert.Equal(1, result.OffensiveCyclesLostA);
        Assert.Equal(0, result.ShotsA);
    }

    [Fact]
    public void Untriggered_held_interception_still_loses_the_offensive_cycle()
    {
        Tl1PowerEnvelopeResult result = new Tl1PowerEnvelopeSimulator(
            Profile(
                Side("energy", reactor: 2, held: true),
                Side("kinetic"),
                turnCap: 1))
            .Run(CriticalMissRoll, CriticalMissRoll);

        Assert.Equal(1, result.HeldDeclarationsA);
        Assert.Equal(0, result.HeldAttemptsA);
        Assert.Equal(1, result.HeldUnusedA);
        Assert.Equal(1, result.OffensiveCyclesLostA);
        Assert.Equal(0, result.TotalSpentA);
    }

    [Fact]
    public void Held_main_resolves_before_pds_and_preserves_pds_ammunition_on_success()
    {
        Tl1PowerEnvelopeSideProfile defender = Side("energy", reactor: 3, held: true) with
        {
            PdsFamily = "kinetic",
            PdsPowerCost = 1,
            PdsReactionCapacity = 1,
            PdsInterceptionChance = 100,
            PdsAmmunition = 50,
        };
        Tl1PowerEnvelopeResult result = new Tl1PowerEnvelopeSimulator(
            Profile(defender, Side("missile"), turnCap: 1))
            .Run(
                CriticalMissRoll,
                CriticalHitRoll,
                nextPdsRollA: CriticalHitRoll,
                nextHeldRollA: CriticalHitRoll);

        Assert.Equal(1, result.HeldAttemptsA);
        Assert.Equal(1, result.HeldInterceptsA);
        Assert.Equal(0, result.PdsAttemptsA);
    }

    [Fact]
    public void Pds_attempts_a_flight_that_survives_held_main()
    {
        Tl1PowerEnvelopeSideProfile defender = Side("energy", reactor: 3, held: true) with
        {
            PdsFamily = "kinetic",
            PdsPowerCost = 1,
            PdsReactionCapacity = 1,
            PdsInterceptionChance = 100,
            PdsAmmunition = 50,
        };
        Tl1PowerEnvelopeResult result = new Tl1PowerEnvelopeSimulator(
            Profile(defender, Side("missile"), turnCap: 1))
            .Run(
                CriticalMissRoll,
                CriticalHitRoll,
                nextPdsRollA: CriticalHitRoll,
                nextHeldRollA: CriticalMissRoll);

        Assert.Equal(1, result.HeldAttemptsA);
        Assert.Equal(0, result.HeldInterceptsA);
        Assert.Equal(1, result.PdsAttemptsA);
        Assert.Equal(1, result.PdsInterceptsA);
    }

    [Fact]
    public void Held_kinetic_interception_earmarks_and_spends_one_power()
    {
        Tl1PowerEnvelopeResult result = new Tl1PowerEnvelopeSimulator(
            Profile(
                Side("kinetic", reactor: 1, held: true),
                Side("missile"),
                turnCap: 1))
            .Run(
                CriticalMissRoll,
                CriticalHitRoll,
                nextHeldRollA: CriticalHitRoll);

        Assert.Equal(1, result.HeldPowerEarmarkedA);
        Assert.Equal(1, result.TotalSpentA);
        Assert.Equal(1, result.HeldAttemptsA);
        Assert.Equal(1, result.HeldInterceptsA);
    }

    [Fact]
    public void Kinetic_main_fire_spends_one_tactical_power()
    {
        Tl1PowerEnvelopeResult result = new Tl1PowerEnvelopeSimulator(
            Profile(Side("kinetic", reactor: 1), Side("kinetic"), turnCap: 1))
            .Run(CriticalHitRoll, CriticalMissRoll);

        Assert.Equal(1, result.ShotsA);
        Assert.Equal(1, result.OffensiveWeaponPowerSpentA);
        Assert.Equal(1, result.TotalSpentA);
    }

    [Fact]
    public void Kinetic_main_cannot_fire_without_tactical_power()
    {
        Tl1PowerEnvelopeResult result = new Tl1PowerEnvelopeSimulator(
            Profile(Side("kinetic", reactor: 0), Side("kinetic"), turnCap: 1))
            .Run(CriticalHitRoll, CriticalMissRoll);

        Assert.Equal(0, result.ShotsA);
        Assert.Equal(1, result.UnfundedWeaponA);
    }

    [Fact]
    public void Missile_launch_remains_zero_power()
    {
        Tl1PowerEnvelopeResult result = new Tl1PowerEnvelopeSimulator(
            Profile(Side("missile", reactor: 0), Side("kinetic"), turnCap: 1))
            .Run(CriticalMissRoll, CriticalMissRoll);

        Assert.Equal(1, result.LaunchesA);
        Assert.Equal(0, result.TotalSpentA);
    }

    [Fact]
    public void Tl1_shield_overcapacity_adds_one_temporary_point_per_activation()
    {
        Tl1PowerEnvelopeSideProfile defender = Side("missile", reactor: 1) with
        {
            ShieldOvercapacitySafeOverload = true,
            SafeOverloadTurnLimit = 1,
        };
        Tl1PowerEnvelopeResult result = new Tl1PowerEnvelopeSimulator(
            Profile(defender, Side("kinetic", reactor: 0), turnCap: 1))
            .Run(CriticalMissRoll, CriticalMissRoll);

        Assert.Equal(1, result.ShieldOvercapacityAddedA);
        Assert.Equal(1, result.ShieldGeneratorStrainA);
        Assert.Equal(1, result.TotalSpentA);
    }

    [Fact]
    public void A_single_held_weapon_can_attempt_only_one_saturation_intercept()
    {
        Tl1PowerEnvelopeSideProfile attacker = Side("missile") with
        {
            MissileLaunchesPerTurn = 2,
        };
        Tl1PowerEnvelopeResult result = new Tl1PowerEnvelopeSimulator(
            Profile(Side("energy", reactor: 2, held: true), attacker, turnCap: 1))
            .Run(
                CriticalMissRoll,
                CriticalHitRoll,
                nextHeldRollA: CriticalHitRoll);

        Assert.Equal(1, result.HeldAttemptsA);
        Assert.Equal(2, result.LaunchesB);
    }

    [Fact]
    public void Full_capacitor_crosses_a_two_power_package_threshold()
    {
        Tl1PowerEnvelopeSideProfile defender = Side("energy", reactor: 3) with
        {
            PdsFamily = "energy",
            PdsPowerCost = 2,
            PdsReactionCapacity = 1,
            PdsInterceptionChance = 40,
            PdsUnlimitedAmmunition = true,
            CapacitorCapacity = 3,
            CapacitorStartingCharge = 3,
            CapacitorDoctrine = "threshold-and-recharge",
        };
        Tl1PowerEnvelopeResult result = new Tl1PowerEnvelopeSimulator(
            Profile(defender, Side("missile"), turnCap: 1))
            .Run(CriticalMissRoll, CriticalHitRoll);

        Assert.True(result.CapacitorPowerDischargedA > 0);
        Assert.True(result.FullPackageTurnsA > 0);
    }

    [Fact]
    public void Combat_battery_crosses_a_power_package_threshold()
    {
        Tl1PowerEnvelopeSideProfile defender = Side("energy", reactor: 3) with
        {
            PdsFamily = "energy",
            PdsPowerCost = 2,
            PdsReactionCapacity = 1,
            PdsInterceptionChance = 40,
            PdsUnlimitedAmmunition = true,
            CombatBatteryCharges = 3,
            CombatBatteryDoctrine = "threshold",
        };
        Tl1PowerEnvelopeResult result = new Tl1PowerEnvelopeSimulator(
            Profile(defender, Side("missile"), turnCap: 1))
            .Run(CriticalMissRoll, CriticalHitRoll);

        Assert.Equal(1, result.CombatBatteryChargesUsedA);
        Assert.Equal(2, result.CombatBatteryPowerA);
    }

    [Fact]
    public void Safe_reactor_overload_adds_one_power_and_one_strain()
    {
        Tl1PowerEnvelopeSideProfile defender = Side("energy", reactor: 1) with
        {
            ReactorSafeOverload = true,
        };
        Tl1PowerEnvelopeResult result = new Tl1PowerEnvelopeSimulator(
            Profile(defender, Side("kinetic"), turnCap: 1))
            .Run(CriticalMissRoll, CriticalMissRoll);

        Assert.Equal(1, result.ReactorOverloadPowerA);
        Assert.Equal(1, result.ReactorStrainA);
    }

    [Fact]
    public void Energy_safe_burst_uses_overload_mode_for_two_shots()
    {
        Tl1PowerEnvelopeSideProfile attacker = Side("energy", reactor: 3) with
        {
            EnergySafeBurst = true,
        };
        Tl1PowerEnvelopeResult result = new Tl1PowerEnvelopeSimulator(
            Profile(attacker, Side("kinetic"), turnCap: 2))
            .Run(CriticalHitRoll, CriticalMissRoll);

        Assert.Equal(2, result.EnergyOverloadShotsA);
        Assert.Equal(2, result.EnergyStrainA);
    }

    private static WeaponState CreateFiniteKineticWeapon(int ammunition) =>
        new(new WeaponProfile(
            "test-kinetic",
            WeaponFamily.Kinetic,
            "standard",
            new AttackPacket(4, 0, 1),
            1,
            1,
            ammunition));

    private static Tl1PowerEnvelopeSideProfile Side(
        string family,
        int reactor = 5,
        bool held = false) => new()
        {
            Family = family,
            Doctrine = "standard",
            Accuracy = family == "energy" ? 25 : family == "kinetic" ? 20 : 0,
            ComputerBonus = 10,
            ReactorOutput = reactor,
            Ammunition = family == "missile" ? 25 : 100,
            MissileGuidance = 55,
            MissileDamage = 5,
            MissileShieldPenetration = 1,
            MissileArmorPenetration = 2,
            MissileSpeed = 1,
            MissileRange = 6,
            MissileLaunchesPerTurn = 1,
            HeldInterception = held,
            HeldInterceptionMode = "standard",
        };

    private static Tl1PowerEnvelopeProfile Profile(
        Tl1PowerEnvelopeSideProfile a,
        Tl1PowerEnvelopeSideProfile b,
        int range = 0,
        int turnCap = 1) => new()
        {
            ShieldCapacity = 2,
            BaseShieldRecharge = 1,
            ArmorIntegrity = 4,
            Hull = 12,
            RangeHexes = range,
            RangePenaltyPerHex = 5,
            TurnCap = turnCap,
            SideA = a,
            SideB = b,
        };
}
