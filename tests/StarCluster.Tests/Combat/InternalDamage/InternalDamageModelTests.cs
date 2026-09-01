using StarCluster.Core.Combat.Components;
using StarCluster.Core.Combat.Damage;
using StarCluster.Core.Combat.DirectFire;
using StarCluster.Core.Combat.InternalDamage;
using StarCluster.Core.Combat.Power;
using StarCluster.Core.Combat.Weapons;
using Xunit;

namespace StarCluster.Tests.Combat.InternalDamage;

public sealed class InternalDamageModelTests
{
    [Fact]
    public void Fifteen_percent_track_uses_seven_six_seven_strata()
    {
        var track = new InternalDamageTrack(
            InternalCriticalDensity.Percent15,
            protectedCompartmentation: true,
            seed: 1,
            originalHullSpan: 20);

        Assert.Equal(InternalMarkerKind.Critical, track.MarkerAt(7));
        Assert.Equal(InternalMarkerKind.Critical, track.MarkerAt(13));
        Assert.Equal(InternalMarkerKind.Critical, track.MarkerAt(19));
        Assert.Equal(InternalMarkerKind.Hull, track.MarkerAt(20));
        Assert.Equal(3, track.CountCriticalMarkers(20));
    }

    [Theory]
    [InlineData(InternalCriticalDensity.Percent20, 5)]
    [InlineData(InternalCriticalDensity.Percent25, 4)]
    [InlineData(InternalCriticalDensity.Percent33, 3)]
    [InlineData(InternalCriticalDensity.Percent50, 2)]
    public void Protected_compartmentation_places_x_at_stratum_end(
        InternalCriticalDensity density,
        int stratum)
    {
        var track = new InternalDamageTrack(density, true, 77, 100);

        Assert.Equal(InternalMarkerKind.Hull, track.MarkerAt(stratum - 1));
        Assert.Equal(InternalMarkerKind.Critical, track.MarkerAt(stratum));
        Assert.Equal(InternalMarkerKind.Critical, track.MarkerAt(stratum * 2));
    }

    [Fact]
    public void Ordinary_track_is_deterministic_for_seed_and_position()
    {
        var first = new InternalDamageTrack(
            InternalCriticalDensity.Percent25,
            false,
            12345,
            40);
        var second = new InternalDamageTrack(
            InternalCriticalDensity.Percent25,
            false,
            12345,
            40);

        Assert.Equal(
            Enumerable.Range(1, 40).Select(first.MarkerAt),
            Enumerable.Range(1, 40).Select(second.MarkerAt));
    }

    [Fact]
    public void Track_continues_beyond_original_hull_without_rewinding()
    {
        var track = new InternalDamageTrack(
            InternalCriticalDensity.Percent25,
            true,
            5,
            12);

        Assert.Equal(3, track.CountCriticalMarkers(12));
        Assert.Equal(4, track.CountCriticalMarkers(16));
    }


    [Theory]
    [InlineData(InternalCriticalDensity.Percent15)]
    [InlineData(InternalCriticalDensity.Percent20)]
    [InlineData(InternalCriticalDensity.Percent25)]
    [InlineData(InternalCriticalDensity.Percent33)]
    [InlineData(InternalCriticalDensity.Percent50)]
    public void Protected_compartmentation_preserves_seeded_finite_x_count(
        InternalCriticalDensity density)
    {
        for (ulong seed = 0; seed < 512; seed++)
        {
            var ordinary = new InternalDamageTrack(density, false, seed, 12);
            var protectedTrack = new InternalDamageTrack(density, true, seed, 12);

            Assert.Equal(
                ordinary.CountCriticalMarkers(12),
                protectedTrack.CountCriticalMarkers(12));
            Assert.Equal(InternalMarkerKind.Hull, protectedTrack.MarkerAt(12));
        }
    }

    [Fact]
    public void Protected_terminal_x_swaps_with_adjacent_hull_marker()
    {
        var track = new InternalDamageTrack(
            InternalCriticalDensity.Percent25,
            protectedCompartmentation: true,
            seed: 99,
            originalHullSpan: 12);

        Assert.Equal(InternalMarkerKind.Critical, track.MarkerAt(11));
        Assert.Equal(InternalMarkerKind.Hull, track.MarkerAt(12));
        Assert.Equal(3, track.CountCriticalMarkers(12));
    }

    [Fact]
    public void Tl1_default_internal_critical_density_is_thirty_three_percent()
    {
        Assert.Equal(
            InternalCriticalDensity.Percent33,
            Tl1InternalDamageDefaults.OrdinaryDensity);
    }

    [Fact]
    public void Critical_exposure_uses_direct_weight_and_group_secondary_selection()
    {
        ShipComponentState reactor = Component("reactor", ShipComponentKind.MainReactor, 2);
        ShipComponentState ftl = Component("ftl", ShipComponentKind.FtlDrive, 1);
        ShipComponentState sensors = Electronics("sensors", ShipComponentKind.ActiveSensors);
        ShipComponentState comms = Electronics("comms", ShipComponentKind.Communications);
        var table = new CriticalExposureTable(new[] { reactor, ftl, sensors, comms });
        var selected = Enumerable.Range(0, 1000)
            .Select(index => table.Select(1234, index).ComponentId)
            .ToArray();

        Assert.Equal(4, table.TopLevelTicketCount);
        Assert.Contains("reactor", selected);
        Assert.Contains("ftl", selected);
        Assert.Contains("sensors", selected);
        Assert.Contains("comms", selected);
        Assert.True(selected.Count(id => id == "reactor") >
            selected.Count(id => id == "ftl"));
    }

    [Fact]
    public void Destroyed_components_remain_selectable_without_reroll()
    {
        ShipComponentState only = Component("reactor", ShipComponentKind.MainReactor, 1);
        only.SetConditionForScenario(ComponentCondition.Destroyed);
        var table = new CriticalExposureTable(new[] { only });

        CriticalExposureSelection result = table.Select(9, 0);

        Assert.Equal("reactor", result.ComponentId);
        Assert.False(only.ApplyCriticalHit().Changed);
    }

    [Fact]
    public void Magazine_first_hit_halves_capacity_and_contents_rounded_up()
    {
        ShipComponentState magazine = Storage(
            "magazine",
            ShipComponentKind.MissileMagazine,
            capacity: 25,
            contents: 25,
            loaded: 1);

        magazine.ApplyCriticalHit();

        Assert.Equal(ComponentCondition.Degraded, magazine.Condition);
        Assert.Equal(13, magazine.CurrentCapacity);
        Assert.Equal(13, magazine.CurrentContents);
        Assert.Equal(1, magazine.LoadedReadyPackages);
    }

    [Fact]
    public void Magazine_second_hit_destroys_stores_but_not_loaded_package()
    {
        ShipComponentState magazine = Storage(
            "magazine",
            ShipComponentKind.KineticMagazine,
            capacity: 25,
            contents: 19,
            loaded: 1);
        magazine.ApplyCriticalHit();

        magazine.ApplyCriticalHit();

        Assert.Equal(ComponentCondition.Destroyed, magazine.Condition);
        Assert.Equal(0, magazine.CurrentCapacity);
        Assert.Equal(0, magazine.CurrentContents);
        Assert.Equal(1, magazine.LoadedReadyPackages);
    }

    [Fact]
    public void Magazine_repair_restores_capacity_but_not_lost_ammunition()
    {
        ShipComponentState magazine = Storage(
            "magazine",
            ShipComponentKind.KineticMagazine,
            capacity: 25,
            contents: 25);
        magazine.ApplyCriticalHit();
        int remaining = magazine.CurrentContents;

        magazine.ApplyCombatRepair();

        Assert.Equal(ComponentCondition.Operational, magazine.Condition);
        Assert.Equal(25, magazine.CurrentCapacity);
        Assert.Equal(remaining, magazine.CurrentContents);
    }

    [Fact]
    public void Capacitor_destroyed_loses_stored_power_but_disabled_retains_it()
    {
        ShipComponentState capacitor = Storage(
            "capacitor",
            ShipComponentKind.PowerCapacitor,
            capacity: 3,
            contents: 2);
        capacitor.ApplyCriticalHit();
        capacitor.ApplyCriticalHit();

        Assert.Equal(ComponentCondition.Disabled, capacitor.Condition);
        Assert.Equal(2, capacitor.CurrentContents);

        capacitor.ApplyCriticalHit();

        Assert.Equal(ComponentCondition.Destroyed, capacitor.Condition);
        Assert.Equal(0, capacitor.CurrentContents);
    }

    [Fact]
    public void Hull_damage_advances_hx_and_applies_sequential_component_steps()
    {
        ShipDamageState ship = SingleComponentShip(
            hull: 6,
            density: InternalCriticalDensity.Percent50,
            protectedCompartmentation: true);

        ShipDamageResolution result = ShipDamageResolver.ResolvePacket(
            ship,
            new AttackPacket(6, 6, 6));

        Assert.Equal(6, result.LayeredDamage.HullDamage);
        Assert.Equal(3, result.InternalEvents.Count(item =>
            item.Marker == InternalMarkerKind.Critical));
        Assert.Equal(ComponentCondition.Destroyed,
            ship.GetComponent("reactor").Condition);
        Assert.True(ship.IsPendingDestruction);
        Assert.False(ship.IsDestroyed);
    }

    [Fact]
    public void Overkill_after_zero_hull_does_not_advance_more_markers()
    {
        ShipDamageState ship = SingleComponentShip(
            hull: 2,
            density: InternalCriticalDensity.Percent50,
            protectedCompartmentation: true);
        ShipDamageResolver.ResolvePacket(ship, new AttackPacket(8, 8, 8));
        int crossed = ship.InternalPositionsCrossed;

        ShipDamageResolution overkill = ShipDamageResolver.ResolvePacket(
            ship,
            new AttackPacket(4, 4, 4));

        Assert.Equal(crossed, ship.InternalPositionsCrossed);
        Assert.Empty(overkill.InternalEvents);
        Assert.Equal(4, overkill.LayeredDamage.OverkillDamage);
    }

    [Fact]
    public void Precision_critical_is_separate_from_hx_marker()
    {
        ShipDamageState ship = SingleComponentShip(
            hull: 6,
            density: InternalCriticalDensity.Percent50,
            protectedCompartmentation: true);

        ShipDamageResolution result = ShipDamageResolver.ResolvePacket(
            ship,
            new AttackPacket(1, 1, 1),
            precisionCritical: true);

        Assert.Equal(2, result.InternalEvents.Count);

        InternalDamageEvent hullEvent = result.InternalEvents[0];
        Assert.Equal(1, hullEvent.InternalPosition);
        Assert.Equal(InternalMarkerKind.Hull, hullEvent.Marker);
        Assert.False(hullEvent.PrecisionCritical);
        Assert.Null(hullEvent.Selection);
        Assert.Null(hullEvent.Transition);

        InternalDamageEvent precisionEvent = result.InternalEvents[1];
        Assert.Equal(1, precisionEvent.InternalPosition);
        Assert.Equal(InternalMarkerKind.Critical, precisionEvent.Marker);
        Assert.True(precisionEvent.PrecisionCritical);
        CriticalExposureSelection selection =
            Assert.IsType<CriticalExposureSelection>(precisionEvent.Selection);
        ComponentConditionTransition transition =
            Assert.IsType<ComponentConditionTransition>(precisionEvent.Transition);
        Assert.Equal("reactor", selection.ComponentId);
        Assert.Equal(ComponentCondition.Operational, transition.PreviousCondition);
        Assert.Equal(ComponentCondition.Degraded, transition.NewCondition);
        Assert.Equal(ComponentCondition.Degraded,
            ship.GetComponent("reactor").Condition);
    }

    [Fact]
    public void Pending_destruction_finalizes_only_at_end_of_damage_phase()
    {
        ShipDamageState ship = SingleComponentShip(
            hull: 1,
            density: InternalCriticalDensity.Percent50,
            protectedCompartmentation: true);
        ShipDamageResolver.ResolvePacket(ship, new AttackPacket(1, 1, 1));

        Assert.Equal(ShipCondition.PendingDestruction,
            ship.CapabilitySnapshot.Condition);

        ship.CompleteDamagePhase();

        Assert.Equal(ShipCondition.Destroyed, ship.CapabilitySnapshot.Condition);
    }

    [Fact]
    public void Shield_generator_destroyed_collapses_remaining_shields()
    {
        ShipComponentState shield = Component(
            "shield",
            ShipComponentKind.ShieldGenerator,
            1,
            ShipComponentCapability.ActiveDefense);
        shield.SetConditionForScenario(ComponentCondition.Disabled);
        var defense = new LayeredDefenseState(
            5, 5, 0, Array.Empty<ArmorLayerState>(), 6, 6);
        var ship = new ShipDamageState(
            defense,
            new InternalDamageTrack(InternalCriticalDensity.Percent50, true, 1, 6),
            new[] { shield },
            1,
            true);

        ShipDamageResolver.ResolvePacket(ship, new AttackPacket(2, 2, 2));

        Assert.Equal(ComponentCondition.Destroyed, shield.Condition);
        Assert.Equal(0, defense.CurrentShieldCapacity);
    }

    [Fact]
    public void Disabled_ship_requires_loss_of_offense_and_standard_stl_only()
    {
        ShipDamageState ship = CapabilityShip(isPlayer: true);
        ship.GetComponent("weapon").SetConditionForScenario(ComponentCondition.Disabled);
        ship.GetComponent("stl").SetConditionForScenario(ComponentCondition.Disabled);

        ShipCapabilitySnapshot snapshot = ship.CapabilitySnapshot;

        Assert.Equal(ShipCondition.Disabled, snapshot.Condition);
        Assert.True(snapshot.HasFtlDeparture);
        Assert.True(snapshot.HasEvasiveManeuvers);
        Assert.Contains("Disarmed", snapshot.Tags);
        Assert.Contains("Immobile", snapshot.Tags);
    }


    [Fact]
    public void Loaded_ready_package_preserves_offense_after_magazine_destruction_until_fired()
    {
        ShipDamageState ship = CapabilityShip(isPlayer: true);
        ShipComponentState magazine = ship.GetComponent("magazine");
        ship.GetComponent("stl").SetConditionForScenario(ComponentCondition.Disabled);
        magazine.SetConditionForScenario(ComponentCondition.Destroyed);

        Assert.True(ship.CapabilitySnapshot.HasOffensiveCapability);
        Assert.Equal(ShipCondition.Degraded, ship.CapabilitySnapshot.Condition);

        magazine.ConsumeReadyPackage();

        Assert.False(ship.CapabilitySnapshot.HasOffensiveCapability);
        Assert.Equal(ShipCondition.Disabled, ship.CapabilitySnapshot.Condition);
    }

    [Fact]
    public void Player_disabled_ftl_has_egress_but_npc_disabled_ftl_does_not()
    {
        ShipDamageState player = CapabilityShip(isPlayer: true);
        ShipDamageState npc = CapabilityShip(isPlayer: false);
        player.GetComponent("ftl").SetConditionForScenario(ComponentCondition.Disabled);
        npc.GetComponent("ftl").SetConditionForScenario(ComponentCondition.Disabled);

        Assert.True(player.CapabilitySnapshot.HasFtlDeparture);
        Assert.False(npc.CapabilitySnapshot.HasFtlDeparture);
    }

    [Fact]
    public void Pristine_ship_has_no_repairable_damage_or_damage_control_eligibility()
    {
        ShipDamageState ship = CapabilityShip(isPlayer: true);
        var power = new TacticalPowerLedger();
        power.BeginTurn(5);
        ship.BeginTurn();

        Assert.False(DamageControlService.HasRepairableComponentDamage(ship));
        Assert.False(DamageControlService.HasRepairableHullDamage(ship));
        Assert.False(DamageControlService.HasAnyRepairableDamage(ship));
        Assert.False(DamageControlService.CanAttemptDamageControl(ship, power));
        Assert.False(ship.CapabilitySnapshot.CanAttemptDamageControl);
    }

    [Fact]
    public void Missing_hull_enables_damage_control_eligibility()
    {
        ShipDamageState ship = CapabilityShip(isPlayer: true);
        ShipDamageResolver.ResolvePacket(ship, new AttackPacket(1, 1, 1));
        var power = new TacticalPowerLedger();
        power.BeginTurn(5);
        ship.BeginTurn();

        DamageControlEligibility eligibility =
            DamageControlService.EvaluateEligibility(ship, power);

        Assert.True(eligibility.HasRepairableHullDamage);
        Assert.True(eligibility.CanAttempt);
        Assert.True(ship.CapabilitySnapshot.CanAttemptDamageControl);
    }

    [Fact]
    public void Pristine_hull_repair_attempt_spends_no_power_or_repair_kit()
    {
        ShipDamageState ship = CapabilityShip(isPlayer: true);
        var power = new TacticalPowerLedger();
        power.BeginTurn(5);
        ship.BeginTurn();

        Assert.Throws<InvalidOperationException>(() =>
            DamageControlService.AttemptHullRepair(ship, power, roll: 1));
        Assert.Equal(0, power.SpentPower);
        Assert.Equal(3, ship.DamageControl.RepairKitsRemaining);
        Assert.Empty(ship.PendingRepairs);
    }

    [Fact]
    public void Destroyed_component_is_not_a_combat_repair_target()
    {
        ShipDamageState ship = CapabilityShip(isPlayer: true);
        ship.GetComponent("weapon").SetConditionForScenario(
            ComponentCondition.Destroyed);
        var power = new TacticalPowerLedger();
        power.BeginTurn(5);
        ship.BeginTurn();

        Assert.False(DamageControlService.HasRepairableComponentDamage(ship));
        Assert.False(DamageControlService.CanAttemptDamageControl(ship, power));
    }

    [Fact]
    public void Five_kit_profile_is_calibration_only()
    {
        Assert.Equal(3, DamageControlProfile.Tl1.StartingRepairKits);
        Assert.Equal(5,
            DamageControlProfile.Tl1CalibrationFiveKits.StartingRepairKits);
        ShipDamageState ship = CapabilityShip(
            isPlayer: true,
            damageControlProfile: DamageControlProfile.Tl1CalibrationFiveKits);

        Assert.Equal(5, ship.DamageControl.RepairKitsRemaining);
    }

    [Fact]
    public void Damage_control_consumes_power_and_kit_even_on_failure()
    {
        ShipDamageState ship = CapabilityShip(isPlayer: true);
        ship.GetComponent("stl").SetConditionForScenario(ComponentCondition.Degraded);
        var power = new TacticalPowerLedger();
        power.BeginTurn(5);
        ship.BeginTurn();

        DamageControlAttemptResult result = DamageControlService.AttemptComponentRepair(
            ship,
            "stl",
            power,
            roll: 100);

        Assert.False(result.Succeeded);
        Assert.Equal(1, power.SpentPower);
        Assert.Equal(2, ship.DamageControl.RepairKitsRemaining);
        Assert.Empty(ship.PendingRepairs);
    }

    [Fact]
    public void Successful_damage_control_activates_at_next_turn_refresh()
    {
        ShipDamageState ship = CapabilityShip(isPlayer: true);
        ship.GetComponent("stl").SetConditionForScenario(ComponentCondition.Disabled);
        var power = new TacticalPowerLedger();
        power.BeginTurn(5);
        ship.BeginTurn();

        DamageControlAttemptResult result = DamageControlService.AttemptComponentRepair(
            ship,
            "stl",
            power,
            roll: 1);

        Assert.True(result.Succeeded);
        Assert.Equal(ComponentCondition.Disabled,
            ship.GetComponent("stl").Condition);

        ship.ApplyPendingRepairsAtTurnRefresh();

        Assert.Equal(ComponentCondition.Degraded,
            ship.GetComponent("stl").Condition);
    }

    [Fact]
    public void Damage_control_capacity_allows_only_one_attempt_per_turn()
    {
        ShipDamageState ship = CapabilityShip(isPlayer: true);
        ship.GetComponent("stl").SetConditionForScenario(ComponentCondition.Degraded);
        ship.GetComponent("weapon").SetConditionForScenario(ComponentCondition.Degraded);
        var power = new TacticalPowerLedger();
        power.BeginTurn(5);
        ship.BeginTurn();
        DamageControlService.AttemptComponentRepair(ship, "stl", power, 100);

        DamageControlEligibility eligibility =
            DamageControlService.EvaluateEligibility(ship, power);
        Assert.False(eligibility.HasAttemptCapacity);
        Assert.False(eligibility.CanAttempt);
        Assert.False(ship.CapabilitySnapshot.CanAttemptDamageControl);
        Assert.Throws<InvalidOperationException>(() =>
            DamageControlService.AttemptComponentRepair(ship, "weapon", power, 100));
        Assert.Equal(1, power.SpentPower);
        Assert.Equal(2, ship.DamageControl.RepairKitsRemaining);
    }

    [Theory]
    [InlineData(WeaponFamily.Kinetic, 3, 2, 3, 2, true)]
    [InlineData(WeaponFamily.Missile, 3, 0, 3, 0, true)]
    [InlineData(WeaponFamily.Energy, 3, 2, 2, 1, false)]
    public void Degraded_weapon_profiles_follow_family_rules(
        WeaponFamily family,
        int damage,
        int power,
        int expectedDamage,
        int expectedPower,
        bool recycle)
    {
        ConditionedWeaponPerformance result = ComponentPerformance.Weapon(
            family,
            ComponentCondition.Degraded,
            damage,
            power);

        Assert.Equal(expectedDamage, result.Damage);
        Assert.Equal(expectedPower, result.TacticalPowerCost);
        Assert.Equal(recycle, result.RequiresFullRecycleTurnAfterFire);
        Assert.False(result.EnhancedModesAvailable);
    }

    [Fact]
    public void Degraded_recycling_weapon_skips_full_turn_after_firing()
    {
        var cycle = new DegradedWeaponRecycleState();
        cycle.BeginTurn();
        cycle.RecordFire(ComponentCondition.Degraded);

        cycle.BeginTurn();
        Assert.True(cycle.IsRecyclingThisTurn);
        Assert.False(cycle.CanFire(ComponentCondition.Degraded));

        cycle.BeginTurn();
        Assert.True(cycle.CanFire(ComponentCondition.Degraded));
    }

    [Fact]
    public void Degraded_pds_halves_native_accuracy_before_computer_bonus()
    {
        int native = ComponentPerformance.PdsBaseAccuracy(
            41,
            ComponentCondition.Degraded);
        int computer = ComponentPerformance.TargetingComputerBonus(
            10,
            ComponentCondition.Degraded);

        Assert.Equal(21, native);
        Assert.Equal(5, computer);
        Assert.Equal(26, native + computer);
    }

    [Fact]
    public void Degraded_sensors_computer_and_evm_use_agreed_rounding()
    {
        Assert.Equal(2, ComponentPerformance.ActiveSensorContribution(
            5, ComponentCondition.Degraded));
        Assert.Equal(2, ComponentPerformance.TargetingComputerBonus(
            5, ComponentCondition.Degraded));
        Assert.Equal(1, ComponentPerformance.EvasiveDefenseBonus(
            3, ComponentCondition.Degraded));
        Assert.Equal(2, ComponentPerformance.EvasiveAttackPenaltyMagnitude(
            3, ComponentCondition.Degraded));
    }

    [Fact]
    public void Degraded_stl_and_ftl_halve_rounding_up()
    {
        Assert.Equal(3, ComponentPerformance.StlMovement(
            5, ComponentCondition.Degraded));
        Assert.Equal(3, ComponentPerformance.FtlRange(
            5, ComponentCondition.Degraded, isPlayerShip: true));
        Assert.Equal(1, ComponentPerformance.FtlRange(
            5, ComponentCondition.Disabled, isPlayerShip: true));
        Assert.Equal(0, ComponentPerformance.FtlRange(
            5, ComponentCondition.Disabled, isPlayerShip: false));
    }

    [Fact]
    public void Degraded_ecm_eccm_and_hardener_require_one_extra_power()
    {
        Assert.Equal(1, ComponentPerformance.AdditionalCommittedPower(
            ShipComponentKind.Ecm,
            ComponentCondition.Degraded));
        Assert.Equal(1, ComponentPerformance.AdditionalCommittedPower(
            ShipComponentKind.Eccm,
            ComponentCondition.Degraded));
        Assert.Equal(1, ComponentPerformance.AdditionalCommittedPower(
            ShipComponentKind.ShieldHardener,
            ComponentCondition.Degraded));
        Assert.Equal(0, ComponentPerformance.AdditionalCommittedPower(
            ShipComponentKind.Ecm,
            ComponentCondition.Operational));
        Assert.Equal(0, ComponentPerformance.AdditionalCommittedPower(
            ShipComponentKind.ActiveSensors,
            ComponentCondition.Degraded));
    }

    [Fact]
    public void Immobile_target_bonus_begins_with_the_following_turn_snapshot()
    {
        ShipDamageState ship = CapabilityShip(isPlayer: true);
        ShipCombatTurnSnapshot committedSnapshot =
            ShipCombatTurnSnapshot.Capture(ship);
        ship.GetComponent("stl").SetConditionForScenario(
            ComponentCondition.Disabled);

        var profile = new DirectFireAccuracyProfile(
            50, 20, 10, 5, 10, 5);
        DirectFireAccuracyResult committed =
            DirectFireAccuracyCalculator.Calculate(
                profile,
                rangeHexes: 2,
                targetEvasive: false,
                shooterEvasive: false,
                targetStlCondition: committedSnapshot.StlCondition);
        ShipCombatTurnSnapshot followingSnapshot =
            ShipCombatTurnSnapshot.Capture(ship);
        DirectFireAccuracyResult following =
            DirectFireAccuracyCalculator.Calculate(
                profile,
                rangeHexes: 2,
                targetEvasive: false,
                shooterEvasive: false,
                targetStlCondition: followingSnapshot.StlCondition);

        Assert.False(committedSnapshot.IsImmobile);
        Assert.Equal(0, committed.TargetMobilityBonus);
        Assert.True(followingSnapshot.IsImmobile);
        Assert.Equal(10, following.TargetMobilityBonus);
    }

    [Theory]
    [InlineData(ComponentCondition.Operational)]
    [InlineData(ComponentCondition.Degraded)]
    [InlineData(ComponentCondition.Disabled)]
    [InlineData(ComponentCondition.Destroyed)]
    public void Target_stl_condition_does_not_modify_pds_accuracy(
        ComponentCondition targetStlCondition)
    {
        _ = targetStlCondition;
        Assert.Equal(35, ComponentPerformance.PdsBaseAccuracy(
            35, ComponentCondition.Operational));
    }

    [Fact]
    public void Degraded_shield_generator_doubles_recharge_cost()
    {
        Assert.Equal(4, ComponentPerformance.ShieldRechargePowerCost(
            2, ComponentCondition.Degraded));
        Assert.Throws<InvalidOperationException>(() =>
            ComponentPerformance.ShieldRechargePowerCost(
                2, ComponentCondition.Disabled));
    }

    private static ShipDamageState SingleComponentShip(
        int hull,
        InternalCriticalDensity density,
        bool protectedCompartmentation)
    {
        var defense = new LayeredDefenseState(
            0, 0, 0, Array.Empty<ArmorLayerState>(), hull, hull);
        return new ShipDamageState(
            defense,
            new InternalDamageTrack(density, protectedCompartmentation, 1, hull),
            new[] { Component("reactor", ShipComponentKind.MainReactor, 1,
                ShipComponentCapability.PowerSource) },
            1,
            true);
    }

    private static ShipDamageState CapabilityShip(
        bool isPlayer,
        DamageControlProfile? damageControlProfile = null)
    {
        var components = new[]
        {
            Component("reactor", ShipComponentKind.MainReactor, 2,
                ShipComponentCapability.PowerSource),
            Component("weapon", ShipComponentKind.KineticWeapon, 1,
                ShipComponentCapability.Offense),
            Storage("magazine", ShipComponentKind.KineticMagazine,
                capacity: 25, contents: 25, loaded: 1),
            Component("stl", ShipComponentKind.StlDrive, 2,
                ShipComponentCapability.StandardStlMovement),
            Component("ftl", ShipComponentKind.FtlDrive, 1,
                ShipComponentCapability.FtlDeparture),
            Component("evm", ShipComponentKind.EvasiveManeuverSystem, 1,
                ShipComponentCapability.ActiveDefense |
                ShipComponentCapability.EvasiveManeuvers),
        };
        return new ShipDamageState(
            new LayeredDefenseState(
                0, 0, 0, Array.Empty<ArmorLayerState>(), 12, 12),
            new InternalDamageTrack(
                InternalCriticalDensity.Percent25, true, 1, 12),
            components,
            2,
            isPlayer,
            damageControlProfile);
    }

    private static ShipComponentState Component(
        string id,
        ShipComponentKind kind,
        int exposure,
        ShipComponentCapability capabilities = ShipComponentCapability.None) => new(
        new ShipComponentDefinition(
            id,
            kind,
            exposure,
            capabilities: capabilities));

    private static ShipComponentState Electronics(
        string id,
        ShipComponentKind kind) => new(
        new ShipComponentDefinition(
            id,
            kind,
            0,
            CriticalExposureGroup.Electronics));

    private static ShipComponentState Storage(
        string id,
        ShipComponentKind kind,
        int capacity,
        int? contents = null,
        int loaded = 0) => new(
        new ShipComponentDefinition(id, kind, 1),
        pristineCapacity: capacity,
        currentContents: contents,
        loadedReadyPackages: loaded);
}
